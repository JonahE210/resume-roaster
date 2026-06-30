# Progress log — Resume Intelligence Engine

This document summarizes all work done so far so an external reviewer (Codex / Claude Code)
can pick up and make further progress. It covers Phases 1–3 of the build defined in
[PHASES.md](PHASES.md), the project rules in [CLAUDE.md](CLAUDE.md), and the current
repository / git state.

## How the work was done

Each phase was built by a three-agent loop:
- **Product Manager / tech lead** — reads the repo + PHASES.md and produces a precise work order; later triages QA findings into fix directives.
- **Software Engineer** — implements the work order; writes production code + tests; never commits (commits are done at the coordinator level).
- **Test / Debug (QA)** — independently re-runs everything, probes adversarially, and reports bugs. Does not trust the SE's self-report.

The loop per phase was: PM work order -> SE implement -> QA verify -> (if bugs) PM triage -> SE fix -> QA re-verify -> commit.

## Git state

| Branch | Points at | Contents |
|--------|-----------|----------|
| `main` | `2c23a9c` | Initial scaffold. Untouched fallback. |
| `feat/phase1` | `15f64bf` | Phase 1 committed. |
| `feat/phase2` | `f8207e8` | Phase 2 committed (on top of Phase 1). |
| `feat/phase3` | `f8207e8` + **uncommitted working tree** | Phase 3 implemented but NOT yet committed (see below). |

**Important:** Phase 3 changes are currently **uncommitted** on `feat/phase3`. The working tree has:
- Modified: `eval/metrics.py`, `eval/run_eval.py`, `backend/tests/conftest.py`, `backend/tests/test_entries.py`
- New (untracked): `eval/make_label_stub.py`, `backend/tests/test_eval_metrics.py`, `backend/tests/test_e2e_smoke.py`

A reviewer should commit these to `feat/phase3` (suggested message at the bottom) before continuing.

## Hard rules honored throughout (from CLAUDE.md)

- MVP scope: single-column, one-page SWE resumes; no DB; stateless.
- `backend/app/parser/` never imports FastAPI.
- `extract.py` is the only module that touches PyMuPDF (`fitz`); all other parser stages operate on `Line`/`Word` primitives.
- Parser unit tests use synthetic `Word`/`Line` fixtures only — no real PDFs.
- Nothing from `BACKLOG.md` is built until accuracy targets are hit.
- Each phase ends with `pytest` green; `xfail` markers flip to real passing tests as features land.

---

## Phase 1 — Line reconstruction (committed: `15f64bf`)

**Goal:** turn raw PDF words into correctly grouped visual lines.

Files changed: `backend/app/parser/extract.py`, `backend/app/parser/lines.py`, `backend/tests/test_lines.py`, `backend/tests/test_extract.py` (new), `backend/tests/conftest.py`.

- `extract.py`: switched to PyMuPDF `"rawdict"` extraction. Added a pure, fitz-free helper `_chars_to_words(chars, *, font_size, bold, page)` that unions per-character bounding boxes into per-word boxes (this preserves true inter-word gaps) and carries `font_size` + `bold` per word. Defensive `.get()` walk of blocks/lines/spans.
- `lines.py`:
  - `reconstruct_lines(words, y_tol_ratio=0.5)` — y-clustering by vertical center within a height-scaled tolerance; sorts by `(page, y0, x0)`; never merges across pages; x-sorts words within each line; guards degenerate (<=0) heights with a floor.
  - `detect_right_aligned_run(line, gap_ratio=3.0)` — returns the trailing right-aligned run (a suffix slice of `line.words`) or `None`, using a font/width-derived spacing baseline (handles 2-word lines; no epsilon false positives).

**Bugs caught by QA and fixed in this phase:** a 2-word line could never split; the original proportional x-split erased the date gap; an epsilon made the detector trigger-happy; degenerate-height shatter. All fixed; `font_size` guard uses `is not None` semantics.

**Deferred (documented in code):** running-mean center can mis-split a gently-sloped line — revisit only if Phase 3 eval surfaces line-grouping errors.

---

## Phase 2 — Structure detection (committed: `f8207e8`)

**Goal:** produce a structured `Resume` (sections, entries, bullets, fields). The hard 60%.

