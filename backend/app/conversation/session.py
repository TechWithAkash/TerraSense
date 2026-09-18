from datetime import UTC, datetime

from sqlalchemy.orm import Session as DbSession

from app.knowledge.defaults import DEFAULT_BASELINES
from app.models import ConversationSession, Message, Site, SiteState
from app.schemas import ExtractedSiteInput

NUMERIC_VARIABLE_FIELDS = {
    "soil_organic_carbon",
    "soil_ph",
    "canopy_cover",
    "fragmentation_index",
    "species_richness",
    "pollinator_abundance",
    "soil_biota_activity",
    "soil_moisture",
    "nutrient_runoff",
    "groundwater_depth",
}

CONTEXT_FIELDS = {
    "land_cover",
    "crop",
    "rainfall_regime",
    "annual_rainfall_mm",
    "aridity",
    "soil_texture",
    "slope_percent",
    "groundwater_depth_m",
    "budget_inr_per_ha",
    "area_hectares",
}


def get_or_create_session(db: DbSession, session_id: str | None) -> ConversationSession:
    if session_id:
        existing = db.get(ConversationSession, session_id)
        if existing:
            return existing

    site = Site()
    db.add(site)
    db.flush()

    session = ConversationSession(site_id=site.id, context={})
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def record_message(db: DbSession, session: ConversationSession, role: str, content: str) -> None:
    db.add(Message(session_id=session.id, role=role, content=content))
    session.last_active = datetime.now(UTC)
    db.commit()


def apply_extracted_input(
    db: DbSession, session: ConversationSession, extracted: ExtractedSiteInput
) -> None:
    data = extracted.model_dump(exclude_none=True)

    context_updates = {key: value for key, value in data.items() if key in CONTEXT_FIELDS}
    if context_updates:
        session.context = {**session.context, **context_updates}
        db.add(session)

    for variable_id, value in data.items():
        if variable_id not in NUMERIC_VARIABLE_FIELDS:
            continue
        existing = (
            db.query(SiteState)
            .filter(SiteState.site_id == session.site_id, SiteState.variable_id == variable_id)
            .first()
        )
        if existing:
            existing.value = value
            existing.provenance = "user"
            existing.source_name = "user provided"
        else:
            db.add(
                SiteState(
                    site_id=session.site_id,
                    variable_id=variable_id,
                    value=value,
                    provenance="user",
                    source_name="user provided",
                )
            )

    db.commit()


def known_fields_snapshot(db: DbSession, session: ConversationSession) -> dict:
    # gap analysis needs to see everything we know, whether it landed in session.context
    # (crop, rainfall, texture, ...) or in the site_states table (soil_organic_carbon, ...)
    states = db.query(SiteState).filter(SiteState.site_id == session.site_id).all()
    numeric_known = {state.variable_id: state.value for state in states}
    return {**session.context, **numeric_known}


def get_baseline_values(db: DbSession, site_id: str) -> tuple[dict[str, float], dict[str, str]]:
    # returns (value_by_variable, provenance_by_variable), filling gaps with inferred defaults
    states = db.query(SiteState).filter(SiteState.site_id == site_id).all()
    values = {state.variable_id: state.value for state in states}
    provenance = {state.variable_id: state.provenance for state in states}

    for variable_id, default_value in DEFAULT_BASELINES.items():
        if variable_id not in values:
            values[variable_id] = default_value
            provenance[variable_id] = "inferred"

    return values, provenance


def seed_inferred_defaults(db: DbSession, site_id: str) -> None:
    # persists the inferred defaults as real rows so the site state panel can show them with provenance
    existing_ids = {
        s.variable_id for s in db.query(SiteState).filter(SiteState.site_id == site_id).all()
    }
    for variable_id, default_value in DEFAULT_BASELINES.items():
        if variable_id in existing_ids:
            continue
        db.add(
            SiteState(
                site_id=site_id,
                variable_id=variable_id,
                value=default_value,
                provenance="inferred",
                source_name="degraded-land default assumption",
            )
        )
    db.commit()
