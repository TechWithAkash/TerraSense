from app.conversation.general_query import is_general_question


def test_recognises_question_mark_as_a_general_question():
    assert is_general_question("What does the knowledge base say about soil carbon?") is True


def test_recognises_question_starter_without_a_question_mark():
    assert is_general_question("Explain the link between canopy cover and pollinators") is True


def test_site_description_is_not_treated_as_a_general_question():
    assert is_general_question("Soil organic carbon: 0.3%, Rainfall: low") is False


def test_empty_text_is_not_a_general_question():
    assert is_general_question("   ") is False
