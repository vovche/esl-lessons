(() => {
  const search = document.getElementById('search');
  const grade = document.getElementById('grade');
  const results = document.getElementById('results');
  const count = document.getElementById('resultCount');
  const more = document.getElementById('more');
  const error = document.getElementById('error');
  const player = document.getElementById('player');
  const voiceLabels = {'gb-female':'🇬🇧 Жіночий','gb-male':'🇬🇧 Чоловічий','us-female':'🇺🇸 Жіночий','us-male':'🇺🇸 Чоловічий'};
  let entries = [], filtered = [], shown = 0, playing = null;
  const esc = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  function card(entry) {
    const pron = accent => `<div class="pronunciation"><b>${accent === 'gb' ? 'Британська' : 'Американська'}</b><span class="ipa">${esc(entry.ipa[accent])}</span><span class="uk">${esc(entry.ukPhonetic[accent])}</span></div>`;
    const buttons = ['gb-female','gb-male','us-female','us-male'].map(voice => `<button type="button" data-word="${esc(entry.word)}" data-voice="${voice}" aria-label="Слухати ${esc(entry.word)}: ${voiceLabels[voice]}">▶ ${voiceLabels[voice]}</button>`).join('');
    const google = `https://www.google.com/search?q=${encodeURIComponent(entry.word + ' pronunciation')}`;
    const from = entry.lessons.length === 1 ? '1 урок' : `${entry.lessons.length} уроків`;
    return `<article class="entry"><h3>${esc(entry.word)}</h3><p class="translation" lang="uk"><strong>Переклад:</strong> ${entry.translationsUk.map(esc).join('; ')}</p><div class="pronunciations">${pron('gb')}${pron('us')}</div><p class="phonics"><strong>Phonics hint</strong><span lang="en">${esc(entry.phonics)}</span></p><div class="audio-grid">${buttons}</div><a class="lookup" href="${google}" target="_blank" rel="noopener noreferrer">Знайти вимову в Google ↗</a><p class="from">У матеріалах: ${from}</p></article>`;
  }
  function appendBatch() {
    const next = filtered.slice(shown, shown + 24);
    results.insertAdjacentHTML('beforeend', next.map(card).join(''));
    shown += next.length;
    more.hidden = shown >= filtered.length;
  }
  function render() {
    const query = search.value.trim().toLocaleLowerCase().replaceAll('’', "'");
    const selected = grade.value;
    filtered = entries.filter(entry => (entry.word.includes(query) || entry.translationsUk.some(value => value.toLocaleLowerCase('uk').replaceAll('’', "'").includes(query))) && (selected === 'all' || entry.lessons.some(path => path.startsWith(selected))));
    shown = 0;
    results.replaceChildren();
    count.textContent = `${filtered.length} слів`;
    if (filtered.length) appendBatch();
    else { results.innerHTML = '<p>Слів не знайдено. Спробуй інше написання або обери всі класи.</p>'; more.hidden = true; }
  }
  results.addEventListener('click', async event => {
    const button = event.target.closest('button[data-word]');
    if (!button) return;
    const entry = entries.find(item => item.word === button.dataset.word);
    if (!entry) return;
    if (playing) playing.classList.remove('playing');
    button.classList.add('playing');
    playing = button;
    player.src = entry.audio[button.dataset.voice];
    try { await player.play(); }
    catch { button.classList.remove('playing'); error.textContent = 'Не вдалося відтворити аудіо. Перевір з’єднання й спробуй ще раз.'; error.hidden = false; }
  });
  player.addEventListener('ended', () => { if (playing) playing.classList.remove('playing'); playing = null; });
  search.addEventListener('input', render);
  grade.addEventListener('change', render);
  more.addEventListener('click', appendBatch);
  const params = new URLSearchParams(location.search);
  search.value = params.get('q') || '';
  fetch('words.json').then(response => { if (!response.ok) throw new Error(response.status); return response.json(); }).then(data => {
    entries = data.entries;
    document.getElementById('totalWords').textContent = `${entries.length} слів`;
    render();
  }).catch(() => { error.textContent = 'Словник не завантажився. Онови сторінку й спробуй ще раз.'; error.hidden = false; count.textContent = ''; });
})();
