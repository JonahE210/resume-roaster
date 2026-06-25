"""Stage 4 — Entry grouping.

Within each section's line range, group lines into entries. An entry typically
starts with a header line (title + right-aligned date), often followed by an
org/location line, then bullets.

A new entry begins when we see a new "header pattern":
  - a line with a right-aligned date run, and/or
  - left-aligned non-bullet text at the section's base indent, and/or
  - bold/emphasized text after a block of bullets.

TODO(phase2): implement the segmentation. Return Entry objects with bbox set
(union of member lines) and a confidence reflecting how clean the boundaries were.
"""
from __future__ import annotations

from app.schemas.primitives import Line
from app.schemas.resume import Entry


def group_entries(section_lines: list[Line]) -> list[Entry]:
    """Segment a section's lines into entries.

    Stub returns a single entry holding all lines' text as bullets so the
    pipeline runs. REPLACE in Phase 2.
    """
    if not section_lines:
        return []
    return [Entry(bullets=[ln.text for ln in section_lines], confidence=0.3)]
