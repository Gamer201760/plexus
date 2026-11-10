import hashlib
import json
from pathlib import Path

from client import ClickHouse

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    client = ClickHouse()
    client.request("CREATE DATABASE IF NOT EXISTS plexus_atlas")
    client.request("DROP TABLE IF EXISTS plexus_atlas.documents__loading")
    client.request("""CREATE TABLE plexus_atlas.documents__loading (
        path String, sha256 String, body String
    ) ENGINE=MergeTree ORDER BY path""")
    root = ROOT / "frontend/atlas/public"
    entries = []
    for path in sorted(root.rglob("*.json")):
        body = path.read_text()
        json.loads(body)
        row = {
            "path": str(path.relative_to(root)),
            "sha256": hashlib.sha256(body.encode()).hexdigest(),
            "body": body,
        }
        client.request(
            "INSERT INTO plexus_atlas.documents__loading FORMAT JSONEachRow",
            json.dumps(row, ensure_ascii=False).encode(),
        )
        entries.append({"path": row["path"], "sha256": row["sha256"]})
    actual = client.rows(
        "SELECT path, sha256, lower(hex(SHA256(body))) AS actual FROM plexus_atlas.documents__loading"
    )
    if len(actual) != len(entries) or any(
        row["sha256"] != row["actual"] for row in actual
    ):
        raise RuntimeError("Atlas document checksum mismatch")
    exists = client.rows("EXISTS TABLE plexus_atlas.documents")[0]["result"]
    if exists:
        client.request(
            "EXCHANGE TABLES plexus_atlas.documents AND plexus_atlas.documents__loading"
        )
        client.request("DROP TABLE plexus_atlas.documents__loading")
    else:
        client.request(
            "RENAME TABLE plexus_atlas.documents__loading TO plexus_atlas.documents"
        )
    for name in ["links", "points", "regions"]:
        client.request(f"""CREATE OR REPLACE VIEW plexus_atlas.{name} AS
            SELECT path AS source, JSONExtractString(record, 'id') AS id, record
            FROM plexus_atlas.documents ARRAY JOIN JSONExtractArrayRaw(body, '{name}') AS record
            WHERE path IN ('atlas.json', 'network-links.json')""")
    (ROOT / "data/analytics-atlas.json").write_text(json.dumps(entries, indent=2))
    print(json.dumps({"documents": len(entries), "sha256_match": True}))


if __name__ == "__main__":
    main()
