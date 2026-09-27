"""Replace local eSpeak clips with four prerecorded Edge neural voice clips.

Install edge-tts separately (see dictionary/README.md). The script downloads
batches, slices them at SentenceBoundary offsets, validates every MP3, then
replaces the dictionary's clips. Interrupted runs resume from staging files.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
DICT = ROOT / 'dictionary'
DATA = DICT / 'words.json'
STAGING = DICT / '.audio-neural-staging'
VOICE_NAMES = {
    'gb-female': 'en-GB-SoniaNeural',
    'gb-male': 'en-GB-RyanNeural',
    'us-female': 'en-US-JennyNeural',
    'us-male': 'en-US-GuyNeural',
}
TICKS_PER_SECOND = 10_000_000
BATCH_SIZE = 35
MANIFEST = DICT / 'audio-manifest.json'
EXISTING_HASHES = json.loads(MANIFEST.read_text(encoding='utf-8'))['sha256'] if MANIFEST.exists() else {}


def valid(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 1_000:
        return False
    with path.open('rb') as handle:
        header = handle.read(3)
    return header == b'ID3' or (len(header) >= 2 and header[0] == 0xff and header[1] & 0xe0 == 0xe0)


def filename(word: str) -> str:
    return hashlib.sha256(word.encode()).hexdigest()[:16] + '.mp3'


def ready(word: str, voice_key: str) -> bool:
    staged = STAGING / voice_key / filename(word)
    if valid(staged):
        return True
    relative = f'audio/{voice_key}/{filename(word)}'
    current = DICT / relative
    return valid(current) and hashlib.sha256(current.read_bytes()).hexdigest() == EXISTING_HASHES.get(relative)


def normalize(text: str) -> str:
    return re.sub(r'[^a-z]', '', text.casefold())


def split_audio(audio: bytes, intervals: list[tuple[float, float]], words: list[str], voice_key: str) -> None:
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=True) as batch_file:
        batch_file.write(audio)
        batch_file.flush()
        for (start, duration), word in zip(intervals, words, strict=True):
            target = STAGING / voice_key / filename(word)
            if valid(target):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix('.tmp.mp3')
            result = subprocess.run([
                'ffmpeg', '-nostdin', '-loglevel', 'error', '-y',
                '-ss', f'{max(0, start - 0.07):.3f}', '-i', batch_file.name,
                '-t', f'{duration + 0.14:.3f}', '-c:a', 'copy', str(tmp),
            ], capture_output=True)
            if result.returncode or not valid(tmp):
                raise RuntimeError(f'Could not split {word}/{voice_key}: {result.stderr.decode()}')
            os.replace(tmp, target)


async def request(words: list[str], voice: str) -> tuple[bytes, list[dict]]:
    utterance = '. '.join(word[0].upper() + word[1:] for word in words) + '.'
    chunks: list[bytes] = []
    boundaries: list[dict] = []
    for attempt in range(4):
        try:
            async for item in edge_tts.Communicate(utterance, voice=voice, rate='-10%').stream():
                if item['type'] == 'audio':
                    chunks.append(item['data'])
                elif item['type'] == 'SentenceBoundary':
                    boundaries.append(item)
            if not chunks:
                raise RuntimeError('No audio returned')
            return b''.join(chunks), boundaries
        except Exception:
            chunks.clear()
            boundaries.clear()
            if attempt == 3:
                raise
            await asyncio.sleep(2 ** attempt)
    raise AssertionError('unreachable')


async def produce(words: list[str], voice_key: str, semaphore: asyncio.Semaphore) -> None:
    if all(ready(word, voice_key) for word in words):
        return
    async with semaphore:
        audio, boundaries = await request(words, VOICE_NAMES[voice_key])
    if len(words) == 1:
        target = STAGING / voice_key / filename(words[0])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(audio)
        if not valid(target):
            raise RuntimeError(f'Invalid single-word audio: {words[0]}/{voice_key}')
        return
    if len(boundaries) != len(words) or any(normalize(item['text']) != normalize(word) for item, word in zip(boundaries, words, strict=False)):
        middle = len(words) // 2
        await produce(words[:middle], voice_key, semaphore)
        await produce(words[middle:], voice_key, semaphore)
        return
    intervals = [(item['offset'] / TICKS_PER_SECOND, item['duration'] / TICKS_PER_SECOND) for item in boundaries]
    await asyncio.to_thread(split_audio, audio, intervals, words, voice_key)


async def generate(entries: list[dict], sample: int | None) -> None:
    words = [entry['word'] for entry in entries]
    if sample:
        words = words[:sample]
    semaphore = asyncio.Semaphore(6)
    tasks = []
    for voice_key in VOICE_NAMES:
        pending = [word for word in words if not ready(word, voice_key)]
        for start in range(0, len(pending), BATCH_SIZE):
            tasks.append((voice_key, start, pending[start:start + BATCH_SIZE]))
    done = 0
    async def one(voice_key: str, start: int, batch: list[str]) -> None:
        nonlocal done
        await produce(batch, voice_key, semaphore)
        done += 1
        if done % 8 == 0 or done == len(tasks):
            print(f'finished {done}/{len(tasks)} batches', flush=True)
    await asyncio.gather(*(one(voice_key, start, batch) for voice_key, start, batch in tasks))


def commit(entries: list[dict], data: dict) -> None:
    for entry in entries:
        for voice_key in VOICE_NAMES:
            staged = STAGING / voice_key / filename(entry['word'])
            if not valid(staged) and not ready(entry['word'], voice_key):
                raise RuntimeError(f'Missing staged recording: {entry["word"]}/{voice_key}')
    manifest = {}
    for entry in entries:
        for voice_key in VOICE_NAMES:
            target = DICT / entry['audio'][voice_key]
            staged = STAGING / voice_key / filename(entry['word'])
            target.parent.mkdir(parents=True, exist_ok=True)
            if valid(staged):
                os.replace(staged, target)
            manifest[entry['audio'][voice_key]] = hashlib.sha256(target.read_bytes()).hexdigest()
    data['audioSource'] = 'Edge TTS neural voices: Sonia, Ryan, Jenny, Guy; prerecorded MP3'
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (DICT / 'audio-manifest.json').write_text(json.dumps({'voices': VOICE_NAMES, 'sha256': manifest}, indent=2) + '\n')
    for folder in STAGING.glob('*'):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
    if STAGING.exists() and not any(STAGING.iterdir()):
        STAGING.rmdir()
    print(f'installed {len(manifest)} neural MP3 recordings', flush=True)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, help='Stage only the first N words for a trial run')
    args = parser.parse_args()
    data = json.loads(DATA.read_text(encoding='utf-8'))
    entries = data['entries']
    await generate(entries, args.sample)
    if args.sample:
        print('sample staged; run without --sample to finish and install', flush=True)
    else:
        commit(entries, data)


if __name__ == '__main__':
    asyncio.run(main())
