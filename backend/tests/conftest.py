"""Shared fixtures. Build synthetic Word lists so parser tests need no real PDFs."""
from __future__ import annotations

import pytest

from app.schemas.primitives import BBox, Line, Word


def w(
    text: str,
    x0: float,
    y0: float,
    *,
    page: int = 1,
    h: float = 10.0,
    cw: float = 6.0,
    font_size: float | None = None,
    bold: bool | None = None,
) -> Word:
    """Convenience: make a Word at (x0, y0) sized by text length.

    Optional font_size/bold let fixtures exercise heading/emphasis signals.
    """
    return Word(
        text=text,
        bbox=BBox(x0=x0, y0=y0, x1=x0 + len(text) * cw, y1=y0 + h),
        page=page,
        font_size=font_size,
        bold=bold,
    )


def _line(words: list[Word], page: int = 1) -> Line:
    """Build a Line from already-positioned words (left-to-right)."""
    return Line(words=words, page=page)


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


# --- Phase 2: structure-detection fixtures -------------------------------------


@pytest.fixture
def heading_detection_lines() -> list[Line]:
    """A real ALL-CAPS/bold/larger/isolated heading plus a name-matching but
    plain body distractor ("Experience building ...") that must NOT fire."""
    distractor = _line([
        w("Experience", 72, 100, font_size=10.0),
        w("building", 134, 100, font_size=10.0),
        w("large", 196, 100, font_size=10.0),
        w("scale", 240, 100, font_size=10.0),
        w("distributed", 280, 100, font_size=10.0),
        w("systems", 350, 100, font_size=10.0),
    ])
    body1 = _line([
        w("Worked", 72, 114, font_size=10.0),
        w("on", 120, 114, font_size=10.0),
        w("things", 140, 114, font_size=10.0),
    ])
    body2 = _line([
        w("More", 72, 128, font_size=10.0),
        w("normal", 110, 128, font_size=10.0),
        w("text", 160, 128, font_size=10.0),
    ])
    heading = _line([w("EXPERIENCE", 72, 180, h=16.0, font_size=16.0, bold=True)])
    after = _line([
        w("Senior", 72, 210, font_size=10.0),
        w("Engineer", 120, 210, font_size=10.0),
    ])
    return [distractor, body1, body2, heading, after]


@pytest.fixture
def experience_section_lines() -> list[Line]:
    """One entry: header (title + right-aligned date) + org line + two bullets."""
    header = _line([
        w("Software", 72, 100), w("Engineer", 140, 100),
        w("May", 430, 100), w("2025", 470, 100),
    ])
    org = _line([w("Google", 72, 115)])
    bullet1 = _line([
        w("\u2022", 90, 130), w("Built", 100, 130),
        w("scalable", 135, 130), w("services", 188, 130),
    ])
    bullet2 = _line([
        w("\u2022", 90, 145), w("Improved", 100, 145),
        w("latency", 155, 145), w("by", 200, 145), w("40%", 218, 145),
    ])
    return [header, org, bullet1, bullet2]


@pytest.fixture
def two_jobs_section_lines() -> list[Line]:
    """Two job headers (each with its own right-aligned date), one bullet each."""
    header1 = _line([
        w("Senior", 72, 100), w("Engineer", 120, 100),
        w("Jan", 430, 100), w("2020", 470, 100),
    ])
    bullet1 = _line([w("\u2022", 90, 115), w("Did", 100, 115), w("stuff", 135, 115)])
    header2 = _line([
        w("Junior", 72, 130), w("Engineer", 120, 130),
        w("Jun", 430, 130), w("2018", 470, 130),
    ])
    bullet2 = _line([w("\u2022", 90, 145), w("Other", 100, 145), w("work", 150, 145)])
    return [header1, bullet1, header2, bullet2]


@pytest.fixture
def ownership_section_lines() -> list[Line]:
    """Two headers at indices 0 and 3, with two bullets under each."""
    header_a = _line([
        w("Alpha", 72, 100), w("Role", 120, 100),
        w("Jan", 430, 100), w("2020", 470, 100),
    ])
    a1 = _line([w("\u2022", 90, 115), w("A-one", 100, 115)])
    a2 = _line([w("\u2022", 90, 130), w("A-two", 100, 130)])
    header_b = _line([
        w("Beta", 72, 145), w("Role", 120, 145),
        w("Jun", 430, 145), w("2019", 470, 145),
    ])
    b1 = _line([w("\u2022", 90, 160), w("B-one", 100, 160)])
    b2 = _line([w("\u2022", 90, 175), w("B-two", 100, 175)])
    return [header_a, a1, a2, header_b, b1, b2]


@pytest.fixture
def wrapped_bullet_lines() -> list[Line]:
    """A bullet that wraps onto a marker-less, hanging-indented second line."""
    header = _line([
        w("Engineer", 72, 100), w("Role", 140, 100),
        w("Jan", 430, 100), w("2020", 470, 100),
    ])
    bullet = _line([
        w("\u2022", 90, 115), w("Built", 100, 115),
        w("a", 135, 115), w("system", 145, 115), w("that", 195, 115),
    ])
    continuation = _line([w("handles", 100, 130), w("requests", 150, 130)])
    return [header, bullet, continuation]


@pytest.fixture
def skills_section_lines() -> list[Line]:
    """Two 'Label: a, b' skill lines."""
    line1 = _line([w("Languages:", 72, 100), w("Java,", 140, 100), w("Python", 175, 100)])
    line2 = _line([w("Frameworks:", 72, 115), w("React,", 150, 115), w("FastAPI", 190, 115)])
    return [line1, line2]


@pytest.fixture
def bold_org_section_lines() -> list[Line]:
    """Header + right-aligned date, then a BOLD single-word org line at base
    indent (no date), then two bullets. The bold org must NOT split into a
    second entry (regression for the emphasis-only-boundary bug)."""
    header = _line([
        w("Software", 72, 100, font_size=11.0, bold=True),
        w("Engineer", 140, 100, font_size=11.0, bold=True),
        w("May", 430, 100, font_size=11.0),
        w("2025", 470, 100, font_size=11.0),
    ])
    org = _line([w("Google", 72, 115, font_size=11.0, bold=True)])
    bullet1 = _line([
        w("\u2022", 90, 130), w("Built", 100, 130),
        w("scalable", 135, 130), w("services", 188, 130),
    ])
    bullet2 = _line([
        w("\u2022", 90, 145), w("Improved", 100, 145),
        w("latency", 155, 145), w("by", 200, 145), w("40%", 218, 145),
    ])
    return [header, org, bullet1, bullet2]


@pytest.fixture
def bold_two_jobs_section_lines() -> list[Line]:
    """Two BOLD job headers, each with its own right-aligned date and one
    bullet. These must still split via the date-run rule despite being bold."""
    header1 = _line([
        w("Senior", 72, 100, font_size=11.0, bold=True),
        w("Engineer", 120, 100, font_size=11.0, bold=True),
        w("Jan", 430, 100, font_size=11.0),
        w("2020", 470, 100, font_size=11.0),
    ])
    bullet1 = _line([w("\u2022", 90, 115), w("Did", 100, 115), w("stuff", 135, 115)])
    header2 = _line([
        w("Junior", 72, 130, font_size=11.0, bold=True),
        w("Engineer", 120, 130, font_size=11.0, bold=True),
        w("Jun", 430, 130, font_size=11.0),
        w("2018", 470, 130, font_size=11.0),
    ])
    bullet2 = _line([w("\u2022", 90, 145), w("Other", 100, 145), w("work", 150, 145)])
    return [header1, bullet1, header2, bullet2]
