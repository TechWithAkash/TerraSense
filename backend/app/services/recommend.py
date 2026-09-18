from sqlalchemy.orm import Session as DbSession

from app.conversation.narrate import build_why_it_works
from app.conversation.session import get_baseline_values
from app.models import CausalEdge, Claim, ConversationSession, Intervention, Variable
from app.reasoning.confidence import compute_confidence
from app.reasoning.graph_engine import DirectEffect, EdgeDTO, detect_trade_offs, propagate
from app.reasoning.ranking import is_feasible, rank_candidates, score_candidate
from app.schemas import ConfidenceOut, EvidenceOut, ImpactedMetric, RecommendationOut, TradeOffOut

RAINFALL_TO_ARIDITY = {"low": "semi_arid", "moderate": "sub_humid", "high": "humid"}

# real aridity indices (e.g. De Martonne) combine temperature and rainfall, not rainfall alone -
# higher temperature raises potential evapotranspiration, pushing the same rainfall level toward
# a more severe classification. this is a coarse but defensible step, not a full index.
ARIDITY_SEVERITY_LADDER = ["humid", "sub_humid", "semi_arid", "arid"]

TRADE_OFF_MITIGATIONS = {
    "groundwater_depth": "Pair with contour bunding or drip irrigation, or choose a lower-transpiration native species instead.",
    "fragmentation_index": "Combine with a field-margin hedgerow so the added structure connects rather than isolates habitat patches.",
    "nutrient_runoff": "Add a native grass buffer strip downslope to intercept the extra runoff.",
}


def _apply_temperature_to_aridity(
    aridity: str | None, mean_temperature_c: float | None
) -> str | None:
    if aridity not in ARIDITY_SEVERITY_LADDER or mean_temperature_c is None:
        return aridity
    steps = 1 if mean_temperature_c >= 35 else (1 if mean_temperature_c >= 30 else 0)
    index = min(len(ARIDITY_SEVERITY_LADDER) - 1, ARIDITY_SEVERITY_LADDER.index(aridity) + steps)
    return ARIDITY_SEVERITY_LADDER[index]


def build_situation(context: dict) -> dict:
    rainfall_regime = context.get("rainfall_regime")
    aridity = context.get("aridity") or RAINFALL_TO_ARIDITY.get(rainfall_regime)
    aridity = _apply_temperature_to_aridity(aridity, context.get("mean_temperature_c"))
    return {
        "soil_texture": context.get("soil_texture"),
        "rainfall_regime": rainfall_regime,
        "aridity": aridity,
    }


def _time_horizon_bucket(months: int | None) -> str:
    if months is None:
        return "medium_term"
    if months <= 12:
        return "short_term"
    if months <= 36:
        return "medium_term"
    return "long_term"


def _load_edges(db: DbSession) -> list[EdgeDTO]:
    return [
        EdgeDTO(
            id=row.id,
            source_variable=row.source_variable,
            target_variable=row.target_variable,
            sign=row.sign,
            per_unit_source=row.per_unit_source,
            delta_low=row.delta_low,
            delta_mid=row.delta_mid,
            delta_high=row.delta_high,
            transform=row.transform,
            saturation_point=row.saturation_point,
            context=row.context or {},
            confidence_tier=row.confidence_tier,
            evidence_claim_ids=row.evidence_claim_ids or [],
            notes=row.notes,
        )
        for row in db.query(CausalEdge).all()
    ]


def _load_variables(db: DbSession) -> dict[str, dict]:
    return {
        row.id: {
            "label": row.label,
            "unit": row.unit,
            "category": row.category,
            "higher_is_worse": row.higher_is_worse,
        }
        for row in db.query(Variable).all()
    }


