"""
=============================================================================
Metrics Aggregation System — Security / Log Data Analytics
=============================================================================
Author  : Senior Python Developer / Data Engineer / Cybersecurity Specialist
Purpose : Ingest simulated security log events, aggregate them into rich
          metrics (per-type, per-IP, per-minute, success/failure), detect
          basic trends, and export results to JSON.
Usage   : python metrics_aggregation_system.py
Deps    : Python standard library only (datetime, random, collections, json)
=============================================================================
"""

import collections
import datetime
import json
import math
import os
import random
import statistics
import time


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & CONFIGURATION DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────

EVENT_TYPES      = ["login", "request", "error", "alert"]
STATUSES         = ["success", "failure"]
EXPORT_FILENAME  = "metrics_report.json"

# Weighted probability for event types (login heavy, alert rare)
EVENT_WEIGHTS    = [0.35, 0.40, 0.15, 0.10]

# Weighted probability for status (more successes than failures)
STATUS_WEIGHTS   = [0.72, 0.28]

# IP pool: mix of internal (10.x) and external (203.x / 45.x) addresses
_IP_POOL: list[str] = (
    [f"10.0.0.{i}"     for i in range(1, 21)]   +   # 20 internal hosts
    [f"203.0.113.{i}"  for i in range(1, 11)]   +   # 10 external (doc range)
    [f"45.33.32.{i}"   for i in range(1, 6)]        #  5 "threat actor" IPs
)

# A small subset that will generate disproportionately more events
_NOISY_IPS: list[str] = random.sample(_IP_POOL[-5:], 3)  # 3 of the "threat" IPs

DEFAULT_NUM_EVENTS       = 500
DEFAULT_WINDOW_MINUTES   = 5      # sliding-window width for trend analysis
DEFAULT_TOP_N            = 10     # how many IPs / types to show in "top" lists


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────────────────────────────────────

class LogEvent:
    """
    Represents a single security log entry.

    Attributes
    ----------
    timestamp  : datetime of the event
    event_type : one of login / request / error / alert
    source_ip  : originating IP address (string)
    status     : "success" or "failure"
    event_id   : sequential integer identifier
    """

    __slots__ = ("event_id", "timestamp", "event_type", "source_ip", "status")

    def __init__(self, event_id: int, timestamp: datetime.datetime,
                 event_type: str, source_ip: str, status: str):
        self.event_id   = event_id
        self.timestamp  = timestamp
        self.event_type = event_type
        self.source_ip  = source_ip
        self.status     = status

    # Convenience: minute-precision bucket key
    @property
    def minute_key(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> dict:
        return {
            "event_id"  : self.event_id,
            "timestamp" : self.timestamp.isoformat(),
            "event_type": self.event_type,
            "source_ip" : self.source_ip,
            "status"    : self.status,
        }

    def __repr__(self) -> str:
        return (f"LogEvent(id={self.event_id}, "
                f"ts={self.timestamp.strftime('%H:%M:%S')}, "
                f"type={self.event_type}, ip={self.source_ip}, "
                f"status={self.status})")


# ─────────────────────────────────────────────────────────────────────────────
# DATA GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_log_events(
        num_events: int = DEFAULT_NUM_EVENTS,
        start_time: datetime.datetime | None = None,
        span_minutes: int = 60,
) -> list[LogEvent]:
    """
    Produce a list of synthetic security log events spread across
    *span_minutes* minutes starting from *start_time*.

    Design decisions
    ----------------
    • Timestamps are NOT perfectly uniform — events cluster in random
      bursts to mimic real traffic patterns.
    • "Noisy" IPs fire ~4× more often to create realistic hot-spots.
    • Errors and alerts are more likely to have status="failure".
    """
    if start_time is None:
        # Round down to the nearest minute for tidy time-window buckets
        now        = datetime.datetime.now()
        start_time = now.replace(second=0, microsecond=0)

    total_seconds = span_minutes * 60
    events: list[LogEvent] = []

    for eid in range(1, num_events + 1):
        # ── timestamp: clustered around random burst centres ──────────────
        offset_sec = int(random.triangular(0, total_seconds,
                                           random.randint(0, total_seconds)))
        ts = start_time + datetime.timedelta(seconds=offset_sec)

        # ── event type ────────────────────────────────────────────────────
        etype = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]

        # ── source IP: noisy IPs are over-represented ─────────────────────
        if random.random() < 0.25:          # 25 % of events from noisy IPs
            ip = random.choice(_NOISY_IPS)
        else:
            ip = random.choice(_IP_POOL)

        # ── status: errors/alerts fail more often ─────────────────────────
        if etype in ("error", "alert"):
            status = random.choices(STATUSES, weights=[0.35, 0.65], k=1)[0]
        else:
            status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

        events.append(LogEvent(
            event_id   = eid,
            timestamp  = ts,
            event_type = etype,
            source_ip  = ip,
            status     = status,
        ))

    # Sort chronologically for coherent display and window analysis
    events.sort(key=lambda e: e.timestamp)
    return events


