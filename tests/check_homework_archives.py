"""Check portable content, answer isolation and placement in the next lesson."""
import copy
import json
import sys
import tempfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from archive_naurok_tests import dump, markdown, sync_grade, validate
from attach_naurok_homework import apply_grade


class NextLesson(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.href = None
        self.label = ''
        self.next_href = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.label = ''

    def handle_data(self, text):
        if self.href:
            self.label += text

    def handle_endtag(self, tag):
        if tag == 'a':
            if 'Наступний урок' in self.label:
                self.next_href = self.href
            self.href = None

index = json.loads((ROOT / 'homework-tests.json').read_text())
assert index['test_count'] == len(index['tests'])
expected_content = set()
for manifest in ROOT.glob('[679]/naurok-homework*.json'):
    for lesson in json.loads(manifest.read_text())['lessons'].values():
        expected_content.update(t['content_path'] for t in lesson['tests'])
assert {t['json'] for t in index['tests']} == expected_content
identities = set()
placements = {'next_lesson': 0, 'no_next_lesson': 0}
for entry in index['tests']:
    document = json.loads((ROOT / entry['json']).read_text())
    validate(document)
    assert document['id'] == entry['id'] and entry['id'] not in identities
    identities.add(entry['id'])
    assert document['source_lesson'] == entry['source_lesson']
    assert document['assessment_lesson'] == entry['assessment_lesson']
    assert (ROOT / entry['json']).parent == (ROOT / entry['assessment_lesson']).parent
    source_page = ROOT / entry['source_lesson']
    next_href = NextLesson(source_page.read_text()).next_href
    if next_href:
        expected = (source_page.parent / unquote(urlparse(next_href).path)).resolve()
        if expected.is_dir():
            expected /= 'index.html'
        assert expected == (ROOT / entry['assessment_lesson']).resolve()
        assert document['placement']['rule'] == 'next_lesson'
    else:
        assert document['assessment_lesson'] == document['source_lesson']
        assert document['placement']['rule'] == 'no_next_lesson'
    placements[document['placement']['rule']] += 1
    for key in ('source_lesson', 'assessment_lesson', 'json', 'markdown', 'answer_key'):
        assert not Path(entry[key]).is_absolute() and (ROOT / entry[key]).is_file()
    student = (ROOT / entry['markdown']).read_text()
    teacher = (ROOT / entry['answer_key']).read_text()
    assert student == markdown(document, entry['json'])
    assert teacher == markdown(document, entry['json'], key=True)
    assert '**Ключ:' not in student and '**Допустимі відповіді:**' not in student
    assert 'platforms' not in student and 'naurok.com.ua' not in student
    offline = copy.deepcopy(document)
    offline.pop('platforms', None)
    validate(offline)
    assert markdown(offline, entry['json']) == student, 'student copy depends on a platform'

# A later homework launch must update metadata without losing portable questions
# or backup-platform receipts, and place links in the assessment lesson only.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    for slug in ('topic', 'next'):
        (root / '6' / slug).mkdir(parents=True)
        (root / '6' / slug / 'index.html').write_text('<main>lesson</main><footer>attribution</footer>')
    document = copy.deepcopy(json.loads((ROOT / index['tests'][0]['json']).read_text()))
    document.update(source_lesson='6/topic/index.html', assessment_lesson='6/next/index.html')
    receipt = dict(document['platforms']['naurok'], content_path='6/next/check.json',
                   assessment_lesson_path='6/next/index.html', status='published_pending_homework_daily_limit')
    document['platforms']['backup'] = {'test_id': 'backup-123'}
    original_questions = copy.deepcopy(document['questions'])
    (root / receipt['content_path']).write_text(dump(document))
    ledger = {'lessons': {'topic': {'lesson_path': '6/topic/index.html', 'tests': [receipt]}}}
    manifest = root / '6' / 'naurok-homework.json'
    manifest.write_text(dump(ledger))
    assert apply_grade(6, root) == (1, 2)
    assert 'data-naurok-homework' not in (root / '6/topic/index.html').read_text()
    assert 'data-naurok-homework' in (root / '6/next/index.html').read_text()
    footer = (root / '6/next/index.html').read_text()
    assert 'check.md' in footer and 'check-key.md' not in footer and 'href="check.json"' not in footer
    receipt.update(status='homework_created', homework_id='456',
                   teacher_homework_url='https://naurok.com.ua/test-beta/homework/456',
                   student_url='https://naurok.ua/test/join?gamecode=1234567', code='1234567')
    manifest.write_text(dump(ledger))
    apply_grade(6, root)
    updated = json.loads((root / receipt['content_path']).read_text())
    assert updated['questions'] == original_questions
    assert updated['platforms']['backup'] == {'test_id': 'backup-123'}
    assert updated['platforms']['naurok']['student_url'] == receipt['student_url']
    assert 'gamecode=1234567' in (root / '6/next/index.html').read_text()
    apply_grade(6, root, check=True)

for grade in (6, 7, 9):
    sync_grade(grade, check=True)
print(f'Portable homework checks: PASS ({len(identities)} tests; {placements})')
