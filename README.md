# ESL Lessons

Статичні інтерактивні уроки англійської, опубліковані через GitHub Pages.

## 6 клас

- [Jolly Phonics: 42 звуки](6/jolly-phonics/) — мобільний тренажер з чотирма наборами локального аудіо, історією проходжень, CSV-звітом, офлайн-кешем і встановленням як PWA.

## 9 клас

- [Future Forms](9/future-forms/)
- [Future Forms Quest](9/future-forms-v2/)

Для перевірки Jolly Phonics перед публікацією:

```bash
python3 tests/check_navigation.py
python3 tests/check_jolly_phonics.py
python3 tests/check_future_forms_v2.py
```

Інструкція із заміни карток, зображень, аудіо та безпечного оновлення кешу: [6/jolly-phonics/UPDATING.md](6/jolly-phonics/UPDATING.md).

Навігація сайту має три рівні: `/` → `/<клас>/` → `/<клас>/<матеріал>/`. Правила для нових матеріалів зафіксовані в [AGENTS.md](AGENTS.md) і перевіряються автоматично перед деплоєм.
