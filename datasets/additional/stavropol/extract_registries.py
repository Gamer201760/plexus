import csv
import json
from pathlib import Path
from read_xlsx import sheets

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
BASE = ROOT / 'data/additional/stavropol'
OUT = BASE / 'derived'

def write_csv(name, rows, fields=None):
    with (OUT / name).open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def medical(year):
    filename = f'medical-{year}.xlsx'
    sheet, source = next(sheets(BASE / 'raw' / filename))
    headers = {key: value for _, row in source[:2] for key, value in row.items() if value}
    names = ['ordinal','region_oktmo','registry_year_id','registry_number','oms_code','full_name','short_name','inn','kpp','ogrn','frmo_oid','organization_type','okopf_code','okopf_name','okfs_code','okfs_name','founder','organization_address','organization_address_id','phone','email','care_address','care_address_id','department_code','department_registry_id','department_name','department_oid','care_type','care_setting','care_profile','included_date','excluded_date','exclusion_reason']
    columns = list(headers)
    assert len(columns) == len(names) == 33
    rows = []
    for number, data in source[3:]:
        if not data.get('C'):
            if any(data.values()):
                raise ValueError(f'Unclassified medical row {number}')
            continue
        row = dict(zip(names, [data.get(c, '') for c in columns]))
        row.update(registry_year=year, source_file=filename, source_sheet=sheet, source_row=number)
        row['region_code_matches_stavropol'] = row['region_oktmo'] == '07000000'
        rows.append(row)
    write_csv(f'medical_care_rows_{year}.csv', rows)
    (META / f'medical-schema-{year}.json').write_text(json.dumps(dict(zip(names, [headers[c] for c in columns])), ensure_ascii=False, indent=2)+'\n')
    organizations = {}
    for row in rows:
        key = row['registry_year_id']
        if key not in organizations:
            organizations[key] = {k: row[k] for k in names[:19] + names[30:] + ['registry_year','source_file','source_sheet','source_row']}
            organizations[key]['care_source_rows'] = 0
        organizations[key]['care_source_rows'] += 1
    write_csv(f'medical_organizations_{year}.csv', list(organizations.values()))
    return dict(source_rows=len(rows), organizations=len(organizations), department_codes=len({r['department_code'] for r in rows if r['department_code']}), distinct_care_address_strings=len({r['care_address'] for r in rows if r['care_address']}), excluded_organization_ids=len({r['registry_year_id'] for r in rows if r['excluded_date']}), other_region_source_rows=sum(not r['region_code_matches_stavropol'] for r in rows), coordinates_available=False)

def buses():
    filename = 'interregional-bus-20261020.xlsx'
    book = list(sheets(BASE / 'raw' / filename))
    schedules = []
    schedule_fields = ['route_registry_id','route_name','route_ordinal','stop_name','stop_region_code','stop_registry_id','winter_departure_days','winter_departure_time','winter_dwell_time','winter_arrival_days','winter_arrival_time','winter_period','summer_departure_days','summer_departure_time','summer_dwell_time','summer_arrival_days','summer_arrival_time','summer_period']
    for direction, (sheet, rows) in zip(['forward','backward'],book[3:]):
        for number, source in rows[2:]:
            if not any(source.values()):
                continue
            row = dict(zip(schedule_fields,[source.get(chr(65+i),'') for i in range(18)]))
            if not row['route_registry_id']:
                raise ValueError(f'Missing schedule route ID at {sheet}:{number}')
            row.update(direction=direction,source_file=filename,source_sheet=sheet,source_row=number)
            schedules.append(row)
    selected = {r['route_registry_id'] for r in schedules if r['stop_region_code'].strip() == '26'}
    schedules = [r for r in schedules if r['route_registry_id'] in selected]
    for row in schedules:
        row['stop_in_stavropol'] = row['stop_region_code'].strip() == '26'
    write_csv('interregional_bus_schedules.csv', schedules)
    profile = dict(routes=len(selected), schedule_rows=len(schedules), stavropol_stop_rows=sum(r['stop_in_stavropol'] for r in schedules), distinct_stavropol_stop_ids=len({r['stop_registry_id'] for r in schedules if r['stop_in_stavropol'] and r['stop_registry_id']}), selection='At least one stop with official stop_region_code=26 in either direction; full schedules retained')
    schemas = {}
    for name,(sheet, rows) in zip(['routes','vehicles','carriers'],book[:3]):
        header = rows[0][1]
        schemas[name] = header
        result = [dict(source_file=filename,source_sheet=sheet,source_row=number,**{k:data.get(k,'') for k in header}) for number,data in rows[1:] if data.get('A') in selected]
        write_csv(f'interregional_bus_{name}.csv', result)
        profile[name+'_rows'] = len(result)
        if name == 'routes':
            assert {r['A'] for r in result} == selected
    schemas['schedules'] = dict(zip(schedule_fields, [book[3][1][0][1].get(chr(65+i),'')+' / '+book[3][1][1][1].get(chr(65+i),'') for i in range(18)]))
    (META/'bus-schema.json').write_text(json.dumps(schemas,ensure_ascii=False,indent=2)+'\n')
    return profile

def main():
    profile = {'medical': {str(year):medical(year) for year in [2025,2026]}, 'interregional_bus': buses()}
    (META/'registry-profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(profile,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
