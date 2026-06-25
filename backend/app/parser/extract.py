"""Stage 1 — PDF word extraction with bounding boxes (PyMuPDF).

Output: a flat list[Word]. This is the only module that touches PyMuPDF; everything
downstream works on our own primitives so the rest of the pipeline is testable
without real PDFs.
"""
from __future__ import annotations

from app.schemas.primitives import BBox, Word


def _chars_to_words(
    chars: list[dict], *, font_size: float, bold: bool, page: int
) -> list[Word]:
    """Assemble Words from a rawdict span's per-character boxes.

    Pure helper (plain dicts/tuples, no fitz): accumulate consecutive
    non-whitespace chars and flush a Word on whitespace or end-of-span. Each
    Word's bbox is the union of its char bboxes; text is the joined chars.
    Empty/whitespace-only accumulations are skipped.
    """
    words: list[Word] = []
    buf: list[dict] = []

    def flush() -> None:
        if not buf:
            return
        text = "".join(c["c"] for c in buf)
        if text.strip():
            x0 = min(c["bbox"][0] for c in buf)
            y0 = min(c["bbox"][1] for c in buf)
            x1 = max(c["bbox"][2] for c in buf)
            y1 = max(c["bbox"][3] for c in buf)
            words.append(
                Word(
                    text=text,
                    bbox=BBox(x0=x0, y0=y0, x1=x1, y1=y1),
                    page=page,
                    font_size=font_size,
                    bold=bold,
                )
            )
        buf.clear()

    for ch in chars:
        if ch["c"].isspace():
            flush()
        else:
            buf.append(ch)
    flush()
    return words


def extract_words(pdf_bytes: bytes) -> tuple[list[Word], int]:
    """Extract every word with its bbox and font signals.

    Returns (words, page_count).

    Uses "rawdict" extraction so each span exposes per-character bboxes; words are
    assembled by unioning consecutive non-whitespace char boxes (see
    ``_chars_to_words``). This preserves the true horizontal gaps the downstream
    right-aligned-run detector relies on. Font signals (font_size, bold) come from
    the span and propagate to every word built from it. Page index is 1-based.
    """
    import fitz  # PyMuPDF — imported lazily so tests can stub this module

    words: list[Word] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = doc.page_count
    for page_index in range(page_count):
        page = doc[page_index]
        data = page.get_text("rawdict")
        for block in data.get("blocks", []):
            # Image blocks have no "lines"; skip them.
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    chars = span.get("chars")
                    if not chars:
                        continue
                    font_size = float(span.get("size", 0.0))
                    flags = span.get("flags", 0)
                    font = span.get("font", "")
                    bold = bool(flags & 2**4) or "bold" in font.lower()
                    words.extend(
                        _chars_to_words(
                            chars,
                            font_size=font_size,
                            bold=bold,
                            page=page_index + 1,
                        )
                    )
    doc.close()
    return words, page_count
