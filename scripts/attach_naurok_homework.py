"""Render verified Naurok homework receipts into lesson footers.

The manifests contain external IDs observed in the browser. This script only
updates local HTML; it never creates or changes tests on Naurok.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r'<p\b(?=[^>]*\bdata-naurok-homework(?:[\s=>]))[^>]*>.*?</p>', re.S)


def ready_tests(lesson: dict) -> list[dict]:
    return [test for test in lesson.get('tests', [])
            if test.get('status') in ('homework_created', 'published', 'published_pending_homework_daily_limit')
            and test.get('verified') is True]


def validate_test(test: dict) -> None:
    assert test.get('points') == 10, f"expected 10 raw points: {test.get('test_id')}"
    weights = test.get('question_points')
    if weights is not None:
        assert all(isinstance(weight, int) and weight > 0 for weight in weights), 'invalid question weight'
        assert sum(weights) == 10 and len(set(weights)) > 1, 'expected progressive weights summing to 10'
    if test.get('deadline'):
        expected_deadline = '2027-01-03T23:00' if test.get('semester') == 1 else '2027-06-01T23:00'
        assert test['deadline'] == expected_deadline, 'semester/deadline mismatch'
    test_id = str(test['test_id'])
    assert test_id.isdigit(), 'invalid recorded test ID'
    link = urlparse(test['test_url'])
    assert link.scheme == 'https' and link.netloc == 'naurok.com.ua' and test_id in link.path, 'invalid test URL'
    if test.get('status') != 'homework_created':
        return
    homework_id = str(test['homework_id'])
    assert homework_id.isdigit(), 'invalid recorded homework ID'
    code = str(test['code']).replace(' ', '')
    assert code.isdigit(), 'invalid recorded join code'
    student = urlparse(test['student_url'])
    assert (student.scheme, student.netloc, student.path) == ('https', 'naurok.ua', '/test/join')
    assert parse_qs(student.query).get('gamecode') == [code], 'join URL/code mismatch'
    for key, identity in [('test_url', test_id), ('teacher_homework_url', homework_id)]:
        link = urlparse(test[key])
        assert link.scheme == 'https' and link.netloc == 'naurok.com.ua', f'invalid {key}'
        assert identity in link.path, f'wrong ID in {key}'
        if key == 'teacher_homework_url':
            assert link.path == f'/test-beta/homework/{homework_id}', 'homework creation form is not a saved assignment'


def render_footer(tests: list[dict], lesson_path: str | None = None, root: Path = ROOT) -> str:
    for test in tests:
        validate_test(test)
    links = []
    for index, test in enumerate(tests, 1):
        if test.get('source_lesson_title'):
            links.append('Перевірка ДЗ за темою «' + html.escape(test['source_lesson_title']) + '».')
        if test.get('status') != 'homework_created':
            label = 'Тест для самоперевірки'
            if len(tests) > 1:
                label += f' · частина {index}'
            links.append(f'<a href="{html.escape(test["test_url"], quote=True)}" target="_blank" '
                         f'rel="noopener noreferrer">{label}</a> (максимум 10 балів). '
                         'Посилання на домашнє завдання буде додано згодом; '
                         'самоперевірка не надсилає результат учителю.')
        else:
            label = 'Домашнє завдання на «На Урок»'
            if len(tests) > 1:
                label += f' · частина {index}'
            links.append(
                f'<a href="{html.escape(test["student_url"], quote=True)}" target="_blank" '
                f'rel="noopener noreferrer">{label}</a> '
                f'(<a href="{html.escape(test["test_url"], quote=True)}" target="_blank" '
                f'rel="noopener noreferrer">переглянути тест</a>; максимум 10 балів)'
            )
        if test.get('content_path') and lesson_path:
            content = Path(os.path.relpath(test['content_path'], Path(lesson_path).parent))
            links.append(f'<a href="{html.escape(content.with_suffix(".md").as_posix(), quote=True)}">'
                         'Версія без відповідей (Markdown)</a>.')
            if (root / test['content_path']).with_suffix('.pdf').is_file():
                links.append(f'<a href="{html.escape(content.with_suffix(".pdf").as_posix(), quote=True)}">'
                             'Завдання для друку (PDF)</a>.')
        if test.get('content_path') and root.is_dir():
            content_file = root / test['content_path']
            if content_file.is_file():
                assert content_file.resolve().is_relative_to(root.resolve()), 'content path outside lesson root'
                document = json.loads(content_file.read_text(encoding='utf-8'))
                kahoot = document.get('platforms', {}).get('kahoot', {})
                if kahoot.get('status') == 'homework_created' and kahoot.get('verified') is True:
                    code = str(kahoot.get('code', ''))
                    assert re.fullmatch(r'[0-9]+', code), 'invalid Kahoot challenge code'
                    student = urlparse(kahoot.get('student_url', ''))
                    assert ((student.scheme, student.netloc, student.path)
                            == ('https', 'kahoot.it', f'/challenge/{code}')
                            and not student.params and not student.query and not student.fragment), \
                        'invalid Kahoot student URL or challenge code mismatch'
                    assert kahoot.get('normalization_max') == 10, 'expected Kahoot normalization to 10'
                    assert kahoot.get('no_deadline') is True and kahoot.get('deadline') is None, \
                        'expected Kahoot homework without a deadline'
                    links.append(
                        f'<a href="{html.escape(kahoot["student_url"], quote=True)}" target="_blank" '
                        'rel="noopener noreferrer">Резервне ДЗ на Kahoot</a> '
                        '(без кінцевої дати; оцінка за шкалою 10).'
                    )
    return '<p data-naurok-homework="true" data-dictionary-skip>' + '<br>'.join(links) + '</p>'


def attach(source: str, tests: list[dict], lesson_path: str | None = None, root: Path = ROOT) -> str:
    block = render_footer(tests, lesson_path, root)
    if BLOCK.search(source):
        return BLOCK.sub(lambda _: block, source, count=1)
    footer = re.search(r'<footer\b[^>]*>', source)
    if not footer:
        raise ValueError('lesson has no footer')
    return source[:footer.end()] + block + source[footer.end():]


def apply_grade(grade: str | int, root: Path = ROOT, *, check: bool = False,
                require_complete: bool = False) -> tuple[int, int]:
    directory = root / str(grade)
    pages = sorted(directory.glob('*/index.html'))
    records = {}
    for manifest in sorted(directory.glob('naurok-homework*.json')):
        for slug, record in json.loads(manifest.read_text(encoding='utf-8')).get('lessons', {}).items():
            assert slug not in records, f'duplicate lesson receipt in {manifest}: {slug}'
            records[slug] = record
    complete = 0
    assigned: dict[str, list[dict]] = {}
    valid_paths = {p.relative_to(root).as_posix() for p in pages}
    for page in pages:
        source_path = page.relative_to(root).as_posix()
        lesson = records.get(page.parent.name, {})
        if lesson.get('lesson_path'):
            assert lesson['lesson_path'] == source_path, 'manifest lesson path mismatch'
        tests = ready_tests(lesson)
        if tests:
            complete += 1
        elif require_complete:
            raise AssertionError(f'no verified homework: {source_path}')
        for test in tests:
            if require_complete:
                assert test.get('status') == 'homework_created', f'homework still pending: {page}'
                assert test.get('question_points') and test.get('deadline'), f'missing assessment metadata: {page}'
            target = test.get('assessment_lesson_path', source_path)
            assert target in valid_paths, 'invalid assessment lesson'
            assigned.setdefault(target, []).append(test)
    from archive_naurok_tests import sync_grade
    sync_grade(grade, root, check=check)
    for page in pages:
        lesson_path = page.relative_to(root).as_posix()
        tests = assigned.get(lesson_path, [])
        if not tests:
            source = page.read_text(encoding='utf-8')
            expected = BLOCK.sub('', source)
            if check:
                assert source == expected, f'unverified test link remains: {page.relative_to(root)}'
            elif source != expected:
                page.write_text(expected, encoding='utf-8')
            continue
        source = page.read_text(encoding='utf-8')
        expected = attach(source, tests, lesson_path, root)
        if check:
            assert source == expected, f'footer out of sync: {page.relative_to(root)}'
        elif source != expected:
            page.write_text(expected, encoding='utf-8')
    return complete, len(pages)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grades', nargs='+', default=['6', '7', '9'])
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    for grade in args.grades:
        done, total = apply_grade(grade, check=args.check, require_complete=args.require_complete)
        print(f'Naurok grade {grade}: {done}/{total} source lessons verified; checks placed in assessment lessons')


if __name__ == '__main__':
    main()
