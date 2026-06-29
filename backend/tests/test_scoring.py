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


from app.scoring.bullets import score_bullet


def test_score_bullet_returns_tech_keywords_and_flag():
    out = score_bullet("Developed services with FastAPI and PostgreSQL")
    assert out["mentions_tech"] is True
    assert {"FastAPI", "PostgreSQL"} <= set(out["tech_keywords"])


def test_score_bullet_no_tech():
    out = score_bullet("Coordinated weekly planning meetings")
    assert out["mentions_tech"] is False
    assert out["tech_keywords"] == []


def test_score_bullet_tech_only_scores_point_one():
    # No strong lead verb, no metric, not vague, has tech -> 0.2 + 0.1 = 0.3.
    out = score_bullet("Maintained Python and Django services")
    assert out["score"] == 0.3


def test_score_bullet_strong_full_score():
    out = score_bullet("Built a scalable service in Python handling 10k requests")
    assert out["score"] == 1.0


def test_score_bullet_empty_does_not_crash():
    out = score_bullet("")
    assert out["score"] == 0.0
    assert out["mentions_tech"] is False
    assert out["tech_keywords"] == []


def test_metric_bare_year_not_counted():
    assert score_bullet("Graduated in 2021 with honors")["has_metric"] is False


def test_metric_version_number_not_counted():
    assert score_bullet("Migrated the app to Python 3.11")["has_metric"] is False


def test_metric_bare_count_counted():
    assert score_bullet("Mentored 5 interns over the summer")["has_metric"] is True


def test_metric_percent_counted():
    assert score_bullet("Reduced latency by 40%")["has_metric"] is True


def test_metric_decimal_with_unit_counted():
    assert score_bullet("Improved uptime to 99.9% availability")["has_metric"] is True


def test_metric_thousands_with_unit_counted():
    assert score_bullet("Served 1,000 users daily")["has_metric"] is True


from app.scoring.completeness import score_completeness
from app.schemas.resume import Contact, Entry, Resume, Section, SectionType


def _complete_resume() -> Resume:
    return Resume(
        contact=Contact(email="a@b.com", github="github.com/x"),
        sections=[
            Section(type=SectionType.education, raw_heading="EDUCATION",
                    entries=[Entry(start_date="2019", end_date="2023",
                                   bullets=["Graduated with honors"])]),
            Section(type=SectionType.experience, raw_heading="EXPERIENCE",
                    entries=[Entry(start_date="2023", end_date="2025",
                                   bullets=["Built scalable services in Python"])]),
            Section(type=SectionType.projects, raw_heading="PROJECTS",
                    entries=[Entry(start_date="2024", end_date="2024",
                                   bullets=["Shipped a CLI tool"])]),
            Section(type=SectionType.skills, raw_heading="SKILLS",
                    skills={"Languages": ["Python", "Java"]}),
        ],
    )


def _incomplete_resume() -> Resume:
    return Resume(
        contact=Contact(),
        sections=[
            Section(type=SectionType.experience, raw_heading="EXPERIENCE",
                    entries=[Entry(title="Intern")]),  # no dates, no bullets
        ],
    )


def test_completeness_complete_scores_full():
    out = score_completeness(_complete_resume())
    assert out["score"] == 1.0
    assert all(out["checks"].values())
    assert out["date_coverage"]["ratio"] == 1.0
    assert out["entries_without_bullets"] == 0


def test_completeness_incomplete_low():
    out = score_completeness(_incomplete_resume())
    assert out["checks"]["has_email"] is False
    assert out["checks"]["has_experience"] is True
    assert out["date_coverage"]["ratio"] == 0.0
    assert out["entries_without_bullets"] == 1


def test_completeness_date_coverage_partial():
    resume = Resume(sections=[
        Section(type=SectionType.experience, raw_heading="EXPERIENCE", entries=[
            Entry(title="A", start_date="2023", bullets=["x"]),
            Entry(title="B", bullets=["y"]),
        ]),
    ])
    out = score_completeness(resume)
    assert out["date_coverage"]["entries_total"] == 2
    assert out["date_coverage"]["entries_with_dates"] == 1
    assert out["date_coverage"]["ratio"] == 0.5


def test_completeness_section_bullet_counts():
    out = score_completeness(_complete_resume())
    assert out["section_bullet_counts"]["experience"] == 1
    assert out["section_bullet_counts"]["skills"] == 0
