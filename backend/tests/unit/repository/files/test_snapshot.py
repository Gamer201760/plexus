from pathlib import Path

import duckdb

from app.repository.files.snapshot import SnapshotAtlasRepository
from app.usecase.dto import RegionRecord


class SnapshotWithShortName(SnapshotAtlasRepository):
    def regions(self) -> list[RegionRecord]:
        return [RegionRecord("11800000", "short display name", 1, 10)]


def test_snapshot_joins_region_identifiers_not_display_names(tmp_path: Path) -> None:
    with duckdb.connect(str(tmp_path / "casechamp.duckdb")) as con:
        con.execute(
            "create table stg_settlements as select '11800000' oktmo, "
            "'canonical database name' region, 'Регион' object_level"
        )
        con.execute(
            "create table idx_np as select 'canonical database name' region, "
            "'road' season, 10 population, 50. hansen_idx, 25. hansen_1h, "
            "50. hansen_2h, 75. hansen_4h"
        )
    rows = SnapshotWithShortName(tmp_path, tmp_path).indices()
    assert len(rows) == 1
    assert rows[0].region_id == "11800000"
    assert rows[0].hansen == 50
