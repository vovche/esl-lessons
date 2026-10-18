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
91:'The fictional form uses the phrase suffer from pain and the word chest. Another card shows an X-ray and the word injection. A nurse asks one question at a time. The exercise describes language, not medical treatment.',
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

ERRORS={'present':('Alex usually read in the club. Today Alex making a poster. Where Alex reads?','Alex usually reads in the club. Today Alex is making a poster. Where does Alex read?'),
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

# Curated texts correspond to individual calendar outcomes, not just the unit name.
# Every closed comprehension answer is an exact phrase in the supplied text.
def passage(text,*qas):
 return {'text':text,'qas':[{'question':q,'answer':a,'evidence':a} for q,a in qas]}

READING={
1:passage('A new study group has three rules. Ask a clear question when a task is difficult. Take turns so that everyone can contribute. Never tease someone who needs more time. Students can write instead of speaking to the whole class. The first task is to make a short word list together.',('What should a learner ask when a task is difficult?','a clear question'),('Why should members take turns?','so that everyone can contribute'),('What can a student do instead of speaking?','write')),
2:passage('Mia writes a school blog: I collect stones in the science club. We compare their colours and make labels. Leo replies: I play the guitar in a band. We practise quietly before our concert. Neither club requires an expensive project. New members can borrow materials and choose a small first task.',('What does Mia collect?','stones'),('What does Leo play?','the guitar'),('How can new members get materials?','borrow materials')),
3:passage('Robin likes reading, but does not want to act on stage. The library club needs someone to recommend books. The drama club needs someone to design posters. Robin asks whether a quiet role is possible. Both clubs say yes. Robin chooses the library club because recommending books fits this hobby.',('What does the library club need?','someone to recommend books'),('Which club does Robin choose?','the library club'),('Why does that choice fit?','recommending books fits this hobby')),
5:passage('Our fictional school is celebrating its anniversary. Students have prepared an exhibition about the school. One group has collected old photographs; another has written short captions. Visitors can compare the classrooms in the pictures with the rooms today. No student has to give a public speech. A caption is also a useful contribution.',('What have students prepared?','an exhibition'),('What has one group collected?','old photographs'),('What is an alternative to a public speech?','A caption')),
6:passage('School A holds a concert for its anniversary. Students practise songs and make decorations. School B holds a book exhibition instead. Students write recommendations and arrange the books. Both schools invite visitors and offer quiet jobs. A fictional pupil can compare the two celebrations without describing a real family or school.',('What does School A hold?','a concert'),('What does School B hold?','a book exhibition'),('What do both schools offer?','quiet jobs')),
18:passage('Alex: I washed up yesterday, but I cannot do every job today. Sam: Let us share the chores. I can sweep the floor. You can dry the dishes. Alex: That is fair. Shall we write a list before we start? Sam: Yes. We can change the plan if someone needs help.',('Which job did Alex do yesterday?','washed up'),('What can Sam do today?','sweep the floor'),('When will they write a list?','before we start')),
19:passage('Dana writes a post about an imaginary home: Our chore chart is a plan, not a label for a person. Yesterday I tidied the table and my brother fed the pet. We checked the chart together. Next time we will ask which job each person can do. A changed plan does not mean that someone is lazy.',('What did Dana tidy?','the table'),('Who fed the pet?','my brother'),('What will they ask next time?','which job each person can do')),
21:passage('Three fictional housemates have different timetables. Kim comes home early, so Kim feeds the pet. Leo washes up after dinner. Robin takes out the garbage before leaving in the morning. At the weekend they review the chart. They agree that a fair plan considers available time, not gender.',('Why does Kim feed the pet?','Kim comes home early'),('When does Leo wash up?','after dinner'),('What does a fair plan consider?','available time')),
22:passage('A class is reading two imaginary chore charts. In Chart A, one child does every job. In Chart B, three children share the jobs and can swap by agreement. The class prefers Chart B because everyone has a manageable task. They ask who checks the chart and how changes are agreed.',('Which chart gives one child every job?','Chart A'),('How can children swap jobs in Chart B?','by agreement'),('Why does the class prefer Chart B?','everyone has a manageable task')),
33:passage('At an imaginary international dinner, a guest is not sure which utensil to use. The host says, You can ask politely; you do not have to copy everyone. The guest asks before taking a shared dish. Different people may have different customs. Respect means listening and asking, rather than calling another custom strange.',('What can a guest do when unsure?','ask politely'),('When does the guest ask?','before taking a shared dish'),('What does respect mean here?','listening and asking')),
34:passage('Two fictional guests discuss table manners. One is used to a spoon; the other often uses chopsticks. They agree to offer choices instead of judging a guest. At their paper dinner plan, shared dishes have separate serving utensils. Either guest can ask the host to explain a custom. A polite question is more useful than a stereotype.',('What does the second guest often use?','chopsticks'),('What do shared dishes have?','separate serving utensils'),('What is more useful than a stereotype?','A polite question')),
36:passage('A paper recipe has three stages: prepare the ingredients, combine them, and write a serving suggestion. Mia has checked the list but has not written the last stage yet. A friend suggests a clear order: first, next, finally. The group is only editing instructions. No food, heat or sharp tools are used in this lesson.',('What is the first stage?','prepare the ingredients'),('Which stage has Mia not written?','the last stage'),('Which words show order?','first, next, finally')),
37:passage('A fictional food artist creates a picture using shapes of fruit on a plate. The plate is like a canvas. First, the artist sketches the design on paper. An adult prepares the pieces; the pupils only arrange paper shapes in this lesson. The artist wants viewers to notice colour and pattern, not the price of the food.',('What is compared with a canvas?','The plate'),('What does the artist do first?','sketches the design on paper'),('What should viewers notice?','colour and pattern')),
48:passage('Two fictional pen pals describe winter celebrations. One makes greeting cards; the other tells a story at a community meeting. Their customs differ, but both ask before sharing another person’s photograph. A class display uses invented names and drawings. Visitors may compare the traditions or simply observe without joining a celebration.',('What does the first pen pal make?','greeting cards'),('What do both ask before sharing?','another person’s photograph'),('What does the display use?','invented names and drawings')),
49:passage('An invented family in Ukraine describes its own spring celebration. They decorate paper eggs and write greetings. One member prefers drawing to singing, and that choice is accepted. Their blog says, This is our family example, not a rule for everyone in Ukraine. Readers can describe an invented tradition instead of personal experiences.',('What do the characters decorate?','paper eggs'),('Which choice is accepted?','drawing to singing'),('Is this a rule for everyone?','not a rule for everyone in Ukraine')),
51:passage('A class compares two invented New Year celebrations. In Story A, people exchange written wishes before midnight. In Story B, they create a paper calendar together the next morning. Both stories are examples, not descriptions of an entire country. The pupils compare the time and the activity, and avoid saying that everyone celebrates alike.',('What is exchanged in Story A?','written wishes'),('What is created in Story B?','a paper calendar'),('What two features do pupils compare?','the time and the activity')),
66:passage('School sports news: A friendly table tennis game was played yesterday. Mia won one game, and Leo won the next. The reporter checked the result with both players before writing the post. The report praised fair play and clear rules. It did not describe the losing player as a failure.',('Which sport is reported?','table tennis'),('Who checked the result?','The reporter'),('What did the report praise?','fair play and clear rules')),
67:passage('A fictional school newsletter has two sports headlines. The first reports a new chess club; the second reports a swimming team. The editor asks reporters to check names and results before publication. If a result is uncertain, they write that it needs checking. Accuracy matters more than posting first.',('What club is new?','a new chess club'),('What should reporters check?','names and results'),('What matters more than posting first?','Accuracy')),
69:passage('At a school exhibition about the Olympic Games, a group chooses three topics: different sports, athletes, and fair play. One poster shows that taking part requires practice. Another asks how an audience can show respect. The exhibition is not a list of current medal results. Pupils write questions rather than guessing facts they have not checked.',('Which three topics are chosen?','different sports, athletes, and fair play'),('What does taking part require?','practice'),('What do pupils write instead of guessing facts?','questions')),
70:passage('An imaginary interview at an Olympic exhibition has three questions: Which sport is shown? What equipment is needed? How can spectators show respect? The guide answers only questions supported by the display. When the date of an event is missing, the guide says it needs checking. A good question helps a reader find reliable information.',('What is the first interview question?','Which sport is shown?'),('Which questions does the guide answer?','questions supported by the display'),('What happens when a date is missing?','the guide says it needs checking')),
84:passage('In a fictional school story, a pupil notices that a character needs adult help. The pupil calls the responsible adult and describes what has been observed in simple words. The class does not practise treatment or invent a diagnosis. The language task is to identify the person, the place and the need for help. Real action follows the school safety procedure.',('Whom does the pupil call?','the responsible adult'),('What does the pupil describe?','what has been observed'),('What must the class not invent?','a diagnosis')),
85:passage('A message card in an invented story says: An adult is needed in Room 5. A pupil is sitting near the door and says they feel unwell. Please send the responsible adult. The speaker gives a clear location and observed details. The message contains no guess about an illness and no medicine instructions.',('Where is an adult needed?','Room 5'),('Where is the fictional pupil sitting?','near the door'),('What does the message avoid guessing?','an illness')),
87:passage('A fictional patient arrives for an appointment. Before the visit, the patient had written a short symptom note. The receptionist checks the name on the appointment card. The nurse asks one question at a time and allows the patient to read the note. The patient can ask for a question to be repeated. This story practises language, not diagnosis.',('What had the patient written?','a short symptom note'),('What does the receptionist check?','the name on the appointment card'),('What may the patient ask?','for a question to be repeated')),
88:passage('An invented doctor begins by listening to the patient. Next, the doctor asks clear questions and checks the written note. The patient asks what a difficult word means. The doctor explains it in simpler language. In our language lesson, no pupil plays the role of choosing treatment. The useful skill is asking for clarification.',('What does the doctor do first?','listening to the patient'),('What does the patient ask about?','a difficult word'),('Which useful skill is practised?','asking for clarification')),
102:passage('A fictional film blog describes a comedy about two robots who lose their map. They ask a musician for help and learn to listen to each other. The plot is simple, but the dialogue is lively. The blogger recommends it to viewers who enjoy gentle humour. No real film or age rating is being reviewed.',('What do the robots lose?','their map'),('Whom do they ask for help?','a musician'),('Who may enjoy the story?','viewers who enjoy gentle humour')),
103:passage('Two invented viewers disagree about a film. Kim enjoys the funny dialogue, while Robin prefers a story with more action. They give reasons instead of saying that one viewer has bad taste. Their class poll allows a third answer: neither film. A recommendation can be useful even when another person chooses differently.',('What does Kim enjoy?','the funny dialogue'),('What does Robin prefer?','a story with more action'),('What third answer does the poll allow?','neither film')),
105:passage('An imaginary theatre exhibition compares two model buildings. Theatre A has a wide stage and a small audience area. Theatre B has balconies and a narrow stage. The guide explains the difference between a live performance and a film on a screen. Pupils describe the models; real theatre names and historical facts require a checked source.',('What is wide in Theatre A?','a wide stage'),('What does Theatre B have above its seats?','balconies'),('Which two forms does the guide compare?','a live performance and a film on a screen')),
106:passage('A pupil presents a fictional theatre called River Theatre. Its leaflet shows a stage, rows of seats and two balconies. The audience can read a short summary before the play. The presentation describes the building first and the programme second. The pupil clearly labels all invented details instead of presenting them as facts about a real theatre.',('What is the theatre called?','River Theatre'),('What can the audience read?','a short summary'),('What is described first?','the building')),
119:passage('A classroom travel folder is labelled United Kingdom. Four separate cards are labelled England, Scotland, Wales and Northern Ireland. Learners compare the names and prepare questions for a guide. One card uses a drawing of a double-decker bus, another a coastline. The task is to read the supplied cards; no learner needs to claim they have travelled there.',('How many separate cards are described?','Four'),('Which card name begins with N?','Northern Ireland'),('What do learners prepare for a guide?','questions')),
120:passage('A fictional blogger is preparing a city post headed London. The draft has three parts: a title, a description of two places on the paper map, and an invitation to ask questions. A peer says the map needs clearer labels. The blogger adds the labels before publishing the classroom draft. No real opening times or prices are claimed.',('What is the heading of the post?','London'),('What needs clearer labels?','the map'),('When are labels added?','before publishing the classroom draft')),
122:passage('A paper exhibition shows three named landmarks: Tower Bridge, the Sydney Opera House and the White House. Each card has a name and a labelled drawing. Pupils practise describing shape and purpose using the information provided. If a card gives no date, they do not invent one. Their final product is a short comparison of two cards.',('How many named landmarks are shown?','three'),('What does each card have?','a name and a labelled drawing'),('What is the final product?','a short comparison of two cards')),
123:passage('A fictional walking leaflet for Kyiv has two stops labelled Golden Gate and a public garden. The paper route begins at a meeting point and finishes at the same place. A quiet stop is marked between the two attractions. Pupils describe this invented route, not a real safe walking route. They can change the plan on paper without giving a home address.',('Which named stop is included?','Golden Gate'),('Where does the paper route finish?','at the same place'),('What is marked between the attractions?','A quiet stop')),
}

# Thematic default questions examine actions, reasons and language, never a universal place/time/item triplet.
UNIT_Q={
0:[('What is one useful tip?','ask a clear question'),('What do members take?','turns'),('What does the learner ask for politely?','help')],
1:[('What are members preparing for?','the school anniversary'),('What is the learner making today?','a decoration'),('What can everyone choose?','a useful role')],
2:[('What did the learner do yesterday?','swept the floor'),('What was Sam doing at ten?','checking the list'),('How were the tasks shared?','fairly')],
3:[('What have members already checked?','the ingredients'),('Who manages sharp tools?','An adult'),('What do the students write today?','instructions')],
4:[('Who makes the cards?','volunteers'),('What is used instead of a real flame?','A drawing of a candle'),('What can visitors do instead of taking part?','quietly observe')],
5:[('Who checked the equipment?','the coach'),('What was the prize given for?','fair play'),('Which alternative role could students choose?','reporters')],
6:[('What symptom does the fictional character describe?','a sore throat'),('What does the receptionist offer for language help?','a paper form'),('How many questions does the nurse ask at a time?','one question')],
7:[('How is the plot described?','quite simple'),('What could the audience read?','subtitles'),('Why did the friend prefer the ending?','it was less predictable')],
8:[('What does each visitor receive?','a leaflet'),('Which route does the learner choose?','the short route'),('Why is that route chosen?','it includes a quiet stop')],
}
OLD_CONTEXT=context
def context(u,n,offset=0):
 d=OLD_CONTEXT(u,n,offset)
 # Avoid inaccurate full-game scores across different sports; this is a reporting task.
 if u==5:d['text']=d['text'].replace('the final score was 12–10','the reporter checked the score before publication')
 if u==2:d['text']=d['text'].replace('while Alex washed up','while Ari washed up')
 # A cooking club is a group, not a room; grammar must remain natural in every variant.
 d['text']=d['text'].replace('to the cooking club','to a meeting of the cooking club').replace('in Room 12','in Room 12')
 d['qas']=[{'question':q,'answer':a,'evidence':a} for q,a in UNIT_Q[u]]
 return d

# Specific spoken/written products replace the former generic event invitation.
PRODUCT={
11:('Проведи мініопитування вигаданого співрозмовника про гурток: 2 запитання (вибір і причина), 2 відповіді та підсумок. 5–6 реплік.','A: Which club would you choose? B: The library club. A: Why? B: Because I enjoy recommending books. A: I will record one vote for the library club. B: Thank you.'),
12:('Напиши допис для вигаданого шкільного сайту: подія, дві дії учнів, спосіб участі без виступу, завершення. 5 речень.','Our school is preparing an anniversary exhibition. One group is collecting photographs. Another group is writing captions. You can write a label instead of making a speech. Come and see the display.'),
27:('У6 репліках домовтеся про підготовку вигаданого свята: 2 справи, розподіл ролей, ввічливе уточнення.','A: Shall we prepare the room? B: Yes. I can tidy the tables. A: I can make decorations. B: Could you repeat your job? A: I can make decorations. B: Good, let us write the plan.'),
28:('Напиши5-реченнєве повідомлення про вигаданий день домашніх справ: привітання, 2 виконані справи, прохання, завершення.','Hi Sam! Yesterday I swept the floor. My friend washed up. Could we share the jobs again tomorrow? Thank you for your help.'),
42:('Поясни роботу кухонного приладдя у6 репліках: запитай про предмет, назви функцію, уточни деталь. Лише мовний опис, нічого не вмикаємо й не готуємо.','A: What is this? B: It is a grater. A: What is it used for? B: It is used for grating food. A: Could we label it on paper? B: Yes, let us write its name and function.'),
43:('Опиши вигадану страву у5–6 коротких реченнях: назва, 3 інгредієнти, два предмети посуду, причина вибору. Не потрібно рецепта з3 кроками.','My imaginary dish is fruit salad. It has apples, bananas and oranges. We use a bowl and a spoon. It is colourful. I chose it because the ingredients are easy to name.'),
56:('У6 репліках обговори вигадане родинне святкування Thanksgiving: чим дякують, як можуть долучитися гості, одне уточнення. Це одна придумана родина, а не правило для країни.','A: What does the family do at its imaginary Thanksgiving meal? B: They write thank-you notes. A: Must every guest read a note aloud? B: No, a guest can leave a written note. A: Could I draw a card instead? B: Yes, that is another way to join.'),
57:('Напиши короткий email про Easter у вигаданій родині: привітання, 2 конкретні традиції, прийняття іншого вибору, завершення.5 речень.','Hi Kim! In our imaginary family, we decorate paper eggs at Easter. We also write greeting cards. Guests can join or quietly observe. Write back when you can. Best wishes, Robin.'),
75:('У6 репліках прочитай/розіграй розмову про underwater hockey: що це за назва, де відбувається гра за карткою, яке приладдя показано; попроси уточнення. Картка: underwater hockey; pool; stick; puck. Нічого не випробовуємо.','A: Which sport is on the card? B: Underwater hockey. A: Where is it played according to the card? B: In a pool. A: Could you name the equipment? B: A stick and a puck.'),
76:('У6 репліках запитай про вигаданий спортивний гурток: назва спорту, час, спосіб участі як репортер.','A: Which club is open? B: The table tennis club. A: When does it meet? B: On Friday at three. A: Can I join as a reporter? B: Yes, you can write our news.'),
77:('Напиши5-реченнєвий блог про вигадану спортсменку/спортсмена: спорт, тренування, конкретне досягнення, fair play, висновок. Не приписуй вигаданих рекордів реальній людині.','Dana is a fictional table tennis player. She practises twice a week. Last month she won a school game. She thanked her opponent and checked the score. I admire her fair play.'),
94:('У6 репліках зіграй вигадані ролі patient/receptionist: симптом персонажа, запит допомоги дорослого, повторення запитання, подяка. Мовні рекомендації обмежені зверненням до відповідального дорослого; діагнозу й ліків немає.','A: Good morning. I have a sore throat. B: Would you like me to call the responsible adult? A: Yes, please. Could you repeat your question? B: Shall I call the responsible adult? A: Yes, thank you for your help.'),
95:('Напиши5-реченнєвий email від вигаданого персонажа: проблема зі самопочуттям, звернення до дорослого, факт розмови з медпрацівником, завершення. Без назв ліків, доз і лікувальних рекомендацій.','Hi Sam! My fictional character had a sore throat. The character asked a responsible adult for help. A nurse listened and explained the next steps privately. I will write again later. Best wishes, Kim.'),
111:('Порекомендуй вигаданий фільм у6 репліках: назва/жанр, одна оцінка, причина, ввічливе прийняття іншого вибору.','A: Would you recommend Lost Robots? B: Yes, it is a comedy. A: Why do you like it? B: The dialogue is quite funny. A: I prefer an action story. B: That is fine; we can choose different films.'),
112:('Напиши5–6-реченнєву рецензію на вигаданий фільм: назва/жанр, конкретний сюжет, 2 оцінки з причинами, рекомендація.','Lost Robots is a fictional comedy. Two robots lose a map and ask a musician for help. The plot is clear because the problem is simple. The dialogue is lively because the characters disagree politely. I recommend it to viewers who enjoy gentle humour.'),
128:('У6 репліках презентуй паперову картку вигаданого визначного місця: назва,2 ознаки з картки, уточнення. Картка: River Castle; two towers; a small garden. Фото замінює намальована картка; інтернет не потрібний.','A: My card shows River Castle. B: What can visitors see? A: Two towers and a small garden. B: Could you repeat the second feature? A: A small garden. B: Thank you; the description is clear.'),
129:('Напиши туристичний мінібуклет із5–6 речень про вигаданий маршрут: точка зустрічі,2 об’єкти,2 варіанти шляху, причина вибору, точка завершення.','Meet at River Castle gate. Our route includes the castle and a public garden. Choose either the short route or the long route. I suggest the short route because it includes a quiet stop. Finish at the same gate.'),
}
LISTENING={
8:passage('Our school anniversary is next week. One group will make decorations, and another will perform a short play. The organiser asks each member to choose a role. A pupil who does not want to speak can write labels for the exhibition. Please tell the organiser your choice before the group writes its plan.',('Which event is being prepared?','school anniversary'),('What will the second group perform?','a short play'),('Which quiet role is offered?','write labels')),
24:passage('In our imaginary home, Alex usually washes up and Sam dries the dishes. Yesterday they changed the jobs because Alex was busy with a school task. Sam washed up, and Robin dried the dishes. They agreed on the change before starting. The story is about a flexible plan, not about what every family must do.',('Who usually washes up?','Alex'),('Who dried the dishes yesterday?','Robin'),('When was the change agreed?','before starting')),
39:passage('This is a paper recipe for fruit salad. The ingredients are an apple, a banana and an orange. The utensils are a bowl and a spoon. First, an adult prepares the fruit. Next, the pieces go into the bowl. Finally, they are stirred gently. The pupils only write these instructions; they do not prepare food in class.',('Name the three ingredients.','an apple, a banana and an orange'),('Which two utensils are named?','a bowl and a spoon'),('What happens finally?','they are stirred gently')),
53:passage('Two invented families describe winter traditions. At an imaginary Christmas gathering, one family makes paper stars. At New Year, another family writes wishes for the coming year. Neither story describes everyone in a country. Guests can join the activity or quietly observe. The class compares what people make and write, without asking pupils to share personal beliefs.',('What does the first family make?','paper stars'),('What does the second family write?','wishes for the coming year'),('What may guests do instead of joining?','quietly observe')),
72:passage('A: Which sport is on this club card? B: Water polo. A: What does the card show? B: A pool, two teams and a ball. A: Is this the underwater hockey card? B: No, that is a different card. Today we only compare the names and equipment on paper. Nobody practises a water sport in this classroom.',('Which sport is discussed?','Water polo'),('What playing object is on the card?','a ball'),('Which other sport is mentioned?','underwater hockey')),
90:passage('A fictional character reads a short verse: I have a note; I have a question. Please listen first to my suggestion. Ask one thing, then let me say: I need an adult here today. After the verse, the character describes a sore throat on a paper card. The class practises polite requests and a symptom phrase, without diagnosis or treatment.',('What does the character have besides a note?','a question'),('Whom does the character request?','an adult'),('What symptom is on the card?','a sore throat')),
108:passage('A school radio story introduces a fictional actor, Robin Ray. Robin began in a school play and later worked on an imaginary comedy about robots. Robin practises clear speech before a performance. A reviewer praises the lively dialogue. The biography is invented for this lesson; it does not claim facts about a real actor.',('What is the fictional actor called?','Robin Ray'),('Where did Robin begin?','a school play'),('What does the reviewer praise?','the lively dialogue')),
125:passage('Listen to an invented classroom guide for Kyiv. Our paper map marks Golden Gate and a public garden. The suggested route begins and ends at the same meeting point. A quiet stop is marked between the attractions. This is a language map, not a real route for travel during an alert. Learners describe the labelled stops and explain one choice.',('Which named landmark is marked?','Golden Gate'),('Where does the route end?','the same meeting point'),('What is marked between the attractions?','A quiet stop')),
}
GRAMMAR['tags']=dict(rule='Present Simple/Continuous та question tags: після ствердження заперечний хвостик; допоміжне дієслово й займенник узгоджені з основою.',model='Alex reads every day, doesn’t he? Mia is making a poster, isn’t she? They do not meet today, do they?',items=[('Alex usually ___ books. (read / reads)','reads'),('Mia ___ making a poster now. (is / does)','is'),('Alex reads every day, ___ he? (doesn’t / isn’t)','doesn’t'),('They do not meet today, ___ they? (do / are)','do')])
ERRORS['tags']=('Alex read every day. Mia making a poster now. Alex reads, isn’t he?','Alex reads every day. Mia is making a poster now. Alex reads, doesn’t he?')

# Two transformations per grammar family; their complete answers are independently authored.
TRANSFER={
'present': [('Запитай про звичку: Alex reads books every day. (What…?)','What does Alex read every day?'),('Запитай про дію зараз: Mia is making a poster. (What…?)','What is Mia making?')],
'past':[('Зроби запитання: Sam swept the floor yesterday.','Did Sam sweep the floor yesterday?'),('Зроби заперечення: They made a chart.','They did not make a chart.')],
'past_cont':[('Запитай про процес: Sam was cleaning at ten. (What…?)','What was Sam doing at ten?'),('Запитай про учасників: They were washing up.','Were they washing up?')],
'perfect':[('Запитай про результат: Alex has brought a bowl. (What…?)','What has Alex brought?'),('Запитай: They have checked the ingredients.','Have they checked the ingredients?')],
'passive':[('Пасив: Volunteers make cards.','Cards are made by volunteers.'),('Запитай про місце: Cards are made in the hall. (Where…?)','Where are cards made?')],
'past_passive':[('Пасив: The coach checked the equipment.','The equipment was checked by the coach.'),('Запитай про місце: The match was played in the gym. (Where…?)','Where was the match played?')],
'zero':[('Поєднай if: A visitor needs language help. The receptionist offers a form.','If a visitor needs language help, the receptionist offers a form.'),('Поєднай if: I do not understand. I ask a question.','If I do not understand, I ask a question.')],
'past_perfect':[('Познач ранішу дію: Alex prepared the form. Then the visit began.','Alex had prepared the form before the visit began.'),('Запитай про ранішу дію: Alex had prepared the form. (What…?)','What had Alex prepared?')],
'degree':[('Розташуй слова: clear / enough / The subtitles / are.','The subtitles are clear enough.'),('Розташуй слова: too / to read / The screen / small / is.','The screen is too small to read.')],
'comparison':[('Порівняй за підказкою: Film A: interesting 5/5; Film B: interesting 3/5. (more…than)','Film A is more interesting than Film B.'),('Рівність: Both plays last 60 minutes. (as long as)','The first play is as long as the second play.')],
'determiners':[('Опиши за each: There are three visitors. Every visitor gets a leaflet.','Each visitor gets a leaflet.'),('Опиши за both: There are two attractions. The two attractions are open.','Both attractions are open.')],
'conjunctions':[('Вибір за either…or: You can take the short route. You can take the long route.','You can take either the short route or the long route.'),('Причина за because: I choose the short route. It includes a quiet stop.','I choose the short route because it includes a quiet stop.')],
 'tags':[('Додай хвостик: Alex reads every day, …?','Alex reads every day, doesn’t he?'),('Додай хвостик: Mia is making a poster, …?','Mia is making a poster, isn’t she?')],
}

MODE_UK={'reading':'читання','vocabulary':'лексика','grammar':'граматика','listening':'слухання','speaking':'усна взаємодія','writing':'письмо','project':'проєкт','review':'повторення','assessment':'діагностика','portfolio':'портфоліо'}

def effective_unit(l):
 if l['unit']:return l['unit']
 return 0 if l['number']==1 else (4 if l['semester']==1 else 8)

def grammar_id(l,u):
 if l['number'] in (64,65):return 'tags'
 if l['number'] in (136,139,140):return 'past_passive'
 selected=grammar(l,u)
 return next(k for k,v in GRAMMAR.items() if v is selected)

def alternate(p):
 """Equivalent reserve: new character/objects/actions, same three comprehension constructs."""
 substitutions=[('volunteers','older pupils'),('the coach','the organiser'),('a sore throat','a headache'),('a paper form','a printed card'),('a leaflet','a route card'),('the short route','the accessible route'),('a decoration','a poster'),('the ingredients','the utensils'),('a bowl','a saucepan'),('subtitles','a written summary'),('quite simple','very clear'),('fair play','teamwork'),('reporters','scorekeepers'),('swept the floor','dried the dishes'),('checking the list','reading the plan'),('fairly','by agreement'),('paper stars','paper lanterns'),('written wishes','greeting cards'),('a question','a request')]
 text=p['text'];qas=[dict(x) for x in p['qas']]
 for old,new in substitutions:
  if old.lower() in text.lower():
   text=re.sub(re.escape(old),new,text,flags=re.I)
   for q in qas:
    for k in ('question','answer','evidence'):q[k]=re.sub(re.escape(old),new,q[k],flags=re.I)
 # Reserve must be substantively distinct, rather than another sheet with the same answer key.
 assert text!=p['text']
 return {'text':text,'qas':qas}

def simple_product(u):
 options={
0:('Створи6 реплік вигаданої навчальної групи: запит завдання, уточнення, відповідь і подяка.','A: What is our task? B: Make a word list. A: Could you repeat that, please? B: Make a short word list. A: Can I write my answer? B: Yes, thank you for asking.'),
1:('Створи коротку картку вигаданої шкільної події: назва, дві дії учнів, тихий спосіб долучитися.4 речення.','Our event is a school exhibition. One group is collecting pictures. Another group is writing captions. You can write a label instead of giving a speech.'),
2:('Напиши4 речення про вигаданий розподіл справ:2 виконані дії, процес у певну мить, ввічлива пропозиція.','Sam swept the floor yesterday. Alex washed up. At ten Robin was checking the list. Could we share the jobs again?'),
3:('Створи4-реченнєву паперову картку: назва страви,3 інгредієнти,2 предмети посуду, одне речення Present Perfect про підготовку. Без реального готування.','Our dish is fruit salad. We need an apple, a banana and an orange. We use a bowl and a spoon. We have checked the ingredients.'),
4:('Напиши4 речення про вигадане свято: що проводять, що роблять/показують, хто створює матеріал і як можна спостерігати.','A paper festival is held in our imaginary hall. Cards are made by volunteers. Drawings are shown to visitors. Guests can join or quietly observe.'),
5:('Напиши4-реченнєву спортивну новину про вигадану подію: що відбулося, хто перевірив спорядження,2 речення Past Simple Passive, згадка fair play.','A school game was organised yesterday. The equipment was checked by the coach. The report praised fair play. The result was checked before publication.'),
6:('Склади6 реплік вигаданого відвідувача й реєстратора: симптом, ввічливе уточнення, звернення до дорослого й подяка. Без діагнозу/ліків.','A: I have a sore throat. B: Shall I call the responsible adult? A: Could you repeat that, please? B: Shall I call the responsible adult? A: Yes, please. B: Thank you for explaining.'),
7:('Напиши4-реченнєвий відгук про вигаданий фільм: назва, конкретний сюжет, оцінка з причиною, рекомендація.','Lost Robots is a fictional comedy. Two robots lose a map and ask a musician for help. I like the dialogue because it is funny. I recommend it to viewers who enjoy gentle humour.'),
8:('Напиши4-реченнєвий мінібуклет вигаданого маршруту:2 об’єкти, вибір двох маршрутів, причина, точка завершення.','Our route includes a castle and a garden. Choose either a short route or a long route. I suggest the short route because it includes a quiet stop. Finish at the castle gate.'),
 }
 return options[u]

# 136 genuinely integrates the four topics named in its calendar title.
INTEGRATED=passage('At a fictional travel fair, one card describes a castle route with a quiet stop. A sports card says the equipment was checked by the coach. A cinema card recommends a comedy because its dialogue is funny. A health-room card asks a responsible adult for help. Visitors choose a card and explain which phrase supports their answer.',('What does the castle route include?','a quiet stop'),('Who checked the equipment?','the coach'),('Why is the comedy recommended?','its dialogue is funny'))


def profile(l):
 n=l['number'];u=effective_unit(l);mode=focus(l)
 if l['kind']=='integrated_review':mode='review'
 gid=grammar_id(l,u);g=GRAMMAR[gid]
 r=READING.get(n,context(u,n,1));a=LISTENING.get(n,context(u,n,2))
 if n in (81,99,116,133):
  a=LISTENING[{81:72,99:90,116:108,133:125}[n]]
 if l['kind']=='pair_diagnostic':r=context(u-1,n,1)
 if l['kind']=='semester_assessment':
  # L+R together sample all four semester units, rather than only the last unit.
  us=range(1,5) if l['semester']==1 else range(5,9)
  cards=[context(v,n,1) for v in us]
  r=passage(' '.join(x['text'] for x in cards[:2]),*[ (x['qas'][0]['question'],x['qas'][0]['answer']) for x in cards[:2] ],(cards[0]['qas'][1]['question'],cards[0]['qas'][1]['answer']))
  a=passage(' '.join(x['text'] for x in cards[2:]),*[ (x['qas'][0]['question'],x['qas'][0]['answer']) for x in cards[2:] ],(cards[3]['qas'][1]['question'],cards[3]['qas'][1]['answer']))
 if n==136:r=INTEGRATED
 lex=LEXICAL.get(n,BANK[u]['lex'])
 task,model=PRODUCT.get(n,simple_product(u))
 if mode=='vocabulary':
  r=passage(LEX_EXAMPLES[n],*[(f'Знайди англійський відповідник «{uk}».',en) for en,uk in lex[:3]])
  task='Напиши4 короткі речення за словником: використай перші4 слова/вирази по одному разу в осмисленому контексті. Дозволено вигадані персонажі; не вживай ярликів до однокласників.'
  model=LEX_EXAMPLES[n]
 if mode=='reading':
  task='Дай3 короткі відповіді R; до двох випиши2–4 слова-докази. Потім2 речення: один точний факт і одна ввічлива реакція/запит до тексту. Нової події вигадувати не треба.'
  model=f"{r['qas'][0]['answer']}. Could you explain the detail about {r['qas'][1]['answer']}?"
 if mode=='listening':
  task='Після двох читань запиши3 факти L. Потім2 речення-перекази з двома різними фактами; можна короткі цитати. Не додавай непочутих деталей.'
  model=' '.join(q['answer'].rstrip('.')+'.' for q in a['qas'][:2])
 if mode=='grammar':
  task='Виконай G1–G4 і T1–T2; поясни один вибір. Новий великий тематичний текст не потрібний.'
  model=' '.join(answer for _,answer in TRANSFER[gid])
 if mode=='review':
  task='Віднови4 слова V, виконай G1–G2 та виправ2 місця у F. Після самоперевірки поясни одну зміну; великий новий текст — лише резерв.'
  model=ERRORS[gid][1]
 if n==136:
  task='За4 картками: дай R1–R3; додатково знайди фразу звернення по допомогу; виконай G1–G2 Past Simple Passive.2 речення пояснення вибору картки — резерв.'
  model='The equipment was checked by the coach. The comedy is recommended because its dialogue is funny. The health-room card asks a responsible adult for help.'
 if mode=='portfolio':
  task='Збережи версії F «до» й «після»; виправ3 мовні помилки, поясни2 зміни, додай1 власне застосування моделі й1 конкретний наступний крок. Не потрібно нового повного проєкту.'
  model=ERRORS[gid][1]+' '+TRANSFER[gid][0][1]+' Next time I will check the auxiliary verb.'
 if mode=='project':
  task+=' Це компактний проєкт: чернетка, один точний відгук,2 позначені зміни. Коротка презентація20–30 секунд за можливості; якщо не почуто — позначити відкладено.'
 # Main load is explicit. Other tasks stay in the teacher's reserve instead of the student packet.
 core={
 'reading':['R: 3 відповіді','P: 2 речення з опорою на текст'],
 'listening':['L: 3 відповіді після двох читань','P: 2 факти-перекази'],
 'grammar':['G: 4 вибори','T: 2 перетворення'],
 'vocabulary':['V: 4 відповідності','P: 4 короткі речення'],
 'speaking':['S: 5–6 реплік за ролями','P: 2 ключові фрази до діалогу'],
 'writing':['P: 5–6 коротких речень','редагування: 1 зміна'],
 'project':['P: компактна картка/чернетка','2 правки і коротка презентація за можливості'],
 'review':['V: 4 відповідності','G: 2 вибори','F: 2 корекції'],
 'portfolio':['F: 3 корекції + 2 пояснення','1 власна модель + 1 наступний крок'],
 'assessment':['тільки визначені контрольні блоки'],
 }[mode]
 if n==136:core=['R: 3 факти з карток + фраза допомоги','G: 2 вибори']
 return dict(number=n,u=u,mode=mode,gid=gid,g=g,r=r,a=a,lex=lex,task=task,model=model,core=core,source=l)


def qsheet(p):
 return '\n\n'.join(f"{i}. {x['question']}\n\n   ______________________________________________________________" for i,x in enumerate(p['qas'],1))

def qkey(p):
 return '\n'.join(f"{i}. **{x['answer'].rstrip('.')}**. Доказ у тексті: «{x['evidence']}»." for i,x in enumerate(p['qas'],1))


def matching(p):
 lex=p['lex'];n=p['number'];order=list(range(4));shift=n%4;order=order[shift:]+order[:shift];order.reverse()
 prompt='\n'.join(f'{i+1}. {lex[i][0]} → ____' for i in range(4))+'\n\n'+ '; '.join(f'{chr(65+j)} — {lex[i][1]}' for j,i in enumerate(order))+'.'
 key=', '.join(f'{i+1} — {chr(65+order.index(i))}' for i in range(4))
 return prompt,key


def rubric(p):
 if p['source']['kind']=='pair_diagnostic':return 'L /3, R /3: по1 за кожний правильний факт; S /3: по1 за запит, змістовну відповідь та уточнення; P /3: по1 за відповідність темі, потрібні деталі та мовну зрозумілість. Первинні12 балів з4 окремими профілями.'
 if p['mode']=='assessment' and 'слухання і читання' in p['source']['topic']:return 'L /3 та R /3: по1 за кожний точний факт. Первинні6 балів; ці два результати зберігаються окремо.'
 if p['mode']=='assessment':return 'S /6: виконання ролі/запитів, зрозумілість і відповідь/уточнення — по0–2. P /6: зміст, організація, мовна зрозумілість — по0–2. Первинні12 балів; S та P окремо.'
 return 'Формувально: точність факту/форми позначати окремо. Відкритий продукт: зміст, організація та мовна зрозумілість — по0–2, для зворотного зв’язку.'


def write(path,text):
 text=re.sub(r'([ap]\.m\.)\.',r'\1',text)
 text=re.sub(r'([А-Яа-яІіЇїЄєґҐ])([0-9])',r'\1 \2',text)
 text=re.sub(r'([0-9])([А-Яа-яІіЇїЄєґҐ])',r'\1 \2',text)
 path.write_text(text.rstrip()+'\n',encoding='utf-8')


def learner_sheet(p,reserve=False):
 l=p['source'];n=p['number'];mode=p['mode'];r=alternate(p['r']) if reserve else p['r'];a=alternate(p['a']) if reserve else p['a'];g=p['g'];assessed=mode=='assessment';diag=l['kind']=='pair_diagnostic';lr=assessed and ('слухання і читання' in l['topic']);sw=assessed and not lr and not diag
 title='Резерв після переривання' if reserve else 'Основний аркуш'
 s=f'''# 7 клас · {n:03d} · {l['date']} · {title}

**Тема:** {l['topic']}  
Код учня: ____________________ Фактична дата: ____________________

Усі життєві ситуації можна вигадати. Камера добровільна. Особисті історії не потрібні. За небезпечних умов припини завдання; у русі до укриття не вчимося.

**Сьогодні обов’язково:** {'; '.join(p['core'])}. Резерв учитель дає лише замість завершеного блоку. Не потрібно виконувати всі вправи з конспекту.

'''
 if assessed:
  s+='**Самостійна перевірка:** '+rubric(p)+' За переривання зберігаємо завершене й переносимо решту; читання не зараховуємо як слухання, чат — як говоріння.\n\n'
 else:
  # Four working items; the rest is a reference, not eight new words to test.
  s+='## Опора · 4 робочі слова\n\n'+ '; '.join(en+' — '+uk for en,uk in p['lex'][:4])+'.\n\n'
  s+='Складні слова з авторської картки можна уточнити в учителя; це не новий обов’язковий словниковий диктант.\n\n'
 if mode=='reading' or (assessed and (lr or diag)) or n==136:
  s+='## R · Прочитай\n\n'+r['text']+'\n\n'+qsheet(r)+'\n\n'
  if n==136:s+='4. Знайди в тексті фразу звернення до дорослого: __________________________\n\n'
 if mode=='listening' or (assessed and (lr or diag)):
  s+='## L · Прослухай двічі\n\nЗакрий додаток L; учитель читає двічі. Якщо звук недоступний, познач блок як відкладений.\n\n'+qsheet(a)+'\n\n'
  if l['kind']=='listening_workshop':
   s+='Письмова картка для зіставлення: «'+a['qas'][0]['answer']+'». Після слухання знайди в ній одну підтверджену деталь; поряд запиши ще один факт L. Це авторські картки, не відтворення SB/WB.\n\n'
 if mode=='vocabulary' or (mode=='review' and n!=136):s+='## V · Зістав\n\n'+matching(p)[0]+'\n\n'
 if mode=='grammar' or mode=='review':
  if mode=='grammar':s+='## Модель\n\n'+g['rule']+'\n\n'+g['model']+'\n\n'
  count=4 if mode=='grammar' else 2
  s+='## G · Обери форму\n\n'+'\n'.join(f'{i}. {q} → __________' for i,(q,_) in enumerate(g['items'][:count],1))+'\n\n'
  if mode=='grammar':s+='## T · Застосуй модель\n\n'+'\n\n'.join(f'{i}. {q}\n\n   __________________________________________________________' for i,(q,_) in enumerate(TRANSFER[p['gid']],1))+'\n\n'
 if mode in ('portfolio','review') and n!=136:
  s+='## F · Чернетка для редагування\n\n'+ERRORS[p['gid']][0]+'\n\nМоя версія: ______________________________________________________________\n\n_________________________________________________________________________\n\nЧому змінив/змінила: ______________________________________________________\n\n'
 if mode in ('speaking','writing','project') or (assessed and (diag or sw)):
  if assessed:
   s+='## S · Усна взаємодія\n\n'+p['s_task']+' На підготовку2 хв. Усне свідчення — лише реально почутий зразок, без вимоги камери.\n\n'
   if reserve:s+='Обери іншу вигадану деталь/роль, ніж у чернетці до переривання.\n\n'
  s+='## '+('S' if mode=='speaking' else 'P')+' · Продукт\n\n'+p['task']+'\n\n'
  if assessed and reserve:s+='Використай нові вигадані деталі; збережи формат і критерії.\n\n'
  s+='План: __________________ / __________________ / __________________\n\n'+'\n\n'.join(f'{i}. ______________________________________________________________' for i in range(1,7))+'\n\n'
 elif mode in ('reading','listening'):
  count=3 if n in (19,49,106,120) else 2
  s+=f'## P · {count} короткі речення/репліки\n\n'+p['task']+'\n\n'+'\n\n'.join(f'{i}. ____________________________________________________________________' for i in range(1,count+1))+'\n\n'
 elif mode=='vocabulary':s+='## P · Лексика в контексті\n\n'+p['task']+'\n\n'+'\n\n'.join(f'{i}. ______________________________________________________________' for i in range(1,5))+'\n\n'
 if mode=='portfolio':s+='Власна модель: ___________________________________________________________\n\nНаступного разу перевірю: _________________________________________________\n\n'
 if mode=='project':s+='Відгук про зміст: _____________________\n\nЗміна1: ________________________ Зміна2: ________________________\n\n'
 if not assessed:s+='**Exit:** одна точна відповідь / виправлена форма: _________________________\n\n**ДЗ до5 хв:** завершити тільки незакінчений основний продукт; якщо завершено — перевірити1 фразу й пояснити1 зміну. Після B/D —2 рядки, без накопичення всього45-хвилинного обсягу.\n\n'
 else:s+='**Після здавання:** який прийом допоміг? _______________________________\n\nОфіційний результат не визначається камерою/емоціями чи недоступним зв’язком.\n\n'
 s+='**Паперовий місток D (12 хв після відновлення безпечних умов і світла):**2 хв прочитай опору/умову;4 хв виконай перші2 доступні пункти або сплануй2 репліки;4 хв перевір одну відповідь/напиши одну власну фразу;2 хв познач завершене та збережи аркуш. Для контролю це підготовка, а не завершена перевірка.\n\n'
 if mode=='listening' or (assessed and (lr or diag)):
  s+='## Додаток L — ВІДДІЛИТИ ДО СЛУХАННЯ\n\nПовний текст для вчителя та подальшої паперової роботи. Самостійне читання цього додатка не є доказом слухання.\n\n'+a['text']+'\n'
 return s
# Corrected lexical models contain all four actually requested target expressions.
LEX_EXAMPLES[4]='A fictional bookworm recommends books. A chatterbox in the story learns to take turns. A computer geek helps with the club website. The class explains why the label drama queen can hurt someone and should not be used to judge a classmate.'
LEX_EXAMPLES[25]='An oven is an appliance. Some appliances are electrical. A clearer paper label is an improvement to our diagram. We describe the words switch on and switch off without operating equipment.'
LEX_EXAMPLES[50]='Our imaginary celebration has cards labelled Good Friday, Boxing Day and New Year’s Eve. Each card explains one custom. A visitor can observe the display without celebrating these days.'
LEX_EXAMPLES[73]='A basketball court has a basket. A football pitch is shown on the next card. A tennis player uses a racket and a net. Ice hockey is played on a rink with a stick and a puck.'

def evidence_sentence(p,answer):
 for sentence in re.split(r'(?<=[.!?])\s+',p['text']):
  if answer.casefold() in sentence.casefold():return sentence
 raise ValueError((p['text'],answer))

BASE_PROFILE=profile
def profile(l):
 p=BASE_PROFILE(l)
 if p['mode']=='reading':p['model']='The text says: “'+evidence_sentence(p['r'],p['r']['qas'][0]['answer'])+'” Could you explain the next detail, please?'
 if p['mode']=='listening':p['model']=' '.join(evidence_sentence(p['a'],x['answer']) for x in p['a']['qas'][:2])
 return p


def teaching_actions(p):
 mode=p['mode'];g=p['g']
 principal={
 'reading':('«Прочитай R. Спочатку визнач головну думку, потім дай3 відповіді; до двох знайди слова-докази».','R1–R3 та2 короткі докази, без нового запрошення на подію.'),
 'listening':('«Закрий L. Після першого читання запиши тему; після другого —3 факти». Читати двічі з паузою45 секунд.','L1–L3. Якщо звук/умови недоступні — позначити відкладено, не підміняти R.'),
 'grammar':('«Обери форми G1–G4; поясни, яке слово допомогло. Потім T1–T2 — запитання або перетворення за сьогоднішньою моделлю».','4 форми та2 перенесення правила; не додаємо новий великий текст.'),
 'vocabulary':('«Закрий переклади. V1–V4: зістав перші4 слова. Поверни переклади для перевірки; склади по одному контексту для кожного слова».','4 відповідності;4 короткі тематичні речення, слова підкреслено.'),
 'speaking':('«Умова S на аркуші: спочатку30 секунд подумати, потім6 реплік. Після однієї спроби обміняйся ролями».','Один короткий діалог; учитель фіксує лише реально почуті запитання/відповіді.'),
 'writing':('«Виділи формат і3 обов’язкові деталі P. План —3 ключові слова. Пиши5–6 коротких речень».','План і чернетка P; достатньо одного завершеного повідомлення.'),
 'project':('«Результат — компактна картка за P; можна працювати самому. Зроби чернетку, попроси один точний відгук і внеси2 зміни».','Чернетка, відгук про зміст,2 правки; одна коротка презентація за можливості.'),
 'review':('«V1–V4, G1–G2, потім2 корекції F. Спочатку самостійно; після сигналу відкрий модель».','4 слова,2 форми,2 виправлення; одна пояснена зміна.'),
 'portfolio':('«F: збережи початкову версію. Виправ3 помилки, поясни2, напиши одну власну модель і конкретний наступний крок».','Дві версії з позначеними змінами; емоційний звіт не потрібний.'),
 }
 if p['number']==136:return ('«Прочитай4 тематичні картки. Дай R1–R3, знайди прохання дорослому; виконай G1–G2».','Факти подорожей/спорту/кіно/самопочуття та2 форми Passive.')
 return principal[mode]


def lesson_plan(p):
 l=p['source'];n=p['number'];mode=p['mode'];g=p['g'];assessed=mode=='assessment'
 primary='; '.join(p['core']);criterion='2 із3 точних фактів' if mode in ('reading','listening') else ('3 із4 лексичних відповідностей' if mode=='vocabulary' else ('3 із4 форм та1 із2 переносів правила' if mode=='grammar' else 'виконано змістову умову й зрозумілий адресату продукт'))
 s=f'''# Урок {n:03d} · 7 клас · {l['date']}

**Тема:** {l['topic']}  
**Рік:** 2026/2027. **Семестр:** {l['semester']}. **Дата:** {l['calendar_status']}.  
**Тип:** {l['kind']}. **Пріоритет:** {MODE_UK[mode]}. Це план підготовки, не запис факту проведення.

## План для адміністрації

- Очікуваний орієнтир календаря: {l.get('expected_learning_evidence','')}
- Дія, яку перевіряємо сьогодні: {p['task']}
- Обов’язковий мінімум A/C: {primary}. Критерій успіху: {criterion}; за потреби окрема адаптація з фіксацією підтримки.
- Комунікативна функція джерела: {l.get('communicative_functions','')}. Авторські тексти відповідають темі; це не дослівні сторінки SB/WB. Реальні особисті, медичні й родинні обставини можна замінювати вигаданими.
- НУШ: іншомовна комунікація (відповідь/уточнення з доказом), навчання впродовж життя (самоперевірка), соціальна та громадянська компетентність (повага до вибору й черга реплік). Нормативні коди не вигадано.
- Авторська SEL-адаптація у дусі «Зерна»: вибір «сам / пара / письмово / пропускаю публічну репліку»; відгук про дію, не про особистість. Це не офіційна вправа програми «Зерна». Емоції, камера, особисті історії не оцінюються.
- Матеріали: [handout.md](handout.md) і олівець; ключ тільки в учителя. Паперовий пакет видати до відключення. Інтернет, підручник і телефон для завдань не потрібні.

## Опорний конспект

**4 робочі слова:** {'; '.join(en+' — '+uk for en,uk in p['lex'][:4])}. Інші слова словника джерела — довідка, не прихований додатковий диктант.

**Мовна модель для навчання:** {g['model']}  
**Правило:** {g['rule']}  
**Зразок продукту саме цього уроку:** {p['model']}

**Типова помилка:** {ERRORS[p['gid']][0]}  
**Корекція:** {ERRORS[p['gid']][1]}  
**Репліка підтримки:** «Зміст зрозумілий. Перевір одне допоміжне слово/факт». Модель і ключ не показувати під час самостійної перевірки.

## Переривання й місток повернення

За тривоги: «Зупиняємо роботу, діємо за правилами школи». У русі до укриття не вчимося й не вимагаємо зберігати аркуш ціною затримки. B — тільки після прибуття, перевірки присутності, дозволу відповідального дорослого та за умов читання. У шумному тісному укритті без руханок/аудіо/публічних особистих розповідей. Якщо немає умов — перенести навчання; D пізніше в безпечному достатньо освітленому місці. При новому сигналі зупиняється і B.

Безпечне повернення:0–2 хв знайти останній завершений код;2–4 хв відновити одну модель/факт;4–6 хв завершити мінімальний пункт і продовжити. Решту обсягу перенести, не накопичувати всі пропущені вправи. Для контролю зберегти завершені блоки, відкладені провести за [резервом](recovery-handout.md), якщо він є.

'''
 if not assessed:
  ca,ua=teaching_actions(p)
  rows=[('0–3 хв','«Можна самостійно, у парі чи письмово; особисті історії не потрібні». Перевірити умови.','Позначка уроку й вибір способу роботи.'),('3–7 хв','«Знайди4 робочі слова; що вже знайоме?». Не перевіряти весь словник джерела.','Коротка проба з4 слів, невідоме можна позначити ?.'),('7–12 хв','Показати потрібну мовну/текстову опору. «'+g['model']+'»; у читанні/слуханні пояснити спосіб знайти доказ.','Один пробний приклад; не новий великий граматичний блок.'),('12–24 хв',ca,ua),('24–33 хв','«Заверши лише основний продукт, зазначений на аркуші. Якщо основне вже готове, виправ одну фразу або поясни доказ».','Завершений основний продукт; у граматиці — T, у читанні/слуханні —2 речення, у письмі — один текст.'),('33–40 хв','«Звір зміст за ключем/критеріями. Назви одну точну деталь та одну правку». Дозволити самоперевірку без обміну.','Одна помітна зміна, коротке пояснення. Не додавати новий контроль.'),('40–45 хв','«Exit: один точний факт/форма і наступний мовний крок». Дати ДЗ до5 хв.','Один рядок exit; позначка завершеного/перенесеного.')]
 else:
  diag=l['kind']=='pair_diagnostic';lr='слухання і читання' in l['topic']
  if lr:
   rows=[('0–4 хв','Пояснити L/R-критерії; відділити додаток L; перевірити чутність без відповідей.','Учні читають тільки запитання.'),('4–13 хв','Прочитати L двічі, між читаннями45 секунд; зібрати відповіді L.','3 самостійні відповіді; непочуте через технічні умови перенесено.'),('13–30 хв','«R: прочитай два тематичні повідомлення, дай3 відповіді з доказами».','R1–R3; довший текст має17 хв, а не час короткого розігріву.'),('30–40 хв','«Перевір тільки R за текстом; L після здавання не змінюй».','Власне редагування й здавання.'),('40–45 хв','Зафіксувати окремі L/R і відкладені блоки; короткий відгук про стратегію після збору.','Заплановано повернення тільки до незавершеного.')]
  elif diag:
   rows=[('0–4 хв','Пояснити4 блоки, відділити L; ключі й моделі закриті.','Читання запитань без відповідей.'),('4–12 хв','Двічі прочитати L з паузою45 секунд; зібрати L.','L1–L3.'),('12–22 хв','«R з попереднього юніту:3 факти».','R1–R3 із підтвердженнями.'),('22–31 хв','S: тихе планування2 хв, потім слухати реально доступну кількість пар/учнів. Інші починають P.','Частина S реально почута; решту відкладено, без вигаданих балів.'),('31–41 хв','«Заверши компактний P:4–6 речень або6 реплік відповідно до теми».','Один письмовий продукт.'),('41–45 хв','Зібрати, позначити відкладені S/інші блоки та індивідуальний наступний крок.','Окремі L/R/S/P; не стверджувати, що кожен учень уже пройшов S.')]
  else:
   rows=[('0–4 хв','Пояснити S/P-критерії; дати вигадану тему поточного юніту.','Умову прочитано; камера не потрібна.'),('4–9 хв','«План —6 ключових слів; заучений учительський текст не даємо».','План S та P.'),('9–25 хв','Слухати короткі S, решта пише P. Для великого класу S розділити на кілька зустрічей.','Лише реально почуті усні зразки мають оцінку S; інші відкладені.'),('25–37 хв','«P: завершити4–6 речень /6 реплік за тематичною умовою».','Самостійний письмовий продукт.'),('37–41 хв','«Перевір потрібні деталі, послідовність, одну мовну модель».','Власне редагування.'),('41–45 хв','Зібрати; узгодити продовження неотриманих S.','Окремі результати письма та реально почутого говоріння.')]
 s+='## A · Клас,45 хв\n\n'+table(rows)
 s+='''\n## B · Укриття,15 хв після прибуття

Без дозволу/умов читання — переносимо, не намагаємося проводити урок. Навіть за дозволених умов це тихий мінімум, а не стиснуті всі45 хв. Для контролю — тільки підготовка; L/S і самостійні блоки перевіряємо пізніше.

'''+table([('0–2 хв','«Можна тихо читати/писати або відкласти».','Знайдено перший доступний основний пункт.'),('2–6 хв','«Прочитай опору/текст/умову. Обери2 пункти; у L після відділення додатка це вже читання, не аудіювання».','Два підкреслені факти або2 форми/план2 реплік.'),('6–11 хв','«Запиши2 короткі відповіді чи2 тематичні репліки. Не потрібно великого продукту».','Два рядки на папері.'),('11–13 хв','«Звір одну відповідь з опорою, якщо це навчальний етап».','Одна перевірена деталь; підтримку позначено.'),('13–15 хв','«Познач завершене. Решту повернемо в доступних умовах».','Зафіксовано незавершене; без фото й публічного звіту.')])
 s+='''\n## C · Дистанційно,45 хв, камера добровільна

Пакет передати до уроку. Паперовий рядок або приватний чат є допустимим входом. Відсутність відповіді без з’ясування умов не дорівнює відмові. Після втрати зв’язку — D, подання при наступному доступному контакті. Чат свідчить про письмову взаємодію; для S потрібний пізніший реально почутий голос без вимоги камери.

'''+table([('0–4 хв','«Напиши номер уроку або почни на папері. Камера за бажанням».','Номер/перший рядок, перевірка доступності.'),('4–10 хв','Передати4 слова й коротку модель звичайним текстом; під час контролю — лише інструкцію/критерії.','Проба1 прикладу або читання самостійної умови.'),('10–23 хв','«Виконай перший основний блок». Для L читати двічі; якщо не чути — перенести L.','Продукт чату1: нумеровані відповіді/план; у контролі приватне подання.'),('23–34 хв','«Заверши основний продукт за аркушем». S слухати коротко голосом; можна відкласти, якщо немає каналу.','Продукт чату2:4–6 речень/6 реплік або2 перенесення G. Письмове не називати усним.'),('34–41 хв','«Перевір одну деталь; виправ одну фразу». У контролі — самоперевірка до здавання, відповіді не показувати.','Виправлений рядок/зданий блок.'),('41–45 хв','Підтвердити подання, записати недоступне й наступний крок.','Exit або паперова позначка; пізнє подання через збій приймається.')])
 s+='''\n## D · Асинхронно,12 хв на папері

Тільки пізніше в безпечному місці з достатнім світлом.0–2 хв: прочитай опору/умову.2–6 хв: виконай перші2 доступні пункти або сплануй2 репліки.6–10 хв: перевір одну відповідь і напиши одну власну фразу.10–12 хв: познач завершене/питання й збережи аркуш. Якщо пакета не було — видати після відновлення контакту. Не вимагаємо інтернету/фото. Для контрольного уроку це підготовка; L/S і самостійну перевірку перенести на резерв, не підміняти письмом.

## Мінімум, підтримка та резерв

- A/C: лише перелік основного навантаження на початку. B/D:2 відповіді/репліки й одна перевірена фраза. Непотрібні в цьому уроці вправи не друкуються на основному учнівському аркуші.
- Підтримка:4 переклади, модель, коротка відповідь ключовими словами; P можна скоротити до3 речень; S — спершу записати. Вказати, яка підтримка була, не вимагати особистого пояснення причин.
- Поглиблення/резерв: одне перефразування з поясненням або додаткове T. Лише замість уже завершеного блоку, не ще один набір обов’язкових вправ.
- ДЗ до5 хв: завершити основний продукт або перевірити одну фразу й пояснити зміну. Після B/D —2 рядки. Після контролю — навчальна рефлексія, не повторний бал за домашнє переписування.
- [Дві ігрові симуляції](games.md): навчальна7 хв і перевірна5 хв. Кожна замінює відповідний блок A/C; не додається до45 хв. У B/D допускається тільки тихий один хід за наявних умов.

## Оцінювання та факт проведення

'''+rubric(p)+''' Це авторські первинні показники, не автоматична офіційна оцінка. Затверджений у закладі порядок застосовується окремо. Емоції/камера/особисті розповіді не оцінюються. Під час контролю модель/словник учителя закриті, крім заздалегідь погоджених адаптацій. У ключі є резерв відкладених блоків; не оцінювати двічі завершений блок. Заповнити [report.md](report.md) за реальними фактами.
'''
 return s
PROFILE_BEFORE_ASSESSMENT=profile
def profile(l):
 p=PROFILE_BEFORE_ASSESSMENT(l)
 p['s_task']='За темою поточного юніту створіть6 реплік. A називає вигадану ситуацію/пропозицію; B ставить змістове запитання й просить уточнення; A відповідає; поміняйтеся ролями.'
 if l['kind']=='semester_assessment' and 'говоріння і письмо' in l['topic']:
  if l['semester']==1:
   p['s_task']='S: у6 репліках обговоріть вигадану кулінарну картку для свята: назва страви,2 інгредієнти, запит про вже перевірений список і ввічливе уточнення. Картка: fruit salad; apples, bananas; ingredients checked.'
   p['task']='P: напиши5 речень про вигадану шкільну подію: назва, що роблять зараз,2 справи підготовки вчора, спосіб долучитися без публічного виступу. Використай Present Continuous і Past Simple.'
   p['model']='Our school is preparing an exhibition. We are writing labels now. Yesterday Sam swept the floor. Alex made decorations. You can add a written caption instead of giving a speech.'
  else:
   p['s_task']='S: у6 репліках обговоріть вигаданий фільм і потребу персонажа: жанр, оцінка з причиною, ввічливе прохання повторити та прохання допомоги відповідального дорослого. Без діагнозу/ліків. Картка: comedy; lively dialogue; character asks for an adult.'
   p['task']='P: напиши5 речень для вигаданої поїздки на спортивну подію:2 об’єкти маршруту, факт про організований матч у Past Simple Passive, вибір двох маршрутів, причина й завершення.'
   p['model']='Our route includes a castle and a sports hall. A school match was organised in the hall. Choose either the short route or the long route. I suggest the short route because it includes a quiet stop. Finish at the castle gate.'
 return p


def teacher_key(p):
 l=p['source'];n=p['number'];g=p['g'];mode=p['mode'];s=f'''# Ключ · 7 клас · {n:03d} · {l['date']}

Відповіді лише для вчителя. Короткий синонімічний факт прийнятний; не знімати вдруге бал за форму, яка не змінює зрозумілий факт. Тут є резерви вчителя: вони не є вимогою виконати всі блоки за45 хв.

## R · Повний текст, факти й докази

{p['r']['text']}

{qkey(p['r'])}

'''
 if n==136:s+='4. The health-room card asks a responsible adult for help.\n\n'
 s+='## L · Текст для двох читань\n\nВідділити додаток L в учня до слухання. Прочитати двічі, між читаннями45 секунд. Не підказувати інтонацією тільки потрібні слова. За відсутності чутності перенести L.\n\n'+p['a']['text']+'\n\n'+qkey(p['a'])+'\n\n'
 s+='## V · Відповідності\n\n'+matching(p)[1]+'. По1 за відповідність; /4, лише коли V є основним блоком.\n\n'
 s+='## G · Форми\n\n'+'\n'.join(f'{i}. {a}.' for i,(_,a) in enumerate(g['items'],1))+'\n\n'+g['rule']+'\n\n'
 s+='## T · Перенесення моделі\n\n'+'\n'.join(f'{i}. {a}' for i,(_,a) in enumerate(TRANSFER[p['gid']],1))+'\n\nКожна відповідь має зберігати зміст, часову форму та структуру; інше граматично правильне формулювання прийнятне за збереження умови.\n\n'
 s+='## F · Повна корекція\n\n'+ERRORS[p['gid']][1]+'\n\nПояснення: '+g['rule']+' Для портфоліо2 пояснення можуть бути українською. Наступний крок має бути конкретною дією, наприклад перевірити auxiliary verb.\n\n'
 s+='## P / S · Умова та повний зразок\n\n'+p['task']+'\n\n**Зразок:** '+p['model']+'\n\n'
 if mode=='assessment':
  s+='**Умова S:** '+p['s_task']+'\n\n'
  if l['kind']=='semester_assessment' and 'говоріння і письмо' in l['topic']:
   smodel='A: What are we preparing? B: Fruit salad with apples and bananas. A: Have you checked the ingredients? B: Yes, I have checked them. A: Could you repeat the second ingredient? B: Bananas.' if l['semester']==1 else 'A: What kind of film is it? B: A comedy with lively dialogue. A: Why do you recommend it? B: Because the dialogue is lively; the character also asks for an adult. A: Could you repeat that request? B: Please call the responsible adult.'
  else:smodel=S_MODELS[p['u']]
  # Keep English in a sample dialogue; the Ukrainian unit title is teacher metadata only.
  english_topic={0:'a study group',1:'a school exhibition',2:'a chore plan',3:'a paper recipe',4:'a fictional celebration',5:'a sports report',6:'a request for adult help',7:'a film review',8:'an imaginary route'}[p['u']]
  smodel=smodel.replace(BANK[p['u']]['title'],english_topic)
  s+='**Зразок S:** '+smodel+'\n\n'
 s+='''## Відкриті відповіді: конкретні критерії

- Зміст0–2:0 немає потрібної дії/теми;1 основна мета зрозуміла, але бракує обов’язкової деталі;2 усі деталі з умови присутні. У читанні/слуханні не додавати непідтверджених фактів.
- Організація0–2:0 послідовність не відновлюється;1 зв’язок зрозумілий із підтримкою;2 логічний текст або взаємний обмін репліками.
- Мовна зрозумілість0–2:0 зміст не відновлюється;1 помилки не руйнують основний зміст;2 цільові слова/структури переважно точні. У T обов’язкова саме модель, названа в умові.

Для S потрібен реально почутий зразок; письмовий чат підтверджує письмову взаємодію. Вимову оцінювати за зрозумілістю, не за акцентом. Пауза/відсутність камери не є помилкою. У проєкті доказ — чернетка, точний відгук,2 зміни; у портфоліо —3 корекції,2 причини, власна модель й наступний крок. Особисте переживання/емоція не оцінюється.

## Критерії саме цього уроку

'''+rubric(p)+' Це первинні показники для педагогічного рішення; офіційне переведення визначає затверджений порядок закладу.\n\n'
 if mode=='assessment':
  rr=alternate(p['r']);aa=alternate(p['a'])
  s+='## Резерв після переривання\n\nОкремий друк: [recovery-handout.md](recovery-handout.md). Проводити тільки відкладені блоки; завершене не перевіряти вдруге. Критерії ті самі. Нові персонажі/деталі не повинні змінювати складність. Якщо учень уже прочитав L, дати резервне L.\n\n**Резерв R:**\n\n'+qkey(rr)+'\n\n**Резерв L — прочитати двічі:**\n\n'+aa['text']+'\n\n'+qkey(aa)+'\n\nРезерв S/P: інші вигадані деталі при збереженому форматі; зразок вище — один можливий, критерії не змінюються.\n\n'
 s+='## ДЗ\n\nДо5 хв: завершений основний продукт або одна перевірена фраза з поясненням правки. Після B/D —2 рядки. Приймати варіанти за критеріями умови; після контролю домашнє переписування не створює нової самостійної оцінки.\n'
 return s


def report(p):
 l=p['source']
 return f'''# Фактичний звіт · 7 клас · {l['number']:03d}

Заплановано: {l['date']} · {l['topic']}

Порожній шаблон, не підтвердження проведення.

- Фактична дата, час, тривалість: ______________________________________
- Маршрут A / B / C / D / перенесено: __________________________________
- Дозвіл/умови читання для B (без персональних відомостей): ______________
- Переривання й останній завершений код: ______________________________
- Реально виконаний основний мінімум: _________________________________
- Використана симуляція/який блок замінила: ____________________________
- Кількість наданих / відкладених робіт: _______________________________
- Реальні докази R / L / S / P (окремо): ________________________________
- Рівень самостійності / підтримка / повтор у грі: ______________________
- Типова мовна помилка й наданий відгук: _______________________________
- Вибір способу участі / SEL без оцінки емоцій: ________________________
- Фактичне ДЗ: ________________________________________________________
- Незавершені блоки контролю / дата резерву: ___________________________
- Місток повернення й наступний крок: _________________________________
- Примітка для журналу після перевірки факту: __________________________

Не записувати тут персональні оцінки, діагнози, контакти чи приватні посилання. Заповнені документи зберігати в дозволеній закладом системі, не у публічному репозиторії. Письмовий чат не позначати як усне мовлення, прочитаний L — як аудіювання.
'''
S_MODELS={
0:simple_product(0)[1],
1:'A: Which club would you choose? B: The library club. A: Why? B: Because I enjoy books. A: Could you name a quiet role? B: I can write a recommendation.',
2:PRODUCT[27][1],
3:'A: What shall we put on the paper recipe? B: Apples and bananas. A: Have you checked the list? B: Yes, I have checked it. A: Could you repeat the first ingredient? B: Apples.',
4:'A: What is made for the celebration? B: Paper cards are made. A: Who makes them? B: Volunteers make them. A: Can guests observe quietly? B: Yes, that choice is accepted.',
5:'A: What was organised yesterday? B: A school game was organised. A: Who checked the equipment? B: The coach checked it. A: Could you repeat that detail? B: The equipment was checked by the coach.',
6:PRODUCT[94][1],
7:PRODUCT[111][1],
8:'A: What is on the route? B: A castle and a garden. A: Which route do you suggest? B: The short route because it has a quiet stop. A: Could you repeat the last stop? B: The castle gate.',
}
# Cards for speaking/writing games use actual lesson products, not unrelated event data.
PRODUCT_CARDS={
11:[('Which club is chosen in the example?','The library club'),('Why is it chosen?','I enjoy recommending books')],
12:[('What event is being prepared?','an anniversary exhibition'),('Which non-speaking contribution is offered?','write a label')],
27:[('Which job can A do?','make decorations'),('Which job can B do?','tidy the tables')],
28:[('Which job did the writer do?','swept the floor'),('What does the writer ask to share?','the jobs')],
42:[('Which utensil is described?','a grater'),('What is its function?','grating food')],
43:[('Which dish is described?','fruit salad'),('Which two utensils are named?','a bowl and a spoon')],
56:[('What do the fictional guests write?','thank-you notes'),('Which alternative does A suggest?','draw a card')],
57:[('What is decorated in the imaginary family?','paper eggs'),('What else is written?','greeting cards')],
75:[('Which sport is on the card?','Underwater hockey'),('Which two pieces of equipment are named?','A stick and a puck')],
76:[('Which club is open?','The table tennis club'),('Which alternative role is offered?','a reporter')],
77:[('Which sport does the fictional athlete play?','table tennis'),('What does the writer admire?','fair play')],
94:[('What symptom does the character describe?','a sore throat'),('Whom does B offer to call?','the responsible adult')],
95:[('What symptom did the fictional character have?','a sore throat'),('Who listened?','A nurse')],
111:[('Which genre is recommended?','a comedy'),('Why is it recommended?','The dialogue is quite funny')],
112:[('What do the robots lose?','a map'),('Why is the dialogue lively?','the characters disagree politely')],
128:[('Which place is on the card?','River Castle'),('Which two features are named?','Two towers and a small garden')],
129:[('What two attractions are on the route?','the castle and a public garden'),('Which route includes a quiet stop?','the short route')],
}

def simulation_cards(p):
 mode=p['mode'];n=p['number']
 if mode in ('grammar','review','portfolio'):
  cards=[]
  for q,answer in p['g']['items'][:2]:
   options=q.rsplit('(',1)[1].rstrip(')').split(' / ');wrong=next(x for x in options if x!=answer)
   cards.append({'prompt':q,'answer':answer,'wrong':wrong,'source':p['g']['rule']})
  return cards
 if mode=='vocabulary':
  return [{'prompt':f'Який вираз означає «{p["lex"][i][1]}»?','answer':p['lex'][i][0],'wrong':p['lex'][i+2][0],'source':p['lex'][i][0]+' — '+p['lex'][i][1]} for i in range(2)]
 if n in PRODUCT_CARDS:
  qs=PRODUCT_CARDS[n];return [{'prompt':q,'answer':a,'wrong':qs[1-i][1],'source':p['model']} for i,(q,a) in enumerate(qs)]
 target=p['a'] if mode=='listening' else p['r']
 return [{'prompt':q['question'],'answer':q['answer'],'wrong':target['qas'][(i+1)%3]['answer'],'source':target['text']} for i,q in enumerate(target['qas'][:2])]


def games(p):
 n=p['number'];l=p['source'];cards=simulation_cards(p)
 r='\n\n'.join(f"**Картка {i}:** {c['source']}\n\nЗапит: {c['prompt']}\n\nВибір A: {c['answer']}\n\nВибір B: {c['wrong']}" for i,c in enumerate(cards,1))
 # Answer positions alternate; the second game reverses them, removing a mechanical always-A key.
 c1,c2=cards
 material1=f"Хід1: {c1['prompt']} A — {c1['answer']}; B — {c1['wrong']}.\n\nХід2: {c2['prompt']} A — {c2['wrong']}; B — {c2['answer']}."
 material2=f"Квиток1: {c2['prompt']} A — {c2['answer']}; B — {c2['wrong']}.\n\nКвиток2: {c1['prompt']} A — {c1['wrong']}; B — {c1['answer']}."
 return f'''# Дві симуляції · 7 клас · {n:03d} · {l['date']}

**Тема:** {l['topic']}  
**Мовний результат дати:** {p['task']}

Це teacher-only сценарії для паперу/чату. Герої вигадані; камери, руху, гучних сигналів, реальних особистих історій не потрібно. Кожна гра замінює час у плані A/C; не додається зверху до45 хв. У контролі ігрова перевірка — окремий формувальний зразок, не заміна офіційних блоків L/R/S/P. За тривоги зупинити; під час переміщення не грати. B — лише після прибуття/дозволу/умов; якщо їх немає, перенести. D — пізніше у безпечному місці зі світлом.

## 1 · Редакція матеріалу: навчання,7 хв

**Роль і мета:** учень — редактор картки з теми «{l['topic']}»; учитель — замовник. Редактор має допустити2 точні рядки й виправити неточний вибір. Це засвоєння з дозволеною опорою.

**Стартовий стан:**0 із2 рядків підтверджено; джерело видно. Учитель читає/показує дві картки нижче; учень має олівець або приватний чат. Для граматики джерело — правило, для лексики — словник, для інших — конкретний текст/зразок цієї дати.

**Готові джерела:**

{r}

**Ходи та наслідки:**

{material1}

- Хід1: A → перший рядок прийнятий (стан1/2); B → рядок залишається в чернетці (стан0/2). Учитель каже: “Check which words answer this exact question.” Учень повертається до видимого джерела й повторює тільки цей хід.
- Хід2: B → другий рядок прийнятий; A → не затверджуємо рядок, повертаємося до відповідної картки. Після повтору записуємо «з підтримкою», не стираємо першу спробу.

**Англійські репліки:** “I choose … because the card says …”; “Could you repeat the question?”; “I will change this word.” Учень може спершу записати репліку.

**Стан успіху:**2/2 точних вибори й одна власна фраза з матеріалу. Для граматики — завершене речення з вибраною формою; для лексики — осмислений контекст; для читання/слухання — точний факт; для P/S — рядок, що виконує умову продукту. Орієнтир відкритого продукту: **{p['model']}**. Прийняти інші зрозумілі варіанти, які зберігають потрібний факт/форму й тему.

**Мовний доказ:** аркуш із2 виборами, підкреслене слово-доказ,1 виправлена/створена фраза. Оцінка емоцій чи швидкості не потрібна.

**Час на заміну:**0–1 хв ролі;1–3 перший хід;3–5 другий;5–6 власна фраза;6–7 фіксація підтримки. Замінити7 хв основного тренувального блоку12–24, решту цього блоку присвятити одному перенесенню. Не виконувати той самий обсяг вправ ще раз.

## 2 · Пропуск до публікації: перевірка,5 хв

**Роль і мета:** учень — незалежний інспектор, що перевіряє2 нові квитки за тим самим матеріалом. Порядок карток та відповідей змінений. Мета — самостійно встановити, який рядок відповідає запиту, а не вгадати постійну букву.

**Стартовий стан:**0/2 квитків перевірено; учитель не показує ключ, модель продукту й пояснення першої гри. У читанні текст залишається; у лексичному/граматичному пригадуванні словник/правило закриті. Для слухання текст не показують: учитель читає відповідне джерело двічі й фіксує L лише за реальної чутності. Якщо джерело прочитане учнем, це R.

{material2}

**Перші2 ходи:** учень записує обидві відповіді до будь-якого зворотного зв’язку. Ключ: квиток1 — **A: {c2['answer']}**; квиток2 — **B: {c1['answer']}**. Правдоподібний варіант за темою ще не є підтвердженою відповіддю; перевірити саме запит і доказ. Кожний правильний вибір дає1 первинний бал.

**Перехід стану:**2/2 → “Ready to publish”;1/2 → “One detail needs checking”;0/2 → “Return to the source”. Це стан тексту, не ярлик учня. Після фіксації першої спроби показати джерело; дати один повтор як навчання, окремо позначений «після підказки».

**Додатковий мовний доказ (без нового прихованого бала):** учень завершує “The correct detail is …” або записує один правильний рядок. В усній взаємодії вчитель має реально почути коротку репліку; чат і записаний сценарій не є доказом говоріння. Відкрита відповідь прийнятна, якщо передає точний факт/форму, відповідає темі й зрозуміла адресату; приклад — модель вище.

**Час на заміну:**0–1 хв інструкція;1–3 два самостійні ходи;3–4 фіксація2 первинних відповідей;4–5 відгук і один навчальний повтор. Замінити5 хв перевірки33–40; для довшого слухового джерела замінити весь7-хвилинний блок і скоротити повтор до наступної зустрічі. Не додавати5 хв до45.

## Варіанти доступу та фіксація

- Папір у класі: учитель виписує лише2 запити/вибори й потрібне джерело, ключ тримає у своїй копії. Учень позначає букви й одну фразу; виграш не потребує швидкості.
- Тихе укриття: тільки після дозволу й за умов читання; один хід мовчки на папері замість частини B. Слухання не проводимо; цей слід позначаємо читанням/мовним вибором. Немає умов — перенести.
- Чат без камери: джерело та2 запити звичайним текстом; учень надсилає “1A;2B” і одну фразу приватно. Це письмовий доказ, не автоматично усний.
- Соло/без електрики: паперова копія видана заздалегідь; учень робить вибори й підкреслює доказ, ключ відкриває після першої спроби або звіряє з учителем пізніше. Тільки у безпечному освітленому місці.

У report.md: назва гри, замінений блок, первинні2 відповіді, підтримка/повтор окремо, реально отриманий вид мовного доказу. Не створювати оцінок за емоції, камеру чи особисті розповіді.
'''
# Checked primary-source facts preserve lessons about known institutions/people.
READING[69]=passage('The Olympic Movement names three core values: excellence, respect and friendship. A fictional class makes one paper poster for each value. The respect poster shows a player thanking an opponent. The friendship poster shows people helping each other learn. The pupils discuss the Olympic values, not current medal tables or a test of physical ability.',('Which three core values are named?','excellence, respect and friendship'),('What does the respect poster show?','a player thanking an opponent'),('What do the friendship characters help each other do?','learn'))
READING[70]=passage('An interviewer at a classroom Olympic exhibition asks: What are the three core values? The guide answers: excellence, respect and friendship. The interviewer then asks for a classroom example of respect. The guide points to a drawing of a player thanking an opponent. This drawing is invented, but the names of the three values come from the Olympic Movement.',('What are the three core values?','excellence, respect and friendship'),('Which value needs an example?','respect'),('What is the player in the drawing doing?','thanking an opponent'))
READING[105]=passage('Two factual cards introduce known opera houses. The Royal Opera House is in London’s Covent Garden. The National Opera of Ukraine is in Kyiv and bears the name of Taras Shevchenko. A fictional pupil compares the city names and the names of the buildings. The cards do not give ticket prices or today’s programme; those details would need a new check.',('Where in London is the Royal Opera House?','Covent Garden'),('In which city is the National Opera of Ukraine?','Kyiv'),('Whose name does the Ukrainian institution bear?','Taras Shevchenko'))
READING[106]=passage('The National Opera of Ukraine is a known theatre in Kyiv. Its building opened in 1901. The architect was Viktor Shreter. A fictional pupil uses these three checked facts in a short presentation: name, city and building history. The pupil distinguishes these facts from a personal comment about the architecture. No current performance date or ticket price is invented.',('In which city is this theatre?','Kyiv'),('When did its building open?','1901'),('Who was the architect?','Viktor Shreter'))
READING[51]=passage('Two invented pen pals compare New Year celebrations in their own stories. Mia in Denmark describes exchanging written wishes before midnight. Leo in Colombia describes creating a paper calendar the next morning. These are fictional individual examples, not national traditions. The pupils compare the time and the activity, without saying everyone in either country celebrates alike.',('What is exchanged in Mia’s story?','written wishes'),('What is created in Leo’s story?','a paper calendar'),('Which two features do the pupils compare?','the time and the activity'))
PRODUCT[77]=('Напиши5-реченнєвий блог про відому плавчиню Яну Клочкову за факт-карткою: Ukraine; swimming;4 Olympic gold medals;1 Olympic silver medal. Додай особисту реакцію вигаданого автора; не вигадуй рекордів, тренувань чи цитат.','Yana Klochkova is a swimmer from Ukraine. Her sport is swimming. She won four Olympic gold medals. She also won one Olympic silver medal. I would like to learn more about her sporting career.')
PRODUCT_CARDS[77]=[('Which sport is named?','swimming'),('How many Olympic gold medals are named?','four')]
LISTENING[108]=passage('Charlie Chaplin was born in London in 1889. He became famous for his screen character, the Tramp. His film City Lights was made as a silent film. A fictional class uses these checked details to prepare a short actor profile. The pupils can describe the facts without copying a long biography or claiming that every Chaplin film was silent.',('Where was Chaplin born?','London'),('What was his famous screen character?','the Tramp'),('Which silent film is named?','City Lights'))
FACT_SOURCES={
69:[('IOC Olympic values','https://brand-centre.olympic.org/olympism')],
70:[('IOC Olympic values','https://brand-centre.olympic.org/olympism')],
77:[('World Aquatics: Klochkova medal record','https://www.worldaquatics.com/athletes/1038214/yana-klochkova/medals')],
105:[('Royal Ballet and Opera','https://www.rbo.org.uk/about/the-royal-ballet-and-opera'),('National Opera architecture','https://www.opera.com.ua/en/about/architecture')],
106:[('National Opera architecture','https://www.opera.com.ua/en/about/architecture')],
108:[('Official Chaplin biography','https://www.charliechaplin.com/en/articles/21-Overview-of-His-Life')],
119:[('UK Parliament: four nations','https://questions-statements.parliament.uk/written-questions/detail/2025-05-06/HL7177/')],
}

def validate_profile(p):
 """Content assertions, not merely presence of document headings."""
 for label in ('r','a'):
  text=p[label]['text'].casefold()
  assert len(p[label]['qas'])==3,(p['number'],label)
  for x in p[label]['qas']:
   assert x['answer'].casefold() in text,(p['number'],label,x)
   assert x['evidence'].casefold() in text,(p['number'],label,x)
 for question,answer in p['g']['items']:
  choices=question.rsplit('(',1)[1].rstrip(')').split(' / ')
  assert answer in choices,(p['number'],question,answer)
  assert len(choices)==2 and len(set(choices))==2
 for card in simulation_cards(p):
  assert card['answer']!=card['wrong'],(p['number'],card)
  if p['mode'] not in ('grammar','review','portfolio'):
   assert card['answer'].casefold() in card['source'].casefold(),(p['number'],card)
 assert 1<=len(p['core'])<=3
 for card in checking_cards(p):
  assert card['answer']!=card['wrong'],(p['number'],card)
  if p['mode'] not in ('grammar','review','portfolio'):
   assert card['answer'].casefold() in card['source'].casefold(),(p['number'],card)
 assert checking_cards(p) != simulation_cards(p),p['number']
 if p['mode']=='assessment':
  for label in ('r','a'):
   reserve=alternate(p[label]);assert reserve['text']!=p[label]['text']
   for q in reserve['qas']:assert q['answer'].casefold() in reserve['text'].casefold()


def build(p):
 validate_profile(p);l=p['source'];folder=BASE/f"{p['number']:03d}";folder.mkdir(parents=True,exist_ok=True)
 write(folder/'lesson.md',lesson_plan(p));write(folder/'handout.md',learner_sheet(p));write(folder/'key.md',teacher_key(p));write(folder/'report.md',report(p));write(folder/'games.md',games(p))
 if p['mode']=='assessment':write(folder/'recovery-handout.md',learner_sheet(p,True))
 if p['number'] in FACT_SOURCES:
  with (folder/'lesson.md').open('a',encoding='utf-8') as f:
   f.write('\n## Перевірені факт-джерела\n\nПеревірено18 жовтня2026; для паперової вправи інтернет не потрібний.\n\n'+'\n'.join(f'- [{name}]({url})' for name,url in FACT_SOURCES[p['number']])+'\n')
 return dict(number=p['number'],date=l['date'],topic=l['topic'],directory=f"{p['number']:03d}",source_id=l['source_id'],kind=l['kind'],focus=p['mode'],semester=l['semester'],calendar_status=l['calendar_status'])


def review_record(p):
 import hashlib
 l=p['source'];d=BASE/f"{p['number']:03d}"
 files=['lesson.md','handout.md','key.md']+(['recovery-handout.md'] if p['mode']=='assessment' else [])
 return dict(number=l['number'],date=l['date'],topic=l['topic'],focus=p['mode'],grammar=p['gid'],primary_load=p['core'],source_outcome=l['expected_learning_evidence'],adaptation=p['task'],reading_words=len(p['r']['text'].split()),listening_words=len(p['a']['text'].split()),closed_reading_checks=p['r']['qas'],closed_listening_checks=p['a']['qas'],closed_grammar_checks=[dict(prompt=q,answer=a) for q,a in p['g']['items']],simulation_checks=simulation_cards(p),simulation_parallel_checks=checking_cards(p),checked=['source_date_topic_unchanged','closed_answers_supported_by_supplied_text','grammar_keys_in_options','model_and_required_product_correspond','main_load_separate_from_teacher_reserve','safe_B_D_and_camera_optional','assessment_reserve_independence','two_themed_simulations_with_actual_keys'],limitations=['Аудит матеріалу, не classroom playtest.','Живе усне мовлення та доступність конкретного класу перевіряє вчитель; чат не є усним доказом.'],source_sha256={f:hashlib.sha256((d/f).read_bytes()).hexdigest() for f in files})


def main():
 source=json.loads((BASE/'source-plan.json').read_text(encoding='utf-8'))
 assert len(source['lessons'])==140
 assert [x['number'] for x in source['lessons']]==list(range(1,141))
 ps=[profile(l) for l in source['lessons']]
 rows=[build(p) for p in ps]
 write(BASE/'manifest.json',json.dumps({'grade':7,'academic_year':source['academic_year'],'lessons':rows},ensure_ascii=False,indent=2))
 write(BASE/'quality-review.json',json.dumps({'grade':7,'review_date':'2026-10-18','method':'Authorial methodological desk review plus exhaustive structured content checks; no classroom playtest.','lessons':[review_record(p) for p in ps]},ensure_ascii=False,indent=2))
 text='''# Службові матеріали вчителя · 7 клас · 2026/2027

140 календарних уроків:65 у I семестрі,75 у II. Номери, дати й теми точно з [очищеного джерела](source-plan.json); там походження й SHA-256 плану та каталогу. II семестр — проєкція джерела. План і порожній звіт не засвідчують факту проведення.

Кожен пакет: `lesson.md` — адміністративний план, опорний конспект, A45/B15/C45/D12, диференціація; `handout.md` — тільки основний учнівський обсяг, без універсального комплекту всіх вправ; `key.md` — повні ключі, моделі й учительський резерв; `report.md` — порожній шаблон факту; `games.md` —2 готові симуляції на заміну блоків. PDF: `handout.pdf`, `teacher.pdf`, `games.pdf`. Для8 перевірок також `recovery-handout.md` і `recovery-handout.pdf`; додаток L відділяють до слухання.

[Методичний аудит](QUALITY_REVIEW.md) описує конкретні недоліки й виправлення. [Поурочний аудит](quality-review.json) містить140 записів, мовні перевірки й SHA-256 актуальних lesson/handout/key/recovery. Генерація: `python3 scripts/build_teacher_grade7.py`; перевірка: `python3 tests/check_teacher_grade7_quality.py`. Стандартна бібліотека, локальні підручники не потрібні.

Матеріали авторські за конкретними цілями плану, не дослівні сторінки SB/WB та не офіційні вправи «Зерна». Додаткові компетентнісні коди й офіційні шкали не вигадано. Емоції, камера та особисті історії не оцінюються. Тексти про відомі театри, спортсменку й актора мають первинні факт-джерела в конспектах; решту особистих ситуацій можна вигадувати.

За тривоги навчання зупинити. Під час переміщення не вчити. B — лише після прибуття, дозволу й за умов читання; без руханок/аудіо/публічних особистих історій. Немає умов — переносити. D — пізніше у безпечному освітленому місці. Чат — письмовий доказ; L/S потребують реально почутого/прослуханого матеріалу. B/D не підтверджують повний контроль. Аркуші видати до відключень. Заповнені персональні звіти не комітити в публічний репозиторій. Ці службові матеріали не додаються у вебкаталог.

## Календарне покриття

| № | Дата | Тема | План / ключ / звіт | Учень | Симуляції |
|---|---|---|---|---|---|
'''
 for row in rows:
  d=row['directory'];rec=f' · [Резерв]({d}/recovery-handout.md)' if row['focus']=='assessment' else ''
  text+=f"| {row['number']} | {row['date']} | {row['topic']} | [План]({d}/lesson.md) · [Ключ]({d}/key.md) · [Звіт]({d}/report.md) · [PDF]({d}/teacher.pdf) | [MD]({d}/handout.md) · [PDF]({d}/handout.pdf){rec} | [MD]({d}/games.md) · [PDF]({d}/games.pdf) |\n"
 write(BASE/'README.md',text)
 print(f'Built and checked140 Grade7 packs,8 reserves,280 simulations.')


GAME_PARALLELS={
1:passage('A different fictional study group asks members to bring one question and a pencil. A learner may write a reply instead of reading it aloud. The group chooses one helper to repeat instructions calmly.',('What should members bring besides a question?','a pencil'),('What may a learner write instead of reading aloud?','a reply'),('Who repeats instructions?','one helper')),
37:passage('Another fictional food artist plans a paper picture of a bird. Yellow shapes form its wings, and green shapes form the leaves around it. The artist makes a sketch before arranging paper shapes. No real food or sharp tool is used.',('What animal is in the planned picture?','a bird'),('Which colour forms the wings?','Yellow'),('What does the artist make first?','a sketch')),
51:passage('In a new invented New Year story, Ada writes a greeting before midnight. Ben makes a paper calendar after breakfast. They compare the order of activities and ask before sharing a picture of the celebration.',('What does Ada write?','a greeting'),('When does Ben make a calendar?','after breakfast'),('What do they ask before sharing?','a picture')),
69:passage('At a different Olympic-values display, a friendship card shows a team helping a newcomer. An excellence card shows an athlete practising a new skill. A respect card shows a player thanking the referee. These are invented examples of the three Olympic values.',('Whom does the team help on the friendship card?','a newcomer'),('What is the athlete practising?','a new skill'),('Whom does the player thank?','the referee')),
70:passage('A new Olympic-values interviewer asks which card shows respect. The guide points to a drawing of a player thanking the referee. A second question asks how the friendship card is different: it shows a team helping a newcomer.',('Whom does the player thank?','the referee'),('Whom does the team help?','a newcomer'),('Which value is on the first card?','respect')),
77:passage('A second checked medal card for Yana Klochkova lists four Olympic gold medals and one Olympic silver medal. That makes five Olympic medals in total. The pupil writes the total and the silver count, without inventing other records.',('How many Olympic silver medals are on the card?','one'),('How many Olympic medals are there in total?','five'),('How many gold medals are on the card?','four')),
108:passage('A second factual card about Charlie Chaplin gives his birth year as 1889. It identifies City Lights as a silent film. A fictional museum visitor copies only these two checked details for a new short profile.',('What birth year is given?','1889'),('Which silent film is identified?','City Lights'),('What kind of visitor copies the facts?','A fictional museum visitor')),
119:passage('A second classroom map has four United Kingdom name cards. The card above England is labelled Scotland. The card west of England is labelled Wales. A separate card reads Northern Ireland. Pupils read the names on this simplified paper layout.',('Which card is above England?','Scotland'),('Which card is west of England?','Wales'),('What does the separate card read?','Northern Ireland')),
120:passage('A new draft city post is headed Dublin. Its classroom map has a museum and a public garden. A peer asks for a title and one reason to choose the short route. The writer adds: it includes a quiet stop. This is an invented itinerary, not travel guidance.',('What is the heading of the new post?','Dublin'),('Which two places are on this map?','a museum and a public garden'),('Why choose the short route?','it includes a quiet stop')),
122:passage('A second classroom landmark card is labelled Tower Bridge. Its paper drawing has two towers and a crossing over water. A different card is labelled the Sydney Opera House. Learners copy only the names and details shown, without inventing prices or visit dates.',('Which named bridge is on the first card?','Tower Bridge'),('How many towers are in its drawing?','two towers'),('Which opera house labels the other card?','the Sydney Opera House')),
123:passage('A different fictional Kyiv leaflet begins at a museum meeting point. Its two labelled stops are Golden Gate and a library. A quiet reading break comes after the library stop. The route ends at the museum meeting point; no real address is supplied.',('Which stop follows Golden Gate on the list?','a library'),('When is the reading break?','after the library stop'),('Where does the route end?','the museum meeting point')),
}
READING_PAIR={2:3,3:2,5:6,6:5,18:19,19:18,21:22,22:21,33:34,34:33,36:37,48:49,49:48,66:67,67:66,84:85,85:84,87:88,88:87,102:103,103:102,105:106,106:105}

# Lesson-specific new situations for productive-mode checks; independent of the first model.
PRODUCT_PARALLEL={
11:passage('A new poll asks fictional Sam about the drama club. Sam chooses poster design because drawing is enjoyable. The interviewer records one vote for a quiet design role.',('Which club is in this new poll?','the drama club'),('Which role does Sam choose?','poster design'),('Why?','drawing is enjoyable')),
12:passage('A new school website draft describes a book day. One group is arranging books; another is making recommendations. A quiet role is writing a caption for the display.',('Which event is described?','a book day'),('What is the first group arranging?','books'),('Which quiet role is offered?','writing a caption')),
27:passage('For a different fictional celebration, Kim offers to arrange chairs. Robin offers to write labels. They ask each other to repeat the jobs before finalising the chart.',('Which job does Kim offer?','arrange chairs'),('Which job does Robin offer?','write labels'),('What do they ask each other to repeat?','the jobs')),
28:passage('A new message says: Yesterday I dried the dishes. My friend fed the pet. Could we swap the jobs tomorrow? Thank you for checking our plan.',('Which job did the writer do?','dried the dishes'),('Which job did the friend do?','fed the pet'),('What does the writer request?','swap the jobs')),
42:passage('A new kitchen-tool card labels a whisk. It is used for mixing ingredients. Pupils copy the name and function onto a paper chart without using the tool.',('Which tool is labelled?','a whisk'),('What is its function?','mixing ingredients'),('Where do pupils copy the information?','a paper chart')),
43:passage('A new fictional dish is a cold sandwich. Its ingredients are bread, cheese and cucumber. Its paper utensil list has a plate and a spoon. The writer likes the clear ingredient list.',('Which dish is described?','a cold sandwich'),('Name the three ingredients.','bread, cheese and cucumber'),('Which utensils are listed?','a plate and a spoon')),
56:passage('A different invented Thanksgiving family thanks guests with a drawing. Guests may leave a written greeting instead of speaking. The host asks permission before sharing the drawings.',('How does the host thank guests?','a drawing'),('What may guests leave instead of speaking?','a written greeting'),('What is asked before sharing?','permission')),
57:passage('A different imaginary Easter email describes paper flower cards. The family also writes wishes for friends. A guest may observe quietly. The writer ends by inviting a reply.',('What kind of cards are described?','paper flower cards'),('What else is written?','wishes for friends'),('What may a guest do?','observe quietly')),
75:passage('A different sport card is labelled water polo. It shows a pool, two teams and a ball. The speaker clarifies that a stick and a puck belong to the other underwater hockey card.',('Which sport labels the new card?','water polo'),('Which playing object does it show?','a ball'),('Which items belong to the other card?','a stick and a puck')),
76:passage('A new club card offers a chess club on Tuesday at two. A learner can join as a scorekeeper. The organiser repeats the time when asked.',('Which club is offered?','a chess club'),('When does it meet?','Tuesday at two'),('Which role is offered?','a scorekeeper')),
94:passage('A different fictional visitor says: I have a headache. Could you repeat the question? The receptionist offers to contact the responsible adult. No one in the language exercise gives a diagnosis.',('What symptom does the visitor describe?','a headache'),('What does the visitor ask to hear again?','the question'),('Whom will the receptionist contact?','the responsible adult')),
95:passage('A different fictional email says the character had a headache. A responsible adult helped the character contact a nurse. The writer reports that conversation without naming medicine or suggesting treatment.',('What symptom is in the new email?','a headache'),('Who helped contact a nurse?','A responsible adult'),('What is not named?','medicine')),
111:passage('A new invented film is a musical called Paper Stars. The viewer recommends it because the songs are memorable. A partner prefers a comedy; both choices are accepted.',('Which genre is Paper Stars?','a musical'),('Why is it recommended?','the songs are memorable'),('Which genre does the partner prefer?','a comedy')),
112:passage('A new fictional review describes Paper Stars, a musical. Two friends prepare a school show. The reviewer likes the songs because they are memorable and the plot because it is clear.',('Which genre is reviewed?','a musical'),('What do the two friends prepare?','a school show'),('Why are the songs praised?','they are memorable')),
128:passage('A new drawn landmark card is labelled Hill Museum. It shows three windows and a small courtyard. The presenter repeats the second feature after a listener asks for clarification.',('What is the landmark called?','Hill Museum'),('How many windows are shown?','three'),('What is the second feature?','a small courtyard')),
129:passage('A new imaginary route starts at Hill Museum. It includes a gallery and a public square. The short route is chosen because it has a quiet bench. It ends at the museum gate.',('Which two attractions are included?','a gallery and a public square'),('Why is the short route chosen?','it has a quiet bench'),('Where does it end?','the museum gate')),
}

def checking_cards(p):
 mode=p['mode'];n=p['number']
 if mode in ('grammar','review','portfolio'):
  out=[]
  for q,answer in p['g']['items'][2:]:
   choices=q.rsplit('(',1)[1].rstrip(')').split(' / ')
   out.append(dict(prompt=q,answer=answer,wrong=next(x for x in choices if x!=answer),source=p['g']['rule']))
  return out
 if mode=='vocabulary':return [dict(prompt=f'Який вираз означає «{p["lex"][i][1]}»?',answer=p['lex'][i][0],wrong=p['lex'][i+2][0],source=p['lex'][i][0]+' — '+p['lex'][i][1]) for i in (2,3)]
 if n in PRODUCT_PARALLEL:t=PRODUCT_PARALLEL[n]
 elif n in GAME_PARALLELS:t=GAME_PARALLELS[n]
 elif n==36:t=LISTEN_PARALLEL[39]
 elif n in READING_PAIR:t=READING[READING_PAIR[n]]
 elif mode=='listening':t=LISTEN_PARALLEL[n]
 else:t=alternate(context(p['u'],n,0))
 qs=t['qas'][1:] if n==105 else t['qas'][:2]
 return [dict(prompt=q['question'],answer=q['answer'],wrong=t['qas'][(i+2)%3]['answer'],source=t['text']) for i,q in enumerate(qs)]

OLD_GAMES=games
def games(p):
 text=OLD_GAMES(p);old1,old2=simulation_cards(p);new1,new2=checking_cards(p)
 oldblock=f"Квиток1: {old2['prompt']} A — {old2['answer']}; B — {old2['wrong']}.\n\nКвиток2: {old1['prompt']} A — {old1['wrong']}; B — {old1['answer']}."
 newblock='**Окрема паралельна картка для перевірки (нові дані):** '+new1['source']
 if new2['source']!=new1['source']:newblock+='\n\n'+new2['source']
 newblock+=f"\n\nКвиток1: {new1['prompt']} A — {new1['answer']}; B — {new1['wrong']}.\n\nКвиток2: {new2['prompt']} A — {new2['wrong']}; B — {new2['answer']}."
 text=text.replace(oldblock,newblock)
 text=text.replace(f"квиток1 — **A: {old2['answer']}**; квиток2 — **B: {old1['answer']}**",f"квиток1 — **A: {new1['answer']}**; квиток2 — **B: {new2['answer']}**")
 text=text.replace('Порядок карток та відповідей змінений.','Дано іншу паралельну картку з новими предметними даними/формами.')
 return text


LISTEN_PARALLEL={
8:passage('For a different school event, Kim will arrange a book display. Robin will write the programme. A learner who prefers a quiet role can check captions. The group agrees to finish the draft before lunch.',('What will Kim arrange?','a book display'),('What will Robin write?','the programme'),('Which quiet role is offered?','check captions')),
24:PRODUCT_PARALLEL[28],
39:passage('A new paper recipe makes a cold sandwich. It lists bread, cheese and cucumber. The utensil list has a plate and a spoon. First, an adult prepares the ingredients; next, the filling goes onto the bread; finally, the sandwich goes onto the plate. Pupils only edit the paper recipe.',('Which dish is described?','a cold sandwich'),('Which ingredients are listed?','bread, cheese and cucumber'),('Where does the sandwich go finally?','onto the plate')),
53:passage('At a different invented winter meeting, one family draws paper lanterns and another writes greeting cards. A quiet guest can leave a drawing instead of speaking. These are individual fictional choices, not rules for a country.',('What does the first family draw?','paper lanterns'),('What does the second family write?','greeting cards'),('What can a quiet guest leave?','a drawing')),
72:passage('A new water polo club card lists two non-playing roles. Ada will report the result, and Ben will check the written team list. The organiser asks both to confirm their role before the paper programme is printed. Nobody practises a water sport here.',('Who will report the result?','Ada'),('What will Ben check?','the written team list'),('What must both confirm?','their role')),
90:passage('A new fictional verse says: Please repeat the word for me. Let me write what I can see. The character then writes a headache on a symptom card and asks a responsible adult for help. The class practises a polite request, not diagnosis.',('What does the speaker ask to hear again?','the word'),('What symptom is written?','a headache'),('Whom does the character ask for help?','a responsible adult')),
108:GAME_PARALLELS[108],
125:GAME_PARALLELS[123],
}
for workshop,base in ((81,72),(99,90),(116,108),(133,125)):LISTEN_PARALLEL[workshop]=LISTEN_PARALLEL[base]


PROFILE_BEFORE_RECAP=profile
def profile(l):
 p=PROFILE_BEFORE_RECAP(l)
 if p['mode']=='review' and p['number']!=136:
  pairs={2:('past','past_cont'),6:('zero','past_perfect'),7:('degree','comparison'),8:('determiners','conjunctions')}
  if p['u'] in pairs:
   k1,k2=pairs[p['u']];g1,g2=GRAMMAR[k1],GRAMMAR[k2]
   p['g']={'rule':g1['rule']+' '+g2['rule'],'model':g1['model']+' '+g2['model'],'items':[g1['items'][0],g2['items'][0],g1['items'][1],g2['items'][2]]}
 return p


READING_PRODUCTION={
3:('Запиши2 репліки про гурток із R: одне змістове запитання й відповідь. Публічно говорити не обов’язково; усну репліку за можливості почує вчитель.','Which club does Robin choose? Robin chooses the library club because recommending books fits this hobby.'),
6:('Напиши2 речення: одне порівняння двох шкільних свят із R, одне уподобання вигаданого героя з причиною.','School A holds a concert, but School B holds a book exhibition. My fictional character prefers the exhibition because it offers a quiet book role.'),
19:('Створи3-реченнєвий мініпост за R:2 виконані справи й одна думка про гнучкий розподіл. Вигаданий автор дозволений.','Yesterday Dana tidied the table. Dana’s brother fed the pet. A chore chart is a plan, not a label for a person.'),
22:('Запиши2 репліки: запит про Chart B і точна відповідь за R.','How can the children swap jobs in Chart B? They can swap by agreement.'),
49:('Напиши3-реченнєвий мініпост про вигаданий український приклад із R: дві дії й прийняття іншого вибору. Не подавай одну родину як правило для країни.','Our imaginary family decorates paper eggs. We also write greetings. Guests can choose drawing instead of singing.'),
67:('Напиши2 короткі спортивні новини з R, не додаючи неперевірених результатів.','The fictional school has a new chess club. Its newsletter also reports a swimming team.'),
70:('Запиши запитання про Olympic values й відповідь за R; дві репліки.','What are the three core values? They are excellence, respect and friendship.'),
88:('Опиши роботу лікаря за R у2 реченнях: спочатку що робить, потім як пояснює незрозуміле слово. Без вибору лікування.','The doctor begins by listening to the patient. The doctor explains a difficult word in simpler language.'),
103:('Напиши2 речення від вигаданого глядача: уподобання з причиною та прийняття іншої думки.','My fictional viewer prefers funny dialogue because gentle humour is enjoyable. Another viewer can prefer an action story.'),
106:('Підготуй3-реченнєву мініпрезентацію відомого театру за R: назва/місто, рік відкриття будівлі, архітектор. Усна версія лише за можливості, без камери.','The National Opera of Ukraine is in Kyiv. Its building opened in 1901. The architect was Viktor Shreter.'),
119:('Запиши2 репліки запит-відповідь про назви з карток United Kingdom; тільки факти R.','Which name on the cards begins with N? Northern Ireland.'),
120:('Напиши3-реченнєвий мініблог про London-картку: заголовок, що показує карта, яку зміну вніс редактор.','My classroom blog post is headed London. Its map describes two places. I have added clearer labels before sharing the draft.'),
123:('Опиши уявний Kyiv-маршрут у2 реченнях: названий об’єкт і як завершується маршрут. Не пропонуй реальної подорожі під час тривоги.','The fictional Kyiv leaflet includes Golden Gate and a public garden. The paper route finishes at the same meeting point.'),
}
TARGET_LEX={
33:[('utensil','столове приладдя'),('guest','гість'),('custom','звичай'),('respect','повага')],
34:[('chopsticks','палички для їжі'),('spoon','ложка'),('serving utensil','приладдя для спільної страви'),('polite question','ввічливе запитання')],
37:[('food artist','фуд-артист'),('canvas','полотно'),('sketch','ескіз'),('pattern','візерунок')],
69:[('excellence','прагнення досконалості'),('respect','повага'),('friendship','дружба'),('opponent','суперник')],
70:[('value','цінність'),('respect','повага'),('guide','екскурсовод'),('exhibition','виставка')],
72:[('water polo','водне поло'),('pool','басейн'),('team','команда'),('ball','м’яч')],
75:[('underwater hockey','підводний хокей'),('pool','басейн'),('stick','ключка'),('puck','шайба')],
84:[('responsible adult','відповідальний дорослий'),('observed','спостережене'),('help','допомога'),('describe','описати')],
85:[('location','місце'),('unwell','нездужає'),('message','повідомлення'),('responsible adult','відповідальний дорослий')],
105:[('opera house','оперний театр'),('building','будівля'),('city','місто'),('compare','порівнювати')],
106:[('architect','архітектор'),('opened','відкрився'),('building','будівля'),('presentation','презентація')],
108:[('screen character','екранний персонаж'),('silent film','німий фільм'),('born','народився'),('profile','коротка біографія')],
}
PROFILE_BEFORE_TARGETS=profile
def profile(l):
 p=PROFILE_BEFORE_TARGETS(l);n=p['number']
 if n in READING_PRODUCTION:
  p['task'],p['model']=READING_PRODUCTION[n]
  count=3 if n in (19,49,106,120) else 2
  p['core']=['R: 3 відповіді',f'P: {count} короткі речення/репліки за конкретною умовою']
 if n in TARGET_LEX:p['lex']=TARGET_LEX[n]+p['lex'][4:]
 return p


# Curated same-category alternatives: the question's grammatical category cannot reveal the key.
DISTRACTOR_TEXT='''a clear question|a personal question
so that everyone can contribute|so that the group finishes first
a pencil|a ruler
a reply|a poem
stones|coins
the guitar|the piano
someone to recommend books|someone to perform songs
the library club|the music club
an exhibition|a concert
old photographs|new drawings
a concert|a competition
a book exhibition|a science exhibition
school anniversary|school sports day
a short play|a short song
a book display|a science display
the programme|the poster
I enjoy recommending books|I enjoy performing songs
the drama club|the science club
poster design|stage acting
an anniversary exhibition|an anniversary concert
write a label|write a song
a book day|a sports day
books|posters
the school anniversary|the school sports day
a decoration|a questionnaire
a poster|a programme
washed up|tidied the table
sweep the floor|dry the dishes
the table|the shelf
my brother|my cousin
Kim comes home early|Kim has more equipment
after dinner|before breakfast
Chart A|Chart B
by agreement|by a random draw
Alex|Sam
Robin|Alex
dried the dishes|mopped the floor
fed the pet|walked the dog
make decorations|make a chore chart
tidy the tables|sweep the floor
arrange chairs|arrange books
write labels|write invitations
swept the floor|washed up
the jobs|the materials
reading the plan|writing the invitations
ask politely|copy silently
before taking a shared dish|after taking a shared dish
chopsticks|a fork
separate serving utensils|the guests’ own utensils
prepare the ingredients|write a serving suggestion
the last stage|the first stage
The plate|The table
sketches the design on paper|arranges the pieces on the plate
a bird|a fish
Yellow|Blue
an apple, a banana and an orange|an apple, a pear and a plum
a bowl and a spoon|a plate and a fork
a cold sandwich|a fruit salad
bread, cheese and cucumber|bread, cheese and tomato
a grater|a whisk
grating food|mixing ingredients
a whisk|a grater
mixing ingredients|grating food
fruit salad|vegetable soup
the ingredients|the utensils
An adult|A pupil
the utensils|the ingredients
greeting cards|paper lanterns
another person’s photograph|another person’s name
paper eggs|paper flowers
drawing to singing|singing to drawing
written wishes|written invitations
a paper calendar|a paper invitation
a greeting|an invitation
after breakfast|before midnight
paper stars|paper trees
wishes for the coming year|wishes for a birthday
paper lanterns|paper stars
thank-you notes|invitation cards
draw a card|read a note aloud
a drawing|a speech
a written greeting|a spoken greeting
paper flower cards|paper egg cards
wishes for friends|wishes for classmates
older pupils|younger pupils
A drawing of a candle|A real candle
table tennis|volleyball
The reporter|The coach
a new chess club|a new swimming club
names and results|names and practice times
excellence, respect and friendship|excellence, respect and competition
a player thanking an opponent|a player thanking a coach
a newcomer|a referee
a new skill|a familiar skill
respect|friendship
the referee|the coach
Water polo|Underwater hockey
a ball|a puck
Ada|Ben
the written team list|the written score report
Underwater hockey|Water polo
A stick and a puck|A racket and a ball
The table tennis club|The chess club
a reporter|a coach
a chess club|a tennis club
Tuesday at two|Thursday at two
swimming|athletics
four|three
one|two
five|six
the coach|the reporter
fair play|the highest score
the organiser|the reporter
teamwork|the final score
the responsible adult|a classmate
what has been observed|what has been guessed
Room 5|Room 6
near the door|near the window
a short symptom note|a long personal story
the name on the appointment card|the time on the appointment card
listening to the patient|checking the written note
a difficult word|a difficult sentence
a question|an answer
an adult|a classmate
the word|the sentence
a headache|a sore throat
a sore throat|a headache
the question|the answer
A nurse|A receptionist
A responsible adult|A classmate
a printed card|a digital form
their map|their ticket
a musician|an artist
the funny dialogue|the fast action
a story with more action|a story with more dialogue
Covent Garden|Westminster
Kyiv|Lviv
1901|1911
Viktor Shreter|Taras Shevchenko
London|Dublin
the Tramp|the Robot
1889|1899
City Lights|The Gold Rush
a comedy|a musical
The dialogue is quite funny|The action is quite exciting
a musical|a comedy
the songs are memorable|the songs are short
a map|a ticket
the characters disagree politely|the characters agree immediately
a school show|a school competition
quite simple|quite complex
subtitles|a spoken explanation
very clear|very complex
a written summary|a spoken summary
Four|Three
Northern Ireland|Northern England
Scotland|Wales
Wales|Scotland
the map|the title
Dublin|London
a museum and a public garden|a museum and a public square
three|four
a name and a labelled drawing|a name and a visit date
Tower Bridge|Golden Gate
two towers|three towers
Golden Gate|Tower Bridge
at the same place|at a different place
a library|a gallery
after the library stop|before the library stop
the same meeting point|a different meeting point
River Castle|River Museum
Two towers and a small garden|Three towers and a large garden
Hill Museum|Hill Castle
the castle and a public garden|the castle and a public square
the short route|the long route
a gallery and a public square|a library and a public garden
it has a quiet bench|it has a ticket desk
a route card|a ticket card
the accessible route|the long route'''
DISTRACTORS={a.casefold():b for a,b in (line.split('|',1) for line in DISTRACTOR_TEXT.splitlines())}
UNCURATED_LEARNING=simulation_cards
UNCURATED_CHECKING=checking_cards

def semantic_choices(cards,mode):
 if mode in ('grammar','review','portfolio','vocabulary'):return cards
 return [{**c,'wrong':DISTRACTORS[c['answer'].casefold()]} for c in cards]

def simulation_cards(p):return semantic_choices(UNCURATED_LEARNING(p),p['mode'])
def checking_cards(p):return semantic_choices(UNCURATED_CHECKING(p),p['mode'])


GAMES_BEFORE_POSITION_VARIATION=games

def answer_positions(p,phase):
 import hashlib
 token=f"{p['source']['date']}:{p['number']}:{phase}".encode()
 bits=hashlib.sha256(token).digest()[0]
 return tuple('B' if bits&(1<<i) else 'A' for i in range(2))

def choice_line(label,card,correct):
 options=(card['answer'],card['wrong']) if correct=='A' else (card['wrong'],card['answer'])
 return f"{label}: {card['prompt']} A — {options[0]}; B — {options[1]}."

def games(p):
 text=GAMES_BEFORE_POSITION_VARIATION(p);first=simulation_cards(p);second=checking_cards(p)
 # Source cards give the evidence, without duplicating another set of keyed choices.
 old_sources='\n\n'.join(f"**Картка {i}:** {c['source']}\n\nЗапит: {c['prompt']}\n\nВибір A: {c['answer']}\n\nВибір B: {c['wrong']}" for i,c in enumerate(first,1))
 sources=[]
 for c in first:
  if c['source'] not in sources:sources.append(c['source'])
 text=text.replace(old_sources,'\n\n'.join(f'**Джерело {i}:** {x}' for i,x in enumerate(sources,1)))
 learning=answer_positions(p,'learning');checking=answer_positions(p,'checking')
 old_learning=choice_line('Хід1',first[0],'A')+'\n\n'+choice_line('Хід2',first[1],'B')
 new_learning=choice_line('Хід1',first[0],learning[0])+'\n\n'+choice_line('Хід2',first[1],learning[1])
 text=text.replace(old_learning,new_learning)
 correct,wrong=learning[0],('B' if learning[0]=='A' else 'A')
 text=text.replace('Хід1: A → перший рядок прийнятий (стан1/2); B → рядок залишається',f'Хід1: {correct} → перший рядок прийнятий (стан1/2); {wrong} → рядок залишається')
 correct,wrong=learning[1],('B' if learning[1]=='A' else 'A')
 text=text.replace('Хід2: B → другий рядок прийнятий; A → не затверджуємо',f'Хід2: {correct} → другий рядок прийнятий; {wrong} → не затверджуємо')
 for i,c in enumerate(second):text=text.replace(choice_line(f'Квиток{i+1}',c,'A' if i==0 else 'B'),choice_line(f'Квиток{i+1}',c,checking[i]))
 text=text.replace(f"квиток1 — **A: {second[0]['answer']}**; квиток2 — **B: {second[1]['answer']}**",f"квиток1 — **{checking[0]}: {second[0]['answer']}**; квиток2 — **{checking[1]}: {second[1]['answer']}**")
 text=text.replace('“1A;2B” і одну фразу приватно','нумеровані вибори й одну фразу приватно')
 return text


LEX_MODELS={
4:'A fictional bookworm recommends books. A chatterbox in the story learns to take turns. A computer geek helps with the club website. The class discusses why the label drama queen can hurt a person.',
9:'Our group will make a decoration. The organiser will give a prize. We will hold an exhibition. Another group will perform a play.',
20:'Sam can do the washing-up. Robin can dry the dishes. Alex can sweep the floor. Kim can walk a dog.',
25:'An appliance is a useful device. A clearer label is an improvement to our diagram. The paper plan shows an oven. Some kitchen equipment is electrical.',
35:'The paper picture shows an apron. A chopping board is on the next card. Our third label says frying pan. The fourth label says grater.',
40:'Our paper recipe says to add fruit. The next instruction says to blend the mixture. Another recipe uses the verb bake. A fourth card uses the verb boil.',
50:'One card is labelled Good Friday. Another is labelled Boxing Day. The third is labelled New Year’s Eve. Visitors compare the names at an imaginary celebration.',
54:'We can define a word. To paraphrase is to express the same idea in different words. A custom is something a group often does. A celebration is a special event.',
68:'One sports card is labelled athletics. Another is labelled weightlifting. The third explains cycle ball. The last names windsurfing.',
73:'A basketball court is shown on our card. It has a basket. A football pitch is shown on another card. A tennis player uses a racket.',
86:'The fictional form has the word rash. The next symptom label says cough. A character reports a headache. Another character reports a sore throat.',
91:'The language card shows the verb suffer. A diagram labels the chest. The fictional symptom note mentions pain. Another paper card is labelled X-ray.',
104:'The curtain is hanging in our theatre. There are two balconies in our drawing. The audience sits in seats. The stage is wide.',
109:'One fictional programme offers a comedy. Another screen shows a cartoon. A science fiction film is on the third card. A historical film is on the fourth card.',
121:'One imaginary route card names Kingston. Another card names Suva. The third names Wellington. The fourth names Dublin.',
126:'Our drawing has two attractions. The leaflet offers excursions. A fictional tour ends at the gate. The map shows a quiet stop.',
}
PROFILE_BEFORE_LEX_MODELS=profile
def profile(l):
 p=PROFILE_BEFORE_LEX_MODELS(l)
 if p['mode']=='vocabulary':p['model']=LEX_MODELS[p['number']]
 return p



# Age-adapted practice informed by the Ukrainian Harvard electronic supports.
# These are our micro-prompts, not names or reproductions of official Kernels.
def sel_profile(p):
 n,u,mode=p['number'],p['u'],p['mode']
 if n==4:
  return dict(domain='Сила емоційного інтелекту / співпраці',focus='Описуємо без ярликів',action='На прикладі вигаданого героя відокремити конкретну дію від оцінного ярлика; не переносити назви з карток на однокласників.',prompt='Як замінити оцінний ярлик одним точним описом дії вигаданого героя?')
 if mode in ('grammar','vocabulary','review','portfolio'):
  return dict(domain='Сила когнітивних навичок',focus='Пауза й перевірка',action='Перед вибором мовчки перечитати запит і назвати для себе одну мовну ознаку; після вибору перевірити її за умовою.',prompt='Яку ознаку слова або речення ти перевірив перед вибором і як використаєш цей прийом у новій картці?')
 if n in (3,11):
  return dict(domain='Сила усвідомленості / співпраці',focus='Просимо потрібну підтримку',action='У вигаданій розмові дати герою можливість попросити більше часу або письмовий спосіб відповіді; не вгадувати його почуття за поведінкою.',prompt='Якою короткою реплікою герой гуртка може попросити більше часу або письмову відповідь?')
 if u==2:
  return dict(domain='Сила співпраці',focus='Домовляємося про роль',action='Перед власною пропозицією врахувати один факт про доступний час чи роль іншого героя; запропонувати зміну без ярлика «ледачий».',prompt='Як змінити план домашніх справ, якщо у вигаданого учасника стало менше часу?')
 if n in (33,34):
  return dict(domain='Сила співпраці',focus='Запитуємо без осуду',action='Уточнити незнайомий звичай ввічливим запитанням; не називати його неправильним і не узагальнювати на всіх людей країни.',prompt='Яке ввічливе запитання допоможе гостю зрозуміти незнайомий звичай за столом?')
 if n==37:
  return dict(domain='Сила когнітивних навичок',focus='Спершу плануємо',action='Показати, як начерк допомагає впорядкувати наступні дії; учень може назвати перший крок без виконання роботи з їжею.',prompt='Як ескіз допоміг би іншому вигаданому фуд-артисту спланувати картину?')
 if u==4:
  return dict(domain='Сила співпраці',focus='Поважаємо різний вибір',action='До пропозиції участі додати прийнятну можливість спостерігати; не вимагати особистих святкових чи релігійних історій.',prompt='Як запросити вигаданого гостя до святкової діяльності й залишити йому вибір лише спостерігати?')
 if u==6:
  return dict(domain='Сила співпраці',focus='Уточнюємо й просимо допомоги',action='Змоделювати ввічливе уточнення або прохання відповідального дорослого про допомогу в умовній історії; не виводити діагноз із поведінки героя.',prompt='Яке коротке уточнення допоможе вигаданому відвідувачу зрозуміти запитання дорослого?')
 if u==7 and n in (103,111,112,117):
  return dict(domain='Сила емоційного інтелекту / співпраці',focus='Допускаємо іншу точку зору',action='Перш ніж оцінювати фільм, назвати аргумент іншого глядача; не приписувати йому «неправильні» почуття чи смаки.',prompt='Яка репліка дозволить не погодитися щодо фільму й зберегти повагу до іншого глядача?')
 return dict(domain='Сила когнітивних навичок',focus='Знаходимо підказку',action='Перед вибором знайти одне слово-доказ у картці; пояснення можна дати подумки, коротко українською або про вигаданого героя.',prompt='Яка деталь картки допомогла перевірити вибір і де ще стане в пригоді така перевірка?')

PROFILE_BEFORE_SEL_ALIGNMENT=profile
def profile(l):
 p=PROFILE_BEFORE_SEL_ALIGNMENT(l)
 if p['number']==101:
  p['task']='Напиши4 короткі речення-повідомлення про вигаданого відвідувача: симптом персонажа, що він підготував раніше, звернення до дорослого та прохання уточнити. Це зв’язне повідомлення, не запис діалогу; без діагнозу й ліків.'
  p['model']='A fictional visitor had a sore throat. Before the visit, the visitor had prepared a note. The receptionist contacted the responsible adult. The visitor asked for the question to be repeated.'
 return p

OFFICIAL_GROUP_NOTE='''L/R/S/P — первинні сліди окремих мовних дій, а не чотири офіційні групи. За додатком2 наказу МОН №1093 для іноземних мов: група1 — сприйняття усної інформації й письмових текстів (L/R); група2 — усна, письмова та онлайн-взаємодія (діалог S, обмін повідомленнями); група3 — надання інформації й висловлювання думок (зв’язний повідомлювальний P або монолог). Взаємодія й повідомлення розрізняються за реальною метою завдання, а не лише за каналом. Два вибори мінігри не встановлюють офіційного рівня групи; їх використовують для відгуку й наступного кроку. Первинні бали не переводяться автоматично у шкільну оцінку.'''

LESSON_BEFORE_SEL_ALIGNMENT=lesson_plan
def lesson_plan(p):
 text=LESSON_BEFORE_SEL_ALIGNMENT(p);sel=sel_profile(p)
 if p['mode']!='assessment':text=text.replace('[резервом](recovery-handout.md)','відкладеним блоком у доступних умовах')
 old='- Авторська SEL-адаптація у дусі «Зерна»: вибір «сам / пара / письмово / пропускаю публічну репліку»; відгук про дію, не про особистість. Це не офіційна вправа програми «Зерна». Емоції, камера, особисті історії не оцінюються.'
 new=f'- Авторська вікова СЕН-адаптація для7 класу, не офіційна вправа чи сертифікація «Зерна». Намір: **{sel["focus"]}** ({sel["domain"]}). Дія: {sel["action"]} Вибір «сам / пара / письмово / пропускаю публічну репліку»; можна попросити паузу без пояснення причин. Емоції, камера, особисті історії не оцінюються; не вимагати «правильної» емоції чи зовнішнього спокою. [Прочитані джерела й межі адаптації](../SEL_NUSH_REVIEW.md).'
 assert old in text;text=text.replace(old,new)
 # A brief model and reflection replace moments inside the existing blocks.
 text=text.replace('Перевірити умови.','Перевірити умови. Назвати намір «'+sel['focus']+'» і запропонувати один власний мовний крок.')
 text=text.replace('Один пробний приклад; не новий великий граматичний блок.','Один пробний приклад; учитель коротко моделює: '+sel['action']+' Не новий великий блок.')
 text=text.replace('Не додавати новий контроль.','Останню хвилину віддати добровільній рефлексії: «'+sel['prompt']+'» Можна подумки; не оцінювати. Не додавати новий контроль.')
 if p['mode']=='assessment':text+='\n## Зіставлення первинних слідів із групами результатів\n\n'+OFFICIAL_GROUP_NOTE+'\n'
 return text

KEY_BEFORE_SEL_ALIGNMENT=teacher_key
def teacher_key(p):
 text=KEY_BEFORE_SEL_ALIGNMENT(p)
 if p['mode']=='assessment':text+='\n## Групи результатів, конфіденційність і відгук\n\n'+OFFICIAL_GROUP_NOTE+' Оцінки й індивідуальні труднощі обговорювати приватно. У рефлексії достатньо назвати стратегію та наступний крок; особисті емоції не збираємо.\n'
 return text

GAMES_BEFORE_SEL_ALIGNMENT=games
def games(p):
 text=GAMES_BEFORE_SEL_ALIGNMENT(p);sel=sel_profile(p)
 introduction=f'**Намір навички:** {sel["focus"]}. **Дія в межах ходів:** {sel["action"]} Перед стартом можна попросити паузу або письмову відповідь.\n\n'
 text=text.replace('## 1 · Редакція матеріалу: навчання,7 хв\n\n','## 1 · Редакція матеріалу: навчання,7 хв\n\n'+introduction)
 text=text.replace('6–7 фіксація підтримки.','6–7 коротка рефлексія й фіксація підтримки. Необов’язкове запитання: «'+sel['prompt']+'» Достатньо подумки або вигаданого прикладу, без бала.')
 text=text.replace('4–5 відгук і один навчальний повтор.','4–5 відгук; учень обирає один навчальний повтор АБО коротку рефлексію: «'+sel['prompt']+'» Без бала за особистий досвід.')
 return text



LEARNER_BEFORE_SEL_ALIGNMENT=learner_sheet
def learner_sheet(p,reserve=False):
 text=LEARNER_BEFORE_SEL_ALIGNMENT(p,reserve)
 sel=sel_profile(p)
 note='**За бажанням, після основного завдання:** '+sel['prompt']+' Можна подумки або про вигаданого героя; відповідь не впливає на мовний бал.\n\n'
 marker='**Паперовий місток D'
 assert marker in text
 return text.replace(marker,note+marker)

if __name__=='__main__':main()
