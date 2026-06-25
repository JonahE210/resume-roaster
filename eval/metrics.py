"""Metric computations comparing parsed output to ground-truth labels.

Pure functions over plain dicts so they're trivially unit-testable and don't
depend on the backend package layout.
"""
from __future__ import annotations


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def section_f1(pred_types: list[str], gold_types: list[str]) -> dict:
    """F1 over the SET of section types found (order-independent)."""
    pred, gold = set(pred_types), set(gold_types)
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def entry_grouping_accuracy(pred_counts: dict[str, int], gold_counts: dict[str, int]) -> float:
    """Fraction of sections where predicted entry count == gold entry count."""
    if not gold_counts:
        return 1.0
    correct = sum(1 for k, v in gold_counts.items() if pred_counts.get(k) == v)
    return correct / len(gold_counts)


def bullet_attribution_accuracy(pred: list[dict], gold: list[dict]) -> float:
    """Fraction of gold bullets attached to the correct entry.

    pred/gold are lists of {"entry_key": str, "bullet": str}. A gold bullet is
    correct if some predicted bullet with the same normalized text shares the
    same normalized entry_key. This is the headline metric.
    """
    if not gold:
        return 1.0
    pred_index = {(_norm(p["entry_key"]), _norm(p["bullet"])) for p in pred}
    correct = sum(
        1 for g in gold if (_norm(g["entry_key"]), _norm(g["bullet"])) in pred_index
    )
    return correct / len(gold)
