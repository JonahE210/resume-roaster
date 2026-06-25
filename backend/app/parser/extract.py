"""Stage 1 — PDF word extraction with bounding boxes (PyMuPDF).

Output: a flat list[Word]. This is the only module that touches PyMuPDF; everything
downstream works on our own primitives so the rest of the pipeline is testable
without real PDFs.
"""
from __future__ import annotations

from app.schemas.primitives import BBox, Word


def extract_words(pdf_bytes: bytes) -> tuple[list[Word], int]:
    """Extract every word with its bbox and font signals.

    Returns (words, page_count).

    Implementation notes for Phase 1:
      - Use `fitz.open(stream=pdf_bytes, filetype="pdf")`.
      - `page.get_text("words")` gives (x0, y0, x1, y1, word, block, line, word_no).
        Fast, but no font size/weight.
      - For font_size/bold, use `page.get_text("dict")` spans and match by bbox,
        OR parse spans directly into Words. Font size is a strong section-header
        signal, so it's worth getting.
      - Set page index (1-based) on each Word.
    """
    import fitz  # PyMuPDF — imported lazily so tests can stub this module

    words: list[Word] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = doc.page_count
    for page_index in range(page_count):
        page = doc[page_index]
        # TODO(phase1): switch to "dict" extraction to capture font_size/bold.
        for x0, y0, x1, y1, text, *_ in page.get_text("words"):
            if not text.strip():
                continue
            words.append(
                Word(
                    text=text,
                    bbox=BBox(x0=x0, y0=y0, x1=x1, y1=y1),
                    page=page_index + 1,
                )
            )
    doc.close()
    return words, page_count
