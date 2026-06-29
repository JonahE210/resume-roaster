"""Curated tech-keyword set + matcher for explainable bullet scoring (Phase 4).

Matching is token-set + n-gram phrase based — NEVER substring — so 'go'⊂'good'
and 'c'-everywhere false positives can't happen, and symbol-bearing terms
(C++, C#, Node.js, CI/CD, .NET) survive tokenization intact. This module is pure
(stdlib only) so it stays inside the scoring purity firewall.
"""
from __future__ import annotations

# Canonical-cased terms grouped by category (source-readable; ~70 total).
TECH_KEYWORDS: dict[str, set[str]] = {
    "languages": {
        "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go",
        "Rust", "Ruby", "Kotlin", "Swift", "Scala", "PHP", "R", "SQL", "Bash",
    },
    "frameworks": {
        "React", "React Native", "Angular", "Vue", "Node.js", "Express",
        "Django", "Flask", "FastAPI", "Spring", "Spring Boot", "Rails", ".NET",
        "TensorFlow", "PyTorch", "Pandas", "NumPy",
    },
    "tools": {
        "Docker", "Kubernetes", "Git", "Linux", "GraphQL", "REST", "CI/CD",
        "GitHub Actions", "Kafka", "Apache Kafka", "Terraform", "Jenkins",
        "Machine Learning",
    },
    "cloud": {
        "AWS", "GCP", "Azure", "Amazon Web Services",
    },
    "databases": {
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "DynamoDB",
    },
}

# Ambiguous single tokens that collide with English words / single letters.
# Matched only by exact original case; 'Go' additionally must not be the first
# token (bullet-initial 'Go' is the imperative verb, not the language).
_AMBIGUOUS = {"Go", "C", "R"}

# Punctuation stripped from the ends of a whitespace token. Leading '.' is NOT
# stripped (keeps '.NET'); trailing '+'/'#' are NOT stripped (keeps 'C++'/'C#').
_LEAD = ",;:!?()[]{}\"'"
_TRAIL = ",;:!?()[]{}\"'."


def _canon_by_lower() -> dict[str, str]:
    out: dict[str, str] = {}
    for terms in TECH_KEYWORDS.values():
        for term in terms:
            out.setdefault(term.lower(), term)
    return out


_CANON_BY_LOWER = _canon_by_lower()
_SINGLE_TOKENS = {
    low: canon
    for low, canon in _CANON_BY_LOWER.items()
    if " " not in low and canon not in _AMBIGUOUS
}
_PHRASES = {low: canon for low, canon in _CANON_BY_LOWER.items() if " " in low}
_MAX_PHRASE_LEN = max((len(p.split()) for p in _PHRASES), default=1)


def _tokenize(text: str) -> list[str]:
    """Whitespace split, then strip surrounding (not internal) punctuation."""
    tokens: list[str] = []
    for raw in text.split():
        tok = raw.lstrip(_LEAD).rstrip(_TRAIL)
        if tok:
            tokens.append(tok)
    return tokens


def match_tech(text: str) -> list[str]:
    """Return canonical-cased tech terms found in ``text`` (deduped, ordered)."""
    tokens = _tokenize(text)
    lowers = [t.lower() for t in tokens]
    consumed = [False] * len(tokens)
    matched: list[str] = []

    # Phrases first, longest n-gram wins, so 'React Native' beats 'React'.
    for n in range(_MAX_PHRASE_LEN, 1, -1):
        for i in range(len(tokens) - n + 1):
            if any(consumed[i:i + n]):
                continue
            gram = " ".join(lowers[i:i + n])
            if gram in _PHRASES:
                matched.append(_PHRASES[gram])
                for j in range(i, i + n):
                    consumed[j] = True

    # Single-token, case-insensitive membership.
    for i, low in enumerate(lowers):
        if not consumed[i] and low in _SINGLE_TOKENS:
            matched.append(_SINGLE_TOKENS[low])

    # Ambiguous terms: exact original case; 'Go' not bullet-initial.
    for i, tok in enumerate(tokens):
        if consumed[i] or tok not in _AMBIGUOUS:
            continue
        if tok == "Go" and i == 0:
            continue
        matched.append(tok)

    seen: set[str] = set()
    ordered: list[str] = []
    for m in matched:
        if m not in seen:
            seen.add(m)
            ordered.append(m)
    return ordered
