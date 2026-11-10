import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_URL = "https://rw-y.ru/passengers/schedule/traffic/?special=Y"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work/regional-collection/rail-air-audit/yakutia-routes.json"


class ScheduleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.groups: list[list[dict[str, str | None]]] = []
        self.heading: str | None = None
        self.heading_parts: list[str] = []
        self.station: str | None = None
        self.station_parts: list[str] = []
        self.active = False

    def finish_station(self) -> None:
        if self.station is None:
            return
        text = " ".join(" ".join(self.station_parts).split())
        match = re.search(r"Прибытие:\s*(\d{2}:\d{2})", text)
        if "Прибытие:" in text and match is None:
            raise ValueError(f"Unrecognized arrival time for {self.station}: {text}")
        self.groups[-1].append({
            "name": self.station,
            "arrival_local_text": match.group(1) if match else None,
        })
        self.station = None
        self.station_parts = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h3", "h4"}:
            self.finish_station()
            self.heading = tag
            self.heading_parts = []

    def handle_data(self, data: str) -> None:
        if self.heading:
            self.heading_parts.append(data)
        elif self.station is not None:
            self.station_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != self.heading:
            return
        text = " ".join(" ".join(self.heading_parts).split())
        if tag == "h3":
            self.active = text == "График движения"
            if self.active:
                self.groups.append([])
        elif self.active:
            self.station = text
        self.heading = None
        self.heading_parts = []


def parse_schedule(raw: bytes, retrieved_at: str) -> dict:
    parser = ScheduleParser()
    parser.feed(raw.decode("utf-8-sig"))
    parser.close()
    parser.finish_station()
    if not parser.groups or any(len(group) < 2 for group in parser.groups):
        raise ValueError("Expected station chains with at least two stops")
    chains = []
    legs = []
    for number, stops in enumerate(parser.groups, 1):
        group_id = f"rw-y-traffic-{number:02d}"
        chains.append({
            "route_group_id": group_id,
            "source_group_position": number,
            "origin": stops[0]["name"],
            "destination": stops[-1]["name"],
            "train_number": None,
            "schedule_validity": "unknown",
            "frequency_per_week": None,
            "stops": stops,
        })
        for position, (origin, destination) in enumerate(zip(stops, stops[1:]), 1):
            legs.append({
                "route_group_id": group_id,
                "leg_position": position,
                "mode": "rail",
                "origin": origin["name"],
                "destination": destination["name"],
                "origin_arrival_local_text": origin["arrival_local_text"],
                "arrival_local_text": destination["arrival_local_text"],
                "time_basis": "unspecified_by_source",
                "duration_minutes": None,
                "day_offset": None,
                "frequency_per_week": None,
                "schedule_validity": "unknown",
                "source_url": SOURCE_URL,
                "retrieved_at": retrieved_at,
            })
    return {
        "schema_version": 1,
        "source_url": SOURCE_URL,
        "source_title": "График движения пассажирских поездов — Железные дороги Якутии",
        "retrieved_at": retrieved_at,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "access_level": "downloaded_document",
        "source_published_at": None,
        "schedule_validity": "unknown",
        "time_basis": "unspecified_by_source",
        "limitations": [
            "Station order follows separately displayed schedule groups.",
            "Route group identifiers are extraction identifiers, not train numbers.",
            "Arrival text is preserved; source does not state its time zone.",
            "Departure times, frequency, validity dates and midnight offsets are unknown.",
            "Consecutive stops do not establish track geometry or settlement coordinates.",
            "Groups are retained separately, including overlapping station chains.",
        ],
        "chains": chains,
        "legs": legs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--retrieved-at")
    args = parser.parse_args()
    if args.input:
        if not args.retrieved_at:
            parser.error("--retrieved-at is required when replaying --input")
        raw = args.input.read_bytes()
        retrieved_at = args.retrieved_at
    else:
        request = Request(SOURCE_URL, headers={"User-Agent": "Plexus transport source audit"})
        with urlopen(request, timeout=40) as response:
            raw = response.read()
        retrieved_at = datetime.now(timezone.utc).isoformat()
    datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
    result = parse_schedule(raw, retrieved_at)
    if args.snapshot:
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_bytes(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"chains": len(result["chains"]), "legs": len(result["legs"])}))


if __name__ == "__main__":
    main()
