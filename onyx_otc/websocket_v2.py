from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, TypeAlias

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType
from google.protobuf.timestamp_pb2 import Timestamp

from .v2.common_pb2 import Decimal, TradableSymbol
from .v2.requests_pb2 import (
    Auth,
    OrdersChannel,
    OtcRequest,
    RfqChannel,
    ServerInfoChannel,
    Subscribe,
    TickersChannel,
    Unsubscribe,
)
from .v2.responses_pb2 import ChannelMessage, OtcResponse
from .v2.types_pb2 import Exchange, Method

logger = logging.getLogger(__name__)

ResponseHandler: TypeAlias = Callable[["OnyxWebsocketClientV2", OtcResponse], None]
EventHandler: TypeAlias = Callable[["OnyxWebsocketClientV2", ChannelMessage], None]
ExitHandler: TypeAlias = Callable[["OnyxWebsocketClientV2"], None]


# Default handlers
def on_response(cli: OnyxWebsocketClientV2, response: OtcResponse) -> None:
    logger.info("Received response: %s", response)


def on_event(cli: OnyxWebsocketClientV2, message: ChannelMessage) -> None:
    logger.info("Received event: %s", message)


def on_exit(cli: OnyxWebsocketClientV2) -> None:
    logger.info("Connection closed")


