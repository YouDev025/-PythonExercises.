"""
Simulated Intrusion Detection System (IDS)
==========================================
A modular OOP-based system that monitors simulated network events
and flags suspicious behaviour using rule-based heuristics.
"""

import random
import ipaddress
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional


# ═══════════════════════════════════════════════════════════
#  Constants / Configuration
# ═══════════════════════════════════════════════════════════

BLACKLISTED_IPS = {
    "192.168.100.200",
    "10.0.0.99",
    "172.16.0.254",
    "203.0.113.5",
    "198.51.100.42",
}

WELL_KNOWN_PORTS = {
    21: "FTP", 22: "SSH", 23: "TELNET", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 3306: "MySQL", 3389: "RDP", 8080: "HTTP-Alt",
}

PROTOCOLS       = ["TCP", "UDP", "ICMP"]
ACTIVITY_TYPES  = [
    "LOGIN_SUCCESS", "LOGIN_FAILURE", "PORT_SCAN",
    "DATA_TRANSFER", "BRUTE_FORCE", "UNAUTHORIZED_ACCESS",
    "NORMAL_TRAFFIC", "FILE_ACCESS", "CONFIG_CHANGE",
]

# Detection thresholds
LOGIN_FAIL_THRESHOLD   = 5    # failures in window → alert
PORT_SCAN_THRESHOLD    = 10   # distinct ports in window → alert
TIME_WINDOW_SECONDS    = 60   # sliding-window width

SEVERITY_LEVELS = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}


# ═══════════════════════════════════════════════════════════
#  NetworkEvent
# ═══════════════════════════════════════════════════════════

class NetworkEvent:
    """Represents a single observed network activity."""

    _id_counter = 0

    def __init__(
        self,
        source_ip: str,
        destination_ip: str,
        protocol: str,
        port: int,
        activity_type: str,
        timestamp: Optional[datetime] = None,
    ):
        NetworkEvent._id_counter += 1
        self._event_id      = NetworkEvent._id_counter
        self._source_ip     = self._validate_ip(source_ip)
        self._destination_ip= self._validate_ip(destination_ip)
        self._protocol      = self._validate_protocol(protocol)
        self._port          = self._validate_port(port)
        self._activity_type = self._validate_activity(activity_type)
        self._timestamp     = timestamp or datetime.now()

    # ── Validators ────────────────────────────
    @staticmethod
    def _validate_ip(ip: str) -> str:
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValueError(f"Invalid IP address: '{ip}'")

    @staticmethod
    def _validate_protocol(proto: str) -> str:
        p = proto.upper()
        if p not in PROTOCOLS:
            raise ValueError(f"Unknown protocol '{proto}'. Choose: {PROTOCOLS}")
        return p

    @staticmethod
    def _validate_port(port) -> int:
        try:
            port = int(port)
        except (TypeError, ValueError):
            raise ValueError(f"Port must be an integer, got '{port}'")
        if not (0 <= port <= 65535):
            raise ValueError(f"Port {port} is out of valid range (0-65535).")
        return port

    @staticmethod
    def _validate_activity(activity: str) -> str:
        a = activity.upper()
        if a not in ACTIVITY_TYPES:
            raise ValueError(
                f"Unknown activity '{activity}'.\nValid types: {ACTIVITY_TYPES}"
            )
        return a

    # ── Properties ────────────────────────────
    @property
    def event_id(self)       -> int:      return self._event_id
    @property
    def source_ip(self)      -> str:      return self._source_ip
    @property
    def destination_ip(self) -> str:      return self._destination_ip
    @property
    def protocol(self)       -> str:      return self._protocol
    @property
    def port(self)            -> int:      return self._port
    @property
    def activity_type(self)  -> str:      return self._activity_type
    @property
    def timestamp(self)       -> datetime: return self._timestamp

    def __repr__(self) -> str:
        ts = self._timestamp.strftime("%H:%M:%S")
        svc = WELL_KNOWN_PORTS.get(self._port, "?")
        return (
            f"[#{self._event_id:04d} {ts}] "
            f"{self._source_ip} → {self._destination_ip} "
            f"{self._protocol}/{self._port}({svc}) "
            f"| {self._activity_type}"
        )


# ═══════════════════════════════════════════════════════════
#  Alert
# ═══════════════════════════════════════════════════════════