# ─────────────────────────────────────────────────────────────────────────────
# AGGREGATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class MetricsAggregator:
    """
    Computes and stores all aggregated metrics from a list of LogEvents.

    Metrics produced
    ----------------
    • total_events             — int
    • events_by_type           — Counter  {event_type: count}
    • events_by_ip             — Counter  {ip: count}
    • events_by_status         — Counter  {status: count}
    • events_by_minute         — Counter  {minute_str: count}
    • failures_by_type         — Counter  {event_type: failure_count}
    • failures_by_ip           — Counter  {ip: failure_count}
    • type_status_matrix       — defaultdict(Counter)
                                  {event_type: {status: count}}
    • ip_type_matrix           — defaultdict(Counter)
                                  {ip: {event_type: count}}
    • sliding_windows          — list of SlidingWindowMetric
    • trend_analysis           — dict with per-window trend data
    """

    def __init__(self, window_minutes: int = DEFAULT_WINDOW_MINUTES):
        self.window_minutes = window_minutes

        # Core counters (populated by aggregate())
        self.total_events    : int                           = 0
        self.events_by_type  : collections.Counter          = collections.Counter()
        self.events_by_ip    : collections.Counter          = collections.Counter()
        self.events_by_status: collections.Counter          = collections.Counter()
        self.events_by_minute: collections.Counter          = collections.Counter()
        self.failures_by_type: collections.Counter          = collections.Counter()
        self.failures_by_ip  : collections.Counter          = collections.Counter()

        self.type_status_matrix: collections.defaultdict = \
            collections.defaultdict(collections.Counter)
        self.ip_type_matrix    : collections.defaultdict = \
            collections.defaultdict(collections.Counter)

        # Advanced structures
        self.sliding_windows: list[dict] = []
        self.trend_analysis : dict       = {}

        # Preserve the raw events for later slicing / display
        self._events: list[LogEvent] = []

    # ── public entry point ────────────────────────────────────────────────────

    def aggregate(self, events: list[LogEvent]) -> None:
        """
        Full aggregation pass over *events*.
        All internal state is reset before processing.
        """
        self._reset()
        self._events = events

        if not events:
            return

        self.total_events = len(events)

        # ── single-pass over all events ────────────────────────────────────
        for ev in events:
            # Core counters
            self.events_by_type[ev.event_type]   += 1
            self.events_by_ip[ev.source_ip]      += 1
            self.events_by_status[ev.status]     += 1
            self.events_by_minute[ev.minute_key] += 1

            # Failure-specific counters
            if ev.status == "failure":
                self.failures_by_type[ev.event_type] += 1
                self.failures_by_ip[ev.source_ip]    += 1

            # Cross-dimension matrices
            self.type_status_matrix[ev.event_type][ev.status] += 1
            self.ip_type_matrix[ev.source_ip][ev.event_type]  += 1

        # ── derived / advanced metrics ─────────────────────────────────────
        self._build_sliding_windows()
        self._build_trend_analysis()

    # ── sliding windows ────────────────────────────────────────────────────

    def _build_sliding_windows(self) -> None:
        """
        Partition the full time span into non-overlapping windows of
        *window_minutes* width and compute per-window metrics.
        """
        if not self._events:
            return

        first_ts = self._events[0].timestamp
        last_ts  = self._events[-1].timestamp

        # Align window start to the nearest lower multiple of window_minutes
        start = first_ts.replace(second=0, microsecond=0)
        start -= datetime.timedelta(minutes=start.minute % self.window_minutes)

        windows: list[dict] = []
        cursor = start
        while cursor <= last_ts:
            window_end = cursor + datetime.timedelta(minutes=self.window_minutes)

            # Collect events in [cursor, window_end)
            bucket = [
                ev for ev in self._events
                if cursor <= ev.timestamp < window_end
            ]

            if bucket:
                cnt_total    = len(bucket)
                cnt_failure  = sum(1 for e in bucket if e.status == "failure")
                type_counter = collections.Counter(e.event_type for e in bucket)
                ip_counter   = collections.Counter(e.source_ip  for e in bucket)
                failure_rate = round(cnt_failure / cnt_total * 100, 2) if cnt_total else 0.0

                windows.append({
                    "window_start"  : cursor.strftime("%H:%M"),
                    "window_end"    : window_end.strftime("%H:%M"),
                    "total"         : cnt_total,
                    "failures"      : cnt_failure,
                    "failure_rate"  : failure_rate,
                    "top_type"      : type_counter.most_common(1)[0][0],
                    "unique_ips"    : len(ip_counter),
                    "top_ip"        : ip_counter.most_common(1)[0][0],
                })

            cursor = window_end

        self.sliding_windows = windows

    # ── trend analysis ─────────────────────────────────────────────────────

    def _build_trend_analysis(self) -> None:
        """
        Derive simple trend signals from the sliding windows:
        • volume trend  : is traffic increasing, stable or decreasing?
        • failure trend : is the failure rate rising?
        • busiest window, quietest window
        • rate of change (events per window delta)
        """
        if len(self.sliding_windows) < 2:
            self.trend_analysis = {"status": "insufficient_data"}
            return

        volumes       = [w["total"]        for w in self.sliding_windows]
        failure_rates = [w["failure_rate"] for w in self.sliding_windows]

        # Linear regression slope via least-squares (no numpy required)
        def _slope(values: list[float]) -> float:
            n   = len(values)
            xs  = list(range(n))
            x_m = statistics.mean(xs)
            y_m = statistics.mean(values)
            num = sum((x - x_m) * (y - y_m) for x, y in zip(xs, values))
            den = sum((x - x_m) ** 2       for x in xs)
            return num / den if abs(den) > 1e-9 else 0.0

        vol_slope  = _slope([float(v) for v in volumes])
        fail_slope = _slope(failure_rates)

        # Classify slope as trend label
        def _label(slope: float, threshold: float = 0.5) -> str:
            if slope > threshold:
                return "INCREASING ↑"
            if slope < -threshold:
                return "DECREASING ↓"
            return "STABLE →"

        busiest  = max(self.sliding_windows, key=lambda w: w["total"])
        quietest = min(self.sliding_windows, key=lambda w: w["total"])

        # Rate of change: mean absolute difference between consecutive windows
        vol_deltas = [abs(volumes[i+1] - volumes[i])
                      for i in range(len(volumes) - 1)]
        mean_roc   = round(statistics.mean(vol_deltas), 2) if vol_deltas else 0.0

        # Z-score-like spike detection per window
        if len(volumes) >= 3:
            vol_mean = statistics.mean(volumes)
            vol_std  = statistics.stdev(volumes)
            spike_windows = [
                w["window_start"]
                for w in self.sliding_windows
                if vol_std > 0 and (w["total"] - vol_mean) / vol_std > 1.5
            ]
        else:
            spike_windows = []

        self.trend_analysis = {
            "volume_trend"          : _label(vol_slope),
            "failure_rate_trend"    : _label(fail_slope, threshold=0.1),
            "volume_slope"          : round(vol_slope, 3),
            "failure_slope"         : round(fail_slope, 3),
            "mean_rate_of_change"   : mean_roc,
            "peak_volume"           : max(volumes),
            "trough_volume"         : min(volumes),
            "busiest_window"        : busiest["window_start"],
            "quietest_window"       : quietest["window_start"],
            "spike_windows"         : spike_windows,
            "window_count"          : len(self.sliding_windows),
        }

    # ── helper: failure rate per type ─────────────────────────────────────

    def failure_rate_by_type(self) -> dict[str, float]:
        """Return {event_type: failure_rate_percent} rounded to 2 dp."""
        result = {}
        for etype in EVENT_TYPES:
            total   = self.events_by_type.get(etype, 0)
            failed  = self.failures_by_type.get(etype, 0)
            result[etype] = round(failed / total * 100, 2) if total else 0.0
        return result

    # ── reset ──────────────────────────────────────────────────────────────

    def _reset(self) -> None:
        self.total_events     = 0
        self.events_by_type   = collections.Counter()
        self.events_by_ip     = collections.Counter()
        self.events_by_status = collections.Counter()
        self.events_by_minute = collections.Counter()
        self.failures_by_type = collections.Counter()
        self.failures_by_ip   = collections.Counter()
        self.type_status_matrix = collections.defaultdict(collections.Counter)
        self.ip_type_matrix     = collections.defaultdict(collections.Counter)
        self.sliding_windows    = []
        self.trend_analysis     = {}
        self._events            = []

    # ── summary dict (for JSON export) ────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "generated_at"      : datetime.datetime.now().isoformat(),
            "total_events"      : self.total_events,
            "events_by_type"    : dict(self.events_by_type),
            "events_by_status"  : dict(self.events_by_status),
            "top_10_ips"        : dict(self.events_by_ip.most_common(10)),
            "failure_rate_pct"  : {
                "overall": round(
                    self.events_by_status.get("failure", 0)
                    / self.total_events * 100, 2
                ) if self.total_events else 0.0,
                **self.failure_rate_by_type(),
            },
            "failures_by_ip"    : dict(self.failures_by_ip.most_common(10)),
            "type_status_matrix": {
                k: dict(v) for k, v in self.type_status_matrix.items()
            },
            "sliding_windows"   : self.sliding_windows,
            "trend_analysis"    : self.trend_analysis,
        }


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY / FORMATTING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

