from client import ClickHouse


def main():
    c=ClickHouse()
    c.request('DROP TABLE IF EXISTS plexus_graph.road_lookup__loading')
    c.request("CREATE TABLE plexus_graph.road_lookup__loading ENGINE=MergeTree ORDER BY (lookup,ref) SETTINGS index_granularity=256 AS SELECT DISTINCT replaceRegexpAll(lowerUTF8(value),'[^a-zа-яё0-9]','') AS lookup,ifNull(ref,'') AS ref FROM plexus_graph.ways ARRAY JOIN [ifNull(name,''),ifNull(ref,'')] AS value WHERE ref IS NOT NULL AND value!=''")
    if c.rows('EXISTS TABLE plexus_graph.road_lookup')[0]['result']:
        c.request('EXCHANGE TABLES plexus_graph.road_lookup AND plexus_graph.road_lookup__loading')
        c.request('DROP TABLE plexus_graph.road_lookup__loading')
    else:c.request('RENAME TABLE plexus_graph.road_lookup__loading TO plexus_graph.road_lookup')
    c.request('ALTER TABLE plexus_graph.ways ADD PROJECTION IF NOT EXISTS by_reference (SELECT way_idx,way_id,name,ref,km ORDER BY ref)')
    c.request('ALTER TABLE plexus_graph.ways MATERIALIZE PROJECTION by_reference SETTINGS mutations_sync=1')
    c.request("CREATE TABLE IF NOT EXISTS plexus_graph.region_codes ENGINE=MergeTree ORDER BY oktmo SETTINGS allow_nullable_key=1,index_granularity=256 AS SELECT oktmo,region FROM plexus_casechamp.stg_settlements WHERE object_level='Регион'")
    print(c.rows('SELECT count() AS lookup_rows FROM plexus_graph.road_lookup'))

if __name__=='__main__':main()
