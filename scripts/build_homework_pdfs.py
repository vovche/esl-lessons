"""Build print-ready student sheets and teacher keys from portable test JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from archive_naurok_tests import ROOT, dump, points_label, validate

rl_config.invariant = True
FONT_DIR = ROOT / 'assets/fonts/dejavu'
pdfmetrics.registerFont(TTFont('ESL', str(FONT_DIR / 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('ESL-Bold', str(FONT_DIR / 'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('ESL', normal='ESL', bold='ESL-Bold', italic='ESL', boldItalic='ESL-Bold')

STYLES = {
    'kicker': ParagraphStyle('kicker', fontName='ESL-Bold', fontSize=8, leading=11, textColor=colors.HexColor('#444444'), spaceAfter=5),
    'title': ParagraphStyle('title', fontName='ESL-Bold', fontSize=13, leading=17, spaceAfter=8),
    'meta': ParagraphStyle('meta', fontName='ESL', fontSize=9, leading=13, spaceAfter=7),
    'body': ParagraphStyle('body', fontName='ESL', fontSize=11, leading=15.5, alignment=TA_LEFT, spaceAfter=5),
    'question': ParagraphStyle('question', fontName='ESL-Bold', fontSize=10, leading=14, spaceAfter=4),
    'option': ParagraphStyle('option', fontName='ESL', fontSize=10.5, leading=14.5, leftIndent=8, spaceAfter=3),
    'reading': ParagraphStyle('reading', fontName='ESL', fontSize=10.5, leading=15),
    'answer': ParagraphStyle('answer', fontName='ESL-Bold', fontSize=10.5, leading=15, spaceAfter=8),
}


def clean(text: str) -> str:
    # Keep spelling, IPA and apostrophes; normalize dash glyphs for print portability.
    return text.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')


def paragraph(text: str, style: str = 'body') -> Paragraph:
    return Paragraph(escape(clean(text)).replace('\n', '<br/>'), STYLES[style])


def input_hash(document: dict) -> str:
    # Launch status, remote IDs and online deadlines do not change a paper test.
    fields = ('id', 'title', 'grade', 'source_title', 'questions', 'total_points')
    return hashlib.sha256(dump({k: document[k] for k in fields}).encode()).hexdigest()


def reading_parts(prompt: str) -> tuple[str | None, str]:
    if not prompt.startswith('Прочитай текст'):
        return None, prompt
    parts = [p.strip() for p in prompt.split('\n\n') if p.strip()]
    if len(parts) >= 3 and parts[0] == 'Прочитай текст і визнач правильну відповідь.':
        return '\n\n'.join(parts[1:-1]), parts[-1]
    if len(parts) == 2:
        text = re.sub(r'^Прочитай текст[.:]\s*', '', parts[0])
        if text != parts[0]:
            return text, parts[1]
    return None, prompt


class AnswerLines(Flowable):
    def __init__(self, lines: int):
        super().__init__()
        self.lines = lines
        self.height = lines * 19 + 3

    def wrap(self, available_width, available_height):
        self.width = available_width
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(colors.HexColor('#888888'))
        self.canv.setLineWidth(.45)
        for line in range(self.lines):
            y = self.height - 16 - line * 19
            self.canv.line(0, y, self.width, y)


def check_glyphs(document: dict) -> None:
    strings = [document['title'], document['source_title'], document['id']]
    for q in document['questions']:
        strings.extend([q['prompt'], *q.get('options', []), *q.get('answers', [])])
    cmap = pdfmetrics.getFont('ESL').face.charToGlyph
    missing = sorted({c for c in clean(''.join(strings)) if not c.isspace() and ord(c) not in cmap})
    assert not missing, f'Missing font glyphs in {document["id"]}: {missing}'


def title(document: dict) -> str:
    base = 'Jolly Phonics' if document['source_lesson'].endswith('/jolly-phonics/index.html') else document['source_title']
    suffix = re.search(r'(?:Units?|Groups?)\s+\d+(?:[–-]\d+)?', document['title'])
    if suffix:
        return base + ' - ' + suffix.group()
    part = int(document['id'].rsplit('-', 1)[1])
    return base + (f' - Частина {part}' if part > 1 else '')


def build(document: dict, destination: Path, *, key: bool) -> int:
    check_glyphs(document)
    pages = []
    identifier = document['id']
    role = 'КЛЮЧ ДЛЯ ВЧИТЕЛЯ' if key else 'ЗАВДАННЯ ДЛЯ УЧНЯ'

    def page_footer(canvas, doc):
        pages.append(doc.page)
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#aaaaaa'))
        canvas.setLineWidth(.4)
        canvas.line(17 * mm, 15 * mm, A4[0] - 17 * mm, 15 * mm)
        canvas.setFont('ESL', 7)
        canvas.setFillColor(colors.HexColor('#444444'))
        canvas.drawString(17 * mm, 11 * mm, identifier)
        canvas.drawRightString(A4[0] - 17 * mm, 11 * mm, f'{role} | {doc.page}')
        if doc.page > 1:
            running = clean(title(document))
            while pdfmetrics.stringWidth(running, 'ESL', 7) > A4[0] - 80 * mm:
                running = running[:-4] + '...'
            canvas.drawString(17 * mm, A4[1] - 10 * mm, running)
            canvas.drawRightString(A4[0] - 17 * mm, A4[1] - 10 * mm,
                                  'Прізвище: __________________' if not key else 'КЛЮЧ ДЛЯ ВЧИТЕЛЯ')
        canvas.restoreState()

    doc = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=17 * mm,
                            leftMargin=17 * mm, topMargin=16 * mm, bottomMargin=20 * mm,
                            title=clean(document['title']) + (' - ключ' if key else ' - завдання'),
                            author='ESL lessons', subject=identifier, pageCompression=1)
    story = [paragraph(role, 'kicker'), paragraph(title(document), 'title'),
             paragraph(f'{document["grade"]} клас | Максимум: {document["total_points"]} балів', 'meta')]
    if key:
        story += [paragraph('Літери відповідають варіантам учнівського PDF. Кожне запитання оцінюється в указані бали; сума - 10.', 'meta')]
    else:
        story += [paragraph('Ім’я та прізвище: __________________________________________', 'body'),
                  paragraph('Клас: __________  Дата: __________________', 'meta'),
                  paragraph('Обери одну відповідь у завданнях із варіантами. У решті завдань напиши відповідь самостійно.', 'meta')]
    story.append(Spacer(1, 6))
    readings = [reading_parts(q['prompt'])[0] for q in document['questions']]
    printed_readings = set()
    def question_block(i, q):
        _, prompt = reading_parts(q['prompt'])
        prompt_html = escape(clean(prompt)).replace('\n', '<br/>')
        block = [Paragraph(f'<b>{i}.</b> {prompt_html} '
                           f'<font size="9">({points_label(q["points"])})</font>', STYLES['body'])]
        if key:
            if q['type'] == 'choice':
                answer = f'{chr(65 + q["key"])}. {q["options"][q["key"]]}'
            else:
                answer = ' / '.join(q['answers'])
            block.append(paragraph('Відповідь: ' + answer, 'answer'))
        elif q['type'] == 'choice':
            block.extend(paragraph(f'[ ] {chr(65 + j)}. {option}', 'option') for j, option in enumerate(q['options']))
        else:
            expected = max(len(answer) for answer in q['answers'])
            block.append(AnswerLines(2 if expected > 65 else 1))
        block.append(Spacer(1, 8 if key else 10))
        return block

    i = 0
    while i < len(document['questions']):
        reading = readings[i]
        block = []
        end = i + 1
        if reading and reading not in printed_readings and not key:
            while end < len(readings) and readings[end] == reading:
                end += 1
            related = [str(j + 1) for j, text in enumerate(readings) if text == reading]
            box = Table([[paragraph(reading, 'reading')]], colWidths=[A4[0] - 34 * mm - 12])
            box.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), .5, colors.HexColor('#999999')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            block += [paragraph('Текст до запитань ' + ', '.join(related), 'question'), box, Spacer(1, 8)]
            printed_readings.add(reading)
        for j in range(i, end):
            block += question_block(j + 1, document['questions'][j])
        group = Table([[block]], colWidths=[A4[0] - 34 * mm - 12])
        group.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(group)
        i = end
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return max(pages)


def write_print_catalog(index: dict) -> None:
    lines = ['# Тести для друку', '',
             'Чорно-білий A4, масштаб друку 100%. Учнівські файли не містять відповідей; ключі призначені для вчителя.', '',
             'Файли лежать у папках уроків перевірки ДЗ, після відповідних тем. [Формат і правила оновлення](HOMEWORK_TESTS.md).', '']
    for grade in (6, 7, 9):
        lines += [f'## {grade} клас', '', '| Тест | Завдання для учня | Ключ для вчителя |', '|---|---|---|']
        for entry in index['tests']:
            if not entry['source_lesson'].startswith(f'{grade}/') or 'pdf' not in entry:
                continue
            label = entry['title'].replace('|', '\\|')
            lines.append(f'| {label} | [PDF]({entry["pdf"]}) | [PDF]({entry["answer_key_pdf"]}) |')
        lines.append('')
    (ROOT / 'PRINT_TESTS.md').write_text('\n'.join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, help='Generate a first review batch only')
    parser.add_argument('--ids', nargs='+', help='Regenerate selected portable test IDs')
    args = parser.parse_args()
    index_path = ROOT / 'homework-tests.json'
    index = json.loads(index_path.read_text())
    entries = index['tests'][:args.limit] if args.limit else index['tests']
    if args.ids:
        entries = [entry for entry in entries if entry['id'] in args.ids]
        assert {entry['id'] for entry in entries} == set(args.ids), 'unknown test ID'
    previous_path = ROOT / 'homework-pdfs.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {'tests': []}
    records = {r['id']: r for r in previous['tests']}
    for entry in entries:
        source = ROOT / entry['json']
        document = json.loads(source.read_text())
        validate(document)
        fingerprint = input_hash(document)
        record = {'id': document['id'], 'source': entry['json'], 'input_sha256': fingerprint}
        for role in ('student', 'teacher'):
            output = source.with_suffix('.pdf') if role == 'student' else source.with_name(source.stem + '-key.pdf')
            count = build(document, output, key=role == 'teacher')
            record[role] = {'path': output.relative_to(ROOT).as_posix(), 'pages': count,
                            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
            entry['pdf' if role == 'student' else 'answer_key_pdf'] = output.relative_to(ROOT).as_posix()
        records[document['id']] = record
    ROOT.joinpath('homework-pdfs.json').write_text(dump({
        'schema_version': 1, 'page_size': 'A4', 'test_count': len(records),
        'tests': [records[key] for key in sorted(records)],
    }))
    index_path.write_text(dump(index))
    write_print_catalog(index)
    counts = Counter(r[role]['pages'] for r in records.values() for role in ('student', 'teacher'))
    print(f'Generated {len(entries) * 2} PDFs; page counts: {dict(counts)}')


if __name__ == '__main__':
    main()
