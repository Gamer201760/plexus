import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv"


def export(source: Path, output: Path) -> None:
    airports = []
    with source.open() as file:
        for row in csv.DictReader(file):
            if row["iso_country"] != "RU" or row["type"] not in {
                "large_airport", "medium_airport", "small_airport"
            }:
                continue
            if row["type"] == "small_airport" and row["scheduled_service"] != "yes":
                continue
            airports.append({
                "id": row["ident"], "name": row["name"], "municipality": row["municipality"],
                "iata": row["iata_code"], "latitude": float(row["latitude_deg"]),
                "longitude": float(row["longitude_deg"]),
                "scheduled": row["scheduled_service"] == "yes", "kind": row["type"],
            })
    document = {"source_url": SOURCE, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "airports": sorted(airports, key=lambda row: row["id"])}
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    print(f"Exported {len(airports)} airports")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.source, args.output)