class Alert:
    """An IDS alert tied to one or more events."""

    _id_counter = 0

    def __init__(
        self,
        alert_type: str,
        description: str,
        severity: int,
        source_ip: str,
        related_events: list[NetworkEvent],
    ):
        Alert._id_counter += 1
        self._alert_id      = Alert._id_counter
        self._alert_type    = alert_type
        self._description   = description
        self._severity      = max(1, min(4, severity))
        self._source_ip     = source_ip
        self._related       = list(related_events)
        self._timestamp     = datetime.now()

    @property
    def alert_id(self)    -> int:   return self._alert_id
    @property
    def alert_type(self)  -> str:   return self._alert_type
    @property
    def description(self) -> str:   return self._description
    @property
    def severity(self)    -> int:   return self._severity
    @property
    def severity_label(self) -> str: return SEVERITY_LEVELS[self._severity]
    @property
    def source_ip(self)   -> str:   return self._source_ip
    @property
    def related_events(self) -> list: return list(self._related)
    @property
    def timestamp(self)   -> datetime: return self._timestamp

    def display(self) -> None:
        sev_icons = {1: "🔵", 2: "🟡", 3: "🔴", 4: "💀"}
        icon = sev_icons.get(self._severity, "❓")
        ts   = self._timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"  {icon}  ALERT #{self._alert_id:03d} [{self.severity_label}]  "
            f"{self._alert_type}"
        )
        print(f"       Source IP  : {self._source_ip}")
        print(f"       {self._description}")
        print(f"       Detected at: {ts}")
        print(f"       Events     : {len(self._related)} related")


# ═══════════════════════════════════════════════════════════
#  IDSAnalyzer
# ═══════════════════════════════════════════════════════════

