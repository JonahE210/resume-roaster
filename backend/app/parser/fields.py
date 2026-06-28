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
# "Summer 2025", "2024". The year is bounded to 19xx/20xx so stray 4-digit
# numbers (counts, IDs, versions) in a title don't parse as a date.
YEAR = r"(?:19|20)\d{2}"
DATE_RANGE = re.compile(
    rf"(?P<start>(?:[A-Z][a-z]+\.?\s+)?(?:Summer\s+|Fall\s+|Spring\s+|Winter\s+)?{YEAR})"
    r"\s*(?:[-–—]+\s*|to\s+)?"
    rf"(?P<end>(?:[A-Z][a-z]+\.?\s+)?{YEAR}|Present|Current|Now)?",
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?\d[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", re.I)
GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", re.I)
# City, ST  or  "Remote". The city is at most three Title-case words, each a
# self-contained token (no spaces *inside* a word), so the match can't run
# backwards and swallow preceding org/title text up to the state code.
LOCATION = re.compile(
    r"\b(?:[A-Z][a-zA-Z.]+\s){0,2}[A-Z][a-zA-Z.]+,\s*[A-Z]{2}\b|\bRemote\b"
)


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
