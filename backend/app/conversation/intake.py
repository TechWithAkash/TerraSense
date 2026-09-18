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
nutrient_runoff (0-1),
land_cover (cropland|grassland|forest), crop (free text), rainfall_regime (low|moderate|high),
annual_rainfall_mm, aridity (arid|semi_arid|sub_humid|humid), mean_temperature_c,
soil_texture (sandy|sandy_loam|loam|clay), slope_percent, groundwater_depth_m, budget_inr_per_ha,
area_hectares.
Do not guess values that were not stated or clearly implied. Return {} if nothing is extractable."""

_RAINFALL_KEYWORDS = {"low": "low", "moderate": "moderate", "medium": "moderate", "high": "high"}
_ARIDITY_KEYWORDS = ["semi-arid", "semi arid", "arid", "sub-humid", "sub humid", "humid"]
_TEXTURE_KEYWORDS = ["sandy loam", "sandy", "loam", "clay"]


def _rule_based_extract(text: str) -> dict:
    lowered = text.lower()
    found: dict = {}

    # keyword-then-value ("soil organic carbon: 0.3%") and value-then-keyword ("0.3% soil organic
    # carbon") are both natural phrasings, so every numeric field below matches either order.
    soc_match = re.search(
        r"(?:soil organic carbon|organic carbon|soc)\D{0,10}(\d+\.?\d*)\s*%"
        r"|(\d+\.?\d*)\s*%\s*(?:soil organic carbon|organic carbon|soc)",
        lowered,
    )
    if soc_match:
        found["soil_organic_carbon"] = float(soc_match.group(1) or soc_match.group(2))

    ph_match = re.search(r"(?:soil )?ph\D{0,5}(\d+\.?\d*)", lowered)
    if ph_match:
        found["soil_ph"] = float(ph_match.group(1))

    canopy_match = re.search(r"canopy\D{0,10}(\d+\.?\d*)\s*%|(\d+\.?\d*)\s*%\s*canopy", lowered)
    if canopy_match:
        found["canopy_cover"] = float(canopy_match.group(1) or canopy_match.group(2))

    rainfall_mm_match = re.search(r"(\d+\.?\d*)\s*mm\b", lowered)
    if rainfall_mm_match:
        found["annual_rainfall_mm"] = float(rainfall_mm_match.group(1))

    rainfall_word_match = re.search(
        r"rainfall\D{0,10}(low|moderate|medium|high)|(low|moderate|medium|high)\s+rainfall",
        lowered,
    )
    if rainfall_word_match:
        word = rainfall_word_match.group(1) or rainfall_word_match.group(2)
        found["rainfall_regime"] = _RAINFALL_KEYWORDS[word]

    for keyword in _ARIDITY_KEYWORDS:
        if keyword in lowered:
            found["aridity"] = keyword.replace(" ", "_").replace("-", "_")
            break

    # non-greedy ".{0,N}?" between keyword and number: a greedy version happily eats into the
    # digits themselves before backtracking (e.g. capturing "8" out of "38"), since matching more
    # of the bridge and less of the number is still a valid match it will find first.
    temperature_match = re.search(
        r"(\d+\.?\d*)\s*(?:°c|deg(?:rees)?\.?\s*c(?:elsius)?|c\b)"
        r".{0,20}?(?:temperature|temp\b)"
        r"|(?:temperature|temp\b).{0,20}?(\d+\.?\d*)\s*(?:°c|deg(?:rees)?\.?\s*c(?:elsius)?|c\b)",
        lowered,
    )
    if temperature_match:
        value = temperature_match.group(1) or temperature_match.group(2)
        found["mean_temperature_c"] = float(value)

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
        r"(\d+\.?\d*)\s*(?:m|metres|meters)\b.{0,25}?(?:deep|below|borewell|water\s*level|groundwater)"
        r"|(?:borewell|water\s*level|groundwater).{0,25}?(\d+\.?\d*)\s*(?:m|metres|meters)\b",
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


def extract_pending_field(text: str, pending_field: str) -> dict:
    # when we know exactly which question was just asked, a reply doesn't need to repeat the
    # keyword to be understood ("About 12 metres, dropping slowly" answers "how deep is your
    # water level" perfectly well without the word "groundwater" anywhere in it). this runs only
    # as a fallback for the one field we're actively waiting on, so it can be looser than the
    # general-purpose scan above without risking misreading an unrelated number elsewhere.
    lowered = text.lower()

    if pending_field == "groundwater_depth_m":
        match = re.search(r"(\d+\.?\d*)\s*(?:m\b|metres?|meters?)", lowered)
        return {"groundwater_depth_m": float(match.group(1))} if match else {}

    if pending_field == "rainfall":
        match = re.search(r"\b(low|moderate|medium|high)\b", lowered)
        return {"rainfall_regime": _RAINFALL_KEYWORDS[match.group(1)]} if match else {}

    if pending_field == "soil_organic_carbon":
        match = re.search(r"(\d+\.?\d*)\s*%", lowered)
        return {"soil_organic_carbon": float(match.group(1))} if match else {}

    if pending_field == "soil_texture":
        for keyword in _TEXTURE_KEYWORDS:
            if keyword in lowered:
                return {"soil_texture": keyword.replace(" ", "_")}
        return {}

    return {}


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
