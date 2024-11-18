from onyx_otc.v2.types_pb2 import Channel, SubscriptionStatus
from onyx_otc.websocket_v2 import OnyxWebsocketClientV2
from tests.utils import OnResponseV2


async def test_server_info(
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
