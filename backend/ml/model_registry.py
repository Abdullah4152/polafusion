# ml/model_registry.py
# Builds exact HuggingFace subfolder paths matching the repo structures.
#
# Repo A: semeval-deberta (5-fold mDeBERTa, all 3 subtasks, augmented)
#   subtask_{task_id}_5fold_mdeberta_aug/subtask{task_id}_final_models/fold_{fold}
#
# Repo B: semeval-3fold-xlmr (3-fold XLM-R Large, all 3 subtasks, augmented)
#   subtask_{task_id}_xlmr_3fold_aug/subtask{task_id}_xlmr_large_final_models/fold_{fold}
#
# Repo C: semeval-xlmr-full-trained (single fully-trained XLM-R, ST2 + ST3 only)
#   ST2: full_train_model_task2_xlm_r/full_train_model_task2
#   ST3: subtask_3_xlmr_full_trained_aug/full_train_model_task3

from config import HF_REPO


def deberta_subfolder(task_id: int, fold: int) -> str:
    """
    5-fold mDeBERTa — Repo A.
    Valid task_id: 1, 2, 3  |  Valid fold: 0–4
    """
    return (
        f"subtask_{task_id}_5fold_mdeberta_aug/"
        f"subtask{task_id}_final_models/"
        f"fold_{fold}"
    )


def xlmr_3fold_subfolder(task_id: int, fold: int) -> str:
    """
    3-fold XLM-R Large — Repo B.
    Valid task_id: 1, 2, 3  |  Valid fold: 0–2
    """
    return (
        f"subtask_{task_id}_xlmr_3fold_aug/"
        f"subtask{task_id}_xlmr_large_final_models/"
        f"fold_{fold}"
    )


def xlmr_full_subfolder(task_id: int) -> str:
    """
    Fully-trained XLM-R — Repo C.
    Valid task_id: 2, 3 only (no full-trained for ST1)
    """
    if task_id == 2:
        return "subtask_2_xlmr_full_trained_aug/full_train_model_task2"
    elif task_id == 3:
        return "subtask_3_xlmr_full_trained_aug/full_train_model_task3"
    else:
        raise ValueError(f"No full-trained XLM-R for subtask {task_id}. Use 3-fold for ST1.")


# ─────────────────────────────────────────────
# Model specs used by fallback.py and ensemble.py
# Each entry: (repo_id, subfolder, weight)
# ─────────────────────────────────────────────

def fallback_specs(task_id: int) -> list[tuple[str, str, float]]:
    """
    Fallback mode: single fold_0 mDeBERTa per subtask.
    Returns list of (repo_id, subfolder, weight).
    """
    return [
        (HF_REPO["deberta"], deberta_subfolder(task_id, fold=0), 1.0)
    ]


def ensemble_specs(task_id: int) -> list[tuple[str, str, float]]:
    """
    Ensemble mode — mirrors competition pipeline exactly:

    ST1 — "8-Fold Gatekeeper":
        5× mDeBERTa (w=1.0) + 3× XLM-R 3fold (w=5/3)
        Total mass: 5.0 + 5.0 = 10.0 (balanced)

    ST2 — "6-Fold Specialist":
        5× mDeBERTa (w=1.0) + 1× XLM-R full-trained (w=5.0)

    ST3 — "6-Fold Specialist":
        5× mDeBERTa (w=1.0) + 1× XLM-R full-trained (w=5.0)
    """
    specs = []
    xlmr_weight = 5.0 / 3.0  # ≈1.667 — balances 3 XLM-R folds to total mass 5.0

    # mDeBERTa folds (all subtasks)
    for fold in range(5):
        specs.append((HF_REPO["deberta"], deberta_subfolder(task_id, fold), 1.0))

    if task_id == 1:
        # 3-fold XLM-R (only ST1 uses 3fold for ensemble)
        for fold in range(3):
            specs.append((HF_REPO["xlmr_3fold"], xlmr_3fold_subfolder(task_id, fold), xlmr_weight))
    else:
        # Full-trained XLM-R (ST2 + ST3)
        specs.append((HF_REPO["xlmr_full"], xlmr_full_subfolder(task_id), 5.0))

    return specs
