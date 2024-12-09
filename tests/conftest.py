import asyncio
from typing import AsyncIterator

import pytest

from onyx_otc.websocket import OnyxWebsocketClient
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2
from tests.utils import OnResponse, OnResponseV2


@pytest.fixture
def responses() -> OnResponse:
    return OnResponse()


@pytest.fixture
def responsesv2() -> OnResponseV2:
    return OnResponseV2()


@pytest.fixture
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


@pytest.fixture
async def cli(responses: OnResponse):
    cli = OnyxWebsocketClient(
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


@pytest.fixture
async def cliv2(responsesv2: OnResponseV2):
    cli = OnyxWebsocketClientV2(
        on_response=responsesv2.on_response,
        on_event=responsesv2.on_event,
    )
    assert cli.api_token
    read_task = asyncio.create_task(cli.connect())
    await responsesv2.get_otc_response()
    try:
        yield cli
    finally:
        read_task.cancel()
        try:
            await read_task
        except asyncio.CancelledError:
            pass
