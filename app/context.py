from __future__ import annotations

from .evidence_context import GPSContext, LocationContext
from .time_context import TimestampContext


def build_gps_context(
    state,
    timezone_name: str,
) -> GPSContext:
    timestamp = None

    if state.gps_time is not None:
        timestamp = TimestampContext.from_datetime(
            state.gps_time,
            timezone_name,
        ).to_dict()

    fix = state.fix

    location = None

    if (
        fix.valid
        and fix.latitude is not None
        and fix.longitude is not None
    ):
        location = LocationContext(
            latitude=fix.latitude,
            longitude=fix.longitude,
            altitude_m=fix.altitude_m,
            quality=fix.quality,
            satellites=fix.satellites,
            hdop=fix.hdop,
            vdop=fix.vdop,
            pdop=fix.pdop,
        )

    return GPSContext(
        timestamp=timestamp,
        location=location,
        navigation={
            "speed_mps": fix.speed_mps,
            "course_deg": fix.course_deg,
        },
        receiver=state.receiver.copy(),
    )