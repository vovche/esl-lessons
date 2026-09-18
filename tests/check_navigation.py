from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.items.append({key: value or "" for key, value in attrs})


def links(path: Path) -> list[dict[str, str]]:
    parser = Links()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.items


def has(items: list[dict[str, str]], href: str, role: str | None = None) -> bool:
    return any(item.get("href") == href and (role is None or item.get("data-site-nav") == role) for item in items)


root_links = links(ROOT / "index.html")
grades = sorted(path for path in ROOT.iterdir() if path.is_dir() and path.name.isdigit())
assert grades, "no numeric grade directories found"

for grade in grades:
    grade_index = grade / "index.html"
    assert grade_index.is_file(), f"/{grade.name}/ must have index.html"
    assert has(root_links, f"{grade.name}/", "grade"), f"root catalog must link to /{grade.name}/"

    grade_links = links(grade_index)
    assert has(grade_links, "../", "root"), f"/{grade.name}/ must link back to root"

    lessons = sorted(path for path in grade.iterdir() if path.is_dir() and (path / "index.html").is_file())
    assert lessons, f"/{grade.name}/ has no lessons"
    for lesson in lessons:
        assert has(root_links, f"{grade.name}/{lesson.name}/"), f"root catalog must list /{grade.name}/{lesson.name}/"
        assert has(grade_links, f"{lesson.name}/"), f"/{grade.name}/ must list {lesson.name}"
        lesson_links = links(lesson / "index.html")
        assert has(lesson_links, "../", "grade"), f"/{grade.name}/{lesson.name}/ must link to its grade page"
        assert has(lesson_links, "../../", "root"), f"/{grade.name}/{lesson.name}/ must link to root"

print(f"navigation contract: PASS ({len(grades)} grades)")
