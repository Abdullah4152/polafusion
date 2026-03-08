# ml/ensemble.py
# Ensemble mode: mirrors the exact competition pipeline.
#
# ST1 — "8-Fold Gatekeeper":   5× mDeBERTa (w=1.0) + 3× XLM-R 3fold (w=5/3)
# ST2 — "6-Fold Specialist":   5× mDeBERTa (w=1.0) + 1× XLM-R full-trained (w=5.0)
# ST3 — "6-Fold Specialist":   5× mDeBERTa (w=1.0) + 1× XLM-R full-trained (w=5.0)
#
# Expected latency: 30-90s on T4 GPU depending on model load cache state.

import time
from config import THRESHOLDS, LANGUAGE_MATRIX, ST3_SUPPRESSED_LANGS
from ml.model_registry import ensemble_specs
from ml.inference import run_single_model, finalize, probs_to_response, get_device


def run_ensemble(text: str, lang_code: str) -> dict:
    """
    Run full 3-subtask hierarchical pipeline in ensemble mode.

    Args:
        text:      Raw input text from user.
        lang_code: 3-letter code from LANGUAGE_MATRIX.

    Returns:
        Full prediction dict matching API response schema.
    """
    device = get_device()
    t_start = time.time()

    lang_info = LANGUAGE_MATRIX[lang_code]
    _, _, _, st3_available = lang_info
    st3_suppressed = lang_code in ST3_SUPPRESSED_LANGS

    # ── SUBTASK 1: 8-FOLD GATEKEEPER ──────────────────────────────
    print(f"\n[Ensemble] ST1 — 8-Fold Gatekeeper (5 mDeBERTa + 3 XLM-R)")
    acc1 = {}
    specs1 = ensemble_specs(task_id=1)
    for i, (repo_id, subfolder, weight) in enumerate(specs1):
        print(f"  Model {i+1}/{len(specs1)}")
        run_single_model(repo_id, subfolder, 1, text, weight, acc1, device)

    avg_probs1, preds1 = finalize(acc1, task_id=1)
    st1_prob = float(avg_probs1[0])
    st1_label = int(preds1[0])

    subtask1_result = {
        "label": st1_label,
        "probability": round(st1_prob, 4),
        "threshold": THRESHOLDS[1],
    }

    # ── GATING ─────────────────────────────────────────────────────
    if st1_label == 0:
        print(f"[Ensemble] ST1=0 — gating out ST2 and ST3")
        return _build_response(
            subtask1=subtask1_result,
            subtask2={"gated_out": True, "labels": None},
            subtask3={"available": st3_available, "gated_out": True,
                      "suppressed": st3_suppressed, "labels": None},
            lang_code=lang_code,
            mode="ensemble",
            elapsed=time.time() - t_start,
        )

    # ── SUBTASK 2: 6-FOLD SPECIALIST ───────────────────────────────
    print(f"\n[Ensemble] ST2 — 6-Fold Specialist (5 mDeBERTa + 1 XLM-R full)")
    acc2 = {}
    specs2 = ensemble_specs(task_id=2)
    for i, (repo_id, subfolder, weight) in enumerate(specs2):
        print(f"  Model {i+1}/{len(specs2)}")
        run_single_model(repo_id, subfolder, 2, text, weight, acc2, device)

    avg_probs2, preds2 = finalize(acc2, task_id=2)
    subtask2_result = {
        "gated_out": False,
        "labels": probs_to_response(avg_probs2, preds2, task_id=2),
    }

    # ── SUBTASK 3: 6-FOLD SPECIALIST ───────────────────────────────
    if not st3_available:
        print(f"[Ensemble] ST3 — skipped (lang {lang_code} not in ST3 data)")
        subtask3_result = {
            "available": False,
            "gated_out": False,
            "suppressed": False,
            "labels": None,
        }
    elif st3_suppressed:
        print(f"[Ensemble] ST3 — suppressed (unreliable for {lang_code})")
        subtask3_result = {
            "available": True,
            "gated_out": False,
            "suppressed": True,
            "labels": None,
            "warning": f"Manifestation detection is not reliable for {LANGUAGE_MATRIX[lang_code][0]}.",
        }
    else:
        print(f"\n[Ensemble] ST3 — 6-Fold Specialist (5 mDeBERTa + 1 XLM-R full)")
        acc3 = {}
        specs3 = ensemble_specs(task_id=3)
        for i, (repo_id, subfolder, weight) in enumerate(specs3):
            print(f"  Model {i+1}/{len(specs3)}")
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
        mode="ensemble",
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
