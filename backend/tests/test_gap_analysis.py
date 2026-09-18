from app.conversation.gap_analysis import next_clarifying_question, next_refinement_suggestion


def test_asks_land_cover_first_when_nothing_is_known():
    question = next_clarifying_question({}, rounds_asked=0, max_rounds=3)
    assert question is not None
    assert question.field == "land_cover"


def test_blocking_fields_are_exactly_the_briefs_own_clarifying_example():
    # the assignment brief's own example asks for soil organic carbon, rainfall, and land use -
    # nothing else should be able to block a first answer
    known = {"land_cover": "cropland", "rainfall_regime": "low"}
    question = next_clarifying_question(known, rounds_asked=0, max_rounds=3)
    assert question.field == "soil_organic_carbon"

    fully_known = {**known, "soil_organic_carbon": 0.3}
    assert next_clarifying_question(fully_known, rounds_asked=0, max_rounds=3) is None


def test_returns_none_once_max_rounds_reached():
    question = next_clarifying_question({}, rounds_asked=3, max_rounds=3)
    assert question is None


def test_refinement_suggests_groundwater_when_tree_interventions_are_plausible():
    suggestion = next_refinement_suggestion({"land_cover": "cropland"})
    assert suggestion.field == "groundwater_depth_m"


def test_refinement_skips_groundwater_when_land_cover_rules_out_trees():
    suggestion = next_refinement_suggestion({"land_cover": "urban"})
    assert suggestion.field == "soil_texture"


def test_refinement_returns_none_when_everything_is_known():
    known = {
        "land_cover": "cropland",
        "rainfall_regime": "low",
        "soil_texture": "sandy_loam",
        "soil_organic_carbon": 0.3,
        "groundwater_depth_m": 18,
    }
    assert next_refinement_suggestion(known) is None
