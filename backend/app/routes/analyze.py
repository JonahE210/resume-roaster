"""POST /analyze — structured resume -> deterministic scores + AI critique."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.critique import critique_resume
from app.scoring.bullets import score_bullet
from app.scoring.completeness import score_completeness
from app.schemas.resume import Resume


class AnalyzeRequest(BaseModel):
    resume: Resume
    target_role: str = "Software Engineering Intern"
    roast: bool = False
    use_ai: bool = True  # allow scoring-only runs without burning tokens


router = APIRouter(tags=["analyze"])


@router.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest) -> dict:
    all_bullets = [
        b for s in req.resume.sections for e in s.entries for b in e.bullets
    ]
    scoring = {
        "completeness": score_completeness(req.resume),
        "bullets": [score_bullet(b) for b in all_bullets],
    }
    result: dict = {"scoring": scoring}
    if req.use_ai:
        result["ai"] = critique_resume(req.resume, req.target_role, req.roast)
    return result
