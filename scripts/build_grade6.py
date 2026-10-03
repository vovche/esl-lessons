"""Render the grade 6 textbook course from reviewed lesson data."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
GRADE = ROOT / '6'
SOURCE = Path('/home/why/-teach/6-eng/sb-pages')
UNITS = {1:"That's me!",2:'Travelling',3:'Adventure',4:'Places',5:'Modern world',6:'Healthy life',7:'Teen life',8:'Fame'}
FOLDERS = {int(p.name[1]):p for p in SOURCE.glob('u[1-8]*')}
PROPER_NAMES = ['The Phantom of the Opera','Central Park','Hyde Park','San Francisco','Loch Ness','White Fang','South Pole','Edinburgh','Scotland','London','Venice','Egypt','Kyiv','Cats','The Oscars','Oscars','Coco','Ukraine']
NAME_PATTERN = re.compile('|'.join(r'\b'+re.escape(name)+r'\b' for name in sorted(PROPER_NAMES,key=len,reverse=True)))


def e(value: object) -> str:
    return escape(str(value), quote=True)


def text(value: str) -> str:
    parts=[];last=0
    for match in NAME_PATTERN.finditer(value):
        parts.extend((e(value[last:match.start()]),f'<span data-dictionary-skip>{e(match[0])}</span>'));last=match.end()
    parts.append(e(value[last:]));return ''.join(parts)


def source_pages(lesson: dict) -> list[Path]:
    code=lesson['code']
    if re.fullmatch(r'[1-8][a-e]',code):
        return sorted((FOLDERS[lesson['unit']]/code).glob('*.png'))
    if code=='hello':return sorted((SOURCE/'intro-hello').glob('*.png'))
    if code.startswith('culture-ukraine'):
        return [SOURCE/'u9-rest/2 - culture page Ukraine'/f'page-{110+int(code[-1])}.png']
    if code.startswith('clil-'):
        number={'history':113,'geography':114,'sport':115,'music':116}[code[5:]]
        return [SOURCE/'u9-rest/3 - clil'/f'page-{number}.png']
    if code.startswith('round-up'):
        return [SOURCE/'u9-rest/1 - roundup'/f'page-{102+lesson["unit"]}.png']
    if code=='pair-work':return sorted((SOURCE/'u9-rest/4 - pair work activities').glob('*.png'))
    if code=='learning-tips':return [SOURCE/'u9-rest/page -131-learning tips.png', SOURCE/'u9-rest/page -132-project skills.png']
    extras={'culture-1':FOLDERS[2]/'page-018-culture-page.png','culture-2':FOLDERS[3]/'page-042-culture page.png','culture-3':FOLDERS[5]/'page-66-culture page.png','culture-4':FOLDERS[7]/'page-90-culture page.png','song-1':FOLDERS[2]/'page-030-song1.png','song-2':FOLDERS[4]/'page-54-song2.png','song-3':FOLDERS[6]/'page-78-song3.png','song-4':FOLDERS[8]/'page-102-song4.png'}
    return [extras[code]]


def printed_page(path: Path) -> int:
    number=int(re.search(r'(\d+)',path.stem)[1])
    return number


def questions(lesson: dict) -> list[dict]:
    if lesson['code'].startswith('round-up'):return lesson['questions']
    vocab=lesson['vocabulary']
    lexical=[]
    for i,(word,meaning) in enumerate(vocab[:3]):
        lexical.append(dict(prompt=f'Обери значення слова {word}.',choices=[meaning,vocab[(i+2)%len(vocab)][1],vocab[(i+3)%len(vocab)][1]],answer=0,why=f'{word} — {meaning}.'))
    return lexical+lesson['questions']


def question_html(q: dict, n: int) -> str:
    shift=n%len(q['choices']);choices=q['choices'][shift:]+q['choices'][:shift];answer=(q['answer']-shift)%len(choices)
    options=''.join(f'<label class="option"><input type="radio" name="q{n}" value="{i}"><span>{text(choice)}</span></label>' for i,choice in enumerate(choices))
    link=f'<a href="../{e(q["sourceLesson"])}/">Повторити правило →</a>' if q.get('sourceLesson') else ''
    return f'<div class="question" data-answer="{answer}"><fieldset><legend>{n}. {text(q["prompt"])}</legend>{options}</fieldset><p class="answer-why" hidden>{text(q["why"])}</p><p class="feedback" role="status"></p>{link}</div>'


def media_html(lesson:dict, media:list[dict]) -> str:
    if not media:return ''
    cards=[]
    for item in media:
        name=Path(item['source']).stem
        act=re.search(r'act_(\d+)([a-z]?)',name)
        label=('Вправа '+act[1]+act[2]) if act else ('Відеодіалог' if item['kind']=='video' else 'Тематичний запис')
        href='media/'+Path(item['file']).name
        player=f'<video controls preload="none" src="{e(href)}"></video>' if item['kind']=='video' else f'<audio controls preload="none" src="{e(href)}"></audio>'
        cards.append(f'<article class="media-card"><h3>{e(label)}</h3>{player}<a href="{e(href)}" download>Завантажити запис</a><details><summary>Назва оригінального файлу</summary><p class="file-name" data-dictionary-skip>{e(Path(item["source"]).name)}</p></details></article>')
    song=lesson['code'].startswith('song-')
    task='Послухай пісню: спочатку визнач тему, потім випиши три слова, які впізнав. Перекажи зміст своїми словами.' if song else 'Обери запис і послухай двічі. Спершу визнач ситуацію та учасників; потім випиши три слова або фрази й один факт, який почув. Зістав деталі з відповідною вправою підручника.'
    return f'<section id="listen"><h2><span class="num">03</span> Слухай і помічай</h2><p class="section-intro">{task}</p><p class="schedule">Це оригінальні записи підручника. Текст для читання вище є короткою адаптацією; деталі й формулювання в записі можуть відрізнятися.</p><div class="media-grid">'+''.join(cards)+'</div><div class="write-card"><label for="listening-notes">Три слова або фрази та один почутий факт</label><textarea id="listening-notes" data-save="listening" placeholder="Мої нотатки…"></textarea><button type="button" class="btn save-notes">Зберегти нотатки</button><p class="saved" role="status"></p></div></section>'


def render(lesson:dict,media:list[dict],previous:dict|None,following:dict|None)->str:
    u=lesson['unit'];code=lesson['code'];intro=''
    if re.fullmatch('[1-8]a',code):
        intro=f'<div class="schedule"><strong>Починаємо Unit {u} · {e(UNITS[u])}</strong><p>{e(lesson["unitIntro"])}</p></div>'
    vocab=''.join(f'<li><span lang="en">{text(word)}</span><span>{e(meaning)}</span></li>' for word,meaning in lesson['vocabulary'])
    qs=questions(lesson)
    unitlabel=f'Unit {u} · {code}' if u else 'Вступ і додаткові матеріали'
    nav=''.join(f'<a href="../{x["slug"]}/">{label}</a>' for x,label in [(previous,'← Попередній урок'),(following,'Наступний урок →')] if x)
    pages=source_pages(lesson);pagenums=', '.join(str(printed_page(p)) for p in pages)
    review=''
    if lesson.get('reviewLinks'):
        review='<nav class="lesson-links" aria-label="Повторити уроки">'+''.join(f'<a href="../{slug}/">{slug.removeprefix("sb-")}</a>' for slug in lesson['reviewLinks'])+'</nav>'
    listenlink='<a href="#listen">03 Слухай</a>' if media else ''
    applynum='04' if media else '03'
    return f'''<!doctype html>
<html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="6 клас · {e(lesson['title_uk'])}: пояснення, лексика, читання, вправи й словник вимови."><title>{e(lesson['title'])} — 6 клас</title>
<link rel="stylesheet" href="../../assets/lesson-theme.css"><link rel="stylesheet" href="../../assets/grade7-lesson.css"><link rel="stylesheet" href="../../assets/grade6-lesson.css"><link rel="stylesheet" href="../../assets/lesson-dictionary.css">
<script src="../../assets/grade6-lesson.js" defer></script><script src="../../assets/lesson-dictionary.js" defer></script><link rel="stylesheet" href="../../assets/mobile.css"><script src="../../assets/mobile.js" defer></script></head>
<body data-unit="6-u{u}" data-lesson="{lesson['slug']}" data-dictionary-root>
<header class="hero"><div class="wrap"><nav class="crumbs" aria-label="Шлях до уроку"><a data-site-nav="root" href="../../">Усі класи</a><span>›</span><a data-site-nav="grade" href="../">6 клас</a><span>›</span><span aria-current="page">{e(unitlabel)}</span></nav>
<h1>{text(lesson['title'])}<br><span>{e(lesson['title_uk'])}</span></h1><p>Розберися в темі, прочитай приклади й застосуй англійську у власній відповіді.</p><div class="meta"><span data-dictionary-skip>{e(unitlabel)}</span><span>≈ 30–40 хвилин</span><span>{len(qs)} завдань із поясненнями</span></div></div></header>
<main class="wrap"><nav class="jump" aria-label="Частини уроку"><a href="#learn">01 Розберися</a><a href="#practice">02 Спробуй</a>{listenlink}<a href="#apply">{applynum} Використай</a></nav>
<section id="learn"><h2><span class="num">01</span> Розберися</h2>{intro}<p class="section-intro">Натисни підкреслене англійське слово, щоб побачити переклад і послухати чотири голоси.</p><div class="grid"><article class="card"><h3>Лексика теми</h3><ul class="vocabulary">{vocab}</ul></article><article class="card"><h3>Правило й приклади</h3><p>{text(lesson['rule'])}</p><div class="example" lang="en">{text(lesson['example'])}</div></article><article class="card"><h3>Прочитай і знайди факти</h3><p lang="en">{text(lesson['reading'])}</p><p class="adapted">Короткий текст адаптовано за темою підручника.</p></article></div>{review}<div class="schedule"><strong>Маршрут уроку</strong><p>8 хв · правило й лексика → 8 хв · читання та вправи → 8 хв · слухання або повторення → 8 хв · власна відповідь.</p></div></section>
<section id="practice" class="practice"><h2><span class="num">02</span> Спробуй</h2><p class="section-intro">Обери відповіді. Перевірка покаже результат і пояснення; помилки можна виправити.</p>{''.join(question_html(q,n) for n,q in enumerate(qs,1))}<div class="actions"><button type="button" class="btn check">Перевірити відповіді</button><button type="button" class="btn reset">Спробувати заново</button><span class="result" role="status" aria-live="polite"></span></div></section>
{media_html(lesson,media)}
<section id="apply"><h2><span class="num">{applynum}</span> Використай самостійно</h2><div class="write-card"><p>{e(lesson['write']['prompt'])}</p><p class="hint"><strong>Початок:</strong> <span lang="en">{text(lesson['write']['starter'])}</span></p><label for="my-answer">Твоя відповідь англійською</label><textarea id="my-answer" data-save="writing" placeholder="Напиши тут…"></textarea><button type="button" class="btn save-notes">Зберегти відповідь</button><p class="saved" role="status"></p><details><summary>Як перевірити себе</summary><ul><li>Я виконав усі частини завдання.</li><li>Мої приклади відповідають правилу цього уроку.</li><li>Я перевірив порядок слів, форми дієслів і написання.</li><li>Я можу пояснити зміст своєї відповіді.</li></ul></details></div></section>
<nav class="lesson-links" aria-label="Інші уроки">{nav}<a href="../#unit-{u}">Каталог 6 класу</a><a href="../sb-grammar/">Граматичний довідник</a><a href="../sb-wordlist/">Лексика курсу</a></nav></main>
<footer class="footer"><div class="wrap"><p>Підручник H. Q. Mitchell, Marileni Malkogianni, 6 клас, «Лінгвіст», 2023. Сторінки: {e(pagenums)}. <a href="sources.md">Джерела та назви файлів</a>. <a href="../../dictionary/">Словник вимови</a>.</p><p>Пояснення, короткі тексти й інтерактивні вправи адаптовано для самостійної роботи.</p><p class="author">Укладач матеріалу: Лишенко Володимир Миколайович</p></div></footer></body></html>'''


UNIT_INTROS={1:'Розкажи про школу, зовнішність, характер і захоплення. Наприкінці склади профіль друга.',2:'Пригадай подорож, обери транспорт, підготуйся до поїздки й напиши лист про неї.',3:'Опиши пригоду, розрізняй фон і події та розкажи, що відчували герої.',4:'Поясни маршрут, порівняй місця й опиши місто, де хотів би жити.',5:'Розкажи про плани, ґаджети, довкілля та запрошення на корисну подію.',6:'Поговори про їжу, самопочуття, спорт і нове активне захоплення.',7:'Розкажи про досвід, музику, повідомлення, покупки та поради.',8:'Читай новини, описуй виступи, створення журналу й фільмів та напиши рецензію.'}


def sources_md(lesson,media):
    pages=source_pages(lesson)
    intro=[]
    if re.fullmatch('[1-8]a',lesson['code']):
        intro=sorted(FOLDERS[lesson['unit']].glob('*intro.png'))
    md=f'# Джерела: {lesson["title"]}\n\nПідручник H. Q. Mitchell, Marileni Malkogianni, 6 клас, «Лінгвіст», 2023.\n\nЛокальне джерело: `{SOURCE}`.\n\n'
    md+='\n'.join(f'- `{p.relative_to(SOURCE)}` — друкована с. {printed_page(p)}' for p in intro+pages)+'\n\n'
    if media:
        md+='## Записи підручника\n\n'+ '\n'.join(f'- Оригінал `{x["source"]}` → [запис](media/{Path(x["file"]).name})' for x in media)+'\n\n'
        if lesson['unit']:
            audio=FOLDERS[lesson['unit']]/'audio.md'
            if audio.exists():md+='Сторінка аудіоджерела, записана викладачем:\n\n'+audio.read_text().strip()+'\n\n'
    md+='Короткий текст, пояснення та вправи адаптовано за матеріалом цих сторінок. Оригінальні аудіо й відео містять діалоги та завдання підручника, тому не є дослівним озвученням адаптації. Скановані сторінки залишаються в локальному сховищі викладача.\n'
    return md


def catalog_card(lesson,prefix=''):
    tag=f'Unit {lesson["unit"]} · {lesson["code"]}' if lesson['unit'] else 'Додатковий урок'
    return f'<article class="card ready"><span class="tag ready">{e(tag)}</span><h3>{e(lesson["title"])}</h3><p>{e(lesson["title_uk"])}</p><a class="btn primary" href="{prefix}{lesson["slug"]}/">Почати урок →</a></article>'


def reference_page(slug,title,body):
    return f'''<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} — 6 клас</title><link rel="stylesheet" href="../../assets/lesson-theme.css"><link rel="stylesheet" href="../../assets/grade7-lesson.css"><link rel="stylesheet" href="../../assets/grade6-lesson.css"><link rel="stylesheet" href="../../assets/lesson-dictionary.css"><script src="../../assets/lesson-dictionary.js" defer></script><link rel="stylesheet" href="../../assets/mobile.css"><script src="../../assets/mobile.js" defer></script></head><body data-dictionary-root><header class="hero"><div class="wrap"><nav class="crumbs"><a data-site-nav="root" href="../../">Усі класи</a><span>›</span><a data-site-nav="grade" href="../">6 клас</a></nav><h1>{e(title)}</h1><p>Обери тему, прочитай приклад і повернися до уроку для практики.</p></div></header><main class="wrap reference">{body}</main><footer class="footer"><div class="wrap"><a href="../">Усі уроки 6 класу</a> · <a href="../../dictionary/?q=&amp;grade=6">Словник вимови</a><p class="author">Укладач матеріалу: Лишенко Володимир Миколайович</p></div></footer></body></html>'''


def main():
    lessons=json.loads((GRADE/'lessons.json').read_text())
    media=json.loads((GRADE/'media-manifest.json').read_text())['entries']
    sequence=[next(x for x in lessons if x['code']=='hello')]
    for u in UNITS:
        sequence += [x for x in lessons if x['unit']==u and len(x['code'])==2]
        sequence += [x for x in lessons if x['unit']==u and len(x['code'])!=2]
    sequence += [x for x in lessons if x['unit']==0 and x['code']!='hello']
    for i,lesson in enumerate(sequence):
        lesson['unitIntro']=UNIT_INTROS.get(lesson['unit'],'')
        dest=GRADE/lesson['slug'];dest.mkdir(exist_ok=True)
        recordings=[x for x in media if x['lesson']==lesson['slug']]
        (dest/'index.html').write_text(render(lesson,recordings,sequence[i-1] if i else None,sequence[i+1] if i+1<len(sequence) else None))
        (dest/'sources.md').write_text(sources_md(lesson,recordings))
    sections='<section class="class-section" id="unit-0"><div class="class-heading"><h2>Починаємо навчання</h2></div><div class="cards">'+catalog_card(sequence[0])+'</div></section>'
    for u,title in UNITS.items():
        group=[x for x in sequence if x['unit']==u]
        sections+=f'<section class="class-section" id="unit-{u}"><div class="class-heading"><h2>Unit {u} · {e(title)}</h2></div><p>{e(UNIT_INTROS[u])}</p><div class="cards">'+''.join(catalog_card(x) for x in group)+'</div></section>'
    additional=[x for x in sequence if x['unit']==0 and x['code']!='hello']
    sections+='<section class="class-section"><div class="class-heading"><h2>Культура, предметні уроки та проєкти</h2></div><div class="cards">'+''.join(catalog_card(x) for x in additional)+'</div></section>'
    refcards=''.join(f'<article class="card ready"><h3>{title}</h3><p>{description}</p><a class="btn primary" href="{slug}/">Відкрити →</a></article>' for slug,title,description in [('sb-grammar','Граматичний довідник','Правила й приклади з усіх юнітів.'),('sb-wordlist','Лексика курсу','Слова й фрази за уроками з вимовою.'),('jolly-phonics','Jolly Phonics: 42 звуки','Тренажер звуків, картки та історія проходжень.')])
    sections+='<section class="class-section"><div class="class-heading"><h2>Довідники й тренажери</h2></div><div class="cards">'+refcards+'</div></section>'
    (GRADE/'index.html').write_text(f'''<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Англійська для 6 класу — ESL Lessons</title><link rel="stylesheet" href="../assets/catalog.css"><link rel="stylesheet" href="../assets/lesson-theme.css"><link rel="stylesheet" href="../assets/grade7-catalog.css"><link rel="stylesheet" href="../assets/mobile.css"><script src="../assets/mobile.js" defer></script></head><body><div class="page"><header class="hero"><a class="home-link" data-site-nav="root" href="../">← Усі класи</a><h1>Англійська для 6 класу</h1><p class="lead">8 юнітів підручника: 40 основних уроків, культурні сторінки, пісні, повторення й предметні проєкти. Теорія українською, інтерактивні вправи та чотири голоси вимови для навчальних слів.</p><nav class="grade-nav" aria-label="Юніти">{''.join(f'<a href="#unit-{u}">Unit {u}</a>' for u in UNITS)}</nav></header><main class="catalog">{sections}</main><footer class="footer">ESL Lessons · 6 клас · матеріали за підручником H. Q. Mitchell, Marileni Malkogianni, 2023<br><span class="author">Укладач матеріалу: Лишенко Володимир Миколайович</span></footer></div></body></html>''')
    grammar=''
    for u,title in UNITS.items():
        grammar+=f'<section><h2>Unit {u} · {e(title)}</h2><div class="reference-grid">'
        for x in lessons:
            if x['unit']==u and len(x['code'])==2:
                grammar+=f'<article class="card"><h3>{e(x["title_uk"])}</h3><p>{text(x["rule"])}</p><div class="example" lang="en">{text(x["example"])}</div><a class="lookup" href="../{x["slug"]}/">Практикувати в уроці →</a></article>'
        grammar+='</div></section>'
    irregular=[('be','was/were','been','бути'),('begin','began','begun','починати'),('break','broke','broken','ламати'),('bring','brought','brought','приносити'),('buy','bought','bought','купувати'),('come','came','come','приходити'),('do','did','done','робити'),('drink','drank','drunk','пити'),('eat','ate','eaten','їсти'),('feel','felt','felt','відчувати'),('find','found','found','знаходити'),('get','got','got','отримувати'),('give','gave','given','давати'),('go','went','gone','йти'),('have','had','had','мати'),('hear','heard','heard','чути'),('know','knew','known','знати'),('leave','left','left','залишати'),('make','made','made','робити'),('read','read','read','читати'),('ride','rode','ridden','їздити'),('run','ran','run','бігти'),('say','said','said','казати'),('see','saw','seen','бачити'),('send','sent','sent','надсилати'),('sing','sang','sung','співати'),('speak','spoke','spoken','говорити'),('take','took','taken','брати'),('tell','told','told','розповідати'),('think','thought','thought','думати'),('wake','woke','woken','прокидатися'),('wear','wore','worn','носити'),('win','won','won','перемагати'),('write','wrote','written','писати')]
    grammar+='<section><h2>Неправильні дієслова</h2><p>Друга форма потрібна для Past Simple; третя — після have/has у Present Perfect і після be у пасиві. Натисни форму, щоб послухати вимову.</p><div class="table-scroll"><table><thead><tr><th>Основна форма</th><th>Минулий час</th><th>Третя форма</th><th>Переклад</th></tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+text(cell)+'</td>' for cell in row)+'</tr>' for row in irregular)+'</tbody></table></div><p lang="en">I went home yesterday. I have been there before. The letter was written yesterday.</p></section>'
    words=''
    for x in sequence:
        words+=f'<section><h2><a href="../{x["slug"]}/">{e(x["code"])} · {e(x["title_uk"])}</a></h2><ul class="vocabulary wordlist">'+''.join(f'<li><span lang="en">{text(w)}</span><span>{e(m)}</span></li>' for w,m in x['vocabulary'])+'</ul></section>'
    for slug,title,body in [('sb-grammar','Граматичний довідник',grammar),('sb-wordlist','Лексика курсу',words)]:
        dest=GRADE/slug;dest.mkdir(exist_ok=True);(dest/'index.html').write_text(reference_page(slug,title,body))
        sources=sorted((SOURCE/'u9-rest'/('5 - grammar reference' if slug=='sb-grammar' else '6 - wordlist')).glob('*.png'))
        if slug=='sb-grammar':sources.append(SOURCE/'u9-rest/page -130-irregular verbs.png')
        (dest/'sources.md').write_text('# Джерела\n\n'+ '\n'.join(f'- `{p}`' for p in sources)+'\n\nДовідник адаптовано до лексики й правил створених уроків.\n')
    root=(ROOT/'index.html').read_text();start=root.index('<section class="class-section" aria-labelledby="class-6">');end=root.index('<section class="class-section" aria-labelledby="class-7">')
    rootsection='<section class="class-section" aria-labelledby="class-6"><div class="class-heading"><h2 id="class-6"><a class="section-link" data-site-nav="grade" href="6/">6 клас →</a></h2><span>8 юнітів · 40 основних уроків + додаткові матеріали</span></div><div class="cards">'+''.join(catalog_card(x,'6/') for x in sequence)+refcards.replace('href="','href="6/')+'</div></section>\n'
    (ROOT/'index.html').write_text(root[:start]+rootsection+root[end:])
    print(f'Built {len(sequence)} grade 6 lessons and 2 reference pages')


if __name__=='__main__':main()
