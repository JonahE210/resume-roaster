# CLAUDE.md — project context

Read this first in every session. It's the single source of truth for what this
project is, the rules that must not be broken, and where things currently stand.
The build is driven by [PHASES.md](PHASES.md); this file is the durable summary.

## Project

**Resume Intelligence Engine** — a layout-aware PDF resume parser + thin AI
analysis platform. It reads a PDF, extracts words with bounding boxes, and
reconstructs the document's structure (sections, entries, bullets, dates) using
coordinate-based reasoning **before any LLM is involved**.

The deterministic, measurable parser is the differentiator and the whole pitch.
The AI layer is intentionally thin (it only analyzes the structured JSON).

## Hard rules (never violate)

- **MVP scope:** single-column, one-page software-engineering resumes only. No
  database. No accounts. Stateless: upload → parse → analyze → return.
- **Parser purity:** `backend/app/parser/` must never import FastAPI. Stages stay
  pure and testable on synthetic `Word` lists (no real PDFs in unit tests).
- **Scope firewall:** do not build anything from [BACKLOG.md](BACKLOG.md) until
  the parser hits its accuracy targets.
- **Tests per stage:** keep/write a unit test for every parser stage. Flip the
  relevant `xfail` to a real passing test as each piece lands.
- **Prove it:** run `pytest` and show the output before claiming a phase is done.
- **Don't skip ahead** in the phases, and don't drift into frontend polish or
  backlog features before the accuracy numbers are real.

## Pipeline

```
PDF → extract → lines → sections → entries → bullets → fields
    → assemble (structured JSON + confidence) → scoring (rules) → AI (critique)
```

File map (`backend/app/`):
- `parser/extract.py` — PyMuPDF word + bbox extraction (only module touching fitz).
- `parser/lines.py` — y-clustering into visual lines; right-aligned run detection.
- `parser/sections.py` — multi-signal heading detection + `SectionType` mapping.
- `parser/entries.py` — segment a section's lines into entries.
- `parser/bullets.py` — bullet detection + ownership + wrapped-line merging.
- `parser/fields.py` — regex/layout date, location, contact detection.
- `parser/assemble.py` — orchestrates the pipeline; builds flat `layout_boxes`.
- `scoring/` — deterministic bullet + completeness scoring (explainable, no AI).
- `ai/` — thin LLM critique layer (client + critique prompt).
- `schemas/primitives.py` — `BBox`, `Word`, `Line`.
- `schemas/resume.py` — `Contact`, `Entry`, `Section`, `Resume`, `ParseResult`.
  `confidence` is first-class (low-confidence elements render red in the overlay).

## Repo layout

- `backend/` — FastAPI + the parser. The real project.
- `eval/` — labeled resumes + metrics harness. The proof.
- `frontend/` — Next.js UI: upload, JSON viewer, bbox debug overlay, feedback.

## Accuracy targets (the pitch)

Measured by `eval/run_eval.py` → `eval/REPORT.md`, then copied into the README table.

| Metric                    | Target  |
|---------------------------|---------|
| Section detection (F1)    | ≥ 0.92  |
| Entry grouping (accuracy) | ≥ 0.90  |
| Bullet attribution (acc)  | ≥ 0.90  |

Bullet attribution is the headline metric — the hard part competitors skip.

## Current state

Scaffold/skeleton. The pipeline runs end-to-end on **stubs**; the real logic is
marked `TODO(phaseN)`, and tests use `xfail` as a build checklist.

Already working: `classify_heading` (sections), `strip_marker` (bullets), the
regex field helpers (`fields.py`), and the `eval/metrics.py` functions.

Not done yet: line reconstruction is a one-word-per-line placeholder, entry
grouping dumps everything into one entry, no eval samples/labels exist, and the
repo is not yet a git repo.

## Phase roadmap (see [PHASES.md](PHASES.md))

1. **Line reconstruction** — y-clustering words into lines (foundation).
2. **Structure** — sections, entries, bullets, fields (the hard 60%).
3. **Eval harness** — measure accuracy against hand-labeled resumes.
   → Then stay in the **2↔3 loop**: improve the weakest stage, re-measure, until
   targets are hit. The metric is the whole pitch.
4. **Deterministic scoring** — rule-based bullet + completeness scores, no AI.
5. **Thin AI layer** — one LLM endpoint critiquing the structured JSON, validated.
6. **Frontend wiring** — the bbox debug overlay is the portfolio centerpiece.
7. **Polish + demo** — real metrics in README, demo GIF, one-command setup, deploy.

## Dev commands

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```

Eval:
```bash
cd eval
python run_eval.py
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Python ≥ 3.10. Key deps: fastapi, pymupdf, pydantic v2, pydantic-settings, openai.

## Endpoints

- `POST /parse` — PDF upload → `ParseResult` (structured resume + `layout_boxes`).
- `POST /analyze` — `Resume` → deterministic scores + AI critique. Pass
  `use_ai=false` to skip token spend (scores only). `roast` flag toggles a roast.
- `GET /health` — liveness check.
