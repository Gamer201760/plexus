import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np

from artifacts import ROOT, file_record, revision, write_json

SEASONS = ("road", "summer", "winter")
BETA = float(np.log(2) / 2)
EXCLUDED = ["Москва", "Санкт-Петербург", "Севастополь"]
PUBLIC = ROOT / "frontend" / "atlas" / "public"
OVERHEAD_H = {"air": 2.5, "rail": 1.0}
CLOSURE_SAMPLE = 3000
CLOSURE_TOL_H = 0.02


def point_hansen(best, markets):
    weights = np.exp(-BETA * np.where(np.isfinite(best), best, np.inf).astype(np.float64))
    return weights @ markets


def city_matrix(con, season, cities, road, best, point_row):
    count = len(cities)
    F = np.full((count, count), np.inf)
    np.fill_diagonal(F, 0.0)
    anchors = {}
    for k, city in enumerate(cities.itertuples()):
        i = point_row.get(city.oktmo)
        if i is not None:
            anchors[k] = i
            F[k] = best[i]
    missing = [k for k in range(count) if k not in anchors]
    if missing:
        E = F.copy()
        if season != "road":
            ic = con.execute(
                """select city_from, city_to, distance_hr, transport_type from stg_intercity
                   where distance_hr is not null and transport_type in ('air', 'rail')"""
            ).df()
            position = {city: index for index, city in enumerate(cities.city)}
            for leg in ic.itertuples():
                weight = leg.distance_hr + 84.0 + OVERHEAD_H[leg.transport_type]
                a, b = position[leg.city_from], position[leg.city_to]
                if a in missing or b in missing:
                    E[a, b] = min(E[a, b], weight)
        for k in missing:
            for m, i in anchors.items():
                r = float(road[i, k])
                E[k, m] = min(E[k, m], r)
                E[m, k] = min(E[m, k], r)
        for k in range(count):
            np.minimum(E, E[:, k, None] + E[None, k, :], out=E)
        F = E
    return F


def closure_gap(road, best, F, generator):
    sample = generator.choice(len(road), size=min(CLOSURE_SAMPLE, len(road)), replace=False)
    reconstructed = np.full((len(sample), F.shape[1]), np.inf)
    for k in range(F.shape[0]):
        np.minimum(reconstructed, road[sample, k, None].astype(np.float64) + F[k][None, :],
                   out=reconstructed)
    reference = np.where(np.isfinite(best[sample]), best[sample], np.inf).astype(np.float64)
    both = np.isfinite(reconstructed) & np.isfinite(reference)
    same = np.isfinite(reconstructed) == np.isfinite(reference)
    gap = float(np.abs(reconstructed[both] - reference[both]).max()) if both.any() else 0.0
    return gap, bool(same.all())


def export_season(con, season, cities, region_ids, out_dir):
    pts = con.execute(
        """select a.point_id, a.region, a.population from np_access a
           where a.season = ? and a.region not in (?, ?, ?) order by a.point_id""",
        [season, *EXCLUDED],
    ).df()
    if pts.point_id.duplicated().any() or pts.population.isna().any():
        raise ValueError("duplicate points or missing population")
    con.execute("drop table if exists pt_order")
    con.execute(
        """create temp table pt_order as
           select point_id, row_number() over (order by point_id) - 1 as ri
           from np_access where season = ? and region not in (?, ?, ?)""",
        [season, *EXCLUDED],
    )
    shape = (len(pts), len(cities))
    road = np.full(shape, np.inf, np.float32)
    best = np.full(shape, np.inf, np.float32)
    chunks = con.execute(
        """select p.ri, c.ci, t.road_h, t.best_h from np_city_times t
           join pt_order p using (point_id) join city_order c using (city)
           where t.season = ?""",
        [season],
    )
    while True:
        chunk = chunks.fetch_df_chunk(32)
        if chunk.empty:
            break
        road[chunk.ri.values, chunk.ci.values] = chunk.road_h.values
        best[chunk.ri.values, chunk.ci.values] = chunk.best_h.values
    point_row = {pid: i for i, pid in enumerate(pts.point_id)}
    F = city_matrix(con, season, cities, road, best, point_row)
    gap, consistent = closure_gap(road, best, F, np.random.default_rng(0))
    if gap > CLOSURE_TOL_H or not consistent:
        raise ValueError(f"{season}: city matrix does not close point times, gap {gap}")
    markets = cities.population.values.astype(np.float64)
    hansen = point_hansen(best, markets)
    region_index = pts.region.map(region_ids)
    if region_index.isna().any():
        raise ValueError("unknown region in access table")
    regions = sorted(region_ids.values())
    region_pos = {rid: i for i, rid in enumerate(regions)}
    region_idx = region_index.map(region_pos).values.astype(np.int32)
    population = pts.population.values.astype(np.float64)
    season_dir = out_dir / season
    season_dir.mkdir(parents=True, exist_ok=True)
    np.save(season_dir / "road_h.npy", road)
    np.save(season_dir / "best_h.npy", best)
    np.save(season_dir / "city_best_h.npy", F)
    np.save(season_dir / "population.npy", population)
    np.save(season_dir / "region_idx.npy", region_idx)
    return {"points": len(pts), "closure_gap_h": gap,
            "hansen": hansen, "population": population, "region_idx": region_idx,
            "regions": regions}


