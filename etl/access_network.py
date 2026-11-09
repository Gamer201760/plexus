import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


OVERHEAD_H = {"rail": 1.0, "air": 2.5}
TRUNK_ASSUMED_FREQUENCY = 1.0
SNAP_KMH = 15.
SNAP_MAX_KM = 5.


def xyz(latitude, longitude):
    lat, lon = np.radians(latitude), np.radians(longitude)
    return np.c_[np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)]


def anchor_cities(cities, points, nodes, node_count):
    cities = cities.merge(points[["point_id", "node", "on_road", "snap_h"]],
                          left_on="oktmo", right_on="point_id", how="left")
    cities["anchor_kind"] = "settlement_road"
    missing = cities.node.isna() | ~cities.on_road.fillna(False).astype(bool)
    cities["anchor_snap_km"] = cities.snap_h * SNAP_KMH
    if missing.any():
        tree = cKDTree(xyz(nodes.lat.values, nodes.lon.values))
        chord, indices = tree.query(xyz(cities.lat[missing].values, cities.lon[missing].values))
        km = 12742 * np.arcsin(np.clip(chord / 2, 0., 1.))
        for position, node, distance in zip(cities.index[missing], indices, km):
            if distance <= SNAP_MAX_KM:
                cities.loc[position, ["node", "snap_h", "anchor_kind", "anchor_snap_km"]] = (
                    node, distance / SNAP_KMH, "nearest_road", distance)
            else:
                cities.loc[position, ["node", "snap_h", "anchor_kind", "anchor_snap_km"]] = (
                    node_count, 0., "virtual_market", distance)
                matching = points.point_id == cities.at[position, "oktmo"]
                points.loc[matching, "node"] = node_count
                points.loc[matching, "snap_h"] = 0.
                node_count += 1
    cities["node"] = cities.node.astype(np.int64)
    return cities, points, node_count


def trunk_matrix(intercity, cities):
    positions = {city: index for index, city in enumerate(cities.city)}
    matrix = np.full((len(cities), len(cities)), np.inf)
    np.fill_diagonal(matrix, 0.)
    legs = intercity[intercity.transport_type.isin(OVERHEAD_H)].copy()
    if not np.isfinite(legs.distance_hr).all() or (legs.distance_hr < 0).any():
        raise ValueError("invalid intercity travel time")
    legs["frequency_per_week"] = np.nan
    legs["assumed_frequency_per_week"] = TRUNK_ASSUMED_FREQUENCY
    legs["waiting_h"] = 84 / TRUNK_ASSUMED_FREQUENCY
    legs["overhead_h"] = legs.transport_type.map(OVERHEAD_H)
    legs["total_h"] = legs.distance_hr + legs.waiting_h + legs.overhead_h
    for row in legs.itertuples():
        source, target = positions[row.city_from], positions[row.city_to]
        matrix[source, target] = min(matrix[source, target], row.total_h)
    return matrix, legs
