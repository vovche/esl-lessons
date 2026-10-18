"""Check receipt rendering and any verified homework already in the repository."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from attach_naurok_homework import apply_grade, attach

receipt = {
    'test_id': '123', 'test_url': 'https://naurok.com.ua/test-beta/test/123',
    'homework_id': '456', 'teacher_homework_url': 'https://naurok.com.ua/test-beta/homework/456',
    'student_url': 'https://naurok.ua/test/join?gamecode=1234567', 'code': '1234567',
    'points': 10, 'verified': True, 'status': 'homework_created',
    'question_points': [1, 1, 1, 2, 2, 3], 'semester': 1, 'deadline': '2027-01-03T23:00',
}
source = '<main>lesson</main><footer class="footer"><p>existing attribution</p></footer>'
rendered = attach(source, [receipt])
assert rendered == attach(rendered, [receipt]), 'repeated build duplicated homework'
assert '<p>existing attribution</p>' in rendered, 'attribution removed'
assert rendered.index('data-naurok-homework') > rendered.index('<footer')
assert 'href="https://naurok.ua/test/join?gamecode=1234567"' in rendered
assert 'максимум 10 балів' in rendered
assert 'частина 2' in attach(source, [receipt, receipt]), 'multiple tests missing'
pending = dict(receipt, status='published_pending_homework_daily_limit')
pending.pop('homework_id')
pending.pop('student_url')
pending_html = attach(source, [pending])
assert 'Тест для самоперевірки' in pending_html and 'не надсилає результат' in pending_html
assert 'test/join?' not in pending_html, 'pending homework got an invented link'
try:
    attach(source, [dict(receipt, points=12)])
except AssertionError:
    pass
else:
    raise AssertionError('invalid total accepted')
try:
    attach(source, [dict(receipt, teacher_homework_url='https://naurok.com.ua/test-beta/homework/new/456')])
except AssertionError:
    pass
else:
    raise AssertionError('unsaved homework form accepted')

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    lesson = root / '6' / 'sample' / 'index.html'
    lesson.parent.mkdir(parents=True)
    lesson.write_text(source)
    manifest = root / '6' / 'naurok-homework.json'
    manifest.write_text(json.dumps({'lessons': {'sample': {'lesson_path': '6/sample/index.html', 'tests': [receipt]}}}))
    assert apply_grade(6, root) == (1, 1)
    assert apply_grade(6, root, check=True, require_complete=True) == (1, 1)
    manifest.write_text(json.dumps({'lessons': {'sample': {'tests': [dict(receipt, status='content_repair_required')]}}}))
    assert apply_grade(6, root) == (0, 1)
    assert lesson.read_text() == source, 'unverified test link was not removed'

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    canonical_path = root / '7' / 'sample' / 'homework-check-sample-01.json'
    canonical_path.parent.mkdir(parents=True)
    kahoot = {
        'status': 'homework_created', 'verified': True, 'code': '0025790251',
        'student_url': 'https://kahoot.it/challenge/0025790251',
        'editor_url': 'https://create.kahoot.it/creator/private-test-id',
        'test_url': 'https://create.kahoot.it/details/private-test-id',
        'teacher_assignment_url': 'https://create.kahoot.it/reports/private-assignment-id',
        'normalization_max': 10, 'no_deadline': True, 'deadline': None,
    }
    portable_receipt = dict(receipt, content_path='7/sample/homework-check-sample-01.json')

    def render_kahoot(remote: dict) -> str:
        canonical_path.write_text(json.dumps({'platforms': {'kahoot': remote}}), encoding='utf-8')
        return attach(source, [portable_receipt], '7/sample/index.html', root)

    kahoot_html = render_kahoot(kahoot)
    assert 'href="https://kahoot.it/challenge/0025790251"' in kahoot_html
    assert 'Резервне ДЗ на Kahoot</a> (без кінцевої дати; оцінка за шкалою 10)' in kahoot_html
    assert 'private-test-id' not in kahoot_html and 'private-assignment-id' not in kahoot_html
    assert 'create.kahoot.it' not in kahoot_html, 'teacher Kahoot URL leaked into student footer'
    assert kahoot_html == attach(kahoot_html, [portable_receipt], '7/sample/index.html', root), \
        'repeated attach duplicated Kahoot homework'
    assert kahoot_html.count('Резервне ДЗ на Kahoot') == 1
    assert 'Резервне ДЗ на Kahoot' not in render_kahoot(dict(kahoot, status='created_pending_assignment'))
    assert 'Резервне ДЗ на Kahoot' not in render_kahoot(dict(kahoot, verified=False))
    for invalid in [
        dict(kahoot, student_url='https://create.kahoot.it/creator/private-test-id'),
        dict(kahoot, student_url='https://kahoot.it/challenge/9999999999'),
        dict(kahoot, student_url='http://kahoot.it/challenge/0025790251'),
        dict(kahoot, student_url='https://kahoot.it.example/challenge/0025790251'),
        dict(kahoot, student_url='https://kahoot.it/challenge/0025790251?teacher=private'),
        dict(kahoot, normalization_max=12),
        dict(kahoot, no_deadline=False, deadline='2027-01-03T23:00'),
    ]:
        try:
            render_kahoot(invalid)
        except AssertionError:
            pass
        else:
            raise AssertionError(f'invalid Kahoot homework accepted: {invalid}')
    canonical_path.unlink()
    assert 'Резервне ДЗ на Kahoot' not in attach(source, [portable_receipt], '7/sample/index.html', root)

for grade in ('6', '7', '9'):
    done, total = apply_grade(grade, check=True)
    print(f'Naurok grade {grade}: {done}/{total} lesson footers verified')
print('Naurok footer rendering: PASS')
