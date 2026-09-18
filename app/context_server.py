from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class GPSContextServer:
    def __init__(self, service, host: str, port: int):
        self.service = service

        service_ref = service

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/context":
                    self.send_response(404)
                    self.end_headers()
                    return

                context = service_ref.last_gps_context

                if context is None:
                    self.send_response(503)
                    self.send_header(
                        "Content-Type",
                        "application/json",
                    )
                    self.end_headers()

                    self.wfile.write(
                        json.dumps(
                            {
                                "status": "unavailable",
                                "reason": "no_gps_context",
                            }
                        ).encode("utf-8")
                    )

                    return

                body = json.dumps(
                    context.to_dict(),
                    separators=(",", ":"),
                ).encode("utf-8")

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/json",
                )
                self.send_header(
                    "Content-Length",
                    str(len(body)),
                )
                self.end_headers()

                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        self.server = ThreadingHTTPServer(
            (host, port),
            Handler,
        )

    def start(self):
        import threading

        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()