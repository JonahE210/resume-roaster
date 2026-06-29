# Phase 4 — Deterministic Scoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explainable, rule-based tech-keyword detection and completeness diagnostics to the scoring layer, with full test coverage and a token-free `/analyze` path.

**Architecture:** A new pure data module `tech_keywords.py` owns the curated keyword set and a token-set/n-gram matcher. `bullets.py` consumes it and gets its metric regex tightened. `completeness.py` gains additive diagnostic fields while keeping its top-level `score` byte-stable. The `/analyze` endpoint needs no code change — only tests proving `use_ai=false` spends zero tokens.

**Tech Stack:** Python 3.10+, pydantic v2, pytest, FastAPI `TestClient`.

## Global Constraints

- `backend/app/scoring/` must NEVER import FastAPI or `app.parser`. Only `app.schemas` + stdlib allowed.
- Scoring stays deterministic and explainable — every signal returns its flags.
- MVP scope: single-column one-page SWE resumes. No DB.
- `score_bullet` formula stays `0.4·verb + 0.3·metric + 0.2·(not vague) + 0.1·tech` (sums to 1.0).
- Curated keyword set capped at ~60–80 terms. No substring matching, no single `\b(...)\b` mega-regex.
- Run `pytest` from `backend/` and show output before claiming the phase done.
- All commands run from the `backend/` directory with the venv active.

---

### Task 1: Tech-keyword data module + matcher

**Files:**
- Create: `backend/app/scoring/tech_keywords.py`
- Test: `backend/tests/test_scoring.py`

**Interfaces:**
- Consumes: nothing (leaf module).
- Produces:
  - `TECH_KEYWORDS: dict[str, set[str]]` — category → canonical-cased terms.
  - `match_tech(text: str) -> list[str]` — deduped, canonical-cased terms found in `text`, first-seen order. Empty list when none.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_scoring.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_scoring.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.scoring.tech_keywords'`

- [ ] **Step 3: Write the data module**

Create `backend/app/scoring/tech_keywords.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_scoring.py -q`
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/scoring/tech_keywords.py backend/tests/test_scoring.py
git commit -m "feat(scoring): tech-keyword data module + token-set matcher"
```

---

### Task 2: Wire tech detection into score_bullet

**Files:**
- Modify: `backend/app/scoring/bullets.py:19-41`
- Test: `backend/tests/test_scoring.py`

**Interfaces:**
- Consumes: `match_tech` from Task 1.
- Produces: `score_bullet(text: str) -> dict` now returns keys
  `text, score, has_strong_verb, has_metric, is_vague, mentions_tech, tech_keywords`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_scoring.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_scoring.py -k "score_bullet" -q`
Expected: FAIL with `KeyError: 'mentions_tech'` (or `'tech_keywords'`)

- [ ] **Step 3: Implement the wiring**

In `backend/app/scoring/bullets.py`, add the import near the top (after `import re`):

```python
from app.scoring.tech_keywords import match_tech
```

Replace the body of `score_bullet` (lines 19-41) with:

```python
def score_bullet(text: str) -> dict:
    """Return a score breakdown for one bullet."""
    lower = text.lower().strip()
    words = lower.split()
    first_word = words[0] if words else ""

    has_strong_verb = first_word in STRONG_VERBS
    has_metric = bool(METRIC.search(text)) and any(c.isdigit() for c in text)
    is_vague = any(p in lower for p in WEAK_PHRASES)
    tech_keywords = match_tech(text)
    mentions_tech = bool(tech_keywords)

    score = (
        0.4 * has_strong_verb
        + 0.3 * has_metric
        + 0.2 * (not is_vague)
        + 0.1 * mentions_tech
    )
    return {
        "text": text,
        "score": round(score, 2),
        "has_strong_verb": has_strong_verb,
        "has_metric": has_metric,
        "is_vague": is_vague,
        "mentions_tech": mentions_tech,
        "tech_keywords": tech_keywords,
    }
```

Note: the empty-string case is safe — `match_tech("")` returns `[]` and `words` is `[]`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_scoring.py -q`
Expected: PASS (all Task 1 + Task 2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/scoring/bullets.py backend/tests/test_scoring.py
git commit -m "feat(scoring): wire tech detection into score_bullet with explainable flags"
```

---

### Task 3: Tighten the metric regex (year + version false positives)

**Files:**
- Modify: `backend/app/scoring/bullets.py` (METRIC constant + `has_metric` line)
- Test: `backend/tests/test_scoring.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `score_bullet(...)["has_metric"]` now excludes standalone 4-digit years and unit-less decimal version numbers, while still crediting bare counts.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_scoring.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_scoring.py -k metric -q`
Expected: FAIL — `test_metric_bare_year_not_counted` and `test_metric_version_number_not_counted` currently return `True`.

- [ ] **Step 3: Implement the tightened detection**

In `backend/app/scoring/bullets.py`, delete the old `METRIC` constant:

```python
METRIC = re.compile(r"\d+(\.\d+)?\s?(%|x|k|ms|s|users|hours|requests|qps)?", re.I)
```

and replace it with:

```python
# A number "counts" as a metric if it carries a recognized unit, OR it is a bare
# integer that is not a 4-digit year. Unit-less decimals (e.g. version "3.11") and
# standalone years (e.g. "2021") are excluded as false positives.
_NUM_WITH_UNIT = re.compile(
    r"\d[\d,]*(?:\.\d+)?\s?"
    r"(?:%|x|×|\+|k|m|b|ms|secs?|s|mins?|hrs?|hours?|days?|weeks?|months?|"
    r"users?|customers?|clients?|requests?|qps|rps|gb|tb|mb|fps)\b",
    re.I,
)
_BARE_INT = re.compile(r"(?<![\d.])\d{1,3}(?:,\d{3})*(?![\d.])")
_YEAR = re.compile(r"^(?:19|20)\d{2}$")


def _has_metric(text: str) -> bool:
    if _NUM_WITH_UNIT.search(text):
        return True
    for m in _BARE_INT.finditer(text):
        if not _YEAR.match(m.group().replace(",", "")):
            return True
    return False
```

