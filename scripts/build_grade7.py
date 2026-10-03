"""Build the complete Karpiuk 2024 course from reviewed SB/AB lesson cards.

Scans remain in the teacher's local library. Published recordings are indexed by
media-manifest.json. Existing authored lessons retain their teaching content.
"""
from pathlib import Path
from html import escape, unescape
import json,re
import build_grade6 as common
ROOT=Path(__file__).resolve().parents[1];GRADE=ROOT/'7'
def e(value):return escape(str(value),quote=True)
def sources(s,media):
 lines=[f'# Джерела: {s["title"]}','', 'О. Карпюк, К. Карпюк. Англійська мова, 7 клас, видання 2024 року.','', '## Підручник (SB)']
 lines += [f'- `{a["path"]}` — друкована с. {a["printed_page"]}' for a in s['sb_assets']]
 lines += ['','## Activity Book (WB)']+[f'- `{a["path"]}` — друкована с. {a["printed_page"]}' for a in s['wb_assets']]
 lines += ['','## Аудіо']+[f'- {m["book"]}: `{m["source"]}` → [запис](../{m["file"]})' for m in media]
 lines += ['','Пояснення, короткі тексти й інтерактивні вправи — авторські адаптації. Аудіо оригінальне; адаптований текст не є його транскриптом. Скановані сторінки залишаються у локальному сховищі викладача.','']
 return '\n'.join(lines)
def players(media):
 if not media:return ''
 cards=[]
 for m in media:
  label=f'{m["book"]} · '+('вступ до юніту' if m['scope']=='unit_introductory_recording' else 'вступ' if m['scope']=='introductory_recording' or not m.get('source_exercise') else 'с. '+', '.join(map(str,m.get('source_pages',[])))+', впр. '+m['source_exercise'])
  cards.append(f'<article class="media-card"><h3>{e(label)}</h3><details><summary>Назва оригінального запису</summary><p data-dictionary-skip>{e(m["original_filename"])}</p></details><audio controls preload="none" src="../{e(m["file"])}"></audio><a href="../{e(m["file"])}" download>Завантажити запис</a></article>')
 return '<section id="listen"><h2>Слухай і перевіряй</h2><p>Спочатку визнач ситуацію та учасників, потім знайди деталі для відповідної вправи SB або WB. Вступ до юніту — короткий запис для початку теми.</p><div class="media-grid">'+''.join(cards)+'</div></section>'
def task_list(tasks,book):
 return '<ol data-dictionary-skip>'+''.join(f'<li>{book} с. {t["page"]}, впр. {t["exercise"]}: {e(t["instruction"])}</li>' for t in tasks)+'</ol>' if tasks else ''
def workbook(s):
 if not s['wb_pages']:return ''
 questions=s.get('workbook_questions',[]);qs=[]
 for n,q in enumerate(questions):
  q=dict(q);shift=(s['unit']+s['section_index']+n)%len(q['choices']);q['choices']=q['choices'][shift:]+q['choices'][:shift];q['answer']=(-shift)%len(q['choices']);qs.append(common.question_html(q,100+n).replace(f'<legend>{100+n}. ',f'<legend>{n+1}. '))
 practice=('<div class="practice"><h3>Слова й ситуації юніту: адаптація завдань зошита</h3>'+''.join(qs)+'<div class="actions"><button type="button" class="btn check">Перевірити</button><button type="button" class="btn reset">Спробувати заново</button><span class="result" role="status" aria-live="polite"></span></div></div>') if qs else ''
 return '<section id="workbook"><h2>Працюємо із зошитом</h2><p>WB с. '+', '.join(map(str,s['wb_pages']))+'. У друкованому зошиті виконай відповідні завдання; нижче — додаткова інтерактивна адаптація теми.</p>'+task_list(s['wb_tasks'],'WB')+practice+'</section>'
