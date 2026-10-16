"""Validate and render portable lesson-local homework checks (no network access)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE_FIELDS = ('test_id', 'test_url', 'builder_url', 'status', 'verified',
                 'homework_id', 'teacher_homework_url', 'student_url', 'code',
                 'deadline', 'semester', 'points', 'question_points')


def dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def write_or_check(path: Path, text: str, check: bool) -> None:
    if check:
        assert path.is_file() and path.read_text(encoding='utf-8') == text, f'archive out of sync: {path}'
    elif not path.is_file() or path.read_text(encoding='utf-8') != text:
        path.write_text(text, encoding='utf-8')


def validate(document: dict) -> None:
    assert document['schema_version'] == 1
    assert document['id'] and document['purpose'] == 'homework_check'
    questions = document['questions']
    assert questions and sum(q['points'] for q in questions) == 10
    assert document['total_points'] == 10
    assert len({q['points'] for q in questions}) > 1
    naurok = document.get('platforms', {}).get('naurok')
    if naurok:
        assert [q['points'] for q in questions] == naurok['question_points']
    for q in questions:
        assert q['prompt'].strip() and isinstance(q['points'], int) and q['points'] > 0
        assert q['type'] in ('choice', 'word')
        if q['type'] == 'choice':
            assert len(q['options']) >= 2 and all(q['options'])
            assert isinstance(q['key'], int) and 0 <= q['key'] < len(q['options'])
        else:
            assert q['answers'] and all(isinstance(a, str) and a.strip() for a in q['answers'])


def relative(target: str, document_path: str) -> str:
    return Path(os.path.relpath(target, Path(document_path).parent)).as_posix()


def points_label(points: int) -> str:
    return f'{points} ' + ('бал' if points == 1 else 'бали' if points < 5 else 'балів')


def markdown(document: dict, document_path: str, *, key: bool = False) -> str:
    source = relative(document['source_lesson'], document_path)
    target = relative(document['assessment_lesson'], document_path)
    lines = ['# ' + ('Ключ до перевірки домашнього завдання' if key else 'Перевірка домашнього завдання'), '',
             f'**Тема:** {document["source_title"]}', '',
             f'**Клас:** {document["grade"]}. **Максимум:** {points_label(document["total_points"])}.', '',
             f'Код матеріалу: `{document["id"]}`.', '']
    if key:
        lines += ['> Для вчителя: містить правильні відповіді.', '',
                  f'[Матеріали теми]({source}) · [Урок перевірки ДЗ]({target}).',
                  document['placement']['note'], '',
                  f'Дедлайн: {document["assessment"]["deadline"]}, {document["assessment"]["timezone"]}.', '']
        for platform, remote in document.get('platforms', {}).items():
            if remote.get('test_url'):
                lines.append(f'[{platform}: тест]({remote["test_url"]}). Стан: `{remote["status"]}`.')
            if remote.get('student_url'):
                lines.append(f'[{platform}: домашнє завдання]({remote["student_url"]}).')
    else:
        lines += ['Ім’я та прізвище: ____________________________________', '',
                  'Дата: ____________________', '',
                  'Обери одну відповідь у завданнях із варіантами. У решті завдань напиши відповідь самостійно.', '']
    for i, q in enumerate(document['questions'], 1):
        lines += [f'## {i}. {points_label(q["points"])}', '', q['prompt'], '']
        if q['type'] == 'choice':
            lines += [f'{j}. {option}' for j, option in enumerate(q['options'], 1)]
            lines += ['']
            if key:
                lines += [f'**Ключ: {q["key"] + 1}. {q["options"][q["key"]]}**', '']
        else:
            if key:
                lines += ['**Допустимі відповіді:** ' + '; '.join(json.dumps(a, ensure_ascii=False) for a in q['answers']), '']
            else:
                lines += ['Відповідь: ______________________________________________________________', '']
    return '\n'.join(lines).rstrip() + '\n'


def sync_grade(grade: str | int, root: Path = ROOT, *, check: bool = False) -> int:
    grouped: dict[str, list[dict]] = {}
    count = 0
    for manifest in sorted((root / str(grade)).glob('naurok-homework*.json')):
        for slug, lesson in json.loads(manifest.read_text(encoding='utf-8'))['lessons'].items():
            for receipt in lesson['tests']:
                if not receipt.get('content_path'):
                    continue
                path = receipt['content_path']
                file = root / path
                assert file.resolve().is_relative_to(root.resolve()) and file.is_file()
                document = json.loads(file.read_text(encoding='utf-8'))
                assert document['source_lesson'] == f'{grade}/{slug}/index.html'
                assert document['assessment_lesson'] == receipt['assessment_lesson_path']
                document.setdefault('platforms', {})['naurok'] = {k: receipt[k] for k in REMOTE_FIELDS if k in receipt}
                assert document['platforms']['naurok']['test_id'] == str(receipt['test_id'])
                document['assessment'] = {k: receipt[k] for k in ('deadline', 'semester')}
                document['assessment']['timezone'] = 'Europe/Kyiv'
                validate(document)
                write_or_check(file, dump(document), check)
                write_or_check(file.with_suffix('.md'), markdown(document, path), check)
                key_file = file.with_name(file.stem + '-key.md')
                write_or_check(key_file, markdown(document, path, key=True), check)
                grouped.setdefault(document['assessment_lesson'], []).append({
                    'id': document['id'], 'title': document['title'],
                    'source_lesson': document['source_lesson'],
                    'json': file.name, 'markdown': file.with_suffix('.md').name,
                    'answer_key': key_file.name,
                    'test_url': receipt['test_url'], 'status': receipt['status'],
                    **({'pdf': file.with_suffix('.pdf').name} if file.with_suffix('.pdf').is_file() else {}),
                    **({'answer_key_pdf': file.with_name(file.stem + '-key.pdf').name}
                       if file.with_name(file.stem + '-key.pdf').is_file() else {}),
                    **({'student_url': receipt['student_url']} if receipt.get('student_url') else {}),
                })
                count += 1
    for lesson_path, tests in grouped.items():
        directory = (root / lesson_path).parent
        tests.sort(key=lambda t: t['id'])
        write_or_check(directory / 'homework-checks.json', dump({
            'schema_version': 1, 'assessment_lesson': lesson_path, 'tests': tests,
        }), check)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grades', nargs='+', default=['6', '7', '9'])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for grade in args.grades:
        print(f'Grade {grade}: {sync_grade(grade, check=args.check)} portable tests')


if __name__ == '__main__':
    main()
