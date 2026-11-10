from pathlib import Path

import duckdb

from app.repository.files.atlas import JsonAtlasRepository
from app.usecase.dto.atlas import IndexRecord


class SnapshotAtlasRepository(JsonAtlasRepository):
    def __init__(self, data_dir: Path, graph_root: Path) -> None:
        super().__init__(data_dir)
        self.graph_root = graph_root

    def indices(self) -> list[IndexRecord]:
        with self._lock:
            if self._indices is None:
                known = {r.id for r in self.regions()}
                with duckdb.connect(
                    str(self.graph_root / "casechamp.duckdb"), read_only=True
                ) as con:
                    names = {
                        str(name): str(code)
                        for code, name in con.execute(
                            "select oktmo, region from stg_settlements where object_level='Регион'"
                        ).fetchall()
                        if str(code) in known
                    }
                    rows = con.execute("""select region, season, sum(population), count(*),
                        sum(population*hansen_idx)/sum(population),
                        sum(population*hansen_1h)/sum(population),
                        sum(population*hansen_2h)/sum(population),
                        sum(population*hansen_4h)/sum(population),
                        sum(case when hansen_2h > 0 then population else 0 end),
                        count(*) filter(where hansen_2h > 0)
                        from idx_np group by region, season""").fetchall()
                self._indices = [
                    IndexRecord(
                        region_id=names[r[0]],
                        scenario=r[1],
                        total_population=int(r[2]),
                        total_settlements=int(r[3]),
                        hansen=float(r[4]),
                        hansen_1h=float(r[5]),
                        hansen_2h=float(r[6]),
                        hansen_4h=float(r[7]),
                        covered_population=int(r[8]),
                        covered_settlements=int(r[9]),
                        model_version="hansen-release-20261107",
                        artifact_version="data-20261107",
                    )
                    for r in rows
                    if r[0] in names
                ]
            return self._indices
