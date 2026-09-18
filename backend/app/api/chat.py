from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.conversation.gap_analysis import next_clarifying_question, next_refinement_suggestion
from app.conversation.general_query import answer_general_question, is_general_question
from app.conversation.intake import (
    extract_from_structured,
    extract_from_text,
    extract_pending_field,
)
from app.conversation.narrate import build_chat_reply
from app.conversation.session import (
    apply_extracted_input,
    get_or_create_session,
    known_fields_snapshot,
    record_message,
    seed_inferred_defaults,
)
from app.database import get_db
from app.models import SiteState
from app.schemas import ChatRequest, ChatResponse, ExtractedSiteInput
from app.services.recommend import generate_recommendations

router = APIRouter(prefix="/api/v1", tags=["chat"])
settings = get_settings()


def _public_context(context: dict) -> dict:
    # internal bookkeeping keys (prefixed with "_") never get shown to the user
    return {key: value for key, value in context.items() if not key.startswith("_")}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    if not request.message and not request.structured_input:
        raise HTTPException(
            status_code=400, detail="Provide either 'message' or 'structured_input'."
        )

    session = get_or_create_session(db, request.session_id)
    pending_field = session.context.get("_last_asked_field")

    if request.message:
        record_message(db, session, "user", request.message)
        extracted = extract_from_text(request.message)
    else:
        record_message(db, session, "user", str(request.structured_input))
        extracted = extract_from_structured(request.structured_input or {})

    extracted_fields = extracted.model_dump(exclude_none=True)

    # a reply to the question we JUST asked doesn't have to repeat its keyword to be understood
    # ("About 12 metres, dropping slowly" answers "how deep is your water level" perfectly well)
    if request.message and pending_field:
        rainfall_known = pending_field == "rainfall" and (
            extracted_fields.get("rainfall_regime") or extracted_fields.get("annual_rainfall_mm")
        )
        if not extracted_fields.get(pending_field) and not rainfall_known:
            lenient_fields = extract_pending_field(request.message, pending_field)
            if lenient_fields:
                extracted_fields = {**extracted_fields, **lenient_fields}
                extracted = ExtractedSiteInput(**extracted_fields)

    apply_extracted_input(db, session, extracted)

    # the message described nothing about a site, but reads as a direct question - answer it
    # from the knowledge base instead of blindly re-asking for land details it didn't provide
    if not extracted_fields and request.message and is_general_question(request.message):
        reply = answer_general_question(request.message)
        record_message(db, session, "assistant", reply)
        return ChatResponse(
            session_id=session.id,
            reply=reply,
            clarifying_question=None,
            site_state=_public_context(known_fields_snapshot(db, session)),
            recommendations=[],
            done=False,
        )

    known = known_fields_snapshot(db, session)
    question = next_clarifying_question(
        known, session.clarification_rounds, settings.max_clarifying_questions
    )

    if question is not None:
        previously_asked = session.context.get("_last_asked_field")
        reply = f"{question.question} ({question.why})"
        if question.field == previously_asked:
            reply = f"I still need this to help you: {reply}"

        session.clarification_rounds += 1
        session.context = {**session.context, "_last_asked_field": question.field}
        db.add(session)
        db.commit()

        record_message(db, session, "assistant", reply)
        return ChatResponse(
            session_id=session.id,
            reply=reply,
            clarifying_question=question.question,
            site_state=_public_context(known),
            recommendations=[],
            done=False,
        )

    seed_inferred_defaults(db, session.site_id)
    recommendations = generate_recommendations(db, session)
    top_label = recommendations[0].label if recommendations else None
    reply = build_chat_reply(len(recommendations), None, top_label)

    # a real answer always ships now; a refinement gets suggested alongside it, never instead of it.
    # still track it as the pending field, so a bare reply next turn ("about 12 metres") is
    # understood as answering it, the same as it would be for a blocking question.
    refinement = next_refinement_suggestion(known)
    if refinement is not None:
        reply += f"\n\n{refinement.question} ({refinement.why})"
        session.context = {**session.context, "_last_asked_field": refinement.field}
        db.add(session)
        db.commit()

    record_message(db, session, "assistant", reply)

    site_states = db.query(SiteState).filter(SiteState.site_id == session.site_id).all()
    site_state_view = {
        **_public_context(session.context),
        **{s.variable_id: {"value": s.value, "provenance": s.provenance} for s in site_states},
    }

    return ChatResponse(
        session_id=session.id,
        reply=reply,
        clarifying_question=None,
        site_state=site_state_view,
        recommendations=recommendations,
        done=True,
    )
