"""
bandwidth_limiter_tool.py
A Python OOP simulation of a network bandwidth limiter and traffic controller.
"""

import time
import random
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from collections import deque


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class StreamStatus(Enum):
    ACTIVE    = "ACTIVE"
    LIMITED   = "LIMITED"
    THROTTLED = "THROTTLED"
    PAUSED    = "PAUSED"
    CLOSED    = "CLOSED"


class Priority(Enum):
    CRITICAL = 1   # highest – nearly never throttled
    HIGH     = 2
    NORMAL   = 3
    LOW      = 4
    BULK     = 5   # lowest – first to be squeezed


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _fmt_bw(mbps: float) -> str:
    """Human-readable bandwidth string."""
    if mbps >= 1000:
        return f"{mbps / 1000:.2f} Gbps"
    if mbps >= 1:
        return f"{mbps:.2f} Mbps"
    return f"{mbps * 1000:.1f} Kbps"


def _validate_ip(ip: str, label: str = "IP") -> None:
    parts = ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        raise ValueError(f"Invalid {label}: {ip!r}")


# ─────────────────────────────────────────────
# NetworkStream
# ─────────────────────────────────────────────

class NetworkStream:
    """Represents a single active network flow between two endpoints."""

    _id_counter = 0
    _lock = threading.Lock()

    def __init__(self, source: str, destination: str,
                 requested_bandwidth: float, priority: Priority = Priority.NORMAL):
        _validate_ip(source, "source IP")
        _validate_ip(destination, "destination IP")
        if source == destination:
            raise ValueError("Source and destination cannot be the same.")
        if requested_bandwidth <= 0:
            raise ValueError("requested_bandwidth must be > 0 Mbps.")
        if not isinstance(priority, Priority):
            raise TypeError("priority must be a Priority enum.")

        with NetworkStream._lock:
            NetworkStream._id_counter += 1
            self.stream_id: int = NetworkStream._id_counter

        self.source: str                    = source
        self.destination: str               = destination
        self.requested_bandwidth: float     = requested_bandwidth   # Mbps
        self.current_bandwidth: float       = 0.0                   # Mbps (after limiting)
        self.priority: Priority             = priority
        self.status: StreamStatus           = StreamStatus.ACTIVE
        self._bytes_transferred: float      = 0.0                   # MB (simulated)
        self._history: deque                = deque(maxlen=10)       # last N bw samples
        self._created_at: float             = time.time()

    # ── simulation ───────────────────────────

    def tick(self, interval: float = 1.0) -> None:
        """Simulate data transfer for one time interval (default 1 s)."""
        if self.status in (StreamStatus.PAUSED, StreamStatus.CLOSED):
            return
        self._bytes_transferred += self.current_bandwidth * interval  # MB
        self._history.append(self.current_bandwidth)

    # ── accessors ────────────────────────────

    @property
    def utilisation_pct(self) -> float:
        """How much of the requested bandwidth is being allocated."""
        if self.requested_bandwidth == 0:
            return 0.0
        return min(100.0, self.current_bandwidth / self.requested_bandwidth * 100)

    @property
    def avg_bandwidth(self) -> float:
        return sum(self._history) / len(self._history) if self._history else 0.0

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._created_at

    def summary(self) -> str:
        bar_len = 20
        filled  = int(self.utilisation_pct / 100 * bar_len)
        bar     = "█" * filled + "░" * (bar_len - filled)
        return (
            f"  Stream #{self.stream_id:<3} [{bar}] {self.utilisation_pct:5.1f}%  "
            f"{_fmt_bw(self.current_bandwidth):>12} / {_fmt_bw(self.requested_bandwidth):<12}  "
            f"P={self.priority.name:<8}  {self.status.value:<9}  "
            f"{self.source} → {self.destination}"
        )

    def __repr__(self) -> str:
        return (f"NetworkStream(id={self.stream_id}, "
                f"{self.source}→{self.destination}, "
                f"bw={_fmt_bw(self.current_bandwidth)}, "
                f"status={self.status.value})")


# ─────────────────────────────────────────────
# BandwidthRule
# ─────────────────────────────────────────────

