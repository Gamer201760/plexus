import json
from dataclasses import asdict
from pathlib import Path

from app.domain.road_economics import MoneyAssumptions, MoneyEffect
from app.usecase.dto.road_graph import (
    GRAPH_DATA_VERSION,
    RoadAddition,
    RoadChange,
    RoadJob,
    RoadResult,
    SettlementEffect,
)


class FileRoadJobStore:
    def __init__(self, root: Path) -> None:
        self.folder = root / "scenario-results"

    def load(self) -> dict[str, RoadJob]:
        result = {}
        paths = sorted(self.folder.glob("*.json"), key=lambda p: p.stat().st_mtime)
        for path in paths[-100:]:
            if len(path.stem) != 32 or any(c not in "0123456789abcdef" for c in path.stem):
                continue
            job = road_job(path)
            if job.version == GRAPH_DATA_VERSION:
                result[job.id] = job
        return result

    def save(self, job: RoadJob) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{job.id}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(job), ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)


def road_job(path: Path) -> RoadJob:
    row = json.loads(path.read_text())
    row["changes"] = [RoadChange(**c) for c in row["changes"]]
    if row.get("addition"):
        row["addition"] = RoadAddition(**row["addition"])
    if row.get("money_assumptions"):
        row["money_assumptions"] = MoneyAssumptions(**row["money_assumptions"])
    if row.get("result"):
        money = row["result"].get("money")
        if money:
            money["assumptions"] = MoneyAssumptions(**money["assumptions"])
            row["result"]["money"] = MoneyEffect(**money)
        row["result"]["settlement_effects"] = [
            SettlementEffect(**effect) for effect in row["result"].get("settlement_effects", [])
        ]
        row["result"] = RoadResult(**row["result"])
    return RoadJob(**row)
