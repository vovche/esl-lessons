"""Regenerate the four word-pronunciation sets.

The app intentionally does not ask TTS to fake isolated phonemes. Stop sounds
such as /t/ and /p/ often acquire a schwa ("tuh", "puh"), which is unsuitable
for phonics teaching. Each clip therefore pronounces the example word clearly;
the grapheme and IPA remain visible on the card.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
CARDS = json.loads((ROOT / 'data/cards.json').read_text(encoding='utf-8'))
VOICES = {
    'uk-female': 'en-GB-SoniaNeural',
    'uk-male': 'en-GB-RyanNeural',
    'us-female': 'en-US-JennyNeural',
    'us-male': 'en-US-GuyNeural',
}


async def generate() -> None:
    for key, voice in VOICES.items():
        folder = ROOT / 'assets/audio' / key
        folder.mkdir(parents=True, exist_ok=True)
        for card in CARDS:
            target = folder / f"{card['id']:02}.mp3"
            text = '. '.join(word.capitalize() for word in card['words']) + '.'
            await edge_tts.Communicate(text, voice=voice, rate='-10%').save(str(target))
            print(f"{key}/{target.name}: {text}", flush=True)


if __name__ == '__main__':
    asyncio.run(generate())
