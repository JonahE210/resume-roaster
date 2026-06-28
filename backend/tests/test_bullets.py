"""Bullet detection + ownership tests. Ownership/merge are the headline metric."""
from app.parser.bullets import assign_bullets, strip_marker


def test_strip_marker():
    assert strip_marker("• Built a thing") == "Built a thing"
    assert strip_marker("- Did the work") == "Did the work"
    assert strip_marker("No marker here") == "No marker here"


def test_bullet_ownership(ownership_section_lines):
    # Headers at indices 0 and 3; each owns the two bullets beneath it.
    result = assign_bullets(ownership_section_lines, [0, 3], body_indent=72.0)
    assert result[0] == ["A-one", "A-two"]
    assert result[1] == ["B-one", "B-two"]


def test_merges_wrapped_bullet_lines(wrapped_bullet_lines):
    result = assign_bullets(wrapped_bullet_lines, [0], body_indent=72.0)
    assert len(result) == 1
    assert len(result[0]) == 1
    assert result[0][0] == "Built a system that handles requests"
