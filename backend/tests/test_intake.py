from app.conversation.intake import (
    extract_from_structured,
    extract_from_text,
    extract_pending_field,
)


def test_extracts_the_assignment_brief_example_use_case():
    text = "Soil organic carbon: 0.3%, Rainfall: low, Crop: monoculture wheat, Region: semi-arid"
    result = extract_from_text(text)
    assert result.soil_organic_carbon == 0.3
    assert result.rainfall_regime == "low"
    assert result.aridity == "semi_arid"


def test_crop_name_is_not_truncated():
    result = extract_from_text(
        "It is cropland, growing wheat as a monoculture, and yields are dropping."
    )
    assert result.crop == "wheat as a monoculture"


def test_groundwater_depth_extracted_from_natural_phrasing():
    result = extract_from_text("About 18 metres deep, it has dropped 4 metres in 6 years")
    assert result.groundwater_depth_m == 18.0


def test_groundwater_depth_extracted_keyword_first():
    # regression: a greedy bridge regex here previously captured "8" out of "18"
    result = extract_from_text("The groundwater level here is about 18 metres deep")
    assert result.groundwater_depth_m == 18.0


def test_structured_input_only_keeps_known_fields():
    result = extract_from_structured({"soil_organic_carbon": 0.4, "not_a_real_field": "ignored"})
    assert result.soil_organic_carbon == 0.4
    assert not hasattr(result, "not_a_real_field")


def test_value_before_keyword_phrasing_is_also_extracted():
    result = extract_from_text(
        "What should I do for my cropland with low rainfall and 0.3% soil organic carbon?"
    )
    assert result.land_cover == "cropland"
    assert result.rainfall_regime == "low"
    assert result.soil_organic_carbon == 0.3


def test_pending_field_extraction_understands_a_bare_reply_to_the_question_just_asked():
    # this is what a real user says back after being asked "how deep is your water level" -
    # no reason to repeat "groundwater" or "borewell" when answering a question directly
    result = extract_pending_field("About 12 metres, dropping slowly", "groundwater_depth_m")
    assert result == {"groundwater_depth_m": 12.0}


def test_pending_field_extraction_is_scoped_to_the_field_actually_asked():
    assert extract_pending_field("low", "rainfall") == {"rainfall_regime": "low"}
    assert extract_pending_field("nothing relevant here", "groundwater_depth_m") == {}


def test_temperature_extracted_either_phrasing_order():
    assert extract_from_text("Temperature: 38°C, semi-arid region").mean_temperature_c == 38.0
    assert (
        extract_from_text(
            "It gets up to 40 degrees C in summer, temperature-wise"
        ).mean_temperature_c
        == 40.0
    )
