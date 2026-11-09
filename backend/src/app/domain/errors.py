class DomainError(Exception):
    code = "domain_error"
    message = "Request failed"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class RegionNotFound(DomainError):
    code = "region_not_found"
    message = "Region not found"


class LinkNotFound(DomainError):
    code = "link_not_found"
    message = "Link not found"


class InvalidQuery(DomainError):
    code = "validation_error"
    message = "Query is invalid"


class DataUnavailable(DomainError):
    code = "data_unavailable"
    message = "Atlas data is unavailable"
