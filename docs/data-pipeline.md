# Как воспроизвести данные и расчёт

> Запуск приложения использует готовые экспорты. Тяжёлый пайплайн отдельно скачивает
> исходники, строит граф, вычисляет времена и индексы, затем проверяет кандидат экспорта.

**Читайте, если** воспроизводите результаты · **Связано:** [Запуск приложения](running.md) · [Метод](indices.md)

---

## Какие входы зафиксированы?

Табличные источники «Если быть точным» и Росстата задаются в `etl/sources.py`.
`etl/download.py` проверяет архив, безопасно извлекает во временный каталог, сохраняет
URL, время получения, HTTP-метаданные и SHA-256, затем переносит завершённый источник.
Повторный запуск сверяет хеши. Непроверенный существующий каталог не считается успехом.

Десять Geofabrik PBF имеют общий исходный timestamp `2026-11-07T21:21:36Z`.
OSM распространяется по [ODbL](https://www.openstreetmap.org/copyright).
Для табличных архивов в реестре сохранена декларация каталога CC BY 4.0;
она не распространяется автоматически на все региональные тексты и внешние публикации.
Ручной реестр хранит URL, период и уверенность, но наличие URL не подтверждает актуальность.

Манифесты под `data/` относятся к полным локальным входам. Краткие манифесты и протоколы
результата поставляются в `docs/results/`; сырые PBF и DuckDB в Git не включены.

Готовые `data/graph_ru/` и `data/casechamp.duckdb` опубликованы с SHA-256 в релизе
[`data-20261107`](https://github.com/GoatWhistle/casechamp/releases/tag/data-20261107);
скачивание избавляет от пересборки графа и матрицы времён:

```bash
gh release download data-20261107 -R GoatWhistle/casechamp -D data
tar -xf data/graph_ru.tar -C data && rm data/graph_ru.tar
```

## Как восстановить национальный слой?

Нужны Python 3.12, uv, сеть для исходников и свободное место под граф/базу. Граф содержит
6991438 узлов и 17395685 ориентированных рёбер до симметризации расчёта.

```bash
uv sync --python 3.12
uv run python etl/download.py
uv run python etl/load.py
uv run python etl/download_osm.py
uv run python etl/osm_extract.py data/raw/osm_russia/*.osm.pbf
uv run python etl/graph_russia.py
uv run python etl/manual_links.py
uv run python etl/access_russia.py
uv run python etl/indices.py
uv run python etl/validate_indices.py
uv run python etl/export_indices.py
uv run python etl/index_sensitivity.py
```

Последний шаг пишет `data/index_candidate/indices.json` и манифест. После проверки
кандидат переносится в `frontend/atlas/public/indices.json`; backend перезапускается.
Пайплайн не заменяет работающий экспорт в ходе поиска путей. SQL-загрузка, времена и
индексы используют транзакции; не запускайте двух писателей одной DuckDB одновременно.

`OSM_GLOB` ограничивает набор извлечённых файлов для контрольной сборки,
`GRAPH_OUTPUT` меняет каталог графа, `POINT_REGION` ограничивает точки привязки.
Такой частичный граф не должен подменять полный национальный граф.
`SCENARIOS` выбирает расчётные режимы; `APPEND_SCENARIOS=1` заменяет только выбранные
сценарии в одной транзакции, сохраняя остальные. Условия модели и версии входов при этом
должны совпадать. Экспорт проверяет состав пяти сценариев, но не доказывает одинаковое
происхождение частично заменённых матриц. Публикуемый расчёт выполнен одной серией всех пяти
сценариев; для новой модели требуется такая же полная серия.

## Как восстановить пилот?

Пилот использует тот же сибирский PBF и реестр `data_manual/tuva_links.csv`.
Отдельный каталог графа предотвращает подмену национального слоя.

```bash
OSM_GLOB=siberian.parquet GRAPH_OUTPUT=data/pilot_graph_build POINT_REGION='Республика Тыва' uv run python etl/graph_russia.py
PYTHONPATH=backend/src uv run python etl/pilot_export.py
PYTHONPATH=backend/src uv run python etl/validate_pilot.py --data-dir data/pilot_candidate --output data/pilot-candidate-validation.json
uv run python etl/audit_pilot_routes.py
```

Кандидат пилота находится в `data/pilot_candidate/pilots/tuva.json`. После проверки его
публикуют в `frontend/atlas/public/pilots/`. Для готового поставляемого артефакта команда
`PYTHONPATH=backend/src uv run python etl/validate_pilot.py` работает без восстановления PBF
и обновляет `docs/results/pilot-validation.json`. Для кандидата путь отчёта задаётся отдельно,
чтобы его проверка не подменяла протокол поставляемого артефакта.
Дорожные пути имеют списки исходных way; редактируемая сезонная связь Сыстыг-Хема не
спрятана в матрице. Внешняя проходимость и действующее расписание остаются ограничениями.

## Где находятся прежние интерфейс и расчёты?

Актуальное приложение — `frontend/`; оно получает результаты через API.
`frontend/atlas/public` — каталог данных API. Оставшиеся скрипты `frontend/atlas` подготавливают данные; рабочий интерфейс запускается
только из `frontend/`.
Старый экспортёр `frontend/atlas/scripts/export-indices.py` не используется в принятой
сборке: полный контракт, покрытие и версии экспортирует `etl/export_indices.py`.
Исследования под другой формулой отделены от текущих результатов в приложениях.

---

<sub>[Оглавление документации](README.md) · [README проекта](../README.md)</sub>
