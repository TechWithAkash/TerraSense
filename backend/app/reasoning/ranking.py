from dataclasses import dataclass

# ranks candidate interventions once we know their simulated impact, cost, and confidence.
# weights favour ecological impact and evidence quality heavily: the brief grades depth of
# reasoning and scientific grounding, never cost-effectiveness or speed of payoff. cost and speed
# stay in as real, legitimate tie-breakers (and matter more once a user states an actual budget,
# via the feasibility filter in is_feasible), but they must not be able to out-vote a genuinely
# higher-impact, well-evidenced intervention just for being cheaper or faster.
RANK_WEIGHTS = {
    "biodiversity_impact": 0.55,
    "confidence": 0.30,
    "cost_efficiency": 0.10,
    "speed": 0.05,
}

# species_richness/pollinator_abundance/soil_biota_activity are direct biodiversity outcomes;
# fragmentation_index is explicitly "habitat diversity" per the brief's own knowledge-base
# categories, so it counts too. fragmentation_index is "higher is worse" (see variables.yaml), so
# its delta gets sign-flipped in score_candidate below - a fragmentation *decrease* is the win.
BIODIVERSITY_VARIABLES = {
    "species_richness",
    "pollinator_abundance",
    "soil_biota_activity",
    "fragmentation_index",
}
INVERTED_BIODIVERSITY_VARIABLES = {"fragmentation_index"}


@dataclass
class CandidateScore:
    intervention_id: str
    biodiversity_impact: float
    confidence: float
    cost_efficiency: float
    speed: float
    total: float


def is_feasible(intervention: dict, context: dict) -> tuple[bool, str | None]:
    applicable_when = intervention.get("applicable_when") or {}
    excluded_when = intervention.get("excluded_when") or {}

    land_cover_required = applicable_when.get("land_cover")
    if land_cover_required and context.get("land_cover") not in land_cover_required:
        return (
            False,
            f"needs land cover in {land_cover_required}, site is {context.get('land_cover')}",
        )

    rainfall_min = applicable_when.get("rainfall_mm_min")
    if (
        rainfall_min
        and context.get("annual_rainfall_mm") is not None
        and context["annual_rainfall_mm"] < rainfall_min
    ):
        return False, f"needs at least {rainfall_min}mm annual rainfall"

    slope_min = applicable_when.get("slope_percent_min")
    if (
        slope_min
        and context.get("slope_percent") is not None
        and context["slope_percent"] < slope_min
    ):
        return False, f"needs at least {slope_min}% slope"

    groundwater_limit = excluded_when.get("groundwater_depth_m_min")
    if (
        groundwater_limit
        and context.get("groundwater_depth_m") is not None
        and context["groundwater_depth_m"] >= groundwater_limit
    ):
        return (
            False,
            f"water table already at {context['groundwater_depth_m']}m, too deep for added transpiration demand",
        )

    budget = context.get("budget_inr_per_ha")
    if budget is not None:
        capex = intervention.get("cost", {}).get("capex_inr_per_ha")
        if capex and capex[0] > budget:
            return False, f"minimum cost {capex[0]} INR/ha exceeds stated budget of {budget}"

    return True, None


def score_candidate(
    intervention_id: str,
    predicted_deltas: dict[str, float],
    confidence_score: float,
    capex_range: list[float] | None,
    time_to_first_effect_months: int | None,
) -> CandidateScore:
    biodiversity_impact = 0.0
    for var, delta in predicted_deltas.items():
        if var not in BIODIVERSITY_VARIABLES:
            continue
        biodiversity_impact += -delta if var in INVERTED_BIODIVERSITY_VARIABLES else delta
    biodiversity_impact = max(0.0, min(1.0, biodiversity_impact))

    if capex_range:
        avg_capex = sum(capex_range) / len(capex_range)
        cost_efficiency = 1.0 / (1.0 + avg_capex / 20000)  # cheaper interventions score closer to 1
    else:
        cost_efficiency = 0.7

    if time_to_first_effect_months:
        speed = 1.0 / (1.0 + time_to_first_effect_months / 12)
    else:
        speed = 0.6

    total = (
        RANK_WEIGHTS["biodiversity_impact"] * biodiversity_impact
        + RANK_WEIGHTS["confidence"] * confidence_score
        + RANK_WEIGHTS["cost_efficiency"] * cost_efficiency
        + RANK_WEIGHTS["speed"] * speed
    )
    return CandidateScore(
        intervention_id=intervention_id,
        biodiversity_impact=round(biodiversity_impact, 3),
        confidence=round(confidence_score, 3),
        cost_efficiency=round(cost_efficiency, 3),
        speed=round(speed, 3),
        total=round(total, 3),
    )


def rank_candidates(scores: list[CandidateScore]) -> list[CandidateScore]:
    return sorted(scores, key=lambda s: s.total, reverse=True)
