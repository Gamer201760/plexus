# Запуск и проверки

Сейчас Compose запускает фронтенд и бэкенд. У бэкенда один метод — `GET /api/v1/health`; сценарии,
база данных и миграции будут добавлены при реализации проекта.

**Читайте, если** вы запускаете шаблон · **Связано:** [архитектура](architecture.md) · [зависимости](dependencies.md)

## Как запустить через Docker?

Нужны Docker и Compose v2. Из корня репозитория:

```bash
cp .env.example .env
docker buildx bake
docker compose up
```

Интерфейс: http://localhost:8080, API: http://localhost:8000, Swagger: http://localhost:8000/docs.
Образы собирает только `docker-bake.hcl`; Compose берёт готовые образы
`<COMPOSE_PROJECT_NAME>-backend:<TAG>` и `<COMPOSE_PROJECT_NAME>-frontend:<TAG>` и не скачивает их
из реестра. Без сборки `docker compose up` остановится с ошибкой об отсутствующем образе.
Переменные контейнеров приходят из `.env` через `env_file`; без `.env` действуют значения по
умолчанию. Первичная сборка требует сети для загрузки зависимостей и образов.

Образ бэкенда по умолчанию собирается без SDK Claude и Codex. Чтобы включить `LANGUAGE_MODEL`,
соберите образ с флагом `LLM`:

```bash
LLM=true docker buildx bake
docker compose up
```

Переменные сборки (`LLM`, `TAG`, `SITE_URL`, `COMPOSE_PROJECT_NAME`) bake берёт из окружения, а не
из `.env`.

## Как разрабатывать без Docker?

Нужны Node.js 22.18+ или поддерживаемая более новая версия и npm.

```bash
cd frontend
npm ci
npm run dev
```

Адрес покажет Vite при запуске. Бэкенд без Docker, из корня:

```bash
cd backend
uv sync                      # группы dev и llm; без SDK LLM: uv sync --no-group llm
uv run uvicorn app.main:create_app --factory --reload
```

## Какие переменные читает бэкенд?

Все необязательны: без них работает офлайн-реализация.

| Переменная | По умолчанию | Что задаёт |
|---|---|---|
| `DECISION_MODEL` | `lexical` | `lexical` — офлайн-замена; `system_one` — HTTP-модель по контракту `/v1/systemone` |
| `DECISION_MODEL_URL` | `https://api.typesafe.ai` | Адрес модели для `system_one`, например локальный `laya-serve` |
| `DECISION_MODEL_API_KEY` | пусто | Ключ для `system_one`; без него заголовок `Authorization` не отправляется |
| `DECISION_MODEL_TIMEOUT_S` | `10` | Таймаут запроса к модели, секунды |
| `LANGUAGE_MODEL` | `none` | `none`, `claude` или `codex` |
| `BACKEND_PORT` | `8000` | Порт бэкенда на хосте в Compose |
| `LLM` | `false` | Сборка: `true` ставит в образ SDK Claude и Codex |
| `TAG` | `latest` | Тег образов Compose и bake |

Неизвестное значение останавливает запуск с ошибкой, где названа переменная и допустимые значения.

## Как проверить фронтенд и презентацию?

Из корня, каждую команду отдельно:

```bash
(cd frontend && npm run verify)
(cd presentation && npm ci && npm run build)
```

## Как проверить бэкенд?

Нужен [uv](https://docs.astral.sh/uv/). Из корня:

```bash
cd backend
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest tests/unit
uv run pytest tests/integration
```

`tests/unit` работает без базы и сети; `tests/integration` требует локальную инфраструктуру
(PostgreSQL, запущенный стенд). `uv run pytest` запускает обе группы. Число процессов pytest-xdist
зависит от размера набора: маленький идёт в один процесс.

Тесты адаптера Claude подменяют вызов SDK и не ходят в сеть. Реальный вызов требует
`ANTHROPIC_API_KEY` или вход в Claude Code и расходует оплату.

## Что делать, если не запускается?

| Симптом | Что проверить |
|---|---|
| Порт 8080 занят | Задайте свободный `FRONTEND_PORT` в `.env` |
| Порт 8000 занят | Задайте свободный `BACKEND_PORT` в `.env` |
| Ошибка состояния API | `docker compose ps backend` и `docker compose logs backend`; затем `API_UPSTREAM` |
| `ConfigError` при старте бэкенда | Значение переменной из сообщения; допустимые перечислены там же |
| `LANGUAGE_MODEL=claude needs package` | Образ собран без SDK: пересоберите с `LLM=true` |
| `No such image` при `docker compose up` | Образы не собраны: `docker buildx bake` с теми же `COMPOSE_PROJECT_NAME` и `TAG` |
| Зависимости не скачиваются | Доступ к реестрам npm и Docker во время сборки |

---

<sub>[Оглавление документации](README.md) · [README проекта](../README.md)</sub>
