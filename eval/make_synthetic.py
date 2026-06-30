"""Generate synthetic single-column SWE resume PDFs + their ground-truth labels.

Why: the eval harness needs `samples/*.pdf` paired with `labels/*.json`. Real
resumes are private and slow to label. These synthetic resumes are driven by one
spec per resume: the SAME spec renders the PDF (via PyMuPDF) and emits the label,
so the PDF<->label pair is correct by construction. The PARSER is the unknown
being measured — nothing here imports the parser, so the numbers are honest.

Diversity is deliberate (bullet glyphs, date/location placement, wrapped bullets,
multi-entry sections, section mix) so the run exercises the real coordinate logic.

Usage:
    python make_synthetic.py            # write samples/*.pdf + labels/*.json
    python make_synthetic.py --stdout   # print one label, write nothing

These are committable fixtures; swap in real anonymized PDFs anytime — the harness
treats both identically.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz  # PyMuPDF

EVAL_DIR = Path(__file__).parent
SAMPLES = EVAL_DIR / "samples"
LABELS = EVAL_DIR / "labels"

# Page + layout constants (US Letter, single column).
PAGE_W, PAGE_H = 612, 792
LEFT = 72.0
RIGHT = 540.0
MARKER_X = 84.0
BULLET_TEXT_X = 96.0
BODY = 10.0
TITLE = 11.0
HEADING = 12.0
NAME = 18.0


def _len(text: str, size: float, bold: bool = False) -> float:
    return fitz.get_text_length(text, fontname="hebo" if bold else "helv", fontsize=size)


def _put(page, x: float, y: float, text: str, size: float, bold: bool = False) -> None:
    page.insert_text((x, y), text, fontsize=size, fontname="hebo" if bold else "helv")


def _put_right(page, y: float, text: str, size: float) -> None:
    _put(page, RIGHT - _len(text, size), y, text, size)


def _date_str(entry: dict) -> str | None:
    start, end = entry.get("start_date"), entry.get("end_date")
    if not start:
        return None
    sep = entry.get("date_sep", " - ")
    return f"{start}{sep}{end}" if end else start


def _render_bullets(page, entry: dict, marker: str, y: float) -> float:
    """Render an entry's bullets and return the y below them."""
    for bullet in entry.get("bullets", []):
        # "\n" in a bullet = a soft wrap: first visual line carries the marker,
        # the rest hang-indent with no marker (continuation).
        lines = bullet.split("\n")
        _put(page, MARKER_X, y, marker, BODY)
        _put(page, BULLET_TEXT_X, y, lines[0], BODY)
        y += 14
        for cont in lines[1:]:
            _put(page, BULLET_TEXT_X, y, cont, BODY)
            y += 14
    return y