def generate_recommendations(
    db: DbSession, session: ConversationSession, top_n: int = 5
) -> list[RecommendationOut]:
    context = session.context or {}
    situation = build_situation(context)
    baseline_values, provenance = get_baseline_values(db, session.site_id)
    edges = _load_edges(db)
    variables_by_id = _load_variables(db)
    interventions = db.query(Intervention).all()

    scored_candidates: list[dict] = []

    for intervention in interventions:
        feasible, _reason = is_feasible(
            {
                "applicable_when": intervention.applicable_when,
                "excluded_when": intervention.excluded_when,
                "cost": intervention.cost,
            },
            context,
        )
        if not feasible:
            continue

        direct_effects = [
            DirectEffect(
                variable=effect["variable"],
                delta_low=effect["delta_low"],
                delta_mid=effect["delta_mid"],
                delta_high=effect["delta_high"],
                evidence_claim_ids=effect.get("evidence_claim_ids", []),
                transform=effect.get("transform", "linear"),
                saturation_point=effect.get("saturation_point"),
            )
            for effect in intervention.direct_effects
        ]

        situation_for_intervention = dict(situation)
        if intervention.trade_off_species_group:
            situation_for_intervention["species_group"] = intervention.trade_off_species_group

        result = propagate(direct_effects, edges, situation_for_intervention, baseline_values)
        trade_offs = detect_trade_offs(result.deltas, variables_by_id, result.paths)

        claim_ids: set[str] = set()
        for effect in direct_effects:
            claim_ids.update(effect.evidence_claim_ids)
        for edge in result.edges_traversed:
            claim_ids.update(edge.evidence_claim_ids)
        claims = db.query(Claim).filter(Claim.id.in_(claim_ids)).all() if claim_ids else []

        touched_variables = set(result.deltas.keys())
        edge_confidence_tiers = [edge.confidence_tier for edge in result.edges_traversed]
        mean_path_length = len(result.edges_traversed) / max(1, len(direct_effects))

        confidence = compute_confidence(
            claim_study_designs=[claim.study_design for claim in claims],
            edge_confidence_tiers=edge_confidence_tiers,
            touched_variables=touched_variables,
            provenance_by_variable=provenance,
            mean_path_length=mean_path_length,
        )

        predicted_mid = {var: delta.mid for var, delta in result.deltas.items()}
        capex_range = intervention.cost.get("capex_inr_per_ha") if intervention.cost else None
        score = score_candidate(
            intervention.id,
            predicted_mid,
            confidence.score,
            capex_range,
            intervention.time_to_first_effect_months,
        )

        scored_candidates.append(
            {
                "intervention": intervention,
                "result": result,
                "trade_offs": trade_offs,
                "claims": claims,
                "confidence": confidence,
                "score": score,
            }
        )

    ranked_scores = rank_candidates([c["score"] for c in scored_candidates])
    scores_by_id = {c["intervention"].id: c for c in scored_candidates}

    recommendations: list[RecommendationOut] = []
    for rank, score in enumerate(ranked_scores[:top_n], start=1):
        candidate = scores_by_id[score.intervention_id]
        intervention: Intervention = candidate["intervention"]
        result = candidate["result"]

        impacted_metrics = [
            ImpactedMetric(
                variable=variable_id,
                label=variables_by_id.get(variable_id, {}).get("label", variable_id),
                baseline=baseline_values.get(variable_id),
                projected_low=round(baseline_values.get(variable_id, 0.0) + delta.low, 3),
                projected_mid=round(baseline_values.get(variable_id, 0.0) + delta.mid, 3),
                projected_high=round(baseline_values.get(variable_id, 0.0) + delta.high, 3),
                unit=variables_by_id.get(variable_id, {}).get("unit", ""),
                horizon=_time_horizon_bucket(intervention.time_to_first_effect_months),
            )
            for variable_id, delta in result.deltas.items()
        ]

        path_steps_for_narration = [
            {
                "from_variable": step.from_variable,
                "to_variable": step.to_variable,
                "to_label": variables_by_id.get(step.to_variable, {}).get(
                    "label", step.to_variable
                ),
            }
            for step in result.paths
        ]
        claim_summaries = [claim.summary for claim in candidate["claims"]]
        why_it_works = build_why_it_works(
            intervention.label, path_steps_for_narration, claim_summaries
        )

        evidence = [
            EvidenceOut(
                claim_id=claim.id,
                document=claim.document,
                publisher=claim.publisher,
                year=claim.year,
                study_design=claim.study_design,
                summary=claim.summary,
            )
            for claim in candidate["claims"]
        ]

        trade_offs = [
            TradeOffOut(
                variable=t["variable"],
                label=t["label"],
                direction=t["direction"],
                magnitude=f"{t['delta_low']:+.2f} to {t['delta_high']:+.2f} {t['unit']}",
                cause_path=t["cause_path"],
                mitigation=TRADE_OFF_MITIGATIONS.get(t["variable"]),
            )
            for t in candidate["trade_offs"]
        ]

        confidence = candidate["confidence"]

        recommendations.append(
            RecommendationOut(
                rank=rank,
                intervention_id=intervention.id,
                label=intervention.label,
                what_to_do=intervention.label,
                why_it_works=why_it_works,
                impacted_metrics=impacted_metrics,
                time_horizon=_time_horizon_bucket(intervention.time_to_first_effect_months),
                confidence=ConfidenceOut(
                    score=confidence.score,
                    band=confidence.band,
                    limiting_factor=confidence.limiting_factor,
                    components=confidence.components,
                ),
                evidence=evidence,
                trade_offs=trade_offs,
                cost_inr_per_ha=intervention.cost.get("capex_inr_per_ha")
                if intervention.cost
                else None,
                labour_days_per_ha=(
                    [intervention.labour_days_low, intervention.labour_days_high]
                    if intervention.labour_days_low is not None
                    else None
                ),
            )
        )

    return recommendations
