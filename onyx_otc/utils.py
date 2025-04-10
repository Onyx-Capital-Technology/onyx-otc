from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from .v2 import common_pb2


def to_proto_decimal(value: Decimal) -> common_pb2.Decimal:
    return common_pb2.Decimal(value=str(value))


def isoformat(dt: datetime, **kwargs: Any) -> str:
    if dt.tzinfo is timezone.utc:
        return dt.replace(tzinfo=None).isoformat(**kwargs) + "Z"
    else:
        return dt.isoformat(**kwargs)
