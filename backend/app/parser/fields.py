"""Stage 6 — Field detection (dates, locations, contact info).

Regex + layout. Dates and locations are often right-aligned, so callers should
prefer the right-aligned run from lines.detect_right_aligned_run() when present.
"""
from __future__ import annotations

import re

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
