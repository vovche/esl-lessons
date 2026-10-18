#!/usr/bin/env python3
"""Export learner-ready Grade 7 missions; no teacher documents are published."""
import json
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'teacher/7/source-plan.json'
OUTPUT = ROOT / '7/simulations.json'

# Existing legacy pages receive only the corresponding language/content focus.
LEGACY = {
    2: ['clubs-and-hobbies'], 3: ['clubs-and-hobbies'],
    5: ['school-special-days'], 6: ['school-special-days'],
    7: ['now-or-usually'], 8: ['our-school-event'], 9: ['our-school-event'],
    10: ['ask-about-school'], 11: ['clubs-and-hobbies'],
    12: ['our-school-event'], 16: ['our-school-event'],
    18: ['home-stories'], 19: ['home-stories'], 20: ['chores'],
    21: ['sharing-chores'], 22: ['sharing-chores'],
    23: ['past-simple-questions'], 26: ['past-continuous-questions'],
    27: ['sharing-chores'], 28: ['home-stories'],
}
LEAD_IN = {2: 1, 18: 2, 33: 3, 48: 4, 66: 5, 84: 6, 102: 7, 119: 8}

TITLES = {
    1: 'Допоможи навчальній групі', 2: 'Камінці чи музика: знайди гурток',
    3: 'Знайди тиху роль у гуртку', 5: 'Фотовиставка до річниці школи',
    6: 'Два шкільні свята', 8: 'Сплануй шкільну подію',
    11: 'Запитай про вибір гуртка', 12: 'Напиши шкільну новину',
    18: 'Домовся про домашні справи', 19: 'Зміни план справ',
    21: 'Різні розклади — спільні справи', 22: 'Вибери справедливий план',
    24: 'Хто сьогодні допомагає вдома?', 27: 'Підготуй кімнату до свята',
    28: 'Передай повідомлення про справи', 33: 'Ввічливе запитання за столом',
    34: 'Різне приладдя — взаємна повага', 36: 'Знайди порядок у рецепті',
    37: 'Фуд-арт: картина з фруктів', 39: 'Розбери картку рецепта',
    42: 'Поясни кухонне приладдя', 43: 'Представ страву на папері',
    48: 'Порівняй зимові святкування', 49: 'Розкажи про вигадану традицію',
    51: 'Дві новорічні історії', 53: 'Знайди деталі зимових традицій',
    56: 'Thanksgiving: обери спосіб подякувати', 57: 'Easter: напиши вітання',
    66: 'Перевір спортивну новину', 67: 'Підготуй спортивні заголовки',
    69: 'Олімпійські цінності в дії', 70: 'Запитай про олімпійські цінності',
    72: 'Розрізни картки водних видів спорту', 75: 'Поясни underwater hockey',
    76: 'Знайди роль у спортивному гуртку', 77: 'Яна Клочкова: перевір спортивні факти',
    84: 'Попроси допомоги чітко', 85: 'Передай місце й спостережені факти',
    87: 'Підготуй записку до прийому', 88: 'Попроси пояснити незнайоме слово',
    90: 'Ввічливе прохання по допомогу', 94: 'Уточни запит у реєстратурі',
    95: 'Повідом про звернення по допомогу',
    102: 'Загублені роботи: зрозумій сюжет', 103: 'Різні смаки — ввічлива розмова',
    105: 'Відомі оперні театри', 106: 'Представ Національну оперу України',
    108: 'Чарлі Чаплін: прочитай біографічну картку',
    111: 'Порекомендуй вигаданий фільм', 112: 'Порівняй дві рецензії',
    119: 'Прочитай карту United Kingdom', 120: 'Створи допис про місто',
    122: 'Розпізнай визначні місця', 123: 'Київ: уявний маршрут на папері',
    125: 'Київ: знайди зупинки на картці', 128: 'Представ намальоване визначне місце',
    129: 'Обери маршрут і поясни вибір', 136: 'Спортивні новини: Past Simple Passive',
}
GRAMMAR_NAMES = {
    'present': 'Зараз чи зазвичай?', 'past': 'Що було вчора?',
    'past_cont': 'Що відбувалося тоді?', 'perfect': 'Що вже підготовлено?',
    'passive': 'Що роблять і хто це робить?', 'past_passive': 'Що було організовано?',
    'zero': 'Умова й звична дія', 'past_perfect': 'Яка дія була раніше?',
    'degree': 'Наскільки цікавий фільм?', 'comparison': 'Порівняй два варіанти',
    'determiners': 'Кожен відвідувач і обидва об’єкти',
    'conjunctions': 'Поєднай вибір і причину', 'tags': 'Уточни й перевір: question tags',
}
RULES = {
    'present': 'Present Simple describes routines. Use do/does in questions. Present Continuous describes an action happening now: am/is/are + verb-ing.',
    'past': 'Past Simple describes a completed past action. Use the past form in statements. After did or did not, use the base form of the verb.',
    'past_cont': 'Past Continuous describes an action in progress at a past moment: was/were + verb-ing. In questions, put was/were before the subject.',
    'perfect': 'Present Perfect connects an earlier action with now: have/has + past participle. In questions, put have/has before the subject.',
    'passive': 'Present Simple Passive: am/is/are + past participle. The subject receives the action. Use by to introduce the person who does it.',
    'past_passive': 'Past Simple Passive: was/were + past participle. In questions, put was/were before the subject. Use by to introduce the person who did the action.',
    'zero': 'For a general condition and its usual result, use if + Present Simple, Present Simple. This card practises language for asking for help.',
    'past_perfect': 'Past Perfect: had + past participle. It shows an action completed before another past action. In questions, put had before the subject.',
    'degree': 'Quite and very normally come before an adjective. Too means more than is suitable. Enough comes after the adjective.',
    'comparison': 'Compare with more/less + adjective + than. To show equal qualities, use as + adjective + as. Use the same as for matching things.',
    'determiners': 'Use each with a singular noun and both with a plural noun. Some is common in positive statements; any is common in questions and negatives.',
    'conjunctions': 'And adds an idea; but contrasts ideas; because gives a reason. Both ... and joins two items. Either ... or offers a choice.',
    'tags': 'Present Simple describes routines; Present Continuous describes actions now. A positive statement usually has a negative question tag; a negative statement has a positive tag. Match the auxiliary and pronoun.',
}
ROLES = {
    0: 'Помічник навчальної групи', 1: 'Редактор шкільної картки',
    2: 'Учасник команди домашніх справ', 3: 'Редактор кулінарної картки',
    4: 'Автор картки святкових традицій', 5: 'Спортивний кореспондент',
    6: 'Автор ввічливого запиту', 7: 'Редактор театральної та кінокартки',
    8: 'Укладач уявного маршруту',
}
GOALS = {
    'grammar': 'Обери мовні форми, що точно передають час, дію або зв’язок думок.',
    'review': 'Віднови потрібні мовні форми й застосуй їх у короткій фразі.',
    'portfolio': 'Перевір мовні форми та запиши один власний приклад.',
    'vocabulary': 'Знайди точні англійські слова й уживи одне у власній фразі.',
    'reading': 'Прочитай картку, знайди дві точні деталі та підтвердь їх словами тексту.',
    'listening': 'Прочитай англійську картку та перевір дві деталі її змісту.',
    'speaking': 'Добери точні деталі для короткої англійської репліки.',
    'writing': 'Перевір деталі картки перед створенням власного повідомлення.',
    'project': 'Звір факти для своєї тематичної картки.',
    'assessment': 'Самостійно перевір дві деталі англійської картки.',
}


