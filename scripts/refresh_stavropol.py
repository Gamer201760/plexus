import argparse
import csv
import json
import shutil
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def refresh(source, project):
    derived = source / "data/additional/stavropol/derived"
    public = project / "frontend/atlas/public"
    downloads = project / "frontend/public/datasets"
    downloads.mkdir(parents=True, exist_ok=True)
    atlas = json.loads((public / "atlas.json").read_text())
    atlas["links"] = [row for row in atlas["links"] if not row["id"].startswith("stavropol-bus-")]
    schedules = defaultdict(list)
    for row in rows(derived / "interregional_bus_schedules.csv"):
        if row["direction"] == "forward":
            schedules[row["route_registry_id"]].append(row)
    for route in rows(derived / "interregional_bus_routes.csv"):
        stops = schedules[route["A"]]
        if not stops:
            raise ValueError(f"Missing forward schedule: {route['A']}")
        first, last = stops[0], stops[-1]
        full_year = all(stop["winter_period"].strip().lower() == "круглогодично" for stop in stops)
        atlas["links"].append({
            "id": "stavropol-bus-" + route["A"], "region": "07000000", "mode": "bus",
            "from_id": "ext:bus:" + (first["stop_registry_id"] or route["A"] + ":start"),
            "to_id": "ext:bus:" + (last["stop_registry_id"] or route["A"] + ":end"),
            "from_name": first["stop_name"], "to_name": last["stop_name"],
            "km": route["I"].replace(",", "."), "season": "all" if full_year else "",
            "freq_per_week": "", "vehicle": "Автобус", "confidence": "high",
            "freq_note": "Реестр " + route["A"] + ". " + route["C"] + ". "
            + "Зимнее/круглогодичное отправление: " + first["winter_departure_days"] + " "
            + first["winter_departure_time"] + "; период: " + first["winter_period"] + ". "
            + "Летнее отправление: " + first["summer_departure_days"] + " "
            + first["summer_departure_time"] + "; период: " + first["summer_period"] + ". "
            + "Полное расписание обоих направлений доступно в источниках. "
            + "Координаты остановок не установлены; выполнение рейсов не проверено.",
            "source_url": "https://mintrans.gov.ru/documents/8/16070", "source_date": "2026-10-20",
        })
    for region in atlas["regions"]:
        region["links"] = sum(link["region"] == region["id"] for link in atlas["links"])
    atlas["totals"]["links"] = len(atlas["links"])
    write(public / "atlas.json", atlas)
    latest = source / "frontend/atlas/public"
    additional = json.loads((latest / "additional.json").read_text())
    shutil.copy2(latest / "additional/regions/07000000.json", public / "additional/regions/07000000.json")
    definitions = [
        ("osm", "Ставропольский край: сеть и объекты OSM", "2026-11-07", 95306,
         ["network_ways.parquet", "osm_places.parquet", "osm_relations.parquet", "boundary.geojson"],
         "95 306 линий, 4 732 объекта. Geofabrik / OpenStreetMap, ODbL. Граф и время проезда не рассчитаны. https://download.geofabrik.de/russia/north-caucasus-fed-district.html"),
        ("bus", "Ставропольский край: межрегиональные автобусы", "2026-10-20", 653,
         ["interregional_bus_routes.csv", "interregional_bus_schedules.csv", "interregional_bus_vehicles.csv"],
         "653 маршрута, 7 124 строки расписаний обоих направлений. Отбор по остановкам в крае. Минтранс: https://mintrans.gov.ru/documents/8/16070"),
        ("medical", "Ставропольский край: реестр ОМС", "2026", 161,
         ["medical_organizations_2026.csv", "medical_care_rows_2026.csv", "medical_organizations_2025.csv", "medical_care_rows_2025.csv"],
         "161 организация, 1 165 строк помощи за 2026 год. Есть исключённые организации; адреса помощи не геокодированы. https://tfomssk.ru/reestry-oms/reestr-mo/"),
        ("roads", "Ставропольский край: архив дорожных справок", "2017", 33,
         ["road_archive_tables.csv", *[p.name for p in sorted(derived.glob("road-archive-*.txt"))]],
         "33 документа, публикация 14.07.2017. Исторические периоды и единицы не нормализованы. https://dorogisk.ru/dorozhnoe-khozyaystvo/avtomobilnye-dorogi-sk/"),
    ]
    additional["sources"] = [s for s in additional["sources"] if not s["id"].startswith("stavropol-")]
    for key, title, period, count, filenames, note in definitions:
        filename = f"stavropol-{key}.zip"
        with zipfile.ZipFile(downloads / filename, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in filenames:
                archive.write(derived / name, name)
            catalog = source / "datasets/additional/stavropol"
            for name in ["README.md", "validation.json", "registry-profile.json", "osm-profile.json", "bus-schema.json", "medical-schema-2026.json"]:
                archive.write(catalog / name, "metadata/" + name)
        additional["sources"].append({"id": "stavropol-" + key, "title": title,
            "period": period, "rows": count, "url": "/datasets/" + filename, "note": note})
    additional["updated_at"] = datetime.now(timezone.utc).isoformat()
    write(public / "additional.json", additional)
    print(json.dumps({"bus_routes": len(schedules), "links": len(atlas["links"]), "archives": len(definitions)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    refresh(args.source, args.project)
