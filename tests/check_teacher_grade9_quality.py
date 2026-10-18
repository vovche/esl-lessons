#!/usr/bin/env python3
"""Read-only regression checks for the revised grade 9 teaching packs (stdlib)."""
import hashlib
import json
from pathlib import Path
import re
import runpy

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'teacher/9'


def check():
    module=runpy.run_path(str(ROOT/'scripts/build_teacher_grade9.py'))
    source=json.loads((BASE/'source-plan.json').read_text())
    manifest=json.loads((BASE/'manifest.json').read_text())
    review=json.loads((BASE/'quality-review.json').read_text())
    assert review['grade']==9
    assert len(source['lessons'])==len(manifest['lessons'])==len(review['lessons'])==121
    grammar={6,9,20,23,34,37,48,51,64,67,78,79,82,93,96,107,110}
    lexical={4,8,17,22,31,36,45,50,61,66,75,81,90,95,104,109}
    genres={11:'мініавтобіографія',25:'абзац думки',39:'survey report',53:'vlog review',69:'CV',84:'biography chart',98:'листівка',112:'e-mail'}
    for n,(l,m,r) in enumerate(zip(source['lessons'],manifest['lessons'],review['lessons']),1):
        for key in ['number','date','topic']:
            assert l[key]==m[key]==r[key],(n,'calendar identity',key)
        assert n==l['number']
        p=BASE/f'{n:03d}'
        texts={name:(p/name).read_text() for name in ['lesson.md','handout.md','key.md','games.md','report.md']}
        for name,expected in r['source_sha256'].items():
            assert hashlib.sha256((p/name).read_bytes()).hexdigest()==expected,(n,'stale audit',name)
        c=module['card'](l)
        assert r['sel_nush_review']['reflection_scored'] is False
        assert r['sel_nush_review']['action'] and r['sel_nush_review']['reflection']
        assert 'перший випуск' in texts['lesson.md'] and '2026/2027' in texts['lesson.md']
        assert 'не сертифікована' in texts['lesson.md']
        assert 'чотирьох сил' in texts['lesson.md']
        assert 'SEL-рефлексія не оцінюється' in texts['key.md']
        assert '41–43' in texts['lesson.md'] and '43–45' in texts['lesson.md']
        assert 'SEL-дія' in texts['games.md']

        assert r['main_question_count']<=7
        assert r['scheduled_main_passages']==1 and r['production_minutes']==12
        if n in lexical: assert c['type']=='lexis' and len(c['questions'])==3
        if n in grammar: assert c['type']=='grammar'
        if n in genres: assert genres[n] in c['genre']
        assert len(module['transfer_items'](c))==2
        for q in c['questions']:
            assert q['answer'] not in q['wrong'] and len(set(q['wrong']))==len(q['wrong']),(n,q)
            assert q['answer'] in texts['key.md'],(n,'missing key',q['answer'])
            assert q['why'] and len(q['why'])>10
        for mode,total in [('A',45),('B',15),('C',45),('D',15)]:
            rows=module['schedules'](c)[mode]
            cursor=0
            for timerange,_,_ in rows:
                start,end=map(int,timerange.split('–'))
                assert start==cursor and end>start,(n,mode,timerange)
                cursor=end
            assert cursor==total
        minimum=texts['handout.md'].split('## Мінімум B/D:')[1].split('## Основний маршрут')[0]
        assert re.search('[A-Za-z]{3,}',minimum),(n,'no English recovery support')
        assert 'для CV' not in minimum and 'для chart' not in minimum,(n,'unrelated recovery genres')
        assert 'Майстерня рішення' in texts['games.md']
        assert texts['games.md'].count('Новий стимул')==2
        assert 'замість' in texts['games.md'].lower() and 'першої' in texts['games.md']
        for forbidden in ['meet.google.com','school.mriia.gov.ua','event_uid','journal_attachment_paths']:
            assert all(forbidden not in t for t in texts.values()),(n,forbidden)
        if c['type']=='listening':
            assert c['transcript'] not in texts['handout.md'],(n,'transcript leak')
            assert c['transcript'] in texts['key.md']
        if c['type']=='assessment':
            assert 'fifteen minutes' in texts['key.md']
            assert c['transcript'] not in texts['handout.md']
    # The L/S-only date must not leave unanswerable reading items or reserve keys.
    ls=(BASE/'117/handout.md').read_text()
    assert 'Цільові пункти' not in ls and 'twenty minutes' not in ls
    assert 'Which source must' not in ls
    assert 'Закриті цільові відповіді' not in (BASE/'117/key.md').read_text()
    r117=review['lessons'][116]
    assert r117['closed_items']==[] and r117['main_question_count']==0
    # New round-two details must discriminate source content, not universal absurdities.
    for l in source['lessons']:
        c=module['card'](l)
        assert r['sel_nush_review']['reflection_scored'] is False
        assert r['sel_nush_review']['action'] and r['sel_nush_review']['reflection']
        assert 'перший випуск' in texts['lesson.md'] and '2026/2027' in texts['lesson.md']
        assert 'не сертифікована' in texts['lesson.md']
        assert 'чотирьох сил' in texts['lesson.md']
        assert 'SEL-рефлексія не оцінюється' in texts['key.md']
        assert '41–43' in texts['lesson.md'] and '43–45' in texts['lesson.md']
        assert 'SEL-дія' in texts['games.md']

        for q in module['transfer_items'](c):
            assert not any(x in ' '.join(q['wrong']) for x in ['everyone must make exactly the same choice','no alternative can ever work'])
    game47=(BASE/'047/games.md').read_text()
    assert 'Which programme explains experiments?' in game47
    assert 'Which programme reviews matches?' in game47
    assert 'the sports programme' in game47 and 'the comedy' in game47
    # First answers alternate by date/round; changing positions must not change textual keys.
    g46=(BASE/'046/games.md').read_text()
    g47=(BASE/'047/games.md').read_text()
    assert 'Choices: the comedy / the science series' in g46 or 'Choices: the comedy / the science series' in g47
    assert 'Choices: the science series / the comedy' in g46 or 'Choices: the science series / the comedy' in g47
    assert 'Ключ після першої спроби: **the science series**' in g46
    cvmodel=module['card'](source['lessons'][68])['sample']
    for label in ['Education:','Skills:','Experience:','Interests:']:
        assert '\n\n'+label in cvmodel
    survey=(BASE/'039/handout.md').read_text()
    assert 'Survey: 20 students; 10 sport, 6 music, 4 film' in survey
    assert '2 of 10 students = 20%' in survey
    # These round-two facts used to repeat the learned question verbatim or semantically.
    for n,expected in [(24,'only dark clothes'),(83,'the battery'),(94,'a reusable bottle')]:
        c=module['card'](source['lessons'][n-1])
        check_answers=[q['answer'] for q in module['transfer_items'](c)]
        assert expected in check_answers

    # Independent regression anchors for material defects, not only metadata.
    assert '30%' in (BASE/'039/games.md').read_text()
    assert '50%' in (BASE/'039/key.md').read_text()
    cv=(BASE/'069/handout.md').read_text()
    assert 'helped organise a school book stall' in cv and 'Experience' in cv
    assert 'classmates’ contacts' not in cv
    cvgame=(BASE/'069/games.md').read_text()
    assert 'Interests' in cvgame and 'Arranged books by topic' in cvgame
    assert 'survey39' not in cvgame and 'chart84' not in cvgame
    assert '1911' in (BASE/'084/key.md').read_text() and '1903' in (BASE/'084/games.md').read_text()
    report=(BASE/'051/handout.md').read_text().split('## Основний маршрут')[0]
    assert 'Monday' in report or 'tomorrow' in report
    assert 'tomorrow' in report and 'here' in report
    for n in [58,118,119,120,121]:
        key=(BASE/f'{n:03d}/key.md').read_text()
        assert 'Correction 1:' in key and 'Correction 2:' in key and 'New example:' in key
    print('Grade 9 quality: 121 calendar identities, current audit hashes, contextual keys, genre regressions, recovery, timing and 242 simulation cards checked.')

if __name__=='__main__': check()