def load_content():
    """Import data/functions without calling the document generator's main()."""
    return runpy.run_path(str(ROOT / 'scripts/build_teacher_grade7.py'))


def public_title(p):
    n, mode = p['number'], p['mode']
    if n in TITLES:
        return TITLES[n]
    unit_title = p['source']['topic'].split(' · ')[0]
    if mode in ('grammar', 'review', 'portfolio'):
        return GRAMMAR_NAMES[p['gid']]
    if mode == 'vocabulary':
        return unit_title + ': обери точне слово'
    if mode == 'listening':
        return {5: 'Спортивна картка: нові деталі', 6: 'Прочитай ввічливе прохання',
                7: 'Прочитай картку про актора', 8: 'Прочитай картку міського маршруту'}[p['u']]
    if mode == 'project':
        return {1: 'Підготуй картку шкільної події', 3: 'Підготуй картку страви',
                5: 'Підготуй спортивний допис', 7: 'Підготуй відгук про фільм'}[p['u']]
    if mode == 'assessment':
        return ('Школа, справи й традиції: нові деталі' if p['source']['semester'] == 1
                else 'Спорт, кіно й подорожі: нові деталі')
    return unit_title


def lesson_slugs(p, available):
    l, n, mode, u = p['source'], p['number'], p['mode'], p['u']
    slugs = list(l['section_ids'])
    if l['kind'] == 'pair_diagnostic':
        slugs = [f'sb-u{v}-{section}' for v in (u-1, u)
                 for section in ('look-back', 'self-check')]
    if l['kind'] == 'portfolio':
        # These particular missions practise the actual language family, not every unit.
        focused_unit = 1 if l['semester'] == 1 else 5
        slugs = [f'sb-u{focused_unit}-self-check', f'sb-u{focused_unit}-look-back']
    if n == 136:
        slugs = ['sb-u5-look-back', 'sb-u5-self-check']
    if n in LEAD_IN:
        slugs.append(f'sb-u{LEAD_IN[n]}-lead-in')
    if mode in ('grammar', 'review', 'portfolio'):
        slugs.append('sb-grammar')
    if mode == 'vocabulary':
        slugs.append('sb-wordlist')
    slugs.extend(LEGACY.get(n, []))
    slugs = list(dict.fromkeys(slugs))
    assert slugs and all(s in available for s in slugs), (n, slugs)
    return slugs


