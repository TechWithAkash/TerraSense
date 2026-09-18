from dataclasses import dataclass, field

# pure python, zero LLM calls. deterministic given the same inputs.
# this is the part of the system that has to be defensible, so it stays simple and testable.

MAX_DEPTH = 3
ATTENUATION_PER_HOP = 0.85


@dataclass
class EdgeDTO:
    id: str
    source_variable: str
    target_variable: str
    sign: str
    per_unit_source: float
    delta_low: float
    delta_mid: float
    delta_high: float
    transform: str
    saturation_point: float | None
    context: dict
    confidence_tier: str
    evidence_claim_ids: list[str]
    notes: str | None = None


@dataclass
class DirectEffect:
    variable: str
    delta_low: float
    delta_mid: float
    delta_high: float
    evidence_claim_ids: list[str] = field(default_factory=list)
    transform: str = "linear"
    saturation_point: float | None = None


@dataclass
class VariableDelta:
    low: float
    mid: float
    high: float


@dataclass
class PathStep:
    from_variable: str
    to_variable: str
    edge_id: str | None
    delta_mid: float
    claim_ids: list[str]


@dataclass
class PropagationResult:
    deltas: dict[str, VariableDelta]
    paths: list[PathStep]
    edges_traversed: list[EdgeDTO]


def _context_matches(edge_context: dict, situation: dict) -> bool:
    # an edge with no context requirement always applies.
    # an edge with a requirement only fires when the situation satisfies every listed key.
    for key, allowed_values in edge_context.items():
        situation_value = situation.get(key)
        if situation_value is None or situation_value not in allowed_values:
            return False
    return True


def _saturation_scale(current_value: float | None, saturation_point: float | None) -> float:
    # the closer a site already is to the saturation point, the less headroom an intervention has.
    # this is what stops a healthy site from getting the same headline gain as a degraded one.
    if saturation_point is None or current_value is None:
        return 1.0
    headroom = (saturation_point - current_value) / saturation_point
    return max(0.05, min(1.0, headroom))


def _apply_transform(
    edge: EdgeDTO, source_units_moved: float, current_source_value: float | None
) -> float:
    if edge.transform == "saturating":
        return source_units_moved * _saturation_scale(current_source_value, edge.saturation_point)
    return source_units_moved  # linear and anything else falls back to a straight scale


def propagate(
    direct_effects: list[DirectEffect],
    edges: list[EdgeDTO],
    situation: dict,
    baseline_values: dict[str, float],
) -> PropagationResult:
    deltas: dict[str, VariableDelta] = {}
    paths: list[PathStep] = []
    edges_traversed: list[EdgeDTO] = []
    frontier: list[tuple[str, float, float, float, int]] = []

    for effect in direct_effects:
        # a saturating direct effect scales down by how much headroom the site's own current
        # value has left - this is what stops an already carbon-rich site from getting credited
        # the same absolute gain as a degraded one for the identical intervention.
        scale = 1.0
        if effect.transform == "saturating":
            scale = _saturation_scale(baseline_values.get(effect.variable), effect.saturation_point)

        delta_low = effect.delta_low * scale
        delta_mid = effect.delta_mid * scale
        delta_high = effect.delta_high * scale

        deltas[effect.variable] = VariableDelta(delta_low, delta_mid, delta_high)
        paths.append(
            PathStep("intervention", effect.variable, None, delta_mid, effect.evidence_claim_ids)
        )
        frontier.append((effect.variable, delta_low, delta_mid, delta_high, 0))

    outgoing_by_source: dict[str, list[EdgeDTO]] = {}
    for edge in edges:
        outgoing_by_source.setdefault(edge.source_variable, []).append(edge)

    while frontier:
        source_var, _low, mid, _high, depth = frontier.pop(0)
        if depth >= MAX_DEPTH:
            continue

        for edge in outgoing_by_source.get(source_var, []):
            if not _context_matches(edge.context, situation):
                continue

            current_value = baseline_values.get(source_var)
            attenuation = ATTENUATION_PER_HOP ** (depth + 1)
            sign = -1 if edge.sign == "negative" else 1

            units_low = mid / edge.per_unit_source if edge.per_unit_source else 0
            scale_low = _apply_transform(edge, units_low, current_value)
            target_low = sign * scale_low * edge.delta_low * attenuation

            units_mid = mid / edge.per_unit_source if edge.per_unit_source else 0
            scale_mid = _apply_transform(edge, units_mid, current_value)
            target_mid = sign * scale_mid * edge.delta_mid * attenuation

            units_high = mid / edge.per_unit_source if edge.per_unit_source else 0
            scale_high = _apply_transform(edge, units_high, current_value)
            target_high = sign * scale_high * edge.delta_high * attenuation

            existing = deltas.get(edge.target_variable, VariableDelta(0.0, 0.0, 0.0))
            deltas[edge.target_variable] = VariableDelta(
                existing.low + target_low,
                existing.mid + target_mid,
                existing.high + target_high,
            )
            paths.append(
                PathStep(
                    source_var, edge.target_variable, edge.id, target_mid, edge.evidence_claim_ids
                )
            )
            edges_traversed.append(edge)
            frontier.append((edge.target_variable, target_low, target_mid, target_high, depth + 1))

    return PropagationResult(deltas=deltas, paths=paths, edges_traversed=edges_traversed)


def detect_trade_offs(
    deltas: dict[str, VariableDelta],
    variables_by_id: dict[str, dict],
    paths: list[PathStep],
) -> list[dict]:
    trade_offs = []
    for variable_id, delta in deltas.items():
        variable = variables_by_id.get(variable_id)
        if variable is None:
            continue
        higher_is_worse = variable.get("higher_is_worse", False)
        moves_badly = (delta.mid > 0) if higher_is_worse else (delta.mid < 0)
        if not moves_badly:
            continue
        cause_path = [p.to_variable for p in paths if p.to_variable == variable_id]
        trade_offs.append(
            {
                "variable": variable_id,
                "label": variable.get("label", variable_id),
                "direction": "worsens",
                "delta_low": delta.low,
                "delta_mid": delta.mid,
                "delta_high": delta.high,
                "unit": variable.get("unit", ""),
                "cause_path": cause_path,
            }
        )
    return trade_offs
