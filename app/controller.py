import json
import logging
import os
import platform
import socket
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


class ControllerClient:
    def __init__(self):
        self.base_url = os.environ.get("EDGE_CONTROLLER_URL", "").rstrip("/")
        self.timeout = int(os.environ.get("EDGE_CONTROLLER_TIMEOUT", "5"))
        self.node_id = os.environ.get("EDGE_NODE_ID") or socket.gethostname()
        self.service_id = os.environ.get("EDGE_SERVICE_ID", "edge-gps")
        self.service_name = os.environ.get("EDGE_SERVICE_NAME", "edge-gps")
        self.service_version = os.environ.get("EDGE_SERVICE_VERSION", "0.1.0")

    def _request(self, method: str, path: str, payload=None):
        if not self.base_url:
            return None
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else None

    def register(self) -> bool:
        if not self.base_url:
            logger.info("EDGE_CONTROLLER_URL is not configured; controller registration disabled")
            return False
        try:
            self._register_node()
            self._register_service()
            logger.info("Registered %s with edge-controller", self.service_id)
            return True
        except Exception as exc:
            logger.warning("Controller registration failed: %s", exc)
            return False

    def _register_node(self):
        try:
            self._request("GET", f"/api/v1/nodes/{self.node_id}")
            return
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
        self._request(
            "POST",
            "/api/v1/nodes",
            {
                "node_id": self.node_id,
                "hostname": socket.gethostname(),
                "platform": f"{platform.system().lower()}-{platform.machine()}",
            },
        )
        logger.info("Registered node: %s", self.node_id)

    def _register_service(self):
        services = self._request("GET", f"/api/v1/nodes/{self.node_id}/services") or []
        for service in services:
            if service.get("service_id") == self.service_id:
                return
        self._request(
            "POST",
            f"/api/v1/nodes/{self.node_id}/services",
            {
                "service_id": self.service_id,
                "name": self.service_name,
                "version": self.service_version,
            },
        )
        logger.info("Registered service: %s version=%s", self.service_id, self.service_version)

    def get_configuration(self) -> dict:
        try:
            response = self._request(
                "GET",
                f"/api/v1/nodes/{self.node_id}/services/{self.service_id}/configuration",
            )
            return (response or {}).get("configuration", {})
        except Exception as exc:
            logger.warning("Controller configuration unavailable: %s", exc)
            return {}

    def update_status(self, status: str, data: dict) -> bool:
        if not self.base_url:
            return False

        try:
            self._request(
                "PUT",
                f"/api/v1/nodes/{self.node_id}/services/{self.service_id}/status",
                {
                    "status": status,
                    "data": data,
                },
            )
            return True
        except Exception as exc:
            logger.warning("Controller status update failed: %s", exc)
            return False