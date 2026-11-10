from pydantic_ai import ModelRetry

from app.adapter.log.stdlib import StdlibLogger
from app.domain.errors import DomainError
from app.usecase.dto.chat import ChatEvent


def chat_failure(error: BaseException, code: str, stage: str) -> ChatEvent:
    reason = ""
    cause: BaseException | None = error
    seen: set[int] = set()
    while cause is not None and id(cause) not in seen:
        seen.add(id(cause))
        if isinstance(cause, (DomainError, ModelRetry)):
            reason = str(cause)[:500]
        cause = cause.__cause__
    status = getattr(error, "status_code", None)
    StdlibLogger("chat").error(
        "chat_request_failed",
        code=code,
        stage=stage,
        error_type=type(error).__name__,
        reason=reason,
        status_code=status if isinstance(status, int) else None,
    )
    return ChatEvent("error", code=code)
