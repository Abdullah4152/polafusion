# db/database.py
import os, json, sqlite3, hashlib, logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("polafusion.db")

# ─── SQLite ───────────────────────────────────────────────────────────────────
DB_PATH = Path("feedback.db")

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at          TEXT NOT NULL,
                session_id          TEXT,
                user_text           TEXT NOT NULL,
                text_hash           TEXT NOT NULL,
                text_length         INTEGER NOT NULL,
                detected_language   TEXT NOT NULL,
                language_name       TEXT NOT NULL,
                confidence_tier     TEXT NOT NULL,
                mode_used           TEXT NOT NULL,
                processing_ms       INTEGER,
                st1_label           INTEGER,
                st1_probability     REAL,
                st2_labels          TEXT,
                st2_gated_out       INTEGER DEFAULT 0,
                st3_labels          TEXT,
                st3_gated_out       INTEGER DEFAULT 0,
                st3_available       INTEGER DEFAULT 1,
                st3_suppressed      INTEGER DEFAULT 0,
                user_feedback       TEXT DEFAULT NULL,
                feedback_at         TEXT DEFAULT NULL
            )
        """)
        conn.commit()

def _save_sqlite(row: dict) -> int:
    with _connect() as conn:
        cursor = conn.execute("""
            INSERT INTO predictions (
                created_at, session_id, user_text, text_hash, text_length,
                detected_language, language_name, confidence_tier,
                mode_used, processing_ms, st1_label, st1_probability,
                st2_labels, st2_gated_out, st3_labels, st3_gated_out,
                st3_available, st3_suppressed, user_feedback, feedback_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row["created_at"], row["session_id"],
                row["user_text"], row["text_hash"], row["text_length"],
                row["detected_language"], row["language_name"], row["confidence_tier"],
                row["mode_used"], row["processing_ms"],
                row["st1_label"], row["st1_probability"],
                row["st2_labels"], row["st2_gated_out"],
                row["st3_labels"], row["st3_gated_out"],
                row["st3_available"], row["st3_suppressed"],
                None, None,
            ),
        )
        conn.commit()
        return cursor.lastrowid

def _update_feedback_sqlite(prediction_id: int, feedback: str):
    with _connect() as conn:
        conn.execute(
            "UPDATE predictions SET user_feedback=?, feedback_at=? WHERE id=?",
            (feedback, datetime.now(timezone.utc).isoformat(), prediction_id),
        )
        conn.commit()

# ─── Google Sheets ────────────────────────────────────────────────────────────
_sheets_ready = False
_worksheet = None

SHEET_HEADERS = [
    "id", "created_at", "session_id",
    "user_text", "text_hash", "text_length",
    "detected_language", "language_name", "confidence_tier",
    "mode_used", "processing_ms",
    "st1_label", "st1_probability",
    "st2_labels", "st2_gated_out",
    "st3_labels", "st3_gated_out", "st3_available", "st3_suppressed",
    "user_feedback", "feedback_at",
]

def _safe_int(v):
    try: return int(v) if v is not None else 0
    except: return 0

def _safe_str(v):
    return str(v) if v is not None else ""

def _init_sheets():
    global _sheets_ready, _worksheet
    sheet_id   = os.environ.get("GOOGLE_SHEET_ID")
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not sheet_id or not creds_json:
        log.warning("⚠️  Google Sheets not configured — SQLite only.")
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        client = gspread.authorize(creds)
        sheet  = client.open_by_key(sheet_id)
        try:
            _worksheet = sheet.worksheet("predictions")
            log.info(f"✅ Found existing 'predictions' sheet with {_worksheet.row_count} rows")
        except gspread.exceptions.WorksheetNotFound:
            _worksheet = sheet.add_worksheet(title="predictions", rows=50000, cols=len(SHEET_HEADERS))
            _worksheet.append_row(SHEET_HEADERS)
            log.info("✅ Created new 'predictions' sheet with headers.")
        _sheets_ready = True
        log.info("✅ Google Sheets connected — all predictions will be persisted.")
    except ImportError:
        log.warning("⚠️  gspread not installed")
    except Exception as e:
        log.error(f"❌ Google Sheets init failed: {type(e).__name__}: {e}")