Files changed: `backend/app/parser/{sections,entries,bullets,fields,assemble}.py`, `backend/tests/{test_sections,test_entries,test_bullets,test_fields,conftest}.py` (`test_fields.py` new).

- `sections.py` — `detect_section_headings(lines)` multi-signal weighted scoring (name 0.45, ALL CAPS 0.20, font larger than body median 0.20, bold 0.15, short 0.10, isolated 0.10), threshold 0.60. A body line that merely starts with a section word (e.g. "Experience building…") does NOT false-fire. Keeps `classify_heading` + `SECTION_SYNONYMS`.
- `entries.py` — `group_entries(section_lines, base_font_size=None)` (the one allowed signature change). Segments a section into entries. **New entry boundaries:** first line, OR a right-aligned date run, OR the first text line after a bullet/continuation block. Emphasis (bold/large) is a **confidence signal only**, never a boundary (see bug below). Populates title / dates / organization / location / bullets / bbox / confidence.
- `bullets.py` — `is_bullet_line(line, body_indent=None)` (marker or hanging indent), `is_continuation(...)`, and `assign_bullets(section_lines, entry_starts, *, body_indent)` for nearest-preceding-entry ownership + wrapped continuation-line merging into one marker-stripped string. The headline accuracy metric.
- `fields.py` — `parse_skills(lines)` ("Languages: Java, Python" -> `{"languages": ["Java","Python"]}`). Splits values on `,;|` always and on `/` only when space-surrounded, so `CI/CD`, `TCP/IP` survive.
- `assemble.py` — wires body-median font into `group_entries`, parses skills sections, sets section `bbox`, and tags `layout_boxes` with real kinds (section/entry/bullet/date/line) + confidence.

**HIGH-severity bug caught by QA and fixed:** a bold organization line (e.g. "Google") on the line after the title was being promoted to its own entry — splitting one job into two and misattributing its bullets. Fix: removed the emphasis-only entry boundary entirely (emphasis kept only as a confidence input). Legitimate new entries are covered by date-run and post-bullet-block rules. Locked by regression tests.

**MEDIUM bug fixed:** `parse_skills` shredded `CI/CD` etc. on `/` — fixed as above.

**Deferred:**
- Overlay `layout_boxes` mis-tags (hanging-indent bullets tagged "line"; date boxes re-detected on every line) -> Phase 6 (overlay only, no metric impact). Approaches documented in `assemble.py` comments.
- **Right-aligned LOCATION vs DATE (known issue):** an org line carrying a right-aligned location (e.g. "Google   Mountain View, CA") trips the date-run boundary and becomes a spurious entry that steals the bullet. Deferred to Phase 3 so the eval can quantify it before a parser fix. There is a tracking test that asserts the current (buggy) behavior and is commented to flip once fixed.

---

## Phase 3 — Eval harness (IMPLEMENTED, uncommitted on `feat/phase3`)

**Goal:** measure parser accuracy against hand-labeled resumes. Per PHASES.md, this phase is split: the agents can build the tooling/tests now, but the **real accuracy numbers require the user to supply ~25 anonymized labeled resume PDFs**.

### Built now (no user data required)

