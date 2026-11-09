<p align="center">
<!-- readme:banner -->
<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/banner.dark.png"><img src="docs/readme/banner.light.png" width="880" height="308" alt="Plexus. Как меняется доступность рынков и поездок к центрам"></picture>
<!-- /readme:banner -->
</p>

Аналитик региональной политики сравнивает территории, меняет сообщение в пилоте Тывы
и видит, как изменяются маршрут, движение и ожидание при заданных условиях.

<p align="center">
<!-- readme:buttons -->
<a href="#запуск"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/button-run.dark.png"><img src="docs/readme/button-run.light.png" width="216" height="44" alt="Запустить локально"></picture></a>
<a href="docs/README.md"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/button-docs.dark.png"><img src="docs/readme/button-docs.light.png" width="175" height="44" alt="Документация"></picture></a>
<!-- /readme:buttons -->
</p>
<p align="center">
<!-- readme:status -->
<a href="#результаты"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/status-settlements.dark.png"><img src="docs/readme/status-settlements.light.png" width="229" height="28" alt="Населённых пунктов: 155 412"></picture></a>
<a href="#результаты"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/status-links.dark.png"><img src="docs/readme/status-links.light.png" width="161" height="28" alt="Ручных связей: 997"></picture></a>
<a href="#результаты"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/status-regions.dark.png"><img src="docs/readme/status-regions.light.png" width="119" height="28" alt="Регионов: 82"></picture></a>
<br>
<a href="#запуск"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/status-tests.dark.png"><img src="docs/readme/status-tests.light.png" width="193" height="28" alt="Проверки: API и браузер"></picture></a>
<a href="#запуск"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/status-offline.dark.png"><img src="docs/readme/status-offline.light.png" width="200" height="28" alt="Платные ключи: не нужны"></picture></a>
<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/status-locale.dark.png"><img src="docs/readme/status-locale.light.png" width="131" height="28" alt="Интерфейс: RU"></picture>
<!-- /readme:status -->
</p>
<p align="center">
<!-- readme:stack -->
<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/stack-frontend.dark.png"><img src="docs/readme/stack-frontend.light.png" width="194" height="28" alt="Фронтенд: React 19, Vite"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/stack-types.dark.png"><img src="docs/readme/stack-types.light.png" width="177" height="28" alt="Типы: TypeScript strict"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/stack-api.dark.png"><img src="docs/readme/stack-api.light.png" width="110" height="28" alt="API: FastAPI"></picture>
<br>
<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/stack-data.dark.png"><img src="docs/readme/stack-data.light.png" width="173" height="28" alt="Расчёт: DuckDB, OSM"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/stack-tools.dark.png"><img src="docs/readme/stack-tools.light.png" width="138" height="28" alt="Пакеты: uv, npm"></picture>
<!-- /readme:stack -->
</p>
<p align="center">
<!-- readme:nav -->
<a href="#зачем-это"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/nav-why.dark.png"><img src="docs/readme/nav-why.light.png" width="86" height="28" alt="Зачем это"></picture></a>
<a href="#как-это-работает"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/nav-how.dark.png"><img src="docs/readme/nav-how.light.png" width="130" height="28" alt="Как это работает"></picture></a>
<a href="#попробовать-за-две-минуты"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/nav-try.dark.png"><img src="docs/readme/nav-try.light.png" width="105" height="28" alt="Попробовать"></picture></a>
<a href="#результаты"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/nav-results.dark.png"><img src="docs/readme/nav-results.light.png" width="94" height="28" alt="Результаты"></picture></a>
<a href="#запуск"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/nav-run.dark.png"><img src="docs/readme/nav-run.light.png" width="66" height="28" alt="Запуск"></picture></a>
<a href="#устройство"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/nav-layout.dark.png"><img src="docs/readme/nav-layout.light.png" width="95" height="28" alt="Устройство"></picture></a>
<br>
<a href="#ограничения"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/nav-limits.dark.png"><img src="docs/readme/nav-limits.light.png" width="105" height="28" alt="Ограничения"></picture></a>
<!-- /readme:nav -->
</p>

> Расчёт показывает эффект в модели. Историческая публикация о рейсе и отсутствие
> тега закрытия в OSM не подтверждают действующее сообщение или проходимость дороги.

## Зачем это

Для Кунгуртуга увеличение частоты с двух до четырёх рейсов в неделю даёт нулевой
выигрыш: дорожная альтернатива ещё быстрее авиации с ожиданием. Семь рейсов дают
другой результат. Поэтому предложение оценивается вместе с альтернативами,
а частота сама по себе не служит мерой хорошей связанности.

Россия представлена потенциальной доступностью 180 рынков по Hansen.
Пилот Тывы оценивает конкретные поездки жителей к названным центрам.
Пользователь выбирает вывод и следующий шаг проверки по данным, а не по числу линий на карте.

## Как это работает

| Участок | Правило | Проверка |
| --- | --- | --- |
| Россия | Население рынка с экспоненциальным затуханием по времени; полупериод 2 ч | Одна дорожная база, чувствительность 1/2/4 ч, покрытие и манифест |
| Тыва | Минимум движения с накладными и ожидания `84/f` при равных интервалах | Независимый расчёт 24 комбинаций, отдельный контроль расписания |
| Сценарий | Меняются только существующие связи, сезон и целая частота 1–28 | Версии, валидация API, неизменность входов |

