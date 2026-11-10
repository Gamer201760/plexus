import json
import hashlib
import os
import sys
from dataclasses import asdict, fields, replace
from pathlib import Path
from typing import get_type_hints

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend/src'))

from client import ClickHouse
from app.adapter.road_graph.job_store import restore_jobs
from app.adapter.road_graph.baselines import BaselineCache
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.records import sql_type
from app.repository.clickhouse.state import AnalysisResult, AnalysisState, ClickHouseAnalysisStore, ClickHouseRoadJobStore
from app.repository.files.road_analysis import FileAnalysisStore
from app.usecase.road_graph import RoadJob


def main():
    client = ClickHouse()
    reader = ClickHouseReader(os.environ['CLICKHOUSE_URL'],os.environ['CLICKHOUSE_USER'],os.environ['CLICKHOUSE_PASSWORD'])
    client.request('CREATE DATABASE IF NOT EXISTS plexus_state')
    definitions=[]
    for name,kind,order in [('road_jobs',RoadJob,'id'),('analysis_jobs',AnalysisState,'id'),('analysis_details',AnalysisResult,'analysis_id,way_id')]:
        hints=get_type_hints(kind)
        columns=','.join('`'+f.name+'` '+sql_type(hints[f.name]) for f in fields(kind))
        sql=f'CREATE TABLE IF NOT EXISTS plexus_state.{name} ({columns},updated UInt64) ENGINE=ReplacingMergeTree(updated) ORDER BY ({order}) SETTINGS index_granularity=256'
        client.request(sql)
        definitions.append(sql+';')
    (ROOT/'infra/clickhouse/state.sql').write_text('\n\n'.join(definitions)+'\n')
    jobs=restore_jobs(ROOT/'data')
    store=ClickHouseRoadJobStore(reader)
    for job in jobs.values():store.save(job)
    restored=store.load()
    assert all(restored[j.id]==j for j in jobs.values())
    source=FileAnalysisStore(ROOT/'data')
    target=ClickHouseAnalysisStore(reader)
    original_states=source.load()
    states=[]
    cache=BaselineCache(ROOT/'data',ClickHouseGraphSnapshot(reader).revision)
    for job,boundary in original_states:
        prefix=cache.path(boundary.id,'analysis-v1').stem
        before=hashlib.sha256((prefix+json.dumps(asdict(boundary),sort_keys=True)).encode()).hexdigest()
        canonical=replace(boundary,bounds=tuple(float(v) for v in boundary.bounds),polygons=[[[tuple(float(v) for v in point) for point in ring] for ring in polygon] for polygon in boundary.polygons])
        after=hashlib.sha256((prefix+json.dumps(asdict(canonical),sort_keys=True)).encode()).hexdigest()
        if job.fingerprint==before:job=replace(job,fingerprint=after)
        states.append((job,canonical))
    details=[]
    for job,boundary in states:
        target.save(job,boundary)
        for path in (source.root/job.id).glob('*.json'):
            if path.stem=='state':continue
            detail=source.detail(job.id,int(path.stem))
            target.save_detail(job.id,detail)
            assert target.detail(job.id,int(path.stem))==detail
            details.append(str(path.relative_to(ROOT)))
    assert json.loads(json.dumps([(asdict(j),asdict(b)) for j,b in target.load()]))==json.loads(json.dumps([(asdict(j),asdict(b)) for j,b in states]))
    manifest={'jobs':len(jobs),'analyses':len(states),'details':len(details),'files':[str((ROOT/'data/scenario-results'/f'{j.id}.json').relative_to(ROOT)) for j in jobs.values()]+[str((source.root/j.id/'state.json').relative_to(ROOT)) for j,b in states]+details}
    (ROOT/'work/clickhouse-migration/state.json').write_text(json.dumps(manifest,indent=2))
    print({k:v for k,v in manifest.items() if k!='files'},flush=True)

if __name__=='__main__':main()
