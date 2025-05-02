from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Self, TypeAlias

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType

from .requests import (
    AuthRequest,
    OrderBookTopChannel,
    OrdersChannel,
    OtcOrderRequest,
    OtcRequest,
    RfqChannel,
    ServerInfoChannel,
    SubscribeRequest,
    TickersChannel,
    UnsubscribeRequest,
)
from .responses import OtcChannelMessage, OtcResponse, otc_response_from_proto_bytes
from .timestamp import Timestamp

logger = logging.getLogger(__name__)

ResponseHandler: TypeAlias = Callable[["OnyxWebsocketClientV2", OtcResponse], None]
EventHandler: TypeAlias = Callable[["OnyxWebsocketClientV2", OtcChannelMessage], None]
ExitHandler: TypeAlias = Callable[["OnyxWebsocketClientV2"], None]


# Default handlers
def on_response(cli: OnyxWebsocketClientV2, response: OtcResponse) -> None:
    logger.info("Received response: %s", response)


def on_event(cli: OnyxWebsocketClientV2, message: OtcChannelMessage) -> None:
    logger.info("Received event: %s", message)


def on_exit(cli: OnyxWebsocketClientV2) -> None:
    logger.info("Connection closed")


@dataclass
class OnyxWebsocketClientV2:
    """
    WebSocket client for the Onyx OTC API v2.

    This clients connects to either the JSON or the binary (protobuf) endpoint

    Attributes:
        ws_url: WebSocket endpoint URL
        api_token: API authentication token
        on_response: Callback for handling responses
        on_event: Callback for handling channel events
        on_exit: Callback for handling connection closure
    """

    ws_url: str
    api_token: str = field(default_factory=lambda: os.environ.get("ONYX_API_TOKEN", ""))
    on_response: ResponseHandler = field(default=on_response)
    on_event: EventHandler = field(default=on_event)
    on_exit: ExitHandler = field(default=on_exit)
    min_reconnect_delay: float = field(default=1.0, init=False)
    max_reconnect_delay: float = field(default=60.0, init=False)

    _queue: asyncio.Queue[bytes | str] = field(
        default_factory=asyncio.Queue, repr=False
    )
    _ws: ClientWebSocketResponse | None = field(default=None, init=False)
    _write_task: asyncio.Task | None = field(default=None, init=False)
    _is_running: bool = field(default=False, init=False)
    _reconnect_delay: float = 0.0
    _id_counter: int = 0

    @classmethod
    def create(
        cls,
        *,
        binary: bool = True,
        ws_url: str | None = None,
        **kwargs: Any,
    ) -> Self:
        """Create a client instance."""
        ws_url_ = (
            ws_url
            or os.environ.get("ONYX_WS_V2_URL")
            or "wss://ws.onyxhub.co/stream/v2/binary"
        )
        if ws_url_.endswith("/binary"):
            if not binary:
                ws_url_ = ws_url_.replace("/binary", "")
        elif binary:
            ws_url_ = f"{ws_url_}/binary"
        params = {key: value for key, value in kwargs.items() if value is not None}
        return cls(ws_url=ws_url_, **params)

    @property
    def is_binary(self) -> bool:
        """Check if the client is using binary protocol."""
        return self.ws_url.endswith("/binary")

    @property
    def is_running(self) -> bool:
        """Check if the client is currently running."""
        return self._is_running

    def authenticate(self) -> None:
        """Authenticate the client."""
        if self.api_token:
            self.send(self.request(AuthRequest(token=self.api_token)))
        else:
            logger.warning("No API token provided, authentication skipped")

    def subscribe_server_info(self) -> None:
        """Subscribe to server info channel."""
        self.send(self.request(SubscribeRequest(data=ServerInfoChannel())))

    def unsubscribe_server_info(self) -> None:
        """Unsubscribe from server info channel."""
        self.send(self.request(UnsubscribeRequest(data=ServerInfoChannel())))

    def subscribe_tickers(self, products: list[str]) -> None:
        """Subscribe to ticker updates for specific products."""
        self.send(
            self.request(SubscribeRequest(data=TickersChannel(products=products)))
        )

    def unsubscribe_tickers(self, products: list[str]) -> None:
        """Unsubscribe from ticker updates for specific products."""
        self.send(
            self.request(UnsubscribeRequest(data=TickersChannel(products=products)))
        )

    def subscribe_obt(self, products: list[str]) -> None:
        """Subscribe to order-book-top updates for specific products."""
        self.send(
            self.request(SubscribeRequest(data=OrderBookTopChannel(products=products)))
        )

    def unsubscribe_obt(self, products: list[str]) -> None:
        """Unsubscribe from order-book-top updates for specific products."""
        self.send(
            self.request(
                UnsubscribeRequest(data=OrderBookTopChannel(products=products))
            )
        )

    def subscribe_orders(self) -> None:
        """Subscribe to order updates."""
        self.send(self.request(SubscribeRequest(data=OrdersChannel())))

    def unsubscribe_orders(self) -> None:
        """Unsubscribe from order updates."""
        self.send(self.request(UnsubscribeRequest(data=OrdersChannel())))

    def subscribe_rfq(self, rfq: RfqChannel) -> None:
        """Subscribe to RFQ updates."""
        self.send(self.request(SubscribeRequest(data=rfq)))

    def unsubscribe_rfq(self, rfq: RfqChannel) -> None:
        """Unsubscribe from RFQ updates."""
        self.send(self.request(UnsubscribeRequest(data=rfq)))

    async def handle_binary_message(self, data: bytes) -> None:
        """Handle incoming binary messages."""
        response = otc_response_from_proto_bytes(data)
        if isinstance(response, OtcResponse):
            self.on_response(self, response)
        elif isinstance(response, OtcChannelMessage):
            self.on_event(self, response)

    async def handle_text_message(self, data: str) -> None:
        """Handle incoming text messages."""
        payload = json.loads(data)
        if response := OtcResponse.from_json(payload):
            self.on_response(self, response)
        elif message := OtcChannelMessage.from_json(payload):
            self.on_event(self, message)
        else:
            logger.warning("Unknown JSON message type received")

    def send(self, msg: OtcRequest) -> None:
        """Queue a message for sending."""
        if not self._is_running:
            logger.warning("Client not running, message dropped: %s", msg)
            return
        if self.is_binary:
            self._queue.put_nowait(msg.to_proto().SerializeToString())
        else:
            self._queue.put_nowait(json.dumps(msg.to_json_dict()))

    def new_id(self) -> str:
        """Generate a new unique ID for requests."""
        self._id_counter += 1
        return f"wscli:{self._id_counter}"

    def request(
        self,
        request: AuthRequest | OtcOrderRequest | SubscribeRequest | UnsubscribeRequest,
    ) -> OtcRequest:
        """Create a new request with the current timestamp."""
        otc_request = OtcRequest(
            id=self.new_id(),
            timestamp=Timestamp.utcnow(),
            request=request,
        )
        logger.debug("Request created: %s", otc_request)
        return otc_request

    async def connect(self) -> None:
        """Connect to the websocket server with automatic reconnection."""
        self._reconnect_delay = self.min_reconnect_delay
        while True:
            try:
                await self._connect_and_run()
            except Exception as e:
                logger.error("Connection error: %s", e, exc_info=True)
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self.max_reconnect_delay
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
                logger.info("Connected to %s", self.ws_url)
                self._reconnect_delay = self.min_reconnect_delay
                # Start write loop
                self._write_task = asyncio.create_task(self._write_loop())
                # Authenticate
                self.authenticate()
                # Handle incoming messages
                try:
                    async for msg in ws:
                        if msg.type == WSMsgType.BINARY:
                            await self.handle_binary_message(msg.data)
                        elif msg.type == WSMsgType.TEXT:
                            await self.handle_text_message(msg.data)
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

    async def _write_loop(self) -> None:
        """Handle outgoing messages."""
        while True:
            try:
                msg = await self._queue.get()
                if self._ws and not self._ws.closed:
                    if isinstance(msg, str):
                        logger.debug("Sending message string: %s", msg)
                        await self._ws.send_str(msg)
                    elif isinstance(msg, bytes):
                        await self._ws.send_bytes(msg)
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