class BandwidthRule:
    """Defines a bandwidth policy that can be attached to a stream."""

    def __init__(self, rule_id: str, max_bandwidth: float,
                 priority_override: Optional[Priority] = None,
                 burst_allowance: float = 0.0,
                 description: str = ""):
        if not rule_id or not isinstance(rule_id, str):
            raise ValueError("rule_id must be a non-empty string.")
        if max_bandwidth <= 0:
            raise ValueError("max_bandwidth must be > 0 Mbps.")
        if burst_allowance < 0:
            raise ValueError("burst_allowance must be ≥ 0 Mbps.")

        self.rule_id: str                          = rule_id
        self.max_bandwidth: float                  = max_bandwidth        # Mbps
        self.priority_override: Optional[Priority] = priority_override
        self.burst_allowance: float                = burst_allowance      # extra Mbps for bursts
        self.description: str                      = description
        self._applied_count: int                   = 0

    def effective_limit(self, burst: bool = False) -> float:
        return self.max_bandwidth + (self.burst_allowance if burst else 0.0)

    def apply(self, stream: NetworkStream, burst: bool = False) -> float:
        """Apply this rule to a stream; return the allocated bandwidth."""
        limit = self.effective_limit(burst)
        allocated = min(stream.requested_bandwidth, limit)
        stream.current_bandwidth = allocated
        if self.priority_override:
            stream.priority = self.priority_override
        if allocated < stream.requested_bandwidth:
            stream.status = StreamStatus.LIMITED
        else:
            stream.status = StreamStatus.ACTIVE
        self._applied_count += 1
        return allocated

    def __repr__(self) -> str:
        return (f"BandwidthRule(id={self.rule_id!r}, "
                f"max={_fmt_bw(self.max_bandwidth)}, "
                f"burst=+{_fmt_bw(self.burst_allowance)})")


# ─────────────────────────────────────────────
# TrafficController
# ─────────────────────────────────────────────

class TrafficController:
    """Enforces bandwidth rules on a collection of streams."""

    def __init__(self, total_capacity: float):
        if total_capacity <= 0:
            raise ValueError("total_capacity must be > 0 Mbps.")
        self.total_capacity: float                      = total_capacity
        self._stream_rules: dict[int, BandwidthRule]    = {}   # stream_id → rule
        self._enforcement_log: list[str]                = []

    # ── rule assignment ──────────────────────

    def assign_rule(self, stream: NetworkStream, rule: BandwidthRule) -> None:
        if not isinstance(stream, NetworkStream):
            raise TypeError("stream must be a NetworkStream.")
        if not isinstance(rule, BandwidthRule):
            raise TypeError("rule must be a BandwidthRule.")
        self._stream_rules[stream.stream_id] = rule
        msg = (f"Rule {rule.rule_id!r} assigned to Stream #{stream.stream_id} "
               f"(limit={_fmt_bw(rule.max_bandwidth)})")
        self._enforcement_log.append(msg)

    def remove_rule(self, stream: NetworkStream) -> None:
        removed = self._stream_rules.pop(stream.stream_id, None)
        if removed:
            self._enforcement_log.append(
                f"Rule {removed.rule_id!r} removed from Stream #{stream.stream_id}")

    # ── enforcement ──────────────────────────

    def enforce(self, streams: list[NetworkStream], burst: bool = False) -> dict:
        """
        Apply rules to all streams.  For streams without an explicit rule,
        apply fair-share allocation of the remaining capacity.
        Returns a summary dict.
        """
        if not streams:
            return {}

        # Sort by priority so high-priority streams are allocated first
        ordered = sorted(
            [s for s in streams if s.status != StreamStatus.CLOSED],
            key=lambda s: s.priority.value
        )

        remaining_capacity = self.total_capacity
        ruled_streams      = set()
        total_allocated    = 0.0

        # ── pass 1: apply explicit rules ──
        for stream in ordered:
            rule = self._stream_rules.get(stream.stream_id)
            if rule:
                cap_before = remaining_capacity
                alloc = rule.apply(stream, burst=burst)
                alloc = min(alloc, remaining_capacity)
                stream.current_bandwidth = alloc
                remaining_capacity -= alloc
                remaining_capacity  = max(0.0, remaining_capacity)
                total_allocated    += alloc
                ruled_streams.add(stream.stream_id)
                if alloc < stream.requested_bandwidth:
                    stream.status = StreamStatus.THROTTLED
                self._enforcement_log.append(
                    f"  Enforced rule {rule.rule_id!r} on Stream #{stream.stream_id}: "
                    f"allocated {_fmt_bw(alloc)} "
                    f"(cap remaining: {_fmt_bw(remaining_capacity)})"
                )

        # ── pass 2: fair-share for unruled streams ──
        unruled = [s for s in ordered if s.stream_id not in ruled_streams]
        if unruled and remaining_capacity > 0:
            total_requested = sum(s.requested_bandwidth for s in unruled)
            for stream in unruled:
                if total_requested > 0:
                    share   = stream.requested_bandwidth / total_requested
                    alloc   = min(stream.requested_bandwidth,
                                  remaining_capacity * share)
                else:
                    alloc   = 0.0
                stream.current_bandwidth = alloc
                total_allocated         += alloc
                remaining_capacity      -= alloc
                remaining_capacity       = max(0.0, remaining_capacity)
                if alloc < stream.requested_bandwidth:
                    stream.status = StreamStatus.LIMITED
                else:
                    stream.status = StreamStatus.ACTIVE

        return {
            "total_capacity":  self.total_capacity,
            "total_allocated": total_allocated,
            "remaining":       remaining_capacity,
            "streams_enforced": len(ordered),
        }

    @property
    def enforcement_log(self) -> list[str]:
        return list(self._enforcement_log)


