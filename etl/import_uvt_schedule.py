import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

SOURCE_URL = 'https://www.uvtaero.ru/raspisanie'
DAYS = {'пн': 1, 'вт': 2, 'ср': 3, 'чт': 4, 'пт': 5, 'сб': 6, 'вс': 7}


class ScheduleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.origin = None
        self.heading = None
        self.in_table = False
        self.row = None
        self.cell = None
        self.rows = []
        self.origins = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'span' and 'js-slide__toggle' in attrs.get('class', '').split():
            self.heading = []
        if tag == 'table' and 'ras__table' in attrs.get('class', '').split():
            if not self.origin:
                raise ValueError('Schedule table without origin heading')
            self.in_table = True
        if self.in_table and tag == 'tr':
            self.row = []
            self.images = []
        if self.in_table and tag == 'td':
            if attrs.get('rowspan', '1') != '1' or attrs.get('colspan', '1') != '1':
                raise ValueError('Unsupported merged schedule cell')
            self.cell = []
        if self.cell is not None and tag == 'img':
            self.images.append(attrs.get('src'))
        if self.cell is not None and tag == 'br':
            self.cell.append(' ')

    def handle_data(self, data):
        if self.heading is not None:
            self.heading.append(data)
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == 'span' and self.heading is not None:
            heading = ' '.join(''.join(self.heading).split())
            if not heading.startswith('Из города '):
                raise ValueError(f'Unexpected origin heading: {heading}')
            self.origin = heading.removeprefix('Из города ')
            self.origins.append(self.origin)
            self.heading = None
        if self.in_table and tag == 'td':
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if self.in_table and tag == 'tr' and self.row:
            if len(self.row) != 12:
                raise ValueError(f'Expected 12 columns, got {len(self.row)}')
            self.rows.append({'origin': self.origin, 'cells': self.row, 'images': self.images})
            self.row = None
        if tag == 'table':
            self.in_table = False


def parse_period(value):
    parts = re.fullmatch(r'(\d{2}\.\d{2}\.\d{2})-(\d{2}\.\d{2}\.\d{2})', value)
    if not parts:
        raise ValueError(f'Unexpected period: {value}')
    start, end = [datetime.strptime(x, '%d.%m.%y').date() for x in parts.groups()]
    if start > end:
        raise ValueError(f'Reversed period: {value}')
    return start, end


def flight_number(value):
    match = re.fullmatch(r'ЮВ\s*\(RT\)\s*-\s*(\d+)', value)
    if not match:
        raise ValueError(f'Unexpected flight: {value}')
    return 'RT' + match.group(1)


def normalize_time(value):
    if not re.fullmatch(r'(?:[01]\d|2[0-3])-[0-5]\d', value):
        raise ValueError(f'Unexpected local time: {value}')
    return value.replace('-', ':')


def extract(parser, reference_date, retrieved_at):
    routes, skipped = {}, []
    for row_index, row in enumerate(parser.rows, 1):
        cells = row['cells']
        start, end = parse_period(cells[1])
        for side, offset in [('outbound', 3), ('return', 8)]:
            values = cells[offset:offset + 4]
            if all(value == '-' for value in values):
                skipped.append({'source_row': row_index, 'side': side, 'reason': 'empty_leg'})
                continue
            flight, departure, arrival, day_text = values
            weekdays = sorted({DAYS[d.strip().lower()] for d in day_text.split(',')})
            origin, destination = row['origin'], cells[0]
            if side == 'return':
                origin, destination = destination, origin
            core = dict(origin=origin, destination=destination, airline='ЮВТ Аэро',
                        flight=flight_number(flight), days=weekdays,
                        period_start=start.isoformat(), period_end=end.isoformat(),
                        departure_local=normalize_time(departure),
                        arrival_local=normalize_time(arrival), aircraft=cells[7])
            identity = json.dumps(core, sort_keys=True, ensure_ascii=False)
            key = hashlib.sha256(identity.encode()).hexdigest()[:20]
            if key not in routes:
                in_period = start <= reference_date <= end
                routes[key] = dict(id=key, **core, source_url=SOURCE_URL,
                                   retrieved_at=retrieved_at,
                                   period_active_on_reference_date=in_period,
                                   active_on_reference_date=in_period and reference_date.isoweekday() in weekdays,
                                   source_occurrences=[], ambiguity_ids=[], eligible_for_import=True)
            routes[key]['source_occurrences'].append(dict(
                source_row=row_index, side=side, flight_raw=flight,
                departure_local_raw=departure, arrival_local_raw=arrival,
                days_raw=day_text, period_raw=cells[1]))
    return list(routes.values()), skipped


