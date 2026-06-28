"""Stage 5 — Bullet detection + ownership.

Two jobs:
  1. Decide which lines are bullets (leading •, -, *, ▪, ◦, or hanging indent
     deeper than the entry header's indent).
  2. Attach each bullet to the correct entry: the nearest preceding entry header
     within the same section. Multi-line bullets (wrapped text) must merge into
     one bullet string based on indent continuation.

This is the single most impressive correctness metric in eval/ (bullet
attribution accuracy). Get it right and measure it.
"""
from __future__ import annotations

from app.parser.lines import detect_right_aligned_run
from app.schemas.primitives import Line

BULLET_MARKERS = ("•", "-", "*", "▪", "◦", "·", "–")
INDENT_TOL = 3.0


def _bullet_text_x0(line: Line) -> float:
    """x0 of the bullet's TEXT (after a standalone marker word, if any)."""
    words = line.words
    if words and words[0].text in BULLET_MARKERS and len(words) > 1:
        return words[1].bbox.x0
    return line.bbox.x0


def is_bullet_line(line: Line, body_indent: float | None = None) -> bool:
    """A bullet line: starts with a marker glyph, OR (when ``body_indent`` is
    given) is hanging-indented deeper than the entry's base text indent."""
    text = line.text.lstrip()
    if text.startswith(BULLET_MARKERS):
        return True
    if body_indent is not None and line.words:
        return line.bbox.x0 > body_indent + INDENT_TOL
    return False


def is_continuation(
    line: Line, prev_bullet_x0: float | None, body_indent: float, *, tol: float = 3.0
) -> bool:
    """A wrapped continuation of the previous bullet: no leading marker, not a
    new header (no right-aligned run), aligned with the previous bullet's text."""
    if prev_bullet_x0 is None:
        return False
    text = line.text.lstrip()
    if text.startswith(BULLET_MARKERS):
        return False
    if detect_right_aligned_run(line) is not None:
        return False
    x0 = line.bbox.x0
    return x0 >= prev_bullet_x0 - tol and x0 > body_indent


def strip_marker(text: str) -> str:
    """Remove a leading bullet marker and surrounding whitespace."""
    text = text.lstrip()
    for marker in BULLET_MARKERS:
        if text.startswith(marker):
            return text[len(marker):].strip()
    return text.strip()


def assign_bullets(
    section_lines: list[Line], entry_starts: list[int], *, body_indent: float
) -> list[list[str]]:
    """Attach bullets to entries, merging wrapped continuation lines.

    Returns one list[str] of merged, marker-stripped bullets per entry, aligned
    to ``entry_starts`` order. Bullets appearing before the first entry start
    attach to entry 0 (defensive).
    """
    starts = sorted(entry_starts)
    result: list[list[str]] = [[] for _ in range(max(len(starts), 1))]

    def entry_for(i: int) -> int:
        idx = 0
        for k, s in enumerate(starts):
            if s <= i:
                idx = k
            else:
                break
        return idx

    last_bullet_x0: float | None = None
    last_bullet_entry: int | None = None
    for i, line in enumerate(section_lines):
        e = entry_for(i)
        # Continuation is checked BEFORE is_bullet_line: a marker-less wrapped
        # line can be hanging-indented (which is_bullet_line would otherwise read
        # as a new bullet). Marker-bearing bullets are unaffected (a continuation
        # requires no marker), so this never mis-merges real bullets.
        if (
            last_bullet_x0 is not None
            and last_bullet_entry == e
            and is_continuation(line, last_bullet_x0, body_indent)
        ):
            result[e][-1] = (result[e][-1] + " " + line.text).strip()
            continue
        if is_bullet_line(line, body_indent=body_indent):
            result[e].append(strip_marker(line.text))
            last_bullet_x0 = _bullet_text_x0(line)
            last_bullet_entry = e
            continue
        # Header / secondary-text line: handled by entries.py; ends the run so a
        # following line can't merge into the prior entry's last bullet.
        last_bullet_x0 = None
        last_bullet_entry = None
    return result
