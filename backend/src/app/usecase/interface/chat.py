from collections.abc import AsyncGenerator
from typing import Protocol

from app.usecase.dto.chat import ChatEvent, ChatRequest


class ChatProvider(Protocol):
    def stream(self, request: ChatRequest) -> AsyncGenerator[ChatEvent, None]: ...
