from functools import cached_property

from app.domain.transport import Mode
from app.usecase.airport_matching import airport_distance, place_key
from app.usecase.dto.airports import AirportAssignment, AirportCatalog
from app.usecase.interface.airports import AirportRepository
from app.usecase.interface.atlas import AtlasRepository


class AirportQueries:
    def __init__(self, repository: AirportRepository, atlas: AtlasRepository) -> None:
        self.repository = repository
        self.atlas = atlas

    @cached_property
    def result(self) -> AirportCatalog:
        catalog = self.repository.catalog()
        eligible = [airport for airport in catalog.airports if airport.scheduled]
        point_ids = {
            point_id for link in self.atlas.links() if link.mode is Mode.AIR
            for point_id in (link.from_id, link.to_id)
        }
        model_ids = {point_id for link in self.atlas.links() if link.mode is Mode.AIR and link.is_model
                     for point_id in (link.from_id, link.to_id)}
        assignments = []
        for point in self.atlas.points().values():
            if point.id not in point_ids or not eligible:
                continue
            named = [a for a in eligible if place_key(a.municipality) == place_key(point.name)]
            if len(named) == 1:
                airport = named[0]
                distance = airport_distance(point, airport.latitude, airport.longitude)
                if distance <= 100:
                    assignments.append(AirportAssignment(point.id, airport.id, distance,
                                                         "unique_municipality_within_100km"))
                    continue
            if point.id not in model_ids:
                continue
            distance, airport_id = min(
                (airport_distance(point, a.latitude, a.longitude), a.id) for a in eligible
            )
            if distance <= 150:
                assignments.append(AirportAssignment(point.id, airport_id, distance))
        return AirportCatalog(catalog.airports, assignments, catalog.source_url, catalog.retrieved_at)
