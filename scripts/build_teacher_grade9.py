#!/usr/bin/env python3
"""Rebuild the audited grade 9 teaching packs from the sanitized local snapshot.

No external plan, network, runtime PDF renderer or student data is required.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'teacher/9'
DATA=json.loads((DEST/'source-plan.json').read_text())
SECTIONS={s['id']:s for s in DATA['sections']}

# Each tuple: contextual prompt, correct answer, plausible distractors, rationale.
def item(prompt,answer,wrong,why): return {'prompt':prompt,'answer':answer,'wrong':wrong,'why':why}
GRAMMAR={
6:('Часи: звичка, дія зараз, завершена минула подія, попередня минула подія', 'Часовий контекст визначає форму: usually → Present Simple; right now → Present Continuous; yesterday → Past Simple; before another past action → Past Perfect.',[
item('Every Friday, Dan ___ a photography club.','attends',['is attending','attended'],'Every Friday позначає звичку.'),item('Look! Emma ___ a photograph right now.','is taking',['takes','took'],'Right now позначає дію зараз.'),item('By the time Dan arrived yesterday, Emma ___ the photos.','had chosen',['chooses','has chosen'],'Вибір фото передував приходу в минулому.')]),
9:('Майбутнє: розклад, домовленість, намір, спонтанне рішення','Present Simple — розклад; Present Continuous — домовленість; going to — попередній намір; will — рішення в момент мовлення.',[
item('The published timetable says the train ___ at six tomorrow.','leaves',['will leaving','leave'],'Розклад: Present Simple.'),item('We have booked a table. We ___ our friends there tomorrow.','are meeting',['met','meeting'],'Підтверджена домовленість: Present Continuous.'),item('“I cannot carry this box.” “I ___ you.”','will help',['helped','am help'],'Спонтанна пропозиція: will + інфінітив.')]),
20:('Gerund','Після enjoy та avoid вживаємо -ing; -ing форма може бути підметом. Не всі дієслова вимагають -ing.',[
item('Emma enjoys ___ comfortable clothes.','wearing',['to wear','wear'],'Enjoy + -ing.'),item('Dan avoids ___ things he does not need.','buying',['to buy','buy'],'Avoid + -ing.'),item('___ a jacket can save money.','Repairing',['Repair','To repairing'],'Gerund як підмет.')]),
23:('Gerund vs to-infinitive','Enjoy/avoid + -ing; decide/plan + to-infinitive. Порівнюємо керування конкретного дієслова, не загальну пораду «після дієслова».',[
item('Emma decided ___ her jacket.','to repair',['repairing','repair'],'Decide + to-infinitive.'),item('She avoids ___ clothes for just one event.','buying',['to buy','buy'],'Avoid + -ing.'),item('They plan ___ clothes instead of buying new ones.','to swap',['swapping','swap'],'Plan + to-infinitive.')]),
34:('Passive Voice: час і форма','Об’єкт стає підметом; be у потрібному часі + V3. Present: is/are; Past: was/were; Future: will be; Present Perfect: has/have been.',[
item('Every year, a charity event ___ by the club.','is organised',['organised','has organise'],'Регулярна подія: is + V3.'),item('The posters ___ by the students yesterday.','were designed',['are designing','have design'],'Yesterday: were + V3.'),item('The report is ready now. It ___.','has been written',['has written','was writing'],'Результат зараз: has been + V3.'),item('The invitations ___ by the club next week.','will be sent',['will sent','will be send'],'Future passive: will be + V3.')]),
37:('Passive Voice: запитання','У запитанні допоміжне дієслово перед підметом: Were they invited? Has it been completed? Will it be published?',[
item('___ the students invited to the club yesterday?','Were',['Did','Have'],'Past passive question: Were + subject + V3.'),item('Has the report ___ completed yet?','been',['being','be'],'Present Perfect passive: has + subject + been + V3.'),item('___ the results be published tomorrow?','Will',['Do','Are'],'Future passive question: Will + subject + be + V3.')]),
48:('Reported statements','Контекст усіх пунктів: наступного дня репортер переповідає завершену розмову; часовий план змінився, використовуємо backshift. Present → Past, will → would. Said + that; told + адресат + that. У незмінно актуальному контексті backshift не завжди обов’язковий.',[
item('Yesterday Emma said, “I like this programme.” Report her words today: Emma said that she ___ the programme.','liked',['likes','liking'],'У заданому минулому контексті: like → liked.'),item('Yesterday Dan said, “I will check the source.” Report it today: Dan said that he ___ check the source.','would',['will','did'],'Will → would у заданому контексті.'),item('Choose the grammatical reporting verb: Dan ___ me that he had checked it.','told',['said','spoke'],'Told + object; said не приєднує me без to.')]),
51:('Reported speech: час і місце','Контекст: у понеділок Emma говорила в студії; у середу Dan переповідає в іншому місці й показує інший екран. Today → that day; tomorrow → the next day; this → that; here → there. Ці зміни залежать від реального контексту.',[
item('On Monday Emma said, “I will watch this tomorrow.” On Wednesday Dan reports: She said she would watch ___ the next day.','that',['these','those'],'This → that: інший екран, інший момент.'),item('Report “I am busy today” from Monday on Wednesday: She said she was busy ___.','that day',['tomorrow','the next day'],'Today з понеділка → that day.'),item('Report “I work here” from the studio in another place: She said she worked ___.','there',['here','tomorrow'],'Місце змінилося: here → there.')]),
64:('Reported commands and requests','Tell/ask + object + to-infinitive; заперечення not to. Це передавання прохання, а не backshift дієслова головної дії.',[
item('“Check the CV,” the teacher told Dan. The teacher told Dan ___ the CV.','to check',['checking','checked'],'Tell + object + to-infinitive.'),item('“Please do not share private details,” she asked Emma. She asked Emma ___ private details.','not to share',['to not sharing','did not share'],'Ask + object + not to-infinitive.'),item('“Please help me,” Emma said to Dan. Emma asked ___ to help her.','Dan',['to Dan','that Dan'],'Адресат після asked без to.')]),
67:('Reported questions','Контекст: наступного дня переповідаємо завершене інтерв’ю з backshift. Yes/no → if/whether; Wh-word зберігаємо; порядок слів стверджувальний, без do/did.',[
item('Yesterday she asked Dan, “Do you have experience?” Report it today: She asked Dan whether he ___ experience.','had',['did have?','has?'],'Present → Past; без питальної інверсії.'),item('Yesterday she asked, “Where do you work?” Report today: She asked where ___.','he worked',['did he work','he work'],'Порядок subject + verb.'),item('Yesterday she asked Dan, “Can you start on Monday?” Report today: She asked ___ he could start on Monday.','whether',['that','what'],'Загальне запитання → whether/if.')]),
78:('Defining / non-defining relative clauses','Defining визначає, про який предмет ідеться, без ком. Non-defining додає інформацію про вже визначений предмет, відокремлюємо комами; that у такому реченні не використовуємо.',[
item('The device ___ sorts the books is mine.','that',['who','whose'],'Предмет; defining that/which.'),item('My tablet, ___ is on the table, needs charging.','which',['that','who'],'Non-defining clause: which.'),item('Choose the correctly punctuated extra information.','My tablet, which I bought last year, is useful.',['My tablet which, I bought last year is useful.','My tablet, that I bought last year, is useful.'],'Дві коми й which для додаткової інформації.')]),
82:('Technology phrasal verbs','Switch off — вимкнути; back up — створити резервну копію; run out of — вичерпати запас. With pronoun: switch it off, не switch off it.',[
item('The lesson is over. Please switch the tablet ___.','off',['out','up'],'Switch off — вимкнути.'),item('To keep a second safe copy, back ___ your files.','up',['off','out'],'Back up — резервна копія.'),item('The battery has run ___ power.','out of',['off','up'],'Run out of — вичерпати запас.')]),
93:('Zero vs First Conditional','Zero: if + Present, Present — загальна закономірність. First: if + Present, will + verb — реальна майбутня можливість.',[
item('General fact: If water freezes, it ___ ice.','becomes',['will became','would become'],'Zero conditional.'),item('Tomorrow’s plan: If it rains, we ___ the swap indoors.','will hold',['would held','held'],'First conditional.'),item('If the weather ___ dry tomorrow, we will collect litter.','is',['will be','would be'],'У if-clause першого типу Present Simple.')]),
96:('Second Conditional','If + Past Simple, would + verb — уявна/малоймовірна теперішня або майбутня ситуація. Past форма тут не позначає завершеної минулої події.',[
item('Imagine being the head teacher: If I managed the school, I ___ refill stations.','would add',['will added','had added'],'Уявна ситуація: would + verb.'),item('We do not have a garden. If we ___ a garden, we would grow vegetables.','had',['have','will have'],'If + Past Simple.'),item('If the club had more time, it would ___ another workshop.','organise',['organised','organising'],'Would + base verb.')]),
107:('Third Conditional','If + had + V3, would have + V3 — уявна зміна завершеного минулого. Чітко назвати, що насправді сталося.',[
item('They did not check the hours and arrived late. If they had checked, they ___ earlier.','would have arrived',['would arrive','will arrive'],'Уявний інший результат у завершеному минулому.'),item('We missed the bus. If we ___ earlier, we would have caught it.','had left',['left','leave'],'If + Past Perfect.'),item('If Dan had bought a map yesterday, he would have ___ the route.','found',['find','finding'],'Would have + V3.')]),
110:('Conditionals: зіставлення часових ситуацій','Реальний майбутній план → First; уява зараз → Second; інше завершене минуле → Third. Не обирати форму лише за словом if.',[
item('Tomorrow is still ahead: If it rains, we ___ a museum.','will visit',['would have visited','had visited'],'First, майбутня реальна умова.'),item('I have little money now: If I had more money, I ___ another city.','would visit',['will visit','would have visited'],'Second, уявна теперішня умова.'),item('Yesterday we missed it: If we had arrived earlier, we ___ the exhibition.','would have seen',['will see','would see'],'Third, завершене минуле.')]),
}
for _g in (48,67):
    for _q in GRAMMAR[_g][2]:
        if 'Yesterday' in _q['prompt']:_q['prompt']='Use backshift for this completed-past reporting task. '+_q['prompt']

GRAMMAR[79]=GRAMMAR[78]
# Contextual lexical selections are exact targets, not unrelated unit-level grammar.
LEX={
4:[('curious','допитливий','Dan asks questions because he wants to understand how things work.'),('private','стриманий щодо особистого','Emma chooses not to discuss her personal life.'),('cheerful','життєрадісний','Robin greets the group with a smile.')],
8:[('forename','ім’я','The fictional form gives Alex as the first name.'),('surname','прізвище','The fictional form gives Green as the family name.'),('occupation','заняття/професія','The form asks what work the person does.')],
17:[('footwear','взуття','The shop puts boots and sandals in one section.'),('accessory','аксесуар','A belt adds a final detail to an outfit.'),('a pair of','пара','The customer asks for two matching shoes.')],
22:[('comfortable','зручний','The shoes feel good during a long walk.'),('plain','однотонний/без візерунка','The shirt has no stripes or pictures.'),('expensive','дорогий','The jacket costs more than the buyer can afford.')],
31:[('Culinary Club','кулінарний клуб','The group learns to prepare different dishes.'),('Photography Club','фотоклуб','Members learn to take and edit photographs.'),('Nature Club','природничий клуб','Members observe plants without disturbing wildlife.')],
36:[('keep in touch','підтримувати зв’язок','The friends send occasional messages after changing schools.'),('hang out','проводити час разом','They spend free time together after lessons.'),('awesome','чудовий; неформально','A friend says that the film was really great.')],
45:[('audience','аудиторія','The people watching the programme ask questions.'),('episode','серія/випуск','The series releases one new part every Friday.'),('review','рецензія/огляд','The writer describes strengths and weaknesses of a programme.')],
50:[('browse','переглядати/шукати','Emma looks through several websites for information.'),('stream','дивитися/слухати потоком','Dan watches the programme online without downloading the whole file first.'),('troll','провокувати у мережі','A user deliberately posts insulting comments to provoke an argument.')],
61:[('vet','ветеринар','The professional treats sick animals.'),('electrician','електрик','The professional installs and repairs electrical wiring.'),('tour guide','екскурсовод','The professional explains landmarks to visitors.')],
66:[('librarian','бібліотекар','The professional helps readers find books.'),('architect','архітектор','The professional designs buildings.'),('software engineer','інженер-програміст','The professional develops and tests software.')],
75:[('charge','заряджати','Connect the tablet to a power source because the battery is low.'),('scan','сканувати','Make a digital copy of a paper page with a scanner.'),('print','друкувати','Produce a paper copy of the digital file.')],
81:[('invent','винаходити','Create a device that did not exist before.'),('discover','відкривати','Find something that already existed but was not known.'),('astronomer','астроном','The scientist studies stars and planets.')],
90:[('arid','посушливий','The climate has very little rain.'),('polar','полярний','The climate near the poles is very cold.'),('wildlife','дика природа','The park protects animals and plants living naturally.')],
95:[('air pollution','забруднення повітря','Harmful substances make the air less clean.'),('overfishing','надмірний вилов риби','People catch fish faster than populations can recover.'),('global warming','глобальне потепління','The long-term average temperature of Earth rises.')],
104:[('gallery','галерея','Visitors look at paintings and other works of art.'),('bridge','міст','People use this structure to cross the river.'),('castle','замок','A historic fortified building stands on a hill.')],
109:[('opposite','навпроти','The library faces the museum across the road.'),('between','між','The café has a bank on one side and a shop on the other.'),('behind','позаду','The garden is at the back of the museum.')],
}
# Authentic school-level genres; models satisfy the exact prompt, not a generic unit essay.
WRITING={
11:('мініавтобіографія вигаданого персонажа','Write 5 sentences as fictional Alex: early interest, one past event, present activity, future arrangement and goal. Do not give real personal details.','I became interested in photography when I was ten. Last year I joined a school club. I am learning to edit pictures now. I am showing my photos at an exhibition next Friday. I hope to learn from the visitors.'),
25:('абзац думки про стиль','Write 5 sentences: state an opinion about clothing, give two reasons, one example and a short conclusion.','In my opinion, comfortable clothes are a good choice for school events. They allow people to move easily. They can also help people focus on the event rather than their outfit. For example, I would choose a plain shirt and comfortable shoes. To sum up, practical choices can still express a personal style.'),
39:('survey report','Use this fictional survey of 20 students: sport 10, music 6, film 4; each chose one favourite club. Write 4 report sentences with two correct percentages and a careful conclusion. Do not generalise to all teenagers.','Twenty students chose one favourite club in a fictional survey. Sport was selected by 10 students, or 50%. Music was selected by 6 students, or 30%, while film was selected by 4 students, or 20%. These results describe this group only, so a school could ask more students before choosing clubs.'),
53:('vlog review','Invent a school science vlog. Write a title and 4 sentences: topic, strength with example, limitation, recommendation for a named audience. Do not invent claims about a real creator.','Science in Five — a fictional vlog. It explains simple inventions for secondary-school learners. The diagrams make the explanation of a water filter easy to follow. However, the episode should name the sources of its information. I recommend it to beginners who want an introduction, provided they check the information elsewhere.'),
69:('CV із вигаданими даними','Create a fictional school-project CV with 5 headings: Name, Education, Skills, Experience, Interests. Give evidence for one skill. Contact details are not required.','Name: Alex Green (fictional).\nEducation: Year 9, fictional River School.\nSkills: Teamwork — helped three classmates organise a book stall.\nExperience: Volunteer helper at a school book event.\nInterests: Reading and digital design.'),
84:('biography chart','Use the fictional scientist fact card: Mira Vale; 2018 studied water filters; 2021 designed a reusable classroom filter; 2023 shared a safety-testing report. Make a 3-row Date / Work / Importance chart. This is fiction, not a real historical biography.','2018 | Studied water filters | Built knowledge for later design.\n2021 | Designed a reusable classroom filter | Developed a model for classroom discussion.\n2023 | Shared a safety-testing report | Allowed others to examine the evidence. No claim that the model is safe for drinking water is established.'),
98:('екологічна листівка','Create a leaflet with a title, 3 brief actions and a practical reason for each. Include a realistic indoor option if it rains.','Small Changes for Eco Day\nBring a reusable bottle to reduce single-use waste.\nUse a clothes swap to give suitable clothes another life.\nIf it rains, hold the swap indoors so the event can continue.'),
112:('неформальний e-mail про поїздку','Write a greeting, 4 short sentences and a closing about a fictional city visit. Include what happened, a missed opportunity and a third-conditional reflection.','Hi Sam,\nWe visited a fictional city museum on Saturday. We enjoyed the local exhibition, but we missed the tower because we arrived after closing time. If we had checked the opening hours, we would have arrived earlier. Next time, we will leave more time for transport.\nBest, Alex'),
}
TOPICS={0:'learning English',1:'personality and interests',2:'clothing and style',3:'clubs and youth organisations',4:'media',5:'jobs and skills',6:'science and technology',7:'the environment',8:'travel and landmarks'}
KIND={'book_lesson':'Практичний урок','grammar_workshop':'Граматична майстерня','unit_recap':'Повторення і самооцінювання','pair_diagnostic':'Діагностична робота','semester_assessment':'Семестровий контроль','portfolio':'Портфоліо і корекція'}

GENRE_ITEMS={
11:[item('An autobiography tells the story in whose voice?','I',['the reader as you','only an unnamed third person'],'Автобіографія: перша особа.'),item('Choose the completed past event.','Last year I joined a club.',['I am joining now.','I will join next year.'],'Last year + Past Simple.')],
25:[item('Which sentence states an opinion?','In my opinion, comfort matters.',['The shirt costs twenty pounds.','The event begins at six.'],'In my opinion маркує думку.'),item('Which detail supports choosing comfortable shoes?','They make a long walk easier.',['They are shoes.','They exist.'],'Конкретний зв’язок між вибором і наслідком.')],
39:[item('Ten out of twenty students chose sport. What percentage is this?','50%',['10%','20%'],'10 / 20 × 100 = 50%.'),item('Which conclusion is supported by this survey?','Half of these twenty students chose sport.',['All teenagers prefer sport.','Nobody chose music.'],'Межа даних: ці20учасників.')],
53:[item('Which review sentence gives an evaluated strength with evidence?','The diagrams explain the filter clearly.',['It is good.','It is a video.'],'Названа якість і її носій, а не порожня оцінка.'),item('Which review sentence gives a specific limitation?','The episode does not name its sources.',['I watched it.','It has a title.'],'Джерела — конкретний аспект якості.')],
69:[item('Where should “helped organise a school book stall” primarily go in a CV?','Experience',['Interests','Name'],'Це приклад виконаної діяльності.'),item('Which entry gives evidence of teamwork?','Worked with three classmates to organise a book stall.',['Expert manager of every project.','Likes all subjects.'],'Спостережувана спільна діяльність, не непідтверджений титул.')],
84:[item('Which achievement belongs to 1903 in the fact card?','Shared Nobel Prize in Physics',['Nobel Prize in Chemistry','Discovery of polonium and radium'],'1903 — Physics;1911 — Chemistry;1898 — відкриття.'),item('Which chart entry avoids an unsupported causal claim?','1911: Nobel Prize in Chemistry, recognising work on radium and polonium.',['1911: proved every radiation exposure is safe.','1911: invented every modern device.'],'Не робимо хибних висновків про безпеку/винаходи.')],
98:[item('Which leaflet line combines action and practical reason?','Bring a reusable bottle to reduce single-use waste.',['Bottles!','Our leaflet is long.'],'Імператив + мета to reduce.'),item('Which line provides the indoor rain option?','If it rains, hold the swap indoors.',['If it rains, always continue outdoors.','Ignore the weather.'],'Реалістичний запасний план у тексті.')],
112:[item('Choose the appropriate opening for an informal e-mail to Sam.','Hi Sam,',['To whom it may concern:','Curriculum Vitae'],'Відомий адресат, неформальне повідомлення.'),item('They arrived after closing yesterday. Choose the accurate reflection.','If we had checked the hours, we would have arrived earlier.',['If we check yesterday, we will arrive earlier.','If we checked tomorrow, we had arrived yesterday.'],'Завершене минуле: Third conditional.')],
}
GENRE_TRANSFER={
11:[item('Use a future arrangement after booking the visit.','I am visiting the club tomorrow.',['I visited the club tomorrow.'],'Booked arrangement → Present Continuous.'),item('Which sentence adds a meaningful learning goal?','I hope to learn how to edit photos.',['My name appears in this sentence.'],'Мета має дію/навичку.')],
25:[item('Choose a reason for repairing clothes instead of replacing them.','Repairing can keep useful clothes in use.',['A jacket is a jacket.'],'Змістовний причинний аргумент.'),item('Which sentence works as a conclusion to an opinion paragraph?','To sum up, practical choices can express a personal style.',['Last Tuesday was Tuesday.'],'Підсумовує позицію, не сторонній факт.')],
39:[item('Six of the twenty students chose music. What percentage is this?','30%',['6%'],'6 / 20 × 100 = 30%.'),item('Four students chose film. Which statement is accurate?','Film was chosen by20%of this group.',['Film was chosen by40%of all teenagers.'],'4 / 20 ×100=20%; обмежуємо цю групу.')],
53:[item('A vlog explains diagrams well but omits sources. Choose the cautious recommendation.','Useful for beginners, but check the information elsewhere.',['Everyone must trust it without checking.'],'Висновок враховує і сильну сторону, і обмеження.'),item('Which new line gives basic information for a review?','The fictional vlog explains inventions for Year9learners.',['The reviewer is a very happy person.'],'Тема й аудиторія, не оцінка людини.')],
69:[item('Move the misplaced line “enjoys reading novels” from Skills to which heading?','Interests',['Education'],'Захоплення → Interests.'),item('Which Skills line supports organisation?','Arranged books by topic for a class display.',['Expert director of an international company.'],'Конкретне діяння є доказом навички; титул не підтверджено.')],
84:[item('A chart places Chemistry at1903. Which correction fits the card?','Move Chemistry to1911.',['Move Chemistry to1898.'],'Картка відносить Chemistry до1911.'),item('What belongs to1898?','Discovery of polonium and radium with Pierre Curie.',['Invention of the internet.'],'Конкретна підтверджена подія картки.')],
98:[item('Choose a second leaflet action with a reason.','Swap suitable clothes so they can be used again.',['Buy something because shopping exists.'],'Практична дія й тематична причина.'),item('What should happen to the swap if it rains?','Move it indoors under the agreed plan.',['Keep everyone outdoors whatever the conditions.'],'Запасний план, не нехтування умовами.')],
112:[item('Choose a sensible closing to a friendly e-mail.','Best, Alex',['Skills: teamwork'],'Завершення листа, не рубрика CV.'),item('The group missed the bus yesterday. Give the correct new reflection.','If we had left earlier, we would have caught it.',['If we leave tomorrow, we had caught it.'],'Новий випадок завершеного минулого, Third conditional.')],
}
GRAMMAR_TRANSFER={
6:[item('During our call at six yesterday, Robin ___ a poster.','was designing',['designs'],'Процес у певний момент минулого.'),item('The photos were ready before the meeting. Robin ___ them before the team arrived.','had selected',['has selected'],'Попередня минула дія.')],
9:[item('A ticket confirms the visit: We ___ the gallery at noon tomorrow.','are visiting',['visited'],'Домовленість.'),item('“The doorbell is ringing.” “I ___ it.”','will answer',['answered'],'Спонтанне рішення.')],
20:[item('Robin enjoys ___ clothes for a performance.','designing',['to design'],'Enjoy + -ing.'),item('___ useful clothes away creates waste.','Throwing',['To throwing'],'Gerund як підмет.')],
23:[item('The class decided ___ a clothes swap.','to organise',['organising'],'Decide + to-infinitive.'),item('Robin avoids ___ unnecessary accessories.','buying',['to buy'],'Avoid + -ing.')],
34:[item('The club ___ in2020.','was founded',['founded'],'Past passive.'),item('The timetable ___ tomorrow.','will be published',['will published'],'Future passive.')],
37:[item('___ the hall cleaned after the event yesterday?','Was',['Did'],'Past passive question.'),item('Have the invitations ___ sent yet?','been',['be'],'Present Perfect passive.')],
48:[item('Yesterday Robin said, “I am tired.” Today, after that situation ended: Robin said they ___ tired.','were',['are'],'Задано завершений минулий контекст, backshift.'),item('Choose a correct structure: Robin ___ that the report was ready.','said',['told'],'Said that; told вимагає адресата.')],
51:[item('On Monday Robin said “tomorrow”. On Wednesday, reporting that plan, we say ___.','the next day',['next year'],'Зміна моменту переповідання.'),item('Robin said “here” in a hall. Reporting from another building, use ___.','there',['today'],'Зміна місця.')],
64:[item('“Please wait,” Robin said to me. Robin asked me ___ .','to wait',['waiting'],'Ask + object + to-infinitive.'),item('“Do not publish the draft,” the editor told us. The editor told us ___ it.','not to publish',['not publishing'],'Tell + object + not to-infinitive.')],
67:[item('Yesterday Robin asked, “Where do you live?” Reporting today, after the interview: Robin asked where ___.','I lived',['did I live'],'Стверджувальний порядок слів і заданий backshift.'),item('Yesterday: “Are you ready?” Reporting today: Robin asked ___ I was ready.','if',['that'],'Yes/no → if/whether.')],
78:[item('Our library, ___ opened last year, is useful.','which',['that'],'Додаткова інформація між комами.'),item('The person ___ scans the pages is Robin.','who',['which'],'Особа: who.')],
82:[item('Save a second copy: back ___ the document.','up',['out'],'Back up.'),item('Choose the pronoun position.','Switch it off.',['Switch off it.'],'У розділюваному phrasalverb займенник між частинами.')],
93:[item('General fact: If ice gets warm enough, it ___.','melts',['would melted'],'Zero conditional.'),item('Tomorrow: If our room is available, we ___ the swap there.','will hold',['would held'],'First conditional.')],
96:[item('We have no workshop now. If we had one, we ___ broken items there.','would repair',['will repaired'],'Second, уявна теперішня ситуація.'),item('If Robin ___ more time now, they would volunteer.','had',['has'],'If + Past Simple.')],
107:[item('They did not book yesterday. If they had booked, they ___ a place.','would have had',['will have'],'Third, інше завершене минуле.'),item('If we had saved the route, we would have ___ it offline.','used',['use'],'Would have + V3.')],
110:[item('We lack time now: If we had time, we ___ the tower.','would visit',['would have visited'],'Second, уява зараз.'),item('We missed the tower yesterday: If we had had time, we ___ it.','would have visited',['will visit'],'Third, інше минуле.')],
}
GRAMMAR_TRANSFER[79]=GRAMMAR_TRANSFER[78]

LISTENING_CARDS={
7:('This is a fictional interview for a school project. Robin uses the invented surname Lake and gives English as the language of the interview. Robin enjoys photography and believes that actions show more than labels. The interviewer asks for an example, and Robin describes helping a new club member find the right room. No real address, birthday or contact detail is needed for the project. A listener should distinguish the invented identity from the reason Robin gives for a belief.',
    item('Which belief does Robin express?','Actions show more than labels.',['Only appearance matters.','Everyone must have the same interests.'],'The interview explicitly states this belief.'),
    item('What example supports the belief?','Helping a new club member find the room.',['Posting a private address.','Buying an expensive camera.'],'The example is a helpful action.')),
21:('A fictional school group is discussing clothing rules. One student supports a plain school shirt because it makes the choice of clothes simpler. Another student wants room for personal style and suggests allowing small accessories. The group has not surveyed the whole school, so it cannot claim to know what every student thinks. It decides to ask different groups before writing a recommendation. The discussion compares reasons rather than judging people by the clothes they wear.',
    item('Why does one student support a plain shirt?','It makes choosing clothes simpler.',['It is always the most expensive option.','It proves a person is kind.'],'The speaker links the shirt to a simpler choice.'),
    item('Why will the group ask others?','It has not surveyed the whole school.',['It already knows every opinion.','It wants to choose by appearance only.'],'The sample is incomplete.')),
35:('A fictional Cyber Club is planning an e-sports tournament and a video workshop. The tournament is only one option: members who do not want to compete can help create a short film about the event. The organiser asks players to agree on fair rules before the first round. Robin will edit the film, while Sam will check the tournament timetable. The club wants to increase participation without treating competitive gaming as an activity that everyone must enjoy.',
    item('What can a member choose instead of competing?','Helping create a short film.',['Leaving school permanently.','Ignoring every club role.'],'The message gives film-making as an alternative.'),
    item('What must players agree on before the first round?','Fair rules.',['Private passwords.','The same personal interests.'],'The organiser explicitly asks for fair rules.')),
49:('A fictional science-vlog creator makes an announcement about the next episode. The creator will first check the examples, then shoot a short demonstration and edit the recording. A guest suggests adding a list of sources so viewers can examine the claims. The creator agrees and asks viewers to subscribe only if the topic is useful to them. Popularity is not presented as proof that every claim is accurate. The message describes both the production process and responsibility to the audience.',
    item('What happens after shooting the demonstration?','Editing the recording.',['Deleting every source.','Treating popularity as proof.'],'First check, then shoot, then edit.'),
    item('Why does the guest suggest listing sources?','So viewers can examine the claims.',['So no checking is needed.','To require everyone to subscribe.'],'The guest gives a verification purpose.')),
65:('A fictional careers speaker describes work in an international project team. Technical knowledge matters, but people also need to explain ideas clearly and interact respectfully with colleagues. Robin asks whether a person must be a genius to take part. The speaker says that several skills can be developed through practice, feedback and training. The team uses shared notes when members cannot attend a meeting. This example concerns one project; it does not prove that every job has the same requirements.',
    item('Which skill is needed besides technical knowledge?','Explaining ideas clearly.',['Never asking questions.','Guessing every requirement.'],'The speaker names clear explanation.'),
    item('What helps members who cannot attend a meeting?','Shared notes.',['Private gossip.','No record of decisions.'],'Shared notes are explicitly named.')),
80:('A fictional inventor shows a classroom prototype that separates paper from other materials. The first version uses a cardboard tube, but dust sometimes blocks it. The inventor does not claim that the prototype is ready for sale. The next step is to test a wider tube and record whether the problem occurs again. A visitor asks about the evidence rather than the colour of the model. This is a design discussion, not an instruction to build or operate a device during the lesson.',
    item('What problem affects the first prototype?','Dust sometimes blocks the tube.',['It has no colour.','It is already perfect.'],'The message names dust as the problem.'),
    item('What will the inventor test next?','A wider tube.',['A private account password.','No change at all.'],'A wider tube is the next proposed test.')),
108:('This route exists only on a fictional city map. Start at the museum entrance. Walk along the waterfront to the bridge, then turn left towards the gallery. The observation deck is beyond the gallery, but it is not included in this short route because the group has limited time. Robin suggests checking the opening hours before leaving the museum. A visitor asks whether the path goes through the harbour; the guide explains that the waterfront path stays on this side of the bridge.',
    item('Where should visitors turn left?','At the bridge.',['Inside the observation deck.','Before leaving the museum entrance.'],'The instruction says reach the bridge, then turn left.'),
    item('Why is the observation deck excluded?','The group has limited time.',['It has no name.','It is the museum entrance.'],'The message explicitly gives the time limit.')),
}

# New round-two source details, with alternatives from the same semantic category.
READING_TRANSFER={
1:[('What does Emma plan to do besides practising and keeping a record?','ask questions','write film reviews'),('What should learners do with mistakes?','Notice and correct them','Only count them')],
2:[('Which instrument does Emma play?','the guitar','the piano'),('Which subject interests Dan?','science','fashion design')],
7:[('Which invented surname does Robin use?','Lake','Green'),('Which language is used for the interview?','English','French')],
10:[('When will Emma take part in the exhibition?','next Friday','next Monday'),('Which two past details does Emma describe in her autobiography?','where she grew up and her interest in photography','a future job and a future city visit')],
15:[('Which shirt does Dan prefer?','striped','plain'),('What does Emma wear with her shirt?','trousers','a skirt')],
21:[('What does the second student suggest allowing?','small accessories','only plain shirts'),('Which groups will be asked before the recommendation?','different groups','only the two speakers')],
24:[('What did Emma use to wear?','only dark clothes','only bright colours'),('Which items does Emma avoid buying?','items she will wear just once','items she will wear regularly')],
29:[('What does Dan want to create in a club?','videos','clothing patterns'),('Which activities does Emma’s preferred group organise?','charity events','gaming tournaments')],
35:[('Who will edit the film?','Robin','Sam'),('Who will check the tournament timetable?','Sam','Robin')],
38:[('How many students were asked?','twenty','thirty'),('Which two creative activities are named?','music and films','photography and painting')],
43:[('What does the source say about popular posts?','They are not always accurate.','They are always accurate.'),('Which reports do the friends compare?','reliable reports','only the most popular posts')],
46:[('Which programme explains experiments?','the science series','the comedy'),('Which programme reviews matches?','the sports programme','the science series')],
49:[('What will the creator do before shooting?','check the examples','edit the recording'),('When does the creator suggest subscribing?','if the topic is useful to the viewer','before checking whether the topic is useful')],
52:[('What kind of programme is being discussed?','a science programme','a sports programme'),('What comes after the opening question and answer?','one follow-up','a second full interview')],
59:[('Besides salary, what does Emma say a dream job should match?','interests and skills','only a job title'),('What do the friends read to identify required qualities?','job adverts','museum reviews')],
65:[('How can several skills be developed according to the speaker?','practice, feedback and training','only a university title'),('What type of team is described?','an international project team','a single-person business')],
68:[('Which section is named alongside experience and interests?','education','medical history'),('What does the teacher ask them to check?','spelling','the price of the event')],
73:[('What did computers open new ways to do?','work and learn','only finish household chores'),('What did household appliances help save?','time on chores','distance between cities')],
76:[('Which year belongs to the Physics prize?','1903','1911'),('What research field is named?','radioactivity','climate science')],
80:[('What material is the prototype’s first tube made from?','cardboard','metal'),('What does the visitor ask about?','evidence','the colour of the model')],
83:[('What does Emma suggest checking?','the battery','the printer'),('How many sources does he use to check information?','more than one','exactly one')],
88:[('Which habitat threat is named besides forests being cut down?','polluted rivers','traffic noise'),('What is another direct threat to some species?','illegal hunting','school surveys')],
94:[('What will the class do in dry weather?','collect litter','hold only the indoor swap'),('Which item does the leaflet suggest bringing?','a reusable bottle','a single-use wrapper')],
102:[('Which two countries are compared?','Ukraine and the UK','Ukraine and Canada'),('What do the friends practise asking for?','directions','job references')],
108:[('Where does the route begin?','the museum entrance','the gallery entrance'),('Which place is beyond the gallery?','the observation deck','the museum entrance')],
111:[('What did the friends still enjoy?','the waterfront and a local exhibition','the closed museum and a theatre'),('What kind of text does Dan write?','an e-mail','a survey report')],
}
# Sessions that revisit the same source inherit its new detail questions, not generic certainty distractors.
for _base,_others in {2:[3,5],15:[16,18,19],29:[30,32,33],43:[44],46:[47],59:[60,62,63],73:[74],76:[77],88:[89,91,92],94:[97],102:[103,105,106]}.items():
    for _other in _others:READING_TRANSFER[_other]=READING_TRANSFER[_base]

def get_section(l):
    ids=l.get('section_ids',[])
    if ids:return SECTIONS[ids[0]]
    return SECTIONS[f"sb-u{l['unit']}-self-check"]

def table(rows):
    return '| Час | Учитель: точна інструкція | Учень: дія й доказ |\n|---|---|---|\n'+'\n'.join('| '+' | '.join(x)+' |' for x in rows)+'\n'

def choices(q,n,i):
    opts=[q['answer'],*q['wrong']];shift=(n+i)%len(opts)
    opts=opts[shift:]+opts[:shift]
    return ' / '.join(f'{chr(65+j)}) {x}' for j,x in enumerate(opts)),chr(65+opts.index(q['answer']))


def card(l):
    n=l['number'];u=l['unit'];s=get_section(l)
    section=s.get('section','self-check')
    control=l['kind'] in ('pair_diagnostic','semester_assessment')
    if n in GRAMMAR:typ='grammar'
    elif n in LEX:typ='lexis'
    elif n in WRITING:typ='writing'
    elif l['kind']=='portfolio':typ='portfolio'
    elif control:typ='assessment'
    elif l['kind']=='unit_recap' or section in ('self-check','look-back'):typ='recap'
    elif section=='listening':typ='listening'
    elif section=='speaking':typ='speaking'
    elif n==1:typ='starter'
    else:typ='reading'
    # All written lessons retain source identity, but only one main passage is scheduled.
    text=s['reading'];rule=s['rule'];model=s['example']
    qs=[];extension='';output='';sample='';genre=''
    if typ=='grammar':
        genre,rule,qs=GRAMMAR[n]
        output='Complete the contextual language items. Then write one new two-clause example using the target form and explain its meaning in Ukrainian or English.'
        sample=qs[0]['prompt'].replace('___',qs[0]['answer'])+' '+qs[0]['why']
        text='Language lab: all events below are fictional. The time and reporting context in each item are part of the task; keep them when choosing a form.'
        examples={
            6:'I usually read before school, but I am drawing a poster now.',
            9:'I have booked a visit, so I am meeting the guide tomorrow.',
            20:'I enjoy repairing clothes because it reduces waste.',
            23:'I decided to repair my coat because I avoid throwing useful things away.',
            34:'The club was founded last year, and its first exhibition will be opened tomorrow.',
            37:'Has the poster been printed, or will it be sent tomorrow?',
            48:'Yesterday Alex said, “I need a new source.” Today I report that Alex said they needed a new source.',
            51:'On Monday Alex said, “I am busy here today.” On Wednesday in another place, I report: Alex said that they were busy there that day.',
            64:'The teacher asked us to check the dates and told us not to include private contacts.',
            67:'Yesterday the teacher asked, “Where do you study?” Today I report that the teacher asked where I studied.',
            78:'The tablet that has a blue cover is mine, while my laptop, which has a silver cover, belongs to my sister.',
            79:'The device that scans pages saves time, while our printer, which is beside the door, makes paper copies.',
            82:'I backed up the file before I switched the tablet off.',
            93:'If it rains tomorrow, we will use an indoor room.',
            96:'If I had more space, I would start a small garden.',
            107:'If we had checked the map yesterday, we would have found the museum earlier.',
            110:'If it rains tomorrow, we will stay indoors; if I had more time now, I would plan another route.',
        }
        sample=examples[n]+' Explanation: '+rule
        model=sample
    elif typ=='lexis':
        targets=LEX[n]
        genre='лексика у контексті'
        rule='Обираємо слово за значенням у ситуації. Після розпізнавання переносимо слово в новий контекст. Публічні форми заповнюємо лише вигаданими даними.'
        text='Word bank: '+ '; '.join(f'{w} — {uk}' for w,uk,_ in targets)+'.'
        for w,uk,ctx in targets:
            qs.append(item(ctx+' Which word or phrase fits?',w,[x[0] for x in targets if x[0]!=w],f'{w} означає «{uk}» і відповідає описаній ситуації.'))
        output='Choose two words from the word bank and write a different contextual example for each. Do not copy the task sentences.'
        new_examples={
            4:('A curious learner asks how a device works.','A private character prefers a fictional profile to a personal story.'),
            8:('Forename: Robin.','Surname: Lake. These are invented details.'),
            17:('This section sells footwear for rainy days.','A scarf can be an accessory for a plain outfit.'),
            22:('A comfortable chair helps me focus.','The poster uses a plain background without a pattern.'),
            31:('The Culinary Club will discuss a simple recipe.','The Photography Club will prepare a picture display.'),
            36:('We can keep in touch by sending a weekly message.','The characters hang out in a fictional park after the club meeting.'),
            45:('The audience voted after the performance.','The next episode follows a different character.'),
            50:('I browse a library catalogue for a useful book.','The characters stream a short documentary together.'),
            61:('A vet checks the injured dog.','An electrician repairs the lighting system.'),
            66:('The librarian recommends an introductory book.','The architect explains a model of the new building.'),
            75:('Charge the camera before the visit.','Scan the signed school-project page to keep a copy.'),
            81:('The fictional engineer wants to invent a quieter alarm.','Researchers can discover a species that was unknown to them.'),
            90:('An arid region may need careful water planning.','The project compares polar and tropical climates.'),
            95:('The class discusses ways to reduce air pollution near roads.','Overfishing can affect an entire marine food web.'),
            104:('The gallery displays local drawings.','A narrow bridge connects the two riverbanks.'),
            109:('On the fictional map, the café is opposite the school.','The museum is between the park and the theatre.'),
        }
        sample=' '.join(new_examples[n])
        model=sample
    elif typ=='writing':
        genre,output,sample=WRITING[n]
        if n==69:sample=sample.replace('\n','\n\n')
        model=sample
        rule='Будуємо саме вказаний жанр: перевіряємо його частини, зміст і доречність адресатові. Не додаємо однакову вимогу «2 факти + 2 причини» до кожного жанру.'
        # Read a brief, do not add a second unrelated narrative to a drafting lesson.
        text=output
        qs=GENRE_ITEMS[n]
        genre_rules={
            11:'Автобіографія: перша особа, часовий зв’язок. Мікромодель: Last year I joined a club. Now I am learning a new skill. I am visiting an exhibition next Friday.',
            25:'Opinion paragraph: позиція → причини → приклад → висновок. Мікромодель: In my opinion, comfort matters because it helps people focus. For example,… To sum up,…',
            53:'Vlog review: basic information → оцінка з прикладом → limitation → адресна recommendation. Мікромодель: The diagrams explain the idea clearly, but the episode should name its sources.',
            98:'Leaflet: короткий заголовок та імператив+мета. Мікромодель: Bring a reusable bottle to reduce single-use waste. Запасний план: If it rains,…',
            112:'Friendly e-mail: Hi Sam,… → зв’язне повідомлення → Best, Alex. Мікромодель минулої нереалізованої можливості: If we had checked the map, we would have found the gallery.',
        }
        if n in genre_rules:rule=genre_rules[n]
        if n==69:rule='CV — рубрики: Name, Education, Skills, Experience, Interests. Experience називає діяльність, Skills — навичку з доказом, Interests — захоплення. Мікроприклад: Skills: teamwork — worked with two classmates to prepare a display.'
        if n==39:rule='Survey report називає вибірку й чисельності; percentage = count / total ×100. Приклад:2 of 10 students = 20%. Висновок обмежуємо саме цією вибіркою.'
        if n==84:rule='Biography chart: Date / Achievement / Importance. Дата й подія — факти; значення формулюємо обережно, без вигаданих причинних висновків.'
    elif typ=='portfolio':
        genre='портфоліо: вибір → корекція → перенесення'
        pindex=([58,118,119,120,121].index(n))
        ptargets=['a past/present contrast','reported speech','a relative clause','a conditional','a genre feature']
        target=ptargets[pindex]
        rule='Порівнюємо початкову й виправлену форму; пояснюємо причину; переносимо навичку в новий приклад. Наявність зошита не є умовою участі.'
        text=f'Fictional portfolio focus: {target}. Alex kept two versions of a school-project task. The first version was understandable but did not make the meaning precise. The revision explains the time, speaker or purpose more clearly. A useful portfolio note shows the original, the correction, the reason and a new example.'
        qs=[item('What shows transfer of learning?','a new example',['copying the key without explanation','counting pages'],'Перенесення — застосування в новому контексті.'),item('Which record is useful?','original, correction, reason',['only a mark','only a title'],'Зберігаємо доказ виправлення.')]
        output=f'Choose one previous artifact with {target}; revise two details, explain each change and write one new example. If no artifact is available, use the two model versions supplied below.'
        oldnew=[('Yesterday Alex go to the club. / Yesterday Alex went to the club.','Go → went: завершена минула подія.'),('Yesterday she said, “I will help.” Today: She said she will help. / She said she would help.','У заданому завершеному минулому контексті will → would.'),('My tablet, that is on the table, is useful. / My tablet, which is on the table, is useful.','Non-defining: which, не that.'),('Yesterday we missed the bus. If we left earlier, we would catch it. / If we had left earlier, we would have caught it.','Завершене минуле: Third conditional.'),('CV: I like books and my school is nice. / Skills: organisation — arranged a class book display.','CV має рубрику й конкретний доказ навички.')][pindex]
        text+='\n\nFallback versions (first / revised): '+oldnew[0]
        second=[
            ('Look! She read now. / Look! She is reading now.','Right now: Present Continuous.'),
            ('He said me that it was ready. / He told me that it was ready.','Told + object, said to + object.'),
            ('The person which scans the pages is Alex. / The person who scans the pages is Alex.','Who позначає особу.'),
            ('Tomorrow: if it rains, we would stay indoors. / Tomorrow: if it rains, we will stay indoors.','Реальна майбутня можливість: First conditional.'),
            ('CV: I am good at everything. / Experience: helped organise a three-person class display.','Конкретний досвід замість непідтвердженої загальної оцінки.'),
        ][pindex]
        text+='\n\nSecond fallback pair: '+second[0]
        sample='Correction 1: '+oldnew[0].split(' / ')[1]+' '+oldnew[1]+' Correction 2: '+second[0].split(' / ')[1]+' '+second[1]+' New example: '+['Last week I visited a gallery.','Yesterday he said he would check the source.','My laptop, which I use for schoolwork, is useful.','If they had checked the hours, they would have arrived earlier.','Skills: teamwork — helped two partners prepare a short report.'][pindex]
        model=sample
    elif typ=='assessment':
        genre='обмежена діагностика / контроль: види перевіряються окремо'
        units=([1,2,3,4] if n==57 else [5,6,7,8] if n in (116,117) else [u-1,u])
        details={1:'personality',2:'repairing clothes',3:'club teamwork',4:'checking media sources',5:'job skills',6:'a useful device',7:'reducing waste',8:'a museum route'}
        text='A fictional school team is preparing a display. '+ ' '.join(f'Station {i+1} is about {details[x]}.' for i,x in enumerate(units))+' The team has twenty minutes for a first draft. Each station needs one clear example rather than a long list. Before sharing the display, the students will check that its information is accurate.'
        qs=[item('How much time is available for the first draft?','twenty minutes',['ten minutes','forty minutes'],'Текст прямо вказує twenty minutes.'),item('What does each station need?','one clear example',['a long list','private contact details'],'Each station needs one clear example.'),item('What will the team check?','the accuracy of information',['only the colours','the viewers’ private lives'],'Check that its information is accurate.')]
        # One targeted item from each covered unit; a cap keeps a 45-minute window feasible.
        gm={1:6,2:23,3:34,4:48,5:67,6:78,7:93,8:107}
        for x in units:qs.append(GRAMMAR[gm[x]][2][0])
        rule='Контрольна картка має один короткий інтегрований текст і 5–7 пунктів, а не чотири повні тексти. Докази видів діяльності записують окремо; формат не замінює критерії закладу.'
        if n==117:
            output='After hearing the teacher-only message, prepare a 45–60 second spoken explanation: compare a job skill and a useful device; then give one environmental and one travel recommendation. Respond to one follow-up question in an arranged oral window.'
            sample='A librarian needs organisation skills to help readers. A tablet can help find information, but its sources still need checking. I suggest reusing suitable materials to reduce waste. Before a museum visit, we should check the opening hours. If we had checked them last time, we would have arrived earlier.'
        else:
            output='Write a short display note (45–65 words): choose two different stations, give one accurate contextual example for each, and explain one useful decision. No requirement to cover every station in a long essay.'
            sample=f'Our display links {details[units[0]]} with {details[units[-1]]}. Each station should show one clear example. This will help visitors understand the main point without reading a long list. We have twenty minutes for a draft, so I suggest choosing useful information first and checking its accuracy before sharing the display.'
        model='Приклади та підказки до контрольних мовних пунктів — тільки у key.md.'
    else:
        genre={'reading':'читання: факт → пояснення','listening':'слухання: головна думка → деталі','speaking':'діалог: запитання → відповідь → реакція','recap':'повторення: помилка → причина → новий приклад','starter':'власний план практики'}[typ]
        # Existing reading questions have explicit source-supported answers; no copied grammar MCQ.
        for q in s['questions'][3:5]:
            qs.append(item(q['prompt'].replace('За адаптованим текстом: ',''),q['choices'][q['answer']],[v for j,v in enumerate(q['choices']) if j!=q['answer']],'Доказ у наведеному тексті: '+q['choices'][q['answer']]))
        first=s['reading'].split('. ')[0].rstrip('.')+'.'
        # Repeated sessions have a genuinely different cognitive target, not just a new name/date.
        previous=[a for a in DATA['lessons'] if a['number']<n and a.get('section_ids')==l.get('section_ids')]
        if typ=='listening':
            output='After listening, give two answers and write one short response explaining a useful next step. The transcript is teacher-only until the listening task is complete.'
            sample=first+' A useful next step is to check the details before deciding.'
        elif typ=='speaking':
            output=f'In pairs, make a 6-turn dialogue about {TOPICS.get(u,"learning")}: request information, answer with a text-based detail, ask for a reason, answer, offer an alternative and react politely. No essay is required.'
            sample=f'A: What does the text tell us?\nB: {first}\nA: Why is that useful?\nB: It gives a concrete example for our decision.\nA: Could we check another option too?\nB: Yes, let us compare the details before deciding.'
        elif typ=='recap':
            g=GRAMMAR[{1:6,2:23,3:34,4:48,5:67,6:78,7:93,8:107}.get(u,6)]
            qs+=g[2][:2]
            output='Choose one language item you initially found difficult. Explain its time/meaning, correct it, then use the form in one new context. Record “before / after / why”.'
            sample=g[2][0]['prompt'].replace('___',g[2][0]['answer'])+' '+g[2][0]['why']+' New example: '+g[2][1]['prompt'].replace('___',g[2][1]['answer'])
        elif typ=='starter':
            output='Write a 3-step English practice plan: one activity, a realistic time and a way to check learning. Add one reason for your choice.'
            sample='I will read a short English text for five minutes on Tuesday. I will record three useful phrases. I will use one phrase in a new sentence to check my learning. I chose a short task because I can repeat it regularly.'
        elif previous:
            genre='повторне читання: порівняння й аргументація'
            output='Do not repeat only the factual answers from the earlier session. Write a two-column note: one fact / one possible interpretation. Then give a different recommendation and support it with one text detail.'
            sample=f'Fact: {first}\nInterpretation: the writer gives an example rather than a rule for everyone.\nRecommendation: check an alternative before deciding, because a single example does not show every possible choice.'
        else:
            output='Make a reading note: two short facts from the text and one clearly labelled opinion or question. Underline one phrase as evidence. Do not treat an inference as a quoted fact.'
            facts='. '.join(s['reading'].split('. ')[:2]).rstrip('.')+'.'
            sample=f'Facts: {facts}\nMy opinion: a specific example is more useful than a label.\nMy question: what other option could be considered?'
        model='In the text, … . My interpretation/question is … .' if typ=='reading' else sample
    if n in (46,47):
        text='Fictional class TV survey: eight students chose a science series, six chose a comedy and six chose a sports programme. Each student chose one favourite. The science series explains an experiment in each episode. The comedy tells stories about neighbours, while the sports programme reviews matches. These preferences describe only this group, not every teenager.'
        qs=[item('How many students chose the science series?','eight',['six','twenty'],'Таблиця вказує eight.'),item('Which claim is supported?','The results describe this group only.',['All teenagers prefer science.','Nobody likes comedy.'],'Останнє речення обмежує узагальнення.')]
        output=('Make a note with two survey facts and one question about programme content.' if n==46 else 'Compare two programme types in a two-column note. Give a recommendation for a fictional viewer interested in experiments; distinguish the survey result from your opinion.')
        sample=('Eight students chose the science series. Six chose a comedy. My question: what experiment does the next episode explain?' if n==46 else 'Science series: explains experiments. Comedy: tells stories about neighbours. I would suggest the science series for a viewer interested in experiments because its content matches that interest. This recommendation is based on programme content, not a claim about all teenagers.')
    if n in (76,77):
        text='Marie Curie shared the Nobel Prize in Physics in 1903. She received the Nobel Prize in Chemistry in 1911. Her research concerned radioactivity. A biography note should distinguish a documented achievement from a personal judgement. The years and prize subjects are facts; calling an achievement inspiring is an interpretation.'
        qs=[item('Which prize did Marie Curie receive in 1911?','Chemistry',['Physics','Literature'],'1911: Chemistry.'),item('Which statement is a judgement rather than a dated fact?','Her work is inspiring.',['She shared the Physics prize in 1903.','She received the Chemistry prize in 1911.'],'Inspiring позначає оцінку, а не подію з датою.')]
        output=('Make a two-row year / achievement note and add one labelled interpretation.' if n==76 else 'Write two connected biography sentences using the dated facts. Then explain the difference: electric = powered by electricity; electrical = related to electricity. Complete one example of each.')
        sample=('1903 — shared the Nobel Prize in Physics. 1911 — received the Nobel Prize in Chemistry. Interpretation: I find the two achievements inspiring.' if n==76 else 'Marie Curie shared the Nobel Prize in Physics in 1903 and received the Chemistry prize in 1911. An electric car is powered by electricity; an electrical engineer works with electrical systems.')
        rule='Факти біографії підтверджуємо джерелом, оцінні слова позначаємо як власне ставлення. Electric / electrical не взаємозамінні в усіх сполученнях.'
        model=sample
    if n==84:
        output='Use this verified fact card about Marie Curie: 1898 discovery of polonium and radium with Pierre Curie; 1903 shared Nobel Prize in Physics; 1911 Nobel Prize in Chemistry. Make a 3-row Date / Achievement / Importance chart; separate fact from interpretation in the final column.'
        text=output
        sample='1898 | Discovery of polonium and radium with Pierre Curie | Added to knowledge of chemical elements.\n1903 | Shared Nobel Prize in Physics | Recognition of research on radiation.\n1911 | Nobel Prize in Chemistry | Recognition of work on radium and polonium.'
        model=sample
    if n in LISTENING_CARDS:
        text,one,two=LISTENING_CARDS[n]
        qs=[one,two]
        output='After listening, answer the two questions and write a two-line response: one accurate detail and one practical next step. Label the suggestion as your own, not as a quoted fact.'
        sample='Fact: '+one['answer']+' My suggested next step: ask one follow-up question to clarify the decision.'
        model=sample
    if n==52:
        genre='радіоінтерв’ю: presenter / guest'
        text='Fictional school radio brief: the presenter interviews a guest about a science programme. The guest values clear demonstrations but wants sources to be named. The interview has time for one question, one follow-up and a brief conclusion; it should separate the guest’s opinion from a documented fact.'
        qs=[item('What does the guest want named?','Sources',['Private contacts','Every viewer’s age'],'The brief says sources should be named.'),item('Which statement is an opinion?','The guest values clear demonstrations.',['The format includes a follow-up.','The interview has a guest.'],'Values expresses the guest’s judgement.')]
        output='Create a6-turn radio interview: opening question, guest answer, follow-up asking for a reason, reason with example, presenter summary and guest confirmation. No real recording or broadcast is required.'
        sample='Presenter: What do you value in a science programme?\nGuest: I value clear demonstrations.\nPresenter: Why are sources important too?\nGuest: They let viewers examine a claim, for example a claim about an invention.\nPresenter: So clear examples help, but the evidence should also be named.\nGuest: Yes, that is my view.'
        model=sample
    if n==117:qs=[]
    # Narratives are for reading; listening students must not receive the same transcript beforehand.
    transcript=text if typ=='listening' else ('A different team is preparing a display for the next lesson. It has fifteen minutes for its first draft. Before sharing, the team will check the spelling and dates. Robin will ask another editor to read the draft.' if typ=='assessment' else '')
    return dict(n=n,u=u,section=s['id'],type=typ,genre=genre,text=text,rule=rule,model=model,questions=qs,output=output,sample=sample,transcript=transcript,control=control)

SAFETY='''Під час сигналу й переміщення навчання зупиняється. Далі — правила закладу й вказівки відповідальних. B починається лише після дозволу, за наявності місця, освітлення й можливості читати; інакше перенести. В укритті немає хорового звуку, рухових ігор, пересування груп чи розповідей про особисті травматичні події. D виконують у доступний час при достатньому світлі, а не в темряві. Папір видають завчасно; за відсутності паперу спочатку відновлюють доступ, а не ставлять нуль.'''
SEL='''Авторське вікове адаптування окремих підходів офіційного українського електронного комплекту СЕН «Зерна» для9класу; це не офіційна вправа, не повний курс і не сертифікована реалізація програми. Вихідні матеріали орієнтовано на1–6класи; для9збережено конкретну навичку, дію й необов’язкове осмислення переносу, а не дитячу форму гри. Чотири сили джерела: співпраця, усвідомленість, когнітивні навички, емоційний інтелект. Цей пакет тренує передусім увагу/планування та співпрацю, не заявляє охоплення всіх чотирьох сил у кожному уроці. Учень може обрати «сам / з опорою / пізніше», не пояснюючи емоцій. Вигаданий герой не готовий відповісти: можна запропонувати “Take your time. You can write your answer”, або пропустити практику. Не оцінювати емоції, камеру, особистість, щирість чи готовність ділитися досвідом. Мовний продукт оцінюють окремо; за SEL-рефлексію балів немає. Джерельне зіставлення й межі — [SEL_NUSH_REVIEW.md](../SEL_NUSH_REVIEW.md).'''
NUSH='''Для2026/2027офіційний графік передбачає перший випуск9класу за Держстандартом НУШ; це не підстава називати цей клас непілотним «неНУШ» лише за номером. Конкретну освітню/навчальну програму закладу, очікувані результати й критерії цього класу слід підтвердити окремо. Орієнтири: Держстандарт898,п.5(цикл7–9),п.6(компетентнісний підхід),п.9(наскрізні вміння); наказ1093для учнів за цим стандартом. Вигаданих кодів результатів немає; пакет сам собою не доводить виконання всієї програми.'''
RESULT_GROUPS='''Звірка з наказом1093,додаток2,«Іноземні мови»: група1—сприйняття усної інформації/письмових текстів; група2—усна, письмова й онлайн-взаємодія; група3—надання інформації та висловлення думок/ставлення. Читання й слухання можуть давати докази групи1; реальний обмін репліками —групи2; власний монолог/текст —групи3. Граматичний MCQ сам не доводить опанування цілої групи; письмовий чат не доводить усного вміння. Локальні0–6/0–2—сирі діагностичні показники, не офіційна альтернативна шкала і не SEL-бали. Для підсумку використовують затверджені критерії й достатні докази конкретних груп.'''


def sel_profile(c):
    t=c['type']
    if t in ('writing','portfolio'):
        focus='Плануй і перевіряй'
        action=f'Перед продуктом «{c["genre"]}» учень обирає одну потрібну частину, робить короткий план, перевіряє її за вимогою жанру та за бажанням уточнює рішення.'
        prompt=f'Яка перевірка допомогла тобі працювати з форматом «{c["genre"]}»? Де ще можна використати такий порядок дій?'
        domain='когнітивні навички: планування й самоконтроль'
    elif t=='speaking':
        focus='Уточнюй і давай слово іншому'
        action='У короткому діалозі учень дає партнерові завершити репліку, ставить одне уточнення й перевіряє, чи правильно зрозумів зміст; у соло-варіанті пише дві ролі як репетицію.'
        prompt=f'Яке уточнювальне запитання допомогло б партнерам у ситуації «{c["genre"]}» зрозуміти одне одного? Де ще воно доречне?'
        domain='співпраця: черговість і зрозуміле спілкування'
    elif t in ('grammar','lexis','recap'):
        focus='Зупинись, знайди ознаку, обери'
        action=f'Перш ніж обрати відповідь для «{c["genre"]}», учень за бажанням робить коротку паузу, знаходить часову/смислову ознаку і перевіряє своє рішення. У перевірному раунді пояснення дається після фіксації першої спроби.'
        prompt=f'Яка ознака допомогла обрати рішення у завданні «{c["genre"]}»? Де ще стане в пригоді пауза перед вибором?'
        domain='когнітивні навички: увага й свідомий вибір'
    else:
        focus='Відділяй факт від припущення'
        subject=(c['questions'][0]['prompt'] if c['questions'] else 'план виставки й уточнення до команди')
        action='Учень знаходить один доказ у джерелі, відокремлює його від власного припущення й за бажанням формулює нейтральне уточнення до вигаданого героя.'
        prompt=f'Який спосіб перевірки допоміг у питанні «{subject}»? У якій іншій ситуації він допоміг би перевірити припущення?'
        domain='когнітивні навички: уважне опрацювання інформації'
    return {'focus':focus,'action':action,'prompt':prompt,'domain':domain}

SOURCE_NOTE='[NobelPrize.org: Marie Curie, Physics 1903](https://www.nobelprize.org/prizes/physics/1903/marie-curie/facts/) і [Chemistry 1911](https://www.nobelprize.org/prizes/chemistry/1911/summary/). Факти перевірено 18.10.2026; текст стисло адаптований, не цитата.'

def schedules(c):
    sp=sel_profile(c)
    t=c['type'];aud=t in ('listening','assessment');control=c['control']
    intake=('Прочитати teacher-only текст двічі з короткою паузою. «First find the main idea, then the details». До завершення не показувати transcript.' if aud else '«Read the main source once. Underline one useful fact or contextual clue». Один основний текст; підручник не потрібний.')
    intake_evidence=('Два факти на слух; за відсутності аудіоканалу «не перевірено», не підміна читанням.' if aud else 'Підкреслений факт/контекст; не другий резервний текст.')
    focus=('«Work independently on the numbered items». Не показувати key; зафіксувати дозволені опори до початку.' if control else '«Explain a choice, not just its letter». Працювати лише з цільовими пунктами цієї картки; можливе заміщення грою1.')
    production=c['output'].replace('|','/')
    rows=[('00–03','Назвати тему, точний мінімум і канал відповіді. «Fictional details are enough. Camera is optional».','Учень обирає папір/чат/голос; особисті розповіді не потрібні.'),
          ('03–08',('Оголосити критерії та дозволені опори; пояснити процедуру без демонстрації відповідей.' if control else 'Пояснити опору уроку; змоделювати один аналогічний приклад без виконання всіх завдань за учнів.'),'Учень записує критерій успіху; питає про незрозуміле.'),
          ('08–16',intake,intake_evidence),
          ('16–24',focus,f"Самостійні відповіді: {len(c['questions'])} пунктів максимум; на пояснення — один обраний пункт."),
          ('24–36',production,'Один головний продукт заданого жанру; 12 хв на коротку чернетку/діалог/корекцію. Не додаються ще есе й другий діалог.'),
          ('36–41',('Зібрати письмові роботи. Для усної складової: 2–3 індивідуальні проби по60–90с; іншим — погоджене окреме вікно. Взаємна практика пари не є перевіркою вчителем усіх.' if control else 'Попросити пояснити один вибір або перевірити одну частину жанру. Можливе заміщення грою2 замість цього блоку.'),'Один перевірний доказ. Усний/письмовий канал позначено окремо; 117: усна проба, решта — не перевірено до свого вікна.' if control else 'Одна відповідь з поясненням або самоперевірка за критерієм; не новий великий продукт.'),
          ('41–45','41–43: повернутися до навички «'+sp['focus']+'». Необов’язкове питання: '+sp['prompt']+' 43–45: назвати точку відновлення й доступний термін ДЗ.','Можна мовчки поміркувати, коротко відповісти чи пропустити рефлексію без пояснення й без бала; зберегти мовний артефакт.')]
    if t=='writing':
        rows[2]=('08–16','«Read the genre brief. Mark its required parts». Розібрати адресата й потрібний формат; не читати ще загальний текст юніту.','План жанру: поля CV / рядки chart / висновок survey / структура e-mail саме цього уроку.')
    if t=='portfolio':
        rows[2]=('08–16','«Choose your earlier artifact, or use the fallback versions». Вибрати одну навичку; не вимагати попередній зошит.','Початкова й виправлена версії; у разі відсутності роботи — готова пара в роздатці.')
        rows[4]=('24–36','«Explain two revisions, then transfer the skill to one new example». Для готової fallback-пари друга корекція: покращити точність/доречність нового власного прикладу.','Картка було/стало/чому + новий приклад. Без есе про загальну тему.')
    if c['n']==117:
        rows[3]=('16–24','«Plan your spoken explanation; mark two language points». Письмових резервних MCQ цього дня немає: працюємо зі слуханням та усним планом.','Короткий план усної відповіді; написаний план не зараховується за говоріння.')
        rows[4]=('24–36','У парах підготувати й по черзі висловити45–60-секундне пояснення за prompt. Партнер ставить одне уточнення; вчитель збирає лише явно прослухані докази.','Усна репетиція/запис за доступності. Усі діти не вважаються перевіреними через саме перебування в парі.')
    b=[('00–02','Після дозволу перевірити умови. Мовчки показати розділ «Мінімум B/D».','Залишається на місці; може обрати паузу.'),('02–06','«Прочитай тільки коротку опору B/D й конкретне завдання під нею».','Не читає весь45-хв пакет; знаходить потрібний контекст.'),('06–12','«Виконай конкретне коротке завдання цієї дати під опорою».','Один мовний приклад або одне поле/рядок потрібного жанру.'),('12–15','«Познач де потрібна допомога. Збережи аркуш». Контроль не проводити.','Фіксує точку повернення; мінімум не називається завершеним45-хв уроком.')]
    d=[('00–02','Друкована інструкція: «Коли є безпечні умови й світло, відкрий Мінімум B/D».','Працює в доступний час без мережі.'),('02–05','«Прочитай коротку опору й точне завдання».','Короткий контекст; без обов’язкового аудіо.'),('05–10','«Запиши відповідь на завдання короткої картки цієї дати».','Мінімальний письмовий доказ за10хв; не повний контроль.'),('10–15','Необов’язково: «Уточни приклад і напиши одне питання вчителю».','Розширення лише за ресурсом; здача після доступного контакту.')]
    crow=[(time,'[Дистанційно: чат/доступний файл; камера добровільна] '+teacher,student) for time,teacher,student in rows]
    return {'A':rows,'B':b,'C':crow,'D':d}


def transfer_items(c):
    n=c['n'];t=c['type']
    if n in GENRE_TRANSFER:return GENRE_TRANSFER[n]
    if n in GRAMMAR_TRANSFER:return GRAMMAR_TRANSFER[n]
    if t=='lexis':
        w1,w2,w3=LEX[n]
        return [item(f'New editor note: choose a term for «{w3[1]}».',w3[0],[w1[0]],f'{w3[0]} — {w3[1]}.'),item(f'Choose the phrase that retains the meaning of «{w1[1]}» in a new note.',w1[0],[w2[0]],f'{w1[0]} — {w1[1]}.')]
    if t=='recap':return GRAMMAR_TRANSFER[{1:6,2:23,3:34,4:48,5:67,6:78,7:93,8:107}.get(c['u'],6)]
    if t=='portfolio':
        if n==121:return GENRE_TRANSFER[69]
        return GRAMMAR_TRANSFER[{58:6,118:48,119:78,120:107}[n]]
    if t=='assessment':
        if n==117:
            return [item('Who will ask another editor to read the draft?','Robin',['Sam'],'The audio names Robin.'),item('When is the display needed?','the next lesson',['the next week'],'The audio specifies the next lesson.')]
        import re
        stations=re.findall(r'Station (\d+) is about ([^.]+)',c['text'])
        return [item('What topic belongs to station'+stations[0][0]+'?',stations[0][1],[stations[-1][1]],'The numbered display brief supplies this topic.'),item('What topic belongs to station'+stations[-1][0]+'?',stations[-1][1],[stations[0][1]],'Use the final numbered station in the brief.')]
    assert n in READING_TRANSFER,('Missing contextual transfer cards',n)
    return [item(prompt,answer,[wrong],'This particular detail is stated in the lesson source; check its named person, event, category or sequence.') for prompt,answer,wrong in READING_TRANSFER[n]]


def games(c):
    sp=sel_profile(c)
    q=c['questions'];n=c['n'];transfer=transfer_items(c)
    if n==117:
        q=[item('How much time does the team have for its first draft?','fifteen minutes',['twenty minutes'],'The independent audio says fifteen.'),item('What will the team check?','the spelling and dates',['the price and colours'],'The audio specifies spelling and dates.')]
    a=q[0];b=q[min(1,len(q)-1)]
    def stimulus(x,round_number,position):
        options=[x['answer'],x['wrong'][0]]
        if (n+round_number+position)%2:options.reverse()
        return x['prompt']+' Choices: '+' / '.join(options)
    first=''
    for j,x in enumerate([a,b],1):
        first+=f"**Хід{j}:** “{stimulus(x,1,j)}” Учень: “I choose … because …”. Правильно → ще1перевірка; помилка → чернетка повертається на доопрацювання. Ключ: **{x['answer']}**. Причина: {x['why']}\n\n"
    second=''
    for j,x in enumerate(transfer,1):
        second+=f"**Новий стимул{j}:** “{stimulus(x,2,j)}” Ключ після першої спроби: **{x['answer']}**. Причина: {x['why']}\n\n"
    return f'''# Ігрові симуляції ·9клас · урок {n:03d}

**Точний фокус:** {c['genre']}. Teacher-only: тут є ключі. Усі персонажі/навчальні ситуації вигадані, якщо історичне джерело не зазначене окремо.

## 1. Майстерня рішення — засвоєння,8хв

**Замість16–24 A/C**, а не додаткові8хв. При підсумковому контролі цю гру використовують як окреме попереднє тренування, не всередині самостійного доказу. Ролі: редактор і консультант; соло — той самий учень спершу редактор, потім читає пояснення. Початковий стан: чернетка0/2, дозвіл на використання ще не отримано. Мета — ухвалити два предметні рішення саме цієї дати й підготувати фрагмент «{c['genre']}».

00–02: прочитати першу картку й зробити вибір.02–05: друга картка й пояснення.05–08: виправити помилку/створити короткий фрагмент головного продукту.

{first}
**Хід3, короткий фрагмент:** {c['output']} У грі виконати лише одну потрібну частину; повний короткий продукт має свій блок24–36. Приклад прийнятного повного варіанта, з якого можна взяти одну частину:

{c['sample']}

**SEL-дія перед першим ходом00–02; рефлексія05–08:** {sp["action"]} Після короткого фрагмента запропонувати необов’язкове запитання: {sp["prompt"]} Можна поміркувати мовчки/пропустити; відповіді й емоції не оцінюються. Це авторське адаптування для9класу з орієнтиром на4сили офіційного електронного комплекту; не офіційна вправа «Зерен».\n\n**Стан успіху:** два точні рішення й один фрагмент із доречною формою/жанром. Відкритий фрагмент: потрібна частина жанру/цільова форма, тематично точний зміст, зрозуміле формулювання. Варіанти приймаються, якщо є ці3ознаки. Помилка → консультант показує лише релевантне правило/фразу джерела → учень пояснює виправлення й повторює. Запис «після підказки» відокремлюється від першої спроби. Мовний доказ — відповідь+пояснення+фрагмент, не кількість жетонів.

## 2. Незалежна редакторська перевірка —5хв

**Замість36–41 A/C**, не додатковий тест після45хв. Інший редактор отримує нові наведені нижче стимули. Стартовий стан:2невирішені редакторські питання; жодної підказки до першої відповіді. Картки й ключі гри1закриті.

00–02: перший новий стимул.02–04: другий новий стимул й одна англійська репліка-пояснення.04–05: спочатку фіксація мовного доказу, потім необов’язкова коротка рефлексія «{sp["prompt"]}»; навчальний повтор після фіксації. SEL-відповідь не додає й не знімає бал.

{second}
Учень каже/пише “The source / context shows …” або “This belongs under … because …”. Правильний вибір з поясненням → питання закрито; неправильний вибір → питання залишається відкритим до зворотного зв’язку. **Стан успіху:** обидва правильні рішення й осмислена причина. Фіксація:0–2точних виборів та окремо є/немає пояснення. Це вузький доказ цілі, не автоматична підсумкова оцінка. Після запису першого результату вчитель дає одну підказку і дозволяє повтор; повтор позначається «з опорою» й не стирає першу самостійну спробу.

## Папір, чат, соло, тихе укриття

Папір: картки за партою, позначки стану ручкою. Чат без камери: приватні вибори й пояснення; це письмовий доказ, не говоріння. Соло: ключ закрито до першої спроби; самоперевірка не видається за перевірку вчителем. Укриття: після дозволу й за умов читання, тільки один короткий письмовий хід на місці **замість** частини мінімуму B/D. Без хорового звуку, руху й особистих історій. Якщо умов немає — перенести. Повні8+5хв не додаються до15хв укриття. Камера/емоції/життєві обставини не є результатом гри.
'''


def build(l):
    import hashlib
    c=card(l);sp=sel_profile(c);n=l['number'];slug=f'{n:03d}';p=DEST/slug;p.mkdir(exist_ok=True)
    schedules_=schedules(c)
    qq='';keys='';answers=[]
    for i,q in enumerate(c['questions'],1):
        opts,letter=choices(q,n,i)
        qq+=f'{i}. {q["prompt"]}\n\n{opts}\n\nAnswer: _____ Reason/evidence: __________________________________\n\n'
        keys+=f'{i}. **{letter} — {q["answer"]}**. {q["why"]}\n\n'
        answers.append({'number':i,'answer':q['answer'],'letter':letter,'rationale':q['why']})
    if c['type']=='grammar':
        small=c['questions'][0]['prompt'].replace('___',c['questions'][0]['answer'])+' '+c['questions'][0]['why']
        mintask=c['questions'][-1]['prompt']+' Choose: '+c['questions'][-1]['answer']+' / '+c['questions'][-1]['wrong'][0]
        minkey=c['questions'][-1]['answer']+' — '+c['questions'][-1]['why']
    elif c['type']=='lexis':
        small='; '.join(f'{w} — {uk}' for w,uk,_ in LEX[n])
        mintask=c['questions'][-1]['prompt']
        minkey=c['questions'][-1]['answer']+' — '+c['questions'][-1]['why']
    elif c['type']=='writing':
        mini={
            11:('Past event: Last year I joined a club.','Write one different fictional past event beginning Last year.','Last year I visited a gallery.'),
            25:('Opinion: I think comfortable shoes suit a school trip.','Add one practical reason for this opinion.','They make a long walk easier.'),
            39:('Survey: 20 students; 10 sport, 6 music, 4 film. 10 / 20 = 50%.','Complete: Music was chosen by___%of this group.','30%:6/20×100.'),
            53:('Review: the fictional vlog uses clear diagrams but does not name sources.','Write one strength or limitation with a specific detail.','The diagrams explain the topic clearly; however, the sources are missing.'),
            69:('CV example: Skills: teamwork — helped two classmates prepare a display.','Write one Skills field with different evidence, using fictional details.','Skills: organisation — arranged books by topic for a class display.'),
            84:('Biography chart:1903—shared Physics Nobel;1911—Chemistry Nobel.','Write the Date / Achievement row for1911.','1911 | Nobel Prize in Chemistry.'),
            98:('Leaflet model: Bring a reusable bottle to reduce single-use waste.','Write one action with a practical reason for an Eco Day.','Swap suitable clothes so they can be used again.'),
            112:('E-mail line: We missed the museum yesterday because we arrived late.','Complete a past reflection: If we had checked the hours,…','…we would have arrived earlier.'),
        }
        small,mintask,minkey=mini[n]
    elif c['type']=='speaking':
        small='. '.join(c['text'].split('. ')[:2]).rstrip('.')+'.'
        mintask='Write a two-turn information exchange: ask about one source detail and answer using that detail. This is written rehearsal, not an oral test.'
        minkey='\n'.join(c['sample'].split('\n')[:2])
    elif c['type']=='starter':
        small='Practice plan: I will read for five minutes on Tuesday and record three useful phrases.'
        mintask='Write one different practice activity and a realistic time; add one way to check your learning.'
        minkey='I will listen to a short message for five minutes on Wednesday and record two details to check my understanding.'
    elif c['type']=='recap':
        focusq=c['questions'][-2];nextq=c['questions'][-1]
        small=focusq['prompt'].replace('___',focusq['answer'])+' '+focusq['why']
        mintask=nextq['prompt']+' Choose: '+nextq['answer']+' / '+nextq['wrong'][0]
        minkey=nextq['answer']+' — '+nextq['why']
    elif c['type']=='portfolio':
        small=c['sample'].split('Correction 2:')[0]
        mintask='Write one new example that applies the corrected feature; explain what stayed accurate.'
        minkey=c['sample'].split('New example:')[-1]
    else:
        shorttext=c['transcript'] if c['type']=='listening' else c['text']
        small='. '.join(shorttext.split('. ')[:2]).rstrip('.')+'.'
        mintask='Copy one accurate short fact from this source and add one clearly labelled question. This is reading, not a listening test.'
        minkey=shorttext.split('. ')[0].rstrip('.')+'. Question: What other detail would help us decide?'
    minimum=f'''## Мінімум B/D: окрема коротка картка

**Опора:** {small}

{mintask}

Не потрібно виконувати весь основний пакет.

My example / field / row: __________________________________________

__________________________________________________________________

Одне питання вчителю (можна українською): ___________________________

B:2хв готовність +4хв опора +6хв приклад +3хв збереження. D:2+3+5хв, потім необов’язково до5хв уточнення. Це тренувальний фрагмент, не повний урок або контроль. Результат можна передати пізніше.
'''
    audio=c['type'] in ('listening','assessment')
    maintext=('[Teacher reads the transcript twice. The transcript is not printed here before the listening task.]' if c['type']=='listening' or n==117 else c['text'])
    h=f'''# Роздатка ·9клас · урок {n:03d} · {l['date']}

**Тема календарного плану:** {l['topic']}

Умовне ім’я/код: __________________ Фактична дата: _______________

Особисті дані й камера не потрібні. Під час переміщення завдання зупиняються. У темряві не читай і не пиши; повернись, коли є безпечні умови. Можна зробити паузу; термін здавання узгоджується за доступністю.

{minimum}
## Основний маршрут A/C —45хв

**Мовний фокус / жанр:** {c['genre']}

**Опора:** {c['rule'] if not c['control'] else 'Контекст кожного мовного пункту є частиною завдання. Дозволені опори оголошує вчитель до початку.'}

### Джерело / brief

{maintext}

### Цільові пункти

{'На117 цей блок — закритий резерв читання/мовного вжитку. До завершення самостійного слухання учень працює лише з аудіопитаннями й усним prompt; цей резерв не відкривати.' if n==117 else ''}

{qq}
### Один головний продукт

{c['output']}

Для навчального мінімуму: один потрібний фрагмент і позначка, що ще треба завершити. Для повного A/C — весь зазначений короткий жанр/продукт. Це не вимога написати120–130слів за7хв.

__________________________________________________________________

__________________________________________________________________

__________________________________________________________________

__________________________________________________________________

__________________________________________________________________

__________________________________________________________________

__________________________________________________________________

__________________________________________________________________

### Після завершення

Мій точний пункт повернення: _______________________________________

Моє мовне питання / одне виправлення: _______________________________

**За бажанням, без бала:** {sp["prompt"]} Можна подумати мовчки або пропустити; приватні історії не потрібні.

**Резерв, тільки за окремим вибором вчителя:** розширити продукт однією новою деталлю й пояснити її; цей резерв не додається до45хв. На інших уроках аудіювання/говоріння не приписуються автоматично, якщо їх не перевіряли.

**ДЗ, до10хв:** виправити один цільовий пункт із поясненням або завершити одну потрібну частину чернетки. Не виконувати заново весь пропущений урок. Після B/D спершу зберегти мінімум, решту погодити з учителем. Контроль удома не зараховується без погодженої процедури.
'''
    if n==117:
        start=h.index('### Цільові пункти');end=h.index('### Один головний продукт',start)
        h=h[:start]+h[end:]
    if audio:
        h+='''\n### Слухання: teacher-only повідомлення\n\n1. How much time does the team have for a first draft? __________\n\n2. What will the team check before sharing? ____________________\n\nБез аудіоканалу ці два питання не виконуються навмання: «не перевірено». Письмовий transcript після завершення — для аналізу, не доказ слухання.\n''' if c['type']=='assessment' else ''
    if n in (76,77,84):h+='\n## Джерело історичних фактів\n\n'+SOURCE_NOTE+'\n'
    assessment=''
    if c['control']:
        assessment='''## Межі контрольних доказів

Це авторський обмежений варіант до календарної теми, а не універсальний повний семестровий контроль.57 і116 мають фокус читання/мовний вжиток/коротке письмо;117 — слухання й говоріння в погоджених вікнах. Короткий45–65-слівний текст є одним зразком письма, не заміною повної підсумкової роботи за вимогами школи. Діагностики28/56/87/115 дають вибірку читання, мовного вжитку, слухання й письма; усна взаємодія всього класу потребує додаткових індивідуальних слотів. У5хв учитель реально перевіряє2–3дітей, а не всіх. Якщо потрібний повний письмовий обсяг програми більший — виділити окреме вікно і не підміняти його скороченим зразком.

Слухання — тільки за доступного аудіоканалу; спершу жодного transcript. Письмовий чат — письмова взаємодія, а не говоріння. Для всіх неперевірених видів запис «не перевірено», без нуля за недоступність. При перериванні зафіксувати валідні фрагменти й перенести решту на рівноцінні умови. Показ ключа або модель до самостійної відповіді означає тренування, а не незалежний доказ. B/D не є проведеним контролем.
'''
    lesson=f'''# 9клас · урок {n:03d} · {l['date']}

## План для адміністрації

**Тема календарного плану:** {l['topic']}

**Тип:** {KIND[l['kind']]}. **Джерельний запис:** {l['id']}. **Фокус:** {c['genre']}. **Одна основна секція:** {c['section']}; додаткові секції джерела — тематичні посилання, не обов’язкові додаткові тексти.

**Функція джерела:** {l['communicative_functions'].replace('y ','')}.

**Джерельний очікуваний доказ:** {l['expected_learning_evidence']}.

**Операційна мета цього варіанта:** опрацювати{len(c['questions'])}цільових пунктів і створити один продукт: {c['output']}

**Доказ:** відповіді+одне пояснення та один жанрово доречний артефакт. Це узгоджена вибірка цілі календарного уроку, не приписування всіх результатів після короткого сценарію.

**Компетентності:** іншомовна — точний зміст/адресат; критичне мислення — факт і висновок; навчання впродовж життя — виправлення з причиною; соціальна — право на доступний канал і ввічлива реакція. Матеріали: самодостатня роздатка, ручка, ключ тільки вчителю; електрика/мережа не потрібні для друкованого мінімуму.

{NUSH}

{RESULT_GROUPS}

## Опорний конспект

{c['rule']}

**Модель для вчителя (для контролю не демонструвати до першої спроби):**

{c['sample']}

**Вікова складність:** базовий доступ через короткий текст/чіткий контекст, рівень вимог визначає програма класу. Основний поступ — пояснення значення, перенос у новий контекст і точний жанр; не механічна заміна назви теми. Для сильніших — один контрприклад/альтернатива у резерві, без примусового додаткового есе.

## SEL і доступність

{SEL}

**Ціль і дія цього уроку:** {sp["domain"]}. {sp["action"]}

**Рефлексія і перенос:** {sp["prompt"]} У41–43вже наявного блоку; відповідь добровільна, можна подумати мовчки або пропустити. Не додавати час до45хв.

{assessment}
## Сценарій A — клас,45хв

{table(schedules_['A'])}
## Сценарій B — тихе укриття,15хв після переміщення

{SAFETY}

{table(schedules_['B'])}
## Сценарій C — дистанційно,45хв

Камера добровільна. Файл/чат/папір і відкладене фото доступні; без відповіді в чаті не роблять висновок про поведінку. Відсутній зв’язок означає домовленість про нове вікно.

{table(schedules_['C'])}
## Сценарій D — асинхронно,10–15хв

{table(schedules_['D'])}
## Переривання й повернення

Сигнал → зупинити навчання → діяти за безпековими правилами. Після дозволеного повернення0–2хв перевірити готовність без особистих історій;2–4хв відновити останній змістовий крок. Ці4хв беруться із залишку, а не додаються після дзвінка. Якщо лишилося менше10хв/немає умов, перенести. Report містить фактичні хвилини без переміщення, останній пункт і дату домовленого повернення. Неперевірені контрольні види не домислюються за наявністю інших робіт.

## Диференціація, оцінювання й ДЗ

З опорою: коротка картка B/D, один цільовий пункт/частина жанру; пояснення може бути українською, мовний приклад англійською. Основний: рівно визначений продукт, не всі резервні види. Розширення: додати новий контекст із поясненням; лише замість частини практики або пізніше. Критерії — в key.md. Окремі сирі бали не переводити автоматично в12-бальну шкалу. Письмо, читання, слухання, говоріння позначати окремо за фактичним способом перевірки.

ДЗ: до10хв — одне виправлення з причиною або завершення потрібної частини чернетки; після B/D не вимагати наздоганяння всього45-хв уроку. Термін — наступний доступний контакт за домовленістю. Відсутність електрики, камера й емоції не оцінюються.

Ігрові заміни: [games.md](games.md) — засвоєння16–24 та перевірка36–41, не додаткові13хв. Звіт: [report.md](report.md), лише фактичні дані.
'''
    key=f'''# Ключ і критерії ·9клас · урок {n:03d}

Тільки вчителю. Не друкувати з учнівською роздаткою. Фокус: **{c['genre']}**.

## Закриті цільові відповіді

{keys}
## Повний модельний продукт саме потрібного жанру

{c['sample']}

Це один прийнятний варіант, не єдиний. Оцінювати відповідність точному prompt: {c['output']}

**Критерії0–6:** зміст/необхідні частини жанру0–2; точність цільових форм/фактів0–2; зрозумілість і логічність0–2.0 — доказу немає;1 — частково або зі змістовою неточністю;2 — достатньо й зрозуміло. Для chart оцінюються рядки, для CV — рубрики та доказ навички, для survey — правильні чисельності/відсотки й межі узагальнення, для e-mail — адресат/повідомлення/закінчення. Не вимагати однакових двох причин і поради у всіх жанрах. Нецiльова помилка не штрафується вдруге за той самий зміст.

Для відкритого пояснення закритого пункту: приймати змістовно еквівалентну аргументацію українською або англійською. Для читання достатній точний переказ фрази-доказу. Закриті пункти: по1 за правильну відповідь, пояснення фіксується як окремий формувальний доказ. Показ ключа/рамки з готовою відповіддю до спроби позначається як робота з опорою.

## Мінімум B/D

Конкретний ключ / прийнятна модель: {minkey} Відкриті інші відповіді приймаються, якщо відповідають саме короткому завданню цієї дати й зберігають цільове значення/форму. Це тренувальний мінімум, не завершений контроль. Одна репліка/поле не отримує оцінку за весь жанр.
'''
    if n==117:key=key.replace('## Закриті цільові відповіді\n\n','')
    if audio:
        key+='\n## Текст слухання — тільки вчителю до завершення\n\n'+c['transcript']+'\n\nПрочитати двічі з20–30с паузою в межах08–16; повтор не супроводжувати transcript. Після завершення можна дати текст для аналізу помилок.\n\n'
        if c['type']=='assessment':key+='Слухання:1) fifteen minutes;2) the spelling and dates. По1балу. Це2факти короткого повідомлення, не доказ повного рівня слухання семестру.\n'
        else:key+='Відповіді до слухання — ті самі два цільові запитання картки, наведені у ключі вище. Учень не має transcript до відповіді; якщо читав — позначити як читання.\n'
    else:key+='\n## Інші види\n\nНа цьому уроці немає обов’язкового окремого тесту слухання. Говоріння засвідчується лише фактично прослуханою відповіддю; письмовий варіант не є усним доказом. Не приписувати весь спектр видів за одним артефактом.\n'
    key+='\n## SEL-рефлексія не оцінюється\n\nЗапитання про стратегію й перенос не має єдиної правильної відповіді. Не включати його у0–6,мовніMCQчи підсумковийбал. Пауза/мовчазнероздумування/пропуск не знижують результат.\n\n## Реальний облік\n\nУсні5хв — максимум2–3індивідуальні проби. Для решти індивідуальні слоти/асинхронний запис за доступності з оголошеною процедурою, інакше «не перевірено». Самодіалог/читання моделі не доводять спонтанної взаємодії. Сирі результати — профіль умінь, не автоматичний12-бальний підсумок. На117 письмових резервних MCQ немає; окремо збираються слухові та усні докази. Короткі контрольні зразки не підміняють обов’язковий повний обсяг програми.\n'
    if n in (76,77,84):key+='\nДжерело фактів: '+SOURCE_NOTE+'\n'
    report=f'''# Звіт фактичного проведення ·9клас ·{n:03d}

Планова дата: {l['date']}. Планова тема: {l['topic']}. Запис: {l['id']}.

Порожній шаблон; жодна планова дата не підтверджує проведення. Не додавати приватні посилання/коди журналу/психологічні оцінки.

- Фактична дата й доступний контакт: __________________
- A/B/C/D/поєднання; навчальні хвилини без переміщення: __________________
- Переривання/відновлення, нейтральна причина: __________________
- Умови B; останній завершений пункт: __________________
- Отриманий конкретний артефакт / вид / канал: __________________
- Читання / письмо: перевірено або не перевірено: __________________
- Слухання / говоріння: перевірено або не перевірено; які саме індивідуальні проби реально прослухано: __________________
- Самостійно / з опорою / після підказки: __________________
- Гра замістила який блок; мовний доказ: __________________
- Доступні альтернативи; SEL запропоновано/пропущено без оцінки емоцій: __________________
- Валідні фрагменти контролю / неперевірені частини / рівноцінне нове вікно: __________________
- Точний пункт повернення й наступний контакт: __________________
- Фактичне ДЗ та доступний термін: __________________
- Корекція наступного уроку: __________________

Учитель/дата заповнення: __________________
'''
    import re
    def readable(text):
        text = re.sub(r'(?<=[.!?])(?=\d{2}–\d{2})', ' ', text)
        return re.sub(r'(?<=[А-Яа-яІіЇїЄє])(?=[0-9])|(?<=[0-9])(?=[А-Яа-яІіЇїЄє])', ' ', text)
    for name,text in [('lesson.md',lesson),('handout.md',h),('key.md',key),('report.md',report),('games.md',games(c))]:(p/name).write_text(readable(text))
    review={'number':n,'date':l['date'],'topic':l['topic'],'type':c['type'],'focus':c['genre'],'source_section':c['section'],'main_passage_words':len(maintext.split()),'listening_transcript_words':len(c['transcript'].split()),'closed_items':answers,'main_question_count':0 if n==117 else len(answers),'product_prompt':c['output'],'model_product':c['sample'],'scheduled_main_passages':1,'production_minutes':12,'oral_individual_checks_per_5_minutes':'2–3; remainder separately','sel_nush_review':{'framework':'official Ukrainian electronic Zerna set; author adaptation for grade9','focus':sp['focus'],'domain':sp['domain'],'action':sp['action'],'reflection':sp['prompt'],'reflection_scored':False,'nush_cohort':'first standard NUSH grade9 graduation 2026/2027; school programme still requires verification'},'review_status':'reviewed_and_revised','review_basis':'source date/topic/function; curated task-key-language check; workload and genre check; not classroom piloted','source_sha256':{f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ['lesson.md','handout.md','key.md']}}
    return review


def main():
    reviews=[build(l) for l in DATA['lessons']]
    (DEST/'quality-review.json').write_text(json.dumps({'grade':9,'review_date':'2026-10-18','lessons':reviews},ensure_ascii=False,indent=2)+'\n')
    # Preserve public calendar metadata; all additions remain teacher-only source material.
    manifest={'grade':9,'academic_year':DATA['academic_year'],'source':'source-plan.json','lessons':[{'number':l['number'],'date':l['date'],'topic':l['topic'],'directory':f"{l['number']:03d}",'source_id':l['id'],'kind':l['kind'],'planned_only':True} for l in DATA['lessons']]}
    (DEST/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    readme='''# Матеріали вчителя ·9клас ·2026/2027

121календарний урок, збережені номери, дати й теми очищеного джерела. Другий семестр — планова проєкція, не факт проведення. Матеріали не додаються до UI каталогу; Git не є конфіденційним сховищем.

Кожна папка: lesson.md (план, опорний конспект, A45/B15/C45/D10–15), handout.md (повний основний маршрут і окремий самодостатній мінімум B/D), key.md (ключі, точні жанрові моделі, критерії), report.md (порожній звіт), games.md (дві ігрові симуляції із заміщенням основних блоків). PDF учню, вчителю та ігри формуються спільним інструментом; ключі не друкувати з роздаткою.

Методичний аудит змінив попередні універсальні вправи на цільові лексичні/граматичні/жанрові картки, звузив45-хв обсяг та розділив види контролю. [Огляд якості](QUALITY_REVIEW.md), [поурочний аудит](quality-review.json). Час — професійна оцінка дизайну, не замір у реальному класі. Короткі контрольні зразки не замінюють повний обсяг вимог школи; неперевірені усні види перевіряються окремими слотами.

Когорта9класу2026/2027відповідає першому випуску за Держстандартом НУШ; освітню програму конкретного закладу перевіряють окремо. SEL — авторське вікове адаптування окремих підходів електронного комплекту «Зерен» для1–6класів; не повний чи сертифікований курс. [Звірка СЕН/НУШ з першоджерелами](SEL_NUSH_REVIEW.md). Емоції, камера й особистість не оцінюються. Під час переміщення завдань немає, укриття — лише за дозволених умов.

Джерела: [очищений план](source-plan.json) з provenance і SHA-256; навчальні тексти9/lessons.json, авторські цільові вправи й жанрові brief. Біографічні факти76/77/84 додатково підтверджено NobelPrize.org. Повторне використання тексту має інший крок: перше читання фактів → повторне тлумачення/альтернатива. Це не лише зміна імені й дати.

Відтворення: `python3 scripts/build_teacher_grade9.py`; перевірка: `python3 tests/check_teacher_grade9_quality.py`. Вихідний локальний план не потрібний. PDF генеруються окремо після завершення MD.

| № | Планова дата | Тема | Файли |
|---|---|---|---|
'''
    for l in manifest['lessons']:
        d=l['directory'];readme+=f"|{l['number']}|{l['date']}|{l['topic']}|[План]({d}/lesson.md) ·[Роздатка]({d}/handout.md) ·[Ключ]({d}/key.md) ·[Звіт]({d}/report.md) ·[Ігри]({d}/games.md) ·[PDF учню]({d}/handout.pdf) ·[PDF учителю]({d}/teacher.pdf) ·[PDF ігри]({d}/games.pdf)|\n"
    (DEST/'README.md').write_text(readme)
    overview='''# Методична перевірка9класу

Фінальне уточнення:117не містить сирітських письмовихпунктів; game2має предметніодноріднідистрактори і новідеталі, Choicesчергуються; CVмодельрозділенона5абзаців.\n\nПеревірено дизайн усіх121дат: тему/функцію, мовну ціль, кожний закритий ключ, модель жанру, обсяг основної роботи, мінімум B/D та чесність контрольних доказів. Це змістовна ревізія генератора й кожного відтвореного комплекту; не результати апробації у класі. Поурочні рішення й хеші3основнихMD — quality-review.json.

## Знайдені дефекти та виправлення

-4/8/17/22/31/36/45/50/61/66/75/81/90/95/104/109: замість загальної граматики юніту —3контекстні лексичні вибори й новий приклад слововживання.
-6/9/20/23/34/37/48/51/64/67/78/79/82/93/96/107/110: контексти визначають конкретну форму;34 має4форми Passive.48/51/67 містять час і місце переповідання; безконтекстне механічне backshift більше не вимагається.78/79 пояснюють коми й обмеження that у non-defining.
-11/25/39/53/69/84/98/112: різні жанри замість однакового4–6-реченнєвого есе.39 дає20учасників і10/6/4=50/30/20%, обмежує узагальнення;69 має рубрики CV й доказ навички;84 має справжню3-рядкову хронологію, підтверджену NobelPrize.org;112 має greeting/body/closing і контрфактичне минуле.
-46/47: загальний текст про джерела в мережі не відповідав темі телепередач; замінено на fictionalTVsurvey й порівняння змісту програм.76/77: загальні винаходи замінено стислими підтвердженими фактами про MarieCurie;77 додатково розрізняє electric/electrical.
-57/116: прибрано4повні тексти+12граматичних пунктів; один короткий інтегрований текст,7пунктів і короткий письмовий зразок.117 має інший усний/слуховий фокус, а не дубль116. На117 письмові резервні MCQ прибрано: залишено чистий фокусL/S із самодостатніми аудіопитаннями.
-28/56/87/115: залишено обмежену діагностичну вибірку, а не обіцянку завершити всі види для всього класу за45хв. Усні докази —2–3індивідуальні проби в5хв та окремі наступні слоти; чат не усний доказ.
-7/21/35/49/65/80/94/108: transcript тільки вkey до завершення;7/21/35/49/65/80/108 мають нові предметні повідомлення проbeliefs,clothingrules,e-sports,vlogproduction,careers,prototype,route замість одного загального тексту юніту.52 — власнерадіоінтерв’ю. Діагностичнеаудіо має нові факти15хв/spelling+dates,відміннівідпрочитаноготексту.
-58/118/119/120/121: різні корекційні цілі портфоліо; fallback-пари дають змогу працювати без попереднього зошита.
-Усі121: один головний продукт,12хв на коротку практику; резерв не додається поверх45хв. B/D має окрему коротку картку без вимоги читати весь пакет. Гра1 заміщує16–24, гра2 —36–41; у контрольному варіанті підказка відділена від першого самостійного доказу.

## Повторна перевірка новизни раундів

У другому раунді1/10/24/43/44/59/60/62/63/68/73/74/83/88/89/91/92/94/97/102/103/105/106/111 були повтори вже тренованих фактів або їх перефразування. Перевірні картки замінено іншими деталями того самого джерела: запитання й минулі інтереси, колишній стиль/одноразові покупки, межі популярності, вимоги до професії, розділи CV, роль комп’ютерів, батарея, інша загроза середовищу, багаторазова пляшка, мовна функція та жанр e-mail. Перша спроба другого раунду більше не дублює ці попередні питання.

## Критерії й обмеження

Всі закриті відповіді звірено з текстом або явним граматичним/лексичним контекстом; правила для reported speech містять причину backshift. Моделі показують фактичний потрібний жанр. Навчальні завдання мають підтримуваний мінімум і складніше перенесення; цей матеріал не встановлює нормативний рівень класу. Повторення текстів з9/lessons.json є свідомим rereading з іншою когнітивною дією; нових121незалежних оригінальних текстів не заявляється.

Не проводилась реальна апробація таймінгу, індивідуальна діагностика дітей чи перевірка локальної програми школи.45–65слів контрольного письма — обмежений зразок, не еквівалент повної підсумкової роботи за будь-якою програмою. За потреби повного обсягу/аудіоканалу/усного контролю всіх учнів потрібні окремі вікна. B/D та камера не можуть створювати фіктивний підсумковий доказ.

## Покриття121дат

| № | Дата | Фокус | Пунктів основного маршруту | Рішення |
|---|---|---|---|---|
'''
    for r in reviews:overview+=f"|{r['number']}|{r['date']}|{r['focus']}|{r['main_question_count']}|ціль/ключ/жанр/обсяг переглянуто; [план]({r['number']:03d}/lesson.md)|\n"
    (DEST/'QUALITY_REVIEW.md').write_text(overview)

if __name__=='__main__': main()