# ANSI colour palette
_C = {
    "red"   : "\033[91m",
    "yellow": "\033[93m",
    "green" : "\033[92m",
    "cyan"  : "\033[96m",
    "blue"  : "\033[94m",
    "magenta": "\033[95m",
    "bold"  : "\033[1m",
    "dim"   : "\033[2m",
    "reset" : "\033[0m",
}
_USE_COLOR: bool = hasattr(os, "get_terminal_size")


def c(text: str, *styles: str) -> str:
    """Apply zero or more ANSI styles to *text* (no-op on unsupported terms)."""
    if not _USE_COLOR:
        return text
    prefix = "".join(_C.get(s, "") for s in styles)
    return f"{prefix}{text}{_C['reset']}"


def _bar(value: int, max_value: int, width: int = 30) -> str:
    """Render a simple ASCII progress bar."""
    filled = int(width * value / max_value) if max_value else 0
    bar    = "█" * filled + "░" * (width - filled)
    return f"[{bar}]"


def _section(title: str) -> None:
    """Print a coloured section divider."""
    border = "═" * 68
    print()
    print(c(f"╔{border}╗", "cyan"))
    print(c("║  " + title.upper().ljust(66) + "║", "cyan", "bold"))
    print(c(f"╚{border}╝", "cyan"))


