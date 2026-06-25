"""Stage 2 — Line reconstruction.

Group words into visual lines. This is the foundation; if it's sloppy, every later
stage breaks. Test it hard (tests/test_lines.py).

Algorithm:
  1. Sort words by (page, y0, x0).
  2. Group words whose vertical center is within `y_tol` of the current line's
     center. y_tol should scale with text height (e.g. 0.5 * median word height),
     not a hard pixel value, so it survives font-size changes.
  3. Within a line, sort words by x0 (left-to-right).
  4. Keep words as a list so callers can detect right-aligned runs via x-gaps.
"""
from __future__ import annotations

from app.schemas.primitives import Line, Word


def reconstruct_lines(words: list[Word], y_tol_ratio: float = 0.5) -> list[Line]:
    """Group words into lines. Returns lines in reading order.

    TODO(phase1): implement the y-clustering described above. Stub returns one
    line per word so the pipeline runs end-to-end before the real logic lands.
    """
    if not words:
        return []

    # --- Placeholder: one word per line (REPLACE in Phase 1) -----------------
    ordered = sorted(words, key=lambda w: (w.page, w.bbox.y0, w.bbox.x0))
    return [Line(words=[w], page=w.page) for w in ordered]


def detect_right_aligned_run(line: Line, gap_ratio: float = 3.0) -> list[Word] | None:
    """Return the trailing words separated from the body by a large x-gap.

    Dates/locations are usually right-aligned, creating a big horizontal gap
    between the title text and the date text on the same line. Use the gap to
    split "Software Engineering Intern        May 2025 - Aug 2025".

    TODO(phase2): compute median inter-word gap; flag the run after a gap
    `gap_ratio`x larger than the median.
    """
    return None
