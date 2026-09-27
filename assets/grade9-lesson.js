(() => {
  const normalize = value => value.trim().toLocaleLowerCase().replace(/[.!?]+$/, '');
  document.querySelectorAll('.practice').forEach(panel => {
    const questions = [...panel.querySelectorAll('.question')];
    panel.querySelector('.check').addEventListener('click', () => {
      let score = 0;
      for (const question of questions) {
        const selected = question.querySelector('input:checked');
        const explanation = question.querySelector('.answer-why').textContent;
        const feedback = question.querySelector('.feedback');
        if (!selected) {
          feedback.textContent = 'Обери відповідь.';
          feedback.className = 'feedback bad';
          continue;
        }
        const correct = normalize(selected.value) === question.dataset.answer;
        if (correct) score++;
        feedback.textContent = `${correct ? 'Правильно!' : 'Спробуй ще.'} ${explanation}`;
        feedback.className = `feedback ${correct ? 'good' : 'bad'}`;
      }
      panel.querySelector('.result').textContent = `${score} із ${questions.length} правильно`;
    });
  });
  document.querySelectorAll('.write-card').forEach(card => {
    const input = card.querySelector('textarea');
    const key = `esl-${document.body.dataset.unit}-${document.body.dataset.lesson}`;
    try { input.value = localStorage.getItem(key) || ''; } catch {}
    card.querySelector('.save').addEventListener('click', () => {
      const status = card.querySelector('.saved');
      try {
        localStorage.setItem(key, input.value);
        status.textContent = 'Збережено на цьому пристрої.';
      } catch {
        status.textContent = 'Не вдалося зберегти. Скопіюй текст перед закриттям сторінки.';
      }
    });
  });
})();
