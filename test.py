import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import NamedTuple

import dotenv

from onyx_otc.websocket import OnyxWebsocketClient

logger = logging.getLogger(__name__)


class ProductRisk(NamedTuple):
    product_symbol: str
    account_id: float


@dataclass
class Workflow:
    products: list[str] = field(default_factory=list)
    tickers: set | None = None
    snapshots: bool = False
    server_info: bool = False
    rfq: list[str] = field(default_factory=list)

    def on_response(self, cli: OnyxWebsocketClient, data: dict):
        if data["method"] == "auth":
            if data.get("error"):
                raise RuntimeError(data["message"])
            if self.server_info:
                cli.subscribe("server_info")
            if self.snapshots:
                cli.subscribe("snapshots")
            if self.products:
                cli.subscribe("tickers", products=self.products)
            for rfq in self.rfq:
                cli.subscribe("rfq", product_symbol=rfq)
        else:
            logger.info("%s", json.dumps(data, indent=2))

    def on_event(self, cli: OnyxWebsocketClient, data: dict):
        channel = data.get("channel")
        match channel:
            case "tickers":
                for ticker in data.get("message", ()):
                    symbol = ticker["symbol"]
                    timestamp = datetime.fromtimestamp(
                        0.001 * ticker["timestamp_millis"], tz=timezone.utc
                    )
                    if self.tickers and symbol not in self.tickers:
                        continue
                    logger.info(
                        "%s - %s - %s",
                        symbol,
                        timestamp.isoformat(),
                        ticker["mid"],
                    )
            case _:
                logger.info("%s", json.dumps(data, indent=2))


async def test_websocket(workflow: Workflow):
    client = OnyxWebsocketClient(
        on_response=workflow.on_response, on_event=workflow.on_event
    )
    await client.run()


async def one_client():
    workflow = Workflow(
        server_info=True,
        snapshots=True,
        # tickers=set(["cfd09u2413u24"]),
        products=["gasarb"],
    )
    try:
        await test_websocket(workflow)
    except Exception as e:
        logger.error("%s", e)


if __name__ == "__main__":
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.DEBUG)
    while True:
        asyncio.get_event_loop().run_until_complete(one_client())
        time.sleep(1)
