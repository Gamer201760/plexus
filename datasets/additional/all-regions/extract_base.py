import hashlib
import json
from pathlib import Path
import duckdb
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
OUT = ROOT / 'data/additional/all-regions/derived/regions'

def main():
    con = duckdb.connect(str(ROOT/'data/additional.duckdb'),read_only=True)
    regions = json.loads((META/'atlas-regions.json').read_text())
    result = []
    for region in regions:
        identifier = region['region_id']
        assert identifier.isdigit() and len(identifier)==8
        directory = OUT/identifier
        directory.mkdir(parents=True,exist_ok=True)
        queries = {
            'settlements':f"select * from dim_settlement where region_id='{identifier}'",
            'companies_2025':f"select * from fact_company where region_id='{identifier}'",
            'fns_matched_2025':f"select f.* from stg_fns f where f.inn in (select inn from fact_company where region_id='{identifier}')",
            'settlement_economy':f"select * from mart_np_economy where region_id='{identifier}'",
            'region_economy':f"select * from mart_region_economy where region_id='{identifier}'",
            'sector_economy':f"select * from mart_region_sector where region_id='{identifier}'",
            'settlement_lights':f"select l.* from stg_lights l join dim_settlement s using(point_id) where s.region_id='{identifier}'",
            'company_settlement':f"select c.* from company_settlement c join dim_settlement s using(point_id) where s.region_id='{identifier}'"
        }
        exports = {}
        for name,query in queries.items():
            path = directory/(name+'.parquet')
            con.execute(f"COPY ({query} order by 1) TO '{path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            exports[name] = dict(path=str(path.relative_to(ROOT)),rows=pq.ParquetFile(path).metadata.num_rows,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
        result.append(dict(**region,exports=exports))
    totals = {name:sum(r['exports'][name]['rows'] for r in result) for name in result[0]['exports']}
    assert totals['settlements'] == con.execute('select count(*) from dim_settlement').fetchone()[0]
    assert totals['companies_2025'] == con.execute('select count(*) from fact_company where region_id in (select id from dim_region)').fetchone()[0]
    assert totals['settlement_lights'] == con.execute('select count(*) from stg_lights').fetchone()[0]
    outside = OUT.parent/'companies_outside_atlas_2025.parquet'
    con.execute(f"COPY (select * from fact_company where region_id is null or region_id not in (select id from dim_region)) TO '{outside}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    outside_rows = pq.ParquetFile(outside).metadata.num_rows
    assert totals['companies_2025']+outside_rows == con.execute('select count(*) from fact_company').fetchone()[0]
    profile = dict(source_database='data/additional.duckdb',scope='82 atlas regions plus all companies outside atlas preserved separately by original source_region',regions=result,totals=totals,outside_atlas=dict(path=str(outside.relative_to(ROOT)),rows=outside_rows,sha256=hashlib.sha256(outside.read_bytes()).hexdigest()),region_count=len(result),checks='settlement, company and lights counts reconcile to source database including outside-atlas companies')
    (META/'base-profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(totals,ensure_ascii=False))

if __name__ == '__main__':
    main()
