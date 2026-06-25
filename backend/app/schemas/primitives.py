"""Low-level geometry primitives produced by the extraction stage.

Everything downstream reasons over these. Keep them dumb and serializable.
"""
from __future__ import annotations

from pydantic import BaseModel


class BBox(BaseModel):
    """Axis-aligned bounding box in PDF coordinate space (origin top-left)."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2


class Word(BaseModel):
    """A single PDF word with position and (when available) font signals."""

    text: str
    bbox: BBox
    page: int
    font_size: float | None = None
    bold: bool | None = None


class Line(BaseModel):
    """Words grouped onto one visual line, left-to-right.

    `words` preserves horizontal order so we can detect right-aligned runs
    (e.g. dates) by looking at large x-gaps.
    """

    words: list[Word]
    page: int

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def bbox(self) -> BBox:
        return BBox(
            x0=min(w.bbox.x0 for w in self.words),
            y0=min(w.bbox.y0 for w in self.words),
            x1=max(w.bbox.x1 for w in self.words),
            y1=max(w.bbox.y1 for w in self.words),
        )
