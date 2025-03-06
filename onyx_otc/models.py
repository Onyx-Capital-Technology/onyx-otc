from datetime import datetime, timezone
from decimal import Decimal
from typing import Self

from pydantic import BaseModel

from .v2 import common_pb2, responses_pb2
from .v2.types_pb2 import Exchange


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

    def as_string(self) -> str:
        if isinstance(self.symbol, str):
            return self.symbol
        return self.symbol.to_string()


class OtcQuote(BaseModel):
    symbol: TradableSymbol
    exchange: Exchange.ValueType
    timestamp: datetime
    product_symbol: str
    buy: PriceAmount
    sell: PriceAmount

    @classmethod
    def from_proto(cls, proto: responses_pb2.OtcQuote) -> Self:
        return cls(
            symbol=TradableSymbol.from_proto(proto.symbol),
            exchange=proto.exchange,
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
