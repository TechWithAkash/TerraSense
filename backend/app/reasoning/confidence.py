from dataclasses import dataclass

# confidence is computed, never invented by an LLM. five components, weighted geometric mean.
# geometric mean punishes a single weak component far more than an arithmetic mean would,
# which is what we want: one badly-supported link should drag the whole score down.

STUDY_DESIGN_WEIGHTS = {
    "meta_analysis": 1.00,
    "long_term_trial": 0.90,
    "rct": 0.85,
    "field_trial": 0.70,
    "observational": 0.55,
    "modelled": 0.45,
    "assessment": 0.65,
    "expert_opinion": 0.30,
}

CONFIDENCE_TIER_WEIGHTS = {"high": 1.0, "medium": 0.75, "low": 0.5}

COMPONENT_WEIGHTS = {
    "evidence_strength": 0.35,
    "edge_reliability": 0.25,
    "input_completeness": 0.25,
    "path_directness": 0.15,
}


@dataclass
class ConfidenceBreakdown:
    score: float
    band: str
    components: dict[str, float]
    limiting_factor: str


def _geometric_mean(components: dict[str, float], weights: dict[str, float]) -> float:
    total_weight = sum(weights.values())
    product = 1.0
    for key, value in components.items():
        weight = weights.get(key, 0.0) / total_weight if total_weight else 0
        safe_value = max(
            value, 0.01
        )  # avoid log(0) tanking the whole score to zero on one weak input
        product *= safe_value**weight
    return product


def _band(score: float) -> str:
    if score >= 0.80:
        return "High"
    if score >= 0.65:
        return "Medium-High"
    if score >= 0.45:
        return "Medium"
    return "Low"


def score_evidence(claim_study_designs: list[str]) -> float:
    if not claim_study_designs:
        return 0.4  # a reasoning path with no supporting claim is weak, not zero
    weights = [STUDY_DESIGN_WEIGHTS.get(design, 0.5) for design in claim_study_designs]
    return sum(weights) / len(weights)


def score_edge_reliability(confidence_tiers: list[str]) -> float:
    if not confidence_tiers:
        return 0.6
    weights = [CONFIDENCE_TIER_WEIGHTS.get(tier, 0.6) for tier in confidence_tiers]
    return sum(weights) / len(weights)


def score_input_completeness(
    touched_variables: set[str], provenance_by_variable: dict[str, str]
) -> float:
    if not touched_variables:
        return 0.5
    known = sum(1 for v in touched_variables if provenance_by_variable.get(v) == "user")
    return 0.4 + 0.6 * (
        known / len(touched_variables)
    )  # never below 0.4, a fully known site approaches 1.0


def score_path_directness(mean_path_length: float) -> float:
    return 1.0 / (1 + 0.4 * mean_path_length)


def compute_confidence(
    claim_study_designs: list[str],
    edge_confidence_tiers: list[str],
    touched_variables: set[str],
    provenance_by_variable: dict[str, str],
    mean_path_length: float,
) -> ConfidenceBreakdown:
    components = {
        "evidence_strength": score_evidence(claim_study_designs),
        "edge_reliability": score_edge_reliability(edge_confidence_tiers),
        "input_completeness": score_input_completeness(touched_variables, provenance_by_variable),
        "path_directness": score_path_directness(mean_path_length),
    }
    score = _geometric_mean(components, COMPONENT_WEIGHTS)
    limiting_factor = min(components, key=components.get)
    return ConfidenceBreakdown(
        score=round(score, 2),
        band=_band(score),
        components=components,
        limiting_factor=limiting_factor,
    )
