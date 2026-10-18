#!/usr/bin/env python3
"""Rebuild grade 9 teacher packs only from the sanitized source snapshot."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'teacher' / '9'
DATA = json.loads((DEST / 'source-plan.json').read_text())
SECTIONS = {s['id']: dict(s) for s in DATA['sections']}
# Starter focuses on learning strategies, not the media/personality defaults in the web catalogue.
SECTIONS['sb-starter']['vocabulary'] = [['practise', 'практикуватися'], ['improve', 'покращувати'], ['feedback', 'зворотний зв’язок'], ['phrase', 'фраза'], ['record', 'запис'], ['mistake', 'помилка'], ['goal', 'мета'], ['regularly', 'регулярно']]
SECTIONS['sb-starter']['questions'] = [
    {'prompt':'Emma wants ... her English.', 'choices':['improving','to improve','improved'], 'answer':1},
    {'prompt':'Dan suggests ... twice.', 'choices':['listening','to listen','listened'], 'answer':0},
    {'prompt':'A useful next step is to ... a record of phrases.', 'choices':['keeping','kept','keep'], 'answer':2},
    *SECTIONS['sb-starter']['questions'][3:],
]
ACTIVITY = {
'starter': ('a learning plan', 'practise in short sessions and check one mistake'),
'lead-in': ('a question board', 'ask two useful questions before choosing a task'),
'blog': ('a blog comment', 'refer to the writer’s idea before giving a different view'),
'vocabulary': ('a word card', 'group words by meaning and add a contextual example'),
'reading': ('a reading note', 'separate the writer’s fact from the reader’s opinion'),
'grammar': ('a grammar explanation', 'choose a form and explain how it changes the meaning'),
'listening': ('a listening note', 'listen first for the purpose and then for details'),
'vocabulary-2': ('a phrase collection', 'choose phrases that fit a particular situation'),
'grammar-2': ('a comparison of two forms', 'compare two versions and explain the difference'),
'speaking': ('a short dialogue', 'ask a question and react to the other speaker’s reason'),
'writing': ('a first draft', 'organise ideas and check the draft before sharing it'),
'look-back': ('a correction card', 'explain two corrections rather than copy an answer'),
'self-check': ('a self-check card', 'name one secure skill and one language question'),
}

TOPICS = {
0: ('learning English', 'practise, feedback, improve, record', 'I can practise for five minutes and keep a record.', 'a short learning plan'),
1: ('personality and interests', 'curious, confident, photography, personality', 'A person can be curious and helpful. Actions matter more than labels.', 'a fictional personal profile'),
2: ('clothes and choices', 'plain, striped, comfortable, quality', 'I enjoy wearing comfortable clothes. I decided to repair my jacket.', 'a reasoned outfit recommendation'),
3: ('youth clubs', 'volunteer, charity, teamwork, welcome', 'The event was organised by the club. Everyone should be welcomed.', 'an inclusive club invitation'),
4: ('media and sources', 'source, reliable, audience, review', 'She said that she would check the source before sharing the story.', 'a short media review with a source-checking step'),
5: ('jobs and skills', 'skills, qualities, training, responsible', 'She asked what skills he had. He said that he was interested in training.', 'a fictional job application'),
6: ('science and technology', 'device, invention, scientist, switch off', 'The device that I use saves time. My tablet, which is on the table, needs charging.', 'a description of an invented device'),
7: ('environmental choices', 'reuse, reduce, waste, refill station', 'If we reduce waste, we will help the environment. If I managed the school, I would add refill stations.', 'an environmental leaflet'),
8: ('travel and landmarks', 'landmark, route, public transport, museum', 'If we had checked the opening hours, we would have arrived earlier.', 'a fictional one-day travel plan'),
}
LISTEN = {
0: ('Alex will practise English on Tuesday. The plan takes ten minutes. Alex will write three useful phrases.', 'Tuesday', 'ten minutes'),
1: ('Alex is curious and enjoys photography. Alex joins a photo club on Tuesday. The club meets in the library.', 'Tuesday', 'the library'),
2: ('Alex chooses a plain shirt for a school event. The event is on Tuesday. Alex borrows the shirt from a cousin.', 'Tuesday', 'a cousin'),
3: ('Alex joins a volunteer club on Tuesday. The group meets in the library. Everyone can choose a small task.', 'Tuesday', 'the library'),
4: ('Alex prepares a school radio review on Tuesday. Alex checks two sources. The review is about a science programme.', 'Tuesday', 'two sources'),
5: ('Alex attends a careers meeting on Tuesday. The meeting is in the library. Alex wants to learn about training.', 'Tuesday', 'the library'),
6: ('Alex shows a new device on Tuesday. The device helps to sort books. Alex presents it in the library.', 'Tuesday', 'the library'),
7: ('Alex plans an Eco Day on Tuesday. The class will swap clothes indoors if it rains. Everyone can bring one item.', 'Tuesday', 'indoors'),
8: ('Alex plans a museum visit on Tuesday. The group will travel by bus. They will check the opening hours first.', 'Tuesday', 'by bus'),
}
KIND = {'book_lesson':'Практичний урок', 'unit_recap':'Повторення та самооцінювання', 'pair_diagnostic':'Діагностична робота за двома юнітами', 'semester_assessment':'Семестровий контроль', 'portfolio':'Портфоліо і корекція', 'grammar_workshop':'Граматична майстерня'}

def selected(l):
    ids = list(l['section_ids'])
    if l['kind'] == 'pair_diagnostic':
        ids = [f"sb-u{u}-self-check" for u in (max(1,l['unit']-1), l['unit'])]
    if not ids:
        u = l['unit'] or (4 if l['number'] < 59 else 8)
        ids = [f'sb-u{u}-self-check']
    return [SECTIONS[x] for x in ids if x in SECTIONS]

def task_questions(s,n,idx):
    out=[]
    for j,q in enumerate(s['questions']):
        # Rotation prevents a fixed answer-position pattern in the original web data.
        shift=(n+j+idx)%len(q['choices'])
        choices=q['choices'][shift:]+q['choices'][:shift]
        answer=(q['answer']-shift)%len(choices)
        out.append((q['prompt'], choices, answer, q['choices'][q['answer']]))
    return out

def mode_rows(rows):
    return '| Час | Репліка / дія вчителя | Дія учня та перевірний продукт |\n|---|---|---|\n'+'\n'.join('| '+' | '.join(r)+' |' for r in rows)+'\n'

def build(l):
    n=l['number']; slug=f'{n:03d}'; d=DEST/slug;d.mkdir(exist_ok=True)
    ss=selected(l);u=l['unit'] or (0 if n==1 else 4 if n<59 else 8)
    topic,vocab,model,product=TOPICS[u]
    title=f"9 клас · урок {n:03d} · {l['date']}\n{l['topic']}"
    control=l['kind'] in ('pair_diagnostic','semester_assessment')
    recap=l['kind']=='unit_recap'
    portfolio=l['kind']=='portfolio'
    listening=LISTEN[u]
    focus='; '.join(s['title_uk'] for s in ss)
    sections=', '.join(s['id'] for s in ss)
    source_out=l.get('expected_learning_evidence','').replace('\n',' ')
    source_fun=l.get('communicative_functions','').replace('y ','').replace('\n',' ')
    activity, strategy = ACTIVITY.get(ss[0].get('section',''), ACTIVITY['self-check'])
    person = ['Robin','Sam','Jess','Lee'][n % 4]
    minutes = 5 + n % 6
    micro = (f'{person} is working on {activity} about {topic}. The task is to {strategy}. '
             f'There are {minutes} minutes for a first attempt. A partner suggests making the message shorter, but {person} wants to keep one clear reason. '
             f'They agree to check the meaning before sharing the final version. The work is about a fictional character, so no private details are needed.')
    objective=f'Учень знаходить два факти у тексті про {topic}, розрізняє мовні форми у трьох контекстах та створює {product} (4–6 речень) із двома аргументами.'
    if portfolio: objective=f'Учень добирає два попередні артефакти про {topic}, пояснює дві виправлені помилки й пише один конкретний наступний навчальний крок; за відсутності артефактів створює їх на роздатці.'
    flow=('самостійно, без підказки ключа' if control else 'спочатку самостійно, потім звіряння з доказом у тексті')
    special=''
    if control:
        special='''### Особливості контролю

Повний варіант A/C збирає окремі докази читання, мовного вжитку, письма, слухання та взаємодії. Текст для слухання є тільки у ключі: учитель читає двічі, не надсилає його до завершення. У дистанційному форматі приватна аудіовідповідь/короткий аудіодзвінок за можливості — доказ говоріння; письмовий чат засвідчує письмову взаємодію. Якщо аудіоканал відсутній, слухання й говоріння позначити «не перевірено» та погодити окреме коротке вікно. Не виставляти комплексний бал за неперевірені види. Це авторський паралельний варіант, а не відтворення Test Book чи офіційна підсумкова форма. Критерії школи й програму уточнює вчитель. У B/D — лише тренувальні фрагменти; контроль переноситься, час не ущільнюється. Не трактувати відсутність зв'язку як відмову від навчання.
'''
    elif recap:
        special='''### Повторення

На початку учень обирає одну мовну форму, яку хоче уточнити. Вправа 2 → пояснення правила своїми словами → повторне виконання одного речення без зразка. Запис «було / стало / чому» є доказом поступу; цей урок не називається контролем.
'''
    elif portfolio:
        special='''### Портфоліо

Два попередні артефакти, якщо вони доступні: письмова робота та коротка взаємодія. За відсутності зошита взяти вправи 2 і 3 цієї роздатки. Для кожного записати «початковий варіант → виправлення → пояснення». Учитель дає одну конкретну рекомендацію. Немає вимоги друкувати особисті дані або оцінювати емоції.
'''
    elif l['kind']=='grammar_workshop':
        special='''### Граматична майстерня

Порівняти “The device that I use saves time” і “My tablet, which is on the table, needs charging”. Закреслити підрядну частину й перевірити, чи зрозуміло, який саме предмет мається на увазі. Показати роль ком у додатковій інформації. Додаткове завдання: описати два пристрої, один раз із необхідною, другий раз із додатковою інформацією.
'''
    core='Вправа 1: два факти з тексту; вправа 2: три мовні рішення; вправа 3: власний продукт. У кожній секції роздатки нумерація починається з 1.'
    artifact=('два виправлення «було → стало → причина» та наступний крок' if portfolio else 'індивідуальний текст 4–6 речень і відповіді до вправ 1–2')
    a=[('00–03','«Працюємо з вигаданими персонажами. Можна взяти паузу або відповісти письмово». Показати тему й мінімум.','Записує номер уроку; обирає зручний спосіб відповіді. Жодних обов’язкових особистих зізнань.'),
       ('03–07',f'«Read the model: {model}» Підкреслити форму й пояснити призначення.','Позначає у моделі два ключові слова; створює одну заміну.'),
       ('07–14',f'«Read section 1. Find evidence for both answers». Дати роздатку, стежити за доступністю.','Читає, виконує вправу 1 першої секції, підкреслює фразу-доказ.'),
       ('14–22',f'«Choose the form and explain one choice». Вправа 2 {flow}; якщо секцій кілька — розподілити час між ними.','Записує три відповіді на секцію; одне коротке пояснення правила.'),
       ('22–27','«Listen twice. First find the day, then the second detail». Прочитати текст ключа двічі; при неможливості аудіоканалу перенести слухання.','Дві відповіді у блоці «Слухання»; не підміняє слухання читанням.'),
       ('27–34',f'«Create {product}. Use two facts and give two reasons». Дати рамку з вправи 3.','Створює текст 4–6 речень; у контрольному варіанті працює самостійно.'),
       ('34–40','«Ask for one reason and respond politely». Пара по черзі виконує блок взаємодії; учитель слухає короткі репліки.','Запитання + відповідь + реакція. Якщо спілкування неможливе — письмовий діалог із позначенням способу.'),
       ('40–43',('Зібрати роботи без показу ключів; пояснити наступний зворотний зв’язок.' if control else 'Показати два приклади з ключа; «Correct one answer and explain why». Для портфоліо оформити два виправлення.'),artifact),
       ('43–45','«Write one next step. Keep this sheet». Пояснити ДЗ й точку відновлення.','Записує конкретний навчальний крок; здає/зберігає артефакт.')]
    b=[('00–02','Після завершеного переміщення й дозволу відповідальних оцінити умови. Показати мовчки картку: «Можна зробити лише мінімум або паузу».','Залишається на визначеному місці. Якщо немає світла/місця/безпеки для читання — навчання перенести.'),
       ('02–05',f'Мовчки вказати на модель і слова: {vocab}.','Читає модель, обводить два знайомі слова; без хорового повторення.'),
       ('05–09','Показати: «Перша секція, вправа 1: два факти. Підкресли доказ».','Виконує два запитання без розмов і пересування.'),
       ('09–13','Показати: «Вправа 3: два речення про героя і одну причину». Контроль не проводити.','Пише 2 речення й because; це мінімальна тренувальна версія.'),
       ('13–15','Позначити точку повернення: наступного разу вправа 2 і розширення тексту; не збирати аркуші через натовп.','Ставить закладку; зберігає папір. Повідомляти результат можна пізніше.')]
    c=[('00–04','Написати в чаті тему, номер, мінімум і час здавання. «Камера добровільна; можна чат, файл, фото після відновлення зв’язку».','Обирає канал; отримує роздатку. Відсутність реакції не доводить відсутності роботи.'),
       ('04–09',f'Надіслати коротку модель: «{model}». «Replace one detail».','Одна змінена модель у приватному чаті/на папері.'),
       ('09–17','«Read section 1. Send two answers with one quoted phrase». Дати час мовчки прочитати.','Індивідуальні відповіді вправи 1 з фразою-доказом; без обов’язкового ввімкнення камери.'),
       ('17–25','«Complete exercise 2; explain one answer». Для кількох секцій розділити 8 хвилин.','Три відповіді на секцію, пояснення в одному реченні.'),
       ('25–30','Прочитати текст ключа двічі через аудіоканал. За відсутності каналу призначити доступне пізніше вікно.','Два факти слухання. Без аудіоканалу позначка «не перевірено», не нуль.'),
       ('30–37',f'«Write {product}: 4–6 sentences, two reasons».','Вправа 3: власний текст, файл або фото аркуша, яке можна надіслати пізніше.'),
       ('37–42','«Ask one question, give a reason, react politely». Приватний чат/пара в чаті; за доступності коротке аудіо.','Три репліки. Чат = письмова взаємодія; для контролю говоріння потрібен окремий усний доказ.'),
       ('42–45','Назвати час доступного вікна для відкладеної здачі; залишити питання «Який наступний мовний крок?».','Здає індивідуальний артефакт або зберігає до відновлення зв’язку; одну помилку позначає для перевірки.')]
    dd=[('00–02','Попередньо надрукована інструкція: «Відкрий першу секцію. Прочитай тему і модель. Можна відкласти, якщо зараз немає умов».','Сам обирає доступний час; без екрана й без вимоги негайної здачі.'),
        ('02–06','На папері: «Прочитай текст. Дай дві відповіді вправи 1; підкресли доказ».','Два факти з опорою на текст.'),
        ('06–10',f'На папері: «Напиши два речення: {model} Зміни зміст для героя».','Короткий власний приклад із теми; мінімум завершений за 10 хвилин.'),
        ('10–13','За ресурсом: «Розв’яжи одне речення вправи 2 і поясни форму».','Одна відповідь із поясненням; факультативно.'),
        ('13–15','На папері: «Познач, де потрібне пояснення. Збережи аркуш до наступного доступного контакту».','Питання до вчителя й паперовий доказ. Не контроль, не оцінка слухання/говоріння.')]
    lesson=f'''# {title}

## План для адміністрації

- **Тип:** {KIND.get(l['kind'], l['kind'])}; базова тривалість 45 хв, альтернативи 15 і 10–15 хв — мінімальні фрагменти, не повний урок.
- **Джерельний запис:** {l['id']}; юніт {l['unit']}; SB {', '.join(map(str,l['sb_pages'])) or 'немає'}; WB {', '.join(map(str,l['wb_pages'])) or 'немає'}; тематичні секції: {sections}.
- **Конкретний фокус:** {focus}.
- **Мета й очікуваний доказ:** {objective}
- **Функція з календарного плану:** {source_fun}
- **Очікування джерела:** {source_out}
- **Компетентності:** іншомовне спілкування — розуміння змісту й аргументована репліка; навчання впродовж життя — пояснення виправлення; соціальна взаємодія — ввічлива незгода; критичне мислення — відокремлення факту тексту від власної поради. Мовна робота не є оцінкою особистості.
- **Матеріали:** handout.md/друкована роздатка, ручка; key.md тільки вчителю, годинник. Підручник і мережа не потрібні. Для слухання — живе читання вчителя за наявності належних умов.
- **Оцінювання:** вправи 1–2 по 1 балу за пункт, письмовий продукт 0–8 за рубрикою ключа; слухання 0–2 й взаємодія 0–6 окремо. Сирі результати не автоматично переводяться у 12-бальну оцінку. Учитель погоджує шкалу із програмою й локальними критеріями.

9 клас: компетентнісні підходи НУШ використано методично. Нормативну належність конкретного класу до програми/пілоту НУШ та критерії закладу слід уточнити; коди результатів не вигадуються.

## Опорний конспект

{''.join(f'### {i+1}. {s["title_uk"]}' + chr(10)*2 + s['rule'] + chr(10)*2 + '**Модель:** ' + s['example'] + chr(10)*2 for i,s in enumerate(ss))}

**Функціональна рамка:** “In the text, … . This shows … . I would suggest … because … .” Відрізняти «текст каже» від власного висновку.

**Мінімальний маршрут:** {core}

**Унікальна комунікативна ситуація дати:** {micro} Учень виконує блок «Окрема ситуація цього уроку», пояснює час і мету завдання, створює {activity}. Для письмового уроку це чернетка, для говоріння — репліки, для повторення — корекційна картка. У повному сценарії використати в блоці створення продукту, у B/D — як необов’язкове продовження.

## SEL: добровільна підтримка участі

Авторська мікропрактика у дусі соціально-емоційного навчання й «Зерен», не офіційна вправа програми. На вибір учень позначає «сам / з опорою / пізніше» без пояснення емоцій. Ситуація: вигаданий Alex не може відповісти одразу. Учні можуть написати одну ввічливу репліку: “Take your time. You can write your answer.” Або пропустити. Не оцінювати щирість, емоції, камеру, публічне саморозкриття чи згоду з учителем. Увага спрямована на повагу до черговості й доступний спосіб участі.

{special}
## Сценарій A — клас, 45 хв

{mode_rows(a)}
## Сценарій B — укриття, 15 хв після переміщення

Під час сигналу й переміщення мовні завдання зупиняються. Дії безпеки — за правилами закладу та вказівками відповідальних. Цей сценарій починається лише після дозволу й за достатнього освітлення, місця та стану дітей. Не проводити слухання, руханки, групове говоріння чи історії особистого досвіду небезпеки. Якщо умов немає, урок переноситься.

{mode_rows(b)}
## Сценарій C — дистанційно, 45 хв

{mode_rows(c)}
## Сценарій D — асинхронно без світла, 10–15 хв

Аркуш видати завчасно; якщо аркуша немає, передати після відновлення доступу. У темряві не вимагати читання чи письма. Таймер не обов’язковий: час орієнтовний, паузи дозволені.

{mode_rows(dd)}
## Переривання, повернення й чесний облік

1. На сигнал: «Зупиняємо урок. Далі — за правилами безпеки». Не давати навчальних завдань у дорозі.
2. Після дозволеного повернення: 0–2 хв перевірити готовність без особистих історій, 2–4 хв перечитати модель, далі від останнього завершеного пункту. Ці 4 хв входять у залишок часу, завдання скорочуються.
3. Якщо залишилося менш як 10 хв або немає умов, зберегти артефакт і перенести решту. У report.md записати фактичні хвилини, останній виконаний пункт та нову домовленість. Не позначати A виконаним після B/D.
4. Контроль, перерваний до отримання рівних умов і достатніх доказів, не вважати завершеним. Зберегти лише валідні фрагменти; неперевірені види позначити й призначити окремий рівноцінний варіант/вікно за правилами закладу. Оцінку за відсутність електрики не виставляти.

## Диференціація й ДЗ

- **З опорою:** перша секція, два факти, 2–3 речення за рамкою; можна словник цієї роздатки й відповідь на папері. Питання учень може сформулювати українською, мовний зразок — англійською.
- **Основний рівень:** усі секції вправ 1–2, один продукт 4–6 речень, дві причини, одна взаємодія.
- **Розширення:** порівняти два рішення щодо {topic}; 6–8 речень, аргумент на користь кожного, ввічлива незгода. Для контролю обсяг і дозволені опори оголосити до початку й застосувати однаково.
- **ДЗ без підручника:** на цьому ж аркуші виправити одну відповідь з поясненням та додати два речення до {product}. До 10 хв. Після B/D — завершити мінімум до наступного доступного контакту, а не наздоганяти весь 45-хв урок за вечір. Контроль не переноситься в неперевірену домашню роботу.
- **Звітність:** незаповнений шаблон report.md; планована дата не є свідченням фактичного проведення.
'''
    hand=f'''# Роздатка · 9 клас · урок {n:03d} · {l['date']}

**Тема:** {l['topic']}

Умовне ім’я/код учня: __________________ Дата фактичної роботи: __________

**Можна:** виконувати на папері, зробити паузу, працювати з вигаданим героєм. Особисті історії й камера не потрібні. Мова завдань не оцінює емоції. Під час переміщення до укриття не виконуй завдань. Читай і пиши лише коли є безпечні умови та достатнє світло.

**Швидкий маршрут без мережі (10 хв):** 2 хв — модель і слова; 4 хв — перша секція, вправа 1; 4 хв — два власні речення за моделлю. За ресурсом ще до 5 хв на одну відповідь вправи 2 й питання до вчителя. Решту виконаєш після домовленості.

'''
    key=f'# Ключ · урок {n:03d}\n\nНе друкувати разом з учнівською роздаткою.\n\n'
    points=0
    for idx,s in enumerate(ss):
        qs=task_questions(s,n,idx)
        words='; '.join(f'{a} — {b}' for a,b in s['vocabulary'][:8])
        hand+=f'''## Секція {idx+1}: {s['title_uk']}

**Слова:** {words}

**Опора:** {s['rule']}\n**Модель:** {s['example']}

### 1. Read and find evidence

{s['reading']}

'''
        key+=f'## Секція {idx+1}: {s["id"]}\n\n'
        for j in [3,4]:
            prompt,choices,ans,correct=qs[j]
            hand+=f'{j-2}. {prompt}\n\n'+' / '.join(f'{chr(65+k)}) {v}' for k,v in enumerate(choices))+'\n\nAnswer: ______ Evidence from the text: ______________________________\n\n'
            key+=f'- Вправа 1, пункт {j-2}: {chr(65+ans)}) {correct}. Доказ: учень підкреслює відповідну фразу наведеного тексту; допускається точний переказ.\n'
        hand+='### 2. Choose a form; explain one choice\n\n'
        for j in range(3):
            prompt,choices,ans,correct=qs[j]
            hand+=f'{j+1}. {prompt}\n\n'+' / '.join(f'{chr(65+k)}) {v}' for k,v in enumerate(choices))+'\n\nAnswer: ______\n\n'
            key+=f'- Вправа 2, пункт {j+1}: {chr(65+ans)}) {correct}.\n'
        hand+='One explanation (time, meaning or form): __________________________\n\n________________________________________________________________\n\n'
        points+=5
    hand+=f'''## Окрема ситуація цього уроку: {activity}

{micro}

A. How much time is available for a first attempt? ___________________

B. What will the partners check before sharing? _____________________

C. Complete the actual mini-product ({activity}) in two lines about {topic}. Include one clear reason. Use the language model above and the strategy from the message.

__________________________________________________________________

__________________________________________________________________

'''
    key+=f'\n## Окрема ситуація\n\nA: {minutes} minutes. B: the meaning. C: продукт {activity}; приймати 2 тематичні рядки з причиною і доречною мовною моделлю. A/B — по 1 балу, C — формувальний коментар; не подвоювати оцінку письма.\n'
    points+=2
    hand+=f'''## 3. Create and explain

Write {product} for a fictional Alex. Use two details from the text(s), give two reasons and add one suggestion. Write 4–6 sentences. You may use the model(s) above. Do not include real addresses, phone numbers or private experiences.

**Start:** In the text, … . Alex could … because … . Another reason is … . I suggest … .

1. ________________________________________________________________

2. ________________________________________________________________

3. ________________________________________________________________

4. ________________________________________________________________

5. ________________________________________________________________

6. ________________________________________________________________

## 4. Interaction

Fictional situation: Alex needs help choosing a next step about {topic}. Ask for one reason, reply and respond politely. Say it if the teacher has arranged an oral channel; otherwise write a dialogue and mark it as written.

A: Why would you choose ________________________________________?

B: I would choose __________________ because ____________________.

A: I see your point. Another option is ____________________________.

Спосіб: усно / письмово. Партнера немає? Напиши обидві ролі як тренування; усну взаємодію перевірять окремо.

## 5. Listening (only with the teacher's audio)

Do not guess if you cannot hear the audio. Write «не перевірено» and arrange another time.

1. On which day does Alex plan the activity? _______________________

2. {('How long does the plan take?' if u==0 else 'Where does the club meet?' if u in (1,3) else 'Who lends Alex the shirt?' if u==2 else 'How many sources does Alex check?' if u==4 else 'Where is the meeting?' if u==5 else 'Where does Alex present the device?' if u==6 else 'Where will the class swap clothes if it rains?' if u==7 else 'How will the group travel?')} ______________________

## 6. Correction / portfolio / homework

Original phrase: __________________________________________________

My corrected phrase and reason: ____________________________________

__________________________________________________________________

Second correction (for portfolio): _________________________________

My next language step: ____________________________________________

Add two sentences to your product, if this is homework: ______________

__________________________________________________________________

Optional respectful phrase for fictional Alex: ______________________

**ДЗ:** одна виправлена відповідь із поясненням і два додані речення, до 10 хв. Термін — наступний доступний контакт за домовленістю. Після короткого маршруту спочатку заверши мінімум.
'''
    advice, reason = {
        0: ('practise for five minutes each day', 'regular short practice is manageable'),
        1: ('describe a fictional person through helpful actions', 'actions give clearer evidence than labels'),
        2: ('compare comfort and quality before choosing an outfit', 'a useful outfit should suit the activity'),
        3: ('offer everyone a choice of a small club task', 'a clear role can help people join in'),
        4: ('check another source before sharing a media story', 'a claim needs supporting evidence'),
        5: ('compare the required skills before choosing training', 'training should match the tasks of the job'),
        6: ('describe what the device does before listing its features', 'the purpose explains why the invention is useful'),
        7: ('offer an indoor option for the Eco Day', 'the plan should still work if it rains'),
        8: ('check the route and opening hours before the visit', 'the group needs enough time for the museum and rest'),
    }[u]
    facts = '. '.join(ss[0]['reading'].split('. ')[:2]).rstrip('.') + '.'
    key+=f'''
## Відкрита відповідь: орієнтир, не єдиний правильний текст

{facts} I suggest that Alex should {advice} because {reason}. Another reason is that a specific next step is easier to explain and check. {ss[0]['example']}

Модель змісту: {product}, тема {topic}; учень має назвати дві конкретні деталі саме тексту секції, дві осмислені причини, одну пораду. Модель містить факти першої секції та авторську пропозицію; учень може обрати інші точні факти й власне обґрунтоване рішення. Текст, що суперечить джерелу, не отримує бал за відповідний факт. Приймати різні обґрунтовані рішення й нейтральних вигаданих персонажів.

Рубрика письма 0–8: зміст (2 факти + 2 причини + порада) 0–2; логічний зв'язок 0–2; доречна тематична лексика 0–2; граматична зрозумілість 0–2. Для кожного: 0 — доказу немає; 1 — частково/є помилки, які заважають; 2 — достатньо й зрозуміло. Помилка не знімається повторно за той самий критерій.

Взаємодія 0–6: 0–2 запитання за змістом; 0–2 відповідь із причиною; 0–2 доречна реакція. Приклад: “Why would you choose this option?” — “Because it matches the information in the text.” — “I see your point. We could also check another option.” Учитель перевіряє зміст конкретної репліки. Усний і письмовий спосіб фіксуються окремо; самодіалог — тренування, не доказ спонтанної усної взаємодії.

## Текст слухання: тільки вчителю

Прочитати у природному повільному темпі двічі з 20-секундною паузою всередині відведеного блоку. Без друкованої опори до завершення. Авторська мініситуація з вигаданим персонажем:

> {listening[0]}

Відповіді: 1) {listening[1]}; 2) {listening[2]}. По 1 балу, приймати семантично еквівалентні короткі відповіді. Якщо текст учень прочитав, це не доказ слухання. За відсутності аудіоканалу — «не перевірено».

## Облік результатів

Вправи 1–2 й два запитання окремої ситуації разом: 0–{points}; письмо: 0–8; слухання: 0–2; взаємодія: 0–6. Зберігати профіль окремих умінь, не підміняти усне письмою й не переводити механічно суму в оцінку. B/D — мінімальні тренувальні докази. Для семестрового контролю та діагностики вчитель перевіряє відповідність шкільній програмі й достатність видів діяльності. Недоступність, пауза, камера та емоції не оцінюються.

Для повторення/портфоліо: показати виправлення, назвати причину і застосувати форму в новому реченні. ДЗ приймати у вигляді паперу або відкладеного фото. Виправлений варіант і пояснення оцінювати за мовним змістом; навчальну рефлексію не прирівнювати до психологічної діагностики.
'''
    report=f'''# Фактичне проведення · 9 клас · урок {n:03d}

Планова дата: {l['date']}\nТема плану: {l['topic']}\nДжерельний запис: {l['id']}

Це порожній шаблон: жодне поле нижче не підтверджує факт проведення. Не вносити приватні посилання, коди журналу, контакти або психологічні характеристики дітей.

- Фактична дата / доступний контакт: __________________
- Сценарій A / B / C / D / поєднання: __________________
- Фактичні навчальні хвилини (без переміщення): _________
- Час переривання / відновлення, нейтральна причина: __________________
- Переміщення й навчання були розділені; умови для B: __________________
- Завершені секції/вправи/останній пункт: __________________
- Реально отримані докази читання / мовного вжитку: __________________
- Письмові артефакти й фактичний спосіб подання: __________________
- Слухання: перевірено / не перевірено; підстава: __________________
- Говоріння: перевірено / не перевірено; усний канал: __________________
- Взаємодія: усна / письмова / не перевірена: __________________
- Застосовані опори й доступні альтернативи: __________________
- Добровільний SEL-компонент запропоновано / пропущено: __________________
- Зворотний зв'язок про мову, без оцінки емоцій/камери: __________________
- Недопроведений контроль: валідні фрагменти / неперевірені види / нове рівноцінне вікно: __________________
- Точний пункт повернення й наступна дата/умови: __________________
- Фактичне ДЗ, обсяг, термін за доступністю: __________________
- Корекція наступного уроку: __________________

Учитель: __________________ Дата заповнення: __________________
'''
    for name,txt in [('lesson.md',lesson),('handout.md',hand),('key.md',key),('report.md',report)]:
        (d/name).write_text(txt)
    return {'number':n,'date':l['date'],'topic':l['topic'],'directory':slug,'source_id':l['id'],'kind':l['kind'],'section_ids':[s['id'] for s in ss],'planned_only':True}


def main():
    assert len(DATA['lessons'])==121
    manifest={'grade':9,'academic_year':DATA['academic_year'],'source':'source-plan.json','lessons':[build(l) for l in DATA['lessons']]}
    (DEST/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    readme='''# Службові матеріали вчителя: 9 клас, 2026/2027

121 календарний урок із загального плану, включно з повторенням, діагностикою, контролем і портфоліо. Пакети призначені вчителю й не додаються до інтерфейсу каталогу. Файли у Git-репозиторії не є конфіденційним сховищем.

Кожна папка містить lesson.md (адміністративний план, опорний конспект, сценарії A 45 / B 15 / C 45 / D 10–15 хв), handout.md (самодостатня паперова роздатка без ключів), key.md (відповіді й рубрики) і report.md (незаповнений звіт фактичного проведення). PDF-версії формуються спільним інструментом проєкту. Дати — планові; другий семестр у джерелі є проєкцією. Друкувати учням тільки handout, не key.

НУШ — методичний компетентнісний підхід; нормативну програму саме цього 9 класу має підтвердити заклад. SEL-підтримка добровільна, авторська, не офіційні вправи «Зерен». Емоції, камеру й особисті переживання не оцінюють. Під час переміщення навчання зупиняється, робота в укритті лише за дозволених умов. B/D не підміняють повного уроку чи контроль.

Джерело: [очищений план і тематичні тексти](source-plan.json); provenance містить вихідні шляхи й SHA-256. Включено лише дозволені навчальні поля, без Meet, ID журналів і даних календарних подій. Тексти та мовні завдання взято з тематичних адаптацій 9/lessons.json; додано авторські офлайн-інструкції, сценарії, слухання й рубрики. Це не офіційний пакет видавництва. Для повторного генерування: `python3 scripts/build_teacher_grade9.py` з кореня репозиторію; зовнішній локальний план більше не потрібен.

Для першого читання відкрийте lesson, для друку handout; key тримайте окремо. Усні види без аудіоканалу не зараховуються за письмовими відповідями, їх перевіряють пізніше. Кожний звіт заповнюється лише за фактичними доказами.

| № | Планова дата | Тема | Матеріали |
|---|---|---|---|
'''
    for l in manifest['lessons']:
        d=l['directory']
        readme+=f"| {l['number']} | {l['date']} | {l['topic']} | [План]({d}/lesson.md) · [Роздатка]({d}/handout.md) · [PDF учню]({d}/handout.pdf) · [PDF учителю]({d}/teacher.pdf) · [Ключ]({d}/key.md) · [Звіт]({d}/report.md) |\n"
    (DEST/'README.md').write_text(readme)

if __name__=='__main__': main()
