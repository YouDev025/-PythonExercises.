#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║        Threat Detection Rule Engine  v1.0                           ║
║        Pure Python · No External Dependencies                        ║
╚══════════════════════════════════════════════════════════════════════╝

A modular, rule-based security event analysis engine that processes
event streams, applies detection rules, scores IP risk, generates
structured alerts, and exports results.

Run:  python threat_detection_rule_engine.py
      python threat_detection_rule_engine.py --demo
"""

import os
import sys
import csv
import json
import random
import logging
import textwrap
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────
#  Terminal Colour Helpers
# ──────────────────────────────────────────────────────────────────────

class C:
    """ANSI colour codes; silently degraded on unsupported terminals."""
    _ON = sys.platform != "win32" or "ANSICON" in os.environ

    RED     = "\033[91m" if _ON else ""
    YELLOW  = "\033[93m" if _ON else ""
    GREEN   = "\033[92m" if _ON else ""
    CYAN    = "\033[96m" if _ON else ""
    MAGENTA = "\033[95m" if _ON else ""
    BLUE    = "\033[94m" if _ON else ""
    BOLD    = "\033[1m"  if _ON else ""
    DIM     = "\033[2m"  if _ON else ""
    RESET   = "\033[0m"  if _ON else ""

    @classmethod
    def fmt(cls, text: str, *codes: str) -> str:
        return "".join(codes) + str(text) + cls.RESET

    @classmethod
    def severity(cls, sev: str) -> str:
        palette = {
            "CRITICAL": cls.MAGENTA,
            "HIGH":     cls.RED,
            "MEDIUM":   cls.YELLOW,
            "LOW":      cls.GREEN,
            "INFO":     cls.CYAN,
        }
        color = palette.get(sev.upper(), cls.RESET)
        return cls.fmt(f"[{sev.upper()}]", color, cls.BOLD)


def banner() -> None:
    print(C.fmt(r"""
