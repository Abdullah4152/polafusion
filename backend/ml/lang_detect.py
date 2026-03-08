# ml/lang_detect.py
# Detects language of input text and maps it to our 3-letter codes.
# Discovers available lingua Language enum values at runtime —
# never crashes on missing languages regardless of lingua version.

from lingua import Language, LanguageDetectorBuilder
from config import LANGUAGE_MATRIX

# ─────────────────────────────────────────────
# Desired mapping: lingua enum NAME → our code
# We use the string name (e.g. "HINDI") and
# look it up with getattr() so missing ones
# are simply skipped, never crash the server.
# ─────────────────────────────────────────────
_DESIRED = {
    "HINDI":    "hin",
    "CHINESE":  "zho",
    "URDU":     "urd",
    "ARABIC":   "arb",
    "NEPALI":   "nep",
    "PUNJABI":  "pan",
    "GERMAN":   "deu",
    "SPANISH":  "spa",
    "BENGALI":  "ben",
    "AMHARIC":  "amh",
    "TELUGU":   "tel",
    "SWAHILI":  "swa",
    "TURKISH":  "tur",
    "ENGLISH":  "eng",
    "BURMESE":  "mya",
    "ITALIAN":  "ita",
    "POLISH":   "pol",
    "RUSSIAN":  "rus",
    "PERSIAN":  "fas",
    "ORIYA":    "ori",
    "KHMER":    "khm",
    "HAUSA":    "hau",
}

# Build map using only languages this build of lingua actually has
_LINGUA_TO_CODE = {}
_skipped = []

for _name, _code in _DESIRED.items():
    _lang = getattr(Language, _name, None)
    if _lang is not None:
        _LINGUA_TO_CODE[_lang] = _code
    else:
        _skipped.append(_name)

if _skipped:
    print(f"[lang_detect] ⚠️  Not in this lingua build (will default to 'eng'): {_skipped}")

_SUPPORTED_LANGUAGES = list(_LINGUA_TO_CODE.keys())

print(f"[lang_detect] ✅ Detector built with {len(_SUPPORTED_LANGUAGES)} languages")

# Build detector once at module import
_detector = (
    LanguageDetectorBuilder
    .from_languages(*_SUPPORTED_LANGUAGES)
    .with_minimum_relative_distance(0.1)
    .build()
)


def detect(text: str) -> tuple[str, str, str, str]:
    """
    Detect language of text.
    Returns (code, name, flag, tier) from LANGUAGE_MATRIX.
    Falls back to English if lingua can't detect or language not in matrix.
    """
    detected = _detector.detect_language_of(text)

    if detected is None or detected not in _LINGUA_TO_CODE:
        code = "eng"
    else:
        code = _LINGUA_TO_CODE[detected]

    name, flag, tier, _ = LANGUAGE_MATRIX[code]
    return code, name, flag, tier


def detect_with_confidence(text: str) -> dict:
    """Returns top language confidence scores — used for debugging."""
    results = _detector.compute_language_confidence_values(text)
    top = [
        {
            "code": _LINGUA_TO_CODE.get(r.language, "???"),
            "language": r.language.name,
            "confidence": round(r.value, 4),
        }
        for r in results[:5]
        if r.language in _LINGUA_TO_CODE
    ]
    return {"top_languages": top, "skipped_langs": _skipped}
