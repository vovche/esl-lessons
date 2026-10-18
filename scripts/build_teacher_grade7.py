#!/usr/bin/env python3
"""Rebuild private Grade 7 Markdown packs from the sanitized source plan; stdlib only."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'teacher'/'7'

# Original classroom micro-stories, not textbook extracts. Fictional details vary per lesson.
BANK={
0:dict(title='Повернення до навчання',lex=[('study group','навчальна група'),('tip','порада'),('ask','запитувати'),('listen','слухати'),('take turns','говорити по черзі'),('tease','дражнити'),('help','допомагати'),('choose','обирати')],
 places=['the school library','Room 12','the reading corner'], times=['Tuesday at 2 p.m.','Thursday at 3 p.m.','Monday at 1 p.m.'],items=['a word list','a short dialogue','a reading card'],
 intro='{name} is joining a study group. The group meets in {place} on {time}. The first task is {item}. Everyone may work alone or with a partner. One useful tip is to ask a clear question. Members take turns and do not tease anyone who needs more time. {name} writes one question and asks for help politely.',
 task='Напиши 6–8 реплік для вигаданого учасника навчальної групи: привітайся, запитай місце й час, попроси пояснення, подякуй.',model='Hello! Where does the group meet? When does it meet? Could you repeat the task, please? Thank you.'),
1:dict(title='Шкільне життя і дозвілля',lex=[('club','гурток'),('science geek','ентузіаст науки'),('bookworm','любитель читати'),('anniversary','річниця'),('decoration','прикраса'),('presentation','презентація'),('exhibition','виставка'),('take turns','говорити по черзі')],
 places=['the science lab','the school hall','the art room'],times=['Friday at 3 p.m.','Wednesday at 2 p.m.','Monday at 4 p.m.'],items=['a presentation about birds','an exhibition of drawings','a short school play'],
 intro='{name} belongs to a school club. The club meets in {place} on {time}. This week the members are preparing {item} for the school anniversary. {name} usually collects ideas, but today is making a decoration. One member calls himself a science geek; another enjoys books. The teacher explains that labels must never be used to tease people. Everyone can choose a useful role.',
 task='Створи запрошення на вигадану шкільну подію: назва, місце, час, дві дії учасників і спосіб долучитися без виступу перед класом.',model='Join our school exhibition! It is in the art room on Monday at 4 p.m. We usually show drawings. Today we are preparing decorations. You can write a label or present a picture.'),
2:dict(title='Домашні справи',lex=[('sweep the floor','підмітати підлогу'),('wash up','мити посуд'),('dishwasher','посудомийна машина'),('vacuum cleaner','пилосос'),('household duty','домашній обов’язок'),('take out the garbage','виносити сміття'),('share','ділити між собою'),('switch off','вимикати')],
 places=['the kitchen','the living room','the community room'],times=['Saturday at 10 a.m.','Sunday at 11 a.m.','Friday at 5 p.m.'],items=['a list of household duties','a shared cleaning plan','a simple chore chart'],
 intro='{name} and two friends met in {place} on {time}. They made {item}. Yesterday {name} swept the floor while Alex washed up. At ten o’clock Sam was checking the list. The dishwasher was not working, so the friends used a bowl. They shared the tasks fairly and asked before changing a partner’s job. They switched off the vacuum cleaner when the work was finished.',
 task='Напиши повідомлення про вигаданий день прибирання: 2 виконані справи, що хтось робив у певну мить, і ввічлива пропозиція розподілу роботи.',model='Yesterday Alex washed up and Sam swept the floor. At ten I was checking our list. Could we share the jobs? I can write the plan.'),
3:dict(title='Приготування їжі',lex=[('chopping board','дошка для нарізання'),('grater','тертка'),('ladle','ополоник'),('bowl','миска'),('stir','помішувати'),('boil','варити / кип’ятити'),('slice','нарізати скибками'),('ingredients','інгредієнти')],
 places=['the cooking club','the school kitchen','the recipe workshop'],times=['Tuesday at 3 p.m.','Thursday at 2 p.m.','Saturday at 11 a.m.'],items=['a vegetable soup recipe','a fruit salad recipe','a recipe for a cold sandwich'],
 intro='{name} has brought {item} to {place}. The group meets on {time}. The members have checked the ingredients, but they have not chosen all the utensils yet. There is a bowl, a ladle and a chopping board on the table. An adult manages all sharp tools and hot equipment. The students only write instructions today. They respect different food choices and ask before suggesting an ingredient.',
 task='Підготуй паперову картку вигаданого рецепта: назва, три інгредієнти, два предмети посуду, 3 послідовні кроки й одне повідомлення про вже виконану дію. Нічого не готуємо.',model='Fruit salad: apples, bananas, oranges. Use a bowl and a spoon. First, ask an adult to prepare the fruit. Next, put it in the bowl. Finally, stir gently. We have checked the ingredients.'),
4:dict(title='Свята і традиції',lex=[('custom','звичай'),('celebrate','святкувати'),('Eve','переддень свята'),('midnight','опівніч'),('candle','свічка'),('receive','отримувати'),('greet','вітати'),('tradition','традиція')],
 places=['the community hall','the town library','the school museum'],times=['Friday at 4 p.m.','Saturday at 2 p.m.','Thursday at 3 p.m.'],items=['a paper lantern display','a collection of greeting cards','a story about a winter custom'],
 intro='{name} is making a guide to an imaginary local celebration. It is held in {place} on {time}. Visitors are shown {item}. Cards are made by volunteers and guests are greeted politely. Some stories mention New Year’s Eve and midnight. A drawing of a candle is used instead of a real flame. Visitors may take part or quietly observe. The guide does not claim that everyone celebrates in the same way.',
 task='Склади 5–6 речень для путівника вигаданим святом: де й коли його проводять, що створюють/показують, як вітають гостей і як можна лише спостерігати.',model='The celebration is held in the library. Paper cards are made by volunteers. Visitors are greeted politely. A candle is drawn on each card. Guests can join the activity or observe.'),
5:dict(title='Спорт',lex=[('team','команда'),('match','матч'),('coach','тренер'),('competition','змагання'),('score','рахунок'),('prize','приз'),('equipment','спорядження'),('fair play','чесна гра')],
 places=['the school gym','the town sports hall','the school playground'],times=['Friday at 2 p.m.','Saturday at 10 a.m.','Wednesday at 3 p.m.'],items=['a friendly basketball match','a school table tennis competition','a friendly volleyball match'],
 intro='{item_cap} was organised by the school club. It was played in {place} on {time}. {name} wrote a short report. The equipment was checked by the coach before the game. Two teams took part and the final score was 12–10. A prize was given for fair play, not only for winning. Students could also help as reporters or scorekeepers. The report describes actions without insulting the other team.',
 task='Напиши звіт про вигадане змагання: назва, місце, час, рахунок, хто перевірив спорядження, за що дали приз. Ужий 2 речення у Past Simple Passive.',model='A friendly match was played in the school gym on Friday. The equipment was checked by the coach. The final score was 12–10. A prize was given for fair play.'),
6:dict(title='Самопочуття і спілкування з лікарем',lex=[('appointment','запис / домовлена зустріч'),('symptom','симптом'),('sore throat','біль у горлі'),('headache','головний біль'),('nurse','медсестра / медбрат'),('ask for help','просити допомоги'),('form','бланк'),('before','до / перед тим як')],
 places=['the school health room','the reception desk','the clinic waiting room'],times=['Monday at 9 a.m.','Tuesday at 10 a.m.','Thursday at 11 a.m.'],items=['an appointment card','a short message for the nurse','a completed information form'],
 intro='{name}, a fictional character, arrives at {place} on {time}. Before the visit, the character had prepared {item}. The receptionist asks about the appointment, and {name} describes a sore throat in simple words. If a visitor needs language help, the receptionist offers a paper form. The nurse listens and asks one question at a time. This is language practice: students do not diagnose illness or suggest medicine.',
 task='Створи діалог із вигаданим відвідувачем і реєстратором: привітання, запит часу, коротке повідомлення про симптом персонажа, прохання повторити й подяка. Без медичних порад.',model='Good morning. I have an appointment at ten. I have a sore throat. Could you repeat the question, please? I had prepared my form before I arrived. Thank you for your help.'),
7:dict(title='Кіно і театр',lex=[('performance','вистава'),('stage','сцена'),('audience','глядачі'),('comedy','комедія'),('review','відгук'),('plot','сюжет'),('sequel','продовження'),('subtitles','субтитри')],
 places=['the school theatre','the community cinema','the small arts centre'],times=['Friday at 5 p.m.','Saturday at 3 p.m.','Thursday at 4 p.m.'],items=['a comedy about two lost robots','a play about a travelling musician','an animated film about a curious fox'],
 intro='{name} watched {item} in {place} on {time}. The plot was quite simple, but the performance was very lively. The audience could read subtitles on a screen. {name} found the first half more interesting than the second half. A friend preferred the ending because it was less predictable. Their review compares the story and the acting. Both opinions are accepted when they include a reason and respectful language.',
 task='Напиши відгук про вигадану виставу/фільм: назва, місце, сюжет одним реченням, 2 оцінки з причинами й одне порівняння. Дозволено мати іншу думку.',model='I watched a comedy about two robots. The plot was quite simple, but the acting was very lively. The first half was more interesting than the second half because it had a surprising problem. I would recommend it.'),
8:dict(title='Подорожі й визначні місця',lex=[('landmark','визначне місце'),('capital','столиця'),('cathedral','собор'),('castle','замок'),('tour guide','екскурсовод'),('leaflet','буклет'),('itinerary','маршрут / план подорожі'),('attraction','туристичний об’єкт')],
 places=['the old castle gate','the city museum entrance','the central library'],times=['Saturday at 10 a.m.','Sunday at 11 a.m.','Friday at 2 p.m.'],items=['a castle and a small museum','a cathedral and a public garden','a landmark and an art gallery'],
 intro='{name} is planning an imaginary trip. The group meets at {place} on {time}. The itinerary includes {item}. Both attractions are shown on a paper map. Each visitor receives a leaflet, but no online ticket is needed for this classroom story. The tour guide suggests either a short route or a longer route. {name} chooses the short route because it includes a quiet stop. The group checks the meeting point before leaving.',
 task='Створи паперовий буклет уявної екскурсії: місце й час зустрічі, два об’єкти, короткий маршрут та довший варіант, причина вибору й точка завершення.',model='Meet at the castle gate at ten. Both the museum and the garden are on our map. You can choose either the short route or the long route. I suggest the short route because it includes a quiet stop. Finish at the gate.'),
}

# Models and controlled practice are selected by the actual grammar focus, not by a single grade template.
GRAMMAR={
'present':dict(rule='Present Simple: звички, do/does у запитанні. Present Continuous: am/is/are + V-ing для дії зараз.',model='Alex usually reads in the club. Today Alex is making a poster. Where does Alex read? What is Alex making?',items=[('Alex usually ___ in the club. (read / reads)','reads'),('Today Alex ___ a poster. (makes / is making)','is making'),('Where ___ Alex usually read? (do / does)','does'),('What ___ Alex making now? (is / does)','is')]),
'past':dict(rule='Past Simple: завершена дія в минулому. Ствердження V2; запитання did + V1; заперечення did not + V1.',model='Sam swept the floor yesterday. Did Sam sweep the floor? Sam did not wash up.',items=[('Yesterday Sam ___ the floor. (sweep / swept)','swept'),('___ Sam wash up yesterday? (Did / Was)','Did'),('Sam did not ___ the dishes. (washed / wash)','wash'),('They ___ a chore chart last week. (made / make)','made')]),
'past_cont':dict(rule='Past Continuous: was/were + V-ing для процесу в певну мить у минулому. Запитання: (Wh-) + was/were + підмет + V-ing?',model='At ten Sam was cleaning. What was Sam doing? Were the friends washing up?',items=[('At ten Sam ___ cleaning. (was / were)','was'),('The friends ___ washing up. (was / were)','were'),('What ___ Sam doing at ten? (did / was)','was'),('___ they using a vacuum cleaner? (Were / Did)','Were')]),
'perfect':dict(rule='Present Perfect: have/has + V3, результат до тепер. Після have/has не ставимо V2. У запитанні have/has перед підметом.',model='We have checked the ingredients. Alex has brought a bowl. What has Alex brought? Have you checked the recipe?',items=[('We ___ checked the ingredients. (have / has)','have'),('Alex has ___ a bowl. (bring / brought)','brought'),('What ___ Alex prepared? (has / did)','has'),('We have not ___ the recipe yet. (finish / finished)','finished')]),
'passive':dict(rule='Present Simple Passive: am/is/are + V3; увага до дії та її об’єкта. Виконавець: by + особа. Wh-запитання: Where + is/are + підмет + V3?',model='Volunteers make cards. → Cards are made by volunteers. Where are cards made? The event is held in the hall.',items=[('Cards ___ made by volunteers. (is / are)','are'),('The event is ___ in the hall. (hold / held)','held'),('Where ___ cards made? (are / do)','are'),('Guests are greeted ___ volunteers. (by / with)','by')]),
'past_passive':dict(rule='Past Simple Passive: was/were + V3 для минулої дії над об’єктом. Wh-запитання: Where/When + was/were + підмет + V3?',model='The coach checked the equipment. → The equipment was checked by the coach. Where was the match played?',items=[('The match ___ played yesterday. (was / is)','was'),('Two prizes ___ given. (was / were)','were'),('The equipment was ___ by the coach. (check / checked)','checked'),('Where ___ the match played? (did / was)','was')]),
'zero':dict(rule='Zero Conditional: if + Present Simple, Present Simple для правила/регулярної умови. Це мовна модель, а не медична рекомендація.',model='If a visitor needs language help, the receptionist offers a paper form. If I do not understand, I ask a question.',items=[('If a visitor ___ help, the receptionist offers a form. (need / needs)','needs'),('If I do not understand, I ___ a question. (ask / asked)','ask'),('If visitors arrive early, they ___ in the waiting room. (wait / waited)','wait'),('The receptionist repeats the question if a visitor ___ her to. (asks / asked)','asks')]),
'past_perfect':dict(rule='Past Perfect: had + V3 — дія раніше іншої минулої дії. Познач дві події на лінії часу; не плутай had prepared з has prepared.',model='Alex had prepared the form before the visit began. Had Alex prepared it? What had Alex prepared?',items=[('Alex ___ prepared the form before the visit began. (had / has)','had'),('The nurse had ___ the message before Alex arrived. (read / reading)','read'),('___ Alex prepared the card before the visit? (Had / Did)','Had'),('Alex had not ___ the time. (forget / forgotten)','forgotten')]),
'degree':dict(rule='Прислівники ступеня уточнюють ознаку: quite simple, very lively, extremely interesting. Too = надмірно; enough стоїть після прикметника.',model='The plot is quite simple. The screen is too small. The subtitles are clear enough.',items=[('The plot is ___ simple. (quite / enough)','quite'),('The screen is ___ small to read. (too / enough)','too'),('The subtitles are clear ___. (enough / very)','enough'),('The acting was ___ lively. (very / enough)','very')]),
'comparison':dict(rule='Порівнюємо ознаки: more/less + довгий прикметник + than; as + прикметник + as; the same as. Для коротких прикметників — -er.',model='The first half is more interesting than the second. This play is not as long as that film. The ending is less predictable.',items=[('This film is more interesting ___ that one. (than / as)','than'),('This play is as long ___ that film. (than / as)','as'),('The plot is ___ predictable than the ending. (less / as)','less'),('These two tickets cost the same ___ those tickets. (as / than)','as')]),
'determiners':dict(rule='Each + однина; both + множина; some у ствердженні; any у загальному запитанні/запереченні; обираємо за кількістю й змістом.',model='Each visitor gets a leaflet. Both attractions are open. There are some maps. Are there any tickets?',items=[('___ visitor gets a leaflet. (Each / Both)','Each'),('___ attractions are on the map. (Each / Both)','Both'),('There are ___ maps on the desk. (some / any)','some'),('Are there ___ tickets left? (some / any)','any')]),
'conjunctions':dict(rule='And додає; but протиставляє; because дає причину. Both… and… поєднує два варіанти; either… or… пропонує вибір.',model='Both the castle and the museum are open. Choose either a short route or a long route. I choose the short route because it includes a quiet stop.',items=[('Both the castle ___ the museum are open. (and / or)','and'),('Choose either the short route ___ the long route. (and / or)','or'),('I choose the short route ___ it has a quiet stop. (because / but)','because'),('The castle is open, ___ the museum is closed. (and / but)','but')]),
}
# Lesson-specific lexical targets from the original plan, with neutral pupil-safe glosses.
LEXICAL={
4:[('bookworm','любитель читати'),('chatterbox','балакун (лише самоопис персонажа)'),('computer geek','ентузіаст комп’ютерів'),('drama queen','людина, що перебільшує (не ярлик для однокласника)'),('dynamo','дуже енергійна людина'),('music addict','великий любитель музики'),('science geek','ентузіаст науки'),('describe','описувати')],
9:[('make a decoration','виготовити прикрасу'),('give a prize','вручити приз'),('hold an exhibition','провести виставку'),('perform a play','зіграти п’єсу'),('make a presentation','підготувати презентацію'),('hold a concert','провести концерт'),('give a present','подарувати подарунок'),('perform a song','виконати пісню')],
20:[('do the washing-up','мити посуд'),('dry the dishes','витирати посуд'),('sweep the floor','підмітати підлогу'),('walk a dog','вигулювати собаку'),('take out the garbage','виносити сміття'),('mop the floor','мити підлогу'),('tidy','прибирати / упорядковувати'),('feed a pet','годувати домашню тварину')],
25:[('appliance','прилад'),('improvement','покращення'),('oven','духова шафа'),('electrical','електричний'),('switch on','вмикати'),('switch off','вимикати'),('turn on','вмикати'),('turn off','вимикати')],
35:[('apron','фартух'),('chopping board','дошка для нарізання'),('frying pan','сковорода'),('grater','тертка'),('kettle','чайник для кип’ятіння'),('ladle','ополоник'),('saucepan','каструля'),('whisk','вінчик')],
40:[('add','додавати'),('blend','змішувати до однорідності'),('bake','пекти'),('boil','варити / кип’ятити'),('chop','дрібно нарізати'),('roast','запікати'),('stir','помішувати'),('ingredients','інгредієнти')],
50:[('Good Friday','Страсна п’ятниця'),('Boxing Day','назва святкового дня 26 грудня'),('New Year’s Eve','переддень Нового року'),('celebration','святкування'),('custom','звичай'),('greet','вітати'),('observe','спостерігати / дотримуватися'),('tradition','традиція')],
54:[('define','давати визначення'),('paraphrase','перефразовувати'),('custom','звичай'),('celebration','святкування'),('in other words','іншими словами'),('means','означає'),('a kind of','вид / різновид'),('for example','наприклад')],
68:[('athletics','легка атлетика'),('weightlifting','важка атлетика'),('cycle ball','велобол'),('windsurfing','віндсерфінг'),('wrestling','боротьба'),('zorbing','зорбінг'),('elephant polo','назва поло на слонах'),('underwater hockey','підводний хокей')],
73:[('court','корт / майданчик'),('basket','баскетбольний кошик'),('pitch','спортивне поле'),('racket','ракетка'),('net','сітка'),('rink','ковзанка'),('stick','ключка'),('puck','шайба')],
86:[('rash','висип'),('cough','кашель'),('headache','головний біль'),('sore throat','біль у горлі'),('bruise','синець'),('stomachache','біль у животі'),('dizzy','той, кому паморочиться'),('toothache','зубний біль')],
91:[('suffer','страждати (від)'),('chest','грудна клітка'),('pain','біль'),('X-ray','рентгенівський знімок'),('injection','ін’єкція'),('appointment','домовлений прийом'),('nurse','медсестра / медбрат'),('form','бланк')],
104:[('curtain','завіса'),('balconies','балкони'),('seats','місця для сидіння'),('stage','сцена'),('lights','освітлення / ліхтарі'),('screen','екран'),('audience','глядачі'),('performance','вистава')],
109:[('comedy','комедія'),('cartoon','мультфільм'),('science fiction film','науково-фантастичний фільм'),('historical film','історичний фільм'),('horror film','фільм жахів'),('musical','мюзикл'),('action film','бойовик'),('thriller','трилер')],
121:[('Kingston','Кінгстон'),('Suva','Сува'),('Wellington','Веллінгтон'),('Dublin','Дублін'),('London','Лондон'),('Ottawa','Оттава'),('Washington, DC','Вашингтон, округ Колумбія'),('Canberra','Канберра')],
126:[('attractions','туристичні об’єкти'),('excursions','екскурсії'),('tour','тур / екскурсія'),('map','мапа'),('tour guide','екскурсовод'),('tickets','квитки'),('luggage','багаж'),('visa','віза')],
}
LEX_EXAMPLES={
4:'A fictional bookworm likes reading. A computer geek enjoys coding. Another character calls herself a science geek. A chatterbox likes talking, but everyone takes turns. We never use these labels to judge classmates.',
9:'We will make a decoration, make a presentation and hold an exhibition. We can also perform a play. A volunteer will give a prize at the end.',
20:'Our imaginary team will do the washing-up and dry the dishes. Two friends will sweep the floor and walk a dog. Everyone can choose a suitable task.',
25:'An oven is an appliance. Some appliances are electrical. Our diagram shows the words switch on and switch off. We only describe the controls on paper; we do not operate equipment.',
35:'Our paper recipe shows an apron, a chopping board, a frying pan and a grater. The adult in the story handles tools. The pupils write labels without cooking.',
40:'Our paper recipe says: chop the fruit, add it to a bowl and blend the mixture. Another recipe uses the words bake, boil and roast. We compare instructions; we do not cook in class.',
50:'Our imaginary display has cards labelled Good Friday, Boxing Day and New Year’s Eve. Each card explains one custom. A visitor can observe the display without celebrating any of these days.',
54:'We can define a custom as something a group often does. A celebration is a special event. To paraphrase means to express the idea in different words. In other words, we keep the meaning and change the wording.',
68:'Our imaginary sports leaflet lists athletics and weightlifting. Another page explains cycle ball and windsurfing. Visitors read about the sports and choose a reporting topic. No one has to perform the activities.',
73:'A basketball court has a basket. A tennis player uses a racket and a net. Ice hockey is played on a rink with a stick and a puck. These are vocabulary examples, not instructions to exercise here.',
86:'Our fictional form lists a rash, a cough, a headache and a sore throat. The character chooses words to explain a symptom to a nurse. Pupils do not diagnose anyone or discuss classmates’ health.',
91:'The fictional form has the words chest and pain. Another card shows an X-ray and the word injection. A nurse asks one question at a time. The exercise describes language, not medical treatment.',
104:'The curtain is in front of the stage. The audience sits in seats and on balconies. The lights are above the stage. Our drawing also has a screen for subtitles.',
109:'Our fictional programme offers a comedy and a cartoon. Another screen shows a science fiction film. A historical film is on later. Viewers can choose a genre without watching frightening content.',
121:'Our imaginary itinerary lists Kingston and Suva. A second leaflet lists Wellington and Dublin. A third lists London, Ottawa, Washington, DC and Canberra. We practise city names and compare paper routes; we do not need real tickets.',
126:'Our paper map shows two attractions. The tour guide offers excursions and checks the tickets. Visitors leave their luggage at the fictional meeting point. The leaflet also explains that a visa is a travel document; this is a story, not travel advice.',
}
DEFAULT={0:'present',1:'present',2:'past',3:'perfect',4:'passive',5:'past_passive',6:'zero',7:'comparison',8:'conjunctions'}

def focus(l):
 t=l['topic'].lower();k=l['kind']
 if k in ('pair_diagnostic','semester_assessment'):return 'assessment'
 if k=='portfolio':return 'portfolio'
 if k=='project_workshop':return 'project'
 if k=='unit_recap' or 'повторення' in t:return 'review'
 if k=='listening_workshop' or 'слухання' in t:return 'listening'
 if k=='grammar_workshop' or 'граматика' in t:return 'grammar'
 if 'письмо' in t:return 'writing'
 if 'говоріння' in t:return 'speaking'
 if 'лексика' in t:return 'vocabulary'
 return 'reading'

def grammar(l,u):
 s=l.get('language_inventory',{}).get('grammar','').lower()
 if 'past continuous' in s:return GRAMMAR['past_cont']
 if 'past perfect' in s:return GRAMMAR['past_perfect']
 if 'zero conditional' in s:return GRAMMAR['zero']
 if 'past simple passive' in s or 'wh-запитання у past' in s:return GRAMMAR['past_passive']
 if 'adverbs of degree' in s:return GRAMMAR['degree']
 if 'comparison' in s or 'порівняння:' in s:return GRAMMAR['comparison']
 if 'determiners' in s:return GRAMMAR['determiners']
 if 'conjunctions' in s:return GRAMMAR['conjunctions']
 if 'passive' in s:return GRAMMAR['passive']
 if 'present perfect' in s:return GRAMMAR['perfect']
 if 'past simple' in s:return GRAMMAR['past']
 return GRAMMAR[DEFAULT[u]]

def context(u,n,offset=0):
 b=BANK[u];j=(n+offset)%3;name=['Mia','Leo','Robin','Dana','Alex','Kim'][(n+offset)%6]
 d=dict(name=name,place=b['places'][j],time=b['times'][j],item=b['items'][j]);d['item_cap']=d['item'][0].upper()+d['item'][1:]
 d['text']=b['intro'].format(**d)
 return d

def table(rows):
 return '| Час | Репліка та дія вчителя | Дії учнів і видимий результат |\n|---|---|---|\n'+'\n'.join('| '+ ' | '.join(r)+' |' for r in rows)+'\n'

def practice(g):
 return '\n'.join(f'{i}. {q} → ____________________' for i,(q,a) in enumerate(g['items'],1))

def build(l):
 n=l['number'];u=l['unit'];mode=focus(l)
 # Semester assessments and portfolios sample the relevant half-year, rather than the Starter.
 if u==0 and n>1:u=4 if l['semester']==1 else 8
 b=BANK[u];g=grammar(l,u);c=context(u,n)
 read_u=u-1 if l['kind']=='pair_diagnostic' else u
 if l['kind']=='semester_assessment':read_u=2 if l['semester']==1 else 6
 r=context(read_u,n,1);a=context(u,n,2)
 folder=BASE/f'{n:03d}';folder.mkdir(parents=True,exist_ok=True)
 assessed=mode=='assessment';lr=assessed and ('слухання і читання' in l['topic']);sw=assessed and ('говоріння і письмо' in l['topic']);diag=l['kind']=='pair_diagnostic'
 lex=LEXICAL.get(n,b['lex'])
 lex_table='| English | Українською |\n|---|---|\n'+'\n'.join('| '+en+' | '+uk+' |' for en,uk in lex)
 rquestion=[('Where does the story take place?',r['place']),('When does the event or meeting happen?',r['time']),('What item, activity or document is mentioned?',r['item'])]
 aquest=[('Where does the story take place?',a['place']),('When does the event or meeting happen?',a['time']),('What item, activity or document is mentioned?',a['item'])]
 questions=lambda qs:'\n'.join(f'{i}. {q}\n\n   __________________________________________________________' for i,(q,_) in enumerate(qs,1))
 # Variant-specific lexical retrieval; reversal prevents answer leakage from aligned lists.
 order=list(range(4));shift=n%4;order=order[shift:]+order[:shift];order.reverse()
 choices='; '.join(f'{chr(65+i)} — {lex[idx][1]}' for i,idx in enumerate(order))
 match='\n'.join(f'{i+1}. {lex[i][0]} → ____' for i in range(4))+'\n\nВаріанти: '+choices+'.'
 match_key=', '.join(f'{i+1} — {chr(65+order.index(i))}' for i in range(4))
 pctx=r if read_u==u else c
 model_by_unit={
 0:f'Hello! Where does the group meet? — In {pctx["place"]}. When does it meet? — {pctx["time"]}. Could you repeat the task, please? — The first task is {pctx["item"]}. Thank you!',
 1:f'Join our school event! We meet in {pctx["place"]} on {pctx["time"]}. We are preparing {pctx["item"]}. It is for the school anniversary. Members usually collect ideas, but today they are making decorations. You can write a label or present an idea.',
 2:f'Our friends met in {pctx["place"]} on {pctx["time"]}. They made {pctx["item"]}. Yesterday {pctx["name"]} swept the floor and Alex washed up. At ten Sam was checking the list. The friends shared the work fairly. Could we write a similar plan and take turns?',
 3:f'Our group meets in {pctx["place"]} on {pctx["time"]}. We have brought {pctx["item"]}. For our paper fruit salad recipe we need apples, bananas and oranges. Use a bowl and a spoon. First, ask an adult to prepare the fruit. Next, put it in the bowl. Finally, stir gently. We have checked the ingredients; we are only writing today.',
 4:f'The celebration is held in {pctx["place"]} on {pctx["time"]}. Visitors are shown {pctx["item"]}. Paper cards are made by volunteers. Guests are greeted politely. A candle is drawn instead of using a real flame. Visitors can join the activity or quietly observe.',
 5:f'{pctx["item_cap"]} was played in {pctx["place"]} on {pctx["time"]}. The equipment was checked by the coach. Two teams took part. The final score was 12–10. A prize was given for fair play. Students could help as reporters.',
 6:f'Good morning. Where is my appointment? — At {pctx["place"]}. When is it? — {pctx["time"]}. I have a sore throat; could you repeat your question, please? I had prepared {pctx["item"]} before I arrived. Thank you for your help.',
 7:f'I watched {pctx["item"]} in {pctx["place"]} on {pctx["time"]}. The story follows its main characters through a problem. The plot was quite simple, but the acting was very lively. The first half was more interesting than the second half. I liked it because the audience could read subtitles. I would recommend it to a friend who enjoys this kind of story.',
 8:f'Meet at {pctx["place"]} on {pctx["time"]}. Our itinerary includes {pctx["item"]}. Both attractions are on our paper map. Choose either a short route or a longer route. I suggest the short route because it includes a quiet stop. Finish at the same meeting point.'}
 product_model=model_by_unit[u]
 if mode=='vocabulary':product_model+=' '+LEX_EXAMPLES.get(n,'')
 section=' / '.join(x.get('title_uk',x.get('title','')) for x in l.get('catalog_sections',[])) or 'доданий календарний урок'
 skill={'reading':'читання й аргументована відповідь','vocabulary':'лексичний вибір у контексті','grammar':'граматична точність і пояснення моделі','listening':'розуміння усного повідомлення','speaking':'діалог і ввічливе уточнення','writing':'зв’язний письмовий текст','project':'створення й редагування продукту','review':'відновлення знань і виправлення помилок','assessment':'самостійне виконання діагностичних завдань','portfolio':'порівняння чернетки та покращеного тексту'}[mode]
 core={'reading':'R1–R3 + доказ із тексту','vocabulary':'V1–V4 + 2 власні словосполучення','grammar':'G1–G4 + одне пояснення вибору','listening':'L1–L3 після двох читань','speaking':'S: 4–6 реплік із запитанням і уточненням','writing':'P: 5–6 зв’язних речень','project':'P: чернетка → відгук → чистова картка','review':'V + G + виправлення 2 помилок','assessment':'продукт за специфікацією контролю нижче','portfolio':'F: до → після → пояснення зміни'}[mode]
 # Per-mode tasks create different learning products; all supporting content is supplied.
 task=b['task']
 if mode=='reading':task+=' Додай 2 факти саме з тексту R; підкресли їх у своєму повідомленні. Для цього варіанта можна 6–8 речень/реплік.'
 if mode=='vocabulary':task+=' Використай щонайменше 4 слова зі словничка; обведи їх. Можна додати 2 короткі речення для точного вживання цих слів.'
 if mode=='grammar':task+=' Застосуй сьогоднішню граматичну модель двічі та підкресли допоміжні дієслова.'
 if mode=='listening':task+=' Додай один факт з L; під час слухання познач ключове слово, а після другого читання перевір.'
 if mode=='speaking':task='Ролі: A — автор пропозиції; B — партнер, який уточнює місце й час та пропонує зміну. '+task+' Спочатку 30 секунд подумай; потім обміняйтеся ролями. Самостійний варіант — запиши обидві ролі.'
 if mode=='project':task+=' Продукт: односторінкова картка для іншої групи. Зроби чернетку, отримай відгук «зрозуміло… / уточни…», внеси 2 зміни й познач їх.'
 if mode=='review':task+=' Перед текстом виконай V і G без підказок; потім відкрий модель, виправ 2 місця іншим кольором і поясни одну зміну.'
 if mode=='portfolio':task='Порівняй чернетку F з моделлю; виправ 3 неточності, поясни 2 зміни. '+b['task']+' Наприкінці допиши конкретний навчальний крок: «Наступного разу перевірю…». Емоції не оцінюються.'
 if assessed:task=b['task']+' Виконай самостійно. Достатньо 5–6 речень або 6 реплік із двома запитаннями; оцінюється зміст і зрозумілість, а не публічність відповіді.'
 # Error-editing examples are independently answerable and tied to grammar.
 wrong={'present':('Alex usually read in the club. Today Alex making a poster. Where Alex reads?','Alex usually reads in the club. Today Alex is making a poster. Where does Alex read?'),
 'past':('Sam sweep the floor yesterday. Did Sam washed up? They did not made a list.','Sam swept the floor yesterday. Did Sam wash up? They did not make a list.'),
 'past_cont':('Sam were cleaning at ten. What Sam was doing? They was washing up.','Sam was cleaning at ten. What was Sam doing? They were washing up.'),
 'perfect':('We has checked the list. Alex has bring a bowl. What Alex has prepared?','We have checked the list. Alex has brought a bowl. What has Alex prepared?'),
 'passive':('Cards is made here. The event is hold in the hall. Where cards are made?','Cards are made here. The event is held in the hall. Where are cards made?'),
 'past_passive':('The match were played yesterday. Prizes was given. Where the match was played?','The match was played yesterday. Prizes were given. Where was the match played?'),
 'zero':('If a visitor need help, the receptionist offers a form. If I do not understand, I asked. If visitors arrive early, they waited.','If a visitor needs help, the receptionist offers a form. If I do not understand, I ask. If visitors arrive early, they wait.'),
 'past_perfect':('Alex has prepared the form before the visit began. The nurse had reading it. Did Alex prepared it before the visit?','Alex had prepared the form before the visit began. The nurse had read it. Had Alex prepared it before the visit?'),
 'degree':('The plot is enough simple. The screen is small too to read. The subtitles are enough clear.','The plot is quite simple. The screen is too small to read. The subtitles are clear enough.'),
 'comparison':('This film is more interesting as that one. This play is as long than that film. These tickets cost the same than those tickets.','This film is more interesting than that one. This play is as long as that film. These tickets cost the same as those tickets.'),
 'determiners':('Both visitor gets a leaflet. Each attractions are open. Are there some tickets left?','Each visitor gets a leaflet. Both attractions are open. Are there any tickets left?'),
 'conjunctions':('Both the castle or the museum are open. Choose either the short route and the long route. I choose this route but it includes a quiet stop.','Both the castle and the museum are open. Choose either the short route or the long route. I choose this route because it includes a quiet stop.')}
 gid=next(k for k,v in GRAMMAR.items() if v is g);bad,fixed=wrong[gid]
 admin=f'''# Урок {n:03d} · 7 клас · {l['date']}

**Тема календарного плану:** {l['topic']}  
**Рік:** 2026/2027. **Семестр:** {l['semester']}. **Статус дати:** {l['calendar_status']}.  
**Тип / пріоритет:** {l['kind']} / {skill}. **Тематичне джерело каталогу:** {section}.  
**Це проєкт підготовки, а не запис про фактичне проведення.** Після уроку заповнити [report.md](report.md).

## План для адміністрації

- Мовна мета: у темі «{b['title']}» зрозуміти 3 конкретні факти, використати 4 тематичні слова та створити короткий продукт; пріоритет цього уроку — {skill}.
- Доказ досягнення: {core}. Критерій успіху: 2 з 3 фактів або 3 з 4 контрольованих виборів; у відкритому продукті є адресат/мета, тематичний зміст і зрозуміла модель.
- Комунікативна функція вихідного плану: {l.get('communicative_functions','Запитує, уточнює, пояснює вибір.').removeprefix('y ')}.
- Орієнтир плану: {l.get('expected_learning_evidence','Надає інформацію за темою.')}. Зміст адаптовано до власних мікротекстів; матеріал не оголошується дослівним відтворенням SB/WB.
- Компетентності НУШ: іншомовна комунікація (запит і відповідь із доказом); навчання впродовж життя (перевірка й наступний крок); громадянська та соціальна (повага до іншого вибору, черга реплік). Нормативні коди не приписано.
- Авторська SEL-адаптація у дусі «Зерна»: вибір «сам / пара / письмово / пропускаю публічну репліку», уважне уточнення, відгук про дію. Це не офіційна вправа програми «Зерна». Емоції, камера та особисті розповіді не є об’єктом оцінювання.
- Матеріали: друк [handout.md](handout.md), олівець, [key.md](key.md) лише в учителя; годинник за наявності. Паперова копія в класній резервній папці ДО відключення. Інтернет і підручник для вправ не потрібні.
- Маршрут A — 45 хв; B — 15 хв після прибуття й дозволу; C — 45 хв дистанційно; D — 12 хв на папері. Скорочення часу не дорівнює повному виконанню плану.

## Опорний конспект учителя

**Ситуація уроку / основний текст R:** {r['text']}

**Робоча лексика (звужене посильне ядро):**

{lex_table}

**Лексичний орієнтир оригінального плану:** {l.get('language_inventory',{}).get('lexis','')}. У цьому авторському пакеті відпрацьовуємо ядро вище; додаткові слова підручника не перевіряємо без окремого введення.

**Модель:** {g['model']}  
**Правило:** {g['rule']}  
**Мовні опори взаємодії:** Where…? When…? Could you repeat that, please? I suggest… because… I see your point. Can I write my answer?  
**Приклад кінцевого продукту:** {product_model}  
**Типова помилка й корекція:** «{bad}» → «{fixed}». Запитати: «Яке слово показує час / кількість / зв’язок думок?» Дати час виправити, не називати учня «неуважним».

## Протокол переривання та повернення

За сигналу: «Зупиняємо завдання, діємо за правилами школи». При переміщенні не проводити урок, не просити відповіді/фото/читання, не затримувати маршрут заради аркуша. B починається лише ПІСЛЯ прибуття, перевірки присутності й дозволу відповідального дорослого, якщо можна безпечно сидіти та читати. У тісному шумному укритті немає руханок, аудіо чи особистих історій. Якщо умов немає — навчання переносимо; D виконується пізніше у безпечних умовах, не в темряві та не під час руху. При новому сигналі зупинити й B.

Залишити на аркуші, якщо це не затримує безпеку, код останнього завершеного завдання: V / R / G / L / P. Місток наступної зустрічі: 0–2 хв «Знайди останній код»; 2–4 хв одна модель і одна відповідь із попереднього; 4–6 хв завершити мінімум, далі перейти до плану. Не починати весь 45-хвилинний урок заново; перенести решту та зафіксувати у звіті. Втрату зв’язку не трактувати автоматично як відмову навчатися.

'''
 core_actions={
 'reading':('«Прочитай R мовчки; знайди місце, час і предмет. Підкресли 3 докази». Не перекладати весь текст замість учня.','Учні заповнюють R1–R3, поруч із відповіддю записують 2–4 слова-докази.'),
 'vocabulary':('«Закрий український стовпчик. Зістав V1–V4; потім знайди в R два слова з нашої теми».','Учні дають 4 відповідності, складають 2 власні словосполучення й перевіряють за словником.'),
 'grammar':('«Виконай G1–G4. Покажи часовий маркер або слово, що керує вибором; поясни один вибір».','Учні записують 4 форми й коротке пояснення до однієї; порівнюють з моделлю.'),
 'listening':('«Закрий додаток L. Спочатку слухай заради загальної ситуації, вдруге — місця, часу, предмета». Прочитати L з key.md двічі, між читаннями пауза 45 секунд.','Після першого читання учні записують тему одним словом; після другого — L1–L3, позначають непевну відповідь знаком ?.'),
 'speaking':('«Підготуй одне запитання Where/When і одне Could you repeat…? Спочатку A, потім B. Можна записати репліку до вимови».','Учні проводять діалог S, обмінюються ролями; учитель фіксує, чи є запит, уточнення та відповідь.'),
 'writing':('«Прочитай умову P; виділи адресата, мету, обов’язкові деталі. Склади план із трьох пунктів».','Учні записують план: початок → факти → завершення; створюють перші 2 речення.'),
 'project':('«Домовтеся про продукт: односторінкова картка. Оберіть ролі: автор тексту, перевіряльник фактів або редактор; можна працювати самому».','Учні створюють чернетку P з назвою, 3 фактами й тематичними моделями; підписують ролі без особистих даних.'),
 'review':('«V і G спочатку без моделі, потім перевірка іншим кольором. Мета — знайти, що треба повторити».','Учні виконують V1–V4 та G1–G4, позначають дві зміни, пояснюють одну.'),
 'portfolio':('«У F є три помилки. Спочатку виправ їх самостійно, потім зістав із моделлю й поясни 2 зміни».','Учні роблять версію «після», стрілками показують зміни та пишуть правило до двох.'),
 }
 if not assessed:
  ca,ua=core_actions[mode]
  rows=[('0–3 хв','«Працюємо з вигаданими героями. Можна самостійно, у парі чи письмово. Покажи готовність аркушем або просто почни». Перевірити безпечні умови.','Учні обирають спосіб участі; записують номер уроку. Особистий емоційний звіт не потрібний.'),
 ('3–7 хв','«Знайди в словнику 4 потрібні слова. Назви або запиши одне слово та його значення».','V1–V4 як проба; невідоме позначають ?, отримують підтримку.'),
 ('7–12 хв',f'На дошці/аркуші модель: «{g["model"]}». «Що змінює зміст?». Показати правило, дати один власний приклад.',f'Учні підкреслюють опору в моделі; за зразком пишуть одне речення про {c["item"]}.'),
 ('12–20 хв',ca,ua),
 ('20–28 хв','«Перевірмо модель у G. Після власної відповіді звірся з партнером/учителем; до F повертаємося для редагування».', 'G1–G4; у граматичному/повторювальному уроці — F і пояснення; в інших — одна виправлена форма та 3 короткі відповіді R.'),
 ('28–37 хв','«Тепер P: '+task.replace('|','/')+'»','Учні створюють P; у говорінні — 6 реплік S і коротка письмова картка; у проєкті — чернетка з 2 позначеними змінами.'),
 ('37–42 хв','«Відгук стосується тексту: одна зрозуміла деталь і одне уточнення. Перевірте місце/час, 2 мовні моделі, ввічливість».','Учні редагують одну фразу. Можна самоперевірка без обміну роботою. Учитель вибірково читає 2–3 продукти.'),
 ('42–45 хв','«Напиши exit: один факт + одна модель + що перевіриш наступного разу». Оголосити паперове ДЗ.','Учні здають/залишають exit і позначають останній виконаний код. Учитель записує, що потребує повернення.')]
 else:
  if lr:
   rows=[('0–4 хв','«Це окремі докази слухання й читання. Перевір, чи чутно. При перериванні зупиняємо контроль». Прибрати додаток L; не показувати модель.','Учні читають лише запитання L1–L3; повідомляють про технічну/мовну потребу без обговорення здоров’я.'),('4–7 хв','Один раз прочитати L з key.md природно й чітко; не підказувати відповіді.','Учні записують тему та чернеткові відповіді.'),('7–10 хв','Дати тиху паузу для відповідей; прочитати L вдруге.','Учні уточнюють L1–L3.'),('10–15 хв','«Перевір, що кожна відповідь відповідає на своє запитання». Зібрати блок L.','Самостійні L1–L3 здано; текст L не відкрито до збору.'),('15–20 хв','«Переходимо до R. Прочитай текст один раз заради змісту».','Учні читають R, підкреслюють факти.'),('20–32 хв','«Дай R1–R3; поруч випиши 2–4 слова-докази».','Самостійні три відповіді з підтвердженням.'),('32–40 хв','«Перевір відповіді за текстом. Не змінюй L після його здавання».','Учні виправляють лише власний блок R, здають.'),('40–45 хв','«Яку стратегію використаєш ще раз?» Прийняти відповідь без оцінювання емоцій; призначити відновлення за потреби.','Окремий короткий коментар про спосіб роботи; учитель фіксує L/R та умови.')]
  elif sw:
   rows=[('0–4 хв','Пояснити критерії S і P. «Камера й емоції не оцінюються; усний продукт можна надати індивідуально». Не показувати зразок відповіді.','Учні читають картку S/P, обирають вигаданого героя.'),('4–10 хв','Дати тиху підготовку: 6 ключових слів, без готового сценарію вчителя.','План діалогу й письмового продукту.'),('10–24 хв','Слухати пари або індивідуальні 45–60-секундні фрагменти, іншим — почати P. Якщо клас великий, зібрати лише посильну частину усних свідчень і призначити продовження.','S: 6 реплік з двома запитаннями й уточненням; решта працює над P. Не приписувати невислуханим учням результат говоріння.'),('24–36 хв','«Заверши P самостійно: 5–6 речень за умовою».','Письмовий продукт P із тематичними фактами та моделлю.'),('36–41 хв','«Перевір зміст, порядок слів і зрозумілість адресату».','Власне редагування; учні здають P.'),('41–45 хв','Зібрати роботи; записати, чиї усні фрагменти ще потрібні, домовитися про безпечний канал продовження.','Фіксуються окремо наявний доказ письма та наявний/відкладений доказ говоріння.')]
  else:
   rows=[('0–4 хв','Пояснити 4 блоки L/R/S/P та порядок; прибрати додаток L. «Це пошук наступного кроку; при перериванні переносимо незавершені блоки».','Учні читають L1–L3, готують аркуш.'),('4–10 хв','Прочитати L двічі з паузою 45 секунд; зібрати L.','3 відповіді слухання.'),('10–19 хв','«Прочитай R з попереднього юніту; знайди 3 факти».','R1–R3 самостійно, з підкресленими доказами.'),('19–29 хв','«S: партнер ставить Where/When та уточнює; поміняйтеся ролями». Слухати доступну кількість коротких фрагментів.','6 реплік; учитель фіксує тільки реально почуті зразки, решту S переносить.'),('29–39 хв','«P: створи короткий тематичний продукт самостійно».','5–6 речень за умовою P.'),('39–45 хв','Зібрати блоки; попросити позначити незавершене; пояснити індивідуальний наступний крок.','Наявні L/R/S/P зафіксовано окремо; незавершене не вигадується й не карається автоматично.')]
 admin+='## A · Клас, 45 хв\n\n'+table(rows)
 bcore='G1–G2 + одне речення P' if mode=='grammar' else 'R1–R2 + одне речення P'
 admin+='''\n## B · Укриття, 15 хв ПІСЛЯ переміщення

Лише якщо є дозвіл, місце безпечне й достатньо світла для паперу. Коли ці умови не виконано, цей маршрут не проводиться. Слухання замінене читанням і не є доказом аудіювання; контроль не оголошується завершеним.

'''+table([
 ('0–2 хв','«Можна тихо працювати на папері або відкласти. Особисте розповідати не потрібно». Показати словник і рядок моделі.','Учні, які мають умови, знаходять R і G; інші залишають аркуш до безпечного часу.'),
 ('2–5 хв','«Прочитай R; підкресли місце й час. Запиши ключові слова».','Два підкреслені фрагменти; R1–R2 або підготовка до G1–G2.'),
 ('5–9 хв','«Мінімум сьогодні: '+bcore+'. Користуйся словником; запиши без озвучування».','Самостійні 2 короткі відповіді; у контролі — тільки тренувальний чернетковий продукт, новий контроль пізніше.'),
 ('9–12 хв','На аркуші вказати: «Одне речення за моделлю про героя тексту». Не організовувати переміщень чи гучних пар.','Учні пишуть одне речення P; можна обрати готовий початок із моделі.'),
 ('12–15 хв','«Познач V/R/G/P, що встиг. Решту продовжимо після відновлення умов». Тихо перевірити 1 відповідь індивідуально за можливості.','Аркуш зі слідом роботи й позначеним незавершеним; учитель переносить решту без нового завдання у момент руху.')])
 if assessed:
  onlinecore='L і R за специфікацією A; L лише за наявного чутного голосу вчителя. S — індивідуально голосом без камери; P — приватним текстом. Не показувати модель і ключі до збору.'
 else:onlinecore=core
 admin+='''\n## C · Дистанційно, 45 хв; камера добровільна

До уроку передати паперовий пакет або короткий текст доступним каналом. «+», приватний чат, один рядок чи робота на папері — способи входу. Після втрати зв’язку перехід на D; пізня відповідь приймається до наступної доступної зустрічі. Камера, швидкість мережі й відсутність відповіді без з’ясування умов не є оцінкою знань. Діалог у чаті тренує взаємодію, але не підтверджує усне мовлення: для S учитель пізніше слухає короткий голосовий/живий зразок без камери.

'''+table([
 ('0–4 хв','«Камера за бажанням. У чаті напиши номер уроку або почни на папері; можна приватно. Якщо немає зв’язку — D з роздатки».','Продукт входу: номер уроку / перший рядок на папері; учитель звіряє доступність.'),
 ('4–9 хв','Надіслати словник і модель звичайним текстом; у контролі — лише інструкцію та критерії, модель закрити. «Назви 2 слова або перечитай їх мовчки».','У навчальному уроці — 2 слова з перекладом; у контролі — готовність до потрібного блоку.'),
 ('9–17 хв','«Основний блок: '+onlinecore.replace('|','/')+'». Для слухання прочитати L двічі без вимоги відео; якщо не чути, блок L перенести.','Чат-продукт 1: нумеровані відповіді R/G/V або L. При слуховому збої — читання з позначкою R, не L.'),
 ('17–24 хв','«Познач одну непевну відповідь знаком ?. Поясни вибір одним словом-доказом». У контролі пояснення тільки після здавання відповідного блоку.','Чат-продукт 2: відповідь + доказ; за відсутності каналу — запис на папері.'),
 ('24–34 хв','«Виконай P: '+task.replace('|','/')+'» Для S слухати короткі фрагменти без камери; решті дозволити писати.','Чат-продукт 3: 5–6 речень / 6 реплік. Усний результат позначається тільки після реального прослуховування.'),
 ('34–41 хв','«Перечитай критерії, уточни 1 деталь і виправ 1 форму». Відгук приватно; під час контролю — власне редагування.','Чат-продукт 4: виправлений рядок і причина; при мережевій паузі — дві версії на папері.'),
 ('41–45 хв','«Exit: один факт, одна модель, наступна мовна перевірка». Підтвердити приймання; не чекати фото негайно.','Exit у чаті/на папері; відкладені продукти учитель приймає при наступному доступному контакті.')])
 admin+='''\n## D · Асинхронно на папері, 12 хв без електрики

Виконувати лише пізніше в безпечному, достатньо освітленому місці. Якщо пакет не був переданий — видати його після відновлення зв’язку, не вимагати завантаження. Для контрольного уроку це тренування й місток; остаточний контроль перенести, аудіювання/говоріння не підміняти читанням/письмом.

'''+table([
 ('0–2 хв','Друкована репліка: «Прочитай словник і правило. Вибери 2 знайомі слова».','Учень підкреслює 2 слова; не шукає відео/підручник.'),
 ('2–5 хв','Друкована репліка: «Прочитай R. Запиши місце й час».','R1–R2 на папері.'),
 ('5–8 хв','Друкована репліка: «Виконай G1–G2 з моделлю. Покажи допоміжне слово».','2 форми, підкреслене слово-підказка.'),
 ('8–11 хв','Друкована репліка: «Напиши 2 речення P про вигаданого героя: факт і свою пропозицію».','2 тематичні речення, за потреби з початком моделі.'),
 ('11–12 хв','Друкована репліка: «Познач останній код, одне ? і збережи аркуш до наступної зустрічі».','Наявний слід роботи без фото/надсилання; учитель пізніше дає короткий зворотний зв’язок.')])
 admin+='''\n## Диференціація, зворотний зв’язок, домашня робота

- Підтримка: дати вибір із двох форм G, дозволити словник і відповідь ключовими словами R; для P 3 речення замість 6. Учень може писати обидві ролі S перед усним зразком. Не вимагати пояснювати особисту причину потреби.
- Базовий рівень: 3 факти R/L, 4 форми G, 5–6 речень або 6 реплік за тематичною умовою.
- Поглиблення: додати запитання Wh-, перефразувати один факт і обґрунтувати вибір because; перевірити текст на 2 моделі. Без додаткового пошуку в мережі.
- Формувальна репліка: «Місце і час зрозумілі. Перевір допоміжне дієслово в другому реченні». Оцінювати реальну мовну дію; підтримка й рівень самостійності фіксуються окремо.
- Паперове ДЗ (5–7 хв): переписати власний P у чистовому варіанті (підтримка — 3 речення, базово — 5–6), підкреслити 2 тематичні слова, позначити одну виправлену форму та створити 1 запитання Where/When за R. Після B/D — лише завершити ці 2 речення й 1 запитання, не накопичувати весь пропущений обсяг.
- Для контрольного уроку: ДЗ — рефлексія стратегії без переписування відповідей як нового контролю; незавершені перевірки проводити окремо у доступних умовах. Домашні письмові відповіді не підтверджують слухання/говоріння.

'''
 if assessed:
  bstart=admin.index('## B ·');bend=admin.index('## C ·',bstart)
  basic='R1–R2' if lr or diag else 'план S (місце, час, два запити)'
  short_b='''## B · Укриття, 15 хв після переміщення

Контроль зупинено. Лише після прибуття, дозволу дорослого й за умов читання можна тихо виконати підготовчий місток. Інакше перенести все. Без руху/аудіо/особистих розповідей. Усних і слухових результатів тут не записуємо.

'''+table([('0–2 хв','«Контроль продовжимо в належних умовах; зараз можна лише підготовку».','Учні, які мають умови, знаходять паперову інструкцію.'),('2–5 хв','«Прочитай коротку історію або умову ролі; підкресли 2 деталі».','Дві позначені деталі.'),('5–9 хв','«Запиши: '+basic+'».','Два ключові факти / план реплік на папері.'),('9–12 хв','«Напиши 2 тематичні речення про вигаданого героя».','Підготовчий текст, який не зараховується як самостійний контроль.'),('12–15 хв','«Познач завершене й збережи аркуш. Новий варіант перевірки буде окремо».','Позначені відкладені блоки, без публічного обговорення.')])
  admin=admin[:bstart]+short_b+'\n'+admin[bend:]
  dstart=admin.index('## D ·');dend=admin.index('## Диференціація',dstart)
  short_d='''## D · Асинхронно, 12 хв на папері

Лише у безпечному місці з достатнім світлом; це підготовка, не завершений контроль. 0–2 хв: прочитай інструкцію. 2–5 хв: знайди 2 факти у R або сплануй 2 репліки S. 5–9 хв: напиши 2 тематичні речення. 9–12 хв: познач питання до вчителя й збережи аркуш до доступного контакту. Інтернет, фото й підручник не потрібні. Аудіювання/говоріння переносимо; за небезпечних умов не виконуємо завдання. Для самостійної перевірки після повернення застосувати резерв із ключа, не знайомий розібраний текст.

'''
  admin=admin[:dstart]+short_d+admin[dend:]
  if lr:spec='L1–L3: 3 бали за 3 правильні факти; R1–R3: 3 бали за 3 факти з опорою на текст. Разом 6 первинних балів, окремі результати L /3 і R /3. Доказова цитата допомагає зворотному зв’язку, за її відсутність не знімати вдруге бал за вже правильний факт.'
  elif sw:spec='S: 0–2 за виконання ролі/запитів, 0–2 за зрозумілість, 0–2 за відповідь/уточнення = /6. P: 0–2 за зміст, 0–2 за зв’язність, 0–2 за мовну зрозумілість = /6. Разом /12 первинних балів, S і P зберігати окремо.'
  else:spec='L /3 і R /3: по 1 за кожний правильний факт. S /3: по 1 за запит, змістовну відповідь, ввічливе уточнення. P /3: по 1 за відповідність темі, 3 факти, зрозумілі речення. Разом /12 первинних балів; зберігати 4 окремі профілі.'
  admin+='## Специфікація діагностики / контролю\n\n'+spec+' Це авторська рубрика первинних балів, не автоматичне переведення у шкільну оцінку. Для офіційного запису застосувати затверджену в закладі процедуру. V/G/F — резерв для корекції після збору робіт, не додаткові приховані контрольні бали. Модель і словник закрити під час самостійного етапу, крім заздалегідь погоджених адаптацій; умови підтримки записати. Текст L тримати у вчителя; паперовий додаток учня відділити до перевірки. За переривання зберегти завершений блок, решту перенести на рівноцінний варіант; не зараховувати B/D як повний контроль.\n\n'
 else:spec='Формувально: V /4, R /3, G /4, L /3 — окремі свідчення, не сума в офіційну оцінку. Відкритий продукт: зміст, організація, зрозумілість — по 0–2; див. ключ.'
 handout=f'''# 7 клас · Урок {n:03d} · {l['date']}

**Тема:** {l['topic']}  
Код учня/позначка: ____________________  Дата виконання: ______________

Усі персонажі й події вигадані. Можна писати про героя; особисті історії не потрібні. Обери спосіб: сам / пара / письмово. Якщо умови небезпечні — зупини роботу й виконуй вказівки дорослих. Дорогою до укриття завдань не виконуємо.

**Мінімум без мережі (12 хв у безпечному місці зі світлом):** 0–2 словник; 2–5 R1–R2; 5–8 G1–G2; 8–11 два речення P; 11–12 познач «завершено/продовжити». В укритті лише після дозволу; не потрібно читати вголос.

## Словник для навчання

{lex_table}

## V · Зістав слова й значення

{match}

Мої 2 словосполучення: ____________________________ / ____________________________

## R · Прочитай авторську історію

{r['text']}

{questions(rquestion)}

Підкресли в тексті слова-докази. Тема історії одним словом: ____________________

## G · Модель і мовний вибір

**Правило для навчального режиму:** {g['rule']}  
**Модель:** {g['model']}

{practice(g)}

Поясни один вибір: __________________________________________________________

## L · Слухання: запитання

Учитель читає текст двічі; додаток у кінці закрий/відділи ДО слухання. Спочатку визнач ситуацію, потім запиши факти. Якщо голосу не чути, повідом учителю; читання не позначається як аудіювання.

{questions(aquest)}

## S · Картка діалогу

A: запропонуй тематичну подію/дію за R або власним вигаданим прикладом, назви місце й час.  
B: запитай Where…? та When…?, попроси повторити деталь, запропонуй одну зміну.  
A: дай відповідь і поясни вибір because…  
Потім поміняйтеся ролями. При самостійній роботі запиши обидві ролі; усний зразок надай пізніше, коли можливо.

A: ______________________________________________________________________

B: ______________________________________________________________________

A: ______________________________________________________________________

B: ______________________________________________________________________

A: ______________________________________________________________________

B: ______________________________________________________________________

## P · Твій тематичний продукт

{task}

Опори для навчання: I suggest… / It is in… / It starts at… / because… / Could you repeat…? У контрольному режимі вчитель відділяє модель/словник до самостійної роботи.

План (3 слова): __________________ / __________________ / __________________

1. ______________________________________________________________________

2. ______________________________________________________________________

3. ______________________________________________________________________

4. ______________________________________________________________________

5. ______________________________________________________________________

6. ______________________________________________________________________

У проєкті — чернетка вище; 2 зміни до чистового варіанта:

Зміна 1: __________________________________________________________________

Зміна 2: __________________________________________________________________

## F · Редагування й портфоліо

У чернетці 3 неточності. Виправ їх і поясни 2 зміни. Для портфоліо збережи обидві версії.

{bad}

Моя версія: ________________________________________________________________

___________________________________________________________________________

Чому змінив/змінила: _______________________________________________________

Наступного разу перевірю (мовна дія): _______________________________________

## Exit і паперове ДЗ

Один факт: ________________________________________________________________

Одна мовна модель: _________________________________________________________

Останній завершений код V / R / G / L / S / P / F: ______  Потрібно уточнити: ______

ДЗ 5–7 хв: чистовий P (підтримка 3 речення; базово 5–6), 2 підкреслені тематичні слова, 1 виправлена форма, 1 Where/When-запитання до R. Після скороченого уроку — тільки 2 речення і 1 запитання. Після контролю — лише навчальна рефлексія; незавершений контроль узгоджуємо окремо.

## Додаток L · Відділити або зігнути до слухання

Для самостійного навчання весь текст доступний на папері. Для перевірки слухання вчитель відділяє цей додаток і читає його зі своєї копії. Самостійне читання цього тексту є практикою читання, а не результатом слухання.

{a['text']}

'''
 if assessed:
  # In assessment mode, remove examples and grammar drills from the learner's test.
  blocks=[]
  if lr or diag:
   blocks += [f'''## L · Слухання /3

Учитель читає двічі. Додаток L в кінці вчитель відділяє ДО перевірки. Якщо голосу не чути, цей блок переноситься. Читання додатка не є результатом слухання.

{questions(aquest)}

## R · Читання /3

{r['text']}

{questions(rquestion)}

Підкресли у тексті слова-докази до відповідей.

''']
  if sw or diag:
   blocks += [f'''## S · Усна взаємодія /{'6' if sw else '3'}

Роль A: запропонуй вигадану тематичну подію/дію «{b['title']}», назви місце, час і мету. Роль B: постав 2 запитання (про місце та час), попроси уточнити одну деталь, запропонуй зміну. A відповідає й дає причину. Поміняйтеся ролями. Підготовка на папері дозволена; зразок має бути реально почутий учителем. Письмовий діалог готує до говоріння, але не замінює усний доказ. Камера добровільна.

План — ключові слова, не готовий текст: _____________________________________

___________________________________________________________________________

## P · Письмо /{'6' if sw else '3'}

{task}

План: __________________ / __________________ / __________________

1. ______________________________________________________________________

2. ______________________________________________________________________

3. ______________________________________________________________________

4. ______________________________________________________________________

5. ______________________________________________________________________

6. ______________________________________________________________________

''']
  handout=f'''# 7 клас · Урок {n:03d} · Самостійна перевірка

**Тема:** {l['topic']}  
Код учня: ____________________  Фактична дата: ____________________

Виконуй лише зазначені нижче блоки. Усі ситуації вигадані; особисті відомості не потрібні. Умови допомоги узгоджуються до початку. За тривоги припини роботу та виконуй вказівки дорослого; незавершене переноситься. У B/D це тренувальний місток, контроль продовжується окремо. Камера не оцінюється.

**Критерії:** {spec}

'''+''.join(blocks)+f'''## Після здавання роботи

Що допомогло знайти факт / побудувати репліку: _______________________________

Що потрібно уточнити наступного разу: _______________________________________

Незавершений блок: __________________ Причина/умови за бажанням: ____________

Для паперового мосту D у безпечному місці зі світлом (12 хв): 0–2 прочитай інструкцію, 2–5 знайди 2 факти у R або сплануй 2 репліки S, 5–9 запиши 2 тематичні речення, 9–12 познач запитання й збережи аркуш. Це підготовка, не підсумковий результат L/S. Завдання не виконуємо під час переміщення або за відсутності умов.

## Додаток L — ВІДДІЛИТИ ДО ПЕРЕВІРКИ

Учитель залишає цю частину собі й читає двічі. Для пізнішого самостійного навчання текст доступний тут повністю. Його самостійне читання — доказ R, а не L. Якщо урок перевіряє лише S/P, це необов’язковий текст для корекції після здавання.

{a['text']}

'''
 key=f'''# Ключі · 7 клас · Урок {n:03d}

Лише для вчителя; не роздавати разом з учнівським аркушем. Переклад/синонімічна коротка відповідь прийнятні для розуміння, якщо факт точний; мовну форму коментувати окремо. Орфографічну помилку, що не змінює факту, не карати вдруге.

## V

{match_key}. По 1 за точну відповідність; /4. Власні словосполучення: прийняти осмислену сполуку з тематичним словом, зразок контекстного вживання — у моделі P нижче; за потреби виправити лексичну сполучуваність; ці 2 приклади не додають прихованих балів.

## R

'''+ '\n'.join(f'{i}. {answer.rstrip(chr(46))}.' for i,(_,answer) in enumerate(rquestion,1))+f'''

По 1 за факт; /3. Можна відповісти коротко; докази — відповідні речення тексту про місце, час і предмет/подію.

## G

'''+ '\n'.join(f'{i}. {answer.rstrip(chr(46))}.' for i,(_,answer) in enumerate(g['items'],1))+f'''

По 1 за правильну форму; /4. Пояснення: {g['rule']}

## L · Сценарій читання вчителем

Закрити/відділити додаток L в учнів. Прочитати двічі чітко, без театральних рухів та звукових ефектів, з паузою 45 секунд. Не наголошувати тільки правильні слова й не підказувати жестами.

{a['text']}

**Відповіді:**

'''+ '\n'.join(f'{i}. {answer.rstrip(chr(46))}.' for i,(_,answer) in enumerate(aquest,1))+f'''

По 1 за факт; /3. При поганій чутності перенести L; текстове читання позначити R, не L.

## S · Зразок діалогу

A: Let us meet at {r['place']}.
B: When shall we meet?
A: {r['time']}.
B: Could you repeat the place, please?
A: {r['place']}. I suggest preparing {r['item']} because it fits our topic.
B: Thank you. Can we write a short plan first?

Це один можливий варіант, не текст для обов’язкового заучування. Додатковий запит Where shall we meet? прийнятний. Оцінити, чи співрозмовник справді отримав відповідь; письмовий сценарій сам собою не доводить говоріння.

## P · Зразок та критерії

{product_model}

Факти власної вигаданої події можуть відрізнятися від R, якщо завдання не вимагає перенесення саме фактів R. Для завдання читання з додатковими 2 фактами перевірити їх за R: **{r['place']}; {r['time']}; {r['item']}**. У проєкті перевірити назву, читабельні 3 факти, чернетку й 2 зміни; у граматичному уроці — дві цільові моделі; у лексичному — 4 слова.

Формувальна рубрика відкритого продукту (кожен вимір 0–2):

- Зміст: 0 — продукт відсутній/поза темою; 1 — мета зрозуміла, але бракує 2 обов’язкових деталей; 2 — є мета, адресат і потрібні тематичні деталі.
- Організація: 0 — не можна відновити послідовність; 1 — послідовність зрозуміла з підтримкою; 2 — логічний початок, факти й завершення / доречна черговість реплік.
- Мовна зрозумілість: 0 — зміст не відновлюється; 1 — помилки є, але основний зміст зрозумілий; 2 — цільові моделі переважно точні, ключові слова доречні.

/6 — первинний навчальний показник, не автоматична офіційна оцінка. У S допускається пауза, паперова підготовка й відсутність камери. Для 6-бальної рубрики S: зміст — виконання ролі/запитів; організація — відповідь/уточнення; мовна зрозумілість — зрозумілий усний зразок. Потрібну допомогу зафіксувати, емоції не оцінювати.

## F

**Виправлена версія:** {fixed}

**Пояснення:** {g['rule']} Прийняти інші граматично коректні виправлення зі збереженим змістом; пояснення двох змін може бути українською. Для портфоліо доказ — «до», «після», дві причини й наступний перевірюваний крок; твердження «я старався» без прикладу попросити конкретизувати.

## Специфікація цього уроку

{spec}

B/D — скорочений місток, не повна перевірка всіх умінь. Не переносити автоматично бал за письмовий чат у результат говоріння; не записувати повне аудіювання, якщо учень читав. За переривання зберегти достовірні блоки, невиконане позначити «перенесено», не нулем за технічну недоступність.

## ДЗ

Приймається будь-який осмислений чистовий текст за тематичною умовою P, 2 тематичні слова й одне запитання з правильною моделлю. Приклади запитання до R: Where does the story take place? When does the event happen? Відповіді: {r['place']}; {r['time']}. Після контрольного уроку перевіряється лише факт навчальної рефлексії; це не новий підсумковий бал.
'''
 report=f'''# Фактичний звіт · 7 клас · запланований урок {n:03d}

Планова дата: {l['date']}  
Тема за планом: {l['topic']}  
Це незаповнений шаблон. Він не засвідчує проведення чи результати.

- Фактична дата / час / тривалість: ______________________________________
- Форма / маршрут A / B / C / D / перенесено: ______________________________
- Умови (без зайвих персональних даних): _________________________________
- Переривання: час, завершений код, що перенесено: ________________________
- Для B: прибуття завершено, дозвіл / умови читання: _______________________
- Реально проведені етапи й використані матеріали: _______________________
- Кількість наданих робіт / відкладених доказів: ___________________________
- Докази R / L / S / P (окремо, лише реально спостережені): ________________
- Результат за критеріями / типові мовні труднощі: _________________________
- Рівень підтримки / адаптації без медичних діагнозів: _____________________
- Авторська SEL-практика / можливість вибору (без оцінок емоцій): ___________
- Наданий зворотний зв’язок: _____________________________________________
- Фактично задана паперова домашня робота: _______________________________
- Невиконаний зміст і дата/спосіб повернення: _____________________________
- Для контролю: завершені блоки / перенесені блоки / умови самостійності: ___
- Наступний навчальний крок: _____________________________________________
- Примітка для журналу після перевірки факту: ____________________________

Не вносити в репозиторій персональні відповіді учнів, оцінки, діагнози, контакти чи приватні посилання. Заповнений облік зберігати в дозволеній закладом системі. План і цей порожній шаблон доступні лише через репозиторій, без посилань у каталозі сайту.
'''
 if assessed:
  reserve=context(u,n,0)
  reserve_r=context(read_u,n,0)
  rq=[('Where does the story take place?',reserve_r['place']),('When does the event or meeting happen?',reserve_r['time']),('What item, activity or document is mentioned?',reserve_r['item'])]
  lq=[('Where does the story take place?',reserve['place']),('When does the event or meeting happen?',reserve['time']),('What item, activity or document is mentioned?',reserve['item'])]
  recovery=f'''# Резерв самостійної перевірки · 7 клас · Урок {n:03d}

Код учня: ____________________ Фактична дата: ____________________

**Тема:** {l['topic']}. Завершені до переривання блоки вдруге не виконуй. Учитель назве тільки відкладені блоки. Усі ситуації вигадані; камеру не вимагаємо. Структура часу й критерії — як у першому варіанті; на поновлення дати 2 хв прочитати інструкцію. Якщо умови знову перервано — зупинити роботу. Моделі/словник не відкривати під час самостійної частини, крім погодженої адаптації.

'''
  if lr or diag:
   recovery+=f'''## L · Слухання /3

Прослухай повідомлення двічі. Додаток L відділяє вчитель до перевірки.

{questions(lq)}

## R · Читання /3

{reserve_r['text']}

{questions(rq)}

'''
  if sw or diag:
   recovery+=f'''## S · Усна взаємодія

Придумайте нову вигадану тематичну подію «{b['title']}» в іншому місці й на годину пізніше, ніж у попередньому вашому діалозі. A пропонує й називає мету; B запитує місце/час, просить уточнення та пропонує зміну; A відповідає з причиною. Поміняйтеся ролями. Шість реплік; учитель має їх реально почути без вимоги камери.

Ключові слова: _____________________________________________________________

## P · Письмо

{b['task']} Використай нові вигадані деталі, відмінні від першої чернетки. 5–6 речень (якщо діалог — 6–8 реплік), самостійно.

___________________________________________________________________________

___________________________________________________________________________

___________________________________________________________________________

___________________________________________________________________________

___________________________________________________________________________

___________________________________________________________________________

'''
  recovery+=f'''## Додаток L — ВІДДІЛИТИ ДО ПЕРЕВІРКИ

Тільки для читання вчителем; текст на папері наданий також для пізнішої самостійної роботи. Після відкриття його читання не є аудіюванням.

{reserve['text']}
'''
  (folder/'recovery-handout.md').write_text(re.sub(r'(?<!\.)\.\.(?!\.)','.',recovery),encoding='utf-8')
  key+='\n## Резерв після переривання — ключ до recovery-handout.md\n\nL: '+ '; '.join(f'{i}. {v.rstrip(chr(46))}' for i,(_,v) in enumerate(lq,1))+'.\n\nR: '+ '; '.join(f'{i}. {v.rstrip(chr(46))}' for i,(_,v) in enumerate(rq,1))+'.\n\nТекст L для двох читань: '+reserve['text']+'\n\nS/P: критерії першого варіанта зберігаються; нові місце, час і деталі є вигаданими, довільними та внутрішньо узгодженими. Для діалогу зсув часу на годину перевіряти відносно попереднього учнівського продукту, а не чужої історії. Якщо зразка попереднього S немає, учень обирає нові деталі без порівняння. Зараховувати тільки відкладені блоки; не підсумовувати два варіанти подвійно.\n'
 for filename,content in [('lesson.md',admin),('handout.md',handout),('key.md',key),('report.md',report)]:
  (folder/filename).write_text(re.sub(r'(?<!\.)\.\.(?!\.)','.',content),encoding='utf-8')
 return dict(number=n,date=l['date'],topic=l['topic'],directory=f'{n:03d}',source_id=l['source_id'],kind=l['kind'],focus=mode,semester=l['semester'],calendar_status=l['calendar_status'])

def main():
 source=json.loads((BASE/'source-plan.json').read_text(encoding='utf-8'))
 assert len(source['lessons'])==140
 assert [x['number'] for x in source['lessons']]==list(range(1,141))
 rows=[build(l) for l in source['lessons']]
 manifest={'grade':7,'academic_year':source['academic_year'],'lessons':rows}
 (BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 readme='''# Службова папка вчителя · 7 клас · 2026/2027

Повне календарне покриття: **140 уроків**, 65 у I семестрі та 75 у II. Номери/дати/теми з очищеного [source-plan.json](source-plan.json), походження та SHA-256 зазначено там. Це підготовка й порожні шаблони звіту; фактичне проведення не підтверджується. Дати II семестру у вихідному плані — проєкція. Тематичні розділи зіставлено з `7/lessons.json` без копіювання приватних URL і журналів.

Для контрольних уроків додано `recovery-handout.md`: рівноцінний резерв відкладених блоків після переривання, ключ у кінці `key.md`. Відділяйте додаток L до самостійної роботи.\n\nУ кожній папці: `lesson.md` (адміністративний план, опорний конспект, A 45 хв / B 15 хв / C 45 хв / D 12 хв, диференціація, ДЗ), `handout.md` (самодостатній паперовий учнівський аркуш), `key.md` (відповіді, сценарій слухання, зразки й критерії), `report.md` (порожній фактичний звіт). `handout.pdf` — для друку учням, `teacher.pdf` — план + ключі + звіт для вчителя. Генератор Markdown: `python3 scripts/build_teacher_grade7.py`, лише стандартна бібліотека та збережене очищене джерело; локальні підручники не потрібні.

Матеріали авторські, адаптовані до тем і функцій плану; це не копії сторінок SB/WB та не офіційні вправи «Зерна». Робочий словник свідомо звужений; повний лексичний орієнтир джерела наведено в конспекті для подальшого введення. Навчальні критерії не вигадують нормативні коди чи офіційне переведення первинних балів у шкільну оцінку.

Сигнал тривоги зупиняє навчання; під час переміщення завдань немає. B дозволений лише після прибуття, перевірки присутності й дозволу дорослого, за наявних умов читання. У тісному шумному укритті без руханок/аудіо/особистих розповідей; якщо умов немає — перенести. D виконується пізніше у безпечному місці зі світлом. Камера добровільна; чат підтверджує письмову участь, усне мовлення потребує реально почутого зразка. Письмо/читання не підміняють говоріння/слухання у звіті. Для контролю додаток L і мовні моделі в учнів відділяють до самостійної частини; за переривання контроль продовжується окремо.

Не публікувати ці файли у вебкаталозі. Публічний репозиторій сам по собі не забезпечує конфіденційність; сюди не додавати заповнені персональні звіти. Паперовий пакет слід видати ДО очікуваних відключень.

## Покриття календаря

| № | Дата | Тема | План | Друк учня | Вчитель |
|---|---|---|---|---|---|
'''
 for x in rows:
  d=x['directory'];readme+=f"| {x['number']} | {x['date']} | {x['topic']} | [MD]({d}/lesson.md) | [MD]({d}/handout.md) · [PDF]({d}/handout.pdf) | [Ключ]({d}/key.md) · [Звіт]({d}/report.md) · [PDF]({d}/teacher.pdf) |\n"
 (BASE/'README.md').write_text(readme,encoding='utf-8')
 print(f'Built {len(rows)} grade-7 packs in {BASE}')

if __name__=='__main__':main()
