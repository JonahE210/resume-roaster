"""Stage 2 — Line reconstruction.

Group words into visual lines. This is the foundation; if it's sloppy, every later
stage breaks. Test it hard (tests/test_lines.py).

Algorithm:
  1. Sort words by (page, y0, x0).
  2. Group words whose vertical center is within `y_tol` of the current line's
     center. y_tol scales with text height (0.5 * median word height), not a hard
     pixel value, so it survives font-size changes.
  3. Within a line, sort words by x0 (left-to-right).
  4. Keep words as a list so callers can detect right-aligned runs via x-gaps.
"""
from __future__ import annotations

from statistics import median

from app.schemas.primitives import Line, Word

# Minimum normal-space width (pt) used to floor the spacing baseline so the
# right-aligned detector never derives an absurdly small threshold.
ABS_MIN_GAP = 2.0


def reconstruct_lines(words: list[Word], y_tol_ratio: float = 0.5) -> list[Line]:
    """Group words into lines. Returns lines in reading order.

    Words are clustered by vertical center within a height-scaled tolerance,
    greedily and left-to-right, never merging across pages.
    """
    if not words:
        return []

    # Guard degenerate boxes (h<=0 from malformed/zero-height spans) without
    # repairing the boxes themselves; fall back to a sane default + floor.
    heights = [h for h in (w.bbox.height for w in words) if h > 0]
    median_h = median(heights) if heights else 10.0
    y_tol = max(y_tol_ratio * median_h, 1.0)

    ordered = sorted(words, key=lambda w: (w.page, w.bbox.y0, w.bbox.x0))

    lines: list[list[Word]] = []
    current: list[Word] = []
    current_page: int | None = None
    line_center: float | None = None

    for word in ordered:
        center = word.bbox.y_center
        if (
            current
            and word.page == current_page
            and abs(center - line_center) <= y_tol
        ):
            current.append(word)
            # Running mean of member centers keeps the comparison baseline stable.
            # KNOWN LIMITATION (Bug #4, deferred): on steeply sloped lines the
            # running mean lags, which can over-split; revisit if Phase 3 eval
            # surfaces line-grouping errors.
            line_center = sum(m.bbox.y_center for m in current) / len(current)
        else:
            if current:
                lines.append(current)
            current = [word]
            current_page = word.page
            line_center = center

    if current:
        lines.append(current)

    return [
        Line(words=sorted(group, key=lambda w: w.bbox.x0), page=group[0].page)
        for group in lines
    ]


def detect_right_aligned_run(line: Line, gap_ratio: float = 3.0) -> list[Word] | None:
    """Return the trailing words separated from the body by a large x-gap.

    Dates/locations are usually right-aligned, creating a big horizontal gap
    between the title text and the date text on the same line. Use the gap to
    split "Software Engineering Intern        May 2025 - Aug 2025".
    """
    words = line.words
    if len(words) < 2:
        return None

    gaps = [words[i + 1].bbox.x0 - words[i].bbox.x1 for i in range(len(words) - 1)]

    # Estimate a normal space width INDEPENDENT of the gaps themselves, so a
    # single-gap line can be judged at all and touching words (gap≈0) don't
    # collapse the baseline to ~0 and trigger false positives.
    # Use None-semantics (not truthiness): a legitimate 0.0 font size is
    # degenerate but still "present", so only fall back when a size is missing.
    if all(w.font_size is not None for w in words):
        space_est = 0.25 * median(w.font_size for w in words)
    else:
        space_est = median(w.bbox.width / max(len(w.text), 1) for w in words)
    space_est = max(space_est, ABS_MIN_GAP)

    if len(gaps) >= 2:
        inter = median(sorted(gaps)[:-1])  # trim the largest (the date gap)
        baseline = max(inter, space_est)  # never below a real space width
    else:  # single gap: 2-word line cannot self-measure; use the space estimate
        baseline = space_est
    threshold = gap_ratio * baseline

    last_big = None
    for i, gap in enumerate(gaps):
        if gap > threshold:
            last_big = i

    if last_big is None:
        return None

    return words[last_big + 1:]
