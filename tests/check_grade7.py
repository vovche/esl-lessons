"""Verify the grade-7 course, source citations and playable recording manifests."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json,re,sys
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1];GRADE=ROOT/'7';sys.path.insert(0,str(ROOT/'scripts'))
lessons=json.loads((GRADE/'lessons.json').read_text());media=json.loads((GRADE/'media-manifest.json').read_text())['entries']
assert len(lessons)==97 and len({s['slug'] for s in lessons})==97
assert {s['unit'] for s in lessons}==set(range(9))
assert len(media)==88 and len({m['id'] for m in media})==88
assert len({m['source'] for m in media})==88
assert {p for s in lessons for p in s['sb_pages']}==set(range(6,159))
assert {p for s in lessons for p in s['wb_pages']}==set(range(4,110))
for s in lessons:
 html=(GRADE/s['slug']/'index.html').read_text();assert 'H. Q. Mitchell' not in html
 assert '<h1>' in html and 'data-site-nav="grade"' in html
 assert len(s['vocabulary'])>=6 and len(s['questions'])>=5
 for q in s['questions']+s.get('workbook_questions',[]):
  assert len(q['choices'])==len(set(q['choices'])) and 0<=q['answer']<len(q['choices']) and q['why'].strip()
 for book in ['sb','wb']:
  assert {a['printed_page'] for a in s[book+'_assets']}==set(s[book+'_pages'])
  for a in s[book+'_assets']:
   assert int(re.search(r'page-(\d+)',Path(a['path']).name)[1])==a['printed_page']
   if Path(a['path']).is_file():assert hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()==a['sha256']
 sources=(GRADE/s['slug']/'sources.md').read_text()
 assert all(a['path'] in sources for a in s['sb_assets']+s['wb_assets'])
 for mid in s['media_ids']:
  m=next(m for m in media if m['id']==mid);assert '../'+m['file'] in html
for m in media:
 p=GRADE/m['file'];assert p.is_file() and m['duration']>0
 assert hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
 assert m['lesson'] in {s['slug'] for s in lessons}
 if m['source_page'] is not None:assert m['source_page'] in next(s for s in lessons if s['slug']==m['lesson'])['sb_pages']
class Links(HTMLParser):
 def __init__(self):super().__init__();self.paths=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  for k in ['href','src']:
   if k in d:self.paths.append(d[k])
for p in GRADE.rglob('index.html'):
 parser=Links();parser.feed(p.read_text())
 for ref in parser.paths:
  if ref.startswith(('http:','https:','data:','#','javascript:')):continue
  path=(p.parent/unquote(ref.split('#')[0].split('?')[0])).resolve()
  assert path.exists(),(p,ref)
print('grade 7: PASS (97 source-mapped sections, 153 SB pages, 106 WB pages, 88 recordings; all local page links resolve)')
