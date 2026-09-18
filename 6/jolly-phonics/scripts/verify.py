from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cards = json.loads((ROOT / 'data/cards.json').read_text(encoding='utf-8'))
manifest = json.loads((ROOT / 'assets-manifest.json').read_text(encoding='utf-8'))
version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()

assert len(cards) == 42
assert [card['id'] for card in cards] == list(range(1, 43))
assert manifest['version'] == version
assert f'const VERSION="{version}";' in (ROOT / 'sw.js').read_text(encoding='utf-8')

for card in cards:
    number = f"{card['id']:02}"
    assert (ROOT / 'assets/cards' / f'{number}.webp').stat().st_size > 1_000
    assert (ROOT / 'assets/illustrations' / f'{number}.webp').stat().st_size > 1_000
    for voice in ('uk-female', 'uk-male', 'us-female', 'us-male'):
        audio = ROOT / 'assets/audio' / voice / f'{number}.mp3'
        assert audio.stat().st_size > 500

for item in manifest['assets']:
    path = ROOT / item['url']
    assert path.is_file(), item['url']
    assert path.stat().st_size == item['bytes'], item['url']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], item['url']

html = (ROOT / 'index.html').read_text(encoding='utf-8')
assert '../../' in html and 'manifest.webmanifest' in html
assert len(list((ROOT / 'assets/audio').glob('*/*.mp3'))) == 168
print(f'OK: 42 cards, 168 audio clips, {len(manifest["assets"])} hashed resources, version {version}')
