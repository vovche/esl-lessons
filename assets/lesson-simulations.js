(function (global) {
  'use strict';

  function signature(game) {
    const value = JSON.stringify(game);
    let hash = 2166136261;
    for (let i = 0; i < value.length; i++) hash = Math.imul(hash ^ value.charCodeAt(i), 16777619);
    return (hash >>> 0).toString(36);
  }

  function createState(game, previous) {
    const fresh = { signature: signature(game), cursor: 0, phase: 'playing', first: game.steps.map(() => null),
      attempts: 0, lastChoice: null, lastCorrect: null, hint: false, paused: false, production: '',
      firstResult: null, run: 1 };
    if (!previous || previous.signature !== fresh.signature) return fresh;
    if (!Number.isInteger(previous.cursor) || previous.cursor < 0 || previous.cursor >= game.steps.length ||
        !['playing', 'accepted', 'complete'].includes(previous.phase) ||
        !Array.isArray(previous.first) || previous.first.length !== game.steps.length ||
        previous.first.some(item => item !== null && typeof item !== 'boolean') ||
        !Number.isInteger(previous.attempts) || previous.attempts < 0 ||
        !Number.isInteger(previous.run) || previous.run < 1 ||
        typeof previous.paused !== 'boolean' || typeof previous.hint !== 'boolean' ||
        (previous.lastCorrect !== null && typeof previous.lastCorrect !== 'boolean') ||
        (previous.lastChoice !== null && (!Number.isInteger(previous.lastChoice) || previous.lastChoice < 0 || previous.lastChoice >= game.steps[previous.cursor].choices.length)) ||
        (previous.firstResult !== null && (!Number.isInteger(previous.firstResult) || previous.firstResult < 0 || previous.firstResult > game.steps.length))) return fresh;
    return { ...fresh, ...previous, production: typeof previous.production === 'string' ? previous.production.slice(0, 500) : '' };
  }

  function choose(game, state, index) {
    if (state.phase !== 'playing' || state.paused || !Number.isInteger(index)) return state;
    const choice = game.steps[state.cursor].choices[index];
    if (!choice) return state;
    const result = { ...state, first: [...state.first], attempts: state.attempts + 1, lastChoice: index,
      lastCorrect: choice.effect === 'advance', hint: false };
    if (result.first[state.cursor] === null) result.first[state.cursor] = result.lastCorrect;
    if (game.mode === 'check' || result.lastCorrect) result.phase = 'accepted';
    return result;
  }

  function advance(game, state) {
    if (state.phase !== 'accepted' || state.paused) return state;
    if (state.cursor === game.steps.length - 1) {
      return { ...state, phase: 'complete', firstResult: state.firstResult === null ? score(state) : state.firstResult };
    }
    return { ...state, cursor: state.cursor + 1, phase: 'playing', lastChoice: null, lastCorrect: null, hint: false };
  }

  function score(state) { return state.first.filter(value => value === true).length; }
  function restart(game, state) {
    return { ...createState(game), firstResult: state.firstResult, run: state.run + 1 };
  }

  const engine = { signature, createState, choose, advance, score, restart };
  if (typeof module !== 'undefined' && module.exports) module.exports = engine;
  if (!global.document) return;

  const siteBase = new URL('../', document.currentScript.src);
  const cache = new Map();
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function button(label, action, secondary) {
    const node = el('button', secondary ? 'sim-button sim-secondary' : 'sim-button', label);
    node.type = 'button'; node.addEventListener('click', action); return node;
  }
  const sessionProgress = new Map();
  function read(key) {
    if (sessionProgress.has(key)) return sessionProgress.get(key);
    try { return JSON.parse(localStorage.getItem(key)); } catch (_) { return null; }
  }
  function write(key, value) {
    sessionProgress.set(key, value);
    try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch (_) { return false; }
  }

  function mount(root) {
    const grade = root.dataset.simGrade;
    const slug = root.dataset.simSlug;
    const host = root.querySelector('[data-sim-host]');
    const loadButton = root.querySelector('[data-sim-load]');
    let lessons = [], selected = null, game = null, state = null, storageKey = '', saved = true;
    const lastKey = ['esl-simulation-last-v1', grade, slug].join(':');
    const keyFor = item => ['esl-simulation-v1', grade, slug, selected.id, item.id].join(':');
    let offlineReady = false, preparing = false;
    const connection = el('p', 'sim-muted'); connection.setAttribute('role', 'status');
    const retryOffline = button('Підготувати для роботи без інтернету', prepareOffline, true);
    root.insertBefore(connection, host); root.insertBefore(retryOffline, host);
    retryOffline.hidden = true;

    function connectionStatus() {
      connection.textContent = offlineReady ? (navigator.onLine ?
        'Місії готові до роботи без інтернету й перезавантаження на цьому пристрої. Не очищуй дані сайту.' :
        'Інтернету немає. Завантажені місії можна продовжувати й перезавантажувати; повний урок потребує зв’язку.') :
        preparing ? 'Готую місії для перезавантаження без інтернету… Поки не закривай сторінку.' :
        'Завантажену гру можна продовжувати тут. Офлайн-перезавантаження ще не підготовлене: для повернення на сторінку потрібен інтернет.';
      if (!saved) connection.textContent += ' Збереження поступу заблоковане: не оновлюй сторінку, якщо хочеш продовжити з цього місця.';
    }
    async function prepareOffline() {
      if (preparing) return;
      preparing = true; retryOffline.hidden = true; connectionStatus();
      let channel, timer;
      try {
        if (!('serviceWorker' in navigator)) throw new Error('unsupported');
        const workerURL = new URL('simulations-sw.js', siteBase).href;
        let registration = await navigator.serviceWorker.getRegistration(siteBase.href);
        if (registration && registration.active && registration.active.scriptURL !== workerURL) throw new Error('different worker');
        if (!registration || navigator.onLine) registration = await navigator.serviceWorker.register(workerURL, {scope: siteBase.href});
        registration = await Promise.race([navigator.serviceWorker.ready, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('timeout')), 15000); })]);
        clearTimeout(timer);
        await new Promise((resolve, reject) => {
          channel = new MessageChannel();
          timer = setTimeout(() => reject(new Error('timeout')), 15000);
          channel.port1.onmessage = event => event.data && event.data.ok ? resolve() : reject(new Error('cache unavailable'));
          registration.active.postMessage({type: 'PREPARE_MISSIONS', grade}, [channel.port2]);
        });
        offlineReady = true;
      } catch (_) { offlineReady = false; }
      finally {
        clearTimeout(timer); if (channel) channel.port1.close();
        preparing = false; retryOffline.hidden = offlineReady; connectionStatus();
      }
    }
    if ('serviceWorker' in navigator) {
      let hadController = Boolean(navigator.serviceWorker.controller);
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (hadController && !root.querySelector('[data-sim-update]')) {
          const notice = el('p', 'sim-note', 'Оновлення готове. Можна завершити поточну місію; нова версія відкриється після перезавантаження.');
          notice.dataset.simUpdate = ''; notice.setAttribute('role', 'status');
          root.insertBefore(notice, host);
        }
        hadController = true;
      });
    }
    global.addEventListener('offline', connectionStatus);
    global.addEventListener('online', () => { connectionStatus(); if (lessons.length && !offlineReady) prepareOffline(); });
    connectionStatus();

    function persist() {
      saved = write(storageKey, state);
      saved = write(lastKey, {lesson: selected.id, game: game.id}) && saved;
      connectionStatus();
    }
    function focusHeading() { const heading = host.querySelector('[tabindex="-1"]'); if (heading) heading.focus(); }
    function go(next) { state = next; persist(); renderGame(); }
    function heading(text) { const h = el('h3', '', text); h.tabIndex = -1; return h; }
    function sourceCard(open) {
      const source = el('details', 'sim-source'); source.open = open;
      source.append(el('summary', '', open ? 'Картка ситуації' : 'Перечитати картку ситуації'));
      const text = el('p', '', game.source); text.lang = 'en'; source.append(text);
      return source;
    }

    function showMenu() {
      game = null;
      host.replaceChildren();
      const label = el('label', 'sim-label', 'Обери ситуацію');
      const select = el('select', 'sim-select');
      select.id = 'sim-situation-' + grade + '-' + slug;
      label.htmlFor = select.id;
      lessons.forEach((lesson, i) => {
        const option = el('option', '', (i + 1) + '. ' + lesson.title);
        option.value = lesson.id; select.append(option);
      });
      const last = read(lastKey);
      select.value = selected ? selected.id : (last && lessons.some(item => item.id === last.lesson) ? last.lesson : lessons[0].id);
      selected = lessons.find(lesson => lesson.id === select.value);
      host.append(label, select);
      const cards = el('div', 'sim-mode-grid');
      function modes() {
        cards.replaceChildren();
        selected.games.forEach(item => {
          const card = el('article', 'sim-mode-card');
          card.append(el('p', 'sim-mode-name', item.mode === 'learn' ? 'Разом із підказками' : 'Самостійна спроба'),
            el('h3', '', item.title), el('p', '', item.role),
            el('p', 'sim-muted', item.mode === 'learn' ? 'Обери відповідь. Після помилки можна взяти підказку й спробувати ще раз.' : 'Обери по одній відповіді на два запитання. Змінити вибір у цій спробі не можна. Результат побачиш наприкінці.'));
          const previous = read(keyFor(item));
          const restored = createState(item, previous);
          const resumable = previous && previous.signature === restored.signature && previous.phase === restored.phase && previous.cursor === restored.cursor;
          if (previous && previous.signature !== restored.signature) card.append(el('p', 'sim-note', 'Зміст місії оновлено. Для нових завдань потрібна нова спроба; попередній поступ до них не застосовується.'));
          if (resumable) card.append(el('p', 'sim-resume', restored.phase === 'complete' ? 'Місію завершено. Результат і чернетка доступні.' :
            'Збережено: хід ' + (restored.cursor + 1) + ' із ' + item.steps.length + (restored.paused ? '. Місія на паузі.' : '.')));
          card.append(button(resumable ? (restored.phase === 'complete' ? 'Переглянути результат' : 'Продовжити місію') : 'Почати місію', () => start(item)));
          cards.append(card);
        });
      }
      select.addEventListener('change', () => { selected = lessons.find(lesson => lesson.id === select.value); write(lastKey, {lesson: selected.id, game: null}); modes(); });
      modes(); host.append(cards); select.focus();
    }

    function start(item) {
      game = item;
      storageKey = keyFor(game);
      state = createState(game, read(storageKey));
      persist();
      renderGame(); focusHeading();
    }

    function renderGame() {
      host.replaceChildren();
      const toolbar = el('div', 'sim-toolbar');
      toolbar.append(button('← Інші місії', showMenu, true));
      toolbar.append(button(state.paused ? 'Продовжити' : 'Пауза', () => { go({ ...state, paused: !state.paused }); focusHeading(); }, true));
      host.append(toolbar, heading(game.title));
      if (!saved) host.append(el('p', 'sim-note', 'Браузер не зберігає поступ після закриття чи оновлення сторінки. Можна продовжувати тут або занотувати, на якому ході зупинився.'));
      if (state.paused) {
        host.append(el('p', 'sim-note', 'Місію призупинено. Повертайся, коли матимеш змогу.'));
        return;
      }
      host.append(el('p', 'sim-role', game.role), el('p', 'sim-goal', game.goal));
      if (game.reflection) host.append(el('p', 'sim-skill-focus', 'Спробуй під час місії: ' + game.reflection.focus));
      if (state.run > 1) host.append(el('p', 'sim-muted', 'Повторна спроба. Перший завершений результат зберігається окремо.'));
      if (state.phase === 'complete') { renderSummary(); return; }
      const progressLabel = el('p', 'sim-progress-label', 'Хід ' + (state.cursor + 1) + ' із ' + game.steps.length);
      const progress = el('progress', 'sim-progress');
      progress.max = game.steps.length; progress.value = state.cursor;
      progress.setAttribute('aria-label', 'Пройдені ходи');
      host.append(progressLabel, progress);
      if (game.source) {
        host.append(sourceCard(true));
      }
      const step = game.steps[state.cursor];
      const fieldset = el('fieldset', 'sim-step');
      const legend = el('legend', '', step.prompt); legend.lang = 'en'; fieldset.append(legend);
      const choices = el('div', 'sim-choices');
      step.choices.forEach((choice, index) => {
        const b = button(choice.text, () => { go(choose(game, state, index)); if (state.phase === 'playing') host.querySelectorAll('.sim-choice')[index].focus(); });
        b.className = 'sim-choice'; b.lang = 'en';
        b.setAttribute('aria-pressed', String(state.lastChoice === index));
        b.disabled = state.phase === 'accepted';
        choices.append(b);
      });
      fieldset.append(choices); host.append(fieldset);
      const feedback = el('p', 'sim-feedback'); feedback.setAttribute('role', 'status'); feedback.setAttribute('aria-live', 'polite');
      if (state.lastChoice !== null) {
        feedback.textContent = game.mode === 'check' ? (state.cursor === game.steps.length - 1 ? 'Вибір збережено. Натисни «Завершити місію», щоб побачити результат.' : 'Вибір збережено. Переходь до наступного ходу.') :
          state.lastCorrect ? 'Рішення прийнято. Можна рухатися далі.' : 'Цей хід ще не відкрив наступний крок. Спробуй інший варіант або візьми підказку.';
        if (game.mode === 'learn') feedback.classList.add(state.lastCorrect ? 'sim-good' : 'sim-retry');
      }
      host.append(feedback);
      if (game.mode === 'learn' && state.lastCorrect === false && step.hint) {
        host.append(button('Підказка', () => { go({ ...state, hint: true }); const note = host.querySelector('.sim-note'); if (note) { note.tabIndex = -1; note.focus(); } }, true));
        if (state.hint) host.append(el('p', 'sim-note', step.hint));
      }
      if (state.phase === 'accepted') {
        const next = button(state.cursor === game.steps.length - 1 ? 'Завершити місію' : 'Наступний хід', () => { go(advance(game, state)); focusHeading(); });
        host.append(next); next.focus();
      }
    }

    function renderSummary() {
      host.append(el('p', 'sim-complete', 'Місію завершено'));
      const total = game.steps.length;
      host.append(el('p', 'sim-score', 'З першої спроби в цьому проходженні: ' + score(state) + ' із ' + total + '.'));
      if (state.run > 1 && state.firstResult !== null) host.append(el('p', 'sim-muted', 'Перший завершений результат: ' + state.firstResult + ' із ' + total + '.'));
      host.append(el('p', 'sim-muted', 'Це коротка самоперевірка. Обери наступний крок: ' + (game.source ? 'перечитати картку' : 'повернутися до матеріалу уроку') + ', потренуватися з підказкою або скласти власний приклад. Результат не є оцінкою за тему.'));
      const review = el('details', 'sim-review');
      review.append(el('summary', '', 'Мої перші рішення: що вдалося і що повторити'));
      game.steps.forEach((step, index) => {
        const item = el('div', 'sim-review-item');
        const prompt = el('p', '', step.prompt); prompt.lang = 'en';
        item.append(el('p', 'sim-review-result', 'Хід ' + (index + 1) + ': ' + (state.first[index] ? 'вдалося з першого вибору.' : 'варто повторити.')), prompt);
        if (!state.first[index] && step.hint) item.append(el('p', 'sim-note', step.hint));
        review.append(item);
      });
      host.append(review);
      if (game.source) host.append(sourceCard(false));
      if (game.production && game.production.prompt) {
        const label = el('label', 'sim-label', 'Твоя англійська репліка');
        const id = 'sim-production-' + grade + '-' + slug;
        label.htmlFor = id;
        host.append(label, el('p', '', game.production.prompt), el('p', 'sim-muted', 'Перевір себе: чи репліка відповідає ситуації та чи використано потрібні слова або мовну конструкцію? Автоматично перевіряються лише два попередні рішення.'));
        const input = el('textarea', 'sim-production'); input.id = id; input.rows = 3; input.maxLength = 500;
        input.value = state.production; input.placeholder = game.production.starter || 'Write one short phrase…';
        input.addEventListener('input', () => { state.production = input.value; persist(); });
        host.append(input);
        const status = el('p', 'sim-muted'); status.setAttribute('role', 'status');
        host.append(button('Зберегти репліку', () => {
          state.production = input.value.trim(); persist();
          status.textContent = !state.production ? 'Спочатку запиши коротку репліку.' : saved ?
            'Чернетку збережено на цьому пристрої. Перевір, чи вона виконує завдання, або обговори її з учителем.' :
            'Чернетка доступна, доки сторінку відкрито. Можеш переписати її в зошит.';
        }), status);
      }
      if (game.reflection) {
        const reflection = el('details', 'sim-reflection');
        reflection.append(el('summary', '', 'Поміркуй про свій спосіб дії'));
        reflection.append(el('p', '', game.reflection.prompt));
        reflection.append(el('p', 'sim-muted', 'Можна подумки, українською або на вигаданому прикладі. Можна пропустити. Ця частина без балів; відповідь нікуди не записується.'));
        host.append(reflection);
      }
      const actions = el('div', 'sim-toolbar');
      actions.append(button('Пройти ще раз', () => { go(restart(game, state)); focusHeading(); }, true), button('Обрати іншу місію', showMenu, true));
      host.append(actions);
    }

    loadButton.addEventListener('click', async () => {
      loadButton.disabled = true;
      loadButton.textContent = 'Завантаження місій…';
      try {
        if (!cache.has(grade)) cache.set(grade, fetch(new URL(grade + '/simulations.json', siteBase)).then(response => {
          if (!response.ok) throw new Error('unavailable'); return response.json();
        }).catch(error => { cache.delete(grade); throw error; }));
        const data = await cache.get(grade);
        lessons = data.lessons.filter(lesson => lesson.slugs.includes(slug));
        if (!lessons.length) throw new Error('no missions');
        showMenu(); loadButton.hidden = true;
        prepareOffline();
        const select = host.querySelector('select'); if (select) select.focus();
      } catch (_) {
        host.replaceChildren(el('p', 'sim-note', 'Не вдалося завантажити місії. Коли буде зв’язок, спробуй ще раз.'));
        loadButton.disabled = false; loadButton.textContent = 'Спробувати завантажити ще раз';
      }
    });
  }

  function connectFullscreenLesson(root) {
    if (!root.closest('.quest-stage')) return;
    const dialog = el('dialog', 'sim-dialog');
    dialog.setAttribute('aria-labelledby', 'lesson-simulations-title');
    const close = button('Повернутися до уроку', () => dialog.close(), true);
    close.classList.add('sim-dialog-close');
    dialog.append(close, root);
    document.body.append(dialog);
    // The legacy fullscreen lesson listens for letter and arrow shortcuts on window.
    // Typing in a mission must not navigate the lesson behind the modal.
    dialog.addEventListener('keydown', event => event.stopPropagation());
    const launch = () => {
      const control = button('Ігрові місії', () => dialog.showModal());
      control.classList.add('sim-launch');
      return control;
    };
    const portrait = document.querySelector('.rotate-card');
    if (portrait) portrait.append(launch());
    const controls = document.querySelector('.quest-tip');
    if (controls) controls.replaceChildren(launch());
  }

  document.querySelectorAll('[data-lesson-simulations]').forEach(root => {
    connectFullscreenLesson(root);
    mount(root);
  });
})(typeof window !== 'undefined' ? window : globalThis);