def grammar_source(p):
    if p['mode'] == 'review' and p['number'] != 136:
        pair = {2: ('past', 'past_cont'), 6: ('zero', 'past_perfect'),
                7: ('degree', 'comparison'), 8: ('determiners', 'conjunctions')}.get(p['u'])
        if pair:
            return '\n\n'.join(RULES[k] for k in pair)
    return RULES[p['gid']]


def hint(p):
    mode = p['mode']
    if mode in ('grammar', 'review', 'portfolio'):
        return 'Знайди підмет і часову підказку. Перевір допоміжне слово та форму дієслова.'
    if mode == 'vocabulary':
        return 'Пригадай значення слова; порівняй обидва варіанти, а не лише першу літеру.'
    return 'Знайди речення про цю деталь. Перевір, чи варіант відповідає саме на поставлене запитання.'


def production(p, cards):
    mode = p['mode']
    n, u = p['number'], p['u']
    if n == 4:
        return {'prompt': 'Опиши одну дію вигаданого героя англійською без оцінного ярлика.',
                'starter': 'The character likes …'}
    if mode not in ('grammar', 'review', 'portfolio', 'vocabulary'):
        if n in (3, 11):
            return {'prompt': 'Напиши одну англійську репліку, якою герой може попросити більше часу або письмову відповідь.',
                    'starter': 'Could I …, please?'}
        if u == 2:
            return {'prompt': 'Запропонуй англійською одну зміну плану справ з урахуванням ролі іншого вигаданого учасника.',
                    'starter': 'Could we share …? I can …'}
        if n in (33, 34):
            return {'prompt': 'Напиши одне ввічливе англійське запитання про незнайомий звичай за столом.',
                    'starter': 'Could you explain …, please?'}
        if n == 37:
            return {'prompt': 'Напиши перший крок паперового плану для нового вигаданого фуд-артиста.',
                    'starter': 'First, …'}
        if u == 4:
            return {'prompt': 'Запроси вигаданого гостя однією англійською реплікою, залишивши вибір долучитися або спостерігати.',
                    'starter': 'You can join or …'}
        if u == 6:
            return {'prompt': 'Напиши одне чітке англійське уточнення або прохання допомоги до дорослого від вигаданого персонажа.',
                    'starter': 'Could you …, please?'}
        if n in (103, 111, 112, 117):
            return {'prompt': 'Однією англійською реплікою прийми іншу думку про фільм і назви власний вибір без осуду.',
                    'starter': 'I see your point. I prefer …'}
    if mode in ('grammar', 'review', 'portfolio'):
        stem = re.sub(r'\s*\([^()]* / [^()]*\)\s*$', '', cards[0]['prompt'])
        return {'prompt': 'Запиши одне повне англійське речення з обраною формою.',
                'starter': stem}
    if mode == 'vocabulary':
        return {'prompt': 'Склади одне коротке англійське речення з одним словом із місії.',
                'starter': 'My card shows …'}
    if mode == 'speaking':
        return {'prompt': 'Напиши одну англійську репліку, яка уточнює деталь картки. Можна вигадати персонажа.',
                'starter': 'Could you repeat …, please?'}
    return {'prompt': 'Передай один підтверджений факт картки коротким реченням англійською.',
            'starter': 'The card says …'}


