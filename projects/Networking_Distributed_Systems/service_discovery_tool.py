"""
service_discovery_tool.py
=========================
A simulated service-discovery mechanism for distributed systems.
Covers registration, deregistration, health-checking, discovery
by name / status / tag, and an interactive console interface.
"""

from __future__ import annotations

import itertools
import logging
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, Iterator, List, Optional, Set


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("service_discovery")


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ServiceStatus(str, Enum):
    HEALTHY   = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING  = "starting"
    STOPPED   = "stopped"
    UNKNOWN   = "unknown"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

@dataclass
class Service:
    """Represents a single service instance in the registry."""

    name:       str
    address:    str
    port:       int
    tags:       List[str]     = field(default_factory=list)
    status:     ServiceStatus = ServiceStatus.STARTING
    service_id: str           = field(default_factory=lambda: str(uuid.uuid4())[:12])

    # Internals managed by HealthChecker / Registry
    _registered_at:   str   = field(default="", init=False, repr=False)
    _last_checked_at: str   = field(default="", init=False, repr=False)
    _check_count:     int   = field(default=0,  init=False, repr=False)
    _fail_count:      int   = field(default=0,  init=False, repr=False)

    # Simulated health-failure probability (0–1); set externally for realism
    _failure_rate: float = field(default=0.10, init=False, repr=False)

    # ---- validation --------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Service name must not be empty.")
        if not self.address or not self.address.strip():
            raise ValueError("Service address must not be empty.")
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Port must be 1–65535, got {self.port}.")
        self.name    = self.name.strip()
        self.address = self.address.strip()
        self._registered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---- helpers -----------------------------------------------------------

    @property
    def endpoint(self) -> str:
        return f"{self.address}:{self.port}"

    @property
    def check_count(self) -> int:
        return self._check_count

    @property
    def fail_count(self) -> int:
        return self._fail_count

    def matches(self, *, name: Optional[str] = None,
                status: Optional[ServiceStatus] = None,
                tag: Optional[str] = None) -> bool:
        if name   and self.name   != name:            return False
        if status and self.status != status:           return False
        if tag    and tag not in self.tags:            return False
        return True

    def row(self) -> str:
        tags = ",".join(self.tags) if self.tags else "—"
        avail = "✓" if self.status == ServiceStatus.HEALTHY else "✗"
        return (f"  {avail}  {self.service_id:14s}  {self.name:22s}  "
                f"{self.endpoint:22s}  {self.status.value:10s}  "
                f"tags=[{tags}]  checks={self._check_count}  fails={self._fail_count}")

    def __hash__(self) -> int:           # allow use in sets
        return hash(self.service_id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Service) and self.service_id == other.service_id


# ---------------------------------------------------------------------------
# Event log
# ---------------------------------------------------------------------------

@dataclass
class RegistryEvent:
    timestamp:  str
    event_type: str          # registered | deregistered | status_changed | health_check
    service_id: str
    service_name: str
    detail:     str = ""


# ---------------------------------------------------------------------------
# ServiceRegistry
# ---------------------------------------------------------------------------

