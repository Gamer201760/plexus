import argparse
import json
import platform
import subprocess
import time
import urllib.request
from datetime import datetime, timezone

import numpy as np

from artifacts import ROOT, revision, write_json


def benchmark(base_url: str, samples: int) -> None:
    with urllib.request.urlopen(f"{base_url}/api/v1/pilots/tuva", timeout=5) as response:
        pilot = json.load(response)
    payload = {"season": "summer", "model_version": pilot["model_version"],
               "artifact_version": pilot["artifact_version"],
               "changes": [{"edge_id": "manual:0", "frequency_per_week": 7}]}
    durations = []
    for index in range(samples + 1):
        request = urllib.request.Request(f"{base_url}/api/v1/pilots/tuva/evaluate",
                                        json.dumps(payload).encode(), {"Content-Type": "application/json"})
        start = time.perf_counter()
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.load(response)
            assert result["artifact_version"] == pilot["artifact_version"]
        if index:
            durations.append(time.perf_counter() - start)
    cpu = platform.processor()
    if platform.system() == "Darwin":
        cpu = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    report = {"measured_at": datetime.now(timezone.utc).isoformat(), "code": revision(),
              "method": "sequential loopback HTTP requests after one warmup evaluation",
              "base_url": base_url, "samples": samples, "p95_s": float(np.percentile(durations, 95)),
              "platform": platform.platform(), "cpu": cpu, "artifact_version": pilot["artifact_version"],
              "threshold_s": 2., "passed": float(np.percentile(durations, 95)) <= 2.,
              "limitations": "local Compose server; no remote network latency or concurrency claim"}
    write_json(ROOT / "docs/results/pilot-http-benchmark.json", report)
    print(f"HTTP p95={report['p95_s']:.6f}s, samples={samples}, cpu={cpu}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--samples", type=int, default=200)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("samples must be positive")
    benchmark(args.base_url.rstrip("/"), args.samples)
