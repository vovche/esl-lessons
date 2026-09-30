(() => {
  const scriptUrl = document.currentScript?.src;
  const root = document.querySelector('[data-dictionary-root]');
  if (!scriptUrl || !root) return;

  const dictionaryUrl = new URL('../dictionary/', scriptUrl);
  const indexUrl = new URL('word-index.json', dictionaryUrl);
  const dataUrl = new URL('words.json', dictionaryUrl);
  const wordPattern = /[A-Za-z]+(?:['’][A-Za-z]+)?(?:-[A-Za-z]+)*/g;
  const skip = 'a, button, nav, footer, script, style, noscript, textarea, select, option, code, pre, svg, [contenteditable], .ld-dialog, .feedback, .result, .saved';
  const voiceLabels = {
    'gb-female': '🇬🇧 Жіночий',
    'gb-male': '🇬🇧 Чоловічий',
    'us-female': '🇺🇸 Жіночий',
    'us-male': '🇺🇸 Чоловічий',
  };
  let knownWords = new Set();
  let entriesPromise;
  let previousFocus;

  const dialog = document.createElement('dialog');
  dialog.className = 'ld-dialog';
  dialog.setAttribute('aria-label', 'Словникова картка');
  dialog.innerHTML = `<div class="ld-head"><span class="ld-caption">Словник вимови</span><button class="ld-close" type="button" aria-label="Закрити картку">×</button></div><div class="ld-content" aria-live="polite"></div><audio preload="none"></audio>`;
  document.body.append(dialog);
  const content = dialog.querySelector('.ld-content');
  const player = dialog.querySelector('audio');
  const close = () => dialog.close();
  dialog.querySelector('.ld-close').addEventListener('click', close);
  dialog.addEventListener('cancel', () => player.pause());
  dialog.addEventListener('close', () => {
    player.pause();
    player.removeAttribute('src');
    previousFocus?.focus();
  });
  dialog.addEventListener('click', event => {
    if (event.target === dialog) close();
  });

  const normalize = word => word.toLocaleLowerCase('en').replaceAll('’', "'");
  const dictionaryLink = word => `${dictionaryUrl}?q=${encodeURIComponent(word)}`;

  function makeLink(word) {
    const link = document.createElement('a');
    link.className = 'ld-word';
    link.href = dictionaryLink(word);
    link.dataset.dictionaryWord = normalize(word);
    link.textContent = word;
    link.setAttribute('aria-label', `${word}: відкрити словникову картку з перекладом і вимовою`);
    link.title = 'Переглянути переклад і послухати слово';
    return link;
  }

  function wrapText(node) {
    if (!node.parentElement || node.parentElement.closest(skip)) return;
    const text = node.nodeValue;
    wordPattern.lastIndex = 0;
    let match;
    let last = 0;
    let changed = false;
    const fragment = document.createDocumentFragment();
    while ((match = wordPattern.exec(text))) {
      if (!knownWords.has(normalize(match[0]))) continue;
      fragment.append(document.createTextNode(text.slice(last, match.index)));
      fragment.append(makeLink(match[0]));
      last = wordPattern.lastIndex;
      changed = true;
    }
    if (!changed) return;
    fragment.append(document.createTextNode(text.slice(last)));
    node.replaceWith(fragment);
  }

  function scan(element) {
    if (element.nodeType === Node.TEXT_NODE) {
      wrapText(element);
      return;
    }
    if (element.nodeType !== Node.ELEMENT_NODE || element.closest(skip)) return;
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(wrapText);
  }

  function details(entry) {
    content.replaceChildren();
    const title = document.createElement('h2');
    title.textContent = entry.word;
    content.append(title);
    const translation = document.createElement('p');
    translation.className = 'ld-translation';
    translation.lang = 'uk';
    const translationLabel = document.createElement('strong');
    translationLabel.textContent = 'Переклад: ';
    translation.append(translationLabel, entry.translationsUk.join('; '));
    content.append(translation);
    for (const [accent, label] of [['gb', 'Британська'], ['us', 'Американська']]) {
      const row = document.createElement('div');
      row.className = 'ld-pronunciation';
      const name = document.createElement('strong');
      name.textContent = label;
      const ipa = document.createElement('span');
      ipa.textContent = entry.ipa[accent];
      const ukrainian = document.createElement('span');
      ukrainian.textContent = entry.ukPhonetic[accent];
      row.append(name, ipa, ukrainian);
      content.append(row);
    }
    const phonics = document.createElement('p');
    phonics.className = 'ld-phonics';
    phonics.innerHTML = '<strong>Phonics hint</strong> ';
    const hint = document.createElement('span');
    hint.lang = 'en';
    hint.textContent = entry.phonics;
    phonics.append(hint);
    content.append(phonics);
    const voices = document.createElement('div');
    voices.className = 'ld-voices';
    for (const [key, label] of Object.entries(voiceLabels)) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = `▶ ${label}`;
      button.setAttribute('aria-label', `Слухати ${entry.word}: ${label}`);
      button.addEventListener('click', async () => {
        voices.querySelectorAll('button').forEach(item => item.classList.remove('ld-playing'));
        button.classList.add('ld-playing');
        player.src = new URL(entry.audio[key], dictionaryUrl);
        try { await player.play(); }
        catch {
          button.classList.remove('ld-playing');
          status.textContent = 'Не вдалося відтворити запис. Перевір з’єднання.';
        }
      });
      voices.append(button);
    }
    content.append(voices);
    const status = document.createElement('p');
    status.className = 'ld-status';
    status.setAttribute('role', 'status');
    content.append(status);
    player.onended = () => voices.querySelectorAll('button').forEach(item => item.classList.remove('ld-playing'));
    const links = document.createElement('div');
    links.className = 'ld-links';
    const full = document.createElement('a');
    full.href = dictionaryLink(entry.word);
    full.textContent = 'Відкрити в словнику';
    const google = document.createElement('a');
    google.href = `https://www.google.com/search?q=${encodeURIComponent(entry.word + ' pronunciation')}`;
    google.target = '_blank';
    google.rel = 'noopener noreferrer';
    google.textContent = 'Знайти вимову в Google ↗';
    links.append(full, google);
    content.append(links);
  }

  async function openWord(word, trigger) {
    previousFocus = trigger;
    content.textContent = 'Завантажуємо словникову картку…';
    if (!dialog.open) dialog.showModal();
    try {
      entriesPromise ||= fetch(dataUrl).then(response => {
        if (!response.ok) throw new Error('Dictionary unavailable');
        return response.json();
      }).then(data => new Map(data.entries.map(entry => [entry.word, entry])));
      const entries = await entriesPromise;
      if (!dialog.open) return;
      const entry = entries.get(word);
      if (entry) details(entry);
      else {
        content.textContent = 'Цього слова поки немає у словнику. ';
        const link = document.createElement('a');
        link.href = dictionaryLink(word);
        link.textContent = 'Пошукати в словнику';
        content.append(link);
      }
    } catch {
      entriesPromise = undefined;
      content.textContent = 'Не вдалося завантажити картку. Перевір з’єднання. ';
      const link = document.createElement('a');
      link.href = dictionaryLink(word);
      link.textContent = 'Відкрити словник';
      content.append(link);
    }
  }

  root.addEventListener('click', event => {
    const link = event.target.closest('a.ld-word');
    if (!link || !root.contains(link) || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    event.stopPropagation();
    openWord(link.dataset.dictionaryWord, link);
  }, true);

  fetch(indexUrl).then(response => {
    if (!response.ok) throw new Error('Dictionary index unavailable');
    return response.json();
  }).then(words => {
    knownWords = new Set(words);
    scan(root);
    const observer = new MutationObserver(records => {
      for (const record of records) {
        if (record.type === 'characterData') scan(record.target);
        else record.addedNodes.forEach(scan);
      }
    });
    observer.observe(root, {subtree: true, childList: true, characterData: true});
  }).catch(() => {});
})();
