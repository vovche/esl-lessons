"""Validate course coverage, source attribution, questions and media integrity."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.build_grade6 import GRADE,SOURCE,source_pages,questions
lessons=json.loads((GRADE/'lessons.json').read_text())
assert len({x['slug'] for x in lessons})==65
assert {x['code'] for x in lessons if len(x['code'])==2}=={f'{u}{c}' for u in range(1,9) for c in 'abcde'}
for lesson in lessons:
 page=GRADE/lesson['slug']/'index.html'
 assert page.is_file(),page
 assert len(lesson['vocabulary'])>=6,lesson['slug']
 assert len(questions(lesson))>=8,lesson['slug']
 for q in questions(lesson):
  assert len(set(q['choices']))==len(q['choices']),q
  assert 0<=q['answer']<len(q['choices']),q
  assert q['why'].strip(),q
 assert (page.parent/'sources.md').is_file(),page
 if SOURCE.is_dir():
  assert source_pages(lesson),lesson['slug']
  for source in source_pages(lesson):
   assert source.exists(),source
media=json.loads((GRADE/'media-manifest.json').read_text())['entries']
assert len(media)==132
assert len({m['source'] for m in media})==132
assert sum(m['kind']=='video' for m in media)==8
for m in media:
 assert m['lesson'] in {x['slug'] for x in lessons},m
 path=GRADE/m['file']
 assert path.is_file() and m['duration']>0,m
 assert hashlib.sha256(path.read_bytes()).hexdigest()==m['sha256'],m
 assert 'media/'+path.name in (GRADE/m['lesson']/'index.html').read_text(),m
print('grade 6: PASS (65 lessons, 40 core lessons, 132 media files)')

from scripts.build_dictionary import LessonText
parser=LessonText()
parser.feed('<p>cats <span data-dictionary-skip><b>Cats</b> London</span> music</p>')
assert " ".join(parser.visible).strip()=="cats   music"
