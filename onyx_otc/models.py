from __future__ import annotations

import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Self

from pydantic import BaseModel

from .timestamp import Timestamp
from .v2 import common_pb2, requests_pb2, responses_pb2, types_pb2


class Exchange(enum.StrEnum):
    UNSPECIFIED = enum.auto()
    ICE = enum.auto()
    CME = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.Exchange.ValueType) -> Self:
        return cls[types_pb2.Exchange.Name(proto)[9:]]

    def to_proto(self) -> types_pb2.Exchange.ValueType:
        return getattr(types_pb2.Exchange, f"EXCHANGE_{self.name}")


class Method(enum.StrEnum):
    UNSPECIFIED = enum.auto()
    AUTH = enum.auto()
    ORDER = enum.auto()
    SUBSCRIBE = enum.auto()
    UNSUBSCRIBE = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.Method.ValueType) -> Self:
        return cls[types_pb2.Method.Name(proto)[7:]]

    def to_proto(self) -> types_pb2.Method.ValueType:
        return getattr(types_pb2.Method, f"METHOD_{self.name}")


class Channel(enum.StrEnum):
    UNSPECIFIED = enum.auto()
    SERVER_INFO = enum.auto()
    TICKERS = enum.auto()
    ORDERS = enum.auto()
    ORDER_BOOK_TOP = enum.auto()
    RFQ = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.Channel.ValueType) -> Self:
        return cls[types_pb2.Channel.Name(proto)[8:]]

    def to_proto(self) -> types_pb2.Channel.ValueType:
        return getattr(types_pb2.Channel, f"CHANNEL_{self.name}")


class OrderType(enum.StrEnum):
    UNSPECIFIED = enum.auto()
    FILL_OR_KILL = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.OrderType.ValueType) -> Self:
        return cls[types_pb2.OrderType.Name(proto)[11:]]

    def to_proto(self) -> types_pb2.OrderType.ValueType:
        return getattr(types_pb2.OrderType, f"ORDER_TYPE_{self.name}")


class Side(enum.StrEnum):
    UNSPECIFIED = enum.auto()
    BUY = enum.auto()
    SELL = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.Side.ValueType) -> Self:
        return cls[types_pb2.Side.Name(proto)[5:]]

    def to_proto(self) -> types_pb2.Side.ValueType:
        return getattr(types_pb2.Side, f"SIDE_{self.name}")


class SubscriptionStatus(enum.StrEnum):
    UNSPECIFIED = enum.auto()
    SUBSCRIBED = enum.auto()
    UNSUBSCRIBED = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.SubscriptionStatus.ValueType) -> Self:
        return cls[types_pb2.SubscriptionStatus.Name(proto)[20:]]

    def to_proto(self) -> types_pb2.SubscriptionStatus.ValueType:
        return getattr(types_pb2.SubscriptionStatus, f"SUBSCRIPTION_STATUS_{self.name}")


class OtcErrorCode(enum.StrEnum):
    UNSPECIFIED = enum.auto()
    INVALID_REQUEST = enum.auto()
    NOT_IMPLEMENTED = enum.auto()
    UNAUTHENTICATED = enum.auto()
    TOO_MANY_REQUESTS = enum.auto()
    NOT_SUBSCRIBED = enum.auto()
    FORBIDDEN = enum.auto()
    INTERNAL_SERVER_ERROR = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.OtcErrorCode.ValueType) -> Self:
        return cls[types_pb2.OtcErrorCode.Name(proto)[13:]]

    def to_proto(self) -> types_pb2.OtcErrorCode.ValueType:
        return getattr(types_pb2.OtcErrorCode, f"OTC_ERROR_CODE_{self.name}")


class Spread(BaseModel):
    front: str
    back: str

    def to_string(self) -> str:
        return f"{self.front}-{self.back}"


class Butterfly(BaseModel):
    front: str
    middle: str
    back: str

    def to_string(self) -> str:
        return f"{self.front}-{self.middle}-{self.back}"


class PriceAmount(BaseModel):
    price: Decimal
    amount: Decimal

    @classmethod
    def from_proto(
        cls, proto: responses_pb2.PriceAmount | responses_pb2.OtcQuoteSide
    ) -> Self:
        return cls(
            price=Decimal(proto.price.value),
            amount=Decimal(proto.amount.value),
        )

    def as_string(self) -> str:
        return f"{self.amount}@{self.price}"


