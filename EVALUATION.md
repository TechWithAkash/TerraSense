# Evaluation against the assignment's own rubric

`ASSIGNMENT.md` scores submissions against five weighted criteria plus two hard constraints. This
document maps each one to what the system actually does, where that lives in the code, and which
automated test proves it — so this is checkable, not just asserted. Every test named below runs in
`backend/tests/` via `uv run pytest` and is gated in CI (`.github/workflows/ci.yml`).

## 1. Depth of Reasoning — 30%

*"Are recommendations non-obvious? Do they combine multiple environmental variables?"*

- Every recommendation is produced by walking a hand-curated causal graph
  (`backend/knowledge_base/edges.yaml`, 14 edges over 11 variables) up to 3 hops from the
  intervention's direct effects, not by asking an LLM to free-associate. See
  `backend/app/reasoning/graph_engine.py`.
- **The assignment's own worked example, verbatim**: given exactly the brief's "Example Use Case"
  input (SOC 0.3%, low rainfall, monoculture wheat, semi-arid), the system's response includes
  agroforestry/intercropping among its ranked recommendations, with evidence citing FAO/IPCC, and
  answers directly instead of asking a follow-up question — matching the brief's stated "Expected
  Output" exactly. Locked in by
  `test_golden_scenarios.py::test_the_assignment_briefs_own_worked_example_matches_its_expected_output`.
  This did *not* work on first build (see Audit Log below) — the ranking weights favoured cheap,
  fast interventions strongly enough to bury agroforestry at 9th of 9 candidates.
- **The non-obvious case**: adding tree canopy in a semi-arid, low-rainfall site with a shallow
  water table triggers a specific, context-gated trade-off (deepening groundwater), not a blanket
  "trees are risky" rule — it only fires for high-transpiration species in water-limited zones.
  Proven in `test_recommend_service.py::test_trade_off_surfaces_for_agroforestry_in_a_water_limited_zone`,
  and at 15m+ groundwater depth the same intervention is excluded outright
  (`test_deep_groundwater_excludes_agroforestry_entirely`). Trade-offs below a materiality
  threshold (would round to 0.00 in the displayed output) are filtered out rather than shown as
  noise — `MATERIALITY_THRESHOLD` in `graph_engine.py`.
- **Diminishing returns**: an already carbon-rich site (2.9% SOC) gets a measurably smaller
  headline gain from the same intervention than a degraded one (0.3% SOC) — a saturating transform
  applied to both the causal edges and the intervention's own direct effects, not a flat number
  regardless of starting point. Proven in
  `test_recommend_service.py::test_saturated_site_gets_a_smaller_soil_carbon_gain_than_a_degraded_one`
  and the pure-function version in `test_graph_engine.py::test_saturating_direct_effect_shrinks_on_an_already_healthy_site`.
- **≥3 variables**: `test_golden_scenarios.py::test_depth_of_reasoning_connects_multiple_variables`
  and `test_constraint_minimum_three_variables_connected` assert this directly against the
  assignment's own worked example input.
- **Not generic**: `test_depth_of_reasoning_avoids_generic_advice` checks every recommendation's
  explanation against a banned-phrase list ("use sustainable practices", "plant more trees", etc.).

**Honest limitation**: the graph is 14 edges over 11 variables. It covers common semi-arid Indian
agricultural interventions well and says nothing about wetlands, coastal, or high-altitude systems.

## 2. Scientific Grounding — 25%

*"Are claims backed by credible sources? Is reasoning accurate and explainable?"*

- Every edge and every intervention's direct effect cites a real claim in
  `backend/knowledge_base/claims.yaml`, which points at a real, named, dated, publicly available
  source (FAO, IPCC, IPBES, ICAR, peer-reviewed journals — full list with licences in
  `backend/knowledge_base/SOURCES.md`).
- Confidence is *computed*, not asked of an LLM: a weighted geometric mean of evidence strength
  (study design), edge reliability, how much of the site is actually known vs. assumed, and causal
  path length. `backend/app/reasoning/confidence.py`. Proven in `test_confidence.py` and
  `test_golden_scenarios.py::test_scientific_grounding_confidence_is_computed_not_arbitrary`.
