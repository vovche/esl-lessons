#!/usr/bin/env python3
"""Export learner-only mission data; importing the teacher builder never runs main()."""
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
BUILD=runpy.run_path(str(ROOT/'scripts/build_teacher_grade9.py'))
PLAN=BUILD['DATA']['lessons']

# The public lesson graph includes97 course pages,2 references and15 older pages.
INTRO={2:1,15:2,29:3,43:4,59:5,73:6,88:7,102:8}
LEGACY={
2:['online-friends'],3:['online-friends'],4:['personality-types'],5:['personality-growth'],
6:['present-past-review'],8:['personal-details'],9:['future-forms','future-forms-v2'],
11:['my-autobiography'],15:['special-occasion-outfits'],16:['special-occasion-outfits'],
17:['clothes-and-accessories'],18:['styles-and-judgement'],19:['styles-and-judgement'],
20:['gerund','fashion-grammar'],22:['styles-and-judgement'],23:['gerund','fashion-grammar'],
24:['fashion-blog'],25:['fashion-opinions'],
}
RULES={
6:'Use the time context: routines take the present simple; an action happening now takes the present continuous; an action completed before another past action takes the past perfect.',
9:'Choose a future form for its purpose: present simple for a timetable, present continuous for an arrangement, going to for a prior intention, will for a decision made now.',
20:'After enjoy and avoid, use the -ing form. An -ing phrase can also act as the subject of a sentence.',
23:'Compare verb patterns: enjoy/avoid + -ing; decide/plan + to + base verb.',
34:'Passive voice: the receiver of the action becomes the subject. Use be in the required tense + past participle: is organised, was organised, will be organised, has been organised.',
37:'Passive questions place the auxiliary before the subject: Was the event organised? Has the work been finished? Will the notice be published?',
48:'These reporting tasks use backshift for a completed past reporting situation. Present becomes past, and will becomes would. Say that; tell someone that.',
51:'The reporting time and place have changed: a Monday statement is reported on Wednesday elsewhere. Today becomes that day, tomorrow the next day, here there and this that. The changes depend on context.',
64:'To report commands and requests, use tell/ask + person + to + base verb. For a negative request use not to.',
67:'Report these completed interviews using backshift. For yes/no questions use if or whether. Keep a wh-word, but use statement word order rather than question inversion.',
78:'A defining relative clause identifies which person or thing is meant. Extra information about an identified thing is separated by commas and uses which rather than that. For people, use who.',
82:'Technology phrases: switch off means stop a device; back up means save a second copy; run out of means have none left. With a pronoun say switch it off.',
93:'Zero conditional describes a general fact: if + present, present. First conditional describes a possible future: if + present, will + base verb.',
96:'Second conditional imagines a different present or future: if + past simple, would + base verb. The past form here does not describe a completed past event.',
107:'Third conditional imagines a different completed past: if + had + past participle, would have + past participle. First identify what actually happened.',
110:'Match the time: a possible future uses the first conditional; an imagined present uses the second; a different completed past uses the third.',
}
RULES[79]=RULES[78]
GENRE_SOURCE={
11:'An autobiography uses I and connects past experiences, present interests and future plans. A short opening can say: Last year I joined a club. Now I am learning a new skill.',
25:'An opinion paragraph states a view, supports it with reasons and an example, then closes the argument. Useful phrases: In my opinion; for example; to sum up.',
39:'Fictional club survey:20 students each chose one favourite club. Sport:10; music:6; film:4. Percentage = number choosing an option / total number surveyed ×100. Describe this group, rather than all teenagers.',
53:'A fictional science vlog uses clear diagrams to explain a water filter, but the episode does not name its sources. A review identifies the topic and audience, evaluates specific strengths and limitations, then gives a recommendation.',
69:'A fictional CV has the headings Name, Education, Skills, Experience and Interests. Experience records activities you have done. A Skills entry should support an ability with evidence. Interests records hobbies. Alex helped classmates organise a book stall and enjoys reading novels.',
84:'Marie Curie fact card:1898—discovery of polonium and radium with Pierre Curie;1903—shared Nobel Prize in Physics;1911—Nobel Prize in Chemistry. A biography chart separates Date, Achievement and Importance. Do not invent a causal claim that the facts do not support.',
98:'An Eco Day leaflet gives short actions with practical reasons. It can use imperatives and a condition for a backup plan: Bring a reusable bottle to reduce single-use waste. Hold the clothes swap indoors if it rains.',
112:'A fictional city visit: the group arrived after the museum closed yesterday. A friendly e-mail to Sam needs a greeting, a clear message and a closing. A reflection on a missed past opportunity uses if + had + past participle and would have + past participle.',
}
SHORT_PRODUCTS={
11:('Write one past event and one present interest for fictional Alex.','Last year I… . Now I… .'),
25:('Write one opinion about clothing with a practical reason.','In my opinion,… because… .'),
39:('Write one accurate sentence about music or film in this survey; name the group.','In this group,…% chose… .'),
53:('Write one cautious recommendation that considers a strength and a limitation.','I recommend it for… , but… .'),
69:('Write one Skills entry with a concrete example from a fictional school project.','Skills:… —… .'),
84:('Write one Date / Achievement row from the fact card.','Date:… | Achievement:…'),
98:('Write one leaflet action with a reason or a rain backup plan.','Bring… to… . / If it rains,… .'),
112:('Write one short e-mail line reflecting on the missed museum visit.','If we had… , we would have… .'),
}
HINTS={
'grammar':'Read the time and situation markers. Match the form to the meaning before choosing.',
'lexis':'Read the whole situation and compare the meanings of the words in the word bank.',
'writing':'Check what this part of the genre is meant to do. Look for concrete evidence rather than a vague claim.',
'listening':'Use this written message as a reading card. Find the named person, event or sequence; do not guess from the length of an option.',
'reading':'Find the sentence about the named person, detail or activity. Compare the two alternatives with that exact sentence.',
'speaking':'Look back at the situation and its specific information. Plan a clear question and a relevant answer.',
'assessment':'Use the facts in this mission card and the exact context in the question.',
'portfolio':'Compare the language context and the required meaning. Explain a change rather than copying a label.',
'recap':'Identify the target language feature and the time context. Try a new example after choosing.',
'starter':'Look for the order of the activities and how the character plans to check learning.',
}


