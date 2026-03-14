"""
security_report_generator.py
=============================
Generate structured security reports from analyzed events/incidents.
Built with Python OOP: encapsulation, abstraction, and modularity.
"""

import uuid
import json
import os
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────
# ANSI Colour Helpers
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
    def sev(s: str) -> str:
        return {
            "CRITICAL": Color.RED,
            "HIGH":     Color.ORANGE,
            "MEDIUM":   Color.YELLOW,
            "LOW":      Color.GREEN,
            "INFO":     Color.CYAN,
        }.get(s.upper(), Color.RESET)


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def _short(uid: str) -> str:
    return uid[:8].upper()


# ─────────────────────────────────────────────────────────────
# SecurityEvent Class
# ─────────────────────────────────────────────────────────────

class SecurityEvent:
    """
    Immutable record of a single security event.
    All data is private and accessed through read-only properties.
    """

    VALID_TYPES = {
        "INTRUSION", "MALWARE", "DATA_BREACH", "PHISHING",
        "DDOS", "PRIVILEGE_ESCALATION", "POLICY_VIOLATION",
        "VULNERABILITY", "UNAUTHORIZED_ACCESS", "RANSOMWARE",
        "INSIDER_THREAT", "RECONNAISSANCE", "LATERAL_MOVEMENT",
        "CREDENTIAL_THEFT", "SUPPLY_CHAIN",
    }
    VALID_SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    _SEV_RANK = {s: i for i, s in enumerate(reversed(VALID_SEVERITIES))}

    def __init__(
        self,
        event_type: str,
        severity: str,
        description: str,
        source: str = "Unknown",
        affected_asset: str = "Unknown",
    ):
        etype = event_type.upper().strip()
        sev   = severity.upper().strip()
        if etype not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid event_type '{event_type}'.\n"
                f"    Valid types: {', '.join(sorted(self.VALID_TYPES))}"
            )
        if sev not in self.VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{severity}'.\n"
                f"    Valid: {', '.join(self.VALID_SEVERITIES)}"
            )
        if not description.strip():
            raise ValueError("description cannot be empty.")

        self.__event_id       = str(uuid.uuid4())
        self.__event_type     = etype
        self.__severity       = sev
        self.__description    = description.strip()
        self.__source         = source.strip()
        self.__affected_asset = affected_asset.strip()
        self.__timestamp      = _now_str()

    # Read-only properties
    @property
    def event_id(self)       -> str: return self.__event_id
    @property
    def event_type(self)     -> str: return self.__event_type
    @property
    def severity(self)       -> str: return self.__severity
    @property
    def description(self)    -> str: return self.__description
    @property
    def source(self)         -> str: return self.__source
    @property
    def affected_asset(self) -> str: return self.__affected_asset
    @property
    def timestamp(self)      -> str: return self.__timestamp
    @property
    def severity_rank(self)  -> int: return self._SEV_RANK.get(self.__severity, 0)

    def to_dict(self) -> dict:
        return {
            "event_id":       self.__event_id,
            "event_type":     self.__event_type,
            "severity":       self.__severity,
            "description":    self.__description,
            "source":         self.__source,
            "affected_asset": self.__affected_asset,
            "timestamp":      self.__timestamp,
        }

    def __repr__(self) -> str:
        return (f"SecurityEvent({_short(self.__event_id)} | "
                f"{self.__event_type} | {self.__severity})")


# ─────────────────────────────────────────────────────────────
# SecurityReport Class
# ─────────────────────────────────────────────────────────────