def render_pdf(spec: dict) -> bytes:
    """Lay the spec out as a one-page PDF and return its bytes."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = 90.0

    _put(page, LEFT, y, spec["contact"]["name"], NAME, bold=True)
    y += 22
    contact = spec["contact"]
    bits = [contact[k] for k in ("email", "phone", "github", "linkedin") if contact.get(k)]
    _put(page, LEFT, y, "  |  ".join(bits), 9.0)
    y += 30  # wide gap -> vertical isolation signal for the first heading

    for section in spec["sections"]:
        if section.get("understated"):
            # Title-case, non-bold, body-size heading with no isolating gap: a
            # deliberately weak heading that should be HARD to detect.
            _put(page, LEFT, y, section["heading"], BODY)
            y += 15
        else:
            y += 8  # isolating gap above a normal heading
            _put(page, LEFT, y, section["heading"], HEADING, bold=True)
            y += 20

        if "skills" in section:
            for label, vals in section["skills"].items():
                _put(page, LEFT, y, f"{label.title()}: {', '.join(vals)}", BODY)
                y += 15
            y += 12
            continue

        for entry in section.get("entries", []):
            if entry.get("inline_meta"):
                # Title, org, and dates packed on ONE left-flowing line with
                # normal spacing -> no big right-gap for the date run to latch.
                parts = [entry["title"]]
                if entry.get("organization"):
                    parts.append(entry["organization"])
                date = _date_str(entry)
                if date:
                    parts.append(date)
                _put(page, LEFT, y, "  |  ".join(parts), TITLE, bold=True)
                y += 16
                y = _render_bullets(page, entry, spec["marker"], y)
                y += 8
                continue
            if entry.get("title"):
                _put(page, LEFT, y, entry["title"], TITLE, bold=True)
            date = _date_str(entry)
            if date:
                _put_right(page, y, date, BODY)
            y += 16
            if entry.get("organization") or entry.get("location"):
                if entry.get("inline_location") and entry.get("organization") and entry.get("location"):
                    # "Org, City, ST" on one left line — location is NOT a
                    # right-aligned run, so it must be recovered from inline text.
                    _put(page, LEFT, y, f'{entry["organization"]}, {entry["location"]}', BODY)
                else:
                    if entry.get("organization"):
                        _put(page, LEFT, y, entry["organization"], BODY)
                    if entry.get("location"):
                        _put_right(page, y, entry["location"], BODY)
                y += 16
            y = _render_bullets(page, entry, spec["marker"], y)
            y += 8
        y += 6

    return doc.tobytes()


def label_from_spec(spec: dict) -> dict:
    """Emit the ground-truth label (template shape) from the same spec."""
    out: dict = {"contact": dict(spec["contact"]), "sections": []}
    for section in spec["sections"]:
        if "skills" in section:
            out["sections"].append({"type": section["type"], "skills": section["skills"]})
            continue
        entries = []
        for entry in section.get("entries", []):
            e = {
                k: entry[k]
                for k in ("title", "organization", "location", "start_date", "end_date")
                if entry.get(k)
            }
            e["bullets"] = [b.replace("\n", " ") for b in entry.get("bullets", [])]
            entries.append(e)
        out["sections"].append({"type": section["type"], "entries": entries})
    return out


# --- The specs. Each is one resume; diverse on purpose. ---------------------
SPECS: list[dict] = [
    {
        "marker": "•",  # bullet •
        "contact": {"name": "Jane Doe", "email": "jane@example.com",
                    "github": "github.com/janedoe"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Software Engineering Intern", "organization": "FileByte LLC",
                 "location": "Los Angeles, CA", "start_date": "May 2025",
                 "end_date": "Aug 2025", "bullets": [
                     "Built reusable React components for the client dashboard",
                     "Integrated backend API endpoints and reduced load time"]}]},
            {"type": "skills", "heading": "SKILLS", "skills": {
                "languages": ["Python", "Java", "TypeScript"],
                "frameworks": ["React", "FastAPI"]}},
            {"type": "education", "heading": "EDUCATION", "entries": [
                {"title": "B.S. Computer Science", "organization": "State University",
                 "location": "Austin, TX", "start_date": "2021", "end_date": "2025",
                 "bullets": []}]},
        ],
    },
    {
        "marker": "-",
        "contact": {"name": "Alan Park", "email": "alan.park@mail.com",
                    "github": "github.com/alanp"},
        "sections": [
            {"type": "experience", "heading": "WORK EXPERIENCE", "entries": [
                {"title": "Backend Engineer", "organization": "Cloudly",
                 "start_date": "Jan 2023", "end_date": "Present", "bullets": [
                     "Designed a sharded Postgres schema serving 2M daily requests",
                     "Cut p99 latency by 40 percent through query batching"]},
                {"title": "Software Developer", "organization": "Initech",
                 "start_date": "Jun 2020", "end_date": "Dec 2022", "bullets": [
                     "Shipped a billing microservice in Go",
                     "Mentored two junior engineers"]}]},
            {"type": "skills", "heading": "TECHNICAL SKILLS", "skills": {
                "languages": ["Go", "Python", "SQL"],
                "tools": ["Docker", "Kubernetes", "AWS"]}},
        ],
    },
    {
        "marker": "▪",  # ▪
        "contact": {"name": "Priya Nair", "email": "priya@dev.io",
                    "linkedin": "linkedin.com/in/priyanair"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Full Stack Engineer", "organization": "Brightline",
                 "location": "Remote", "start_date": "Mar 2024", "bullets": [
                     "Led migration from REST to GraphQL across three services"]}]},
            {"type": "projects", "heading": "PROJECTS", "entries": [
                {"title": "OpenMetrics Dashboard", "start_date": "2024", "bullets": [
                     "Real-time charts over a 50GB time-series store",
                     "Open-sourced; 400+ GitHub stars"]}]},
            {"type": "skills", "heading": "SKILLS", "skills": {
                "languages": ["JavaScript", "Python"],
                "frameworks": ["Node", "GraphQL", "React"]}},
        ],
    },
    {
        "marker": "·",  # ·
        "contact": {"name": "Marcus Webb", "email": "mwebb@school.edu",
                    "github": "github.com/mwebb"},
        "sections": [
            {"type": "education", "heading": "EDUCATION", "entries": [
                {"title": "M.S. Computer Engineering", "organization": "Tech Institute",
                 "location": "Boston, MA", "start_date": "2022", "end_date": "2024",
                 "bullets": ["GPA 3.9; focus in distributed systems"]}]},
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Research Assistant", "organization": "Systems Lab",
                 "start_date": "Sep 2022", "end_date": "May 2024", "bullets": [
                     "Built a fault-tolerant consensus simulator in Rust",
                     "Co-authored a paper on Raft optimizations"]}]},
            {"type": "skills", "heading": "SKILLS", "skills": {
                "languages": ["Rust", "C++", "Python"]}},
        ],
    },
    {
        "marker": "•",
        "contact": {"name": "Sofia Reyes", "email": "sofia.reyes@inbox.com",
                    "github": "github.com/sreyes"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Platform Engineer", "organization": "DataForge",
                 "location": "Seattle, WA", "start_date": "Feb 2023",
                 "end_date": "Present", "bullets": [
                     "Owned the CI/CD pipeline migration to GitHub Actions"]},
                {"title": "DevOps Intern", "organization": "Nimbus",
                 "location": "Denver, CO", "start_date": "Jun 2022",
                 "end_date": "Dec 2022", "bullets": [
                     "Automated infrastructure provisioning with Terraform"]}]},
            {"type": "projects", "heading": "PROJECTS", "entries": [
                {"title": "kubelite", "bullets": [
                     "A minimal container scheduler written in Go"]}]},
        ],
    },
    {
        "marker": "-",
        "contact": {"name": "Tom Becker", "email": "tom@becker.dev",
                    "github": "github.com/tbecker"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Machine Learning Engineer", "organization": "VisionAI",
                 "location": "San Jose, CA", "start_date": "Aug 2021",
                 "end_date": "Present", "bullets": [
                     "Trained a detection model improving recall by 12 points",
                     "Deployed inference to edge devices with ONNX"]}]},
            {"type": "leadership", "heading": "LEADERSHIP", "entries": [
                {"title": "ACM Chapter President", "organization": "State University",
                 "start_date": "2020", "end_date": "2021", "bullets": [
                     "Organized a 200-person hackathon"]}]},
            {"type": "skills", "heading": "SKILLS", "skills": {
                "languages": ["Python", "C++"],
                "frameworks": ["PyTorch", "TensorFlow"]}},
        ],
    },
    {
        "marker": "•",
        "contact": {"name": "Grace Liu", "email": "grace.liu@corp.com",
                    "linkedin": "linkedin.com/in/graceliu"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Senior Software Engineer", "organization": "Quanta",
                 "location": "New York, NY", "start_date": "Apr 2019",
                 "end_date": "Present", "bullets": [
                     # wrapped bullet: spans two visual lines, one logical bullet
                     "Architected a multi-tenant event pipeline processing\n"
                     "billions of messages per day with exactly-once semantics",
                     "Reduced infra cost by 30 percent via autoscaling"]}]},
            {"type": "skills", "heading": "TECHNICAL SKILLS", "skills": {
                "languages": ["Java", "Scala", "Python"],
                "tools": ["Kafka", "Spark", "AWS"]}},
        ],
    },
    {
        "marker": "•",
        "contact": {"name": "Omar Said", "email": "omar@said.io",
                    "github": "github.com/osaid"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Junior Developer", "organization": "Webworks",
                 "start_date": "2024", "end_date": "Present", "bullets": [
                     "Maintained a Django monolith and added test coverage"]}]},
            {"type": "skills", "heading": "SKILLS", "skills": {
                "languages": ["Python", "JavaScript"]}},
        ],
    },
    # --- Adversarial-but-fair samples (009+). Stress documented weak spots so
    # the benchmark can score below 1.00 and reveal real parser gaps. ---
    {
        # 009 — INLINE metadata: title|org|dates on one line, no right-aligned
        # date run. Stresses title extraction (the run crutch is gone).
        "marker": "•",
        "contact": {"name": "Dana Kim", "email": "dana.kim@mail.com",
                    "github": "github.com/danakim"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Software Engineer", "organization": "Acme Corp",
                 "start_date": "2021", "end_date": "2023", "inline_meta": True,
                 "bullets": [
                     "Built an internal analytics service used company-wide",
                     "Reduced deploy time from 30 to 6 minutes"]}]},
            {"type": "skills", "heading": "SKILLS", "skills": {
                "languages": ["Python", "Go"]}},
        ],
    },
    {
        # 010 — UNDER-SEGMENTATION: an awards section of one-liner entries with
        # no dates and no bullets. The parser folds consecutive text lines into
        # one entry (documented "safer failure direction"); gold has three.
        "marker": "•",
        "contact": {"name": "Leo Fontaine", "email": "leo@fontaine.dev",
                    "github": "github.com/leof"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Software Engineer", "organization": "Hatch",
                 "location": "Chicago, IL", "start_date": "Jul 2021",
                 "end_date": "Present", "bullets": [
                     "Owned the notifications subsystem end to end"]}]},
            {"type": "awards", "heading": "AWARDS", "entries": [
                {"title": "Hackathon Winner 2022", "bullets": []},
                {"title": "Dean's List", "bullets": []},
                {"title": "Best Capstone Project", "bullets": []}]},
        ],
    },
    {
        # 011 — UNDERSTATED HEADINGS: Title-case, non-bold, body-size, tight
        # spacing. Likely below the heading threshold -> section(s) dropped.
        "marker": "-",
        "contact": {"name": "Ruth Adler", "email": "ruth.adler@inbox.com",
                    "github": "github.com/radler"},
        "sections": [
            {"type": "experience", "heading": "Experience", "understated": True,
             "entries": [
                {"title": "Data Engineer", "organization": "Streamline",
                 "location": "Portland, OR", "start_date": "Jan 2022",
                 "end_date": "Present", "bullets": [
                     "Built batch ETL jobs over a petabyte-scale warehouse"]}]},
            {"type": "skills", "heading": "Skills", "understated": True,
             "skills": {"languages": ["Python", "SQL", "Scala"]}},
        ],
    },
    {
        # 012 — UNCOMMON MARKER glyph (not in BULLET_MARKERS). Bullets are still
        # detectable by hanging indent, but the glyph leaks into the bullet text
        # since strip_marker doesn't know it -> attribution text mismatch.
        "marker": "»",
        "contact": {"name": "Wei Chen", "email": "wei.chen@corp.com",
                    "github": "github.com/weichen"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Frontend Engineer", "organization": "Pixelworks",
                 "location": "Remote", "start_date": "Mar 2023",
                 "end_date": "Present", "bullets": [
                     "Rebuilt the design system in TypeScript and Storybook",
                     "Improved Lighthouse performance score to 98"]}]},
            {"type": "skills", "heading": "SKILLS", "skills": {
                "languages": ["TypeScript", "CSS"]}},
        ],
    },
    {
        # 013 — INLINE LOCATION + "to" date separator. Org line is "Org, City, ST"
        # with no right-aligned run; date uses the word "to". Tests find_location
        # / find_date_range on un-separated text (should mostly hold post-fix).
        "marker": "•",
        "contact": {"name": "Maya Brooks", "email": "maya@brooks.io",
                    "github": "github.com/mbrooks"},
        "sections": [
            {"type": "experience", "heading": "EXPERIENCE", "entries": [
                {"title": "Site Reliability Engineer", "organization": "Northwind",
                 "location": "San Diego, CA", "start_date": "Jun 2022",
                 "end_date": "Aug 2024", "inline_location": True, "date_sep": " to ",
                 "bullets": [
                     "Ran the on-call rotation and cut paging volume by half"]}]},
            {"type": "skills", "heading": "SKILLS", "skills": {
                "languages": ["Python", "Bash"]}},
        ],
    },
]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--stdout" in argv:
        print(json.dumps(label_from_spec(SPECS[0]), indent=2))
        return 0

    SAMPLES.mkdir(exist_ok=True)
    LABELS.mkdir(exist_ok=True)
    for i, spec in enumerate(SPECS, start=1):
        stem = f"{i:03d}"
        (SAMPLES / f"{stem}.pdf").write_bytes(render_pdf(spec))
        (LABELS / f"{stem}.json").write_text(
            json.dumps(label_from_spec(spec), indent=2) + "\n"
        )
    print(f"Wrote {len(SPECS)} synthetic samples + labels to samples/ and labels/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