class TradableSymbol(BaseModel):
    symbol: str | Spread | Butterfly

    @classmethod
    def from_string(cls, symbol: str) -> Self:
        if "-" in symbol:
            parts = symbol.split("-")
            if len(parts) == 2:
                return cls(symbol=Spread(front=parts[0], back=parts[1]))
            if len(parts) == 3:
                return cls(
                    symbol=Butterfly(front=parts[0], middle=parts[1], back=parts[2])
                )
        return cls(symbol=symbol)

    @classmethod
    def from_proto(cls, proto: common_pb2.TradableSymbol) -> Self:
        match proto.WhichOneof("symbol"):
            case "flat":
                return cls(symbol=proto.flat)
            case "spread":
                return cls(
                    symbol=Spread(front=proto.spread.front, back=proto.spread.back)
                )
            case "butterfly":
                return cls(
                    symbol=Butterfly(
                        front=proto.butterfly.front,
                        middle=proto.butterfly.middle,
                        back=proto.butterfly.back,
                    )
                )
            case _:
                raise ValueError(f"Unknown symbol type: {proto}")

    def to_proto(self) -> common_pb2.TradableSymbol:
        if isinstance(self.symbol, str):
            return common_pb2.TradableSymbol(flat=self.symbol)
        elif isinstance(self.symbol, Spread):
            return common_pb2.TradableSymbol(
                spread=common_pb2.Spread(front=self.symbol.front, back=self.symbol.back)
            )
        elif isinstance(self.symbol, Butterfly):
            return common_pb2.TradableSymbol(
                butterfly=common_pb2.Butterfly(
                    front=self.symbol.front,
                    middle=self.symbol.middle,
                    back=self.symbol.back,
                )
            )
        raise ValueError(f"Unknown symbol type: {self.symbol}")

    def as_string(self) -> str:
        if isinstance(self.symbol, str):
            return self.symbol
        return self.symbol.to_string()


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
    """Request for subscribing to ticker updates for a list of product symbols."""

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
            raise ValueError(
                f"Invalid RFQ format: {rfq}. Expected <symbol>@<exchange>@<size>"
            )

    def to_proto(self) -> requests_pb2.RfqChannel:
        return requests_pb2.RfqChannel(
            symbol=self.symbol.to_proto(),
            size=common_pb2.Decimal(value=str(self.size)),
            exchange=self.exchange.to_proto(),
        )


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

    def model_dump(self, **kwargs: Any) -> dict:
        data = self.data.model_dump(**kwargs)
        return {"channel": {self.channel.value: data}}


class SubscribeRequest(SubscribeRequestBase):
    """Request for subscribing to a channel."""

    def to_proto(self) -> requests_pb2.Subscribe:
        return requests_pb2.Subscribe(**{self.channel.value: self.data.to_proto()})  # type: ignore[arg-type]


class UnsubscribeRequest(SubscribeRequestBase):
    """Request for unsubscribing from a channel."""

    def to_proto(self) -> requests_pb2.Unsubscribe:
        return requests_pb2.Unsubscribe(**{self.channel.value: self.data.to_proto()})  # type: ignore[arg-type]


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


class Auth(BaseModel):
    message: str = ""

    @classmethod
    def from_proto(cls, proto: responses_pb2.AuthResponse) -> Self:
        return cls(message=proto.message)


class ServerInfo(BaseModel):
    socket_uid: str
    age_millis: int

    @classmethod
    def from_proto(cls, proto: responses_pb2.ServerInfo) -> Self:
        return cls(
            socket_uid=proto.socket_uid,
            age_millis=proto.age_millis,
        )


class Ticker(BaseModel):
    symbol: str
    product_symbol: str
    timestamp: Timestamp
    mid: Decimal

    @classmethod
    def from_proto(cls, proto: responses_pb2.Ticker) -> Self:
        return cls(
            symbol=proto.symbol,
            product_symbol=proto.product_symbol,
            timestamp=Timestamp.from_proto(proto.timestamp),
            mid=Decimal(proto.mid.value),
        )


class OrderBookTop(BaseModel):
    buy: PriceAmount
    sell: PriceAmount
    symbol: str
    product_symbol: str
    timestamp: Timestamp
    exchange: Exchange

    @classmethod
    def from_proto(cls, proto: responses_pb2.OrderBookTop) -> Self:
        return cls(
            buy=PriceAmount.from_proto(proto.buy),
            sell=PriceAmount.from_proto(proto.sell),
            symbol=proto.symbol,
            product_symbol=proto.product_symbol,
            timestamp=Timestamp.from_proto(proto.timestamp),
            exchange=Exchange.from_proto(proto.exchange),
        )


