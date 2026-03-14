"""
mini_soc_console.py
====================
A simulated Security Operations Center (SOC) console.
Security analysts can monitor events, triage alerts, and manage incidents.
Built with Python OOP: encapsulation, abstraction, and modularity.
"""

import random
import uuid
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────
# ANSI colour helpers
# ─────────────────────────────────────────────────────────────

class Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    ORANGE  = "\033[38;5;208m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    CYAN    = "\033[96m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    GREY    = "\033[90m"
    WHITE   = "\033[97m"

    @staticmethod
    def severity(sev: str) -> str:
        return {
            "CRITICAL": Color.RED,
            "HIGH":     Color.ORANGE,
            "MEDIUM":   Color.YELLOW,
            "LOW":      Color.GREEN,
            "INFO":     Color.CYAN,
        }.get(sev.upper(), Color.RESET)

    @staticmethod
    def status(st: str) -> str:
        return {
            "OPEN":         Color.RED,
            "INVESTIGATING":Color.YELLOW,
            "RESOLVED":     Color.GREEN,
        }.get(st.upper(), Color.RESET)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _short_id(full_id: str) -> str:
    return full_id[:8].upper()


# ─────────────────────────────────────────────────────────────
# SecurityEvent Class
# ─────────────────────────────────────────────────────────────

class SecurityEvent:
    """
    Represents a raw security event ingested from a network source.
    All attributes are private; accessed via read-only properties.
    """

    VALID_TYPES = {
        "BRUTE_FORCE", "PORT_SCAN", "SQL_INJECTION", "XSS_ATTEMPT",
        "MALWARE_DETECTED", "PRIVILEGE_ESCALATION", "DATA_EXFILTRATION",
        "DDOS_TRAFFIC", "UNAUTHORIZED_ACCESS", "PHISHING_CLICK",
        "LATERAL_MOVEMENT", "C2_BEACON", "INSIDER_THREAT", "RECON_ACTIVITY",
    }
    VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}

    def __init__(
        self,
        source_ip: str,
        event_type: str,
        severity: str,
        description: str,
    ):
        self._validate(source_ip, event_type, severity, description)
        self.__event_id   = str(uuid.uuid4())
        self.__source_ip  = source_ip.strip()
        self.__event_type = event_type.upper().strip()
        self.__severity   = severity.upper().strip()
        self.__description = description.strip()
        self.__timestamp  = _now()

    # ── Validation ───────────────────────────

    @classmethod
    def _validate(cls, ip, etype, sev, desc):
        if not ip or not isinstance(ip, str):
            raise ValueError("source_ip must be a non-empty string.")
        if etype.upper() not in cls.VALID_TYPES:
            raise ValueError(
                f"Invalid event_type '{etype}'. "
                f"Valid types: {', '.join(sorted(cls.VALID_TYPES))}"
            )
        if sev.upper() not in cls.VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{sev}'. Must be one of {cls.VALID_SEVERITIES}.")
        if not desc or not isinstance(desc, str):
            raise ValueError("description must be a non-empty string.")

    # ── Properties ───────────────────────────

    @property
    def event_id(self)   -> str: return self.__event_id
    @property
    def source_ip(self)  -> str: return self.__source_ip
    @property
    def event_type(self) -> str: return self.__event_type
    @property
    def severity(self)   -> str: return self.__severity
    @property
    def description(self)-> str: return self.__description
    @property
    def timestamp(self)  -> str: return self.__timestamp

    def __repr__(self) -> str:
        return (f"SecurityEvent({_short_id(self.__event_id)} | "
                f"{self.__event_type} | {self.__severity} | {self.__source_ip})")


# ─────────────────────────────────────────────────────────────
# Alert Class
# ─────────────────────────────────────────────────────────────

