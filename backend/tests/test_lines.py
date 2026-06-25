"""Phase 1 tests for line reconstruction. The xfails are your TODO checklist."""
import pytest

from app.parser.lines import reconstruct_lines


def test_returns_empty_on_no_words():
    assert reconstruct_lines([]) == []


@pytest.mark.xfail(reason="Phase 1: implement y-clustering in lines.reconstruct_lines")
def test_groups_words_on_same_line(two_words_same_line):
    lines = reconstruct_lines(two_words_same_line)
    assert len(lines) == 1
    assert lines[0].text == "Software Engineer"


@pytest.mark.xfail(reason="Phase 2: implement detect_right_aligned_run")
def test_splits_right_aligned_date(header_with_right_aligned_date):
    from app.parser.lines import detect_right_aligned_run

    lines = reconstruct_lines(header_with_right_aligned_date)
    run = detect_right_aligned_run(lines[0])
    assert run is not None
    assert " ".join(word.text for word in run) == "May 2025"
