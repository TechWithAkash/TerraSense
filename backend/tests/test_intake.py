from app.conversation.intake import extract_from_structured, extract_from_text


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
