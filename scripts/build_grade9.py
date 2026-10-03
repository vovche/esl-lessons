"""Build the Karpiuk 2026 grade-9 course from source-mapped lesson cards.

Scans stay in the local teacher library; every recording has a unique canonical
site copy. Previously authored lessons retain their content and interactions.
"""
from pathlib import Path
from html import escape,unescape
import json,re
import build_grade6 as common
import build_grade7 as support
ROOT=Path(__file__).resolve().parents[1];GRADE=ROOT/'9'
def e(s):return escape(str(s),quote=True)
def sources(s,media):
 lines=[f'# Джерела: {s["title"]}','','О. Карпюк, К. Карпюк. Англійська мова, 9 клас, видання 2026 року.','','## Підручник (SB)']
 for book,label in [('sb','Підручник (SB)'),('wb','Activity Book (WB)')]:
  if book=='wb':lines+=['','## '+label]
  lines += [f'- `{a["path"]}` — друкована с. {a["printed_page"]}' for a in s[book+'_assets']]
 lines += ['','## Аудіо']+[f'- {m["book"]}: `{m["source"]}` → [запис](../{m["file"]})' for m in media]
 lines += ['','Пояснення, короткі тексти й інтерактивні вправи — авторські адаптації. Аудіо оригінальне; текст для читання не є його транскриптом. Номер t у назві запису збережено як мітку файлу; для WB він іноді відрізняється від номера надрукованої вправи. Скановані сторінки зберігаються локально у викладача.','']
 return '\n'.join(lines)
def players(media):
 if not media:return ''
 cards=[]
 for m in media:
  label=m['book']+' · '+('вступ до юніту' if m['scope']=='unit_introductory_recording' else 'вступ' if m['scope']=='introductory_recording' else 'с. '+str(m['source_page']))
  task=(' · запис t.'+m['source_exercise']) if m.get('source_exercise') else ''
  cards.append(f'<article class="media-card"><h3>{e(label+task)}</h3><details><summary>Назва оригінального запису</summary><p data-dictionary-skip>{e(m["original_filename"])}</p></details><audio controls preload="none" src="../{e(m["file"])}"></audio><a href="../{e(m["file"])}" download>Завантажити запис</a></article>')
 return '<section id="listen"><h2>Слухай і перевіряй</h2><p>Перше прослуховування — ситуація та головна думка; друге — деталі для відповідної сторінки SB або WB. Мітка запису збережена з назви файлу; звір завдання з номером у своєму зошиті.</p><div class="media-grid">'+''.join(cards)+'</div></section>'
def card(s,prefix=''):
 return f'<article class="card ready"><span class="tag ready">'+('Unit '+str(s['unit']) if s['unit'] else 'Starter')+f' · SB {", ".join(map(str,s["sb_pages"]))}</span><h3>{e(s["title"])}</h3><p>{e(s["title_uk"])}</p><a class="btn primary" href="{prefix}{s["slug"]}/">Почати урок →</a></article>'
