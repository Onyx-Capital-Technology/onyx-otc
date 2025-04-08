import asyncio

import pytest

from onyx_otc import websocket_v2_client

from .utils import OnResponseV2


@pytest.fixture
def responsesv2() -> OnResponseV2:
    return OnResponseV2()


@pytest.fixture
async def cliv2(responsesv2: OnResponseV2):
    cli = websocket_v2_client(
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


@pytest.fixture
async def cliv2_json(responsesv2: OnResponseV2):
    cli = websocket_v2_client(
        on_response=responsesv2.on_response,
        on_event=responsesv2.on_event,
        json=True,
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
