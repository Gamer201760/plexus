import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pyarrow.parquet as pq
import duckdb
import pyarrow as pa

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'etl'))
import osm_extract
import graph_russia
from road_access import include_way


class RoadCollectionTests(unittest.TestCase):
    def test_graph_anchors_settlement_to_road_instead_of_closer_ferry(self):
        rows = []
        for identifier, highway, latitude, node_ids in [
            (1, 'ferry', 60., [1, 2]),
            (2, 'residential', 60.002, [3, 4]),
        ]:
            row = {field.name: None for field in osm_extract.SCHEMA}
            row.update(way_id=identifier, highway=highway, nodes=node_ids,
                       lat=[latitude, latitude], lon=[50., 50.01],
                       is_ferry=highway == 'ferry', is_seasonal=False,
                       is_bridge=False, operating_season='all', source_tags='{}')
            rows.append(row)
        original = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / 'ways'
                source.mkdir()
                pq.write_table(pa.Table.from_pylist(rows, schema=osm_extract.SCHEMA), source / 'test.parquet')
                database = root / 'test.duckdb'
                with duckdb.connect(str(database)) as con:
                    con.execute("create table stg_settlements as select 'a' oktmo, 'Test' region, 60. latitude, 50. longitude, 100 population, 'Населенный пункт' object_level")
                with patch.multiple(graph_russia, ROOT=root, SRC=source, OUT=root / 'graph', DB=database, MIN_COMP_NODES=2):
                    graph_russia.main()
                points = pq.read_table(root / 'graph/points.parquet').to_pylist()
                nodes = pq.read_table(root / 'graph/nodes.parquet').to_pylist()
                self.assertTrue(points[0]['on_road'])
                self.assertEqual(nodes[points[0]['node']]['osm_node'], 3)
        finally:
            os.chdir(original)

    def test_public_service_connector_is_preserved_with_real_osm_nodes(self):
        source = '''<osm version="0.6">
<node id="1" lat="60" lon="50"/><node id="2" lat="60" lon="50.01"/>
<node id="3" lat="60" lon="50.02"/><node id="4" lat="60" lon="50.03"/>
<way id="1"><nd ref="1"/><nd ref="2"/><tag k="highway" v="residential"/></way>
<way id="2"><nd ref="2"/><nd ref="3"/><tag k="highway" v="service"/></way>
<way id="3"><nd ref="3"/><nd ref="4"/><tag k="highway" v="residential"/></way>
<way id="4"><nd ref="1"/><nd ref="4"/><tag k="highway" v="service"/><tag k="access" v="private"/></way>
</osm>'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / 'connector.osm'
            fixture.write_text(source)
            with patch.object(osm_extract, 'OUT', root / 'out'):
                osm_extract.main(fixture)
            rows = pq.read_table(root / 'out/connector.parquet').to_pylist()
            self.assertEqual([row['way_id'] for row in rows], [1, 2, 3])
            self.assertEqual(rows[1]['nodes'], [2, 3])
            self.assertEqual(rows[1]['operating_season'], 'all')

    def test_restricted_service_is_not_used_as_a_through_connection(self):
        for restriction in ['no', 'private', 'destination', 'customers', 'delivery']:
            self.assertFalse(include_way({'highway': 'service', 'access': restriction}))
        for subtype in ['parking_aisle', 'driveway', 'drive-through', 'emergency_access']:
            self.assertFalse(include_way({'highway': 'service', 'service': subtype}))
        self.assertFalse(include_way({'highway': 'service', 'access:conditional': 'no @ (winter)'}))
        self.assertTrue(include_way({'highway': 'service', 'access': 'private', 'motorcar': 'yes'}))
        self.assertFalse(include_way({'highway': 'service', 'motorcar': 'no', 'access': 'yes'}))
        self.assertFalse(include_way({'highway': 'footway'}))


if __name__ == '__main__':
    unittest.main()
