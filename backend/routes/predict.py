# routes/predict.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from config import MIN_TEXT_CHARS, LANGUAGE_MATRIX
from ml.lang_detect import detect
from ml.fallback import run_fallback
from ml.ensemble import run_ensemble

router = APIRouter()


class PredictRequest(BaseModel):
    text: str
    mode: str = "fallback"

    @field_validator("text")
    @classmethod
    def text_min_length(cls, v):
        if len(v.strip()) < MIN_TEXT_CHARS:
            raise ValueError(
                f"Text must be at least {MIN_TEXT_CHARS} characters. "
                f"Got {len(v.strip())}."
            )
        return v.strip()

    @field_validator("mode")
    @classmethod
    def mode_valid(cls, v):
        if v not in ("fallback", "ensemble"):
            raise ValueError("mode must be 'fallback' or 'ensemble'")
        return v


@router.post("/predict")
async def predict(req: PredictRequest):
    # 1. Detect language
    lang_code, lang_name, lang_flag, tier = detect(req.text)

    # 2. Route to correct pipeline
    if req.mode == "ensemble":
        result = run_ensemble(req.text, lang_code)
    else:
        result = run_fallback(req.text, lang_code)

    # 3. Attach text preview (never store full text in response)
    result["text_preview"] = req.text[:80] + ("…" if len(req.text) > 80 else "")
    return result
