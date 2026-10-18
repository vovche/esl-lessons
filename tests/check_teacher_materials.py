"""Check calendar coverage, print freshness and separation from the public site."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_pages import prepare


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_timing(text, path):
    modes = {mode: [] for mode in "ABCD"}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            match = re.match(r"## (?:Сценарій )?([ABCD])\b", line)
            current = match[1] if match else None
        if current:
            match = re.match(r"\|\s*(\d+)\s*[-–—]\s*(\d+)", line)
            if match:
                modes[current].append(tuple(map(int, match.groups())))
            elif not line.startswith("|"):
                modes[current].extend(tuple(map(int, pair)) for pair in
                                      re.findall(r"\b(\d+)\s*[-–—]\s*(\d+)\s*хв:", line))
    for mode, intervals in modes.items():
        assert intervals and intervals[0][0] == 0, (path, mode)
        cursor = 0
        for start, end in intervals:
            assert start == cursor and end > start, (path, mode, intervals)
            cursor = end
        assert cursor == (45 if mode in "AC" else 12 if mode == "D" and "/7/" in str(path) else 15), (path, mode, cursor)


def main():
    count = 0
    pdf_count = 0
    for grade, expected in ((6, 123), (7, 140), (9, 121)):
        folder = ROOT / "teacher" / str(grade)
        source = json.loads((folder / "source-plan.json").read_text())
        manifest = json.loads((folder / "manifest.json").read_text())
        printed = json.loads((folder / "print-manifest.json").read_text())
        reviewed = json.loads((folder / "quality-review.json").read_text())
        lessons, entries = source["lessons"], manifest["lessons"]
        assert len(lessons) == len(entries) == len(printed["lessons"]) == expected, grade
        assert reviewed["grade"] == grade and len(reviewed["lessons"]) == expected, grade
        reviews = {entry["number"]: entry for entry in reviewed["lessons"]}
        assert len(reviews) == expected, grade
        assert [x["number"] for x in entries] == list(range(1, expected+1)), grade
        assert len({x["date"] for x in entries}) == expected, grade
        sources = {x["number"]: x for x in lessons}
        pdf_entries = {x["directory"]: x for x in printed["lessons"]}
        for entry in entries:
            original = sources[entry["number"]]
            assert entry["date"] == original["date"], entry
            assert entry["topic"] == original["topic"], entry
            lesson = folder / entry["directory"]
            assert lesson.resolve().parent == folder.resolve(), lesson
            review = reviews[entry["number"]]
            assert review["date"] == entry["date"] and review["topic"] == entry["topic"], entry
            reviewed_files = {"lesson.md", "handout.md", "key.md"}
            if (lesson/"recovery-handout.md").exists():
                reviewed_files.add("recovery-handout.md")
            assert set(review["source_sha256"]) == reviewed_files, lesson
            for name in reviewed_files:
                assert digest(lesson/name) == review["source_sha256"][name], f"Stale quality review: {lesson/name}"
            for name in ("lesson.md", "handout.md", "key.md", "report.md", "games.md"):
                assert (lesson / name).stat().st_size > 100, lesson / name
            games = (lesson/"games.md").read_text()
            game_headings = re.findall(r"^## (?:[12]\s*[.·—–:]|(?:Гра|Симуляція)\s*[12](?:[.\s—–·:]|$))",
                                       games, flags=re.MULTILINE | re.IGNORECASE)
            assert len(game_headings) == 2, f"Expected two game simulations: {lesson}"
            text = (lesson / "lesson.md").read_text()
            assert entry["date"] in text, lesson
            check_timing(text, lesson)
            assert not re.search(r"https?://(?:meet\.google\.com|school\.mriia\.gov\.ua)",
                                 "\n".join(p.read_text() for p in lesson.glob("*.md"))), lesson
            pdf_entry = pdf_entries[f"{grade}/{lesson.name}"]
            variants = [("handout.pdf", ["handout.md"]),
                        ("teacher.pdf", ["lesson.md", "key.md", "report.md"]),
                        ("games.pdf", ["games.md"])]
            if (lesson/"recovery-handout.md").exists():
                variants.append(("recovery-handout.pdf", ["recovery-handout.md"]))
            assert set(pdf_entry["files"]) == {v[0] for v in variants}, lesson
            for pdf, names in variants:
                target = lesson / pdf
                info = pdf_entry["files"][pdf]
                assert target.read_bytes().startswith(b"%PDF-"), target
                assert info["pages"] > 0 and digest(target) == info["sha256"], target
                current = hashlib.sha256("\n".join((lesson/name).read_text() for name in names).encode()).hexdigest()
                assert current == info["source_sha256"], f"Stale PDF: {target}"
                pdf_count += 1
            count += 1
        snapshot = (folder / "source-plan.json").read_text()
        assert not re.search(r"https?://(?:meet\.google\.com|school\.mriia\.gov\.ua)", snapshot), folder
    for page in [ROOT/"index.html", *ROOT.glob("[679]/**/*.html")]:
        assert not re.search(r'(?:href|src)=[\"\'][^\"\']*(?:teacher/|teacher%2[fF])', page.read_text()), page
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    assert 'scripts/prepare_pages.py --output "$RUNNER_TEMP/esl-pages"' in workflow
    assert "path: ${{ runner.temp }}/esl-pages" in workflow
    # Exercise the same staging function on a small fixture, including a symlink.
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "repo"
        source.mkdir()
        (source/"teacher").mkdir()
        (source/"teacher"/"secret.md").write_text("service data")
        (source/"index.html").write_text("catalog")
        (source/".nojekyll").touch()
        (source/"alias").symlink_to(source/"teacher", target_is_directory=True)
        destination = Path(tmp)/"site"
        prepare(source, destination)
        assert (destination/"index.html").read_text() == "catalog"
        assert (destination/".nojekyll").exists()
        assert not (destination/"teacher").exists() and not (destination/"alias").exists()
    print(f"Teacher materials OK: {count} calendar packs, {pdf_count} current PDFs; public staging excludes teacher/.")


if __name__ == "__main__":
    main()