def tidy(text):
    import re
    text=re.sub(r'(?<=\d)(?=[А-Яа-яІіЇїЄє])|(?<=[А-Яа-яІіЇїЄє])(?=\d)', ' ',text)
    text=re.sub(r'(?<=\d)(?=students|sport|music|film|learners|of\b)', ' ',text)
    text=re.sub(r'Year(?=\d)', 'Year ',text)
    text=re.sub(r'(?<=\d)(?=—)|(?<=—)(?=\d)', ' ',text)
    text=re.sub(r':(?=\d)', ': ',text)
    text=re.sub(r';(?=\d)', '; ',text)
    return text


def slugs(l,c):
    values=list(l['section_ids']) or [c['section']]
    if l['number'] in INTRO:values.append(f"sb-u{INTRO[l['number']]}-lead-in")
    if c['type'] in ('grammar','recap'):values.append('sb-grammar')
    if c['type']=='lexis':values.append('sb-wordlist')
    values.extend(LEGACY.get(l['number'],[]))
    # Portfolio missions target the actual correction rather than every semester page.
    if c['type']=='portfolio':
        primary={58:'sb-u1-grammar',118:'sb-u4-grammar',119:'sb-u6-grammar',120:'sb-u8-grammar',121:'sb-u5-writing'}[l['number']]
        values=[primary,'sb-grammar'] if l['number']!=121 else [primary]
    return list(dict.fromkeys(values))


def material(c,mode='learn'):
    n=c['n'];t=c['type']
    # A first-attempt language check must not display the teaching rule or bilingual bank.
    if mode=='check' and t in ('grammar','lexis','recap','portfolio'):
        if t=='lexis':return 'Choose the expression that fits each new situation. Use what you remember, then write a short example of your own.'
        if n!=121:return 'Make an independent choice for each fictional situation. Use the time, speaker and purpose stated in the question. Then write a short new example.'
    if n in GENRE_SOURCE:return GENRE_SOURCE[n]
    if n in RULES:return RULES[n]
    if t=='listening':return c['transcript']
    if n==117:return c['transcript']
    if t=='recap':
        rule=RULES[{1:6,2:23,3:34,4:48,5:67,6:78,7:93,8:107}.get(c['u'],6)]
        return c['text']+'\n\nLanguage focus: '+rule
    if t=='portfolio':
        if n==121:return GENRE_SOURCE[69]
        return RULES[{58:6,118:48,119:78,120:107}[n]]
    return c['text']


