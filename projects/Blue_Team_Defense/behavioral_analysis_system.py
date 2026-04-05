#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║        Behavioral Analysis System  v1.0                                 ║
║        Pure Python · No External Dependencies                            ║
╚══════════════════════════════════════════════════════════════════════════╝

A statistical behavioral analysis engine that:
  • Builds per-user / per-IP behavior profiles from event streams
  • Detects anomalies using frequency analysis and baseline deviation
  • Scores risk, generates structured alerts, and exports results

Run:  python behavioral_analysis_system.py
      python behavioral_analysis_system.py --demo
"""

import os
import sys
import json
import math
import random
import logging
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────
#  Terminal Colours
# ──────────────────────────────────────────────────────────────────────────

class C:
    """ANSI colour helpers; degrades gracefully on Windows cmd."""
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
    def p(cls, text: str, *codes: str) -> str:
        return "".join(codes) + str(text) + cls.RESET

    @classmethod
    def severity(cls, sev: str) -> str:
        m = {"CRITICAL": cls.MAGENTA, "HIGH": cls.RED,
             "MEDIUM": cls.YELLOW, "LOW": cls.GREEN, "INFO": cls.CYAN}
        return cls.p(f"[{sev}]", m.get(sev.upper(), ""), cls.BOLD)


def banner() -> None:
    print(C.p(r"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ██████╗ ███████╗██╗  ██╗ █████╗ ██╗   ██╗                             ║
║  ██╔══██╗██╔════╝██║  ██║██╔══██╗██║   ██║                             ║
║  ██████╔╝█████╗  ███████║███████║██║   ██║                             ║
║  ██╔══██╗██╔══╝  ██╔══██║██╔══██║╚██╗ ██╔╝                             ║
║  ██████╔╝███████╗██║  ██║██║  ██║ ╚████╔╝                              ║
║  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝                              ║
║     Behavioral Analysis System  v1.0  ·  Pure Python                    ║
╚══════════════════════════════════════════════════════════════════════════╝
""", C.CYAN, C.BOLD))


# ──────────────────────────────────────────────────────────────────────────
#  Data Models
# ──────────────────────────────────────────────────────────────────────────

# Catalogues used for generation and profiling
ACTIONS    = ["login", "logout", "file_access", "request",
              "command", "data_transfer", "config_change", "privilege_use"]
STATUSES   = ["success", "failure", "blocked", "timeout"]

# Resources bucketed as normal / sensitive
NORMAL_RESOURCES = [
    "/home", "/dashboard", "/reports", "/api/v1/data",
    "/api/v1/products", "/search", "/profile",
    "/docs/README.md", "/logs/app.log",
]
SENSITIVE_RESOURCES = [
    "/admin", "/admin/users", "/etc/passwd", "/etc/shadow",
    "/.env", "/config/db", "/backup/full.tar.gz",
    "/api/internal/secrets", "/root/.ssh/id_rsa",
    "/var/log/auth.log", "/proc/1/maps",
]

# Hour-windows considered "off-hours" for a typical 9-17 office worker
BUSINESS_HOURS = set(range(8, 19))   # 08:00 – 18:59


@dataclass
class Event:
    """Normalised behavioural event."""
    timestamp:   datetime
    user_id:     str           # may be a user name or a source IP
    action:      str
    resource:    str
    status:      str
    extra:       Dict = field(default_factory=dict)

    # ── helpers ──────────────────────────────────────────────────────────

    @property
    def hour(self) -> int:
        return self.timestamp.hour

    @property
    def is_off_hours(self) -> bool:
        return self.hour not in BUSINESS_HOURS

    @property
    def is_sensitive(self) -> bool:
        rl = self.resource.lower()
        return any(s in rl for s in SENSITIVE_RESOURCES)

    def short(self) -> str:
        ts  = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        uid = C.p(f"{self.user_id:18s}", C.CYAN)
        act = C.p(f"{self.action:14s}", C.BOLD)
        res = self.resource[:35]
        st  = (C.p(self.status, C.GREEN)
               if self.status == "success"
               else C.p(self.status, C.RED))
        return f"  [{ts}] {uid} {act} {res:38s} {st}"

    # ── serialisation ────────────────────────────────────────────────────

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @staticmethod
    def from_dict(d: Dict) -> "Event":
        d = dict(d)
        d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        d.setdefault("extra", {})
        return Event(**d)

    def to_tsv(self) -> str:
        return "\t".join([
            self.timestamp.isoformat(),
            self.user_id, self.action,
            self.resource, self.status,
            json.dumps(self.extra),
        ])

    @staticmethod
    def from_tsv(line: str) -> Optional["Event"]:
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        parts = line.split("\t")
        if len(parts) < 5:
            return None
        try:
            extra = json.loads(parts[5]) if len(parts) > 5 else {}
            return Event(
                timestamp = datetime.fromisoformat(parts[0]),
                user_id   = parts[1],
                action    = parts[2],
                resource  = parts[3],
                status    = parts[4],
                extra     = extra,
            )
        except (ValueError, json.JSONDecodeError):
            return None


