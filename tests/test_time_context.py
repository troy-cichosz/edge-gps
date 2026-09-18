from datetime import datetime, timezone

import pytest

from app.time_context import TimestampContext


def test_timestamp_context_utc():
    value = datetime(
        2026,
        9,
        9,
        14,
        56,
        29,
        tzinfo=timezone.utc,
    )

    context = TimestampContext.from_datetime(
        value,
        "America/Denver",
    )

    assert context.utc == (
        "2026-09-09T14:56:29+00:00"
    )

    assert context.local == (
        "2026-09-09T08:56:29-06:00"
    )

    assert context.timezone == "America/Denver"
    assert context.utc_offset == "-06:00"


def test_timestamp_context_rejects_naive_datetime():
    value = datetime(
        2026,
        9,
        9,
        14,
        56,
        29,
    )

    with pytest.raises(ValueError):
        TimestampContext.from_datetime(
            value,
            "America/Denver",
        )


def test_timestamp_context_handles_dst():
    value = datetime(
        2026,
        1,
        15,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    context = TimestampContext.from_datetime(
        value,
        "America/Denver",
    )

    assert context.local == (
        "2026-01-15T05:00:00-07:00"
    )

    assert context.utc_offset == "-07:00"

def test_timestamp_context_preserves_utc():
    value = datetime(
        2026,
        9,
        9,
        14,
        56,
        29,
        tzinfo=timezone.utc,
    )

    context = TimestampContext.from_datetime(
        value,
        "America/Denver",
    )

    assert context.utc == "2026-09-09T14:56:29+00:00"
    assert context.local == "2026-09-09T08:56:29-06:00"