def _sub(title: str) -> None:
    """Print a lighter sub-section divider."""
    print(c(f"\n  ┌─ {title} " + "─" * max(0, 56 - len(title)) + "┐", "blue"))


def _row(label: str, value: str, indent: int = 4) -> None:
    pad = " " * indent
    print(f"{pad}{c(label + ':', 'bold'):<38} {value}")


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def display_summary(agg: MetricsAggregator) -> None:
    """High-level overview of all aggregated metrics."""
    _section("📊  Aggregation Summary")

    if agg.total_events == 0:
        print(c("  ✖  No data to display.", "red"))
        return

    total    = agg.total_events
    success  = agg.events_by_status.get("success", 0)
    failure  = agg.events_by_status.get("failure", 0)
    fail_pct = round(failure / total * 100, 2) if total else 0.0

    # ── totals ────────────────────────────────────────────────────────────
    _sub("Overall Counts")
    _row("Total events",       c(str(total), "bold"))
    _row("Unique source IPs",  str(len(agg.events_by_ip)))
    _row("Time span (minutes)",str(len(agg.events_by_minute)))

    _sub("Status Breakdown")
    _row("Successes",
         f"{c(str(success), 'green')}  ({100 - fail_pct:.2f} %)")
    _row("Failures",
         f"{c(str(failure), 'red')}   ({fail_pct:.2f} %)")

    # ── events by type ────────────────────────────────────────────────────
    _sub("Events by Type")
    max_count = max(agg.events_by_type.values(), default=1)
    for etype in EVENT_TYPES:
        cnt  = agg.events_by_type.get(etype, 0)
        pct  = round(cnt / total * 100, 1) if total else 0.0
        bar  = _bar(cnt, max_count)
        fail = agg.failures_by_type.get(etype, 0)
        frate= round(fail / cnt * 100, 1) if cnt else 0.0
        colour = "yellow" if etype in ("error", "alert") else "green"
        print(f"    {c(etype.ljust(10), colour, 'bold')} "
              f"{bar} {c(str(cnt).rjust(5), 'bold')}  "
              f"({pct:5.1f} %)   fail-rate: "
              f"{c(f'{frate:5.1f}%', 'red' if frate > 40 else 'reset')}")

    # ── failure rates per type ────────────────────────────────────────────
    _sub("Failure Rate by Event Type")
    fr = agg.failure_rate_by_type()
    for etype, rate in sorted(fr.items(), key=lambda x: -x[1]):
        bar   = _bar(int(rate), 100, width=20)
        colour= "red" if rate > 50 else ("yellow" if rate > 25 else "green")
        print(f"    {etype.ljust(10)} {bar}  {c(f'{rate:6.2f} %', colour)}")


