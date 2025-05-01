import asyncio

import pytest

from onyx_otc.websocket_v2 import OnyxWebsocketClientV2

from .utils import OnResponseV2


@pytest.fixture
def responsesv2() -> OnResponseV2:
    return OnResponseV2()


@pytest.fixture(params=[False])
async def cliv2(request, responsesv2: OnResponseV2):
    cli = OnyxWebsocketClientV2.create(
        on_response=responsesv2.on_response,
        on_event=responsesv2.on_event,
        binary=request.param,
    )
    assert cli.is_binary is request.param
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
    await asyncio.sleep(1)
