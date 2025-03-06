import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta, timezone
from typing import NamedTuple

import dotenv

from onyx_otc.models import OtcQuote
from onyx_otc.v2.common_pb2 import Decimal, TradableSymbol
from onyx_otc.v2.responses_pb2 import ChannelMessage, OtcResponse
from onyx_otc.v2.types_pb2 import Exchange
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2

logger = logging.getLogger(__name__)


class ProductRisk(NamedTuple):
    product_symbol: str
    account_id: float


class Rfq(NamedTuple):
    symbol: TradableSymbol
    exchange: Exchange.ValueType
    quantity: Decimal = Decimal(value="1")


@dataclass
class Workflow:
    tickers: list[str] = field(default_factory=list)
    server_info: bool = False
    rfq: list[Rfq] = field(default_factory=list)

    def on_response(self, cli: OnyxWebsocketClientV2, response: OtcResponse) -> None:
        match response.WhichOneof("response"):
            case "auth":
                logger.info("Auth response: %s", response.auth.message)
                if self.server_info:
                    cli.subscribe_server_info()
                if self.tickers:
                    cli.subscribe_tickers(self.tickers)
                for rfq in self.rfq:
                    cli.subscribe_rfq(rfq.symbol, rfq.quantity, rfq.exchange)
            case "subscription":
                logger.info(
                    "Subscription channel: %s, message: %s, status: %s",
                    response.subscription.channel,
                    response.subscription.message,
                    response.subscription.status,
                )
            case "order":
                logger.info("Order: %s", response.order)
            case "error":
                logger.error("Error: %s", response.error.message)

    def on_event(self, cli: OnyxWebsocketClientV2, message: ChannelMessage) -> None:
        match message.WhichOneof("message"):
            case "order":
                logger.info("Order: %s", message.order)
            case "server_info":
                delta = timedelta(seconds=int(0.001 * message.server_info.age_millis))
                logger.info(
                    "Server info: %s, age: %s", message.server_info.socket_uid, delta
                )
            case "tickers":
                for ticker in message.tickers.tickers:
                    symbol = ticker.symbol
                    timestamp = ticker.timestamp.ToDatetime(timezone.utc)
                    logger.info(
                        "%s - %s - %s",
                        symbol,
                        timestamp.isoformat(),
                        ticker.mid.value,
                    )
            case "otc_quote":
                logger.info(OtcQuote.from_proto(message.otc_quote).as_string())


async def test_websocket(workflow: Workflow) -> None:
    client = OnyxWebsocketClientV2(
        on_response=workflow.on_response, on_event=workflow.on_event
    )
    await client.connect()


async def one_client() -> None:
    workflow = Workflow(
        server_info=True,
        # tickers=set(["cfd09u2413u24"]),
        rfq=[Rfq(TradableSymbol(flat="brtz25"), exchange=Exchange.EXCHANGE_ICE)],
    )
    try:
        await test_websocket(workflow)
    except Exception as e:
        logger.error("%s", e)


if __name__ == "__main__":
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    try:
        while True:
            asyncio.run(one_client())
            time.sleep(1)
    except KeyboardInterrupt:
        pass
