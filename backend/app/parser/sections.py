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

from app.schemas.primitives import Line
from app.schemas.resume import SectionType

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


def detect_section_headings(lines: list[Line]) -> list[tuple[int, SectionType, float]]:
    """Return (line_index, section_type, confidence) for each detected heading.

    TODO(phase2): implement the multi-signal scoring described in the docstring.
    Stub uses name-matching only.
    """
    headings: list[tuple[int, SectionType, float]] = []
    for i, line in enumerate(lines):
        section_type = classify_heading(line.text)
        if section_type is not SectionType.unknown:
            headings.append((i, section_type, 0.6))  # low confidence until scored
    return headings
