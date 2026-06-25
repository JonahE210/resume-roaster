# Eval harness — the proof

This is what makes the project look senior. It measures how well the parser
reconstructs resume structure against hand-labeled ground truth.

## Workflow

1. Drop anonymized resume PDFs into `samples/` (e.g. `001.pdf`, `002.pdf`).
2. For each, hand-write the ground-truth structure in `labels/001.json`
   (see `labels/_TEMPLATE.json`). Label ~20-30 diverse single-column resumes.
3. Run `python run_eval.py`. It parses each sample, compares to the label, and
   writes a metrics table to `REPORT.md`.
4. Copy the headline numbers into the root `README.md` table.

## Metrics

- **Section detection F1** — did we find the right section headings & types?
- **Entry grouping accuracy** — right number of entries per section, boundaries correct.
- **Bullet attribution accuracy** — each bullet attached to the correct entry.
  This is the headline metric; it's the hard part competitors skip.

## Labeling tips

- Keep PDFs anonymized (swap real names/emails). Don't commit private ones — see
  `.gitignore`.
- Aim for diversity: different schools, formats, marker styles, date placements.
- A bullet is "correctly attributed" if it lands under the entry whose title/org
  matches the label, regardless of minor text differences (compare normalized).
