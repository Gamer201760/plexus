import json
from dataclasses import asdict
from pathlib import Path

from app.adapter.road_graph.data import VERSION
from app.domain.road_economics import MoneyAssumptions, MoneyEffect
from app.usecase.dto.road_graph import (
    RoadAddition,
    RoadChange,
    RoadJob,
    RoadResult,
    SettlementEffect,
)


def restore_jobs(root: Path) -> dict[str, RoadJob]:
    result = {}
    paths = sorted((root / "scenario-results").glob("*.json"), key=lambda p: p.stat().st_mtime)
    for path in paths[-100:]:
        if len(path.stem) != 32 or any(c not in "0123456789abcdef" for c in path.stem):
            continue
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
        job = RoadJob(**row)
        if job.version == VERSION:
            result[job.id] = job
    return result


def save_job(root: Path, job: RoadJob) -> None:
    folder = root / "scenario-results"
    folder.mkdir(exist_ok=True)
    path = folder / f"{job.id}.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(asdict(job), ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