class IDSAnalyzer:
    """
    Stateless rule engine that analyses a snapshot of events
    and returns a list of Alerts.

    Rules implemented
    -----------------
    1. Blacklisted source IP
    2. Repeated login failures  (≥ threshold in time window)
    3. Port scan detection      (≥ threshold distinct ports in window)
    4. Explicit brute-force activity type
    5. Unauthorized access activity type
    6. Telnet usage (insecure protocol)
    7. High-volume traffic spike from single source
    """

    def __init__(
        self,
        login_fail_threshold: int = LOGIN_FAIL_THRESHOLD,
        port_scan_threshold: int  = PORT_SCAN_THRESHOLD,
        time_window: int          = TIME_WINDOW_SECONDS,
    ):
        self._login_fail_threshold = login_fail_threshold
        self._port_scan_threshold  = port_scan_threshold
        self._time_window          = time_window

    # ── Public entry-point ────────────────────
    def analyse(self, events: list[NetworkEvent]) -> list[Alert]:
        alerts: list[Alert] = []
        if not events:
            return alerts

        alerts += self._check_blacklist(events)
        alerts += self._check_login_failures(events)
        alerts += self._check_port_scan(events)
        alerts += self._check_brute_force(events)
        alerts += self._check_unauthorized(events)
        alerts += self._check_insecure_protocols(events)
        alerts += self._check_traffic_spike(events)
        return alerts

    # ── Private rules ─────────────────────────
    @staticmethod
    def _check_blacklist(events: list[NetworkEvent]) -> list[Alert]:
        alerts = []
        seen: set[str] = set()
        for ev in events:
            if ev.source_ip in BLACKLISTED_IPS and ev.source_ip not in seen:
                seen.add(ev.source_ip)
                related = [e for e in events if e.source_ip == ev.source_ip]
                alerts.append(Alert(
                    alert_type     = "BLACKLISTED_IP",
                    description    = (
                        f"Traffic from known-malicious IP {ev.source_ip} "
                        f"({len(related)} event(s))."
                    ),
                    severity       = 4,
                    source_ip      = ev.source_ip,
                    related_events = related,
                ))
        return alerts

    def _check_login_failures(self, events: list[NetworkEvent]) -> list[Alert]:
        alerts = []
        by_src: dict[str, list[NetworkEvent]] = defaultdict(list)
        for ev in events:
            if ev.activity_type == "LOGIN_FAILURE":
                by_src[ev.source_ip].append(ev)

        for src_ip, fail_events in by_src.items():
            # Sliding window
            fail_events.sort(key=lambda e: e.timestamp)
            window_start = fail_events[-1].timestamp - timedelta(
                seconds=self._time_window
            )
            window_events = [e for e in fail_events if e.timestamp >= window_start]
            if len(window_events) >= self._login_fail_threshold:
                alerts.append(Alert(
                    alert_type     = "REPEATED_LOGIN_FAILURES",
                    description    = (
                        f"{len(window_events)} login failures from {src_ip} "
                        f"within {self._time_window}s."
                    ),
                    severity       = 2,
                    source_ip      = src_ip,
                    related_events = window_events,
                ))
        return alerts

    def _check_port_scan(self, events: list[NetworkEvent]) -> list[Alert]:
        alerts = []
        by_src: dict[str, list[NetworkEvent]] = defaultdict(list)
        for ev in events:
            by_src[ev.source_ip].append(ev)

        for src_ip, src_events in by_src.items():
            src_events.sort(key=lambda e: e.timestamp)
            window_start = src_events[-1].timestamp - timedelta(
                seconds=self._time_window
            )
            window_events = [e for e in src_events if e.timestamp >= window_start]
            distinct_ports = {e.port for e in window_events}
            if len(distinct_ports) >= self._port_scan_threshold:
                alerts.append(Alert(
                    alert_type     = "PORT_SCAN",
                    description    = (
                        f"{src_ip} probed {len(distinct_ports)} distinct ports: "
                        f"{sorted(distinct_ports)[:8]}{'…' if len(distinct_ports)>8 else ''}."
                    ),
                    severity       = 3,
                    source_ip      = src_ip,
                    related_events = window_events,
                ))
        return alerts

    @staticmethod
    def _check_brute_force(events: list[NetworkEvent]) -> list[Alert]:
        alerts = []
        seen: set[str] = set()
        for ev in events:
            if ev.activity_type == "BRUTE_FORCE" and ev.source_ip not in seen:
                seen.add(ev.source_ip)
                related = [e for e in events
                           if e.source_ip == ev.source_ip
                           and e.activity_type == "BRUTE_FORCE"]
                alerts.append(Alert(
                    alert_type     = "BRUTE_FORCE_ATTACK",
                    description    = (
                        f"Brute-force activity detected from {ev.source_ip} "
                        f"({len(related)} event(s))."
                    ),
                    severity       = 3,
                    source_ip      = ev.source_ip,
                    related_events = related,
                ))
        return alerts

    @staticmethod
    def _check_unauthorized(events: list[NetworkEvent]) -> list[Alert]:
        alerts = []
        seen: set[str] = set()
        for ev in events:
            if ev.activity_type == "UNAUTHORIZED_ACCESS" and ev.source_ip not in seen:
                seen.add(ev.source_ip)
                related = [e for e in events
                           if e.source_ip == ev.source_ip
                           and e.activity_type == "UNAUTHORIZED_ACCESS"]
                alerts.append(Alert(
                    alert_type     = "UNAUTHORIZED_ACCESS",
                    description    = (
                        f"Unauthorized access attempt from {ev.source_ip} "
                        f"on port {ev.port}."
                    ),
                    severity       = 3,
                    source_ip      = ev.source_ip,
                    related_events = related,
                ))
        return alerts

    @staticmethod
    def _check_insecure_protocols(events: list[NetworkEvent]) -> list[Alert]:
        """Flag Telnet (port 23) connections."""
        alerts = []
        telnet_events = [e for e in events if e.port == 23]
        if telnet_events:
            src_ips = {e.source_ip for e in telnet_events}
            alerts.append(Alert(
                alert_type     = "INSECURE_PROTOCOL",
                description    = (
                    f"Telnet (port 23) used by {len(src_ips)} source(s). "
                    "Plaintext credential risk."
                ),
                severity       = 2,
                source_ip      = ", ".join(src_ips),
                related_events = telnet_events,
            ))
        return alerts

    def _check_traffic_spike(self, events: list[NetworkEvent]) -> list[Alert]:
        """Flag any single IP generating > 20 % of all events."""
        if len(events) < 10:
            return []
        alerts = []
        counts: dict[str, int] = defaultdict(int)
        for ev in events:
            counts[ev.source_ip] += 1
        total = len(events)
        for src_ip, count in counts.items():
            if count / total > 0.20:
                related = [e for e in events if e.source_ip == src_ip]
                alerts.append(Alert(
                    alert_type     = "TRAFFIC_SPIKE",
                    description    = (
                        f"{src_ip} generated {count}/{total} events "
                        f"({count/total:.0%} of total traffic)."
                    ),
                    severity       = 2,
                    source_ip      = src_ip,
                    related_events = related,
                ))
        return alerts


