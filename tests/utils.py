import asyncio
from dataclasses import dataclass, field

from onyx_otc.v2.responses_pb2 import ChannelMessage, OtcResponse
from onyx_otc.websocket import OnyxWebsocketClient
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2


@dataclass
class OnResponse:
    responses: asyncio.Queue[dict] = field(default_factory=asyncio.Queue)
    events: asyncio.Queue[dict] = field(default_factory=asyncio.Queue)

    def on_response(self, cli: OnyxWebsocketClient, data: dict) -> None:
        self.responses.put_nowait(data)

    def on_event(self, cli: OnyxWebsocketClient, data: dict) -> None:
        self.events.put_nowait(data)

    async def get_response(self, timeout: float = 2.0) -> dict:
        async with asyncio.timeout(timeout):
            return await self.responses.get()

    async def get_event(self, timeout: float = 2.0) -> dict:
        async with asyncio.timeout(timeout):
            return await self.events.get()


@dataclass
class OnResponseV2:
    responses: asyncio.Queue[OtcResponse] = field(default_factory=asyncio.Queue)
    events: asyncio.Queue[ChannelMessage] = field(default_factory=asyncio.Queue)

    def on_response(self, client: OnyxWebsocketClientV2, response: OtcResponse) -> None:
        self.responses.put_nowait(response)

    def on_event(self, client: OnyxWebsocketClientV2, event: ChannelMessage) -> None:
        self.events.put_nowait(event)

    async def get_otc_response(self, timeout: float = 2.0) -> OtcResponse:
        async with asyncio.timeout(timeout):
            return await self.responses.get()

    async def get_otc_event(self, timeout: float = 2.0) -> ChannelMessage:
        async with asyncio.timeout(timeout):
            return await self.events.get()
