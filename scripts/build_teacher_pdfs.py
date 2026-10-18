"""Render repository-only Markdown packs to A4 handouts and teacher copies.

Requires reportlab (also used by build_homework_pdfs.py). No browser or network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
rl_config.invariant = True
for name, filename in (("Teacher", "DejaVuSans.ttf"), ("TeacherBold", "DejaVuSans-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(ROOT / "assets/fonts/dejavu" / filename)))
pdfmetrics.registerFontFamily("Teacher", normal="Teacher", bold="TeacherBold",
                            italic="Teacher", boldItalic="TeacherBold")


class RuledLine(Flowable):
    def __init__(self, label=""):
        super().__init__()
        self.label = label
        self.height = 22

    def wrap(self, width, height):
        self.width = width
        return width, self.height

    def draw(self):
        self.canv.setFont("Teacher", 10)
        self.canv.setStrokeColor(colors.HexColor("#888888"))
        self.canv.setLineWidth(.4)
        self.canv.drawString(0, 6, self.label)
        start = 17 if self.label else 0
        self.canv.line(start, 5, self.width, 5)


def normalize(value):
    value = value.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"_{36,}", "_" * 35, value)


def inline(value):
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = escape(normalize(value))
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    return value


def markdown(text, *, student):
    size = 10.5 if student else 9.5
    body = ParagraphStyle("Body", fontName="Teacher", fontSize=size, leading=size * 1.43,
                          spaceAfter=6, splitLongWords=True)
    styles = {n: ParagraphStyle(f"H{n}", parent=body, fontName="TeacherBold",
                                fontSize=17 if n == 1 else 12 if n == 2 else 10.5,
                                leading=21 if n == 1 else 16, spaceBefore=10,
                                spaceAfter=7, keepWithNext=True) for n in range(1, 7)}
    glyphs = pdfmetrics.getFont("Teacher").face.charToGlyph
    missing = {c for c in normalize(text) if not c.isspace() and ord(c) not in glyphs}
    if missing:
        raise ValueError(f"Unsupported print glyphs: {sorted(missing)}")
    story, buffer, headers = [], [], None
    def flush():
        if buffer:
            story.append(Paragraph(inline(" ".join(buffer)), body))
            buffer.clear()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            flush()
            continue
        if re.fullmatch(r"[-*]{3,}", line) or line.startswith("```"):
            flush()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)", line)
        if heading:
            flush()
            headers = None
            if student and "Додаток L" in heading[2]:
                story.append(PageBreak())
            story.append(Paragraph(inline(heading[2]), styles[len(heading[1])]))
        elif line.startswith("|"):
            flush()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue
            if headers is None:
                headers = cells
                continue
            if len(cells) == 2:
                story.append(Paragraph(f"<b>{inline(cells[0])}</b> - {inline(cells[1])}", body))
                continue
            # Schedule tables become labelled blocks, avoiding narrow text columns.
            parts = [f"<b>{inline(headers[i] if i < len(headers) else str(i + 1))}:</b> {inline(c)}"
                     for i, c in enumerate(cells)]
            story.append(Paragraph("<br/>".join(parts), body))
            story.append(Spacer(1, 3))
        elif re.fullmatch(r"(?:\d+[.)]\s*)?_{8,}", line):
            flush()
            story.append(RuledLine(line.split("_")[0].strip()))
        elif re.match(r"^(?:[-*+] |\d+[.)] |>)", line):
            flush()
            story.append(Paragraph(inline(line.lstrip("> ")), body))
        else:
            buffer.append(line)
    flush()
    if student:
        for i in range(len(story)-1):
            current, following = story[i:i+2]
            if isinstance(current, Paragraph) and isinstance(following, RuledLine):
                current.keepWithNext = True
            if not isinstance(current, Paragraph) or not isinstance(following, Paragraph):
                continue
            a, b = current.getPlainText(), following.getPlainText()
            answer = b.startswith(("Answer:", "Відповідь:"))
            if b.startswith("A)") or (a.startswith("A)") and answer):
                current.keepWithNext = True
            if re.match(r"^\d+[.)] ", a) and (answer or b.startswith("___")):
                current.keepWithNext = True
    return story


def render(directory):
    directory = Path(directory)
    result = {"directory": str(directory.relative_to(ROOT / "teacher")), "files": {}}
    variants = [(True, ["handout.md"], "handout.pdf"),
                (False, ["lesson.md", "key.md", "report.md"], "teacher.pdf")]
    if (directory/"recovery-handout.md").exists():
        variants.append((True, ["recovery-handout.md"], "recovery-handout.pdf"))
    if (directory/"games.md").exists():
        variants.append((False, ["games.md"], "games.pdf"))
    for student, names, output in variants:
        pages = []
        label = ("Ігрові симуляції для вчителя" if output == "games.pdf" else
                 "Резервний учнівський варіант" if output.startswith("recovery") else
                 "Учнівська роздатка" if student else "План, сценарії, ключ і форма звіту")
        def footer(canvas, doc):
            pages.append(doc.page)
            canvas.saveState()
            canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
            canvas.line(17*mm, 15*mm, A4[0]-17*mm, 15*mm)
            canvas.setFont("Teacher", 7)
            canvas.drawString(17*mm, 11*mm, f"{result['directory']} | {label}")
            canvas.drawRightString(A4[0]-17*mm, 11*mm, str(doc.page))
            canvas.restoreState()
        story = []
        inputs = [(directory/name).read_text() for name in names]
        for i, source in enumerate(inputs):
            if i:
                story.append(PageBreak())
            story.extend(markdown(source, student=student))
        target = directory/output
        doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=17*mm,
                                rightMargin=17*mm, topMargin=16*mm, bottomMargin=21*mm,
                                title=f"{result['directory']} - {label}", author="ESL Lessons")
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        source_hash = hashlib.sha256("\n".join(inputs).encode()).hexdigest()
        result["files"][output] = {"pages": len(pages), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                                  "source_sha256": source_hash}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grade", choices=["6", "7", "9"], action="append")
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--lesson", help="Render only one three-digit lesson directory")
    args = parser.parse_args()
    for grade in args.grade or ["6", "7", "9"]:
        dirs = sorted((ROOT/"teacher"/grade).glob("[0-9][0-9][0-9]"))
        if args.lesson:
            dirs = [p for p in dirs if p.name == args.lesson]
        if not dirs:
            raise SystemExit(f"No lesson packs found for grade {grade}")
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            entries = list(pool.map(render, dirs))
        if not args.lesson:
            (ROOT/"teacher"/grade/"print-manifest.json").write_text(
                json.dumps({"grade": int(grade), "lessons": entries}, ensure_ascii=False, indent=2)+"\n")
        print(f"Grade {grade}: {len(entries)} packs, {sum(len(e['files']) for e in entries)} PDFs")


if __name__ == "__main__":
    main()
