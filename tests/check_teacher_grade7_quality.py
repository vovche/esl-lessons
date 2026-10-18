#!/usr/bin/env python3
"""Read-only methodological regression checks for every Grade 7 pack (stdlib)."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'teacher'/'7'
spec=importlib.util.spec_from_file_location('grade7_content',ROOT/'scripts'/'build_teacher_grade7.py')
g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
source=json.loads((BASE/'source-plan.json').read_text())['lessons']
review=json.loads((BASE/'quality-review.json').read_text())
assert review['grade']==7 and len(review['lessons'])==140

# Independently fixed curriculum regressions: wrong default tense must not return.
EXPECTED_GIDS={7:'present',10:'present',23:'past',26:'past_cont',38:'perfect',41:'perfect',52:'passive',55:'passive',64:'tags',65:'tags',71:'past_passive',74:'past_passive',80:'past_passive',89:'zero',92:'past_perfect',93:'past_perfect',98:'past_perfect',107:'degree',110:'comparison',115:'comparison',124:'determiners',127:'conjunctions',132:'conjunctions',136:'past_passive',139:'past_passive',140:'past_passive'}
# Answers are separately checked, not inferred from the generator's selected alternatives.
EXPECTED_FORMS={
'present':['reads','is making','does','is'],
'past':['swept','Did','wash','made'],
'past_cont':['was','were','was','Were'],
'perfect':['have','brought','has','finished'],
'passive':['are','held','are','by'],
'past_passive':['was','were','checked','was'],
'zero':['needs','ask','wait','asks'],
'past_perfect':['had','read','Had','forgotten'],
'degree':['quite','too','enough','very'],
'comparison':['than','as','less','as'],
'determiners':['Each','Both','some','any'],
'conjunctions':['and','or','because','but'],
'tags':['reads','is','doesn’t','do'],
}
# Specific topics previously replaced by a generic event/recipe must appear in pupil material.
TOPIC_FIXTURES={33:['utensil','respect'],34:['chopsticks','spoon'],37:['food artist','canvas'],43:['інгредієнти','посуду'],56:['Thanksgiving'],57:['Easter'],69:['Olympic','excellence','respect','friendship'],70:['Olympic','respect'],72:['Water polo'],75:['underwater hockey','puck'],77:['Klochkova','Olympic gold'],84:['responsible adult','diagnosis'],85:['Room 5'],95:['email','ліків'],105:['Royal Opera House','National Opera'],106:['1901','Viktor Shreter'],108:['Charlie Chaplin','City Lights'],119:['Northern Ireland'],120:['London'],123:['Kyiv','Golden Gate'],128:['River Castle'],129:['маршрут']}

for l,row in zip(source,review['lessons']):
 n=l['number'];folder=BASE/f'{n:03d}';p=g.profile(l)
 assert (row['number'],row['date'],row['topic'])==(n,l['date'],l['topic'])
 for f,expected in row['source_sha256'].items():
  assert hashlib.sha256((folder/f).read_bytes()).hexdigest()==expected,(n,'stale audit',f)
 lesson=(folder/'lesson.md').read_text();handout=(folder/'handout.md').read_text();key=(folder/'key.md').read_text();games=(folder/'games.md').read_text()
 assert l['topic'] in lesson and l['topic'] in handout
 assert 'Where does the story take place?' not in handout
 assert 'What item, activity or document is mentioned?' not in handout
 assert len(handout.split())<=650,(n,'main sheet overloaded')
 assert len(p['core'])<=3
 for label in ('r','a'):
  for qa in p[label]['qas']:
   assert qa['answer'].casefold() in p[label]['text'].casefold(),(n,label,'unsupported answer',qa)
   assert qa['evidence'].casefold() in p[label]['text'].casefold()
   assert qa['answer'] in key,(n,label,'missing key')
 # The actual G key section, rather than any incidental occurrence elsewhere.
 actual_g=re.search(r'## G · Форми\n\n(.*?)\n\n',key,re.S).group(1)
 actual_answers=[re.sub(r'^\d+\. |\.$','',line) for line in actual_g.splitlines()]
 assert actual_answers==[a for _,a in p['g']['items']],(n,'wrong G key')
 if n in EXPECTED_GIDS:assert p['gid']==EXPECTED_GIDS[n]
 if p['mode']=='grammar' or p['mode']=='portfolio':assert actual_answers==EXPECTED_FORMS[p['gid']]
 if p['mode']=='vocabulary':
  for en,_ in p['lex'][:4]:assert en.casefold() in p['model'].casefold(),(n,'model misses requested word',en)
 if n in TOPIC_FIXTURES:
  for word in TOPIC_FIXTURES[n]:assert word.casefold() in (handout+key).casefold(),(n,'wrong lesson topic',word)
 if n in (19,49,106,120):assert '## P · 3 короткі' in handout and '3. _____' in handout
 if p['mode']=='grammar':
  assert '## T ·' in handout and '## F ·' not in handout and '## P ·' not in handout
 if p['mode']=='reading':assert '## G ·' not in handout and '## V ·' not in handout and '## L ·' not in handout
 if p['mode']=='assessment':
  assert '## Модель' not in handout and '## Опора' not in handout
  for label in ('r','a'):
   reserve=g.alternate(p[label]);assert reserve['text']!=p[label]['text']
   for qa in reserve['qas']:assert qa['answer'].casefold() in reserve['text'].casefold()
  assert 'Резерв після переривання' in (folder/'recovery-handout.md').read_text()
 if l['kind']=='pair_diagnostic':
  assert p['r']['qas'][0]['answer'] in handout
  assert p['a']['qas'][0]['answer'] in handout  # in removable teacher transcript only
 # Each game has real language/content answers and a distinct parallel check card.
 first=g.simulation_cards(p);second=g.checking_cards(p)
 assert first!=second,(n,'game 2 only repeats game 1')
 for phase in (first,second):
  for c in phase:
   assert c['answer']!=c['wrong']
   assert c['answer'] in games and c['prompt'] in games
   if p['mode'] not in ('grammar','review','portfolio'):
    assert c['answer'].casefold() in c['source'].casefold()
 assert 'Окрема паралельна картка' in games
 assert 'після підказки' in games and 'не додається' in games
 assert 'камер' in games and 'переміщення' in games
 if p['mode']=='speaking':assert p['model'].count('A:')>=2 and p['model'].count('B:')>=2
 # Cross-unit reviews actually retain both taught grammar families.
 if p['mode']=='review' and p['u'] in (2,6,7,8) and n!=136:
  assert len(set(a for _,a in p['g']['items']))>=3

# Regression: both half-year reception checks use all four unit contexts.
for n,words in [(62,['school anniversary','dishwasher','ingredients','greeted']),(137,['coach','receptionist','subtitles','tour guide'])]:
 p=g.profile(source[n-1]);text=p['r']['text']+' '+p['a']['text']
 for word in words:assert word in text,(n,'semester coverage',word)
for n in (63,138):
 p=g.profile(source[n-1]);expected=re.sub(r'([А-Яа-яІіЇїЄєґҐ])([0-9])',r'\1 \2',p['s_task']);expected=re.sub(r'([0-9])([А-Яа-яІіЇїЄєґҐ])',r'\1 \2',expected);assert expected in (BASE/f'{n:03d}'/'handout.md').read_text()
print('PASS: all 140 Grade 7 lessons: source focus, supported R/L, exact G keys, requested model words, compact load, independent reserves and 280 simulation branches.')
# Plausible distractors: semantic category alone must not reveal the reading answer.
p37=g.profile(source[36]);learn=g.simulation_cards(p37);check=g.checking_cards(p37)
assert [(c['answer'],c['wrong']) for c in learn]==[('The plate','The table'),('sketches the design on paper','arranges the pieces on the plate')]
assert [(c['answer'],c['wrong']) for c in check]==[('a bird','a fish'),('Yellow','Blue')]
for l in source:
 p=g.profile(l)
 if p['mode']=='vocabulary':assert len(re.split(r'(?<=[.!?])\s+',p['model']))==4,(l['number'],'lexical model does not meet four-sentence instruction')
 for phase in ('learning','checking'):
  pos=g.answer_positions(p,phase)
  assert len(pos)==2 and all(x in ('A','B') for x in pos)
 if p['mode'] not in ('grammar','review','portfolio','vocabulary'):
  for c in g.simulation_cards(p)+g.checking_cards(p):
   assert c['wrong']==g.DISTRACTORS[c['answer'].casefold()]
 assert g.checking_cards(p)!=g.simulation_cards(p)
 # Generated positions and explicit check keys must agree for every date.
 text=(BASE/f"{l['number']:03d}"/'games.md').read_text()
 for i,(c,letter) in enumerate(zip(g.checking_cards(p),g.answer_positions(p,'checking')),1):
  assert f'квиток {i} — **{letter}: {c["answer"]}**' in text
for phase in ('learning','checking'):
 assert len({g.answer_positions(g.profile(l),phase) for l in source})==4
print('PASS: homogeneous distractors, four-sentence lexical models, distinct parallel game cards and all four balanced A/B position patterns.')

# The protagonist may be Alex; a simultaneous second chore must belong to somebody else.
for number in range(1,141):
 for offset in (0,1,2):
  text=g.context(2,number,offset)['text']
  assert 'while Ari washed up' in text
  assert not re.search(r'Yesterday (\w+) swept the floor while \1 washed up',text)
print('PASS: all household-story variants keep simultaneous actors distinct.')
