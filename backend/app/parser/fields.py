"""Stage 6 — Field detection (dates, locations, contact info).

Regex + layout. Dates and locations are often right-aligned, so callers should
prefer the right-aligned run from lines.detect_right_aligned_run() when present.
"""
from __future__ import annotations

import re

from app.schemas.primitives import Line

# Split skill VALUE lists on , ; | always, and on "/" only when space-delimited
# (so "React / Node" splits but "CI/CD", "TCP/IP", "A/B" stay intact).
SKILL_SPLIT = re.compile(r"[,;|]|\s+/\s+")

# Matches: "May 2025 - Aug 2025", "2024 - Present", "Jan 2024 – May 2024",
# "Summer 2025", "2024".
DATE_RANGE = re.compile(
    r"(?P<start>(?:[A-Z][a-z]+\.?\s+)?(?:Summer\s+|Fall\s+|Spring\s+|Winter\s+)?\d{4})"
    r"\s*(?:[-–—to]+\s*)?"
    r"(?P<end>(?:[A-Z][a-z]+\.?\s+)?\d{4}|Present|Current|Now)?",
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?\d[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", re.I)
GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", re.I)
# City, ST  or  "Remote"
LOCATION = re.compile(r"\b([A-Z][a-zA-Z.\s]+,\s*[A-Z]{2})\b|\bRemote\b")


def find_date_range(text: str) -> tuple[str | None, str | None]:
    m = DATE_RANGE.search(text)
    if not m:
        return None, None
    return m.group("start"), m.group("end")


def find_location(text: str) -> str | None:
    m = LOCATION.search(text)
    return m.group(0) if m else None


def find_contact(text: str) -> dict[str, str | None]:
    """Pull contact fields out of the (usually) header block text."""
    def first(rx: re.Pattern[str]) -> str | None:
        m = rx.search(text)
        return m.group(0) if m else None

    return {
        "email": first(EMAIL),
        "phone": first(PHONE),
        "linkedin": first(LINKEDIN),
        "github": first(GITHUB),
    }


def parse_skills(lines: list[Line]) -> dict[str, list[str]]:
    """Parse a skills section's lines into a label -> values mapping.

    "Languages: Java, Python"        -> {"languages": ["Java", "Python"]}
    "Tools / Frameworks: React; Node" -> {"tools / frameworks": ["React", "Node"]}
    A line with no colon contributes its split tokens under the "general" key.
    Duplicate labels merge (values are extended).
    """
    result: dict[str, list[str]] = {}
    for line in lines:
        text = line.text.strip()
        if not text:
            continue
        if ":" in text:
            label, rest = text.split(":", 1)  # split on the FIRST colon only
            key = label.strip().lower()
            values = [t.strip() for t in SKILL_SPLIT.split(rest) if t.strip()]
        else:
            key = "general"
            values = [t.strip() for t in SKILL_SPLIT.split(text) if t.strip()]
        if key in result:
            result[key].extend(values)
        else:
            result[key] = values
    return result
