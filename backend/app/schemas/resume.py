"""The structured resume model — the parser's final output and the AI's input.

`confidence` fields are first-class: the parser should say how sure it is, and the
debug overlay renders low-confidence elements in red. This is part of the pitch.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.primitives import BBox


class SectionType(str, Enum):
    education = "education"
    experience = "experience"
    projects = "projects"
    skills = "skills"
    leadership = "leadership"
    certifications = "certifications"
    awards = "awards"
    unknown = "unknown"


class Contact(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class Entry(BaseModel):
    """One item within a section (a job, a project, a degree)."""

    title: str | None = None
    organization: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    bbox: BBox | None = None
    confidence: float = 1.0


class Section(BaseModel):
    type: SectionType
    raw_heading: str
    entries: list[Entry] = Field(default_factory=list)
    # Skills sections are key/value-ish rather than entry lists:
    skills: dict[str, list[str]] = Field(default_factory=dict)
    bbox: BBox | None = None
    confidence: float = 1.0


class Resume(BaseModel):
    contact: Contact = Field(default_factory=Contact)
    sections: list[Section] = Field(default_factory=list)
    # Flat list of every laid-out element + its bbox, for the debug overlay:
    layout_boxes: list[dict] = Field(default_factory=list)


class ParseResult(BaseModel):
    resume: Resume
    page_count: int
    warnings: list[str] = Field(default_factory=list)
