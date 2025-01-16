import asyncio
from dataclasses import dataclass, field

from onyx_otc.websocket_v1 import OnyxWebsocketClientV1


@dataclass
class OnResponseV1:
    responses: asyncio.Queue[dict] = field(default_factory=asyncio.Queue)
    events: asyncio.Queue[dict] = field(default_factory=asyncio.Queue)

    def on_response(self, cli: OnyxWebsocketClientV1, data: dict) -> None:
        self.responses.put_nowait(data)

    def on_event(self, cli: OnyxWebsocketClientV1, data: dict) -> None:
        self.events.put_nowait(data)

    async def get_response(self, timeout: float = 2.0) -> dict:
        async with asyncio.timeout(timeout):
            return await self.responses.get()

    async def get_event(self, timeout: float = 2.0) -> dict:
        async with asyncio.timeout(timeout):
            return await self.events.get()
