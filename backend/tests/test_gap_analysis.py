from app.conversation.gap_analysis import next_clarifying_question


def test_asks_land_cover_first_when_nothing_is_known():
    question = next_clarifying_question({}, rounds_asked=0, max_rounds=3)
    assert question is not None
    assert question.field == "land_cover"


def test_asks_groundwater_early_when_tree_interventions_are_plausible():
    question = next_clarifying_question({"land_cover": "cropland"}, rounds_asked=1, max_rounds=3)
    assert question.field == "groundwater_depth_m"


def test_skips_groundwater_question_when_land_cover_rules_out_trees():
    question = next_clarifying_question({"land_cover": "urban"}, rounds_asked=1, max_rounds=3)
    assert question.field == "rainfall"


def test_returns_none_once_max_rounds_reached():
    question = next_clarifying_question({}, rounds_asked=3, max_rounds=3)
    assert question is None


def test_returns_none_when_all_critical_fields_are_known():
    known = {
        "land_cover": "cropland",
        "rainfall_regime": "low",
        "soil_texture": "sandy_loam",
        "soil_organic_carbon": 0.3,
        "groundwater_depth_m": 18,
    }
    question = next_clarifying_question(known, rounds_asked=0, max_rounds=3)
    assert question is None
