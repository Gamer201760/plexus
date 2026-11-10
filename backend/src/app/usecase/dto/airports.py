from dataclasses import dataclass


@dataclass(frozen=True)
class Airport:
    id: str
    name: str
    municipality: str
    iata: str
    latitude: float
    longitude: float
    scheduled: bool
    kind: str


@dataclass(frozen=True)
class AirportAssignment:
    point_id: str
    airport_id: str
    distance_km: float
    method: str = "nearest_scheduled_airport_within_150km"


@dataclass(frozen=True)
class AirportCatalog:
    airports: list[Airport]
    assignments: list[AirportAssignment]
    source_url: str
    retrieved_at: str
