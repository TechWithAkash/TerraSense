from app.reasoning.ranking import is_feasible, rank_candidates, score_candidate


def test_feasible_when_no_constraints_are_violated():
    intervention = {
        "applicable_when": {"land_cover": ["cropland"]},
        "excluded_when": {},
        "cost": {},
    }
    feasible, reason = is_feasible(intervention, {"land_cover": "cropland"})
    assert feasible is True
    assert reason is None


def test_infeasible_when_land_cover_does_not_match():
    intervention = {"applicable_when": {"land_cover": ["forest"]}, "excluded_when": {}, "cost": {}}
    feasible, reason = is_feasible(intervention, {"land_cover": "cropland"})
    assert feasible is False
    assert "land cover" in reason


def test_infeasible_when_groundwater_already_too_deep():
    intervention = {
        "applicable_when": {},
        "excluded_when": {"groundwater_depth_m_min": 15},
        "cost": {},
    }
    feasible, _reason = is_feasible(intervention, {"groundwater_depth_m": 18})
    assert feasible is False


def test_infeasible_when_below_budget():
    intervention = {
        "applicable_when": {},
        "excluded_when": {},
        "cost": {"capex_inr_per_ha": [30000, 70000]},
    }
    feasible, _reason = is_feasible(intervention, {"budget_inr_per_ha": 10000})
    assert feasible is False


def test_cheaper_faster_intervention_scores_higher_all_else_equal():
    cheap_fast = score_candidate("a", {"species_richness": 0.1}, 0.8, [1000, 3000], 3)
    expensive_slow = score_candidate("b", {"species_richness": 0.1}, 0.8, [40000, 70000], 36)
    assert cheap_fast.total > expensive_slow.total


def test_rank_candidates_sorts_descending_by_total():
    low = score_candidate("low", {}, 0.3, [5000, 5000], 12)
    high = score_candidate("high", {"species_richness": 0.3}, 0.9, [2000, 2000], 3)
    ranked = rank_candidates([low, high])
    assert ranked[0].intervention_id == "high"
