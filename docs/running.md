# Как запустить готовый сценарий

> Приложение использует поставляемые экспорты и небольшой граф пилота.
> Скачивание OSM и тяжёлый национальный пересчёт не входят в обычный запуск.

**Читайте, если** запускаете стенд или проверяете воспроизводимость · **Связано:** [Пайплайн](data-pipeline.md)

---

## Что нужно для первого запуска?

Docker с Compose. Первый build скачивает образы и зависимости; готовое приложение работает
без платных ключей и внешних модельных API. `.env` не требуется.

```bash
docker compose up --build -d
docker compose ps
```

Откройте `http://localhost:8080`. `PORT=8081` меняет только внешний порт frontend.
Backend доступен через `/api/v1` на том же адресе. В Compose его порт наружу не публикуется.
`docker compose down` останавливает эти два сервиса и не удаляет исходные данные.

## Где лежат данные?

`DATA_DIR` — каталог настоящих экспортов. В Compose это `/data`, read-only mount из
`frontend/atlas/public`. Там находятся `atlas.json`, дополнительные региональные данные,
`indices.json` и `pilots/tuva.json`. Приложение не читает сырые PBF и не меняет DuckDB.
Запрос пилота меняет только локальный сценарий запроса.

Отсутствующий или повреждённый пилот даёт 503 `data_unavailable`. Неизвестный пилот — 404,
устаревшие версии модели/артефакта — 409, неверная частота — 422. Healthcheck проверяет
живой процесс; он не доказывает готовность каждого необязательного экспорта.

## Как запустить разработку?

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

Vite проксирует `/api` на `http://localhost:8000`. `API_URL` меняет upstream разработки,
`API_SCHEMA_URL` — источник генерации типов. `SITE_URL` используется при сборке метаданных сайта.
При замене артефактов перезапустите backend: файлы читаются как неизменный снимок и кешируются.

## Какие проверки существуют?

| Команда | Что проверяет |
| --- | --- |
| `cd frontend && npm run verify` | Правила, типы, lint, unit-тесты и production build |
| `cd backend && uv run ruff check . && uv run mypy .` | Стиль и типы backend |
| `cd backend && uv run pytest tests/unit` | Бизнес-правила, HTTP, репозитории и импорты |
| `cd backend && uv run pytest tests/integration` | Поставляемый пилот и реальный API-путь с файловыми данными |
| `uv run python -m unittest discover -s tests` | Модель, ожидание, Palma, сжатие, сезонность и восстановление данных |
| `PYTHONPATH=backend/src uv run python etl/validate_pilot.py` | 24 независимых сравнения пилота и локальный benchmark |
| `uv run python etl/validate_indices.py` | Полный локальный расчёт индексов; требует DuckDB из пайплайна |

Desktop-сценарий на работающем стенде:

```bash
cd frontend
E2E_BASE_URL=http://127.0.0.1:8080 npx playwright test e2e/pilot-experiment.spec.ts e2e/national-index.spec.ts e2e/stand-resilience.spec.ts
```

Мобильные проверки не проводились. Внешние расписания и проходимость не проверяются
автоматическими тестами. Полная пересборка требует root-окружения `uv sync --python 3.12`,
свободного места для исходников и вычислений; параметры приведены в пайплайне.

---

<sub>[Оглавление документации](README.md) · [README проекта](../README.md)</sub>
