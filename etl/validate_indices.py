import argparse
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np

from artifacts import ROOT, file_record, revision, write_json


def validate(database: Path) -> dict:
    with duckdb.connect(str(database), read_only=True) as con:
        frame = con.sql("select season, point_id, population, hansen_2h, hansen_idx, reachable_markets from idx_np").df()
        regions = con.sql("select season, region, hansen_idx, population, covered_population, covered_settlements, n_np from idx_region").df()
        metadata = con.sql("select * from index_model_metadata").df().iloc[0].to_dict()
        duplicates = con.sql("select count(*) from (select season, point_id from idx_np group by all having count(*) > 1)").fetchone()[0]
        assert duplicates == 0
        assert set(frame.season) == {"road", "road_summer", "road_winter", "summer", "winter"}
        assert all(len(group) == 155412 for _, group in frame.groupby("season"))
        assert all(len(group) == 82 for _, group in regions.groupby("season"))
        assert (frame.population >= 0).all() and frame.population.notna().all()
        assert np.isfinite(frame.hansen_idx).all() and (frame.hansen_idx >= 0).all()
        assert (regions.covered_population <= regions.population).all()
        assert (regions.covered_settlements <= regions.n_np).all()
        pivot = frame.pivot(index="point_id", columns="season", values="hansen_2h")
        relations = (("road_summer", "road"), ("road_winter", "road"),
                     ("summer", "road_summer"), ("winter", "road_winter"))
        monotonic = {}
        for larger, smaller in relations:
            tolerance = np.maximum(1e-8, abs(pivot[smaller]) * 1e-7)
            violations = int((pivot[larger] + tolerance < pivot[smaller]).sum())
            assert violations == 0, (larger, smaller, violations)
            monotonic[f"{larger}_not_worse_than_{smaller}"] = violations
        base = frame[frame.season == "road"]
        normalized = float(np.average(base.hansen_idx, weights=base.population))
        assert abs(normalized - 100.) < 1e-7
        independent = []
        for season in ("road", "road_summer", "summer", "winter"):
            for point in ("93701000001", "93643425101", "93650444101"):
                values = con.execute("select t.best_h,c.population from np_city_times t join market_cities c using(city) where t.season=? and t.point_id=?", [season, point]).fetchall()
                reference = sum(population * np.exp(-np.log(2) / 2 * hours) for hours, population in values)
                stored = frame[(frame.season == season) & (frame.point_id == point)].hansen_2h.iloc[0]
                assert np.isclose(reference, stored, rtol=1e-10, atol=1e-6)
                independent.append({"point_id": point, "scenario": season, "reference_hansen": float(reference), "stored_hansen": float(stored)})
    report = {"measured_at": datetime.now(timezone.utc).isoformat(), "code": revision(),
              "model_metadata": metadata, "origin_rows": len(frame), "regional_rows": len(regions),
              "origins_per_scenario": 155412, "regions_per_scenario": 82,
              "road_weighted_mean": normalized, "monotonicity_violations": monotonic,
              "independent_formula_checks": independent,
              "tolerance": "relative 1e-7 for graph monotonicity; 1e-10 for formula samples",
              "input": file_record(database),
              "limitation": "checks model arithmetic and internal graph invariants, not field operability"}
    write_json(ROOT / "docs/results/national-validation.json", report)
    print(f"validated {len(regions)} regional rows; road mean {normalized}; 12 formula controls")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=ROOT / "data/casechamp.duckdb")
    validate(parser.parse_args().database)
