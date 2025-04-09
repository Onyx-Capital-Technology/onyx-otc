from onyx_otc.types import Channel, OtcErrorCode, SubscriptionStatus
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2

from .utils import OnResponseV2


async def test_server_info_subscribe_unsubscribe(
    cliv2: OnyxWebsocketClientV2, responsesv2: OnResponseV2
) -> None:

    # Setup Test
    cliv2.subscribe_server_info()

    # Await Response to Subscribe request
    response = await responsesv2.get_otc_response()

    # Assert Response
    subscription = response.subscription()
    assert subscription is not None
    assert subscription.channel == Channel.SERVER_INFO
    assert subscription.status == SubscriptionStatus.SUBSCRIBED
    assert subscription.message == "successfully subscribed to server_info"

    # Await for ServerInfo Channel Message After Subscription
    channel_message = await responsesv2.get_otc_event(timeout=6.0)

    # Assert Channel Message
    server_info = channel_message.server_info()
    assert server_info is not None
    assert channel_message.channel == Channel.SERVER_INFO
    assert server_info.socket_uid != ""
    assert server_info.age_millis > 0

    # Unsubscribe from ServerInfo Channel
    cliv2.unsubscribe_server_info()

    # Await Response to Unsubscribe request
    unsubscribe_response = await responsesv2.get_otc_response()

    # Assert Response
    unsubscription = unsubscribe_response.subscription()
    assert unsubscription is not None
    assert unsubscription.channel == Channel.SERVER_INFO
    assert unsubscription.status == SubscriptionStatus.UNSUBSCRIBED


async def test_tickers_error_forbidden(
    cliv2: OnyxWebsocketClientV2, responsesv2: OnResponseV2
) -> None:

    # Setup Test
    cliv2.subscribe_tickers(products=["foobar"])

    # Await Response to Subscribe request
    response = await responsesv2.get_otc_response()

    # Assert Response
    error = response.error()
    assert error is not None
    assert error.code == OtcErrorCode.FORBIDDEN
    assert (
        error.message == "no permissions for product foobar or product does not exist"
    )


async def test_tickers_error_invalid_request(
    cliv2: OnyxWebsocketClientV2, responsesv2: OnResponseV2
) -> None:

    # Setup Test
    cliv2.subscribe_tickers(products=[])

    # Await Response to Subscribe request
    response = await responsesv2.get_otc_response()

    # Assert Response
    error = response.error()
    assert error is not None
    assert error.code == OtcErrorCode.INVALID_REQUEST
    assert error.message == "no products specified to subscribe to on tickers channel"
