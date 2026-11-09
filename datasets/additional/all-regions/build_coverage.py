import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
CATALOG = META.parent

def read(path):
    return json.loads(path.read_text())

def main():
    base = read(META/'base-profile.json')
    medical = {r['region_id_if_known']:r for r in read(CATALOG/'all-regions-medical/region-crosswalk.json') if r['region_id_if_known']}
    osm = {r['region_id']:r for r in read(CATALOG/'all-regions-osm/atlas-coverage.json')['regions']}
    roads = {r['region_id']:r for r in read(CATALOG/'all-regions-roads/atlas82-coverage.json')}
    bus_profile = read(META/'bus-profile.json')
    buses = {r['atlas_region_id']:r for r in bus_profile['regions'] if r['atlas_region_id']}
    rows = []
    for region in base['regions']:
        identifier = region['region_id']
        exp = region['exports']
        bus = buses.get(identifier)
        remote = ROOT/f'data_manual/regions/{identifier}_remote.csv'
        prior = ROOT/f'data_manual/regions/{identifier}.csv'
        prior_counts = {}
        for name,path in [('remote_tax_rows',remote),('prior_manual_transport_rows',prior)]:
            if path.exists():
                with path.open(newline='') as source:
                    prior_counts[name] = sum(1 for _ in csv.DictReader(source))
            else:
                prior_counts[name] = None
        row = dict(region_id=identifier,region_name=region['name'],settlements=exp['settlements']['rows'],company_records=exp['companies_2025']['rows'],fns_matched_records=exp['fns_matched_2025']['rows'],light_observations=exp['settlement_lights']['rows'],medical_registry_rows=medical[identifier]['registry_rows'],medical_status='downloaded_national_legal_address_registry_2026_03_03',interregional_bus_routes=bus['route_count'] if bus else 0,interregional_bus_status='downloaded_records_present' if bus else 'no_records_in_this_national_snapshot',stop_region_code=bus['stop_region_code'] if bus else '',osm_url=osm[identifier]['source_urls'][0],osm_status='head_verified_source_not_downloaded',road_statistics_status=roads[identifier]['road_categories_status'],intraregional_bus_status=roads[identifier]['intraregional_bus_status'],regional_exports_directory=f'data/additional/all-regions/derived/regions/{identifier}',**prior_counts)
        rows.append(row)
    assert len(rows)==len({r['region_id'] for r in rows})==82
    assert all(r['medical_registry_rows']>0 and r['osm_url'] for r in rows)
    (META/'coverage.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    with (META/'coverage.csv').open('w',newline='') as output:
        writer=csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    text = '# Покрытие регионов\n\nПроверено 09.11.2026. ОМС — строки мартовского национального реестра; автобусы — маршруты с остановками в регионе в реестре 05.11.2026. Ноль означает отсутствие записей в этом снимке. OSM — проверенная ссылка, новый PBF не скачан. Историческая статистика дорог получена для всех строк; современные замеры трафика не подтверждены.\n\n'
    text += '| Регион | Пункты | Компании | ФНС | ОМС | Межрегиональные маршруты | OSM |\n|---|---:|---:|---:|---:|---:|---|\n'
    for r in rows:
        text += f"| {r['region_name']} | {r['settlements']} | {r['company_records']} | {r['fns_matched_records']} | {r['medical_registry_rows']} | {r['interregional_bus_routes']} | [PBF]({r['osm_url']}) |\n"
    (META/'coverage.md').write_text(text)
    summary = dict(atlas_regions=82,regional_base_exports=sum(len(r['exports']) for r in base['regions']),medical_atlas_regions=len(medical),osm_atlas_source_links=len(osm),historical_roads_atlas_regions=len(roads),bus_atlas_regions=len(buses),bus_source_region_categories=bus_profile['regions_in_source'],bus_routes=bus_profile['routes'],bus_schedules=bus_profile['schedule_rows'],bus_stops=bus_profile['stop_records'],national_base_totals=base['totals'],outside_atlas_companies=base['outside_atlas']['rows'],missing_bus_atlas_regions=[r['region_name'] for r in rows if r['interregional_bus_routes']==0],not_complete=['current intraregional timetables','national care-location addresses and geocoding','current traffic measurements','current physical road asset inventory','OSM PBF download/extraction for every region'])
    (META/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
