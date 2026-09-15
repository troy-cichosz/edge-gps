from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class GPSFix:
    valid: bool = False
    quality: int = 0
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    speed_mps: float | None = None
    course_deg: float | None = None
    satellites: int | None = None
    hdop: float | None = None
    vdop: float | None = None
    pdop: float | None = None


@dataclass
class GPSState:
    received_at: datetime
    gps_time: datetime | None
    fix: GPSFix
    receiver: dict[str, Any]
    raw_sentence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        data["received_at"] = self.received_at.isoformat()

        data["gps_time"] = (
            self.gps_time.isoformat()
            if self.gps_time
            else None
        )

        return data


def utc_now() -> datetime:
    return datetime.now(timezone.utc)