# ═══════════════════════════════════════════════════════════
#  IDSManager
# ═══════════════════════════════════════════════════════════

class IDSManager:
    """
    Collects NetworkEvents, coordinates analysis, and stores Alerts.
    """

    def __init__(self):
        self._events:  list[NetworkEvent] = []
        self._alerts:  list[Alert]        = []
        self._analyzer = IDSAnalyzer()

    # ── Event management ──────────────────────
    def add_event(
        self,
        source_ip: str,
        destination_ip: str,
        protocol: str,
        port: int,
        activity_type: str,
        timestamp: Optional[datetime] = None,
    ) -> NetworkEvent:
        ev = NetworkEvent(
            source_ip, destination_ip, protocol, port, activity_type, timestamp
        )
        self._events.append(ev)
        return ev

    def clear_events(self) -> None:
        self._events.clear()

    def clear_alerts(self) -> None:
        self._alerts.clear()

    @property
    def events(self) -> list[NetworkEvent]:
        return list(self._events)

    @property
    def alerts(self) -> list[Alert]:
        return list(self._alerts)

    @property
    def event_count(self) -> int:
        return len(self._events)

    @property
    def alert_count(self) -> int:
        return len(self._alerts)

    # ── Analysis ──────────────────────────────
    def run_analysis(self) -> list[Alert]:
        """Analyse all stored events; append new alerts; return them."""
        new_alerts = self._analyzer.analyse(self._events)
        # De-duplicate by (type, source_ip)
        existing_keys = {(a.alert_type, a.source_ip) for a in self._alerts}
        added = []
        for alert in new_alerts:
            key = (alert.alert_type, alert.source_ip)
            if key not in existing_keys:
                self._alerts.append(alert)
                existing_keys.add(key)
                added.append(alert)
        return added

    # ── Display helpers ───────────────────────
    def display_event_history(self, last_n: int = 20) -> None:
        if not self._events:
            print("\n  No events recorded yet.\n")
            return
        subset = self._events[-last_n:]
        print(f"\n{'─'*66}")
        print(f"  EVENT HISTORY  (showing last {len(subset)} of {self.event_count})")
        print(f"{'─'*66}")
        for ev in subset:
            print(f"  {ev}")
        print(f"{'─'*66}\n")

    def display_alerts(self, severity_filter: Optional[int] = None) -> None:
        filtered = self._alerts
        if severity_filter:
            filtered = [a for a in filtered if a.severity >= severity_filter]

        if not filtered:
            label = f" (severity ≥ {SEVERITY_LEVELS.get(severity_filter,'')})" \
                    if severity_filter else ""
            print(f"\n  No alerts{label}.\n")
            return

        print(f"\n{'═'*66}")
        print(f"  INTRUSION ALERTS  ({len(filtered)} total)")
        print(f"{'═'*66}")
        for alert in sorted(filtered, key=lambda a: a.severity, reverse=True):
            alert.display()
            print()
        print(f"{'═'*66}\n")

    def display_summary(self) -> None:
        severity_counts = defaultdict(int)
        for a in self._alerts:
            severity_counts[a.severity] += 1

        print(f"\n{'─'*45}")
        print("  IDS SUMMARY")
        print(f"{'─'*45}")
        print(f"  Total events  : {self.event_count}")
        print(f"  Total alerts  : {self.alert_count}")
        if self._alerts:
            print("  By severity   :")
            for sev in sorted(severity_counts, reverse=True):
                bar = "█" * severity_counts[sev]
                print(f"    {SEVERITY_LEVELS[sev]:<8} {bar} ({severity_counts[sev]})")
        print(f"{'─'*45}\n")


# ═══════════════════════════════════════════════════════════
#  Scenario / Event Simulator
# ═══════════════════════════════════════════════════════════

