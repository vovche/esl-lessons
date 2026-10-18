#!/usr/bin/env python3
"""Read-only schema, semantics, mapping and privacy checks for learner missions."""
import importlib.util
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('export_grade7',ROOT/'scripts/export_grade7_simulations.py')
exporter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)
actual=json.loads((ROOT/'7/simulations.json').read_text())
assert actual==exporter.export_data(), 'simulation export is stale'
content=exporter.load_content()
calendar=json.loads((ROOT/'teacher/7/source-plan.json').read_text())['lessons']
assert set(actual)=={'version','grade','lessons'}
assert actual['version']==1 and actual['grade']==7 and len(actual['lessons'])==140
available={p.parent.name for p in (ROOT/'7').glob('*/index.html')}
covered=set()
patterns=set()
for record,original in zip(actual['lessons'],calendar):
 n=original['number'];p=content['profile'](original)
 assert set(record)=={'id','number','title','slugs','games'}
 assert record['id']==f'g7-{n:03d}' and record['number']==n
 assert record['title'] and record['slugs']
 assert len(record['slugs'])==len(set(record['slugs']))
 assert set(record['slugs'])<=available
 covered.update(record['slugs'])
 assert [x['id'] for x in record['games']]==['learn','check']
 for game in record['games']:
  assert set(game)=={'id','mode','title','role','goal','source','steps','production'}
  phase=game['mode'];assert phase==game['id'] and phase in ('learn','check')
  cards=content['simulation_cards' if phase=='learn' else 'checking_cards'](p)
  assert len(game['steps'])==2
  pattern=[]
  for step,card in zip(game['steps'],cards):
   assert set(step)=={'prompt','choices','hint'}
   assert step['prompt']==card['prompt']
   assert len(step['choices'])==2
   assert all(set(c)=={'text','effect'} for c in step['choices'])
   correct=[c for c in step['choices'] if c['effect']=='advance']
   wrong=[c for c in step['choices'] if c['effect']=='retry']
   assert len(correct)==len(wrong)==1
   assert correct[0]['text']==card['answer']
   assert wrong[0]['text']==card['wrong']
   assert correct[0]['text']!=wrong[0]['text']
   pattern.append(next(i for i,c in enumerate(step['choices']) if c['effect']=='advance'))
   assert step['hint'] and 'advance' not in step['hint']
   if p['mode'] not in ('grammar','review','portfolio','vocabulary'):
    assert game['source']
    assert correct[0]['text'].casefold() in game['source'].casefold(),(n,'unsupported public answer')
  patterns.add(tuple(pattern))
  assert game['production']['prompt'] and set(game['production'])=={'prompt','starter'}
  if p['mode'] in ('grammar','review','portfolio','vocabulary') and phase=='check':
   assert game['source']=='', 'recall check must not display grammar rule/dictionary'
  if p['mode']=='listening':
   assert 'Прочитай' in game['goal']
  # Calendar dates, private platforms, audit fields and teacher-only prose cannot leak.
  text=json.dumps(game,ensure_ascii=False)
  assert not re.search(r'\b20\d{2}-\d{2}-\d{2}\b|meet\.google|school\.mriia|Teacher.only|SHA-?256|source_sha256|journal_|report\.md|key\.md|teacher/|рубри[кц]|похвилин|за розкладом',text,re.I),(n,'service content leak')
 assert record['games'][0]['steps']!=record['games'][1]['steps']
assert covered==available and len(covered)==109
assert len(patterns)==4,'choices must not use a fixed answer-position pattern'

# Concrete curriculum regressions: public missions retain the actual tested material.
def lesson(n):return actual['lessons'][n-1]
def all_text(n):return json.dumps(lesson(n),ensure_ascii=False)
for n,words in {33:['utensil','respect'],37:['food artist','canvas','bird','fish','Yellow','Blue'],69:['excellence','respect','friendship'],72:['Water polo'],75:['Underwater hockey','puck'],77:['swimming','four','five'],105:['Covent Garden','1901'],106:['National Opera','Viktor Shreter'],108:['Chaplin','City Lights','1889'],121:['Kingston','Suva','Wellington','Dublin']}.items():
 for word in words:assert word.casefold() in all_text(n).casefold(),(n,word)
for n,slug in {7:'now-or-usually',10:'ask-about-school',20:'chores',23:'past-simple-questions',26:'past-continuous-questions',27:'sharing-chores',28:'home-stories'}.items():
 assert slug in lesson(n)['slugs']
assert 'sb-u1-lead-in' in lesson(2)['slugs']
assert 'sb-u8-lead-in' in lesson(119)['slugs']
for n in (32,61,101,135):assert any('self-check' in s for s in lesson(n)['slugs'])
for n in (64,65):
 assert 'question tags' in lesson(n)['title']
 assert 'sb-grammar' in lesson(n)['slugs']
 assert 'sb-u4-self-check' not in lesson(n)['slugs'],'tags must not be mapped to passive-only unit'
# Known teaching models are not pasted into titles/goals as ready answer keys.
for record in actual['lessons']:
 for game in record['games']:
  for field in ('title','role','goal'):
   assert not re.search(r'\b[1-4]\.\s*(?:reads|was|are|had)\b',game[field])
print('PASS: 140 learner lessons / 280 missions / 560 keyed steps; independent parallel cards, all 109 existing pages, precise legacy mapping, no service data and no listening claim for reading.')
