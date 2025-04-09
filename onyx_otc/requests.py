from __future__ import annotations

from decimal import Decimal
from typing import Any, Self

from pydantic import BaseModel

from .common import TradableSymbol
from .timestamp import Timestamp
from .types import Channel, Exchange, Method, OrderType, Side
from .v2 import common_pb2, requests_pb2


class InvalidInputError(ValueError):
    pass


class AuthRequest(BaseModel):
    """Request for authentication."""

    token: str

    def to_proto(self) -> requests_pb2.Auth:
        return requests_pb2.Auth(token=self.token)


class OtcOrderRequest(BaseModel):
    """Request for placing an order."""

    account_id: str
    symbol: TradableSymbol
    quantity: Decimal
    side: Side
    price: Decimal
    order_type: OrderType = OrderType.FILL_OR_KILL
    client_order_id: str = ""

    def to_proto(self) -> requests_pb2.NewOrderRequest:
        return requests_pb2.NewOrderRequest(
            account_id=self.account_id,
            symbol=self.symbol.to_proto(),
            quantity=common_pb2.Decimal(value=str(self.quantity)),
            side=self.side.to_proto(),
            price=common_pb2.Decimal(value=str(self.price)),
            order_type=self.order_type.to_proto(),
            client_order_id=self.client_order_id,
        )


class TickersChannel(BaseModel):
    """Request for subscribing to ticker updates for a list of product symbols."""

    products: list[str]

    def to_proto(self) -> requests_pb2.TickersChannel:
        return requests_pb2.TickersChannel(products=self.products)


class OrderBookTopChannel(BaseModel):
    """Request for subscribing to order book top updates for
    a list of product symbols.
    """

    products: list[str]

    def to_proto(self) -> requests_pb2.OrderBookTopChannel:
        return requests_pb2.OrderBookTopChannel(products=self.products)


class ServerInfoChannel(BaseModel):

    def to_proto(self) -> requests_pb2.ServerInfoChannel:
        return requests_pb2.ServerInfoChannel()


class OrdersChannel(BaseModel):

    def to_proto(self) -> requests_pb2.OrdersChannel:
        return requests_pb2.OrdersChannel()


class RfqChannel(BaseModel):
    """Request for subscribing to RFQ updates for a symbol."""

    symbol: TradableSymbol
    exchange: Exchange
    size: Decimal = Decimal(1)

    @classmethod
    def from_string(cls, rfq: str) -> Self:
        bits = rfq.split("@")
        if len(bits) > 1:
            symbol = TradableSymbol.from_string(bits[0])
            exchange = Exchange[bits[1].upper()]
            size = Decimal(bits[2]) if len(bits) > 2 else Decimal(1)
            return cls(symbol=symbol, exchange=exchange, size=size)
        else:
            raise InvalidInputError(
                f"Invalid RFQ format: {rfq}. Expected <symbol>@<exchange>@<size>"
            )

    def to_proto(self) -> requests_pb2.RfqChannel:
        return requests_pb2.RfqChannel(
            symbol=self.symbol.to_proto(),
            size=common_pb2.Decimal(value=str(self.size)),
            exchange=self.exchange.to_proto(),
        )

    def model_dump(self, **kwargs: Any) -> dict:
        """Customize serialization to ensure `symbol` is a string."""
        data = super().model_dump(**kwargs)
        data["symbol"] = self.symbol.as_string()  # Convert symbol to string
        return data


channel_from_data_type = {
    ServerInfoChannel: Channel.SERVER_INFO,
    TickersChannel: Channel.TICKERS,
    OrdersChannel: Channel.ORDERS,
    OrderBookTopChannel: Channel.ORDER_BOOK_TOP,
    RfqChannel: Channel.RFQ,
}


class SubscribeRequestBase(BaseModel):
    data: (
        ServerInfoChannel
        | TickersChannel
        | OrdersChannel
        | RfqChannel
        | OrderBookTopChannel
    )

    @property
    def channel(self) -> Channel:
        return channel_from_data_type[type(self.data)]

    def proto_dict(self) -> dict:
        return {self.channel.subscribe_proto_key: self.data.to_proto()}

    def model_dump(self, **kwargs: Any) -> dict:
        kwargs["mode"] = "json"
        data = self.data.model_dump(**kwargs)
        return {"channel": {self.channel.value: data}}


class SubscribeRequest(SubscribeRequestBase):
    """Request for subscribing to a channel."""

    def to_proto(self) -> requests_pb2.Subscribe:
        return requests_pb2.Subscribe(**self.proto_dict())  # type: ignore[arg-type]


class UnsubscribeRequest(SubscribeRequestBase):
    """Request for unsubscribing from a channel."""

    def to_proto(self) -> requests_pb2.Unsubscribe:
        return requests_pb2.Unsubscribe(**self.proto_dict())  # type: ignore[arg-type]


request_method_from_data_type = {
    AuthRequest: Method.AUTH,
    OtcOrderRequest: Method.ORDER,
    SubscribeRequest: Method.SUBSCRIBE,
    UnsubscribeRequest: Method.UNSUBSCRIBE,
}


class OtcRequest(BaseModel):
    """A request to the websocket API."""

    id: str
    timestamp: Timestamp
    request: AuthRequest | OtcOrderRequest | SubscribeRequest | UnsubscribeRequest

    @property
    def method(self) -> Method:
        return request_method_from_data_type[type(self.request)]

    def to_proto(self) -> requests_pb2.OtcRequest:
        method = self.method
        return requests_pb2.OtcRequest(
            id=self.id,
            timestamp=self.timestamp.to_proto(),
            method=method.to_proto(),
            **{method.value: self.request.to_proto()},  # type: ignore[arg-type]
        )

    def to_json_dict(self) -> dict:
        return dict(
            id=self.id,
            method=self.method.value,
            timestamp=self.timestamp.to_datetime().isoformat(),
            **self.request.model_dump(),
        )
