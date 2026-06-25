"""Stage 7 — Assemble the full pipeline into a ParseResult.

This is the one public entrypoint the API calls. It orchestrates the stages and
builds the flat `layout_boxes` list the frontend debug overlay consumes.
"""
from __future__ import annotations

from app.parser import bullets, entries, extract, fields, lines, sections
from app.schemas.resume import Contact, ParseResult, Resume, Section, SectionType


def parse_resume(pdf_bytes: bytes) -> ParseResult:
    """Run the full pipeline: bytes -> structured ParseResult.

    The orchestration below is intentionally skeletal. As each stage's TODOs are
    implemented, this wiring tightens. It already runs end-to-end on the stubs.
    """
    words, page_count = extract.extract_words(pdf_bytes)
    warnings: list[str] = []
    if page_count > 1:
        warnings.append("MVP targets one-page resumes; extra pages may parse poorly.")

    all_lines = lines.reconstruct_lines(words)
    headings = sections.detect_section_headings(all_lines)

    resume = Resume()

    # Contact: assume it lives above the first detected section heading.
    first_heading_idx = headings[0][0] if headings else len(all_lines)
    header_text = " ".join(ln.text for ln in all_lines[:first_heading_idx])
    contact_fields = fields.find_contact(header_text)
    resume.contact = Contact(**contact_fields)

    # Build sections from heading boundaries.
    boundaries = [h[0] for h in headings] + [len(all_lines)]
    for (start_idx, section_type, conf), end_idx in zip(headings, boundaries[1:]):
        body = all_lines[start_idx + 1 : end_idx]
        section = Section(
            type=section_type,
            raw_heading=all_lines[start_idx].text,
            confidence=conf,
        )
        if section_type is SectionType.skills:
            # TODO(phase2): parse "Languages: Java, Python" into section.skills.
            section.entries = []
        else:
            section.entries = entries.group_entries(body)
        resume.sections.append(section)

    # Flat layout boxes for the debug overlay (color-coded on the frontend).
    for ln in all_lines:
        kind = "bullet" if bullets.is_bullet_line(ln) else "line"
        resume.layout_boxes.append(
            {"kind": kind, "text": ln.text, "page": ln.page, "bbox": ln.bbox.model_dump()}
        )

    return ParseResult(resume=resume, page_count=page_count, warnings=warnings)
