"""Rule-based bullet quality scoring.

Each bullet gets a 0-1 score plus flags. This is deterministic so it's testable
and explainable — a deliberate contrast to "ask the LLM what it thinks".
"""
from __future__ import annotations

import re

from app.scoring.tech_keywords import match_tech

STRONG_VERBS = {
    "built", "designed", "implemented", "developed", "led", "shipped", "created",
    "optimized", "reduced", "increased", "automated", "architected", "launched",
    "engineered", "refactored", "deployed", "integrated", "migrated", "scaled",
}
WEAK_PHRASES = ("worked on", "helped with", "responsible for", "assisted", "various")
# A number "counts" as a metric if it carries a recognized unit, OR it is a bare
# integer that is not a 4-digit year. Unit-less decimals (e.g. version "3.11") and
# standalone years (e.g. "2021") are excluded as false positives.
_NUM_WITH_UNIT = re.compile(
    r"\d[\d,]*(?:\.\d+)?\s?"
    r"(?:%|x|×|\+|k|m|b|ms|secs?|s|mins?|hrs?|hours?|days?|weeks?|months?|"
    r"users?|customers?|clients?|requests?|qps|rps|gb|tb|mb|fps)(?!\w)",
    re.I,
)
_BARE_INT = re.compile(r"(?<![\d.])\d{1,3}(?:,\d{3})*(?![\d.])")
_YEAR = re.compile(r"^(?:19|20)\d{2}$")


def _has_metric(text: str) -> bool:
    if _NUM_WITH_UNIT.search(text):
        return True
    for m in _BARE_INT.finditer(text):
        if not _YEAR.match(m.group().replace(",", "")):
            return True
    return False


def score_bullet(text: str) -> dict:
    """Return a score breakdown for one bullet."""
    lower = text.lower().strip()
    words = lower.split()
    first_word = words[0] if words else ""

    has_strong_verb = first_word in STRONG_VERBS
    has_metric = _has_metric(text)
    is_vague = any(p in lower for p in WEAK_PHRASES)
    tech_keywords = match_tech(text)
    mentions_tech = bool(tech_keywords)

    score = (
        0.4 * has_strong_verb
        + 0.3 * has_metric
        + 0.2 * (not is_vague and bool(words))
        + 0.1 * mentions_tech
    )
    return {
        "text": text,
        "score": round(score, 2),
        "has_strong_verb": has_strong_verb,
        "has_metric": has_metric,
        "is_vague": is_vague,
        "mentions_tech": mentions_tech,
        "tech_keywords": tech_keywords,
    }
