from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class TimestampContext:
    """
    Canonical timestamp representation.

    UTC is the authoritative timestamp.
    Local time is a derived convenience representation.
    """

    utc: str
    local: str
    timezone: str
    utc_offset: str

    @classmethod
    def from_datetime(
        cls,
        value: datetime,
        timezone_name: str,
    ) -> "TimestampContext":
        if value.tzinfo is None:
            raise ValueError(
                "Timestamp must be timezone-aware"
            )

        utc_value = value.astimezone(timezone.utc)
        local_zone = ZoneInfo(timezone_name)
        local_value = value.astimezone(local_zone)

        offset = local_value.utcoffset()
        if offset is None:
            raise ValueError(
                "Unable to determine UTC offset"
            )

        total_seconds = int(offset.total_seconds())
        sign = "+" if total_seconds >= 0 else "-"
        total_seconds = abs(total_seconds)

        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60

        utc_offset = f"{sign}{hours:02d}:{minutes:02d}"

        return cls(
            utc=utc_value.isoformat(),
            local=local_value.isoformat(),
            timezone=timezone_name,
            utc_offset=utc_offset,
        )

    def to_dict(self) -> dict:
        return asdict(self)