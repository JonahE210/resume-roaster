"""Section classification + multi-signal heading detection tests."""
from app.parser.sections import classify_heading, detect_section_headings
from app.schemas.resume import SectionType


def test_classify_known_headings():
    assert classify_heading("EXPERIENCE") is SectionType.experience
    assert classify_heading("Technical Skills") is SectionType.skills
    assert classify_heading("Work Experience") is SectionType.experience


def test_classify_unknown():
    assert classify_heading("Random Heading") is SectionType.unknown


def test_detects_heading_by_font_not_just_name(heading_detection_lines):
    headings = detect_section_headings(heading_detection_lines)
    found = {idx: (section_type, conf) for idx, section_type, conf in headings}

    # The real heading (index 3) fires with the experience type and high score.
    assert 3 in found
    assert found[3][0] is SectionType.experience
    assert found[3][1] >= 0.6

    # The plain body distractor (index 0) name-matches but must NOT be a heading.
    assert 0 not in found
