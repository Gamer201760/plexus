import collections
import csv
import datetime
import io
import json
import pathlib
import zipfile


ROOT = pathlib.Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def airports():
    folder = ROOT / 'ourairports-russia'
    derived = folder / 'derived'
    derived.mkdir(exist_ok=True)
    with (folder / 'raw/airports.csv').open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = [row for row in reader if row['iso_country'] == 'RU']
    identifiers = {row['ident'] for row in rows}
    ids = {row['id'] for row in rows}
    write_csv(derived / 'airports_ru.csv', rows, fields)
    support_counts = {}
    for name in ['runways', 'airport-frequencies', 'navaids', 'regions', 'countries']:
        with (folder / f'raw/{name}.csv').open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            support_fields = reader.fieldnames
            support = []
            for row in reader:
                included = row.get('airport_ident') in identifiers or row.get('airport_ref') in ids
                included = included or row.get('iso_country') == 'RU'
                included = included or (name == 'countries' and row.get('code') == 'RU')
                if included:
                    support.append(row)
        support_counts[name] = len(support)
        write_csv(derived / f'{name}_ru.csv', support, support_fields)
    by_region = collections.Counter(row['iso_region'] for row in rows)
    scheduled = collections.Counter(row['iso_region'] for row in rows if row['scheduled_service'] == 'yes')
    with (derived / 'regions_ru.csv').open(encoding='utf-8') as stream:
        names = {row['code']: row['name'] for row in csv.DictReader(stream)}
    coverage = [dict(region_code=code, region_name=names.get(code, ''), airports=number,
                     scheduled_service_yes=scheduled[code]) for code, number in sorted({code: by_region[code] for code in set(names) | set(by_region)}.items())]
    write_csv(folder / 'coverage_by_region.csv', coverage, ['region_code', 'region_name', 'airports', 'scheduled_service_yes'])
    profile = dict(rows=len(rows), fields=fields, source_filter="iso_country == 'RU'",
                   regions_with_records=len(by_region), regions_in_dictionary=len(names),
                   regions_without_records=sorted(set(names) - set(by_region)), support_rows=support_counts,
                   types=dict(collections.Counter(row['type'] for row in rows)),
                   scheduled_service=dict(collections.Counter(row['scheduled_service'] for row in rows)),
                   missing={field: sum(not row[field] for row in rows) for field in fields})
    write_json(folder / 'profile.json', profile)
    (folder / 'README.md').write_text(f'''# OurAirports: аэропорты России

Скачаны исходные глобальные CSV аэропортов, полос, частот, навигационных средств, стран и регионов. Из них получены полные выборки записей с кодом страны RU и связанные полосы/частоты. Географию определяет классификация источника.

- Источник: https://ourairports.com/data/; файлы: https://davidmegginson.github.io/ourairports-data/.
- Период: текущий снимок изменяемого справочника, не исторический ряд перевозок.
- Условия источника: Public Domain; точность не гарантируется.
- Российская выборка: {len(rows)} объектов, {len(by_region)} кодов регионов с записями.
- Типы объектов: {json.dumps(profile['types'], ensure_ascii=False)}.

## Что лежит в папке

`raw/` — исходные CSV без правок. `derived/*_ru.csv` — российские выборки. [coverage_by_region.csv](coverage_by_region.csv) показывает число объектов и отметок регулярного сообщения по региону. [profile.json](profile.json) содержит схему, число строк и пропуски; [metadata.json](metadata.json) — ссылки, размер и SHA-256.

Координаты, тип и коды можно использовать для привязки авиационных узлов. Включены закрытые объекты, вертолётные площадки и небольшие аэродромы. Пустой IATA не означает ошибку; наличие аэропорта и scheduled_service не доказывают доступность рейса, его частоту, цену или актуальное расписание. Покрытие справочника не равно полноте транспортного обслуживания.

Повторная подготовка: `python3 datasets/profile_geography.py` из корня проекта.
''')


