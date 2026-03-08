# ml/inference.py
# Shared inference engine used by both fallback.py and ensemble.py.
# Handles: model loading from HF, tokenization, sigmoid, accumulation.

import os
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from config import MAX_LEN, TASK_LABELS

# Token from env — set as HF_TOKEN in HuggingFace Spaces secrets
HF_TOKEN = os.environ.get("HF_TOKEN", None)


def _tokenize(text: str, tokenizer) -> dict:
    """Tokenize a single string. Returns dict of tensors on CPU."""
    enc = tokenizer(
        text,
        add_special_tokens=True,
        max_length=MAX_LEN,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    return enc


def run_single_model(
    repo_id: str,
    subfolder: str,
    task_id: int,
    text: str,
    weight: float,
    accumulator: dict,
    device: str,
) -> None:
    """
    Load one model from HuggingFace, run inference on a single text string,
    and accumulate weighted probabilities into `accumulator`.

    accumulator is mutated in place:
        accumulator["probs"]  → np.array of weighted summed probs (shape: n_labels)
        accumulator["mass"]   → float, sum of weights applied so far
    """
    print(f"  → Loading {repo_id}/{subfolder}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            repo_id, subfolder=subfolder, token=HF_TOKEN
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            repo_id, subfolder=subfolder, token=HF_TOKEN
        )
    except Exception as e:
        print(f"  ⚠️ Failed to load {subfolder}: {e}")
        return

    model.to(device)
    model.eval()

    enc = _tokenize(text, tokenizer)
    input_ids = enc["input_ids"].to(device)
    attention_mask = enc["attention_mask"].to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        probs = torch.sigmoid(outputs.logits).cpu().numpy().squeeze()  # shape: (n_labels,)

    # Handle single-label case (ST1 returns shape () not (1,))
    if probs.ndim == 0:
        probs = np.array([float(probs)])

    if "probs" not in accumulator:
        accumulator["probs"] = probs * weight
        accumulator["mass"] = weight
    else:
        accumulator["probs"] += probs * weight
        accumulator["mass"] += weight

    del model, tokenizer
    torch.cuda.empty_cache()


def finalize(accumulator: dict, task_id: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute weighted average probabilities and apply global threshold.

    Returns:
        avg_probs  → np.array of floats  (shape: n_labels)
        predictions → np.array of 0/1    (shape: n_labels)
    """
    from config import THRESHOLDS

    avg_probs = accumulator["probs"] / accumulator["mass"]
    predictions = (avg_probs > THRESHOLDS[task_id]).astype(int)
    return avg_probs, predictions


def probs_to_response(avg_probs: np.ndarray, predictions: np.ndarray, task_id: int) -> dict:
    """
    Package averaged probabilities + binary predictions into response dict
    keyed by label name.

    Returns dict like:
        {
          "political":     {"score": 0.87, "predicted": 1},
          "racial/ethnic": {"score": 0.12, "predicted": 0},
          ...
        }
    """
    labels = TASK_LABELS[task_id]
    return {
        label: {
            "score": round(float(avg_probs[i]), 4),
            "predicted": int(predictions[i]),
        }
        for i, label in enumerate(labels)
    }


def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"