def mission(p, phase, content):
    learn = phase == 'learn'
    cards = content['simulation_cards' if learn else 'checking_cards'](p)
    letters = content['answer_positions'](p, 'learning' if learn else 'checking')
    if p['mode'] in ('grammar', 'review', 'portfolio'):
        source = grammar_source(p) if learn else ''
    elif p['mode'] == 'vocabulary':
        source = '\n'.join(en+' — '+uk for en, uk in p['lex'][:4]) if learn else ''
    else:
        source = '\n\n'.join(dict.fromkeys(c['source'] for c in cards))
    # Source-card assembly may add a sentence stop after an a.m./p.m. abbreviation.
    # Clean only that duplicated stop, preserving abbreviations and relative paths.
    source = re.sub(r'([ap]\.m\.)\.', r'\1', source)
    steps = []
    for c, letter in zip(cards, letters):
        ordered = [(c['answer'], 'advance'), (c['wrong'], 'retry')]
        if letter == 'B':
            ordered.reverse()
        steps.append({'prompt': c['prompt'],
                      'choices': [{'text': text, 'effect': effect} for text, effect in ordered],
                      'hint': hint(p)})
    return {'id': phase, 'mode': phase,
            'title': ('Відкрий картку: ' if learn else 'Нова картка: ') + public_title(p),
            'role': ('Редактор підсумкової тематичної картки' if p['mode'] == 'assessment' else ROLES[p['u']]),
            'goal': ('Прочитай картку й потренуйся перевіряти дві деталі з підказкою.'
                     if learn and p['mode'] == 'assessment' else GOALS[p['mode']]), 'source': source,
            'steps': steps, 'production': production(p, cards),
            'reflection': {key: content['sel_profile'](p)[key] for key in ('focus', 'prompt')}}


def export_data():
    content = load_content()
    lessons = json.loads(SOURCE.read_text(encoding='utf-8'))['lessons']
    available = {p.parent.name for p in (ROOT / '7').glob('*/index.html')}
    output = []
    for original in lessons:
        p = content['profile'](original)
        output.append({'id': f'g7-{p["number"]:03d}', 'number': p['number'],
                       'title': public_title(p), 'slugs': lesson_slugs(p, available),
                       'games': [mission(p, phase, content) for phase in ('learn', 'check')]})
    covered = {s for lesson in output for s in lesson['slugs']}
    assert covered == available, ('unmapped pages', sorted(available-covered))
    return {'version': 1, 'grade': 7, 'lessons': output}


def main():
    data = export_data()
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Exported {len(data["lessons"])} lessons, 280 learner missions, '
          f'{len({s for l in data["lessons"] for s in l["slugs"]})} existing page slugs.')


if __name__ == '__main__':
    main()
