"""Entry grouping tests — Phase 2."""
from app.parser.entries import group_entries


def test_groups_header_org_bullets_into_one_entry(experience_section_lines):
    result = group_entries(experience_section_lines)
    assert len(result) == 1
    entry = result[0]
    assert entry.title == "Software Engineer"
    assert entry.organization == "Google"
    assert entry.start_date is not None
    assert len(entry.bullets) == 2


def test_starts_new_entry_on_new_header(two_jobs_section_lines):
    result = group_entries(two_jobs_section_lines)
    assert len(result) == 2
    assert result[0].title == "Senior Engineer"
    assert result[1].title == "Junior Engineer"
    assert result[0].bullets == ["Did stuff"]
    assert result[1].bullets == ["Other work"]


def test_bold_org_line_stays_one_entry(bold_org_section_lines):
    # A bold org line at base indent must remain a secondary line, not a fake
    # second entry (regression for the emphasis-only boundary bug).
    result = group_entries(bold_org_section_lines, base_font_size=10.0)
    assert len(result) == 1
    entry = result[0]
    assert entry.title == "Software Engineer"
    assert entry.organization == "Google"
    assert len(entry.bullets) == 2


def test_bold_dated_second_job_still_splits(bold_two_jobs_section_lines):
    # Bold headers still split when each carries its own right-aligned date.
    result = group_entries(bold_two_jobs_section_lines, base_font_size=10.0)
    assert len(result) == 2
    assert result[0].bullets == ["Did stuff"]
    assert result[1].bullets == ["Other work"]


def test_inline_header_title_excludes_org_and_dates():
    # "Title | Org | Dates" packed on one line (no right-aligned run). The title
    # must be just the role, so bullets attribute to the right entry key.
    from app.schemas.primitives import BBox, Line, Word

    def W(text: str, x: float) -> Word:
        return Word(text=text, bbox=BBox(x0=x, y0=100, x1=x + len(text) * 6, y1=110), page=1)

    # uniform small gaps -> no right-aligned date run
    toks = ["Software", "Engineer", "|", "Acme", "Corp", "|", "2021", "-", "2023"]
    words, x = [], 72.0
    for t in toks:
        words.append(W(t, x))
        x += len(t) * 6 + 6
    header = Line(words=words, page=1)
    bullet = Line(
        words=[
            Word(text="•", bbox=BBox(x0=96, y0=115, x1=102, y1=125), page=1),
            Word(text="Shipped", bbox=BBox(x0=108, y0=115, x1=150, y1=125), page=1),
            Word(text="it", bbox=BBox(x0=156, y0=115, x1=168, y1=125), page=1),
        ],
        page=1,
    )
    result = group_entries([header, bullet])
    assert len(result) == 1
    assert result[0].title == "Software Engineer"
    assert result[0].bullets == ["Shipped it"]


def test_right_aligned_location_stays_one_entry(location_vs_date_section_lines):
    # A right-aligned LOCATION on the org line must NOT trip the date-run
    # boundary: only a right-aligned DATE run opens a new entry. The org line
    # stays a secondary line, and its location/org are extracted cleanly.
    result = group_entries(location_vs_date_section_lines)
    assert len(result) == 1
    entry = result[0]
    assert entry.title == "Software Engineer"
    assert entry.organization == "Google"
    assert entry.location == "Mountain View, CA"
    assert len(entry.bullets) == 2
