"""
reverse_proxy_server.py
=======================
A simulated reverse proxy server with round-robin load balancing,
request logging, and a console management interface.
"""

from __future__ import annotations

import itertools
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("reverse_proxy")


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class HttpMethod(str, Enum):
    GET  = "GET"
    POST = "POST"


class ServerStatus(str, Enum):
    HEALTHY  = "healthy"
    DEGRADED = "degraded"
    DOWN     = "down"


# ---------------------------------------------------------------------------
# ClientRequest
# ---------------------------------------------------------------------------

@dataclass
class ClientRequest:
    """Represents an incoming HTTP request from a client."""

    method:  HttpMethod
    path:    str
    headers: Dict[str, str] = field(default_factory=dict)
    body:    Optional[str]  = None
    request_id: str         = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # ---- validation --------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(self.method, HttpMethod):
            raise ValueError(f"Unsupported HTTP method: {self.method!r}")
        if not self.path.startswith("/"):
            raise ValueError(f"Path must start with '/': {self.path!r}")
        if self.method is HttpMethod.GET and self.body:
            logger.warning("[%s] GET request contains a body — body will be ignored.",
                           self.request_id)
            self.body = None

    # ---- helpers -----------------------------------------------------------

    def summary(self) -> str:
        return f"{self.method.value} {self.path} (id={self.request_id})"


# ---------------------------------------------------------------------------
# BackendResponse  (simple value object)
# ---------------------------------------------------------------------------

@dataclass
class BackendResponse:
    status_code: int
    body:        str
    server_id:   str
    latency_ms:  float


# ---------------------------------------------------------------------------
# BackendServer
# ---------------------------------------------------------------------------

class BackendServer:
    """Represents a single backend server."""

    def __init__(
        self,
        server_id: str,
        address:   str,
        port:      int,
        status:    ServerStatus = ServerStatus.HEALTHY,
        failure_rate: float = 0.05,
    ) -> None:
        if not (0 <= failure_rate <= 1):
            raise ValueError("failure_rate must be between 0 and 1.")
        if not (1 <= port <= 65535):
            raise ValueError(f"Invalid port number: {port}")

        self.server_id    = server_id
        self.address      = address
        self.port         = port
        self.status       = status
        self.failure_rate = failure_rate
        self._request_count: int = 0

    # ---- properties --------------------------------------------------------

    @property
    def is_available(self) -> bool:
        return self.status != ServerStatus.DOWN

    @property
    def request_count(self) -> int:
        return self._request_count

    # ---- core --------------------------------------------------------------

    def handle_request(self, request: ClientRequest) -> BackendResponse:
        """Simulate processing the request and returning a response."""
        if not self.is_available:
            raise RuntimeError(f"Server {self.server_id} is DOWN.")

        self._request_count += 1
        latency = random.uniform(10, 150)          # ms
        time.sleep(latency / 1_000)                # simulate I/O

        if random.random() < self.failure_rate:
            return BackendResponse(
                status_code=500,
                body=json.dumps({"error": "Internal Server Error"}),
                server_id=self.server_id,
                latency_ms=round(latency, 2),
            )

        payload = {
            "server":  self.server_id,
            "method":  request.method.value,
            "path":    request.path,
            "message": "OK",
        }
        if request.body:
            payload["echo"] = request.body

        return BackendResponse(
            status_code=200,
            body=json.dumps(payload),
            server_id=self.server_id,
            latency_ms=round(latency, 2),
        )

    def __repr__(self) -> str:
        return (f"BackendServer(id={self.server_id!r}, "
                f"addr={self.address}:{self.port}, status={self.status.value})")


# ---------------------------------------------------------------------------
# LoadBalancer
# ---------------------------------------------------------------------------

