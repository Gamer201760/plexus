import argparse
import json
import os
import re
from client import ClickHouse
from pathlib import Path
from statistics import median
from time import perf_counter

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_queries import QUERIES

r=ClickHouseReader(os.environ['CLICKHOUSE_URL'],os.environ['CLICKHOUSE_USER'],os.environ['CLICKHOUSE_PASSWORD'])
way=r.rows('SELECT way_id FROM plexus_graph.ways WHERE way_id IS NOT NULL LIMIT 1',{})[0]['way_id']
cases={
 'regional_matrix':(QUERIES['delta_times'],{'region':'Владимирская область'}),
 'road_osm_id':(QUERIES['way_indices'],{'ids':[int(way)]}),
 'settlements_region':('SELECT id,name,population,x,y FROM plexus_atlas.atlas_settlements WHERE region_id={region:String}',{'region':'17000000'}),
 'settlement_search':('SELECT id,name,region_id,population FROM plexus_atlas.atlas_settlements WHERE name_key LIKE {pattern:String} ORDER BY ordinal',{'pattern':'%владимир%'}),
 'graph_search':(QUERIES['locations'],{'pattern':'%владимир%','region':''}),
 'road_reference':(QUERIES['road_reference'],{'name':'м7'}),
 'road_geometry':('SELECT count(),sum(edge_count) FROM plexus_graph.road_lines WHERE rank<=3 AND min_lon<=43 AND max_lon>=38 AND min_lat<=57 AND max_lat>=54',{}),
}
report=[]
for name,(sql,params) in cases.items():
 with r.response('EXPLAIN indexes=1 '+sql,params,'JSON') as response:plan=json.load(response)['data']
 runs=[]
 for i in range(3):
  started=perf_counter()
  with r.response(sql,params,'JSON') as response:result=json.load(response)
  runs.append({'wall_seconds':perf_counter()-started,**result['statistics'],'returned':result['rows']})
 row={'name':name,'sql':sql,'parameters':params,'plan':plan,'runs':runs,'median_wall_seconds':median(x['wall_seconds'] for x in runs)}
 if name in ['road_osm_id','settlement_search','graph_search']:
  settings=' SETTINGS optimize_use_projections=0,use_skip_indexes=0'
  def literal(value):
   if isinstance(value,list):return '['+','.join(str(i) for i in value)+']'
   return "'"+str(value).replace("'","\\'")+"'"
  rendered=re.sub(r'\{(\w+):[^}]+\}',lambda m:literal(params[m[1]]),sql)
  unindexed=json.loads(ClickHouse().request(rendered+settings+' FORMAT JSON'))
  row['without_secondary_indexes']=unindexed['statistics']
 report.append(row)
 print(name,'rows read',runs[-1]['rows_read'],'returned',runs[-1]['returned'],'median',round(row['median_wall_seconds'],4),flush=True)
parser = argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
