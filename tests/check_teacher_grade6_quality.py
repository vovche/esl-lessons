#!/usr/bin/env python3
"""Read-only regression checks for concrete grade-6 editorial failures."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'teacher/6'
spec=importlib.util.spec_from_file_location('grade6_teacher',ROOT/'scripts/build_teacher_grade6.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
source=json.loads((BASE/'source-plan.json').read_text())
ads=g.curate_adaptations({a['slug']:a for a in source['adaptations']})

# Independent expected keys, checked against source/model meaning during the audit.
EXPECTED={
'1a':['studies','Do','does not','In the theatre.','The writer likes learning about animals.'],
'1b':['is reading','are standing','is','Brown.','Near a tree.'],
'1c':['wears','are making','like','A skirt.','To cover the drawing.'],
'1d':['playing','to join','to leave','Arts and crafts.','At ten.'],
'1e':['She has got straight hair.','What are you like?','He is a helpful boy.','The friend is clever and helpful.','Play ice hockey.'],
'2a':['went','take','did not','The camel was tall.','Her camera was at home.'],
'2b':['carefully','could not','well','The traffic was slow.','No, it was closed.'],
'2c':['us','him','me','They checked the weather.','Download them.'],
'2d':['used to','use to','use to','Land.','Places to charge them.'],
'2e':['because','so','but','By coach.','The experiment room.'],
'3a':['was walking','were playing','Was','A ball rolled under the table.','A teacher.'],
'3b':['were walking','rang','was listening to','They were much bigger than human footprints.','To the campsite.'],
'3c':['any','some','any','A sandwich.','No, there were none.'],
'3d':['Nobody','anything','is','Nobody is at the gate.','Relieved.'],
'3e':['Unfortunately','closed','In the end, we got home safely.','His keys were inside.','His aunt.'],
'4a':['May','open','might','He has no library card with him.','On a shelf.'],
'4b':['into it','opposite','Turn left at the traffic lights.','In front of a supermarket.','Behind the supermarket.'],
'4c':['quieter','comfortable','better','It is quieter and more peaceful.','Travel with their home.'],
'4d':['the largest','hottest','the most','Eight.','The biggest.'],
'4e':['are','is','I think this city is beautiful.','In the park.','The view from the old bridge.'],
'5a':['is','buy','are','A keyboard.','At the entrance.'],
'5b':['will','will','help','They sometimes fail with a computer.','Visit an electronics shop.'],
'5c':['must not','do not have to','had to','Plastic.','A leaflet.'],
'5d':['pollute','will have','pick','To breathe.','Fishing nets.'],
'5e':['Would you like to come to our event?','I would love to come.','The place and time.','At eight.','A reply.'],
'6a':['many','little','few','Protein and calcium.','Water.'],
'6b':['tell','should not','Should','In the school library.','Ask the teacher for help.'],
'6c':["isn't she","don't you",'can they','The friend who prefers aerobics.','Choosing an enjoyable activity.'],
'6d':['won','spectator','play','Yes, in different sports.','Where the team plays and why you support it.'],
'6e':['joined','practise','play','Three times a week.','Take part in a tournament.'],
'7a':['seen','has','Have you ever appeared on TV?','Five.','One boy answered too quickly and made mistakes.'],
'7b':['saw','gone','yet','Last summer.','Nervous.'],
'7c':['for','since','have','To type faster.','Who took it and when it will be returned.'],
'7d':['too','enough','ones','It is too big.','Their receipts.'],
'7e':['hers','my','Mia’s notebook','The student has exams.','Show the brother how to study independently.'],
'8a':['who','which','Mia, who won a prize, is my friend.','At a supermarket.','Share it with a friend.'],
'8b':['So','can','did','The audition could lead to a TV appearance.','Do their best and have fun.'],
'8c':['is','delivered','Articles are written by reporters.','Graphic designers.','It is checked.'],
'8d':['was','were','filmed','The best project.','Two.'],
'8e':['plot','It was directed by an artist.','who','Museum exhibits come to life.','The soundtrack.']}
EXPECTED.update({
'culture-1':['double-decker','boats.','Cable cars travel along streets.','Canals.','Three.'],
'song-1':['wake','chorus','explore','Skateboarding.','Plays a skateboard game.'],
'culture-2':['bagpipes.','People believe…','clothing','Lakes.','A monster legend.'],
'song-2':['woke','was walking','Later.','They missed the bus.','An unlucky day.'],
'culture-3':['Both parks have trees.','walk','busy cities','Nature.','Yes.'],
'song-3':['think','will help','extinct',"The planet's future.",'Saving water.'],
'culture-4':['composer','written','I liked the costumes because they were colourful.','In an opera house.','Music, costumes and scenery.'],
'song-4':['won','go','fans','Going on tour.','Pride and excitement.'],
'culture-ukraine-1':['little','many','Many families often…','Beetroot.','Yes.'],
'culture-ukraine-2':['visit','like','square','History.','Activities and sights.'],
'clil-history':['began','saw','the way people travel.','Dogs.','A flag.'],
'clil-geography':['the biggest city.','a year.','has','Short facts about a country.','No.'],
'clil-sport':['played','puck','follow','Referees.','For protection.'],
'clil-music':['percussion','strings','bow','By blowing into them.','A way of being played.'],
'learning-tips':['plan','draft','a source.','History, equipment and rules.','Checks and improves the work.']})
for code,expected in EXPECTED.items():
    a=ads['sb-'+code]
    actual=[q['choices'][q['answer']] for q in a['questions']]
    assert actual==expected,(code,actual,expected)

# The old recap used first-sentence summaries but asked for omitted facts.
for unit in range(1,9):
    recap=ads[f'sb-round-up-{unit}']
    assert len(recap['reading'].split())<90
    assert recap['questions']==[ads[f'sb-{unit}{c}']['questions'][0] for c in 'abcde']
    assert 'Повтори п’ять мовних фокусів' in recap['rule']
    assert len(recap['example'].split())<65
assert ads['sb-1c']['title']=='Clothes and fashion'
assert 'cheaper than' not in g.SAMPLES['2b'] and 'slowly' in g.SAMPLES['2b']
assert 'zoo' not in ' '.join(q['prompt'] for q in ads['sb-culture-3']['questions'])
assert 'busy cities' in ads['sb-culture-3']['reading']
assert 'What was one film chosen as?'==ads['sb-8d']['questions'][3]['prompt']
assert 'does not have to be the largest city' in ads['sb-clil-geography']['reading']
assert 'has got a headache' in ads['sb-6b']['reading']
assert 'admits' not in ads['sb-6b']['reading']
assert 'climbed a ladder' not in ads['sb-3e']['reading']
assert 'not a quotation' in ads['sb-3d']['reading']
assert 'hers' in ads['sb-7e']['example'] and 'Mia’s' in ads['sb-7e']['example']
assert 'who won a prize,' in ads['sb-8a']['rule']

active_stimuli={'L':set(),'R':set(),'S':set(),'W':set()}
assessment_count=0
for l in source['lessons']:
    number=l['number'];folder=BASE/f'{number:03d}'
    assert l['topic'] in (folder/'lesson.md').read_text()
    hand=(folder/'handout.md').read_text();key=(folder/'key.md').read_text();lesson=(folder/'lesson.md').read_text();games=(folder/'games.md').read_text()
    formal=l['lesson_type'] in ('pair_diagnostic','semester_check')
    if formal:
        assessment_count+=1
        skills=['L','R','S','W'] if l['lesson_type']=='pair_diagnostic' else [l['section'].split('-')[-1]]
        p=g.assessment_data(l);r=g.assessment_data(l,True)
        reserve=(folder/'recovery-handout.md').read_text()
        for skill in skills:
            field={'L':'listen','R':'read','S':'speaking','W':'writing'}[skill]
            assert p[field]!=r[field],(number,'same primary/reserve',skill)
            for d in (p,r):
                assert d[field] not in active_stimuli[skill],(number,'reused stimulus',skill)
                active_stimuli[skill].add(d[field])
        if 'L' in skills:
            assert p['listen'] not in hand and r['listen'] not in reserve
            assert p['listen'] in key and r['listen'] in key
        for d in (p,r):
            for kind in ('lq','rq'):
                assert len(d[kind])==6
                for question,options,answer in d[kind]:
                    assert len(options)==3 and len(set(options))==3,(number,question,options)
                    assert answer==0
        assert 'Резервний варіант' in key
        assert 'recovery-handout.md' in lesson
        if number==28:assert 'going to' not in p['listen']+r['listen']
        assert 'Їх не запускають перед / під час' in games
    else:
        aa=g.choose(l,ads);assert aa,(number,'no curricular adaptation')
        # The rendered answer letters must correspond to the displayed shuffled choices.
        for index,a in enumerate(aa,1):
            block,bkey=g.block(a,index,l)
            assert block in hand and bkey in key
            assert not any(q['why'] in block for q in a['questions'] if len(q['why'])>90)
        if len(aa)>1:assert 'окремого письмового твору не потрібно' in hand
        if l['lesson_type']=='language_and_production':assert aa[0]['write']['prompt'] in hand
        if l['lesson_type']=='module_intro':
            assert 'Обери переклад:' in hand
            assert 'нова граматична форма' not in hand.lower() or 'ще не потрібно' in hand
        if l['lesson_type']=='unit_recap':assert hand.index('Опора після спроби:')>hand.index('5. ')
    # New game2 cards must differ from practiced worksheet cards, not just shuffled options.
    check_section=games.split('## 2. Перевірка')[1]
    assert 'Окремий паралельний контекст' in check_section
    assert 'із підтримкою' in games and 'не переписують первинний результат' in games
    assert 'Допустимий приклад зі зміненою деталлю:' in games
    assert 'вправа3 аркуша' in check_section
    assert games.count('Картка ходу')==2
    assert 'Заявка1:' in games and 'Заявка2:' in games
    answer_positions=re.findall(r'(?:хід1|Хід2|заявка1|Заявка2) — ([ABC]) —',games)
    assert len(answer_positions)==4 and len(set(answer_positions))==3,(number,'predictable game keys')
    if not formal:
        assert 'замість звичайної практики' in games
    # Authentic amount of work, not a second mandatory text for every extra source.
    assert 'камер' in lesson and 'під час переміщення' in lesson.lower()
assert assessment_count==12

review=json.loads((BASE/'quality-review.json').read_text())
assert review['grade']==6 and len(review['lessons'])==123
for l in review['lessons']:
    for name,expected in l['source_sha256'].items():
        assert hashlib.sha256((BASE/f'{l["number"]:03d}'/name).read_bytes()).hexdigest()==expected,(l['number'],name,'stale review')
print('Grade6 quality: 123 dates; 275 core/culture/process closed answers; 8 complete recaps; 12 distinct primary/reserve assessments; 246 thematic simulations; audit hashes OK.')
