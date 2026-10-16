"""Verify every printable student sheet and answer key against portable JSON."""
import hashlib
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_homework_pdfs import clean, input_hash, reading_parts, points_label


def normalized(text):
    return re.sub(r'\s+', '', clean(text))


index = json.loads((ROOT / 'homework-tests.json').read_text())
manifest = json.loads((ROOT / 'homework-pdfs.json').read_text())
records = {r['id']: r for r in manifest['tests']}
assert len(records) == manifest['test_count'] == len(index['tests'])
total_pages = 0
catalog = (ROOT / 'PRINT_TESTS.md').read_text()
for entry in index['tests']:
    document = json.loads((ROOT / entry['json']).read_text())
    record = records[document['id']]
    assert record['input_sha256'] == input_hash(document), f'stale PDF: {document["id"]}'
    for role in ('student', 'teacher'):
        artifact = record[role]
        path = ROOT / artifact['path']
        assert path.parent == (ROOT / entry['assessment_lesson']).parent
        assert entry['pdf' if role == 'student' else 'answer_key_pdf'] == artifact['path']
        assert f'({artifact["path"]})' in catalog
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256']
        pdf = PdfReader(path)
        assert not pdf.is_encrypted and len(pdf.pages) == artifact['pages']
        assert pdf.metadata.subject == document['id']
        pages = []
        for page in pdf.pages:
            assert abs(float(page.mediabox.width) - 595.276) < 1
            assert abs(float(page.mediabox.height) - 841.890) < 1
            text = normalized(page.extract_text())
            assert len(text) > 50, f'empty page: {path}'
            pages.append(text)
        total_pages += len(pages)
        text = ''.join(pages)
        assert document['id'] in text and '10балів' in text
        if role == 'student':
            assert 'КЛЮЧДЛЯВЧИТЕЛЯ' not in text and 'Відповідь:' not in text
        else:
            assert 'КЛЮЧДЛЯВЧИТЕЛЯ' in text
        for q in document['questions']:
            reading, prompt = reading_parts(q['prompt'])
            assert normalized(prompt) in text, (path, 'missing prompt', prompt)
            assert normalized(prompt + f' ({points_label(q["points"])})') in text, (path, 'wrong question weight')
            if role == 'student':
                parts = [prompt, *q.get('options', [])]
                if reading:
                    parts.append(reading)
                    assert text.count(normalized(reading)) == 1, (path, 'repeated reading')
                assert any(all(normalized(part) in page for part in parts) for page in pages), (path, 'split question')
            else:
                answers = [f'{chr(65 + q["key"])}. {q["options"][q["key"]]}'] if q['type'] == 'choice' else q['answers']
                assert all(normalized(a) in text for a in answers), (path, 'missing answer')
print(f'Print PDFs: PASS ({len(records) * 2} files, {total_pages} A4 pages)')
