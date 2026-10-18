#!/usr/bin/env python3
"""Export the 123 reviewed two-mission scripts into the public student schema.

Only authored card prompts, English stimuli and student-facing roles enter the
payload. Teacher answer labels are used solely to encode state transitions.
No answer commentary, assessment stimulus, reporting field or teacher script is
published. Run after build_teacher_grade6.py when the source missions change.
"""
from pathlib import Path
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
TEACHER = ROOT / 'teacher/6'
OUTPUT = ROOT / '6/simulations.json'


def extract_card(text, marker):
    match = re.search(re.escape(marker) + r'\n\n“(.*?)”\n\n([^\n]+)', text, re.S)
    if not match:
        raise ValueError(f'Missing authored card: {marker}')
    prompt, options = match.groups()
    choices = re.findall(r'(?:^|\s/\s)([A-C])\)\s*(.*?)(?=\s/\s[A-C]\)|$)', options)
    if [letter for letter, _ in choices] != ['A', 'B', 'C']:
        raise ValueError(f'Unexpected choices: {marker}: {options}')
    return prompt, [value.strip() for _, value in choices]


def reviewed_mission_data(lesson):
    """Read the exact cards and their reviewed transition labels, not worksheet MCQs."""
    number = lesson['number']
    text = (TEACHER / f'{number:03d}/games.md').read_text()
    titles = re.findall(r'^## [12]\. (?:Засвоєння, 7 хв|Перевірка, 5 хв) — (.+)$', text, re.M)
    labels = re.findall(r'(?:хід1|Хід2|заявка1|Заявка2) — ([ABC]) —', text)
    if len(titles) != 2 or len(labels) != 4:
        raise ValueError(f'Unrecognized reviewed game layout: {number}')
    role, goal = re.search(r'\nРоль: (.*?)\. Мета: (.*?)\n\nСтартовий стан:', text, re.S).groups()
    model = re.search(r'\nМодель: (.*?)\n\nМатеріал стану', text, re.S).group(1)
    learn_source = re.search(r'Матеріал стану \(можна читати й підкреслювати\): (.*?)\n\nКартка ходу1:', text, re.S).group(1)
    check_source = re.search(r'Окремий паралельний контекст.*?:\n\n(.*?)\n\nЗаявка1:', text, re.S).group(1)
    return {
        'titles': titles,
        'role': role,
        'goal': goal,
        'model': model,
        'sources': [learn_source, check_source],
        'cards': [extract_card(text, marker) for marker in ('Картка ходу1:', 'Картка ходу2:', 'Заявка1:', 'Заявка2:')],
        'labels': labels,
    }


def public_slugs(lesson, authored, existing):
    # Keep real calendar-to-page mappings. Integrated lessons also reach their
    # constituent topic pages; no public calendar directories are created.
    slugs = list(lesson['adaptation_ids'])
    # The correction workshop rehearses modules7–8. Its source manifest lists
    # every round-up as background, not as a suitable home for advanced games.
    if lesson['lesson_type'] == 'reflection':
        slugs = ['sb-round-up-7', 'sb-round-up-8']
    formal = lesson['lesson_type'] in ('pair_diagnostic', 'semester_check')
    if formal:
        unit = {28: 2, 53: 4, 86: 6, 115: 8}.get(lesson['number'], 4 if lesson['semester'] == 1 else 8)
        slugs.append(f'sb-round-up-{unit}')
    else:
        for block in authored['choose'](lesson, existing['adaptations']):
            if block.get('slug'):
                slugs.append(block['slug'])
    if lesson['lesson_type'] == 'reflection':
        slugs.append('sb-grammar')
    if lesson['lesson_type'] == 'module_intro':
        slugs.append('sb-wordlist')
    result = sorted({slug for slug in slugs if slug in existing['pages']})
    if not result:
        raise ValueError(f'Calendar mission without a real page: {lesson["number"]}')
    return result



# Information specified by the authored starting state, absent from the prose
# reading. These are fictional learner data, not classroom-management scripts.
INITIAL_DATA = {
    '4b': 'Imaginary map: School — Park — Library on one straight street.',
    '4d': 'Imaginary planets, size in arbitrary units: A = 3; B = 5; C = 8.',
    '7d': 'Imaginary shop: T-shirt size S = 8 pounds; size M = 10 pounds. The customer has 12 pounds.',
}


