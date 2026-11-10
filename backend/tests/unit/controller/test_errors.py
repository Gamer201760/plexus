from dataclasses import dataclass, field

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.controller.errors import ErrorHandlers
from app.domain.errors import DataUnavailable, DomainError, InvalidQuery, RegionNotFound
from app.usecase.interface.log import LogValue


@dataclass
class RecordingLogger:
    records: list[tuple[str, str, BaseException | None, dict[str, LogValue]]] = field(
        default_factory=list
    )

    def info(self, event: str, **fields: LogValue) -> None:
        self.records.append(("info", event, None, fields))

    def warning(self, event: str, **fields: LogValue) -> None:
        self.records.append(("warning", event, None, fields))

    def error(self, event: str, *, exc: BaseException | None = None, **fields: LogValue) -> None:
        self.records.append(("error", event, exc, fields))


class Payload(BaseModel):
    count: int


def build_client(error: Exception, logger: RecordingLogger | None = None) -> TestClient:
    app = FastAPI()
    ErrorHandlers(logger or RecordingLogger()).register(app)

    @app.get("/fail")
    async def fail() -> None:
        raise error

    @app.post("/echo")
    async def echo(payload: Payload) -> Payload:
        return payload

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("error", "status", "body"),
    [
        (
            InvalidQuery("Query needs at least 2 characters"),
            422,
            {"code": "validation_error", "message": "Query needs at least 2 characters"},
        ),
        (RegionNotFound(), 404, {"code": "region_not_found", "message": "Region not found"}),
        (
            DataUnavailable("DATA_DIR=/secret/path has no atlas.json"),
            503,
            {"code": "data_unavailable", "message": "Atlas data is unavailable"},
        ),
        (DomainError("unmapped"), 500, {"code": "internal_error", "message": "Internal error"}),
        (RuntimeError("boom"), 500, {"code": "internal_error", "message": "Internal error"}),
    ],
)
def test_failures_use_error_envelope(error: Exception, status: int, body: dict[str, str]) -> None:
    response = build_client(error).get("/fail")

    assert response.status_code == status
    assert response.json() == body


def test_validation_error_names_fields() -> None:
    response = build_client(RuntimeError()).post("/echo", json={"count": "many"})

    assert response.status_code == 422
    assert response.json() == {
        "code": "validation_error",
        "message": "Invalid request: body.count",
    }


def test_unknown_route_uses_error_envelope() -> None:
    response = build_client(RuntimeError()).get("/missing")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "Not Found"}


@pytest.mark.parametrize(
    ("error", "level", "event"),
    [
        (DataUnavailable("missing file"), "warning", "domain_failure"),
        (DomainError("unmapped"), "error", "unmapped_domain_error"),
        (RuntimeError("boom"), "error", "unexpected_error"),
    ],
)
def test_server_failures_are_logged_through_port(error: Exception, level: str, event: str) -> None:
    logger = RecordingLogger()

    build_client(error, logger).get("/fail")

    [(logged_level, logged_event, _, fields)] = logger.records
    assert (logged_level, logged_event, fields["path"]) == (level, event, "/fail")


def test_unexpected_error_passes_exception_to_logger() -> None:
    error = RuntimeError("boom")
    logger = RecordingLogger()

    build_client(error, logger).get("/fail")

    assert logger.records[0][2] is error


def test_client_errors_are_not_logged() -> None:
    logger = RecordingLogger()

    build_client(InvalidQuery("bad"), logger).get("/fail")

    assert logger.records == []
