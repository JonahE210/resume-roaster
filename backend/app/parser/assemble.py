"""Stage 7 — Assemble the full pipeline into a ParseResult.

This is the one public entrypoint the API calls. It orchestrates the stages and
builds the flat `layout_boxes` list the frontend debug overlay consumes.
"""
from __future__ import annotations

from statistics import median

from app.parser import bullets, entries, extract, fields, lines, sections
from app.parser.lines import detect_right_aligned_run
from app.schemas.primitives import BBox, Line, Word
from app.schemas.resume import Contact, ParseResult, Resume, Section, SectionType


def _line_font(line: Line) -> float | None:
    sizes = [w.font_size for w in line.words if w.font_size is not None]
    return max(sizes) if sizes else None


def _union_lines(section_lines: list[Line]) -> BBox:
    return BBox(
        x0=min(ln.bbox.x0 for ln in section_lines),
        y0=min(ln.bbox.y0 for ln in section_lines),
        x1=max(ln.bbox.x1 for ln in section_lines),
        y1=max(ln.bbox.y1 for ln in section_lines),
    )


def _union_words(words: list[Word]) -> BBox:
    return BBox(
        x0=min(x.bbox.x0 for x in words),
        y0=min(x.bbox.y0 for x in words),
        x1=max(x.bbox.x1 for x in words),
        y1=max(x.bbox.y1 for x in words),
    )


def parse_resume(pdf_bytes: bytes) -> ParseResult:
    """Run the full pipeline: bytes -> structured ParseResult."""
    words, page_count = extract.extract_words(pdf_bytes)
    warnings: list[str] = []
    if page_count > 1:
        warnings.append("MVP targets one-page resumes; extra pages may parse poorly.")

    all_lines = lines.reconstruct_lines(words)
    headings = sections.detect_section_headings(all_lines)

    # Body-median font size, reused for entry emphasis detection.
    fonts = [f for f in (_line_font(ln) for ln in all_lines) if f is not None]
    body_font = median(fonts) if fonts else None

    resume = Resume()

    # Contact: assume it lives above the first detected section heading.
    first_heading_idx = headings[0][0] if headings else len(all_lines)
    header_text = " ".join(ln.text for ln in all_lines[:first_heading_idx])
    contact_fields = fields.find_contact(header_text)
    resume.contact = Contact(**contact_fields)
    # Optional: the first line above the contact block is usually the name.
    if first_heading_idx > 0:
        first_text = all_lines[0].text
        if not any(fields.find_contact(first_text).values()):
            resume.contact.name = first_text

    # Build sections from heading boundaries.
    boundaries = [h[0] for h in headings] + [len(all_lines)]
    section_bodies: list[tuple[Section, list[Line]]] = []
    for (start_idx, section_type, conf), end_idx in zip(headings, boundaries[1:]):
        body = all_lines[start_idx + 1 : end_idx]
        section = Section(
            type=section_type,
            raw_heading=all_lines[start_idx].text,
            confidence=conf,
        )
        if section_type is SectionType.skills:
            section.skills = fields.parse_skills(body)
            section.entries = []
        else:
            section.entries = entries.group_entries(body, base_font_size=body_font)
        section_lines = all_lines[start_idx:end_idx]
        if section_lines:
            section.bbox = _union_lines(section_lines)
        resume.sections.append(section)
        section_bodies.append((section, body))

    # Flat layout boxes for the debug overlay (color-coded on the frontend).
    # DEFERRED to Phase 6 (overlay-only, no metric impact):
    #   #3a: build layout_boxes per section and tag bullets with that section's
    #        base_indent via is_bullet_line(ln, body_indent=base_indent).
    #   #3b: restrict "date" boxes to entry header lines only (not every line).
    #   #4:  when bullets precede the first header, union their bboxes into
    #        entry 0's bbox.
    heading_conf = {idx: conf for idx, _, conf in headings}
    boxes: list[dict] = []
    for i, ln in enumerate(all_lines):
        if i in heading_conf:
            kind, conf = "section", heading_conf[i]
        elif bullets.is_bullet_line(ln):
            kind, conf = "bullet", 1.0
        else:
            kind, conf = "line", 1.0
        boxes.append(
            {
                "kind": kind,
                "confidence": conf,
                "text": ln.text,
                "page": ln.page,
                "bbox": ln.bbox.model_dump(),
            }
        )

    # Entry boxes (from the structured result) and right-aligned date runs.
    for section, body in section_bodies:
        page = body[0].page if body else 1
        for entry in section.entries:
            if entry.bbox is not None:
                boxes.append(
                    {
                        "kind": "entry",
                        "confidence": entry.confidence,
                        "text": entry.title or "",
                        "page": page,
                        "bbox": entry.bbox.model_dump(),
                    }
                )
    for ln in all_lines:
        run = detect_right_aligned_run(ln)
        if run:
            boxes.append(
                {
                    "kind": "date",
                    "confidence": 1.0,
                    "text": " ".join(x.text for x in run),
                    "page": ln.page,
                    "bbox": _union_words(run).model_dump(),
                }
            )
    resume.layout_boxes = boxes

    return ParseResult(resume=resume, page_count=page_count, warnings=warnings)
