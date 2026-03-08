# routes/health.py
import torch
from fastapi import APIRouter
from config import LANGUAGE_MATRIX, ST3_SUPPRESSED_LANGS

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "modes_available": ["fallback", "ensemble"],
        "languages_supported": len(LANGUAGE_MATRIX),
        "st3_suppressed_langs": list(ST3_SUPPRESSED_LANGS),
    }
