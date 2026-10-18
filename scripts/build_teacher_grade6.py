#!/usr/bin/env python3
"""Rebuild every grade 6 teacher packet from the checked-in, sanitized source only."""
from pathlib import Path
import json
import re
import copy
import hashlib

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
'1b':'Mia has got curly hair. She is wearing a blue jacket. She is reading a book and pointing at a map.',
'1c':'I usually wear jeans. I often wear trainers. I never wear a hat at school. Today I am wearing a skirt. I am wearing a blue shirt. I am carrying a red bag.',
'1d':'I enjoy reading. I love drawing. I like playing tennis. I cannot stand singing karaoke. I would like to try skating.',
'1e':'I am tall and I have got dark hair. I am quiet.\n\nMy imaginary friend Mia has got short hair. She is helpful. We play tennis together.',
'2a':'Last summer I visited a lake. I went there by bus. I took photos. I bought a postcard. I did not swim. I enjoyed the trip.',
'2b':'A bus is cheap and comfortable. It moves slowly in traffic. A taxi is expensive and fast. When I was five, I could ride a bike.',
'2c':'List: tickets, passport, weather forecast, bag. Did you book the tickets? Have you got your passport? What is the weather like? Did you pack your bag? Yes, I packed the tickets. I packed them this morning. The tickets are for us.',
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
'6e':'Dear Mia, I joined the tennis club last month. I practise twice a week. Last week I played a friendly match. Next week I am going to practise with Leo. Would you like to join us? Alex',
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
# Deliberate editorial corrections; source snapshots and provenance remain unchanged.
def question(prompt, choices, why):
    return {'prompt':prompt,'choices':choices,'answer':0,'why':why}


def curate_adaptations(ads):
    import copy
    ads=copy.deepcopy(ads)
    ads['sb-1c']['title']='Clothes and fashion'
    a=ads['sb-3a']; a['reading']='Leo was carrying a box in the school garden. Mia was drawing at a table. Eva was playing with a ball. The ball rolled under the table and the box fell. Nobody was hurt. A teacher helped Leo pick up the pencils. The children thanked her.'
    a['example']='Leo was carrying a box. Mia was drawing. What was Eva doing? She was playing with a ball.'
    a['questions'][2]=question('___ Eva playing with a ball?',['Was','Were','Did'],'Eva + was; запитання у Past Continuous.')
    a['questions'][3:]=[question('What made the box fall?',['A ball rolled under the table.','A car hit the table.','A dog jumped.'],'За текстом м’яч покотився під стіл.'),question('Who helped Leo?',['A teacher.','A driver.','A police officer.'],'Учитель допоміг зібрати олівці.')]
    a=ads['sb-3d']; a['reading']='This is an original classroom story inspired by the theme of White Fang, not a quotation. A traveller and a dog are waiting at a forest camp. Their friend has gone to get food. The traveller feels worried because nobody is at the gate. Then someone calls his name. The friend returns with something to eat. Everyone feels relieved.'
    a['example']='Someone is at the gate. Nobody is alone now. Everyone feels relieved. There is something to eat.'
    a['questions'][3:]=[question('Why does the traveller feel worried?',['Nobody is at the gate.','He has lost his passport.','A wolf attacks him.'],'У тексті названо причину: nobody is at the gate.'),question('How does everyone feel at the end?',['Relieved.','Angry.','Afraid.'],'Останнє речення: everyone feels relieved.')]
    a=ads['sb-3e']; a['reading']='Leo was reading in his garden when the door closed. His keys were inside. Unfortunately, he could not open the door. He stayed in the garden and asked a neighbour to call his aunt. Luckily, his aunt had a key. She came and opened the door. In the end, Leo got inside safely and thanked them.'
    a['questions'][1]=question('Leo was reading when the door ___.',['closed','closes','closing'],'Past Simple позначає коротку подію.')
    a['questions'][3:]=[question('Why could Leo not open the door?',['His keys were inside.','He was on a bus.','The house had no door.'],'Ключі залишилися всередині.'),question('Who opened the door?',['His aunt.','A police officer.','A driver.'],'Тітка мала ключ і відчинила двері.')]
    a=ads['sb-2c'];a['write']['prompt']+=' Додай дві відповіді з me, us або them.'
    a=ads['sb-5b'];a['example']='I think gadgets will change. People will be able to use better batteries. I will help you. Will you bring the headphones?'
    a['rule']+=' Will be able to + базова форма — майбутнє вміння. Future Progressive згадується в календарі лише для ознайомлення; не вимагаємо його у продукті цього уроку.'
    a=ads['sb-6b'];a['reading']='Mia is waiting for Leo in the school library. Leo tells her that he feels unwell and has got a headache. Mia listens and asks, “Should we tell the teacher?” Leo agrees. They ask the teacher for help. The teacher stays with Leo and contacts the responsible adult. Mia keeps his books for him.'
    a['questions'][3:]=[question('Where is Mia waiting?',['In the school library.','At the airport.','At a music class.'],'Перше речення називає school library.'),question('What do the children do?',['Ask the teacher for help.','Choose medicine.','Hide the problem.'],'They ask the teacher for help; лікування не обирають.')]
    a=ads['sb-6c'];a['example']='You like tennis, don’t you? She is the instructor, isn’t she? They cannot swim, can they?'
    a=ads['sb-7e'];a['rule']='Присвійний прикметник стоїть перед іменником: my book, your bag, her notebook, their desk. Присвійний займенник замінює іменник: mine, yours, hers, theirs. Mia’s notebook = зошит Мії. Should + базова форма — доброзичлива порада.'
    a['example']='Mia’s notebook is on her desk. It is hers. This book is mine. You should ask for help.'
    a['questions'][0]=question('This is Mia’s notebook. It is ___.',['hers','her','she'],'Hers замінює her notebook; після нього іменник не потрібен.')
    a['questions'][1]=question('This is ___ book; it belongs to me.',['my','mine','me'],'My стоїть перед book.')
    a['questions'][2]=question('Choose the possessive form.',['Mia’s notebook','Mia notebook','Mias notebook'],'Mia + ’s виражає належність.')
    a=ads['sb-8a'];a['rule']+=' Defining: The girl who won the prize is my friend (без цієї частини неясно, котра дівчина). Non-defining: Mia, who won a prize, is my friend (додаткова інформація відокремлена комами; that тут не вживаємо).'
    a['example']='The girl who won the prize is happy. This is a camera which takes clear photos. Mia, who won a prize, is my friend.'
    a['questions'][2]=question('Choose a sentence with additional information.',['Mia, who won a prize, is my friend.','Mia that won a prize, is my friend.','Mia, which won a prize, is my friend.'],'Ім’я визначає особу; додаткова інформація з who виділена комами.')
    a=ads['sb-8d'];a['questions'][3]=question('What was one film chosen as?',['The best project.','The oldest cartoon.','The longest report.'],'Текст не називає фільм: він повідомляє, що той став best project.')
    a=ads['sb-culture-3'];a['questions'][2]=question('The parks are green spaces in ___.',['busy cities','deserts','airports'],'Перше речення прямо називає busy cities.')
    a['example']='Both parks have trees. Visitors can walk and enjoy nature. Parks have changed over time.'
    a=ads['sb-clil-geography'];a['reading']+=' A capital does not have to be the largest city.'
    a=ads['sb-clil-music'];a['questions'][2]=question('A violin can be played with a ___.',['bow','printer','receipt'],'Bow — смичок; пояснено в словнику.')
    a['vocabulary'].append(['bow','смичок'])
    # Core recap: all five subunit structures, with no questions about missing stories.
    recaptexts={
    1:'Mia studies at Green School. Classes start at nine. She has got curly hair. Today she is wearing a blue shirt and reading in the library. She usually wears jeans. Mia enjoys drawing and would like to join an art club. Her friend Leo is helpful. They both like music.',
    2:'Last Saturday Mia went to a museum by bus. The driver drove carefully. Mia could read a map when she was six. She gave her tickets to Leo and asked him to keep them. People used to travel more slowly. The friends enjoyed the trip because they saw an interesting exhibition.',
    3:'Mia was reading when she heard a noise. While Leo was drawing, a cat came into the garden. There were some pencils on the table, but there was no food. Someone opened the gate. It was their teacher. Luckily, the cat went home and everyone felt happy.',
    4:'Mia asked, “May I borrow a book?” Then she walked through the park. The library is opposite the school. The park is quieter than the street. The library is the largest building in the square. Mia likes this place because she can read there. It has two reading rooms.',
    5:'Mia is going to visit a technology fair. She is meeting Leo at ten. They think future gadgets will use less energy. At school they must sort paper, but they do not have to buy new bags. If they keep the river clean, animals will have a safer home. They invite a friend to a garden event.',
    6:'Mia has a few carrots and a little rice for lunch. Leo feels unwell and should tell an adult. He likes tennis, doesn’t he? Last month Mia joined a tennis club. She practises twice a week. She is going to play a friendly match on Friday. Her team won a small cup last year.',
    7:'Mia has never appeared on TV. She has seen her favourite band twice and saw them last summer. She has lived in Green Town for two years. In a shop, she finds shoes that are too small. She asks for larger ones. Later she finds Leo’s notebook. It is his, so she returns it.',
    8:'Mia is the student who writes for our magazine. Articles are checked by the teacher. Last week a film was shown at school. Mia liked it because it was about a girl who helped her friends. Leo said, “I like this film.” Mia answered, “So do I.” They wrote a short review.'}
    for module,text in recaptexts.items():
        a=ads[f'sb-round-up-{module}'];a['reading']=text
        a['questions']=[copy.deepcopy(ads[f'sb-{module}{letter}']['questions'][0]) for letter in 'abcde']
        a['example']=' '.join(ads[f'sb-{module}{letter}']['example'].split('. ')[0].rstrip('.')+'.' for letter in 'abcde')
        a['rule']='Повтори п’ять мовних фокусів у вправах 3 №1–5. Спочатку дай власну відповідь; опора відкривається після спроби. Після перевірки обери одну форму для власного прикладу. Це формувальне повторення, не контроль.'
        a['vocabulary']=[ads[f'sb-{module}{letter}']['vocabulary'][0] for letter in 'abcde']
    return ads


INTERACTIONS={
'hello-1':('What is your name?','My name is Mia.','Where are you from?','I am from Ukraine.'),
'hello-2':('Have you got a sister?','Yes, I have.','Can she draw?','Yes, she can.'),
'hello-3':('How many boxes are there?','There are two.','Where are they?','They are under the desk.'),
'1a':('What time do your classes start?','At nine.','What subject do you enjoy?','I enjoy art.'),
'1b':('What is Mia doing?','She is reading.','Is she wearing glasses?','Yes, she is.'),
'1c':('What do you usually wear?','I usually wear jeans.','What are you wearing today?','I am wearing a blue shirt.'),
'1d':('Would you like to join an art club?','Yes, I would.','Do you enjoy drawing?','Yes, I do.'),
'1e':('What is your friend like?','She is helpful.','What do you do together?','We play tennis.'),
'2a':('Where did you go last summer?','I went to a lake.','Did you take photos?','Yes, I did.'),
'2b':('Could you ride a bike when you were six?','Yes, I could.','How does Leo drive?','He drives carefully.'),
'2c':('Did you pack the tickets?','Yes, I packed them.','Can you give them to me?','Yes, here you are.'),
'2d':('Did people use to travel on slow ships?','Yes, they did.','How do they travel now?','They can travel by fast trains.'),
'2e':('How was your school trip?','It was great.','Why did you enjoy it?','I enjoyed it because I saw new things.'),
'3a':('What was Mia doing at five?','She was drawing.','Was Leo reading?','No, he was carrying a box.'),
'3b':('What happened while you were walking?','We heard a noise.','What was it?','It was a cat.'),
'3c':('Are there any rides?','Yes, there are some.','Is there any food?','No, there is no food.'),
'3d':('Is there anyone at the gate?','Yes, someone is there.','How does the traveller feel now?','He feels relieved.'),
'3e':('What happened when the door closed?','Leo stayed in the garden.','Who helped him?','His aunt helped him.'),
'4a':('May I borrow this book?','Yes, you may.','Could you help me find another book?','Of course.'),
'4b':('How do I get to the library?','Go straight on.','Is it opposite the school?','Yes, it is.'),
'4c':('Is the village quieter than the town?','Yes, it is.','Which place do you prefer?','I prefer the village.'),
'4d':('Which planet is the largest in this imaginary group?','Planet C is the largest.','Is planet A hotter than B?','No, it is colder.'),
'4e':('What is your favourite place in Green Town?','It is the park.','Why do you like it?','I like it because it is quiet.'),
'5a':('What are you going to do on Saturday?','I am going to visit a fair.','When are you meeting Mia?','I am meeting her at ten.'),
'5b':('Will phones use less energy?','I think they will.','Will you help me compare them?','Yes, I will.'),
'5c':('Do we have to buy new bags?','No, we do not.','Must we sort the paper?','Yes, we must.'),
'5d':('What will happen if we keep the river clean?','Animals will have a safer home.','What can we do today?','We can learn about local animals.'),
'5e':('Would you like to come to our event?','I would love to.','Where are we meeting?','At school at ten.'),
'6a':('How many carrots are there?','There are a few.','How much rice is there?','There is a little.'),
'6b':('Mia feels unwell. What should she do?','She should tell an adult.','Should she ask the teacher for help?','Yes, she should.'),
'6c':('You like tennis, don’t you?','Yes, I do.','Mia can swim, can’t she?','Yes, she can.'),
'6d':('Where does Green Stars play?','It plays in Green Town.','What did the team win last year?','It won a local cup.'),
'6e':('When did you join the tennis club?','Last month.','What are you going to do next?','I am going to play a friendly match.'),
'7a':('Have you ever watched a musical?','Yes, I have.','Have you ever won a prize?','No, I haven’t.'),
'7b':('Have you ever seen this band?','Yes, I have.','When did you see them?','I saw them last summer.'),
'7c':('How long have you had this book?','I have had it for two days.','When will you return it?','I will return it on Monday.'),
'7d':('Can I try on the blue T-shirt?','Yes, here you are.','How much is it?','It is ten pounds.'),
'7e':('Is this notebook yours?','No, it is Mia’s.','What should I do?','You should give it to her.'),
'8a':('Who is Mia?','She is the girl who won a prize.','What is this?','It is the camera which she bought.'),
'8b':('I am nervous.','So am I.','I haven’t been on TV.','Neither have I.'),
'8c':('Who writes the articles?','They are written by students.','Are the pages checked?','Yes, they are.'),
'8d':('Was the film shown on Friday?','Yes, it was.','How many prizes were given?','Two prizes were given.'),
'8e':('What is the film about?','It is about a girl who helps her friends.','Did you like it?','Yes, I liked the plot.')}