class Alert:
    """
    Represents an alert raised by the SOCAnalyzer for a suspicious SecurityEvent.
    Tracks lifecycle: OPEN → INVESTIGATING → RESOLVED.
    """

    VALID_STATUSES = {"OPEN", "INVESTIGATING", "RESOLVED"}

    def __init__(self, event: SecurityEvent, rule_triggered: str):
        if not isinstance(event, SecurityEvent):
            raise TypeError("event must be a SecurityEvent instance.")
        self.__alert_id       = str(uuid.uuid4())
        self.__event          = event
        self.__rule_triggered = rule_triggered
        self.__status         = "OPEN"
        self.__created_at     = _now()
        self.__updated_at     = _now()
        self.__analyst_notes  = ""
        self.__resolved_at: Optional[str] = None

    # ── Properties ───────────────────────────

    @property
    def alert_id(self)       -> str: return self.__alert_id
    @property
    def event(self)          -> SecurityEvent: return self.__event
    @property
    def rule_triggered(self) -> str: return self.__rule_triggered
    @property
    def status(self)         -> str: return self.__status
    @property
    def created_at(self)     -> str: return self.__created_at
    @property
    def updated_at(self)     -> str: return self.__updated_at
    @property
    def analyst_notes(self)  -> str: return self.__analyst_notes
    @property
    def resolved_at(self)    -> Optional[str]: return self.__resolved_at

    # ── State Transitions ────────────────────

    def investigate(self, notes: str = "") -> None:
        if self.__status == "RESOLVED":
            raise RuntimeError("Cannot investigate a resolved alert.")
        self.__status     = "INVESTIGATING"
        self.__updated_at = _now()
        if notes:
            self.__analyst_notes = notes.strip()

    def resolve(self, notes: str = "") -> None:
        if self.__status == "RESOLVED":
            raise RuntimeError("Alert is already resolved.")
        self.__status      = "RESOLVED"
        self.__resolved_at = _now()
        self.__updated_at  = _now()
        if notes:
            self.__analyst_notes = notes.strip()

    def add_note(self, notes: str) -> None:
        if not notes.strip():
            raise ValueError("Notes cannot be empty.")
        self.__analyst_notes = notes.strip()
        self.__updated_at = _now()

    def __repr__(self) -> str:
        return (f"Alert({_short_id(self.__alert_id)} | "
                f"{self.__event.event_type} | {self.__status})")


# ─────────────────────────────────────────────────────────────
# SOCAnalyzer Class
# ─────────────────────────────────────────────────────────────

class SOCAnalyzer:
    """
    Applies predefined detection rules to SecurityEvent objects.
    Generates Alert instances when rules are triggered.
    """

    # Each rule: (rule_name, lambda event → bool)
    _RULES: list[tuple[str, object]] = [
        ("R001: Critical severity auto-escalation",
         lambda e: e.severity == "CRITICAL"),

        ("R002: Brute-force attack detected",
         lambda e: e.event_type == "BRUTE_FORCE"),

        ("R003: Active C2 beacon communication",
         lambda e: e.event_type == "C2_BEACON"),

        ("R004: Malware detected on host",
         lambda e: e.event_type == "MALWARE_DETECTED"),

        ("R005: Data exfiltration attempt",
         lambda e: e.event_type == "DATA_EXFILTRATION"),

        ("R006: Privilege escalation attempt",
         lambda e: e.event_type == "PRIVILEGE_ESCALATION"),

        ("R007: High-severity lateral movement",
         lambda e: e.event_type == "LATERAL_MOVEMENT" and e.severity in ("HIGH", "CRITICAL")),

        ("R008: SQL injection on production IP",
         lambda e: e.event_type == "SQL_INJECTION" and e.severity in ("HIGH", "CRITICAL")),

        ("R009: DDoS traffic surge",
         lambda e: e.event_type == "DDOS_TRAFFIC" and e.severity in ("HIGH", "CRITICAL")),

        ("R010: Insider threat activity",
         lambda e: e.event_type == "INSIDER_THREAT"),

        ("R011: Phishing click — user compromised",
         lambda e: e.event_type == "PHISHING_CLICK" and e.severity in ("HIGH", "CRITICAL")),

        ("R012: Unauthorized access attempt",
         lambda e: e.event_type == "UNAUTHORIZED_ACCESS" and e.severity in ("HIGH", "CRITICAL", "MEDIUM")),
    ]

    @classmethod
    def analyze(cls, event: SecurityEvent) -> list[Alert]:
        """
        Evaluate all rules against the event.
        Returns a (possibly empty) list of Alert objects.
        """
        if not isinstance(event, SecurityEvent):
            raise TypeError("event must be a SecurityEvent instance.")
        alerts = []
        for rule_name, condition in cls._RULES:
            try:
                if condition(event):
                    alerts.append(Alert(event, rule_name))
            except Exception:
                pass  # Rule evaluation errors are silently skipped
        return alerts

    @classmethod
    def list_rules(cls) -> list[str]:
        return [name for name, _ in cls._RULES]


