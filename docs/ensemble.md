# Ensemble Design

## Motivation

A single fine-tuned model can be brittle — its predictions are sensitive to random seed, fold composition, and training dynamics. The PolaFusion ensemble combines multiple models with calibrated weights so no single model dominates the vote.

## Architecture per Subtask

### ST1 — 8-Fold Gatekeeper

ST1 is the most critical subtask: a false negative here means the text is never analyzed for type or manifestation. We use the most models here.

```
Model                   Folds   Weight    Mass
──────────────────────────────────────────────
mDeBERTa-v3-base          5     1.000     5.0
XLM-R Large (3-fold)      3     1.667     5.0
──────────────────────────────────────────────
Total                     8               10.0
```

**Weight derivation:** Each XLM-R fold gets weight = 5.0 / 3 ≈ 1.667 so the total XLM-R contribution equals the total mDeBERTa contribution. Neither architecture dominates.

### ST2 — 6-Fold Specialist

ST2 uses a full-trained XLM-R rather than a 3-fold one because ST2 has more training signal and benefits from seeing the full dataset.

```
Model                   Folds   Weight    Mass
──────────────────────────────────────────────
mDeBERTa-v3-base          5     1.000     5.0
XLM-R Large (full-train)  1     5.000     5.0
──────────────────────────────────────────────
Total                     6               10.0
```

### ST3 — 6-Fold Specialist

Same architecture as ST2.

```
Model                   Folds   Weight    Mass
──────────────────────────────────────────────
mDeBERTa-v3-base          5     1.000     5.0
XLM-R Large (full-train)  1     5.000     5.0
──────────────────────────────────────────────
Total                     6               10.0
```

## Aggregation

For each label, each model outputs a probability. The ensemble computes a weighted average:

```python
weighted_prob = sum(prob_i * weight_i for model_i) / sum(weights)
predicted = 1 if weighted_prob >= threshold else 0
```

Thresholds: ST1=0.50, ST2=0.35, ST3=0.30

## Hierarchical Gating

```
Text → ST1
        │
        ├─ ST1 = 0 (not polarized)
        │         └─ Return: { polarized: false, st2: gated_out, st3: gated_out }
        │
        └─ ST1 = 1 (polarized)
                  ├─ Run ST2 → type labels
                  └─ Run ST3 → manifestation labels (if language available)
```

This prevents nonsensical outputs like "this text is not polarized but shows vilification."
