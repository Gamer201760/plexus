import json
from dataclasses import dataclass
from pathlib import Path

from app.repository.files.airports import FileAirportRepository
from app.repository.files.atlas import JsonAtlasRepository
from app.repository.files.snapshot import SnapshotAtlasRepository
from app.usecase.dto import RegionRecord,PointRecord,LinkRecord,EconomyRecord,SettlementRecord,SourceRecord,WinterRoadRecord,IndexRecord,BoundaryShape,RegionShape
from app.usecase.airports import Airport
from client import ClickHouse
from typed_tables import write_records

ROOT=Path(__file__).resolve().parents[2]

@dataclass
class Metadata:
    key: str
    value: str


def main() -> None:
    root=ROOT/'frontend/atlas/public'
    atlas=SnapshotAtlasRepository(root,ROOT/'data')
    airport=FileAirportRepository(root).catalog()
    client=ClickHouse(); results=[]
    tables=[
      ('atlas_regions',RegionRecord,atlas.regions(),'id'),
      ('atlas_points',PointRecord,list(atlas.points().values()),'region_id,id'),
      ('atlas_links',LinkRecord,atlas.links(),'region_id,mode,season,id'),
      ('atlas_economy',EconomyRecord,list(atlas.economy().values()),'region_id'),
      ('atlas_sources',SourceRecord,atlas.sources(),'id,ordinal'),
      ('atlas_winter_roads',WinterRoadRecord,atlas.winter_roads(),'ordinal'),
      ('atlas_indices',IndexRecord,atlas.indices(),'scenario,region_id'),
      ('atlas_exported_indices',IndexRecord,JsonAtlasRepository(root).indices(),'scenario,region_id'),
      ('atlas_boundaries',BoundaryShape,atlas.boundaries(),'id'),
      ('atlas_shapes',RegionShape,atlas.geo().shapes,'id'),
      ('atlas_airports',Airport,airport.airports,'id'),
    ]
    for name,kind,rows,order in tables:
        results.append(write_records(client,name,kind,rows,order)); print(results[-1],flush=True)
    rows=[s for region in atlas.regions() for s in atlas.settlements(region.id)]
    results.append(write_records(client,'atlas_settlements',SettlementRecord,rows,'region_id,id'))
    metadata=[Metadata('view_box',atlas.geo().view_box),Metadata('geo_source',atlas.geo().source or ''),
              Metadata('geo_url',atlas.geo().source_url or ''),Metadata('airport_url',airport.source_url),Metadata('airport_date',airport.retrieved_at)]
    paths=[ROOT/'data/casechamp.duckdb',*sorted((ROOT/'data/graph_ru').glob('*.parquet'))]
    signature=[(p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in paths]
    metadata.append(Metadata('graph_revision',json.dumps(signature)))
    results.append(write_records(client,'atlas_metadata',Metadata,metadata,'key'))
    (ROOT/'work/clickhouse-migration/typed-atlas.json').write_text(json.dumps(results,indent=2))
    print(results[-2:],flush=True)

if __name__=='__main__':main()
