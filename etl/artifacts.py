import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def file_record(path: Path, root: Path = ROOT) -> dict:
    path, root = path.resolve(), root.resolve()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path), "bytes": path.stat().st_size,
            "sha256": digest.hexdigest()}


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def revision() -> dict:
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))
    return {"sha": sha, "dirty": dirty}


def source_record(directory: Path, url: str, license_name: str,
                  retrieved_at: str | None = None, response_headers: dict | None = None) -> dict:
    return {
        "schema_version": 1, "source_url": url, "license": license_name,
        "retrieved_at": retrieved_at, "observed_at": datetime.now(timezone.utc).isoformat(),
        "response_headers": response_headers or {},
        "files": [file_record(path, directory) for path in sorted(directory.rglob("*"))
                  if path.is_file() and path.name != ".source.json"],
    }


def verified_source(directory: Path, url: str) -> bool:
    manifest = directory / ".source.json"
    if not manifest.exists():
        return False
    try:
        record = json.loads(manifest.read_text())
    except (ValueError, OSError):
        return False
    if record["source_url"] != url or not record["files"]:
        return False
    actual = {str(path.relative_to(directory)) for path in directory.rglob("*")
              if path.is_file() and path != manifest}
    if actual != {entry["path"] for entry in record["files"]}:
        return False
    for entry in record["files"]:
        path = directory / entry["path"]
        if not path.is_file() or file_record(path, directory) != entry:
            return False
    return True
