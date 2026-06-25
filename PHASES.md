# Build phases — Claude Code prompts

Each phase below is a self-contained prompt you can paste into Claude Code from the
repo root. They're ordered: **don't skip ahead.** The parser (Phases 1–3) is the
project; everything else is support.

**Rules to give Claude Code every time** (paste once at the start of a session, or
keep in `CLAUDE.md`):

> - Stay inside the MVP constraint: single-column, one-page SWE resumes. No DB.
> - The `backend/app/parser/` package must never import FastAPI.
> - Write/keep unit tests for every parser stage. Flip the relevant `xfail` to a
>   real passing test as you implement it.
> - Don't add anything from `BACKLOG.md`.
> - Run `pytest` and show me the output before claiming a phase is done.

---

## Phase 1 — Line reconstruction (foundation)

**Goal:** turn raw PDF words into correctly grouped visual lines. Everything breaks
if this is sloppy.

**Done when:** `test_groups_words_on_same_line` and `test_splits_right_aligned_date`
pass (remove their `xfail`), plus new edge-case tests.

```
Implement Phase 1 of the resume parser.

1. In backend/app/parser/extract.py, switch extract_words() to PyMuPDF "dict"
   extraction so each Word carries font_size and bold. Match the existing Word /
   BBox schema in app/schemas/primitives.py.
2. In backend/app/parser/lines.py, implement reconstruct_lines() using the
   y-clustering algorithm in the docstring: sort by (page, y0, x0), group words
   whose vertical center is within y_tol of the line, where y_tol scales with
   median word height. Sort each line's words left-to-right.
3. Implement detect_right_aligned_run() to split a trailing right-aligned run
   (dates/locations) from the body using a large x-gap relative to the median
   inter-word gap.
4. Update backend/tests/test_lines.py: remove the xfail markers, make the tests
   pass, and add edge cases (multi-line, varying font sizes, a line with no
   right-aligned run).

Run pytest and show me the results.
```

---

## Phase 2 — Structure: sections, entries, bullets

**Goal:** produce a correct structured `Resume` from the lines. This is the hard
60% of the project.

**Done when:** the `xfail`s in `test_sections.py`, `test_entries.py`,
`test_bullets.py` are implemented and passing, and `/parse` returns sane JSON on
a real resume.

```
Implement Phase 2 of the resume parser: structure detection.

Work in backend/app/parser/. Keep these pure (no FastAPI imports).

1. sections.py — implement detect_section_headings() with multi-signal scoring:
   known section name, ALL CAPS, font size larger than body median, bold, short
   isolated line with whitespace above/below. Return (line_index, type,
   confidence). Replace the name-only stub.
2. entries.py — implement group_entries(): segment a section's lines into entries.
   A new entry starts on a new header pattern (right-aligned date run, and/or
   left-aligned non-bullet text at base indent, and/or emphasized text after a
   bullet block). Set each Entry's bbox and a confidence.
3. bullets.py — implement bullet ownership: detect bullet lines (marker OR hanging
   indent), attach each to the nearest preceding entry in the same section, and
   merge wrapped continuation lines into one bullet string.
4. fields.py — wire date/location/contact detection into entries during assembly,
   preferring the right-aligned run from lines.py when present. Parse the skills
   section into Section.skills (e.g. "Languages: Java, Python").
5. assemble.py — tighten parse_resume() to use the above and tag layout_boxes with
   real kinds (section/entry/bullet/date) and confidence.
6. Implement the xfail tests in test_sections.py, test_entries.py, test_bullets.py
   with realistic synthetic fixtures (build on conftest.py). Make them pass.

Run pytest and show me the results.
```

---

## Phase 3 — Eval harness: prove the parser

**Goal:** measure accuracy against hand-labeled resumes. This is what makes the
project look senior. **Do this before adding more features.**

**Done when:** `eval/run_eval.py` produces `REPORT.md` with real numbers, and you
iterate Phase 2 until you hit the README targets (≥0.92 section F1, ≥0.90 entry,
≥0.90 bullet attribution).

