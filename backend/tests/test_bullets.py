"""Bullet detection + ownership tests. Detection works now; ownership is Phase 2."""
import pytest

from app.parser.bullets import strip_marker


def test_strip_marker():
    assert strip_marker("• Built a thing") == "Built a thing"
    assert strip_marker("- Did the work") == "Did the work"
    assert strip_marker("No marker here") == "No marker here"


@pytest.mark.xfail(reason="Phase 2: attach bullets to nearest preceding entry")
def test_bullet_ownership():
    raise AssertionError("Bullets must attach to the correct entry; this is the headline metric.")


@pytest.mark.xfail(reason="Phase 2: merge wrapped continuation lines into one bullet")
def test_merges_wrapped_bullet_lines():
    raise AssertionError("A bullet spanning two visual lines should be one string.")