def interaction(a):
    code=a['code']
    if code.startswith('round-up-'):code=code[-1]+'a'
    if code in INTERACTIONS:return INTERACTIONS[code]
    # Text-based interaction for culture / CLIL, with a topical anchored answer.
    first=a['reading'].split('. ')[0].rstrip('.')+'.'
    model=a['example'].split('. ')[0].rstrip('.')+'.'
    return ('What does the text say?',first,'Can you give another example?',model)


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
    if l['lesson_type']=='module_intro': ids={5:['sb-5a','sb-5c'],6:['sb-6a','sb-6c'],7:['sb-7a','sb-7d'],8:['sb-8a','sb-8b']}[l['module']]
    if l['section']=='error-analysis': ids=['sb-round-up-7','sb-round-up-8']
    if l['section']=='year-summary-1': ids=['sb-2e','sb-3e']
    if l['section']=='year-summary-2': ids=['sb-7d','sb-7e']
    # Long recap content is deliberately divided into two short independent tasks.
    return [ads[i] for i in ids if i in ads][:2]

def sample(a):
    if a['code'] in SAMPLES:return SAMPLES[a['code']]
    return a['example']

def block(a,idx,l):
    label=f'Блок {idx}: {a["title"]}'
    intro=l['lesson_type']=='module_intro'
    repeat=l['lesson_type']=='unit_recap'
    secondary=idx>1
    full_task=l['lesson_type'] in ('language_and_production','integrated_skills','year_summary') and a['code'] in SAMPLES
    vocab=a['vocabulary'][:8]
    # Introductory lessons retrieve meanings before teaching the new grammar.
    qs=a['questions'][:(3 if full_task else 5)]
    if intro:
        qs=[question(f'Обери переклад: {w}',[u]+[u2 for w2,u2 in vocab if u2!=u][:2],f'{w} — {u}; це перевірка лексики, не нової граматики.') for w,u in vocab[:3]]
    if secondary: qs=qs[:2]
    lines=[f'## {label}']
    if secondary:lines+=['Другий змістовий ракурс: лише текст і 2 відповіді; окремого письмового твору не потрібно. За браку часу переноситься без додаткового ДЗ.']
    lines+=['### 1. Словник', '; '.join(f'{w} — {u}' for w,u in vocab)]
    if not repeat:
        lines+=['Опора (можна відкрити): '+a['rule'],f'Мовна модель: {a["example"]}']
    lines+=['### 2. Прочитай',a['reading'],'### 3. Обери відповідь. Для мовної форми поясни правило; для факту підкресли його в тексті.']
    keys=[]
    for n,q in enumerate(qs,1):
        opts=list(enumerate(q['choices'])); offset=(l['number']+n)%len(opts); opts=opts[offset:]+opts[:offset]
        lines += [f'{n}. {q["prompt"]}', ' / '.join(f'{chr(65+j)}) {opt}' for j,(_,opt) in enumerate(opts)), 'Відповідь: __________ Доказ / пояснення: __________________________']
        letter=next(chr(65+j) for j,(original,opt) in enumerate(opts) if original==q['answer'])
        keys.append(f'{n}. **{letter} — {q["choices"][q["answer"]]}**. {q.get("why", "За текстом / моделлю.")}')
    if repeat:lines+=['Після власної спроби: '+a['rule'], 'Опора після спроби: '+a['example']]
    if secondary:return '\n\n'.join(lines),f'## {label}\n\n'+'\n\n'.join(keys)
    short_task=f'За текстом «{a["title"]}» запиши два факти (можна короткими реченнями). Окремо під заголовком «Мій вигаданий варіант» напиши ще два тематичні речення. Використай структуру з опори. Це 4 речення разом; не потрібно розкривати особисті дані.'
    writing_task=(a['write']['prompt']+' Можна обрати вигаданих персонажів та обставини.') if full_task else short_task
    if intro:writing_task='Вибери 4 слова зі словника. Розподіли їх за двома власними підгрупами або намалюй 2 предмети й підпиши 4 деталі. Напиши одну коротку репліку за моделлю; нову граматичну форму самостійно будувати ще не потрібно.'
    if l['lesson_type'] in ('portfolio','reflection'):writing_task='Необов’язковий запасний матеріал. Основний продукт цього уроку — спеціальне завдання на початку аркуша; другий текст не створюй.'
    lines+=['### 4. Мій тематичний продукт',writing_task,f'Початок на вибір: {a["write"]["starter"]}',*['________________________________________________________________________']*(10 if full_task else 6),'Перевірка: □ виконав зміст завдання □ зрозумілі речення □ перевірив(ла) одну форму.']
    if l['lesson_type'] not in ('reflection','portfolio','module_intro'):
        turns=interaction(a)
        lines+=['### 5. Мініситуація на вибір (якщо лишився час)',f'Вигадана ситуація «{a["title"]}». A починає: “{turns[0]}” B відповідає за темою; A ставить друге запитання / репліку, B реагує. Поміняйте одну деталь і ролі. Можна грати соло й записати обидві ролі. Мовчазна / чат-версія дає письмовий доказ; усний фіксують тільки за реальним говорінням.','A: __________________________ B: __________________________','A: __________________________ B: __________________________']
        keys+=['Вправа 5, можливий тематичний діалог: '+' '.join(f'{"A" if i%2==0 else "B"}: {t}' for i,t in enumerate(turns))]
    sentences=re.split(r'(?<=[.!?])\s+',a['reading'])
    facts=' '.join(sentences[:2])
    models=[x for x in re.split(r'(?<=[.!?])\s+',sample(a)) if x.endswith('.')][:2]
    named_models=' '.join(models)
    named_models=re.sub(r'\bShe\b','Mia',named_models)
    named_models=re.sub(r'\bHe\b','Leo',named_models)
    exemplar=sample(a) if full_task else f'Два факти: {facts} Мій вигаданий варіант: '+ named_models
    if intro:exemplar='Можливі слова: '+ '; '.join(w for w,u in vocab[:4])+'. Припустимі різні підгрупи, якщо пояснення логічне. Репліку можна скопіювати з моделі; це не доказ самостійного володіння новою формою.'
    return '\n\n'.join(lines),f'## {label}\n\n'+'\n\n'.join(keys)+f'\n\nВправа 4, можливий варіант: {exemplar}'


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
    stage2='Спочатку без опори обери відповідь; потім перевір моделлю й виправ іншим знаком.' if repeat else ('Прочитай текст мовчки. Підкресли два слова й знайди головну думку.' if reception else 'Прочитай текст, виконай 3 мовні пункти вправи 3; знайди модель для свого продукту.')
    stage3='Зроби спеціальне завдання на початку аркуша: корекцію або відбір зразків; запиши причину правки.' if typ in ('reflection','portfolio') else ('Виконай вправу 3 блоку 1; за наявності другого блоку — його 2 пункти. Для фактів познач доказ, для форм — правило.' if reception or repeat else 'Плануй і починай продукт вправи 4 тільки блоку 1; другий блок — лише короткий текст і 2 відповіді.')
    if typ=='module_intro':stage3='Виконай лексичні пункти вправи 3; розподіли слова у вправі 4. Нова граматика — тільки ознайомча модель.'
    continuation='Заверши спеціальне завдання на початку аркуша; інші продуктивні вправи не обов’язкові.' if typ in ('reflection','portfolio') else f'Заверши продукт вправи 4 тільки блоку 1 «{ptitle}». Мініситуація 5 — вибір за наявності часу, а не ще одна обов’язкова робота.'
    objective=f'Розуміти короткий текст «{ptitle}», знайти 2 підтвердження, застосувати цільову модель у власному короткому продукті.'
    if repeat: objective=f'Відновити матеріал «{ptitle}», пояснити одну мовну правку та обрати наступний крок.'
    if typ=='portfolio':objective='Дібрати два зразки, внести обґрунтовану правку й описати поступ без порівняння дітей між собою.'
    arows=[('00–03','«Можна почати з одного слова або взяти паузу». Пропонує добровільну SEL перевірку.','Обирає спосіб участі.','Приватний вибір; не оцінюється.'),('03–07',f'«Тема: {title}. Наприкінці покажемо два докази й короткий продукт». Називає критерії.','Відзначає знайомі слова блоку 1.','2 позначені слова.'),('07–12',f'Показує словник і читає модель: «{primary["example"]}». Просить порівняти форми.','Читає / слухає в класі за можливості; знаходить структуру.','1 виділена структура.'),('12–20',f'Дає блоки {blocks}. «{stage2}»','Читає текст; ставить ? біля незрозумілого.','Два підкреслення / чернетка.'),('20–28',f'«{stage3}»; допомагає точковим запитанням «Where is your evidence?»','Працює індивідуально; пояснює одну дію.','Вправа 3 або чернетка 4; спеціальний продукт.'),('28–37',f'«{continuation}».','Створює продукт вправи 4 у вказаному обсязі; співрозмовник реагує.','Короткий текст; усний доказ лише за фактичного говоріння.'),('37–42','Показує ключ тільки після спроби; «Знайди одну правку й поясни її».','Самоперевірка й редагування.','Одна видима правка.'),('42–45','«Покажи два слова й одну структуру, які вже можеш використати». Пояснює ДЗ.','Позначає наступний крок; здає доступний продукт.','Вихідний квиток / позначка відсутності доказу.')]
    brows=[('00–02','Після дозволу пропонує мовчазний вибір: аркуш чи пауза.','Обирає без пояснення.','Жодної оцінки стану.'),('02–05',f'Показує на аркуші модель «{primary["example"]}». Не перекрикує шум.','Мовчки знаходить 2 слова у блоці 1.','2 позначки.'),('05–10',f'Вказує: блок 1 «{ptitle}», текст і тільки вправу 3 №1–2.','Читає доступну частину, обирає дві відповіді.','До 2 відповідей.'),('10–13','Вказує на вправу 4: «Одне речення достатньо».','Пише одне тематичне речення або обирає паузу.','0–1 речення; не контрольна оцінка.'),('13–15','Позначає місце зупинки; організовує збереження аркуша без фото.','Зберігає роботу; за бажанням позначає ?.','Точка повернення: блок 1, вправа 3 №3.')]
    crows=[('00–04','Надсилає / завчасно видає аркуш. «Камера необов’язкова; можна відповідати цифрою в чаті або на папері».','Позначає доступність через чат, реакцію або пізніший зв’язок.','Канал доступу; мовчання не доказ відмови.'),('04–09',f'«Тема {title}. Прочитайте модель блоку 1». Дає письмову інструкцію.','Відмічає 2 слова.','2 слова на папері / в чаті.'),('09–16',f'Пише «{stage2}» й показує структуру у словнику.','Читає без увімкнення камери / мікрофона.','Два докази в тексті.'),('16–25',f'Дає вправу 3 у блоках {blocks}. У чат — номер+літера; публічно не ранжує.','Відповідає в чаті або на аркуші.','До 5 відповідей на блок.'),('25–35',f'Дає тільки один продукт: {continuation}','Створює текст; надсилає 1–2 речення або зберігає папір.','Продукт вправи 4 / спеціальний продукт.'),('35–41','Дає час завершити основний продукт. Мініситуація 5 — тільки якщо завершено; приватний голос за згодою або письмова участь.','Реагує на партнера; редагує одну репліку.','Дві взаємопов’язані репліки; тип доказу за фактом.'),('41–45','Дає ключ після спроби, ДЗ і маршрут повернення для тих, хто зник зі зв’язку.','Виправляє один пункт; позначає завершене.','Правка; точка наступного входу.')]
    drows=[('00–02',f'Завчасна друкована інструкція: «Візьми тільки блок 1 {ptitle}; інтернет і підручник не потрібні».','Читає словник і модель, якщо є безпечні умови та освітлення.','Обрано 2 слова.'),('02–06','На аркуші: прочитай текст; підкресли 2 факти.','Читає у власному темпі.','Два підкреслення.'),('06–10','На аркуші: зроби вправу 3 №1–2; без таймера й поспіху.','Записує дві відповіді.','Дві літери.'),('10–13','На аркуші: напиши 1–2 речення вправи 4; якщо ресурсу немає — зупинись.','Пише короткий продукт.','1–2 речення.'),('13–15','На аркуші: постав ? біля труднощів; принеси аркуш за наступної можливості.','Зберігає роботу; нічого не надсилає під час відключення.','Аркуш для наступного контакту.')]
    focus='; '.join(l.get('language_inventory',{}).get('grammar',[])) or 'лексика теми та зв’язний зміст'
    script=f'''# Урок {n:03d}. {title}

Планова дата: **{l['date']}**. 6 клас; {l['semester']} семестр; тривалість A/C — 45 хв, B — до 15 хв після завершення переміщення, D — 10–15 хв у власному темпі. Статус: план, а не запис фактично проведеного заняття.

## План для адміністрації

Тип: {phase}. Розділ: {l.get('module_title','')}; календарна секція: {l['section']}. Орієнтир підручника: {', '.join(map(str,l.get('sb_pages',[]))) or 'узагальнення календарного матеріалу'} (друковані сторінки; для виконання пакета підручник не потрібен).

Мета: {objective}

Календарний мовний фокус: {focus}. У вступному / рецептивному уроці це опора для розуміння; продуктивний доказ очікується після практики, не за копіюванням моделі.

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

Підтримка: тільки блок 1, словник відкритий, 2 закриті відповіді та 1 речення за моделлю; інструкція українською; можна диктувати дорослому за звичайних умов, зазначивши допомогу. Базово: 5 відповідей на введенні / повторенні або 3 на продуктивному уроці; лише один продукт вправи 4. Якщо є блок 2 — тільки його текст і 2 відповіді, без другого твору. На вступі — лексична класифікація замість вимоги нової граматики. На корекції / портфоліо основний лише спеціальний продукт; інші вправи запасні. Розширення: пояснення вибору форми або мініситуація 5 замість частини письма. Швидкість, камера, охайність та особисті переживання не є критеріями мовного досягнення. Рубрика відкритої роботи — у key.md. Усну навичку фіксуємо лише за усним доказом; письмова заміна є способом участі.

## Домашня робота, до 10 хвилин

Відредагувати одне речення / деталь уже початого основного продукту «{ptitle}». Новий повний твір не потрібен; якщо базове завдання завершене, достатньо однієї правки. Після B/D — завершити лише два початі пункти й 1–2 речення; нової додаткової вправи немає. Якщо немає світла / ресурсу, виконати після відновлення або під час наступного контакту без штрафу за технічну затримку.
'''
    script+='\n\n'+sel_teaching_note(l,primary)+'\n\n'+NUSH_GROUP_NOTE
    hand.append('## За бажанням: як я перевіряю рішення\n\n'+sel_profile(l,primary)['prompt']+'\n\nМожна нічого не записувати. Якщо хочеш, познач лише спосіб: □ повторив умову □ зробив нотатку □ перевірив приклад. Це не оцінюється. Не потрібно описувати особисті переживання.')
    return script,'\n\n'.join(hand),'\n\n'.join(key)

