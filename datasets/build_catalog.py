import collections
import csv
import datetime
import hashlib
import json
import pathlib
import zipfile


ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = ROOT.parent
STATUS = {
    'downloaded': 'скачан',
    'partial': 'частично',
    'blocked': 'доступ не получен',
    'needs_parameters': 'нужны параметры',
    'deferred_disk': 'не помещается на диск',
    'excluded_by_user': 'исключён пользователем',
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            digest.update(chunk)
    return digest.hexdigest()


def stringify(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value or '')


def file_kind(path):
    if path.name == 'download-file-info.json':
        return 'metadata'
    if path.suffix.lower() in ('.html', '.htm'):
        return 'source_snapshot'
    if path.suffix.lower() == '.pdf':
        return 'report'
    return 'data'


def main():
    lines = [line for line in (PROJECT / 'docs/istochniki_dannyh.md').read_text().splitlines()
             if line.startswith('|')]
    sources = {number: line.split('|')[1].strip() for number, line in enumerate(lines[2:], 1)}
    assert len(sources) == 38
    records = {}
    manifest = []
    issues = []
    for path in sorted(ROOT.glob('*/metadata.json')):
        metadata = json.loads(path.read_text())
        number = int(metadata['source_row'])
        assert number not in records, ('Duplicate source row', number)
        assert metadata['status'] in STATUS, metadata['status']
        folder = path.parent
        assert (folder / 'README.md').exists(), folder
        expected = {item['path']: item for item in metadata.get('files', [])}
        files = []
        for subfolder in ['raw', 'derived']:
            for file in sorted((folder / subfolder).rglob('*')):
                if not file.is_file():
                    continue
                relative = file.relative_to(folder).as_posix()
                digest = sha256(file)
                entry = expected.get(relative, {})
                if entry.get('sha256'):
                    assert digest == entry['sha256'], file
                expected_size = entry.get('bytes', entry.get('size_bytes'))
                if expected_size is not None:
                    assert file.stat().st_size == expected_size, file
                with file.open('rb') as stream:
                    prefix = stream.read(512)
                suffix = file.suffix.lower()
                if suffix == '.pdf':
                    assert prefix.startswith(b'%PDF-'), file
                if suffix in ('.zip', '.xlsx'):
                    assert zipfile.is_zipfile(file), file
                if suffix not in ('.html', '.htm'):
                    assert b'<!doctype html' not in prefix.lower(), file
                    assert b'<html' not in prefix.lower(), file
                item = {
                    'source_row': number,
                    'dataset': folder.name,
                    'path': file.relative_to(PROJECT).as_posix(),
                    'kind': file_kind(file),
                    'derived': subfolder == 'derived',
                    'bytes': file.stat().st_size,
                    'sha256': digest,
                    'url': entry.get('url', entry.get('download_url', '')),
                }
                files.append(item)
                manifest.append(item)
        for name in expected:
            if not (folder / name).exists():
                issues.append(f'{folder.name}: metadata file missing: {name}')
        raw_files = [item for item in files if not item['derived'] and item['kind'] in ('data', 'report')]
        derived_files = [item for item in files if item['derived'] and item['kind'] in ('data', 'report')]
        records[number] = {
            'source_row': number,
            'title': sources[number],
            'folder': folder.name,
            'status': metadata['status'],
            'raw_files': len(raw_files),
            'derived_files': len(derived_files),
            'bytes': sum(item['bytes'] for item in files),
            'geography': stringify(metadata.get('geography', metadata.get('coverage'))),
            'period': stringify(metadata.get('period')),
            'limitations': stringify(metadata.get('limitations')),
        }
    assert not issues, issues
    assert set(records) == set(sources), ('Unaccounted source rows', sorted(set(sources)-set(records)))
    rows = [records[number] for number in sorted(records)]
    with (ROOT / 'catalog.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sources': len(rows),
        'status_counts': dict(collections.Counter(row['status'] for row in rows)),
        'files': len(manifest),
        'bytes': sum(item['bytes'] for item in manifest),
        'manifest': manifest,
    }
    (ROOT / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    size = report['bytes'] / 1024 ** 2
    counts = report['status_counts']
    text = f'''# Наборы данных из исходной таблицы

Учтены все 38 строк [исходного списка](../docs/istochniki_dannyh.md). Карта России исключена из загрузки по указанию пользователя. Для каждого источника есть отдельная папка с README и metadata.json; наличие папки не означает, что данные удалось скачать.

Скачаны описанные выгрузки по {counts.get('downloaded', 0)} источникам, частичные данные или материалы — по {counts.get('partial', 0)}. По {counts.get('blocked', 0)} источникам файлы получить не удалось; причины указаны в их папках.

Файлов в raw/ и derived/: {report['files']}; общий размер {size:.1f} МиБ. Точные статусы — в таблице ниже. Исходные документы PDF обозначены в паспортах как документы: это не готовые матрицы транспортных связей.

## Как смотреть данные

- `raw/` — полученные файлы без изменения содержимого; HTML, если есть, является снимком источника, не датасетом.
- `derived/` — извлечённые или отфильтрованные таблицы; ограничения извлечения описаны рядом.
- `metadata.json` — первоисточник, прямые ссылки, период, география, время получения, SHA-256 и ограничения.
- `profile.json` и файлы coverage — проверенная структура, регионы, периоды и пропуски там, где формат позволил их определить.
- [COVERAGE.md](COVERAGE.md) — ориентиры для просмотра географии и полноты; масштаб исследования ещё не выбран.
- [catalog.csv](catalog.csv) — машиночитаемый каталог всех 38 источников; [manifest.json](manifest.json) — перечень локальных файлов, размеров и контрольных сумм.

«Скачан» относится к конкретной описанной выгрузке. «Частично» означает ограниченный период, часть показателей или документ вместо полного требуемого массива. «Доступ не получен» сопровождается причинами и проверенными адресами. API без выбранных координат и периода не подменяется произвольной выборкой.

Данные в raw/ и derived/ хранятся локально и исключены из Git; описания, профили и каталог можно версионировать. Лицензии и условия повторного использования фиксируются отдельно по источникам. Наборы с пересекающимися показателями и агрегатами нельзя суммировать как независимые наблюдения.

## Каталог

| № | Источник | Статус | Файлы исходные / производные | Размер, МиБ |
|---|---|---|---|---|
'''
    for row in rows:
        text += f"| {row['source_row']} | [{row['title']}]({row['folder']}/README.md) | {STATUS[row['status']]} | {row['raw_files']} / {row['derived_files']} | {row['bytes']/1024**2:.2f} |\n"
    if (ROOT / 'additional/README.md').exists():
        text += '\n## Дополнительные источники\n\n[Отдельный каталог](additional/README.md) содержит материалы последующей разведки за пределами исходных 38 строк. Их файлы и контрольные суммы учитываются отдельно.\n'
    text += '\n## Проверка и повторное получение\n\n'
    text += '`python3 datasets/build_catalog.py` повторно проверяет SHA-256 исходных файлов с метаданными, сигнатуры PDF/ZIP/XLSX и пересобирает каталог. Для исходных ссылок сначала смотрите metadata.json конкретного набора. `download.py` принимает JSON-план url/destination и сохраняет результаты HTTP, размеры и SHA-256; root-download-plan.json содержит только группу геоданных и календарей. Скрипты загрузки/обработки остальных групп, если сохранены, отмечены в их README. Перед повторным получением проверьте изменяемые URL и условия провайдера.\n'
    (ROOT / 'README.md').write_text(text)
    print(json.dumps({key: value for key, value in report.items() if key != 'manifest'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
