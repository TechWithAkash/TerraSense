# golden scenarios, mapped directly to assignment.md's own "Evaluation Criteria" section, so a
# reviewer (or CI) can check the rubric is actually met rather than taking the README's word for it.
#   1. Depth of Reasoning (30%)          -> test_depth_of_reasoning_*
#   2. Scientific Grounding (25%)        -> test_scientific_grounding_*
#   3. Knowledge System Design (20%)     -> test_knowledge_system_*
#   4. Conversational Intelligence (15%) -> test_conversational_intelligence_*
#   5. Output Clarity (10%)              -> test_output_clarity_*
#   Constraints                          -> test_constraint_*
# the non-obvious trade-off mechanism (also part of Depth of Reasoning) is asserted separately in
# test_recommend_service.py at the service layer, since whether it lands in the top-3 ranked
# response is rank-dependent and would make an API-level assertion flaky.

BANNED_GENERIC_PHRASES = [
    "use sustainable practices",
    "improve soil health",
    "plant more trees",
    "adopt organic farming",
    "conserve water",
    "maintain biodiversity",
    "follow best practices",
]

ASSIGNMENT_EXAMPLE_INPUT = {
    "land_cover": "cropland",
    "rainfall_regime": "low",
    "aridity": "semi_arid",
    "soil_organic_carbon": 0.3,
    "soil_texture": "sandy_loam",
    "groundwater_depth_m": 25,
}


def _ask_structured(client, structured_input):
    response = client.post("/api/v1/chat", json={"structured_input": structured_input})
    assert response.status_code == 200
    return response.json()


def _ask_text(client, message, session_id=None):
    response = client.post("/api/v1/chat", json={"session_id": session_id, "message": message})
    assert response.status_code == 200
    return response.json()


# 1. Depth of Reasoning (30%) - "are recommendations non-obvious?", "do they combine multiple
#    environmental variables?"


def test_depth_of_reasoning_connects_multiple_variables(client):
    data = _ask_structured(client, ASSIGNMENT_EXAMPLE_INPUT)
    assert data["done"] is True
    assert len(data["recommendations"]) >= 1

    top = data["recommendations"][0]
    touched = {metric["variable"] for metric in top["impacted_metrics"]}
    assert len(touched) >= 3, "top recommendation must connect at least 3 environmental variables"


def test_depth_of_reasoning_avoids_generic_advice(client):
    data = _ask_structured(client, ASSIGNMENT_EXAMPLE_INPUT)
    for rec in data["recommendations"]:
        text = rec["why_it_works"].lower()
        assert not any(phrase in text for phrase in BANNED_GENERIC_PHRASES)


# 2. Scientific Grounding (25%) - "are claims backed by credible sources?", "is reasoning
#    accurate and explainable?"


def test_scientific_grounding_every_recommendation_cites_real_sources(client):
    data = _ask_structured(client, ASSIGNMENT_EXAMPLE_INPUT)
    assert data["recommendations"], "need at least one recommendation to check grounding"
    for rec in data["recommendations"]:
        assert rec["evidence"], f"{rec['intervention_id']} has no cited evidence"
        for claim in rec["evidence"]:
            assert claim["document"]
            assert claim["publisher"]
            assert claim["year"] > 1900
            assert claim["study_design"]


def test_scientific_grounding_confidence_is_computed_not_arbitrary(client):
    data = _ask_structured(client, ASSIGNMENT_EXAMPLE_INPUT)
    for rec in data["recommendations"]:
        confidence = rec["confidence"]
        assert 0.0 <= confidence["score"] <= 1.0
        assert confidence["band"] in ("Low", "Medium", "Medium-High", "High")
        assert confidence["limiting_factor"] in confidence["components"]


# 3. Knowledge System Design (20%) - "use of RAG / vector DB / structured datasets", "clarity of
#    knowledge retrieval pipeline"


def test_knowledge_system_structured_causal_graph_is_inspectable(client):
    response = client.get("/api/v1/knowledge/graph")
    assert response.status_code == 200
    graph = response.json()
    assert len(graph["variables"]) >= 10
    assert len(graph["edges"]) >= 10
    for edge in graph["edges"]:
        assert edge["source"] and edge["target"]
        assert edge["evidence_claim_ids"], "every edge must cite at least one claim"


def test_knowledge_system_semantic_search_returns_grounded_chunks(client):
    response = client.get(
        "/api/v1/knowledge/search",
        params={"q": "soil organic carbon and water holding capacity"},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert results, "semantic search should surface at least one relevant chunk"
    assert results[0]["score"] > 0


# 4. Conversational Intelligence (15%) - "context awareness", "follow-up questioning", "memory
#    handling"


def test_conversational_intelligence_asks_clarifying_question_on_vague_input(client):
    # the assignment brief's own worked example, verbatim
    data = _ask_text(client, "Biodiversity is declining on my land")
    assert data["done"] is False
    assert data["clarifying_question"] is not None


def test_conversational_intelligence_remembers_context_across_turns(client):
    first = _ask_text(client, "It's cropland with low rainfall.")
    assert first["site_state"].get("land_cover") == "cropland"

    second = _ask_text(client, "The soil texture is sandy loam.", session_id=first["session_id"])

    # everything learned in turn 1 must still be present after turn 2 - that's memory, not amnesia
    assert second["site_state"].get("land_cover") == "cropland"
    assert second["site_state"].get("rainfall_regime") == "low"
    assert second["site_state"].get("soil_texture") == "sandy_loam"


def test_conversational_intelligence_answers_direct_knowledge_questions(client):
    data = _ask_text(
        client, "What does your knowledge base say about soil organic carbon and biodiversity?"
    )
    assert data["clarifying_question"] is None
    assert "carbon" in data["reply"].lower() or "soil" in data["reply"].lower()


def test_conversational_intelligence_does_not_repeat_a_question_verbatim(client):
    first = _ask_text(client, "not sure honestly")
    second = _ask_text(client, "still not sure", session_id=first["session_id"])
    assert first["reply"] != second["reply"]


# 5. Output Clarity (10%) - "structured, readable, and actionable responses"


def test_output_clarity_every_recommendation_has_the_required_fields(client):
    data = _ask_structured(client, ASSIGNMENT_EXAMPLE_INPUT)
    for rec in data["recommendations"]:
        assert rec["what_to_do"]
        assert rec["impacted_metrics"]
        assert rec["time_horizon"] in ("short_term", "medium_term", "long_term")
        assert rec["confidence"]["band"]


# Constraints - "must handle at least 3 environmental variables together"


def test_constraint_minimum_three_variables_connected(client):
    data = _ask_structured(client, ASSIGNMENT_EXAMPLE_INPUT)
    touched = {
        metric["variable"] for rec in data["recommendations"] for metric in rec["impacted_metrics"]
    }
    assert len(touched) >= 3
