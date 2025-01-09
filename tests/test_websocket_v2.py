from onyx_otc.v2.types_pb2 import Channel, SubscriptionStatus
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2
from tests.utils import OnResponseV2, assert_server_info_message


async def test_server_info_subscribe_unsubscribe(
    cliv2: OnyxWebsocketClientV2, responsesv2: OnResponseV2
) -> None:

    # Setup Test
    request = cliv2.subscribe_server_info()

    # Await Response to Subscribe request
    await responsesv2.assert_otc_response(
        predicate=lambda response: (
            response.subscription.channel == Channel.CHANNEL_SERVER_INFO
            and response.subscription.status
            == SubscriptionStatus.SUBSCRIPTION_STATUS_SUBSCRIBED
            and response.id == request.id
            and response.subscription.message
            == "successfully subscribed to server_info"
        )
    )

    await responsesv2.assert_otc_event(
        predicate=assert_server_info_message, timeout=6.0
    )

    request = cliv2.unsubscribe_server_info()

    await responsesv2.assert_otc_response(
        predicate=lambda response: (
            response.subscription.channel == Channel.CHANNEL_SERVER_INFO
            and response.subscription.status
            == SubscriptionStatus.SUBSCRIPTION_STATUS_UNSUBSCRIBED
            and response.id == request.id
        )
    )
