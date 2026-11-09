from datetime import datetime, timezone

import duckdb
import numpy as np
from scipy.stats import spearmanr

from artifacts import ROOT, file_record, revision, write_json


def main():
    database = ROOT / "data/casechamp.duckdb"
    metadata = {"measured_at": datetime.now(timezone.utc).isoformat(), "code": revision(),
                "implementation": file_record(ROOT / "etl/index_sensitivity.py")}
    with duckdb.connect(str(database), read_only=True) as con:
        rows = con.sql("""select season, count(*) finite_pairs,
            count(*) filter (best_h > 72) pairs_over_72h,
            sum(c.population * exp(-ln(2.) * best_h / 2)) hansen_sum,
            sum(c.population * exp(-ln(2.) * best_h / 2)) filter (best_h > 72) hansen_tail,
            sum(c.population / (best_h + .5)) harris_sum,
            sum(c.population / (best_h + .5)) filter (best_h > 72) harris_tail
            from np_city_times t join market_cities c using (city) group by season order by season""").df().to_dict("records")
        for row in rows:
            row["hansen_tail_share"] = row["hansen_tail"] / row["hansen_sum"]
            row["harris_tail_share"] = row["harris_tail"] / row["harris_sum"]
        write_json(ROOT / "docs/results/cutoff-sensitivity.json", {
            **metadata, "method": "sum market contributions over all finite origin-target pairs; unweighted by origin population",
            "threshold_h": 72, "rows": rows,
            "limitation": "aggregate contribution sensitivity, not a maximum error bound for every origin"})
        regions = con.sql("select season,region,hansen_1h,hansen_2h,hansen_4h from idx_region order by season,region").df()
        rows = [{"scenario": season, "regions": len(group),
                 "spearman_1h_vs_2h": float(spearmanr(group.hansen_1h, group.hansen_2h).statistic),
                 "spearman_4h_vs_2h": float(spearmanr(group.hansen_4h, group.hansen_2h).statistic)}
                for season, group in regions.groupby("season")]
        write_json(ROOT / "docs/results/half-life-sensitivity.json", {
            **metadata, "method": "Spearman correlation of population-weighted regional Hansen scores, 82 regions per scenario",
            "rows": rows, "limitation": "parameter sensitivity, not behavioural calibration"})
        largest = con.sql("select city,population from market_cities order by population desc limit 1").fetchone()
        reduced = con.execute("""with removed as (
            select season,point_id,sum(c.population * exp(-ln(2.) * best_h / 2)) contribution
            from np_city_times t join market_cities c using(city) where city=? group by all)
            select i.season,i.region,
                sum(i.population * greatest(0,i.hansen_2h - coalesce(r.contribution,0))) / sum(i.population) reduced,
                sum(i.population * i.hansen_2h) / sum(i.population) baseline
            from idx_np i left join removed r using(season,point_id)
            group by i.season,i.region order by i.season,i.region""", [largest[0]]).df()
        rows = []
        for season, group in reduced.groupby("season"):
            loss = np.where(group.baseline > 0, (group.baseline - group.reduced) / group.baseline, 0.)
            worst = int(np.argmax(loss))
            rows.append({"scenario": season, "regions": len(group),
                         "rank_spearman": float(spearmanr(group.baseline, group.reduced).statistic),
                         "median_relative_loss": float(np.median(loss)),
                         "maximum_relative_loss": float(loss[worst]),
                         "maximum_loss_region": str(group.iloc[worst].region)})
        write_json(ROOT / "docs/results/target-coverage-sensitivity.json", {
            **metadata, "method": "leave out the largest population market; retain the original normalization base",
            "removed_market": largest[0], "removed_population": largest[1], "rows": rows,
            "limitation": "one target perturbation, not proof that the 180 markets represent all opportunities"})
    print("wrote cutoff, half-life and target-coverage sensitivity reports")


if __name__ == "__main__":
    main()
