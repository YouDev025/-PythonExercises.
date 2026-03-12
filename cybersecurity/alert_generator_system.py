"""
Alert Generator System
======================
Simulates a real-world alert pipeline: conditions are evaluated,
alerts are created and tracked through their lifecycle (active →
acknowledged → resolved), and a full audit history is maintained.

Architecture
────────────
  Alert            – encapsulated alert entity with lifecycle methods
  AlertCondition   – rule/condition that can trigger an Alert
  AlertGenerator   – evaluates conditions and mints new Alerts
  AlertManager     – stores alerts, owns business operations
  CLI              – interactive menu loop
"""

from __future__ import annotations

import random
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Enums
# ─────────────────────────────────────────────────────────────────────────────

class Severity(Enum):
    INFO     = 1
    LOW      = 2
    MEDIUM   = 3
    HIGH     = 4
    CRITICAL = 5

    def label(self) -> str:
        colours = {
            "INFO":     "\033[96m",   # cyan
            "LOW":      "\033[92m",   # green
            "MEDIUM":   "\033[93m",   # yellow
            "HIGH":     "\033[91m",   # red
            "CRITICAL": "\033[95m",   # magenta
        }
        return f"{colours[self.name]}{self.name}\033[0m"


class AlertStatus(Enum):
    ACTIVE       = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED     = "RESOLVED"


# ─────────────────────────────────────────────────────────────────────────────
#  Alert  – core entity with encapsulated state
# ─────────────────────────────────────────────────────────────────────────────

