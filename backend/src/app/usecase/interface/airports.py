from typing import Protocol

from app.usecase.dto.airports import AirportCatalog


class AirportRepository(Protocol):
    def catalog(self) -> AirportCatalog: ...
