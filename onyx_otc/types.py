from __future__ import annotations

import enum
from typing import Self

from .v2 import types_pb2


class ProtoEnum(enum.StrEnum):

    def __repr__(self) -> str:
        return self.value


class Exchange(ProtoEnum):
    UNSPECIFIED = enum.auto()
    ICE = enum.auto()
    CME = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.Exchange.ValueType) -> Self:
        return cls[types_pb2.Exchange.Name(proto)[9:]]

    def to_proto(self) -> types_pb2.Exchange.ValueType:
        return getattr(types_pb2.Exchange, f"EXCHANGE_{self.name}")

    def __str__(self) -> str:
        return self.value


class Method(ProtoEnum):
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


class Channel(ProtoEnum):
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

    @property
    def subscribe_proto_key(self) -> str:
        # TODO: this needs fixing on a new version
        if self is Channel.RFQ:
            return "rfq_channel"
        return self.value


class OrderType(ProtoEnum):
    UNSPECIFIED = enum.auto()
    FILL_OR_KILL = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.OrderType.ValueType) -> Self:
        return cls[types_pb2.OrderType.Name(proto)[11:]]

    def to_proto(self) -> types_pb2.OrderType.ValueType:
        return getattr(types_pb2.OrderType, f"ORDER_TYPE_{self.name}")


class Side(ProtoEnum):
    UNSPECIFIED = enum.auto()
    BUY = enum.auto()
    SELL = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.Side.ValueType) -> Self:
        return cls[types_pb2.Side.Name(proto)[5:]]

    def to_proto(self) -> types_pb2.Side.ValueType:
        return getattr(types_pb2.Side, f"SIDE_{self.name}")


class SubscriptionStatus(ProtoEnum):
    UNSPECIFIED = enum.auto()
    SUBSCRIBED = enum.auto()
    UNSUBSCRIBED = enum.auto()

    @classmethod
    def from_proto(cls, proto: types_pb2.SubscriptionStatus.ValueType) -> Self:
        return cls[types_pb2.SubscriptionStatus.Name(proto)[20:]]

    def to_proto(self) -> types_pb2.SubscriptionStatus.ValueType:
        return getattr(types_pb2.SubscriptionStatus, f"SUBSCRIPTION_STATUS_{self.name}")


class OtcErrorCode(ProtoEnum):
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
        return cls[types_pb2.OtcErrorCode.Name(proto)[15:]]

    def to_proto(self) -> types_pb2.OtcErrorCode.ValueType:
        return getattr(types_pb2.OtcErrorCode, f"OTC_ERROR_CODE_{self.name}")
