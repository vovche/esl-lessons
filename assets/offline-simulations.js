(function () {
  'use strict';
  const script = document.currentScript;
  if (!script) return;
  const base = new URL('../', script.src), url = new URL(location.href);
  const rootLink = document.querySelector('[data-offline-root]');
  if (rootLink) rootLink.href = base.href;
  if (!url.pathname.startsWith(base.pathname)) return;
  const relative = url.pathname.slice(base.pathname.length);
  const match = /^(6|7|9)\/([^/]+)\/(?:index\.html)?$/.exec(relative);
  if (!match) return;
  const section = document.querySelector('[data-lesson-simulations]');
  section.dataset.simGrade = match[1]; section.dataset.simSlug = match[2];
  section.dataset.simDataUrl = new URL(match[1] + '/simulations.json', base).href;
  const loadButton = section.querySelector('[data-sim-load]');
  loadButton.disabled = true;
  loadButton.textContent = 'Готую ігри…';
  section.hidden = false;
  document.querySelector('[data-offline-hint]').textContent = 'Доступні збережені місії цього уроку. Після відновлення зв’язку можна повернутися до повного матеріалу.';
  const returnButton = document.querySelector('[data-offline-return]');
  returnButton.hidden = false;
  returnButton.textContent = 'Перевірити зв’язок і відкрити урок';
  returnButton.addEventListener('click', async () => {
    returnButton.disabled = true;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 4000);
    try {
      const response = await fetch(new URL('simulations-sw.js?connection-check=1', base), {cache: 'no-store', signal: controller.signal});
      if (!response.ok) throw new Error('unavailable');
      location.reload();
    } catch (_) {
      document.querySelector('[data-offline-hint]').textContent = 'Зв’язок поки недоступний. Продовжуй збережену місію або перевір зв’язок пізніше; поточна гра залишається відкритою.';
    } finally { clearTimeout(timer); returnButton.disabled = false; }
  });
  const runtime = document.createElement('script');
  runtime.src = new URL('assets/lesson-simulations.js', base).href;
  runtime.onload = () => { loadButton.textContent = 'Відкрити місії'; loadButton.disabled = false; };
  runtime.onerror = () => { loadButton.textContent = 'Ігри недоступні'; document.querySelector('[data-offline-hint]').textContent = 'Не вдалося відкрити збережені місії. Коли з’явиться зв’язок, повернися до уроку й підготуй місії до роботи без мережі.'; };
  document.head.append(runtime);
})();
