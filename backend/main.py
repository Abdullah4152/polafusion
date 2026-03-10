# main.py — PolaFusion FastAPI Backend
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Logging setup (before any imports that might fail) ─────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("polafusion")

# ── Verify HF_TOKEN early — fail fast with a clear message ─────────
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    log.error("❌ HF_TOKEN environment variable is not set.")
    log.error("   → Go to Space Settings → Variables and secrets → add HF_TOKEN")
    sys.exit(1)

log.info(f"✅ HF_TOKEN found (starts with: {HF_TOKEN[:8]}...)")

from db.database import init_storage
from routes.predict import router as predict_router
from routes.feedback import router as feedback_router
from routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 PolaFusion API starting...")
    try:
        init_storage()
        log.info("✅ Database initialized.")
    except Exception as e:
        log.error(f"❌ Database init failed: {e}")
        raise
    log.info("✅ Ready — waiting for requests.")
    yield
    log.info("⏹ Shutting down.")


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

app.include_router(predict_router)
app.include_router(feedback_router)
app.include_router(health_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled error on {request.url}: {exc}")
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
