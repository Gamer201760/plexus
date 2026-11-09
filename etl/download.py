import shutil
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from artifacts import source_record, verified_source, write_json
from sources import SOURCES


RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def prune(dst: Path) -> None:
    shutil.rmtree(dst / "__MACOSX", ignore_errors=True)
    if not any(dst.glob("*.parquet")):
        return
    for path in dst.iterdir():
        if path.is_dir() and path.name.endswith("_parts"):
            shutil.rmtree(path)
        elif path.suffix in (".csv", ".xlsx"):
            path.unlink()


def fetch(name: str, url: str) -> None:
    dst = RAW / name
    if verified_source(dst, url):
        print(f"skip verified {name}", flush=True)
        return
    if dst.exists():
        raise ValueError(f"unverified input {dst}; move it aside or record its provenance before retrying")
    RAW.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=RAW) as temporary:
        stage = Path(temporary)
        archive = stage / "source.zip"
        print(f"get {name}", flush=True)
        request = urllib.request.Request(url, headers={"User-Agent": "plexus-a2/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as stream:
            headers = {key: response.headers[key] for key in ("ETag", "Last-Modified")
                       if key in response.headers}
            shutil.copyfileobj(response, stream)
        extracted = stage / "extracted"
        extracted.mkdir()
        with zipfile.ZipFile(archive) as zipped:
            for member in zipped.infolist():
                if not (extracted / member.filename).resolve().is_relative_to(extracted.resolve()):
                    raise ValueError(f"bad path in archive: {member.filename}")
            zipped.extractall(extracted)
        prune(extracted)
        if not any(path.is_file() for path in extracted.rglob("*")):
            raise ValueError(f"empty archive for {name}")
        record = source_record(extracted, url, "CC BY 4.0 (catalog declaration)",
                               datetime.now(timezone.utc).isoformat(), headers)
        write_json(extracted / ".source.json", record)
        extracted.rename(dst)


if __name__ == "__main__":
    for name in sys.argv[1:] or list(SOURCES):
        fetch(name, SOURCES[name])
