from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from session.session_store import get_session

router = APIRouter(tags=["history"])


@router.get("/history")
async def get_history(x_session_id: str = Header(...)):
    session = get_session(x_session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    return {"history": session["history"]}


class FeedbackRequest(BaseModel):
    history_index: int
    rating: str  # "up" or "down"


@router.post("/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    x_session_id: str = Header(...),
):
    session = get_session(x_session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    if req.rating not in ("up", "down"):
        raise HTTPException(400, "Rating must be 'up' or 'down'")

    if req.history_index < 0 or req.history_index >= len(session["history"]):
        raise HTTPException(400, "Invalid history index")

    session["feedback"][str(req.history_index)] = req.rating

    # Calculate summary
    feedback = session["feedback"]
    total = len(feedback)
    positive = sum(1 for v in feedback.values() if v == "up")
    pct = round((positive / total) * 100) if total > 0 else 0

    return {
        "success": True,
        "summary": {"total": total, "positive": positive, "percent_positive": pct},
    }


@router.get("/feedback/summary")
async def feedback_summary(x_session_id: str = Header(...)):
    session = get_session(x_session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    feedback = session["feedback"]
    total = len(feedback)
    positive = sum(1 for v in feedback.values() if v == "up")
    pct = round((positive / total) * 100) if total > 0 else 0

    return {"total": total, "positive": positive, "percent_positive": pct}
