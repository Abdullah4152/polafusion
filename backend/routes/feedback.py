# routes/feedback.py
import logging
from fastapi import APIRouter
from pydantic import BaseModel, field_validator
from db.database import save_feedback

router = APIRouter()
log = logging.getLogger("polafusion.feedback")


class FeedbackRequest(BaseModel):
    prediction_id: int | None = None    # optional — old cached results may not have it
    feedback: str                        # "correct" | "incorrect"

    @field_validator("feedback")
    @classmethod
    def feedback_valid(cls, v):
        if v not in ("correct", "incorrect"):
            raise ValueError("feedback must be 'correct' or 'incorrect'")
        return v


@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    if req.prediction_id is None:
        # Old cached result — log it but don't crash
        log.warning("Feedback received with no prediction_id — skipping DB write.")
        return {"status": "skipped", "reason": "no prediction_id"}

    save_feedback(
        prediction_id=req.prediction_id,
        feedback=req.feedback,
    )
    log.info(f"Feedback saved: id={req.prediction_id} → {req.feedback}")
    return {"status": "saved", "prediction_id": req.prediction_id, "feedback": req.feedback}
