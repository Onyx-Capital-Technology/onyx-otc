from __future__ import annotations

from decimal import Decimal
from typing import Self

from pydantic import BaseModel

from .v2 import common_pb2, responses_pb2


class InvalidInputError(ValueError):
    pass


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
