from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
if not version or any(char not in '0123456789.' for char in version):
    raise SystemExit('VERSION must contain a dotted numeric version, for example 1.0.1')

assets = []
runtime_roots = {'assets', 'data', 'icons'}
runtime_files = {'index.html', 'styles.css', 'app.js', 'manifest.webmanifest'}
for path in sorted(ROOT.rglob('*')):
    if not path.is_file():
        continue
    relative = path.relative_to(ROOT).as_posix()
    if path.name not in runtime_files and relative.split('/', 1)[0] not in runtime_roots:
        continue
    assets.append({
        'url': relative,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'bytes': path.stat().st_size,
    })

(ROOT / 'assets-manifest.json').write_text(
    json.dumps({'version': version, 'assets': assets}, indent=2) + '\n', encoding='utf-8'
)
template = (ROOT / 'scripts/sw.template.js').read_text(encoding='utf-8')
(ROOT / 'sw.js').write_text(template.replace('__VERSION__', json.dumps(version)), encoding='utf-8')
print(f'Built manifest and service worker for {version}: {len(assets)} resources')
