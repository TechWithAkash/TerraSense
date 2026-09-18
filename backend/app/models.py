import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


# knowledge layer, loaded from knowledge_base/*.yaml at startup


class Variable(Base):
    __tablename__ = "variables"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    typical_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    typical_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    higher_is_worse: Mapped[bool] = mapped_column(default=False)
    derived: Mapped[bool] = mapped_column(default=False)


class CausalEdge(Base):
    __tablename__ = "causal_edges"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_variable: Mapped[str] = mapped_column(String, index=True)
    target_variable: Mapped[str] = mapped_column(String, index=True)
    sign: Mapped[str] = mapped_column(String)  # positive | negative
    per_unit_source: Mapped[float] = mapped_column(Float)
    delta_low: Mapped[float] = mapped_column(Float)
    delta_mid: Mapped[float] = mapped_column(Float)
    delta_high: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    transform: Mapped[str] = mapped_column(String, default="linear")
    saturation_point: Mapped[float | None] = mapped_column(Float, nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence_tier: Mapped[str] = mapped_column(String, default="medium")
    evidence_claim_ids: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    direct_effects: Mapped[list] = mapped_column(JSON)
    applicable_when: Mapped[dict] = mapped_column(JSON, default=dict)
    excluded_when: Mapped[dict] = mapped_column(JSON, default=dict)
    cost: Mapped[dict] = mapped_column(JSON, default=dict)
    labour_days_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    labour_days_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_to_first_effect_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reversibility: Mapped[str] = mapped_column(String, default="medium")
    trade_off_species_group: Mapped[str | None] = mapped_column(String, nullable=True)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document: Mapped[str] = mapped_column(String)
    publisher: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    study_design: Mapped[str] = mapped_column(String)
    target_variable: Mapped[str] = mapped_column(String, index=True)
    source_variable: Mapped[str | None] = mapped_column(String, nullable=True)
    intervention_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    n_studies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    context: Mapped[dict] = mapped_column(JSON, default=dict)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source_file: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)


# site and conversation layer


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    states: Mapped[list["SiteState"]] = relationship(
        back_populates="site", cascade="all, delete-orphan"
    )


class SiteState(Base):
    __tablename__ = "site_states"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    variable_id: Mapped[str] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float)
    # who told us this: the user typed it, we inferred a default, or (future) we fetched it from an API
    provenance: Mapped[str] = mapped_column(String)  # user | inferred | fetched
    source_name: Mapped[str | None] = mapped_column(String, nullable=True)

    site: Mapped[Site] = relationship(back_populates="states")


class ConversationSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    context: Mapped[dict] = mapped_column(
        JSON, default=dict
    )  # crop, budget, slope, groundwater, etc
    clarification_rounds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=_now)
    last_active: Mapped[datetime] = mapped_column(default=_now)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String)  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    session: Mapped[ConversationSession] = relationship(back_populates="messages")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    intervention_id: Mapped[str] = mapped_column(String)
    rank: Mapped[int] = mapped_column(Integer)
    predicted_deltas: Mapped[dict] = mapped_column(JSON)
    causal_paths: Mapped[list] = mapped_column(JSON)
    trade_offs: Mapped[list] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float)
    confidence_breakdown: Mapped[dict] = mapped_column(JSON)
    cited_claim_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(default=_now)
