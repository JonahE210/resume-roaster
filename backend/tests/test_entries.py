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


def test_right_aligned_location_mis_splits_entry(location_vs_date_section_lines):
    # KNOWN ISSUE (Phase 2 watch-item): a right-aligned location on the org line
    # trips the date-run boundary -> spurious entry. Expected 1 entry once the
    # 2<->3 loop fixes location-vs-date; update this assertion when fixed.
    result = group_entries(location_vs_date_section_lines)
    assert len(result) == 2  # buggy-but-current; should become 1 after the fix
