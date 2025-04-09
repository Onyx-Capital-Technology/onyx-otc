import asyncio
import logging
from dataclasses import dataclass, field
from datetime import timedelta

import click
import dotenv

from onyx_otc.requests import InvalidInputError, RfqChannel
from onyx_otc.responses import OtcChannelMessage, OtcResponse
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2

logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    server_info: bool = False
    tickers: list[str] = field(default_factory=list)
    rfqs: list[RfqChannel] = field(default_factory=list)

    def on_response(self, cli: OnyxWebsocketClientV2, response: OtcResponse) -> None:
        if auth := response.auth():
            logger.info("Auth response: %s", auth.message)
            if self.server_info:
                cli.subscribe_server_info()
            if self.tickers:
                cli.subscribe_tickers(self.tickers)
            for rfq in self.rfqs:
                cli.subscribe_rfq(rfq)
        elif subscription := response.subscription():
            logger.info(
                "Subscription channel: %s, message: %s, status: %s",
                subscription.channel,
                subscription.message,
                subscription.status,
            )
        elif order := response.order():
            logger.info("Order: %s", order)
        elif error := response.error():
            logger.error("Error %s: %s", error.code, error.message)

    def on_event(self, cli: OnyxWebsocketClientV2, message: OtcChannelMessage) -> None:
        if order := message.order():
            logger.info("Order: %s", order)
        elif server_info := message.server_info():
            delta = timedelta(seconds=int(0.001 * server_info.age_millis))
            logger.info(
                "Server info: socket_uid: %s, age: %s", server_info.socket_uid, delta
            )
        elif tickers := message.tickers():
            for ticker in tickers.tickers:
                symbol = ticker.symbol
                timestamp = ticker.timestamp.to_datetime()
                logger.info(
                    "%s - %s - %s",
                    symbol,
                    timestamp.isoformat(),
                    ticker.mid,
                )
        elif otc_quote := message.otc_quote():
            logger.info(otc_quote.as_string())


async def run_client_websocket(
    workflow: Workflow, binary: bool, token: str | None = None
) -> None:
    client = OnyxWebsocketClientV2.create(
        binary=binary,
        on_response=workflow.on_response,
        on_event=workflow.on_event,
        api_token=token,
    )
    await client.connect()


@click.command()
@click.option(
    "--tickers",
    "-t",
    multiple=True,
    help="Product symbols to subscribe to tickers channel",
)
@click.option(
    "--server-info",
    "-s",
    is_flag=True,
    help="Subscribe to server info",
)
@click.option(
    "--rfq",
    "-r",
    help="RFQ symbols as <symbol>@<exchange>@<size=1>",
    multiple=True,
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    help="Use JSON stream instead of protobuf",
)
@click.option(
    "--token",
    help="API token",
)
def stream(
    tickers: list[str], server_info: bool, rfq: list[str], json: bool, token: str | None
) -> None:
    """Stream websocket data from Onyx."""
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    try:
        workflow = Workflow(
            server_info=server_info,
            tickers=tickers,
            rfqs=[RfqChannel.from_string(r) for r in rfq],
        )
    except InvalidInputError as e:
        click.echo(e, err=True)
        raise click.Abort() from None
    try:
        asyncio.run(run_client_websocket(workflow, binary=not json, token=token))
    except KeyboardInterrupt:
        pass
