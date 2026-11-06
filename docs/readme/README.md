# Картинки README

Баннер, кнопки, бейджи фактов, стека и разделов, знак в подвале README. Каждая картинка — в двух
вариантах, `*.light.png` и `*.dark.png`, README выбирает вариант по теме GitHub через `<picture>`.

Картинки не рисуются руками: их рендерит браузер из [`presentation/readme/assets.html`](../../presentation/readme/assets.html)
на токенах, шрифтах и знаке продукта, поэтому README выглядит так же, как интерфейс и презентация.

| Что поменять | Где |
|---|---|
| Кнопки и бейджи: тексты, ссылки, акцент | `presentation/readme/readme.json` |
| Обещание на баннере | `presentation/readme/assets.html` |
| Цвета, шрифты, скругления | токены фронтенда, затем `cd frontend && npm run tokens:export` |
| Знак | шаблон `brand-mark` в `presentation/src/shell.html` |

Пересборка: `cd presentation && npm run readme`. Команда заново снимает все картинки в 2x, пересобирает
ряды кнопок и бейджей в README, проставляет размеры картинок и красит mermaid-диаграммы README и
документации цветами продукта. Числа в бейджах совпадают с разделом «Результаты» README и с
[доказательствами](../evidence.md).

<sub>[Оглавление документации](../README.md) · [README проекта](../../README.md)</sub>
