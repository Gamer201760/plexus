import csv
import hashlib
import json
import shutil
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
OUT = ROOT / 'data/additional/stavropol/derived'
OUT.mkdir(parents=True, exist_ok=True)
con = duckdb.connect(str(ROOT / 'data/additional.duckdb'), read_only=True)
queries = {
    'settlements': "select * from dim_settlement where region_id='07000000'",
    'companies_2025': "select * from fact_company where region_id='07000000'",
    'fns_matched_2025': "select f.* from stg_fns f where f.inn in (select inn from fact_company where region_id='07000000')",
    'settlement_economy': "select * from mart_np_economy where region_id='07000000'",
    'region_economy': "select * from mart_region_economy where region_id='07000000'",
    'sector_economy': "select * from mart_region_sector where region_id='07000000'",
    'settlement_lights': "select l.* from stg_lights l join dim_settlement s using(point_id) where s.region_id='07000000'",
    'company_settlement': "select cs.* from company_settlement cs join dim_settlement s using(point_id) where s.region_id='07000000'"
}
profile = {}
for name, query in queries.items():
    suffix = 'parquet' if name in {'companies_2025','fns_matched_2025','company_settlement'} else 'csv'
    path = OUT / f'{name}.{suffix}'
    options = "FORMAT PARQUET, COMPRESSION ZSTD" if suffix == 'parquet' else 'FORMAT CSV, HEADER'
    con.execute(f"COPY ({query} order by 1) TO '{path}' ({options})")
    profile[name] = dict(rows=con.execute(f'select count(*) from ({query})').fetchone()[0], path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
for origin, name in [('data_manual/regions_input/07000000.csv','settlements_input.csv'),('data_manual/regions/07000000_remote.csv','remote_tax_status.csv'),('data_manual/regions/07000000.csv','nonroad_links_prior_search.csv')]:
    path = OUT / name
    shutil.copyfile(ROOT / origin, path)
    profile[name] = dict(source=origin, rows=sum(1 for _ in csv.DictReader(path.open())), path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
profile['checks'] = dict(settlement_duplicates=con.execute("select count(*)-count(distinct point_id) from dim_settlement where region_id='07000000'").fetchone()[0], geography='RFSD source region mapped to atlas code07000000; not INN prefix', source_database='data/additional.duckdb', financial_units='company revenue_rub and FNS income_rub/expense_rub in RUB; distinct concepts', lights_units='raw source integer; not calibrated radiance')
(META / 'local-profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(profile,ensure_ascii=False))
