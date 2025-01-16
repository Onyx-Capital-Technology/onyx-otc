import asyncio
from typing import AsyncIterator

import pytest

from onyx_otc.websocket_v1 import OnyxWebsocketClientV1

from .utils import OnResponseV1


@pytest.fixture
def responses() -> OnResponseV1:
    return OnResponseV1()


@pytest.fixture
async def cli_no_auth(responses: OnResponseV1) -> AsyncIterator[OnyxWebsocketClientV1]:
    cli = OnyxWebsocketClientV1(
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


@pytest.fixture
async def cli(responses: OnResponseV1):
    cli = OnyxWebsocketClientV1(
        on_response=responses.on_response,
        on_event=responses.on_event,
    )
    assert cli.api_token
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
    # sleep to prevent connection limit exceeded
    await asyncio.sleep(0.6)
