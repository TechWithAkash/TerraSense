from app.reasoning.graph_engine import DirectEffect, EdgeDTO, detect_trade_offs, propagate


def make_edge(**overrides) -> EdgeDTO:
    defaults = {
        "id": "e1",
        "source_variable": "soil_organic_carbon",
        "target_variable": "soil_biota_activity",
        "sign": "positive",
        "per_unit_source": 1.0,
        "delta_low": 0.05,
        "delta_mid": 0.10,
        "delta_high": 0.15,
        "transform": "linear",
        "saturation_point": None,
        "context": {},
        "confidence_tier": "high",
        "evidence_claim_ids": ["clm_001"],
    }
    defaults.update(overrides)
    return EdgeDTO(**defaults)


def test_direct_effect_seeds_delta_with_no_edges():
    effect = DirectEffect("soil_organic_carbon", 0.1, 0.2, 0.4, ["clm_x"])
    result = propagate([effect], [], {}, {})
    assert result.deltas["soil_organic_carbon"].mid == 0.2
    assert result.paths[0].from_variable == "intervention"


def test_saturating_direct_effect_shrinks_on_an_already_healthy_site():
    effect = DirectEffect(
        "soil_organic_carbon", 0.10, 0.22, 0.40, [], transform="saturating", saturation_point=4.0
    )
    degraded = propagate([effect], [], {}, {"soil_organic_carbon": 0.3})
    healthy = propagate([effect], [], {}, {"soil_organic_carbon": 2.9})
    assert healthy.deltas["soil_organic_carbon"].mid < degraded.deltas["soil_organic_carbon"].mid


def test_propagation_reaches_second_hop_variable():
    effect = DirectEffect("soil_organic_carbon", 0.1, 0.2, 0.4, [])
    edge = make_edge()
    result = propagate([effect], [edge], {}, {})
    assert "soil_biota_activity" in result.deltas
    assert result.deltas["soil_biota_activity"].mid > 0


def test_negative_sign_moves_target_down():
    effect = DirectEffect("fragmentation_index", 0.1, 0.2, 0.3, [])
    edge = make_edge(
        id="e2",
        source_variable="fragmentation_index",
        target_variable="species_richness",
        sign="negative",
        per_unit_source=0.1,
    )
    result = propagate([effect], [edge], {}, {})
    assert result.deltas["species_richness"].mid < 0


def test_context_gated_edge_only_fires_when_situation_matches():
    effect = DirectEffect("canopy_cover", 10, 15, 25, [])
    edge = make_edge(
        id="trade_off",
        source_variable="canopy_cover",
        target_variable="groundwater_depth",
        sign="positive",
        per_unit_source=10,
        context={"species_group": ["high_transpiration"], "rainfall_regime": ["low"]},
    )

    result_without_match = propagate([effect], [edge], {"rainfall_regime": "high"}, {})
    assert "groundwater_depth" not in result_without_match.deltas

    result_with_match = propagate(
        [effect], [edge], {"species_group": "high_transpiration", "rainfall_regime": "low"}, {}
    )
    assert "groundwater_depth" in result_with_match.deltas


def test_saturating_transform_shrinks_effect_on_already_healthy_site():
    effect = DirectEffect("soil_organic_carbon", 0.1, 0.2, 0.4, [])
    edge = make_edge(transform="saturating", saturation_point=3.0)

    degraded_result = propagate([effect], [edge], {}, {"soil_organic_carbon": 0.3})
    healthy_result = propagate([effect], [edge], {}, {"soil_organic_carbon": 2.9})

    assert (
        healthy_result.deltas["soil_biota_activity"].mid
        < degraded_result.deltas["soil_biota_activity"].mid
    )


def test_propagation_stops_at_max_depth():
    effect = DirectEffect("a", 1, 1, 1, [])
    edges = [
        make_edge(id="a_b", source_variable="a", target_variable="b", per_unit_source=1),
        make_edge(id="b_c", source_variable="b", target_variable="c", per_unit_source=1),
        make_edge(id="c_d", source_variable="c", target_variable="d", per_unit_source=1),
        make_edge(id="d_e", source_variable="d", target_variable="e", per_unit_source=1),
    ]
    result = propagate([effect], edges, {}, {})
    assert "d" in result.deltas  # reached at depth 3
    assert "e" not in result.deltas  # would require depth 4, beyond MAX_DEPTH


def test_detect_trade_offs_flags_worsening_higher_is_worse_variable():
    from app.reasoning.graph_engine import PathStep, VariableDelta

    deltas = {"groundwater_depth": VariableDelta(0.1, 0.4, 1.2)}
    variables = {
        "groundwater_depth": {"label": "Groundwater Depth", "unit": "m", "higher_is_worse": True}
    }
    paths = [PathStep("canopy_cover", "groundwater_depth", "trade_off", 0.4, [])]

    trade_offs = detect_trade_offs(deltas, variables, paths)
    assert len(trade_offs) == 1
    assert trade_offs[0]["variable"] == "groundwater_depth"
