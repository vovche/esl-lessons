# Мобільна емуляція: відновлення після закриття процесу браузера

18 жовтня 2026 року. Підсумкова перевірка через блокований HTTP CONNECT proxy: **Chromium і WebKit пройшли обидві сторінки**. Підтвердженого дефекту сайту в цій вибірці не виявлено. Початкову помилку Playwright WebKit з `offline:true` відокремлено від результату перевірки мережевим proxy.

## Опубліковані сторінки та середовище

- [Gerund](https://vovche.github.io/esl-lessons/9/gerund/), ситуація `g9-023`, не перша у списку.
- [Future forms v2](https://vovche.github.io/esl-lessons/9/future-forms-v2/), ситуація `g9-009`; online запуск через кнопку «Ігрові місії» повноекранного уроку.
- Відповіді для автоматизованих дій отримано тільки з [опублікованого JSON](https://vovche.github.io/esl-lessons/9/simulations.json); локальний JSON не використовувався.
- Playwright Chromium 151, Pixel 7 mobile/touch emulation: viewport 412 × 839 CSS px, scale 2.625.
- Playwright WebKit 26.5, iPhone 13 mobile/touch emulation: viewport 390 × 664 CSS px, scale 3.
- Це **не реальні Android Chrome або iOS Safari**. Фізичні телефони не використовувалися.
- Для кожного поєднання engine + URL створено свіжий persistent userDataDir. Між фазами він зберігався. `launchPersistentContext` закривався повністю через `context.close()`, потім запускався заново; це не reload і не нова вкладка чинного процесу.
- Кнопки натискалися `tap()`, поле чернетки отримувало touch-фокус; для вводу тексту використано `fill()`. Select змінювався `selectOption()`, тому поведінка нативного picker/екранної клавіатури цим не оцінена.

## Як блокували мережу

Підсумковий тест використовував власний Node HTTP CONNECT proxy на localhost. HTTPS-трафік тунелювався до справжнього GitHub Pages без підміни TLS. При відключенні proxy знищував усі чинні тунелі та відхиляв нові CONNECT-запити. Після цього весь браузер закривався й повторно запускався з тим самим профілем і заблокованим proxy. Playwright `offline` залишався `false` у всіх фазах proxy-тесту. Перед початковим закриттям дочекалися повідомлення готовності місій до роботи offline. Сторонні embed-ресурси ізольовано; весь site-origin і SW завантажувалися з published HTTPS.

Обидва engines фактично зареєстрували controller `https://vovche.github.io/esl-lessons/simulations-sw.js`. Під час блокування натискання кнопки перевірки зв’язку завершувалося видимим повідомленням про недоступність, а не навігацією; після зняття блокування та повторного натискання повертався повний online-урок.

## Пройдені фази

Кожне з чотирьох поєднань engine + URL пройшло однаковий сценарій:

1. Online: завантажити місії, дочекатися ready, обрати потрібну ситуацію, дати помилкову відповідь, відкрити підказку, поставити на паузу; закрити весь persistent context / браузер.
2. Повторний запуск без мережі з тим самим профілем: перейти на оригінальний URL без online-підготовки. Відновилися ситуація, пауза, перша помилка й підказка. Завершити два ходи, отримати **1 із 2**, зберегти чернетку; закрити браузер.
3. Другий запуск без мережі: відновилися завершений результат **1 із 2** й точний текст чернетки. Відкрити самостійну місію, прийняти помилковий перший вибір; закрити браузер.
4. Третій запуск без мережі: перший вибір самостійної місії залишився заблокованим, підказка недоступна. Невдале натискання повернення online не стерло поточний стан. Завершити другий хід правильно, отримати **1 із 2**. Розблокувати proxy; натискання кнопки зв’язку повернуло повний урок.

| Engine / mobile emulation | Gerund g9-023 | Fullscreen future g9-009 | JavaScript pageerror |
| --- | --- | --- | --- |
| Chromium / Pixel 7, CONNECT proxy | PASS усіх 4 фаз | PASS усіх 4 фаз | 0 |
| WebKit / iPhone 13, CONNECT proxy | PASS усіх 4 фаз | PASS усіх 4 фаз | 0 |

У цій вибірці після offline-запуску відображалася оболонка «Ігрові місії без мережі». Повноекранний урок offline не вимагав landscape і дозволяв працювати зі збереженою місією.

## Початкова помилка інструментування WebKit

Окремий початковий тест з `launchPersistentContext({offline:true})` пройшов у Chromium на обох URL, але WebKit на обох URL після першого закриття повернув `page.goto: WebKit encountered an internal error`, показавши порожню сторінку. Це не було доказом втрати прогресу: наступний online-запуск тих самих WebKit-профілів показав збережені `first:[false,null]`, `hint:true`, `paused:true`, вибрану ситуацію, SW registration і cache `esl-missions-v1`.

Контрольний тест через proxy, з `offline:false` і реально заблокованими тунелями, пройшов повністю в WebKit на обох URL. Тому початковий internal error у цьому середовищі трактуємо як обмеження/артефакт offline-інструментування Playwright WebKit. Підтвердженням offline-відновлення є proxy-тест; висновок про дефект actual Safari на підставі internal error не робимо.

## Візуальний огляд і докази

Знято paused, restored draft та completed check screenshots. Оглянуто Chromium future paused, Chromium gerund restored draft, WebKit gerund restored draft, WebKit future paused і completed check. Тексти, відновлена чернетка, результат і кнопки читаються у вузькому layout, кнопки доступні touch-діям; явного обрізання контенту не виявлено. Також оглянуто порожній screenshot початкового WebKit internal error — він не приймався за успішне завантаження.

Тимчасові артефакти: `/tmp/grade9-mobile-restart/`. Основні runner-файли: `playtest.cjs` (початковий offline:true), `proxy-playtest.cjs` (WebKit gerund), `proxy-future-playtest.cjs` (WebKit future), `proxy-chromium-playtest.cjs` (обидва Chromium URL). Результати: `proxy-results-webkit.json`, `proxy-future-results-webkit.json`, `proxy-results-chromium.json`; початкова діагностика — `results-webkit.json` і `webkit-online-diagnostic.json`. Це локальні докази сесії, не постійні артефакти репозиторію. Proxy-підхід передано потоку 6 класу для спільного відтворюваного тесту.

## Межі висновку

Підтверджено чотири engine/URL сценарії, по чотири окремі запуски persistent браузера, на двох ситуаціях і чотирьох різних місіях. Це не перевірка всіх 121 ситуації. Proxy блокує мережу браузера, проте не відтворює фізичну втрату живлення, перезапуск ОС, апаратний телефон, background suspension iOS/Android, примусове вбивство процесу посеред запису або витіснення даних браузером. Для offline-початку потрібна попередня підготовка профілю online і збереження його даних. Зміни навчального контенту або shared runtime за результатами цієї перевірки не вносилися.