@dataclass
class OnyxWebsocketClientV2:
    """
    WebSocket client for the Onyx OTC API v2.
    This clients connects to the API v2 binary WebSocket endpoint

    Attributes:
        api_token: API authentication token
        ws_url: WebSocket endpoint URL
        on_response: Callback for handling responses
        on_event: Callback for handling channel events
        on_exit: Callback for handling connection closure
    """

    api_token: str = field(default_factory=lambda: os.environ.get("ONYX_API_TOKEN", ""))
    ws_url: str = field(
        default_factory=lambda: os.environ.get(
            "ONYX_WS_V2_URL", "wss://ws.onyxhub.co/stream/v2/binary"
        )
    )

    on_response: ResponseHandler = field(default=on_response)
    on_event: EventHandler = field(default=on_event)
    on_exit: ExitHandler = field(default=on_exit)

    _queue: asyncio.Queue[OtcRequest] = field(default_factory=asyncio.Queue)
    _ws: ClientWebSocketResponse | None = field(default=None, init=False)
    _write_task: asyncio.Task | None = field(default=None, init=False)
    _is_running: bool = field(default=False, init=False)
    _reconnect_delay: float = field(default=1.0, init=False)
    _max_reconnect_delay: float = field(default=60.0, init=False)

    def _create_request(self, method: Method.ValueType, **kwargs: Any) -> OtcRequest:
        """Create a new request with the current timestamp."""
        timestamp = Timestamp()
        timestamp.FromDatetime(datetime.now(UTC))
        return OtcRequest(method=method, timestamp=timestamp, **kwargs)

    async def _handle_binary_message(self, data: bytes) -> None:
        """Handle incoming binary messages."""
        if response := self.parse_response(data):
            self.on_response(self, response)
        elif message := self.parse_channel_message(data):
            self.on_event(self, message)
        else:
            logger.warning("Unknown message type received")

    def parse_response(self, data: bytes) -> OtcResponse | None:
        """Parse binary data as OtcResponse."""
        try:
            response = OtcResponse.FromString(data)

            if (
                response.HasField("error")
                or response.HasField("auth")
                or response.HasField("subscription")
                or response.HasField("order")
            ):
                return response
            return None
        except Exception:
            logger.debug("Failed to parse as OtcResponse", exc_info=True)
            return None

    def parse_channel_message(self, data: bytes) -> ChannelMessage | None:
        """Parse binary data as ChannelMessage."""
        try:
            message = ChannelMessage.FromString(data)
            return message
        except Exception:
            logger.error("Failed to parse as ChannelMessage", exc_info=True)
            raise

    def subscribe_server_info(self) -> None:
        """Subscribe to server info channel."""
        self.send(
            self._create_request(
                method=Method.METHOD_SUBSCRIBE,
                subscribe=Subscribe(server_info=ServerInfoChannel()),
            )
        )

    def unsubscribe_server_info(self) -> None:
        """Unsubscribe from server info channel."""
        self.send(
            self._create_request(
                method=Method.METHOD_UNSUBSCRIBE,
                unsubscribe=Unsubscribe(server_info=ServerInfoChannel()),
            )
        )

    def subscribe_tickers(self, products: list[str]) -> None:
        """Subscribe to ticker updates for specific products."""
        self.send(
            self._create_request(
                method=Method.METHOD_SUBSCRIBE,
                subscribe=Subscribe(tickers=TickersChannel(products=products)),
            )
        )

    def unsubscribe_tickers(self, products: list[str]) -> None:
        """Unsubscribe from ticker updates for specific products."""
        self.send(
            self._create_request(
                method=Method.METHOD_UNSUBSCRIBE,
                unsubscribe=Unsubscribe(tickers=TickersChannel(products=products)),
            )
        )

    def subscribe_orders(self) -> None:
        """Subscribe to order updates."""
        self.send(
            self._create_request(
                method=Method.METHOD_SUBSCRIBE,
                subscribe=Subscribe(orders=OrdersChannel()),
            )
        )

    def unsubscribe_orders(self) -> None:
        """Unsubscribe from order updates."""
        self.send(
            self._create_request(
                method=Method.METHOD_UNSUBSCRIBE,
                unsubscribe=Unsubscribe(orders=OrdersChannel()),
            )
        )

    def subscribe_rfq(
        self, symbol: TradableSymbol, size: Decimal, exchange: Exchange.ValueType
    ) -> None:
        """Subscribe to RFQ updates."""
        self.send(
            self._create_request(
                method=Method.METHOD_SUBSCRIBE,
                subscribe=Subscribe(
                    rfq_channel=RfqChannel(symbol=symbol, size=size, exchange=exchange)
                ),
            )
        )

    def send(self, msg: OtcRequest) -> None:
        """Queue a message for sending."""
        if not self._is_running:
            logger.warning("Client not running, message dropped: %s", msg)
            return
        self._queue.put_nowait(msg)

    async def connect(self) -> None:
        """Connect to the websocket server with automatic reconnection."""
        while True:
            try:
                await self._connect_and_run()
            except Exception as e:
                logger.error("Connection error: %s", e, exc_info=True)
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self._max_reconnect_delay
                )
            finally:
                self._ws = None
                if self._write_task:
                    self._write_task.cancel()
                    self._write_task = None

    async def _connect_and_run(self) -> None:
        """Establish connection and start message loops."""
        async with ClientSession() as session:
            logger.info("Connecting to %s", self.ws_url)
            async with session.ws_connect(self.ws_url) as ws:
                self._ws = ws
                self._is_running = True
                logger.info("Connected to websocket")

                # Start write loop
                self._write_task = asyncio.create_task(self._write_loop())

                # Authenticate
                if auth_msg := self._create_auth_request():
                    self.send(auth_msg)

                # Handle incoming messages
                try:
                    async for msg in ws:
                        if msg.type == WSMsgType.BINARY:
                            await self._handle_binary_message(msg.data)
                        elif msg.type in (
                            WSMsgType.CLOSED,
                            WSMsgType.CLOSE,
                            WSMsgType.ERROR,
                        ):
                            logger.info("WebSocket closed: %s", msg.type)
                            break
                finally:
                    self._is_running = False
                    self.on_exit(self)

    def _create_auth_request(self) -> OtcRequest | None:
        """Create authentication request if token is available."""
        if self.api_token:
            return self._create_request(
                method=Method.METHOD_AUTH, auth=Auth(token=self.api_token)
            )
        return None

    async def _write_loop(self) -> None:
        """Handle outgoing messages."""
        while True:
            try:
                msg = await self._queue.get()
                if self._ws and not self._ws.closed:
                    logger.debug("Sending message: %s", msg)
                    await self._ws.send_bytes(msg.SerializeToString())
                else:
                    logger.warning("WebSocket closed, message dropped: %s", msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error sending message: %s", e, exc_info=True)

    async def close(self) -> None:
        """Gracefully close the connection."""
        self._is_running = False
        if self._ws:
            await self._ws.close()
        if self._write_task:
            self._write_task.cancel()
            try:
                await self._write_task
            except asyncio.CancelledError:
                pass
