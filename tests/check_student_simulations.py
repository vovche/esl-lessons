"""Verify complete route coverage and repeatable integration without private UI."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from attach_lesson_simulations import attach, START, END
for grade, count, pages in ((6,123,67),(7,140,109),(9,121,114)):
    data=json.loads((ROOT/str(grade)/'simulations.json').read_text())
    assert len(data['lessons'])==count
    slugs={slug for item in data['lessons'] for slug in item['slugs']}
    assert len(slugs)==pages
    for slug in slugs:
        path=ROOT/str(grade)/slug/'index.html'; html=path.read_text()
        assert html.count(START)==html.count(END)==1,path
        assert attach(html,grade,slug)==html, f'Non-idempotent integration: {path}'
        section=html.split(START)[1].split(END)[0]
        assert 'data-dictionary-skip' in section
        assert 'teacher/' not in section and 'key.pdf' not in section
        for asset in ('lesson-simulations.js','lesson-simulations.css'):
            assert html.count('../../assets/'+asset)==1,path
    print(f'PASS grade {grade}: {count} calendar lessons, {pages} integrated pages')
