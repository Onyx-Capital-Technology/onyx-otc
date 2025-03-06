from decimal import Decimal

from .v2 import common_pb2


def to_proto_decimal(value: Decimal) -> common_pb2.Decimal:
    return common_pb2.Decimal(value=str(value))