class SecurityReport:
    """
    Structured report that aggregates SecurityEvent objects and
    provides analytical summaries and risk scores.
    """

    def __init__(self, title: str, analyst: str = "Automated System"):
        if not title.strip():
            raise ValueError("Report title cannot be empty.")
        self.__report_id     = str(uuid.uuid4())
        self.__title         = title.strip()
        self.__analyst       = analyst.strip()
        self.__creation_date = _date_str()
        self.__created_at    = _now_str()
        self.__events:  list[SecurityEvent] = []
        self.__findings:list[str]           = []
        self.__recommendations: list[str]   = []

    # ── Properties ───────────────────────────

    @property
    def report_id(self)       -> str:  return self.__report_id
    @property
    def title(self)           -> str:  return self.__title
    @property
    def analyst(self)         -> str:  return self.__analyst
    @property
    def creation_date(self)   -> str:  return self.__creation_date
    @property
    def created_at(self)      -> str:  return self.__created_at
    @property
    def events(self)          -> list: return list(self.__events)
    @property
    def findings(self)        -> list: return list(self.__findings)
    @property
    def recommendations(self) -> list: return list(self.__recommendations)

    # ── Mutation via controlled methods ──────

    def add_event(self, event: SecurityEvent) -> None:
        if not isinstance(event, SecurityEvent):
            raise TypeError("Only SecurityEvent instances can be added.")
        # Avoid exact duplicates (same event_id)
        if any(e.event_id == event.event_id for e in self.__events):
            raise ValueError(f"Event {_short(event.event_id)} is already in this report.")
        self.__events.append(event)

    def add_finding(self, finding: str) -> None:
        if finding.strip():
            self.__findings.append(finding.strip())

    def add_recommendation(self, rec: str) -> None:
        if rec.strip():
            self.__recommendations.append(rec.strip())

    # ── Analytics ────────────────────────────

    def severity_breakdown(self) -> dict:
        counts = {s: 0 for s in SecurityEvent.VALID_SEVERITIES}
        for e in self.__events:
            counts[e.severity] += 1
        return counts

    def type_breakdown(self) -> dict:
        counts: dict[str, int] = {}
        for e in self.__events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def risk_score(self) -> int:
        """
        Weighted risk score 0-100 based on event severities.
        CRITICAL=20, HIGH=10, MEDIUM=5, LOW=2, INFO=1
        Capped at 100.
        """
        weights = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 2, "INFO": 1}
        total = sum(weights.get(e.severity, 0) for e in self.__events)
        return min(total, 100)

    def risk_label(self) -> str:
        score = self.risk_score()
        if score >= 80: return "CRITICAL"
        if score >= 60: return "HIGH"
        if score >= 35: return "MEDIUM"
        if score >= 10: return "LOW"
        return "MINIMAL"

    def top_events(self, n: int = 5) -> list:
        return sorted(self.__events, key=lambda e: e.severity_rank, reverse=True)[:n]

    def to_dict(self) -> dict:
        return {
            "report_id":       self.__report_id,
            "title":           self.__title,
            "analyst":         self.__analyst,
            "creation_date":   self.__creation_date,
            "created_at":      self.__created_at,
            "risk_score":      self.risk_score(),
            "risk_label":      self.risk_label(),
            "total_events":    len(self.__events),
            "severity_breakdown": self.severity_breakdown(),
            "type_breakdown":  self.type_breakdown(),
            "findings":        self.__findings,
            "recommendations": self.__recommendations,
            "events":          [e.to_dict() for e in self.__events],
        }

    def __repr__(self) -> str:
        return (f"SecurityReport({_short(self.__report_id)} | "
                f"'{self.__title}' | {len(self.__events)} events)")


# ─────────────────────────────────────────────────────────────
# ReportGenerator Class
# ─────────────────────────────────────────────────────────────

