from datetime import datetime, timedelta, timezone

from pydantic import TypeAdapter

from onyx_otc.responses import LiveWebsocket


def test_conversions() -> None:
    now = datetime.now(timezone.utc)
    started = now - timedelta(seconds=1)
    lv = LiveWebsocket(started=started, current_time=now)  # type: ignore[arg-type]
    assert lv.started
    assert lv.started.to_datetime() == started
    assert lv.age == timedelta(seconds=1)
    lv = LiveWebsocket(started=started.isoformat(), current_time=now)  # type: ignore[arg-type]
    assert lv.started
    assert lv.started.to_datetime() == started
    assert lv.age == timedelta(seconds=1)


def test_json_schema() -> None:
    schema = TypeAdapter(LiveWebsocket).json_schema()
    assert schema
    started = schema["properties"]["started"]
    assert started == dict(
        type="string",
        title="Started",
        format="date-time",
        default="1970-01-01T00:00:00Z",
    )


def test_serialize() -> None:
    now = datetime.now(timezone.utc)
    lv = LiveWebsocket(started=now)  # type: ignore[arg-type]
    value = lv.model_dump()
    assert value["started"] == now
    value = lv.model_dump(mode="json")
    assert datetime.fromisoformat(value["started"]) == now
