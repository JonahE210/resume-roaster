# Phase 4 — Deterministic Scoring (Design)

Date: 2026-06-28
Status: Approved (two-designer reconciliation)

## Goal

Rule-based, explainable scoring with no AI. Done when `POST /analyze` returns
completeness + per-bullet scores, covered by tests, and `use_ai=false` spends
zero tokens.

This design is the reconciliation of two independent proposals (a minimal/YAGNI
lens and a coverage/explainability lens). Consensus and resolved splits below.

## Hard constraints (inherited)

- `backend/app/scoring/` must never import FastAPI or `parser/`. It already imports
  only `app.schemas` + stdlib `re`. Keep it that way.
- MVP scope: single-column one-page SWE resumes. No DB.
- Keep scoring deterministic and explainable (return the flags).
- Run `pytest` and show output before claiming the phase done.

## Decisions

### 1. Tech-keyword detection (`bullets.py` + new `tech_keywords.py`)

- **Storage:** new data module `backend/app/scoring/tech_keywords.py` exporting a
  `dict[str, set[str]]` (category → canonical terms) for `languages`,
  `frameworks`, `tools`, `cloud`, `databases`. Derived lookup structures
  (lowercased single-token set, lowercased phrase set, ambiguous set) built once
  at import. Auditable and independently testable — serves the "explainable" pitch.
- **Size:** ~60–80 curated canonical terms total. Big enough for real coverage,
  small enough to hand-audit. Do not balloon to 150+.
- **Matching strategy — token-set membership + n-gram phrases + ambiguous special-case.
  Reject substring matching and reject a single `\b(...)\b` mega-alternation.**
  - Custom tokenizer: split on whitespace, strip *surrounding* punctuation
    (`, . ; : ( ) [ ]`) but preserve *internal* `+ # . / -` so `C++`, `C#`,
    `Node.js`, `CI/CD`, `React-Native` survive as single tokens.
  - Single-token terms → lowercase membership against the canonical set; map back
    to canonical casing for display.
  - Multi-word terms (`React Native`, `Machine Learning`, `GitHub Actions`,
    `Spring Boot`, `Apache Kafka`) → 2- and 3-gram windows; **longest match wins +
    dedupe** so `React Native` claims the span and `React` isn't double-counted.
  - Ambiguous terms (`Go`, `C`, `R`) → strict matcher: require exact original-case
    token; for `Go` additionally require position > 0 (bullet-initial "Go" is the
    imperative verb, not the language). Residual FP risk accepted; full POS
    disambiguation is explicitly out of scope (YAGNI).
  - **Rationale:** substring gives `go`⊂"good"/`c` everywhere; a `\b` mega-regex
    breaks on `C++`/`C#`/`.NET`/`Node.js`/`CI/CD` boundary chars. Token-set avoids
    both and yields *which* terms matched for free.

### 2. `score_bullet` return shape and formula

- Formula **unchanged**: `0.4·verb + 0.3·metric + 0.2·(not vague) + 0.1·tech`
  (sums to 1.0 → score in [0,1]). Tech is the weakest signal; keep it at 0.1 so
  keyword-stuffed bullets can't score artificially high.
- Wire the real boolean into the existing `0.1·tech` term.
- Return dict gains:
  - `tech_keywords: list[str]` — deduped, canonical-cased matched terms.
  - `mentions_tech: bool` — defined as `bool(tech_keywords)`; kept for the math
    and explainability.

### 3. METRIC regex false positives (`bullets.py`)

- Keep bare counts counting ("Mentored 5 interns", "Led team of 4") — they are
  legitimate quantified impact; do **not** require a unit (that would drop them).
- Add targeted exclusions for two realistic noise cases:
  - **Standalone 4-digit years** (`(?:19|20)\d{2}` as a whole token), e.g.
    "Graduated in 2021".
  - **Decimal version numbers**, e.g. "Python 3.11".
