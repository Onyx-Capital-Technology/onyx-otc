import pytest

from onyx_otc.v2.types_pb2 import Channel, OtcErrorCode, SubscriptionStatus
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2
from tests.utils import OnResponseV2


@pytest.mark.skip(reason="skip until promoted to UAT")
@pytest.mark.description(
    "Test that a server info subscription and unsubscription works"
)
async def test_server_info_subscribe_unsubscribe(
    cliv2: OnyxWebsocketClientV2, responsesv2: OnResponseV2
) -> None:

    # Setup Test
    cliv2.subscribe_server_info()

    # Await Response to Subscribe request
    response = await responsesv2.get_otc_response()

    # Assert Response
    subscription = response.subscription
    assert subscription.channel == Channel.CHANNEL_SERVER_INFO
    assert subscription.status == SubscriptionStatus.SUBSCRIPTION_STATUS_SUBSCRIBED
    assert subscription.message == "successfully subscribed to server_info"

    # Await for ServerInfo Channel Message After Subscription
    channel_message = await responsesv2.get_otc_event(timeout=6.0)

    # Assert Channel Message
    server_info_message = channel_message.server_info
    assert channel_message.channel == Channel.CHANNEL_SERVER_INFO
    assert server_info_message.socket_uid != ""
    assert server_info_message.age_millis > 0

    # Unsubscribe from ServerInfo Channel
    cliv2.unsubscribe_server_info()

    # Await Response to Unsubscribe request
    unsubscribe_response = await responsesv2.get_otc_response()

    # Assert Response
    unsubscription = unsubscribe_response.subscription
    assert unsubscription.channel == Channel.CHANNEL_SERVER_INFO
    assert unsubscription.status == SubscriptionStatus.SUBSCRIPTION_STATUS_UNSUBSCRIBED


@pytest.mark.skip(reason="skip until promoted to UAT")
@pytest.mark.description(
    "Test that a forbidden error is returned when the product does not exist"
)
async def test_tickers_error_forbidden(
    cliv2: OnyxWebsocketClientV2, responsesv2: OnResponseV2
) -> None:

    # Setup Test
    cliv2.subscribe_tickers(products=["foobar"])

    # Await Response to Subscribe request
    response = await responsesv2.get_otc_response()

    # Assert Response
    error = response.error
    assert error.code == OtcErrorCode.OTC_ERROR_CODE_FORBIDDEN
    assert (
        error.message == "no permissions for product foobar or product does not exist"
    )


@pytest.mark.skip(reason="skip until promoted to UAT")
@pytest.mark.description(
    "Test that an invalid request error is returned when no products \
    are specified to subscribe"
)
async def test_tickers_error_invalid_request(
    cliv2: OnyxWebsocketClientV2, responsesv2: OnResponseV2
) -> None:

    # Setup Test
    cliv2.subscribe_tickers(products=[])

    # Await Response to Subscribe request
    response = await responsesv2.get_otc_response()

    # Assert Response
    error = response.error
    assert error.code == OtcErrorCode.OTC_ERROR_CODE_INVALID_REQUEST
    assert error.message == "no products specified to subscribe to on tickers channel"
