# Какие зависимости и права относятся к поставке

> Данные и код имеют разные условия использования. Ссылки и версии ниже позволяют проверить происхождение без приписывания общей лицензии всему комплекту.

**Читайте, если** переиспользуете код или данные

---


## Где зафиксированы версии?

| Часть | Версия и состав | Условия |
| --- | --- | --- |
| Frontend | [package.json](../frontend/package.json), [lockfile](../frontend/package-lock.json) | Лицензия каждого пакета из его метаданных; React, Vite, TypeScript |
| Backend | [pyproject.toml](../backend/pyproject.toml), [uv.lock](../backend/uv.lock) | FastAPI, Pydantic и зависимости из lockfile |
| ETL | [pyproject.toml](../pyproject.toml), [uv.lock](../uv.lock) | DuckDB, NumPy, SciPy, Pandas, PyArrow |
| Шрифты | Onest и JetBrains Mono, поставляются локально | SIL Open Font License в пакетах шрифтов |
| Дорожные данные | OpenStreetMap, выгрузка Geofabrik | [ODbL и атрибуция](https://www.openstreetmap.org/copyright) |
| Табличные источники | Каталог «Если быть точным» | Лицензии и первичные организации проверять по конкретному набору; [реестр](../datasets/README.md) |

Репозиторий не устанавливает отдельную открытую лицензию команды на весь код. Нельзя считать перечень зависимостей разрешением на переиспользование любых исходных публикаций. Для новой поставки нужно отдельно согласовать лицензию кода и условия распространения конкретных данных.

---

<sub>[Оглавление документации](README.md) · [README проекта](../README.md)</sub>

## Провайдер чата

Pydantic AI 2.66.0 использует `openai-codex` 0.167.0 и Responses API.
Для локального запуска требуется действующая авторизация `codex login` через ChatGPT.
[Codex SDK](https://learn.chatgpt.com/docs/codex-sdk),
[Responses provider](https://pydantic.dev/docs/ai/models/openai-codex/).