class ReportGenerator:
    """
    Collects SecurityEvents, performs automated analysis,
    generates SecurityReport objects, and handles export.
    """

    # Auto-generated finding templates per event type
    _FINDINGS: dict[str, str] = {
        "INTRUSION":           "External intrusion attempt detected against network perimeter.",
        "MALWARE":             "Malicious software identified on one or more endpoints.",
        "DATA_BREACH":         "Potential data breach — sensitive data may have been exfiltrated.",
        "PHISHING":            "Phishing activity targeting users detected.",
        "DDOS":                "Distributed Denial-of-Service attack traffic observed.",
        "PRIVILEGE_ESCALATION":"Unauthorized privilege escalation attempt recorded.",
        "POLICY_VIOLATION":    "Security policy violation detected — review access controls.",
        "VULNERABILITY":       "Exploitable vulnerability identified in system or application.",
        "UNAUTHORIZED_ACCESS": "Unauthorized access to protected resources detected.",
        "RANSOMWARE":          "Ransomware indicators of compromise identified — isolate affected hosts.",
        "INSIDER_THREAT":      "Insider threat behaviour pattern detected.",
        "RECONNAISSANCE":      "Reconnaissance / scanning activity observed from external source.",
        "LATERAL_MOVEMENT":    "Lateral movement within the network detected.",
        "CREDENTIAL_THEFT":    "Credential theft attempt or credential leak identified.",
        "SUPPLY_CHAIN":        "Supply chain compromise indicators detected.",
    }

    _RECS: dict[str, str] = {
        "INTRUSION":           "Review firewall rules; block source IPs; enable IPS signatures.",
        "MALWARE":             "Isolate affected endpoints; run full AV scan; patch OS and apps.",
        "DATA_BREACH":         "Engage incident response; notify DPO; audit data access logs.",
        "PHISHING":            "Block malicious domains; reset credentials; run phishing training.",
        "DDOS":                "Enable rate-limiting and traffic scrubbing; contact upstream ISP.",
        "PRIVILEGE_ESCALATION":"Revoke elevated privileges; audit sudo/admin groups; patch exploits.",
        "POLICY_VIOLATION":    "Review and enforce security policies; conduct user awareness training.",
        "VULNERABILITY":       "Apply vendor patches immediately; consider virtual patching.",
        "UNAUTHORIZED_ACCESS": "Revoke sessions; enforce MFA; review IAM policies.",
        "RANSOMWARE":          "Isolate hosts; restore from clean backups; engage IR team.",
        "INSIDER_THREAT":      "Suspend access; initiate HR/legal process; preserve audit logs.",
        "RECONNAISSANCE":      "Block scanning IPs; review exposed services; enable honeypots.",
        "LATERAL_MOVEMENT":    "Segment network; rotate credentials; review EDR telemetry.",
        "CREDENTIAL_THEFT":    "Force password reset; enable MFA; monitor for credential reuse.",
        "SUPPLY_CHAIN":        "Audit third-party dependencies; verify software hashes; patch.",
    }

    def __init__(self):
        self.__events:  list[SecurityEvent]  = []
        self.__reports: dict[str, SecurityReport] = {}

    # ── Event Management ─────────────────────

    def add_event(self, event: SecurityEvent) -> None:
        if not isinstance(event, SecurityEvent):
            raise TypeError("Must pass a SecurityEvent instance.")
        self.__events.append(event)

    def remove_event(self, event_id_prefix: str) -> Optional[SecurityEvent]:
        prefix = event_id_prefix.strip().lower()
        for i, e in enumerate(self.__events):
            if e.event_id.lower().startswith(prefix):
                return self.__events.pop(i)
        return None

    def clear_events(self) -> int:
        n = len(self.__events)
        self.__events.clear()
        return n

    def all_events(self) -> list:
        return list(self.__events)

    def get_event(self, prefix: str) -> Optional[SecurityEvent]:
        prefix = prefix.strip().lower()
        for e in self.__events:
            if e.event_id.lower().startswith(prefix):
                return e
        return None

    # ── Report Generation ────────────────────

    def generate_report(self, title: str, analyst: str = "Automated System") -> SecurityReport:
        if not self.__events:
            raise ValueError("Cannot generate a report with no events. Add events first.")
        if not title.strip():
            raise ValueError("Report title cannot be empty.")

        report = SecurityReport(title, analyst)

        # Add all events sorted by severity descending
        for event in sorted(self.__events, key=lambda e: e.severity_rank, reverse=True):
            report.add_event(event)

        # Auto-generate findings (deduplicated by event type)
        seen_types: set[str] = set()
        for event in sorted(self.__events, key=lambda e: e.severity_rank, reverse=True):
            if event.event_type not in seen_types:
                seen_types.add(event.event_type)
                finding = self._FINDINGS.get(event.event_type)
                if finding:
                    report.add_finding(finding)

        # Auto-generate recommendations
        seen_rec: set[str] = set()
        for event in sorted(self.__events, key=lambda e: e.severity_rank, reverse=True):
            if event.event_type not in seen_rec:
                seen_rec.add(event.event_type)
                rec = self._RECS.get(event.event_type)
                if rec:
                    report.add_recommendation(rec)

        self.__reports[report.report_id] = report
        return report

    # ── Report Management ────────────────────

    def all_reports(self) -> list:
        return list(self.__reports.values())

    def get_report(self, prefix: str) -> Optional[SecurityReport]:
        prefix = prefix.strip().lower()
        for rid, r in self.__reports.items():
            if rid.lower().startswith(prefix):
                return r
        return None

    # ── Export Methods ───────────────────────

    def export_txt(self, report: SecurityReport, filepath: str) -> str:
        """Export report as formatted plain-text file."""
        W = 72
        lines = []

        def h1(text):
            lines.append("=" * W)
            lines.append(f"  {text}")
            lines.append("=" * W)

        def h2(text):
            lines.append(f"  {'─' * (W-2)}")
            lines.append(f"  {text}")
            lines.append(f"  {'─' * (W-2)}")

        def row(label, value, pad=20):
            lines.append(f"  {label:<{pad}}: {value}")

        h1(f"SECURITY REPORT — {report.title.upper()}")
        lines.append("")
        row("Report ID",      _short(report.report_id))
        row("Title",          report.title)
        row("Analyst",        report.analyst)
        row("Date",           report.creation_date)
        row("Generated At",   report.created_at)
        row("Total Events",   str(len(report.events)))
        row("Risk Score",     f"{report.risk_score()}/100")
        row("Overall Risk",   report.risk_label())
        lines.append("")

        h2("SEVERITY BREAKDOWN")
        breakdown = report.severity_breakdown()
        for sev in SecurityEvent.VALID_SEVERITIES:
            cnt = breakdown[sev]
            bar = "█" * min(cnt, 40)
            lines.append(f"  {sev:<10} {bar} {cnt}")
        lines.append("")

        h2("EVENT TYPE BREAKDOWN")
        for etype, cnt in report.type_breakdown().items():
            lines.append(f"  {etype:<25} {cnt}")
        lines.append("")

        h2("KEY FINDINGS")
        for i, f in enumerate(report.findings, 1):
            lines.append(f"  {i}. {f}")
        lines.append("")

        h2("RECOMMENDATIONS")
        for i, r in enumerate(report.recommendations, 1):
            lines.append(f"  {i}. {r}")
        lines.append("")

        h2(f"TOP {min(5, len(report.events))} PRIORITY EVENTS")
        for e in report.top_events(5):
            lines.append(f"  [{e.severity}] {e.event_type}")
            lines.append(f"    ID     : {_short(e.event_id)}")
            lines.append(f"    Source : {e.source}")
            lines.append(f"    Asset  : {e.affected_asset}")
            lines.append(f"    Time   : {e.timestamp}")
            lines.append(f"    Desc   : {e.description}")
            lines.append("")

        h2("ALL EVENTS")
        for i, e in enumerate(report.events, 1):
            lines.append(f"  {i:>3}. [{e.severity:<8}] {e.event_type:<25} {e.timestamp}")
            lines.append(f"       {e.description[:65]}")
        lines.append("")
        lines.append("=" * W)
        lines.append("  END OF REPORT")
        lines.append("=" * W)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath

    def export_json(self, report: SecurityReport, filepath: str) -> str:
        """Export report as JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        return filepath


# ─────────────────────────────────────────────────────────────
# Pre-built Event Library (for quick demos)
# ─────────────────────────────────────────────────────────────

SAMPLE_EVENTS = [
    dict(event_type="RANSOMWARE",          severity="CRITICAL",
         description="Ryuk ransomware dropper detected on FINANCE-PC-04; encryption in progress.",
         source="EDR Agent", affected_asset="FINANCE-PC-04"),
    dict(event_type="DATA_BREACH",         severity="CRITICAL",
         description="250,000 customer PII records exfiltrated to external FTP server.",
         source="DLP System", affected_asset="CRM-DB-01"),
    dict(event_type="LATERAL_MOVEMENT",    severity="HIGH",
         description="Pass-the-hash detected; attacker pivoted from DMZ to internal network.",
         source="SIEM", affected_asset="CORP-NET"),
    dict(event_type="CREDENTIAL_THEFT",    severity="HIGH",
         description="LSASS memory dump detected — credential harvest attempted.",
         source="EDR Agent", affected_asset="DC-01"),
    dict(event_type="PHISHING",            severity="HIGH",
         description="Spear-phishing email with malicious macro delivered to 14 executives.",
         source="Email Gateway", affected_asset="Executive Mailboxes"),
    dict(event_type="VULNERABILITY",       severity="HIGH",
         description="CVE-2024-1234 (CVSS 9.8) unpatched on public-facing web server.",
         source="Vuln Scanner", affected_asset="WEB-PROD-02"),
    dict(event_type="INTRUSION",           severity="MEDIUM",
         description="Port scan followed by SSH brute-force from 185.220.101.47.",
         source="Firewall", affected_asset="Perimeter"),
    dict(event_type="PRIVILEGE_ESCALATION",severity="MEDIUM",
         description="Non-admin user executed sudo su on LINUX-SRV-07.",
         source="Syslog", affected_asset="LINUX-SRV-07"),
    dict(event_type="DDOS",                severity="MEDIUM",
         description="HTTP flood: 45,000 req/s against /api/auth endpoint.",
         source="WAF", affected_asset="API-GW-01"),
    dict(event_type="UNAUTHORIZED_ACCESS", severity="MEDIUM",
         description="Admin panel accessed from unrecognized device outside business hours.",
         source="IAM", affected_asset="ADMIN-PORTAL"),
    dict(event_type="POLICY_VIOLATION",    severity="LOW",
         description="User uploaded 2GB to personal Dropbox account from corporate device.",
         source="CASB", affected_asset="EMP-LAPTOP-112"),
    dict(event_type="RECONNAISSANCE",      severity="LOW",
         description="Public subdomain enumeration detected via DNS zone transfer attempt.",
         source="DNS Server", affected_asset="corp.example.com"),
    dict(event_type="MALWARE",             severity="LOW",
         description="PUP (Potentially Unwanted Program) detected; auto-quarantined.",
         source="AV Agent", affected_asset="SALES-PC-09"),
    dict(event_type="INSIDER_THREAT",      severity="HIGH",
         description="Departing employee bulk-downloaded 50,000 source code files.",
         source="DLP System", affected_asset="Code Repository"),
    dict(event_type="SUPPLY_CHAIN",        severity="CRITICAL",
         description="Compromised npm package 'event-stream' detected in build pipeline.",
         source="SAST Tool", affected_asset="CI/CD Pipeline"),
]


# ─────────────────────────────────────────────────────────────
# Display Helpers
# ─────────────────────────────────────────────────────────────

_W = 72

def _sep():   print(f"  {'─' * (_W - 2)}")
def _head():  print(f"  {'=' * (_W - 2)}")


def print_banner():
    print(f"""
{Color.MAGENTA}  {'#' * (_W - 2)}{Color.RESET}
{Color.BOLD}{Color.MAGENTA}  {'SECURITY REPORT GENERATOR':^{_W-2}}{Color.RESET}
{Color.GREY}  {'Incident Analysis & Reporting System  v1.0':^{_W-2}}{Color.RESET}
{Color.MAGENTA}  {'#' * (_W - 2)}{Color.RESET}
""")


def print_menu():
    opts = [
        ("1", "Add a security event manually"),
        ("2", "Load sample events (pre-built library)"),
        ("3", "View staged events"),
        ("4", "Remove a staged event"),
        ("5", "Clear all staged events"),
        ("6", "Generate report from staged events"),
        ("7", "View report summary"),
        ("8", "View full report detail"),
        ("9", "Export report to TXT file"),
        ("J", "Export report to JSON file"),
        ("R", "List all generated reports"),
        ("X", "Exit"),
    ]
    _head()
    print(f"  {Color.BOLD}  MAIN MENU{Color.RESET}")
    _sep()
    for key, label in opts:
        print(f"    {Color.MAGENTA}[{key}]{Color.RESET}  {label}")
    _head()


def print_event_table(events: list, title: str = "STAGED EVENTS") -> None:
    if not events:
        print(f"\n  {Color.GREY}No events to display.{Color.RESET}\n")
        return
    _head()
    print(f"  {Color.BOLD}  {title}  ({len(events)} total){Color.RESET}")
    _sep()
    print(f"  {'#':<4} {'ID':<10} {'Timestamp':<20} {'Severity':<10} {'Type':<25} {'Source'}")
    _sep()
    for i, e in enumerate(events, 1):
        sc = Color.sev(e.severity)
        sv = f"{sc}{e.severity:<9}{Color.RESET}"
        print(f"  {i:<4} {_short(e.event_id):<10} {e.timestamp:<20} {sv} {e.event_type:<25} {e.source}")
    _head()


def print_report_summary(report: SecurityReport) -> None:
    sc = Color.sev(report.risk_label())
    _head()
    print(f"  {Color.BOLD}  REPORT SUMMARY{Color.RESET}")
    _sep()
    print(f"  Report ID     : {Color.MAGENTA}{_short(report.report_id)}{Color.RESET}")
    print(f"  Title         : {Color.BOLD}{report.title}{Color.RESET}")
    print(f"  Analyst       : {report.analyst}")
    print(f"  Date          : {report.creation_date}")
    print(f"  Total Events  : {len(report.events)}")
    print(f"  Risk Score    : {Color.BOLD}{report.risk_score()}/100{Color.RESET}")
    print(f"  Overall Risk  : {sc}{Color.BOLD}{report.risk_label()}{Color.RESET}")
    _sep()
    print(f"  {Color.BOLD}  Severity Breakdown{Color.RESET}")
    bd = report.severity_breakdown()
    total = len(report.events) or 1
    for sev in SecurityEvent.VALID_SEVERITIES:
        cnt  = bd[sev]
        pct  = cnt / total * 100
        bar  = "█" * int(pct / 100 * 25)
        rest = "░" * (25 - len(bar))
        sc2  = Color.sev(sev)
        print(f"    {sc2}{sev:<10}{Color.RESET} {bar}{Color.GREY}{rest}{Color.RESET}  {cnt:>3}  ({pct:4.1f}%)")
    _sep()
    print(f"  {Color.BOLD}  Top 5 Priority Events{Color.RESET}")
    for e in report.top_events(5):
        sc2 = Color.sev(e.severity)
        print(f"    {sc2}[{e.severity:<8}]{Color.RESET} {e.event_type:<25} {Color.GREY}{e.source}{Color.RESET}")
    _head()


def print_report_full(report: SecurityReport) -> None:
    print_report_summary(report)
    _head()
    print(f"  {Color.BOLD}  KEY FINDINGS{Color.RESET}")
    _sep()
    for i, f in enumerate(report.findings, 1):
        print(f"  {i:>2}. {f}")
    _head()
    print(f"  {Color.BOLD}  RECOMMENDATIONS{Color.RESET}")
    _sep()
    for i, r in enumerate(report.recommendations, 1):
        print(f"  {i:>2}. {r}")
    _head()
    print(f"  {Color.BOLD}  ALL EVENTS  ({len(report.events)}){Color.RESET}")
    _sep()
    for i, e in enumerate(report.events, 1):
        sc = Color.sev(e.severity)
        print(f"  {i:>3}. {sc}[{e.severity:<8}]{Color.RESET} {e.event_type}")
        print(f"       ID     : {_short(e.event_id)}  |  {e.timestamp}")
        print(f"       Source : {e.source}  |  Asset: {e.affected_asset}")
        print(f"       {e.description}")
        if i < len(report.events):
            print()
    _head()


def print_report_list(reports: list) -> None:
    if not reports:
        print(f"\n  {Color.GREY}No reports generated yet.{Color.RESET}\n")
        return
    _head()
    print(f"  {Color.BOLD}  GENERATED REPORTS  ({len(reports)}){Color.RESET}")
    _sep()
    print(f"  {'#':<4} {'ID':<10} {'Date':<12} {'Risk':<10} {'Events':<8} {'Title'}")
    _sep()
    for i, r in enumerate(reports, 1):
        sc = Color.sev(r.risk_label())
        rl = f"{sc}{r.risk_label():<9}{Color.RESET}"
        print(f"  {i:<4} {_short(r.report_id):<10} {r.creation_date:<12} {rl} {len(r.events):<8} {r.title}")
    _head()


# ─────────────────────────────────────────────────────────────
# CLI Helpers
# ─────────────────────────────────────────────────────────────

def _prompt(msg: str) -> str:
    return input(f"\n  {Color.MAGENTA}>{Color.RESET} {msg} ").strip()


def _select_report(generator: ReportGenerator) -> Optional[SecurityReport]:
    reports = generator.all_reports()
    if not reports:
        print(f"\n  {Color.GREY}No reports available. Generate one first (option 6).{Color.RESET}")
        return None
    if len(reports) == 1:
        return reports[0]
    print_report_list(reports)
    rid = _prompt("Enter Report ID prefix (or ENTER for latest):")
    if not rid:
        return reports[-1]
    r = generator.get_report(rid)
    if not r:
        print(f"  {Color.RED}[!] Report not found.{Color.RESET}")
    return r


# ─────────────────────────────────────────────────────────────
# Menu Action Functions
# ─────────────────────────────────────────────────────────────

def cmd_add_event(generator: ReportGenerator) -> None:
    print(f"\n  {Color.BOLD}-- Add Security Event --{Color.RESET}")

    # Show event types
    types = sorted(SecurityEvent.VALID_TYPES)
    print(f"\n  Available event types:")
    for i, t in enumerate(types, 1):
        print(f"    {i:>2}. {t}")
    raw = _prompt(f"Select type number [1-{len(types)}]:")
    try:
        idx = int(raw) - 1
        if not 0 <= idx < len(types):
            raise ValueError
        etype = types[idx]
    except (ValueError, IndexError):
        print(f"  {Color.RED}[!] Invalid selection.{Color.RESET}")
        return

    # Severity
    sevs = SecurityEvent.VALID_SEVERITIES
    print(f"\n  Severities: " + "  ".join(f"{i+1}.{s}" for i, s in enumerate(sevs)))
    raw_s = _prompt(f"Select severity [1-{len(sevs)}]:")
    try:
        sidx = int(raw_s) - 1
        if not 0 <= sidx < len(sevs):
            raise ValueError
        severity = sevs[sidx]
    except ValueError:
        print(f"  {Color.RED}[!] Invalid severity selection.{Color.RESET}")
        return

    description = _prompt("Description:")
    if not description:
        print(f"  {Color.RED}[!] Description cannot be empty.{Color.RESET}")
        return

    source         = _prompt("Source (e.g. SIEM, EDR) [default: Manual]:")  or "Manual"
    affected_asset = _prompt("Affected asset [default: Unknown]:")           or "Unknown"

    try:
        event = SecurityEvent(etype, severity, description, source, affected_asset)
        generator.add_event(event)
        sc = Color.sev(severity)
        print(f"\n  {Color.GREEN}[+]{Color.RESET} Event {Color.MAGENTA}{_short(event.event_id)}{Color.RESET} added. "
              f"{sc}[{severity}]{Color.RESET} {etype}")
    except (ValueError, TypeError) as e:
        print(f"  {Color.RED}[!] {e}{Color.RESET}")


def cmd_load_samples(generator: ReportGenerator) -> None:
    print(f"\n  -- Load Sample Events --")
    print(f"  Library contains {len(SAMPLE_EVENTS)} pre-built events.")
    raw = _prompt(f"Load how many? [1-{len(SAMPLE_EVENTS)}, default all]:")
    try:
        n = int(raw) if raw else len(SAMPLE_EVENTS)
        if not 1 <= n <= len(SAMPLE_EVENTS):
            raise ValueError
    except ValueError:
        n = len(SAMPLE_EVENTS)

    loaded = 0
    for sample in SAMPLE_EVENTS[:n]:
        try:
            e = SecurityEvent(**sample)
            generator.add_event(e)
            loaded += 1
        except Exception:
            pass
    print(f"  {Color.GREEN}[+]{Color.RESET} {loaded} sample event(s) loaded into staging area.")


def cmd_view_events(generator: ReportGenerator) -> None:
    events = generator.all_events()
    print_event_table(events)
    if events:
        sev_counts: dict[str, int] = {}
        for e in events:
            sev_counts[e.severity] = sev_counts.get(e.severity, 0) + 1
        parts = [f"{Color.sev(k)}{k}: {v}{Color.RESET}"
                 for k, v in sev_counts.items() if v]
        print(f"  Summary: {' | '.join(parts)}\n")


def cmd_remove_event(generator: ReportGenerator) -> None:
    events = generator.all_events()
    if not events:
        print(f"\n  {Color.GREY}No staged events.{Color.RESET}")
        return
    print_event_table(events)
    eid = _prompt("Enter Event ID prefix to remove:")
    removed = generator.remove_event(eid)
    if removed:
        print(f"  {Color.GREEN}[OK]{Color.RESET} Removed event {_short(removed.event_id)} ({removed.event_type}).")
    else:
        print(f"  {Color.RED}[!] Event not found.{Color.RESET}")


def cmd_clear_events(generator: ReportGenerator) -> None:
    if not generator.all_events():
        print(f"\n  {Color.GREY}No events to clear.{Color.RESET}")
        return
    confirm = _prompt(f"Clear all {len(generator.all_events())} staged events? (y/n):")
    if confirm.lower() == "y":
        n = generator.clear_events()
        print(f"  {Color.GREEN}[OK]{Color.RESET} {n} event(s) cleared.")
    else:
        print("  Cancelled.")


def cmd_generate_report(generator: ReportGenerator) -> Optional[SecurityReport]:
    if not generator.all_events():
        print(f"\n  {Color.RED}[!] No events staged. Add or load events first.{Color.RESET}")
        return None
    print(f"\n  -- Generate Report ({len(generator.all_events())} events) --")
    title   = _prompt("Report title [default: Security Incident Report]:")  or "Security Incident Report"
    analyst = _prompt("Analyst name [default: Automated System]:")          or "Automated System"
    try:
        report = generator.generate_report(title, analyst)
        print(f"\n  {Color.GREEN}[+]{Color.RESET} Report generated: "
              f"{Color.MAGENTA}{_short(report.report_id)}{Color.RESET}  "
              f"'{report.title}'")
        print(f"      Risk: {Color.sev(report.risk_label())}{report.risk_label()}{Color.RESET}  "
              f"({report.risk_score()}/100)  |  Events: {len(report.events)}")
        return report
    except ValueError as e:
        print(f"  {Color.RED}[!] {e}{Color.RESET}")
        return None


def cmd_view_summary(generator: ReportGenerator) -> None:
    report = _select_report(generator)
    if report:
        print_report_summary(report)


def cmd_view_full(generator: ReportGenerator) -> None:
    report = _select_report(generator)
    if report:
        print_report_full(report)


def cmd_export_txt(generator: ReportGenerator) -> None:
    report = _select_report(generator)
    if not report:
        return
    default = f"security_report_{_short(report.report_id)}_{report.creation_date}.txt"
    path = _prompt(f"Output file path [default: {default}]:") or default
    try:
        out = generator.export_txt(report, path)
        size = os.path.getsize(out)
        print(f"  {Color.GREEN}[+]{Color.RESET} TXT report saved: {Color.CYAN}{out}{Color.RESET}  ({size:,} bytes)")
    except Exception as e:
        print(f"  {Color.RED}[!] Export failed: {e}{Color.RESET}")


def cmd_export_json(generator: ReportGenerator) -> None:
    report = _select_report(generator)
    if not report:
        return
    default = f"security_report_{_short(report.report_id)}_{report.creation_date}.json"
    path = _prompt(f"Output file path [default: {default}]:") or default
    try:
        out = generator.export_json(report, path)
        size = os.path.getsize(out)
        print(f"  {Color.GREEN}[+]{Color.RESET} JSON report saved: {Color.CYAN}{out}{Color.RESET}  ({size:,} bytes)")
    except Exception as e:
        print(f"  {Color.RED}[!] Export failed: {e}{Color.RESET}")


def cmd_list_reports(generator: ReportGenerator) -> None:
    print_report_list(generator.all_reports())


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    print_banner()
    generator = ReportGenerator()

    VALID = {"1","2","3","4","5","6","7","8","9","J","R","X"}
    DISPATCH = {
        "1": lambda: cmd_add_event(generator),
        "2": lambda: cmd_load_samples(generator),
        "3": lambda: cmd_view_events(generator),
        "4": lambda: cmd_remove_event(generator),
        "5": lambda: cmd_clear_events(generator),
        "6": lambda: cmd_generate_report(generator),
        "7": lambda: cmd_view_summary(generator),
        "8": lambda: cmd_view_full(generator),
        "9": lambda: cmd_export_txt(generator),
        "J": lambda: cmd_export_json(generator),
        "R": lambda: cmd_list_reports(generator),
    }

    while True:
        n_events  = len(generator.all_events())
        n_reports = len(generator.all_reports())
        print(f"\n  {Color.GREY}Staged Events: {Color.MAGENTA}{n_events}{Color.GREY}  |  "
              f"Reports Generated: {Color.MAGENTA}{n_reports}{Color.RESET}")

        print_menu()

        choice = ""
        while choice not in VALID:
            choice = _prompt("Select option:").upper()
            if choice not in VALID:
                print(f"  {Color.RED}[!] Invalid. Options: {', '.join(sorted(VALID))}{Color.RESET}")

        if choice == "X":
            print(f"\n  {Color.MAGENTA}[*] Exiting Security Report Generator. Stay secure.{Color.RESET}\n")
            break

        try:
            DISPATCH[choice]()
        except Exception as exc:
            print(f"\n  {Color.RED}[ERROR] Unexpected error: {exc}{Color.RESET}")


if __name__ == "__main__":
    main()