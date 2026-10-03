"""Build phonetic data from lesson text, or verify the published dictionary.

The local eSpeak audio path is only for an initial fallback build. Once neural
recordings exist, update data with --no-audio and run the neural audio script.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import ctypes as C
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dictionary'
WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?(?:-[A-Za-z]+)*")
VOICES = {'gb-male': 'en', 'gb-female': 'en+f3', 'us-male': 'en-US', 'us-female': 'en-US+f3'}
# UI/CSS/code tokens, file extensions, phoneme labels and deliberately misspelt
# distractors are not English vocabulary entries.
EXCLUDE = set('''app b c csv d e esl f g h i j jp kl k la nd o p pdf pm png q s t th v vs wh y
page-xx v-ing v-s pre-test washing-up test-items choice-btn checkproduce
classlist div document err fieldset getelementbyid goodnote id input label legend
micro neganswer option path producefeedback produceinput qanswer radio replace
runeing runing select skill span strip strong style text tolowercase
button checked checking click display feedback language prompt
sweeped google excel doesn don isn ed ing ie'''.split())
EXCLUDE.update({'advices','clil','er','est','fin','ful','learning-tips','shoulding','waked','pair-work','clil-geography','clil-history','clil-music','clil-sport','culture-ukraine', 'enoughly', 'sb', 'wb'})
EXCLUDE.difference_update({'checked','label','legend','text'})
EXCLUDE.discard('i')
EXCLUDE.discard('washing-up')
PROPER_NOUNS = set(json.loads((OUTPUT / 'proper-nouns.json').read_text(encoding='utf-8')))


def translations() -> dict[str, list[str]]:
    data = json.loads((OUTPUT / 'translations-uk.json').read_text(encoding='utf-8'))
    for word, meanings in data.items():
        if (normalise(word) != word or not isinstance(meanings, list) or not meanings
                or any(not isinstance(value, str) or not value.strip() for value in meanings)
                or len(meanings) != len(set(meanings))):
            raise ValueError(f'Invalid Ukrainian translations: {word}')
    return data


class LessonText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.suppressed: list[str] = []
        self.visible: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {'script', 'style', 'nav', 'footer'} or 'data-dictionary-skip' in dict(attrs):
            self.suppressed.append(tag)
        elif self.suppressed and tag not in {'img','br','hr','input','meta','link','source','wbr'}:
            self.suppressed.append(tag)
        if not self.suppressed and tag == 'img':
            self.visible.append(dict(attrs).get('alt') or '')

    def handle_endtag(self, tag: str) -> None:
        if self.suppressed and self.suppressed[-1] == tag:
            self.suppressed.pop()

    def handle_data(self, data: str) -> None:
        if self.suppressed:
            if self.suppressed[-1] == 'script':
                self.scripts.append(data)
        else:
            self.visible.append(data)


def js_literals(source: str) -> list[str]:
    """Read JS quoted literals and static template text without evaluating code."""
    values: list[str] = []
    i = 0
    while i < len(source):
        if source.startswith('//', i):
            end = source.find('\n', i + 2)
            i = len(source) if end < 0 else end + 1
            continue
        if source.startswith('/*', i):
            end = source.find('*/', i + 2)
            i = len(source) if end < 0 else end + 2
            continue
        quote = source[i]
        if quote not in "'\"`":
            i += 1
            continue
        i += 1
        chars: list[str] = []
        while i < len(source):
            char = source[i]
            if char == '\\' and i + 1 < len(source):
                chars.append(source[i + 1])
                i += 2
                continue
            if char == quote:
                i += 1
                break
            if quote == '`' and source.startswith('${', i):
                # Dynamic interpolation is code, not literal lesson copy.
                depth = 1
                i += 2
                while i < len(source) and depth:
                    if source[i] == '{':
                        depth += 1
                    elif source[i] == '}':
                        depth -= 1
                    i += 1
                chars.append(' ')
                continue
            chars.append(char)
            i += 1
        values.append(''.join(chars))
    return values


def normalise(word: str) -> str:
    return word.lower().replace('’', "'")


def useful(word: str) -> bool:
    return (word not in EXCLUDE and word not in PROPER_NOUNS and (len(word) > 1 or word in {'a', 'i'})
            and not any(c.isdigit() for c in word) and not word.startswith('-'))


def inventory() -> dict[str, set[str]]:
    occurrences: dict[str, set[str]] = {}
    def add(text: str, location: str) -> None:
        for raw in WORD.findall(unescape(text)):
            word = normalise(raw)
            if useful(word):
                occurrences.setdefault(word, set()).add(location)
    for page in sorted(ROOT.glob('[679]/*/index.html')):
        parser = LessonText()
        parser.feed(page.read_text(encoding='utf-8'))
        location = str(page.parent.relative_to(ROOT)) + '/'
        add(' '.join(parser.visible), location)
        for literal in js_literals('\n'.join(parser.scripts)):
            literal = re.sub(r'<[^>]*>', ' ', literal)
            if any(marker in literal for marker in ('=>', 'function ', 'return ', 'const ', '{', '}', ';')):
                continue
            words = WORD.findall(literal)
            if len(words) > 1 or (len(words) == 1 and literal.strip().isalpha()):
                add(literal, location)
    cards = json.loads((ROOT / '6/jolly-phonics/data/cards.json').read_text())
    for card in cards:
        for word in card['words']:
            add(word, '6/jolly-phonics/')
    return occurrences


class Espeak:
    def __init__(self) -> None:
        self.lib = C.CDLL('libespeak-ng.so.1')
        self.lib.espeak_Initialize.argtypes = [C.c_int, C.c_int, C.c_char_p, C.c_int]
        self.lib.espeak_Initialize.restype = C.c_int
        self.lib.espeak_SetVoiceByName.argtypes = [C.c_char_p]
        self.lib.espeak_SetVoiceByName.restype = C.c_int
        self.lib.espeak_TextToPhonemes.argtypes = [C.POINTER(C.c_void_p), C.c_int, C.c_int]
        self.lib.espeak_TextToPhonemes.restype = C.c_char_p
        self.lib.espeak_SetSynthCallback.argtypes = [C.c_void_p]
        self.lib.espeak_Synth.argtypes = [C.c_void_p, C.c_size_t, C.c_uint, C.c_int, C.c_uint, C.c_uint, C.c_void_p, C.c_void_p]
        self.lib.espeak_Synth.restype = C.c_int
        self.lib.espeak_Synchronize.argtypes = []
        self.lib.espeak_Synchronize.restype = C.c_int
        self.frames: list[bytes] = []
        callback_type = C.CFUNCTYPE(C.c_int, C.POINTER(C.c_short), C.c_int, C.c_void_p)
        def callback(samples: C.POINTER(C.c_short), count: int, _events: C.c_void_p) -> int:
            if samples and count:
                self.frames.append(C.string_at(samples, count * 2))
            return 0
        self.callback = callback_type(callback)
        self.rate = self.lib.espeak_Initialize(2, 0, None, 0)
        if self.rate <= 0:
            raise RuntimeError('libespeak-ng initialization failed')
        self.lib.espeak_SetSynthCallback(self.callback)

    def voice(self, name: str) -> None:
        if self.lib.espeak_SetVoiceByName(name.encode()) != 0:
            raise RuntimeError(f'espeak voice unavailable: {name}')

    def ipa(self, word: str) -> str:
        source = C.create_string_buffer(word.encode())
        pointer = C.c_void_p(C.addressof(source))
        result = self.lib.espeak_TextToPhonemes(C.byref(pointer), 1, 2)
        return result.decode().strip() if result else ''

    def pcm(self, word: str) -> bytes:
        self.frames.clear()
        source = C.create_string_buffer(word.encode())
        if self.lib.espeak_Synth(source, len(source), 0, 1, 0, 1, None, None) != 0:
            raise RuntimeError(f'espeak synthesis failed: {word}')
        self.lib.espeak_Synchronize()
        return b''.join(self.frames)


# Deliberately approximate: a Ukrainian reading aid, not a substitute for IPA/audio.
IPA_UK = [
    ('tʃ', 'ч'), ('dʒ', 'дж'), ('eɪ', 'ей'), ('aɪ', 'ай'), ('ɔɪ', 'ой'),
    ('aʊ', 'ау'), ('əʊ', 'оу'), ('oʊ', 'оу'), ('ɪə', 'іе'), ('eə', 'еа'),
    ('ʊə', 'уе'), ('iː', 'і'), ('uː', 'у'), ('ɑː', 'а'), ('ɔː', 'о'),
    ('ɜː', 'ер'), ('ɚ', 'ер'), ('ɝ', 'ер'), ('ʌ', 'а'), ('æ', 'е'),
    ('ɒ', 'о'), ('ɑ', 'а'), ('ɔ', 'о'), ('ɜ', 'ер'), ('ɐ', 'а'),
    ('ᵻ', 'и'), ('ə', 'е'), ('ɛ', 'е'), ('e', 'е'), ('o', 'о'),
    ('a', 'а'), ('ɪ', 'и'), ('i', 'і'), ('ʊ', 'у'), ('u', 'у'),
    ('p', 'п'), ('b', 'б'), ('t', 'т'), ('d', 'д'), ('k', 'к'),
    ('g', 'ґ'), ('f', 'ф'), ('v', 'в'), ('θ', 'с'), ('ð', 'з'),
    ('s', 'с'), ('z', 'з'), ('ʃ', 'ш'), ('ʒ', 'ж'), ('h', 'х'),
    ('m', 'м'), ('n', 'н'), ('ŋ', 'нґ'), ('l', 'л'), ('r', 'р'),
    ('ɹ', 'р'), ('j', 'й'), ('w', 'в'), ('ɾ', 'т'), ('ɡ', 'ґ'),
]
VOWELS = set('аеєиіїоуюя')


def ukrainian_hint(ipa: str) -> str:
    out: list[str] = []
    stress = False
    for symbol in re.sub(r'[\[\]/]', '', ipa).split():
        index = 0
        while index < len(symbol):
            if symbol[index] in 'ˈˌ':
                stress = symbol[index] == 'ˈ'
                index += 1
                continue
            if symbol[index] in 'ːˑ':
                index += 1
                continue
            match = next(((sound, uk) for sound, uk in IPA_UK if symbol.startswith(sound, index)), None)
            if match:
                sound, uk = match
                if stress and any(letter in VOWELS for letter in uk):
                    vowel = next(i for i, letter in enumerate(uk) if letter in VOWELS)
                    uk = uk[:vowel + 1] + '\u0301' + uk[vowel + 1:]
                    stress = False
                out.append(uk)
                index += len(sound)
            else:
                index += 1
    return '[' + ''.join(out) + ']'

PATTERNS = [
    ('tion', '/ʃən/', 'The ending "tion" often sounds like /ʃən/.'),
    ('igh', '/aɪ/', 'The letters "igh" often say /aɪ/ as in night.'),
    ('sh', '/ʃ/', 'The letters "sh" say /ʃ/ as in ship.'),
    ('ch', '/tʃ/', 'The letters "ch" often say /tʃ/ as in chip.'),
    ('ph', '/f/', 'The letters "ph" say /f/ as in phone.'),
    ('th', None, 'Look at "th": put your tongue gently between your teeth.'),
    ('ck', '/k/', 'The letters "ck" say /k/ as in back.'),
    ('ng', '/ŋ/', 'The letters "ng" say /ŋ/ as in sing.'),
    ('ee', '/iː/', 'The letters "ee" often say /iː/ as in see.'),
    ('ai', '/eɪ/', 'The letters "ai" often say /eɪ/ as in rain.'),
    ('ay', '/eɪ/', 'The letters "ay" often say /eɪ/ as in day.'),
    ('oa', '/əʊ/', 'The letters "oa" often make a long o sound as in boat.'),
]
FIRST_SOUND = [
    ('aɪ', 'ice'), ('eɪ', 'day'), ('oʊ', 'open'), ('əʊ', 'open'),
    ('tʃ', 'chair'), ('dʒ', 'jump'), ('θ', 'thin'), ('ð', 'this'),
    ('ʃ', 'ship'), ('ʒ', 'measure'), ('æ', 'cat'), ('ʌ', 'cup'),
    ('ɪ', 'sit'), ('ə', 'about'), ('e', 'bed'), ('i', 'see'),
    ('p', 'pen'), ('b', 'bat'), ('t', 'top'), ('d', 'dog'),
    ('k', 'cat'), ('g', 'go'), ('f', 'fish'), ('v', 'van'),
    ('s', 'sun'), ('z', 'zoo'), ('h', 'hat'), ('m', 'man'),
    ('n', 'net'), ('l', 'leg'), ('r', 'red'), ('w', 'wet'),
    ('j', 'yes'), ('ɑ', 'arm'), ('ɔ', 'all'), ('o', 'open'),
    ('u', 'moon'),
]


def phonics_hint(word: str, ipa: str) -> str:
    for spelling, sound, hint in PATTERNS:
        if spelling in word and (sound is None or sound.strip('/') in ipa or spelling == 'oa'):
            return hint
    clean = ipa.lstrip('ˈˌ').replace('ɹ', 'r', 1)
    for sound, example in FIRST_SOUND:
        if clean.startswith(sound):
            return f'Start with /{sound}/ as in {example}, then blend the sounds.'
    return 'Listen to the first sound, then blend the word slowly.'


def audio_file(word: str, voice: str) -> Path:
    digest = hashlib.sha256(word.encode()).hexdigest()[:16]
    return OUTPUT / 'audio' / voice / f'{digest}.mp3'


def encode(pcm: bytes, sample_rate: int, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([
        'ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-f', 's16le', '-ar', str(sample_rate),
        '-ac', '1', '-i', 'pipe:0', '-codec:a', 'libmp3lame', '-b:a', '32k', str(target),
    ], input=pcm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode or target.stat().st_size < 500:
        raise RuntimeError(f'ffmpeg failed for {target}: {result.stderr.decode()}')


def build(with_audio: bool) -> None:
    existing = json.loads((OUTPUT / 'words.json').read_text(encoding='utf-8')) if (OUTPUT / 'words.json').exists() else {}
    if with_audio and existing.get('audioSource', '').startswith('Edge TTS'):
        raise SystemExit('Neural audio exists: use --no-audio, then scripts/generate_dictionary_neural_audio.py')
    locations = inventory()
    meanings = translations()
    missing = sorted(set(locations) - set(meanings))
    if missing:
        raise SystemExit(f'Add Ukrainian translations to dictionary/translations-uk.json: {missing}')
    engine = Espeak()
    entries = []
    for word in sorted(locations):
        engine.voice('en')
        gb = engine.ipa(word)
        engine.voice('en-US')
        us = engine.ipa(word)
        if not gb or not us:
            raise RuntimeError(f'No IPA for {word}')
        entries.append({
            'word': word,
            'translationsUk': meanings[word],
            'ipa': {'gb': f'/{gb}/', 'us': f'/{us}/'},
            'ukPhonetic': {'gb': ukrainian_hint(gb), 'us': ukrainian_hint(us)},
            'phonics': phonics_hint(word, gb),
            'audio': {key: f'audio/{key}/{audio_file(word, key).name}' for key in VOICES},
            'lessons': sorted(locations[word]),
        })
    data = {'version': 1, 'source': 'learner-facing text and quiz literals in 6/7/9 lessons',
            'ipaSource': 'eSpeak NG en and en-US',
            'audioSource': existing.get('audioSource', 'eSpeak NG, four locally generated voice variants'),
            'entries': entries}
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / 'words.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUTPUT / 'word-index.json').write_text(json.dumps([entry['word'] for entry in entries], ensure_ascii=False) + '\n', encoding='utf-8')
    manifest_path = OUTPUT / 'audio-manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        paths = {path for entry in entries for path in entry['audio'].values()}
        manifest['sha256'] = {path: digest for path, digest in manifest['sha256'].items() if path in paths}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(entries)} dictionary words', flush=True)
    if not with_audio:
        return
    pending = set()
    with ThreadPoolExecutor(max_workers=6) as executor:
        for i, entry in enumerate(entries, 1):
            for key, voice in VOICES.items():
                target = audio_file(entry['word'], key)
                if target.exists() and target.stat().st_size >= 500:
                    continue
                engine.voice(voice)
                pcm = engine.pcm(entry['word'])
                pending.add(executor.submit(encode, pcm, engine.rate, target))
                if len(pending) >= 12:
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        future.result()
            if i % 50 == 0:
                print(f'audio {i}/{len(entries)}', flush=True)
        for future in pending:
            future.result()
    print('audio complete', flush=True)


def check() -> None:
    data = json.loads((OUTPUT / 'words.json').read_text(encoding='utf-8'))
    current = inventory()
    meanings = translations()
    entries = data['entries']
    index_path = OUTPUT / 'word-index.json'
    manifest_path = OUTPUT / 'audio-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    hashes = manifest.get('sha256', {})
    indexed = {entry['word']: entry for entry in entries}
    missing = sorted(set(current) - set(indexed))
    stale = sorted(set(indexed) - set(current))
    errors = []
    if not index_path.is_file() or json.loads(index_path.read_text(encoding='utf-8')) != [entry['word'] for entry in entries]:
        errors.append('lesson word index does not match the dictionary')
    if data.get('audioSource', '').startswith('Edge TTS'):
        expected_paths = {entry['audio'][key] for entry in entries for key in VOICES}
        if set(hashes) != expected_paths:
            errors.append('neural audio manifest does not match the word inventory')
        if set(manifest.get('voices', {})) != set(VOICES):
            errors.append('neural audio manifest does not list all four voices')
    if missing or stale:
        errors.append(f'inventory mismatch: missing={missing[:20]} stale={stale[:20]}')
    for entry in entries:
        word = entry['word']
        if not meanings.get(word) or entry.get('translationsUk') != meanings[word]:
            errors.append(f'missing or outdated Ukrainian translations: {word}')
        if not all(entry['ipa'].get(a) and entry['ukPhonetic'].get(a) for a in ('gb', 'us')):
            errors.append(f'missing phonetics: {word}')
        if not entry['phonics']:
            errors.append(f'missing phonics: {word}')
        fingerprints = set()
        for key in VOICES:
            audio = OUTPUT / entry['audio'][key]
            if not audio.is_file() or audio.stat().st_size < 500:
                errors.append(f'missing audio: {word}/{key}')
                continue
            content = audio.read_bytes()
            if not (content.startswith(b'ID3') or (len(content) >= 2 and content[0] == 0xff and content[1] & 0xe0 == 0xe0)):
                errors.append(f'invalid MP3 header: {word}/{key}')
            if hashes and hashlib.sha256(content).hexdigest() != hashes.get(entry['audio'][key]):
                errors.append(f'audio manifest mismatch: {word}/{key}')
            fingerprints.add(hashlib.sha256(content).digest())
        if len(fingerprints) != len(VOICES):
            errors.append(f'duplicate voice clips: {word}')
    if errors:
        raise SystemExit('\n'.join(errors[:30]))
    print(f'dictionary: PASS ({len(entries)} words, {len(entries) * 4} audio clips)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--no-audio', action='store_true')
    args = parser.parse_args()
    check() if args.check else build(not args.no_audio)
