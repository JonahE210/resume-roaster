"""Shared fixtures. Build synthetic Word lists so parser tests need no real PDFs."""
from __future__ import annotations

import pytest

from app.schemas.primitives import BBox, Word


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
    return [w("Software", 72, 100), w("Intern", 140, 100), w("May", 430, 100), w("2025", 470, 100)]
