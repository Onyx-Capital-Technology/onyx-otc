from __future__ import annotations

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, field_validator

from .common import PriceAmount, TradableSymbol
from .timestamp import Timestamp
from .types import Channel, Exchange, OtcErrorCode, Side, SubscriptionStatus
from .v2 import responses_pb2


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
    """An Quote from an RFQ subscription"""

    symbol: TradableSymbol
    exchange: Exchange
    timestamp: Timestamp
    product_symbol: str
    buy: PriceAmount
    sell: PriceAmount

    @classmethod
    def from_proto(cls, proto: responses_pb2.OtcQuote) -> Self:
        return cls(
            symbol=TradableSymbol.from_proto(proto.symbol),
            exchange=Exchange.from_proto(proto.exchange),
            timestamp=Timestamp.from_proto(proto.timestamp),
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

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: str) -> TradableSymbol:
        """Custom validator to create TradableSymbol from a string."""
        if isinstance(value, str):
            return TradableSymbol.from_string(value)
        return value


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
                                timestamp=Timestamp.from_iso_string(
                                    ticker.pop("timestamp")
                                ),
                                **ticker,
                            )
                            for ticker in message
                        ]
                    ),
                )
            case Channel.RFQ:
                message["timestamp"] = Timestamp.from_iso_string(message["timestamp"])
                return OtcChannelMessage(
                    channel=channel,
                    timestamp=timestamp,
                    data=OtcQuote(**message),
                )
            case Channel.ORDERS:
                return OtcChannelMessage(
                    channel=channel,
                    timestamp=timestamp,
                    data=OtcOrder(**message),
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