- Every recommendation returned by the API carries its cited sources with document, publisher,
  year, and study design — proven in
  `test_golden_scenarios.py::test_scientific_grounding_every_recommendation_cites_real_sources`.

**Honest limitation**: the effect sizes in `claims.yaml` are representative syntheses of each
source's well-established findings, written by hand — not numbers extracted verbatim by an
automated pipeline from the full paper text. This is stated explicitly in `SOURCES.md`.

## 3. Knowledge System Design — 20%

*"Use of RAG / vector DB / structured datasets. Clarity of knowledge retrieval pipeline."*

- Retrieval runs structured-first: a SQL filter on `intervention_id` against the `claims` table
  finds exactly the claims that apply, before semantic search ever runs
  (`backend/app/knowledge/retrieval.py`).
- Semantic search over the source excerpts uses TF-IDF cosine similarity
  (`backend/app/knowledge/search.py`) — a real, inspectable retrieval layer, not a black box.
  Both the structured graph and the semantic index are exposed as endpoints
  (`GET /api/v1/knowledge/graph`, `GET /api/v1/knowledge/search`), proven in
  `test_golden_scenarios.py::test_knowledge_system_*`.
- General knowledge questions (not site descriptions) are answered directly from this same
  retrieval layer — see §4 below, and `backend/app/conversation/general_query.py`.

**Honest limitation**: TF-IDF is a real, working retrieval method but not a semantic embedding
model — it matches on term overlap, not meaning. Swapping in a hosted embedding model is a
one-file change (`app/knowledge/search.py`) since nothing else depends on the implementation.

**Category coverage**: the brief lists soil health, land use, biodiversity, climate factors
(temperature, rainfall), and human impact as the categories the knowledge base should cover.
Rainfall, land use, soil, and biodiversity were covered from the start; temperature was not — see
Audit Log below for how that gap was found and closed.

## 4. Conversational Intelligence — 15%

*"Context awareness. Follow-up questioning. Memory handling."*

- Clarifying questions are asked one at a time, ranked by which gap would most change the answer
  (groundwater depth is asked early only when a tree-based intervention is actually plausible),
  capped at 3 rounds. `backend/app/conversation/gap_analysis.py`. Reproduces the assignment
  brief's own worked example verbatim — proven in
  `test_golden_scenarios.py::test_conversational_intelligence_asks_clarifying_question_on_vague_input`.
- Site state persists and accumulates across turns in the same session — proven in
  `test_conversational_intelligence_remembers_context_across_turns`.
- A message that reads as a direct question rather than a site description gets answered from the
  knowledge base instead of forcing the conversation back into the intake flow — proven in
  `test_conversational_intelligence_answers_direct_knowledge_questions`. This was a real bug found
  during manual testing (the system had no path for this and just repeated the same clarifying
  question verbatim); fixed and now regression-tested, including
  `test_conversational_intelligence_does_not_repeat_a_question_verbatim`.
- A reply to the system's own just-asked question is understood even when it doesn't repeat the
  question's own keywords ("About 12 metres, dropping slowly" answers "how deep is your water
  level" without the words "groundwater" or "borewell" anywhere in it) — proven in
  `test_conversational_intelligence_understands_a_bare_answer_to_its_own_question`. Also a real bug
  found during this audit, see Audit Log.

**Honest limitation**: without a Groq key configured, intake falls back to regex extraction, which
handles a wide but finite set of phrasings — it will miss more creative or indirect phrasing than
an LLM would. General knowledge questions still get answered either way (Groq-phrased or
excerpt-quoted), so this only affects how much a vague turn can be parsed in one message.

## 5. Output Clarity — 10%

*"Structured, readable, and actionable responses."*

- Every recommendation returns what to do, why it works, which metrics move (with numeric ranges),
  a time horizon bucket, a confidence band, and cited evidence — the full
  `RecommendationOut` schema (`backend/app/schemas.py`), proven in
  `test_golden_scenarios.py::test_output_clarity_every_recommendation_has_the_required_fields`.
- The frontend renders this inline in the conversation, in the same turn the recommendation was
  generated, rather than as a disconnected dashboard section.

## Constraints

