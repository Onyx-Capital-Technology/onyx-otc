import asyncio
from dataclasses import dataclass, field

from onyx_otc.responses import OtcChannelMessage, OtcResponse
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2


@dataclass
class OnResponseV2:
    responses: asyncio.Queue[OtcResponse] = field(default_factory=asyncio.Queue)
    events: asyncio.Queue[OtcChannelMessage] = field(default_factory=asyncio.Queue)

    def on_response(self, client: OnyxWebsocketClientV2, response: OtcResponse) -> None:
        self.responses.put_nowait(response)

    def on_event(self, client: OnyxWebsocketClientV2, event: OtcChannelMessage) -> None:
        self.events.put_nowait(event)

    async def get_otc_response(self, timeout: float = 2.0) -> OtcResponse:
        async with asyncio.timeout(timeout):
            return await self.responses.get()

    async def get_otc_event(self, timeout: float = 2.0) -> OtcChannelMessage:
        async with asyncio.timeout(timeout):
            return await self.events.get()
