"""Hand-computed tests for eval/metrics.py plus run_eval glue/format tests.

eval/ is outside the backend package (pythonpath=["."] is rooted at backend/),
so insert it explicitly before importing the eval modules.
"""
import json
import sys
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parents[2] / "eval"  # tests -> backend -> repo root
sys.path.insert(0, str(EVAL))

import metrics  # eval/metrics.py  # noqa: E402
import run_eval  # eval/run_eval.py  # noqa: E402

from app.schemas.resume import (  # noqa: E402
    Entry,
    ParseResult,
    Resume,
    Section,
    SectionType,
)


# --- section_f1 ---------------------------------------------------------------


def test_section_f1_perfect():
    r = metrics.section_f1(
        ["experience", "skills", "education"], ["experience", "skills", "education"]
    )
    assert r == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_section_f1_recall_miss():
    r = metrics.section_f1(
        ["experience", "skills"], ["experience", "skills", "education"]
    )
    assert r["precision"] == 1.0
    assert r["recall"] == pytest.approx(2 / 3)
    assert r["f1"] == pytest.approx(0.8)


def test_section_f1_precision_miss():
    r = metrics.section_f1(
        ["experience", "skills", "projects"], ["experience", "skills"]
    )
    assert r["precision"] == pytest.approx(2 / 3)
    assert r["recall"] == 1.0
    assert r["f1"] == pytest.approx(0.8)


def test_section_f1_disjoint():
    assert metrics.section_f1(["projects"], ["experience"])["f1"] == 0.0


def test_section_f1_one_sided_empty():
    r = metrics.section_f1([], ["experience"])
    assert r["precision"] == 0.0
    assert r["recall"] == 0.0
    assert r["f1"] == 0.0


def test_section_f1_empty_empty_is_perfect():
    # §2.4 fix: empty/empty is a vacuous perfect match (was 0.0 before Phase 3).
    assert metrics.section_f1([], []) == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_section_f1_set_dedup():
    assert metrics.section_f1(["experience", "experience"], ["experience"])["f1"] == 1.0


# --- entry_grouping_accuracy --------------------------------------------------


def test_entry_grouping_perfect():
    assert (
        metrics.entry_grouping_accuracy(
            {"experience": 2, "projects": 1}, {"experience": 2, "projects": 1}
        )
        == 1.0
    )


def test_entry_grouping_partial():
    gold = {"experience": 2, "projects": 1, "education": 1}
    pred = {"experience": 2, "projects": 2, "education": 1}
    assert metrics.entry_grouping_accuracy(pred, gold) == pytest.approx(2 / 3)


def test_entry_grouping_missing_predicted_section_penalized():
    # pred.get("skills") is None, which != 0, so the 0-entry gold section misses.
    assert (
        metrics.entry_grouping_accuracy({"experience": 1}, {"experience": 1, "skills": 0})
        == 0.5
    )


def test_entry_grouping_empty_gold():
    assert metrics.entry_grouping_accuracy({}, {}) == 1.0


def test_entry_grouping_extra_predicted_ignored():
    assert (
        metrics.entry_grouping_accuracy({"experience": 1, "awards": 3}, {"experience": 1})
        == 1.0
    )


# --- bullet_attribution_accuracy ----------------------------------------------


def test_bullet_attribution_perfect_with_normalization():
    gold = [
        {"entry_key": "Software Engineer", "bullet": "Built services"},
        {"entry_key": "Software Engineer", "bullet": "Improved latency"},
        {"entry_key": "Data Analyst", "bullet": "Wrote dashboards"},
    ]
    pred = [
        {"entry_key": "software engineer", "bullet": "built services"},
        {"entry_key": "  Software   Engineer ", "bullet": "Improved   latency"},
        {"entry_key": "data analyst", "bullet": "wrote dashboards"},
    ]
    assert metrics.bullet_attribution_accuracy(pred, gold) == 1.0


def test_bullet_attribution_wrong_attribution():
    gold = [{"entry_key": "Software Engineer", "bullet": "Built X"}]
    pred = [{"entry_key": "Data Analyst", "bullet": "Built X"}]
    assert metrics.bullet_attribution_accuracy(pred, gold) == 0.0


def test_bullet_attribution_missing_bullet():
    gold = [
        {"entry_key": "SE", "bullet": "a"},
        {"entry_key": "SE", "bullet": "b"},
        {"entry_key": "SE", "bullet": "c"},
    ]
    pred = [
        {"entry_key": "SE", "bullet": "a"},
        {"entry_key": "SE", "bullet": "b"},
    ]
    assert metrics.bullet_attribution_accuracy(pred, gold) == pytest.approx(2 / 3)


def test_bullet_attribution_empty_gold():
    assert metrics.bullet_attribution_accuracy([], []) == 1.0


# --- glue / template-format ---------------------------------------------------


def test_gold_to_compare_shapes_from_template():
    label = json.loads((EVAL / "labels" / "_TEMPLATE.json").read_text())
    gold_types, gold_counts, gold_bullets = run_eval._gold_to_compare_shapes(label)

    assert gold_types == ["experience", "skills"]
    assert gold_counts == {"experience": 1, "skills": 0}
    assert len(gold_bullets) == 2
    assert all(g["entry_key"] == "Software Engineering Intern" for g in gold_bullets)


def test_pred_to_compare_shapes_matches_gold_shapes():
    resume = Resume(
        sections=[
            Section(
                type=SectionType.experience,
                raw_heading="EXPERIENCE",
                entries=[
                    Entry(
                        title="Software Engineering Intern",
                        bullets=[
                            "Built reusable React components for the client dashboard",
                            "Integrated backend API endpoints",
                        ],
                    )
                ],
            ),
            Section(
                type=SectionType.skills,
                raw_heading="SKILLS",
                skills={"languages": ["Python"]},
            ),
        ]
    )
    result = ParseResult(resume=resume, page_count=1)

    pred_types, pred_counts, pred_bullets = run_eval._pred_to_compare_shapes(result)
    assert pred_types == ["experience", "skills"]
    assert pred_counts == {"experience": 1, "skills": 0}
    assert len(pred_bullets) == 2
    assert all(p["entry_key"] == "Software Engineering Intern" for p in pred_bullets)