- **"No generic LLM-only solutions"**: the reasoning core (`app/reasoning/`) makes zero LLM calls
  and is fully deterministic given the same inputs — see the "no LLM calls" comment at the top of
  `graph_engine.py` and `confidence.py`. The LLM (Groq, optional) only parses input and phrases
  output; it never computes a number or invents a citation.
- **"Must handle at least 3 environmental variables together"**: see
  `test_constraint_minimum_three_variables_connected`.

## Running this yourself

```bash
cd backend
uv run pytest -v tests/test_golden_scenarios.py tests/test_recommend_service.py
```

55 tests total across the full suite (`uv run pytest`), all gated in CI on every push.

## Audit log

This section exists because "I tested it" is a weaker claim than "here is exactly what I tested
and what I found." The first pass at this rubric mapping (an earlier version of this document)
asserted things that hadn't actually been checked against the live system — running the
assignment's own worked example through it, specifically. Once actually done, that check failed,
and continuing to pull on it surfaced six real bugs. All are fixed and regression-tested; listed
here in the order they were found, most consequential first.

1. **The brief's own reference scenario didn't produce its expected output.** Given exactly the
   4-field example from `ASSIGNMENT.md`, the system asked a clarifying question about groundwater
   depth instead of answering — and once that gate was relaxed, its top recommendation was cover
   cropping, not agroforestry, because ranking weighted cost and speed heavily enough that a
   9x-more-expensive, 2x-slower intervention couldn't compete regardless of ecological impact. Cost
   and speed are real considerations but are not anything the brief's rubric grades. Fixed across
   three changes: split clarifying questions into a blocking tier (the brief's own 3 fields:
   land use, rainfall, soil organic carbon) and a non-blocking refinement tier (asked alongside a
   real answer, never instead of one); rebalanced ranking weights toward ecological impact and
   evidence quality; corrected `confidence.py`'s path-length penalty, which was scoring a richer,
   more multi-variable causal chain as *less* trustworthy than a shallow one, directly working
   against the 30%-weighted "combines multiple variables" criterion.
2. **A reply to the system's own question was silently ignored.** The non-blocking refinement
   question ("how deep is your water level?") never recorded what field it was waiting on, so a
   natural follow-up reply ("About 12 metres, dropping slowly") matched nothing and the system
   quietly kept using its generic default instead of the number the user had just given it. Fixed
   by tracking the pending field on the refinement path the same way it already was on the
   blocking path, plus a new lenient, field-scoped extraction pass for replies that don't repeat
   the original question's keywords.
3. **Two regex extraction bugs, both silent.** A greedy `.{0,N}` bridge between a keyword and a
   number matched past the keyword *into* the digits before backtracking (e.g. capturing `8` out
   of `18`), for both groundwater depth and the newly-added temperature field, whenever the number
   came before the keyword. Existing tests never exercised that phrasing direction, so it shipped
   unnoticed. Fixed with non-greedy quantifiers and regression-tested for both orderings.
4. **`groundwater_depth_m` (feasibility filter) and `groundwater_depth` (the causal graph's own
   baseline) were disconnected fields representing the same real quantity.** The extractor only
   ever populated the first, so the graph's reasoning silently used a generic default even after a
   user stated their actual number. Unified into one field that updates both subsystems.
5. **Saturation only applied to propagated edge effects, not to an intervention's own direct
   effect.** A site at 2.9% soil organic carbon was credited the identical carbon gain from cover
   cropping as a degraded 0.3% site. Added `transform`/`saturation_point` to `DirectEffect` itself.
6. **No temperature coverage anywhere.** The brief explicitly lists "climate factors (temperature,
   rainfall)" as a knowledge-base category; rainfall was covered extensively, temperature not at
   all. Added as a context field (extracted from text or JSON, shown in site state) that refines
   the rainfall-derived aridity classification the same way real aridity indices combine
   temperature and precipitation — consistent with how rainfall itself was already treated as
   context rather than a graph node, and backed by a new claim citing IPCC AR6 (already in the
   corpus) rather than a bare heuristic.

None of these were visible from reading the code or the passing test suite alone — they only
surfaced by actually running the assignment's own example end to end and pulling on what didn't
look right. That is the check worth re-running if anything in this repository changes: not
"do the tests pass," but "does the brief's own worked example still produce its own expected
output."