class Alert:
    """
    Represents a single alert event.

    All attributes are private; external code uses the read-only
    properties and the lifecycle methods (acknowledge, resolve).
    State transitions are enforced: ACTIVE → ACKNOWLEDGED → RESOLVED.
    """

    _VALID_TRANSITIONS: dict[AlertStatus, set[AlertStatus]] = {
        AlertStatus.ACTIVE:       {AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED},
        AlertStatus.ACKNOWLEDGED: {AlertStatus.RESOLVED},
        AlertStatus.RESOLVED:     set(),
    }

    def __init__(
        self,
        message:       str,
        severity:      Severity,
        source:        str = "system",
        category:      str = "general",
    ) -> None:
        if not message.strip():
            raise ValueError("Alert message cannot be empty.")

        self._alert_id:    str         = str(uuid.uuid4())[:8].upper()
        self._message:     str         = message.strip()
        self._severity:    Severity    = severity
        self._source:      str         = source
        self._category:    str         = category
        self._status:      AlertStatus = AlertStatus.ACTIVE
        self._timestamp:   datetime    = datetime.now()
        self._resolved_at: Optional[datetime] = None
        self._ack_at:      Optional[datetime] = None
        self._notes:       list[str]   = []

    # ── read-only properties ──────────────────────────────────────────
    @property
    def alert_id(self)    -> str:           return self._alert_id
    @property
    def message(self)     -> str:           return self._message
    @property
    def severity(self)    -> Severity:      return self._severity
    @property
    def source(self)      -> str:           return self._source
    @property
    def category(self)    -> str:           return self._category
    @property
    def status(self)      -> AlertStatus:   return self._status
    @property
    def timestamp(self)   -> datetime:      return self._timestamp
    @property
    def resolved_at(self) -> Optional[datetime]: return self._resolved_at
    @property
    def ack_at(self)      -> Optional[datetime]: return self._ack_at
    @property
    def notes(self)       -> list[str]:     return list(self._notes)

    # ── lifecycle methods ─────────────────────────────────────────────

    def acknowledge(self, note: str = "") -> None:
        """Move ACTIVE → ACKNOWLEDGED."""
        self._transition_to(AlertStatus.ACKNOWLEDGED)
        self._ack_at = datetime.now()
        if note:
            self._notes.append(f"[ACK] {note}")

    def resolve(self, note: str = "") -> None:
        """Move ACTIVE or ACKNOWLEDGED → RESOLVED."""
        self._transition_to(AlertStatus.RESOLVED)
        self._resolved_at = datetime.now()
        if note:
            self._notes.append(f"[RESOLVED] {note}")

    def add_note(self, note: str) -> None:
        if note.strip():
            self._notes.append(f"[{datetime.now().strftime('%H:%M:%S')}] {note.strip()}")

    def duration_seconds(self) -> Optional[float]:
        """Seconds from creation to resolution (None if still active)."""
        if self._resolved_at:
            return (self._resolved_at - self._timestamp).total_seconds()
        return None

    def age_seconds(self) -> float:
        return (datetime.now() - self._timestamp).total_seconds()

    # ── private ───────────────────────────────────────────────────────

    def _transition_to(self, new_status: AlertStatus) -> None:
        allowed = self._VALID_TRANSITIONS[self._status]
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition alert from {self._status.value} to {new_status.value}."
            )
        self._status = new_status

    def __repr__(self) -> str:
        return (
            f"Alert(id={self._alert_id}, severity={self._severity.name}, "
            f"status={self._status.value}, source={self._source!r})"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  AlertCondition  – a named rule that can fire an alert
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AlertCondition:
    """
    Describes one triggerable condition.
    `check_fn` receives a dict of current readings and returns
    (triggered: bool, detail: str).
    """
    name:        str
    description: str
    severity:    Severity
    category:    str
    check_fn:    Callable[[dict], tuple[bool, str]]
    cooldown_s:  float = 30.0   # minimum seconds between repeat alerts
    _last_fired: float = field(default=0.0, repr=False, compare=False)

    def evaluate(self, readings: dict) -> tuple[bool, str]:
        import time
        now = time.monotonic()
        if (now - self._last_fired) < self.cooldown_s:
            return False, ""
        triggered, detail = self.check_fn(readings)
        if triggered:
            self._last_fired = now
        return triggered, detail


# ─────────────────────────────────────────────────────────────────────────────
#  Built-in conditions
# ─────────────────────────────────────────────────────────────────────────────

def _build_default_conditions() -> list[AlertCondition]:
    return [
        AlertCondition(
            name        = "HIGH_CPU",
            description = "CPU usage exceeds 85%",
            severity    = Severity.HIGH,
            category    = "performance",
            check_fn    = lambda r: (
                r.get("cpu_pct", 0) > 85,
                f"CPU at {r.get('cpu_pct', 0):.1f}%",
            ),
            cooldown_s  = 60.0,
        ),
        AlertCondition(
            name        = "CRITICAL_CPU",
            description = "CPU usage exceeds 95%",
            severity    = Severity.CRITICAL,
            category    = "performance",
            check_fn    = lambda r: (
                r.get("cpu_pct", 0) > 95,
                f"CPU at {r.get('cpu_pct', 0):.1f}% — system may be unresponsive",
            ),
            cooldown_s  = 30.0,
        ),
        AlertCondition(
            name        = "HIGH_MEMORY",
            description = "Memory usage exceeds 80%",
            severity    = Severity.MEDIUM,
            category    = "performance",
            check_fn    = lambda r: (
                r.get("mem_pct", 0) > 80,
                f"Memory at {r.get('mem_pct', 0):.1f}%",
            ),
        ),
        AlertCondition(
            name        = "LOW_DISK",
            description = "Disk free space below 10%",
            severity    = Severity.HIGH,
            category    = "storage",
            check_fn    = lambda r: (
                r.get("disk_free_pct", 100) < 10,
                f"Only {r.get('disk_free_pct', 100):.1f}% disk space remaining",
            ),
        ),
        AlertCondition(
            name        = "SUSPICIOUS_LOGIN",
            description = "Login attempt from unknown IP",
            severity    = Severity.HIGH,
            category    = "security",
            check_fn    = lambda r: (
                r.get("suspicious_login", False),
                f"Login attempt from IP {r.get('login_ip', 'unknown')}",
            ),
            cooldown_s  = 10.0,
        ),
        AlertCondition(
            name        = "MULTIPLE_FAILED_LOGINS",
            description = "≥5 failed login attempts in 60 s",
            severity    = Severity.CRITICAL,
            category    = "security",
            check_fn    = lambda r: (
                r.get("failed_logins", 0) >= 5,
                f"{r.get('failed_logins', 0)} failed logins detected",
            ),
            cooldown_s  = 15.0,
        ),
        AlertCondition(
            name        = "SERVICE_DOWN",
            description = "Critical service not responding",
            severity    = Severity.CRITICAL,
            category    = "availability",
            check_fn    = lambda r: (
                r.get("service_down", False),
                f"Service '{r.get('service_name', 'unknown')}' is not responding",
            ),
            cooldown_s  = 20.0,
        ),
        AlertCondition(
            name        = "HIGH_NETWORK_TRAFFIC",
            description = "Outbound bandwidth exceeds 90%",
            severity    = Severity.MEDIUM,
            category    = "network",
            check_fn    = lambda r: (
                r.get("net_out_pct", 0) > 90,
                f"Outbound bandwidth at {r.get('net_out_pct', 0):.1f}%",
            ),
        ),
        AlertCondition(
            name        = "MALWARE_DETECTED",
            description = "Malware signature match found",
            severity    = Severity.CRITICAL,
            category    = "security",
            check_fn    = lambda r: (
                r.get("malware_found", False),
                f"Signature '{r.get('malware_sig', 'unknown')}' matched in scan",
            ),
            cooldown_s  = 5.0,
        ),
        AlertCondition(
            name        = "DB_QUERY_SLOW",
            description = "Database query time exceeds 5 s",
            severity    = Severity.LOW,
            category    = "performance",
            check_fn    = lambda r: (
                r.get("db_query_ms", 0) > 5000,
                f"Query took {r.get('db_query_ms', 0):,} ms",
            ),
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  AlertGenerator  – evaluates conditions and creates Alert objects
# ─────────────────────────────────────────────────────────────────────────────

class AlertGenerator:
    """
    Owns the set of AlertConditions.  Callers supply a readings dict;
    the generator evaluates every condition and returns new Alerts.
    """

    def __init__(self) -> None:
        self._conditions: list[AlertCondition] = _build_default_conditions()

    # ── public API ────────────────────────────────────────────────────

    def evaluate(self, readings: dict) -> list[Alert]:
        """Evaluate all conditions against `readings`; return triggered Alerts."""
        fired: list[Alert] = []
        for cond in self._conditions:
            triggered, detail = cond.evaluate(readings)
            if triggered:
                fired.append(self._create_alert(cond, detail))
        return fired

    def create_manual(
        self,
        message:  str,
        severity: Severity,
        source:   str   = "manual",
        category: str   = "general",
    ) -> Alert:
        """Create an alert directly (not via a condition)."""
        return Alert(message=message, severity=severity,
                     source=source, category=category)

    def simulate_scenario(self, scenario: str) -> list[Alert]:
        """
        Generate a realistic readings dict for a named scenario and
        evaluate all conditions against it.
        """
        readings = self._scenario_readings(scenario)
        return self.evaluate(readings)

    @property
    def conditions(self) -> list[AlertCondition]:
        return list(self._conditions)

    def add_condition(self, condition: AlertCondition) -> None:
        self._conditions.append(condition)

    # ── private ───────────────────────────────────────────────────────

    @staticmethod
    def _create_alert(cond: AlertCondition, detail: str) -> Alert:
        msg = f"{cond.description}"
        if detail:
            msg += f" — {detail}"
        return Alert(
            message  = msg,
            severity = cond.severity,
            source   = cond.name,
            category = cond.category,
        )

    @staticmethod
    def _scenario_readings(scenario: str) -> dict:
        scenarios = {
            "cpu_spike": {
                "cpu_pct": random.uniform(88, 99),
                "mem_pct": random.uniform(40, 60),
            },
            "memory_pressure": {
                "cpu_pct": random.uniform(30, 50),
                "mem_pct": random.uniform(83, 96),
            },
            "disk_full": {
                "disk_free_pct": random.uniform(2, 9),
            },
            "brute_force": {
                "failed_logins": random.randint(5, 12),
                "suspicious_login": True,
                "login_ip": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
            },
            "service_outage": {
                "service_down":  True,
                "service_name":  random.choice(["nginx", "postgres", "redis", "api-gateway"]),
                "cpu_pct":       random.uniform(10, 30),
            },
            "malware": {
                "malware_found": True,
                "malware_sig":   random.choice(["Trojan.GenericKD", "Ransomware.WannaCry", "Rootkit.Hidden"]),
            },
            "network_flood": {
                "net_out_pct": random.uniform(91, 99),
                "cpu_pct":     random.uniform(50, 70),
            },
            "all_clear": {
                "cpu_pct":       random.uniform(5, 40),
                "mem_pct":       random.uniform(20, 50),
                "disk_free_pct": random.uniform(40, 80),
            },
        }
        return scenarios.get(scenario, {})


# ─────────────────────────────────────────────────────────────────────────────
#  AlertManager  – storage + lifecycle operations
# ─────────────────────────────────────────────────────────────────────────────

class AlertManager:
    """
    Central store for all alerts.
    Provides filtered views, lifecycle operations, and statistics.
    """

    def __init__(self) -> None:
        self._alerts: dict[str, Alert] = {}   # alert_id → Alert
        self._lock:   threading.Lock   = threading.Lock()

    # ── ingestion ─────────────────────────────────────────────────────

    def add(self, alert: Alert) -> None:
        with self._lock:
            self._alerts[alert.alert_id] = alert

    def add_many(self, alerts: list[Alert]) -> int:
        for a in alerts:
            self.add(a)
        return len(alerts)

    # ── retrieval ─────────────────────────────────────────────────────

    def get(self, alert_id: str) -> Optional[Alert]:
        return self._alerts.get(alert_id.upper())

    def all_alerts(self) -> list[Alert]:
        with self._lock:
            return sorted(self._alerts.values(),
                          key=lambda a: a.timestamp, reverse=True)

    def active(self) -> list[Alert]:
        return [a for a in self.all_alerts() if a.status == AlertStatus.ACTIVE]

    def acknowledged(self) -> list[Alert]:
        return [a for a in self.all_alerts() if a.status == AlertStatus.ACKNOWLEDGED]

    def resolved(self) -> list[Alert]:
        return [a for a in self.all_alerts() if a.status == AlertStatus.RESOLVED]

    def by_severity(self, severity: Severity) -> list[Alert]:
        return [a for a in self.all_alerts() if a.severity == severity]

    def by_category(self, category: str) -> list[Alert]:
        return [a for a in self.all_alerts() if a.category.lower() == category.lower()]

    def search(self, query: str) -> list[Alert]:
        q = query.lower()
        return [
            a for a in self.all_alerts()
            if q in a.message.lower()
            or q in a.source.lower()
            or q in a.category.lower()
            or q in a.alert_id.lower()
        ]

    # ── lifecycle operations ──────────────────────────────────────────

    def acknowledge_alert(self, alert_id: str, note: str = "") -> Alert:
        alert = self._require(alert_id)
        alert.acknowledge(note)
        return alert

    def resolve_alert(self, alert_id: str, note: str = "") -> Alert:
        alert = self._require(alert_id)
        alert.resolve(note)
        return alert

    def resolve_all_active(self, note: str = "Bulk resolved") -> int:
        count = 0
        for a in self.active():
            try:
                a.resolve(note)
                count += 1
            except ValueError:
                pass
        return count

    def add_note_to(self, alert_id: str, note: str) -> Alert:
        alert = self._require(alert_id)
        alert.add_note(note)
        return alert

    # ── statistics ────────────────────────────────────────────────────

    def stats(self) -> dict:
        alerts = self.all_alerts()
        resolved = [a for a in alerts if a.status == AlertStatus.RESOLVED and a.duration_seconds()]
        avg_resolve = (
            sum(a.duration_seconds() for a in resolved) / len(resolved)  # type: ignore
            if resolved else None
        )
        return {
            "total":        len(alerts),
            "active":       len(self.active()),
            "acknowledged": len(self.acknowledged()),
            "resolved":     len(self.resolved()),
            "by_severity":  {s.name: len(self.by_severity(s)) for s in Severity},
            "avg_resolve_s": round(avg_resolve, 1) if avg_resolve else None,
        }

    # ── private ───────────────────────────────────────────────────────

    def _require(self, alert_id: str) -> Alert:
        alert = self.get(alert_id)
        if alert is None:
            raise KeyError(f"No alert found with ID '{alert_id}'.")
        return alert


# ─────────────────────────────────────────────────────────────────────────────
#  CLI helpers
# ─────────────────────────────────────────────────────────────────────────────

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_CYAN   = "\033[96m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_MAG    = "\033[95m"

STATUS_COLOUR = {
    AlertStatus.ACTIVE:       _RED,
    AlertStatus.ACKNOWLEDGED: _YELLOW,
    AlertStatus.RESOLVED:     _GREEN,
}

SEV_COLOUR = {
    Severity.INFO:     _CYAN,
    Severity.LOW:      _GREEN,
    Severity.MEDIUM:   _YELLOW,
    Severity.HIGH:     _RED,
    Severity.CRITICAL: _MAG,
}


def _c(text: str, colour: str) -> str:
    return f"{colour}{text}{_RESET}"


def _fmt_status(s: AlertStatus) -> str:
    return _c(f"{s.value:<12}", STATUS_COLOUR[s])


def _fmt_sev(s: Severity) -> str:
    return _c(f"{s.name:<8}", SEV_COLOUR[s])


def _hr(w: int = 72, ch: str = "─") -> str:
    return ch * w


def _print_alert_row(a: Alert, idx: Optional[int] = None) -> None:
    prefix = f"  {idx:>3}." if idx is not None else "    "
    ts = a.timestamp.strftime("%m-%d %H:%M:%S")
    print(
        f"{prefix} [{_BOLD}{a.alert_id}{_RESET}]"
        f"  {_fmt_sev(a.severity)}"
        f"  {_fmt_status(a.status)}"
        f"  {_DIM}{ts}{_RESET}"
        f"  {a.source}"
    )
    print(f"       {a.message}")


def _print_alert_detail(a: Alert) -> None:
    w = 64
    print(f"\n{_BOLD}{_hr(w)}{_RESET}")
    print(f"  {_BOLD}Alert Detail  —  ID: {a.alert_id}{_RESET}")
    print(_hr(w))
    print(f"  {'Message':<14}: {a.message}")
    print(f"  {'Severity':<14}: {_fmt_sev(a.severity)}")
    print(f"  {'Status':<14}: {_fmt_status(a.status)}")
    print(f"  {'Category':<14}: {a.category}")
    print(f"  {'Source':<14}: {a.source}")
    print(f"  {'Created':<14}: {a.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    if a.ack_at:
        print(f"  {'Acknowledged':<14}: {a.ack_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if a.resolved_at:
        dur = a.duration_seconds()
        print(f"  {'Resolved':<14}: {a.resolved_at.strftime('%Y-%m-%d %H:%M:%S')}"
              f"  (took {dur:.0f}s)")
    if a.notes:
        print(f"  {'Notes':<14}:")
        for note in a.notes:
            print(f"    • {note}")
    print(f"{_BOLD}{_hr(w)}{_RESET}\n")


def _get_input(prompt: str, required: bool = True) -> str:
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("  ⚠  Input cannot be empty.")


def _get_choice(prompt: str, valid: set[str]) -> str:
    while True:
        ch = input(prompt).strip().lower()
        if ch in valid:
            return ch
        print(f"  ⚠  Choose: {', '.join(sorted(valid))}")


def _pick_severity() -> Severity:
    mapping = {str(s.value): s for s in Severity}
    print("  Severity levels:")
    for s in Severity:
        print(f"    {s.value} — {_fmt_sev(s)}")
    while True:
        raw = input("  Enter number (1–5): ").strip()
        if raw in mapping:
            return mapping[raw]
        print("  ⚠  Enter a number between 1 and 5.")


def _pick_alert_id(manager: AlertManager, pool: list[Alert]) -> Optional[str]:
    if not pool:
        print("  No alerts available.")
        return None
    raw = _get_input("  Enter Alert ID (or row number): ")
    # Try direct ID first
    if manager.get(raw.upper()):
        return raw.upper()
    # Try row index
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(pool):
            return pool[idx].alert_id
    except ValueError:
        pass
    print(f"  ⚠  No alert found for '{raw}'.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  CLI actions
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS = {
    "1": ("cpu_spike",       "CPU spike (>85%)"),
    "2": ("memory_pressure", "Memory pressure (>80%)"),
    "3": ("disk_full",       "Disk nearly full (<10% free)"),
    "4": ("brute_force",     "Brute-force / suspicious login"),
    "5": ("service_outage",  "Critical service outage"),
    "6": ("malware",         "Malware detected"),
    "7": ("network_flood",   "Network bandwidth flood"),
    "8": ("all_clear",       "All-clear (no alerts expected)"),
}


def action_simulate(gen: AlertGenerator, mgr: AlertManager) -> None:
    print(f"\n{_BOLD}── Simulate a Scenario ─────────────────────────────────{_RESET}")
    for key, (_, label) in SCENARIOS.items():
        print(f"  {_BOLD}[{key}]{_RESET} {label}")
    choice = _get_choice("\n  Select scenario: ", set(SCENARIOS))
    scenario_key, scenario_label = SCENARIOS[choice]
    new_alerts = gen.simulate_scenario(scenario_key)
    if new_alerts:
        count = mgr.add_many(new_alerts)
        print(f"\n  {_GREEN}✓{_RESET}  {count} alert(s) generated for '{scenario_label}':\n")
        for i, a in enumerate(new_alerts, 1):
            _print_alert_row(a, i)
    else:
        print(f"\n  {_GREEN}✓{_RESET}  No conditions triggered for '{scenario_label}' — system normal.\n")


def action_manual_alert(gen: AlertGenerator, mgr: AlertManager) -> None:
    print(f"\n{_BOLD}── Create Manual Alert ──────────────────────────────────{_RESET}")
    message  = _get_input("  Message       : ")
    severity = _pick_severity()
    source   = _get_input("  Source        [manual]: ", required=False) or "manual"
    category = _get_input("  Category      [general]: ", required=False) or "general"
    alert = gen.create_manual(message, severity, source, category)
    mgr.add(alert)
    print(f"\n  {_GREEN}✓{_RESET}  Alert {_BOLD}{alert.alert_id}{_RESET} created.\n")
    _print_alert_detail(alert)


def action_view_active(mgr: AlertManager) -> None:
    active = mgr.active()
    print(f"\n{_BOLD}── Active Alerts ({len(active)}) ─────────────────────────────────{_RESET}")
    if not active:
        print(f"  {_GREEN}No active alerts.{_RESET}\n")
        return
    for i, a in enumerate(active, 1):
        _print_alert_row(a, i)
    print()


def action_view_all(mgr: AlertManager) -> None:
    all_a = mgr.all_alerts()
    print(f"\n{_BOLD}── All Alerts ({len(all_a)}) ──────────────────────────────────────{_RESET}")
    if not all_a:
        print("  No alerts on record.\n")
        return
    for i, a in enumerate(all_a, 1):
        _print_alert_row(a, i)
    print()


def action_acknowledge(mgr: AlertManager) -> None:
    pool = mgr.active()
    print(f"\n{_BOLD}── Acknowledge Alert ────────────────────────────────────{_RESET}")
    action_view_active(mgr)
    if not pool:
        return
    aid = _pick_alert_id(mgr, pool)
    if not aid:
        return
    note = _get_input("  Note (optional): ", required=False)
    try:
        alert = mgr.acknowledge_alert(aid, note)
        print(f"\n  {_GREEN}✓{_RESET}  Alert {_BOLD}{alert.alert_id}{_RESET} acknowledged.\n")
    except (KeyError, ValueError) as exc:
        print(f"\n  ✗  {exc}\n")


def action_resolve(mgr: AlertManager) -> None:
    pool = [a for a in mgr.all_alerts()
            if a.status in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED)]
    print(f"\n{_BOLD}── Resolve Alert ────────────────────────────────────────{_RESET}")
    if not pool:
        print(f"  {_GREEN}Nothing to resolve.{_RESET}\n")
        return
    for i, a in enumerate(pool, 1):
        _print_alert_row(a, i)
    print()
    aid = _pick_alert_id(mgr, pool)
    if not aid:
        return
    note = _get_input("  Resolution note (optional): ", required=False)
    try:
        alert = mgr.resolve_alert(aid, note)
        print(f"\n  {_GREEN}✓{_RESET}  Alert {_BOLD}{alert.alert_id}{_RESET} resolved.\n")
    except (KeyError, ValueError) as exc:
        print(f"\n  ✗  {exc}\n")


def action_resolve_all(mgr: AlertManager) -> None:
    count = mgr.resolve_all_active("Bulk resolve via menu")
    print(f"\n  {_GREEN}✓{_RESET}  {count} active alert(s) resolved.\n")


def action_detail(mgr: AlertManager) -> None:
    print(f"\n{_BOLD}── Alert Detail ─────────────────────────────────────────{_RESET}")
    all_a = mgr.all_alerts()
    if not all_a:
        print("  No alerts.\n")
        return
    aid = _get_input("  Enter Alert ID: ")
    alert = mgr.get(aid.upper())
    if alert:
        _print_alert_detail(alert)
    else:
        print(f"  ⚠  No alert with ID '{aid}'.\n")


def action_search(mgr: AlertManager) -> None:
    q = _get_input("  Search query: ")
    results = mgr.search(q)
    print(f"\n  Found {len(results)} result(s) for '{q}':\n")
    for i, a in enumerate(results, 1):
        _print_alert_row(a, i)
    print()


def action_stats(mgr: AlertManager) -> None:
    s = mgr.stats()
    W = 52
    print(f"\n{_BOLD}{_hr(W)}{_RESET}")
    print(f"{_BOLD}  Alert Statistics{_RESET}")
    print(_hr(W))
    print(f"  {'Total alerts':<24}: {s['total']}")
    print(f"  {'Active':<24}: {_c(str(s['active']),       _RED    if s['active']       else _GREEN)}")
    print(f"  {'Acknowledged':<24}: {_c(str(s['acknowledged']), _YELLOW if s['acknowledged'] else _GREEN)}")
    print(f"  {'Resolved':<24}: {_c(str(s['resolved']),   _GREEN)}")
    if s['avg_resolve_s'] is not None:
        print(f"  {'Avg resolve time':<24}: {s['avg_resolve_s']}s")
    print()
    print(f"  {'Severity breakdown':}")
    for sev_name, count in s['by_severity'].items():
        bar  = "█" * count
        sev  = Severity[sev_name]
        line = f"    {sev_name:<10}: {count:>3}  {_c(bar, SEV_COLOUR[sev])}"
        print(line)
    print(f"{_BOLD}{_hr(W)}{_RESET}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Main CLI loop
# ─────────────────────────────────────────────────────────────────────────────

BANNER = f"""
{_BOLD}╔══════════════════════════════════════════════════════════════╗
║           Alert Generator System  v1.0                       ║
║   Simulate · Generate · Track · Resolve system alerts        ║
╚══════════════════════════════════════════════════════════════╝{_RESET}"""

MENU = f"""
  {_BOLD}[1]{_RESET} Simulate a scenario (auto-generate alerts)
  {_BOLD}[2]{_RESET} Create a manual alert
  {_BOLD}[3]{_RESET} View active alerts
  {_BOLD}[4]{_RESET} View all alerts (history)
  {_BOLD}[5]{_RESET} Acknowledge an alert
  {_BOLD}[6]{_RESET} Resolve an alert
  {_BOLD}[7]{_RESET} Resolve ALL active alerts
  {_BOLD}[8]{_RESET} Alert detail / add note
  {_BOLD}[9]{_RESET} Search alerts
  {_BOLD}[S]{_RESET} Statistics
  {_BOLD}[Q]{_RESET} Quit
"""


def main() -> None:
    print(BANNER)

    gen = AlertGenerator()
    mgr = AlertManager()

    # Seed a few alerts to make the session immediately interesting
    print(f"  {_DIM}Seeding sample alerts…{_RESET}\n")
    for scenario in ("cpu_spike", "brute_force"):
        new = gen.simulate_scenario(scenario)
        mgr.add_many(new)

    while True:
        active_count = len(mgr.active())
        active_label = (
            f"  {_RED}{_BOLD}⚠  {active_count} active alert(s){_RESET}"
            if active_count else
            f"  {_GREEN}✓  No active alerts{_RESET}"
        )
        print(MENU)
        print(active_label)
        choice = _get_choice("\n  Your choice: ",
                             {"1","2","3","4","5","6","7","8","9","s","q"})

        if   choice == "1": action_simulate(gen, mgr)
        elif choice == "2": action_manual_alert(gen, mgr)
        elif choice == "3": action_view_active(mgr)
        elif choice == "4": action_view_all(mgr)
        elif choice == "5": action_acknowledge(mgr)
        elif choice == "6": action_resolve(mgr)
        elif choice == "7": action_resolve_all(mgr)
        elif choice == "8": action_detail(mgr)
        elif choice == "9": action_search(mgr)
        elif choice == "s": action_stats(mgr)
        elif choice == "q":
            print(f"\n  {_BOLD}Stay vigilant!  Goodbye. 👋{_RESET}\n")
            break


if __name__ == "__main__":
    main()