def _save_sheets(row: dict, sqlite_id: int):
    if not _sheets_ready or _worksheet is None:
        return
    try:
        sheet_row = [
            sqlite_id,
            _safe_str(row.get("created_at")),
            _safe_str(row.get("session_id")),
            _safe_str(row.get("user_text")),
            _safe_str(row.get("text_hash")),
            _safe_int(row.get("text_length")),
            _safe_str(row.get("detected_language")),
            _safe_str(row.get("language_name")),
            _safe_str(row.get("confidence_tier")),
            _safe_str(row.get("mode_used")),
            _safe_int(row.get("processing_ms")),
            _safe_int(row.get("st1_label")),
            float(row["st1_probability"]) if row.get("st1_probability") is not None else 0.0,
            _safe_str(row.get("st2_labels")),
            _safe_int(row.get("st2_gated_out")),
            _safe_str(row.get("st3_labels")),
            _safe_int(row.get("st3_gated_out")),
            _safe_int(row.get("st3_available", 1)),
            _safe_int(row.get("st3_suppressed")),
            "",
            "",
        ]
        log.info(f"📊 Writing to Sheets: sqlite_id={sqlite_id} lang={row.get('detected_language')} st1={row.get('st1_label')}")
        _worksheet.append_row(sheet_row, value_input_option="RAW")
        log.info(f"✅ Sheets row written: id={sqlite_id}")
    except Exception as e:
        log.error(f"❌ Sheets write FAILED id={sqlite_id}: {type(e).__name__}: {e}")

def _update_feedback_sheets(prediction_id: int, feedback: str):
    if not _sheets_ready or _worksheet is None:
        return
    try:
        col_a = _worksheet.col_values(1)
        for idx, val in enumerate(col_a[1:], start=2):
            if str(val) == str(prediction_id):
                _worksheet.update_cell(idx, 20, feedback)
                _worksheet.update_cell(idx, 21, datetime.now(timezone.utc).isoformat())
                log.info(f"✅ Sheets feedback updated: id={prediction_id} → {feedback}")
                return
        log.warning(f"⚠️  prediction_id={prediction_id} not found in Sheets for feedback update")
    except Exception as e:
        log.error(f"❌ Sheets feedback update failed: {type(e).__name__}: {e}")

# ─── Public API ───────────────────────────────────────────────────────────────
def init_storage():
    init_db()
    _init_sheets()
    log.info("✅ Storage ready.")

def save_prediction(api_response: dict, user_text: str, session_id: str | None = None) -> int:
    st1 = api_response.get("subtask1") or {}
    st2 = api_response.get("subtask2") or {}
    st3 = api_response.get("subtask3") or {}
    row = {
        "created_at":        datetime.now(timezone.utc).isoformat(),
        "session_id":        session_id,
        "user_text":         user_text,
        "text_hash":         hashlib.sha256(user_text.encode()).hexdigest()[:16],
        "text_length":       len(user_text),
        "detected_language": api_response.get("detected_language", ""),
        "language_name":     api_response.get("language_name", ""),
        "confidence_tier":   api_response.get("confidence_tier", ""),
        "mode_used":         api_response.get("mode_used", ""),
        "processing_ms":     api_response.get("processing_ms"),
        "st1_label":         st1.get("label"),
        "st1_probability":   st1.get("probability"),
        "st2_labels":        json.dumps(st2.get("labels")) if st2.get("labels") else None,
        "st2_gated_out":     int(bool(st2.get("gated_out", False))),
        "st3_labels":        json.dumps(st3.get("labels")) if st3.get("labels") else None,
        "st3_gated_out":     int(bool(st3.get("gated_out", False))),
        "st3_available":     int(bool(st3.get("available", True))),
        "st3_suppressed":    int(bool(st3.get("suppressed", False))),
    }
    sqlite_id = _save_sqlite(row)
    _save_sheets(row, sqlite_id)
    return sqlite_id

def save_feedback(prediction_id: int, feedback: str) -> bool:
    _update_feedback_sqlite(prediction_id, feedback)
    _update_feedback_sheets(prediction_id, feedback)
    return True