class EventSimulator:
    """Generates realistic-ish random NetworkEvent data for the manager."""

    INTERNAL_NETS = [
        "192.168.1.", "192.168.2.", "10.0.0.", "172.16.0."
    ]
    EXTERNAL_IPS = [
        "203.0.113.10", "198.51.100.5", "8.8.8.8",
        "1.1.1.1", "185.220.101.1", "45.33.32.156",
    ] + list(BLACKLISTED_IPS)

    # Pre-built attack / normal scenario bundles
    SCENARIOS = {
        "1": ("SSH Brute-Force",            "_ssh_brute_force"),
        "2": ("Port Scan",                  "_port_scan"),
        "3": ("Blacklisted IP Traffic",     "_blacklisted_ip"),
        "4": ("Telnet Usage",               "_telnet_usage"),
        "5": ("Unauthorized Access Burst",  "_unauthorized_burst"),
        "6": ("Mixed Normal Traffic",       "_normal_traffic"),
        "7": ("Full Attack Scenario",       "_full_attack"),
    }

    def __init__(self, manager: IDSManager):
        self._mgr = manager

    def _rnd_internal(self) -> str:
        net = random.choice(self.INTERNAL_NETS)
        return net + str(random.randint(2, 254))

    def _rnd_external(self) -> str:
        return random.choice(self.EXTERNAL_IPS)

    def _base_time(self) -> datetime:
        return datetime.now() - timedelta(seconds=random.randint(0, 55))

    # ── Scenarios ─────────────────────────────
    def _ssh_brute_force(self) -> int:
        attacker = self._rnd_external()
        target   = self._rnd_internal()
        count = random.randint(6, 15)
        for _ in range(count):
            self._mgr.add_event(attacker, target, "TCP", 22,
                                "LOGIN_FAILURE", self._base_time())
        return count

    def _port_scan(self) -> int:
        attacker = self._rnd_external()
        target   = self._rnd_internal()
        ports    = random.sample(range(1, 10000), random.randint(12, 25))
        for p in ports:
            self._mgr.add_event(attacker, target, "TCP", p,
                                "PORT_SCAN", self._base_time())
        return len(ports)

    def _blacklisted_ip(self) -> int:
        bad_ip = random.choice(list(BLACKLISTED_IPS))
        target = self._rnd_internal()
        count  = random.randint(3, 8)
        for _ in range(count):
            act = random.choice(ACTIVITY_TYPES)
            self._mgr.add_event(bad_ip, target,
                                random.choice(PROTOCOLS),
                                random.choice(list(WELL_KNOWN_PORTS.keys())),
                                act, self._base_time())
        return count

    def _telnet_usage(self) -> int:
        src    = self._rnd_external()
        target = self._rnd_internal()
        count  = random.randint(2, 5)
        for _ in range(count):
            self._mgr.add_event(src, target, "TCP", 23,
                                "NORMAL_TRAFFIC", self._base_time())
        return count

    def _unauthorized_burst(self) -> int:
        attacker = self._rnd_external()
        target   = self._rnd_internal()
        count    = random.randint(4, 9)
        for _ in range(count):
            p = random.choice([22, 3389, 8080, 443, 3306])
            self._mgr.add_event(attacker, target, "TCP", p,
                                "UNAUTHORIZED_ACCESS", self._base_time())
        return count

    def _normal_traffic(self) -> int:
        count = random.randint(10, 20)
        for _ in range(count):
            src  = self._rnd_internal()
            dst  = random.choice([self._rnd_internal(), self._rnd_external()])
            port = random.choice([80, 443, 53, 8080])
            self._mgr.add_event(src, dst, "TCP", port,
                                random.choice(["NORMAL_TRAFFIC", "DATA_TRANSFER",
                                               "LOGIN_SUCCESS"]),
                                self._base_time())
        return count

    def _full_attack(self) -> int:
        total  = self._ssh_brute_force()
        total += self._port_scan()
        total += self._blacklisted_ip()
        total += self._unauthorized_burst()
        total += self._normal_traffic()
        return total

    def run_scenario(self, key: str) -> int:
        if key not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario '{key}'")
        _, method_name = self.SCENARIOS[key]
        method = getattr(self, method_name)
        return method()


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════

BANNER = r"""
  ╔══════════════════════════════════════════════════════╗
  ║     SIMULATED INTRUSION DETECTION SYSTEM  v1.0       ║
  ║   Rule-based network event analysis & alerting       ║
  ╚══════════════════════════════════════════════════════╝
"""

MAIN_MENU = """
  ┌──────────────────────────────────────────────────┐
  │  EVENTS                                          │
  │   1. Simulate a scenario (preset)                │
  │   2. Add a custom network event                  │
  │   3. View event history                          │
  │   4. Clear all events                            │
  │                                                  │
  │  DETECTION                                       │
  │   5. Run intrusion detection analysis            │
  │   6. View all alerts                             │
  │   7. View high-severity alerts only (≥ HIGH)     │
  │   8. View summary dashboard                      │
  │   9. Clear alerts                                │
  │                                                  │
  │   0. Exit                                        │
  └──────────────────────────────────────────────────┘
  Choice: """

