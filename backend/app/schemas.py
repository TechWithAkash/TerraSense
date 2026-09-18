from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str | None = None  # free text input
    structured_input: dict[str, Any] | None = (
        None  # JSON input, per the assignment's "structured input" requirement
    )


class ExtractedSiteInput(BaseModel):
    # everything is optional: intake fills in whatever it can find, gap analysis handles the rest
    soil_organic_carbon: float | None = None
    soil_ph: float | None = None
    canopy_cover: float | None = None
    fragmentation_index: float | None = None
    species_richness: float | None = None
    pollinator_abundance: float | None = None
    soil_biota_activity: float | None = None
    soil_moisture: float | None = None
    nutrient_runoff: float | None = None

    land_cover: str | None = None  # cropland | grassland | forest
    crop: str | None = None
    rainfall_regime: str | None = None  # low | moderate | high
    annual_rainfall_mm: float | None = None
    aridity: str | None = None  # arid | semi_arid | sub_humid | humid
    soil_texture: str | None = None  # sandy | sandy_loam | loam | clay
    slope_percent: float | None = None
    groundwater_depth_m: float | None = None
    budget_inr_per_ha: float | None = None
    area_hectares: float | None = None


class ImpactedMetric(BaseModel):
    variable: str
    label: str
    baseline: float | None
    projected_low: float
    projected_mid: float
    projected_high: float
    unit: str
    horizon: str


class TradeOffOut(BaseModel):
    variable: str
    label: str
    direction: str
    magnitude: str
    cause_path: list[str]
    mitigation: str | None = None


class EvidenceOut(BaseModel):
    claim_id: str
    document: str
    publisher: str
    year: int
    study_design: str
    summary: str


class ConfidenceOut(BaseModel):
    score: float
    band: str
    limiting_factor: str
    components: dict[str, float]


class RecommendationOut(BaseModel):
    rank: int
    intervention_id: str
    label: str
    what_to_do: str
    why_it_works: str
    impacted_metrics: list[ImpactedMetric]
    time_horizon: str
    confidence: ConfidenceOut
    evidence: list[EvidenceOut]
    trade_offs: list[TradeOffOut]
    cost_inr_per_ha: list[float] | None = None
    labour_days_per_ha: list[float] | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    clarifying_question: str | None = None
    site_state: dict[str, Any]
    recommendations: list[RecommendationOut] = Field(default_factory=list)
    done: bool = False
