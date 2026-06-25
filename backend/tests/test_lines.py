"""Phase 1 tests for line reconstruction."""
from app.parser.lines import detect_right_aligned_run, reconstruct_lines


def test_returns_empty_on_no_words():
    assert reconstruct_lines([]) == []


def test_groups_words_on_same_line(two_words_same_line):
    lines = reconstruct_lines(two_words_same_line)
    assert len(lines) == 1
    assert lines[0].text == "Software Engineer"


def test_splits_right_aligned_date(header_with_right_aligned_date):
    lines = reconstruct_lines(header_with_right_aligned_date)
    run = detect_right_aligned_run(lines[0])
    assert run is not None
    assert " ".join(word.text for word in run) == "May 2025"


def test_groups_multiple_lines(three_lines_normal_spacing):
    lines = reconstruct_lines(three_lines_normal_spacing)
    assert len(lines) == 3
    assert [line.text for line in lines] == [
        "Software Engineer",
        "Backend Systems",
        "Distributed Teams",
    ]


def test_words_out_of_order_are_sorted(shuffled_two_lines):
    lines = reconstruct_lines(shuffled_two_lines)
    assert len(lines) == 2
    assert [line.text for line in lines] == ["Software Engineer", "Hello World"]


def test_varying_font_sizes_same_line(varying_font_sizes_same_line):
    lines = reconstruct_lines(varying_font_sizes_same_line)
    assert len(lines) == 1
    assert lines[0].text == "HEADING note"


def test_no_right_aligned_run(evenly_spaced_body_line):
    lines = reconstruct_lines(evenly_spaced_body_line)
    assert detect_right_aligned_run(lines[0]) is None


def test_single_word_line_has_no_run(single_word_line):
    lines = reconstruct_lines(single_word_line)
    assert detect_right_aligned_run(lines[0]) is None


def test_multi_page_not_merged(same_y_two_pages):
    lines = reconstruct_lines(same_y_two_pages)
    assert len(lines) == 2
    assert [line.page for line in lines] == [1, 2]
    assert [line.text for line in lines] == ["PageOne", "PageTwo"]


def test_two_word_right_aligned_splits(two_word_right_aligned):
    lines = reconstruct_lines(two_word_right_aligned)
    run = detect_right_aligned_run(lines[0])
    assert run is not None
    assert " ".join(word.text for word in run) == "May2025"


def test_two_word_normal_line_no_split(two_word_normal_line):
    lines = reconstruct_lines(two_word_normal_line)
    assert detect_right_aligned_run(lines[0]) is None


def test_touching_words_no_false_positive(touching_words_gaps_005):
    lines = reconstruct_lines(touching_words_gaps_005)
    assert detect_right_aligned_run(lines[0]) is None


def test_degenerate_heights_group_into_one_line(degenerate_height_words):
    lines = reconstruct_lines(degenerate_height_words)
    assert len(lines) == 1
    assert lines[0].text == "Flat Line"


def test_font_size_guard_uses_none_semantics(
    line_all_font_size_zero, line_with_none_font_size
):
    # font_size=0.0 is "present" (None-semantics), so the font-based estimate is
    # used (floored to ABS_MIN_GAP) and a big right-aligned gap still splits.
    run = detect_right_aligned_run(line_all_font_size_zero)
    assert run is not None
    assert " ".join(word.text for word in run) == "May2025"

    # A missing (None) font size falls back to the width/len estimate cleanly.
    assert detect_right_aligned_run(line_with_none_font_size) is None