def published_reference(season, result, base):
    rows = json.loads((PUBLIC / "indices.json").read_text())
    published = {row["region_id"]: row["hansen_idx"] for row in rows if row["season"] == season}
    weights = np.bincount(result["region_idx"], weights=result["population"],
                          minlength=len(result["regions"]))
    sums = np.bincount(result["region_idx"], weights=result["population"] * result["hansen"],
                       minlength=len(result["regions"]))
    index = sums / weights / base * 100
    diffs = [abs(index[i] - published[rid]) / max(published[rid], 1e-9)
             for i, rid in enumerate(result["regions"]) if rid in published]
    return {"regions_compared": len(diffs), "max_rel_diff": max(diffs), "index": index}


def main(database, out_dir):
    con = duckdb.connect(str(database), read_only=True)
    con.execute("set threads = 4")
    cities = con.sql(
        """select city, oktmo, region, is_capital, population, lat, lon
           from market_cities order by city"""
    ).df()
    if cities.city.duplicated().any():
        raise ValueError("duplicate market cities")
    con.execute("create temp table city_order (city varchar, ci integer)")
    con.executemany("insert into city_order values (?, ?)",
                    [(city, i) for i, city in enumerate(cities.city)])
    region_ids = dict(con.sql(
        "select region, oktmo from stg_settlements where object_level = 'Регион'"
    ).df().itertuples(index=False, name=None))
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for season in SEASONS:
        results[season] = export_season(con, season, cities, region_ids, out_dir)
        print(f"[{season}] points={results[season]['points']} "
              f"closure_gap={results[season]['closure_gap_h']:.4f}h", flush=True)
    road = results["road"]
    base = float(np.average(road["hansen"], weights=road["population"]))
    if not np.isfinite(base) or base <= 0:
        raise ValueError("positive population-weighted road baseline is required")
    manifest = {
        "schema_version": 1, "model_version": "hansen-frequency-v2",
        "created_at": datetime.now(timezone.utc).isoformat(), "code": revision(),
        "normalization_base": base, "half_life_h": 2, "beta_per_h": BETA,
        "trunk": {"overhead_h": OVERHEAD_H, "waiting_h_week": 84.0,
                  "assumed_frequency_per_week": 1},
        "assumptions": ["uniform_headways_random_need", "independent_transfer_waits",
                        "seasonal_roads_approximated_from_is_seasonal",
                        "roads_undirected_for_national_model"],
        "excluded_origin_regions": EXCLUDED,
        "cities": cities.replace({np.nan: None}).to_dict("records"),
        "regions": [{"region_id": rid, "name": name}
                    for name, rid in sorted(region_ids.items(), key=lambda item: item[1])
                    if name not in EXCLUDED],
        "seasons": {},
        "published_reference": {},
    }
    for season, result in results.items():
        reference = published_reference(season, result, base)
        manifest["seasons"][season] = {
            "points": result["points"], "closure_gap_h": result["closure_gap_h"],
            "files": [file_record(out_dir / season / name, out_dir)
                      for name in ("road_h.npy", "best_h.npy", "city_best_h.npy",
                                   "population.npy", "region_idx.npy")],
        }
        manifest["published_reference"][season] = {
            "regions_compared": reference["regions_compared"],
            "max_rel_diff": reference["max_rel_diff"],
        }
        print(f"[{season}] vs published indices.json: max rel diff "
              f"{reference['max_rel_diff']:.4f}", flush=True)
    encoded = json.dumps({key: value for key, value in manifest.items() if key != "created_at"},
                         ensure_ascii=False, sort_keys=True, default=str)
    manifest["artifact_version"] = hashlib.sha256(encoded.encode()).hexdigest()
    write_json(out_dir / "manifest.json", manifest)
    print(f"artifact {manifest['artifact_version']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=ROOT / "data/casechamp.duckdb")
    parser.add_argument("--output", type=Path, default=ROOT / "data/scenario_ru")
    args = parser.parse_args()
    main(args.database, args.output)