- Drop the now-redundant `any(c.isdigit())` guard.

### 4. `completeness.py` — additive diagnostics only

- Top-level `score` and the existing 6 `checks` stay **byte-stable** (no semantic
  shift for existing callers/tests).
- Add additive fields:
  - `date_coverage`: `{entries_total, entries_with_dates, ratio}` over entries that
    should carry dates (experience, projects, education); `ratio == 0.0` when
    `entries_total == 0`.
  - `section_bullet_counts`: `dict` keyed by `SectionType.value`.
  - `entries_without_bullets`: `int`.
- **Skip (YAGNI):** skills-vs-bullets cross-referencing, multi-page/multi-column
  checks, GPA/readability metrics.

### 5. `/analyze` with `use_ai=false`

- **No production change.** The `if req.use_ai:` gate already exists and the
  OpenAI client is constructed lazily inside the AI path, so the scores-only path
  spends zero tokens.
- Covered by tests only (see below).

## Tests (`backend/tests/test_scoring.py`)

Fixtures built directly from schema types (`Resume`/`Section`/`Entry`/`Contact`),
never synthetic `Word` lists.

**Bullet scoring:**
- `test_strong_bullet_full_score` — strong verb + metric-with-unit + tech → 1.0
- `test_weak_vague_bullet_zero` — "various tasks…" → 0.0
- `test_responsible_for_is_vague` — vague flag set, no verb/metric → 0.0
- `test_metric_with_unit_counts` — "Reduced latency by 40%" → 0.9, tech F
- `test_bare_count_still_counts_as_metric` — "Mentored 5 interns" → has_metric T
- `test_bare_year_not_metric` — "Graduated in 2021" → has_metric F (regression)
- `test_version_number_not_metric` — "Migrated to Python 3.11" → has_metric F
- `test_tech_keywords_returned` — tech_keywords ⊇ {FastAPI, PostgreSQL}
- `test_multiword_react_native` — "React Native" present, "React" not double-listed
- `test_ci_cd_and_github_actions` — ⊇ {CI/CD, GitHub Actions}
- `test_ambiguous_go_midsentence_matches` — "services in Go" → Go matched
- `test_ambiguous_go_lowercase_ignored` — "helped go through…" → Go not matched
- `test_single_letter_langs` — "C and C++" → {C, C++}; "C#" → C#
- `test_punctuation_stripping` — "Node.js, Redis, Kafka." → {Node.js, Redis, Kafka}
- `test_empty_bullet` / `test_whitespace_only_bullet` — no crash, all flags F, score 0.0
- `test_all_caps_bullet` — case-insensitive verb/tech, ambiguous stays case-strict

**Completeness:**
- `test_complete_resume_scores_high` — score 1.0, all checks T, date ratio 1.0,
  entries_without_bullets 0
- `test_incomplete_resume_low` — has_email F, date ratio 0.0, entries_without_bullets ≥ 1
- `test_date_coverage_partial` — 2 entries, 1 dated → ratio 0.5
- `test_section_bullet_counts` — dict keyed by `SectionType.value` with correct totals

**Endpoint:**
- `test_analyze_use_ai_false_no_token_spend` — monkeypatch
  `app.routes.analyze.critique_resume` to raise if called; POST with `use_ai=false`;
  assert `"scoring"` present, `"ai"` absent, stub never invoked.
- `test_analyze_use_ai_true_calls_critique` — monkeypatch to a stub dict; assert
  `"ai"` present. No real API calls.

## Change surface

- `backend/app/scoring/tech_keywords.py` — new data module.
- `backend/app/scoring/bullets.py` — tokenizer + tech detection + return list +
  metric-regex fix. Formula unchanged.
- `backend/app/scoring/completeness.py` — additive diagnostics only.
- `backend/app/routes/analyze.py` — no change.
- `backend/tests/test_scoring.py` — new (~18 tests).
