"""Phase 4 deterministic scoring tests."""
from __future__ import annotations

from app.scoring.tech_keywords import match_tech


def test_match_tech_basic_single_tokens():
    assert set(match_tech("Developed REST APIs with FastAPI and PostgreSQL")) >= {
        "FastAPI", "PostgreSQL", "REST",
    }


def test_match_tech_lowercase_token():
    assert "Python" in match_tech("scripted everything in python")


def test_match_tech_multiword_longest_wins():
    out = match_tech("Built mobile apps using React Native")
    assert "React Native" in out
    assert "React" not in out  # the phrase claims the span


def test_match_tech_ci_cd_and_github_actions():
    out = match_tech("Automated CI/CD pipelines with GitHub Actions")
    assert "CI/CD" in out
    assert "GitHub Actions" in out


def test_match_tech_symbol_tokens_survive():
    out = match_tech("Wrote drivers in C, C++, and C# on .NET")
    assert {"C", "C++", "C#", ".NET"} <= set(out)


def test_match_tech_punctuation_stripped():
    out = match_tech("Optimized Node.js, Redis, and Kafka.")
    assert {"Node.js", "Redis", "Kafka"} <= set(out)


def test_match_tech_go_midsentence_matches():
    assert "Go" in match_tech("Wrote backend services in Go")


def test_match_tech_go_lowercase_ignored():
    assert "Go" not in match_tech("Helped go through the backlog")


def test_match_tech_go_bullet_initial_ignored():
    assert "Go" not in match_tech("Go build the deployment pipeline")


def test_match_tech_no_substring_false_positive():
    # 'go'⊂'organizations', 'c'⊂'collaboration' must NOT match.
    assert match_tech("Encouraged collaboration across organizations") == []


def test_match_tech_empty():
    assert match_tech("") == []
    assert match_tech("   ") == []
