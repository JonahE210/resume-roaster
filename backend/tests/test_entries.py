"""Entry grouping tests — Phase 2."""
import pytest


@pytest.mark.xfail(reason="Phase 2: implement entries.group_entries segmentation")
def test_groups_header_org_bullets_into_one_entry():
    raise AssertionError("Build a fixture section and assert one Entry with title/org/bullets.")


@pytest.mark.xfail(reason="Phase 2: new entry begins at new header pattern")
def test_starts_new_entry_on_new_header():
    raise AssertionError("Two jobs -> two entries.")