ASSESSMENTS={1:{'setting':'A school trip'},2:{'setting':'A town story'},3:{'setting':'A school garden event'},4:{'setting':'A school film club'}}

ASSESSMENT_NUMBERS=[28,53,54,55,56,57,86,115,116,117,118,119]


def assessment_data(l,reserve=False):
    """Independent parallel forms. All facts used by questions occur in the stimulus."""
    n=l['number']; group={28:1,53:2,86:3,115:4}.get(n,2 if l['semester']==1 else 4)
    serial=ASSESSMENT_NUMBERS.index(n)*2+int(reserve)
    pick=lambda xs:xs[serial%len(xs)]
    day=pick(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    time=pick(['nine','ten','eleven']);end=pick(['two','three','four']);name=pick(['Mia','Eva','Anna','Nina']);friend=pick(['Leo','Sam','Alex'])
    place=pick(['school gate','library entrance','museum entrance']); item=pick(['notebook','pencil','water bottle']);price=pick(['two','three','four'])
    def q(prompt,answer,others):
        return (prompt,[answer]+[x for x in others if x!=answer][:2],0)
    data=copy.deepcopy(ASSESSMENTS[group]); data['setting']+=f' · варіант {n:03d}'+(' R' if reserve else ' P')
    if group in (1,3):
        event='school trip' if group==1 else 'garden event'
        activity=pick(['plant flowers','sort paper','make bird posters'])
        if group==1:
            data['listen']=f'Our {event} was on {day}. We met at {time} near the {place}. Everyone took a {item}. The ticket was {price} pounds. We returned at {end}. We enjoyed the day because we saw interesting things.'
        else:
            data['listen']=f'Our {event} is on {day}. We are meeting at {time} near the {place}. We are going to {activity}. You must bring a {item}, but you do not have to buy new gloves. We finish at {end}. If we work together, we will help our school.'
        data['lq']=[q('Which day is mentioned?',day,['Monday','Tuesday','Wednesday','Thursday','Friday']),q('Where is the meeting point?',f'Near the {place}.',[f'Near the {x}.' for x in ['school gate','library entrance','museum entrance']]),q('What item is mentioned?',f'A {item}.',[f'A {x}.' for x in ['notebook','pencil','water bottle']]),q('What time is the meeting?',f'At {time}.',['At nine.','At ten.','At eleven.']),q('What time does the event end?',f'At {end}.',['At two.','At three.','At four.'])]
        data['lq'].append(q('How much was the ticket?',f'{price.capitalize()} pounds.',['Two pounds.','Three pounds.','Four pounds.']) if group==1 else q('What are students going to do?',activity.capitalize()+'.',[x.capitalize()+'.' for x in ['plant flowers','sort paper','make bird posters']]))
    elif group==2:
        building=pick(['library','museum','school']);topic=pick(['planets','animals','trains']);colour=pick(['blue','green','red'])
        data['listen']=f'{name} was reading in the {building} when {friend} arrived. It was {time} o’clock. {friend} wanted a book about {topic}. A teacher showed them a {colour} book. They sat near the window. {name} left at {end}.'
        data['lq']=[q(f'Where was {name}?',f'In the {building}.',[f'In the {x}.' for x in ['library','museum','school']]),q(f'What book did {friend} want?',f'A book about {topic}.',[f'A book about {x}.' for x in ['planets','animals','trains']]),q(f'When did {name} leave?',f'At {end}.',['At two.','At three.','At four.']),q('What colour was the book?',colour.capitalize()+'.',['Blue.','Green.','Red.']),q('What time did the friend arrive?',f'At {time}.',['At nine.','At ten.','At eleven.']),q('Where did they sit?','Near the window.',['At the gate.','Under a tree.'])]
    else:
        kind=pick(['comedy','adventure film','cartoon']);site=pick(['school garden','library','town park'])
        data['listen']=f'Our film club has made a short {kind}. The film was written by {name} and directed by {friend}. It was filmed in the {site}. We are showing it on {day} at {end}. Tickets are free. You can bring a friend.'
        data['lq']=[q('Who directed the film?',friend+'.',['Leo.','Sam.','Alex.']),q('Where was it filmed?',f'In the {site}.',[f'In the {x}.' for x in ['school garden','library','town park']]),q('Which day is the show?',day+'.',['Monday.','Tuesday.','Wednesday.','Thursday.']),q('Who wrote the film?',name+'.',['Mia.','Eva.','Anna.','Nina.']),q('What time is the show?',f'At {end}.',['At two.','At three.','At four.']),q('What kind of film is it?',kind.capitalize()+'.',['Comedy.','Adventure film.','Cartoon.'])]
    if group==1:
        site=pick(['art museum','history museum','science museum']);transport=pick(['bus','train','coach']);gift=pick(['postcard','small book','poster'])
        data['read']=f'On {day}, {name} visited an {site}.' if site=='art museum' else f'On {day}, {name} visited a {site}.'
        data['read']+=f' She went with {friend}. They travelled by {transport}. They saw an exhibition and had lunch in the garden. The shop was open, so {name} bought a {gift} for her cousin. They did not visit the tower because it was closed. They enjoyed the quiet garden.'
        data['rq']=[q('How did the friends travel?',f'By {transport}.',['By bus.','By train.','By coach.']),q('Why did they not visit the tower?','It was closed.',['It was too expensive.','They lost the map.']),q('Who was the gift for?','Her cousin.',['Her teacher.','Her neighbour.']),q('What did she buy?',f'A {gift}.',[f'A {x}.' for x in ['postcard','small book','poster']]),q('Who went with her?',friend+'.',['Leo.','Sam.','Alex.']),q('Where did they have lunch?','In the garden.',['On the train.','In the tower.'])]
    elif group==2:
        obj=pick(['green notebook','blue bag','red pencil case','yellow folder']);helper=pick(['librarian','teacher','shop assistant','museum guide']);feature=pick(['park','school','market'])
        data['read']=f'Green Town has a library, a park and a small market. The library is opposite the {feature}. On {day}, {name} was walking to the library when she found a {obj}. She gave it to a {helper}. Later {friend} came to ask for it. He thanked {name}. She felt happy because the object was back with its owner.'
        data['rq']=[q('Where is the library?',f'Opposite the {feature}.',[f'Opposite the {x}.' for x in ['park','school','market']]),q('What did the girl find?',f'A {obj}.',[f'A {x}.' for x in ['green notebook','blue bag','red pencil case']]),q('Who received the object from her?',f'A {helper}.',[f'A {x}.' for x in ['librarian','teacher','shop assistant']]),q('Who asked for the object?',friend+'.',['Leo.','Sam.','Alex.']),q('Where was the girl going?','To the library.',['To the cinema.','To the airport.']),q('Why did she feel happy?','The owner had the object again.',['She won a prize.','She bought a new bag.'])]
    elif group==3:
        sport=pick(['tennis','hockey','football']);freq=pick(['twice','three times','once']);nextact=pick(['join a friendly match','try a different sport','help a new player'])
        data['read']=f'{name} joined a {sport} club last month. She practises {freq} a week. Her coach says that everyone should bring a water bottle. Last {day} the group played a friendly match. {name} did not win, but she enjoyed helping {friend}, a new player. Next month she is going to {nextact}. She likes the club because people help each other.'
        data['rq']=[q('How often does she practise?',freq.capitalize()+' a week.',['Twice a week.','Three times a week.','Once a week.']),q('What should players bring?','A water bottle.',['A camera.','A new bag.']),q('What did she enjoy?','Helping a new player.',['Winning a prize.','Buying a bottle.']),q('When did she join?','Last month.',['Last year.','Yesterday.']),q('What is she going to do next month?',nextact.capitalize()+'.',[x.capitalize()+'.' for x in ['join a friendly match','try a different sport','help a new player']]),q('Why does she like the club?','People help each other.',['There are no rules.','She always wins.'])]
    else:
        years=pick(['two','three','four']);site=pick(['town library','school garden','town park','music room']);song=pick(['Mia','Eva','Anna','Nina'])
        data['read']=f'The Green Stars are a fictional school band. They have played together for {years} years. Last week they performed in the {site}. Their new song was written by {song}. The audience liked the quiet music. A school magazine published an interview with the band. Next month the students are going to make a short music video.'
        data['rq']=[q('How long have they played together?',f'For {years} years.',['For two years.','For three years.','For four years.']),q('Where did they perform?',f'In the {site}.',[f'In the {x}.' for x in ['town library','school garden','town park']]),q('Who wrote the song?',song+'.',['Mia.','Eva.','Anna.']),q('What did the audience like?','The quiet music.',['The sports match.','The new shoes.']),q('What published the interview?','A school magazine.',['A travel guide.','A sports poster.']),q('What is their next plan?','Make a short music video.',['Leave the band.','Open a shop.'])]
    # Role constraints and writing details also vary by date and reserve, not only L/R.
    if group==1:
        target=pick(['museum','library','park']);later={'nine':'ten','ten':'eleven','eleven':'twelve'}[time]
        data['speaking']=f'A пропонує {target} о {time} у {day}. B може лише після {later}. Узгодьте місце, новий час і транспорт. По 3–4 репліки; дані вигадані.'
        data['ssample']=f'A: Would you like to visit the {target} on {day} at {time}? B: I can only come after {later}. A: Let’s meet at {later}, then. How can we get there? B: We can go by bus. A: Good idea. B: See you there.'
        data['writing']=f'Напиши 5–6 речень другові про вигадану минулу екскурсію у {day}: транспорт, дві події й враження. Використай Past Simple та because або so.'
        data['wsample']=f'Dear Sam, On {day} I visited a museum. I went there by bus. I saw an exhibition and had lunch in a garden. The tower was closed, so I bought a postcard. I enjoyed the day because I learnt new things. Alex'
    elif group==2:
        feature=pick(['park','art gallery','market','museum']);direction=pick(['Go straight on from the school.','Turn left at the school.','Turn right at the school.']);obj=pick(['book','notebook','bag'])
        data['speaking']=f'A — відвідувач, шукає бібліотеку. B пояснює: «{direction}», потім повз {feature}, бібліотека навпроти {feature}. A уточнює положення, B перевіряє розуміння. По 3–4 репліки; карта вигадана.'
        data['ssample']=f'A: Excuse me, how do I get to the library? B: {direction} Walk past the {feature}. A: Is the library opposite the {feature}? B: Yes, it is. Is that clear? A: Yes. Thank you. B: You’re welcome.'
        data['writing']=f'Напиши 5–6 речень про безпечну вигадану пригоду: герой загубив {obj} біля {feature}, а друг допоміг. Опиши фон, подію й завершення; ужий when або while.'
        data['wsample']=f'Mia was walking near the {feature}. She was carrying a {obj}. While she was looking at a map, she put it on a bench. Then she could not find it. Leo showed her the bench. She found her {obj} and thanked him.'
    elif group==3:
        later={'nine':'ten','ten':'eleven','eleven':'twelve'}[time]
        data['speaking']=f'A запрошує B на шкільну екоподію у {day} о {time} біля {place}; треба принести {item}. B має заняття до {later}. Запитайте про план, узгодьте пізнішу участь або ввічливо відмовте; по 3–4 репліки.'
        data['ssample']=f'A: Would you like to come to our garden event on {day}? B: What time does it start? A: At {time}, near the {place}. B: I have a class until {later}. Can I come later? A: Yes. Please bring a {item}. B: Great, I will come at {later}.'
        data['writing']=f'Напиши 5–6 речень із запрошенням на вигаданий екозахід у {day}: де, коли, два плани, одне правило та причина долучитися.'
        data['wsample']=f'Hi Mia, Would you like to come to our garden event on {day}? We are meeting near the {place} at {time}. We are going to plant flowers and make posters. You must bring a {item}. If we work together, we will help our school. Please write back. Alex'
    else:
        colour=pick(['blue','green','red','yellow']);size=pick(['M','L','XL']);cost=pick(['eight','ten','eleven']);item=pick(['T-shirt','jacket','shirt'])
        data['speaking']=f'A — покупець: потрібен {colour} {item}, розмір {size}, має 12 фунтів. B — продавець: потрібний товар {size} коштує {cost} фунтів; інший товар S замалий. Уточніть товар, розмір, ціну; ужийте too small / big enough і one. По 3–4 репліки.'
        data['ssample']=f'A: I would like a {colour} {item}, please. B: What size? A: {size}. This one is too small. B: The {colour} one is {size} and costs {cost} pounds. A: It is big enough. I will take it. B: Here you are.'
        movie=pick(['Garden Friends','The Music Room','A Day in Green Town','The Lost Notebook']);plot=pick(['a garden party','a music show','a school trip'])
        data['writing']=f'Напиши 5–6 речень про вигаданий фільм «{movie}» про {plot}: автор / режисер, зміст, що сподобалося й рекомендація. Ужийwho абоwhich іодну пасивну конструкцію.'
        data['wsample']=f'{movie} is a fictional comedy. It was directed by Mia. It is about a girl who organises {plot}. The story is kind and funny. I liked the bright colours. I would recommend it to my classmates.'
    return data


def recovery_material(l):
    data=assessment_data(l,True);diag=l['lesson_type']=='pair_diagnostic';skills=['L','R','S','W'] if diag else [l['section'].split('-')[-1]]
    hand=[f'# Резервний учнівський аркуш · 6 клас · урок {l["number"]:03d}',f'Планова тема: {l["topic"]}. Дата повторного контакту: __________', 'Видавати тільки на перенесенні / повторній перевірці, не для домашнього тренування до основної спроби. На аркуші немає відповідей і тексту слухання. Потрібні ті самі придатні умови, що для основного варіанта.']
    key=['## Резервний варіант — ключ учителя', 'Видайте recovery-handout.md тільки після визначення окремого слота. Не відкривайте цей ключ учням.']
    for skill in skills:
        hand+=['## '+skill]
        if skill=='L':key+=['Прихований текст резервного слухання (двічі): '+data['listen']]
        if skill=='R':hand+=[data['read']]
        if skill in ('L','R'):
            for i,(prompt,opts,ans) in enumerate(data['lq' if skill=='L' else 'rq'][:3 if diag else 6],1):
                rotated=list(enumerate(opts));offset=(l['number']+i+1)%len(opts);rotated=rotated[offset:]+rotated[:offset]
                hand+=[f'{i}. {prompt}',' / '.join(f'{chr(65+j)}) {o}' for j,(_,o) in enumerate(rotated)),'Відповідь: __________']
                letter=next(chr(65+j) for j,(old,o) in enumerate(rotated) if old==ans);key+=[f'Резерв {skill}{i}: {letter} — {opts[ans]}']
        else:
            hand+=[data['speaking' if skill=='S' else 'writing'],*['________________________________________________________________________']*8]
            # Adapted roles admit the primary model as a structure, not a literal answer.
            key+=['Резерв '+skill+': '+data['ssample' if skill=='S' else 'wsample']+' Допускаються інші відповіді за тими самими критеріями; змістові деталі мають відповідати саме резервному завданню.']
    return '\n\n'.join(hand),'\n\n'.join(key)


def assessment(l):
    n=l['number']; diag=l['lesson_type']=='pair_diagnostic'
    data=assessment_data(l)
    skills=['L','R','S','W'] if diag else [l['section'].split('-')[-1]]
    hand=[f'# Завдання: {data["setting"]}', 'Це запропонований матеріал перевірки, а не підтвердження її проведення. Працюй самостійно; перед початком учитель пояснить критерії. Якщо зв’язок зник або пролунала тривога, зупинись. Відсутній доказ перевірять іншого безпечного разу.']
    keys=[]
    for skill in skills:
        if skill in ('L','R'):
            hand += ['## '+('L — розуміння на слух' if skill=='L' else 'R — розуміння прочитаного')]
            if skill=='R': hand += [data['read']]
            else: hand += ['Прочитай запитання. Прослухай учителя двічі у звичайних безпечних умовах. Не потрібно повторювати вголос. Текст слухання міститься тільки в учительському ключі. Якщо не чути, повідом доступним способом; читання тексту не замінює перевірку слухання.']
            for i,(q,opts,ans) in enumerate(data['lq' if skill=='L' else 'rq'][:3 if diag else 6],1):
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
        activities=[('00–05','Пояснює навичку й критерії; добровільний вибір паузи.','Готує аркуш.','Факт доступності.'),('05–10',f'Пояснює процедуру {s}; відповідає на процедурні запитання без предметних підказок.','Читає умови / запитання.','План роботи.'),('10–25',action,'Виконує цільове завдання '+s+'.','Доказ '+s+' за наявності доступу.'),('25–35','Приймає завершені L/R роботи, решті дає тихо закінчити. Хто здав — обирає коротке неоцінюване читання з власної книжки / спокійний відпочинок без обговорення відповідей; для S слухає наступні пари.','Перевіряє / завершує роботу, для S чекає черги тихо.','Завершений продукт; ще не висновок про досягнення.'),('35–42','Збирає роботи / завершує доступні індивідуальні слоти S.','Здає продукт; неперевірену навичку переносить.','Список отриманих і відсутніх доказів.'),('42–45','Фіксує умови й домовляється про відсутні слоти.','Позначає потребу повторного контакту.','Незаповнений результат доповнюється тільки за фактом.')]
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

При тривозі роботу припинити. Зберегти лише вже отримані докази, якщо це не затримує безпечні дії. Не робити висновок «контроль успішно проведено» для всього класу. У report.md зазначити навичку, перервану частину, доступність і дату нового слота. Для L після частково почутого стимулу дати інший еквівалентний стимул та перевірити чутність; для S — новий усний слот; для R/W — вирішити, чи продовжити з тієї точки або надати рівноцінне завдання. Готовий рівноцінний резерв для тієї самої навички та вже вивченого мовного діапазону — recovery-handout.md; відповіді й прихований L-текст у key.md. Видавати резерв лише на окремому контакті; не роздавати його разом з основною спробою. Зміна варіанта фіксується. B/D не є завершенням формальної перевірки. Чат не доводить усне мовлення, читання стимулу не доводить аудіювання.

## Диференціація й оцінювання

Збільшений час, великий друк, окреме тихе місце й повторення процедурної інструкції — за потребою. Під час R не читати текст замість учня, під час L не показувати його; це змінить навичку і має бути позначено як інша діяльність. Допомогу у змісті зафіксувати, не представляти як незалежну роботу. Закриті завдання — по 1 робочому балу (у діагностиці L/R 0–3 окремо; на окремій семестровій перевірці відповідної навички 0–6); S/W — окремі аналітичні описи в ключі, не автоматична офіційна оцінка. Не виставляти нуль через відсутність доступу.

## Домашня робота

Нової контрольної роботи додому немає. Після отримання зворотного зв’язку — до 5 хв на одну правку або одну ціль на наступний раз. Невиконаний через переривання контроль проходить за погодженим графіком у придатних умовах.
'''
    lesson+='\n\n'+sel_teaching_note(l,game_adaptation(l,curate_adaptations({a['slug']:a for a in json.loads(SOURCE.read_text())['adaptations']})))+'\n\n'+NUSH_GROUP_NOTE
    return lesson,'\n\n'.join(hand),'\n\n'.join(keys)

RUBRIC='''## Рубрика відкритого продукту

Робоча аналітична рубрика, не офіційне переведення в 12 балів. За кожним критерієм: 0 — доказу ознаки немає у наданій роботі; 1 — частково; 2 — достатньо для сформульованого завдання. Критерії: (1) виконання змістового завдання; (2) зрозумілість і зв’язність; (3) доречні слова / форми. Для S додатково описово зафіксувати реакцію на партнера та зрозумілість усного мовлення; підказки / читання заготовки відмічати. Для W позначити самостійну правку. Сума 0–6 — лише внутрішня опора для зворотного зв’язку, не власна шкільна шкала й не запис до журналу. Ні почуття, ні участь у рефлексії до неї не входять. Відсутність доступу позначати «немає доказу», не нулем. Дозволені інші змістовні відповіді, вигадані персонажі й альтернативні рішення. Приклад зворотного зв’язку: «Ти назвав місце й час; наступний крок — додати причину з because».
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
- Мовні докази за групами:1 сприйняття ___;2 взаємодія ___;3 висловлення ___; достатність / підтримка: ___
- SEL запропоновано / пропущено (без оцінювання емоцій): __________
- Місце зупинки й конкретний наступний крок: _____________________
- Перенесено на дату / контакт; відповідальний: __________________
- Домашня робота фактично оголошена; скорочення навантаження: _____
- Потреба корекції плану: _______________________________________

Підпис / дата заповнення: ______________________________________
'''# New checking contexts; none of these two-card sets is copied from worksheet exercise 3.
GAME_CHECKS={
'hello-1':('Nora is eleven. She is Canadian. Her birthday is in April.',('Nora ___ eleven.',['is','are','am']),('When is Nora’s birthday?',['In April.','In May.','In June.'])),
'hello-2':('Tom has got a brother. His brother can sing. They eat lunch at quarter past one.',('What can the brother do?',['Sing.','Swim.','Draw.']),('What time is lunch?',['1:15.','1:30.','2:15.'])),
'hello-3':('Four books are on a chair. A red bag is behind the chair.',('How many books are there?',['Four.','Three.','Two.']),('Where is the bag?',['Behind the chair.','Under the chair.','On the books.'])),
'1a':('Nora has art on Friday. Her lessons finish at three.',('Nora ___ art on Friday.',['has','have','having']),('When do her lessons finish?',['At three.','At four.','At two.'])),
'1b':('Nora is wearing a red hat. She is looking at a map. Tom is sitting next to her.',('Nora ___ at a map now.',['is looking','looks every day','look']),('Who is sitting next to Nora?',['Tom.','Leo.','Eva.'])),
'1c':('Tom usually wears a cap. Today he is wearing a green scarf.',('Tom usually ___ a cap.',['wears','is wearing now','wear']),('Today he ___ a scarf.',['is wearing','wear every day','wears usually'])),
'1d':('Nora enjoys painting. She wants to try chess at a club.',('Nora enjoys ___.',['painting','to paint','paint']),('She wants ___ chess.',['to try','trying','tries'])),
'1e':('Tom is helpful. He has got straight hair. He and Nora play chess together.',('A question about Tom’s character is…',['What is he like?','What does he look like?','What colour is his hair?']),('What do Tom and Nora do together?',['Play chess.','Play hockey.','Sing in a band.'])),
'2a':('On Sunday Nora visited a gallery. She travelled by train and bought a poster.',('Nora ___ a gallery on Sunday.',['visited','visits','visiting']),('What did she buy?',['A poster.','A ticket for a play.','A camera.'])),
'2b':('At six, Tom could swim. His coach says that Tom swims carefully.',('At six Tom ___ swim.',['could','can now','cans']),('Tom is careful. He swims ___.',['carefully','careful','care'])),
'2c':('Nora has two tickets for Tom and Eva. She gives the tickets to them.',('These tickets are for Tom and Eva. They are for ___.',['them','they','their']),('Nora says, “Please give the bag to ___.”',['me','I','my'])),
'2d':('In this imaginary town, people used to walk to the island. Now they use a bridge.',('People ___ walk to the island.',['used to','use to yesterday','using to']),('Did they ___ use a bridge?',['use to','used to','using to'])),
'2e':('The class visited a gallery. It rained, so they stayed inside. They enjoyed the pictures.',('They stayed inside ___ it rained.',['because','so','and so because']),('It rained, ___ they stayed inside.',['so','because','but because'])),
'3a':('At six Nora was drawing. Tom and Eva were sorting pencils. Then a box fell; nobody was hurt.',('At six Nora ___ drawing.',['was','were','did']),('Tom and Eva ___ sorting pencils.',['were','was','is'])),
'3b':('Nora was drawing when a cat jumped onto the table. Tom was reading at the same time.',('Nora was drawing when the cat ___.',['jumped','was jump','jumps now']),('While Nora was drawing, Tom ___ reading.',['was','were','did'])),
'3c':('The imaginary park has some boats. It has no café.',('Are there ___ boats?',['any','no','a']),('The park has ___ café.',['no','any','some a'])),
'3d':('Someone left a red bag at the camp. Nobody knows its owner. Everyone is ready to ask the teacher.',('Everyone ___ ready.',['is','are','have']),('___ knows the owner.',['Nobody','Nothing','Nowhere'])),
'3e':('Nora lost her pen while she was reading. Luckily, her friend found it under a chair.',('Nora ___ reading when she lost her pen.',['was','were','does']),('___, her friend found it.',['Luckily','Unfortunately','Sadly'])),
'4a':('Nora is at a book desk. She wants a story and politely asks for help.',('Choose her request.',['Could you help me, please?','Could you to help me?','Could you helps me?']),('Choose a permission question.',['May I borrow this story?','May I borrowing this story?','May I borrowed this story?'])),
'4b':('Map: School — Café — Museum on one straight road. The museum is opposite a garden.',('From school to the museum:',['Go straight on past the café.','Go into the garden and stop.','Go back to school.']),('The museum faces the garden. It is ___ it.',['opposite','into','through'])),
'4c':('Imaginary places: Hill Village has 100 people. Oak Town has 900 people. Hill Village is quiet.',('Oak Town is ___ than Hill Village.',['bigger','biggest','big']),('Hill Village is ___ than Oak Town in this story.',['quieter','quietest','quiet'])),
'4d':('Imaginary planet data: A size2 / temperature10; B size4 / temperature20; C size6 / temperature30.',('Which is the largest?',['C.','B.','A.']),('B is ___ than A.',['hotter','hottest','hot'])),
'4e':('Oak Town has one gallery and three bridges. Nora thinks its garden is beautiful.',('There ___ three bridges.',['are','is','has']),('Which statement is an opinion?',['The garden is beautiful.','There are three bridges.','There is one gallery.'])),
'5a':('Nora has a plan to visit a computer shop. She has arranged to meet Tom at eleven.',('Nora is going to ___ a shop.',['visit','visiting','visited']),('She ___ meeting Tom at eleven.',['is','does','did'])),
'5b':('The imaginary company predicts smaller screens. Tom promises to help Nora choose one.',('The screens ___ be smaller, the company predicts.',['will','did','are yesterday']),('Tom says, “I ___ help you.”',['will','was','am yesterday'])),
'5c':('At the school paper station, sorting is required. Buying a new folder is optional.',('We ___ sort paper.',['must','must not','do not have to']),('We ___ buy a new folder.',['do not have to','must not','cannot ever'])),
'5d':('The imaginary town plans to protect its lake. Clean water will help local animals.',('If we ___ the lake, animals will have a safer home.',['protect','will protect','protected yesterday']),('If we protect it, animals ___ have cleaner water.',['will','did','were'])),
'5e':('Nora invites Tom to a garden event at the library at eleven on Saturday.',('Which detail belongs in the invitation?',['Library, Saturday, eleven.','Only Nora’s favourite colour.','Only a goodbye.']),('Choose a polite refusal.',['Thank you, but I cannot come.','You are wrong to invite me.','I must you not.'])),
'6a':('Imaginary lunch A: three carrots and a little rice. Lunch B: one carrot and a lot of rice.',('Lunch A has a ___ carrots.',['few','little','much']),('How ___ rice is in lunch B?',['much','many','few'])),
'6b':('In a fictional school story, Nora feels unwell. Tom offers to stay with her while they ask a teacher for help.',('Nora ___ tell an adult.',['should','should to','shoulding']),('What does Tom offer?',['Stay with Nora and ask a teacher.','Choose medicine.','Hide the problem.'])),
'6c':('Nora likes hockey. Tom can skate. They are answering a friendly interview.',('Nora likes hockey, ___?',['doesn’t she','isn’t she','did she']),('Tom can skate, ___?',['can’t he','doesn’t he','isn’t he'])),
'6d':('Oak Stars play basketball in Oak Town. Last year they won a school cup.',('Oak Stars ___ basketball every week.',['play','played yesterday','is play']),('Last year they ___ a cup.',['won','win','winning'])),
'6e':('Nora joined a hockey club last week. She practises twice a week. Next month she plans a friendly match.',('Nora ___ the club last week.',['joined','joins','join now']),('Next month she is going to ___ a match.',['play','played','playing'])),
'7a':('Nora has never been on TV. She has watched a musical twice.',('Nora ___ never been on TV.',['has','have','is']),('Have you ever ___ a musical?',['watched','watch','watching'])),
'7b':('Nora has seen a jazz band twice. She saw them on Friday. Tom has gone to the concert and is not back yet.',('Nora ___ the band on Friday.',['saw','has seen yesterday','seeing']),('Tom has ___ to the concert and is not back.',['gone','been','went'])),
'7c':('Nora has had Tom’s book since Monday. Today is Thursday. She will return it at four.',('She has had the book ___ Monday.',['since','for','ago']),('When will she return it?',['At four.','At six.','At noon.'])),
'7d':('Imaginary shop: red shoes size36; blue shoes size38. Nora needs38 and has15 pounds; the blue ones cost12 pounds.',('The red shoes are ___ small.',['too','enough','many']),('Nora says, “I will take the blue ___.”',['ones','one','it'])),
'7e':('Nora owns a red folder. Tom owns a blue bag. Nora asks for help finding her folder.',('The red folder is ___.',['hers','her','she']),('This is ___ bag; it belongs to him.',['Tom’s','Tom','Toms'])),
'8a':('Nora won an art prize. Her new camera takes clear pictures.',('Nora is the student ___ won the prize.',['who','which','where']),('Choose additional information.',['Nora, who won an art prize, is here.','Nora, which won an art prize, is here.','Nora that won an art prize, is here.'])),
'8b':('Two fictional actors discuss a school play. Nora is excited. Tom is excited too. Neither has performed here before.',('Nora: I am excited. Tom: ___ am I.',['So','Neither','Not']),('Nora: I haven’t performed here. Tom: Neither ___ I.',['have','do','am'])),
'8c':('The club makes a newsletter. Students write articles. A teacher checks every page.',('Articles ___ written by students.',['are','is','do']),('Every page is ___ by a teacher.',['checked','check','checking'])),
'8d':('At the fictional ceremony, a cartoon was shown. Three awards were given to young actors.',('A cartoon ___ shown.',['was','were','did']),('Three awards ___ given.',['were','was','is'])),
'8e':('River Friends is a fictional comedy. It was directed by Nora. It tells the story of a girl who helps a lost dog.',('It was ___ by Nora.',['directed','direct','directing']),('It is about a girl ___ helps a dog.',['who','which','when'])),
'culture-1':('A fictional town has yellow buses with two levels. They travel along Oak Street. Boats use the canal.',('How many levels do the buses have?',['Two.','Three.','One.']),('Where do the buses travel?',['Along Oak Street.','Along the canal.','Under the lake.'])),
'song-1':('In an original mini-story, Nora skates in the morning. After school she draws a skateboard poster.',('When does Nora skate?',['In the morning.','At midnight.','After lunch.']),('What does she do after school?',['Draws a poster.','Takes a flight.','Visits a museum.'])),
'culture-2':('Nora’s guide lists Edinburgh as Scotland’s capital. It labels a picture “bagpipes: traditional musical instrument”.',('Which capital is listed?',['Edinburgh.','Kyiv.','London.']),('What are bagpipes in the guide?',['A musical instrument.','A boat.','A food.'])),
'song-2':('In an original mini-story, Tom missed a train. He walked to the library and found a friend there. Luckily, the friend had his book.',('What did Tom miss?',['A train.','A boat.','A lesson.']),('Choose the ending word.',['Luckily.','Unfortunately.','Sadly.'])),
'culture-3':('Imaginary Green Park has a lake and a path. Blue Park has a path and a stage. Both parks have trees.',('What do both parks have?',['A path and trees.','A lake.','A stage.']),('Which park has a stage?',['Blue Park.','Green Park.','Neither park.'])),
'song-3':('In an original eco-poster, Nora suggests saving water. Tom suggests sorting paper. They both want less rubbish.',('What does Tom suggest?',['Sorting paper.','Buying more plastic.','Dropping rubbish.']),('If they sort paper, they ___ reduce rubbish.',['will','did','were'])),
'culture-4':('A fictional musical called River Cats is set near a river. Nora wrote its music. Tom designed blue costumes.',('Who wrote the music?',['Nora.','Tom.','Leo.']),('Which opinion gives a reason?',['I liked the costumes because they were colourful.','There are costumes.','It is a musical.'])),
'song-4':('In an original story, singer Nora wins a school award. She plans to record a new song next month.',('What has Nora won?',['A school award.','A train ticket.','A sports cup.']),('What is her next plan?',['Record a new song.','Buy a library.','Leave music.'])),
'culture-ukraine-1':('In a fictional family, Nora helps make vegetable soup on Sunday. The soup contains beetroot and carrots.',('When do they make the soup?',['On Sunday.','On Friday.','On Monday.']),('Which ingredient is named?',['Carrots.','Coffee.','Rice only.'])),
'culture-ukraine-2':('A fictional city guide offers a museum for history fans, a gallery for art fans and a park for walkers.',('Where should an art fan go?',['To the gallery.','To the museum.','To the airport.']),('Where should a walker go?',['To the park.','To the bank.','To the airport.'])),
'clil-history':('A fictional polar team left camp on Monday. They reached Hill Camp on Tuesday and put up a red flag on Wednesday.',('What happened first?',['The team left camp.','They put up a flag.','They reached Hill Camp.']),('When was the flag put up?',['On Wednesday.','On Monday.','On Tuesday.'])),
'clil-geography':('Imaginary Oakland: capital Pine City; largest city River City; climate cool and wet; currency oak coins.',('Which is the largest city?',['River City.','Pine City.','Oakland.']),('What is the currency?',['Oak coins.','Pounds.','Dollars.'])),
'clil-sport':('At a fictional hockey lesson, Nora wears a helmet. Tom moves a puck with a stick. Eva checks the rules as referee.',('Who is the referee?',['Eva.','Nora.','Tom.']),('What does Tom use to move the puck?',['A stick.','A helmet.','A book.'])),
'clil-music':('Nora has a flute, Tom has a violin and Eva has a drum.',('Who has a string instrument?',['Tom.','Nora.','Eva.']),('Who has a wind instrument?',['Nora.','Tom.','Eva.'])),
'learning-tips':('Nora’s portfolio has a first draft and a revised draft. She changed go to went because the story happened yesterday.',('Which version shows the improvement?',['The revised draft.','Only the title.','Only a blank page.']),('Why did she use went?',['The event happened yesterday.','The event is a daily routine.','The event is tomorrow.']))}

CHANGED_MODELS={
'hello-1':'My name is Nora. I am Canadian.','hello-2':'We have breakfast at quarter past eight.','hello-3':'There are three boxes under the desk.',
'1a':'Our school starts at ten.','1b':'Mia is reading a map.','1c':'Today I am wearing a red shirt.','1d':'I enjoy playing basketball.','1e':'My friend Nora has got straight hair.',
'2a':'We went to a gallery.','2b':'Tom drives slowly.','2c':'These tickets are for them.','2d':'People used to travel on slow trains.','2e':'We were hungry, so we had lunch.',
'3a':'Nora was reading at six.','3b':'While we were drawing, we heard a cat.','3c':'There are some boats.','3d':'Someone is at the library door.','3e':'Luckily, my aunt found the key.',
'4a':'May I borrow this map?','4b':'Turn left at the school.','4c':'The village is smaller than the town.','4d':'Planet B is smaller than planet C.','4e':'There are three galleries in Oak Town.',
'5a':'I am going to buy a printer.','5b':'I think screens will use less energy.','5c':'We do not have to buy new folders.','5d':'If we protect the lake, animals will have a safer home.','5e':'Would you like to come to our garden event?',
'6a':'There are a few carrots.','6b':'Nora should ask a teacher for help.','6c':'Nora likes hockey, doesn’t she?','6d':'Last year Oak Stars won a school cup.','6e':'I joined a hockey club last month.',
'7a':'Have you ever visited a gallery?','7b':'I saw the band on Friday.','7c':'I have had this book for three days.','7d':'These trousers are too small.','7e':'The blue bag is Tom’s. It is his.',
'8a':'Nora is the girl who won the art prize.','8b':'I am excited. So am I.','8c':'The pages are checked by a teacher.','8d':'Three awards were given.','8e':'It is about a girl who helps a dog.',
'culture-1':'This imaginary bus has three levels.','song-1':'I go to the skatepark in the afternoon.','culture-2':'Our imaginary town has an old castle.','song-2':'I missed a train yesterday.','culture-3':'Both imaginary parks have a stage.','song-3':'If we sort paper, we will reduce rubbish.','culture-4':'The costumes were designed by Tom.','song-4':'The singer is going to record a new song.','culture-ukraine-1':'This imaginary soup contains carrots.','culture-ukraine-2':'If you enjoy art, you should visit the gallery.','clil-history':'The team reached Hill Camp on Tuesday.','clil-geography':'The imaginary capital is near a lake.','clil-sport':'A stick is used to move this red puck.','clil-music':'Tom has a violin. He plays a string instrument.','learning-tips':'First I revise my draft. Then I check the spelling.'}


def checking_context(a):
    code=a['code']
    if code.startswith('round-up-'):code=code[-1]+'a'
    text,q1,q2=GAME_CHECKS[code]
    qs=[]
    for prompt,options in (q1,q2):
        correct=options[0]
        qs.append(question(prompt,options,'Паралельний контекст: '+text+' Правильний вибір: '+correct))
    return text,*qs


def changed_model(a):
    code=a['code']
    if code.startswith('round-up-'):code=code[-1]+'a'
    return CHANGED_MODELS[code]


GAME_CONTEXTS={
'hello-1':('Бюро знайомств персонажів','секретар вигаданого мовного клубу','Зареєструй Mia й Leo, не переплутавши країну, be і дату.','дві порожні клубні картки','дві картки прийнято до клубного реєстру'),
'hello-2':('Сімейний календар героїв','організатор зустрічі вигаданої сім’ї','Узгодь час сніданку й можливу спільну активність через have got / can.','годинник і дві картки вмінь','зустріч має час і доступне заняття'),
'hello-3':('Загублена коробка','помічник бібліотекаря','Розмісти коробки й книжки так, щоб англійський опис збігався з планом.','схема столу, полиці й дві коробки','коробки знайдені за описом місця й кількості'),
'1a':('Розклад Green School','диспетчер шкільного дня','Відкрий кабінети в правильний час і перевір розклад / звички учнів.','дві неперевірені картки шкільного розкладу','обидві картки можна опублікувати'),
'1b':('Пошук ігрового персонажа','оператор вигаданої онлайн-гри','Знайди потрібного гравця за волоссям, одягом і дією зараз.','два схожі аватари на папері','обрано аватар з brown hair near a tree'),
'1c':('Майстерня нового дизайну','дизайнер одягу для аватара','Розрізни звичний одяг і дію сьогодні, щоб обрати картку дизайну.','джинси для переробки й два мовні ярлики','ярлики usually / today розміщені правильно'),
'1d':('Молодіжний клуб','координатор клубних активностей','Підбери заняття та ввічливе запрошення, не плутаючи enjoy doing / would like to.','два вільні місця в уявному клубі','для обох місць є зрозумілі запрошення'),
'1e':('Клубний профіль друга','редактор профілів вигаданих героїв','Склади нейтральний опис характеру й спільного заняття.','профіль без двох речень','профіль зрозумілий і без оцінювання зовнішності дітей'),
'2a':('Архів канікул','архіваріус вигаданих подорожей','Віднови події завершеної поїздки через Past Simple.','два порожні підписи до уявних фото','події й підписи збігаються'),
'2b':('Транспортна довідка','помічник пасажира','Перевір спосіб пересування й опис дії: could / прислівник.','пасажир не може обрати правильну мовну довідку','пасажир має два зрозумілі пояснення'),
'2c':('Стійка підготовки до рейсу','помічник вигаданих мандрівників','Передай квитки потрібній особі, уживаючи us / him / me / them.','квитки без адресата і два повідомлення','обидва повідомлення мають правильного адресата'),
'2d':('Музей транспорту','куратор порівняльної виставки','Підпиши транспорт колись і тепер через used to / didn’t use to.','два експонати без часових ярликів','відвідувач бачить відмінність then / now'),
'2e':('Поштова скринька екскурсії','автор листа про шкільну поїздку','Поєднай події з причинами й наслідками: because / so / but.','два розірвані повідомлення про музей','обидва повідомлення мають зрозумілий зв’язок'),
'3a':('Садова команда','координатор героїв шкільного саду','Віднови, що робили троє героїв, коли впала коробка; без травм.','три герої, коробка й картки дій у минулому','дії описано через was / were + ing'),
'3b':('Детектив слідів','дослідник вигаданої таємниці','Відокрем фон і коротку подію через while / when.','два записи про сліди й шум','історія має зрозумілу послідовність'),
'3c':('Довідка парку розваг','черговий уявного парку','Поясни, що є і чого немає: some / any / no.','дві заплутані таблички атракціонів','таблички не обіцяють відсутніх речей'),
'3d':('Лісова пошта White Fang','помічник героя авторської безпечної історії','Уточни, чи хтось повернувся й чи є щось поїсти, через someone / nobody / something.','герої чекають друга біля табору','повідомлення передає повернення друга й полегшення'),
'3e':('Сусідська допомога','автор безпечної історії про ключі','Поясни подію та допомогу тітки без небезпечного проникнення.','двері зачинилися, ключі всередині','історія завершується допомогою дорослого'),
'4a':('Бібліотечна стійка','відвідувач і бібліотекар','Отримай потрібну довідку ввічливим проханням may / could / can.','дві незавершені бібліотечні репліки','прохання зрозумілі й мають доречну форму'),
'4b':('Навігатор умовного міста','автор паперового маршруту','Проведи персонажа до бібліотеки через конкретні прийменники й команди.','вигадана мапа: School — Park — Library на прямій вулиці','персонаж дістається бібліотеки без реальних адрес'),
'4c':('Агенція вибору місця','консультант уявних місць','Порівняй село й місто, не підміняючи переваги людини оцінкою дітей.','два профілі місць','для вибору наведено порівняння та причину'),
'4d':('Лабораторія трьох планет','куратор вигаданого космічного атласу','Порівняй планети A / B / C: розмір 3 / 5 / 8 умовних одиниць.','таблиця A=3, B=5, C=8','підписано largest / bigger than без вигаданих наукових фактів'),
'4e':('Міський путівник','редактор Green Town','Створи зрозумілу довідку: місця, думка й слова-замінники.','дві картки пам’яток без опису','відвідувач може обрати місце за інтересом'),
'5a':('Планувальник техноярмарку','помічник двох друзів','Розрізни намір going to й домовленість meeting at ten.','незавершений план суботи','місце зустрічі й наміри зрозумілі'),
'5b':('Майстерня майбутніх гаджетів','автор прогнозів для уявного ярмарку','Підпиши прогноз і обіцянку через will; advanced Future Progressive не потрібен.','два ескізи пристроїв без прогнозів','обидва ескізи мають зрозумілий прогноз / обіцянку'),
'5c':('Сортувальна станція','консультант шкільного екопункту','Розрізни заборону, обов’язок і необов’язковість: mustn’t / must / don’t have to.','дві таблички правил для паперу й пляшок','правила не плутають заборону з вибором'),
'5d':('Заповідник річки','планувальник захисту середовища','Обери умовний план if + Present, will + verb.','картки чистої / забрудненої річки','наслідок плану сформульовано через if'),
'5e':('Організатор екоподії','секретар вигаданого молодіжного клубу','Надішли запрошення з часом / місцем і прийми відповідь.','два непрочитані запрошення','є ввічлива згода або відмова без тиску'),
'6a':('Меню вигаданого кафе','редактор нейтральних меню','Розподіли many / much / a few / a little між злічуваними й незлічуваними назвами.','два меню з carrots / rice / milk','підписи кількості граматично доречні; тіла й раціон дітей не оцінюються'),
'6b':('Служба звернення по допомогу','помічник вигаданого персонажа','Передай повідомлення дорослому й загальну пораду should без діагнозу й лікування.','Mia чекає Leo в шкільній бібліотеці; Leo почувається недобре','герой просить учителя / відповідального дорослого про допомогу'),
'6c':('Інтерв’ю спортивного клубу','автор доброзичливого інтерв’ю','Перевір здогадки через question tags і справжні відповіді персонажів.','два неповні запитання до інструктора','питання мають узгоджений auxiliary і займенник'),
'6d':('Пресслужба Green Stars','автор довідки про вигадану команду','Розрізни регулярні матчі й минулий виграш через Present / Past Simple.','дві картки командних новин','є факт про команду зараз і досягнення в минулому'),
'6e':('Спортивна пошта','автор новини другові','Повідом про початок заняття, частоту й наступний план.','чернетка листа про тенісний клуб','лист розрізняє joined / practise / am going to'),
'7a':('Телевікторина досвіду','ведучий вигаданої передачі','Запитай про досвід через Have you ever…? без вимоги реальних зізнань.','два питання для персонажів','досвід відокремлено від завершеного часу'),
'7b':('Музичний архів','редактор концертних спогадів персонажа','Розрізни загальний досвід і конкретний last summer.','два музичні повідомлення без правильного часу','загальний досвід і дата не суперечать формі'),
'7c':('Бюро записок','координатор повернення позиченої речі','Укажи тривалість for / since і зрозумілий час повернення.','дві записки про книжку й зміну планів','одержувач знає, хто взяв річ і коли поверне'),
'7d':('Крамниця для сцени','покупець / продавець уявного одягу','Знайди товар відповідного розміру через too / enough / one / ones.','T-shirt S=8 pounds; M=10 pounds; покупець має 12 pounds','товар підходить і ціна не перевищує бюджет'),
'7e':('Загублений зошит','черговий бюро речей','Уточни власника my / mine / her / hers / Mia’s і дай одну доброзичливу пораду.','Mia’s notebook і Leo’s book без власників на полиці','речі передано правильним власникам'),
'8a':('Шкільна новинна редакція','редактор вигаданого заголовка','Ідентифікуй героя через who і предмет через which; додаткові дані відокрем комами.','дві новини без зв’язку між героєм і подією','новину можна зрозуміти без запитання «хто саме?»'),
'8b':('Репетиційна команда','партнер вигаданого музиканта','Відгукнися на почуття / досвід через So / Neither + auxiliary.','два повідомлення перед виступом','обидва герої одержали доречну відповідь без примусу виступати'),
'8c':('Шкільна друкарня','редактор процесу створення журналу','Передай замовлення на етап checked / printed / delivered у Present Passive.','два мовні ярлики процесу без auxiliary','журнал проходить перевірку й друк за правильними підписами'),
'8d':('Уявна церемонія','архіваріус шкільних нагород','Зафіксуй уже проведені shown / chosen / given через was / were.','два записи про минулу церемонію','підписи нагород у Past Simple Passive'),
'8e':('Кіноклуб рецензентів','рецензент вигаданого фільму','Відокрем сюжет, soundtrack і власну оцінку; використай who / passive.','дві короткі заявки до кіноклубу','глядач розуміє сюжет і причину рекомендації')}


def game_adaptation(l,ads):
    if l['lesson_type'] in ('pair_diagnostic','semester_check'):
        group={28:2,53:4,86:6,115:8}.get(l['number'],4 if l['semester']==1 else 8)
        return ads[f'sb-{group}e']
    return choose(l,ads)[0]


def games(l,ads):
    a=copy.deepcopy(game_adaptation(l,ads));code=a['code'];special=l['lesson_type'] in ('reflection','portfolio')
    if code.startswith('round-up-'):
        module=code[-1];ctx=('Модульна місія '+module,'редактор п’яти мовних станцій','Пройди дві різні станції модуля й узгодь один спільний текст.','п’ять станцій '+', '.join(module+x for x in 'abcde'),'виправлено дві форми різних підтем')
    elif code in GAME_CONTEXTS:ctx=GAME_CONTEXTS[code]
    else:ctx=('Культурна експедиція: '+a['title'],'куратор текстового мінімузею','Відбери підтверджені факти про '+a['title']+'; реальні спогади й інтернет не потрібні.','дві порожні етикетки до стенду '+a['title'],'на стенді два підтверджені мовні рішення')
    title,role,goal,state,success=ctx
    if special:
        title='Редакційна майстерня' if l['lesson_type']=='reflection' else 'Куратор портфоліо'
        goal='Покажи одну правку «до / після» й поясни вибір через правило.' if l['lesson_type']=='reflection' else 'Обери два міні-зразки й обґрунтуй одну правку та наступний крок.'
    if l['lesson_type']=='module_intro':
        vocab=a['vocabulary']
        a['questions']=[question(f'Обери переклад: {w}',[u]+[u2 for w2,u2 in vocab if u2!=u][:2],f'{w} — {u}.') for w,u in vocab[:2]]+a['questions'][-2:]
    if l['number'] in STARTERS:
        a['questions']+= {1:[question('What nationality is Leo?',['Polish.','Ukrainian.','British.'],'Her friend Leo is Polish.'),question('What day is it in the story?',['Tuesday.','Monday.','Friday.'],'It is Tuesday today.')],2:[question('Who has got a sister called Eva?',['Leo.','Mia.','A teacher.'],'Leo has got a sister, Eva.'),question('When does the cousin visit?',['At8:15.','At7:30.','At8:30.'],'Quarter past eight =8:15.')],3:[question('Where is the bag?',['Next to the desk.','Under the shelf.','In a box.'],'One bag is next to the desk.'),question('What is between two pens?',['A pencil.','A bag.','A box.'],'A pencil is between two pens.')]}[l['number']]
    q1,q2=a['questions'][0],a['questions'][1]
    # Checking mission uses two different cards, not the teaching rehearsal.
    formal=l['lesson_type'] in ('pair_diagnostic','semester_check')
    all_blocks=choose(l,ads) if not formal else [a]
    check_a=all_blocks[1] if len(all_blocks)>1 else a
    if l['lesson_type']=='reflection':check_a=ads['sb-8c']
    check_text,q3,q4=checking_context(check_a)
    check_title=check_a['title']
    if l['lesson_type']=='module_intro':
        intro_checks={58:('At the imaginary club: keyboard = computer equipment; paper bin = place for paper.',('Which item belongs with a computer?',['A keyboard.','A paper bin.','A suitcase.']),('Where does paper go?',['In the paper bin.','In the keyboard.','In a suitcase.'])),73:('Imaginary labels: milk and rice = food; tennis and hockey = sports.',('Which word names a sport?',['Hockey.','Milk.','Rice.']),('Which word names food?',['Rice.','Tennis.','Hockey.'])),87:('Imaginary labels: cartoon and news = TV programmes; skirt and jacket = clothes.',('Which is a TV programme?',['Cartoon.','Skirt.','Jacket.']),('Which word names clothes?',['Jacket.','News.','Cartoon.'])),102:('A fictional poster shows Nora, an actor, and Tom, a reporter. Nora performs in a film. Tom writes news.',('Who writes news?',['Tom.','Nora.','Both of them.']),('What does Nora do?',['Performs in a film.','Writes news.','Sells tickets.']))}
        check_text,z1,z2=intro_checks[l['number']]
        q3=question(z1[0],z1[1],check_text)
        q4=question(z2[0],z2[1],check_text)
    # Independent contexts remain parallel on successive calendar dates.
    replacements={'Nora':['Iris','Lena','Maya','Rita','Sara'][l['number']%5],'Tom':['Noah','Ben','Max','Dan'][l['number']%4]}
    def contextualize(value):
        for old,new in replacements.items():value=re.sub(r'\b'+old+r'\b',new,value)
        return value
    check_text=contextualize(check_text)
    for q in (q3,q4):
        q['prompt']=contextualize(q['prompt']);q['choices']=[contextualize(x) for x in q['choices']];q['why']=contextualize(q['why'])
    for round_index,q in enumerate((q1,q2,q3,q4),1):
        indexed=list(enumerate(q['choices']));offset=(l['number']+round_index)%len(indexed)
        indexed=indexed[offset:]+indexed[:offset];old_answer=q['answer']
        q['choices']=[value for _,value in indexed]
        q['answer']=next(i for i,(old,value) in enumerate(indexed) if old==old_answer)
    def card(q):return f'“{q["prompt"]}”\n\n'+' / '.join(f'{chr(65+i)}) {v}' for i,v in enumerate(q['choices']))
    def solution(q):return f'{chr(65+q["answer"])} — “{q["choices"][q["answer"]]}”. Підстава: {q["why"]}'
    formal=l['lesson_type'] in ('pair_diagnostic','semester_check')
    timing='На цій контрольній даті обидві гри — після зданої незалежної спроби, замість залишку звичайної практики або на окремому контакті. Їх не запускають перед / під час основного чи резервного контролю. Результат гри не є результатом L/S/R/W контрольної; ігрова роздатка не містить контрольних стимулів.' if formal else 'Обрати одну гру замість звичайної практики: гра1 займає 20–28 A (або 16–24 C); гра2 займає 37–42 A (або 36–41 C). Якщо обрано гру1 на продуктивному уроці, її короткий продукт замінює відповідну частину вправи4; не вимагати додаткового повного твору. Разом із заміненим блоком загальна тривалість залишається45хв. Обидві гри одночасно не обов’язкові.'
    text=f'''# Ігрові симуляції · 6 клас · урок {l['number']:03d}

Планова дата: {l['date']}. Тема: {l['topic']}. Мовний матеріал: {a['title']}; фокус: {'; '.join(l['language_inventory']['grammar']) or 'тематична лексика й зв’язне повідомлення'}.

{timing}

Спільна доступність: усі ролі й дані вигадані. Камера необов’язкова. У команді A приймає рішення, B перевіряє джерело, потім ролі міняються; соло учень веде обидві ролі на папері. У чаті пишуть «хід1 + відповідь», учитель відповідає станом; це письмова взаємодія. В укритті — тільки за дозволу після переміщення й прийнятних умов, мовчки: обвести вибір, провести стрілку до наступного стану. Можна пропустити гру або грати без рейтингу. За відсутності умов — пауза; під час переміщення завдань немає. Усний доказ — тільки фактично почута репліка у придатних умовах; чат / папір не зараховуються як говоріння. Для контрольних L паперова гра тренує читання / мовний матеріал; аудіювання перевіряють окремо зі звуком.

## 1. Засвоєння, 7 хв — {title}

Роль: {role}. Мета: {goal}

Стартовий стан: {state}; два рішення ще не прийнято, стан0/2. Ресурси на папері нижче: текст, дві картки й модель. Учитель: “You can use the model. Choose, check and try again.”

Модель: {a['example']}

Матеріал стану (можна читати й підкреслювати): {a['reading']}

Картка ходу1:

{card(q1)}

Картка ходу2:

{card(q2)}

00–01: учень бере роль і читає ціль. 01–03: обирає варіант ходу1 й каже / пише “I choose…” + потрібну форму або відповідь. Правильне рішення → стан1/2, перша картка прийнята. Інше рішення → картка повертається на виправлення, стан0/2; жодної втрати оцінки.

03–05: учень робить хід2; партнер питає “Why this one?” Потрібен один змістовий доказ або посилання на правило. Правильне рішення → стан2/2. 05–07: учень змінює одну деталь мовної моделі (герой, предмет, час у дозволеній структурі) та перевіряє, чи не змінився сенс форми. Стан успіху: {success}; одна власна тематична зміна зрозуміла.

Відповіді для вчителя: хід1 — {solution(q1)} Хід2 — {solution(q2)} Допустимий приклад зі зміненою деталлю: {changed_model(a)}; інші приклади прийнятні, якщо зберігають цільову структуру й тематичний сенс.

Помилка → підказка → повтор: учитель не називає літеру; пропонує “Check the model” і вказує потрібну форму / факт. Учень змінює рішення й пояснює одну причину. Спостережуваний доказ засвоєння: два виправлені рішення та одна власна зміна. Позначити, що опора була доступна; не подавати це як незалежну контрольну спробу.

## 2. Перевірка, 5 хв — Нова ситуація «{check_title}»

Роль: незалежний перевіряльник двох нових заявок за ракурсом «{check_title}» цієї календарної теми. Старт: у черзі дві заявки, статус «не перевірено». Ціль — прийняти тільки обґрунтовані мовні / змістові рішення й виправити одну неточність до відправлення. Модель та ключ на першій спробі закриті.

Окремий паралельний контекст для перевірки (це не вправа3 аркуша; мовні форми пояснюють правилом):

{check_text}

Заявка1:

{card(q3)}

Заявка2:

{card(q4)}

00–01: учень читає дві заявки. Обирає дію «check first» або «send now»; без обґрунтування одразу відправлена заявка повертається як «потрібен доказ», її не зараховують як правильний мовний результат. 01–03: перевіряє заявку1, обирає мовний варіант і додає факт / правило: “My evidence is…”; за правильного рішення статус «готово1/2». 03–04: перевіряє заявку2, записує відповідь і доказ, статус «готово2/2». 04–05: показує / надсилає обидва рішення. Стан успіху — два змістовно правильні самостійні рішення з доречним доказом; жодного заліку за сам факт кліку / відправлення.

Ключ для вчителя (учням не показувати до першої спроби): заявка1 — {solution(q3)} Заявка2 — {solution(q4)} Робочий запис: «2/2 самостійно», «1/2 самостійно» або «потрібен наступний приклад»; це формувальна перевірка двох ознак, не повний висновок про урок і не офіційна оцінка.

Якщо помилка: спочатку зберегти першу відповідь як самостійний доказ. Тільки потім відкрити відповідний рядок тексту / модель; учень повторює хід іншою позначкою. Успіх після підказки записують окремо «із підтримкою», не переписують первинний результат. Спостережуваний мовний доказ: конкретні відповіді до двох заявок плюс дві підстави; у чаті це письмовий доказ. Для сильнішого учня замість вибору — закрити варіанти й сформулювати відповідь самостійно у тому самому часі.
'''
    learn_sel=sel_profile(l,a,'learn');check_sel=sel_profile(l,check_a,'check')
    text+='\n\n## Необов’язкова рефлексія навички\n\nГра1: '+learn_sel['focus']+'. Дія перед вибором: '+learn_sel['action']+' У 06–07 хв заміни одне повторення на запитання: '+learn_sel['prompt']+'\n\nГра2: '+check_sel['focus']+'. У 04–05 хв після фіксації перших самостійних рішень запропонуй: '+check_sel['prompt']+'\n\nПочуття, готовність до розмови й відповіді на рефлексію не оцінюють. Не вимагати швидкого натискання, контакту очима, камери чи особистої історії. Соло є репетицією соціальної взаємодії; письмовий вибір не є доказом слухання або говоріння. Джерельна основа адаптацій — SEL_NUSH_REVIEW.md; це не офіційні вправи «Зерна».\n'
    if special:text+='\n\nНа цій даті кінцевий ігровий продукт — також один рядок «До: ___ / Після: ___ / Why: ___». Для портфоліо додайте «Next time I will…». Це замінює спеціальний блок, а не додається до нього.\n'
    return text

# Author adaptations informed by the official EASEL Ukrainian electronic set.
# These are not reproductions or renamed official Kernels; references are kept
# in SEL_NUSH_REVIEW.md, outside student-facing data.
def sel_profile(lesson, adaptation, mode='learn'):
    code=adaptation['code'];topic=adaptation['title']
    if code.startswith('round-up-'):code=code[-1]+'a'
    anchors={
        'hello-1':'ім’я, країна й місяць народження вигаданого героя',
        'hello-2':'родич, його вміння й час зустрічі',
        'hello-3':'кількість речей і їхнє місце на схемі',
        '1a':'час початку занять і предмет у розкладі',
        '1b':'опис аватара й дія, яку він виконує зараз',
        '1c':'різниця між звичним одягом і тим, що персонаж носить сьогодні',
        '1d':'два різні клубні захоплення вигаданих друзів',
        '1e':'різні інтереси друзів і їхня спільна справа',
        '2a':'маркер минулого часу й послідовність поїздки',
        '2b':'спосіб пересування та умови маршруту',
        '2c':'кому передають квитки й сумку',
        '2d':'ознаки транспорту колись і тепер',
        '2e':'події екскурсії, причина й результат',
        '3a':'допомога герою після падіння коробки',
        '3b':'дві можливі реакції персонажа на незнайомий шум',
        '3c':'наявні й відсутні речі у вигаданому парку',
        '3d':'почуття героя біля табору й підстава для припущення',
        '3e':'вчинок сусіда чи друга, який допомагає з ключем або загубленою річчю',
        '4a':'ввічливе прохання й відповідь у бібліотеці',
        '4b':'місце початку, поворот і орієнтир на умовній мапі',
        '4c':'різні потреби того, хто обирає місто, і того, хто обирає село',
        '4d':'розмір планети й дані, на яких ґрунтується порівняння',
        '4e':'відмінні інтереси відвідувачів вигаданого міста',
        '5a':'намір, час і місце домовленої зустрічі',
        '5b':'відмінність перевіреного факту від прогнозу про гаджет',
        '5c':'обов’язок, заборона й необов’язкова дія на екостанції',
        '5d':'умова природоохоронного плану та її можливий наслідок',
        '5e':'дата, місце й згода або відмова на запрошення',
        '6a':'назва продукту й одиниця кількості у вигаданому меню',
        '6b':'прохання вигаданого учня про допомогу відповідального дорослого',
        '6c':'твердження про спортивний інтерес і справжня відповідь персонажа',
        '6d':'різні причини підтримувати вигадану спортивну команду',
        '6e':'коли почалося заняття, як часто воно відбувається й наступний план',
        '7a':'що точно відомо про досвід персонажа, а що не вказано',
        '7b':'різні музичні вподобання й конкретна концертна подія',
        '7c':'хто позичив річ, від якого часу й коли поверне',
        '7d':'колір, розмір і ціна вигаданого замовлення',
        '7e':'власник речі й доброзичлива порада, яка не звинувачує іншого',
        '8a':'джерельний факт новини й додаткова інформація про героя',
        '8b':'можливе хвилювання або радість вигаданих учасників виступу',
        '8c':'хто створює, перевіряє й передає сторінки журналу',
        '8d':'подія, учасники й час у записі вигаданої церемонії',
        '8e':'відмінні думки двох вигаданих глядачів про фільм',
        'learning-tips':'перша версія, правка й наступний крок власного навчального зразка',
    }
    anchor=anchors.get(code,'підтверджений факт і припущення в темі '+topic)
    if code in ('hello-2','hello-3','2c','4b','7c','7d'):
        domain='когнітивні навички: оперативна пам’ять і планування'
        focus='Утримую важливі умови'
        action='Перед вибором відміть дві важливі деталі умови «'+anchor+'». Спробуй подумки їх відтворити, потім звір. Можна весь час користуватися записом.'
        reflection='Який спосіб — короткий запис, повторення чи схема — допоміг запам’ятати дані: '+anchor+'? Де ще він знадобиться?'
        transfer='Яку одну деталь умови «'+anchor+'» варто перевірити вдруге перед дією?'
        source_note='«Магазин одягу», с.1–2; «Соціально-емоційні навички та сили СЕН», с.3.'
    elif code in ('3a','3b','3d','3e','8b'):
        domain='емоційний інтелект: емпатія й розрізнення факту та припущення'
        focus='Розумію героя без поспішних висновків'
        action='Відокрем написаний у тексті факт від здогадки за темою «'+anchor+'». Подумки запропонуй два можливі почуття іншого вигаданого героя; вони можуть різнитися. Про себе розповідати не треба.'
        reflection='Що в історії допомогло обміркувати тему «'+anchor+'»? Яке уточнення можна поставити героєві замість того, щоб вгадувати його стан?'
        transfer='Як у новій історії за темою «'+anchor+'» відрізнити повідомлений факт від припущення? Можливі різні обґрунтовані погляди.'
        source_note='«Історії з почуттями», с.1–2; «Різні точки зору», с.1–2; «Вгадаймо емоцію», с.2.'
    elif code in ('1d','1e','4c','4e','6d','7b','8e'):
        domain='співпраця: прийняття різних поглядів'
        focus='Поважаю інший вибір'
        action='Уяви ситуацію за темою «'+anchor+'». Сформулюй дві різні прийнятні думки без ярликів «краща людина / гірша людина». У парі спершу точно повтори одну думку партнера; соло — думку вигаданого героя.'
        reflection='Що допомогло розібратися в темі «'+anchor+'», навіть коли вибір інший? Як уточнити причину без оцінювання людини?'
        transfer='Яку ввічливу репліку можна використати в іншій розмові за темою «'+anchor+'», щоб не нав’язувати власний вибір?'
        source_note='«Різні точки зору», с.1–2; «Ділимося нашими інтересами», с.1–2.'
    elif code in ('4a','5e','6b','7e','8c'):
        domain='співпраця: уважне слухання й уточнення'
        focus='Уточнюю потребу співрозмовника'
        action='Зверни увагу на умову «'+anchor+'». У парі дай завершити репліку, потім повтори одну важливу умову перед власною відповіддю. Соло — прочитай і перекажи умову вигаданого співрозмовника.'
        reflection='Яка уточнювальна репліка допомогла точно передати умову «'+anchor+'»? Де таке уточнення допоможе поза грою?'
        transfer='Що варто уточнити в новій розмові за темою «'+anchor+'», перш ніж пропонувати рішення?'
        source_note='«Слухаємо уважно», с.1–2; «Дорожні карти Програми СЕН «Зерна»», с.2–3.'
    elif code in ('1a','2e','5a','5c','5d','6e','learning-tips'):
        domain='когнітивні навички: цілепокладання і планування'
        focus='Планую й перевіряю кроки'
        action='Перед вибором коротко визнач мету й два кроки для умови «'+anchor+'». Після першого кроку звір, чи він наближає до мети; план можна змінити.'
        reflection='Як план із двох кроків допоміг урахувати умову «'+anchor+'»? Що наступного разу зробиш інакше в подібному завданні?'
        transfer='Де в новій ситуації за темою «'+anchor+'» доречно зупинитися й змінити план після перевірки?'
        source_note='«Соціально-емоційні навички та сили СЕН», с.3; «Зачекай», с.1–2.'
    else:
        domain='когнітивні навички: увага і критичне мислення'
        focus='Роблю паузу й шукаю доказ'
        action='Перед вибором зроби коротку паузу й знайди опорне слово або факт в умові «'+anchor+'». Зістав його з умовою, а не обирай лише за знайомим виглядом слова.'
        reflection='Яка перевірка допомогла врахувати умову «'+anchor+'»? Як цей спосіб можна застосувати в іншому тексті або дорученні?'
        transfer='Який факт у новій ситуації за темою «'+anchor+'» потрібно перевірити, перш ніж довіритися першому враженню?'
        source_note='«Зачекай», с.1–2; «Соціально-емоційні навички та сили СЕН», с.3.'
    return {'domain':domain,'focus':focus,'action':action,'prompt':(reflection if mode=='learn' else transfer)+' Можна подумки або на вигаданому прикладі; відповідати необов’язково.','source_note':source_note}


def sel_teaching_note(lesson,adaptation):
    profile=sel_profile(lesson,adaptation)
    formal=lesson['lesson_type'] in ('pair_diagnostic','semester_check')
    timing=('Змістову мікродію виконати тільки після зданої самостійної спроби або на окремому контакті. Перед формальним завданням — лише зрозумілий порядок роботи й право паузи; не підказувати зміст.' if formal else 'На початку наявного блоку 20–28 A / 16–25 C відвести до 30 сек на мету й мікродію; у37–42 A / 41–45 C замінити до 1 хв звичайної перевірки на необов’язкову рефлексію. Час не додається до 45 хв. У B/D можна лише подумати в межах завершення або пропустити.')
    return f'''## СЕН: конкретна навичка й дія

Фокус: **{profile['focus']}**. Напрям: {profile['domain']}. Авторська навчальна адаптація, не відтворення офіційної активності.

{timing}

Дія: {profile['action']}

Рефлексія й перенесення: {profile['prompt']}

Учитель моделює стратегію на одному нейтральному прикладі, а не оцінює «правильність» переживань. Мовчазна / письмова версія є способом участі. Соло-роль не доводить фактичної співпраці з іншою дитиною. Результат мовного тесту не є оцінкою СЕН-навички. Не робити психологічних висновків із камери, паузи або відмови відповідати.

Підстава для адаптації: {profile['source_note']} Детальні URL, локальні сторінки PDF та межі звірки — у [SEL_NUSH_REVIEW.md](../SEL_NUSH_REVIEW.md).
'''


NUSH_GROUP_NOTE='''## Як фіксувати мовні докази

L/R/S/W — види первинних доказів, не чотири офіційні групи. Для іноземних мов за наказом МОН №1093: група1 — сприйняття, група2 — взаємодія, група3 — надання інформації та висловлювання. Факти читання / слухання співвідносимо з першою; реальну відповідь співрозмовникові — з другою; самостійне тематичне повідомлення — з третьою. Вибір граматичної форми сам по собі ще не доводить цілу групу. Записані соло обидві ролі — репетиція, а не доказ реальної взаємодії. Відмічати, що саме учень продемонстрував і з якою підтримкою; недостатній доказ залишаємо непідтвердженим. Офіційну оцінку визначають за чинними критеріями й освітньою програмою закладу, не автоматично за часткою двох ігрових виборів чи внутрішньою рубрикою0–6. Посилання на МОН і сторінки — у SEL_NUSH_REVIEW.md.
'''


def main():
    data=json.loads(SOURCE.read_text()); lessons=data['lessons']; ads=curate_adaptations({a['slug']:a for a in data['adaptations']})
    assert len(lessons)==123 and [l['number'] for l in lessons]==list(range(1,124))
    manifests=[]
    for l in lessons:
        folder=BASE/f'{l["number"]:03d}'; folder.mkdir(parents=True,exist_ok=True)
        write(folder,'games.md',games(l,ads))
        assess=l['lesson_type'] in ('pair_diagnostic','semester_check')
        if assess:
            lesson,hand,key=assessment(l)
            recovery,recovery_key=recovery_material(l)
            write(folder,'recovery-handout.md',recovery)
            key+='\n\n'+recovery_key
        else: lesson,hand,key=lesson_regular(l,choose(l,ads))
        hand=f'# 6 клас · урок {l["number"]:03d} · {l["topic"]}\n\nПланова дата: {l["date"]}. Ім’я або умовне позначення: __________________\n\nМожна працювати з вигаданими персонажами. Під час переміщення в укриття не виконувати завдань. Якщо немає безпечних умов / освітлення, відкласти. Перевірку стану можна пропустити.\n\n'+hand
        if not assess:
            hand+='\n\n## Короткий маршрут без інтернету (D, 10–15 хв)\n\n00–02: відкрий блок 1, словник і модель. 02–06: прочитай текст, підкресли 2 факти. 06–10: виконай вправу 3 №1–2. 10–13: напиши 1–2 речення вправи 4. 13–15: постав ? біля труднощів і збережи аркуш. За відсутності ресурсу зупинись раніше; надсилати роботу під час відключення не потрібно. Принеси її за наступної можливості.\n\nДЗ до 10 хв: відредагуй одне речення / деталь уже початого основного продукту; нового повного твору не потрібно. Після короткого маршруту — лише два початі пункти й 1–2 речення; без подвійного навантаження.'
        else:
            hand+='\n\n## Якщо немає світла / звуку або ви в укритті\n\nКонтроль відкладається. За бажанням 00–03 прочитай тільки інструкцію, 03–08 запиши 2 знайомі слова до теми, 08–12 познач процедурне запитання, 12–15 збережи аркуш. Це підготовка, а не контрольний результат. Нового контрольного ДЗ немає.'
        write(folder,'lesson.md',lesson);write(folder,'handout.md',hand);write(folder,'key.md',f'# Ключ учителя · урок {l["number"]:03d}\n\nНе долучати цей аркуш до учнівської роздатки.\n\n'+key+'\n\n'+RUBRIC);write(folder,'report.md',report(l))
        manifests.append({'number':l['number'],'date':l['date'],'topic':l['topic'],'directory':folder.name,'source_id':l['id'],'lesson_type':l['lesson_type'],'files':['lesson.md','handout.md','key.md','report.md','games.md'],'assessment':assess,'recovery_file':'recovery-handout.md' if assess else None})
    (BASE/'manifest.json').write_text(json.dumps({'grade':6,'count':len(manifests),'academic_year':data['academic_year'],'lessons':manifests},ensure_ascii=False,indent=2)+'\n')
    readme='''# 6 клас — службові пакети на весь календар

Покриття: **123 із 123 календарних уроків**, 2026/2027; від 2026-09-01 до 2027-06-01. Кожен урок має окремі план/опорний конспект із чотирма сценаріями, самодостатню роздатку, ключ із рубрикою та порожній шаблон фактичного звіту. Дати — планові; джерело має статус запропонованого календаря. Це не підтвердження проведених уроків і не заповнена звітність.

Відтворення: `python3 scripts/build_teacher_grade6.py` із кореня репозиторію. Генератор читає тільки `teacher/6/source-plan.json`: очищені календарні поля та вбудовані локальні адаптації. `/home/why/-teach` потрібен лише для історичного походження, не для генерації. SHA-256 і початкові шляхи записані у provenance; службові лінки, журнальні ідентифікатори та відомості про зустрічі не імпортуються. Початкове джерело — річний план, а не каталог сайту. Планові сторінки підручника збережено як орієнтир, але роздатка не потребує підручника, інтернету чи аудіозаписів.

A: 45 хв у класі. B: до 15 хв тільки після завершення переміщення, дозволу й оцінки умов; за шуму / тісноти не проводити. C: 45 хв онлайн, камера необов’язкова, письмовий канал участі. D: 10–15 хв із завчасно виданим папером, якщо є безпечне освітлення та ресурс. Під час переміщення навчальних завдань немає. SEL — авторські підтримувальні мікропрактики з правом пропуску й вигаданими персонажами; вони не названі офіційними вправами «Зерна». Нормативні коди та офіційні шкали не вигадувалися.

На контрольних L/S письмовий канал є підготовкою, а не заміною відповідної навички. У B/D формальний контроль переноситься; у C слухання потребує чутності, говоріння — фактичного усного доказу. Окремі слоти для всіх учнів планує вчитель: у 12 хв діагностичного уроку весь клас прослухати неможливо. Тексти слухання — тільки в ключі. Матеріали культурних / пісенних уроків є текстовою адаптацією, без твердження, що аудіювання оригінальної пісні відбулося.

Обмеження: авторські готові до адаптації пакети потребують учительського перегляду під фактичний клас, ІПР, затверджені критерії закладу й актуальний розклад. Робоча рубрика 0–6 не є автоматичною офіційною оцінкою. Фактичні звіти заповнюються тільки після проведення; персональні дані учнів не комітити. Роздатка handout.pdf призначена учневі; teacher.pdf містить службові ключі та звіт і видається тільки вчителю.

Ігри:2 сценарії на кожну дату (засвоєння7хв і формувальна перевірка5хв); повторюються механіки, змінюються ролі, зміст і мовні рішення. Вони замінюють відповідний блок, не додаються до 45 хв. На контрольних — після незалежної спроби / окремим контактом; гра не зараховується за формальний контроль. Готові резерви контрольних — recovery-handout.md у відповідних папках, приховані стимули й ключі — вkey.md.

Методична повторна перевірка: [QUALITY_REVIEW.md](QUALITY_REVIEW.md), поурочний машинний звіт [quality-review.json](quality-review.json).

## Календар і файли

| № | Планова дата | Тема | Матеріали |
|---|---|---|---|
'''
    for m in manifests:
        d=m['directory']; links=' · '.join(f'[{label}]({d}/{file})' for label,file in [('план','lesson.md'),('роздатка','handout.md'),('ключ','key.md'),('звіт','report.md'),('PDF учня','handout.pdf'),('PDF учителя','teacher.pdf'),('ігри','games.md'),('PDF ігор','games.pdf')])
        if m['assessment']:links+=f' · [резерв]({d}/recovery-handout.md)'
        readme+=f'| {m["number"]} | {m["date"]} | {m["topic"]} | {links} |\n'
    write(BASE,'README.md',readme)
    print(f'Generated {len(lessons)} lesson packets in {BASE}')

if __name__=='__main__':main()
