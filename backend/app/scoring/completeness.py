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
    return {"score": round(score, 2), "checks": checks}
