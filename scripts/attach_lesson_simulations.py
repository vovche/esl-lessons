"""Attach the student simulation player without publishing teacher documents."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- lesson-simulations:start -->'
END = '<!-- lesson-simulations:end -->'


def attach(html: str, grade: int, slug: str) -> str:
    html = re.sub(re.escape(START)+r'.*?'+re.escape(END)+r'\n?', '', html, flags=re.S)
    section = f'''{START}
<section id="lesson-simulations" class="lesson-simulations" data-lesson-simulations data-sim-grade="{grade}" data-sim-slug="{escape(slug, quote=True)}" data-dictionary-skip aria-labelledby="lesson-simulations-title">
<h2 id="lesson-simulations-title">Ігрові місії</h2>
<p>Обери ситуацію, прийми два рішення та додай власну англійську репліку. Можна зробити паузу й повернутися пізніше.</p>
<button type="button" class="sim-button" data-sim-load>Відкрити місії</button>
<div data-sim-host></div>
<noscript><p>Щоб пройти інтерактивну місію, увімкни JavaScript. Матеріал уроку вище залишається доступним.</p></noscript>
</section>
{END}'''
    if '../../assets/lesson-theme.css' not in html:
        html = html.replace('</head>', '<link rel="stylesheet" href="../../assets/lesson-theme.css">\n</head>', 1)
    for tag in ('<link rel="stylesheet" href="../../assets/lesson-simulations.css">',
                '<script src="../../assets/lesson-simulations.js" defer></script>'):
        if tag not in html:
            html = html.replace('</head>', tag+'\n</head>', 1)
    if '</main>' in html:
        return html.replace('</main>', section+'\n</main>', 1)
    if '<footer' in html:
        index = html.index('<footer')
        return html[:index]+section+'\n'+html[index:]
    return html.replace('</body>', section+'\n</body>', 1)


def apply_grade(grade: int) -> int:
    folder = ROOT/str(grade)
    data = json.loads((folder/'simulations.json').read_text())
    slugs = sorted({slug for lesson in data['lessons'] for slug in lesson['slugs']})
    for slug in slugs:
        path = folder/slug/'index.html'
        if not path.is_file():
            raise ValueError(f'Missing student lesson: {path}')
        html = path.read_text()
        result = attach(html, grade, slug)
        if result != html:
            path.write_text(result)
    print(f'Grade {grade}: simulation player attached to {len(slugs)} lesson pages')
    return len(slugs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grade', type=int, choices=[6, 7, 9], action='append')
    args = parser.parse_args()
    for grade in args.grade or [6, 7, 9]:
        apply_grade(grade)