╔══════════════════════════════════════════════════════════════════════╗
║  ████████╗██╗  ██╗██████╗ ███████╗ █████╗ ████████╗                ║
║     ██╔══╝██║  ██║██╔══██╗██╔════╝██╔══██╗╚══██╔══╝               ║
║     ██║   ███████║██████╔╝█████╗  ███████║   ██║                   ║
║     ██║   ██╔══██║██╔══██╗██╔══╝  ██╔══██║   ██║                   ║
║     ██║   ██║  ██║██║  ██║███████╗██║  ██║   ██║                   ║
║     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝                  ║
║           Detection Rule Engine  v1.0  ·  Pure Python               ║
╚══════════════════════════════════════════════════════════════════════╝
""", C.CYAN, C.BOLD))


# ──────────────────────────────────────────────────────────────────────
#  Core Data Models
# ──────────────────────────────────────────────────────────────────────

# Valid event types and status values
EVENT_TYPES = [
    "LOGIN", "LOGOUT", "REQUEST", "ERROR",
    "FILE_ACCESS", "COMMAND_EXEC", "PRIVILEGE_ESC",
    "DATA_TRANSFER", "DNS_QUERY", "PORT_SCAN",
]
STATUS_VALUES = ["SUCCESS", "FAILURE", "BLOCKED", "TIMEOUT"]

# Severity ordering for comparisons
SEV_RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass
class SecurityEvent:
    """
    Normalised security event.  All rule logic operates on this type.
    """
    timestamp:      datetime
    source_ip:      str
    destination_ip: str
    event_type:     str       # from EVENT_TYPES
    status:         str       # from STATUS_VALUES
    message:        str
    extra:          Dict      = field(default_factory=dict)  # rule-specific extras

    # ── display ──────────────────────────────────────────────────────

    def short(self) -> str:
        ts  = self.timestamp.strftime("%H:%M:%S")
        src = C.fmt(self.source_ip, C.CYAN)
        et  = C.fmt(f"{self.event_type:15s}", C.BOLD)
        st  = (C.fmt(self.status, C.GREEN)
               if self.status == "SUCCESS"
               else C.fmt(self.status, C.RED))
        return f"  [{ts}] {src:26s} {et} {st:20s} {self.message}"

    def __str__(self) -> str:
        return self.short()

    # ── serialisation ─────────────────────────────────────────────────

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @staticmethod
    def from_dict(d: Dict) -> "SecurityEvent":
        d = dict(d)
        d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        d.setdefault("extra", {})
        return SecurityEvent(**d)

    def to_tsv(self) -> str:
        return "\t".join([
            self.timestamp.isoformat(),
            self.source_ip,
            self.destination_ip,
            self.event_type,
            self.status,
            self.message,
            json.dumps(self.extra),
        ])

    @staticmethod
    def from_tsv(line: str) -> Optional["SecurityEvent"]:
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        parts = line.split("\t")
        if len(parts) < 6:
            return None
        try:
            extra = json.loads(parts[6]) if len(parts) > 6 else {}
            return SecurityEvent(
                timestamp      = datetime.fromisoformat(parts[0]),
                source_ip      = parts[1],
                destination_ip = parts[2],
                event_type     = parts[3],
                status         = parts[4],
                message        = parts[5],
                extra          = extra,
            )
        except (ValueError, json.JSONDecodeError):
            return None


@dataclass
class Alert:
    """
    A threat alert produced by a detection rule.
    """
    rule_name:      str
    severity:       str          # LOW | MEDIUM | HIGH | CRITICAL
    risk_score:     int          # 0-100
    involved_ip:    str
    description:    str
    related_events: List[SecurityEvent] = field(default_factory=list)
    triggered_at:   datetime            = field(default_factory=datetime.now)
    tags:           List[str]           = field(default_factory=list)

    # ── display ──────────────────────────────────────────────────────

    def display(self, show_events: bool = True) -> None:
        W   = 72
        sep = C.fmt("─" * W, C.DIM)
        print(sep)
        print(C.fmt(f"  🚨  {self.rule_name}", C.BOLD, C.RED))
        print(f"  Severity   : {C.severity(self.severity)}")
        print(f"  Risk Score : {C.fmt(str(self.risk_score) + '/100', C.YELLOW, C.BOLD)}")
        print(f"  Source IP  : {C.fmt(self.involved_ip, C.CYAN)}")
        print(f"  Triggered  : {self.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.tags:
            tag_str = "  ".join(C.fmt(f"#{t}", C.BLUE) for t in self.tags)
            print(f"  Tags       : {tag_str}")
        # Wrapped description
        lines = textwrap.wrap(self.description, W - 15)
        print(f"  Detail     : {lines[0]}")
        for ln in lines[1:]:
            print(f"               {ln}")
        if show_events and self.related_events:
            print(C.fmt(f"\n  Related Events ({len(self.related_events)}):", C.BOLD))
            for ev in self.related_events[:6]:
                print(ev.short())
            if len(self.related_events) > 6:
                print(C.fmt(f"    … +{len(self.related_events)-6} more", C.DIM))
        print(sep)

    # ── serialisation ─────────────────────────────────────────────────

    def to_dict(self) -> Dict:
        return {
            "rule_name":    self.rule_name,
            "severity":     self.severity,
            "risk_score":   self.risk_score,
            "involved_ip":  self.involved_ip,
            "description":  self.description,
            "triggered_at": self.triggered_at.isoformat(),
            "tags":         self.tags,
            "event_count":  len(self.related_events),
        }

    def to_text(self) -> str:
        lines = [
            "=" * 70,
            f"RULE      : {self.rule_name}",
            f"SEVERITY  : {self.severity}",
            f"SCORE     : {self.risk_score}/100",
            f"IP        : {self.involved_ip}",
            f"TRIGGERED : {self.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"TAGS      : {', '.join(self.tags)}",
            f"DETAIL    : {self.description}",
            f"EVENTS ({len(self.related_events)}):",
        ]
        ts_fmt = "%Y-%m-%d %H:%M:%S"
        for ev in self.related_events[:10]:
            lines.append(
                f"  [{ev.timestamp.strftime(ts_fmt)}] "
                f"{ev.source_ip:17s} {ev.event_type:15s} "
                f"{ev.status:8s}  {ev.message}"
            )
        lines.append("=" * 70)
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
#  IP Risk Scorer
# ──────────────────────────────────────────────────────────────────────

class IPRiskTracker:
    """
    Maintains a cumulative risk score per source IP.
    Rules can call bump() to record findings.
    """

    _SEV_BUMP = {"INFO": 2, "LOW": 5, "MEDIUM": 15, "HIGH": 30, "CRITICAL": 50}

    def __init__(self) -> None:
        self._scores:   Dict[str, int]       = defaultdict(int)
        self._history:  Dict[str, List[str]] = defaultdict(list)

    def bump(self, ip: str, reason: str, severity: str = "MEDIUM") -> None:
        delta = self._SEV_BUMP.get(severity.upper(), 10)
        self._scores[ip]   = min(100, self._scores[ip] + delta)
        self._history[ip].append(f"[{severity}] {reason}")

    def score(self, ip: str) -> int:
        return self._scores.get(ip, 0)

    def risk_label(self, ip: str) -> str:
        s = self.score(ip)
        if s >= 80: return "CRITICAL"
        if s >= 60: return "HIGH"
        if s >= 35: return "MEDIUM"
        if s >= 10: return "LOW"
        return "CLEAN"

    def top(self, n: int = 10) -> List[Tuple[str, int]]:
        return sorted(self._scores.items(), key=lambda x: -x[1])[:n]

    def report(self, ip: str) -> str:
        hist = self._history.get(ip, [])
        lines = [f"  Score: {self.score(ip)}/100  ({self.risk_label(ip)})"]
        for h in hist[-8:]:
            lines.append(f"    {C.fmt('▸', C.DIM)} {h}")
        return "\n".join(lines)

    def reset(self) -> None:
        self._scores.clear()
        self._history.clear()


# ──────────────────────────────────────────────────────────────────────
#  Abstract Rule Base
# ──────────────────────────────────────────────────────────────────────

class BaseRule(ABC):
    """
    Every detection rule inherits from this class and implements analyse().

    Rules receive the full ordered event list plus shared state objects
    (risk tracker, a context dict for cross-rule communication).
    """

    # Override in subclasses
    name:        str = "UnnamedRule"
    description: str = ""
    tags:        List[str] = []

    def __init__(self) -> None:
        self.enabled: bool = True

    @abstractmethod
    def analyse(
        self,
        events:  List[SecurityEvent],
        tracker: IPRiskTracker,
        ctx:     Dict,
    ) -> List[Alert]:
        """Return a (possibly empty) list of alerts."""

    def _window(
        self,
        events:   List[SecurityEvent],
        ip:       str,
        anchor:   datetime,
        seconds:  int,
        direction: str = "before",
        event_type: Optional[str] = None,
        status:     Optional[str] = None,
    ) -> List[SecurityEvent]:
        """
        Utility: filter events for a given IP within a time window.
        direction: 'before' | 'after' | 'both'
        """
        delta = timedelta(seconds=seconds)
        if direction == "before":
            lo, hi = anchor - delta, anchor
        elif direction == "after":
            lo, hi = anchor, anchor + delta
        else:
            lo, hi = anchor - delta, anchor + delta

        result = [
            e for e in events
            if e.source_ip == ip and lo <= e.timestamp <= hi
        ]
        if event_type:
            result = [e for e in result if e.event_type == event_type]
        if status:
            result = [e for e in result if e.status == status]
        return result


# ──────────────────────────────────────────────────────────────────────
#  Detection Rules
# ──────────────────────────────────────────────────────────────────────

class BruteForceRule(BaseRule):
    """
    Detect credential brute-force: N failed LOGINs within a time window
    followed by a SUCCESS from the same IP.
    """

    name        = "BRUTE_FORCE_LOGIN"
    description = "Multiple failed logins followed by success – credential brute force."
    tags        = ["auth", "brute-force", "credential"]

    FAIL_THRESHOLD   = 5     # min failures to trigger
    WINDOW_FAIL_S    = 300   # 5-min failure window
    WINDOW_SUCCESS_S = 180   # success must appear within 3 min of last failure

    def analyse(self, events, tracker, ctx):
        alerts: List[Alert] = []
        by_ip: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for e in events:
            if e.event_type == "LOGIN":
                by_ip[e.source_ip].append(e)

        for ip, evts in by_ip.items():
            evts.sort(key=lambda x: x.timestamp)
            failures  = [e for e in evts if e.status == "FAILURE"]
            successes = [e for e in evts if e.status == "SUCCESS"]

            alerted = False
            for i in range(len(failures)):
                if alerted:
                    break
                win_end   = failures[i].timestamp + timedelta(seconds=self.WINDOW_FAIL_S)
                win_fails = [f for f in failures
                             if failures[i].timestamp <= f.timestamp <= win_end]
                if len(win_fails) < self.FAIL_THRESHOLD:
                    continue

                last_fail = max(win_fails, key=lambda x: x.timestamp)
                post_ok   = [s for s in successes
                             if last_fail.timestamp < s.timestamp
                             <= last_fail.timestamp + timedelta(seconds=self.WINDOW_SUCCESS_S)]
                if post_ok:
                    n     = len(win_fails)
                    score = min(100, 50 + n * 4)
                    sev   = "CRITICAL" if score >= 85 else "HIGH"
                    tracker.bump(ip, f"Brute-force: {n} failures → success", sev)
                    alerts.append(Alert(
                        rule_name    = self.name,
                        severity     = sev,
                        risk_score   = score,
                        involved_ip  = ip,
                        description  = (
                            f"{n} failed login attempt(s) from {ip} within "
                            f"{self.WINDOW_FAIL_S // 60} minutes, followed by "
                            f"a successful authentication – likely brute-force."
                        ),
                        related_events = win_fails + post_ok,
                        triggered_at   = post_ok[0].timestamp,
                        tags           = self.tags,
                    ))
                    alerted = True

        return alerts


class SuspiciousIPRule(BaseRule):
    """
    High request volume from one IP within a short window – possible
    scanning, DDoS, or automated tool activity.
    """

    name        = "SUSPICIOUS_IP_FLOOD"
    description = "Unusually high request rate from a single IP."
    tags        = ["network", "flood", "scan", "dos"]

    THRESHOLD = 40     # requests
    WINDOW_S  = 120    # 2 minutes

    def analyse(self, events, tracker, ctx):
        alerts: List[Alert] = []
        by_ip: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for e in events:
            by_ip[e.source_ip].append(e)

        for ip, evts in by_ip.items():
            evts.sort(key=lambda x: x.timestamp)
            alerted = False
            for i in range(len(evts)):
                if alerted:
                    break
                win_end = evts[i].timestamp + timedelta(seconds=self.WINDOW_S)
                window  = [e for e in evts
                           if evts[i].timestamp <= e.timestamp <= win_end]
                if len(window) >= self.THRESHOLD:
                    rate  = len(window) / self.WINDOW_S * 60
                    score = min(100, 35 + int(rate * 0.8))
                    sev   = "CRITICAL" if score >= 90 else ("HIGH" if score >= 65 else "MEDIUM")
                    tracker.bump(ip, f"Request flood: {len(window)} in {self.WINDOW_S}s", sev)
                    alerts.append(Alert(
                        rule_name    = self.name,
                        severity     = sev,
                        risk_score   = score,
                        involved_ip  = ip,
                        description  = (
                            f"{len(window)} event(s) from {ip} in "
                            f"{self.WINDOW_S}s (~{rate:.1f}/min) – "
                            f"possible scan or flood."
                        ),
                        related_events = window[:20],
                        triggered_at   = evts[i].timestamp,
                        tags           = self.tags,
                    ))
                    alerted = True

        return alerts


class RestrictedResourceRule(BaseRule):
    """
    Access attempts targeting sensitive paths/resources such as
    /admin, /config, /.env, database endpoints, etc.
    """

    name        = "RESTRICTED_RESOURCE_ACCESS"
    description = "Attempts to access restricted resources or sensitive paths."
    tags        = ["web", "access-control", "recon"]

    SENSITIVE = [
        "/admin", "/admin/", "/admin/login",
        "/config", "/configuration",
        "/.env", "/.git", "/.htpasswd",
        "/wp-admin", "/phpmyadmin",
        "/backup", "/db", "/database",
        "/api/internal", "/secret",
        "etc/passwd", "etc/shadow",
    ]
    MIN_HITS = 2   # alert after at least this many distinct sensitive hits

    def _is_sensitive(self, msg: str) -> bool:
        ml = msg.lower()
        return any(s in ml for s in self.SENSITIVE)

    def analyse(self, events, tracker, ctx):
        alerts: List[Alert] = []
        by_ip: Dict[str, List[SecurityEvent]] = defaultdict(list)

        for e in events:
            if e.event_type in ("REQUEST", "FILE_ACCESS") and self._is_sensitive(e.message):
                by_ip[e.source_ip].append(e)

        for ip, evts in by_ip.items():
            if len(evts) < self.MIN_HITS:
                score = 40
                sev   = "MEDIUM"
            else:
                score = min(100, 40 + len(evts) * 8)
                sev   = "HIGH" if score >= 60 else "MEDIUM"

            tracker.bump(ip, f"Sensitive path access: {len(evts)} hit(s)", sev)
            alerts.append(Alert(
                rule_name    = self.name,
                severity     = sev,
                risk_score   = score,
                involved_ip  = ip,
                description  = (
                    f"{ip} made {len(evts)} access attempt(s) to sensitive "
                    f"resource(s) – possible reconnaissance or privilege abuse."
                ),
                related_events = evts,
                triggered_at   = evts[0].timestamp,
                tags           = self.tags,
            ))

        return alerts


class NomadLoginRule(BaseRule):
    """
    Detect logins from multiple distinct source IPs for the same
    logical user / target in a short window – indicates account
    sharing, credential theft, or impossible travel.
    """

    name        = "MULTI_IP_LOGIN"
    description = "Successful logins from multiple IPs in a short time window."
    tags        = ["auth", "account-takeover", "impossible-travel"]

    DISTINCT_IP_THRESHOLD = 3    # min distinct IPs
    WINDOW_S              = 600  # 10 minutes

    def analyse(self, events, tracker, ctx):
        alerts: List[Alert] = []
        login_events = sorted(
            [e for e in events if e.event_type == "LOGIN" and e.status == "SUCCESS"],
            key=lambda x: x.timestamp,
        )
        # Group by destination (the server/service being logged into)
        by_dest: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for e in login_events:
            by_dest[e.destination_ip].append(e)

        for dest, evts in by_dest.items():
            for i in range(len(evts)):
                win_end = evts[i].timestamp + timedelta(seconds=self.WINDOW_S)
                window  = [e for e in evts
                           if evts[i].timestamp <= e.timestamp <= win_end]
                distinct = set(e.source_ip for e in window)
                if len(distinct) >= self.DISTINCT_IP_THRESHOLD:
                    for ip in distinct:
                        tracker.bump(ip, f"Multi-IP login to {dest}", "MEDIUM")
                    # Report as a single alert for the destination
                    representative = sorted(distinct)[0]
                    alerts.append(Alert(
                        rule_name    = self.name,
                        severity     = "HIGH",
                        risk_score   = 65,
                        involved_ip  = representative,
                        description  = (
                            f"Successful logins to {dest} from {len(distinct)} "
                            f"distinct IP(s) within {self.WINDOW_S // 60} min: "
                            f"{', '.join(sorted(distinct)[:5])}. "
                            f"Possible account takeover or credential sharing."
                        ),
                        related_events = window,
                        triggered_at   = window[0].timestamp,
                        tags           = self.tags,
                    ))
                    break   # one alert per destination

        return alerts


class PrivilegeEscalationRule(BaseRule):
    """
    Detect PRIVILEGE_ESC events, especially after recent auth failures –
    a pattern consistent with local privilege escalation post-compromise.
    """

    name        = "PRIVILEGE_ESCALATION"
    description = "Privilege escalation detected, possibly after auth failures."
    tags        = ["endpoint", "privilege-escalation", "post-exploitation"]

    PRE_FAIL_WINDOW_S = 300   # look back 5 min for prior auth failures

    def analyse(self, events, tracker, ctx):
        alerts: List[Alert] = []
        seen_ips: set = set()

        for e in sorted(events, key=lambda x: x.timestamp):
            if e.event_type != "PRIVILEGE_ESC" or e.source_ip in seen_ips:
                continue
            seen_ips.add(e.source_ip)

            prior_fails = self._window(
                events, e.source_ip, e.timestamp,
                self.PRE_FAIL_WINDOW_S, "before",
                event_type="LOGIN", status="FAILURE",
            )
            score = 70 + min(25, len(prior_fails) * 3)
            sev   = "CRITICAL" if prior_fails else "HIGH"
            tracker.bump(e.source_ip, "Privilege escalation event", sev)

            alerts.append(Alert(
                rule_name    = self.name,
                severity     = sev,
                risk_score   = score,
                involved_ip  = e.source_ip,
                description  = (
                    f"Privilege escalation event from {e.source_ip}. "
                    + (f"{len(prior_fails)} auth failure(s) preceded this in "
                       f"{self.PRE_FAIL_WINDOW_S // 60} min – likely post-exploit."
                       if prior_fails else
                       "No prior auth failures – may be insider threat.")
                ),
                related_events = prior_fails + [e],
                triggered_at   = e.timestamp,
                tags           = self.tags,
            ))

        return alerts


class DataExfiltrationRule(BaseRule):
    """
    High-volume outbound DATA_TRANSFER events from a single IP in a
    short window – potential data exfiltration.
    """

    name        = "DATA_EXFILTRATION"
    description = "Unusually high data transfer volume – possible exfiltration."
    tags        = ["data-loss", "exfiltration", "insider-threat"]

    THRESHOLD = 8     # transfer events
    WINDOW_S  = 300   # 5 minutes

    def analyse(self, events, tracker, ctx):
        alerts: List[Alert] = []
        by_ip: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for e in events:
            if e.event_type == "DATA_TRANSFER":
                by_ip[e.source_ip].append(e)

        for ip, evts in by_ip.items():
            evts.sort(key=lambda x: x.timestamp)
            alerted = False
            for i in range(len(evts)):
                if alerted:
                    break
                win_end = evts[i].timestamp + timedelta(seconds=self.WINDOW_S)
                window  = [e for e in evts
                           if evts[i].timestamp <= e.timestamp <= win_end]
                if len(window) >= self.THRESHOLD:
                    score = min(100, 55 + len(window) * 3)
                    sev   = "CRITICAL" if score >= 85 else "HIGH"
                    tracker.bump(ip, f"Data exfiltration: {len(window)} transfers", sev)
                    alerts.append(Alert(
                        rule_name    = self.name,
                        severity     = sev,
                        risk_score   = score,
                        involved_ip  = ip,
                        description  = (
                            f"{len(window)} DATA_TRANSFER event(s) from {ip} in "
                            f"{self.WINDOW_S // 60} min – possible data exfiltration."
                        ),
                        related_events = window,
                        triggered_at   = evts[i].timestamp,
                        tags           = self.tags,
                    ))
                    alerted = True

        return alerts


class PortScanRule(BaseRule):
    """
    Multiple PORT_SCAN events or rapid connection attempts to many
    distinct destinations from one IP.
    """

    name        = "PORT_SCAN_DETECTED"
    description = "Port scanning activity detected from source IP."
    tags        = ["network", "recon", "port-scan"]

    THRESHOLD = 5

    def analyse(self, events, tracker, ctx):
        alerts: List[Alert] = []
        by_ip: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for e in events:
            if e.event_type == "PORT_SCAN":
                by_ip[e.source_ip].append(e)

        for ip, evts in by_ip.items():
            if len(evts) >= self.THRESHOLD:
                score = min(100, 45 + len(evts) * 3)
                sev   = "HIGH" if score >= 60 else "MEDIUM"
                tracker.bump(ip, f"Port scan: {len(evts)} events", sev)
                alerts.append(Alert(
                    rule_name    = self.name,
                    severity     = sev,
                    risk_score   = score,
                    involved_ip  = ip,
                    description  = (
                        f"{len(evts)} port scan event(s) from {ip} – "
                        f"active network reconnaissance."
                    ),
                    related_events = evts[:15],
                    triggered_at   = evts[0].timestamp,
                    tags           = self.tags,
                ))

        return alerts


class RepeatedErrorRule(BaseRule):
    """
    Flood of ERROR events from a single IP – may indicate automated
    fuzzing, crash-loop, or deliberate resource exhaustion.
    """

    name        = "ERROR_FLOOD"
    description = "Repeated error events – possible fuzzing or resource exhaustion."
    tags        = ["availability", "fuzzing", "error-flood"]

    THRESHOLD = 15
    WINDOW_S  = 180   # 3 minutes

    def analyse(self, events, tracker, ctx):
        alerts: List[Alert] = []
        by_ip: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for e in events:
            if e.event_type == "ERROR":
                by_ip[e.source_ip].append(e)

        for ip, evts in by_ip.items():
            evts.sort(key=lambda x: x.timestamp)
            alerted = False
            for i in range(len(evts)):
                if alerted:
                    break
                win_end = evts[i].timestamp + timedelta(seconds=self.WINDOW_S)
                window  = [e for e in evts
                           if evts[i].timestamp <= e.timestamp <= win_end]
                if len(window) >= self.THRESHOLD:
                    tracker.bump(ip, f"Error flood: {len(window)} errors", "MEDIUM")
                    alerts.append(Alert(
                        rule_name    = self.name,
                        severity     = "MEDIUM",
                        risk_score   = min(100, 40 + len(window)),
                        involved_ip  = ip,
                        description  = (
                            f"{len(window)} ERROR event(s) from {ip} in "
                            f"{self.WINDOW_S // 60} min – possible fuzzing."
                        ),
                        related_events = window[:10],
                        triggered_at   = evts[i].timestamp,
                        tags           = self.tags,
                    ))
                    alerted = True

        return alerts


# ──────────────────────────────────────────────────────────────────────
#  Event Generator
# ──────────────────────────────────────────────────────────────────────

class EventGenerator:
    """
    Generates a synthetic event stream with planted attack patterns
    that the rule engine should detect.
    """

    ATTACKER_IPS   = ["198.51.100.7", "203.0.113.42", "192.0.2.99"]
    INTERNAL_IPS   = [f"10.0.0.{i}" for i in range(101, 108)]
    SERVER_IPS     = ["10.10.0.1", "10.10.0.2", "10.10.0.3"]
    SENSITIVE_URLS = [
        "GET /admin", "GET /.env", "GET /wp-admin",
        "GET /phpmyadmin", "GET /config", "GET /backup",
        "GET /api/internal/users", "GET /secret",
    ]
    NORMAL_MSGS = [
        "GET /index.html", "GET /about", "GET /contact",
        "GET /api/v1/products", "POST /api/v1/order",
        "GET /login", "GET /dashboard", "POST /search",
    ]

    def __init__(self, base_time: Optional[datetime] = None) -> None:
        self._base  = base_time or datetime.now() - timedelta(hours=1)
        self._evts: List[SecurityEvent] = []

    def _t(self, offset_s: float) -> datetime:
        return self._base + timedelta(seconds=offset_s)

    def _ev(self, offset_s: float, src: str, dst: str,
            etype: str, status: str, msg: str, **kw) -> SecurityEvent:
        return SecurityEvent(
            timestamp      = self._t(offset_s),
            source_ip      = src,
            destination_ip = dst,
            event_type     = etype,
            status         = status,
            message        = msg,
            extra          = kw,
        )

    # ── scenario builders ─────────────────────────────────────────────

    def _normal_logins(self, n: int = 30) -> None:
        for _ in range(n):
            self._evts.append(self._ev(
                random.uniform(0, 3000),
                random.choice(self.INTERNAL_IPS),
                random.choice(self.SERVER_IPS),
                "LOGIN", "SUCCESS",
                f"User '{random.choice(['alice','bob','carol','dave'])}' logged in",
            ))

    def _normal_requests(self, n: int = 50) -> None:
        for _ in range(n):
            self._evts.append(self._ev(
                random.uniform(0, 3500),
                random.choice(self.INTERNAL_IPS),
                random.choice(self.SERVER_IPS),
                "REQUEST", random.choice(["SUCCESS", "SUCCESS", "FAILURE"]),
                random.choice(self.NORMAL_MSGS),
            ))

    def _brute_force(self, attacker: str, offset: float = 300.0) -> None:
        n = random.randint(8, 14)
        srv = random.choice(self.SERVER_IPS)
        for i in range(n):
            self._evts.append(self._ev(
                offset + i * 5, attacker, srv,
                "LOGIN", "FAILURE",
                f"Failed login attempt #{i+1} user='admin'",
            ))
        self._evts.append(self._ev(
            offset + n * 5 + 3, attacker, srv,
            "LOGIN", "SUCCESS",
            "Login succeeded for user='admin'",
        ))

    def _ip_flood(self, attacker: str, offset: float = 800.0) -> None:
        srv = random.choice(self.SERVER_IPS)
        for i in range(random.randint(55, 70)):
            self._evts.append(self._ev(
                offset + i * 1.5, attacker, srv,
                "REQUEST", "SUCCESS",
                random.choice(self.NORMAL_MSGS + self.SENSITIVE_URLS),
            ))

    def _sensitive_access(self, attacker: str, offset: float = 600.0) -> None:
        srv = random.choice(self.SERVER_IPS)
        for i, url in enumerate(self.SENSITIVE_URLS):
            self._evts.append(self._ev(
                offset + i * 20, attacker, srv,
                "REQUEST", "BLOCKED", url,
            ))

    def _multi_ip_login(self, offset: float = 1500.0) -> None:
        """Three different IPs login to the same server within minutes."""
        srv = self.SERVER_IPS[0]
        for i, ip in enumerate(self.ATTACKER_IPS):
            self._evts.append(self._ev(
                offset + i * 30, ip, srv,
                "LOGIN", "SUCCESS",
                f"Login from {ip}",
            ))

    def _privilege_escalation(self, attacker: str, offset: float = 1200.0) -> None:
        srv = random.choice(self.SERVER_IPS)
        # Some failed logins beforehand
        for i in range(3):
            self._evts.append(self._ev(
                offset + i * 10, attacker, srv,
                "LOGIN", "FAILURE",
                f"Auth failure #{i+1}",
            ))
        self._evts.append(self._ev(
            offset + 60, attacker, srv,
            "PRIVILEGE_ESC", "SUCCESS",
            "sudo escalation to root detected",
        ))

    def _data_exfiltration(self, attacker: str, offset: float = 2000.0) -> None:
        srv = random.choice(self.SERVER_IPS)
        for i in range(random.randint(10, 15)):
            self._evts.append(self._ev(
                offset + i * 18, attacker, srv,
                "DATA_TRANSFER", "SUCCESS",
                f"Outbound transfer #{i+1}: 50 MB",
                bytes_mb=50,
            ))

    def _port_scan(self, attacker: str, offset: float = 2400.0) -> None:
        srv = random.choice(self.SERVER_IPS)
        for i in range(random.randint(8, 12)):
            self._evts.append(self._ev(
                offset + i * 6, attacker, srv,
                "PORT_SCAN", "BLOCKED",
                f"Scan probe to port {1000 + i * 111}",
            ))

    def _error_flood(self, attacker: str, offset: float = 2800.0) -> None:
        srv = random.choice(self.SERVER_IPS)
        for i in range(random.randint(18, 25)):
            self._evts.append(self._ev(
                offset + i * 7, attacker, srv,
                "ERROR", "FAILURE",
                f"500 Internal Server Error – malformed payload #{i+1}",
            ))

    # ── public API ────────────────────────────────────────────────────

    def generate(self) -> List[SecurityEvent]:
        random.seed(99)
        attacker = self.ATTACKER_IPS[0]
        second   = self.ATTACKER_IPS[1]

        self._normal_logins()
        self._normal_requests()

        self._brute_force(attacker,          offset=300.0)
        self._sensitive_access(attacker,     offset=600.0)
        self._ip_flood(attacker,             offset=800.0)
        self._privilege_escalation(attacker, offset=1200.0)
        self._multi_ip_login(                offset=1500.0)
        self._data_exfiltration(attacker,    offset=2000.0)
        self._port_scan(second,              offset=2400.0)
        self._error_flood(second,            offset=2800.0)
        self._ip_flood(second,               offset=3000.0)

        self._evts.sort(key=lambda e: e.timestamp)
        return self._evts


# ──────────────────────────────────────────────────────────────────────
#  Event Store  (load / save / query)
# ──────────────────────────────────────────────────────────────────────

class EventStore:
    """In-memory event store with TSV and JSON I/O."""

    def __init__(self) -> None:
        self._events: List[SecurityEvent] = []

    # ── loading ───────────────────────────────────────────────────────

    def load_tsv(self, path: str) -> int:
        loaded = 0
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for raw in fh:
                    ev = SecurityEvent.from_tsv(raw)
                    if ev:
                        self._events.append(ev)
                        loaded += 1
        except FileNotFoundError:
            print(C.fmt(f"  [!] File not found: {path}", C.RED))
        except OSError as exc:
            print(C.fmt(f"  [!] I/O error: {exc}", C.RED))
        return loaded

    def load_json(self, path: str) -> int:
        loaded = 0
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                print(C.fmt("  [!] JSON must be an array of event objects.", C.RED))
                return 0
            for item in data:
                try:
                    self._events.append(SecurityEvent.from_dict(item))
                    loaded += 1
                except (KeyError, TypeError, ValueError):
                    pass
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(C.fmt(f"  [!] {exc}", C.RED))
        return loaded

    # ── saving ────────────────────────────────────────────────────────

    def save_tsv(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# Threat Detection Engine – event log\n")
            for e in self._events:
                fh.write(e.to_tsv() + "\n")

    def save_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([e.to_dict() for e in self._events], fh, indent=2)

    # ── queries ───────────────────────────────────────────────────────

    def all(self) -> List[SecurityEvent]:
        return list(self._events)

    def by_ip(self, ip: str) -> List[SecurityEvent]:
        return [e for e in self._events if e.source_ip == ip]

    def by_type(self, etype: str) -> List[SecurityEvent]:
        return [e for e in self._events if e.event_type == etype]

    def add_all(self, events: List[SecurityEvent]) -> None:
        self._events.extend(events)
        self._events.sort(key=lambda e: e.timestamp)

    def clear(self) -> None:
        self._events.clear()

    def stats(self) -> Dict:
        if not self._events:
            return {}
        times = sorted(e.timestamp for e in self._events)
        span  = (times[-1] - times[0]).total_seconds()
        by_type: Dict[str, int]  = defaultdict(int)
        by_status: Dict[str, int] = defaultdict(int)
        by_ip: Dict[str, int]    = defaultdict(int)
        for e in self._events:
            by_type[e.event_type]  += 1
            by_status[e.status]    += 1
            by_ip[e.source_ip]     += 1
        return {
            "total":     len(self._events),
            "span_min":  span / 60,
            "unique_ips": len(by_ip),
            "by_type":   dict(by_type),
            "by_status": dict(by_status),
            "top_ips":   sorted(by_ip.items(), key=lambda x: -x[1])[:5],
        }

    def __len__(self) -> int:
        return len(self._events)


# ──────────────────────────────────────────────────────────────────────
#  Rule Engine
# ──────────────────────────────────────────────────────────────────────

class ThreatDetectionEngine:
    """
    Orchestrates rule execution, deduplication, scoring, and reporting.

    Usage:
        engine = ThreatDetectionEngine()
        engine.register(MyRule())
        alerts = engine.run(event_store.all())
        engine.print_report()
        engine.export_alerts_txt("alerts.txt")
    """

    def __init__(self) -> None:
        self._rules:   List[BaseRule]  = []
        self._alerts:  List[Alert]     = []
        self._tracker: IPRiskTracker   = IPRiskTracker()
        # Wire the standard Python logger to a file
        logging.basicConfig(
            filename="threat_engine.log",
            level=logging.INFO,
            format="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # ── rule management ───────────────────────────────────────────────

    def register(self, rule: BaseRule) -> None:
        self._rules.append(rule)

    def enable_rule(self, name: str) -> bool:
        for r in self._rules:
            if r.name == name:
                r.enabled = True
                return True
        return False

    def disable_rule(self, name: str) -> bool:
        for r in self._rules:
            if r.name == name:
                r.enabled = False
                return True
        return False

    def list_rules(self) -> None:
        print(C.fmt(f"\n  Registered rules ({len(self._rules)}):", C.BOLD))
        for r in self._rules:
            status = C.fmt("● ON ", C.GREEN) if r.enabled else C.fmt("○ OFF", C.DIM)
            tags   = C.fmt(" ".join(f"#{t}" for t in r.tags[:3]), C.BLUE)
            print(f"  [{status}] {C.fmt(r.name, C.CYAN, C.BOLD):40s}  {tags}")
        print()

    # ── analysis ──────────────────────────────────────────────────────

    def run(self, events: List[SecurityEvent]) -> List[Alert]:
        """Run all enabled rules and return deduplicated, sorted alerts."""
        if not events:
            print(C.fmt("  [!] No events to analyse.", C.YELLOW))
            return []

        self._alerts  = []
        self._tracker.reset()
        ctx: Dict     = {}   # cross-rule shared context (extensible)
        active = [r for r in self._rules if r.enabled]

        print(C.fmt(
            f"\n  Running {len(active)} rule(s) against "
            f"{len(events):,} event(s) …\n",
            C.CYAN,
        ))

        for rule in active:
            try:
                found = rule.analyse(events, self._tracker, ctx)
                status = (
                    C.fmt(f"  ✔ {rule.name:40s} → {len(found)} alert(s)", C.GREEN)
                    if found
                    else C.fmt(f"  · {rule.name:40s} → no alerts", C.DIM)
                )
                print(status)
                self._alerts.extend(found)
            except Exception as exc:
                print(C.fmt(f"  ✗ {rule.name}: ERROR – {exc}", C.RED))

        # Dedup: keep highest-score per (rule, IP)
        best: Dict[Tuple[str, str], Alert] = {}
        for a in self._alerts:
            key = (a.rule_name, a.involved_ip)
            if key not in best or a.risk_score > best[key].risk_score:
                best[key] = a
        self._alerts = sorted(best.values(), key=lambda x: -x.risk_score)

        # Log every alert
        for a in self._alerts:
            logging.warning(
                "ALERT  rule=%-35s  ip=%-18s  sev=%-8s  score=%d",
                a.rule_name, a.involved_ip, a.severity, a.risk_score,
            )

        return self._alerts

    # ── reporting ─────────────────────────────────────────────────────

    def print_report(self, grouped_by_ip: bool = False) -> None:
        if not self._alerts:
            print(C.fmt("\n  ✔ No threats detected.\n", C.GREEN, C.BOLD))
            return

        title = (
            f"\n{'═'*72}\n"
            f"  DETECTION REPORT  –  {len(self._alerts)} ALERT(S)\n"
            f"{'═'*72}"
        )
        print(C.fmt(title, C.RED, C.BOLD))

        if grouped_by_ip:
            by_ip: Dict[str, List[Alert]] = defaultdict(list)
            for a in self._alerts:
                by_ip[a.involved_ip].append(a)
            for ip, alerts in sorted(by_ip.items(),
                                     key=lambda x: -max(a.risk_score for a in x[1])):
                score = self._tracker.score(ip)
                label = self._tracker.risk_label(ip)
                print(C.fmt(
                    f"\n  ┌── IP: {ip}  "
                    f"  Overall Risk: {score}/100  [{label}]", C.BOLD,
                ))
                for a in sorted(alerts, key=lambda x: -x.risk_score):
                    a.display()
        else:
            for a in self._alerts:
                a.display()

        # Summary table
        self._print_summary()

    def _print_summary(self) -> None:
        print(C.fmt("\n  ── Summary ──────────────────────────────────────────", C.BOLD))
        counts: Dict[str, int] = defaultdict(int)
        for a in self._alerts:
            counts[a.severity] += 1
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if counts[sev]:
                bar = "█" * counts[sev]
                print(f"  {C.severity(sev):30s}  {bar} ({counts[sev]})")
        avg  = sum(a.risk_score for a in self._alerts) / len(self._alerts)
        top5 = self._tracker.top(5)
        print(f"\n  Avg risk score : {C.fmt(f'{avg:.1f}/100', C.YELLOW, C.BOLD)}")
        print(f"  Total alerts   : {C.fmt(str(len(self._alerts)), C.BOLD)}")
        if top5:
            print(C.fmt("\n  Highest-risk IPs:", C.BOLD))
            for ip, score in top5:
                label = self._tracker.risk_label(ip)
                bar   = "▓" * (score // 10)
                print(f"    {C.fmt(ip, C.CYAN):20s}  {bar:<12s} {score:3d}/100  [{label}]")
        print()

    def print_ip_detail(self, ip: str) -> None:
        ip_alerts = [a for a in self._alerts if a.involved_ip == ip]
        if not ip_alerts:
            print(C.fmt(f"  [i] No alerts for IP {ip}", C.YELLOW))
            return
        print(C.fmt(f"\n  Detail for IP: {ip}", C.BOLD, C.CYAN))
        print(self._tracker.report(ip))
        for a in ip_alerts:
            a.display(show_events=True)

    # ── export ────────────────────────────────────────────────────────

    def export_txt(self, path: str = "alerts.txt") -> None:
        if not self._alerts:
            print(C.fmt("  [i] No alerts to export.", C.YELLOW))
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(
                f"THREAT DETECTION REPORT\n"
                f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Alerts    : {len(self._alerts)}\n\n"
            )
            for a in self._alerts:
                fh.write(a.to_text() + "\n\n")
        print(C.fmt(f"  [✔] Exported {len(self._alerts)} alert(s) → {path}", C.GREEN))

    def export_json(self, path: str = "alerts.json") -> None:
        if not self._alerts:
            print(C.fmt("  [i] No alerts to export.", C.YELLOW))
            return
        payload = {
            "generated_at": datetime.now().isoformat(),
            "total_alerts": len(self._alerts),
            "alerts":       [a.to_dict() for a in self._alerts],
            "ip_scores":    dict(self._tracker.top(50)),
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(C.fmt(f"  [✔] Exported {len(self._alerts)} alert(s) → {path}", C.GREEN))

    @property
    def alerts(self) -> List[Alert]:
        return list(self._alerts)

    @property
    def tracker(self) -> IPRiskTracker:
        return self._tracker


# ──────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────

MENU_TEXT = """
  ┌──────────────────────────────────────────────────┐
  │   {b}Threat Detection Rule Engine{r}                  │
  ├──────────────────────────────────────────────────┤
  │  {b}1{r}  Generate sample events                      │
  │  {b}2{r}  Load events from file (TSV / JSON)          │
  │  {b}3{r}  Show event statistics                       │
  │  {b}4{r}  Run threat detection                        │
  │  {b}5{r}  Show / re-display alerts                    │
  │  {b}6{r}  Show alerts grouped by IP                   │
  │  {b}7{r}  Show detail for a specific IP               │
  │  {b}8{r}  Export alerts (TXT + JSON)                  │
  │  {b}9{r}  Save events to file                         │
  │  {b}A{r}  List registered rules                       │
  │  {b}B{r}  Enable / disable a rule                     │
  │  {b}C{r}  Clear all loaded data                       │
  │  {b}0{r}  Exit                                        │
  └──────────────────────────────────────────────────┘