class LoadBalancer:
    """Round-robin load balancer over a pool of BackendServer instances."""

    def __init__(self) -> None:
        self._servers: List[BackendServer] = []
        self._cycle: Optional[itertools.cycle] = None

    # ---- management --------------------------------------------------------

    def add_server(self, server: BackendServer) -> None:
        if any(s.server_id == server.server_id for s in self._servers):
            raise ValueError(f"Server '{server.server_id}' already registered.")
        self._servers.append(server)
        self._rebuild_cycle()
        logger.info("LoadBalancer: added %s", server)

    def remove_server(self, server_id: str) -> None:
        before = len(self._servers)
        self._servers = [s for s in self._servers if s.server_id != server_id]
        if len(self._servers) == before:
            raise KeyError(f"No server with id '{server_id}'.")
        self._rebuild_cycle()
        logger.info("LoadBalancer: removed server '%s'.", server_id)

    def set_status(self, server_id: str, status: ServerStatus) -> None:
        server = self._get(server_id)
        server.status = status
        logger.info("LoadBalancer: server '%s' status → %s", server_id, status.value)

    # ---- selection ---------------------------------------------------------

    def next_server(self) -> BackendServer:
        """Return the next available server (round-robin, skipping DOWN nodes)."""
        available = [s for s in self._servers if s.is_available]
        if not available:
            raise RuntimeError("No backend servers are currently available.")

        # Walk the cycle until we land on an available server.
        for _ in range(len(self._servers) * 2):
            candidate = next(self._cycle)
            if candidate.is_available:
                return candidate

        raise RuntimeError("Could not find an available server in the pool.")

    # ---- helpers -----------------------------------------------------------

    def list_servers(self) -> List[BackendServer]:
        return list(self._servers)

    def _get(self, server_id: str) -> BackendServer:
        for s in self._servers:
            if s.server_id == server_id:
                return s
        raise KeyError(f"Server '{server_id}' not found.")

    def _rebuild_cycle(self) -> None:
        self._cycle = itertools.cycle(self._servers) if self._servers else None


# ---------------------------------------------------------------------------
# RequestLog
# ---------------------------------------------------------------------------

@dataclass
class RequestLog:
    timestamp:   str
    request_id:  str
    method:      str
    path:        str
    server_id:   str
    status_code: int
    latency_ms:  float


# ---------------------------------------------------------------------------
# ProxyManager  (configuration + monitoring)
# ---------------------------------------------------------------------------

class ProxyManager:
    """Manages configuration, logging, and monitoring."""

    def __init__(self, max_log_entries: int = 1_000) -> None:
        self.max_log_entries = max_log_entries
        self._logs: List[RequestLog] = []
        self._total_requests: int = 0
        self._error_requests: int = 0

    # ---- logging -----------------------------------------------------------

    def record(self, request: ClientRequest, response: BackendResponse) -> None:
        self._total_requests += 1
        if response.status_code >= 400:
            self._error_requests += 1

        entry = RequestLog(
            timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            request_id  = request.request_id,
            method      = request.method.value,
            path        = request.path,
            server_id   = response.server_id,
            status_code = response.status_code,
            latency_ms  = response.latency_ms,
        )
        self._logs.append(entry)
        if len(self._logs) > self.max_log_entries:
            self._logs.pop(0)

    # ---- stats -------------------------------------------------------------

    def stats(self) -> Dict:
        if self._total_requests == 0:
            error_rate = 0.0
        else:
            error_rate = self._error_requests / self._total_requests * 100

        return {
            "total_requests": self._total_requests,
            "error_requests": self._error_requests,
            "error_rate_pct": round(error_rate, 2),
        }

    def recent_logs(self, n: int = 10) -> List[RequestLog]:
        return self._logs[-n:]

    def print_stats(self) -> None:
        s = self.stats()
        print("\n── Proxy Statistics ─────────────────────────────")
        print(f"  Total requests : {s['total_requests']}")
        print(f"  Errors         : {s['error_requests']}")
        print(f"  Error rate     : {s['error_rate_pct']}%")
        print("─────────────────────────────────────────────────\n")

    def print_logs(self, n: int = 10) -> None:
        logs = self.recent_logs(n)
        if not logs:
            print("  (no log entries yet)")
            return
        print(f"\n── Last {len(logs)} Request(s) ──────────────────────────")
        for lg in logs:
            print(f"  [{lg.timestamp}] {lg.request_id} "
                  f"{lg.method} {lg.path} → {lg.server_id} "
                  f"HTTP {lg.status_code}  {lg.latency_ms}ms")
        print("─────────────────────────────────────────────────\n")


