"""Import the teacher's local textbook recordings, retaining their source mapping."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path('/home/why/-teach/6-eng/sb-pages')


def destination(path: Path) -> str:
    name = path.name.lower()
    if 'culture_page_for_ukraine' in name:
        return 'sb-culture-ukraine-' + re.search(r'ukraine_(\d)', name)[1]
    if 'clil_' in name:
        return 'sb-clil-' + {'1': 'history', '2': 'geography', '3': 'sport', '4': 'music'}[re.search(r'clil_(\d)', name)[1]]
    if 'song_' in name:
        return 'sb-song-' + re.search(r'song_(\d)', name)[1]
    if 'culture_page' in name:
        return 'sb-culture-' + re.search(r'culture_page_(\d)', name)[1]
    match = re.search(r'module[_-]0?(\d)[_-]?(?:lesson_)?([a-e])', name)
    if match:
        return 'sb-' + match[1] + match[2]
    raise ValueError(f'No lesson mapping for {path}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    files = sorted(p for p in args.source.rglob('*') if p.suffix.lower() in {'.mp3', '.wav', '.mp4'})
    def convert(path: Path) -> dict:
        lesson = destination(path)
        folder = ROOT / '6' / lesson / 'media'
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / (path.stem + ('.mp4' if path.suffix == '.mp4' else '.mp3'))
        if not target.exists():
            if path.suffix == '.mp4':
                shutil.copyfile(path, target)
            else:
                temporary = target.with_suffix('.tmp.mp3')
                result = subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-i', str(path), '-vn', '-c:a', 'libmp3lame', '-b:a', '96k', str(temporary)], capture_output=True)
                if result.returncode:
                    raise RuntimeError(result.stderr.decode())
                temporary.replace(target)
        info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(target)]))
        return {'source': str(path.relative_to(args.source)), 'lesson': lesson,
                'file': str(target.relative_to(ROOT / '6')), 'duration': round(float(info['format']['duration']), 2),
                'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'kind': 'video' if path.suffix == '.mp4' else 'audio'}
    entries=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, future in enumerate(as_completed([pool.submit(convert, path) for path in files]), 1):
            entries.append(future.result())
            if i % 25 == 0:
                print(f'media {i}/{len(files)}', flush=True)
    (ROOT / '6' / 'media-manifest.json').write_text(json.dumps({'sourceRoot': str(args.source), 'entries': sorted(entries, key=lambda x:x['source'])}, ensure_ascii=False, indent=2)+'\n')
    print(f'Imported {len(entries)} textbook media files', flush=True)


if __name__ == '__main__':
    main()
