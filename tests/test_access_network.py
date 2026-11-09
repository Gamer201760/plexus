import sys
import unittest
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))
from access_network import anchor_cities, trunk_matrix
from access_russia import manual_edges


class AccessNetworkTests(unittest.TestCase):
    def test_remote_market_does_not_receive_a_free_road_connection(self):
        cities = pd.DataFrame({"city": ["remote"], "oktmo": ["a"], "lat": [60.], "lon": [100.]})
        points = pd.DataFrame({"point_id": ["a"], "node": [-1], "on_road": [False], "snap_h": [10.]})
        nodes = pd.DataFrame({"lat": [50.], "lon": [90.]})
        anchored, points, size = anchor_cities(cities, points, nodes, 1)
        self.assertEqual(size, 2)
        self.assertEqual(anchored.node.iloc[0], 1)
        self.assertEqual(points.node.iloc[0], 1)
        self.assertEqual(anchored.anchor_kind.iloc[0], "virtual_market")
        self.assertGreater(anchored.anchor_snap_km.iloc[0], 5.)

    def test_near_market_retains_measured_access_time(self):
        cities = pd.DataFrame({"city": ["near"], "oktmo": ["absent"], "lat": [50.001], "lon": [90.]})
        points = pd.DataFrame({"point_id": ["a"], "node": [0], "on_road": [True], "snap_h": [0.]})
        nodes = pd.DataFrame({"lat": [50.], "lon": [90.]})
        anchored, _, size = anchor_cities(cities, points, nodes, 1)
        self.assertEqual(size, 1)
        self.assertEqual(anchored.anchor_kind.iloc[0], "nearest_road")
        self.assertGreater(anchored.snap_h.iloc[0], 0.)

    def test_unknown_trunk_frequency_is_not_stored_as_observed(self):
        cities = pd.DataFrame({"city": ["a", "b"]})
        intercity = pd.DataFrame({"city_from": ["a"], "city_to": ["b"],
                                  "transport_type": ["air"], "distance_hr": [2.]})
        matrix, legs = trunk_matrix(intercity, cities)
        self.assertTrue(np.isnan(legs.frequency_per_week.iloc[0]))
        self.assertEqual(legs.assumed_frequency_per_week.iloc[0], 1.)
        self.assertEqual(legs.waiting_h.iloc[0], 84.)
        self.assertEqual(matrix[0, 1], 88.5)
        self.assertTrue(np.isinf(matrix[1, 0]))

    def test_season_and_transport_mode_filter_before_manual_route_edges(self):
        points = pd.DataFrame({"point_id": ["a", "b", "c"], "node": [0, 1, 2],
                               "on_road": [True] * 3, "snap_h": [0.] * 3})
        with duckdb.connect() as con:
            con.execute("create table manual_links_ru(season varchar, from_id varchar, to_id varchar, h double, mode varchar)")
            for season in ("summer", "winter"):
                con.execute("insert into manual_links_ru values (?, 'a', 'b', 1., 'winter_road'), (?, 'a', 'c', 2., 'air'), (?, 'b', 'c', 3., 'pontoon_bridge')", [season] * 3)
            for scenario, count in (("road_summer", 1), ("road_winter", 2), ("summer", 2), ("winter", 3)):
                source, _, _, _, _ = manual_edges(con, scenario, points, 3)
                self.assertEqual(len(source), count)


if __name__ == "__main__":
    unittest.main()