# ─────────────────────────────────────────────────────────────
# SOCManager Class
# ─────────────────────────────────────────────────────────────

class SOCManager:
    """
    Central manager for the SOC console.
    Stores events and alerts, orchestrates analysis, and provides reporting.
    """

    def __init__(self):
        self.__events: list[SecurityEvent] = []
        self.__alerts: dict[str, Alert]    = {}   # alert_id → Alert
        self.__analyzer = SOCAnalyzer()

    # ── Event Ingestion ──────────────────────

    def ingest_event(self, event: SecurityEvent) -> list[Alert]:
        """Store an event and run analysis. Returns any generated alerts."""
        if not isinstance(event, SecurityEvent):
            raise TypeError("Must pass a SecurityEvent instance.")
        self.__events.append(event)
        new_alerts = self.__analyzer.analyze(event)
        for alert in new_alerts:
            self.__alerts[alert.alert_id] = alert
        return new_alerts

    # ── Alert Management ─────────────────────

    def get_alert(self, alert_id_prefix: str) -> Optional[Alert]:
        """Find alert by full or 8-char prefix of alert_id (case-insensitive)."""
        prefix = alert_id_prefix.strip().lower()
        for aid, alert in self.__alerts.items():
            if aid.lower().startswith(prefix):
                return alert
        return None

    def open_alerts(self) -> list[Alert]:
        return [a for a in self.__alerts.values() if a.status == "OPEN"]

    def investigating_alerts(self) -> list[Alert]:
        return [a for a in self.__alerts.values() if a.status == "INVESTIGATING"]

    def resolved_alerts(self) -> list[Alert]:
        return [a for a in self.__alerts.values() if a.status == "RESOLVED"]

    def all_alerts(self) -> list[Alert]:
        return list(self.__alerts.values())

    def all_events(self) -> list[SecurityEvent]:
        return list(self.__events)

    # ── Statistics ───────────────────────────

    def stats(self) -> dict:
        alerts = list(self.__alerts.values())
        sev_counts: dict[str, int] = {}
        for e in self.__events:
            sev_counts[e.severity] = sev_counts.get(e.severity, 0) + 1

        return {
            "total_events":    len(self.__events),
            "total_alerts":    len(alerts),
            "open":            sum(1 for a in alerts if a.status == "OPEN"),
            "investigating":   sum(1 for a in alerts if a.status == "INVESTIGATING"),
            "resolved":        sum(1 for a in alerts if a.status == "RESOLVED"),
            "severity_counts": sev_counts,
        }


# ─────────────────────────────────────────────────────────────
# Simulated Event Generator
# ─────────────────────────────────────────────────────────────

