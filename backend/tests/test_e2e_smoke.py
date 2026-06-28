"""Synthetic-PDF end-to-end smoke test (skippable when PyMuPDF is unavailable).

This is NOT an accuracy test — it only proves the full pipeline runs on a real
in-memory PDF and produces a sane structure. The PDF is generated in memory and
never written/committed.
"""
import sys
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

from app.parser.assemble import parse_resume  # noqa: E402


def _build_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "EXPERIENCE", fontsize=16)
    page.insert_text((72, 140), "Software Engineer", fontsize=11)
    page.insert_text((430, 140), "May 2025 - Aug 2025", fontsize=11)
    page.insert_text((72, 160), "Google", fontsize=11)
    page.insert_text((90, 180), "\u2022 Built scalable services", fontsize=11)
    page.insert_text((90, 200), "\u2022 Improved latency by 40%", fontsize=11)
    pdf = doc.tobytes()
    doc.close()
    return pdf


def test_synthetic_pdf_end_to_end():
    try:
        pdf = _build_pdf()
    except Exception as exc:  # noqa: BLE001 - fitz drawing API may differ by version
        pytest.skip(f"fitz rendering API differs: {exc}")

    result = parse_resume(pdf)

    assert result.page_count == 1
    experience = [s for s in result.resume.sections if s.type.value == "experience"]
    assert experience, "expected an experience section"
    section = experience[0]
    assert len(section.entries) >= 1
    assert any(len(e.bullets) >= 1 for e in section.entries)

    # Optional: the eval glue accepts this real result without error.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eval"))
    import run_eval  # noqa: E402

    shapes = run_eval._pred_to_compare_shapes(result)
    assert len(shapes) == 3