def display_top_ips(agg: MetricsAggregator, top_n: int = DEFAULT_TOP_N) -> None:
    """Display the most active source IPs with per-type breakdown."""
    _section(f"🌐  Top {top_n} Source IPs")

    if not agg.events_by_ip:
        print(c("  ✖  No IP data available.", "red"))
        return

    top_ips     = agg.events_by_ip.most_common(top_n)
    max_count   = top_ips[0][1] if top_ips else 1
    total       = agg.total_events

    header = (f"  {'#':>3}  {'IP Address':<18}  "
              f"{'Events':>7}  {'Share':>6}  "
              f"{'Failures':>8}  {'F-Rate':>7}  "
              f"{'Activity Bar':<32}")
    print(c(header, "bold"))
    print(c("  " + "─" * 86, "blue"))

    for rank, (ip, cnt) in enumerate(top_ips, 1):
        pct   = round(cnt / total * 100, 2) if total else 0.0
        fail  = agg.failures_by_ip.get(ip, 0)
        frate = round(fail / cnt * 100, 1) if cnt else 0.0
        bar   = _bar(cnt, max_count, width=28)
        alarm = c(" ⚠", "red", "bold") if frate > 50 or cnt > total * 0.05 else ""
        print(f"  {rank:>3}.  {ip:<18}  {cnt:>7}  "
              f"{pct:>5.2f} %  {fail:>8}  "
              f"{c(f'{frate:6.1f}%', 'red' if frate > 40 else 'reset'):>7}  "
              f"{bar}{alarm}")

    # Bonus: IPs with highest absolute failures
    _sub("Top IPs by Failures")
    top_fail = agg.failures_by_ip.most_common(min(5, top_n))
    max_fail = top_fail[0][1] if top_fail else 1
    for ip, fail_cnt in top_fail:
        total_for_ip = agg.events_by_ip[ip]
        frate        = round(fail_cnt / total_for_ip * 100, 1)
        bar          = _bar(fail_cnt, max_fail, width=22)
        print(f"    {ip:<18}  {bar}  "
              f"{c(str(fail_cnt), 'red')} failures  "
              f"({frate:.1f} % of their traffic)")


def display_time_windows(agg: MetricsAggregator) -> None:
    """Display per-minute event distribution and sliding-window metrics."""
    _section("⏱  Time-Window Analysis")

    if not agg.events_by_minute:
        print(c("  ✖  No time-window data available.", "red"))
        return

    # ── per-minute heatmap (up to 30 most recent minutes) ─────────────────
    _sub("Events per Minute (last 30 minutes)")
    sorted_minutes = sorted(agg.events_by_minute.items())
    display_slice  = sorted_minutes[-30:]
    max_min_count  = max(v for _, v in display_slice) if display_slice else 1

    for minute, cnt in display_slice:
        bar    = _bar(cnt, max_min_count, width=35)
        colour = "red" if cnt > max_min_count * 0.8 else (
                 "yellow" if cnt > max_min_count * 0.5 else "green")
        print(f"    {minute}  {bar}  {c(str(cnt).rjust(4), colour)}")

    # ── sliding windows ────────────────────────────────────────────────────
    _sub(f"Sliding Windows ({agg.window_minutes}-minute buckets)")
    if not agg.sliding_windows:
        print("    No window data computed.")
        return

    hdr = (f"  {'Window':^12}  {'Events':>7}  "
           f"{'Failures':>9}  {'F-Rate':>7}  "
           f"{'Unique IPs':>11}  {'Top Type':<10}  Top IP")
    print(c(hdr, "bold"))
    print(c("  " + "─" * 82, "blue"))

    max_win = max(w["total"] for w in agg.sliding_windows)
    for w in agg.sliding_windows:
        frate  = w["failure_rate"]
        colour = "red" if frate > 40 else ("yellow" if frate > 20 else "green")
        print(f"  {w['window_start']:>5}–{w['window_end']:<5}   "
              f"{w['total']:>7}  "
              f"{w['failures']:>9}  "
              f"{c(f'{frate:6.2f}%', colour):>7}  "
              f"{w['unique_ips']:>11}  "
              f"{w['top_type']:<10}  {w['top_ip']}")


