from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from decimal import Decimal

from .models import Exchange, OtcChannelMessage, OtcResponse, TradableSymbol
from .websocket_v2 import OnyxWebsocketClientV2

logger = logging.getLogger(__name__)


@dataclass
class OnyxJsonWebsocketClientV2(OnyxWebsocketClientV2):
    ws_url: str = field(
        default_factory=lambda: os.environ.get(
            "ONYX_WS_V2_URL", "wss://ws.onyxhub.co/stream/v2"
        )
    )

    async def handle_binary_message(self, data: bytes) -> None:
        """Handle incoming binary messages."""
        logger.warning("Received unexpected binary message: %s", data)

    async def handle_text_message(self, data: str) -> None:
        """Handle incoming text messages."""
        payload = json.loads(data)
        if response := OtcResponse.from_json(payload):
            self.on_response(self, response)
        elif message := OtcChannelMessage.from_json(payload):
            self.on_event(self, message)
        else:
            logger.warning("Unknown message type received")

    def authenticate(self) -> None:
        """Authenticate the client."""
        if self.api_token:
            self.send(
                dict(
                    method="auth",
                    token=self.api_token,
                )
            )
        else:
            logger.warning("No API token provided, authentication skipped.")

    def subscribe_server_info(self) -> None:
        """Subscribe to server info channel."""
        self.send(dict(method="subscribe", channel="server_info"))

    def unsubscribe_server_info(self) -> None:
        """Unsubscribe from server info channel."""
        self.send(dict(method="unsubscribe", channel="server_info"))

    def subscribe_tickers(self, products: list[str]) -> None:
        """Subscribe to ticker updates for specific products."""
        self.send(dict(method="subscribe", channel="tickers", products=products))

    def unsubscribe_tickers(self, products: list[str]) -> None:
        """Unsubscribe from ticker updates for specific products."""
        self.send(dict(method="unsubscribe", channel="tickers", products=products))

    def subscribe_orders(self) -> None:
        """Subscribe to order updates."""
        self.send(dict(method="subscribe", channel="orders"))

    def unsubscribe_orders(self) -> None:
        """Unsubscribe from order updates."""
        self.send(dict(method="unsubscribe", channel="orders"))

    def subscribe_rfq(
        self, symbol: TradableSymbol, size: Decimal, exchange: Exchange
    ) -> None:
        """Subscribe to RFQ updates."""
        self.send(
            dict(
                method="subscribe",
                channel="rfq",
                symbol=symbol.to_string(),
                size=str(size),
                exchange=exchange.value,
            )
        )

    def send(self, data: dict) -> None:
        """Send a message to the server."""
        if not self.is_running:
            logger.warning("Client not running, message dropped: %s", data)
            return
        self._queue.put_nowait(json.dumps(data))
