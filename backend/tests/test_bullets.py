"""Bullet detection + ownership tests. Ownership/merge are the headline metric."""
from app.parser.bullets import assign_bullets, strip_marker


def test_strip_marker():
    assert strip_marker("• Built a thing") == "Built a thing"
    assert strip_marker("- Did the work") == "Did the work"
    assert strip_marker("No marker here") == "No marker here"


def test_strip_marker_uncommon_glyphs():
    assert strip_marker("» Improved performance") == "Improved performance"
    assert strip_marker("‣ Shipped a feature") == "Shipped a feature"


def test_uncommon_marker_bullets_not_merged():
    # A non-standard marker glyph must still be recognized so consecutive bullets
    # stay separate (and aren't mis-merged as a wrapped continuation).
    from app.schemas.primitives import BBox, Line, Word

    def bullet(marker: str, text: str, y: float) -> Line:
        return Line(
            words=[
                Word(text=marker, bbox=BBox(x0=84, y0=y, x1=90, y1=y + 10), page=1),
                Word(text=text, bbox=BBox(x0=96, y0=y, x1=200, y1=y + 10), page=1),
            ],
            page=1,
        )

    lines = [bullet("»", "First", 100), bullet("»", "Second", 115)]
    result = assign_bullets(lines, [0], body_indent=72.0)
    assert result[0] == ["First", "Second"]


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
