"""Run the parser over every labeled sample and write a metrics report.

Usage:
    python run_eval.py            # from the eval/ directory

Requires the backend importable. Easiest: run with the backend venv active and
`PYTHONPATH` including ../backend, or `pip install -e ../backend` first.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

import metrics

EVAL_DIR = Path(__file__).parent
SAMPLES = EVAL_DIR / "samples"
LABELS = EVAL_DIR / "labels"


def _load_parser():
    sys.path.insert(0, str(EVAL_DIR.parent / "backend"))
    from app.parser.assemble import parse_resume  # noqa: WPS433

    return parse_resume


def _pred_to_compare_shapes(parse_result) -> tuple[list[str], dict[str, int], list[dict]]:
    """Flatten a ParseResult into the shapes metrics.py expects."""
    resume = parse_result.resume
    pred_types = [s.type.value for s in resume.sections]
    pred_counts = {s.type.value: len(s.entries) for s in resume.sections}
    pred_bullets = [
        {"entry_key": (e.title or e.organization or ""), "bullet": b}
        for s in resume.sections
        for e in s.entries
        for b in e.bullets
    ]
    return pred_types, pred_counts, pred_bullets


def _gold_to_compare_shapes(label: dict) -> tuple[list[str], dict[str, int], list[dict]]:
    gold_types = [s["type"] for s in label.get("sections", [])]
    gold_counts: dict[str, int] = {}
    gold_bullets: list[dict] = []
    for s in label.get("sections", []):
        entries = s.get("entries", [])
        gold_counts[s["type"]] = len(entries)
        for e in entries:
            key = e.get("title") or e.get("organization") or ""
            for b in e.get("bullets", []):
                gold_bullets.append({"entry_key": key, "bullet": b})
    return gold_types, gold_counts, gold_bullets


def main() -> int:
    label_files = sorted(p for p in LABELS.glob("*.json") if not p.name.startswith("_"))
    if not label_files:
        print("No labels found. Add samples/*.pdf and labels/*.json first.")
        print("See eval/README.md for the workflow.")
        return 0

    parse_resume = _load_parser()
    rows, f1s, entry_accs, bullet_accs = [], [], [], []

    for label_path in label_files:
        sample = SAMPLES / f"{label_path.stem}.pdf"
        if not sample.exists():
            print(f"skip {label_path.name}: no matching {sample.name}")
            continue
        label = json.loads(label_path.read_text())
        result = parse_resume(sample.read_bytes())

        p_types, p_counts, p_bullets = _pred_to_compare_shapes(result)
        g_types, g_counts, g_bullets = _gold_to_compare_shapes(label)

        f1 = metrics.section_f1(p_types, g_types)["f1"]
        ea = metrics.entry_grouping_accuracy(p_counts, g_counts)
        ba = metrics.bullet_attribution_accuracy(p_bullets, g_bullets)
        f1s.append(f1); entry_accs.append(ea); bullet_accs.append(ba)
        rows.append((label_path.stem, f1, ea, ba))

    _write_report(rows, f1s, entry_accs, bullet_accs)
    print(f"Done. {len(rows)} samples. See REPORT.md")
    return 0


def _write_report(rows, f1s, entry_accs, bullet_accs) -> None:
    lines = ["# Eval report", "", "| Sample | Section F1 | Entry acc | Bullet attr |",
             "|--------|-----------|-----------|-------------|"]
    for name, f1, ea, ba in rows:
        lines.append(f"| {name} | {f1:.2f} | {ea:.2f} | {ba:.2f} |")
    if rows:
        lines += ["| **mean** | "
                  f"**{mean(f1s):.2f}** | **{mean(entry_accs):.2f}** | "
                  f"**{mean(bullet_accs):.2f}** |"]
    (EVAL_DIR / "REPORT.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