Then in `score_bullet`, replace the `has_metric` line:

```python
    has_metric = bool(METRIC.search(text)) and any(c.isdigit() for c in text)
```

with:

```python
    has_metric = _has_metric(text)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_scoring.py -q`
Expected: PASS (all tests so far)

- [ ] **Step 5: Commit**

```bash
git add backend/app/scoring/bullets.py backend/tests/test_scoring.py
git commit -m "fix(scoring): exclude years and version numbers from metric detection"
```

---

### Task 4: Extend completeness with additive diagnostics

**Files:**
- Modify: `backend/app/scoring/completeness.py`
- Test: `backend/tests/test_scoring.py`

**Interfaces:**
- Consumes: `Resume`, `SectionType` from `app.schemas.resume`.
- Produces: `score_completeness(resume) -> dict` with unchanged `score`/`checks` plus
  `date_coverage: {entries_total, entries_with_dates, ratio}`,
  `section_bullet_counts: dict[str, int]`, `entries_without_bullets: int`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_scoring.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_scoring.py -k completeness -q`
Expected: FAIL with `KeyError: 'date_coverage'`

- [ ] **Step 3: Implement the diagnostics**

Replace the body of `score_completeness` in `backend/app/scoring/completeness.py` with:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_scoring.py -q`
Expected: PASS (all tests so far)

- [ ] **Step 5: Commit**

```bash
git add backend/app/scoring/completeness.py backend/tests/test_scoring.py
git commit -m "feat(scoring): additive completeness diagnostics (dates, bullet counts)"
```

---

### Task 5: Prove /analyze use_ai=false spends no tokens

**Files:**
- Test: `backend/tests/test_scoring.py`
- (No production change — the `if req.use_ai:` gate already exists in `analyze.py`.)

**Interfaces:**
- Consumes: the FastAPI app + `app.routes.analyze.critique_resume` (monkeypatch target).
- Produces: nothing (test-only task).

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_scoring.py`:

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _resume_payload() -> dict:
    return {
        "contact": {"email": "a@b.com", "github": "github.com/x"},
        "sections": [
            {
                "type": "experience",
                "raw_heading": "EXPERIENCE",
                "entries": [
                    {"title": "SWE Intern", "start_date": "2024", "end_date": "2025",
                     "bullets": ["Built services in Python handling 10k requests"]}
                ],
            }
        ],
    }


def test_analyze_use_ai_false_no_token_spend(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("critique_resume must not be called when use_ai=False")

    monkeypatch.setattr("app.routes.analyze.critique_resume", _boom)
    resp = client.post("/analyze", json={"resume": _resume_payload(), "use_ai": False})
    assert resp.status_code == 200
    body = resp.json()
    assert "scoring" in body
    assert "ai" not in body
    assert body["scoring"]["bullets"][0]["mentions_tech"] is True


def test_analyze_use_ai_true_calls_critique(monkeypatch):
    sentinel = {"summary": "stub critique"}
    monkeypatch.setattr(
        "app.routes.analyze.critique_resume", lambda *a, **k: sentinel
    )
    resp = client.post("/analyze", json={"resume": _resume_payload(), "use_ai": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ai"] == sentinel
```

- [ ] **Step 2: Run tests to verify behavior**

Run: `cd backend && python -m pytest tests/test_scoring.py -k analyze -q`
Expected: PASS immediately if the gate is correct. If `test_analyze_use_ai_false_no_token_spend` FAILS with the `AssertionError`, the gate is broken — fix `backend/app/routes/analyze.py` so the AI call is inside `if req.use_ai:` before continuing.

- [ ] **Step 3: (Only if Step 2 failed) confirm the gate**

`backend/app/routes/analyze.py` should already read:

```python
    result: dict = {"scoring": scoring}
    if req.use_ai:
        result["ai"] = critique_resume(req.resume, req.target_role, req.roast)
    return result
```

No change expected; verify and re-run.

- [ ] **Step 4: Run the full suite**

Run: `cd backend && python -m pytest -q`
Expected: PASS — the whole project suite including the new `test_scoring.py`, with no network calls.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_scoring.py
git commit -m "test(analyze): assert use_ai=false returns scores only, no token spend"
```

---

## Self-Review

**Spec coverage:**
- Tech-keyword detection (curated set, explainable flags) → Task 1 + Task 2. ✔
- Completeness extension (date coverage, per-section bullet counts) → Task 4. ✔
- `test_scoring.py` strong/weak/vague + complete/incomplete → Tasks 2, 3, 4. ✔
- `/analyze` use_ai=false scores-only, no token spend → Task 5. ✔
- METRIC false-positive fix (years/versions) → Task 3. ✔
- Parser/scoring purity (no FastAPI/parser imports in scoring/) → honored; only the test file imports `TestClient`. ✔

**Placeholder scan:** No TBD/TODO/"handle edge cases" — every step ships real code and exact commands. ✔

**Type consistency:** `match_tech(text) -> list[str]` defined in Task 1 and consumed identically in Task 2. `score_bullet` return keys are consistent across Tasks 2–3 and asserted in Task 5. `score_completeness` return shape defined in Task 4 matches its tests. ✔