def learner_rule(adaptation):
    if adaptation['code'] == '5b':
        return 'Will + основна форма: прогноз, обіцянка або пропозиція допомоги. Заперечення: won’t. Запитання: Will you…? Will be able to + основна форма — майбутнє вміння.'
    return adaptation['rule']


def learning_support(lesson, adaptation, adaptations):
    vocabulary = '; '.join(f'{word} — {meaning}' for word, meaning in adaptation['vocabulary'][:8])
    parts = []
    if adaptation['code'] in INITIAL_DATA:
        parts.append(INITIAL_DATA[adaptation['code']])
    parts.append('Words: ' + vocabulary)
    if lesson['lesson_type'] != 'module_intro':
        if adaptation['code'].startswith('round-up-'):
            module = adaptation['code'][-1]
            # The two teaching cards use subunits a/b; the classroom recap's
            # instruction to open a later worksheet is unsuitable in the UI.
            rule = '\n'.join(learner_rule(adaptations[f'sb-{module}{part}']) for part in 'ab')
        else:
            rule = learner_rule(adaptation)
        parts.append(rule)
    return '\n\n'.join(parts)


def export_payload():
    source = json.loads((TEACHER / 'source-plan.json').read_text())
    authored = runpy.run_path(str(ROOT / 'scripts/build_teacher_grade6.py'))
    adaptations = authored['curate_adaptations']({a['slug']: a for a in source['adaptations']})
    existing = {'pages': {p.parent.name for p in (ROOT / '6').glob('*/index.html')}, 'adaptations': adaptations}
    result = {'version': 1, 'grade': 6, 'lessons': []}
    for lesson in source['lessons']:
        number = lesson['number']
        reviewed = reviewed_mission_data(lesson)
        adaptation = authored['game_adaptation'](lesson, adaptations)
        support = learning_support(lesson, adaptation, adaptations)
        missions = []
        for game_index, mode in enumerate(('learn', 'check')):
            steps = []
            for round_index in range(2):
                card_index = game_index * 2 + round_index
                prompt, options = reviewed['cards'][card_index]
                advance_index = ord(reviewed['labels'][card_index]) - ord('A')
                steps.append({
                    'prompt': prompt,
                    'choices': [{'text': value, 'effect': 'advance' if i == advance_index else 'retry'} for i, value in enumerate(options)],
                    'hint': 'Знайди потрібний факт у тексті або порівняй форму зі зразком. Спробуй ще раз.' if mode == 'learn' else 'Зістав запитання з новим текстом. Для мовної форми згадай правило; не поспішай.',
                })
            if mode == 'learn':
                role = 'Ти — ' + reviewed['role'] + '.'
                goal = reviewed['goal']
                # The model is a learning resource, never answer commentary.
                stimulus = support + '\n\n' + reviewed['sources'][0] + '\n\nModel: ' + reviewed['model']
                production = {
                    'prompt': 'Обери одну фразу з моделей цієї місії, яка використовує слова або структуру з першого чи другого ходу. Зміни героя, предмет або час і напиши одну коротку англійську репліку. Можна вигадувати.',
                    'starter': '',
                }
            else:
                role = 'Ти перевіряєш дві заявки в новій ситуації.'
                goal = 'Прийми два обґрунтовані рішення за новим текстом. Спочатку обери самостійно, потім поясни одну підставу.'
                stimulus = reviewed['sources'][1]
                production = {
                    'prompt': 'До запиту «' + steps[0]['prompt'] + '» напиши англійською одну коротку підставу: факт із нового тексту або доречну мовну форму.',
                    'starter': 'My evidence is…',
                }
            missions.append({'id': mode, 'mode': mode, 'title': reviewed['titles'][game_index], 'role': role, 'goal': goal, 'source': stimulus, 'steps': steps, 'production': production})
        result['lessons'].append({'id': f'g6-{number:03d}', 'number': number, 'title': reviewed['titles'][0], 'slugs': public_slugs(lesson, authored, existing), 'games': missions})
    return result


def main():
    payload = export_payload()
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    pages = {p.parent.name for p in (ROOT / '6').glob('*/index.html')} - {'jolly-phonics'}
    mapped = {slug for lesson in payload['lessons'] for slug in lesson['slugs']}
    print(f'Grade6: {len(payload["lessons"])} calendar missions, 246 games, {len(mapped)}/{len(pages)} lesson pages; unmapped: {sorted(pages-mapped)}')


if __name__ == '__main__':
    main()
