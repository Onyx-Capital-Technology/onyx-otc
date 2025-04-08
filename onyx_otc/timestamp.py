from __future__ import annotations

import time
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Self

from google.protobuf import timestamp_pb2
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

NANOS_PER_MICROS = 1000
NANOS_PER_MILLIS = 1000 * NANOS_PER_MICROS
NANOS_PER_SECOND = 1000 * NANOS_PER_MILLIS
ZERO = Decimal()
ONE = Decimal(1)


class Timestamp(int):
    """An UTC timestamp with converstion to and from proto"""

    @property
    def nanos(self) -> int:
        """timestamp as nanoseconds"""
        return self

    @property
    def micros(self) -> int:
        """timestamp as microseconds"""
        return self // NANOS_PER_MICROS

    @property
    def millis(self) -> int:
        """timestamp as milliseconds"""
        return self // NANOS_PER_MILLIS

    @property
    def seconds(self) -> int:
        """timestamp as seconds"""
        return self // NANOS_PER_SECOND

    @property
    def total_seconds(self) -> float:
        return self / NANOS_PER_SECOND

    @property
    def total_millis(self) -> float:
        return self / NANOS_PER_MILLIS

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(int))

    @classmethod
    def utcnow(cls) -> Self:
        return cls(time.time_ns())

    @classmethod
    def utcnow_plus_millis(cls, millis: int) -> Self:
        return cls(time.time_ns() + millis * NANOS_PER_MILLIS)

    @classmethod
    def from_micros(cls, micros: int) -> Self:
        return cls(micros * NANOS_PER_MICROS)

    @classmethod
    def from_millis(cls, millis: int | float) -> Self:
        return cls(millis * NANOS_PER_MILLIS)

    @classmethod
    def from_seconds(cls, seconds: float, nanos: int = 0) -> Self:
        return cls(seconds * NANOS_PER_SECOND + nanos)

    @classmethod
    def from_datetime(cls, dte: date | None) -> Self:
        if dte is None:
            return cls(0)
        elif not isinstance(dte, datetime):
            dte = datetime.combine(dte, datetime.min.time())
        return cls(int(dte.timestamp() * NANOS_PER_SECOND))

    @classmethod
    def from_datetime_or_none(cls, dte: date | None) -> Self | None:
        if dte is None:
            return None
        return cls.from_datetime(dte)

    @classmethod
    def from_iso_string(cls, dte: str) -> Self:
        return cls.from_datetime(datetime.fromisoformat(dte))

    @classmethod
    def from_proto(cls, timestamp: timestamp_pb2.Timestamp) -> Self:
        return cls(NANOS_PER_SECOND * timestamp.seconds + timestamp.nanos)

    def to_proto(self) -> timestamp_pb2.Timestamp:
        return timestamp_pb2.Timestamp(
            seconds=self // NANOS_PER_SECOND,
            nanos=self % NANOS_PER_SECOND,
        )

    def to_datetime(self, tzinfo: timezone | None = timezone.utc) -> datetime:
        return datetime.fromtimestamp(self.total_seconds, tz=tzinfo)
