from pathlib import Path
from collections import defaultdict
import csv,json,math
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'data/additional/rfsd'
profile=json.loads((BASE/'derived/profile_2025.json').read_text())
assert profile['publisher_hash_matches']
f=pq.ParquetFile(BASE/'raw/RFSD/year=2025/part-0.parquet')
dims=['region','okved_section','filed','imputed','outlier','geocoding_quality']
cols=dims+['line_2110','lon','lat']
groups=defaultdict(lambda:{'firm_rows':0,'revenue_nonmissing_rows':0,'revenue_sum_thousand_rub':0.0,'coordinate_rows':0})
for batch in f.iter_batches(batch_size=65536,columns=cols):
    for row in batch.to_pylist():
        key=tuple(row[c] if row[c] is not None else '__missing__' for c in dims)
        g=groups[key];g['firm_rows']+=1
        v=row['line_2110']
        if v is not None and math.isfinite(v):g['revenue_nonmissing_rows']+=1;g['revenue_sum_thousand_rub']+=v
        if row['lat'] is not None and row['lon'] is not None:g['coordinate_rows']+=1
out=BASE/'derived/region_sector_flags_2025.csv'
fields=dims+['firm_rows','revenue_nonmissing_rows','revenue_sum_thousand_rub','coordinate_rows']
with out.open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    for key,g in sorted(groups.items(),key=lambda x:str(x[0])):writer.writerow(dict(zip(dims,key))|g)
assert sum(g['firm_rows'] for g in groups.values())==profile['rows']
assert sum(g['revenue_nonmissing_rows'] for g in groups.values())==profile['all_field_nonmissing_rows']['line_2110']
(BASE/'derived/aggregation_2025.json').write_text(json.dumps({'source_rows':profile['rows'],'aggregate_rows':len(groups),'group_columns':dims,'financial_units':'Thousands of nominal RUB; line_2110 revenue, double precision sum','filters':'No rows excluded; outlier, filed, imputed and geocoding_quality are explicit grouping dimensions. Missing source values labelled __missing__. Missing financial values are excluded from sum and counted separately.','geography':'Region and coordinates of legal incorporation, not plant location.','validation':'Aggregated firm and nonmissing revenue counts match verified annual profile.'},indent=2))
print(profile['rows'],len(groups),out)