Источники и периоды раскрываются в интерфейсе. Неизвестная частота сохраняется
неизвестной; допущение отмечается. Если неизвестные альтернативы могут быть быстрее,
путь не объявляется доказанным оптимумом. Отсутствие пути имеет отдельный статус.

## Попробовать за две минуты

1. Откройте карту, выберите «Доступность рынков Hansen», сезон и режим транспорта.
2. Откройте «Пилот Тывы», задайте первой авиационной линии 7 рейсов в неделю и нажмите «Пересчитать».
3. Сравните 18,10 и 14,24 ч, откройте маршрут, выгрузите CSV и JSON. Затем попробуйте 4 рейса: эффект нулевой.

[Маршрут жюри](docs/for-jury.md) связывает действия с доказательствами.
[Карта требований](docs/requirements-map.md) отдельно отмечает неподтверждённые прошлые события и отправку.

## Результаты

| Проверенный опыт | Результат | Граница вывода |
| --- | --- | --- |
| Кунгуртуг → Кызыл, 2 → 4 рейса | 18,095 → 18,095 ч | Условная дорожная альтернатива остаётся быстрее |
| Та же поездка, 2 → 7 рейсов | 18,095 → 14,243 ч | Выигрыш 3,852 ч при частотной модели |
| Сезонная связь Сыстыг-Хем → Тоора-Хем отключена | Пути нет | Относится к рассматриваемой сети |
| Независимый контроль пилота | 24 комбинации совпали | Время и статус на том же графе, не полевая валидация |
| Национальный входной масштаб | 82 региона, 155412 пунктов | Частичные федеральные города исключены; не всё население России |

Методы, даты, версии и протоколы приведены в [доказательствах](docs/evidence.md).
Отрицательный результат четырёх рейсов сохранён. Затраты, ВРП и пассажиропоток не оценивались.

<details><summary>Повторить расчёт пилота</summary>

```bash
uv sync --python 3.12
PYTHONPATH=backend/src uv run python etl/validate_pilot.py
uv run python -m unittest discover -s tests
```

Проверка использует поставляемый артефакт; тяжёлая национальная пересборка отделена
от запуска приложения и описана в [пайплайне](docs/data-pipeline.md).

</details>

## Запуск

```bash
docker compose up --build -d
docker compose ps
```

Приложение: **http://localhost:8080**. API доступен через `/api/v1` на том же адресе.
Первичная сборка скачивает образы и зависимости. Работа готового сценария не требует
платных ключей, регистрации или скачивания исходных графов.
Для другого порта: `PORT=8081 docker compose up --build -d`.

<details><summary>Разработка и проверки</summary>

```bash
cd backend
uv sync
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Во втором терминале:

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 8080
```

```bash
cd frontend
npm run verify
E2E_BASE_URL=http://127.0.0.1:8080 npx playwright test e2e/pilot-experiment.spec.ts
```

```bash
cd backend
uv run ruff check .
uv run mypy .
uv run pytest tests/unit tests/integration
```

`DATA_DIR` задаёт каталог настоящих экспортов. Compose монтирует поставляемые данные
только для чтения. Healthcheck проверяет живой процесс; отсутствие конкретного артефакта
возвращает честную ошибку соответствующего API. Подробнее: [запуск](docs/running.md).

</details>

## Устройство

React, Vite и TypeScript; FastAPI с разделением domain/usecase/repository/controller;
отдельный пакетный расчёт на DuckDB, NumPy и SciPy. Текущий интерфейс находится в `frontend/`.
`frontend/atlas/public` содержит данные API; старый интерфейс атласа не является вторым продуктом.

| Материал | Назначение |
| --- | --- |
| [Документация](docs/README.md) | Методика, API, источники, ограничения и воспроизводимость |
| [Пилот](docs/pilot-method.md) | Поездки, варианты, ожидание и проверка |
| [Реестр ИИ](docs/ai-register.md) | Задачи, инструменты, материалы и найденные ошибки |
| [Комплект сдачи](docs/submission/README.md) | Паспорт, семь слайдов, речь и статус отправки |

Контур Крыма дополнен из geoBoundaries / OpenStreetMap (2017). Локально подключены 653 автобусных маршрута Ставрополья; они не входят в зафиксированный расчёт национальных индексов.

## Ограничения

- **Транспортные сведения исторические.** Действующее расписание и проходимость OSM не проверены на месте.
- **Время условное.** Равные интервалы и независимые пересадки упрощают реальные поездки; сезон не означает конкретную дату открытия.
- **Экономический эффект не рассчитан.** Без затрат и спроса модельный выигрыш не определяет инвестиционный приоритет.

Полный перечень и статусы: [ограничения](docs/limitations.md).
Данные OSM распространяются на условиях [ODbL](https://www.openstreetmap.org/copyright).
Источники, лицензии и периоды перечислены в манифестах; наличие URL не заменяет проверку.

<p align="center">
<!-- readme:footer -->
<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/footer.dark.png"><img src="docs/readme/footer.light.png" width="98" height="44" alt="Plexus"></picture>
<!-- /readme:footer -->
</p>
