import asyncio
from typing import AsyncIterator

import pytest

from onyx_otc.websocket import OnyxWebsocketClient
from tests.utils import OnResponse


@pytest.fixture(scope="module")
def responses() -> OnResponse:
    return OnResponse()


@pytest.fixture(scope="module")
async def cli_no_auth(responses: OnResponse) -> AsyncIterator[OnyxWebsocketClient]:
    cli = OnyxWebsocketClient(
        api_token="",
        on_response=responses.on_response,
        on_event=responses.on_event,
    )
    read_task = asyncio.create_task(cli.run())
    # await for connection
    await cli.connected()
    try:
        yield cli
    finally:
        read_task.cancel()
        try:
            await read_task
        except asyncio.CancelledError:
            pass


@pytest.fixture(scope="module")
async def cli(responses: OnResponse):
    cli = OnyxWebsocketClient(
        on_response=responses.on_response,
        on_event=responses.on_event,
    )
    read_task = asyncio.create_task(cli.run())
    # await for authentication
    await responses.get_response()
    try:
        yield cli
    finally:
        read_task.cancel()
        try:
            await read_task
        except asyncio.CancelledError:
            pass
