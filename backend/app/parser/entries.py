"""Stage 4 — Entry grouping.

Within each section's line range, group lines into entries. An entry typically
starts with a header line (title + right-aligned date), often followed by an
org/location line, then bullets.

A new entry begins when we see a new "header pattern":
  - a line with a right-aligned date run, and/or
  - left-aligned non-bullet text at the section's base indent, and/or
  - bold/emphasized text after a block of bullets.
"""
from __future__ import annotations

from app.parser import bullets, fields
from app.parser.lines import detect_right_aligned_run
from app.schemas.primitives import BBox, Line
from app.schemas.resume import Entry

INDENT_TOL = 3.0
EMPHASIS_FONT_RATIO = 1.1


def _line_font(line: Line) -> float | None:
    sizes = [w.font_size for w in line.words if w.font_size is not None]
    return max(sizes) if sizes else None


def _bullet_text_x0(line: Line) -> float:
    words = line.words
    if words and words[0].text in bullets.BULLET_MARKERS and len(words) > 1:
        return words[1].bbox.x0
    return line.bbox.x0


def _run_split(line: Line) -> tuple[list | None, str, str]:
    """Return (run, body_text, run_text) for a header line; run is the trailing
    right-aligned Word suffix (or None), body_text is the title/org prefix."""
    run = detect_right_aligned_run(line)
    n = len(run) if run else 0
    body_words = line.words[: len(line.words) - n]
    body_text = " ".join(x.text for x in body_words)
    run_text = " ".join(x.text for x in run) if run else ""
    return run, body_text, run_text


def _union_bbox(section_lines: list[Line]) -> BBox:
    return BBox(
        x0=min(ln.bbox.x0 for ln in section_lines),
        y0=min(ln.bbox.y0 for ln in section_lines),
        x1=max(ln.bbox.x1 for ln in section_lines),
        y1=max(ln.bbox.y1 for ln in section_lines),
    )


def group_entries(
    section_lines: list[Line], base_font_size: float | None = None
) -> list[Entry]:
    """Segment a section's lines into entries and populate their fields."""
    if not section_lines:
        return []

    # Step A — base indent from non-bullet lines (headers/org), tolerance applied.
    non_bullet = [ln for ln in section_lines if not bullets.is_bullet_line(ln)]
    pool = non_bullet if non_bullet else section_lines
    base_indent = min(ln.bbox.x0 for ln in pool)

    # Step B — classify each line as BULLET / CONTINUATION / TEXT.
    kinds: list[str] = []
    last_bullet_x0: float | None = None
    for line in section_lines:
        if last_bullet_x0 is not None and bullets.is_continuation(
            line, last_bullet_x0, base_indent
        ):
            kinds.append("CONTINUATION")
        elif bullets.is_bullet_line(line, body_indent=base_indent):
            kinds.append("BULLET")
            last_bullet_x0 = _bullet_text_x0(line)
        else:
            kinds.append("TEXT")
            last_bullet_x0 = None

    # Step C — entry boundaries (only TEXT lines may start an entry).
    # A bold company/org line is locally indistinguishable from a bold new-entry
    # header, so emphasis alone must NEVER open a new entry (that mis-split a
    # secondary org line into a fake entry, corrupting bullet attribution). Real
    # new entries are covered by rule 2 (own right-aligned date run) and rule 3
    # (first text after a bullet/continuation block). `emphasized` is retained
    # purely as a confidence signal. Accepted limitation: entries distinguished
    # ONLY by bold titles with no dates and no bullets under-segment into one
    # entry — rare for SWE resumes and the safer failure direction.
    entry_starts: list[int] = []
    entry_signals: list[bool] = []
    prev_kind: str | None = None
    for i, line in enumerate(section_lines):
        if kinds[i] == "TEXT":
            run = detect_right_aligned_run(line)
            lf = _line_font(line)
            emphasized = abs(line.bbox.x0 - base_indent) <= INDENT_TOL and (
                any(w.bold for w in line.words)
                or (
                    base_font_size is not None
                    and lf is not None
                    and lf > EMPHASIS_FONT_RATIO * base_font_size
                )
            )
            boundary = (
                i == 0
                or run is not None  # rule 2: own right-aligned date run
                or prev_kind in ("BULLET", "CONTINUATION")  # rule 3: out of a bullet block
            )
            if boundary:
                entry_starts.append(i)
                # emphasis still informs confidence but NEVER creates a boundary.
                entry_signals.append(
                    run is not None
                    or prev_kind in ("BULLET", "CONTINUATION")
                    or emphasized
                )
        prev_kind = kinds[i]

    # Defensive: a section with no header line at all -> one bullet-only entry.
    if not entry_starts:
        merged = bullets.assign_bullets(section_lines, [0], body_indent=base_indent)
        return [
            Entry(bullets=merged[0], bbox=_union_bbox(section_lines), confidence=0.7)
        ]

    bullet_lists = bullets.assign_bullets(
        section_lines, entry_starts, body_indent=base_indent
    )

    # Step D — build entries.
    out: list[Entry] = []
    n = len(entry_starts)
    for e in range(n):
        start_i = entry_starts[e]
        end_i = entry_starts[e + 1] if e + 1 < n else len(section_lines)
        header = section_lines[start_i]
        member_lines = section_lines[start_i:end_i]

        run, body_text, run_text = _run_split(header)
        title = body_text or None

        start_date = end_date = None
        if run_text:
            start_date, end_date = fields.find_date_range(run_text)
        if start_date is None and end_date is None:
            start_date, end_date = fields.find_date_range(header.text)

        secondary = [
            section_lines[j]
            for j in range(start_i + 1, end_i)
            if kinds[j] == "TEXT"
        ]
        organization = secondary[0].text if secondary else None

        location = fields.find_location(run_text) if run_text else None
        if location is None and secondary:
            location = fields.find_location(secondary[0].text)

        confidence = 1.0
        if not entry_signals[e]:
            confidence -= 0.3
        if title is not None and start_date is None and end_date is None:
            confidence -= 0.2
        confidence = max(0.0, min(1.0, confidence))

        out.append(
            Entry(
                title=title,
                organization=organization,
                location=location,
                start_date=start_date,
                end_date=end_date,
                bullets=bullet_lists[e] if e < len(bullet_lists) else [],
                bbox=_union_bbox(member_lines),
                confidence=confidence,
            )
        )
    return out
