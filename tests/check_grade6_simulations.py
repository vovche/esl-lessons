#!/usr/bin/env python3
"""Read-only checks for the student export and its reviewed mission semantics."""
from pathlib import Path
import importlib.util
import json
import re

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('grade6_simulation_export',ROOT/'scripts/export_grade6_simulations.py')
exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
payload=json.loads((ROOT/'6/simulations.json').read_text())
source=json.loads((ROOT/'teacher/6/source-plan.json').read_text())
assert set(payload)=={'version','grade','lessons'}
assert payload['version']==1 and payload['grade']==6
assert payload==exporter.export_payload(),'Student payload is stale or nondeterministic'
assert len(payload['lessons'])==123
existing={p.parent.name for p in (ROOT/'6').glob('*/index.html')}
mapped=set();positions=set()
for public,planned in zip(payload['lessons'],source['lessons']):
    number=planned['number']
    assert set(public)=={'id','number','title','slugs','games'}
    assert public['id']==f'g6-{number:03d}' and public['number']==number
    assert public['title'] and public['slugs']
    assert set(public['slugs'])<=existing
    mapped.update(public['slugs'])
    reviewed=exporter.reviewed_mission_data(planned)
    assert len(public['games'])==2
    for game_index,(game,mode) in enumerate(zip(public['games'],('learn','check'))):
        assert set(game)=={'id','mode','title','role','goal','source','steps','production'}
        assert game['id']==game['mode']==mode
        assert all(game[field] for field in ('title','role','goal','source'))
        assert game['title']==reviewed['titles'][game_index]
        if mode=='learn':
            assert game['source'].endswith(reviewed['sources'][0]+'\n\nModel: '+reviewed['model'])
            assert 'Words:' in game['source']
            assert game['goal']==reviewed['goal']
            assert 'першого чи другого ходу' in game['production']['prompt']
        else:
            assert game['source']==reviewed['sources'][1]
            assert 'Model:' not in game['source']
            assert 'Підстава:' not in game['source']
            assert game['steps'][0]['prompt'] in game['production']['prompt']
        assert len(game['steps'])==2
        for step_index,step in enumerate(game['steps']):
            card_index=game_index*2+step_index
            prompt,choices=reviewed['cards'][card_index]
            assert set(step)=={'prompt','choices','hint'}
            assert step['prompt']==prompt
            assert [c['text'] for c in step['choices']]==choices
            assert len(step['choices'])==3
            for choice in step['choices']:
                assert set(choice)=={'text','effect'}
                assert choice['effect'] in ('advance','retry')
            advancing=[i for i,c in enumerate(step['choices']) if c['effect']=='advance']
            expected=ord(reviewed['labels'][card_index])-ord('A')
            assert advancing==[expected],(number,mode,step_index,'incorrect transition')
            positions.add(expected)
            assert step['hint'] and 'Правильний' not in step['hint']
        assert set(game['production'])=={'prompt','starter'}
        assert game['production']['prompt']
by_number={lesson['number']:lesson for lesson in payload['lessons']}
assert by_number[120]['slugs']==['sb-grammar','sb-round-up-7','sb-round-up-8']
assert 'we/you/they → were' in by_number[29]['games'][0]['source']
assert 'us' in by_number[21]['games'][0]['source']
assert 'me, him, her, us, them' in by_number[21]['games'][0]['source']
assert 'Words:' in by_number[58]['games'][0]['source']
assert 'printer —' in by_number[58]['games'][0]['source']
assert 'School — Park — Library' in by_number[44]['games'][0]['source']
assert 'A = 3; B = 5; C = 8' in by_number[48]['games'][0]['source']
assert 'The customer has 12 pounds' in by_number[94]['games'][0]['source']
assert 'в календарі' not in json.dumps(payload,ensure_ascii=False)
assert mapped==existing-{'jolly-phonics'},('Unmapped public pages',sorted(existing-{'jolly-phonics'}-mapped))
assert positions=={0,1,2},'Correct choice position is predictable'
# Allow ordinary fictional teachers in an English reading; exclude teacher-only
# scaffolding, reports, hashes, formal-assessment prompts and private metadata.
encoded=json.dumps(payload,ensure_ascii=False)
for token in ('Відповіді для вчителя','Ключ для вчителя','Робочий запис:','Підстава:','Рубрика','report.md','teacher.pdf','source_sha256','sha256','provenance','recovery-handout','Планова дата:','Перевірка розуміння на слух за','Teacher-only','учитель не називає'):
    assert token not in encoded,('Teacher-only leak',token)
assert not re.search(r'\b202[67]-\d\d-\d\d\b',encoded)
print('Grade6 student simulations:123/123 dates,246 games,492 exact reviewed transitions,67/67 pages,student-only schema OK.')
