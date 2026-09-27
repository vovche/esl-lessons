"""Build the source-backed, 30-minute Unit 1–2 lessons for grade 9."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRADE = ROOT / '9'
DATA = [GRADE / 'unit1-lessons.json', GRADE / 'unit2-lessons.json']
TEXTBOOK = '/home/why/-teach/9-eng/9-klas-angliyska-karpuk-2026.pdf'
WORKBOOK_ROOT = '/home/why/-teach/9-eng/друкований зошит'


def e(value: object) -> str:
    return escape(str(value), quote=True)


def page_list(pages: list[int], separator: str) -> str:
    groups: list[str] = []
    start = end = pages[0]
    for page in pages[1:] + [None]:
        if page is not None and page == end + 1:
            end = page
            continue
        groups.append(str(start) if start == end else f'{start}–{end}')
        start = end = page
    return separator.join(groups)


def render_question(question: dict, number: int, prefix: str) -> str:
    rotation = number % len(question['choices'])
    rotated = question['choices'][rotation:] + question['choices'][:rotation]
    answer = (question['answer'] - rotation) % len(question['choices'])
    choices = ''.join(
        f'<label class="option"><input type="radio" name="{prefix}-q{number}" value="{index}"><span>{e(choice)}</span></label>'
        for index, choice in enumerate(rotated)
    )
    return (
        f'<div class="question" data-answer="{answer}">'
        f'<fieldset><legend>{number}. {e(question["prompt"])}</legend>{choices}</fieldset>'
        f'<span class="answer-why" hidden>{e(question["why"])}</span>'
        '<p class="feedback" aria-live="polite"></p></div>'
    )


def render_lesson(lesson: dict, previous: dict | None, following: dict | None, position: int) -> str:
    unit = lesson['unit']
    pages = lesson['sources']
    workbook = page_list(pages['workbook'], ',')
    textbook = page_list(pages['textbook'], ', ')
    cards = ''.join(
        '<article class="card">'
        f'<h3>{number}. {e(card["title"])}</h3>'
        f'<p>{e(card["body"])}</p>'
        f'<div class="example" lang="en">{e(card["example"])}</div>'
        '</article>'
        for number, card in enumerate(lesson['cards'], 1)
    )
    questions = ''.join(render_question(question, number, lesson['slug']) for number, question in enumerate(lesson['questions'], 1))
    checks = ''.join(f'<li>{e(item)}</li>' for item in lesson['write']['checklist'])
    lesson_links = ''.join(
        f'<a href="../{e(neighbor["slug"])}/">{label}</a>'
        for neighbor, label in ((previous, '← Попередній урок'), (following, 'Наступний урок →'))
        if neighbor
    )
    if lesson.get('extra_link'):
        link = lesson['extra_link']
        lesson_links += f'<a href="{e(link["href"])}">{e(link["text"])}</a>'
    return f'''<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="9 клас, Unit {unit}: {e(lesson['title_uk'])}. Інтерактивний урок англійської на 30 хвилин.">
  <title>{e(lesson['title'])} — 9 клас</title>
  <link rel="stylesheet" href="../../assets/lesson-theme.css">
  <link rel="stylesheet" href="../../assets/grade9-lesson.css">
  <link rel="stylesheet" href="../../assets/lesson-dictionary.css">
  <script src="../../assets/grade9-lesson.js" defer></script>
  <script src="../../assets/lesson-dictionary.js" defer></script>
</head>
<body data-unit="u{unit}" data-lesson="{e(lesson['slug'])}" data-dictionary-root>
  <header class="hero"><div class="wrap">
    <nav class="crumbs" aria-label="Шлях до уроку"><a data-site-nav="root" href="../../">Усі класи</a><span>›</span><a data-site-nav="grade" href="../">9 клас</a><span>›</span><span aria-current="page">Unit {unit} · урок {position}</span></nav>
    <h1>{e(lesson['title'])}<br><span>{e(lesson['title_uk'])}</span></h1>
    <p>{e(lesson['lead'])}</p>
    <div class="meta"><span>Unit {unit} · урок {position} із 6</span><span>≈ 30 хвилин</span><span>8 запитань + власна відповідь</span></div>
  </div></header>
  <main class="wrap">
    <nav class="jump" aria-label="Частини уроку"><a href="#learn">01 Розберися</a><a href="#practice">02 Перевір себе</a><a href="#apply">03 Використай</a></nav>
    <section id="learn"><h2><span class="num">01</span> Розберися</h2><p class="section-intro">{e(lesson['learn_intro'])}</p><div class="grid">{cards}</div><div class="schedule"><strong>Маршрут на 30 хвилин</strong><p>9 хв · приклади й читання → 10 хв · самоперевірка → 8 хв · власна відповідь → 3 хв · перевірка за критеріями.</p></div></section>
    <section id="practice" class="practice"><h2><span class="num">02</span> Перевір себе</h2><p class="section-intro">Обери відповідь у кожному завданні. Після перевірки прочитай пояснення та спробуй виправити помилки.</p>{questions}<div class="actions"><button class="btn check" type="button">Перевірити відповіді</button><span class="result" role="status" aria-live="polite"></span></div></section>
    <section id="apply"><h2><span class="num">03</span> Використай самостійно</h2><div class="write-card"><p>{e(lesson['write']['prompt'])}</p><p class="hint"><strong>Початок:</strong> <span lang="en">{e(lesson['write']['starter'])}</span></p><label class="prompt" for="my-answer"><strong>Твоя відповідь англійською</strong></label><textarea id="my-answer" aria-label="Твоя відповідь англійською" placeholder="Напиши тут…"></textarea><div class="actions"><button type="button" class="btn save">Зберегти відповідь</button><span class="saved" role="status"></span></div><details><summary>Як перевірити себе</summary><ul>{checks}</ul></details></div></section>
    <nav class="lesson-links" aria-label="Інші уроки">{lesson_links}<a href="../">Усі уроки 9 класу</a></nav>
  </main>
  <footer class="footer"><div class="wrap"><p><strong>Джерела уроку:</strong> Друкований зошит Unit {unit}, с. {e(workbook)}; підручник с. {e(textbook)}. <a href="sources.md">Детальні посилання на файли й сторінки</a>. <a href="../../dictionary/">Словник вимови</a>.</p><p>Приклади й інтерактивні запитання адаптовано для цього уроку.</p></div></footer>
</body>
</html>
'''


def render_sources(lesson: dict) -> str:
    unit = lesson['unit']
    folder = 'u1.p6-20' if unit == 1 else 'u2.p21-38'
    workbook = '\n'.join(f'   - `page-{page}.png` — с. {page}' for page in lesson['sources']['workbook'])
    textbook = page_list(lesson['sources']['textbook'], ', ')
    note = lesson['sources'].get('note', 'Пояснення, приклади та інтерактивні запитання адаптовано для уроку.')
    return f'''# Джерела до уроку «{lesson['title']}»

**Тема:** {lesson['title_uk']}.

1. Друкований зошит, Unit {unit}. Каталог джерела: `{WORKBOOK_ROOT}/{folder}/`.
{workbook}
2. Підручник О. Карпюк, К. Карпюк «Англійська мова. 9 клас» (2026), с. **{textbook}**. Файл: `{TEXTBOOK}`.

{note} Скановані сторінки й PDF зберігаються в локальному сховищі викладача поза репозиторієм.
'''


def main() -> None:
    lessons = [lesson for source in DATA for lesson in json.loads(source.read_text(encoding='utf-8'))]
    slugs = [lesson['slug'] for lesson in lessons]
    assert len(lessons) == 12 and len(slugs) == len(set(slugs))
    assert [lesson['unit'] for lesson in lessons] == [1] * 6 + [2] * 6
    for index, lesson in enumerate(lessons):
        assert len(lesson['cards']) == 3 and len(lesson['questions']) == 8, lesson['slug']
        assert all(len(question['choices']) == 3 and 0 <= question['answer'] < 3 for question in lesson['questions'])
        wb, tb = lesson['sources']['workbook'], lesson['sources']['textbook']
        assert wb == sorted(set(wb)) and tb == sorted(set(tb))
        assert all((6 <= page <= 20) if lesson['unit'] == 1 else (21 <= page <= 38) for page in wb)
        assert all((7 <= page <= 26 and page not in {18, 19}) if lesson['unit'] == 1 else (27 <= page <= 44) for page in tb)
        destination = GRADE / lesson['slug']
        destination.mkdir(parents=True, exist_ok=True)
        position = index % 6 + 1
        (destination / 'index.html').write_text(render_lesson(lesson, lessons[index - 1] if index else None, lessons[index + 1] if index + 1 < len(lessons) else None, position), encoding='utf-8')
        (destination / 'sources.md').write_text(render_sources(lesson), encoding='utf-8')
    print(f'Built {len(lessons)} grade 9 Unit 1–2 lessons')


if __name__ == '__main__':
    main()
