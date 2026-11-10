from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.usecase.dto.airports import Airport, AirportCatalog


class ClickHouseAirportRepository:
    def __init__(self, atlas: ClickHouseAtlasRepository) -> None:
        self.atlas = atlas

    def catalog(self) -> AirportCatalog:
        return AirportCatalog(
            self.atlas.load("atlas_airports", Airport),
            [],
            self.atlas.metadata["airport_url"],
            self.atlas.metadata["airport_date"],
        )
