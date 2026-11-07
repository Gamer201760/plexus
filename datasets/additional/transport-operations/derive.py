import csv
import hashlib
import io
import json
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
RAW = ROOT / 'data/additional/transport-operations'
URL = 'https://aokap.ru/uslugi/regulyarnye-perevozki/raspisanie-zima/'


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def kap_schedule():
    path = RAW / (hashlib.sha256(URL.encode()).hexdigest()[:20] + '.html')
    tables = pd.read_html(io.StringIO(path.read_text()), flavor='lxml')
    segments = []
    for table_index, table in enumerate(tables):
        for row_index, values in enumerate(table.itertuples(index=False, name=None)):
            cells = [str(value) for value in values]
            if len(cells) != 7 or not re.fullmatch(r'ДЕ\s*\d+', cells[1]):
                continue
            if table_index == 0:
                origin, destination = 'Петропавловск-Камчатский (Елизово)', cells[0]
            elif table_index == 2:
                origin, destination = cells[0], 'Петропавловск-Камчатский (Елизово)'
            else:
                origin, destination = re.split(r'\s*→\s*', cells[0], maxsplit=1)
            segments.append(dict(origin=origin, destination=destination, flight=cells[1], departure_local=cells[2], arrival_local=cells[3], aircraft=cells[4], weekdays_raw=cells[5], validity_raw=cells[6], season_start='2026-10-26', season_end='2027-03-26', source_table_index=table_index, source_row_index=row_index, source_url=URL, status='published_schedule_not_operations'))
    write_csv(RAW / 'kap_winter_2026_2027_segments.csv', segments)
    return len(segments)


def html_tables(records):
    target = RAW / 'tables'
    target.mkdir(exist_ok=True)
    index = []
    for record in records:
        if record['status'] != 'downloaded' or not record.get('path', '').endswith('.html'):
            continue
        path = ROOT / record['path']
        soup = BeautifulSoup(path.read_bytes(), 'lxml')
        tables = soup.find_all('table')
        for table_index, table in enumerate(tables):
            try:
                frames = pd.read_html(io.StringIO(str(table)), flavor='lxml')
                frame = frames[0]
                output = target / f'{path.stem}_{table_index:03d}.csv'
                frame.to_csv(output, index=False)
                index.append(dict(source_url=record['url'], source_sha256=record['sha256'], table_index=table_index, rows=len(frame), columns=len(frame.columns), path=str(output.relative_to(ROOT)), validation='structural_extraction_only'))
            except (ValueError, IndexError, AttributeError, AssertionError):
                continue
    write_csv(target / 'index.csv', index)
    return len(index), sum(row['rows'] for row in index)


def repair_contract():
    source = RAW / 'c7ee5251c115c99008b6.pages.json'
    pages = json.loads(source.read_text())
    for page in pages:
        page['text'] = ''.join(chr(ord(char) + 470) if 0x23A <= ord(char) <= 0x279 else char for char in page['text'])
    source.with_name(source.stem + '.repaired.json').write_text(json.dumps(pages, ensure_ascii=False, indent=2) + '\n')


def main():
    rows = {row['url']: row for row in map(json.loads, (META / 'manifest.jsonl').read_text().splitlines())}
    kap_rows = kap_schedule()
    table_count, table_rows = html_tables(rows.values())
    repair_contract()
    write_csv(RAW / 'hmrn_subsidy_2024_schedule.csv', json.loads((META / 'contract_schedule.json').read_text()))
    profile = dict(source_count=len(rows), status_counts={status: sum(row['status'] == status for row in rows.values()) for status in sorted({row['status'] for row in rows.values()})}, raw_bytes=sum(row.get('bytes', 0) for row in rows.values()), html_tables=table_count, html_table_rows=table_rows, kap_schedule_segments=kap_rows, full_national_timetable=False, yandex_api_status='blocked_missing_api_key')
    (META / 'profile.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(profile))


if __name__ == '__main__':
    main()
