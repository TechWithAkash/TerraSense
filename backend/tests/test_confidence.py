from app.reasoning.confidence import compute_confidence


def test_meta_analyses_and_full_provenance_yield_high_confidence():
    result = compute_confidence(
        claim_study_designs=["meta_analysis", "meta_analysis"],
        edge_confidence_tiers=["high", "high"],
        touched_variables={"soil_organic_carbon", "soil_biota_activity"},
        provenance_by_variable={"soil_organic_carbon": "user", "soil_biota_activity": "user"},
        mean_path_length=1.0,
    )
    assert result.score >= 0.65
    assert result.band in ("Medium-High", "High")


def test_expert_opinion_and_all_inferred_values_yield_lower_confidence():
    strong = compute_confidence(
        claim_study_designs=["meta_analysis"],
        edge_confidence_tiers=["high"],
        touched_variables={"soil_organic_carbon"},
        provenance_by_variable={"soil_organic_carbon": "user"},
        mean_path_length=1.0,
    )
    weak = compute_confidence(
        claim_study_designs=["expert_opinion"],
        edge_confidence_tiers=["low"],
        touched_variables={"soil_organic_carbon"},
        provenance_by_variable={"soil_organic_carbon": "inferred"},
        mean_path_length=3.0,
    )
    assert weak.score < strong.score


def test_limiting_factor_names_the_weakest_component():
    result = compute_confidence(
        claim_study_designs=["meta_analysis"],
        edge_confidence_tiers=["high"],
        touched_variables={"soil_organic_carbon"},
        provenance_by_variable={},  # nothing user-provided, input completeness should be the bottleneck
        mean_path_length=1.0,
    )
    assert result.limiting_factor == "input_completeness"


def test_longer_causal_paths_reduce_path_directness_and_score():
    direct = compute_confidence(
        ["meta_analysis"], ["high"], {"a"}, {"a": "user"}, mean_path_length=1.0
    )
    indirect = compute_confidence(
        ["meta_analysis"], ["high"], {"a"}, {"a": "user"}, mean_path_length=5.0
    )
    assert indirect.components["path_directness"] < direct.components["path_directness"]
