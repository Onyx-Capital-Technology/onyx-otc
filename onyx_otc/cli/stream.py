import asyncio
import logging
from dataclasses import dataclass, field

import click

from onyx_otc.requests import InvalidInputError, RfqChannel
from onyx_otc.responses import OtcChannelMessage, OtcResponse
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2

from . import common

logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    server_info: bool = False
    tickers: list[str] = field(default_factory=list)
    obt: list[str] = field(default_factory=list)
    rfqs: list[RfqChannel] = field(default_factory=list)

    def on_response(self, cli: OnyxWebsocketClientV2, response: OtcResponse) -> None:
        response.log()
        if response.auth():
            if self.server_info:
                cli.subscribe_server_info()
            if self.tickers:
                cli.subscribe_tickers(self.tickers)
            if self.obt:
                cli.subscribe_obt(self.obt)
            for rfq in self.rfqs:
                cli.subscribe_rfq(rfq)

    def on_event(self, cli: OnyxWebsocketClientV2, message: OtcChannelMessage) -> None:
        message.log()


async def run_client_websocket(
    workflow: Workflow,
    binary: bool,
    token: str | None = None,
    ws_url: str | None = None,
) -> None:
    client = OnyxWebsocketClientV2.create(
        binary=binary,
        on_response=workflow.on_response,
        on_event=workflow.on_event,
        api_token=token,
        ws_url=ws_url,
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
    "--obt",
    "-o",
    multiple=True,
    help="Product symbols to subscribe to order-book-top channel",
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
@common.token_option
@common.url_option
def stream(
    tickers: list[str],
    obt: list[str],
    server_info: bool,
    rfq: list[str],
    json: bool,
    token: str | None,
    url: str | None,
) -> None:
    """Stream websocket data from Onyx."""
    try:
        workflow = Workflow(
            server_info=server_info,
            tickers=tickers,
            obt=obt,
            rfqs=[RfqChannel.from_string(r) for r in rfq],
        )
    except InvalidInputError as e:
        click.echo(e, err=True)
        raise click.Abort() from None
    try:
        asyncio.run(
            run_client_websocket(workflow, binary=not json, token=token, ws_url=url)
        )
    except KeyboardInterrupt:
        pass
