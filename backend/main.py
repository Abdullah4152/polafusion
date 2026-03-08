# main.py — PolaFusion FastAPI Backend
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db.database import init_db
from routes.predict import router as predict_router
from routes.feedback import router as feedback_router
from routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────
    print("🚀 PolaFusion API starting...")
    init_db()
    # Models are NOT pre-loaded — they are loaded on first request.
    # This keeps startup fast on HuggingFace Spaces free tier.
    # For production with GPU, consider pre-loading fallback models here.
    print("✅ Ready.")
    yield
    # ── Shutdown ───────────────────────────────────────────────────
    print("⏹ Shutting down.")


app = FastAPI(
    title="PolaFusion API",
    description=(
        "Multilingual polarization detection across 22 languages. "
        "Subtask 1: Binary polarization. "
        "Subtask 2: Polarization type (5 labels). "
        "Subtask 3: Rhetorical manifestation (6 labels)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────
# Allow Chrome extension origin + local development.
# In production, replace "*" with your exact extension ID:
#   chrome-extension://<YOUR_EXTENSION_ID>
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# ── Routes ─────────────────────────────────────────────────────────
app.include_router(predict_router)
app.include_router(feedback_router)
app.include_router(health_router)


# ── Global error handler ───────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": str(exc)},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "validation_error", "detail": str(exc)},
    )
