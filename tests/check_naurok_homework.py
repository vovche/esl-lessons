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

for grade in ('6', '7', '9'):
    done, total = apply_grade(grade, check=True)
    print(f'Naurok grade {grade}: {done}/{total} lesson footers verified')
print('Naurok footer rendering: PASS')
