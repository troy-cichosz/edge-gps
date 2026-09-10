from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LocationContext:
    latitude: float
    longitude: float
    altitude_m: float | None = None
    quality: int | None = None
    satellites: int | None = None
    hdop: float | None = None
    vdop: float | None = None
    pdop: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SourceContext:
    node_id: str
    service_id: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceContext:
    timestamp: dict
    source: SourceContext
    location: LocationContext | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "source": self.source.to_dict(),
            "location": (
                self.location.to_dict()
                if self.location is not None
                else None
            ),
        }

@dataclass(frozen=True)
class GPSContext:
    timestamp: dict
    location: LocationContext | None
    navigation: dict
    receiver: dict

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "location": (
                self.location.to_dict()
                if self.location is not None
                else None
            ),
            "navigation": self.navigation,
            "receiver": self.receiver,
        }