- `eval/metrics.py` — one fix: `section_f1` returns `f1=1.0` for empty/empty (vacuous perfect match; was 0.0). One-sided empty still correctly returns `f1=0.0`.
- `eval/run_eval.py` — hardened: per-sample `try/except` isolation (one bad PDF can't abort the batch; prints `error {stem}: …` and records a zero row) and a weakest-stage summary appended to `REPORT.md` + stdout, comparing the three means to `TARGETS = {Section F1: 0.92, Entry acc: 0.90, Bullet attr: 0.90}` (PASS / BELOW TARGET per metric + a `Weakest stage:` line). Empty `eval/labels/` still prints a clean "no labels" message and exits 0.
- `eval/make_label_stub.py` (new) — CLI `python make_label_stub.py <sample.pdf> [--force] [--stdout]`. Runs the parser on a sample and emits a pre-filled label JSON in `_TEMPLATE.json` shape to bootstrap hand-labeling. Refuses to overwrite an existing label without `--force`.
- `backend/tests/test_eval_metrics.py` (new) — hand-computed unit tests for all three metrics (precision/recall + empty-input edges) plus glue tests that drive `_gold_to_compare_shapes` on the real `_TEMPLATE.json` and `_pred_to_compare_shapes` on a synthetic `ParseResult`.
- `backend/tests/test_e2e_smoke.py` (new) — skippable (`pytest.importorskip("fitz")`) synthetic-PDF end-to-end smoke test: generates a one-page PDF in memory and runs `parse_resume`, with loose structural asserts (not an accuracy test).
- `backend/tests/test_entries.py` + `conftest.py` — the location-vs-date watch-item tracking test described above. No parser logic changed.

**Guardrail confirmed:** `git diff` of `backend/app/parser/` and `backend/app/schemas/` is EMPTY for Phase 3 — no parser logic was touched (fixing the parser is the job of the Phase 2<->3 loop, after numbers exist).

### Blocked on the user (the real numbers)

To produce real accuracy numbers and start the Phase 2<->3 improvement loop:
1. Make the backend importable from `eval/` (activate the backend venv; `pip install -e ../backend`, or set `PYTHONPATH=../backend`).
2. Drop ~20–30 anonymized, single-column, one-page SWE resume PDFs into `eval/samples/` as `001.pdf`, `002.pdf`, … (these are git-ignored by default; `git add -f` only ones you want committed).
3. For each: `python make_label_stub.py samples/001.pdf` -> `eval/labels/001.json`, then **hand-correct it to ground truth** (section types must be exact `SectionType` values; fix entry boundaries, bullet text/attribution, skills). The stub mirrors the parser's current output including mistakes.
4. Include diversity, and at least one resume with an org line carrying a right-aligned location to quantify the deferred watch-item.
5. `python run_eval.py` -> writes `eval/REPORT.md` (per-sample table, means vs targets, weakest stage).
6. Copy headline numbers into the root `README.md` table; then run the 2<->3 loop: improve the weakest parser stage on a fresh branch, re-run, repeat until targets met.

---

## Test status

- After Phases 1+2 (committed): 30 tests, zero `xfail`.
- After Phase 3 (uncommitted): **50 passed** when PyMuPDF/`fitz` is importable (e2e smoke runs), or **49 passed + 1 skipped** when `fitz` is unavailable (e2e skips cleanly). Zero `xfail`/`xpass`.

## Environment issue a reviewer must fix (NOT a code bug)

`backend/.venv` is broken/inconsistent: after `source .venv/bin/activate`, the shell's `python` resolves to an Anaconda 3.13 interpreter that does NOT have `fitz`, while the venv's actual installed deps (incl. PyMuPDF) live under `.venv/lib/python3.14/site-packages`. Consequence: the default `python -m pytest` **silently skips the only end-to-end test** — a HIGH false-confidence risk for CI.

Recommended fix: `rm -rf backend/.venv && python3.14 -m venv backend/.venv && (cd backend && source .venv/bin/activate && pip install -e ".[dev]")`, disable conda `base` auto-activation, and make CI fail if the e2e test is collected as skipped.

## Suggested next steps for the reviewer

1. Commit the Phase 3 working tree to `feat/phase3` (see message below).
2. Fix the `.venv` so the e2e test runs by default.
3. Provide the labeled eval set (the 6 steps above) to unlock real numbers.
4. Begin the Phase 2<->3 loop on the weakest stage; the location-vs-date watch-item is the most likely first target.
5. Then proceed to Phase 4 (deterministic scoring), Phase 5 (thin AI layer), Phase 6 (frontend + debug overlay, where the deferred overlay nits get fixed), Phase 7 (polish/deploy).

Suggested commit message for the pending Phase 3 changes:

```
Phase 3: eval harness tooling + tests (agent-buildable portion)

- metrics.py: section_f1 empty/empty -> f1=1.0
- run_eval.py: per-sample error isolation + weakest-stage-vs-targets summary
- make_label_stub.py: parser-output -> _TEMPLATE.json label bootstrap (--force/--stdout)
- tests: hand-computed metrics + glue tests, skippable synthetic-PDF e2e smoke,
  location-vs-date watch-item tracking test
No backend/app/parser/ logic changed. Real numbers blocked on user-provided labeled PDFs.
```