class ServiceRegistry:
    """Thread-safe in-memory registry of Service instances."""

    def __init__(self) -> None:
        self._services: Dict[str, Service] = {}
        self._lock = threading.RLock()
        self._events: List[RegistryEvent] = []

    # ---- registration ------------------------------------------------------

    def register(self, service: Service) -> None:
        with self._lock:
            if service.service_id in self._services:
                raise ValueError(f"Service '{service.service_id}' already registered.")
            self._services[service.service_id] = service
            service.status = ServiceStatus.HEALTHY
            self._log("registered", service, f"endpoint={service.endpoint}")
            logger.info("Registered  %-22s  %s", service.name, service.service_id)

    def deregister(self, service_id: str) -> Service:
        with self._lock:
            svc = self._services.pop(service_id, None)
            if svc is None:
                raise KeyError(f"No service with id '{service_id}'.")
            svc.status = ServiceStatus.STOPPED
            self._log("deregistered", svc)
            logger.info("Deregistered %-22s  %s", svc.name, svc.service_id)
            return svc

    def update_status(self, service_id: str, status: ServiceStatus, detail: str = "") -> None:
        with self._lock:
            svc = self._get(service_id)
            old = svc.status
            svc.status = status
            svc._last_checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._log("status_changed", svc, f"{old.value} → {status.value}  {detail}")

    # ---- queries -----------------------------------------------------------

    def get(self, service_id: str) -> Service:
        with self._lock:
            return self._get(service_id)

    def all_services(self) -> List[Service]:
        with self._lock:
            return list(self._services.values())

    def find(self, *, name: Optional[str] = None,
             status: Optional[ServiceStatus] = None,
             tag: Optional[str] = None) -> List[Service]:
        with self._lock:
            return [s for s in self._services.values()
                    if s.matches(name=name, status=status, tag=tag)]

    # ---- events ------------------------------------------------------------

    def recent_events(self, n: int = 15) -> List[RegistryEvent]:
        with self._lock:
            return self._events[-n:]

    # ---- internals ---------------------------------------------------------

    def _get(self, service_id: str) -> Service:
        svc = self._services.get(service_id)
        if svc is None:
            raise KeyError(f"No service with id '{service_id}'.")
        return svc

    def _log(self, event_type: str, svc: Service, detail: str = "") -> None:
        self._events.append(RegistryEvent(
            timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type   = event_type,
            service_id   = svc.service_id,
            service_name = svc.name,
            detail       = detail,
        ))
        if len(self._events) > 1_000:
            self._events = self._events[-1_000:]


# ---------------------------------------------------------------------------
# HealthChecker
# ---------------------------------------------------------------------------

class HealthChecker:
    """
    Background thread that periodically simulates health-checks for every
    service in the registry and updates their status accordingly.
    """

    def __init__(
        self,
        registry:        ServiceRegistry,
        interval_secs:   float = 5.0,
        fail_threshold:  int   = 3,      # consecutive fails before UNHEALTHY
    ) -> None:
        if interval_secs <= 0:
            raise ValueError("interval_secs must be positive.")
        self._registry       = registry
        self._interval       = interval_secs
        self._fail_threshold = fail_threshold
        self._consecutive: Dict[str, int] = {}   # service_id → consecutive fail count
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._total_checks: int = 0
        self._total_failures: int = 0

    # ---- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="HealthChecker")
        self._thread.start()
        logger.info("HealthChecker started (interval=%.1fs).", self._interval)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._interval + 1)
        logger.info("HealthChecker stopped.")

    # ---- main loop ---------------------------------------------------------

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval):
            for svc in self._registry.all_services():
                if svc.status == ServiceStatus.STOPPED:
                    continue
                self._check(svc)

    def _check(self, svc: Service) -> None:
        svc._check_count += 1
        self._total_checks += 1

        # Simulate: healthy services occasionally fail
        failed = random.random() < svc._failure_rate

        if failed:
            svc._fail_count += 1
            self._total_failures += 1
            self._consecutive[svc.service_id] = \
                self._consecutive.get(svc.service_id, 0) + 1

            if self._consecutive[svc.service_id] >= self._fail_threshold:
                if svc.status != ServiceStatus.UNHEALTHY:
                    self._registry.update_status(
                        svc.service_id, ServiceStatus.UNHEALTHY,
                        f"consecutive_fails={self._consecutive[svc.service_id]}"
                    )
                    logger.warning("UNHEALTHY  %s  (%s)", svc.name, svc.service_id)
        else:
            self._consecutive[svc.service_id] = 0
            if svc.status in (ServiceStatus.UNHEALTHY, ServiceStatus.STARTING,
                              ServiceStatus.UNKNOWN):
                self._registry.update_status(
                    svc.service_id, ServiceStatus.HEALTHY, "recovered"
                )
                logger.info("RECOVERED  %s  (%s)", svc.name, svc.service_id)

    # ---- stats -------------------------------------------------------------

    def stats(self) -> Dict:
        return {
            "total_checks":   self._total_checks,
            "total_failures": self._total_failures,
            "failure_rate_%": round(
                self._total_failures / self._total_checks * 100, 2
            ) if self._total_checks else 0.0,
        }

    def force_check_all(self) -> None:
        """Run one immediate check cycle (blocking, for console use)."""
        services = self._registry.all_services()
        for svc in services:
            if svc.status != ServiceStatus.STOPPED:
                self._check(svc)
        print(f"  ✓ Health-checked {len(services)} service(s).")


