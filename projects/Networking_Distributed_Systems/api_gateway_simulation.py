"""
api_gateway_simulation.py
=========================
A simulated API Gateway with authentication, rate limiting, endpoint routing,
structured logging, and an interactive console management interface.
"""

from __future__ import annotations

import json
import logging
import random
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Deque, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("api_gateway")


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class HttpMethod(str, Enum):
    GET    = "GET"
    POST   = "POST"
    PUT    = "PUT"
    DELETE = "DELETE"


class ServiceStatus(str, Enum):
    ONLINE      = "online"
    DEGRADED    = "degraded"
    OFFLINE     = "offline"


class GatewayResponseCode(int, Enum):
    OK                  = 200
    CREATED             = 201
    BAD_REQUEST         = 400
    UNAUTHORIZED        = 401
    FORBIDDEN           = 403
    NOT_FOUND           = 404
    TOO_MANY_REQUESTS   = 429
    INTERNAL_ERROR      = 500
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT     = 504


# ---------------------------------------------------------------------------
# Registered API keys (auth store)
# ---------------------------------------------------------------------------

_VALID_API_KEYS: Dict[str, str] = {
    "key-alpha-001":   "client-alpha",
    "key-beta-002":    "client-beta",
    "key-gamma-003":   "client-gamma",
    "key-demo-999":    "demo-user",
}


# ---------------------------------------------------------------------------
# APIRequest
# ---------------------------------------------------------------------------

@dataclass
class APIRequest:
    """Represents an incoming client request to the gateway."""

    method:    HttpMethod
    endpoint:  str                          # e.g. "/users/42"
    headers:   Dict[str, str] = field(default_factory=dict)
    body:      Optional[str]  = None
    client_id: str            = "anonymous"
    request_id: str           = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp:  str           = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    # ---- validation --------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(self.method, HttpMethod):
            raise ValueError(f"Unsupported HTTP method: {self.method!r}")
        if not self.endpoint.startswith("/"):
            raise ValueError(f"Endpoint must start with '/': {self.endpoint!r}")
        if self.method is HttpMethod.GET and self.body:
            logger.debug("[%s] GET body ignored.", self.request_id)
            self.body = None

    # ---- helpers -----------------------------------------------------------

    @property
    def api_key(self) -> Optional[str]:
        return self.headers.get("X-API-Key") or self.headers.get("x-api-key")

    def summary(self) -> str:
        return f"{self.method.value} {self.endpoint} (id={self.request_id}, client={self.client_id})"


# ---------------------------------------------------------------------------
# GatewayResponse
# ---------------------------------------------------------------------------