def questions(c):
    n=c['n']
    if n==117:
        make=BUILD['item']
        return [make('How much time does this team have for its first draft?','fifteen minutes',['twenty minutes'],'not exported'),make('What will the team check?','the spelling and dates',['the price and colours'],'not exported')]
    if c['type']=='portfolio':
        if n==121:return BUILD['GENRE_ITEMS'][69]
        return BUILD['GRAMMAR'][{58:6,118:48,119:78,120:107}[n]][2][:2]
    return c['questions'][:2]


def production(c):
    if c['n'] in SHORT_PRODUCTS:prompt,starter=SHORT_PRODUCTS[c['n']]
    elif c['type'] in ('grammar','recap','portfolio'):
        prompt='Write one new short example using this language feature; keep its time and meaning clear.'
        starter='My new example:…'
    elif c['type']=='lexis':
        prompt='Use one word from this mission in a new situation. Give enough detail to show its meaning.';starter='In this situation,…'
    elif c['type']=='speaking':
        prompt='Write a two-turn exchange: ask for one detail from the situation and give a relevant answer.';starter='A:…? B:… .'
    elif c['n']==1:
        prompt='Write one realistic practice activity, a time and a way to check your learning.';starter='I will… for… minutes. I can check by… .'
    elif c['type']=='assessment':
        prompt='Write one clear question to ask the project team about its display.';starter='Could you explain…?'
    else:
        prompt='Write one accurate detail from the card and one follow-up question.';starter='The card says… . My question is…?'
    return {'prompt':prompt,'starter':starter}


def export():
    lessons=[]
    for l in PLAN:
        c=BUILD['card'](l);n=l['number'];typ=c['type']
        title=tidy(c['genre'])
        if typ=='listening':title='Повідомлення: головна думка та деталі'
        if typ=='assessment':title='Командна виставка: факти, мовні рішення й запитання'
        if typ=='portfolio':title={58:'Минуле й теперішнє: уточни повідомлення',118:'Передай слова персонажа',119:'Опиши предмет точно',120:'Уяви інший результат',121:'Підтвердь навичку у CV'}[n]
        learner_role={'writing':'Автор короткого '+title,'lexis':'Редактор слововживання','grammar':'Редактор мовних ситуацій','speaking':'Учасник діалогу','reading':'Дослідник повідомлення','listening':'Читач повідомлення','assessment':'Редактор командної виставки','portfolio':'Редактор власного прикладу','recap':'Дослідник мовних рішень','starter':'Автор плану практики'}[typ]
        goal='Знайди точну інформацію та застосуй її у короткому власному прикладі.'
        if typ=='grammar':goal='Обери форму за часовим і смисловим контекстом та застосуй її у новому прикладі.'
        if typ=='writing':goal='Зроби точний вибір щодо змісту або частини жанру й створи один доречний фрагмент.'
        if typ=='lexis':goal='Зістав значення слова із ситуацією та використай слово у новому контексті.'
        games=[]
        for round_index,(mode,qs) in enumerate([('learn',questions(c)),('check',BUILD['transfer_items'](c))]):
            assert len(qs)>=2,(n,mode)
            steps=[]
            for i,q in enumerate(qs[:2]):
                opts=[{'text':tidy(q['answer']),'effect':'advance'},{'text':tidy(q['wrong'][0]),'effect':'retry'}]
                if (n+round_index+i)%2:opts.reverse()
                steps.append({'prompt':tidy(q['prompt']),'choices':opts,'hint':HINTS[typ]})
            games.append({'id':mode,'mode':mode,'title':('Майстерня: ' if mode=='learn' else 'Новий виклик: ')+title,'role':learner_role,'goal':goal,'source':tidy(material(c,mode)),'steps':steps,'production':production(c)})
        lessons.append({'id':f'g9-{n:03d}','number':n,'title':title,'slugs':slugs(l,c),'games':games})
    return {'version':1,'grade':9,'lessons':lessons}


def main():
    data=export()
    (ROOT/'9/simulations.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    mapped={s for l in data['lessons'] for s in l['slugs']}
    existing={p.parent.name for p in (ROOT/'9').glob('*/index.html')}
    assert mapped==existing,{'unmapped':sorted(existing-mapped),'missing_page':sorted(mapped-existing)}
    print(f'Grade9: {len(data["lessons"])} calendar missions,242 games, {len(mapped)} existing pages mapped.')

if __name__=='__main__':main()