# ---------------------------------------------------------------------------
# DiscoveryAgent
# ---------------------------------------------------------------------------

class DiscoveryAgent:
    """
    Client-facing discovery interface.
    Supports lookup by name, status, tag, and round-robin selection.
    """

    def __init__(self, registry: ServiceRegistry) -> None:
        self._registry = registry
        self._rr_iterators: Dict[str, Iterator[Service]] = {}
        self._rr_state: Dict[str, frozenset] = {}

    # ---- discovery ---------------------------------------------------------

    def discover(
        self,
        name:   Optional[str]           = None,
        status: Optional[ServiceStatus] = None,
        tag:    Optional[str]           = None,
    ) -> List[Service]:
        """Return all matching services."""
        return self._registry.find(name=name, status=status, tag=tag)

    def discover_healthy(self, name: Optional[str] = None,
                         tag: Optional[str] = None) -> List[Service]:
        return self.discover(name=name, status=ServiceStatus.HEALTHY, tag=tag)

    def pick_one(self, name: str, tag: Optional[str] = None) -> Optional[Service]:
        """
        Round-robin selection among healthy instances of `name`.
        The cycle is rebuilt whenever the candidate set changes.
        Returns None if none available.
        """
        candidates = self.discover_healthy(name=name, tag=tag)
        if not candidates:
            return None

        key        = f"{name}:{tag or ''}"
        ids_now    = frozenset(s.service_id for s in candidates)
        prev_ids   = self._rr_state.get(key)

        if prev_ids != ids_now:
            # Candidate set changed — rebuild the iterator
            self._rr_iterators[key] = itertools.cycle(candidates)
            self._rr_state[key]     = ids_now

        return next(self._rr_iterators[key])

    def service_by_id(self, service_id: str) -> Optional[Service]:
        try:
            return self._registry.get(service_id)
        except KeyError:
            return None


# ---------------------------------------------------------------------------
# DiscoveryManager  (façade / orchestrator)
# ---------------------------------------------------------------------------

class DiscoveryManager:
    """
    Top-level façade: wires registry + health-checker + discovery agent,
    and exposes high-level operations used by the console UI.
    """

    def __init__(
        self,
        health_interval: float = 5.0,
        fail_threshold:  int   = 3,
    ) -> None:
        self.registry      = ServiceRegistry()
        self.health_checker = HealthChecker(self.registry, health_interval, fail_threshold)
        self.agent         = DiscoveryAgent(self.registry)

    # ---- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        self.health_checker.start()
        logger.info("DiscoveryManager ready.")

    def stop(self) -> None:
        self.health_checker.stop()

    # ---- registration ------------------------------------------------------

    def register(self, name: str, address: str, port: int,
                 tags: Optional[List[str]] = None,
                 failure_rate: float = 0.08) -> Service:
        svc = Service(name=name, address=address, port=port, tags=tags or [])
        svc._failure_rate = failure_rate
        self.registry.register(svc)
        return svc

    def deregister(self, service_id: str) -> Service:
        return self.registry.deregister(service_id)

    def set_status(self, service_id: str, status: ServiceStatus) -> None:
        self.registry.update_status(service_id, status, "manual")

    # ---- discovery ---------------------------------------------------------

    def discover(self, name: Optional[str] = None,
                 status: Optional[ServiceStatus] = None,
                 tag: Optional[str] = None) -> List[Service]:
        return self.agent.discover(name=name, status=status, tag=tag)

    def pick_one(self, name: str, tag: Optional[str] = None) -> Optional[Service]:
        return self.agent.pick_one(name, tag)

    # ---- monitoring --------------------------------------------------------

    def print_all_services(self) -> None:
        services = self.registry.all_services()
        if not services:
            print("  (registry is empty)")
            return
        print(f"\n── Registry ({len(services)} service(s)) " + "─" * 50)
        for svc in sorted(services, key=lambda s: s.name):
            print(svc.row())
        print("─" * 80 + "\n")

    def print_events(self, n: int = 12) -> None:
        events = self.registry.recent_events(n)
        if not events:
            print("  (no events yet)")
            return
        print(f"\n── Last {len(events)} Event(s) " + "─" * 55)
        icons = {
            "registered":    "➕",
            "deregistered":  "➖",
            "status_changed":"↺ ",
            "health_check":  "♥ ",
        }
        for ev in events:
            icon = icons.get(ev.event_type, "  ")
            print(f"  {icon} [{ev.timestamp}]  {ev.event_type:16s}  "
                  f"{ev.service_name:22s}  {ev.service_id}  {ev.detail}")
        print("─" * 80 + "\n")

    def print_health_stats(self) -> None:
        s = self.health_checker.stats()
        print("\n── Health-Checker Statistics " + "─" * 48)
        print(f"  Total checks   : {s['total_checks']}")
        print(f"  Total failures : {s['total_failures']}")
        print(f"  Failure rate   : {s['failure_rate_%']}%")
        print("─" * 80 + "\n")

    def print_discovery_results(self, results: List[Service], criteria: str) -> None:
        print(f"\n── Discovery results for [{criteria}] ── {len(results)} match(es) " + "─" * 20)
        if not results:
            print("  (no matching services)")
        for svc in results:
            print(svc.row())
        print("─" * 80 + "\n")


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------

