"""Stage 5 — Bullet detection + ownership.

Two jobs:
  1. Decide which lines are bullets (leading •, -, *, ▪, ◦, or hanging indent
     deeper than the entry header's indent).
  2. Attach each bullet to the correct entry: the nearest preceding entry header
     within the same section. Multi-line bullets (wrapped text) must merge into
     one bullet string based on indent continuation.

This is the single most impressive correctness metric in eval/ (bullet
attribution accuracy). Get it right and measure it.

TODO(phase2): implement detection + ownership; merge wrapped continuation lines.
"""
from __future__ import annotations

from app.schemas.primitives import Line

BULLET_MARKERS = ("•", "-", "*", "▪", "◦", "·", "–")


def is_bullet_line(line: Line) -> bool:
    """Heuristic: starts with a known marker. Extend with indent-based detection."""
    text = line.text.lstrip()
    return text.startswith(BULLET_MARKERS)


def strip_marker(text: str) -> str:
    """Remove a leading bullet marker and surrounding whitespace."""
    text = text.lstrip()
    for marker in BULLET_MARKERS:
        if text.startswith(marker):
            return text[len(marker):].strip()
    return text.strip()
