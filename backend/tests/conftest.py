"""Shared fixtures. Build synthetic Word lists so parser tests need no real PDFs."""
from __future__ import annotations

import pytest

from app.schemas.primitives import BBox, Line, Word


def w(text: str, x0: float, y0: float, *, page: int = 1, h: float = 10.0, cw: float = 6.0) -> Word:
    """Convenience: make a Word at (x0, y0) sized by text length."""
    return Word(text=text, bbox=BBox(x0=x0, y0=y0, x1=x0 + len(text) * cw, y1=y0 + h), page=page)


@pytest.fixture
def two_words_same_line() -> list[Word]:
    # "Software" at left, "Engineer" further right, same y -> one line.
    return [w("Software", 72, 100), w("Engineer", 140, 101)]


@pytest.fixture
def header_with_right_aligned_date() -> list[Word]:
    # Title on the left, date pushed to the right margin (big x-gap).
    # Gaps: 20, 254, 22 -> excluding the largest, median{20,22}=21 -> 254 > 3*21.
    return [w("Software", 72, 100), w("Intern", 140, 100), w("May", 430, 100), w("2025", 470, 100)]


@pytest.fixture
def three_lines_normal_spacing() -> list[Word]:
    # Three distinct, normally-spaced lines top-to-bottom.
    return [
        w("Software", 72, 100), w("Engineer", 140, 100),
        w("Backend", 72, 120), w("Systems", 140, 120),
        w("Distributed", 72, 140), w("Teams", 160, 140),
    ]


@pytest.fixture
def shuffled_two_lines() -> list[Word]:
    # Out of reading order: lower line first, right word before left.
    return [
        w("World", 140, 120), w("Hello", 72, 120),
        w("Engineer", 140, 100), w("Software", 72, 100),
    ]


@pytest.fixture
def varying_font_sizes_same_line() -> list[Word]:
    # Tall heading word and a normal word sharing a vertical center (within tol).
    # Heading: y0=98, h=18 -> center 107. Normal: y0=102, h=10 -> center 107.
    return [w("HEADING", 72, 98, h=18), w("note", 200, 102, h=10)]


@pytest.fixture
def evenly_spaced_body_line() -> list[Word]:
    # Body words, uniform spacing -> no right-aligned run.
    return [w("one", 72, 100), w("two", 100, 100), w("three", 128, 100), w("four", 168, 100)]


@pytest.fixture
def single_word_line() -> list[Word]:
    return [w("Lonely", 72, 100)]


@pytest.fixture
def same_y_two_pages() -> list[Word]:
    # Identical y on different pages must never merge.
    return [w("PageOne", 72, 100, page=1), w("PageTwo", 72, 100, page=2)]


@pytest.fixture
def two_word_right_aligned() -> list[Word]:
    # Title left, date pushed to the right margin: single huge gap must split.
    return [w("Intern", 72, 100), w("May2025", 430, 100)]


@pytest.fixture
def two_word_normal_line() -> list[Word]:
    # One normal space between two words: must NOT split.
    return [w("Hello", 72, 100), w("World", 110, 100)]


@pytest.fixture
def touching_words_gaps_005() -> list[Word]:
    # Explicit boxes so inter-word gaps are [0, 0, 5]: first three words touch
    # (each x0 == previous x1), last word starts 5pt after. Must NOT split.
    return [
        Word(text="aa", bbox=BBox(x0=0, y0=100, x1=10, y1=110), page=1),
        Word(text="bb", bbox=BBox(x0=10, y0=100, x1=20, y1=110), page=1),
        Word(text="cc", bbox=BBox(x0=20, y0=100, x1=30, y1=110), page=1),
        Word(text="dd", bbox=BBox(x0=35, y0=100, x1=45, y1=110), page=1),
    ]


@pytest.fixture
def degenerate_height_words() -> list[Word]:
    # Zero-height and inverted (y1<y0) boxes sharing a baseline must still group.
    return [
        Word(text="Flat", bbox=BBox(x0=72, y0=100, x1=100, y1=100), page=1),
        Word(text="Line", bbox=BBox(x0=120, y0=100, x1=150, y1=99), page=1),
    ]


@pytest.fixture
def line_all_font_size_zero() -> Line:
    # Every word has font_size set to a degenerate 0.0 -> treated as PRESENT;
    # big right-aligned gap must still split.
    return Line(
        words=[
            Word(text="Intern", bbox=BBox(x0=72, y0=100, x1=108, y1=110), page=1, font_size=0.0),
            Word(text="May2025", bbox=BBox(x0=430, y0=100, x1=472, y1=110), page=1, font_size=0.0),
        ],
        page=1,
    )


@pytest.fixture
def line_with_none_font_size() -> Line:
    # One word missing font_size -> width/len fallback; normal gap, no split.
    return Line(
        words=[
            Word(text="Hello", bbox=BBox(x0=72, y0=100, x1=102, y1=110), page=1, font_size=11.0),
            Word(text="World", bbox=BBox(x0=110, y0=100, x1=140, y1=110), page=1, font_size=None),
        ],
        page=1,
    )