BANNER = r"""
╔══════════════════════════════════════════════════════════════════╗
║           SERVICE  DISCOVERY  TOOL  (distributed systems sim)    ║
║     Register · Deregister · Health-Check · Discover              ║
╚══════════════════════════════════════════════════════════════════╝
"""

MENU = """
  ─── Registration ──────────────────────────
  [1] Register a service
  [2] Deregister a service
  [3] Set service status manually

  ─── Discovery ─────────────────────────────
  [4] Discover by name
  [5] Discover by status
  [6] Discover by tag
  [7] Pick one (round-robin)
  [8] Discover all healthy services

  ─── Monitoring ────────────────────────────
  [9] List all services
  [A] View event log
  [B] View health-checker stats
  [C] Force health-check now
  [D] Run demo (populate + simulate)

  [0] Quit
"""


def _p(prompt: str, default: str = "") -> str:
    v = input(prompt).strip()
    return v if v else default


def _register_interactive(mgr: DiscoveryManager) -> None:
    name    = _p("  Service name     : ")
    if not name:
        print("  ✗ Name is required.")
        return
    address = _p("  Address          [127.0.0.1]: ", "127.0.0.1")
    port_s  = _p("  Port             [8080]: ", "8080")
    tags_s  = _p("  Tags (comma-sep) []: ", "")

    try:
        port = int(port_s)
        tags = [t.strip() for t in tags_s.split(",") if t.strip()]
        svc  = mgr.register(name=name, address=address, port=port, tags=tags)
        print(f"  ✓ Registered: id={svc.service_id}  {svc.name}@{svc.endpoint}")
    except (ValueError, Exception) as exc:
        print(f"  ✗ {exc}")


def _deregister_interactive(mgr: DiscoveryManager) -> None:
    sid = _p("  Service ID: ")
    try:
        svc = mgr.deregister(sid)
        print(f"  ✓ Deregistered: {svc.name} ({svc.service_id})")
    except KeyError as exc:
        print(f"  ✗ {exc}")


def _set_status_interactive(mgr: DiscoveryManager) -> None:
    sid = _p("  Service ID: ")
    print(f"  Statuses: {', '.join(s.value for s in ServiceStatus)}")
    raw = _p("  New status: ", "healthy").lower()
    try:
        status = ServiceStatus(raw)
        mgr.set_status(sid, status)
        print(f"  ✓ Status updated → {status.value}")
    except (ValueError, KeyError) as exc:
        print(f"  ✗ {exc}")


def _discover_by_name(mgr: DiscoveryManager) -> None:
    name    = _p("  Service name: ")
    results = mgr.discover(name=name)
    mgr.print_discovery_results(results, f"name={name}")


def _discover_by_status(mgr: DiscoveryManager) -> None:
    print(f"  Statuses: {', '.join(s.value for s in ServiceStatus)}")
    raw = _p("  Status: ", "healthy")
    try:
        status  = ServiceStatus(raw)
        results = mgr.discover(status=status)
        mgr.print_discovery_results(results, f"status={status.value}")
    except ValueError as exc:
        print(f"  ✗ {exc}")


def _discover_by_tag(mgr: DiscoveryManager) -> None:
    tag     = _p("  Tag: ")
    results = mgr.discover(tag=tag)
    mgr.print_discovery_results(results, f"tag={tag}")


