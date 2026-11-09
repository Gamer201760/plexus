import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
args = parser.parse_args()
root = args.repo / 'datasets'
out = Path(__file__).parent

def normalized(value):
    return re.sub(r'\s+', ' ', value).strip()

def numeric(value):
    match = re.match(r'\s*([0-9]+(?:[ \u00a0\u202f][0-9]{3})*(?:[,.][0-9]+)?)', value)
    return float(re.sub(r'\s', '', match[1]).replace(',', '.')) if match else None

def capacity(value):
    number = numeric(value)
    if number is None or not re.search(r'тонн', value, re.I):
        return None
    multiplier = 1e6 if re.search(r'млн', value) else 1e3 if re.search(r'тыс', value) else 1
    return number * multiplier

def bbox(path):
    process = subprocess.run(['pdftotext', '-bbox', str(path), '-'], capture_output=True, text=True, check=True)
    parsed = ET.fromstring(process.stdout)
    return [{'text': node.text or '', 'x': (float(node.attrib['xMin']) + float(node.attrib['xMax'])) / 2, 'xmin': float(node.attrib['xMin']), 'y': float(node.attrib['yMin'])} for node in parsed.iter() if node.tag.endswith('word')]

ports = pd.read_csv(root / 'rosmorport-port-characteristics/derived/ports.csv', keep_default_na=False)
characteristics = pd.read_csv(root / 'rosmorport-port-characteristics/derived/characteristics.csv', keep_default_na=False)
characteristics['metric_normalized'] = characteristics.metric_raw.map(lambda value: normalized(value.lower()).strip('• :-–'))
duplicate_metrics = characteristics.groupby(['port_name', 'metric_normalized']).filter(lambda group: len(group) > 1)
duplicate_metrics.to_csv(out / 'port_duplicate_metric_rows.csv', index=False)
records = []
flags = []
for item in ports.to_dict('records'):
    text = normalized(item['technical_characteristics_raw'])
    rows = characteristics[characteristics.port_name == item['port_name']]
    cargo = None
    berths = None
    front = None
    front_source = ''
    source_value = ''
    method = 'adjacent_metric_value'
    for row in rows.to_dict('records'):
        metric = normalized(row['metric_raw']).lower()
        value = normalized(row['value_raw'])
        if len(metric) > 250:
            labels_ok = re.match(r'^[• ]*площадь территории.*площадь акватории.*количество причалов.*длина причального фронта.*пропускная способность грузовых терминалов', metric)
            parts = value.split(';')
            if labels_ok and len(parts) >= 5:
                cargo = capacity(parts[4])
                berths = numeric(parts[2])
                front = numeric(parts[3])
                front_source = parts[3]
                source_value = parts[4]
                method = 'parallel_cells_first_five_fields'
            continue
        if 'количество причалов' in metric:
            berths = numeric(value)
        if 'длина причального фронта' in metric:
            front = numeric(value)
            front_source = value
        if 'пропускная способность грузовых терминалов' in metric and value:
            cargo = capacity(value)
            source_value = value
    if cargo is None:
        match = re.search(r'пропускная способность грузовых терминалов\s*[:,]?\s*[-–]?\s*(?:всего\s*[:]?\s*)?([0-9][^;•]+)', text, re.I)
        if match:
            source_value = match[1]
            cargo = capacity(source_value)
    if berths is None:
        match = re.search(r'количество причалов\s*:?\s*([0-9][^;•]+)', text, re.I)
        berths = numeric(match[1]) if match else None
    if front is None:
        match = re.search(r'длина причального фронта(?: морского порта)?\s*:?\s*([0-9][^;•]+)', text, re.I)
        front = numeric(match[1]) if match else None
        front_source = match[1] if match else ''
    if front is not None and re.search(r'км', front_source):
        front *= 1000
    annual = bool(re.search(r'в год', source_value))
    issue = []
    if cargo is not None and not annual:
        issue.append('annual_period_not_explicit')
    if item['port_name'] == 'Морской порт Приморск':
        issue.append('source_says_89500_tonnes_not_thousand_tonnes_do_not_correct')
    if '31,77 кв. м' in text:
        issue.append('aquatory_unit_suspicious_source_literal')
    dimensions = {}
    for label, pattern in [('first_explicit_draft_m', r'(?:по\s+)?осадк[ае]\s*:?\s*([0-9][^;•]+)'), ('first_explicit_length_m', r'(?:по\s+)?длин[ае]\s*:?\s*([0-9][^;•]+)'), ('first_explicit_width_m', r'(?:по\s+)?ширин[ае]\s*:?\s*([0-9][^;•]+)')]:
        match = re.search(pattern, text, re.I)
        dimensions[label] = numeric(match[1]) if match else None
    records.append({'port_name': item['port_name'], 'cargo_capacity_tonnes_per_year_literal': cargo, 'annual_period_explicit': annual, 'capacity_unit_screen_pass': cargo is not None and annual and not issue, 'berths': berths, 'berth_front_m': front, 'berth_front_source': front_source, 'capacity_source_text': source_value, 'extraction_method': method, 'flags': ';'.join(issue), 'source_url': item['source_url'], **dimensions})
    for issue_name in issue:
        flags.append({'port_name': item['port_name'], 'issue': issue_name, 'source_value': source_value})
