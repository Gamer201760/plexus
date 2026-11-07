"""Скачать OSM-выгрузки Geofabrik по России в data/raw/osm_russia/.

Уже скачанные файлы пропускаются. Докачки (-C -) нет: «latest» меняет версию ежедневно,
докачка склеила бы две разные версии в битый файл. Обновить — удалить файл и запустить снова.

Крымский ФО и Калининград у Geofabrik — отдельные файлы, в федеральные округа не входят.
Дубли way на стыках выгрузок убираются в etl/graph_russia.py.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DST = ROOT / "data" / "raw" / "osm_russia"
BASE = "https://download.geofabrik.de/russia"
EXTRACTS = [
    "central-fed-district", "northwestern-fed-district", "volga-fed-district", "south-fed-district",
    "north-caucasus-fed-district", "ural-fed-district", "siberian-fed-district", "far-eastern-fed-district",
    "crimean-fed-district", "kaliningrad",
]

if __name__ == "__main__":
    DST.mkdir(parents=True, exist_ok=True)
    for name in EXTRACTS:
        short = name.replace("-fed-district", "")
        out = DST / f"{short}.osm.pbf"
        if out.exists() and out.stat().st_size > 0:
            print(f"skip {short}", flush=True)
            continue
        tmp = out.with_suffix(".part")
        subprocess.run(["curl", "-sfL", "--retry", "5", "-A", "casechamp-a2/0.1",
                        "-o", str(tmp), f"{BASE}/{name}-latest.osm.pbf"], check=True)
        tmp.rename(out)
        print(f"{short}: {out.stat().st_size / 1e6:.0f} MB", flush=True)
