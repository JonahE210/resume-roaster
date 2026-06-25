"""Rule-based bullet quality scoring.

Each bullet gets a 0-1 score plus flags. This is deterministic so it's testable
and explainable — a deliberate contrast to "ask the LLM what it thinks".
"""
from __future__ import annotations

import re

STRONG_VERBS = {
    "built", "designed", "implemented", "developed", "led", "shipped", "created",
    "optimized", "reduced", "increased", "automated", "architected", "launched",
    "engineered", "refactored", "deployed", "integrated", "migrated", "scaled",
}
WEAK_PHRASES = ("worked on", "helped with", "responsible for", "assisted", "various")
METRIC = re.compile(r"\d+(\.\d+)?\s?(%|x|k|ms|s|users|hours|requests|qps)?", re.I)


def score_bullet(text: str) -> dict:
    """Return a score breakdown for one bullet."""
    lower = text.lower().strip()
    first_word = lower.split()[0] if lower.split() else ""

    has_strong_verb = first_word in STRONG_VERBS
    has_metric = bool(METRIC.search(text)) and any(c.isdigit() for c in text)
    is_vague = any(p in lower for p in WEAK_PHRASES)
    mentions_tech = False  # TODO(phase4): match against a tech-keyword set

    score = (
        0.4 * has_strong_verb
        + 0.3 * has_metric
        + 0.2 * (not is_vague)
        + 0.1 * mentions_tech
    )
    return {
        "text": text,
        "score": round(score, 2),
        "has_strong_verb": has_strong_verb,
        "has_metric": has_metric,
        "is_vague": is_vague,
    }
