"""Generate a label *stub* from the parser's own output for a sample PDF.

This is a labeling accelerator, NOT ground truth. It runs the parser over a PDF
and serializes the result into the labels/_TEMPLATE.json shape so you can correct
it by hand instead of typing a label from scratch.

Usage:
    python make_label_stub.py <sample.pdf> [--force] [--stdout]

  --force   overwrite an existing label (default: refuse, to protect hand labels)
  --stdout  print the JSON instead of writing labels/<stem>.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).parent
LABELS = EVAL_DIR / "labels"

REMINDER = (
    "Auto-generated from the parser - CORRECT BY HAND before using as ground "
    "truth (fix section types, entry boundaries, bullet text/attribution, skills)."
)


def _load_parser():
    """Import the parser the same way run_eval does (backend on sys.path)."""
    sys.path.insert(0, str(EVAL_DIR.parent / "backend"))
    from app.parser.assemble import parse_resume  # noqa: WPS433

    return parse_resume


def label_from_result(result) -> dict:
    """Serialize a ParseResult into the _TEMPLATE.json label shape."""
    r = result.resume
    out = {
        "_comment": REMINDER,
        "contact": {k: v for k, v in r.contact.model_dump().items() if v},
    }
    secs = []
    for s in r.sections:
        d = {"type": s.type.value}
        if s.skills:
            d["skills"] = s.skills
        else:
            d["entries"] = [
                {
                    k: v
                    for k, v in {
                        "title": e.title,
                        "organization": e.organization,
                        "location": e.location,
                        "start_date": e.start_date,
                        "end_date": e.end_date,
                        "bullets": e.bullets,
                    }.items()
                    if v not in (None, [], "")
                }
                for e in s.entries
            ]
        secs.append(d)
    out["sections"] = secs
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a hand-correctable label stub from parser output."
    )
    parser.add_argument("pdf", help="Path to the sample PDF.")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite an existing label."
    )
    parser.add_argument(
        "--stdout", action="store_true", help="Print JSON instead of writing a file."
    )
    args = parser.parse_args(argv)

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        print(f"error: {pdf_path} not found")
        return 1

    parse_resume = _load_parser()
    result = parse_resume(pdf_path.read_bytes())
    text = json.dumps(label_from_result(result), indent=2)

    if args.stdout:
        print(text)
        return 0

    out_path = LABELS / f"{pdf_path.stem}.json"
    if out_path.exists() and not args.force:
        print(
            f"error: {out_path} already exists; pass --force to overwrite "
            "(never clobber hand labels)"
        )
        return 1

    out_path.write_text(text + "\n")
    print(f"Wrote {out_path}; review against the PDF.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
