"""Unit tests for the pure char->word boxing helper in extract.py.

These exercise ``_chars_to_words`` on synthetic rawdict-style char lists (no
fitz, no real PDFs). The end-to-end PDF extraction path (fitz.open ->
get_text("rawdict") -> _chars_to_words) is verified by manual check rather than
unit tests, per the Phase 1 no-real-PDF guardrail.
"""
from app.parser.extract import _chars_to_words


def _ch(c: str, x0: float, x1: float, *, y0: float = 100.0, y1: float = 110.0) -> dict:
    return {"c": c, "bbox": (x0, y0, x1, y1)}


def test_chars_to_words_splits_on_whitespace_and_propagates_font():
    # "Intern" packed tightly, a WIDE whitespace gap, then "May".
    chars: list[dict] = []
    x = 0.0
    for c in "Intern":
        chars.append(_ch(c, x, x + 6))
        x += 6
    # Wide space: jump far to the right to simulate a right-aligned date gap.
    chars.append(_ch(" ", x, x + 300))
    x += 300
    for c in "May":
        chars.append(_ch(c, x, x + 6))
        x += 6

    words = _chars_to_words(chars, font_size=11.0, bold=True, page=1)

    assert len(words) == 2
    assert [word.text for word in words] == ["Intern", "May"]

    gap = words[1].bbox.x0 - words[0].bbox.x1
    one_char_width = 6.0
    assert gap > one_char_width

    for word in words:
        assert word.font_size == 11.0
        assert word.bold is True
        assert word.page == 1


def test_chars_to_words_unions_char_boxes():
    chars = [_ch("H", 10, 18), _ch("i", 18, 22)]
    words = _chars_to_words(chars, font_size=12.0, bold=False, page=2)
    assert len(words) == 1
    assert words[0].text == "Hi"
    assert words[0].bbox.x0 == 10
    assert words[0].bbox.x1 == 22
    assert words[0].page == 2


def test_chars_to_words_skips_empty_and_whitespace_only():
    chars = [_ch(" ", 0, 5), _ch("\t", 5, 8)]
    assert _chars_to_words(chars, font_size=10.0, bold=False, page=1) == []