@dataclass
class GatewayResponse:
    code:        GatewayResponseCode
    body:        Dict
    service:     str = "gateway"
    latency_ms:  float = 0.0
    request_id:  str   = ""

    def ok(self) -> bool:
        return self.code.value < 400

    def to_dict(self) -> Dict:
        return {
            "status":      self.code.value,
            "service":     self.service,
            "latency_ms":  self.latency_ms,
            "request_id":  self.request_id,
            "body":        self.body,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class Service:
    """Represents a backend micro-service."""

    def __init__(
        self,
        service_name: str,
        base_url:     str,
        status:       ServiceStatus = ServiceStatus.ONLINE,
        failure_rate: float = 0.04,
        latency_range: Tuple[float, float] = (10.0, 120.0),
    ) -> None:
        if not (0.0 <= failure_rate <= 1.0):
            raise ValueError("failure_rate must be in [0, 1].")
        self.service_name  = service_name
        self.base_url      = base_url
        self.status        = status
        self.failure_rate  = failure_rate
        self.latency_range = latency_range
        self._req_count: int = 0
        self._err_count: int = 0

    # ---- properties --------------------------------------------------------

    @property
    def is_available(self) -> bool:
        return self.status != ServiceStatus.OFFLINE

    @property
    def request_count(self) -> int:
        return self._req_count

    @property
    def error_count(self) -> int:
        return self._err_count

    # ---- core --------------------------------------------------------------

    def call(self, request: APIRequest, path: str) -> GatewayResponse:
        if not self.is_available:
            return GatewayResponse(
                code=GatewayResponseCode.SERVICE_UNAVAILABLE,
                body={"error": f"Service '{self.service_name}' is offline."},
                service=self.service_name,
                request_id=request.request_id,
            )

        self._req_count += 1
        lo, hi = self.latency_range
        latency = random.uniform(lo, hi)

        # Simulate degraded slowness
        if self.status is ServiceStatus.DEGRADED:
            latency *= 3.0

        time.sleep(latency / 1_000)

        if random.random() < self.failure_rate:
            self._err_count += 1
            return GatewayResponse(
                code=GatewayResponseCode.INTERNAL_ERROR,
                body={"error": "Upstream service error."},
                service=self.service_name,
                latency_ms=round(latency, 2),
                request_id=request.request_id,
            )

        # Build a plausible mock response
        payload = self._mock_payload(request.method, path, request.body)
        code    = GatewayResponseCode.CREATED if request.method is HttpMethod.POST else GatewayResponseCode.OK

        return GatewayResponse(
            code=code,
            body=payload,
            service=self.service_name,
            latency_ms=round(latency, 2),
            request_id=request.request_id,
        )

    # ---- mock payload factory ----------------------------------------------

    def _mock_payload(self, method: HttpMethod, path: str, body: Optional[str]) -> Dict:
        base = {
            "service": self.service_name,
            "path":    path,
            "method":  method.value,
        }
        if method is HttpMethod.GET:
            base["data"] = {"id": random.randint(1, 999), "status": "active"}
        elif method is HttpMethod.POST:
            base["created"] = True
            if body:
                try:
                    base["received"] = json.loads(body)
                except json.JSONDecodeError:
                    base["received"] = body
        elif method is HttpMethod.PUT:
            base["updated"] = True
        elif method is HttpMethod.DELETE:
            base["deleted"] = True
        return base

    def __repr__(self) -> str:
        return (f"Service(name={self.service_name!r}, url={self.base_url}, "
                f"status={self.status.value})")


# ---------------------------------------------------------------------------
# RateLimiter  —  sliding-window per client
# ---------------------------------------------------------------------------

class RateLimiter:
    """
    Sliding-window rate limiter.
    Each client is allowed `max_requests` per `window_seconds`.
    """

    def __init__(self, max_requests: int = 10, window_seconds: float = 60.0) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be >= 1.")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive.")
        self.max_requests    = max_requests
        self.window_seconds  = window_seconds
        self._timestamps: Dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        Returns (allowed, remaining_quota).
        Mutates internal state — call once per request.
        """
        now    = time.monotonic()
        window = self._timestamps[client_id]

        # Evict timestamps outside the window
        while window and window[0] < now - self.window_seconds:
            window.popleft()

        if len(window) >= self.max_requests:
            return False, 0

        window.append(now)
        return True, self.max_requests - len(window)

    def reset(self, client_id: str) -> None:
        self._timestamps.pop(client_id, None)

    def client_usage(self, client_id: str) -> Dict:
        now    = time.monotonic()
        window = self._timestamps[client_id]
        recent = sum(1 for t in window if t >= now - self.window_seconds)
        return {
            "client_id":   client_id,
            "used":        recent,
            "limit":       self.max_requests,
            "window_secs": self.window_seconds,
        }


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

@dataclass
class RouteRule:
    prefix:       str           # e.g. "/users"
    service_name: str
    allowed_methods: List[HttpMethod] = field(default_factory=lambda: list(HttpMethod))


class Router:
    """Maps endpoint prefixes to named services."""

    def __init__(self) -> None:
        self._rules: List[RouteRule] = []

    def add_route(self, prefix: str, service_name: str,
                  allowed_methods: Optional[List[HttpMethod]] = None) -> None:
        if not prefix.startswith("/"):
            raise ValueError(f"Route prefix must start with '/': {prefix!r}")
        methods = allowed_methods or list(HttpMethod)
        self._rules.append(RouteRule(prefix=prefix, service_name=service_name,
                                     allowed_methods=methods))
        # Keep longest-prefix first for specificity matching
        self._rules.sort(key=lambda r: len(r.prefix), reverse=True)
        logger.info("Router: %s → service='%s'", prefix, service_name)

    def resolve(self, endpoint: str, method: HttpMethod) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns (service_name, sub_path) or (None, reason).
        """
        for rule in self._rules:
            if endpoint == rule.prefix or endpoint.startswith(rule.prefix + "/") or endpoint.startswith(rule.prefix + "?"):
                if method not in rule.allowed_methods:
                    return None, f"Method {method.value} not allowed on {rule.prefix}"
                sub_path = endpoint[len(rule.prefix):] or "/"
                return rule.service_name, sub_path
        return None, f"No route found for '{endpoint}'"

    def list_routes(self) -> List[RouteRule]:
        return list(self._rules)