@dataclass
class AnomalyAlert:
    """A behavioural anomaly detected for a user / IP."""
    anomaly_type:   str
    severity:       str          # LOW | MEDIUM | HIGH | CRITICAL
    risk_score:     int          # 0–100
    user_id:        str
    description:    str
    related_events: List[Event]  = field(default_factory=list)
    detected_at:    datetime     = field(default_factory=datetime.now)
    tags:           List[str]    = field(default_factory=list)
    evidence:       Dict         = field(default_factory=dict)  # statistical evidence

    def display(self, show_events: bool = True) -> None:
        W   = 74
        sep = C.p("─" * W, C.DIM)
        print(sep)
        print(C.p(f"  🔍  {self.anomaly_type}", C.BOLD, C.YELLOW))
        print(f"  Severity   : {C.severity(self.severity)}")
        print(f"  Risk Score : {C.p(str(self.risk_score) + '/100', C.YELLOW, C.BOLD)}")
        print(f"  Entity     : {C.p(self.user_id, C.CYAN)}")
        print(f"  Detected   : {self.detected_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.tags:
            print(f"  Tags       : {' '.join(C.p('#' + t, C.BLUE) for t in self.tags)}")
        # Evidence block
        if self.evidence:
            ev_parts = []
            for k, v in self.evidence.items():
                if isinstance(v, float):
                    ev_parts.append(f"{k}={v:.2f}")
                else:
                    ev_parts.append(f"{k}={v}")
            print(f"  Evidence   : {C.p(', '.join(ev_parts), C.DIM)}")
        # Word-wrapped description
        lines = textwrap.wrap(self.description, W - 15)
        print(f"  Detail     : {lines[0]}")
        for ln in lines[1:]:
            print(f"               {ln}")
        if show_events and self.related_events:
            print(C.p(f"\n  Related Events ({len(self.related_events)}):", C.BOLD))
            for ev in self.related_events[:6]:
                print(ev.short())
            if len(self.related_events) > 6:
                print(C.p(f"    … +{len(self.related_events) - 6} more", C.DIM))
        print(sep)

    def to_dict(self) -> Dict:
        return {
            "anomaly_type": self.anomaly_type,
            "severity":     self.severity,
            "risk_score":   self.risk_score,
            "user_id":      self.user_id,
            "description":  self.description,
            "detected_at":  self.detected_at.isoformat(),
            "tags":         self.tags,
            "evidence":     self.evidence,
            "event_count":  len(self.related_events),
        }

    def to_text(self) -> str:
        lines = [
            "=" * 70,
            f"TYPE      : {self.anomaly_type}",
            f"SEVERITY  : {self.severity}",
            f"SCORE     : {self.risk_score}/100",
            f"ENTITY    : {self.user_id}",
            f"DETECTED  : {self.detected_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"TAGS      : {', '.join(self.tags)}",
            f"EVIDENCE  : {self.evidence}",
            f"DETAIL    : {self.description}",
            f"EVENTS ({len(self.related_events)}):",
        ]
        for ev in self.related_events[:10]:
            ts = ev.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(
                f"  [{ts}] {ev.user_id:18s} {ev.action:14s} "
                f"{ev.resource:35s} {ev.status}"
            )
        lines.append("=" * 70)
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────
#  Statistical Utilities  (no external libraries)
# ──────────────────────────────────────────────────────────────────────────

def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / (len(values) - 1)


def _stddev(values: List[float]) -> float:
    return math.sqrt(_variance(values))


def _z_score(value: float, mean: float, std: float) -> float:
    """Standard score; returns 0 when std is negligible."""
    return (value - mean) / std if std > 1e-9 else 0.0


def _percentile(values: List[float], pct: float) -> float:
    """Return the *pct*-th percentile (0–100) of *values*."""
    if not values:
        return 0.0
    s  = sorted(values)
    n  = len(s)
    k  = (n - 1) * pct / 100.0
    lo = int(k)
    hi = min(lo + 1, n - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _iqr_bounds(values: List[float], factor: float = 1.5) -> Tuple[float, float]:
    """Return (lower, upper) outlier fences using the IQR method."""
    q1 = _percentile(values, 25)
    q3 = _percentile(values, 75)
    iqr = q3 - q1
    return q1 - factor * iqr, q3 + factor * iqr


def _frequency_map(items: List[Any]) -> Dict[Any, int]:
    freq: Dict[Any, int] = defaultdict(int)
    for x in items:
        freq[x] += 1
    return dict(freq)


def _entropy(freq: Dict[Any, int]) -> float:
    """Shannon entropy of a frequency distribution."""
    total = sum(freq.values())
    if total == 0:
        return 0.0
    return -sum(
        (c / total) * math.log2(c / total)
        for c in freq.values() if c > 0
    )


# ──────────────────────────────────────────────────────────────────────────
#  Behavior Profile
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class BehaviorProfile:
    """
    Statistical summary of a single entity's (user / IP) normal behaviour,
    built from a training window of events.
    """
    user_id: str

    # ── temporal ─────────────────────────────────────────────────────────
    active_hours:        List[int]  = field(default_factory=list)   # all observed hours
    hour_freq:           Dict       = field(default_factory=dict)   # hour → count
    mean_hour:           float      = 0.0
    std_hour:            float      = 0.0

    # ── volume ────────────────────────────────────────────────────────────
    daily_event_counts:  List[int]  = field(default_factory=list)
    mean_daily:          float      = 0.0
    std_daily:           float      = 0.0
    p95_daily:           float      = 0.0

    # ── resources ────────────────────────────────────────────────────────
    resource_freq:       Dict       = field(default_factory=dict)   # resource → count
    rare_resources:      List[str]  = field(default_factory=list)   # seen < rare_threshold times
    sensitive_access_count: int     = 0

    # ── actions ───────────────────────────────────────────────────────────
    action_freq:         Dict       = field(default_factory=dict)
    failure_rate:        float      = 0.0   # fraction of events that failed

    # ── meta ──────────────────────────────────────────────────────────────
    total_events:        int        = 0
    training_days:       int        = 0
    trained_at:          Optional[datetime] = None
    sufficient:          bool       = False  # True when enough data to trust profile

    RARE_THRESHOLD = 2   # resource seen ≤ this many times → "rare"
    MIN_EVENTS     = 10  # minimum events to consider a profile trustworthy

    def summary(self) -> str:
        lines = [
            C.p(f"  Profile  : {self.user_id}", C.BOLD, C.CYAN),
            f"  Events   : {self.total_events} over {self.training_days} day(s)",
            f"  Avg/day  : {self.mean_daily:.1f}  (σ={self.std_daily:.1f}, p95={self.p95_daily:.1f})",
            f"  Hours    : mean={self.mean_hour:.1f}h  σ={self.std_hour:.1f}h",
            f"  Fail rate: {self.failure_rate * 100:.1f}%",
            f"  Resources: {len(self.resource_freq)} distinct  "
            f"({len(self.rare_resources)} rare, {self.sensitive_access_count} sensitive)",
            f"  Sufficient: {C.p('YES', C.GREEN) if self.sufficient else C.p('NO', C.YELLOW)}",
        ]
        return "\n".join(lines)


class ProfileBuilder:
    """
    Builds BehaviorProfile objects from a list of historical events.
    Profiles are stored in a registry keyed by user_id.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, BehaviorProfile] = {}

    # ── public API ────────────────────────────────────────────────────────

    def train(self, events: List[Event]) -> Dict[str, BehaviorProfile]:
        """
        Build / rebuild profiles for all entities in *events*.
        Returns the updated profile registry.
        """
        if not events:
            return {}

        by_user: Dict[str, List[Event]] = defaultdict(list)
        for ev in events:
            by_user[ev.user_id].append(ev)

        self._profiles = {}
        for uid, evts in by_user.items():
            self._profiles[uid] = self._build(uid, evts)

        return self._profiles

    def get(self, user_id: str) -> Optional[BehaviorProfile]:
        return self._profiles.get(user_id)

    def all_profiles(self) -> Dict[str, BehaviorProfile]:
        return dict(self._profiles)

    def count(self) -> int:
        return len(self._profiles)

    # ── internals ────────────────────────────────────────────────────────

    def _build(self, uid: str, events: List[Event]) -> BehaviorProfile:
        p = BehaviorProfile(user_id=uid)
        p.total_events  = len(events)
        p.trained_at    = datetime.now()
        p.sufficient    = p.total_events >= BehaviorProfile.MIN_EVENTS

        # ── temporal ─────────────────────────────────────────────────────
        hours            = [ev.hour for ev in events]
        p.active_hours   = hours
        p.hour_freq      = _frequency_map(hours)
        p.mean_hour      = _mean(hours)
        p.std_hour       = _stddev(hours)

        # ── volume (events per calendar day) ─────────────────────────────
        daily: Dict[str, int] = defaultdict(int)
        for ev in events:
            daily[ev.timestamp.strftime("%Y-%m-%d")] += 1
        dates = sorted(daily.keys())
        if len(dates) >= 2:
            # Fill in zero-event days in between
            start = datetime.strptime(dates[0],  "%Y-%m-%d")
            end   = datetime.strptime(dates[-1], "%Y-%m-%d")
            cursor = start
            counts: List[int] = []
            while cursor <= end:
                key = cursor.strftime("%Y-%m-%d")
                counts.append(daily.get(key, 0))
                cursor += timedelta(days=1)
            p.daily_event_counts = counts
        else:
            p.daily_event_counts = list(daily.values())

        p.mean_daily = _mean(p.daily_event_counts)
        p.std_daily  = _stddev(p.daily_event_counts)
        p.p95_daily  = _percentile(p.daily_event_counts, 95)
        p.training_days = len(p.daily_event_counts)

        # ── resources ────────────────────────────────────────────────────
        resources         = [ev.resource for ev in events]
        p.resource_freq   = _frequency_map(resources)
        p.rare_resources  = [
            r for r, cnt in p.resource_freq.items()
            if cnt <= BehaviorProfile.RARE_THRESHOLD
        ]
        p.sensitive_access_count = sum(
            1 for ev in events if ev.is_sensitive
        )

        # ── actions ───────────────────────────────────────────────────────
        p.action_freq = _frequency_map([ev.action for ev in events])
        failures      = sum(1 for ev in events if ev.status != "success")
        p.failure_rate = failures / len(events) if events else 0.0

        return p


# ──────────────────────────────────────────────────────────────────────────
#  Risk Scorer
# ──────────────────────────────────────────────────────────────────────────

class RiskScorer:
    """Tracks cumulative risk scores and reasoning per entity."""

    _SEV_DELTA = {"INFO": 2, "LOW": 5, "MEDIUM": 15, "HIGH": 30, "CRITICAL": 50}

    def __init__(self) -> None:
        self._scores:  Dict[str, int]        = defaultdict(int)
        self._history: Dict[str, List[str]]  = defaultdict(list)

    def bump(self, uid: str, reason: str, severity: str = "MEDIUM") -> None:
        delta = self._SEV_DELTA.get(severity.upper(), 10)
        self._scores[uid] = min(100, self._scores[uid] + delta)
        self._history[uid].append(f"[{severity.upper()}] {reason}")

    def score(self, uid: str) -> int:
        return self._scores.get(uid, 0)

    def label(self, uid: str) -> str:
        s = self.score(uid)
        if s >= 80: return "CRITICAL"
        if s >= 60: return "HIGH"
        if s >= 35: return "MEDIUM"
        if s >= 10: return "LOW"
        return "CLEAN"

    def top(self, n: int = 10) -> List[Tuple[str, int]]:
        return sorted(self._scores.items(), key=lambda x: -x[1])[:n]

    def history(self, uid: str) -> List[str]:
        return list(self._history.get(uid, []))

    def reset(self) -> None:
        self._scores.clear()
        self._history.clear()


# ──────────────────────────────────────────────────────────────────────────
#  Anomaly Detectors
# ──────────────────────────────────────────────────────────────────────────

class AnomalyDetector:
    """
    Base for all anomaly detectors.  Each subclass implements detect().
    """

    name: str = "BaseDetector"
    tags: List[str] = []

    def detect(
        self,
        user_id:  str,
        events:   List[Event],
        profile:  Optional[BehaviorProfile],
        scorer:   RiskScorer,
    ) -> List[AnomalyAlert]:
        raise NotImplementedError


# ── 1. Off-Hours Login ────────────────────────────────────────────────────

class OffHoursDetector(AnomalyDetector):
    """
    Flags login/auth events occurring outside the entity's normal active
    hours as established in its behavior profile.
    """
    name = "OFF_HOURS_ACTIVITY"
    tags = ["temporal", "auth", "insider-threat"]

    # If no profile: flag any logins outside conventional business hours
    STD_FACTOR = 2.0   # hours beyond mean ± N*std → suspicious

    def detect(self, user_id, events, profile, scorer):
        alerts: List[AnomalyAlert] = []
        candidates = [e for e in events
                      if e.action in ("login", "privilege_use", "config_change")]
        if not candidates:
            return []

        for ev in candidates:
            flagged = False
            evidence: Dict = {}

            if profile and profile.sufficient:
                # Statistical deviation from the user's own hour distribution
                z = abs(_z_score(ev.hour, profile.mean_hour, profile.std_hour))
                evidence = {
                    "event_hour": ev.hour,
                    "profile_mean_hour": round(profile.mean_hour, 1),
                    "profile_std_hour":  round(profile.std_hour, 1),
                    "z_score": round(z, 2),
                }
                if z >= self.STD_FACTOR and ev.hour not in profile.hour_freq:
                    flagged = True
            else:
                # Fallback: conventional business-hours check
                if ev.is_off_hours:
                    flagged = True
                    evidence = {"event_hour": ev.hour, "business_hours": "08-18"}

            if flagged:
                sev = "HIGH" if ev.is_off_hours else "MEDIUM"
                scorer.bump(user_id, f"Off-hours {ev.action} at {ev.hour:02d}:00", sev)
                alerts.append(AnomalyAlert(
                    anomaly_type   = self.name,
                    severity       = sev,
                    risk_score     = scorer.score(user_id),
                    user_id        = user_id,
                    description    = (
                        f"'{ev.action}' at {ev.hour:02d}:00 deviates from "
                        f"{user_id}'s normal activity window – possible "
                        f"account misuse or credential theft."
                    ),
                    related_events = [ev],
                    tags           = self.tags,
                    evidence       = evidence,
                ))
        return alerts


# ── 2. Sensitive / Rare Resource Access ───────────────────────────────────

class SensitiveResourceDetector(AnomalyDetector):
    """
    Flags access to known-sensitive paths and resources that are outside
    the entity's established resource profile.
    """
    name = "SENSITIVE_RESOURCE_ACCESS"
    tags = ["access-control", "data-theft", "recon"]

    def detect(self, user_id, events, profile, scorer):
        alerts: List[AnomalyAlert] = []
        known_resources = set(profile.resource_freq.keys()) if profile else set()

        sensitive_hits = [e for e in events if e.is_sensitive]
        rare_new_hits  = [
            e for e in events
            if e.resource not in known_resources and not e.is_sensitive
        ]

        if sensitive_hits:
            sev = "CRITICAL" if len(sensitive_hits) >= 3 else "HIGH"
            scorer.bump(user_id, f"Sensitive resource access x{len(sensitive_hits)}", sev)
            paths = list({e.resource for e in sensitive_hits})[:5]
            alerts.append(AnomalyAlert(
                anomaly_type   = self.name,
                severity       = sev,
                risk_score     = scorer.score(user_id),
                user_id        = user_id,
                description    = (
                    f"{user_id} accessed {len(sensitive_hits)} sensitive "
                    f"resource(s): {', '.join(paths)}. "
                    f"This may indicate reconnaissance or data exfiltration."
                ),
                related_events = sensitive_hits,
                tags           = self.tags,
                evidence       = {
                    "sensitive_hits": len(sensitive_hits),
                    "unique_paths": len(set(e.resource for e in sensitive_hits)),
                },
            ))

        if rare_new_hits and profile and profile.sufficient:
            scorer.bump(user_id, f"Rare/new resource access x{len(rare_new_hits)}", "MEDIUM")
            paths = list({e.resource for e in rare_new_hits})[:5]
            alerts.append(AnomalyAlert(
                anomaly_type   = "RARE_RESOURCE_ACCESS",
                severity       = "MEDIUM",
                risk_score     = scorer.score(user_id),
                user_id        = user_id,
                description    = (
                    f"{user_id} accessed {len(rare_new_hits)} resource(s) "
                    f"never seen during profiling: {', '.join(paths)}."
                ),
                related_events = rare_new_hits[:10],
                tags           = ["access-control", "new-behavior"],
                evidence       = {"new_resource_count": len(rare_new_hits)},
            ))

        return alerts


# ── 3. Activity Spike Detector ────────────────────────────────────────────

class ActivitySpikeDetector(AnomalyDetector):
    """
    Detects when an entity's event volume in a rolling window significantly
    exceeds its established baseline using z-score and IQR methods.
    """
    name = "ACTIVITY_SPIKE"
    tags = ["volume", "dos", "automation", "exfiltration"]

    WINDOW_MINUTES = 30       # rolling window size
    ABS_THRESHOLD  = 50       # absolute events in window (no-profile fallback)
    Z_THRESHOLD    = 2.5      # z-score threshold for spike

    def detect(self, user_id, events, profile, scorer):
        if not events:
            return []
        alerts: List[AnomalyAlert] = []
        events_s = sorted(events, key=lambda e: e.timestamp)
        window   = timedelta(minutes=self.WINDOW_MINUTES)

        # Count events in each rolling window starting from each event
        max_count   = 0
        peak_window: List[Event] = []
        for i, anchor in enumerate(events_s):
            wend = anchor.timestamp + window
            batch = [e for e in events_s[i:] if e.timestamp <= wend]
            if len(batch) > max_count:
                max_count   = len(batch)
                peak_window = batch

        if not peak_window:
            return []

        flagged   = False
        evidence: Dict = {"peak_count": max_count, "window_minutes": self.WINDOW_MINUTES}

        if profile and profile.sufficient and profile.mean_daily > 0:
            # Convert daily baseline to per-window expectation
            expected_per_window = (
                profile.mean_daily / (24 * 60 / self.WINDOW_MINUTES)
            )
            std_per_window = (
                profile.std_daily / (24 * 60 / self.WINDOW_MINUTES)
            )
            z = _z_score(max_count, expected_per_window, max(std_per_window, 1))
            _, iqr_upper = _iqr_bounds(
                [c / (24 * 60 / self.WINDOW_MINUTES)
                 for c in profile.daily_event_counts]
            )
            evidence.update({
                "expected_per_window": round(expected_per_window, 1),
                "z_score": round(z, 2),
                "iqr_upper": round(iqr_upper, 1),
            })
            if z >= self.Z_THRESHOLD or max_count > iqr_upper * 2:
                flagged = True
        else:
            if max_count >= self.ABS_THRESHOLD:
                flagged = True

        if flagged:
            sev = "CRITICAL" if max_count >= self.ABS_THRESHOLD * 2 else "HIGH"
            scorer.bump(user_id, f"Activity spike: {max_count} events in {self.WINDOW_MINUTES}min", sev)
            alerts.append(AnomalyAlert(
                anomaly_type   = self.name,
                severity       = sev,
                risk_score     = scorer.score(user_id),
                user_id        = user_id,
                description    = (
                    f"{max_count} events from {user_id} in a "
                    f"{self.WINDOW_MINUTES}-minute window – "
                    f"far above baseline. Possible automation, "
                    f"scanning, or denial-of-service behavior."
                ),
                related_events = peak_window[:20],
                tags           = self.tags,
                evidence       = evidence,
            ))

        return alerts


# ── 4. Failure Storm Detector ─────────────────────────────────────────────

class FailureStormDetector(AnomalyDetector):
    """
    Detects unusually high failure/blocked event rates – brute-force,
    fuzzing, misuse, or broken automation.
    """
    name = "FAILURE_STORM"
    tags = ["auth", "brute-force", "fuzzing", "error-flood"]

    WINDOW_SECONDS   = 300      # 5-minute window
    ABS_FAIL_THRESH  = 10       # absolute failures in window
    RATE_MULTIPLIER  = 3.0      # N× the profiled failure rate

    def detect(self, user_id, events, profile, scorer):
        alerts: List[AnomalyAlert] = []
        failures = sorted(
            [e for e in events if e.status in ("failure", "blocked", "timeout")],
            key=lambda e: e.timestamp,
        )
        if not failures:
            return []

        # Find the densest failure window
        window  = timedelta(seconds=self.WINDOW_SECONDS)
        max_f   = 0
        peak_f: List[Event] = []
        for i, anchor in enumerate(failures):
            batch = [f for f in failures[i:] if f.timestamp <= anchor.timestamp + window]
            if len(batch) > max_f:
                max_f   = len(batch)
                peak_f  = batch

        total_f   = len(failures)
        fail_rate = total_f / len(events) if events else 0.0
        evidence  = {
            "total_failures": total_f,
            "peak_in_window": max_f,
            "current_fail_rate": round(fail_rate, 3),
        }

        if profile and profile.sufficient:
            evidence["profiled_fail_rate"] = round(profile.failure_rate, 3)
            spike = (fail_rate > profile.failure_rate * self.RATE_MULTIPLIER
                     and fail_rate > 0.2)
        else:
            spike = fail_rate > 0.35

        if max_f >= self.ABS_FAIL_THRESH or spike:
            sev = "HIGH" if max_f >= self.ABS_FAIL_THRESH * 2 else "MEDIUM"
            scorer.bump(user_id, f"Failure storm: {max_f} failures in {self.WINDOW_SECONDS}s", sev)
            alerts.append(AnomalyAlert(
                anomaly_type   = self.name,
                severity       = sev,
                risk_score     = scorer.score(user_id),
                user_id        = user_id,
                description    = (
                    f"{max_f} failure/blocked events from {user_id} "
                    f"in {self.WINDOW_SECONDS // 60} min "
                    f"(failure rate {fail_rate * 100:.1f}%). "
                    f"Possible brute-force or credential stuffing."
                ),
                related_events = peak_f,
                tags           = self.tags,
                evidence       = evidence,
            ))

        return alerts


# ── 5. Impossible Travel / Multi-Location ────────────────────────────────

class MultiLocationDetector(AnomalyDetector):
    """
    Flags when the same logical user_id logs in from multiple distinct
    source IPs (stored in event.extra['peer_ip']) in a short window –
    a proxy for impossible travel or session hijacking.

    If events don't carry peer_ip, this detector uses action sequences
    to infer rapid context-switching between different resources/services
    as a weaker signal.
    """
    name = "MULTI_LOCATION_LOGIN"
    tags = ["auth", "impossible-travel", "account-takeover"]

    WINDOW_SECONDS   = 600    # 10-min window
    DISTINCT_THRESH  = 3      # distinct peer IPs

    def detect(self, user_id, events, profile, scorer):
        alerts: List[AnomalyAlert] = []
        logins = sorted(
            [e for e in events
             if e.action == "login" and e.status == "success"],
            key=lambda e: e.timestamp,
        )
        if len(logins) < 2:
            return []

        window = timedelta(seconds=self.WINDOW_SECONDS)
        for i, anchor in enumerate(logins):
            batch = [e for e in logins[i:]
                     if e.timestamp <= anchor.timestamp + window]
            peer_ips = {e.extra.get("peer_ip", e.resource) for e in batch}
            if len(peer_ips) >= self.DISTINCT_THRESH:
                scorer.bump(user_id, "Multi-location login", "HIGH")
                alerts.append(AnomalyAlert(
                    anomaly_type   = self.name,
                    severity       = "HIGH",
                    risk_score     = scorer.score(user_id),
                    user_id        = user_id,
                    description    = (
                        f"{user_id} logged in from {len(peer_ips)} distinct "
                        f"source(s) within {self.WINDOW_SECONDS // 60} min: "
                        f"{', '.join(list(peer_ips)[:5])}. "
                        f"Possible account takeover or credential sharing."
                    ),
                    related_events = batch,
                    tags           = self.tags,
                    evidence       = {
                        "distinct_sources": len(peer_ips),
                        "window_minutes": self.WINDOW_SECONDS // 60,
                    },
                ))
                break  # one alert per entity per run

        return alerts


# ── 6. Privilege Use Anomaly ──────────────────────────────────────────────

class PrivilegeAnomalyDetector(AnomalyDetector):
    """
    Flags privilege_use or config_change events that are rare in the
    entity's profile, especially after a sequence of failures.
    """
    name = "PRIVILEGE_ANOMALY"
    tags = ["privilege", "escalation", "insider-threat"]

    PRE_WINDOW_S = 300   # look back 5 min for failures before priv event

    def detect(self, user_id, events, profile, scorer):
        alerts: List[AnomalyAlert] = []
        priv_events = [e for e in events
                       if e.action in ("privilege_use", "config_change")]
        if not priv_events:
            return []

        # Check if privilege use is abnormal given profile
        profiled_priv = 0
        if profile and profile.sufficient:
            profiled_priv = (
                profile.action_freq.get("privilege_use", 0)
                + profile.action_freq.get("config_change", 0)
            )

        events_s = sorted(events, key=lambda e: e.timestamp)

        for pev in priv_events:
            # Look for failures shortly before this privilege event
            prior_failures = [
                e for e in events_s
                if e.status in ("failure", "blocked")
                and 0 < (pev.timestamp - e.timestamp).total_seconds() <= self.PRE_WINDOW_S
            ]
            evidence = {
                "prior_failures":    len(prior_failures),
                "profiled_priv_use": profiled_priv,
            }
            sev = "CRITICAL" if prior_failures else ("HIGH" if profiled_priv == 0 else "MEDIUM")
            scorer.bump(user_id, f"Privilege event after {len(prior_failures)} failure(s)", sev)
            alerts.append(AnomalyAlert(
                anomaly_type   = self.name,
                severity       = sev,
                risk_score     = scorer.score(user_id),
                user_id        = user_id,
                description    = (
                    f"{user_id} executed '{pev.action}' on '{pev.resource}'"
                    + (f" following {len(prior_failures)} failure(s)"
                       if prior_failures else "")
                    + (" – no privilege use in baseline."
                       if profiled_priv == 0 else "")
                    + " Possible privilege escalation or abuse."
                ),
                related_events = prior_failures + [pev],
                tags           = self.tags,
                evidence       = evidence,
            ))

        return alerts


# ── 7. Entropy / Diversity Anomaly ────────────────────────────────────────

class ResourceEntropyDetector(AnomalyDetector):
    """
    A sudden dramatic increase in the diversity of resources accessed
    (high entropy) indicates scanning or data harvesting behaviour.
    """
    name = "HIGH_RESOURCE_ENTROPY"
    tags = ["recon", "data-harvesting", "scanning"]

    ENTROPY_THRESHOLD = 3.5   # bits – high diversity
    MIN_EVENTS        = 15    # need enough events for entropy to be meaningful

    def detect(self, user_id, events, profile, scorer):
        alerts: List[AnomalyAlert] = []
        if len(events) < self.MIN_EVENTS:
            return []

        current_freq    = _frequency_map([e.resource for e in events])
        current_entropy = _entropy(current_freq)

        if profile and profile.sufficient:
            baseline_entropy = _entropy(profile.resource_freq)
            delta            = current_entropy - baseline_entropy
            evidence         = {
                "current_entropy":  round(current_entropy, 3),
                "baseline_entropy": round(baseline_entropy, 3),
                "delta":            round(delta, 3),
            }
            if delta >= 1.5:
                scorer.bump(user_id, f"Resource entropy spike Δ{delta:.2f}", "MEDIUM")
                alerts.append(AnomalyAlert(
                    anomaly_type   = self.name,
                    severity       = "MEDIUM",
                    risk_score     = scorer.score(user_id),
                    user_id        = user_id,
                    description    = (
                        f"{user_id} is accessing a far wider variety of resources "
                        f"(entropy={current_entropy:.2f} bits) than normal "
                        f"(baseline={baseline_entropy:.2f} bits, Δ={delta:.2f}). "
                        f"Possible data harvesting or scanning activity."
                    ),
                    related_events = events[:15],
                    tags           = self.tags,
                    evidence       = evidence,
                ))
        else:
            if current_entropy >= self.ENTROPY_THRESHOLD:
                scorer.bump(user_id, f"High resource entropy {current_entropy:.2f}", "MEDIUM")
                alerts.append(AnomalyAlert(
                    anomaly_type   = self.name,
                    severity       = "MEDIUM",
                    risk_score     = scorer.score(user_id),
                    user_id        = user_id,
                    description    = (
                        f"High resource diversity from {user_id} "
                        f"(entropy={current_entropy:.2f} bits > threshold "
                        f"{self.ENTROPY_THRESHOLD}). Possible scanning."
                    ),
                    related_events = events[:15],
                    tags           = self.tags,
                    evidence       = {"current_entropy": round(current_entropy, 3)},
                ))

        return alerts


# ── 8. Dormant Account Reactivation ───────────────────────────────────────

class DormantAccountDetector(AnomalyDetector):
    """
    Detects activity from an entity that has been inactive for a long
    period (relative to its profiled rhythm) – a common indicator of
    account compromise or insider re-activation.
    """
    name = "DORMANT_ACCOUNT_ACTIVITY"
    tags = ["auth", "account-takeover", "dormant"]

    DORMANCY_DAYS = 14   # inactive for at least this many days → alert

    def detect(self, user_id, events, profile, scorer):
        alerts: List[AnomalyAlert] = []
        if not profile or not profile.sufficient or not events:
            return []

        if not profile.trained_at:
            return []

        # The profile was trained on historical data.
        # The gap is between the last training event and the first new event.
        earliest_new = min(e.timestamp for e in events)
        gap_days     = (earliest_new - profile.trained_at).days

        if gap_days >= self.DORMANCY_DAYS:
            scorer.bump(user_id, f"Dormant account reactivated after {gap_days}d", "HIGH")
            alerts.append(AnomalyAlert(
                anomaly_type   = self.name,
                severity       = "HIGH",
                risk_score     = scorer.score(user_id),
                user_id        = user_id,
                description    = (
                    f"{user_id} showed activity after {gap_days} day(s) of inactivity. "
                    f"Dormant accounts being reactivated may indicate "
                    f"unauthorized access or insider threat."
                ),
                related_events = events[:5],
                tags           = self.tags,
                evidence       = {"dormancy_days": gap_days},
            ))

        return alerts


# ──────────────────────────────────────────────────────────────────────────
#  Behavioral Analysis Engine
# ──────────────────────────────────────────────────────────────────────────

class BehavioralAnalysisEngine:
    """
    Orchestrates profiling, anomaly detection, scoring, and reporting.

    Workflow:
        1. engine.train(training_events)     # build profiles
        2. engine.analyse(new_events)        # run detectors
        3. engine.print_report()             # display results
        4. engine.export(...)                # save to file
    """

    def __init__(self) -> None:
        self._builder   = ProfileBuilder()
        self._scorer    = RiskScorer()
        self._detectors: List[AnomalyDetector] = []
        self._alerts:    List[AnomalyAlert]    = []
        self._profiles:  Dict[str, BehaviorProfile] = {}
        self._trained    = False

        # Configure file logger
        logging.basicConfig(
            filename="behavioral_analysis.log",
            level=logging.INFO,
            format="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # ── setup ────────────────────────────────────────────────────────────

    def register(self, detector: AnomalyDetector) -> None:
        self._detectors.append(detector)

    # ── training ─────────────────────────────────────────────────────────

    def train(self, events: List[Event]) -> None:
        if not events:
            print(C.p("  [!] No events for training.", C.YELLOW))
            return

        print(C.p(
            f"\n  Training profiles from {len(events):,} events …", C.CYAN
        ))
        self._profiles = self._builder.train(events)
        self._trained  = True
        print(C.p(
            f"  [✔] Built {len(self._profiles)} behavior profile(s).", C.GREEN
        ))
        sufficient = sum(1 for p in self._profiles.values() if p.sufficient)
        print(C.p(
            f"      {sufficient} profile(s) have sufficient data "
            f"({len(self._profiles) - sufficient} sparse).", C.DIM
        ))

    # ── analysis ─────────────────────────────────────────────────────────

    def analyse(self, events: List[Event]) -> List[AnomalyAlert]:
        """
        Apply every registered detector to each entity's event slice.
        """
        if not events:
            print(C.p("  [!] No events to analyse.", C.YELLOW))
            return []

        self._alerts = []
        self._scorer.reset()
        active = [d for d in self._detectors if True]  # all enabled

        # Group events by user
        by_user: Dict[str, List[Event]] = defaultdict(list)
        for ev in events:
            by_user[ev.user_id].append(ev)

        n_entities = len(by_user)
        n_detectors = len(active)
        print(C.p(
            f"\n  Analysing {len(events):,} events across "
            f"{n_entities} entit(y/ies) with "
            f"{n_detectors} detector(s) …\n",
            C.CYAN,
        ))

        for det in active:
            det_alerts: List[AnomalyAlert] = []
            for uid, evts in by_user.items():
                profile = self._profiles.get(uid)
                try:
                    found = det.detect(uid, evts, profile, self._scorer)
                    det_alerts.extend(found)
                except Exception as exc:
                    print(C.p(f"  ✗ [{det.name}] error for {uid}: {exc}", C.RED))

            status = (
                C.p(f"  ✔ {det.name:38s} → {len(det_alerts)} alert(s)", C.GREEN)
                if det_alerts
                else C.p(f"  · {det.name:38s} → no alerts", C.DIM)
            )
            print(status)
            self._alerts.extend(det_alerts)

        # Deduplicate: keep highest-score per (type, user_id)
        best: Dict[Tuple[str, str], AnomalyAlert] = {}
        for a in self._alerts:
            key = (a.anomaly_type, a.user_id)
            if key not in best or a.risk_score > best[key].risk_score:
                best[key] = a
        self._alerts = sorted(best.values(), key=lambda x: -x.risk_score)

        # Log every alert
        for a in self._alerts:
            logging.warning(
                "ANOMALY  type=%-35s  user=%-20s  sev=%-8s  score=%d",
                a.anomaly_type, a.user_id, a.severity, a.risk_score,
            )

        return self._alerts

    # ── reporting ────────────────────────────────────────────────────────

    def print_report(self, grouped: bool = False) -> None:
        if not self._alerts:
            print(C.p("\n  ✔ No anomalies detected.\n", C.GREEN, C.BOLD))
            return

        hdr = (
            f"\n{'═' * 74}\n"
            f"  BEHAVIORAL ANOMALY REPORT  –  {len(self._alerts)} ALERT(S)\n"
            f"{'═' * 74}"
        )
        print(C.p(hdr, C.YELLOW, C.BOLD))

        if grouped:
            by_uid: Dict[str, List[AnomalyAlert]] = defaultdict(list)
            for a in self._alerts:
                by_uid[a.user_id].append(a)

            for uid, alerts in sorted(
                by_uid.items(),
                key=lambda x: -max(a.risk_score for a in x[1])
            ):
                sc  = self._scorer.score(uid)
                lbl = self._scorer.label(uid)
                print(C.p(
                    f"\n  ┌── Entity: {uid}   "
                    f"Risk: {sc}/100  [{lbl}]", C.BOLD,
                ))
                for a in sorted(alerts, key=lambda x: -x.risk_score):
                    a.display()
        else:
            for a in self._alerts:
                a.display()

        self._print_summary()

    def _print_summary(self) -> None:
        print(C.p("\n  ── Summary ──────────────────────────────────────────────", C.BOLD))
        counts: Dict[str, int] = defaultdict(int)
        for a in self._alerts:
            counts[a.severity] += 1
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if counts[sev]:
                bar = "█" * counts[sev]
                print(f"  {C.severity(sev):32s}  {bar} ({counts[sev]})")
        avg_score = sum(a.risk_score for a in self._alerts) / len(self._alerts)
        print(f"\n  Avg risk score : {C.p(f'{avg_score:.1f}/100', C.YELLOW, C.BOLD)}")
        print(f"  Total anomalies: {C.p(str(len(self._alerts)), C.BOLD)}")

        top = self._scorer.top(5)
        if top:
            print(C.p("\n  Top Risk Entities:", C.BOLD))
            for uid, score in top:
                lbl = self._scorer.label(uid)
                bar = "▓" * (score // 10)
                col = (C.MAGENTA if score >= 80 else
                       C.RED if score >= 60 else
                       C.YELLOW if score >= 35 else C.GREEN)
                print(f"    {C.p(uid, C.CYAN):26s}  "
                      f"{C.p(bar, col):<14s}  "
                      f"{score:3d}/100  [{lbl}]")
        print()

    def print_profiles(self) -> None:
        if not self._profiles:
            print(C.p("  [!] No profiles built yet.", C.YELLOW))
            return
        print(C.p(
            f"\n  ── Behavior Profiles ({len(self._profiles)}) "
            f"──────────────────────────────────", C.BOLD,
        ))
        for uid, p in sorted(self._profiles.items()):
            print()
            print(p.summary())
        print()

    def print_entity_detail(self, uid: str) -> None:
        p = self._profiles.get(uid)
        if p:
            print(C.p(f"\n  Behavior Profile – {uid}", C.BOLD, C.CYAN))
            print(p.summary())
            # Hour histogram
            if p.hour_freq:
                print(C.p("\n  Hour Distribution:", C.BOLD))
                for h in range(24):
                    cnt = p.hour_freq.get(h, 0)
                    bar = "▪" * min(cnt, 30)
                    print(f"    {h:02d}:00  {bar:30s} {cnt}")
            # Risk history
            hist = self._scorer.history(uid)
            if hist:
                print(C.p("\n  Risk History:", C.BOLD))
                for h in hist[-8:]:
                    print(f"    {C.p('▸', C.DIM)} {h}")
        else:
            print(C.p(f"  [i] No profile for '{uid}'.", C.YELLOW))

        uid_alerts = [a for a in self._alerts if a.user_id == uid]
        if uid_alerts:
            print(C.p(f"\n  Alerts for {uid} ({len(uid_alerts)}):", C.BOLD))
            for a in uid_alerts:
                a.display(show_events=False)
        print()

    # ── export ────────────────────────────────────────────────────────────

    def export_json(self, path: str = "anomaly_alerts.json") -> None:
        if not self._alerts:
            print(C.p("  [i] No alerts to export.", C.YELLOW))
            return
        payload = {
            "generated_at": datetime.now().isoformat(),
            "total_alerts": len(self._alerts),
            "alerts":       [a.to_dict() for a in self._alerts],
            "risk_scores":  {uid: self._scorer.score(uid)
                             for uid in {a.user_id for a in self._alerts}},
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(C.p(f"  [✔] Exported {len(self._alerts)} alert(s) → {path}", C.GREEN))

    def export_txt(self, path: str = "anomaly_alerts.txt") -> None:
        if not self._alerts:
            print(C.p("  [i] No alerts to export.", C.YELLOW))
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(
                f"BEHAVIORAL ANOMALY REPORT\n"
                f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Alerts    : {len(self._alerts)}\n\n"
            )
            for a in self._alerts:
                fh.write(a.to_text() + "\n\n")
        print(C.p(f"  [✔] Exported {len(self._alerts)} alert(s) → {path}", C.GREEN))

    # ── properties ───────────────────────────────────────────────────────

    @property
    def alerts(self) -> List[AnomalyAlert]:
        return list(self._alerts)

    @property
    def profiles(self) -> Dict[str, BehaviorProfile]:
        return dict(self._profiles)

    @property
    def is_trained(self) -> bool:
        return self._trained


# ──────────────────────────────────────────────────────────────────────────
#  Event Generator
# ──────────────────────────────────────────────────────────────────────────

class EventGenerator:
    """
    Produces two correlated event datasets:
      • *training set*  – a week of normal, profiled behaviour
      • *analysis set*  – current day with planted anomalies

    Planted anomalies:
      1. Off-hours login  (attacker logs in at 03:00)
      2. Sensitive resource sweep
      3. Activity spike (80 events in 20 min)
      4. Failure storm (15 failures in 4 min)
      5. Multi-location logins from 3 IPs
      6. Privilege escalation after failures
      7. High-entropy resource scan
      8. Data exfiltration burst
    """

    USERS = [
        "alice", "bob", "carol", "dave",
        "sysop", "analyst1", "analyst2",
    ]
    ATTACKER = "alice"   # compromised account
    ROGUE_IP = "198.51.100.7"

    def __init__(self, base: Optional[datetime] = None) -> None:
        self._base = (base or datetime.now()).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        random.seed(7)

    # ── helpers ───────────────────────────────────────────────────────────

    def _ev(self, dt: datetime, uid: str, action: str,
             resource: str, status: str = "success", **kw) -> Event:
        return Event(
            timestamp = dt,
            user_id   = uid,
            action    = action,
            resource  = resource,
            status    = status,
            extra     = kw,
        )

    def _rand_dt(self, day_offset: int = 0, hour_min: int = 8,
                 hour_max: int = 18) -> datetime:
        base = self._base - timedelta(days=day_offset)
        h = random.randint(hour_min, hour_max - 1)
        m = random.randint(0, 59)
        s = random.randint(0, 59)
        return base.replace(hour=h, minute=m, second=s)

    def _normal_day(self, uid: str, day: int, n: int = 30) -> List[Event]:
        """Generate a plausible normal workday for one user."""
        evts: List[Event] = []
        # Morning login
        evts.append(self._ev(
            self._rand_dt(day, 8, 10), uid,
            "login", random.choice(self.USERS) + "@workstation",
        ))
        # Bulk activity
        for _ in range(n):
            action   = random.choice(["request", "file_access", "request",
                                      "request", "data_transfer"])
            resource = random.choice(NORMAL_RESOURCES)
            status   = random.choices(
                ["success", "failure"], weights=[90, 10]
            )[0]
            evts.append(self._ev(
                self._rand_dt(day, 9, 17), uid, action, resource, status,
            ))
        # Evening logout
        evts.append(self._ev(
            self._rand_dt(day, 17, 19), uid, "logout",
            uid + "@workstation",
        ))
        return evts

    # ── training set ──────────────────────────────────────────────────────

    def training_set(self, days: int = 7) -> List[Event]:
        """7 days of normal activity for all users."""
        evts: List[Event] = []
        for uid in self.USERS:
            for day in range(1, days + 1):
                evts.extend(self._normal_day(uid, day, n=random.randint(20, 40)))
        evts.sort(key=lambda e: e.timestamp)
        return evts

    # ── analysis set with planted anomalies ───────────────────────────────

    def analysis_set(self) -> List[Event]:
        evts: List[Event] = []

        # Background noise: normal users today
        for uid in self.USERS:
            if uid != self.ATTACKER:
                evts.extend(self._normal_day(uid, 0, n=random.randint(15, 25)))

        base = self._base  # today 00:00

        # ── Anomaly 1: Off-hours login at 03:00 ──────────────────────────
        evts.append(self._ev(
            base.replace(hour=3, minute=12, second=7),
            self.ATTACKER, "login", "/auth/session",
            peer_ip=self.ROGUE_IP,
        ))

        # ── Anomaly 2: Sensitive resource sweep at 03:15 ─────────────────
        sweep_start = base.replace(hour=3, minute=15, second=0)
        for i, path in enumerate(SENSITIVE_RESOURCES):
            evts.append(self._ev(
                sweep_start + timedelta(seconds=i * 8),
                self.ATTACKER, "request", path, "blocked",
            ))

        # ── Anomaly 3: Activity spike – 80 events in 20 min ──────────────
        spike_start = base.replace(hour=4, minute=0, second=0)
        for i in range(80):
            dt = spike_start + timedelta(seconds=i * 15)
            evts.append(self._ev(
                dt, self.ATTACKER, "request",
                random.choice(NORMAL_RESOURCES + SENSITIVE_RESOURCES),
                random.choice(["success", "blocked"]),
            ))

        # ── Anomaly 4: Failure storm – 15 failures in 4 min ──────────────
        fail_start = base.replace(hour=5, minute=30, second=0)
        for i in range(15):
            dt = fail_start + timedelta(seconds=i * 16)
            evts.append(self._ev(
                dt, self.ATTACKER, "login", "/auth/session", "failure",
            ))

        # ── Anomaly 5: Multi-location logins (3 IPs in 5 min) ────────────
        multi_start = base.replace(hour=9, minute=0, second=0)
        for i, ip in enumerate(["10.10.5.1", "172.16.200.3", self.ROGUE_IP]):
            evts.append(self._ev(
                multi_start + timedelta(minutes=i * 1.5),
                self.ATTACKER, "login", "/auth/session",
                peer_ip=ip,
            ))

        # ── Anomaly 6: Privilege escalation after 3 failures ─────────────
        priv_start = base.replace(hour=10, minute=0, second=0)
        for i in range(3):
            evts.append(self._ev(
                priv_start + timedelta(seconds=i * 20),
                self.ATTACKER, "login", "/auth/sudo", "failure",
            ))
        evts.append(self._ev(
            priv_start + timedelta(minutes=2),
            self.ATTACKER, "privilege_use", "/root/.ssh/authorized_keys",
        ))
        evts.append(self._ev(
            priv_start + timedelta(minutes=3),
            self.ATTACKER, "config_change", "/etc/crontab",
        ))

        # ── Anomaly 7: High-entropy resource scan (many unique paths) ─────
        entropy_start = base.replace(hour=11, minute=0, second=0)
        all_paths = (
            NORMAL_RESOURCES + SENSITIVE_RESOURCES
            + [f"/srv/data/record_{i:04d}.db" for i in range(20)]
        )
        for i, path in enumerate(all_paths):
            evts.append(self._ev(
                entropy_start + timedelta(seconds=i * 10),
                self.ATTACKER, "file_access", path,
                random.choice(["success", "blocked"]),
            ))

        # ── Anomaly 8: Data exfiltration burst ────────────────────────────
        exfil_start = base.replace(hour=12, minute=0, second=0)
        for i in range(12):
            evts.append(self._ev(
                exfil_start + timedelta(seconds=i * 25),
                self.ATTACKER, "data_transfer",
                "/api/v1/export/full_db.csv",
                extra_bytes=random.randint(50, 200),
            ))

        evts.sort(key=lambda e: e.timestamp)
        return evts


# ──────────────────────────────────────────────────────────────────────────
#  Event Store
# ──────────────────────────────────────────────────────────────────────────

class EventStore:
    """In-memory event store with TSV and JSON persistence."""

    def __init__(self) -> None:
        self._train: List[Event] = []
        self._analyse: List[Event] = []

    def add_training(self, events: List[Event]) -> None:
        self._train.extend(events)
        self._train.sort(key=lambda e: e.timestamp)

    def add_analysis(self, events: List[Event]) -> None:
        self._analyse.extend(events)
        self._analyse.sort(key=lambda e: e.timestamp)

    def training_events(self) -> List[Event]:
        return list(self._train)

    def analysis_events(self) -> List[Event]:
        return list(self._analyse)

    def load_tsv(self, path: str, dataset: str = "analysis") -> int:
        n = 0
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    ev = Event.from_tsv(line)
                    if ev:
                        if dataset == "training":
                            self._train.append(ev)
                        else:
                            self._analyse.append(ev)
                        n += 1
        except FileNotFoundError:
            print(C.p(f"  [!] File not found: {path}", C.RED))
        except OSError as exc:
            print(C.p(f"  [!] I/O error: {exc}", C.RED))
        return n

    def save_tsv(self, events: List[Event], path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# Behavioral Analysis System – event log\n")
            for ev in events:
                fh.write(ev.to_tsv() + "\n")
        print(C.p(f"  [✔] Saved {len(events):,} event(s) → {path}", C.GREEN))

    def stats(self, events: List[Event]) -> Dict:
        if not events:
            return {}
        times = sorted(e.timestamp for e in events)
        span  = (times[-1] - times[0]).total_seconds() / 3600
        by_user: Dict[str, int]   = defaultdict(int)
        by_action: Dict[str, int] = defaultdict(int)
        by_status: Dict[str, int] = defaultdict(int)
        for e in events:
            by_user[e.user_id]   += 1
            by_action[e.action]  += 1
            by_status[e.status]  += 1
        return {
            "total":        len(events),
            "span_hours":   round(span, 1),
            "unique_users": len(by_user),
            "by_action":    dict(by_action),
            "by_status":    dict(by_status),
            "top_users":    sorted(by_user.items(), key=lambda x: -x[1])[:5],
        }

    def clear(self, dataset: str = "all") -> None:
        if dataset in ("training", "all"):
            self._train.clear()
        if dataset in ("analysis", "all"):
            self._analyse.clear()


# ──────────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────────

MENU_TEXT = """
  ┌────────────────────────────────────────────────────┐
  │  {b}Behavioral Analysis System{r}                      │
  ├────────────────────────────────────────────────────┤
  │  {b}1{r}  Generate synthetic event data               │
  │  {b}2{r}  Load events from file (TSV)                 │
  │  {b}3{r}  Show event statistics                       │
  │  {b}4{r}  Train behavior profiles                     │
  │  {b}5{r}  Run anomaly detection                       │
  │  {b}6{r}  Show / redisplay alerts                     │
  │  {b}7{r}  Show alerts grouped by entity               │
  │  {b}8{r}  Inspect entity (profile + alerts)           │
  │  {b}9{r}  Show all behavior profiles                  │
  │  {b}A{r}  Export alerts (JSON + TXT)                  │
  │  {b}B{r}  Save events to file                         │
  │  {b}C{r}  Clear all data                              │
  │  {b}0{r}  Exit                                        │
  └────────────────────────────────────────────────────┘
"""


class CLI:
    def __init__(self) -> None:
        self._store  = EventStore()
        self._engine = BehavioralAnalysisEngine()
        self._register_detectors()

    def _register_detectors(self) -> None:
        for cls in [
            OffHoursDetector,
            SensitiveResourceDetector,
            ActivitySpikeDetector,
            FailureStormDetector,
            MultiLocationDetector,
            PrivilegeAnomalyDetector,
            ResourceEntropyDetector,
            DormantAccountDetector,
        ]:
            self._engine.register(cls())

    # ── helpers ───────────────────────────────────────────────────────────

    def _ask(self, msg: str) -> str:
        try:
            return input(C.p(msg, C.BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    def _need_data(self, dataset: str = "analysis") -> bool:
        evts = (self._store.training_events()
                if dataset == "training"
                else self._store.analysis_events())
        if not evts:
            label = "training" if dataset == "training" else "analysis"
            print(C.p(f"  [!] No {label} events. Use option 1 or 2 first.", C.YELLOW))
            return False
        return True

    def _need_alerts(self) -> bool:
        if not self._engine.alerts:
            print(C.p("  [!] No alerts yet. Run detection first (option 5).", C.YELLOW))
            return False
        return True

    def _print_stats(self, events: List[Event], label: str) -> None:
        s = self._store.stats(events)
        if not s:
            return
        print(C.p(f"\n  ── {label} Statistics ─────────────────────────────────────", C.BOLD))
        print(f"  Total events : {s['total']:,}")
        print(f"  Time span    : {s['span_hours']:.1f} hours")
        print(f"  Unique users : {s['unique_users']}")
        print(C.p("\n  By Action:", C.BOLD))
        for act, cnt in sorted(s["by_action"].items(), key=lambda x: -x[1]):
            print(f"    {act:18s}  {cnt:,}")
        print(C.p("\n  By Status:", C.BOLD))
        for st, cnt in sorted(s["by_status"].items(), key=lambda x: -x[1]):
            print(f"    {st:12s}  {cnt:,}")
        print(C.p("\n  Top Entities:", C.BOLD))
        for uid, cnt in s["top_users"]:
            print(f"    {uid:20s}  {cnt:,} event(s)")
        print()

    # ── actions ───────────────────────────────────────────────────────────

    def _do_generate(self) -> None:
        print(C.p("\n  Generating synthetic event data …", C.CYAN))
        gen = EventGenerator()
        train = gen.training_set(days=7)
        analy = gen.analysis_set()
        self._store.add_training(train)
        self._store.add_analysis(analy)
        print(C.p(
            f"  [✔] Training set : {len(train):,} events (7 days)\n"
            f"  [✔] Analysis set : {len(analy):,} events (today + anomalies)",
            C.GREEN,
        ))

    def _do_load(self) -> None:
        path = self._ask("  File path (TSV): ")
        if not path:
            return
        ds = self._ask("  Dataset [training/analysis] (default: analysis): ").lower()
        ds = "training" if ds == "training" else "analysis"
        n = self._store.load_tsv(path, ds)
        if n:
            print(C.p(f"  [✔] Loaded {n:,} event(s) into '{ds}' set.", C.GREEN))

    def _do_stats(self) -> None:
        tr = self._store.training_events()
        an = self._store.analysis_events()
        if tr:
            self._print_stats(tr, "Training")
        if an:
            self._print_stats(an, "Analysis")
        if not tr and not an:
            print(C.p("  [!] No events loaded.", C.YELLOW))

    def _do_train(self) -> None:
        if not self._need_data("training"):
            return
        self._engine.train(self._store.training_events())

    def _do_detect(self) -> None:
        if not self._need_data("analysis"):
            return
        self._engine.analyse(self._store.analysis_events())
        self._engine.print_report()

    def _do_show_alerts(self) -> None:
        if not self._need_alerts():
            return
        self._engine.print_report()

    def _do_show_grouped(self) -> None:
        if not self._need_alerts():
            return
        self._engine.print_report(grouped=True)

    def _do_entity_detail(self) -> None:
        uid = self._ask("  Entity (user_id / IP): ")
        if uid:
            self._engine.print_entity_detail(uid)

    def _do_show_profiles(self) -> None:
        self._engine.print_profiles()

    def _do_export(self) -> None:
        if not self._need_alerts():
            return
        self._engine.export_json("anomaly_alerts.json")
        self._engine.export_txt("anomaly_alerts.txt")

    def _do_save_events(self) -> None:
        ds   = self._ask("  Dataset [training/analysis] (default: analysis): ").lower()
        ds   = "training" if ds == "training" else "analysis"
        evts = (self._store.training_events()
                if ds == "training"
                else self._store.analysis_events())
        if not evts:
            print(C.p(f"  [!] No '{ds}' events to save.", C.YELLOW))
            return
        path = self._ask(f"  Output path [{ds}_events.tsv]: ") or f"{ds}_events.tsv"
        self._store.save_tsv(evts, path)

    def _do_clear(self) -> None:
        self._store.clear()
        self._engine._alerts.clear()
        self._engine._profiles.clear()
        self._engine._trained = False
        self._engine._scorer.reset()
        print(C.p("  [✔] All data cleared.", C.GREEN))

    # ── main loop ──────────────────────────────────────────────────────────

    def run(self) -> None:
        banner()
        dispatch = {
            "1": self._do_generate,
            "2": self._do_load,
            "3": self._do_stats,
            "4": self._do_train,
            "5": self._do_detect,
            "6": self._do_show_alerts,
            "7": self._do_show_grouped,
            "8": self._do_entity_detail,
            "9": self._do_show_profiles,
            "a": self._do_export,
            "b": self._do_save_events,
            "c": self._do_clear,
            "0": None,
        }

        while True:
            print(MENU_TEXT.format(b=C.BOLD, r=C.RESET))
            choice = ""
            try:
                choice = input(C.p("  Select option ▶ ", C.BOLD)).strip().lower()
            except (EOFError, KeyboardInterrupt):
                choice = "0"

            if choice == "0":
                print(C.p("\n  Goodbye.\n", C.CYAN))
                break

            action = dispatch.get(choice)
            if action is None:
                print(C.p(f"  [!] Unknown option '{choice}'.", C.YELLOW))
            else:
                try:
                    action()
                except Exception as exc:
                    print(C.p(f"  [ERROR] {exc}", C.RED))


# ──────────────────────────────────────────────────────────────────────────
#  Demo Mode  (non-interactive pipeline)
# ──────────────────────────────────────────────────────────────────────────

def run_demo() -> None:
    banner()
    print(C.p("  [DEMO]  Generate → Train → Detect → Export\n", C.MAGENTA, C.BOLD))

    # 1. Generate data
    gen        = EventGenerator()
    train_evts = gen.training_set(days=7)
    anal_evts  = gen.analysis_set()
    print(C.p(f"  [✔] Training : {len(train_evts):,} events  |  "
              f"Analysis : {len(anal_evts):,} events", C.GREEN))

    # 2. Build engine + register all detectors
    engine = BehavioralAnalysisEngine()
    for cls in [
        OffHoursDetector, SensitiveResourceDetector, ActivitySpikeDetector,
        FailureStormDetector, MultiLocationDetector, PrivilegeAnomalyDetector,
        ResourceEntropyDetector, DormantAccountDetector,
    ]:
        engine.register(cls())

    # 3. Train
    engine.train(train_evts)

    # 4. Analyse
    engine.analyse(anal_evts)
    engine.print_report()

    # 5. Export
    engine.export_json("anomaly_alerts.json")
    engine.export_txt("anomaly_alerts.txt")

    # 6. Save events for reference
    store = EventStore()
    store.add_training(train_evts)
    store.add_analysis(anal_evts)
    store.save_tsv(train_evts, "training_events.tsv")
    store.save_tsv(anal_evts,  "analysis_events.tsv")

    print(C.p(
        "\n  Demo complete.\n"
        "  Files: anomaly_alerts.json  anomaly_alerts.txt  "
        "training_events.tsv  analysis_events.tsv  behavioral_analysis.log\n",
        C.CYAN,
    ))


# ──────────────────────────────────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────────────────────────────────

def main() -> None:
    args = {a.lstrip("-").lower() for a in sys.argv[1:]}
    if args & {"demo", "d"}:
        run_demo()
    else:
        CLI().run()


if __name__ == "__main__":
    main()