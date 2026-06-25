"""Field-parsing tests — Phase 2 skills parsing."""
from app.parser.fields import parse_skills


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
