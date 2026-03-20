"""
service_manager.py
A simulated system service manager built with Python OOP.
Supports register, start, stop, restart, status, and audit-log operations.
"""

from __future__ import annotations

import random
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional


# ══════════════════════════════════════════════════════════════
# Enums & Exceptions
# ══════════════════════════════════════════════════════════════

class ServiceStatus(Enum):
    RUNNING  = "running"
    STOPPED  = "stopped"
    FAILED   = "failed"
    STARTING = "starting"
    STOPPING = "stopping"


class ServiceError(Exception):
    """Base exception for all service-manager errors."""


class ServiceNotFoundError(ServiceError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Service '{name}' is not registered.")


class ServiceAlreadyExistsError(ServiceError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Service '{name}' is already registered.")


class ServiceStateError(ServiceError):
    """Raised when an operation is invalid for the current service state."""


class ValidationError(ServiceError):
    """Raised on bad user input."""


# ══════════════════════════════════════════════════════════════
# ANSI helpers  (colour / formatting)
# ══════════════════════════════════════════════════════════════

def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"

def _ok  (msg: str) -> None: print(_c(f"  ✔  {msg}", "32"))
def _err (msg: str) -> None: print(_c(f"  ✘  {msg}", "31"))
def _info(msg: str) -> None: print(_c(f"  ℹ  {msg}", "36"))
def _warn(msg: str) -> None: print(_c(f"  ⚠  {msg}", "33"))
def _head(msg: str) -> None: print(_c(msg, "1;34"))

def _status_tag(status: ServiceStatus) -> str:
    colours = {
        ServiceStatus.RUNNING : "32",   # green
        ServiceStatus.STOPPED : "33",   # yellow
        ServiceStatus.FAILED  : "31",   # red
        ServiceStatus.STARTING: "36",   # cyan
        ServiceStatus.STOPPING: "36",
    }
    return _c(f"[{status.value.upper():8}]", colours.get(status, "0"))


# ══════════════════════════════════════════════════════════════
# LogEntry  (immutable audit record)
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LogEntry:
    timestamp: datetime
    service_name: str
    action: str
    detail: str

    def __str__(self) -> str:
        ts  = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        svc = f"{self.service_name:<22}"
        return f"  {ts}  {svc}  [{self.action:<9}]  {self.detail}"


# ══════════════════════════════════════════════════════════════
# Service
# ══════════════════════════════════════════════════════════════

class Service:
    """Represents a single manageable service daemon."""

    _VALID_CHARS = frozenset(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789-_."
    )

    def __init__(
        self,
        service_name: str,
        description: str = "",
        auto_restart: bool = False,
    ) -> None:
        self._validate_name(service_name)
        self.service_name: str          = service_name
        self.description:  str          = description or f"Service '{service_name}'"
        self.auto_restart: bool         = auto_restart
        self.status:       ServiceStatus = ServiceStatus.STOPPED
        self.process_id:   Optional[int] = None
        self.start_time:   Optional[datetime] = None
        self._restart_count: int        = 0

    # ── validation ──────────────────────────────────────────
    @classmethod
    def _validate_name(cls, name: str) -> None:
        if not name:
            raise ValidationError("Service name cannot be empty.")
        if len(name) > 64:
            raise ValidationError("Service name must be ≤ 64 characters.")
        bad = set(name) - cls._VALID_CHARS
        if bad:
            raise ValidationError(
                f"Service name contains invalid characters: {bad}. "
                "Use letters, digits, hyphens, underscores, or dots."
            )

    # ── computed properties ──────────────────────────────────
    @property
    def uptime(self) -> Optional[timedelta]:
        if self.status == ServiceStatus.RUNNING and self.start_time:
            return datetime.now() - self.start_time
        return None

    @property
    def uptime_str(self) -> str:
        td = self.uptime
        if td is None:
            return "—"
        total = int(td.total_seconds())
        h, rem = divmod(total, 3600)
        m, s   = divmod(rem, 60)
        return f"{h:02d}h {m:02d}m {s:02d}s"

    @property
    def restart_count(self) -> int:
        return self._restart_count

    # ── state transitions (called by ServiceController) ─────
    def _do_start(self) -> None:
        self.process_id = random.randint(1000, 99999)
        self.start_time = datetime.now()
        self.status     = ServiceStatus.RUNNING

    def _do_stop(self) -> None:
        self.process_id = None
        self.start_time = None
        self.status     = ServiceStatus.STOPPED

    def _do_fail(self) -> None:
        self.process_id = None
        self.start_time = None
        self.status     = ServiceStatus.FAILED

    def _inc_restart(self) -> None:
        self._restart_count += 1

    # ── display ──────────────────────────────────────────────
    def status_line(self) -> str:
        pid  = str(self.process_id) if self.process_id else "—"
        tag  = _status_tag(self.status)
        ar   = _c("AUTO-RESTART", "35") if self.auto_restart else ""
        return (
            f"  {tag}  {self.service_name:<22}  PID:{pid:<7}"
            f"  uptime:{self.uptime_str:<14}  {ar}"
        )

    def detail_block(self) -> str:
        st = self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else "—"
        return textwrap.dedent(f"""\
            Name         : {self.service_name}
            Description  : {self.description}
            Status       : {self.status.value.upper()}
            PID          : {self.process_id or '—'}
            Started at   : {st}
            Uptime       : {self.uptime_str}
            Auto-restart : {'yes' if self.auto_restart else 'no'}
            Restarts     : {self._restart_count}
        """)

    def __repr__(self) -> str:
        return f"Service(name={self.service_name!r}, status={self.status.name})"


# ══════════════════════════════════════════════════════════════
# ServiceRegistry
# ══════════════════════════════════════════════════════════════

class ServiceRegistry:
    """Stores and manages the catalogue of known services."""

    def __init__(self) -> None:
        self._services: Dict[str, Service] = {}

    # ── mutations ────────────────────────────────────────────
    def register(self, service: Service) -> None:
        if service.service_name in self._services:
            raise ServiceAlreadyExistsError(service.service_name)
        self._services[service.service_name] = service

    def deregister(self, name: str) -> Service:
        svc = self.get(name)
        if svc.status == ServiceStatus.RUNNING:
            raise ServiceStateError(
                f"Cannot deregister running service '{name}'. Stop it first."
            )
        del self._services[name]
        return svc

    # ── queries ──────────────────────────────────────────────
    def get(self, name: str) -> Service:
        if name not in self._services:
            raise ServiceNotFoundError(name)
        return self._services[name]

    def exists(self, name: str) -> bool:
        return name in self._services

    def all_services(self) -> List[Service]:
        return sorted(self._services.values(), key=lambda s: s.service_name)

    def by_status(self, status: ServiceStatus) -> List[Service]:
        return [s for s in self._services.values() if s.status == status]

    def search(self, query: str) -> List[Service]:
        q = query.lower()
        return [
            s for s in self._services.values()
            if q in s.service_name.lower() or q in s.description.lower()
        ]

    def __len__(self) -> int:
        return len(self._services)


# ══════════════════════════════════════════════════════════════
# ServiceController
# ══════════════════════════════════════════════════════════════

class ServiceController:
    """
    Low-level controller: executes start / stop / restart transitions
    and validates that the requested operation is legal for the current state.
    Does NOT touch the registry or the log — the ServiceManager owns those.
    """

    # ── start ────────────────────────────────────────────────
    def start(self, service: Service) -> None:
        if service.status == ServiceStatus.RUNNING:
            raise ServiceStateError(
                f"Service '{service.service_name}' is already running "
                f"(PID {service.process_id})."
            )
        if service.status == ServiceStatus.STARTING:
            raise ServiceStateError(
                f"Service '{service.service_name}' is already starting."
            )
        service.status = ServiceStatus.STARTING
        # Simulate occasional start failure (5 % chance) for realism
        if random.random() < 0.05:
            service._do_fail()
            raise ServiceStateError(
                f"Service '{service.service_name}' failed to start."
            )
        service._do_start()

    # ── stop ─────────────────────────────────────────────────
    def stop(self, service: Service) -> None:
        if service.status in (ServiceStatus.STOPPED, ServiceStatus.FAILED):
            raise ServiceStateError(
                f"Service '{service.service_name}' is not running."
            )
        if service.status == ServiceStatus.STOPPING:
            raise ServiceStateError(
                f"Service '{service.service_name}' is already stopping."
            )
        service.status = ServiceStatus.STOPPING
        service._do_stop()

    # ── restart ──────────────────────────────────────────────
    def restart(self, service: Service) -> None:
        was_running = service.status == ServiceStatus.RUNNING
        if was_running:
            service.status = ServiceStatus.STOPPING
            service._do_stop()
        service._inc_restart()
        service.status = ServiceStatus.STARTING
        if random.random() < 0.04:          # 4 % failure on restart
            service._do_fail()
            raise ServiceStateError(
                f"Service '{service.service_name}' failed to restart."
            )
        service._do_start()

    # ── reload (sends SIGHUP equivalent) ────────────────────
    def reload(self, service: Service) -> None:
        if service.status != ServiceStatus.RUNNING:
            raise ServiceStateError(
                f"Cannot reload '{service.service_name}': not running."
            )
        # Reload keeps the PID but resets the simulated config timestamp
        service.start_time = datetime.now()   # pretend config reloaded


# ══════════════════════════════════════════════════════════════
# ServiceManager  (top-level coordinator)
# ══════════════════════════════════════════════════════════════

class ServiceManager:
    """
    Coordinates registry, controller, and audit log.
    Every user-facing operation goes through this class.
    """

    def __init__(self) -> None:
        self._registry   = ServiceRegistry()
        self._controller = ServiceController()
        self._log: List[LogEntry] = []

    # ── audit log ────────────────────────────────────────────
    def _record(self, service_name: str, action: str, detail: str) -> None:
        self._log.append(
            LogEntry(
                timestamp    = datetime.now(),
                service_name = service_name,
                action       = action,
                detail       = detail,
            )
        )

    # ── register / deregister ────────────────────────────────
    def register_service(
        self,
        name: str,
        description: str = "",
        auto_restart: bool = False,
    ) -> Service:
        svc = Service(name, description, auto_restart)
        self._registry.register(svc)
        self._record(name, "REGISTER", f"Registered — auto_restart={auto_restart}")
        return svc

    def deregister_service(self, name: str) -> None:
        svc = self._registry.deregister(name)
        self._record(name, "DEREGISTER", "Removed from registry")

    # ── lifecycle ────────────────────────────────────────────
    def start_service(self, name: str) -> Service:
        svc = self._registry.get(name)
        self._controller.start(svc)
        self._record(name, "START", f"Started — PID {svc.process_id}")
        return svc

    def stop_service(self, name: str) -> Service:
        svc = self._registry.get(name)
        self._controller.stop(svc)
        self._record(name, "STOP", "Stopped cleanly")
        return svc

    def restart_service(self, name: str) -> Service:
        svc = self._registry.get(name)
        self._controller.restart(svc)
        self._record(name, "RESTART",
                     f"Restarted (×{svc.restart_count}) — PID {svc.process_id}")
        return svc

    def reload_service(self, name: str) -> Service:
        svc = self._registry.get(name)
        self._controller.reload(svc)
        self._record(name, "RELOAD", "Configuration reloaded")
        return svc

    # ── queries ──────────────────────────────────────────────
    def status(self, name: str) -> Service:
        return self._registry.get(name)

    def list_services(self) -> List[Service]:
        return self._registry.all_services()

    def search_services(self, query: str) -> List[Service]:
        return self._registry.search(query)

    def get_log(self, limit: int = 50) -> List[LogEntry]:
        return self._log[-limit:]

    def running_count(self) -> int:
        return len(self._registry.by_status(ServiceStatus.RUNNING))

    def total_count(self) -> int:
        return len(self._registry)


# ══════════════════════════════════════════════════════════════
# Seed data
# ══════════════════════════════════════════════════════════════

def _seed(manager: ServiceManager) -> None:
    services = [
        ("nginx",        "NGINX HTTP & reverse-proxy server",          True),
        ("postgresql",   "PostgreSQL 15 relational database",           True),
        ("redis",        "Redis in-memory cache / message broker",      True),
        ("celery-worker","Celery asynchronous task worker",             True),
        ("celery-beat",  "Celery periodic task scheduler",              False),
        ("gunicorn",     "Gunicorn WSGI application server",            True),
        ("prometheus",   "Prometheus metrics collection daemon",        False),
        ("grafana",      "Grafana observability dashboard",             False),
        ("ssh",          "OpenSSH secure shell daemon",                 True),
        ("cron",         "System cron job scheduler",                   True),
        ("elasticsearch","Elasticsearch search & analytics engine",     True),
        ("logstash",     "Logstash log-processing pipeline",            False),
    ]
    for name, desc, ar in services:
        manager.register_service(name, desc, ar)

    # Pre-start a handful so the demo looks alive
    for name in ("nginx", "postgresql", "redis", "ssh", "cron", "gunicorn"):
        try:
            manager.start_service(name)
        except ServiceStateError:
            pass   # swallow simulated start-failure in seed


# ══════════════════════════════════════════════════════════════
# CLI  (menu-driven interface)
# ══════════════════════════════════════════════════════════════

BANNER = textwrap.dedent("""\
    ╔══════════════════════════════════════════════════════╗
    ║           service_manager  v1.0  (simulated)         ║
    ║      A Python OOP system service control console     ║
    ╚══════════════════════════════════════════════════════╝
""")

MENU = textwrap.dedent("""\
    {head}
      1.  List all services
      2.  Start a service
      3.  Stop a service
      4.  Restart a service
      5.  Reload a service (config refresh)
      6.  Show service status / details
      7.  Search services
      8.  Register a new service
      9.  Deregister a service
     10.  View audit log
     11.  Dashboard summary
      0.  Exit
""")


def _prompt(label: str, allow_empty: bool = False) -> str:
    while True:
        val = input(_c(f"  {label}: ", "1;33")).strip()
        if val or allow_empty:
            return val
        _warn("Input cannot be empty.")


def _confirm(question: str) -> bool:
    ans = input(_c(f"  {question} [y/N] ", "1;31")).strip().lower()
    return ans in ("y", "yes")


# ── individual screens ────────────────────────────────────────

def screen_list(mgr: ServiceManager) -> None:
    services = mgr.list_services()
    _head(f"\n  All Services ({len(services)} registered, {mgr.running_count()} running)\n")
    print("  " + "─" * 72)
    if not services:
        _info("No services registered.")
    else:
        for svc in services:
            print(svc.status_line())
    print()


def screen_start(mgr: ServiceManager) -> None:
    name = _prompt("Service name to START")
    try:
        svc = mgr.start_service(name)
        _ok(f"'{svc.service_name}' is now running  (PID {svc.process_id})")
    except (ServiceNotFoundError, ServiceStateError) as e:
        _err(str(e))


def screen_stop(mgr: ServiceManager) -> None:
    name = _prompt("Service name to STOP")
    try:
        svc = mgr.stop_service(name)
        _ok(f"'{svc.service_name}' has been stopped.")
    except (ServiceNotFoundError, ServiceStateError) as e:
        _err(str(e))


def screen_restart(mgr: ServiceManager) -> None:
    name = _prompt("Service name to RESTART")
    try:
        svc = mgr.restart_service(name)
        _ok(f"'{svc.service_name}' restarted successfully  (PID {svc.process_id})")
    except (ServiceNotFoundError, ServiceStateError) as e:
        _err(str(e))


def screen_reload(mgr: ServiceManager) -> None:
    name = _prompt("Service name to RELOAD")
    try:
        mgr.reload_service(name)
        _ok(f"'{name}' configuration reloaded.")
    except (ServiceNotFoundError, ServiceStateError) as e:
        _err(str(e))


def screen_status(mgr: ServiceManager) -> None:
    name = _prompt("Service name")
    try:
        svc = mgr.status(name)
        _head(f"\n  ── Service details: {svc.service_name} ──\n")
        for line in svc.detail_block().splitlines():
            print(f"    {line}")
        print()
    except ServiceNotFoundError as e:
        _err(str(e))


def screen_search(mgr: ServiceManager) -> None:
    query = _prompt("Search query")
    results = mgr.search_services(query)
    _head(f"\n  Search results for '{query}'  ({len(results)} found)\n")
    print("  " + "─" * 72)
    if not results:
        _info("No matching services found.")
    else:
        for svc in results:
            print(svc.status_line())
    print()


def screen_register(mgr: ServiceManager) -> None:
    _head("\n  ── Register New Service ──\n")
    name = _prompt("Service name")
    desc = _prompt("Description (optional)", allow_empty=True) or ""
    ar   = _confirm("Enable auto-restart?")
    try:
        svc = mgr.register_service(name, desc, ar)
        _ok(f"Service '{svc.service_name}' registered successfully.")
        if _confirm("Start it now?"):
            try:
                mgr.start_service(svc.service_name)
                _ok(f"'{svc.service_name}' started  (PID {svc.process_id})")
            except ServiceStateError as e:
                _err(str(e))
    except (ServiceAlreadyExistsError, ValidationError) as e:
        _err(str(e))


def screen_deregister(mgr: ServiceManager) -> None:
    name = _prompt("Service name to DEREGISTER")
    if not _confirm(f"Permanently remove '{name}' from the registry?"):
        _info("Cancelled.")
        return
    try:
        mgr.deregister_service(name)
        _ok(f"Service '{name}' deregistered.")
    except (ServiceNotFoundError, ServiceStateError) as e:
        _err(str(e))


def screen_log(mgr: ServiceManager) -> None:
    _head("\n  ── Audit Log (last 30 entries) ──\n")
    print("  " + "─" * 72)
    entries = mgr.get_log(30)
    if not entries:
        _info("No log entries yet.")
    else:
        for entry in reversed(entries):
            print(str(entry))
    print()


def screen_dashboard(mgr: ServiceManager) -> None:
    services = mgr.list_services()
    running  = [s for s in services if s.status == ServiceStatus.RUNNING]
    stopped  = [s for s in services if s.status == ServiceStatus.STOPPED]
    failed   = [s for s in services if s.status == ServiceStatus.FAILED]

    _head("\n  ╔══════════ Dashboard ═══════════╗\n")
    print(f"    Total registered :  {len(services)}")
    print(_c(f"    Running          :  {len(running)}", "32"))
    print(_c(f"    Stopped          :  {len(stopped)}", "33"))
    print(_c(f"    Failed           :  {len(failed)}",  "31"))

    if running:
        _head("\n  Running services:")
        for svc in running:
            print(f"    • {svc.service_name:<22} PID {svc.process_id}  uptime {svc.uptime_str}")

    if failed:
        _head("\n  Failed services (need attention):")
        for svc in failed:
            print(_c(f"    ✘ {svc.service_name}", "31"))
    print()


# ── main loop ────────────────────────────────────────────────

SCREENS = {
    "1" : screen_list,
    "2" : screen_start,
    "3" : screen_stop,
    "4" : screen_restart,
    "5" : screen_reload,
    "6" : screen_status,
    "7" : screen_search,
    "8" : screen_register,
    "9" : screen_deregister,
    "10": screen_log,
    "11": screen_dashboard,
}


def main() -> None:
    print(_c(BANNER, "1;36"))
    manager = ServiceManager()
    _seed(manager)
    _info(f"Loaded {manager.total_count()} services  "
          f"({manager.running_count()} already running).")

    while True:
        print(MENU.format(head=_c("  Main Menu", "1;34")))
        try:
            choice = input(_c("  Choose an option: ", "1;32")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            _info("Exiting service manager.  Goodbye!")
            break

        if choice == "0":
            _info("Exiting service manager.  Goodbye!")
            break

        handler = SCREENS.get(choice)
        if handler:
            handler(manager)
        else:
            _warn(f"Unknown option '{choice}'.  Enter a number from 0–11.")


if __name__ == "__main__":
    main()