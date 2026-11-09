import argparse
import json

from artifacts import ROOT, file_record, revision, source_record, verified_source, write_json
from sources import SOURCES


def main() -> None:
    records = []
    missing = []
    for name, url in SOURCES.items():
        directory = ROOT / "data" / "raw" / name
        if not directory.exists() or not any(directory.glob("*.parquet")) and not any(directory.glob("*.csv")):
            missing.append(name)
            continue
        if verified_source(directory, url):
            record = json.loads((directory / ".source.json").read_text())
        elif (directory / ".source.json").exists():
            raise ValueError(f"snapshot checksum mismatch: {name}")
        else:
            record = source_record(directory, url, "CC BY 4.0 (catalog declaration)")
            record["provenance_status"] = "downloaded_in_session_observed_snapshot"
            write_json(directory / ".source.json", record)
        records.append({"name": name, **record})
    write_json(ROOT / "data" / "source-manifest.json", {
        "schema_version": 1, "code": revision(), "sources": records, "missing": missing,
        "manual_sources": [file_record(path) for path in sorted((ROOT / "data_manual").rglob("*.csv"))],
    })
    print(f"snapshots: {len(records)}; missing: {', '.join(missing)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-observed-snapshots", action="store_true", required=True)
    parser.parse_args()
    main()
