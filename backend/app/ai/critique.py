"""The single AI feature: critique + rewrites, with an optional roast flag."""
from __future__ import annotations

from app.ai.client import complete_json
from app.schemas.resume import Resume

SYSTEM = """You are a senior software engineer reviewing a student's resume for a \
software-engineering internship. You receive STRUCTURED JSON that has already been \
parsed from the resume — trust its structure. Critique for clarity, technical depth, \
measurable impact, and recruiter readability. Return ONLY JSON matching this shape:
{
  "overall_feedback": str,
  "top_strengths": [str],
  "main_issues": [str],
  "rewritten_bullets": [{"original": str, "improved": str}],
  "roast": str | null
}"""


def critique_resume(resume: Resume, target_role: str, roast: bool = False) -> dict:
    """Generate structured feedback. Pass roast=True to include a roast line."""
    user = (
        f"Target role: {target_role}\n"
        f"Roast mode: {'on' if roast else 'off'}\n"
        f"Resume JSON:\n{resume.model_dump_json(indent=2)}"
    )
    return complete_json(SYSTEM, user)
