(() => {
  const key = `esl-mobile:${location.pathname}`;
  const read = k => { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch { return false; } };
  const button = (text, action) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.className = 'mobile-button'; b.addEventListener('click', action); return b; };
  const catalog = document.querySelector('main.catalog');
  if (catalog) {
    const sections = [...catalog.querySelectorAll('.class-section')];
    const tools = document.createElement('div'); tools.className = 'catalog-tools';
    const label = document.createElement('label'); label.textContent = 'Знайти урок';
    const search = document.createElement('input'); search.type = 'search'; search.placeholder = 'Тема, Unit або сторінка SB'; label.append(search); tools.append(label);
    const status = document.createElement('p'); status.setAttribute('role', 'status'); tools.append(status);
    const last = read('esl-last-lesson');
    if (last && /^\/(?:esl-lessons\/)?(?:6|7|9)\/[\w-]+\/$/.test(last.path)) {
      const a = document.createElement('a'); a.href = last.path; a.textContent = `Продовжити: ${last.title}`; a.className = 'mobile-button'; tools.append(a);
    }
    catalog.prepend(tools);
    const groups = sections.map(section => {
      const cards = section.querySelector('.cards'); const heading = section.querySelector('h2');
      if (!cards || !heading) return null;
      const details = document.createElement('details'); details.className = 'catalog-unit';
      const summary = document.createElement('summary'); summary.textContent = `${heading.textContent.trim()} · ${cards.children.length}`;
      const headingRow = heading.closest('.class-heading'); if (!heading.querySelector('a')) { if (headingRow) headingRow.hidden = true; else heading.hidden = true; }
      details.append(summary, cards); section.append(details);
      return { section, details, cards: [...cards.children] };
    }).filter(Boolean);
    const filter = () => {
      const query = search.value.trim().toLocaleLowerCase(); let count = 0;
      groups.forEach(group => {
        let matches = 0; group.cards.forEach(card => { const match = !query || card.textContent.toLocaleLowerCase().includes(query); card.hidden = !match; if (match) matches++; });
        group.section.hidden = !matches; group.details.open = Boolean(query && matches); count += matches;
      });
      status.textContent = query ? `Знайдено уроків: ${count}` : 'Відкрий потрібний розділ або скористайся пошуком.';
    };
    search.addEventListener('input', filter); filter();
    document.querySelectorAll('a[href^="#"]').forEach(a => a.addEventListener('click', () => { const target = document.getElementById(a.hash.slice(1)); const group = groups.find(g => g.section === target || g.section.contains(target)); if (group) group.details.open = true; }));
    return;
  }
  if (!document.querySelector('[data-site-nav="grade"]')) return;
  save('esl-last-lesson', {path: location.pathname, title: document.title});
  document.querySelectorAll('label.option .ld-word').forEach(link => link.replaceWith(document.createTextNode(link.textContent)));
  const state = read(key) || {fields: {}, positions: {}}; state.fields ||= {}; state.positions ||= {};
  const fields = [...document.querySelectorAll('main input:not([type=button]):not([type=submit]), main textarea')];
  fields.forEach((field, i) => {
    if (Object.hasOwn(state.fields, i)) { if (/^(radio|checkbox)$/.test(field.type)) field.checked = state.fields[i]; else field.value = state.fields[i]; }
    const persist = () => { fields.forEach((f, j) => state.fields[j] = /^(radio|checkbox)$/.test(f.type) ? f.checked : f.value); const ok = save(key, state); if (field.matches('textarea')) { const status = field.closest('.write-card')?.querySelector('.saved'); if (status) status.textContent = ok ? 'Чернетку збережено на цьому пристрої.' : 'Не вдалося зберегти. Скопіюй текст.'; } };
    field.addEventListener('input', persist); field.addEventListener('change', persist);
  });
  document.querySelectorAll('.practice').forEach((panel, p) => {
    const questions = [...panel.querySelectorAll('.question[data-answer]')]; if (!questions.length) return;
    let current = Math.min(state.positions[p] || 0, questions.length - 1); let all = !matchMedia('(max-width: 720px)').matches;
    const controls = document.createElement('div'); controls.className = 'exercise-controls'; controls.dataset.dictionarySkip = '';
    const counter = document.createElement('span'); counter.setAttribute('role', 'status');
    const show = () => { questions.forEach((q, i) => q.hidden = !all && i !== current); counter.textContent = `${current + 1} із ${questions.length}`; prev.disabled = all || current === 0; next.disabled = all || current === questions.length - 1; toggle.textContent = all ? 'По одному' : 'Усі питання'; toggle.setAttribute('aria-pressed', String(all)); state.positions[p] = current; save(key, state); };
    const prev = button('Назад', () => { current--; show(); }); const next = button('Далі', () => { current++; show(); }); const toggle = button('', () => { all = !all; show(); });
    controls.append(prev, counter, next, toggle); panel.insertBefore(controls, questions[0]);
    questions.forEach(question => {
      const check = button('Перевірити відповідь', () => {
        const selected = question.querySelector('input:checked, input[type=text]'); const value = selected?.value.trim() || '';
        const normalize = text => text.toLocaleLowerCase().replace(/[.!?]+$/, ''); const ok = normalize(value) === normalize(question.dataset.answer);
        const feedback = question.querySelector('.feedback'); if (!feedback) return;
        feedback.textContent = !value ? 'Обери або впиши відповідь.' : `${ok ? 'Правильно.' : 'Спробуй ще.'} ${question.querySelector('.answer-why')?.textContent || ''}`;
        feedback.className = `feedback ${ok ? 'good' : 'bad'}`;
      }); question.append(check);
    });
    panel.querySelector('.reset')?.addEventListener('click', () => { fields.forEach((f, i) => state.fields[i] = /^(radio|checkbox)$/.test(f.type) ? f.checked : f.value); current = 0; show(); }); show();
  });
  const nav = document.querySelector('nav.jump');
  if (nav) {
    const dock = document.createElement('nav'); dock.className = 'mobile-dock'; dock.setAttribute('aria-label', 'Навігація уроком');
    const menu = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = 'Зміст'; const list = document.createElement('div'); list.className = 'mobile-contents';
    [...nav.querySelectorAll('a')].forEach(link => { const copy = link.cloneNode(true); copy.addEventListener('click', () => menu.open = false); list.append(copy); }); menu.append(summary, list); dock.append(menu);
    const back = document.querySelector('[data-site-nav="grade"]').cloneNode(true); back.textContent = 'До уроків'; dock.append(back);
    const sections = [...document.querySelectorAll('main section[id]')];
    dock.append(button('Далі', () => { const next = sections.find(section => section.getBoundingClientRect().top > 80); (next || sections[0])?.scrollIntoView({behavior: 'auto'}); })); document.body.append(dock);
    if (window.visualViewport) { const keyboard = () => dock.hidden = window.visualViewport.height < window.innerHeight * .75; window.visualViewport.addEventListener('resize', keyboard); }
  }
})();
