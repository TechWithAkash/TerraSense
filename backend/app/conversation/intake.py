import json
import re

from app.llm.client import complete
from app.schemas import ExtractedSiteInput

# turns messy human input into the structured fields the reasoning engine needs.
# tries the LLM first when a key is configured, falls back to regex extraction otherwise,
# so the system keeps working for a reviewer who never adds an API key.

_SYSTEM_PROMPT = """You extract structured land and site data from a farmer or land manager's message.
Return ONLY a JSON object with any of these keys you can confidently fill in, omit anything unclear:
soil_organic_carbon (percent, e.g. 0.3), soil_ph, canopy_cover (percent), fragmentation_index (0-1),
species_richness (0-1), pollinator_abundance (0-1), soil_biota_activity (0-1), soil_moisture (0-1),
nutrient_runoff (0-1), groundwater_depth (0-1),
land_cover (cropland|grassland|forest), crop (free text), rainfall_regime (low|moderate|high),
annual_rainfall_mm, aridity (arid|semi_arid|sub_humid|humid), soil_texture (sandy|sandy_loam|loam|clay),
slope_percent, groundwater_depth_m, budget_inr_per_ha, area_hectares.
Do not guess values that were not stated or clearly implied. Return {} if nothing is extractable."""

_RAINFALL_KEYWORDS = {"low": "low", "moderate": "moderate", "medium": "moderate", "high": "high"}
_ARIDITY_KEYWORDS = ["semi-arid", "semi arid", "arid", "sub-humid", "sub humid", "humid"]
_TEXTURE_KEYWORDS = ["sandy loam", "sandy", "loam", "clay"]


def _rule_based_extract(text: str) -> dict:
    lowered = text.lower()
    found: dict = {}

    soc_match = re.search(
        r"(?:soil organic carbon|organic carbon|soc)\D{0,10}(\d+\.?\d*)\s*%", lowered
    )
    if soc_match:
        found["soil_organic_carbon"] = float(soc_match.group(1))

    ph_match = re.search(r"(?:soil )?ph\D{0,5}(\d+\.?\d*)", lowered)
    if ph_match:
        found["soil_ph"] = float(ph_match.group(1))

    canopy_match = re.search(r"canopy\D{0,10}(\d+\.?\d*)\s*%", lowered)
    if canopy_match:
        found["canopy_cover"] = float(canopy_match.group(1))

    rainfall_mm_match = re.search(r"(\d+\.?\d*)\s*mm\b", lowered)
    if rainfall_mm_match:
        found["annual_rainfall_mm"] = float(rainfall_mm_match.group(1))

    rainfall_word_match = re.search(r"rainfall\D{0,10}(low|moderate|medium|high)", lowered)
    if rainfall_word_match:
        found["rainfall_regime"] = _RAINFALL_KEYWORDS[rainfall_word_match.group(1)]

    for keyword in _ARIDITY_KEYWORDS:
        if keyword in lowered:
            found["aridity"] = keyword.replace(" ", "_").replace("-", "_")
            break

    for keyword in _TEXTURE_KEYWORDS:
        if keyword in lowered:
            found["soil_texture"] = keyword.replace(" ", "_")
            break

    if "monoculture" in lowered or any(
        word in lowered for word in ["cropland", "farmland", "field", "crop"]
    ):
        found["land_cover"] = "cropland"
    elif "grassland" in lowered or "pasture" in lowered:
        found["land_cover"] = "grassland"
    elif "forest" in lowered:
        found["land_cover"] = "forest"

    crop_match = re.search(
        r"(?:growing|crop(?:ping)?(?: is)?:?)\s+([a-z][a-z\s]{2,50}?)(?=[.,;]|$)", lowered
    )
    if crop_match:
        found["crop"] = crop_match.group(1).strip()

    slope_match = re.search(r"(\d+\.?\d*)\s*%?\s*slope", lowered)
    if slope_match:
        found["slope_percent"] = float(slope_match.group(1))

    groundwater_match = re.search(
        r"(\d+\.?\d*)\s*(?:m|metres|meters)\b.{0,25}(?:deep|below|borewell|water\s*level|groundwater)"
        r"|(?:borewell|water\s*level|groundwater).{0,25}(\d+\.?\d*)\s*(?:m|metres|meters)\b",
        lowered,
    )
    if groundwater_match:
        value = groundwater_match.group(1) or groundwater_match.group(2)
        found["groundwater_depth_m"] = float(value)

    budget_match = re.search(r"(\d[\d,]*)\s*(?:inr|rupees|rs\.?|₹)", lowered)
    if budget_match:
        found["budget_inr_per_ha"] = float(budget_match.group(1).replace(",", ""))

    area_match = re.search(r"(\d+\.?\d*)\s*hectares?", lowered)
    if area_match:
        found["area_hectares"] = float(area_match.group(1))

    return found


def extract_from_text(text: str) -> ExtractedSiteInput:
    llm_response = complete(_SYSTEM_PROMPT, text, json_mode=True)
    if llm_response:
        try:
            parsed = json.loads(llm_response)
            return ExtractedSiteInput(**parsed)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass  # fall through to the rule-based path below

    return ExtractedSiteInput(**_rule_based_extract(text))


def extract_from_structured(payload: dict) -> ExtractedSiteInput:
    known_fields = set(ExtractedSiteInput.model_fields.keys())
    filtered = {key: value for key, value in payload.items() if key in known_fields}
    return ExtractedSiteInput(**filtered)