class EventSimulator:
    """Generates realistic-looking synthetic SecurityEvent objects."""

    _IPS = [
        "192.168.1.105", "10.0.0.44", "172.16.0.23", "203.0.113.77",
        "198.51.100.12", "185.220.101.42", "91.108.4.188", "45.142.212.100",
        "10.10.5.88", "192.168.3.200", "66.249.64.1", "104.16.0.0",
    ]

    _SCENARIOS: list[tuple[str, str, str]] = [
        ("BRUTE_FORCE",         "HIGH",     "Multiple failed SSH login attempts detected (>50 in 60s)."),
        ("BRUTE_FORCE",         "CRITICAL", "Credential stuffing attack — 500+ attempts across 20 accounts."),
        ("PORT_SCAN",           "MEDIUM",   "Horizontal port scan across /24 subnet detected."),
        ("PORT_SCAN",           "LOW",      "Vertical port scan on single host, low rate."),
        ("SQL_INJECTION",       "CRITICAL", "SQL injection payload in POST /login; possible auth bypass."),
        ("SQL_INJECTION",       "HIGH",     "Union-based SQLi detected in search endpoint."),
        ("XSS_ATTEMPT",         "MEDIUM",   "Reflected XSS payload in query parameter."),
        ("MALWARE_DETECTED",    "CRITICAL", "Ransomware dropper detected: Ryuk variant. Quarantine initiated."),
        ("MALWARE_DETECTED",    "HIGH",     "Trojan horse binary flagged by AV on endpoint 10.0.0.44."),
        ("PRIVILEGE_ESCALATION","CRITICAL", "Kernel exploit (CVE-2023-XXXX) used to gain root on web server."),
        ("PRIVILEGE_ESCALATION","HIGH",     "Sudo abuse detected — non-admin user executed privileged command."),
        ("DATA_EXFILTRATION",   "CRITICAL", "Large DNS TXT record exfil detected — 400MB over 2 hours."),
        ("DATA_EXFILTRATION",   "HIGH",     "Unusual outbound HTTPS traffic to uncategorised domain."),
        ("DDOS_TRAFFIC",        "CRITICAL", "SYN flood targeting port 443 — 2M PPS from botnet."),
        ("DDOS_TRAFFIC",        "HIGH",     "HTTP flood against /api/login — 50K RPS from multiple IPs."),
        ("UNAUTHORIZED_ACCESS", "HIGH",     "Successful login from impossible travel — NY then HK within 1hr."),
        ("UNAUTHORIZED_ACCESS", "MEDIUM",   "After-hours admin panel access from unrecognised device."),
        ("PHISHING_CLICK",      "HIGH",     "User clicked phishing URL; credential harvesting page loaded."),
        ("PHISHING_CLICK",      "CRITICAL", "Multiple users in Finance clicked same phishing link."),
        ("LATERAL_MOVEMENT",    "CRITICAL", "Pass-the-hash attack across domain; 5 hosts compromised."),
        ("LATERAL_MOVEMENT",    "HIGH",     "SMB lateral movement detected using stolen credentials."),
        ("C2_BEACON",           "CRITICAL", "Regular 60s interval beaconing to known Cobalt Strike C2."),
        ("C2_BEACON",           "HIGH",     "DNS-based C2 communication detected via long TXT lookups."),
        ("INSIDER_THREAT",      "HIGH",     "Bulk download of customer PII database by departing employee."),
        ("INSIDER_THREAT",      "CRITICAL", "Privileged user accessed 10,000 records outside work hours."),
        ("RECON_ACTIVITY",      "LOW",      "Public OSINT scraping detected against corporate domain."),
        ("RECON_ACTIVITY",      "MEDIUM",   "Active directory enumeration via LDAP queries from internal IP."),
    ]

    @classmethod
    def random_event(cls) -> SecurityEvent:
        etype, sev, desc = random.choice(cls._SCENARIOS)
        ip = random.choice(cls._IPS)
        return SecurityEvent(ip, etype, sev, desc)

    @classmethod
    def bulk_events(cls, n: int) -> list[SecurityEvent]:
        return [cls.random_event() for _ in range(n)]


# ─────────────────────────────────────────────────────────────
# Display / Rendering Helpers
# ─────────────────────────────────────────────────────────────

_W = 70  # console width

def _sep(ch="─"):        print(f"  {ch * (_W - 2)}")
def _head(ch="═"):       print(f"  {ch * (_W - 2)}")
def _title(text):
    pad = (_W - 2 - len(text)) // 2
    print(f"  {'═' * (_W-2)}")
    print(f"  {' ' * pad}{Color.BOLD}{text}{Color.RESET}")
    print(f"  {'═' * (_W-2)}")


def print_banner():
    print(f"""
{Color.CYAN}  {'▓' * (_W - 2)}{Color.RESET}
{Color.BOLD}{Color.CYAN}  {'SOC MONITOR — MINI SECURITY OPERATIONS CENTER':^{_W-2}}{Color.RESET}
{Color.GREY}  {'Analyst Console  v2.0':^{_W-2}}{Color.RESET}
{Color.CYAN}  {'▓' * (_W - 2)}{Color.RESET}
""")


def print_menu():
    opts = [
        ("1", "Simulate incoming security event(s)"),
        ("2", "View all security events"),
        ("3", "View active alerts  [OPEN / INVESTIGATING]"),
        ("4", "Investigate an alert"),
        ("5", "Resolve an alert"),
        ("6", "Add analyst note to alert"),
        ("7", "View full alert detail"),
        ("8", "View resolved alerts"),
        ("9", "View detection rules"),
        ("0", "SOC Statistics dashboard"),
        ("X", "Exit console"),
    ]
    _head()
    print(f"  {Color.BOLD}  ANALYST MENU{Color.RESET}")
    _sep()
    for key, label in opts:
        print(f"    {Color.CYAN}[{key}]{Color.RESET}  {label}")
    _head()


def _render_severity(sev: str) -> str:
    return f"{Color.severity(sev)}{Color.BOLD}{sev:<8}{Color.RESET}"


