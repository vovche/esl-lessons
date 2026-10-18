#!/usr/bin/env python3
"""Rebuild every grade 6 teacher packet from the checked-in, sanitized source only."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'teacher/6'
SOURCE = BASE / 'source-plan.json'

SAFETY = '''Під час сигналу тривоги вчитель зупиняє навчання та діє за затвердженим шкільним алгоритмом. Під час переміщення немає читання, вправ, опитування чи фотографування робіт. Таймер навчання зупинено. B починається тільки після завершення переміщення, обліку дітей і дозволу відповідального дорослого та лише за прийнятних умов. Якщо шумно, тісно або немає ресурсу — навчання не проводиться. Пріоритет — безпека, доступ до дорослого й відпочинок. Жодних обов’язкових рухів, співу, аудіо чи розмов в укритті. Не використовувати реальний досвід небезпеки як матеріал для висловлення.'''
SEL = '''Авторська SEL мікропрактика, сумісна з принципами підтримки й добровільності; це не офіційна вправа програми «Зерна». Учитель: «Можна обрати: почати з одного слова, попросити зразок або пропустити перевірку стану. Розповідати про особисте не потрібно». Учень може мовчки позначити «готовий / потрібна пауза / пропускаю» на власному аркуші; показувати його не обов’язково. У завданнях можна завжди обирати вигаданого героя. Замість оцінювання емоцій учитель підтримує конкретну дію: «Ти знайшов доказ у тексті; це допомагає перевірити відповідь».'''

STARTERS = {
1: dict(code='hello-1',title='Countries and dates',vocabulary=[['Ukraine','Україна'],['Ukrainian','український'],['Poland','Польща'],['Polish','польський'],['Tuesday','вівторок'],['September','вересень']],rule='I am; he/she/it is; you/we/they are. Для запитання постав be перед підметом. Для заперечення додай not.',example='My name is Mia. I am Ukrainian. My birthday is in September. Are you Polish?',reading='Mia is twelve. She is from Ukraine. Her friend Leo is Polish. It is Tuesday today. Mia’s birthday is in September, and Leo’s birthday is in May.',questions=[{'prompt':'Mia ___ twelve.','choices':['is','are','am'],'answer':0,'why':'She/Mia + is.'},{'prompt':'___ Leo Polish?','choices':['Is','Are','Am'],'answer':0,'why':'Leo = he.'},{'prompt':'When is Mia’s birthday?','choices':['In September.','In May.','In March.'],'answer':0,'why':'Факт у тексті.'}],write={'prompt':'Напиши 4 речення про вигаданого учня: ім’я, вік, країна, місяць народження.','starter':'My name is… I am…'}),
2: dict(code='hello-2',title='Family, time and abilities',vocabulary=[['cousin','двоюрідний брат / сестра'],['sister','сестра'],['half past','половина після'],['quarter past','чверть після'],['swim','плавати'],['draw','малювати']],rule='Have got / has got: приналежність. Can + базова форма: вміння. Half past seven = 7:30; quarter past eight = 8:15.',example='I have got a sister. She can draw. We have breakfast at half past seven. Can you swim?',reading='Leo has got a sister, Eva. Eva can draw, but she cannot swim. Leo can swim. They have breakfast at half past seven. Their cousin visits them at quarter past eight.',questions=[{'prompt':'Eva ___ draw.','choices':['can','cans','has'],'answer':0,'why':'Can + базова форма.'},{'prompt':'Breakfast is at…','choices':['7:30.','8:15.','7:15.'],'answer':0,'why':'Half past seven.'},{'prompt':'Who can swim?','choices':['Leo.','Eva.','Nobody.'],'answer':0,'why':'Прямий факт у тексті.'}],write={'prompt':'Напиши 4 речення про вигадану сім’ю: родич, два вміння й час сніданку.','starter':'I have got… He/She can…'}),
3: dict(code='hello-3',title='Things and places',vocabulary=[['shelf','полиця'],['shelves','полиці'],['box','коробка'],['boxes','коробки'],['under','під'],['between','між']],rule='This/that + однина; these/those + множина. Box → boxes; shelf → shelves. How many + множина? In/on/under/next to показують місце.',example='There are two boxes under the desk. These books are on the shelf. How many books are there?',reading='There are two boxes under the desk. One bag is next to the desk. Three books are on the shelf. A pencil is between two pens. This is Leo’s desk.',questions=[{'prompt':'Two ___.','choices':['boxes','box','boxs'],'answer':0,'why':'Box + es.'},{'prompt':'Where are the boxes?','choices':['Under the desk.','On the shelf.','In the bag.'],'answer':0,'why':'Прямий факт.'},{'prompt':'How many books are there?','choices':['Three.','Two.','One.'],'answer':0,'why':'Three books.'}],write={'prompt':'Намалюй умовний стіл. Напиши 4 речення про предмети з in/on/under/next to і множиною.','starter':'There are… These…'})}

# Editorial samples are demonstrations, not the only correct personal responses.
SAMPLES = {
'1a':'Our school has a library. There is a music room. We study English and art. Lessons start at nine. We have music on Monday. My favourite subject is art.',
'1b':'Mia is tall. She has got curly hair. She is wearing a blue jacket. She is reading a book and drawing a map.',
'1c':'I usually wear jeans. I often wear trainers. I never wear a hat at school. Today I am wearing a skirt. I am wearing a blue shirt. I am carrying a red bag.',
'1d':'I enjoy reading. I love drawing. I like playing tennis. I cannot stand singing karaoke. I would like to try skating.',
'1e':'I am tall and I have got dark hair. I am quiet.\n\nMy imaginary friend Mia has got short hair. She is helpful. We play tennis together.',
'2a':'Last summer I visited a lake. I went there by bus. I took photos. I bought a postcard. I did not swim. I enjoyed the trip.',
'2b':'A bus is cheaper than a taxi. A taxi is faster than a bus. Both are comfortable. When I was five, I could ride a bike.',
'2c':'List: tickets, passport, weather forecast, bag. Did you book the tickets? Have you got your passport? What is the weather like? Did you pack your bag?',
'2d':'People used to travel by horse. They used to walk long distances. Ships used to be slow. Today people travel by train. They fly to other countries. They use fast buses.',
'2e':'Dear Sam, We went from school to a museum by bus and visited the art room. I liked the paintings because they were colourful. We wanted to see the garden, but it was closed. We were tired, so we went home. It was a great trip! Alex',
'3a':'Mia was reading in the garden. Leo was drawing. Eva was playing with a ball. The ball rolled under a bench. They found it and laughed.',
'3b':'We were walking near a house when we heard a noise. While I was looking at the door, Mia saw a shadow. We stopped. Something moved behind a box. It was a small cat. We smiled and went home.',
'3c':'There are some rides in our park. There are no long queues today. There is a small café. We went on a slow ride and saw the whole park. It was fun.',
'3d':'At first, Mia was worried because nobody was at the gate. Then someone waved to her. She felt happy. At the end, she found something funny in her bag and laughed.',
'3e':'Yesterday I was walking to the library. I felt excited. While I was looking at a map, my pencil fell. I felt worried when I could not find it. Suddenly a girl pointed to a bench. My pencil was under it. Luckily, I found it. I thanked her and went to the library.',
'4a':'Library — A: May I borrow this book? B: Yes, you may. Shop — A: Could you show me that bag? B: Of course. Post office — A: Can I buy a stamp, please? B: Certainly.',
'4b':'Map: School — Park — Library — Shop (one straight street). Go straight on from the school. Walk past the park. The library is next to the park and before the shop.',
'4c':'I would like to live in Green Town or Hill Village. The village is quieter than the town. The town is bigger than the village. The village is as beautiful as the town.',
'4d':'Fictional data: A — size 3, temperature 10, distance 5; B — size 5, temperature 20, distance 8; C — size 8, temperature 30, distance 12 (arbitrary units). C is the largest. A is the smallest. B is hotter than A. C is the hottest. C is the farthest from our star.',
'4e':'Green Town is a small fictional town. It is near a river.\n\nThere are two parks and a library. The library is next to the school.\n\nI like Green Town because it is quiet. The park is my favourite place.',
'5a':'I am going to read a book. I am going to clean my desk. I am going to buy a keyboard. I am meeting Mia at ten. I am not going to play computer games.',
'5b':'Phones will be smaller. Robots will help people. Batteries will last longer. Screens will use less energy. I will help you fix your computer.',
'5c':'We must keep the classroom tidy. We must not drop rubbish. We do not have to buy new folders. Yesterday we had to sort the paper.',
'5d':'If we keep the river clean, animals will have a safer home. If we plant trees, birds will have more places to live. If we save water, we will help nature. If we pick up litter, the park will be cleaner. If we protect forests, animals will have more space.',
'5e':'Hi Mia, Would you like to come to our school garden event? We are meeting at ten on Saturday. We are going to plant flowers. Please write back. Alex.\nReply 1: Thanks! I would love to come.\nReply 2: Thanks for inviting me. I cannot come on Saturday. Have a lovely day!',
'6a':'Lunch A has a few tomatoes and a little rice. There are not many carrots. There is not much juice. Lunch B has a lot of vegetables and a little bread.',
'6b':'A: I have got a headache. Can you help me? B: You should tell an adult. A: I feel tired. What should I do? B: You should ask an adult for help. A: I feel unwell. Can you stay with me? B: Yes. We should tell the teacher.',
'6c':'You like tennis, don’t you? Yes, I do. Mia enjoys skating, doesn’t she? Yes, she does. Leo can swim, can’t he? Yes, he can. You aren’t a football fan, are you? No, I’m not. They play hockey, don’t they? Yes, they do.',
'6d':'Our fictional team is Green Stars. They play football in Green Town. Last year they won a local cup. I support them because they help each other.',
'6e':'Dear Mia, I joined the art club last month. I go there twice a week. We draw animals. Next week I am going to paint a bird. Would you like to come? Alex',
'7a':'Have you ever watched a musical? Yes, I have. Have you ever played tennis? Yes, I have. Have you ever made a film? No, I haven’t. Have you ever visited a museum? Yes, I have. Have you ever won a prize? No, I haven’t.',
'7b':'I have listened to this band many times. I have never met the musicians. Last Saturday I watched their concert on TV. It was exciting.',
'7c':'Mia, I have borrowed your book. I have had it for two days. I will return it on Monday. Thanks! Alex.\nLeo, our meeting is now at four. I have been at the library since two. See you at the entrance. Mia',
'7d':'A: Can I help you? B: I would like a T-shirt. A: What size? B: Medium, please. This one is too small. A: Are these ones big enough? B: Yes. How much is the blue one? A: Ten pounds. B: I will pay in cash.',
'7e':'Mia has lost her notebook. It is hers. Her homework is in it. She feels worried. You should ask the teacher for help. You should explain what happened.',
'8a':'YOUNG ARTIST WINS A PRIZE. Mia is a student who loves painting. She won a prize for a picture which shows a beautiful garden. Her friends congratulated her.',
'8b':'A: I am nervous about the show. B: So am I. A: I have not performed here before. B: Neither have I. A: I like our song. B: So do I.',
'8c':'First we plan the magazine. Articles are written by students. Photos are taken by our art club. The pages are designed on a computer. We check every page. Then we share the magazine.',
'8d':'Our ceremony was held on Friday. The hall was decorated with paper stars. Three prizes were given. A short film was shown. All the helpers were thanked.',
'8e':'Garden Friends is a fictional comedy. It is about a boy who helps his neighbours. The film was made by a school club. The actors are friendly and funny. I liked the plot. I would recommend it to my classmates.',
'hello-1':'My name is Mia. I am twelve. I am from Ukraine. My birthday is in September.',
'hello-2':'I have got a sister. She can draw. She can sing. We have breakfast at half past seven.',
'hello-3':'There are two books on the desk. There is a bag under the desk. These pens are in a box. The box is next to a lamp.'}

def table(rows):
    return '| Час | Дії й репліка вчителя | Дії учня | Продукт / доказ |\n|---|---|---|---|\n' + '\n'.join('| '+' | '.join(str(x).replace('|',' / ').replace('\n',' ') for x in row)+' |' for row in rows)

def write(folder,name,content):
    (folder/name).write_text(content.rstrip()+'\n',encoding='utf-8')

def choose(l,ads):
    if l['number'] in STARTERS:
        return [STARTERS[l['number']]]
    ids=l['adaptation_ids']
    if l['lesson_type']=='integrated_skills' and l['section'].startswith('test-'):
        ids=['sb-'+str(l['module'])+'b','sb-'+str(l['module'])+'e']
    if not ids:
        ids=['sb-'+str(l.get('module') or 8)+'e']
    if l['section']=='error-analysis': ids=['sb-round-up-7','sb-round-up-8']
    if l['section']=='year-summary-1': ids=['sb-2e','sb-3e']
    if l['section']=='year-summary-2': ids=['sb-7d','sb-7e']
    # Long recap content is deliberately divided into two short independent tasks.
    return [ads[i] for i in ids if i in ads][:2]

def sample(a):
    if a['code'] in SAMPLES:return SAMPLES[a['code']]
    return a['example']

def block(a,idx,l):
    """A complete quiet worksheet. Deliberately use a short, explicit writing task."""
    label=f'Блок {idx}: {a["title"]}'
    vocab=a['vocabulary'][:8]
    lines=[f'## {label}','### 1. Словник і опора', '; '.join(f'{w} — {u}' for w,u in vocab),a['rule'],f'Мовна модель: {a["example"]}','### 2. Прочитай',a['reading'],'### 3. Обери відповідь. Запиши літеру та підкресли доказ / форму в тексті.']
    keys=[]
    for n,q in enumerate(a['questions'][:5],1):
        opts=list(enumerate(q['choices'])); offset=(l['number']+n)%len(opts); opts=opts[offset:]+opts[:offset]
        lines += [f'{n}. {q["prompt"]}', ' / '.join(f'{chr(65+j)}) {opt}' for j,(_,opt) in enumerate(opts)), 'Відповідь: __________ Доказ / пояснення: __________________________']
        letter=next(chr(65+j) for j,(original,opt) in enumerate(opts) if original==q['answer'])
        keys.append(f'{n}. **{letter} — {q["choices"][q["answer"]]}**. {q.get("why", "За текстом / моделлю.")}')
    # Use the actual subunit production task where a complete editorial sample exists.
    full_task=l['lesson_type'] in ('language_and_production','integrated_skills','year_summary') and a['code'] in SAMPLES
    short_task=f'Використай тему «{a["title"]}». Напиши 4 пов’язані речення (або 4 репліки діалогу): два за змістом тексту й два про вигаданого героя / власний варіант. Ужий щонайменше два слова зі словника та одну структуру з опори. Особисті дані не потрібні.'
    writing_task=(a['write']['prompt']+' Можна обрати вигаданих персонажів та обставини; особисті дані не потрібні.') if full_task else short_task
    lines += ['### 4. Мій короткий продукт',writing_task,f'Початок на вибір: {a["write"]["starter"]}', *['________________________________________________________________________']*6,'Перевірка: □ зміст зрозумілий □ два слова □ структура □ перевірив(ла) одне місце.','### 5. Взаємодія за бажанням у класі / онлайн',f'Учень A читає одне своє речення про «{a["title"]}». Учень B питає “Could you explain?” або “What about you?” A додає ще один факт. Зміна ролей. Можна записати репліки замість говоріння; це письмова взаємодія, не доказ усної.','A: __________________________ B: __________________________','A: __________________________ B: __________________________']
    # Provide sample satisfying precisely the four-sentence task.
    sentences=a['reading'].replace('!','.').replace('?','.').split('. ')
    facts='. '.join(sentences[:2]).rstrip('.')+'.'
    exemplar=sample(a) if full_task else facts+' '+a['example']
    return '\n\n'.join(lines), f'## {label}\n\n'+'\n\n'.join(keys)+f'\n\nВправа 4, можливий варіант (допускаються інші пов’язані речення): {exemplar}\n\nМодель додаткового висловлення: {sample(a)}\n\nВправа 5, зразок: A: {a["example"].split(". ")[0]}. B: Could you explain? A: {a["reading"].split(". ")[0]}. Відповідь може бути іншою, якщо зрозуміла й тематично доречна.'


def topic_sel(l):
    module=l.get('module',0)
    notes={
        0:'Знайомство: учень може обрати псевдонім і вигадану сім’ю, країну або дату; реальна адреса й родинні обставини не потрібні.',
        1:'Опис зовнішності й уподобань: тільки нейтральні характеристики вигаданого героя. Не оцінювати тіло, одяг або привабливість однокласників. У взаємодії тренувати “Could you repeat, please?” без висміювання помилок.',
        2:'Подорожі: не порівнювати можливості родин і не вимагати розповіді про реальні поїздки. Повністю вигадані канікули мають ту саму навчальну цінність.',
        3:'Пригоди та емоції: працювати з вигаданою короткою історією без подробиць травм. Не просити згадати особистий небезпечний досвід. Почуття персонажа можна назвати словом або пропустити.',
        4:'Місця й маршрути: використовувати умовну карту; не запитувати домашню адресу або реальний маршрут дитини. Прохання повторити є навчальною стратегією, не помилкою.',
        5:'Екологія й технології: не оцінювати наявність гаджетів удома та фінансові можливості; вигаданий пристрій / подія допустимі. Обов’язок і заборону розглядати на нейтральних прикладах.',
        6:'Здоров’я й харчування: описувати тільки вигадані меню та персонажів; не збирати відомості про діагнози, вагу або харчування дітей. Не порівнювати тіла. Порада в мовній вправі — звернутися до дорослого; лікування і ліки не призначати.',
        7:'Досвід, покупки й труднощі: вигадана роль дозволяє не розкривати сімейних грошей, стосунків або переживань. Відповідь партнеру має бути доброзичливою; не вимагати публічної відвертості.',
        8:'Слава й виступ: не порівнювати популярність дітей; роль у вигаданому проєкті доступна без виступу перед класом. Для невпевненого учня почати з одного речення, а не примусу.'}
    return notes.get(module,notes[8])


def lesson_regular(l,aa):
    n=l['number']; title=l['topic']; typ=l['lesson_type']; primary=aa[0]; ptitle=primary['title']; blocks=' та '.join(f'{i+1} ({a["title"]})' for i,a in enumerate(aa))
    reception=typ in ('reception','starter','culture_clil_song','module_intro')
    repeat=typ in ('unit_recap','reflection')
    phase={'reception':'введення й розуміння тексту','language_and_production':'мовні структури та перенесення у висловлення','unit_recap':'повторення й самооцінювання','integrated_skills':'інтегрована практика й корекція','culture_clil_song':'культурна / міжпредметна текстова практика','starter':'актуалізація базових умінь','module_intro':'лексичний вступ','reflection':'аналіз і виправлення','portfolio':'добір, редагування та презентація','year_summary':'підсумкова мовленнєва практика'}.get(typ,typ)
    hand=[]; key=[]
    for i,a in enumerate(aa,1):
        h,k=block(a,i,l); hand.append(h);key.append(k)
    special=''
    if typ=='portfolio':
        special='''## Портфоліо — окремий результат уроку

Можна взяти власну попередню роботу або створити нову за текстом цього аркуша. Не потрібно розкривати особисті дані. Обери 2 зразки: речення й короткий діалог. Поруч запиши «До» та «Після» для однієї правки. Додай пояснення «I changed… because…» і наступний крок «Next time I will…». Представити можна тихо письмово; усна презентація добровільна.

Зразок 1: _______________________________________________________

Зразок 2: _______________________________________________________

До: ________________________ Після: ___________________________

Причина / наступний крок: ______________________________________
'''
    elif typ=='reflection':
        special='''## Майстерня корекції — окремий результат уроку

Виправ 4 навчальні речення вигаданого учня: 1. She have never watched a musical. 2. This shoes are too small. 3. The articles is written by students. 4. Yesterday two prizes are given. Поясни одну правку й напиши власне правильне речення.

1. __________________________ 2. _______________________________

3. __________________________ 4. _______________________________

Причина й новий приклад: _______________________________________
'''
        key.append('## Майстерня корекції\n\n1. She has never watched a musical. 2. These shoes are too small. 3. The articles are written by students. 4. Yesterday two prizes were given. Зразок причини: articles — множина, тому are; власний приклад: The photos are taken by our club.')
    if special: hand.insert(0,special)
    stage2='Спочатку без опори обери відповідь; потім перевір моделлю й виправ іншим знаком.' if repeat else ('Прочитай текст мовчки. Підкресли два слова й знайди головну думку.' if reception else 'Знайди в тексті модель і зміни два слова, зберігаючи структуру.')
    stage3='Зроби майстерню корекції / відбір зразків; запиши причину правки.' if typ in ('reflection','portfolio') else ('Виконай вправу 3: біля кожної відповіді познач доказ.' if reception else 'Напиши вправу 4 і розіграй / запиши взаємодію 5.')
    objective=f'Розуміти короткий текст «{ptitle}», знайти 2 підтвердження, застосувати цільову модель у власному короткому продукті.'
    if repeat: objective=f'Відновити матеріал «{ptitle}», пояснити одну мовну правку та обрати наступний крок.'
    if typ=='portfolio':objective='Дібрати два зразки, внести обґрунтовану правку й описати поступ без порівняння дітей між собою.'
    arows=[('00–03','«Можна почати з одного слова або взяти паузу». Пропонує добровільну SEL перевірку.','Обирає спосіб участі.','Приватний вибір; не оцінюється.'),('03–07',f'«Тема: {title}. Наприкінці покажемо два докази й короткий продукт». Називає критерії.','Відзначає знайомі слова блоку 1.','2 позначені слова.'),('07–12',f'Показує словник і читає модель: «{primary["example"]}». Просить порівняти форми.','Читає / слухає в класі за можливості; знаходить структуру.','1 виділена структура.'),('12–20',f'Дає блоки {blocks}. «{stage2}»','Читає текст; ставить ? біля незрозумілого.','Два підкреслення / чернетка.'),('20–28',f'«{stage3}»; допомагає точковим запитанням «Where is your evidence?»','Працює індивідуально; пояснює одну дію.','Вправа 3 або чернетка 4; спеціальний продукт.'),('28–37',f'«Заверши вправу 4 за темою {ptitle}; потім обміняйся репліками 5 за бажанням».','Створює продукт вправи 4 у вказаному обсязі; співрозмовник реагує.','Короткий текст; усний доказ лише за фактичного говоріння.'),('37–42','Показує ключ тільки після спроби; «Знайди одну правку й поясни її».','Самоперевірка й редагування.','Одна видима правка.'),('42–45','«Покажи два слова й одну структуру, які вже можеш використати». Пояснює ДЗ.','Позначає наступний крок; здає доступний продукт.','Вихідний квиток / позначка відсутності доказу.')]
    brows=[('00–02','Після дозволу пропонує мовчазний вибір: аркуш чи пауза.','Обирає без пояснення.','Жодної оцінки стану.'),('02–05',f'Показує на аркуші модель «{primary["example"]}». Не перекрикує шум.','Мовчки знаходить 2 слова у блоці 1.','2 позначки.'),('05–10',f'Вказує: блок 1 «{ptitle}», текст і тільки вправу 3 №1–2.','Читає доступну частину, обирає дві відповіді.','До 2 відповідей.'),('10–13','Вказує на вправу 4: «Одне речення достатньо».','Пише одне тематичне речення або обирає паузу.','0–1 речення; не контрольна оцінка.'),('13–15','Позначає місце зупинки; організовує збереження аркуша без фото.','Зберігає роботу; за бажанням позначає ?.','Точка повернення: блок 1, вправа 3 №3.')]
    crows=[('00–04','Надсилає / завчасно видає аркуш. «Камера необов’язкова; можна відповідати цифрою в чаті або на папері».','Позначає доступність через чат, реакцію або пізніший зв’язок.','Канал доступу; мовчання не доказ відмови.'),('04–09',f'«Тема {title}. Прочитайте модель блоку 1». Дає письмову інструкцію.','Відмічає 2 слова.','2 слова на папері / в чаті.'),('09–16',f'Пише «{stage2}» й показує структуру у словнику.','Читає без увімкнення камери / мікрофона.','Два докази в тексті.'),('16–25',f'Дає вправу 3 у блоках {blocks}. У чат — номер+літера; публічно не ранжує.','Відповідає в чаті або на аркуші.','До 5 відповідей на блок.'),('25–35',f'Дає вправу 4 за темою {ptitle}; для портфоліо / корекції — спеціальне завдання.','Створює текст; надсилає 1–2 речення або зберігає папір.','Продукт вправи 4 / спеціальний продукт.'),('35–41','Дає вправу 5; приватний голос лише за згодою або письмова взаємодія.','Реагує на партнера; редагує одну репліку.','Дві взаємопов’язані репліки; тип доказу за фактом.'),('41–45','Дає ключ після спроби, ДЗ і маршрут повернення для тих, хто зник зі зв’язку.','Виправляє один пункт; позначає завершене.','Правка; точка наступного входу.')]
    drows=[('00–02',f'Завчасна друкована інструкція: «Візьми тільки блок 1 {ptitle}; інтернет і підручник не потрібні».','Читає словник і модель, якщо є безпечні умови та освітлення.','Обрано 2 слова.'),('02–06','На аркуші: прочитай текст; підкресли 2 факти.','Читає у власному темпі.','Два підкреслення.'),('06–10','На аркуші: зроби вправу 3 №1–2; без таймера й поспіху.','Записує дві відповіді.','Дві літери.'),('10–13','На аркуші: напиши 1–2 речення вправи 4; якщо ресурсу немає — зупинись.','Пише короткий продукт.','1–2 речення.'),('13–15','На аркуші: постав ? біля труднощів; принеси аркуш за наступної можливості.','Зберігає роботу; нічого не надсилає під час відключення.','Аркуш для наступного контакту.')]
    script=f'''# Урок {n:03d}. {title}

Планова дата: **{l['date']}**. 6 клас; {l['semester']} семестр; тривалість A/C — 45 хв, B — до 15 хв після завершення переміщення, D — 10–15 хв у власному темпі. Статус: план, а не запис фактично проведеного заняття.

## План для адміністрації

Тип: {phase}. Розділ: {l.get('module_title','')}; календарна секція: {l['section']}. Орієнтир підручника: {', '.join(map(str,l.get('sb_pages',[]))) or 'узагальнення календарного матеріалу'} (друковані сторінки; для виконання пакета підручник не потрібен).

Мета: {objective}

Очікувані докази: дві обґрунтовані відповіді до тексту; тематичний продукт в обсязі, зазначеному у вправі 4; одна виправлена помилка. У короткому режимі фіксувати тільки наявні докази. Це робочі критерії вчителя, без вигаданих нормативних кодів. Компетентності НУШ: іншомовна комунікація через розуміння та власне повідомлення; навчання впродовж життя через самоперевірку; соціальна компетентність через добровільну взаємодію й повагу до вибору; культурна обізнаність через аналіз змісту без стереотипів.

Оснащення: роздруковані handout.md / handout.pdf, олівець, ключ лише в учителя. Цифрова сторінка не потрібна. Пакет — авторська адаптація на основі календаря й локальних матеріалів, без копій сканів і без вимоги прослуховувати зовнішній запис. На уроках із позначкою song працюємо з текстовим змістом; аудіювання пісні не вважаємо проведеним.

## Опорний конспект і репліки

'''+ '\n\n'.join(f'**{a["title"]}.** {a["rule"]}\n\nЗразок: {a["example"]}\n\nУчитель: “Read the model. Find two useful words. What is your evidence?” Після відповіді: “Thank you. Check the form in the model.” Учень може показати рядок замість відповіді вголос.' for a in aa)+f'''

## SEL та безпечна організація

{SEL}

{topic_sel(l)}

{SAFETY}

## A — клас, 45 хвилин

{table(arows)}

## B — дозволене тихе заняття в укритті, до 15 хвилин

{table(brows)}

## C — дистанційно, 45 хвилин

{table(crows)}

## D — асинхронно, 10–15 хвилин, без електрики та інтернету

{table(drows)}

## Переривання, повернення й перенесення

Поставити позначку останньої завершеної вправи, якщо це не затримує безпечні дії. Після відновлення: 2 хв на доступ до аркуша та добровільну паузу, 3 хв на відновлення моделі «{primary['example']}», потім наступний незавершений пункт вправи 3. Не починати все знову. Якщо часу менш як 8 хв або умов немає — перенести вправу 4 / другий блок на наступний контакт і внести це у report.md. Скорочення не компенсувати подвійним ДЗ. Після B/D повний продукт і взаємодію перевірити на наступному доступному уроці; непоказане вміння не оцінювати як нуль.

## Диференціація й оцінювання

Підтримка: тільки блок 1, словник відкритий, 2 закриті відповіді та 1 речення за моделлю; інструкція українською; можна диктувати дорослому за звичайних умов, зазначивши допомогу. Базово: 5 відповідей і повний продукт вправи 4 у вказаному там обсязі. Розширення: другий блок, пояснення вибору форми й додаткове запитання партнеру. Швидкість, камера, охайність та особисті переживання не є критеріями мовного досягнення. Рубрика відкритої роботи — у key.md. Усну навичку фіксуємо лише за усним доказом; письмова заміна є способом участі.

## Домашня робота, до 10 хвилин

Відредагувати одне речення вправи 4 блоку 1 «{ptitle}» і дописати до 4 речень за моделлю. Після B/D — завершити лише два початі пункти й 1–2 речення; нової додаткової вправи немає. Якщо немає світла / ресурсу, виконати після відновлення або під час наступного контакту без штрафу за технічну затримку.
'''
    return script,'\n\n'.join(hand),'\n\n'.join(key)

ASSESSMENTS={
1:{'setting':'A school trip','listen':'Our school trip is on Friday. We are going to the history museum by bus. We meet at school at nine. Bring a notebook. The ticket is four pounds. We return at three.', 'lq':[('Which day is the trip?',['Friday','Monday','Sunday'],0),('How do the students travel?',['By bus','By train','On foot'],0),('When do they return?',['At three','At nine','At four'],0)], 'read':'On Saturday, Mia visited a small town with Leo. They travelled by train. First they went to a bookshop. Then they had lunch in a park. Mia wanted to visit a museum, but it was closed. She bought a postcard for her cousin. They enjoyed the quiet streets.', 'rq':[('How did Mia and Leo travel?',['By train','By bus','By boat'],0),('Why did they not visit the museum?',['It was closed','They were late','It was too expensive'],0),('Who was the postcard for?',['Mia’s cousin','Leo’s teacher','Mia’s neighbour'],0)],'speaking':'Ви з партнером плануєте шкільну екскурсію. A пропонує музей о 10:00 і автобус. B може лише після 11:00 та пропонує парк. Запитайте про час / місце, узгодьте один план; кожен має зробити 3–4 репліки й відповісти на пропозицію.','writing':'Напиши 5–6 речень другові про вигадану подорож у минулому: куди, транспорт, дві події, враження; додай because або so.','wsample':'Dear Mia, Last Saturday I visited Green Town. I went there by bus. I visited a library and had lunch in a park. The museum was closed, so I bought a postcard. I enjoyed the trip because the town was quiet. Alex', 'ssample':'A: Would you like to visit the museum at ten? B: I can only come after eleven. What about the park? A: Good idea. How can we get there? B: We can go by bus. A: Let’s meet at school at eleven. B: Great, see you there.'},
2:{'setting':'A town story','listen':'Leo was reading in the library when Mia arrived. It was half past four. Mia wanted a book about planets. The librarian showed her a blue book. They sat near the window. Leo left at five.', 'lq':[('Where was Leo?',['In the library','At the bank','In a shop'],0),('What book did Mia want?',['A book about planets','A book about cooking','A book about football'],0),('When did Leo leave?',['At five','At half past four','At six'],0)],'read':'Green Town has a library, a park and a small market. The library is opposite the park. On Monday, Eva was walking to the library when she found a green notebook. She gave it to the librarian. Later a boy came to ask for it. He thanked Eva. It was the happiest moment of her day.', 'rq':[('Where is the library?',['Opposite the park','Behind the market','Next to a lake'],0),('What did Eva find?',['A green notebook','A blue book','A bag'],0),('Who received the notebook from Eva?',['The librarian','A bus driver','A shop assistant'],0)],'speaking':'A — відвідувач міста, шукає бібліотеку. B — місцевий житель: від школи прямо, парк ліворуч, бібліотека навпроти парку. A питає шлях, уточнює одне місце й дякує; B пояснює та перевіряє розуміння. По 3–4 репліки.','writing':'Напиши 5–6 речень про безпечну вигадану пригоду в місті. Назви двох героїв, що вони робили, що сталося й чим завершилося; використай when або while.','wsample':'Mia and Leo were walking in Green Town. They were looking for the library. While they were reading a map, a girl came to help. She showed them the library opposite the park. They thanked her. They found an interesting book and went home.', 'ssample':'A: Excuse me, how do I get to the library? B: Go straight on from the school. A: Is it next to the park? B: It is opposite the park, on your right. Is that clear? A: Yes, opposite the park. Thank you. B: You’re welcome.'},
3:{'setting':'A school garden event','listen':'Our garden event is on Sunday. We are meeting at ten near the school gate. We are going to plant flowers. You must bring water, but you do not have to buy gloves. The school has gloves for everyone. We finish at twelve.', 'lq':[('When is the event?',['Sunday','Saturday','Friday'],0),('What will students plant?',['Flowers','Trees','Vegetables'],0),('What must students bring?',['Water','New gloves','A camera'],0)], 'read':'Mia joined a tennis club last month. She practises twice a week. Her coach says that everyone should take a water bottle. Last Saturday the group played a friendly match. Mia did not win, but she enjoyed helping a new player. Next month she is going to try a different sport with her cousin.', 'rq':[('How often does Mia practise?',['Twice a week','Every day','Once a month'],0),('What should players take?',['A water bottle','A new racket','A camera'],0),('What did Mia enjoy?',['Helping a new player','Winning a prize','Buying a bottle'],0)],'speaking':'A запрошує B на екоподію в неділю о 10:00. B має заняття до 11:00. Запитайте про час, заняття й потрібні речі; узгодьте інший час або ввічливо відмовте. По 3–4 репліки.','writing':'Напиши 5–6 речень із запрошенням на вигадану екоподію: де, коли, два плани, одне правило та причина долучитися.','wsample':'Hi Mia, Would you like to come to our garden event? We are meeting at school at ten on Sunday. We are going to plant flowers and clean the paths. You must bring water. If we help together, our garden will be cleaner. Please write back. Alex','ssample':'A: Would you like to join our garden event on Sunday? B: What time does it start? A: At ten. We are going to plant flowers. B: I have a class until eleven. Can I come later? A: Yes. Please bring water. B: Great, I will come at eleven.'},
4:{'setting':'A school film club','listen':'Our film club has made a short comedy. The film was written by Mia and directed by Leo. It was filmed in the school garden. We are showing it on Wednesday at four. Tickets are free. You can bring a friend.', 'lq':[('Who directed the film?',['Leo','Mia','Eva'],0),('Where was it filmed?',['In the school garden','In a shop','In a museum'],0),('When is the show?',['Wednesday at four','Friday at five','Monday at three'],0)], 'read':'The Green Stars are a fictional school band. They have played together for two years. Last week they performed in the town library. Their new song was written by Eva. The audience liked the quiet music. A school magazine published an interview with the band. Next month the students are going to make a short music video.', 'rq':[('How long have they played together?',['For two years','Since last week','For two months'],0),('Where did they perform last week?',['In the town library','At a stadium','In a shop'],0),('Who wrote the new song?',['Eva','The librarian','A reporter'],0)],'speaking':'A — покупець, хоче синю футболку для виступу, розмір M, має 12 фунтів. B — продавець: синя M коштує 10 фунтів, зелена S — 8. Попросіть товар, уточніть розмір / ціну, відреагуйте на too small / big enough і завершіть покупку. По 3–4 репліки.','writing':'Напиши 5–6 речень про вигаданий шкільний фільм: назва, автор / режисер, зміст, що сподобалося й рекомендація. Ужий who або which і одну пасивну конструкцію.','wsample':'Garden Friends is a fictional comedy. It was directed by Mia. It is about a boy who helps his neighbours. The story is funny and kind. I liked the costumes. I would recommend it to my classmates.','ssample':'A: I would like a blue T-shirt, please. B: What size do you need? A: Medium. This green one is too small. B: The blue one is medium and costs ten pounds. A: That is big enough. I will take it. B: Thank you. Here you are.'}}


def assessment(l):
    n=l['number']; diag=l['lesson_type']=='pair_diagnostic'
    group={28:1,53:2,86:3,115:4}.get(n,2 if l['semester']==1 else 4); data=ASSESSMENTS[group]
    skills=['L','R','S','W'] if diag else [l['section'].split('-')[-1]]
    hand=[f'# Завдання: {data["setting"]}', 'Це запропонований матеріал перевірки, а не підтвердження її проведення. Працюй самостійно; перед початком учитель пояснить критерії. Якщо зв’язок зник або пролунала тривога, зупинись. Відсутній доказ перевірять іншого безпечного разу.']
    keys=[]
    for skill in skills:
        if skill in ('L','R'):
            hand += ['## '+('L — розуміння на слух' if skill=='L' else 'R — розуміння прочитаного')]
            if skill=='R': hand += [data['read']]
            else: hand += ['Прочитай запитання. Прослухай учителя двічі у звичайних безпечних умовах. Не потрібно повторювати вголос. Текст слухання міститься тільки в учительському ключі. Якщо не чути, повідом доступним способом; читання тексту не замінює перевірку слухання.']
            for i,(q,opts,ans) in enumerate(data['lq' if skill=='L' else 'rq'],1):
                offset=(n+i)%len(opts); reordered=list(enumerate(opts))[offset:]+list(enumerate(opts))[:offset]
                hand += [f'{i}. {q}', ' / '.join(f'{chr(65+j)}) {o}' for j,(_,o) in enumerate(reordered)), 'Відповідь: __________']
                letter=next(chr(65+j) for j,(k,o) in enumerate(reordered) if k==ans)
                keys += [f'{skill}{i}. {letter} — {opts[ans]}.']
        else:
            hand += ['## '+('S — усна взаємодія' if skill=='S' else 'W — письмове висловлення'),data['speaking' if skill=='S' else 'writing']]
            if skill=='S':hand += ['Можна взяти 2 хвилини на план і 3 ключові слова. У звичайних умовах говоріть 2–3 хв на пару; партнером може бути вчитель. Письмові репліки доступні як підготовка, але не є завершеним усним контролем.']
            hand += ['________________________________________________________________________']*8
            keys += [f'## {skill}: можливий зразок\n\n'+data['ssample' if skill=='S' else 'wsample']]
    keys.insert(0,'## Текст учителя для слухання — не друкувати учням\n\n'+data['listen']+'\n\nЧитати двічі чітко, без зайвих підказок; між читаннями пауза близько 30 секунд. На контрольних не показувати текст на екрані. Після переривання початий стимул не оцінювати автоматично: провести еквівалентну перевірку за погодженим графіком.')
    if diag:
        activities=[('00–04','Пояснює 4 окремі докази та критерії; добровільний SEL вибір.','Читає інструкції.','Не оцінюється.'),('04–12',f'Двічі читає прихований стимул «{data["setting"]}».','Виконує L1–L3.','До 3 відповідей L.'),('12–20','Дає надрукований текст R; не пояснює відповіді.','Виконує R1–R3.','До 3 відповідей R.'),('20–32','Організовує тихі усні пари; слухає по черзі й фіксує лише особисто почуте.','Виконує рольове завдання S; решта готує W.','S тільки для почутих учнів; іншим слот наступного контакту.'),('32–42','Дає незалежне письмове завдання W.','Пише 5–6 речень.','Текст W.'),('42–45','Збирає доступні докази, фіксує неперевірене. Ключ не роздає до завершення перевірки.','Позначає технічне переривання за потреби.','Факт у report.md, без вигаданих результатів.')]
    else:
        s=skills[0]
        action={'L':'Читає прихований стимул двічі; забезпечує чутність.', 'R':'Дає текст R; допомагає тільки з процедурою.', 'S':'Слухає пари / окремі взаємодії з учителем; решта тихо готується.', 'W':'Дає завдання W; учні пишуть самостійно.'}[s]
        activities=[('00–05','Пояснює навичку й критерії; добровільний вибір паузи.','Готує аркуш.','Факт доступності.'),('05–10',f'Пояснює процедуру {s}; відповідає на процедурні запитання без предметних підказок.','Читає умови / запитання.','План роботи.'),('10–25',action,'Виконує цільове завдання '+s+'.','Доказ '+s+' за наявності доступу.'),('25–35','Надає час для завершення; для S слухає наступні пари.','Перевіряє / завершує роботу, для S чекає черги тихо.','Завершений продукт; ще не висновок про досягнення.'),('35–42','Збирає роботи / завершує доступні індивідуальні слоти S.','Здає продукт; неперевірену навичку переносить.','Список отриманих і відсутніх доказів.'),('42–45','Фіксує умови й домовляється про відсутні слоти.','Позначає потребу повторного контакту.','Незаповнений результат доповнюється тільки за фактом.')]
    online=[(a,b+' Онлайн: камера необов’язкова; інструкція також у чаті. '+('L проводити лише за перевіреної чутності; без звуку перенести. ' if 'L' in skills else '')+('Для S потрібен добровільний аудіоканал; чат є підготовкою, усний доказ переноситься. ' if 'S' in skills else ''),c,d) for a,b,c,d in activities]
    brows=[('00–03','Після дозволу пояснює: формальний контроль відкладається, це лише тихе відновлення ресурсу.','Обирає аркуш чи паузу.','Не оцінюється.'),('03–08',f'Дає для читання тільки інструкцію теми «{data["setting"]}», не аудіотекст і не ключ.','Обводить знайомі слова; може пропустити.','Позначки готовності.'),('08–12','Пропонує 2 ключові слова до майбутнього повідомлення.','За бажанням пише два слова; не виконує контроль.','Чернетка, не контрольний доказ.'),('12–15','Визначає наступний контакт для перевірки в придатних умовах.','Зберігає аркуш.','Перенесення у report.md.')]
    drows=[('00–03','Завчасно на аркуші: контроль переноситься до відновлення придатних умов.','Читає інструкцію, якщо є ресурс і освітлення.','Не оцінюється.'),('03–08',f'На аркуші: «До теми {data["setting"]} запиши 2 знайомі слова».','Пише за бажанням.','Підготовчі слова.'),('08–12','На аркуші: прочитай процедуру; познач запитання до вчителя.','Пише ? або одне процедурне запитання.','Питання для контакту.'),('12–15','На аркуші: збережи папір, не шукай інтернет і не надсилай негайно.','Зберігає роботу.','Контроль лишається непроведеним.')]
    lesson=f'''# Урок {n:03d}. {l['topic']}

Планова дата: {l['date']}; 6 клас, {l['semester']} семестр. **Це план перевірки, не запис факту й не готовий висновок про результати.**

## План для адміністрації та опорний конспект

Тип: {'діагностична робота L/R/S/W' if diag else 'перевірка окремої навички '+skills[0]}. Тема стимулів: {data['setting']}. Мета — одержати окремі докази {', '.join(skills)} на вивченому матеріалі, визначити наступний навчальний крок. Показники: точність розуміння фактів, виконання комунікативного завдання, зрозумілість і доречність мови. Компетентності: іншомовна комунікація; самостійність; повага до партнера; самоорганізація. Нормативні коди й автоматичний перерахунок у шкільну шкалу не приписуються.

Учитель: «Сьогодні перевіряємо {', '.join(skills)}. Камера й технічний доступ не є предметом оцінювання. Якщо не чути або потрібна пауза, повідом будь-яким доступним способом. Якщо доказу немає, ми перевіримо його іншого разу». Опорні мовні моделі й відповіді містяться тільки у key.md; до завершення самостійної спроби їх не показувати. Роздатка повністю друкована; для L текст читає вчитель із ключа; зовнішній запис не потрібен.

Перед початком узгодити порядок, доступність і критерії. Після перевірки пояснити одну наступну дію. За 12 хв неможливо почути весь клас: у діагностиці провести вибіркові слоти S, решту явно перенести, не зараховувати спостереження з письма як усне мовлення.

## SEL й безпека

{SEL}

{SAFETY}

## A — клас, 45 хвилин

{table(activities)}

## B — укриття, до 15 хвилин, тільки підготовка

{table(brows)}

## C — дистанційно, 45 хвилин, камера необов’язкова

{table(online)}

## D — асинхронно, 10–15 хвилин, тільки підготовка

{table(drows)}

## Переривання та повторна перевірка

При тривозі роботу припинити. Зберегти лише вже отримані докази, якщо це не затримує безпечні дії. Не робити висновок «контроль успішно проведено» для всього класу. У report.md зазначити навичку, перервану частину, доступність і дату нового слота. Для L після частково почутого стимулу дати інший еквівалентний стимул та перевірити чутність; для S — новий усний слот; для R/W — вирішити, чи продовжити з тієї точки або надати рівноцінне завдання. На перенесенні використовувати варіант іншої групи ASSESSMENTS у генераторі з відповідною навичкою й лексичним рівнем; учитель перевіряє відповідність уже вивченому. Зміна варіанта фіксується. B/D не є завершенням формальної перевірки. Чат не доводить усне мовлення, читання стимулу не доводить аудіювання.

## Диференціація й оцінювання

Збільшений час, великий друк, окреме тихе місце й повторення процедурної інструкції — за потребою. Під час R не читати текст замість учня, під час L не показувати його; це змінить навичку і має бути позначено як інша діяльність. Допомогу у змісті зафіксувати, не представляти як незалежну роботу. Закриті завдання — по 1 робочому балу (окремо L 0–3, R 0–3); S/W — окремі аналітичні описи в ключі, не автоматична офіційна оцінка. Не виставляти нуль через відсутність доступу.

## Домашня робота

Нової контрольної роботи додому немає. Після отримання зворотного зв’язку — до 5 хв на одну правку або одну ціль на наступний раз. Невиконаний через переривання контроль проходить за погодженим графіком у придатних умовах.
'''
    return lesson,'\n\n'.join(hand),'\n\n'.join(keys)

RUBRIC='''## Рубрика відкритого продукту

Робоча аналітична рубрика, не офіційне переведення в 12 балів. За кожним критерієм: 0 — доказу ознаки немає у наданій роботі; 1 — частково; 2 — достатньо для сформульованого завдання. Критерії: (1) виконання змістового завдання; (2) зрозумілість і зв’язність; (3) доречні слова / форми. Для S додатково описово зафіксувати реакцію на партнера та зрозумілість усного мовлення; підказки / читання заготовки відмічати. Для W позначити самостійну правку. Сума 0–6 — лише внутрішня опора для зворотного зв’язку. Відсутність доступу позначати «немає доказу», не нулем. Дозволені інші змістовні відповіді, вигадані персонажі й альтернативні рішення. Приклад зворотного зв’язку: «Ти назвав місце й час; наступний крок — додати причину з because».
'''

def report(l):
    return f'''# Факт уроку {l['number']:03d} — незаповнений шаблон

Планова дата: {l['date']}. Планова тема: {l['topic']}.

**Заповнювати тільки після фактичного контакту. Дата в календарі не означає, що урок проведено. Не вносити персональні дані до публічного Git-репозиторію; індивідуальні докази зберігати в дозволеній шкільній системі.**

- Фактична дата / час / тривалість: ______________________________
- Режим: □ A □ B □ C □ D □ перенесено □ навчання не відбулося
- Умови / переривання (без чутливих подробиць): ___________________
- Фактично опрацьовані блоки, вправи та інтервали: ________________
- Кількість учнів із доступним каналом участі: ____ / ____ (не робити висновку за камерою)
- Отримані докази: □ L ____ □ R ____ □ S ____ □ W ____
- Не отримані докази / причини доступу: _________________________
- Контроль: □ не планувався □ не розпочато □ частково □ завершено для зазначеної групи; доказ / кількість: ________________________
- Спостереження за критеріями, без припущень: ____________________
- Допомога / адаптації та їхній вплив на самостійність: ___________
- SEL запропоновано / пропущено (без оцінювання емоцій): __________
- Місце зупинки й конкретний наступний крок: _____________________
- Перенесено на дату / контакт; відповідальний: __________________
- Домашня робота фактично оголошена; скорочення навантаження: _____
- Потреба корекції плану: _______________________________________

Підпис / дата заповнення: ______________________________________
'''

def main():
    data=json.loads(SOURCE.read_text()); lessons=data['lessons']; ads={a['slug']:a for a in data['adaptations']}
    assert len(lessons)==123 and [l['number'] for l in lessons]==list(range(1,124))
    manifests=[]
    for l in lessons:
        folder=BASE/f'{l["number"]:03d}'; folder.mkdir(parents=True,exist_ok=True)
        assess=l['lesson_type'] in ('pair_diagnostic','semester_check')
        if assess: lesson,hand,key=assessment(l)
        else: lesson,hand,key=lesson_regular(l,choose(l,ads))
        hand=f'# 6 клас · урок {l["number"]:03d} · {l["topic"]}\n\nПланова дата: {l["date"]}. Ім’я або умовне позначення: __________________\n\nМожна працювати з вигаданими персонажами. Під час переміщення в укриття не виконувати завдань. Якщо немає безпечних умов / освітлення, відкласти. Перевірку стану можна пропустити.\n\n'+hand
        if not assess:
            hand+='\n\n## Короткий маршрут без інтернету (D, 10–15 хв)\n\n00–02: відкрий блок 1, словник і модель. 02–06: прочитай текст, підкресли 2 факти. 06–10: виконай вправу 3 №1–2. 10–13: напиши 1–2 речення вправи 4. 13–15: постав ? біля труднощів і збережи аркуш. За відсутності ресурсу зупинись раніше; надсилати роботу під час відключення не потрібно. Принеси її за наступної можливості.\n\nДЗ до 10 хв: допиши / відредагуй до 4 речень вправи 4. Після короткого маршруту — лише два початі пункти й 1–2 речення; без подвійного навантаження.'
        else:
            hand+='\n\n## Якщо немає світла / звуку або ви в укритті\n\nКонтроль відкладається. За бажанням 00–03 прочитай тільки інструкцію, 03–08 запиши 2 знайомі слова до теми, 08–12 познач процедурне запитання, 12–15 збережи аркуш. Це підготовка, а не контрольний результат. Нового контрольного ДЗ немає.'
        write(folder,'lesson.md',lesson);write(folder,'handout.md',hand);write(folder,'key.md',f'# Ключ учителя · урок {l["number"]:03d}\n\nНе долучати цей аркуш до учнівської роздатки.\n\n'+key+'\n\n'+RUBRIC);write(folder,'report.md',report(l))
        manifests.append({'number':l['number'],'date':l['date'],'topic':l['topic'],'directory':folder.name,'source_id':l['id'],'lesson_type':l['lesson_type'],'files':['lesson.md','handout.md','key.md','report.md'],'assessment':assess})
    (BASE/'manifest.json').write_text(json.dumps({'grade':6,'count':len(manifests),'academic_year':data['academic_year'],'lessons':manifests},ensure_ascii=False,indent=2)+'\n')
    readme='''# 6 клас — службові пакети на весь календар

Покриття: **123 із 123 календарних уроків**, 2026/2027; від 2026-09-01 до 2027-06-01. Кожен урок має окремі план/опорний конспект із чотирма сценаріями, самодостатню роздатку, ключ із рубрикою та порожній шаблон фактичного звіту. Дати — планові; джерело має статус запропонованого календаря. Це не підтвердження проведених уроків і не заповнена звітність.

Відтворення: `python3 scripts/build_teacher_grade6.py` із кореня репозиторію. Генератор читає тільки `teacher/6/source-plan.json`: очищені календарні поля та вбудовані локальні адаптації. `/home/why/-teach` потрібен лише для історичного походження, не для генерації. SHA-256 і початкові шляхи записані у provenance; службові лінки, журнальні ідентифікатори та відомості про зустрічі не імпортуються. Початкове джерело — річний план, а не каталог сайту. Планові сторінки підручника збережено як орієнтир, але роздатка не потребує підручника, інтернету чи аудіозаписів.

A: 45 хв у класі. B: до 15 хв тільки після завершення переміщення, дозволу й оцінки умов; за шуму / тісноти не проводити. C: 45 хв онлайн, камера необов’язкова, письмовий канал участі. D: 10–15 хв із завчасно виданим папером, якщо є безпечне освітлення та ресурс. Під час переміщення навчальних завдань немає. SEL — авторські підтримувальні мікропрактики з правом пропуску й вигаданими персонажами; вони не названі офіційними вправами «Зерна». Нормативні коди та офіційні шкали не вигадувалися.

На контрольних L/S письмовий канал є підготовкою, а не заміною відповідної навички. У B/D формальний контроль переноситься; у C слухання потребує чутності, говоріння — фактичного усного доказу. Окремі слоти для всіх учнів планує вчитель: у 12 хв діагностичного уроку весь клас прослухати неможливо. Тексти слухання — тільки в ключі. Матеріали культурних / пісенних уроків є текстовою адаптацією, без твердження, що аудіювання оригінальної пісні відбулося.

Обмеження: авторські готові до адаптації пакети потребують учительського перегляду під фактичний клас, ІПР, затверджені критерії закладу й актуальний розклад. Робоча рубрика 0–6 не є автоматичною офіційною оцінкою. Фактичні звіти заповнюються тільки після проведення; персональні дані учнів не комітити. Роздатка handout.pdf призначена учневі; teacher.pdf містить службові ключі та звіт і видається тільки вчителю.

## Календар і файли

| № | Планова дата | Тема | Матеріали |
|---|---|---|---|
'''
    for m in manifests:
        d=m['directory']; links=' · '.join(f'[{label}]({d}/{file})' for label,file in [('план','lesson.md'),('роздатка','handout.md'),('ключ','key.md'),('звіт','report.md'),('PDF учня','handout.pdf'),('PDF учителя','teacher.pdf')])
        readme+=f'| {m["number"]} | {m["date"]} | {m["topic"]} | {links} |\n'
    write(BASE,'README.md',readme)
    print(f'Generated {len(lessons)} lesson packets in {BASE}')

if __name__=='__main__':main()