# ---------------------------------------------------------------------------
# ProxyServer
# ---------------------------------------------------------------------------

class ProxyServer:
    """
    Core reverse proxy: receives ClientRequest objects, picks a backend via
    the LoadBalancer, forwards the request, and returns the BackendResponse.
    """

    def __init__(
        self,
        load_balancer: LoadBalancer,
        proxy_manager: ProxyManager,
        max_retries: int = 2,
    ) -> None:
        self.load_balancer = load_balancer
        self.proxy_manager = proxy_manager
        self.max_retries   = max_retries
        self._running      = False

    # ---- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        self._running = True
        logger.info("ProxyServer started.")

    def stop(self) -> None:
        self._running = False
        logger.info("ProxyServer stopped.")

    # ---- request handling --------------------------------------------------

    def forward(self, request: ClientRequest) -> BackendResponse:
        if not self._running:
            raise RuntimeError("ProxyServer is not running.")

        logger.info("→ Received  %s", request.summary())

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 2):
            try:
                server   = self.load_balancer.next_server()
                response = server.handle_request(request)
                self.proxy_manager.record(request, response)

                logger.info(
                    "← Response  id=%s  server=%s  HTTP %d  %.1fms",
                    request.request_id, server.server_id,
                    response.status_code, response.latency_ms,
                )
                return response

            except RuntimeError as exc:
                last_error = exc
                logger.warning("Attempt %d failed: %s", attempt, exc)

        # All retries exhausted
        fallback = BackendResponse(
            status_code = 503,
            body        = json.dumps({"error": "Service Unavailable"}),
            server_id   = "proxy",
            latency_ms  = 0.0,
        )
        self.proxy_manager.record(request, fallback)
        logger.error("All retries exhausted for %s: %s", request.request_id, last_error)
        return fallback


# ---------------------------------------------------------------------------
# Console UI helpers
# ---------------------------------------------------------------------------

BANNER = r"""
╔══════════════════════════════════════════════════════╗
║           REVERSE PROXY SERVER  (simulator)          ║
╚══════════════════════════════════════════════════════╝
"""

MENU = """
  [1] Send a GET  request
  [2] Send a POST request
  [3] Add a backend server
  [4] Remove a backend server
  [5] Set server status
  [6] List backend servers
  [7] Show recent logs
  [8] Show statistics
  [9] Run demo (10 random requests)
  [0] Quit
"""


def _prompt(msg: str, default: str = "") -> str:
    val = input(msg).strip()
    return val if val else default


def _send_demo_requests(proxy: ProxyServer, n: int = 10) -> None:
    paths   = ["/api/users", "/api/orders", "/health", "/api/data"]
    methods = [HttpMethod.GET, HttpMethod.GET, HttpMethod.GET, HttpMethod.POST]
    bodies  = [None, None, None, '{"item": "widget"}']

    print(f"\n  Sending {n} random requests …\n")
    for _ in range(n):
        idx = random.randrange(len(paths))
        req = ClientRequest(
            method  = methods[idx],
            path    = paths[idx],
            headers = {"Host": "proxy.local"},
            body    = bodies[idx],
        )
        resp = proxy.forward(req)
        status_icon = "✓" if resp.status_code < 400 else "✗"
        print(f"    {status_icon} {req.summary():45s}  HTTP {resp.status_code}  "
              f"via {resp.server_id}  {resp.latency_ms}ms")
    print()