def _render_status(st: str) -> str:
    return f"{Color.status(st)}{Color.BOLD}{st:<13}{Color.RESET}"


def print_event_table(events: list[SecurityEvent]) -> None:
    if not events:
        print(f"\n  {Color.GREY}No events to display.{Color.RESET}\n")
        return
    _head()
    print(f"  {Color.BOLD}  SECURITY EVENTS  ({len(events)} total){Color.RESET}")
    _sep()
    print(f"  {'#':<4} {'Time':<20} {'Source IP':<16} {'Type':<22} {'SEV':<10}")
    _sep()
    for i, e in enumerate(events[-30:], 1):  # show last 30
        sev = _render_severity(e.severity)
        print(f"  {i:<4} {e.timestamp:<20} {e.source_ip:<16} {e.event_type:<22} {sev}")
    if len(events) > 30:
        print(f"\n  {Color.GREY}  ... showing last 30 of {len(events)} events.{Color.RESET}")
    _head()


def print_alert_table(alerts: list[Alert], title: str = "ALERTS") -> None:
    if not alerts:
        print(f"\n  {Color.GREY}No alerts to display.{Color.RESET}\n")
        return
    _head()
    print(f"  {Color.BOLD}  {title}  ({len(alerts)} total){Color.RESET}")
    _sep()
    print(f"  {'Alert ID':<10} {'Created':<20} {'Type':<22} {'SEV':<10} {'Status'}")
    _sep()
    for a in alerts:
        sev    = _render_severity(a.event.severity)
        status = _render_status(a.status)
        print(f"  {_short_id(a.alert_id):<10} {a.created_at:<20} "
              f"{a.event.event_type:<22} {sev} {status}")
    _head()