# ─────────────────────────────────────────────
# LimiterEngine
# ─────────────────────────────────────────────

class LimiterEngine:
    """
    Monitors streams over time and dynamically adjusts allocations
    to react to overuse, underuse, or priority changes.
    """

    def __init__(self, controller: TrafficController, tick_interval: float = 1.0):
        if not isinstance(controller, TrafficController):
            raise TypeError("controller must be a TrafficController.")
        if tick_interval <= 0:
            raise ValueError("tick_interval must be > 0.")
        self._controller    = controller
        self._tick_interval = tick_interval
        self._tick_count    = 0
        self._alerts: list[str] = []

    def _detect_anomalies(self, streams: list[NetworkStream]) -> None:
        """Flag streams that are consistently over- or under-utilised."""
        for s in streams:
            if s.status == StreamStatus.CLOSED:
                continue
            if len(s._history) >= 3:
                avg = s.avg_bandwidth
                # Chronically starved high-priority stream
                if s.priority in (Priority.CRITICAL, Priority.HIGH):
                    if avg < s.requested_bandwidth * 0.5:
                        self._alerts.append(
                            f"  ⚠  Stream #{s.stream_id} (PRIORITY {s.priority.name}) "
                            f"starved — avg {_fmt_bw(avg)} vs "
                            f"requested {_fmt_bw(s.requested_bandwidth)}")
                # Bulk stream consuming too much
                if s.priority == Priority.BULK:
                    if avg > self._controller.total_capacity * 0.3:
                        self._alerts.append(
                            f"  ⚠  BULK Stream #{s.stream_id} consuming "
                            f"{_fmt_bw(avg)} (>30% of link capacity)")

    def _dynamic_adjust(self, streams: list[NetworkStream]) -> None:
        """
        Simulate dynamic adjustment: slightly vary requested bandwidth
        to model real traffic fluctuations, then re-enforce.
        """
        for s in streams:
            if s.status in (StreamStatus.CLOSED, StreamStatus.PAUSED):
                continue
            # fluctuate ±10 %
            delta = s.requested_bandwidth * random.uniform(-0.10, 0.10)
            s.requested_bandwidth = max(0.1, s.requested_bandwidth + delta)

    def run_tick(self, streams: list[NetworkStream],
                 burst: bool = False) -> dict:
        """Execute one monitoring / enforcement cycle."""
        self._tick_count += 1

        # Simulate traffic fluctuations
        self._dynamic_adjust(streams)

        # Re-enforce rules
        stats = self._controller.enforce(streams, burst=burst)

        # Advance simulation clock on each stream
        for s in streams:
            s.tick(self._tick_interval)

        # Anomaly detection
        self._detect_anomalies(streams)

        stats["tick"] = self._tick_count
        return stats

    @property
    def alerts(self) -> list[str]:
        return list(self._alerts)

    def clear_alerts(self) -> None:
        self._alerts.clear()


# ─────────────────────────────────────────────
# LimiterManager
# ─────────────────────────────────────────────