def display_trend_analysis(agg: MetricsAggregator) -> None:
    """Display trend signals derived from sliding windows."""
    _section("📈  Trend Analysis")

    tr = agg.trend_analysis
    if tr.get("status") == "insufficient_data" or not tr:
        print(c("  ⚠  Not enough windows to derive trends (need ≥ 2).", "yellow"))
        return

    _sub("Traffic Volume Trend")
    _row("Volume trend",
         c(tr["volume_trend"],
           "red" if "INC" in tr["volume_trend"] else "green"))
    _row("Volume slope (events/window)", str(tr["volume_slope"]))
    _row("Mean rate of change",          str(tr["mean_rate_of_change"]))
    _row("Peak window volume",           str(tr["peak_volume"]))
    _row("Trough window volume",         str(tr["trough_volume"]))
    _row("Busiest window",               tr["busiest_window"])
    _row("Quietest window",              tr["quietest_window"])
    _row("Windows analysed",             str(tr["window_count"]))

    _sub("Failure Rate Trend")
    _row("Failure rate trend",
         c(tr["failure_rate_trend"],
           "red" if "INC" in tr["failure_rate_trend"] else "green"))
    _row("Failure slope (%/window)",     str(tr["failure_slope"]))

    _sub("Spike Detection (Z > 1.5)")
    spikes = tr.get("spike_windows", [])
    if spikes:
        for sw in spikes:
            print(f"    {c('⚠  Spike detected at window starting', 'red', 'bold')} "
                  f"{c(sw, 'yellow', 'bold')}")
    else:
        print(c("    ✔  No abnormal traffic spikes detected.", "green"))


def display_cross_matrix(agg: MetricsAggregator) -> None:
    """Display the event-type × status cross-tabulation matrix."""
    _section("🔀  Event Type × Status Matrix")

    if not agg.type_status_matrix:
        print(c("  ✖  No matrix data available.", "red"))
        return

    col_w = 12
    # Header row
    header = f"  {'Event Type':<14}" + "".join(
        s.rjust(col_w) for s in STATUSES) + "   Total  Fail-Rate"
    print(c(header, "bold"))
    print(c("  " + "─" * 58, "blue"))

    for etype in EVENT_TYPES:
        row    = agg.type_status_matrix.get(etype, collections.Counter())
        total  = sum(row.values())
        fail   = row.get("failure", 0)
        frate  = round(fail / total * 100, 1) if total else 0.0
        colour = "red" if frate > 50 else ("yellow" if frate > 25 else "green")
        cells  = "".join(str(row.get(s, 0)).rjust(col_w) for s in STATUSES)
        print(f"  {etype:<14}{cells}  {str(total).rjust(6)}   "
              f"{c(f'{frate:5.1f}%', colour)}")


def display_raw_sample(events: list[LogEvent], n: int = 20) -> None:
    """Print the first *n* raw log events in a table."""
    _section(f"📋  Raw Event Sample (first {n} of {len(events)})")

    if not events:
        print(c("  ✖  No events to display.", "red"))
        return

    header = (f"  {'ID':>5}  {'Timestamp':^19}  {'Type':<10}  "
              f"{'Source IP':<18}  Status")
    print(c(header, "bold"))
    print(c("  " + "─" * 72, "blue"))

    for ev in events[:n]:
        colour = "red" if ev.status == "failure" else "green"
        type_c = "yellow" if ev.event_type in ("error", "alert") else "reset"
        print(f"  {ev.event_id:>5}  "
              f"{ev.timestamp.strftime('%Y-%m-%d %H:%M:%S'):^19}  "
              f"{c(ev.event_type.ljust(10), type_c)}  "
              f"{ev.source_ip:<18}  "
              f"{c(ev.status, colour)}")


