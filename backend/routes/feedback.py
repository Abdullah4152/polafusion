# routes/feedback.py
import json
from fastapi import APIRouter
from pydantic import BaseModel
from db.database import save_feedback

router = APIRouter()


class FeedbackRequest(BaseModel):
    text: str
    lang_code: str
    mode_used: str
    st1_predicted: int
    st1_correct: int | None = None
    correction: dict | None = None
    raw_response: dict | None = None


@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    row_id = save_feedback(
        text=req.text,
        lang_code=req.lang_code,
        mode_used=req.mode_used,
        st1_predicted=req.st1_predicted,
        st1_correct=req.st1_correct,
        correction=json.dumps(req.correction) if req.correction else None,
        raw_response=json.dumps(req.raw_response) if req.raw_response else None,
    )
    return {"status": "saved", "id": row_id}