# ---------------------------------------------------------------------------
# Authenticator
# ---------------------------------------------------------------------------

class Authenticator:
    """Validates API keys and resolves client identities."""

    def __init__(self, api_keys: Optional[Dict[str, str]] = None) -> None:
        self._keys: Dict[str, str] = dict(api_keys or _VALID_API_KEYS)

    def authenticate(self, request: APIRequest) -> Tuple[bool, str]:
        """Returns (is_valid, client_id_or_reason)."""
        key = request.api_key
        if not key:
            return False, "Missing X-API-Key header"
        client = self._keys.get(key)
        if client is None:
            return False, "Invalid API key"
        return True, client

    def register_key(self, api_key: str, client_id: str) -> None:
        self._keys[api_key] = client_id
        logger.info("Auth: registered key for client '%s'.", client_id)

    def revoke_key(self, api_key: str) -> None:
        if api_key in self._keys:
            self._keys.pop(api_key)
            logger.info("Auth: revoked key '%s'.", api_key)


# ---------------------------------------------------------------------------
# RequestLog
# ---------------------------------------------------------------------------

@dataclass
class RequestLog:
    timestamp:   str
    request_id:  str
    client_id:   str
    method:      str
    endpoint:    str
    service:     str
    status_code: int
    latency_ms:  float
    note:        str = ""


# ---------------------------------------------------------------------------
# GatewayManager
# ---------------------------------------------------------------------------

class GatewayManager:
    """Manages services, request logs, and monitoring metrics."""

    def __init__(self, max_logs: int = 500) -> None:
        self._services: Dict[str, Service] = {}
        self._logs: List[RequestLog] = []
        self._max_logs = max_logs
        self._total: int = 0
        self._errors: int = 0
        self._rate_limited: int = 0

    # ---- service registry --------------------------------------------------

    def register(self, service: Service) -> None:
        self._services[service.service_name] = service
        logger.info("Manager: registered service '%s'.", service.service_name)

    def deregister(self, name: str) -> None:
        if name not in self._services:
            raise KeyError(f"Service '{name}' not found.")
        del self._services[name]
        logger.info("Manager: deregistered service '%s'.", name)

    def get_service(self, name: str) -> Optional[Service]:
        return self._services.get(name)

    def set_service_status(self, name: str, status: ServiceStatus) -> None:
        svc = self._services.get(name)
        if svc is None:
            raise KeyError(f"Service '{name}' not found.")
        svc.status = status
        logger.info("Manager: service '%s' → %s", name, status.value)

    def list_services(self) -> List[Service]:
        return list(self._services.values())

    # ---- logging -----------------------------------------------------------

    def log(self, request: APIRequest, response: GatewayResponse, note: str = "") -> None:
        self._total += 1
        if response.code.value >= 500:
            self._errors += 1
        if response.code == GatewayResponseCode.TOO_MANY_REQUESTS:
            self._rate_limited += 1

        entry = RequestLog(
            timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            request_id  = request.request_id,
            client_id   = request.client_id,
            method      = request.method.value,
            endpoint    = request.endpoint,
            service     = response.service,
            status_code = response.code.value,
            latency_ms  = response.latency_ms,
            note        = note,
        )
        self._logs.append(entry)
        if len(self._logs) > self._max_logs:
            self._logs.pop(0)

    # ---- reporting ---------------------------------------------------------

    def recent_logs(self, n: int = 10) -> List[RequestLog]:
        return self._logs[-n:]

    def stats(self) -> Dict:
        er = round(self._errors / self._total * 100, 2) if self._total else 0.0
        return {
            "total":        self._total,
            "errors":       self._errors,
            "rate_limited": self._rate_limited,
            "error_rate_%": er,
        }

    def print_logs(self, n: int = 10) -> None:
        logs = self.recent_logs(n)
        if not logs:
            print("  (no logs yet)")
            return
        print(f"\n── Last {len(logs)} Request(s) ──────────────────────────────────────")
        for lg in logs:
            icon = "✓" if lg.status_code < 400 else "✗"
            note = f"  [{lg.note}]" if lg.note else ""
            print(f"  {icon} [{lg.timestamp}] {lg.request_id}  "
                  f"{lg.client_id:14s}  {lg.method:6s} {lg.endpoint:25s} "
                  f"→ {lg.service:16s}  HTTP {lg.status_code}  {lg.latency_ms}ms{note}")
        print("────────────────────────────────────────────────────────────────\n")

    def print_stats(self) -> None:
        s = self.stats()
        print("\n── Gateway Statistics ───────────────────────────────────────────")
        print(f"  Total requests : {s['total']}")
        print(f"  Errors (5xx)   : {s['errors']}")
        print(f"  Rate-limited   : {s['rate_limited']}")
        print(f"  Error rate     : {s['error_rate_%']}%")
        print("────────────────────────────────────────────────────────────────\n")

    def print_services(self) -> None:
        svcs = self.list_services()
        if not svcs:
            print("  (no services registered)")
            return
        print("\n── Registered Services ──────────────────────────────────────────")
        for s in svcs:
            avail = "✓" if s.is_available else "✗"
            print(f"  {avail}  {s.service_name:20s}  {s.base_url:30s}  "
                  f"{s.status.value:10s}  reqs={s.request_count}  errs={s.error_count}")
        print("────────────────────────────────────────────────────────────────\n")