def card(s,prefix=''):
 return f'<article class="card ready"><span class="tag ready">{("Unit "+str(s["unit"])) if s["unit"] else "Starter"} · SB {", ".join(map(str,s["sb_pages"]))}</span><h3>{e(s["title"])}</h3><p>{e(s["title_uk"])}</p><a class="btn primary" href="{prefix}{s["slug"]}/">Почати урок →</a></article>'
def render_reference(slug,title,body):
 return common.reference_page(slug,title,body).replace('6 клас','7 клас')
def main():
 lessons=json.loads((GRADE/'lessons.json').read_text());media=json.loads((GRADE/'media-manifest.json').read_text())['entries'];by={s['slug']:s for s in lessons}
 common.source_pages=lambda s:[Path(a['path']) for a in s['sb_assets']]
 original_questions=common.questions
 def questions(s):
  out=[]
  for n,q in enumerate(original_questions(s)):
   q=dict(q);shift=(s['unit']+s['section_index']+n)%len(q['choices']);q['choices']=q['choices'][shift:]+q['choices'][:shift];q['answer']=(q['answer']-shift)%len(q['choices']);out.append(q)
  return out
 common.questions=questions;common.media_html=lambda s,ms:players(ms)
 for i,s in enumerate(lessons):
  ms=[m for m in media if m['id'] in s['media_ids']];folder=GRADE/s['slug'];folder.mkdir(exist_ok=True)
  html=common.render(s,ms,lessons[i-1] if i else None,lessons[i+1] if i+1<len(lessons) else None).replace('6 клас','7 клас').replace('6-u','7-u').replace('6 клас ·','7 клас ·')
  support='<section id="book-tasks"><h2>Застосуй у підручнику</h2>'+task_list(s['sb_tasks'],'SB')+'</section>'+workbook(s)
  html=html.replace('<nav class="lesson-links" aria-label="Інші уроки">',support+'<nav class="lesson-links" aria-label="Інші уроки">').replace('Підручник H. Q. Mitchell, Marileni Malkogianni, 6 клас, «Лінгвіст», 2023.','Підручник О. Карпюк, К. Карпюк, 7 клас, 2024.')
  # The grade replacement above also affects the source sentence.
  html=html.replace('Підручник H. Q. Mitchell, Marileni Malkogianni, 7 клас, «Лінгвіст», 2023.','Підручник О. Карпюк, К. Карпюк, 7 клас, 2024.')
  (folder/'index.html').write_text(html);(folder/'sources.md').write_text(sources(s,ms))
 # Preserve the ten existing authored lessons, update their source mapping and add recordings.
 existing={'clubs-and-hobbies':([8,9,10],[6,7,8]),'school-special-days':([11,12,13],[9,10]),'now-or-usually':([14,15],[]),'ask-about-school':([15,18,19],[]),'our-school-event':([16,17,20,21,22],[11,12,13,14]),'chores':([28,29,30],[18,19,20,21]),'sharing-chores':([31,32,33],[22,23]),'past-simple-questions':([34,35],[]),'past-continuous-questions':([37,38],[25]),'home-stories':([39,40,41,42,43],[26,27,28,29,30])}
 legacy=[]
 for slug,(sps,wps) in existing.items():
  unit=1 if slug in list(existing)[:5] else 2;matched=[s for s in lessons if set(s['sb_pages'])&set(sps)];ms=[m for m in media if m['lesson'] in {s['slug'] for s in matched}];s=dict(slug=slug,title=slug,unit=unit,sb_pages=sps,wb_pages=wps,sb_assets=[a for row in matched for a in row['sb_assets'] if a['printed_page'] in sps],wb_assets=[a for row in lessons for a in row['wb_assets'] if a['printed_page'] in wps],wb_tasks=[t for row in lessons for t in row['wb_tasks'] if t['page'] in wps],workbook_questions=[],section_index=0)
  path=GRADE/slug/'index.html';html=path.read_text();s['title']=unescape(re.sub('<[^>]+>','',re.search(r'<h1[^>]*>(.*?)<br',html,re.S)[1]));html=re.sub(r'<!-- grade7-source-support-start -->.*?<!-- grade7-source-support-end -->','',html,flags=re.S)
  support='<!-- grade7-source-support-start -->'+players(ms)+workbook(s)+'<!-- grade7-source-support-end -->';html=html.replace('</main>',support+'</main>');path.write_text(html);(path.parent/'sources.md').write_text(sources(s,ms));legacy.append(s)
 for slug,title,body in [('sb-grammar','Граматика курсу',''.join(f'<article class="card"><h2>Unit {u}</h2><p>{e(next(s for s in lessons if s["unit"]==u and s["section"]=="grammar")["example"])}</p><a href="../sb-u{u}-grammar/">Пояснення і практика →</a><a href="../sb-u{u}-grammar-2/">Застосування →</a></article>' for u in range(1,9))),('sb-wordlist','Лексика курсу',''.join(f'<article class="card"><h2>Unit {u}</h2><p>{e(" · ".join(w+" — "+v for w,v in next(s for s in lessons if s["unit"]==u)["vocabulary"]))}</p><a href="../sb-u{u}-vocabulary/">Практика →</a></article>' for u in range(1,9)))]:
  folder=GRADE/slug;folder.mkdir(exist_ok=True);(folder/'index.html').write_text(render_reference(slug,title,body))
 blocks=[]
 for u in range(9):
  group=[s for s in lessons if s['unit']==u];blocks.append(f'<section class="class-section" id="unit-{u}"><div class="class-heading"><h2>{"Starter" if not u else "Unit "+str(u)}</h2><span>{len(group)} розділів</span></div><div class="cards">'+''.join(card(s) for s in group)+'</div></section>')
 extra=''.join(f'<article class="card ready"><h3>{e(s["title"])}</h3><a class="btn primary" href="{s["slug"]}/">Відкрити →</a></article>' for s in legacy)+''.join(f'<article class="card ready"><h3>{title}</h3><a class="btn primary" href="{slug}/">Відкрити →</a></article>' for slug,title in [('sb-grammar','Граматика курсу'),('sb-wordlist','Лексика курсу')])
 page='<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>7 клас — повний курс</title><link rel="stylesheet" href="../assets/catalog.css"><link rel="stylesheet" href="../assets/lesson-theme.css"><link rel="stylesheet" href="../assets/grade7-catalog.css"><link rel="stylesheet" href="../assets/mobile.css"><script src="../assets/mobile.js" defer></script></head><body><div class="page"><header class="hero"><a class="home-link" data-site-nav="root" href="../">← Усі класи</a><h1>Англійська для 7 класу</h1><p class="lead">Карпюк, 2024 · Starter і всі 8 юнітів. Пояснення, вправи, завдання зошита та оригінальні аудіозаписи.</p></header><main class="catalog">'+''.join(blocks)+'<section class="class-section"><h2>Додаткові уроки й довідники</h2><div class="cards">'+extra+'</div></section></main><footer class="footer">Лишенко Володимир Миколайович</footer></div></body></html>'
 (GRADE/'index.html').write_text(page)
 root=ROOT/'index.html';html=root.read_text();start=html.index('<div class="class-heading"><h2 id="class-7">');section_start=html.rfind('<section',0,start);end=html.index('</section>',start)+len('</section>')
 rootblock='<section class="class-section"><div class="class-heading"><h2 id="class-7"><a class="section-link" data-site-nav="grade" href="7/">7 клас →</a></h2><span>Starter · Unit 1–8 · аудіо SB і WB</span></div><div class="cards">'+''.join(card(s,'7/') for s in lessons)+extra.replace('href="','href="7/')+'</div></section>'
 root.write_text(html[:section_start]+rootblock+html[end:]);print(f'grade 7: built {len(lessons)} course sections; retained {len(legacy)} authored lessons; 2 references')
if __name__=='__main__':main()
