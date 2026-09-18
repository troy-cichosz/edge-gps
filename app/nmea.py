import math
from datetime import datetime, timezone
from typing import Any

from .models import GPSFix, GPSState, utc_now


KNOTS_TO_MPS = 0.5144444444444444


def _float(value: str | None) -> float | None:
    if value in (None, ""):
        return None

    try:
        return float(value)
    except ValueError:
        return None


def _int(value: str | None) -> int | None:
    if value in (None, ""):
        return None

    try:
        return int(value)
    except ValueError:
        return None


def _checksum_valid(sentence: str) -> bool:
    if not sentence.startswith("$") or "*" not in sentence:
        return False

    body, checksum = sentence[1:].split("*", 1)

    if len(checksum) < 2:
        return False

    try:
        expected = int(checksum[:2], 16)
    except ValueError:
        return False

    actual = 0

    for char in body:
        actual ^= ord(char)

    return actual == expected


def _coord(
    value: str,
    hemisphere: str,
    degree_digits: int,
) -> float | None:
    if not value or len(value) <= degree_digits:
        return None

    try:
        degrees = float(value[:degree_digits])
        minutes = float(value[degree_digits:])
        result = degrees + minutes / 60.0
    except ValueError:
        return None

    if hemisphere in ("S", "W"):
        result = -result

    return result


def _utc_datetime(
    hhmmss: str,
    date_ddmmyy: str | None = None,
    fallback_date: datetime | None = None,
) -> datetime | None:
    if not hhmmss:
        return None

    try:
        raw = hhmmss.split(".", 1)

        whole = raw[0].ljust(6, "0")[:6]

        hour = int(whole[:2])
        minute = int(whole[2:4])
        second = int(whole[4:6])

        microsecond = (
            int((raw[1] + "000000")[:6])
            if len(raw) == 2
            else 0
        )

        if date_ddmmyy:
            day = int(date_ddmmyy[:2])
            month = int(date_ddmmyy[2:4])
            year = int(date_ddmmyy[4:6])

            year += 2000 if year < 80 else 1900

            return datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
                microsecond,
                tzinfo=timezone.utc,
            )

        if fallback_date:
            return datetime(
                fallback_date.year,
                fallback_date.month,
                fallback_date.day,
                hour,
                minute,
                second,
                microsecond,
                tzinfo=timezone.utc,
            )

        return None

    except (ValueError, IndexError):
        return None


class NMEAParser:
    """Small dependency-free parser for the NMEA messages used by the NEO-6M."""

    def __init__(self, model: str = "NEO-6M"):
        self.model = model

        self.fix = GPSFix()

        self.gps_time: datetime | None = None
        self.gps_date: datetime | None = None
        self.last_sentence: str | None = None
        self.last_message_type: str | None = None
        self.last_message_received_at: datetime | None = None

        self.message_count = 0
        self.valid_checksum_count = 0
        self.invalid_checksum_count = 0

        self.gsv_total_messages: int | None = None
        self.gsv_message_number = 0
        self.gsv_satellites_in_view: int | None = None

    def feed(self, sentence: str) -> GPSState | None:
        sentence = sentence.strip()

        if not sentence.startswith("$"):
            return None

        self.message_count += 1

        if not _checksum_valid(sentence):
            self.invalid_checksum_count += 1
            return None

        self.valid_checksum_count += 1

        self.last_sentence = sentence

        body = sentence[1:].split("*", 1)[0]
        fields = body.split(",")

        if not fields:
            return None

        message_type = fields[0][-3:]

        self.last_message_type = message_type

        if message_type == "GGA":
            self._gga(fields)

        elif message_type == "RMC":
            self._rmc(fields)

        elif message_type == "GSA":
            self._gsa(fields)

        elif message_type == "GSV":
            self._gsv(fields)

        else:
            return None

        self.last_message_received_at = utc_now()

        return GPSState(
            received_at=self.last_message_received_at,
            gps_time=self.gps_time,
            fix=self.fix,
            receiver={
                "model": self.model,
                "protocol": "NMEA",
            },
            raw_sentence=sentence,
        )

    def _gga(self, f: list[str]) -> None:
        # GGA:
        # time, lat, N/S, lon, E/W, quality, sats,
        # HDOP, altitude, ...

        self.gps_time = _utc_datetime(
            f[1],
            fallback_date=self.gps_date,
        )

        self.fix.latitude = _coord(
            f[2],
            f[3],
            2,
        )

        self.fix.longitude = _coord(
            f[4],
            f[5],
            3,
        )

        self.fix.quality = _int(f[6]) or 0

        self.fix.valid = self.fix.quality > 0

        self.fix.satellites = _int(f[7])

        self.fix.hdop = _float(f[8])

        self.fix.altitude_m = _float(f[9])

    def _rmc(self, f: list[str]) -> None:
        # RMC:
        # time, status, lat, N/S, lon, E/W,
        # speed knots, course, date, ...

        self.gps_time = _utc_datetime(
            f[1],
            f[9],
        )

        if self.gps_time is not None:
            self.gps_date = self.gps_time

        self.fix.valid = f[2] == "A"

        self.fix.latitude = _coord(
            f[3],
            f[4],
            2,
        )

        self.fix.longitude = _coord(
            f[5],
            f[6],
            3,
        )

        speed_knots = _float(f[7])

        self.fix.speed_mps = (
            speed_knots * KNOTS_TO_MPS
            if speed_knots is not None
            else None
        )

        self.fix.course_deg = _float(f[8])

    def _gsa(self, f: list[str]) -> None:
        self.fix.pdop = (
            _float(f[15])
            if len(f) > 15
            else None
        )

        self.fix.hdop = (
            _float(f[16])
            if len(f) > 16
            else self.fix.hdop
        )

        self.fix.vdop = (
            _float(f[17].split("*", 1)[0])
            if len(f) > 17
            else None
        )

    def _gsv(self, f: list[str]) -> None:
        self.gsv_total_messages = _int(f[1])

        self.gsv_message_number = _int(f[2]) or 0

        self.gsv_satellites_in_view = _int(f[3])

    def diagnostics(self) -> dict[str, Any]:
        return {
            "messages_received": self.message_count,
            "valid_checksums": self.valid_checksum_count,
            "invalid_checksums": self.invalid_checksum_count,
            "last_message_type": self.last_message_type,
            "last_message_received_at": (
                self.last_message_received_at.isoformat()
                if self.last_message_received_at
                else None
            ),
            "satellites_in_view": self.gsv_satellites_in_view,
            "fix": self.fix.valid,
            "quality": self.fix.quality,
            "hdop": self.fix.hdop,
        }