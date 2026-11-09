import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from download_osm import DST, EXTRACTS


def main(download_pid: int) -> None:
    remaining = {name.replace("-fed-district", "") for name in EXTRACTS}
    while remaining:
        for name in sorted(remaining.copy()):
            source = DST / f"{name}.osm.pbf"
            if source.exists():
                subprocess.run([sys.executable, str(Path(__file__).with_name("osm_extract.py")),
                                str(source)], check=True)
                remaining.remove(name)
        if not remaining:
            break
        try:
            os.kill(download_pid, 0)
        except ProcessLookupError as error:
            raise FileNotFoundError("download stopped; missing PBF: " + ", ".join(sorted(remaining))) from error
        time.sleep(10)
    print("all national extracts ready", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-pid", required=True, type=int)
    main(parser.parse_args().download_pid)
