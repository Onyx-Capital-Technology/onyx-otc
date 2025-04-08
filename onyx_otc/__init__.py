import os
from typing import Any

from .websocket_v2 import OnyxProtoWebsocketClientV2, OnyxWebsocketClientV2
from .websocket_v2_json import OnyxJsonWebsocketClientV2


def websocket_v2_client(*, json: bool = False, **kwargs: Any) -> OnyxWebsocketClientV2:
    """Create a client instance from environment variables."""
    ws_url = os.environ.get("ONYX_WS_V2_URL", "wss://ws.onyxhub.co/stream/v2/binary")
    if ws_url.endswith("/binary") and json:
        ws_url = ws_url.replace("/binary", "")
    kwargs["ws_url"] = ws_url
    if ws_url.endswith("/binary"):
        return OnyxProtoWebsocketClientV2(**kwargs)
    else:
        return OnyxJsonWebsocketClientV2(**kwargs)
