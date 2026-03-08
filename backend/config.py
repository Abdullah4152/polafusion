# config.py — PolaFusion Backend
# All static config baked in — no DB reads needed for inference

# ─────────────────────────────────────────────
# GLOBAL THRESHOLDS (best performing in competition)
# ─────────────────────────────────────────────
THRESHOLDS = {
    1: 0.50,   # Gatekeeper — binary polarization
    2: 0.35,   # Type labels (multi-label)
    3: 0.30,   # Manifestation labels (multi-label)
}

# ─────────────────────────────────────────────
# TASK LABELS
# ─────────────────────────────────────────────
TASK_LABELS = {
    1: ["polarization"],
    2: ["political", "racial/ethnic", "religious", "gender/sexual", "other"],
    3: [
        "stereotype",
        "vilification",
        "dehumanization",
        "extreme_language",
        "lack_of_empathy",
        "invalidation",
    ],
}

# ─────────────────────────────────────────────
# LANGUAGE MATRIX
# code → (display_name, flag, confidence_tier, subtask3_available)
#
# tier logic:
#   high   → F1 macro ≥ 0.60 on ST2 best model
#   medium → F1 macro 0.35–0.59
#   low    → F1 macro < 0.35  (show ⚠️ warning in UI)
#
# subtask3_available = False for mya, ita, pol, rus
# (these 4 were excluded from ST3 in the competition data)
#
# ST3 suppressed (tier=low AND st3 known-bad):
#   fas (Persian) — ST3 F1=0.0 in all experiments
#   hau (Hausa)   — ST3 F1=0.14 avg
#   ori (Odia)    — ST3 F1=0.03 avg
# ─────────────────────────────────────────────
LANGUAGE_MATRIX = {
    #  code      name          flag   tier       st3_avail
    "hin": ("Hindi",     "🇮🇳", "high",   True),
    "zho": ("Chinese",   "🇨🇳", "high",   True),
    "urd": ("Urdu",      "🇵🇰", "high",   True),
    "khm": ("Khmer",     "🇰🇭", "high",   True),
    "arb": ("Arabic",    "🇸🇦", "high",   True),
    "nep": ("Nepali",    "🇳🇵", "high",   True),
    "pan": ("Punjabi",   "🇮🇳", "medium", True),
    "deu": ("German",    "🇩🇪", "medium", True),
    "spa": ("Spanish",   "🇪🇸", "medium", True),
    "ben": ("Bengali",   "🇧🇩", "medium", True),
    "amh": ("Amharic",   "🇪🇹", "medium", True),
    "tel": ("Telugu",    "🇮🇳", "medium", True),
    "swa": ("Swahili",   "🇹🇿", "medium", True),
    "tur": ("Turkish",   "🇹🇷", "medium", True),
    "eng": ("English",   "🇬🇧", "medium", True),
    "mya": ("Burmese",   "🇲🇲", "medium", False),  # no ST3 data
    "ita": ("Italian",   "🇮🇹", "medium", False),  # no ST3 data
    "pol": ("Polish",    "🇵🇱", "medium", False),  # no ST3 data
    "rus": ("Russian",   "🇷🇺", "medium", False),  # no ST3 data
    "hau": ("Hausa",     "🇳🇬", "low",    True),   # ST3 unreliable
    "fas": ("Persian",   "🇮🇷", "low",    True),   # ST3 F1=0.0
    "ori": ("Odia",      "🇮🇳", "low",    True),   # ST3 weak
}

# Languages where ST3 scores are so poor they must be suppressed in UI
# (available in data but results are not trustworthy to show)
ST3_SUPPRESSED_LANGS = {"fas", "hau", "ori"}

# Minimum text length before we attempt prediction
MIN_TEXT_CHARS = 20

# ─────────────────────────────────────────────
# HuggingFace Repo IDs
# ─────────────────────────────────────────────
HF_REPO = {
    "deberta":      "EkcupKadakChai/semeval-deberta",
    "xlmr_3fold":   "EkcupKadakChai/semeval-3fold-xlmr",
    "xlmr_full":    "EkcupKadakChai/semeval-xlmr-full-trained",
}

# Model settings
MAX_LEN   = 128
BATCH_SIZE = 1   # Single-text inference from extension