def print_alert_detail(alert: Alert) -> None:
    e = alert.event
    _head()
    print(f"  {Color.BOLD}  ALERT DETAIL{Color.RESET}")
    _sep()
    print(f"  Alert ID      : {Color.CYAN}{_short_id(alert.alert_id)}{Color.RESET}  "
          f"({alert.alert_id})")
    print(f"  Status        : {_render_status(alert.status)}")
    print(f"  Rule          : {alert.rule_triggered}")
    print(f"  Created       : {alert.created_at}")
    print(f"  Last Updated  : {alert.updated_at}")
    if alert.resolved_at:
        print(f"  Resolved At   : {Color.GREEN}{alert.resolved_at}{Color.RESET}")
    _sep()
    print(f"  {Color.BOLD}  ORIGINATING EVENT{Color.RESET}")
    _sep()
    print(f"  Event ID      : {_short_id(e.event_id)}")
    print(f"  Timestamp     : {e.timestamp}")
    print(f"  Source IP     : {Color.YELLOW}{e.source_ip}{Color.RESET}")
    print(f"  Event Type    : {e.event_type}")
    print(f"  Severity      : {_render_severity(e.severity)}")
    print(f"  Description   :")
    # Word-wrap description
    words = e.description.split()
    line, lines = [], []
    for w in words:
        if len(" ".join(line + [w])) > 58:
            lines.append(" ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append(" ".join(line))
    for ln in lines:
        print(f"    {ln}")
    if alert.analyst_notes:
        _sep()
        print(f"  {Color.BOLD}  ANALYST NOTES{Color.RESET}")
        print(f"    {Color.WHITE}{alert.analyst_notes}{Color.RESET}")
    _head()


def print_stats(stats: dict) -> None:
    _head()
    print(f"  {Color.BOLD}  SOC STATISTICS DASHBOARD{Color.RESET}")
    _sep()
    print(f"  Total Events Ingested : {Color.CYAN}{stats['total_events']}{Color.RESET}")
    print(f"  Total Alerts Generated: {Color.CYAN}{stats['total_alerts']}{Color.RESET}")
    _sep()
    print(f"  {Color.BOLD}  Alert Status Breakdown{Color.RESET}")
    print(f"    {Color.RED}OPEN          : {stats['open']}{Color.RESET}")
    print(f"    {Color.YELLOW}INVESTIGATING : {stats['investigating']}{Color.RESET}")
    print(f"    {Color.GREEN}RESOLVED      : {stats['resolved']}{Color.RESET}")
    _sep()
    print(f"  {Color.BOLD}  Events by Severity{Color.RESET}")
    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    for sev in order:
        count = stats["severity_counts"].get(sev, 0)
        bar = "█" * min(count, 40)
        c = Color.severity(sev)
        print(f"    {c}{sev:<10}{Color.RESET} {bar} {count}")
    _head()


# ─────────────────────────────────────────────────────────────
# CLI Helpers
# ─────────────────────────────────────────────────────────────

def _input(prompt: str) -> str:
    return input(f"\n  {Color.CYAN}>{Color.RESET} {prompt} ").strip()


def _confirm(msg: str) -> bool:
    ans = _input(f"{msg} (y/n):").lower()
    return ans == "y"


def get_menu_choice(valid: set) -> str:
    while True:
        choice = _input("Select option:").upper()
        if choice in valid:
            return choice
        print(f"  {Color.RED}[!] Invalid choice. Options: {', '.join(sorted(valid))}{Color.RESET}")


# ─────────────────────────────────────────────────────────────
# Menu Action Functions
# ─────────────────────────────────────────────────────────────

def cmd_simulate(manager: SOCManager) -> None:
    """Simulate 1 or more incoming events."""
    print(f"\n  {Color.BOLD}── Simulate Events ──{Color.RESET}")
    raw = _input("How many events to simulate? [1-20, default 1]:")
    try:
        n = int(raw) if raw else 1
        if not 1 <= n <= 20:
            raise ValueError
    except ValueError:
        print(f"  {Color.RED}[!] Enter a number between 1 and 20.{Color.RESET}")
        return

    total_alerts = 0
    for _ in range(n):
        event = EventSimulator.random_event()
        alerts = manager.ingest_event(event)
        sev_col = Color.severity(event.severity)
        print(f"\n  {Color.GREY}[{_now()}]{Color.RESET} "
              f"{sev_col}[{event.severity}]{Color.RESET} "
              f"{event.event_type} from {Color.YELLOW}{event.source_ip}{Color.RESET}")
        print(f"    {Color.GREY}{event.description[:70]}{Color.RESET}")
        if alerts:
            for a in alerts:
                print(f"    {Color.RED}⚑ ALERT RAISED:{Color.RESET} "
                      f"{_short_id(a.alert_id)} — {a.rule_triggered}")
            total_alerts += len(alerts)
        else:
            print(f"    {Color.GREEN}✓ No alert triggered.{Color.RESET}")

    print(f"\n  {Color.CYAN}[+]{Color.RESET} {n} event(s) ingested. "
          f"{Color.RED}{total_alerts} alert(s) raised.{Color.RESET}")


def cmd_view_events(manager: SOCManager) -> None:
    print_event_table(manager.all_events())


def cmd_view_active_alerts(manager: SOCManager) -> None:
    active = manager.open_alerts() + manager.investigating_alerts()
    active.sort(key=lambda a: a.created_at, reverse=True)
    print_alert_table(active, "ACTIVE ALERTS (OPEN + INVESTIGATING)")


def cmd_investigate(manager: SOCManager) -> None:
    active = manager.open_alerts()
    if not active:
        print(f"\n  {Color.GREEN}✓ No open alerts to investigate.{Color.RESET}")
        return

    print_alert_table(active, "OPEN ALERTS")
    aid = _input("Enter Alert ID (8-char prefix) to investigate:")
    alert = manager.get_alert(aid)
    if not alert:
        print(f"  {Color.RED}[!] Alert '{aid}' not found.{Color.RESET}")
        return
    if alert.status != "OPEN":
        print(f"  {Color.YELLOW}[!] Alert is already '{alert.status}'.{Color.RESET}")
        return

    notes = _input("Add analyst note (optional, press ENTER to skip):")
    try:
        alert.investigate(notes)
        print(f"  {Color.YELLOW}[→] Alert {_short_id(alert.alert_id)} marked as INVESTIGATING.{Color.RESET}")
    except RuntimeError as e:
        print(f"  {Color.RED}[!] {e}{Color.RESET}")


def cmd_resolve(manager: SOCManager) -> None:
    active = manager.open_alerts() + manager.investigating_alerts()
    if not active:
        print(f"\n  {Color.GREEN}✓ No active alerts to resolve.{Color.RESET}")
        return

    print_alert_table(active, "ACTIVE ALERTS")
    aid = _input("Enter Alert ID (8-char prefix) to resolve:")
    alert = manager.get_alert(aid)
    if not alert:
        print(f"  {Color.RED}[!] Alert '{aid}' not found.{Color.RESET}")
        return
    if alert.status == "RESOLVED":
        print(f"  {Color.GREEN}[✓] Alert already resolved.{Color.RESET}")
        return

    notes = _input("Resolution notes (required):")
    if not notes:
        print(f"  {Color.RED}[!] Resolution notes are required.{Color.RESET}")
        return
    try:
        alert.resolve(notes)
        print(f"  {Color.GREEN}[✓] Alert {_short_id(alert.alert_id)} marked as RESOLVED.{Color.RESET}")
    except RuntimeError as e:
        print(f"  {Color.RED}[!] {e}{Color.RESET}")


def cmd_add_note(manager: SOCManager) -> None:
    all_a = manager.all_alerts()
    if not all_a:
        print(f"\n  {Color.GREY}No alerts exist yet.{Color.RESET}")
        return

    active = manager.open_alerts() + manager.investigating_alerts()
    print_alert_table(active or all_a, "ALERTS")
    aid = _input("Enter Alert ID (8-char prefix):")
    alert = manager.get_alert(aid)
    if not alert:
        print(f"  {Color.RED}[!] Alert not found.{Color.RESET}")
        return
    note = _input("Enter note:")
    if not note:
        print(f"  {Color.RED}[!] Note cannot be empty.{Color.RESET}")
        return
    try:
        alert.add_note(note)
        print(f"  {Color.GREEN}[✓] Note added to alert {_short_id(alert.alert_id)}.{Color.RESET}")
    except ValueError as e:
        print(f"  {Color.RED}[!] {e}{Color.RESET}")


def cmd_alert_detail(manager: SOCManager) -> None:
    all_a = manager.all_alerts()
    if not all_a:
        print(f"\n  {Color.GREY}No alerts exist yet.{Color.RESET}")
        return
    print_alert_table(all_a, "ALL ALERTS")
    aid = _input("Enter Alert ID (8-char prefix) for full detail:")
    alert = manager.get_alert(aid)
    if not alert:
        print(f"  {Color.RED}[!] Alert not found.{Color.RESET}")
    else:
        print_alert_detail(alert)


def cmd_resolved(manager: SOCManager) -> None:
    print_alert_table(manager.resolved_alerts(), "RESOLVED ALERTS")


def cmd_rules() -> None:
    rules = SOCAnalyzer.list_rules()
    _head()
    print(f"  {Color.BOLD}  DETECTION RULES  ({len(rules)} active){Color.RESET}")
    _sep()
    for rule in rules:
        print(f"    {Color.CYAN}•{Color.RESET}  {rule}")
    _head()


def cmd_stats(manager: SOCManager) -> None:
    print_stats(manager.stats())


# ─────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────

def main():
    print_banner()
    manager = SOCManager()

    VALID = {"1","2","3","4","5","6","7","8","9","0","X"}
    DISPATCH = {
        "1": lambda: cmd_simulate(manager),
        "2": lambda: cmd_view_events(manager),
        "3": lambda: cmd_view_active_alerts(manager),
        "4": lambda: cmd_investigate(manager),
        "5": lambda: cmd_resolve(manager),
        "6": lambda: cmd_add_note(manager),
        "7": lambda: cmd_alert_detail(manager),
        "8": lambda: cmd_resolved(manager),
        "9": lambda: cmd_rules(),
        "0": lambda: cmd_stats(manager),
    }

    while True:
        # Mini status bar
        s = manager.stats()
        open_c  = s["open"]
        inv_c   = s["investigating"]
        print(f"\n  {Color.GREY}Events: {s['total_events']}  │  "
              f"{Color.RED}Open: {open_c}{Color.GREY}  │  "
              f"{Color.YELLOW}Investigating: {inv_c}{Color.GREY}  │  "
              f"{Color.GREEN}Resolved: {s['resolved']}{Color.RESET}")

        print_menu()
        choice = get_menu_choice(VALID)

        if choice == "X":
            print(f"\n  {Color.CYAN}[*] Logging out of SOC console. Stay vigilant.{Color.RESET}\n")
            break

        try:
            DISPATCH[choice]()
        except Exception as exc:
            print(f"\n  {Color.RED}[ERROR] Unexpected error: {exc}{Color.RESET}")


if __name__ == "__main__":
    main()