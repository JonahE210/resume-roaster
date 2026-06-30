"""Field-parsing tests — Phase 2 skills parsing."""
from app.parser.fields import (
    find_contact,
    find_date_range,
    find_location,
    parse_skills,
)


def test_find_location_simple_city_state():
    assert find_location("Mountain View, CA") == "Mountain View, CA"


def test_find_location_multiword_city():
    assert find_location("San Francisco, CA") == "San Francisco, CA"
    assert find_location("New York, NY") == "New York, NY"


def test_find_location_does_not_span_preceding_words():
    # A lowercase word before the city breaks the title-case run, so the org/title
    # text must NOT be swallowed into the location.
    assert find_location("Software Engineer at Mountain View, CA") == "Mountain View, CA"


def test_find_location_remote():
    assert find_location("Remote") == "Remote"


def test_find_location_none_when_absent():
    assert find_location("Built scalable services") is None


def test_find_date_range_real_ranges():
    assert find_date_range("May 2025 - Aug 2025") == ("May 2025", "Aug 2025")
    assert find_date_range("2024 - Present") == ("2024", "Present")
    assert find_date_range("Jan 2024 – May 2024") == ("Jan 2024", "May 2024")


def test_find_date_range_ignores_non_year_numbers():
    # Stray 4-digit numbers that aren't plausible years must not parse as dates.
    assert find_date_range("Handled 1234 requests") == (None, None)
    assert find_date_range("Scaled to 4096 nodes") == (None, None)


def test_find_contact_pulls_fields():
    text = "jane@example.com | (415) 555-0100 | linkedin.com/in/jane | github.com/jane"
    contact = find_contact(text)
    assert contact["email"] == "jane@example.com"
    assert contact["phone"] == "(415) 555-0100"
    assert contact["linkedin"] == "linkedin.com/in/jane"
    assert contact["github"] == "github.com/jane"


def test_parse_skills_label_value_lines(skills_section_lines):
    skills = parse_skills(skills_section_lines)
    assert skills == {
        "languages": ["Java", "Python"],
        "frameworks": ["React", "FastAPI"],
    }


def test_parse_skills_preserves_compound():
    from app.schemas.primitives import BBox, Line, Word

    def line(text: str) -> Line:
        return Line(
            words=[Word(text=text, bbox=BBox(x0=0, y0=0, x1=200, y1=10), page=1)],
            page=1,
        )

    skills = parse_skills([line("DevOps: CI/CD, Docker"), line("Web: React / Node")])
    assert skills == {"devops": ["CI/CD", "Docker"], "web": ["React", "Node"]}
    # Bare in-word slashes survive intact.
    assert parse_skills([line("Networking: TCP/IP")]) == {"networking": ["TCP/IP"]}


def test_parse_skills_splits_on_first_colon_only():
    from app.schemas.primitives import BBox, Line, Word

    line = Line(
        words=[
            Word(text="Tools", bbox=BBox(x0=0, y0=0, x1=30, y1=10), page=1),
            Word(text="/", bbox=BBox(x0=32, y0=0, x1=36, y1=10), page=1),
            Word(text="Frameworks:", bbox=BBox(x0=38, y0=0, x1=110, y1=10), page=1),
            Word(text="React;", bbox=BBox(x0=112, y0=0, x1=150, y1=10), page=1),
            Word(text="Node", bbox=BBox(x0=152, y0=0, x1=180, y1=10), page=1),
        ],
        page=1,
    )
    assert parse_skills([line]) == {"tools / frameworks": ["React", "Node"]}
