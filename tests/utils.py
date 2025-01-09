import asyncio
from dataclasses import dataclass, field
from typing import Callable

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

    async def assert_otc_response(
        self, predicate: Callable[[OtcResponse], bool], timeout: float = 2.0
    ) -> None:
        async with asyncio.timeout(timeout):
            while True:
                response = await self.responses.get()
                if predicate(response):
                    return
                await self.responses.put(response)

    async def assert_otc_event(
        self, predicate: Callable[[ChannelMessage], bool], timeout: float = 2.0
    ) -> None:
        async with asyncio.timeout(timeout):
            while True:
                event = await self.events.get()
                if predicate(event):
                    return
                await self.events.put(event)


def assert_server_info_message(channel_message: ChannelMessage) -> bool:
    server_info_message = channel_message.server_info
    return server_info_message.socket_uid != "" and server_info_message.age_millis > 0
