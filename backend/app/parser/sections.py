"""Stage 3 — Section detection.

Identify which lines are section headings and what type they are. Signals to
combine (no single one is reliable):
  - text matches a known section name (EDUCATION, EXPERIENCE, PROJECTS, SKILLS...)
  - ALL CAPS
  - larger font size than body text
  - bold
  - line is short and isolated (extra vertical whitespace above/below)
  - a horizontal rule near the line

Score each line; treat it as a heading above a threshold. Map the heading text to
a SectionType via a synonym table (e.g. "Work Experience" -> experience).
"""
from __future__ import annotations

from statistics import median

from app.schemas.primitives import Line
from app.schemas.resume import SectionType

# Multi-signal heading scoring (tunable). A heading must accumulate MORE than a
# name match alone (0.45 < THRESHOLD), so body lines that merely start with a
# section word ("Experience building ...") never fire.
W_NAME = 0.45
W_CAPS = 0.20
W_FONT = 0.20
W_BOLD = 0.15
W_SHORT = 0.10
W_ISOLATED = 0.10
HEADING_THRESHOLD = 0.60
FONT_LARGER_RATIO = 1.15
ISOLATED_GAP_RATIO = 1.5
SHORT_MAX_WORDS = 4

SECTION_SYNONYMS: dict[SectionType, tuple[str, ...]] = {
    SectionType.education: ("education", "academics"),
    SectionType.experience: ("experience", "work experience", "employment"),
    SectionType.projects: ("projects", "personal projects", "technical projects"),
    SectionType.skills: ("skills", "technical skills", "technologies"),
    SectionType.leadership: ("leadership", "activities", "involvement"),
    SectionType.certifications: ("certifications", "certificates"),
    SectionType.awards: ("awards", "honors", "achievements"),
}


def classify_heading(text: str) -> SectionType:
    """Map raw heading text to a SectionType. Returns unknown if no match."""
    norm = text.strip().lower()
    for section_type, names in SECTION_SYNONYMS.items():
        if any(norm == n or norm.startswith(n) for n in names):
            return section_type
    return SectionType.unknown


def _line_font(line: Line) -> float | None:
    """Dominant font size on a line (the heading word, if larger)."""
    sizes = [w.font_size for w in line.words if w.font_size is not None]
    return max(sizes) if sizes else None


def detect_section_headings(lines: list[Line]) -> list[tuple[int, SectionType, float]]:
    """Return (line_index, section_type, confidence) for each detected heading.

    Combines name match, ALL CAPS, larger font, bold, short, and vertical
    isolation into a weighted score; a line is a heading at/above the threshold.
    """
    if not lines:
        return []

    fonts = [f for f in (_line_font(ln) for ln in lines) if f is not None]
    body_font = median(fonts) if fonts else None

    gaps = [
        lines[i + 1].bbox.y0 - lines[i].bbox.y1
        for i in range(len(lines) - 1)
        if lines[i + 1].page == lines[i].page
    ]
    median_gap = median(gaps) if gaps else 0.0

    headings: list[tuple[int, SectionType, float]] = []
    for i, line in enumerate(lines):
        text = line.text
        section_type = classify_heading(text)

        score = 0.0
        if section_type is not SectionType.unknown:
            score += W_NAME
        if text.isupper() and any(c.isalpha() for c in text):
            score += W_CAPS
        lf = _line_font(line)
        if body_font is not None and lf is not None and lf > FONT_LARGER_RATIO * body_font:
            score += W_FONT
        if any(w.bold for w in line.words):
            score += W_BOLD
        if len(line.words) <= SHORT_MAX_WORDS:
            score += W_SHORT

        gap_above = (
            line.bbox.y0 - lines[i - 1].bbox.y1
            if i > 0 and lines[i - 1].page == line.page
            else None
        )
        gap_below = (
            lines[i + 1].bbox.y0 - line.bbox.y1
            if i < len(lines) - 1 and lines[i + 1].page == line.page
            else None
        )
        if median_gap > 0 and (
            (gap_above is not None and gap_above > ISOLATED_GAP_RATIO * median_gap)
            or (gap_below is not None and gap_below > ISOLATED_GAP_RATIO * median_gap)
        ):
            score += W_ISOLATED

        score = min(1.0, score)
        if score >= HEADING_THRESHOLD:
            headings.append((i, section_type, score))
    return headings
