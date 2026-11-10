from typing import Protocol

type LogValue = str | int | float | bool | None


class Logger(Protocol):
    def info(self, event: str, **fields: LogValue) -> None: ...

    def warning(self, event: str, **fields: LogValue) -> None: ...

    def error(
        self, event: str, *, exc: BaseException | None = None, **fields: LogValue
    ) -> None: ...
