from pathlib import Path

from app.domain.errors import DataUnavailable
from app.repository.files.json_values import number, obj, objects, read_json, text
from app.usecase.airports import Airport, AirportCatalog


class FileAirportRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def catalog(self) -> AirportCatalog:
        document = obj(read_json(self.data_dir, "airports.json"))
        airports = []
        for row in objects(document.get("airports")):
            lat, lon = number(row, "latitude"), number(row, "longitude")
            if lat is None or lon is None or not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise DataUnavailable("Airport coordinates are invalid")
            airports.append(Airport(
                text(row, "id") or "", text(row, "name") or "", text(row, "municipality") or "",
                text(row, "iata") or "", lat, lon, row.get("scheduled") is True,
                text(row, "kind") or "",
            ))
        if not airports:
            raise DataUnavailable("Airport catalog is empty")
        return AirportCatalog(airports, [], text(document, "source_url") or "",
                              text(document, "retrieved_at") or "")
