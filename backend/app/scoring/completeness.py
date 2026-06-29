"""Resume completeness scoring — presence of expected components."""
from __future__ import annotations

from app.schemas.resume import Resume, SectionType


def score_completeness(resume: Resume) -> dict:
    """Check for the components a SWE-internship resume should have."""
    present = {s.type for s in resume.sections}
    checks = {
        "has_email": bool(resume.contact.email),
        "has_github_or_linkedin": bool(resume.contact.github or resume.contact.linkedin),
        "has_education": SectionType.education in present,
        "has_experience": SectionType.experience in present,
        "has_projects": SectionType.projects in present,
        "has_skills": SectionType.skills in present,
    }
    score = sum(checks.values()) / len(checks)

    dated_types = {SectionType.experience, SectionType.projects, SectionType.education}
    dated_entries = [
        e for s in resume.sections if s.type in dated_types for e in s.entries
    ]
    entries_total = len(dated_entries)
    entries_with_dates = sum(1 for e in dated_entries if e.start_date or e.end_date)
    ratio = round(entries_with_dates / entries_total, 2) if entries_total else 0.0

    section_bullet_counts = {
        s.type.value: sum(len(e.bullets) for e in s.entries) for s in resume.sections
    }
    entries_without_bullets = sum(
        1 for s in resume.sections for e in s.entries if not e.bullets
    )

    return {
        "score": round(score, 2),
        "checks": checks,
        "date_coverage": {
            "entries_total": entries_total,
            "entries_with_dates": entries_with_dates,
            "ratio": ratio,
        },
        "section_bullet_counts": section_bullet_counts,
        "entries_without_bullets": entries_without_bullets,
    }