# ─────────────────────────────────────────────────────────────────────────────
# JSON EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def export_metrics_json(agg: MetricsAggregator,
                        filename: str = EXPORT_FILENAME) -> str:
    """
    Serialise all aggregated metrics to a JSON file.
    Returns the absolute path of the written file.
    """
    filepath = os.path.abspath(filename)
    payload  = agg.to_dict()

    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)

    return filepath


# ─────────────────────────────────────────────────────────────────────────────
# INPUT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def prompt_int(prompt: str, default: int,
               min_val: int = 1, max_val: int = 100_000) -> int:
    while True:
        raw = input(f"  {prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(c(f"  ⚠  Enter a value between {min_val} and {max_val}.", "yellow"))
        except ValueError:
            print(c("  ⚠  Please enter a whole number.", "yellow"))


def prompt_yes_no(prompt: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    raw = input(f"  {prompt} [{default_str}]: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")


# ─────────────────────────────────────────────────────────────────────────────
# APPLICATION STATE
# ─────────────────────────────────────────────────────────────────────────────

_events   : list[LogEvent]     = []
_aggregator: MetricsAggregator = MetricsAggregator()
_aggregated: bool              = False

_config: dict = {
    "num_events"    : DEFAULT_NUM_EVENTS,
    "span_minutes"  : 60,
    "window_minutes": DEFAULT_WINDOW_MINUTES,
    "top_n"         : DEFAULT_TOP_N,
}


# ─────────────────────────────────────────────────────────────────────────────
# MENU HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

def menu_generate() -> None:
    global _events, _aggregated
    print(c("\n  ── Generate Log Events ──", "bold"))

    if prompt_yes_no("Customise generation parameters?", default=False):
        _config["num_events"]   = prompt_int(
            "Number of events to generate", _config["num_events"], 10, 100_000)
        _config["span_minutes"] = prompt_int(
            "Time span (minutes)",          _config["span_minutes"], 1, 1440)

    _events     = generate_log_events(
        num_events   = _config["num_events"],
        span_minutes = _config["span_minutes"],
    )
    _aggregated = False   # Invalidate previous aggregation

    print(c(f"\n  ✔  Generated {len(_events)} log events.", "green"))
    print(f"     Span    : {_events[0].timestamp.strftime('%H:%M:%S')} "
          f"→ {_events[-1].timestamp.strftime('%H:%M:%S')}")
    print(f"     Types   : { {t: sum(1 for e in _events if e.event_type==t) for t in EVENT_TYPES} }")
    print(f"     Statuses: { {s: sum(1 for e in _events if e.status==s) for s in STATUSES} }")


def menu_aggregate() -> None:
    global _aggregator, _aggregated
    if not _events:
        print(c("\n  ✖  No data. Please generate events first (option 1).", "red"))
        return

    print(c("\n  ── Run Aggregation ──", "bold"))

    if prompt_yes_no("Customise aggregation parameters?", default=False):
        _config["window_minutes"] = prompt_int(
            "Sliding window width (minutes)", _config["window_minutes"], 1, 120)
        _config["top_n"]          = prompt_int(
            "Top-N count for IP ranking",     _config["top_n"],          1, 50)

    _aggregator = MetricsAggregator(window_minutes=_config["window_minutes"])
    start_ts    = time.perf_counter()
    _aggregator.aggregate(_events)
    elapsed     = time.perf_counter() - start_ts
    _aggregated = True

    print(c(f"\n  ✔  Aggregation complete in {elapsed * 1000:.2f} ms.", "green"))
    print(f"     Events processed  : {_aggregator.total_events}")
    print(f"     Unique IPs        : {len(_aggregator.events_by_ip)}")
    print(f"     Sliding windows   : {len(_aggregator.sliding_windows)}")


def _require_aggregation() -> bool:
    """Return True if aggregated data exists; print an error otherwise."""
    if not _aggregated or _aggregator.total_events == 0:
        print(c("\n  ✖  No aggregated data. Please run aggregation first (option 2).",
                "red"))
        return False
    return True


def menu_view_summary() -> None:
    if _require_aggregation():
        display_summary(_aggregator)


def menu_view_ips() -> None:
    if _require_aggregation():
        display_top_ips(_aggregator, top_n=_config["top_n"])


def menu_view_windows() -> None:
    if _require_aggregation():
        display_time_windows(_aggregator)


def menu_view_trends() -> None:
    if _require_aggregation():
        display_trend_analysis(_aggregator)


def menu_view_matrix() -> None:
    if _require_aggregation():
        display_cross_matrix(_aggregator)


def menu_view_raw() -> None:
    if not _events:
        print(c("\n  ✖  No events. Please generate data first (option 1).", "red"))
        return
    n = prompt_int("How many raw events to display?", 20, 1, len(_events))
    display_raw_sample(_events, n=n)


def menu_view_all() -> None:
    """Run all display functions in one shot."""
    if not _require_aggregation():
        return
    display_summary(_aggregator)
    display_top_ips(_aggregator, top_n=_config["top_n"])
    display_time_windows(_aggregator)
    display_trend_analysis(_aggregator)
    display_cross_matrix(_aggregator)


def menu_export() -> None:
    if not _require_aggregation():
        return
    fname    = input(f"  Output filename [{EXPORT_FILENAME}]: ").strip()
    fname    = fname if fname else EXPORT_FILENAME
    filepath = export_metrics_json(_aggregator, fname)
    print(c(f"\n  ✔  Metrics exported to: {filepath}", "green"))
    size_kb = os.path.getsize(filepath) / 1024
    print(f"     File size: {size_kb:.1f} KB")


def menu_config() -> None:
    print(c("\n  ── Current Configuration ──\n", "bold"))
    labels = {
        "num_events"    : "Events to generate",
        "span_minutes"  : "Time span (minutes)",
        "window_minutes": "Sliding window size (min)",
        "top_n"         : "Top-N for IP display",
    }
    for k, lbl in labels.items():
        print(f"  {lbl:<30} : {_config[k]}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# MENU SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

MENU: dict[str, tuple[str, object]] = {
    "1" : ("Generate log events",            menu_generate),
    "2" : ("Run aggregation",                menu_aggregate),
    "3" : ("View summary metrics",           menu_view_summary),
    "4" : ("View top IPs",                   menu_view_ips),
    "5" : ("View time-window analysis",      menu_view_windows),
    "6" : ("View trend analysis",            menu_view_trends),
    "7" : ("View type × status matrix",      menu_view_matrix),
    "8" : ("View raw event sample",          menu_view_raw),
    "9" : ("View ALL metrics (full report)", menu_view_all),
    "E" : ("Export metrics to JSON",         menu_export),
    "C" : ("Show configuration",             menu_config),
    "0" : ("Exit",                           None),
}


def print_header() -> None:
    border = "═" * 68
    print(c(f"\n╔{border}╗", "cyan"))
    print(c("║{:^68}║".format("  📊  SECURITY METRICS AGGREGATION SYSTEM  📊  "), "cyan"))
    print(c(f"╚{border}╝\n", "cyan"))


def print_menu() -> None:
    print(c("\n  ┌─ Main Menu " + "─" * 44 + "┐", "cyan"))
    for key, (label, _) in MENU.items():
        print(f"  │  {c(f'[{key}]', 'bold')}  {label:<46} │")
    print(c("  └" + "─" * 56 + "┘\n", "cyan"))


def main() -> None:
    print_header()
    print("  Welcome to the Security Metrics Aggregation System.")
    print("  Quickstart: generate data (1) → aggregate (2) → view full report (9).\n")

    while True:
        print_menu()
        choice = input("  Enter option: ").strip().upper()

        if choice not in MENU:
            print(c("  ⚠  Invalid option — please choose from the menu.", "yellow"))
            continue

        label, handler = MENU[choice]
        if choice == "0":
            print(c("\n  Goodbye! Stay secure. 🔒\n", "green"))
            break

        print(c(f"\n  → {label}", "bold"))
        try:
            handler()
        except KeyboardInterrupt:
            print(c("\n  ⚠  Operation interrupted by user.", "yellow"))
        except Exception as exc:
            print(c(f"\n  ✖  Unexpected error: {exc}", "red"))


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(c("\n\n  Session terminated. Goodbye!\n", "yellow"))