def _pick_one(mgr: DiscoveryManager) -> None:
    name = _p("  Service name: ")
    tag  = _p("  Filter by tag (leave blank for none): ", "") or None
    svc  = mgr.pick_one(name, tag=tag)
    if svc:
        print(f"\n  ✓ Selected → {svc.name}  {svc.endpoint}  ({svc.service_id})\n")
    else:
        print(f"  ✗ No healthy instance of '{name}' found.\n")


def _discover_healthy(mgr: DiscoveryManager) -> None:
    results = mgr.discover(status=ServiceStatus.HEALTHY)
    mgr.print_discovery_results(results, "status=healthy")


def _run_demo(mgr: DiscoveryManager) -> None:
    """Populate the registry with realistic services and simulate activity."""
    print("\n  ── Populating registry …")
    services_spec = [
        ("auth-service",      "10.0.1.10", 3001, ["auth", "security"],  0.05),
        ("auth-service",      "10.0.1.11", 3001, ["auth", "security"],  0.12),
        ("user-service",      "10.0.2.10", 4000, ["users", "api"],      0.08),
        ("user-service",      "10.0.2.11", 4000, ["users", "api"],      0.04),
        ("order-service",     "10.0.3.10", 5000, ["orders", "api"],     0.15),
        ("payment-service",   "10.0.4.10", 6000, ["payments", "api"],   0.06),
        ("notification-svc",  "10.0.5.10", 7000, ["notify", "async"],   0.20),
        ("cache-service",     "10.0.6.10", 6379, ["cache", "infra"],    0.02),
    ]
    registered: List[Service] = []
    for name, addr, port, tags, fr in services_spec:
        try:
            svc = mgr.register(name=name, address=addr, port=port,
                               tags=tags, failure_rate=fr)
            registered.append(svc)
            print(f"    ✓  {svc.name:22s}  {svc.endpoint}  [{','.join(tags)}]")
        except Exception as exc:
            print(f"    ✗  {exc}")

    print(f"\n  ── Running health checks …")
    mgr.health_checker.force_check_all()
    time.sleep(0.3)

    print(f"\n  ── Discovery: all healthy 'user-service' instances …")
    results = mgr.discover(name="user-service", status=ServiceStatus.HEALTHY)
    for svc in results:
        print(f"    → {svc.name}  {svc.endpoint}  {svc.status.value}")

    print(f"\n  ── Round-robin picks for 'auth-service' …")
    for _ in range(4):
        svc = mgr.pick_one("auth-service")
        if svc:
            print(f"    → {svc.service_id}  {svc.endpoint}")

    print(f"\n  ── Discovery: all services tagged 'api' …")
    results = mgr.discover(tag="api")
    for svc in results:
        print(f"    → {svc.name:22s}  {svc.endpoint}  {svc.status.value}")

    print(f"\n  ── Simulating one deregistration …")
    if registered:
        target = registered[-1]
        mgr.deregister(target.service_id)
        print(f"    ✓ Deregistered {target.name} ({target.service_id})")

    print(f"\n  Demo complete — {len(mgr.registry.all_services())} services in registry.\n")


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def _bootstrap() -> DiscoveryManager:
    mgr = DiscoveryManager(health_interval=6.0, fail_threshold=3)
    mgr.start()
    return mgr


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(BANNER)
    mgr = _bootstrap()
    print("  Health-checker running every 6 s in the background.\n")

    while True:
        print(MENU)
        choice = _p("  Choice: ", "0").upper()

        if   choice == "1": _register_interactive(mgr)
        elif choice == "2": _deregister_interactive(mgr)
        elif choice == "3": _set_status_interactive(mgr)
        elif choice == "4": _discover_by_name(mgr)
        elif choice == "5": _discover_by_status(mgr)
        elif choice == "6": _discover_by_tag(mgr)
        elif choice == "7": _pick_one(mgr)
        elif choice == "8": _discover_healthy(mgr)
        elif choice == "9": mgr.print_all_services()
        elif choice == "A": mgr.print_events()
        elif choice == "B": mgr.print_health_stats()
        elif choice == "C": mgr.health_checker.force_check_all()
        elif choice == "D": _run_demo(mgr)
        elif choice == "0":
            mgr.stop()
            print("\n  Goodbye!\n")
            break
        else:
            print("  Unknown option — please try again.")


if __name__ == "__main__":
    main()