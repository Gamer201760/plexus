import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path


INACTIVE = re.compile(
    r"временно не обслуж|движение приостанов|не осуществляется|не обслуживается|"
    r"нет перевозчика|перевозчик будет определен|маршрут отмен",
    re.IGNORECASE,
)
PREFIX = "regional-transport-"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)


def refresh(source, project):
    collection = source / "datasets/additional/regional-transport"
    public = project / "frontend/atlas/public"
    atlas = json.loads((public / "atlas.json").read_text())
    atlas["links"] = [row for row in atlas["links"] if not row["id"].startswith(PREFIX)]
    known = {}
    for path in sorted((source / "data_manual/regions_input").glob("*.csv")):
        for row in rows(path):
            known[row["point_id"]] = {
                "id": row["point_id"], "name": row["name"], "region": path.stem,
                "lat": float(row["lat"]), "lon": float(row["lon"]),
            }
    points = {row["id"]: row for row in atlas["points"]}
    regions = {row["id"] for row in atlas["regions"]}
    existing = {(r["region"], r["mode"], r["from_id"], r["to_id"]) for r in atlas["links"]}
    seen = set()
    stats = Counter()
    for folder in sorted(collection.iterdir()):
        if not folder.is_dir() or folder.name not in regions:
            continue
        for kind in ("bus_routes", "links_add"):
            for row in rows(folder / (kind + ".csv")):
                stats["input_" + kind] += 1
                if not row.get("source_url"):
                    stats["excluded_no_source"] += 1
                    continue
                if row["from_id"] not in known or row["to_id"] not in known:
                    stats["excluded_unmatched"] += 1
                    continue
                note = row.get("schedule_note", row.get("freq_note", ""))
                if INACTIVE.search(note):
                    stats["excluded_inactive"] += 1
                    continue
                mode = "bus" if kind == "bus_routes" else row["mode"]
                pair = (folder.name, mode, row["from_id"], row["to_id"])
                if kind == "links_add" and pair in existing:
                    stats["excluded_existing_link"] += 1
                    continue
                existing.add(pair)
                fingerprint = json.dumps([folder.name, kind, row], sort_keys=True)
                key = hashlib.sha256(fingerprint.encode()).hexdigest()[:20]
                if key in seen:
                    stats["excluded_duplicate"] += 1
                    continue
                seen.add(key)
                for point_id in (row["from_id"], row["to_id"]):
                    points.setdefault(point_id, known[point_id])
                context = "Каталог источников: выполнение рейса не проверено; индекс Hansen не пересчитан."
                if kind == "bus_routes":
                    context += " Реестр " + row.get("registry_no", "") + ". " + row.get("route_name", "")
                atlas["links"].append({
                    "id": PREFIX + key, "region": folder.name, "mode": mode,
                    "from_id": row["from_id"], "to_id": row["to_id"],
                    "from_name": row["from_name"], "to_name": row["to_name"],
                    "km": row.get("km", ""), "season": row.get("season", ""),
                    "freq_per_week": row.get("trips_per_week", row.get("freq_per_week", "")),
                    "freq_note": context + " " + note,
                    "vehicle": "Автобус" if kind == "bus_routes" else row.get("vehicle", ""),
                    "confidence": row.get("confidence", ""),
                    "source_url": row["source_url"], "source_date": row.get("source_date", ""),
                })
                stats["added_" + kind] += 1
    atlas["points"] = list(points.values())
    counts = Counter(row["region"] for row in atlas["links"])
    for region in atlas["regions"]:
        region["links"] = counts[region["id"]]
    atlas["totals"]["links"] = len(atlas["links"])
    downloads = project / "frontend/public/datasets"
    downloads.mkdir(parents=True, exist_ok=True)
    archive_path = downloads / "regional-transport.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in sorted(collection.iterdir()):
            if not folder.is_dir():
                continue
            for name in ("README.md", "bus_routes.csv", "links_add.csv", "freq_fill.csv"):
                path = folder / name
                if path.exists():
                    archive.write(path, folder.name + "/" + name)
        archive.writestr("IMPORT.json", json.dumps(dict(stats), ensure_ascii=False, indent=2))
        archive.writestr("README.txt",
            "Каталог найденных маршрутов, не подтверждение выполнения рейсов. "
            "Покрытие регионов неодинаково. В атлас включены строки с двумя привязанными "
            "пунктами без явной отметки остановки движения. Частоты из freq_fill не применены: "
            "нужна сверка периода и направления. Индекс Hansen не пересчитан. "
            "Неоднозначные кандидаты из raw в архив не включены.")
    additional = json.loads((public / "additional.json").read_text())
    additional["sources"] = [s for s in additional["sources"] if s["id"] != "regional-transport"]
    additional["sources"].append({
        "id": "regional-transport", "title": "Региональные маршруты: сбор по 82 регионам",
        "period": "Срез сбора 09.11.2026; даты документов указаны в CSV",
        "rows": stats["input_bus_routes"] + stats["input_links_add"],
        "url": "/datasets/regional-transport.zip",
        "note": "Автобусы, авиация и сезонные связи. Покрытие неодинаково; часть расписаний "
        "историческая. Архив включает несопоставленные строки. Индекс Hansen не пересчитан. "
        "Источники и ограничения — в README каждого региона.",
    })
    write(public / "atlas.json", atlas)
    write(public / "additional.json", additional)
    write(public / "regional-transport-import.json", dict(stats))
    print(json.dumps(dict(stats)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    refresh(args.source, args.project)
