# ESL Lessons

Статичні інтерактивні уроки англійської, опубліковані через GitHub Pages.

## 6 клас

- [Jolly Phonics: 42 звуки](6/jolly-phonics/) — мобільний тренажер з чотирма наборами локального аудіо, історією проходжень, CSV-звітом, офлайн-кешем і встановленням як PWA.

## 7 клас

- [Unit 1: In and out of school](7/) — п’ять інтерактивних уроків про клуби, шкільні події та запитання в теперішньому часі.
- [Unit 2: Do your chores](7/) — п’ять інтерактивних уроків про хатні справи та запитання в минулому часі.

## Словник

- [Словник вимови](dictionary/) — слова з навчального тексту 6, 7 і 9 класів з IPA, наближеним українським записом, фонікс-підказкою та чотирма локальними записами вимови. [Як оновлювати](dictionary/README.md).

## 9 клас

- [Future Forms](9/future-forms/)
- [Future Forms Quest](9/future-forms-v2/)
- [Gerund: форма -ing](9/gerund/) — правила, слова-пастки, вправи та тест для 9 класу.

Для перевірки Jolly Phonics перед публікацією:

```bash
python3 tests/check_navigation.py
python3 scripts/build_dictionary.py --check
python3 tests/check_jolly_phonics.py
python3 tests/check_future_forms_v2.py
```

Інструкція із заміни карток, зображень, аудіо та безпечного оновлення кешу: [6/jolly-phonics/UPDATING.md](6/jolly-phonics/UPDATING.md).

Навігація сайту має три рівні: `/` → `/<клас>/` → `/<клас>/<матеріал>/`. Правила для нових матеріалів зафіксовані в [AGENTS.md](AGENTS.md) і перевіряються автоматично перед деплоєм.
