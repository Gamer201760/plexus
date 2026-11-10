from starlette.middleware.gzip import GZipMiddleware
from starlette.types import Receive, Scope, Send


class RoadGraphCompression(GZipMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"] == "/api/v1/road-graph":
            await super().__call__(scope, receive, send)
        else:
            await self.app(scope, receive, send)
