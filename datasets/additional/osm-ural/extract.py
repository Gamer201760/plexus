"""Extract network source features, retaining original node IDs, geometry and all tags.
This is a source layer, not a routable/validated transport graph.
"""
import json,hashlib
from pathlib import Path
from collections import Counter
import osmium
import pyarrow as pa
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'data/additional/osm-ural'
SOURCE=BASE/'raw/ural-fed-district-261106.osm.pbf'
OUT=BASE/'derived'
OUT.mkdir(parents=True,exist_ok=True)
SCHEMA=pa.schema([('osm_way_id',pa.int64()),('version',pa.int32()),('timestamp',pa.string()),('name',pa.string()),('highway',pa.string()),('railway',pa.string()),('route',pa.string()),('bridge',pa.string()),('surface',pa.string()),('oneway',pa.string()),('access',pa.string()),('maxweight',pa.string()),('seasonal',pa.string()),('tags_json',pa.string()),('node_ids',pa.list_(pa.int64())),('lat',pa.list_(pa.float64())),('lon',pa.list_(pa.float64()))])
class Extract(osmium.SimpleHandler):
 def __init__(self):
  super().__init__();self.batch=[];self.counts=Counter();self.writer=pq.ParquetWriter(OUT/'network_ways.parquet',SCHEMA,compression='zstd')
 def way(self,w):
  t=dict(w.tags)
  if not (t.get('highway') or t.get('railway') or t.get('route')=='ferry' or t.get('man_made')=='bridge' or t.get('bridge') not in (None,'no')):return
  self.counts['selected_ways']+=1
  if not all(n.location.valid() for n in w.nodes):self.counts['missing_geometry']+=1;return
  r={k:t.get(k) for k in ['name','highway','railway','route','bridge','surface','oneway','access','maxweight','seasonal']}
  r.update(osm_way_id=w.id,version=w.version,timestamp=str(w.timestamp),tags_json=json.dumps(t,ensure_ascii=False),node_ids=[n.ref for n in w.nodes],lat=[n.lat for n in w.nodes],lon=[n.lon for n in w.nodes])
  self.batch.append(r);self.counts['exported_ways']+=1
  for k,yes in [('highway_ways',bool(t.get('highway'))),('railway_ways',bool(t.get('railway'))),('bridge_ways',t.get('bridge') not in (None,'no')),('ferry_ways',t.get('route')=='ferry'),('seasonal_tagged_ways',bool(t.get('seasonal'))),('maxweight_tagged_ways',bool(t.get('maxweight')))]:
   if yes:self.counts[k]+=1
  if len(self.batch)>=10000:self.flush()
 def flush(self):
  if self.batch:self.writer.write_table(pa.Table.from_pylist(self.batch,schema=SCHEMA));self.batch=[]
h=Extract()
try:h.apply_file(str(SOURCE),locations=True,idx='flex_mem');h.flush()
finally:h.writer.close()
with osmium.io.Reader(str(SOURCE)) as reader:timestamp=reader.header().get('osmosis_replication_timestamp')
p=OUT/'network_ways.parquet'
profile={'source':str(SOURCE.relative_to(ROOT)),'replication_timestamp':timestamp,'geography':'Ural Federal District (not Yugra-only)','counts':dict(h.counts),'derived':{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()},'limitations':['Feature counts are OSM way segments, not unique roads or bridges.','No tags are treated as evidence of unrestricted year-round operation.','Rail, pedestrian and private ways retained as source data; vehicle routing filters not applied.','Coordinates are source vertices; network connectivity and restrictions require model validation.']}
(ROOT/'datasets/additional/osm-ural/profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(profile,ensure_ascii=False))
