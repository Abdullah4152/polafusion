# ml/fallback.py
# Fallback mode: one mDeBERTa fold_0 per subtask.
# Runs the full hierarchical pipeline (ST1 → ST2 → ST3).
# Fastest mode — target latency ~1-2s on GPU, ~5-8s on CPU.

import time
from config import THRESHOLDS, LANGUAGE_MATRIX, ST3_SUPPRESSED_LANGS
from ml.model_registry import fallback_specs
from ml.inference import run_single_model, finalize, probs_to_response, get_device


def run_fallback(text: str, lang_code: str) -> dict:
    """
    Run full 3-subtask hierarchical pipeline in fallback mode.

    Args:
        text:      Raw input text from user.
        lang_code: 3-letter code from LANGUAGE_MATRIX (e.g. "hin").

    Returns:
        Full prediction dict matching API response schema.
    """
    device = get_device()
    t_start = time.time()

    lang_info = LANGUAGE_MATRIX[lang_code]
    _, _, _, st3_available = lang_info
    st3_suppressed = lang_code in ST3_SUPPRESSED_LANGS

    # ── SUBTASK 1: GATEKEEPER ──────────────────────────────────────
    print(f"\n[Fallback] ST1 — Gatekeeper")
    acc1 = {}
    for repo_id, subfolder, weight in fallback_specs(task_id=1):
        run_single_model(repo_id, subfolder, 1, text, weight, acc1, device)

    avg_probs1, preds1 = finalize(acc1, task_id=1)
    st1_prob = float(avg_probs1[0])
    st1_label = int(preds1[0])

    subtask1_result = {
        "label": st1_label,
        "probability": round(st1_prob, 4),
        "threshold": THRESHOLDS[1],
    }

    # ── GATING: If not polarized, skip ST2 + ST3 ──────────────────
    if st1_label == 0:
        print(f"[Fallback] ST1=0 — gating out ST2 and ST3")
        return _build_response(
            subtask1=subtask1_result,
            subtask2={"gated_out": True, "labels": None},
            subtask3={"available": st3_available, "gated_out": True,
                      "suppressed": st3_suppressed, "labels": None},
            lang_code=lang_code,
            mode="fallback",
            elapsed=time.time() - t_start,
        )

    # ── SUBTASK 2: TYPE CLASSIFIER ─────────────────────────────────
    print(f"[Fallback] ST2 — Type Classifier")
    acc2 = {}
    for repo_id, subfolder, weight in fallback_specs(task_id=2):
        run_single_model(repo_id, subfolder, 2, text, weight, acc2, device)

    avg_probs2, preds2 = finalize(acc2, task_id=2)
    subtask2_result = {
        "gated_out": False,
        "labels": probs_to_response(avg_probs2, preds2, task_id=2),
    }

    # ── SUBTASK 3: MANIFESTATION ────────────────────────────────────
    if not st3_available:
        print(f"[Fallback] ST3 — skipped (lang {lang_code} not in ST3 data)")
        subtask3_result = {
            "available": False,
            "gated_out": False,
            "suppressed": False,
            "labels": None,
        }
    elif st3_suppressed:
        print(f"[Fallback] ST3 — suppressed (unreliable for {lang_code})")
        subtask3_result = {
            "available": True,
            "gated_out": False,
            "suppressed": True,
            "labels": None,
            "warning": f"Manifestation detection is not reliable for {LANGUAGE_MATRIX[lang_code][0]}.",
        }
    else:
        print(f"[Fallback] ST3 — Manifestation Classifier")
        acc3 = {}
        for repo_id, subfolder, weight in fallback_specs(task_id=3):
            run_single_model(repo_id, subfolder, 3, text, weight, acc3, device)

        avg_probs3, preds3 = finalize(acc3, task_id=3)
        subtask3_result = {
            "available": True,
            "gated_out": False,
            "suppressed": False,
            "labels": probs_to_response(avg_probs3, preds3, task_id=3),
        }

    return _build_response(
        subtask1=subtask1_result,
        subtask2=subtask2_result,
        subtask3=subtask3_result,
        lang_code=lang_code,
        mode="fallback",
        elapsed=time.time() - t_start,
    )


def _build_response(subtask1, subtask2, subtask3, lang_code, mode, elapsed) -> dict:
    name, flag, tier, _ = LANGUAGE_MATRIX[lang_code]
    return {
        "detected_language": lang_code,
        "language_name": name,
        "language_flag": flag,
        "confidence_tier": tier,
        "subtask1": subtask1,
        "subtask2": subtask2,
        "subtask3": subtask3,
        "mode_used": mode,
        "processing_ms": round(elapsed * 1000),
    }
