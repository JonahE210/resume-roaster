"""Section classification tests. classify_heading works now; detection scoring is Phase 2."""
import pytest

from app.parser.sections import classify_heading
from app.schemas.resume import SectionType


def test_classify_known_headings():
    assert classify_heading("EXPERIENCE") is SectionType.experience
    assert classify_heading("Technical Skills") is SectionType.skills
    assert classify_heading("Work Experience") is SectionType.experience


def test_classify_unknown():
    assert classify_heading("Random Heading") is SectionType.unknown


@pytest.mark.xfail(reason="Phase 2: multi-signal heading detection (font/caps/spacing)")
def test_detects_heading_by_font_not_just_name():
    raise AssertionError("Implement detect_section_headings scoring with font signals.")