def ambiguities(routes):
    groups = defaultdict(list)
    conflicts = []
    for route in routes:
        groups[(route['origin'], route['destination'], route['flight'])].append(route)
    for group in groups.values():
        for index, left in enumerate(group):
            for right in group[index + 1:]:
                weekdays = set(left['days']) & set(right['days'])
                start = date.fromisoformat(max(left['period_start'], right['period_start']))
                end = date.fromisoformat(min(left['period_end'], right['period_end']))
                overlaps = any(start + timedelta(days=n) <= end and
                               (start + timedelta(days=n)).isoweekday() in weekdays for n in range(7))
                if not overlaps:
                    continue
                same_times = all(left[k] == right[k] for k in ('departure_local', 'arrival_local'))
                issue_id = f'ambiguity-{len(conflicts) + 1}'
                conflicts.append(dict(id=issue_id, route_ids=[left['id'], right['id']],
                                      kind='overlapping_schedule_rows' if same_times else 'conflicting_local_times',
                                      origin=left['origin'], destination=left['destination'],
                                      flight=left['flight'], overlap_start=start.isoformat(),
                                      overlap_end=end.isoformat(), days=sorted(weekdays)))
                for route in (left, right):
                    route['ambiguity_ids'].append(issue_id)
                    route['eligible_for_import'] = False
    return conflicts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', type=Path)
    parser.add_argument('--retrieved-at')
    parser.add_argument('--as-of', type=date.fromisoformat, default=date(2026, 11, 10))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    snapshot = args.output.with_name('uvt-schedule-source.html')
    if args.html:
        if not args.retrieved_at:
            parser.error('--retrieved-at is required when replaying --html')
        content = args.html.read_bytes()
    else:
        content = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                                  '--max-time', '60', SOURCE_URL], check=True, capture_output=True).stdout
    retrieved_at = args.retrieved_at or datetime.now(timezone.utc).isoformat()
    if datetime.fromisoformat(retrieved_at.replace('Z', '+00:00')).tzinfo is None:
        parser.error('--retrieved-at must include a timezone')
    snapshot.write_bytes(content)
    schedule = ScheduleParser()
    schedule.feed(content.decode('utf-8'))
    if not schedule.rows:
        raise ValueError('No schedule rows found')
    routes, skipped = extract(schedule, args.as_of, retrieved_at)
    conflicts = ambiguities(routes)
    result = dict(schema_version=1, source_url=SOURCE_URL, retrieved_at=retrieved_at,
                  reference_date=args.as_of.isoformat(), source_sha256=hashlib.sha256(content).hexdigest(),
                  source_snapshot=snapshot.name, source_table_count=len(schedule.origins),
                  source_row_count=len(schedule.rows), source_origins=schedule.origins,
                  raw_rows=schedule.rows, routes=routes, skipped_legs=skipped, ambiguities=conflicts,
                  notes=['All times are local to each airport; no timezone or duration inference.',
                         'Return legs inherit the period shown in the shared source row.',
                         'active_on_reference_date requires both period and weekday match.',
                         'Identical mirrored rows are deduplicated with all source occurrences retained.',
                         'Conflicting or overlapping schedule rows are excluded from eligible_for_import.',
                         'Airport identity, region and coordinates are intentionally not inferred.'])
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(source_rows=len(schedule.rows), routes=len(routes),
                          active=sum(r['active_on_reference_date'] for r in routes),
                          eligible=sum(r['eligible_for_import'] for r in routes),
                          ambiguities=len(conflicts), skipped_legs=len(skipped))))


if __name__ == '__main__':
    main()
