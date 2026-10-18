#!/usr/bin/env python3
"""Read-only learner export checks: source details, answer effects and page coverage."""
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]


def check():
    mod=runpy.run_path(str(ROOT/'scripts/export_grade9_simulations.py'))
    data=json.loads((ROOT/'9/simulations.json').read_text())
    assert data==mod['export'](),'Rebuild simulations.json after changing its exporter or content.'
    assert set(data)=={'version','grade','lessons'} and data['version']==1 and data['grade']==9
    assert len(data['lessons'])==121
    routes=set();positions=set()
    for n,l in enumerate(data['lessons'],1):
        assert set(l)=={'id','number','title','slugs','games'}
        assert l['number']==n and l['id']==f'g9-{n:03d}'
        assert l['slugs'] and len(l['slugs'])==len(set(l['slugs']))
        routes.update(l['slugs'])
        assert len(l['games'])==2
        c=mod['BUILD']['card'](mod['PLAN'][n-1])
        raw=[mod['questions'](c),mod['BUILD']['transfer_items'](c)]
        for ri,(g,mode) in enumerate(zip(l['games'],['learn','check'])):
            assert set(g)=={'id','mode','title','role','goal','source','steps','production','reflection'}
            assert g['id']==g['mode']==mode
            assert set(g['reflection'])=={'focus','prompt'}
            assert g['reflection']['focus'] and 'За бажанням' in g['reflection']['prompt']
            assert 'пропустити' in g['reflection']['prompt'] and 'балів' in g['reflection']['prompt']
            assert 'How do you feel' not in g['reflection']['prompt']
            assert 'Оціни' not in g['reflection']['prompt']
            if mode=='check' and c['type'] in ('reading','listening','assessment','starter'):
                assert mod['tidy'](raw[ri][0]['prompt']) in g['reflection']['prompt'],(n,'reflection points to another round')
            assert len(g['steps'])==2 and g['source'] and g['production']['prompt']
            for si,step in enumerate(g['steps']):
                assert set(step)=={'prompt','choices','hint'}
                assert step['hint'] and len(step['choices'])==2
                assert all(set(o)=={'text','effect'} for o in step['choices'])
                assert {o['effect'] for o in step['choices']}=={'advance','retry'}
                good=[o['text'] for o in step['choices'] if o['effect']=='advance']
                assert good==[mod['tidy'](raw[ri][si]['answer'])],(n,mode,'incorrect effect')
                assert len({o['text'] for o in step['choices']})==2
                positions.add(next(i for i,o in enumerate(step['choices']) if o['effect']=='advance'))
            copy=' '.join(g[k] for k in ['title','role','goal','source'])+' '+json.dumps(g['production'],ensure_ascii=False)
            for forbidden in ['Teacher-only','teacher-only','SHA-256','quality-review','report.md','key.md','2026-','2027-','не перевірено','підсумков','семестров']:
                assert forbidden.lower() not in copy.lower(),(n,forbidden)
            if c['type']=='listening':
                assert 'слухання' not in g['title'].lower()
                assert g['source']==mod['tidy'](c['transcript'])
    assert positions=={0,1},'Do not always put the correct option first.'
    pages={p.parent.name for p in (ROOT/'9').glob('*/index.html')}
    assert routes==pages and len(routes)==114,(pages-routes,routes-pages)
    def lesson(n):return data['lessons'][n-1]
    def answer(n,game,step):return next(x['text'] for x in lesson(n)['games'][game]['steps'][step]['choices'] if x['effect']=='advance')
    # Anchors for previously observed content and routing defects.
    assert answer(39,0,0)=='50%' and answer(39,1,0)=='30%'
    assert answer(69,0,0)=='Experience'
    assert 'Interests'==answer(69,1,0)
    assert answer(84,0,0)=='Shared Nobel Prize in Physics'
    assert '1911' in answer(84,1,0)
    assert answer(47,1,0)=='the science series'
    assert answer(47,1,1)=='the sports programme'
    assert answer(117,0,0)=='fifteen minutes'
    assert 'fifteen minutes' in lesson(117)['games'][0]['source']
    assert 'twenty minutes' not in lesson(117)['games'][0]['source']
    assert 'future-forms' in lesson(9)['slugs'] and 'future-forms-v2' in lesson(9)['slugs']
    assert 'gerund' in lesson(20)['slugs'] and 'fashion-grammar' in lesson(23)['slugs']
    assert lesson(121)['slugs']==['sb-u5-writing']
    assert 'sb-wordlist' in lesson(104)['slugs']
    # Teaching rules and bilingual vocabulary banks must not reveal first-attempt check answers.
    for l in data['lessons']:
        c=mod['BUILD']['card'](mod['PLAN'][l['number']-1])
        if c['type'] in ('grammar','lexis','recap','portfolio') and c['n']!=121:
            assert l['games'][0]['source']!=l['games'][1]['source']
            assert l['games'][1]['source']==mod['tidy'](mod['material'](c,'check'))
    assert 'enjoy/avoid' not in lesson(23)['games'][1]['source']
    assert '-ing' not in lesson(20)['games'][1]['source']
    assert 'avoid' not in lesson(20)['games'][1]['source']
    assert 'curious —' not in lesson(4)['games'][1]['source']
    # Fact-based reading check cards still include their source facts.
    assert 'science series' in lesson(47)['games'][1]['source']

    # A check round must introduce unused source details, not paraphrase a learned answer.
    assert answer(1,1,0)=='ask questions'
    assert answer(24,1,0)=='only dark clothes'
    assert answer(24,1,1)=='items she will wear just once'
    assert answer(43,1,0)=='They are not always accurate.'
    assert answer(59,1,0)=='interests and skills'
    assert answer(68,1,0)=='education'
    assert answer(73,1,0)=='work and learn'
    assert answer(83,1,0)=='the battery'
    assert answer(94,1,1)=='a reusable bottle'
    assert answer(102,1,1)=='directions'
    assert answer(111,1,1)=='an e-mail'
    # Check the entire payload, including steps/hints, for unintended private/service metadata.
    all_copy=json.dumps(data,ensure_ascii=False).lower()
    for forbidden in ['meet.google.com','school.mriia.gov.ua','/home/why/','event_uid','journal_attachment','teacher-only','source_sha256']:
        assert forbidden not in all_copy,forbidden

    print('Grade9 learner simulations:121 missions,242 games,484 answer effects and114 public-page mappings checked.')

if __name__=='__main__':check()
