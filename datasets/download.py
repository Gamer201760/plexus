import argparse
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import subprocess


def download(item):
    destination = pathlib.Path(item["destination"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    maximum = item.get("max_bytes", 268435456)
    process = subprocess.run(
        [
            "curl", "--fail", "--location", "--silent", "--show-error",
            "--retry", "2", "--connect-timeout", "20", "--max-time", "300",
            "--max-filesize", str(maximum), "--output", str(partial),
            "--write-out", "%{json}", item["url"],
        ],
        capture_output=True,
        text=True,
    )
    result = {
        **item,
        "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "returncode": process.returncode,
    }
    try:
        response = json.loads(process.stdout)
        result.update({key: response.get(key) for key in
                       ("url_effective", "http_code", "content_type", "size_download")})
    except json.JSONDecodeError:
        result["response_metadata"] = process.stdout[:500]
    if process.returncode:
        result["error"] = process.stderr[-2000:]
        partial.unlink(missing_ok=True)
    else:
        prefix = partial.read_bytes()[:512] if partial.stat().st_size < 512 else b""
        if not prefix:
            with partial.open("rb") as stream:
                prefix = stream.read(512)
        if b"<html" in prefix.lower() or b"<!doctype html" in prefix.lower():
            result["error"] = "HTML response rejected: this is not a dataset"
            partial.unlink()
        else:
            partial.replace(destination)
            digest = hashlib.sha256()
            with destination.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1048576), b""):
                    digest.update(chunk)
            result.update(bytes=destination.stat().st_size, sha256=digest.hexdigest())
    print(json.dumps({"destination": str(destination), "ok": "error" not in result,
                      "bytes": result.get("bytes"), "error": result.get("error")},
                     ensure_ascii=False), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=pathlib.Path)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--result", type=pathlib.Path, required=True)
    arguments = parser.parse_args()
    items = json.loads(arguments.plan.read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        results = list(pool.map(download, items))
    arguments.result.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