class LimiterManager:
    """Top-level façade: manage streams, rules, engine, and reporting."""

    def __init__(self, link_capacity: float):
        if link_capacity <= 0:
            raise ValueError("link_capacity must be > 0 Mbps.")
        self.link_capacity: float = link_capacity
        self._streams: dict[int, NetworkStream]    = {}
        self._rules:   dict[str, BandwidthRule]    = {}
        self._controller = TrafficController(link_capacity)
        self._engine     = LimiterEngine(self._controller)
        self._tick_stats: list[dict]               = []

    # ── stream management ────────────────────

    def add_stream(self, stream: NetworkStream) -> None:
        if not isinstance(stream, NetworkStream):
            raise TypeError("stream must be a NetworkStream.")
        self._streams[stream.stream_id] = stream
        print(f"  ✔  Stream #{stream.stream_id} added  "
              f"({stream.source} → {stream.destination}, "
              f"req={_fmt_bw(stream.requested_bandwidth)}, "
              f"priority={stream.priority.name})")

    def close_stream(self, stream_id: int) -> None:
        s = self._streams.get(stream_id)
        if s is None:
            raise KeyError(f"Stream #{stream_id} not found.")
        s.status = StreamStatus.CLOSED
        s.current_bandwidth = 0.0
        print(f"  ✖  Stream #{stream_id} closed.")

    def pause_stream(self, stream_id: int) -> None:
        s = self._streams.get(stream_id)
        if s is None:
            raise KeyError(f"Stream #{stream_id} not found.")
        s.status = StreamStatus.PAUSED
        s.current_bandwidth = 0.0
        print(f"  ⏸  Stream #{stream_id} paused.")

    def resume_stream(self, stream_id: int) -> None:
        s = self._streams.get(stream_id)
        if s is None:
            raise KeyError(f"Stream #{stream_id} not found.")
        if s.status == StreamStatus.PAUSED:
            s.status = StreamStatus.ACTIVE
            print(f"  ▶  Stream #{stream_id} resumed.")

    # ── rule management ──────────────────────

    def add_rule(self, rule: BandwidthRule) -> None:
        if not isinstance(rule, BandwidthRule):
            raise TypeError("rule must be a BandwidthRule.")
        self._rules[rule.rule_id] = rule
        print(f"  ✔  Rule {rule.rule_id!r} added "
              f"(max={_fmt_bw(rule.max_bandwidth)}"
              + (f", burst=+{_fmt_bw(rule.burst_allowance)}" if rule.burst_allowance else "")
              + f")  — {rule.description}")

    def apply_rule_to_stream(self, rule_id: str, stream_id: int) -> None:
        rule   = self._rules.get(rule_id)
        stream = self._streams.get(stream_id)
        if rule is None:
            raise KeyError(f"Rule {rule_id!r} not found.")
        if stream is None:
            raise KeyError(f"Stream #{stream_id} not found.")
        self._controller.assign_rule(stream, rule)
        print(f"  ✔  Rule {rule_id!r} → Stream #{stream_id}.")

    # ── simulation ───────────────────────────

    def run_simulation(self, ticks: int = 5, burst_at: Optional[set] = None,
                       label: str = "") -> None:
        if ticks < 1:
            raise ValueError("ticks must be ≥ 1.")
        burst_at = burst_at or set()
        active   = [s for s in self._streams.values()
                    if s.status != StreamStatus.CLOSED]

        if label:
            print(f"\n  {'─' * 54}")
            print(f"  {label}")
            print(f"  {'─' * 54}")

        for t in range(1, ticks + 1):
            burst = t in burst_at
            stats = self._engine.run_tick(active, burst=burst)
            self._tick_stats.append(stats)

            burst_tag = "  ⚡ BURST" if burst else ""
            print(f"\n  Tick {t:>2}/{ticks}  |  "
                  f"Allocated: {_fmt_bw(stats['total_allocated']):>12}  /  "
                  f"Capacity: {_fmt_bw(stats['total_capacity'])}"
                  f"{burst_tag}")
            print(f"  {'Stream':<10} {'Progress Bar':>22}   "
                  f"{'Allocated':>12}   {'Requested':>12}   "
                  f"{'Priority':<10}  {'Status'}")
            print(f"  {'─' * 100}")
            for s in sorted(active, key=lambda x: x.priority.value):
                if s.status != StreamStatus.CLOSED:
                    print(s.summary())

            # Print any new alerts
            if self._engine.alerts:
                for alert in self._engine.alerts:
                    print(alert)
                self._engine.clear_alerts()

            time.sleep(0.15)   # small delay for readability

    # ── statistics ───────────────────────────

    def print_statistics(self) -> None:
        sep = "═" * 62
        print(f"\n{sep}")
        print("  BANDWIDTH LIMITER — FINAL STATISTICS")
        print(sep)

        active_streams = [s for s in self._streams.values()
                          if s.status != StreamStatus.CLOSED]

        print(f"  Link capacity    : {_fmt_bw(self.link_capacity)}")
        print(f"  Total streams    : {len(self._streams)}")
        print(f"  Active streams   : {len(active_streams)}")
        print(f"  Rules defined    : {len(self._rules)}")
        print(f"  Simulation ticks : {len(self._tick_stats)}")

        if self._tick_stats:
            avg_alloc = sum(t["total_allocated"] for t in self._tick_stats) / len(self._tick_stats)
            peak      = max(t["total_allocated"] for t in self._tick_stats)
            print(f"  Avg allocation   : {_fmt_bw(avg_alloc)}")
            print(f"  Peak allocation  : {_fmt_bw(peak)}")
            utilisation = avg_alloc / self.link_capacity * 100
            print(f"  Avg utilisation  : {utilisation:.1f}%")

        if self._streams:
            print(f"\n  Per-stream summary:")
            print(f"  {'ID':<5} {'Source':>15} {'Destination':>15} "
                  f"{'Avg BW':>12} {'Total MB':>10} {'Priority':<10} {'Status'}")
            print(f"  {'─' * 80}")
            for s in sorted(self._streams.values(), key=lambda x: x.stream_id):
                print(f"  #{s.stream_id:<4} {s.source:>15} → {s.destination:<15} "
                      f"{_fmt_bw(s.avg_bandwidth):>12} "
                      f"{s._bytes_transferred:>9.1f}MB  "
                      f"{s.priority.name:<10} {s.status.value}")

        # Protocol breakdown by priority
        print(f"\n  Allocation by priority tier:")
        for prio in Priority:
            streams = [s for s in self._streams.values() if s.priority == prio]
            if streams:
                total_bw = sum(s.current_bandwidth for s in streams)
                print(f"    {prio.name:<10} — {len(streams):>2} stream(s)  "
                      f"current total = {_fmt_bw(total_bw)}")

        print(sep)


