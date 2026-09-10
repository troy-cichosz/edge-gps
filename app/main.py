import json
import logging
import os
import signal
import sys
import time
from datetime import timezone
from zoneinfo import ZoneInfo
from .time_context import TimestampContext
from .context import build_gps_context

import serial

from .config import GPSConfig
from .controller import ControllerClient
from .nmea import NMEAParser

class GPSService:
    def __init__(self, config: GPSConfig):
        self.config = config
        self.controller = ControllerClient()
        self.parser = NMEAParser(model=config.model)
        self.local_timezone = ZoneInfo(config.timezone)
        self.last_gps_context = None
        self.stop_requested = False
        self.serial_port = None
        self.last_state = None
        self.last_gps_context = None
        self.last_valid_state = None
        self.last_nmea_monotonic = None
        self.last_status_publish = time.monotonic()

    def stop(self, *_args):
        self.stop_requested = True

    def open(self):
        self.serial_port = serial.Serial(
            port=self.config.device,
            baudrate=self.config.baudrate,
            timeout=self.config.timeout_seconds,
        )

        logging.info(
            "Opened GPS device %s at %d baud",
            self.config.device,
            self.config.baudrate,
        )

    def _serial_connected(self) -> bool:
        return (
            self.serial_port is not None
            and self.serial_port.is_open
        )

    def _nmea_receiving(self, now: float) -> bool:
        if self.last_nmea_monotonic is None:
            return False

        timeout = max(
            self.config.update_interval_seconds * 3,
            5.0,
        )

        return (
            now - self.last_nmea_monotonic
        ) <= timeout

    def _timestamp_data(self):
        gps_time = (
            self.last_state.gps_time
            if self.last_state is not None
            else None
        )

        received_at = (
            self.last_state.received_at
            if self.last_state is not None
            else None
        )

        gps_timestamp = (
            TimestampContext.from_datetime(
                gps_time,
                self.config.timezone,
            )
            if gps_time is not None
            else None
        )

        received_timestamp = (
            TimestampContext.from_datetime(
                received_at,
                self.config.timezone,
            )
            if received_at is not None
            else None
        )

        return {
            "gps_time_utc": (
                gps_timestamp.utc
                if gps_timestamp
                else None
            ),
            "gps_time_local": (
                gps_timestamp.local
                if gps_timestamp
                else None
            ),
            "received_at_utc": (
                received_timestamp.utc
                if received_timestamp
                else None
            ),
            "received_at_local": (
                received_timestamp.local
                if received_timestamp
                else None
            ),
            "timezone": self.config.timezone,
            "utc_offset": (
                gps_timestamp.utc_offset
                if gps_timestamp
                else None
            ),
        }
    
    def _publish_status(self, now: float):
        diagnostics = self.parser.diagnostics()

        diagnostics["receiver_connected"] = (
            self._serial_connected()
        )

        diagnostics["nmea_receiving"] = (
            self._nmea_receiving(now)
        )

        if self.last_nmea_monotonic is not None:
            diagnostics["seconds_since_last_nmea"] = round(
                now - self.last_nmea_monotonic,
                3,
            )
        else:
            diagnostics["seconds_since_last_nmea"] = None

        self.controller.update_status(
            "running",
            {
                "state": (
                    self.last_state.to_dict()
                    if self.last_state is not None
                    else None
                ),
                "timestamps": self._timestamp_data(),
                "diagnostics": diagnostics,
            },
        )

        self.last_status_publish = now

    def run(self):
        self.controller.register()

        self.open()

        while not self.stop_requested:
            raw = self.serial_port.readline()

            now = time.monotonic()

            if raw:
                try:
                    sentence = raw.decode(
                        "ascii",
                        errors="ignore",
                    ).strip()

                except Exception:
                    sentence = ""

                if sentence:
                    state = self.parser.feed(sentence)

                    if state is not None:
                        self.last_state = state

                        self.last_gps_context = build_gps_context(
                            state,
                            self.config.timezone,
                        )

                        self.last_nmea_monotonic = now

                        if self._is_acceptable_fix(state):
                            self.last_valid_state = state

                            logging.info(
                                "GPS fix: "
                                "lat=%.7f "
                                "lon=%.7f "
                                "sats=%s "
                                "hdop=%s",
                                state.fix.latitude,
                                state.fix.longitude,
                                state.fix.satellites,
                                state.fix.hdop,
                            )

                        else:
                            logging.debug(
                                "GPS state: %s",
                                json.dumps(
                                    state.to_dict(),
                                    default=str,
                                ),
                            )

            now = time.monotonic()

            if (
                now - self.last_status_publish
                >= self.config.update_interval_seconds
            ):
                self._publish_status(now)

    def _is_acceptable_fix(self, state):
        fix = state.fix

        if (
            not fix.valid
            or fix.latitude is None
            or fix.longitude is None
        ):
            return False

        if (
            fix.satellites is not None
            and fix.satellites
            < self.config.minimum_satellites
        ):
            return False

        if (
            fix.hdop is not None
            and fix.hdop > self.config.maximum_hdop
        ):
            return False

        return True

    def close(self):
        if self.serial_port is not None:
            self.serial_port.close()
            self.serial_port = None


def main() -> int:
    config_path = os.environ.get(
        "GPS_CONFIG",
        "/app/config/gps.yaml",
    )

    config = GPSConfig.load(config_path)

    logging.basicConfig(
        level=getattr(
            logging,
            config.log_level.upper(),
            logging.INFO,
        ),
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s: "
            "%(message)s"
        ),
    )

    service = GPSService(config)

    signal.signal(
        signal.SIGTERM,
        service.stop,
    )

    signal.signal(
        signal.SIGINT,
        service.stop,
    )

    try:
        service.run()

        return 0

    except FileNotFoundError:
        logging.exception(
            "GPS device does not exist: %s",
            config.device,
        )

        return 2

    except serial.SerialException:
        logging.exception(
            "Unable to open/read GPS device: %s",
            config.device,
        )

        return 3

    except Exception:
        logging.exception(
            "edge-gps terminated unexpectedly"
        )

        return 1

    finally:
        service.close()


if __name__ == "__main__":
    sys.exit(main())