def _add_server_interactive(lb: LoadBalancer) -> None:
    sid  = _prompt("  Server ID   : ", f"backend-{random.randint(10,99)}")
    addr = _prompt("  Address     : ", "127.0.0.1")
    port_str = _prompt("  Port        : ", "8080")

    try:
        port = int(port_str)
        server = BackendServer(server_id=sid, address=addr, port=port)
        lb.add_server(server)
        print(f"  ✓ Added {server}")
    except (ValueError, Exception) as exc:
        print(f"  ✗ Error: {exc}")


def _remove_server_interactive(lb: LoadBalancer) -> None:
    sid = _prompt("  Server ID to remove: ")
    try:
        lb.remove_server(sid)
        print(f"  ✓ Removed '{sid}'.")
    except KeyError as exc:
        print(f"  ✗ {exc}")


def _set_status_interactive(lb: LoadBalancer) -> None:
    sid = _prompt("  Server ID: ")
    print("  Statuses: healthy / degraded / down")
    raw = _prompt("  New status: ", "healthy").lower()
    try:
        status = ServerStatus(raw)
        lb.set_status(sid, status)
        print(f"  ✓ Updated.")
    except (ValueError, KeyError) as exc:
        print(f"  ✗ {exc}")


def _list_servers(lb: LoadBalancer) -> None:
    servers = lb.list_servers()
    if not servers:
        print("  (no servers registered)")
        return
    print()
    for s in servers:
        avail = "✓" if s.is_available else "✗"
        print(f"  {avail}  {s.server_id:15s}  {s.address}:{s.port:<6d}  "
              f"{s.status.value:10s}  requests={s.request_count}")
    print()


def _send_request_interactive(proxy: ProxyServer, method: HttpMethod) -> None:
    path = _prompt(f"  Path [/api/hello]: ", "/api/hello")
    body = None
    if method is HttpMethod.POST:
        raw = _prompt('  Body (JSON) [{"key":"value"}]: ', '{"key":"value"}')
        body = raw

    try:
        req  = ClientRequest(method=method, path=path, headers={"Host": "proxy.local"}, body=body)
        resp = proxy.forward(req)
        print(f"\n  ← HTTP {resp.status_code}  via {resp.server_id}  {resp.latency_ms}ms")
        print(f"     {resp.body}\n")
    except (ValueError, RuntimeError) as exc:
        print(f"  ✗ {exc}")


# ---------------------------------------------------------------------------
# Bootstrap: default backend servers
# ---------------------------------------------------------------------------

def _bootstrap() -> tuple[ProxyServer, LoadBalancer, ProxyManager]:
    lb      = LoadBalancer()
    manager = ProxyManager()
    proxy   = ProxyServer(load_balancer=lb, proxy_manager=manager)

    # Seed with three backend servers
    for idx, port in enumerate([8081, 8082, 8083], start=1):
        lb.add_server(BackendServer(
            server_id = f"backend-{idx}",
            address   = "127.0.0.1",
            port      = port,
        ))

    proxy.start()
    return proxy, lb, manager


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(BANNER)
    proxy, lb, manager = _bootstrap()
    print("  Three backend servers pre-configured (backend-1, backend-2, backend-3).\n")

    while True:
        print(MENU)
        choice = _prompt("  Choice: ", "0")

        if   choice == "1":  _send_request_interactive(proxy, HttpMethod.GET)
        elif choice == "2":  _send_request_interactive(proxy, HttpMethod.POST)
        elif choice == "3":  _add_server_interactive(lb)
        elif choice == "4":  _remove_server_interactive(lb)
        elif choice == "5":  _set_status_interactive(lb)
        elif choice == "6":  _list_servers(lb)
        elif choice == "7":  manager.print_logs()
        elif choice == "8":  manager.print_stats()
        elif choice == "9":  _send_demo_requests(proxy)
        elif choice == "0":
            proxy.stop()
            print("\n  Goodbye!\n")
            break
        else:
            print("  Unknown option — please try again.")


if __name__ == "__main__":
    main()