port_frame = pd.DataFrame(records)
port_frame.to_csv(out / 'port_capacity_panel.csv', index=False)
availability = [{'metric': column, 'non_null_ports': int(port_frame[column].notna().sum()), 'total_ports': len(port_frame)} for column in ['cargo_capacity_tonnes_per_year_literal','berths','berth_front_m','first_explicit_draft_m','first_explicit_length_m','first_explicit_width_m']]
pd.DataFrame(availability).to_csv(out / 'port_metric_availability.csv', index=False)
pd.DataFrame(flags).to_csv(out / 'port_source_warnings.csv', index=False)

national_path = root / 'asop-port-turnover-capacity/raw/turnover-capacity-2000-2024.pdf'
words = bbox(national_path)
years = {int(word['text']): word['x'] + 3.8 for word in words if re.fullmatch(r'20\d\d', word['text']) and word['y'] > 480}
national = []
for year, center in years.items():
    candidates = [word for word in words if re.fullmatch(r'\d+(?:,\d+)?', word['text']) and word['x'] > 65 and 110 < word['y'] < 445 and min(years, key=lambda y: abs(years[y] - word['x'])) == year]
    assert len(candidates) == 2, (year, candidates)
    values = sorted(float(word['text'].replace(',', '.')) for word in candidates)
    percentages = [word for word in words if re.fullmatch(r'\d+,\d+%?', word['text']) and 445 < word['y'] < 470 and min(years, key=lambda y: abs(years[y] - word['x'])) == year]
    assert len(percentages) == 1, (year, percentages)
    stated = float(percentages[0]['text'].rstrip('%').replace(',', '.'))
    computed = values[0] / values[1] * 100
    assert abs(stated - computed) < 0.1, (year, stated, computed)
    national.append({'year': year, 'turnover_million_tonnes': values[0], 'capacity_million_tonnes': values[1], 'utilization_stated_pct': stated, 'utilization_computed_pct': computed, 'source_file': str(national_path.relative_to(args.repo))})
national_frame = pd.DataFrame(national).sort_values('year')
national_frame.to_csv(out / 'national_turnover_capacity_2000_2024.csv', index=False)

configs = [
('12_2023_basseyny_i_napravleniya.pdf', 'basin', 'annual', [2022, 2023], 200, 0, 250),
('basseyny_i_napravleniya_1_kv-l_2024_g.pdf', 'basin', 'Q1', [2023, 2024], 80, 125, 325),
('basseyny_i_napravleniya_1_kv-l_2024_g.pdf', 'direction', 'Q1', [2023, 2024], 90, 450, 670),
('12_2022_basseyny_i_napravleniya_1.pdf', 'direction', 'annual', [2021, 2022], 80, 500, 720),
('basseyn_napravleniya_03_2023.pdf', 'direction', 'Q1', [2022, 2023], 80, 500, 704)
]
labels = {'basin': ['Арктический', 'Балтийский', 'Азово-Черноморский', 'Каспийский', 'Дальневосточный'], 'direction': ['экспорт', 'импорт', 'транзит', 'каботаж']}
chart_records = []
for filename, kind, period, chart_years, minx, miny, maxy in configs:
    path = root / 'asop-port-basins/raw' / filename
    candidates = sorted([word for word in bbox(path) if re.fullmatch(r'\d+,\d+', word['text']) and word['xmin'] > minx and miny < word['y'] < maxy], key=lambda word: word['x'])
    assert len(candidates) == 2 * len(labels[kind]), (filename, kind, candidates)
    for index, label in enumerate(labels[kind]):
        for vintage_index, year in enumerate(chart_years):
            chart_records.append({'geography_or_direction': label, 'kind': kind, 'year': year, 'period': period, 'turnover_million_tonnes': float(candidates[2 * index + vintage_index]['text'].replace(',', '.')), 'source_file': filename})
