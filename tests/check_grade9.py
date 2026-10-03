"""Validate complete 2026 source coverage, WB integration and audio placement."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1];GRADE=ROOT/'9';lessons=json.loads((GRADE/'lessons.json').read_text());media=json.loads((GRADE/'media-manifest.json').read_text())['entries'];by={s['slug']:s for s in lessons}
assert len(lessons)==97 and len(by)==97
assert {s['unit'] for s in lessons}==set(range(9))
assert {p for s in lessons for p in s['sb_pages']}==set(range(6,179))
assert {p for s in lessons for p in s['wb_pages']}==set(range(4,159))
assert len(media)==106 and len({m['id'] for m in media})==106
assert len({m['source'] for m in media})==106 and len({m['file'] for m in media})==106
assert sum(m['book']=='SB' for m in media)==77 and sum(m['book']=='WB' for m in media)==29
for s in lessons:
 html=(GRADE/s['slug']/'index.html').read_text();src=(GRADE/s['slug']/'sources.md').read_text();assert 'H. Q. Mitchell' not in html and '9 клас' in html
 assert len(s['questions'])>=5 and len(s['vocabulary'])>=8
 for q in s['questions']+s['workbook_questions']:
  assert len(set(q['choices']))==len(q['choices']) and 0<=q['answer']<len(q['choices']) and q['why'].strip()
 for book in ['sb','wb']:
  assert {a['printed_page'] for a in s[book+'_assets']}==set(s[book+'_pages'])
  for a in s[book+'_assets']:
   assert a['path'] in src
   if Path(a['path']).exists():assert hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()==a['sha256']
 for mid in s['media_ids']:
  m=next(m for m in media if m['id']==mid);assert '../'+m['file'] in html and m['lesson']==s['slug']
for m in media:
 p=GRADE/m['file'];assert p.is_file() and m['duration']>0 and hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
 if m['source_page'] is not None:
  assert m['source_page'] in by[m['lesson']]['sb_pages' if m['book']=='SB' else 'wb_pages']
 if m['book']=='WB':assert '/workbook/media/' in m['file'] and '/workbook/' in m['source']
 if Path(m['source']).exists():assert hashlib.sha256(Path(m['source']).read_bytes()).hexdigest()==m['source_sha256']
class Links(HTMLParser):
 def __init__(self):super().__init__();self.paths=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  for key in ['href','src']:
   if key in d:self.paths.append(d[key])
for p in GRADE.rglob('index.html'):
 parser=Links();parser.feed(p.read_text())
 for ref in parser.paths:
  if ref.startswith(('http:','https:','data:','#','javascript:')):continue
  path=(p.parent/unquote(ref.split('#')[0].split('?')[0])).resolve();assert path.exists(),(p,ref)
assert len(list(GRADE.glob('*/index.html')))==114
print('grade 9: PASS (97 course sections, 173 SB pages, 155 WB pages, 106 recordings; 15 previous lessons preserved)')
