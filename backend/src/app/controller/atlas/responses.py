from typing import Any

from app.controller.errors import ErrorResponse

type Responses = dict[int | str, dict[str, Any]]

UNAVAILABLE: Responses = {503: {"model": ErrorResponse}}
INVALID: Responses = {422: {"model": ErrorResponse}, **UNAVAILABLE}
NOT_FOUND: Responses = {404: {"model": ErrorResponse}, **INVALID}