charts = pd.DataFrame(chart_records)
charts.to_csv(out / 'asop_chart_values.csv', index=False)
conflicts = charts.groupby(['kind', 'geography_or_direction', 'year', 'period']).filter(lambda group: group.turnover_million_tonnes.nunique() > 1)
conflicts.to_csv(out / 'asop_publication_conflicts.csv', index=False)
basin_totals = charts[(charts.kind == 'basin') & (charts.period == 'annual')].groupby('year').turnover_million_tonnes.sum()
consistency = national_frame.set_index('year').join(basin_totals.rename('basin_sum_million_tonnes'), how='inner')
consistency['national_minus_basins_million_tonnes'] = consistency.turnover_million_tonnes - consistency.basin_sum_million_tonnes
consistency.to_csv(out / 'asop_annual_total_consistency.csv')

audit = []
for slug in ['asop-port-basins', 'asop-port-arrival-modes']:
    for path in sorted((root / slug / 'raw').glob('*.pdf')):
        text = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True, check=True).stdout
        decimal_count = len(re.findall(r'\b\d+,\d+\b', text))
        port_hits = [name for name in ports.port_name.str.replace('Морской порт ', '', regex=False) if re.search(r'\b' + re.escape(name) + r'\b', text, re.I)]
        audit.append({'source': slug, 'file': path.name, 'text_chars': len(text.strip()), 'decimal_tokens': decimal_count, 'numeric_text_present': decimal_count > 10, 'port_name_hits': '|'.join(port_hits)})
audit_frame = pd.DataFrame(audit)
audit_frame.to_csv(out / 'asop_pdf_audit.csv', index=False)

airports = pd.read_csv(root / 'ourairports-russia/derived/airports_ru.csv', keep_default_na=False)
regions = pd.read_csv(root / 'ourairports-russia/derived/regions_ru.csv', keep_default_na=False)
active_scheduled = airports[(airports.scheduled_service == 'yes') & (airports.type != 'closed')]
airport_regions = active_scheduled.groupby('iso_region').size().rename('scheduled_airports').reset_index().merge(regions[['code', 'name']], how='left', left_on='iso_region', right_on='code')
airport_regions.to_csv(out / 'scheduled_airports_by_region.csv', index=False)

summary = {'ports': {'rows': len(ports), 'duplicate_dimension_ports': duplicate_metrics.port_name.nunique(), 'duplicate_dimension_rows': len(duplicate_metrics), 'capacity_parsed': int(port_frame.cargo_capacity_tonnes_per_year_literal.notna().sum()), 'capacity_unit_screen_pass': int(port_frame.capacity_unit_screen_pass.sum()), 'berths_parsed': int(port_frame.berths.notna().sum()), 'front_parsed': int(port_frame.berth_front_m.notna().sum()), 'collapsed_parallel_cell_ports': port_frame.loc[port_frame.extraction_method == 'parallel_cells_first_five_fields', 'port_name'].tolist(), 'without_capacity': port_frame.loc[port_frame.cargo_capacity_tonnes_per_year_literal.isna(), 'port_name'].tolist(), 'cargo_capacity_year_uniform': False, 'capacity_unit_screen_is_not_full_comparability': True, 'individual_port_observed_turnover_available': False}, 'asop': {'national_years': len(national_frame), 'national_utilization_max_abs_error_pp': float((national_frame.utilization_stated_pct - national_frame.utilization_computed_pct).abs().max()), 'readable_numeric_pdf_by_source': audit_frame.groupby('source').numeric_text_present.sum().to_dict(), 'all_pdf_by_source': audit_frame.groupby('source').size().to_dict(), 'chart_values_extracted': len(charts), 'publication_conflict_rows': len(conflicts), 'national_vs_basin_consistency': consistency.reset_index()[['year', 'turnover_million_tonnes', 'basin_sum_million_tonnes', 'national_minus_basins_million_tonnes']].to_dict('records')}, 'airports': {'rows': len(airports), 'closed': int((airports.type == 'closed').sum()), 'scheduled_yes': int((airports.scheduled_service == 'yes').sum()), 'active_scheduled': len(active_scheduled), 'regions_with_active_scheduled': active_scheduled.iso_region.nunique(), 'scheduled_service_is_routes': False}, 'input_hashes': {str(path.relative_to(args.repo)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [root / 'rosmorport-port-characteristics/derived/ports.csv', root / 'rosmorport-port-characteristics/derived/characteristics.csv', national_path]}}
(out / 'results.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
