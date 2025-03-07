import asyncio
import logging
from dataclasses import dataclass, field
from datetime import timedelta, timezone
from decimal import Decimal
from typing import NamedTuple, Self

import click
import dotenv

from onyx_otc.models import OtcQuote, TradableSymbol
from onyx_otc.utils import to_proto_decimal
from onyx_otc.v2.responses_pb2 import ChannelMessage, OtcResponse
from onyx_otc.v2.types_pb2 import Exchange
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2

logger = logging.getLogger(__name__)


class InvalidInputError(ValueError):
    pass


class ProductRisk(NamedTuple):
    product_symbol: str
    account_id: float


class Rfq(NamedTuple):
    symbol: TradableSymbol
    exchange: Exchange.ValueType
    quantity: Decimal = Decimal(1)

    @classmethod
    def from_string(cls, rfq: str) -> Self:
        try:
            symbol, exchange = rfq.split("@")
        except ValueError:
            raise InvalidInputError(
                f"Invalid RFQ format: {rfq} - must be symbol@exchange"
            ) from None
        try:
            exchange_enum = Exchange.Value(f"EXCHANGE_{exchange.upper()}")
        except ValueError:
            raise InvalidInputError(f"Invalid exchange: {exchange}") from None
        return cls(
            symbol=TradableSymbol.from_string(symbol),
            exchange=exchange_enum,
        )


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
                    cli.subscribe_rfq(
                        rfq.symbol.to_proto(),
                        to_proto_decimal(rfq.quantity),
                        rfq.exchange,
                    )
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


async def one_client(workflow: Workflow | None = None) -> None:
    if workflow is None:
        workflow = Workflow(
            server_info=True,
            rfq=[Rfq(TradableSymbol(symbol="brtz25"), exchange=Exchange.EXCHANGE_ICE)],
        )
    try:
        await test_websocket(workflow)
    except Exception as e:
        logger.error("%s", e)


@click.command()
@click.option(
    "--tickers",
    "-t",
    multiple=True,
    help="Product symbols to subscribe to tickers channel",
)
@click.option("--server-info", "-s", is_flag=True, help="Subscribe to server info")
@click.option("--rfq", "-r", help="RFQ symbols as symbol@exchange", multiple=True)
def main(tickers: list[str], server_info: bool, rfq: list[str]) -> None:
    """Example of using the Onyx OTC websocket client."""
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    try:
        workflow = Workflow(
            server_info=server_info,
            tickers=tickers,
            rfq=[Rfq.from_string(r) for r in rfq],
        )
    except InvalidInputError as e:
        click.echo(e, err=True)
        raise click.Abort() from None
    asyncio.run(one_client(workflow))


if __name__ == "__main__":
    main()