class OrderBookTops(BaseModel):
    order_book_tops: list[OrderBookTop]

    @classmethod
    def from_proto(cls, proto: responses_pb2.OrderBookTops) -> Self:
        return cls(
            order_book_tops=[
                OrderBookTop.from_proto(order_book_top)
                for order_book_top in proto.order_book_tops
            ]
        )


class Tickers(BaseModel):
    tickers: list[Ticker]

    @classmethod
    def from_proto(cls, proto: responses_pb2.Tickers) -> Self:
        return cls(
            tickers=[Ticker.from_proto(ticker) for ticker in proto.tickers],
        )


class OtcSubscription(BaseModel):
    channel: Channel
    status: SubscriptionStatus
    message: str

    @classmethod
    def from_proto(cls, proto: responses_pb2.Subscription) -> Self:
        return cls(
            channel=Channel.from_proto(proto.channel),
            status=SubscriptionStatus.from_proto(proto.status),
            message=proto.message,
        )


class OtcError(BaseModel):
    code: OtcErrorCode
    message: str

    @classmethod
    def from_proto(cls, proto: responses_pb2.OtcError) -> Self:
        return cls(
            code=OtcErrorCode.from_proto(proto.code),
            message=proto.message,
        )


class OtcQuote(BaseModel):
    symbol: TradableSymbol
    exchange: Exchange
    timestamp: datetime
    product_symbol: str
    buy: PriceAmount
    sell: PriceAmount

    @classmethod
    def from_proto(cls, proto: responses_pb2.OtcQuote) -> Self:
        return cls(
            symbol=TradableSymbol.from_proto(proto.symbol),
            exchange=Exchange.from_proto(proto.exchange),
            timestamp=proto.timestamp.ToDatetime(timezone.utc),
            product_symbol=proto.product_symbol,
            buy=PriceAmount.from_proto(proto.buy),
            sell=PriceAmount.from_proto(proto.sell),
        )

    def as_string(self) -> str:
        return (
            f"{self.symbol.as_string()} "
            f"buy: {self.buy.as_string()}, "
            f"sell: {self.sell.as_string()}"
        )


class OtcOrder(BaseModel):
    id: str
    client_order_id: str
    account_id: str
    symbol: TradableSymbol
    product_symbol: str
    amount: Decimal
    side: Side
    price: Decimal

    @classmethod
    def from_proto(cls, proto: responses_pb2.Order) -> Self:
        return cls(
            id=proto.id,
            client_order_id=proto.client_order_id,
            account_id=proto.account_id,
            symbol=TradableSymbol.from_proto(proto.symbol),
            product_symbol=proto.product_symbol,
            amount=Decimal(proto.amount.value),
            side=Side.from_proto(proto.side),
            price=Decimal(proto.price.value),
        )


class OtcResponse(BaseModel):
    id: str
    timestamp: Timestamp
    data: Auth | OtcError | OtcSubscription | OtcOrder

    def auth(self) -> Auth | None:
        if isinstance(self.data, Auth):
            return self.data
        return None

    def error(self) -> OtcError | None:
        if isinstance(self.data, OtcError):
            return self.data
        return None

    def subscription(self) -> OtcSubscription | None:
        if isinstance(self.data, OtcSubscription):
            return self.data
        return None

    def order(self) -> OtcOrder | None:
        if isinstance(self.data, OtcOrder):
            return self.data
        return None

    @classmethod
    def from_proto_bytes(cls, proto_bytes: bytes) -> Self | None:
        try:
            proto = responses_pb2.OtcResponse.FromString(proto_bytes)
        except Exception:
            return None
        if data := cls.get_data_from_proto(proto):
            return cls(
                id=proto.id,
                timestamp=Timestamp.from_proto(proto.timestamp),
                data=data,
            )
        return None

    @classmethod
    def get_data_from_proto(
        cls, proto: responses_pb2.OtcResponse
    ) -> Auth | OtcError | OtcSubscription | OtcOrder | None:
        match proto.WhichOneof("response"):  # type: ignore[arg-type]
            case "auth":
                return Auth.from_proto(proto.auth)
            case "error":
                return OtcError.from_proto(proto.error)
            case "subscription":
                return OtcSubscription.from_proto(proto.subscription)
            case "order":
                return OtcOrder.from_proto(proto.order)
            case _:
                return None

    @classmethod
    def from_json(cls, payload: dict) -> Self | None:
        id_ = payload.get("id")
        if id_ is None:
            return None
        method = payload["method"]
        timestamp = Timestamp.from_iso_string(payload["timestamp"])
        match method:
            case "auth":
                return cls(
                    id=id_, timestamp=timestamp, data=Auth(message=payload["message"])
                )
            case "otcerror":
                return cls(
                    id=id_,
                    timestamp=timestamp,
                    data=OtcError(
                        message=payload["message"],
                        code=OtcErrorCode[payload["code"].upper()],
                    ),
                )
            case "subscribe" | "unsubscribe":
                return cls(
                    id=id_,
                    timestamp=timestamp,
                    data=OtcSubscription(
                        channel=payload["channel"],
                        message=payload["message"],
                        status=payload["status"],
                    ),
                )
            case "order":
                return cls(
                    id=id_,
                    timestamp=timestamp,
                    data=OtcOrder(
                        id=payload["id"],
                        client_order_id=payload["client_order_id"],
                        account_id=payload["account_id"],
                        symbol=TradableSymbol.from_string(payload["symbol"]),
                        product_symbol=payload["product_symbol"],
                        amount=Decimal(payload["amount"]),
                        side=Side.from_proto(payload["side"]),
                        price=Decimal(payload["price"]),
                    ),
                )
            case _:
                raise ValueError(f"Unknown method: {method}")


