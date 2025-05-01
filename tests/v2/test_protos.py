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
        type="string", title="Started", format="date-time", default=0
    )
