# Resume Intelligence Engine

A **layout-aware** resume parser + analysis platform. The engineering focus is the
parser: it reads a PDF, extracts words with bounding boxes, and reconstructs the
document's structure (sections, entries, bullets, dates) using coordinate-based
reasoning — *before* any LLM is involved.

The AI layer is intentionally thin. The differentiator is the deterministic,
measurable parser.

## Hard MVP constraint (do not violate)

> v1 supports **single-column, one-page software-engineering resumes** only.
> No database. No accounts. Stateless: upload → parse → analyze → return.

Everything else lives in [`BACKLOG.md`](./BACKLOG.md). Do not pull from the backlog
until the parser hits its accuracy target (see below).

## Parser accuracy (the pitch)

Measured by `eval/run_eval.py` against the hand-labeled set in `eval/`.

| Metric                     | Target | Current |
|----------------------------|--------|---------|
| Section detection (F1)     | ≥ 0.92 | TBD     |
| Entry grouping (accuracy)  | ≥ 0.90 | TBD     |
| Bullet attribution (acc)   | ≥ 0.90 | TBD     |

> Fill this in from `eval/REPORT.md`. These numbers are the headline of the project.

## Architecture

```
PDF → extract (PyMuPDF, words+bboxes) → lines → sections → entries → bullets
    → assemble (structured JSON + confidence) → scoring (rules) → AI (critique)
```

## Repo layout

```
backend/   FastAPI + the parser (the real project)
eval/      labeled resumes + metrics harness (the proof)
frontend/  Next.js UI: upload, JSON viewer, bbox debug overlay, feedback
```

## Quickstart

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

## Build order

See the phased plan. Build the parser first, prove it with `eval/`, then add
scoring, then the thin AI layer, then the frontend. Resist building the UI early.