# ─────────────────────────────────────────────
# Demo / main
# ─────────────────────────────────────────────

def _section(title: str) -> None:
    print(f"\n{'═' * 62}")
    print(f"  {title}")
    print(f"{'═' * 62}")


def main() -> None:
    _section("BANDWIDTH LIMITER TOOL  —  Demo")

    # ──────────────────────────────────────────
    # SCENARIO 1: Basic fair-share with no rules
    # ──────────────────────────────────────────
    _section("SCENARIO 1 — Fair-Share (no explicit rules)")

    mgr1 = LimiterManager(link_capacity=100.0)   # 100 Mbps link

    streams_s1 = [
        NetworkStream("192.168.1.10", "10.0.0.1", requested_bandwidth=40.0, priority=Priority.HIGH),
        NetworkStream("192.168.1.20", "10.0.0.2", requested_bandwidth=40.0, priority=Priority.NORMAL),
        NetworkStream("192.168.1.30", "10.0.0.3", requested_bandwidth=40.0, priority=Priority.BULK),
    ]
    for s in streams_s1:
        mgr1.add_stream(s)

    mgr1.run_simulation(ticks=4, label="No rules — pure fair-share across 100 Mbps")
    mgr1.print_statistics()

    # ──────────────────────────────────────────
    # SCENARIO 2: Rules + priority enforcement
    # ──────────────────────────────────────────
    _section("SCENARIO 2 — Priority Rules + Burst Allowance")

    mgr2 = LimiterManager(link_capacity=100.0)

    # Rules
    rule_critical = BandwidthRule("CRIT_RULE",  max_bandwidth=50.0, burst_allowance=10.0,
                                  description="Critical VoIP / real-time")
    rule_standard = BandwidthRule("STD_RULE",   max_bandwidth=25.0,
                                  description="Standard web traffic")
    rule_bulk     = BandwidthRule("BULK_RULE",  max_bandwidth=10.0,
                                  priority_override=Priority.BULK,
                                  description="Background backup / P2P")

    for r in (rule_critical, rule_standard, rule_bulk):
        mgr2.add_rule(r)

    # Streams
    voip     = NetworkStream("10.0.1.1", "10.0.2.1", requested_bandwidth=45.0, priority=Priority.CRITICAL)
    web1     = NetworkStream("10.0.1.2", "10.0.2.2", requested_bandwidth=30.0, priority=Priority.HIGH)
    web2     = NetworkStream("10.0.1.3", "10.0.2.3", requested_bandwidth=30.0, priority=Priority.NORMAL)
    backup   = NetworkStream("10.0.1.4", "10.0.2.4", requested_bandwidth=50.0, priority=Priority.LOW)

    for s in (voip, web1, web2, backup):
        mgr2.add_stream(s)

    # Assign rules
    mgr2.apply_rule_to_stream("CRIT_RULE", voip.stream_id)
    mgr2.apply_rule_to_stream("STD_RULE",  web1.stream_id)
    mgr2.apply_rule_to_stream("STD_RULE",  web2.stream_id)
    mgr2.apply_rule_to_stream("BULK_RULE", backup.stream_id)

    # Run — tick 3 is a burst tick
    mgr2.run_simulation(ticks=6, burst_at={3},
                        label="Priority rules enforced — burst at tick 3")
    mgr2.print_statistics()

    # ──────────────────────────────────────────
    # SCENARIO 3: Stream lifecycle (pause / resume / close)
    # ──────────────────────────────────────────
    _section("SCENARIO 3 — Stream Lifecycle Events")

    mgr3 = LimiterManager(link_capacity=80.0)

    s_a = NetworkStream("172.16.0.1", "172.16.0.10", requested_bandwidth=20.0, priority=Priority.HIGH)
    s_b = NetworkStream("172.16.0.2", "172.16.0.11", requested_bandwidth=20.0, priority=Priority.NORMAL)
    s_c = NetworkStream("172.16.0.3", "172.16.0.12", requested_bandwidth=20.0, priority=Priority.BULK)
    s_d = NetworkStream("172.16.0.4", "172.16.0.13", requested_bandwidth=20.0, priority=Priority.NORMAL)

    for s in (s_a, s_b, s_c, s_d):
        mgr3.add_stream(s)

    rule_cap = BandwidthRule("CAP_15", max_bandwidth=15.0, description="Hard cap 15 Mbps")
    mgr3.add_rule(rule_cap)
    mgr3.apply_rule_to_stream("CAP_15", s_c.stream_id)

    mgr3.run_simulation(ticks=2, label="Initial run — all 4 streams active")

    print("\n  ── Pausing stream B and closing stream C ──")
    mgr3.pause_stream(s_b.stream_id)
    mgr3.close_stream(s_c.stream_id)

    mgr3.run_simulation(ticks=2, label="After pause/close — bandwidth redistributed")

    print("\n  ── Resuming stream B ──")
    mgr3.resume_stream(s_b.stream_id)

    mgr3.run_simulation(ticks=2, label="After resume — stream B back online")

    mgr3.print_statistics()

    # ──────────────────────────────────────────
    # SCENARIO 4: Oversubscribed link
    # ──────────────────────────────────────────
    _section("SCENARIO 4 — Oversubscribed Link (500 Mbps requested / 100 Mbps available)")

    mgr4 = LimiterManager(link_capacity=100.0)

    big_streams = [
        NetworkStream("10.1.0.1", "10.2.0.1", requested_bandwidth=100.0, priority=Priority.CRITICAL),
        NetworkStream("10.1.0.2", "10.2.0.2", requested_bandwidth=100.0, priority=Priority.HIGH),
        NetworkStream("10.1.0.3", "10.2.0.3", requested_bandwidth=100.0, priority=Priority.NORMAL),
        NetworkStream("10.1.0.4", "10.2.0.4", requested_bandwidth=100.0, priority=Priority.LOW),
        NetworkStream("10.1.0.5", "10.2.0.5", requested_bandwidth=100.0, priority=Priority.BULK),
    ]
    for s in big_streams:
        mgr4.add_stream(s)

    # Give CRITICAL a guaranteed floor
    rule_guaranteed = BandwidthRule("GUARANTEED", max_bandwidth=40.0,
                                    burst_allowance=5.0,
                                    description="Guaranteed minimum for critical")
    mgr4.add_rule(rule_guaranteed)
    mgr4.apply_rule_to_stream("GUARANTEED", big_streams[0].stream_id)

    mgr4.run_simulation(ticks=5, burst_at={2, 4},
                        label="5 streams each wanting 100 Mbps on a 100 Mbps link")
    mgr4.print_statistics()

    _section("All scenarios complete.")


if __name__ == "__main__":
    main()