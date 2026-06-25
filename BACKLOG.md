# Backlog (NOT in MVP)

Nothing here gets built until the parser hits its accuracy targets in the README.
This file is a scope firewall. If an idea is cool but not in the MVP, it goes here.

## Parsing
- Multi-column resume support
- Two-page / multi-page resumes
- Non-standard / graphical / designer resume layouts
- Table-based layouts
- OCR fallback for image-only / scanned PDFs

## Product
- User accounts + auth
- Resume version history + improvement-over-time analytics
- Resume comparison (A/B)
- Manual correction mode (user fixes parser mistakes, feeds back into eval set)
- PDF export of the improved resume
- Job-description matching / internship match score
- Chrome extension for job postings
- Cover letter generator
- LinkedIn summary generator
- Role-specific fine-tuned scoring

## Infra
- Database (SQLite → Postgres)
- Deployed object storage for uploads
- Auth + rate limiting
- Caching layer

## AI
- Roast mode (trivial — do as a flag in critique.py, last)
- Resume heatmap visualization
- Per-role tuned critique prompts