# ---------------------------------------------------------------------------
# APIGateway
# ---------------------------------------------------------------------------

class APIGateway:
    """
    Central gateway: authenticates → rate-limits → routes → calls service.
    """

    def __init__(
        self,
        router:        Router,
        rate_limiter:  RateLimiter,
        authenticator: Authenticator,
        manager:       GatewayManager,
        require_auth:  bool = True,
    ) -> None:
        self.router        = router
        self.rate_limiter  = rate_limiter
        self.authenticator = authenticator
        self.manager       = manager
        self.require_auth  = require_auth
        self._running      = False

    # ---- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        self._running = True
        logger.info("APIGateway started.")

    def stop(self) -> None:
        self._running = False
        logger.info("APIGateway stopped.")

    # ---- pipeline ----------------------------------------------------------

    def handle(self, request: APIRequest) -> GatewayResponse:
        if not self._running:
            return self._error(request, GatewayResponseCode.SERVICE_UNAVAILABLE,
                               "Gateway is not running.", "gateway-down")

        logger.info("→ %s", request.summary())
        t0 = time.monotonic()

        # 1. Authentication
        if self.require_auth:
            ok, identity = self.authenticator.authenticate(request)
            if not ok:
                resp = self._error(request, GatewayResponseCode.UNAUTHORIZED, identity, "auth-failed")
                self.manager.log(request, resp, note="auth-failed")
                return resp
            request.client_id = identity

        # 2. Rate limiting
        allowed, remaining = self.rate_limiter.is_allowed(request.client_id)
        if not allowed:
            resp = self._error(request, GatewayResponseCode.TOO_MANY_REQUESTS,
                               "Rate limit exceeded.", "rate-limited")
            self.manager.log(request, resp, note="rate-limited")
            logger.warning("Rate-limited: client='%s'", request.client_id)
            return resp

        # 3. Route resolution
        service_name, detail = self.router.resolve(request.endpoint, request.method)
        if service_name is None:
            resp = self._error(request, GatewayResponseCode.NOT_FOUND, detail, "no-route")
            self.manager.log(request, resp, note="no-route")
            return resp

        logger.info("  ↪ Routing to service='%s'  (remaining quota=%d)", service_name, remaining)

        # 4. Service lookup
        service = self.manager.get_service(service_name)
        if service is None:
            resp = self._error(request, GatewayResponseCode.BAD_REQUEST,
                               f"Service '{service_name}' not registered.", "no-service")
            self.manager.log(request, resp, note="no-service")
            return resp

        # 5. Forward to service
        sub_path = detail  # router returns sub_path in detail on success
        response = service.call(request, sub_path)
        elapsed  = round((time.monotonic() - t0) * 1_000, 2)

        logger.info(
            "← HTTP %d  service=%s  latency=%.1fms",
            response.code.value, service_name, elapsed,
        )
        self.manager.log(request, response)
        return response

    # ---- helpers -----------------------------------------------------------

    @staticmethod
    def _error(request: APIRequest, code: GatewayResponseCode,
               message: str, stage: str) -> GatewayResponse:
        return GatewayResponse(
            code=code,
            body={"error": message, "stage": stage},
            service="gateway",
            latency_ms=0.0,
            request_id=request.request_id,
        )


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║              API  GATEWAY  SIMULATION                        ║
║    Auth · Rate-Limiting · Routing · Monitoring               ║
╚══════════════════════════════════════════════════════════════╝
"""

MENU = """
  ─── Requests ──────────────────────────
  [1] Send a GET  request
  [2] Send a POST request
  [3] Send a PUT  request
  [4] Send a DELETE request
  [5] Run demo (15 mixed requests)

  ─── Configuration ─────────────────────
  [6] List services
  [7] Set service status
  [8] List routes
  [9] Add a route

  ─── Monitoring ────────────────────────
  [A] Show recent logs
  [B] Show statistics
  [C] Show rate-limiter usage

  [0] Quit