def geonames():
    folder = ROOT / 'geonames-russia'
    derived = folder / 'derived'
    derived.mkdir(exist_ok=True)
    fields = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude',
              'feature_class', 'feature_code', 'country_code', 'cc2', 'admin1_code',
              'admin2_code', 'admin3_code', 'admin4_code', 'population', 'elevation',
              'dem', 'timezone', 'modification_date']
    names = {}
    with (folder / 'raw/admin1CodesASCII.txt').open(encoding='utf-8') as stream:
        for row in csv.reader(stream, delimiter='\t'):
            if row[0].startswith('RU.'):
                names[row[0][3:]] = row[1]
    classes, codes, regions, missing = (collections.Counter() for _ in range(4))
    zero_population = 0
    total = 0
    dates = []
    with zipfile.ZipFile(folder / 'raw/RU.zip') as archive:
        assert archive.testzip() is None
        with archive.open('RU.txt') as binary, (derived / 'populated_places_ru.csv').open('w', newline='', encoding='utf-8') as output:
            writer = csv.writer(output)
            writer.writerow(fields)
            for row in csv.reader(io.TextIOWrapper(binary, encoding='utf-8'), delimiter='\t'):
                assert len(row) == len(fields)
                total += 1
                classes[row[6]] += 1
                if row[6] != 'P':
                    continue
                writer.writerow(row)
                codes[row[7]] += 1
                regions[row[10]] += 1
                zero_population += row[14] in ('', '0')
                for field, value in zip(fields, row):
                    missing[field] += not bool(value)
                if row[18]:
                    dates.append(row[18])
    coverage = [dict(admin1_code=code, region_name=names.get(code, ''), populated_places=number)
                for code, number in sorted(regions.items())]
    write_csv(folder / 'coverage_by_region.csv', coverage, ['admin1_code', 'region_name', 'populated_places'])
    profile = dict(raw_rows=total, feature_classes=dict(classes), populated_place_rows=sum(regions.values()),
                   populated_place_codes=dict(codes), regions_with_records=len(regions),
                   mapped_region_codes=sum(code in names for code in regions),
                   records_without_mapped_region=sum(count for code, count in regions.items() if code not in names),
                   zero_or_missing_population=zero_population, missing=dict(missing), fields=fields,
                   minimum_modification_date=min(dates), maximum_modification_date=max(dates))
    write_json(folder / 'profile.json', profile)
    (folder / 'README.md').write_text(f'''# GeoNames: географические объекты и населённые пункты России

Скачана полная страновая выгрузка RU.zip и справочники административных кодов, типов объектов и стран.

- Источник: https://download.geonames.org/export/dump/.
- Описание полей и лицензии: https://download.geonames.org/export/dump/readme.txt.
- Лицензия: CC BY 4.0; требуется указание GeoNames. Данные предоставлены без гарантии полноты и точности.
- Исходных записей: {total}; населённых пунктов класса P: {sum(regions.values())}; кодов admin1 с такими записями: {len(regions)}.
- Регионов, сопоставленных справочнику GeoNames: {profile['mapped_region_codes']}; записей без сопоставленного региона: {profile['records_without_mapped_region']}.
- С нулевой или отсутствующей численностью: {zero_population} населённых пунктов. Ноль не подтверждает отсутствие жителей.

## География и полнота

[coverage_by_region.csv](coverage_by_region.csv) перечисляет коды admin1, названия и количество записей. Эти коды принадлежат GeoNames и не равны автоматически кодам Росстата/ФИАС/ISO. Требуется отдельное сопоставление перед объединением источников.

`raw/RU.zip` сохранён без изменений, без распаковки всего архива на диск. `derived/populated_places_ru.csv` — все записи класса P с исходными 19 полями. Справочник содержит также исторические и заброшенные места: типы перечислены в [profile.json](profile.json). Файл не является переписью населения и не доказывает полноту всех официальных населённых пунктов.

Период неоднороден: modification_date — дата обновления записи, а не единая дата наблюдения населения. Координаты годятся для предварительного сопоставления, не описывают транспортные связи.

Размеры, время скачивания, ссылки и SHA-256 — в [metadata.json](metadata.json). Повторная подготовка: `python3 datasets/profile_geography.py`.
''')


def calendars():
    folder = ROOT / 'production-calendar'
    derived = folder / 'derived'
    derived.mkdir(exist_ok=True)
    inventory = []
    with zipfile.ZipFile(folder / 'raw/isdayoff-calendars-main.zip') as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            if not name.endswith('.json'):
                continue
            data = json.loads(archive.read(name))
            if data.get('countrycode', '').lower().startswith('ru'):
                output = derived / pathlib.Path(name).name
                output.write_bytes(archive.read(name))
                inventory.append({'file': output.name, 'year': data['year'], 'countrycode': data['countrycode']})
    values = (folder / 'raw/ru-2026-api.txt').read_text().strip()
    assert len(values) == 365 and set(values) <= {'0', '1', '2', '4'}
    start = datetime.date(2026, 1, 1)
    rows = [{'date': str(start + datetime.timedelta(days=i)), 'api_code': value} for i, value in enumerate(values)]
    write_csv(derived / 'ru-2026-api.csv', rows, ['date', 'api_code'])
    profile = dict(russian_calendars=inventory, api_year=2026, api_rows=len(rows), api_codes=dict(collections.Counter(values)))
    write_json(folder / 'profile.json', profile)
    years = sorted({row['year'] for row in inventory if row['countrycode'] == 'ru'})
    (folder / 'README.md').write_text(f'''# Производственный календарь isDayOff

Скачан полный снимок официального репозитория календарей сервиса и ответ API для России за 2026 год.

- Первоисточник: https://github.com/isdayoff/calendars; описание JSON находится в README внутри архива.
- Ответ API: https://isdayoff.ru/api/getdata?year=2026&cc=ru.
- Общероссийские годы в репозитории: {', '.join(map(str, years))}. Есть отдельные региональные календари за 2022 год; точный список — [profile.json](profile.json).
- Ответ API содержит {len(values)} дневных кодов; он развёрнут в `derived/ru-2026-api.csv`. Код 0 — рабочий день, 1 — нерабочий. Исходная строка сохранена отдельно.

В `raw/` лежат исходный ZIP и текст API; в `derived/` — все JSON с countrycode ru или региональным ru-* и календарь с датами. Это календарь, а не транспортная статистика: можно использовать как временной признак. Региональные праздники представлены не для всех лет/регионов. Перспективные календари могут пересматриваться. Отдельная лицензия в скачанном репозитории не обнаружена; публичность репозитория не приравнивается к CC0.

Ссылки, время получения, размеры и SHA-256 — в [metadata.json](metadata.json). Полная дата-таблица API проверена на 365 кодов. Скрипты из архива не выполнялись.
''')


if __name__ == '__main__':
    airports()
    geonames()
    calendars()