"""


class CLI:
    def __init__(self) -> None:
        self._store  = EventStore()
        self._engine = ThreatDetectionEngine()
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        for cls in [
            BruteForceRule,
            SuspiciousIPRule,
            RestrictedResourceRule,
            NomadLoginRule,
            PrivilegeEscalationRule,
            DataExfiltrationRule,
            PortScanRule,
            RepeatedErrorRule,
        ]:
            self._engine.register(cls())

    # ── helpers ───────────────────────────────────────────────────────

    def _prompt(self, msg: str) -> str:
        try:
            return input(C.fmt(msg, C.BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    def _require_events(self) -> bool:
        if not len(self._store):
            print(C.fmt("  [!] No events loaded. Use option 1 or 2 first.", C.YELLOW))
            return False
        return True

    def _require_alerts(self) -> bool:
        if not self._engine.alerts:
            print(C.fmt("  [!] No alerts yet. Run detection first (option 4).", C.YELLOW))
            return False
        return True

    # ── actions ───────────────────────────────────────────────────────

    def _do_generate(self) -> None:
        print(C.fmt("\n  Generating synthetic event stream …", C.CYAN))
        gen    = EventGenerator()
        events = gen.generate()
        self._store.add_all(events)
        print(C.fmt(f"  [✔] Generated {len(events):,} events (total: {len(self._store):,}).", C.GREEN))

    def _do_load(self) -> None:
        path = self._prompt("  File path (TSV or JSON): ")
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext == ".json":
            n = self._store.load_json(path)
        else:
            n = self._store.load_tsv(path)
        if n:
            print(C.fmt(f"  [✔] Loaded {n:,} event(s) (total: {len(self._store):,}).", C.GREEN))

    def _do_stats(self) -> None:
        if not self._require_events():
            return
        s = self._store.stats()
        print(C.fmt("\n  ── Event Statistics ───────────────────────────────────", C.BOLD))
        print(f"  Total events : {s['total']:,}")
        print(f"  Time span    : {s['span_min']:.1f} minutes")
        print(f"  Unique IPs   : {s['unique_ips']}")
        print(C.fmt("\n  By Event Type:", C.BOLD))
        for et, cnt in sorted(s["by_type"].items(), key=lambda x: -x[1]):
            print(f"    {et:20s}  {cnt:,}")
        print(C.fmt("\n  By Status:", C.BOLD))
        for st, cnt in sorted(s["by_status"].items(), key=lambda x: -x[1]):
            print(f"    {st:12s}  {cnt:,}")
        print(C.fmt("\n  Top 5 Source IPs:", C.BOLD))
        for ip, cnt in s["top_ips"]:
            print(f"    {ip:18s}  {cnt:,} event(s)")
        print()

    def _do_detect(self) -> None:
        if not self._require_events():
            return
        self._engine.run(self._store.all())
        self._engine.print_report()

    def _do_show_alerts(self) -> None:
        if not self._require_alerts():
            return
        self._engine.print_report()

    def _do_show_by_ip(self) -> None:
        if not self._require_alerts():
            return
        self._engine.print_report(grouped_by_ip=True)

    def _do_ip_detail(self) -> None:
        if not self._require_alerts():
            return
        ip = self._prompt("  Enter IP address: ")
        if ip:
            self._engine.print_ip_detail(ip)

    def _do_export(self) -> None:
        if not self._require_alerts():
            return
        self._engine.export_txt("alerts.txt")
        self._engine.export_json("alerts.json")

    def _do_save_events(self) -> None:
        if not self._require_events():
            return
        fmt  = self._prompt("  Format [tsv/json] (default: tsv): ").lower() or "tsv"
        path = self._prompt(f"  Output path [events.{fmt}]: ") or f"events.{fmt}"
        if fmt == "json":
            self._store.save_json(path)
        else:
            self._store.save_tsv(path)
        print(C.fmt(f"  [✔] Saved {len(self._store):,} event(s) → {path}", C.GREEN))

    def _do_list_rules(self) -> None:
        self._engine.list_rules()

    def _do_toggle_rule(self) -> None:
        self._engine.list_rules()
        name = self._prompt("  Rule name to toggle (exact): ")
        rule = next((r for r in self._engine._rules if r.name == name), None)
        if rule is None:
            print(C.fmt("  [!] Rule not found.", C.YELLOW))
            return
        rule.enabled = not rule.enabled
        state = "enabled" if rule.enabled else "disabled"
        print(C.fmt(f"  [✔] Rule '{name}' {state}.", C.GREEN))

    def _do_clear(self) -> None:
        self._store.clear()
        self._engine._alerts.clear()
        self._engine._tracker.reset()
        print(C.fmt("  [✔] All data cleared.", C.GREEN))

    # ── main loop ──────────────────────────────────────────────────────

    def run(self) -> None:
        banner()
        dispatch = {
            "1": self._do_generate,
            "2": self._do_load,
            "3": self._do_stats,
            "4": self._do_detect,
            "5": self._do_show_alerts,
            "6": self._do_show_by_ip,
            "7": self._do_ip_detail,
            "8": self._do_export,
            "9": self._do_save_events,
            "a": self._do_list_rules,
            "b": self._do_toggle_rule,
            "c": self._do_clear,
            "0": None,
        }

        while True:
            print(MENU_TEXT.format(b=C.BOLD, r=C.RESET))
            choice = self._prompt("  Select option ▶ ").lower()
            if choice == "0":
                print(C.fmt("\n  Goodbye.\n", C.CYAN))
                break
            action = dispatch.get(choice)
            if action is None and choice != "0":
                print(C.fmt(f"  [!] Unknown option '{choice}'.", C.YELLOW))
            elif action:
                try:
                    action()
                except Exception as exc:
                    print(C.fmt(f"  [ERROR] {exc}", C.RED))


# ──────────────────────────────────────────────────────────────────────
#  Demo Mode  (non-interactive smoke-test / quick look)
# ──────────────────────────────────────────────────────────────────────

def run_demo() -> None:
    banner()
    print(C.fmt("  [DEMO]  Generate → Detect → Export\n", C.MAGENTA, C.BOLD))

    # 1. Generate events
    store  = EventStore()
    events = EventGenerator().generate()
    store.add_all(events)
    s = store.stats()
    print(C.fmt(f"  [✔] {s['total']:,} events across {s['span_min']:.1f} min  "
                f"| {s['unique_ips']} IPs\n", C.GREEN))

    # 2. Build engine and run
    engine = ThreatDetectionEngine()
    for cls in [
        BruteForceRule, SuspiciousIPRule, RestrictedResourceRule,
        NomadLoginRule, PrivilegeEscalationRule, DataExfiltrationRule,
        PortScanRule, RepeatedErrorRule,
    ]:
        engine.register(cls())

    engine.run(store.all())
    engine.print_report(grouped_by_ip=False)

    # 3. Export
    engine.export_txt("alerts.txt")
    engine.export_json("alerts.json")
    store.save_tsv("events.tsv")

    print(C.fmt(
        "  Demo complete.\n"
        "  Files written: alerts.txt  alerts.json  events.tsv  threat_engine.log\n",
        C.CYAN,
    ))


# ──────────────────────────────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = {a.lstrip("-").lower() for a in sys.argv[1:]}
    if args & {"demo", "d"}:
        run_demo()
    else:
        CLI().run()


if __name__ == "__main__":
    main()