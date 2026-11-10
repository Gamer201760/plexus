import json
from dataclasses import asdict
from pathlib import Path

from app.domain.errors import InvalidQuery
from app.domain.road_analysis import SettlementImpact
from app.usecase.dto import BoundaryShape
from app.usecase.road_analysis import (
    AnalysisDetail,
    AnalysisFailure,
    AnalysisJob,
    Candidate,
    ImpactLocation,
    VerifiedRoad,
)


class FileAnalysisStore:
    def __init__(self, root: Path) -> None:
        self.root = root / "road-analyses"

    def load(self) -> list[tuple[AnalysisJob, BoundaryShape]]:
        result = []
        for path in sorted(self.root.glob("*/state.json"), key=lambda p: p.stat().st_mtime):
            try:
                raw = json.loads(path.read_text())
                row = raw["job"]
                row["candidates"] = [Candidate(**c) for c in row["candidates"]]
                row["results"] = [
                    VerifiedRoad(**{**r, "candidate": Candidate(**r["candidate"])})
                    for r in row["results"]
                ]
                row["failures"] = [AnalysisFailure(**f) for f in row["failures"]]
                result.append((AnalysisJob(**row), BoundaryShape(**raw["boundary"])))
            except (ValueError, TypeError, KeyError):
                continue
        return result

    def write(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False))
        temporary.replace(path)

    def save(self, job: AnalysisJob, boundary: BoundaryShape) -> None:
        self.write(
            self.root / job.id / "state.json", {"job": asdict(job), "boundary": asdict(boundary)}
        )

    def save_detail(self, analysis_id: str, detail: AnalysisDetail) -> None:
        self.write(
            self.root / analysis_id / f"{detail.result.candidate.way_id}.json", asdict(detail)
        )

    def detail(self, analysis_id: str, way_id: int) -> AnalysisDetail:
        path = self.root / analysis_id / f"{way_id}.json"
        if not path.exists():
            raise InvalidQuery("Verified result is unavailable")
        raw = json.loads(path.read_text())
        r = raw["result"]
        return AnalysisDetail(
            VerifiedRoad(**{**r, "candidate": Candidate(**r["candidate"])}),
            raw["lines"],
            [
                ImpactLocation(**{**p, "impact": SettlementImpact(**p["impact"])})
                for p in raw["settlements"]
            ],
        )
