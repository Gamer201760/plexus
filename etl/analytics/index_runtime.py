from client import ClickHouse
from normalize_search import EXPRESSION


def main() -> None:
    c=ClickHouse()
    models={
      'locations': "SELECT p.point_id AS point_id,coalesce(s.settlement,p.point_id) AS settlement,p.region AS region,p.node AS node,p.lon AS lon,p.lat AS lat,p.snap_km AS snap_km,p.population AS population FROM plexus_graph.points p LEFT JOIN (SELECT oktmo,settlement FROM plexus_casechamp.stg_settlements WHERE object_level='Населенный пункт') s ON p.point_id=s.oktmo SETTINGS join_use_nulls=1",
      'region_points': "SELECT i.region AS region,i.season AS season,i.point_id AS point_id,i.population AS population,p.node AS node,p.snap_km AS snap_km FROM plexus_casechamp.idx_np i LEFT JOIN plexus_graph.points p ON i.point_id=p.point_id SETTINGS join_use_nulls=1",
    }
    for name,sql in models.items():
        target='plexus_graph.'+name;stage=target+'__loading'
        order='region,point_id' if name=='locations' else 'region,season,point_id'
        c.request(f'DROP TABLE IF EXISTS {stage}')
        c.request(f'CREATE TABLE {stage} ENGINE=MergeTree ORDER BY ({order}) SETTINGS allow_nullable_key=1,index_granularity=1024 AS '+sql)
        if c.rows(f'EXISTS TABLE {target}')[0]['result']:
            c.request(f'EXCHANGE TABLES {target} AND {stage}');c.request(f'DROP TABLE {stage}')
        else:c.request(f'RENAME TABLE {stage} TO {target}')
        print(name,flush=True)
    statements=[
     "ALTER TABLE plexus_graph.ways ADD PROJECTION IF NOT EXISTS by_osm_id (SELECT way_id,way_idx ORDER BY way_id)",
     "ALTER TABLE plexus_graph.ways MATERIALIZE PROJECTION by_osm_id SETTINGS mutations_sync=1",
     "ALTER TABLE plexus_graph.points ADD PROJECTION IF NOT EXISTS by_point (SELECT point_id,node,snap_km ORDER BY point_id)",
     "ALTER TABLE plexus_graph.points MATERIALIZE PROJECTION by_point SETTINGS mutations_sync=1",
     "ALTER TABLE plexus_graph.locations ADD INDEX IF NOT EXISTS place_name lowerUTF8(ifNull(settlement,'')) TYPE ngrambf_v1(3,8192,3,0) GRANULARITY 1",
     "ALTER TABLE plexus_graph.locations MATERIALIZE INDEX place_name SETTINGS mutations_sync=1",
     "ALTER TABLE plexus_atlas.atlas_settlements ADD COLUMN IF NOT EXISTS name_key String MATERIALIZED "+EXPRESSION,
     "ALTER TABLE plexus_atlas.atlas_settlements ADD INDEX IF NOT EXISTS place_name name_key TYPE ngrambf_v1(3,8192,3,0) GRANULARITY 1",
     "ALTER TABLE plexus_atlas.atlas_settlements MATERIALIZE INDEX place_name SETTINGS mutations_sync=1",
    ]
    for statement in statements:
        c.request(statement);print(statement,flush=True)

if __name__=='__main__':main()
