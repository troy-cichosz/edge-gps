import json
import logging
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

logger = logging.getLogger(__name__)


def _iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


class ObservationServer:
    def __init__(self, service, host: str, port: int):
        self.service = service
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        service = self.service

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                logger.debug("GNSS HTTP: " + fmt, *args)

            def do_GET(self):
                if self.path == "/health":
                    payload = {
                        "status": "ok",
                        "service": "edge-gps",
                        "endpoint": "/observation",
                    }
                    self._send(200, payload)
                    return

                if self.path != "/observation":
                    self._send(404, {"detail": "not found"})
                    return

                state = service.last_state
                now_mono = time.monotonic()

                if state is None or state.gps_time is None:
                    self._send(503, {
                        "source_id": "gnss",
                        "source_type": "gnss",
                        "valid": False,
                        "reason": "no_gnss_time",
                    })
                    return

                fresh = service._nmea_receiving(now_mono)
                acceptable = service._is_acceptable_fix(state)
                valid = bool(fresh and acceptable)

                age_ms = None
                if service.last_nmea_monotonic is not None:
                    age_ms = max(
                        0.0,
                        (now_mono - service.last_nmea_monotonic) * 1000.0,
                    )

                # NMEA UTC from a conventional GPS receiver is normally
                # second-resolution. Until PPS is implemented, treat the
                # GNSS timestamp as having at least +/-500 ms uncertainty.
                uncertainty_ms = 500.0 + (age_ms or 0.0)

                payload = {
                    "source_id": "gnss",
                    "source_type": "gnss",
                    "utc": _iso(state.gps_time),
                    "uncertainty_ms": round(uncertainty_ms, 3),
                    "valid": valid,
                    "observed_monotonic_ns": time.monotonic_ns(),
                    "observed_wall_utc": _iso(datetime.now(timezone.utc)),
                    "details": {
                        "receiver": state.receiver,
                        "received_at_utc": _iso(state.received_at),
                        "nmea_age_ms": round(age_ms, 3) if age_ms is not None else None,
                        "fix": state.fix.__dict__,
                        "pps": False,
                        "valid_fix": acceptable,
                        "nmea_receiving": fresh,
                    },
                }
                self._send(200 if valid else 503, payload)

            def _send(self, status, payload):
                body = json.dumps(payload, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            name="edge-gps-http",
            daemon=True,
        )
        self.thread.start()
        logger.info(
            "GNSS observation API listening on %s:%d",
            self.host,
            self.port,
        )

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