SCENARIO_MENU = """
  Preset scenarios:
"""


class CLI:
    def __init__(self):
        self._mgr       = IDSManager()
        self._simulator = EventSimulator(self._mgr)

    # ── Helpers ───────────────────────────────
    @staticmethod
    def _prompt(msg: str) -> str:
        return input(f"  {msg}").strip()

    @staticmethod
    def _pause() -> None:
        input("  [Press Enter to continue]")

    # ── Scenario simulation ───────────────────
    def _simulate_scenario(self) -> None:
        print(SCENARIO_MENU)
        for k, (name, _) in EventSimulator.SCENARIOS.items():
            print(f"    {k}. {name}")
        choice = self._prompt("\n  Enter scenario number: ")
        if choice not in EventSimulator.SCENARIOS:
            print("  [!] Invalid scenario.")
            return
        name, _ = EventSimulator.SCENARIOS[choice]
        added   = self._simulator.run_scenario(choice)
        print(f"\n  ✔  Scenario '{name}' → {added} event(s) added "
              f"(total: {self._mgr.event_count}).")

    # ── Manual event ──────────────────────────
    def _add_custom_event(self) -> None:
        print()
        try:
            src  = self._prompt("Source IP       : ")
            dst  = self._prompt("Destination IP  : ")
            print(f"  Protocols       : {', '.join(PROTOCOLS)}")
            proto = self._prompt("Protocol        : ").upper()
            port  = int(self._prompt("Port (0-65535)  : "))
            print(f"  Activity types  :")
            for i, a in enumerate(ACTIVITY_TYPES, 1):
                print(f"    {i:>2}. {a}")
            idx  = int(self._prompt("Activity # (1-{len(ACTIVITY_TYPES)}): ")) - 1
            act  = ACTIVITY_TYPES[idx]
            ev   = self._mgr.add_event(src, dst, proto, port, act)
            print(f"\n  ✔  Event added: {ev}")
        except (ValueError, IndexError) as exc:
            print(f"\n  [!] {exc}")

    # ── Analysis ──────────────────────────────
    def _run_analysis(self) -> None:
        if self._mgr.event_count == 0:
            print("\n  [!] No events to analyse. Simulate some first.\n")
            return
        new_alerts = self._mgr.run_analysis()
        if new_alerts:
            print(f"\n  ✔  Analysis complete — {len(new_alerts)} new alert(s) raised:\n")
            for alert in new_alerts:
                alert.display()
                print()
        else:
            print(f"\n  ✔  Analysis complete — no NEW alerts (total stored: "
                  f"{self._mgr.alert_count}).\n")

    # ── Main loop ─────────────────────────────
    def run(self) -> None:
        print(BANNER)
        dispatch = {
            "1": self._simulate_scenario,
            "2": self._add_custom_event,
            "3": self._mgr.display_event_history,
            "4": self._clear_events,
            "5": self._run_analysis,
            "6": self._mgr.display_alerts,
            "7": lambda: self._mgr.display_alerts(severity_filter=3),
            "8": self._mgr.display_summary,
            "9": self._clear_alerts,
            "0": None,
        }

        while True:
            try:
                choice = input(MAIN_MENU).strip()
                if choice == "0":
                    print("\n  IDS shutdown. Goodbye!\n")
                    break
                action = dispatch.get(choice)
                if action is None:
                    print("  [!] Invalid choice. Enter 0-9.")
                else:
                    action()
            except KeyboardInterrupt:
                print("\n\n  Interrupted. Goodbye!\n")
                break
            except Exception as exc:
                print(f"\n  [!] Unexpected error: {exc}\n")

    def _clear_events(self) -> None:
        confirm = self._prompt(
            f"Clear all {self._mgr.event_count} events? (yes/no): "
        ).lower()
        if confirm in ("yes", "y"):
            self._mgr.clear_events()
            print("  ✔  Events cleared.")
        else:
            print("  Cancelled.")

    def _clear_alerts(self) -> None:
        confirm = self._prompt(
            f"Clear all {self._mgr.alert_count} alerts? (yes/no): "
        ).lower()
        if confirm in ("yes", "y"):
            self._mgr.clear_alerts()
            print("  ✔  Alerts cleared.")
        else:
            print("  Cancelled.")


# ═══════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    CLI().run()