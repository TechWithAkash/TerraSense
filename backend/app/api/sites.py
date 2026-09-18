from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ConversationSession, Message, SiteState

router = APIRouter(prefix="/api/v1", tags=["sites"])


@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)) -> dict:
    session = db.get(ConversationSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at)
        .all()
    )
    return {
        "session_id": session.id,
        "site_id": session.site_id,
        "context": session.context,
        "clarification_rounds": session.clarification_rounds,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages
        ],
    }


@router.get("/sites/{site_id}/state")
def get_site_state(site_id: str, db: Session = Depends(get_db)) -> dict:
    states = db.query(SiteState).filter(SiteState.site_id == site_id).all()
    if not states:
        raise HTTPException(status_code=404, detail="No state recorded for this site yet")
    return {
        "site_id": site_id,
        "variables": {
            s.variable_id: {"value": s.value, "provenance": s.provenance, "source": s.source_name}
            for s in states
        },
    }