def main():
 lessons=json.loads((GRADE/'lessons.json').read_text());media=json.loads((GRADE/'media-manifest.json').read_text())['entries'];assets={a['path']:a for s in lessons for a in s['sb_assets']+s['wb_assets']};by_page={p:s for s in lessons for p in s['sb_pages']};common.source_pages=lambda s:[Path(a['path']) for a in s['sb_assets']];common.media_html=lambda s,ms:players(ms)
 for i,s in enumerate(lessons):
  ms=[m for m in media if m['id'] in s['media_ids']];folder=GRADE/s['slug'];folder.mkdir(exist_ok=True);html=common.render(s,ms,lessons[i-1] if i else None,lessons[i+1] if i+1<len(lessons) else None)
  html=html.replace('Unit '+str(s['unit'])+' · '+s['code'], 'Unit '+str(s['unit'])+' · '+s['title_uk'].split(': ')[-1])
  html=html.replace('6 клас','9 клас').replace('6-u','9-u').replace('grade=6','grade=9').replace('Підручник H. Q. Mitchell, Marileni Malkogianni, 9 клас, «Лінгвіст», 2023.','Підручник О. Карпюк, К. Карпюк, 9 клас, 2026.')
  extra='<section id="book-tasks"><h2>Застосуй у підручнику</h2>'+support.task_list(s['sb_tasks'],'SB')+'</section>'+support.workbook(s)
  html=html.replace('<nav class="lesson-links" aria-label="Інші уроки">',extra+'<nav class="lesson-links" aria-label="Інші уроки">');(folder/'index.html').write_text(html);(folder/'sources.md').write_text(sources(s,ms))
 # Existing twelve textbook adaptations and three grammar workshops keep their HTML.
 legacy=[];existing=[]
 for filename in ['unit1-lessons.json','unit2-lessons.json']:existing+=json.loads((GRADE/filename).read_text())
 existing += [dict(slug='gerund',sources=dict(textbook=[35,38],workbook=[])),dict(slug='future-forms',sources=dict(textbook=[18,19],workbook=[])),dict(slug='future-forms-v2',sources=dict(textbook=[18,19],workbook=[]))]
 for row in existing:
  slug=row['slug'];path=GRADE/slug/'index.html';html=path.read_text();title_match=re.search(r'<h1[^>]*>(.*?)</h1>',html,re.S);title=unescape(re.sub('<[^>]+>',' ',title_match[1])).strip();src=row['sources'];s=dict(slug=slug,title=title,unit=by_page[src['textbook'][0]]['unit'],section_index=0,sb_pages=src['textbook'],wb_pages=src['workbook'],sb_assets=[a for a in assets.values() if a['kind']=='sb_scan' and a['printed_page'] in src['textbook']],wb_assets=[a for a in assets.values() if a['kind']=='wb_scan' and a['printed_page'] in src['workbook']],wb_tasks=[t for a in assets.values() if a['kind']=='wb_scan' and a['printed_page'] in src['workbook'] for t in a.get('tasks',[])],workbook_questions=[])
  ms=[m for m in media if m['source_page'] in s['sb_pages' if m['book']=='SB' else 'wb_pages'] or m['scope']=='unit_introductory_recording' and m['unit']==s['unit'] and 'lead-in' in {by_page[p]['section'] for p in s['sb_pages']}];html=re.sub(r'<!-- grade9-source-support-start -->.*?<!-- grade9-source-support-end -->','',html,flags=re.S);extra='<!-- grade9-source-support-start -->'+players(ms)+support.workbook(s)+'<!-- grade9-source-support-end -->';html=html.replace('</main>',extra+'</main>');path.write_text(html);(path.parent/'sources.md').write_text(sources(s,ms));legacy.append(s)
 refs=[]
 for slug,title,body in [('sb-grammar','Граматика курсу',''.join(f'<article class="card"><h2>Unit {u}</h2><p>{e(next(s for s in lessons if s["unit"]==u and s["section"]=="grammar")["grammar_topic"])}</p><a href="../sb-u{u}-grammar/">Пояснення і практика →</a><a href="../sb-u{u}-grammar-2/">Застосування →</a></article>' for u in range(1,9))),('sb-wordlist','Лексика курсу',''.join(f'<article class="card"><h2>Unit {u}</h2><p>{e(" · ".join(w+" — "+v for w,v in next(s for s in lessons if s["unit"]==u)["vocabulary"]))}</p><a href="../sb-u{u}-vocabulary/">Практика →</a></article>' for u in range(1,9)))]:
  folder=GRADE/slug;folder.mkdir(exist_ok=True);html=common.reference_page(slug,title,body).replace('6 клас','9 клас').replace('grade=6','grade=9');(folder/'index.html').write_text(html);refs.append(dict(slug=slug,title=title))
 blocks=[]
 for u in range(9):
  group=[s for s in lessons if s['unit']==u];blocks.append(f'<section class="class-section" id="unit-{u}"><div class="class-heading"><h2>{"Starter" if not u else "Unit "+str(u)+" · "+e(group[0]["title"].split(": ")[0])}</h2></div><div class="cards">'+''.join(card(s) for s in group)+'</div></section>')
 extra=''.join(f'<article class="card ready"><h3>{e(s["title"])}</h3><a class="btn primary" href="{s["slug"]}/">Відкрити →</a></article>' for s in legacy+refs)
 page='<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>9 клас — повний курс</title><link rel="stylesheet" href="../assets/catalog.css"><link rel="stylesheet" href="../assets/lesson-theme.css"><link rel="stylesheet" href="../assets/grade7-catalog.css"><link rel="stylesheet" href="../assets/mobile.css"><script src="../assets/mobile.js" defer></script></head><body><div class="page"><header class="hero"><a class="home-link" data-site-nav="root" href="../">← Усі класи</a><h1>Англійська для 9 класу</h1><p class="lead">Карпюк, 2026 · Starter і всі 8 юнітів. Пояснення, практика, завдання зошита та оригінальні аудіозаписи SB і WB.</p></header><main class="catalog">'+''.join(blocks)+'<section class="class-section"><h2>Додаткові уроки й довідники</h2><div class="cards">'+extra+'</div></section></main><footer class="footer">Лишенко Володимир Миколайович</footer></div></body></html>';(GRADE/'index.html').write_text(page)
 root=ROOT/'index.html';html=root.read_text();start=html.index('<h2 id="class-9">');a=html.rfind('<section',0,start);b=html.index('</section>',start)+len('</section>');rootblock='<section class="class-section"><div class="class-heading"><h2 id="class-9"><a class="section-link" data-site-nav="grade" href="9/">9 клас →</a></h2><span>Starter · Unit 1–8 · аудіо SB і WB</span></div><div class="cards">'+''.join(card(s,'9/') for s in lessons)+extra.replace('href="','href="9/')+'</div></section>';root.write_text(html[:a]+rootblock+html[b:]);print('grade 9: built',len(lessons),'sections; retained',len(legacy),'lessons; 2 references')
if __name__=='__main__':main()