"""

_DEMO_API_KEYS = list(_VALID_API_KEYS.keys())


def _p(prompt: str, default: str = "") -> str:
    val = input(prompt).strip()
    return val if val else default


def _pick_method(raw: str) -> Optional[HttpMethod]:
    try:
        return HttpMethod(raw.upper())
    except ValueError:
        return None


def _send_interactive(gateway: APIGateway, method: HttpMethod) -> None:
    endpoint = _p(f"  Endpoint [/users]: ", "/users")
    api_key  = _p("  API key  [key-demo-999]: ", "key-demo-999")
    body     = None
    if method in (HttpMethod.POST, HttpMethod.PUT):
        body = _p('  Body JSON [{"name":"test"}]: ', '{"name":"test"}')

    try:
        req  = APIRequest(method=method, endpoint=endpoint,
                          headers={"X-API-Key": api_key})
        resp = gateway.handle(req)
        icon = "✓" if resp.ok() else "✗"
        print(f"\n  {icon} HTTP {resp.code.value}  service={resp.service}  {resp.latency_ms}ms")
        print(f"  {json.dumps(resp.body, indent=4)}\n")
    except ValueError as exc:
        print(f"  ✗ Validation error: {exc}\n")


def _run_demo(gateway: APIGateway) -> None:
    scenarios = [
        # (method, endpoint, api_key, body)
        (HttpMethod.GET,    "/users",           "key-alpha-001", None),
        (HttpMethod.GET,    "/users/42",         "key-beta-002",  None),
        (HttpMethod.POST,   "/users",            "key-alpha-001", '{"name":"Alice"}'),
        (HttpMethod.GET,    "/products",         "key-gamma-003", None),
        (HttpMethod.GET,    "/products/7",       "key-demo-999",  None),
        (HttpMethod.POST,   "/orders",           "key-beta-002",  '{"product_id":7,"qty":2}'),
        (HttpMethod.GET,    "/orders/100",       "key-alpha-001", None),
        (HttpMethod.DELETE, "/users/5",          "key-gamma-003", None),
        (HttpMethod.PUT,    "/products/3",       "key-demo-999",  '{"price":29.99}'),
        (HttpMethod.GET,    "/unknown/path",     "key-alpha-001", None),   # 404
        (HttpMethod.GET,    "/users",            "bad-key-!!!",   None),   # 401
        (HttpMethod.GET,    "/users",            "key-alpha-001", None),   # normal
        (HttpMethod.POST,   "/orders",           "key-beta-002",  '{"product_id":1}'),
        (HttpMethod.GET,    "/products",         "key-gamma-003", None),
        (HttpMethod.DELETE, "/orders/99",        "key-demo-999",  None),
    ]
    print(f"\n  Running {len(scenarios)} demo requests …\n")
    for method, endpoint, key, body in scenarios:
        req  = APIRequest(method=method, endpoint=endpoint,
                          headers={"X-API-Key": key}, body=body)
        resp = gateway.handle(req)
        icon = "✓" if resp.ok() else "✗"
        print(f"  {icon}  {req.request_id}  {method.value:6s} {endpoint:25s} "
              f"HTTP {resp.code.value:3d}  via {resp.service:18s}  {resp.latency_ms}ms")
        time.sleep(0.05)
    print()


def _set_status_interactive(manager: GatewayManager) -> None:
    name = _p("  Service name: ")
    print("  Statuses: online / degraded / offline")
    raw  = _p("  New status: ", "online").lower()
    try:
        status = ServiceStatus(raw)
        manager.set_service_status(name, status)
        print(f"  ✓ {name} → {status.value}")
    except (ValueError, KeyError) as exc:
        print(f"  ✗ {exc}")


def _list_routes(router: Router) -> None:
    rules = router.list_routes()
    if not rules:
        print("  (no routes configured)")
        return
    print("\n── Routes ───────────────────────────────────────────────────────")
    for r in rules:
        methods = ", ".join(m.value for m in r.allowed_methods)
        print(f"  {r.prefix:30s} → {r.service_name:20s}  [{methods}]")
    print("────────────────────────────────────────────────────────────────\n")


def _add_route_interactive(router: Router) -> None:
    prefix  = _p("  Prefix (e.g. /newpath): ")
    service = _p("  Target service name   : ")
    try:
        router.add_route(prefix, service)
        print(f"  ✓ Route {prefix} → {service} added.")
    except ValueError as exc:
        print(f"  ✗ {exc}")


def _show_rate_usage(rate_limiter: RateLimiter) -> None:
    clients = [
        "client-alpha", "client-beta", "client-gamma", "demo-user", "anonymous"
    ]
    print("\n── Rate Limiter State ───────────────────────────────────────────")
    for cid in clients:
        u = rate_limiter.client_usage(cid)
        bar_filled = "█" * u["used"]
        bar_empty  = "░" * (u["limit"] - u["used"])
        print(f"  {cid:16s}  {bar_filled}{bar_empty}  {u['used']}/{u['limit']}")
    print("────────────────────────────────────────────────────────────────\n")


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def _bootstrap() -> Tuple[APIGateway, Router, RateLimiter, GatewayManager]:
    # --- services ---
    manager = GatewayManager()
    for name, url in [
        ("user-service",    "http://internal/users"),
        ("product-service", "http://internal/products"),
        ("order-service",   "http://internal/orders"),
    ]:
        manager.register(Service(service_name=name, base_url=url))

    # --- router ---
    router = Router()
    router.add_route("/users",    "user-service",    list(HttpMethod))
    router.add_route("/products", "product-service", list(HttpMethod))
    router.add_route("/orders",   "order-service",   list(HttpMethod))

    # --- rate limiter: 20 requests / 60 seconds ---
    rate_limiter = RateLimiter(max_requests=20, window_seconds=60.0)

    # --- authenticator ---
    auth = Authenticator()

    # --- gateway ---
    gateway = APIGateway(
        router=router,
        rate_limiter=rate_limiter,
        authenticator=auth,
        manager=manager,
        require_auth=True,
    )
    gateway.start()
    return gateway, router, rate_limiter, manager


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(BANNER)
    gateway, router, rate_limiter, manager = _bootstrap()
    print("\n  Services : user-service, product-service, order-service")
    print("  Routes   : /users  /products  /orders")
    print("  API keys : key-alpha-001, key-beta-002, key-gamma-003, key-demo-999\n")

    while True:
        print(MENU)
        choice = _p("  Choice: ", "0").upper()

        if   choice == "1": _send_interactive(gateway, HttpMethod.GET)
        elif choice == "2": _send_interactive(gateway, HttpMethod.POST)
        elif choice == "3": _send_interactive(gateway, HttpMethod.PUT)
        elif choice == "4": _send_interactive(gateway, HttpMethod.DELETE)
        elif choice == "5": _run_demo(gateway)
        elif choice == "6": manager.print_services()
        elif choice == "7": _set_status_interactive(manager)
        elif choice == "8": _list_routes(router)
        elif choice == "9": _add_route_interactive(router)
        elif choice == "A": manager.print_logs()
        elif choice == "B": manager.print_stats()
        elif choice == "C": _show_rate_usage(rate_limiter)
        elif choice == "0":
            gateway.stop()
            print("\n  Goodbye!\n")
            break
        else:
            print("  Unknown option — please try again.")


if __name__ == "__main__":
    main()