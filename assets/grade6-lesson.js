(() => {
  document.querySelectorAll('.practice').forEach(panel => {
    const items = [...panel.querySelectorAll('.question')];
    panel.querySelector('.check').addEventListener('click', () => {
      let score = 0, answered = 0;
      items.forEach(item => {
        const selected = item.querySelector('input:checked');
        const ok = Boolean(selected && selected.value === item.dataset.answer);
        const feedback = item.querySelector('.feedback');
        if (selected) answered++;
        if (ok) score++;
        feedback.textContent = !selected ? 'Обери відповідь.' : (ok ? 'Правильно. ' : 'Поки неправильно. ') + item.querySelector('.answer-why').textContent;
        feedback.className = 'feedback ' + (ok ? 'good' : 'bad');
      });
      panel.querySelector('.result').textContent = `${score} із ${items.length} правильно. Відповідей: ${answered} із ${items.length}.`;
    });
    panel.querySelector('.reset').addEventListener('click', () => {
      items.forEach(item => {
        item.querySelectorAll('input').forEach(input => input.checked = false);
        const feedback = item.querySelector('.feedback');
        feedback.textContent = '';
        feedback.className = 'feedback';
      });
      panel.querySelector('.result').textContent = '';
    });
  });
  document.querySelectorAll('textarea[data-save]').forEach(input => {
    const card = input.closest('.write-card');
    const key = `esl-grade6-${document.body.dataset.lesson}-${input.dataset.save}`;
    try { input.value = localStorage.getItem(key) || ''; } catch {}
    card.querySelector('.save-notes').addEventListener('click', () => {
      const status = card.querySelector('.saved');
      try { localStorage.setItem(key, input.value); status.textContent = 'Збережено на цьому пристрої.'; }
      catch { status.textContent = 'Не вдалося зберегти. Скопіюй текст перед закриттям сторінки.'; }
    });
  });
  document.addEventListener('play', event => {
    if (!event.target.matches('audio, video')) return;
    document.querySelectorAll('audio, video').forEach(other => {
      if (other !== event.target) other.pause();
    });
  }, true);
})();