```
Help me build out the eval loop.

1. Confirm eval/run_eval.py and eval/metrics.py work end-to-end against the
   labels/_TEMPLATE.json format.
2. Add backend/tests for eval/metrics.py (section_f1, entry_grouping_accuracy,
   bullet_attribution_accuracy) with hand-computed expected values.
3. I'll add ~25 anonymized resume PDFs to eval/samples/ and labels to
   eval/labels/. Write a small helper script eval/make_label_stub.py that runs the
   parser on a sample and emits a pre-filled label JSON I can correct by hand
   (speeds up labeling).
4. Run run_eval.py, show me REPORT.md, and tell me which stage is the weakest
   based on the numbers.

Run pytest and show me the results.
```

> After this, loop: look at the lowest metric → improve that parser stage →
> re-run eval. Repeat until targets are hit. Update the README table.

---

## Phase 4 — Deterministic scoring

**Goal:** rule-based scores, no AI yet.

**Done when:** `/analyze` returns completeness + per-bullet scores with tests.

```
Implement Phase 4: deterministic scoring.

1. backend/app/scoring/bullets.py — finish score_bullet(): add tech-keyword
   detection (match against a curated set of languages/frameworks/tools). Keep it
   explainable (return the flags).
2. backend/app/scoring/completeness.py — keep as is or extend with date coverage
   and per-section bullet counts.
3. Add backend/tests/test_scoring.py covering strong vs weak vs vague bullets and
   a complete vs incomplete resume.
4. Confirm POST /analyze with use_ai=false returns scores only (no token spend).

Run pytest and show me the results.
```

---

## Phase 5 — Thin AI layer

**Goal:** one LLM endpoint that critiques + rewrites the *structured* resume.

**Done when:** `/analyze` with `use_ai=true` returns the critique JSON shape,
validated, with retry on bad JSON.

```
Implement Phase 5: the AI critique layer. Keep it thin — it only analyzes the
structured Resume JSON, never raw PDF text.

1. backend/app/ai/client.py — add a Pydantic model for the critique response shape
   in app/schemas/, validate the LLM output against it, and retry once on invalid
   JSON.
2. backend/app/ai/critique.py — keep the prompt, wire in the validated schema, and
   support the roast flag.
3. Add a test that mocks the LLM client (no real API calls) and asserts the
   endpoint shape. Do NOT hit the real API in tests.

Run pytest and show me the results.
```

---

## Phase 6 — Frontend wiring

**Goal:** make the three pages actually work, with the debug overlay as the star.

**Done when:** upload → see JSON + warnings; debug page overlays color-coded boxes
on the rendered PDF; analysis page shows scores + feedback.

```
Wire up the Next.js frontend (frontend/).

1. Add shared state (React context or a simple store) so a parsed resume persists
   across /, /analysis, and /debug.
2. /debug — render the uploaded PDF page (use pdf.js or render to image) and
   absolutely-position the layout_boxes over it, scaled to the rendered size,
   color-coded by kind/confidence (blue=section, green=entry, yellow=bullet,
   purple=date, red=low confidence). This is the portfolio centerpiece — make it
   clean.
3. /analysis — call analyzeResume(), render FeedbackCards with the AI critique and
   bullet rewrites; add a roast toggle.
4. Handle loading + error states. Keep styling minimal with Tailwind.

Then run the backend and frontend together and tell me how to test it manually.
```

---

## Phase 7 — Polish + demo

**Goal:** make it recruiter-ready.

**Done when:** README has real metrics, there's a demo GIF, and it deploys.

```
Final polish.

1. Update README.md accuracy table with the latest eval numbers and add a short
   "How it works" section with the pipeline diagram.
2. Record a demo GIF (upload → debug overlay → feedback) and embed it in README.
3. Add a one-command dev setup (Makefile or docker-compose) for backend+frontend.
4. Deploy: backend (Render/Fly/Railway) + frontend (Vercel). Add the live URL to
   README.
5. Write the resume bullet for this project, leading with the parser accuracy
   metric.

Only after all of the above: optionally pull ONE item from BACKLOG.md if I ask.
```

---

## The loop that matters

Phases 1→2→3, then **stay in the 2↔3 loop** (improve parser → re-measure) until the
accuracy targets are hit. The metric is the whole pitch. Don't let Claude Code drift
into frontend polish or backlog features before the numbers are real.