class OtcChannelMessage(BaseModel):
    """A message in a subscribed channel"""

    channel: Channel
    timestamp: Timestamp
    data: ServerInfo | Tickers | OtcQuote | OrderBookTops | OtcOrder

    def server_info(self) -> ServerInfo | None:
        if isinstance(self.data, ServerInfo):
            return self.data
        return None

    def tickers(self) -> Tickers | None:
        if isinstance(self.data, Tickers):
            return self.data
        return None

    def order_book_tops(self) -> OrderBookTops | None:
        if isinstance(self.data, OrderBookTops):
            return self.data
        return None

    def otc_quote(self) -> OtcQuote | None:
        if isinstance(self.data, OtcQuote):
            return self.data
        return None

    def order(self) -> OtcOrder | None:
        if isinstance(self.data, OtcOrder):
            return self.data
        return None

    @classmethod
    def from_proto_bytes(cls, proto_bytes: bytes) -> Self | None:
        try:
            proto = responses_pb2.ChannelMessage.FromString(proto_bytes)
            if data := cls.get_data_from_proto(proto):
                return cls(
                    channel=Channel.from_proto(proto.channel),
                    timestamp=Timestamp.from_proto(proto.timestamp),
                    data=data,
                )
            return None
        except Exception:
            return None

    @classmethod
    def get_data_from_proto(
        cls, proto: responses_pb2.ChannelMessage
    ) -> ServerInfo | Tickers | OtcQuote | OrderBookTops | OtcOrder | None:
        match proto.WhichOneof("message"):  # type: ignore[arg-type]
            case "server_info":
                return ServerInfo.from_proto(proto.server_info)
            case "tickers":
                return Tickers.from_proto(proto.tickers)
            case "otc_quote":
                return OtcQuote.from_proto(proto.otc_quote)
            case "order_book_tops":
                return OrderBookTops.from_proto(proto.order_book_tops)
            case "order":
                return OtcOrder.from_proto(proto.order)
            case _:
                return None

    @classmethod
    def from_json(cls, data: dict) -> OtcChannelMessage | None:
        channel = getattr(Channel, (data.get("channel") or "").upper(), None)
        if channel is None:
            return None
        timestamp = Timestamp.from_iso_string(data["timestamp"])
        message = data["message"]
        match channel:
            case Channel.SERVER_INFO:
                return OtcChannelMessage(
                    channel=channel,
                    timestamp=timestamp,
                    data=ServerInfo(**message),
                )
            case Channel.TICKERS:
                return OtcChannelMessage(
                    channel=channel,
                    timestamp=timestamp,
                    data=Tickers(
                        tickers=[
                            Ticker(
                                symbol=ticker["symbol"],
                                product_symbol=ticker["product_symbol"],
                                timestamp=Timestamp.from_iso_string(
                                    ticker["timestamp"]
                                ),
                                mid=Decimal(ticker["mid"]),
                            )
                            for ticker in message
                        ]
                    ),
                )
            case Channel.ORDERS:
                return OtcChannelMessage(
                    channel=channel,
                    timestamp=timestamp,
                    data=OtcOrder(**data),
                )
            case Channel.ORDER_BOOK_TOP:
                return OtcChannelMessage(
                    channel=channel,
                    timestamp=timestamp,
                    data=OrderBookTops(
                        order_book_tops=[
                            OrderBookTop(**obt) for obt in data["order_book_tops"]
                        ]
                    ),
                )
            case _:
                raise ValueError(f"Unknown channel: {channel}")
