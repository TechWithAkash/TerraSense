from dataclasses import dataclass

# decides what to ask next. one question at a time, always the one that would change the
# recommendation the most, never just "the next blank field in a form."
#
# two tiers, not one:
#   - BLOCKING_FIELDS: nothing useful can be said without these. this is deliberately the exact
#     3 fields the assignment brief's own clarifying-question example asks for (soil organic
#     carbon, rainfall pattern, land use type) - matching it means a reasonably complete first
#     message (like the brief's own worked example) gets a real answer immediately, not another
#     question.
#   - REFINEMENT_FIELDS: genuinely useful (they sharpen confidence and can change which
#     intervention is safe), but the system answers now with an inferred assumption and invites
#     the user to correct it, rather than gating the whole response on one more question.

BLOCKING_FIELDS: list[dict] = [
    {
        "field": "land_cover",
        "question": "What is this land currently used for — cropland, grassland, or forest?",
        "why": "it decides which interventions are even applicable here",
    },
    {
        "field": "rainfall",  # satisfied by either rainfall_regime or annual_rainfall_mm
        "question": "Roughly how much rain does this land get? A rough sense — low, moderate, or high — is enough.",
        "why": "rainfall gates whether moisture and cover-based interventions will actually work",
    },
    {
        "field": "soil_organic_carbon",
        "question": "Do you know roughly what your soil organic carbon percentage is, or should I assume it's degraded based on what you've told me?",
        "why": "it is the anchor baseline for almost every soil health calculation",
    },
]

GROUNDWATER_FIELD = {
    "field": "groundwater_depth_m",
    "question": "One more thing would sharpen this: roughly how deep is your borewell water level, and has it dropped in recent years?",
    "why": "it decides whether tree-based options are safe here or would make your water problem worse",
}

SOIL_TEXTURE_FIELD = {
    "field": "soil_texture",
    "question": "If you know it, what's the general soil texture — sandy, loamy, or clay?",
    "why": "it strongly changes how much benefit added organic carbon actually delivers",
}


@dataclass
class ClarifyingQuestion:
    field: str
    question: str
    why: str


def _is_known(field: str, known_context: dict) -> bool:
    if field == "rainfall":
        return (
            known_context.get("rainfall_regime") is not None
            or known_context.get("annual_rainfall_mm") is not None
        )
    return known_context.get(field) is not None


def _tree_intervention_plausible(known_context: dict) -> bool:
    land_cover = known_context.get("land_cover")
    return land_cover in (None, "cropland", "grassland")


def next_clarifying_question(
    known_context: dict, rounds_asked: int, max_rounds: int
) -> ClarifyingQuestion | None:
    # only these three ever block a first answer - matches the brief's own worked example exactly
    if rounds_asked >= max_rounds:
        return None

    for candidate in BLOCKING_FIELDS:
        if not _is_known(candidate["field"], known_context):
            return ClarifyingQuestion(
                field=candidate["field"], question=candidate["question"], why=candidate["why"]
            )

    return None


def next_refinement_suggestion(known_context: dict) -> ClarifyingQuestion | None:
    # asked alongside a real answer, never instead of one
    candidates = [GROUNDWATER_FIELD] if _tree_intervention_plausible(known_context) else []
    candidates.append(SOIL_TEXTURE_FIELD)

    for candidate in candidates:
        if not _is_known(candidate["field"], known_context):
            return ClarifyingQuestion(
                field=candidate["field"], question=candidate["question"], why=candidate["why"]
            )

    return None
