import os
from dataclasses import dataclass

import yaml


@dataclass
class GPSConfig:
    device: str = "/dev/serial0"
    baudrate: int = 9600
    timeout_seconds: float = 2.0
    update_interval_seconds: float = 1.0
    minimum_satellites: int = 3
    maximum_hdop: float = 10.0
    model: str = "NEO-6M"
    timezone: str = "UTC"
    log_level: str = "INFO"

    @classmethod
    def load(cls, path: str) -> "GPSConfig":
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        gps = data.get("gps", data)

        return cls(
            device=os.environ.get(
                "GPS_DEVICE",
                gps.get("device", cls.device),
            ),
            baudrate=int(
                os.environ.get(
                    "GPS_BAUDRATE",
                    gps.get("baudrate", cls.baudrate),
                )
            ),
            timeout_seconds=float(
                os.environ.get(
                    "GPS_TIMEOUT_SECONDS",
                    gps.get("timeout_seconds", cls.timeout_seconds),
                )
            ),
            update_interval_seconds=float(
                os.environ.get(
                    "GPS_UPDATE_INTERVAL",
                    gps.get(
                        "update_interval_seconds",
                        cls.update_interval_seconds,
                    ),
                )
            ),
            minimum_satellites=int(
                os.environ.get(
                    "GPS_MINIMUM_SATELLITES",
                    gps.get(
                        "minimum_satellites",
                        cls.minimum_satellites,
                    ),
                )
            ),
            maximum_hdop=float(
                os.environ.get(
                    "GPS_MAXIMUM_HDOP",
                    gps.get("maximum_hdop", cls.maximum_hdop),
                )
            ),
            model=os.environ.get(
                "GPS_MODEL",
                gps.get("model", cls.model),
            ),
            timezone=os.environ.get(
                "GPS_TIMEZONE",
                gps.get("timezone", cls.timezone),
            ),
            log_level=os.environ.get(
                "GPS_LOG_LEVEL",
                gps.get("log_level", cls.log_level),
            ),
        )