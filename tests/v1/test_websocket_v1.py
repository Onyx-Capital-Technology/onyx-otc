from onyx_otc.websocket_v1 import OnyxWebsocketClientV1

from .utils import OnResponseV1


async def test_no_auth(cli_no_auth: OnyxWebsocketClientV1, responses: OnResponseV1):
    cli_no_auth.subscribe("server_info")
    msg = await responses.get_response(3.0)
    assert msg["method"] == "subscribe"
    assert msg["message"] == dict(
        Message="authentication required for method subscribe"
    )


async def test_server_info(cli: OnyxWebsocketClientV1, responses: OnResponseV1):
    cli.subscribe("server_info")
    msg = await responses.get_response()
    assert msg["method"] == "subscribe"
    assert msg["message"] == dict(Message="subscribed to server_info")
    event = await responses.get_event(timeout=10)
    assert event["channel"] == "server_info"
    assert event["message_type"] == 0
    cli.unsubscribe("server_info")
    msg = await responses.get_response()
    assert msg["method"] == "unsubscribe"
    assert msg["message"] == dict(Message="unsubscribed from server_info")
    cli.unsubscribe("server_info")
    msg = await responses.get_response()
    assert msg["method"] == "unsubscribe"
    assert msg["error"] is True
    assert msg["message"] == dict(Message="not subscribed to server_info")


async def test_dashboards(cli: OnyxWebsocketClientV1, responses: OnResponseV1):
    cli.subscribe("dashboards")
    msg = await responses.get_response()
    assert msg["method"] == "subscribe"
    assert msg["message"] == dict(Message="subscribed to dashboards")
    cli.subscribe("dashboards")
    msg = await responses.get_response()
    assert msg["method"] == "subscribe"
    assert msg["message"] == dict(Message="already subscribed to dashboards")
    event = await responses.get_event(timeout=10)
    assert event["channel"] == "dashboards"
    assert event["message_type"] == 0
    assert event["message"]
    assert isinstance(event["message"], list)
    cli.unsubscribe("dashboards")
    msg = await responses.get_response()
    assert msg["method"] == "unsubscribe"
    assert msg["message"] == dict(Message="unsubscribed from dashboards")


async def test_tickers_error(cli: OnyxWebsocketClientV1, responses: OnResponseV1):
    cli.subscribe("tickers", products=[])
    msg = await responses.get_response()
    assert msg["method"] == "subscribe"
    assert msg["error"]
    assert msg["message"] == dict(Message="no products specified")
    cli.subscribe("tickers", products=["gjhgjg"])
    msg = await responses.get_response()
    assert msg["method"] == "subscribe"
    assert msg["error"]
    assert msg["message"] == dict(
        Message="no permissions for product gjhgjg or product does not exist"
    )


async def test_snapshots(cli: OnyxWebsocketClientV1, responses: OnResponseV1):
    cli.subscribe("snapshots")
    msg = await responses.get_response()
    assert msg["method"] == "subscribe"
    assert msg["message"] == dict(Message="subscribed to snapshots")
    cli.subscribe("snapshots")
    msg = await responses.get_response()
    assert msg["method"] == "subscribe"
    assert msg["message"] == dict(Message="already subscribed to snapshots")
    event = await responses.get_event(timeout=10)
    assert event["channel"] == "snapshots"
    assert event["message_type"] == 0
    assert event["message"]
    cli.unsubscribe("snapshots")
    msg = await responses.get_response()
    assert msg["method"] == "unsubscribe"
    assert msg["message"] == dict(Message="unsubscribed from snapshots")


async def test_bad_payload(cli: OnyxWebsocketClientV1, responses: OnResponseV1):
    cli.send(dict(id="msg:1", method="order", random=True))
    msg = await responses.get_response()
    assert msg["error"]
    assert msg["message"] == dict(Message="bad request")


async def test_tickers(cli: OnyxWebsocketClientV1, responses: OnResponseV1):
    cli.subscribe("tickers", products=["dub"])
    msg = await responses.get_response()
    assert msg["method"] == "subscribe"
    assert msg["message"] == dict(Message="subscribed to tickers for product dub")
    event = await responses.get_event()
    assert event["channel"] == "tickers"
    assert event["message_type"] == 1
    tickers = event["message"]
    for ticker in tickers:
        assert ticker["product_symbol"] == "dub"
