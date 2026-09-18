from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / '6/jolly-phonics'
cards = json.loads((ROOT / 'data/cards.json').read_text(encoding='utf-8'))
manifest = json.loads((ROOT / 'assets-manifest.json').read_text(encoding='utf-8'))
version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()

assert len(cards) == 42
assert [card['id'] for card in cards] == list(range(1, 43))
assert manifest['version'] == version
assert f'const VERSION="{version}";' in (ROOT / 'sw.js').read_text(encoding='utf-8')
assert len(list((ROOT / 'assets/audio').glob('*/*.mp3'))) == 168
assert len(list((ROOT / 'assets/cards').glob('*.webp'))) == 42
assert len(list((ROOT / 'assets/illustrations').glob('*.webp'))) == 42

for item in manifest['assets']:
    path = ROOT / item['url']
    assert path.is_file(), item['url']
    assert path.stat().st_size == item['bytes'], item['url']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], item['url']

html = (ROOT / 'index.html').read_text(encoding='utf-8')
for link in ('styles.css', 'app.js', 'data/cards.js', 'manifest.webmanifest'):
    assert link in html
assert '6 клас' not in html
for marker in ('id="swipeCoach"', 'id="exportStatus"', 'Завантажити CSV для вчителя'):
    assert marker in html
app = (ROOT / 'app.js').read_text(encoding='utf-8')
for marker in ("$('card').addEventListener('click'", 'showSwipeCoach', 'prepareReportLinks'):
    assert marker in app
print(f'Jolly Phonics OK: 42 cards, 168 clips, version {version}')
