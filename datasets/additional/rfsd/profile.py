from pathlib import Path
from collections import Counter
import hashlib,json,re,sys
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'data/additional/rfsd'
raw=BASE/'raw'
inventory=json.loads((raw/'source_inventory.json').read_text())
records=[]
for item in inventory:
    if not item['path'].endswith('.parquet'):continue
    if len(sys.argv)>1 and f'year={int(sys.argv[1])}/' not in item['path']:continue
    path=raw/item['path']
    if not path.exists():continue
    digest=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
    assert path.stat().st_size==item['size'] and digest==item['lfs']['oid'],f'Incomplete or corrupt: {path}'
    f=pq.ParquetFile(path)
    year=int(re.search(r'year=(\d+)',item['path'])[1])
    schema=[{'name':s.name,'type':str(s.type)} for s in f.schema_arrow]
    field_null_counts={s.name:0 for s in f.schema_arrow}
    for group in range(f.metadata.num_row_groups):
        rg=f.metadata.row_group(group)
        for ci in range(rg.num_columns):
            col=rg.column(ci);name=col.path_in_schema;stats=col.statistics
            if name not in field_null_counts:continue
            if stats is None or stats.null_count is None:field_null_counts[name]=None
            elif field_null_counts[name] is not None:field_null_counts[name]+=stats.null_count
    (BASE/f'derived/schema_{year}.json').write_text(json.dumps(schema,indent=2))
    categories=[s.name for s in f.schema_arrow if any(x in s.name.lower() for x in ['filed','imput','eligib','outlier','articul','geocod','adjust','simplif'])]
    numeric=[s.name for s in f.schema_arrow if s.name in ['line_2110','line_1600','lat','lon','latitude','longitude']]
    selected=list(dict.fromkeys(categories+numeric+(['inn'] if 'inn' in f.schema_arrow.names else [])))
    counts={c:Counter() for c in categories}; nulls=Counter();minima={};maxima={};inns=set();rows=0
    for batch in f.iter_batches(batch_size=65536,columns=selected):
        rows+=batch.num_rows
        for c in selected:
            arr=batch.column(batch.schema.get_field_index(c));nulls[c]+=arr.null_count
            if c in categories:
                for value,n in zip(pc.value_counts(arr).field('values').to_pylist(),pc.value_counts(arr).field('counts').to_pylist()):counts[c][str(value)]+=n
            elif c=='inn':inns.update(x for x in arr.to_pylist() if x is not None)
            else:
                mm=pc.min_max(arr).as_py()
                if mm['min'] is not None:minima[c]=min(minima.get(c,mm['min']),mm['min'])
                if mm['max'] is not None:maxima[c]=max(maxima.get(c,mm['max']),mm['max'])
    assert rows==f.metadata.num_rows
    record={'year':year,'source_path':item['path'],'bytes':item['size'],'sha256':digest,'publisher_hash_matches':True,'rows':rows,'unique_nonnull_inn':len(inns),'columns':len(schema),'row_groups':f.metadata.num_row_groups,'category_counts':counts,'selected_null_counts':dict(nulls),'all_field_null_counts_from_parquet_statistics':field_null_counts,'all_field_nonmissing_rows':{c:None if n is None else rows-n for c,n in field_null_counts.items()},'selected_min':minima,'selected_max':maxima}
    records.append(record)
    (BASE/f'derived/profile_{year}.json').write_text(json.dumps(record,indent=2,default=str))
    print(year,rows,len(schema),flush=True)
records=[json.loads(p.read_text()) for p in sorted((BASE/'derived').glob('profile_[0-9][0-9][0-9][0-9].json'))]
profile={'complete_published_coverage':len(records)==15,'period':[min(r['year'] for r in records),max(r['year'] for r in records)],'rows':sum(r['rows'] for r in records),'raw_parquet_bytes':sum(r['bytes'] for r in records),'annual_profiles':records,'validation':'All file lengths and SHA256 match pinned publisher inventory; Parquet footer parsed and all selected columns decoded in batches. Not every financial column is decoded.','financial_units':'Thousands of RUB according to author Rosstat unit harmonization code; no rescaling applied here.','geography':'Legal entity incorporation address; preserve geocoding_quality, not establishment/plant coordinates.'}
(BASE/'derived/profile.json').write_text(json.dumps(profile,indent=2,default=str))
print('TOTAL',profile['rows'],flush=True)
