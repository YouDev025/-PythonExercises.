"""
System Monitoring Tool
======================
Monitors CPU, memory, disk, and network resources in real time.
Built with Python OOP: encapsulation, single-responsibility classes,
clean public APIs, and immutable metric snapshots.

Requirements:
    pip install psutil
"""

from __future__ import annotations

import os
import sys
import time
import threading
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    import psutil
except ImportError:
    sys.exit("ERROR: psutil is required.  Run:  pip install psutil")


# ─────────────────────────────────────────────────────────────────────────────
#  SystemMetrics  – immutable snapshot of one collection cycle
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NetworkStats:
    bytes_sent:     int
    bytes_recv:     int
    packets_sent:   int
    packets_recv:   int
    # Derived rates (bytes/s) – populated after first snapshot
    send_rate_bps:  float = 0.0
    recv_rate_bps:  float = 0.0


@dataclass(frozen=True)
class DiskStats:
    path:        str
    total_gb:    float
    used_gb:     float
    free_gb:     float
    percent:     float
    read_bps:    float = 0.0   # bytes/s since last snapshot
    write_bps:   float = 0.0


@dataclass(frozen=True)
class SystemMetrics:
    """One point-in-time snapshot of all monitored resources."""
    timestamp:      datetime
    cpu_percent:    float                   # overall CPU %
    cpu_per_core:   tuple[float, ...]       # per-core %
    mem_total_gb:   float
    mem_used_gb:    float
    mem_available_gb: float
    mem_percent:    float
    swap_total_gb:  float
    swap_used_gb:   float
    swap_percent:   float
    disks:          tuple[DiskStats, ...]
    network:        NetworkStats
    process_count:  int
    load_avg:       tuple[float, float, float]  # 1 / 5 / 15 min

    def age_seconds(self) -> float:
        return (datetime.now() - self.timestamp).total_seconds()

    def __str__(self) -> str:
        return (
            f"[{self.timestamp.strftime('%H:%M:%S')}] "
            f"CPU {self.cpu_percent:5.1f}%  "
            f"MEM {self.mem_percent:5.1f}%  "
            f"DISK {self.disks[0].percent:5.1f}% (root)"
            if self.disks else
            f"[{self.timestamp.strftime('%H:%M:%S')}] "
            f"CPU {self.cpu_percent:5.1f}%  "
            f"MEM {self.mem_percent:5.1f}%"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  SystemMonitor  – all psutil data-collection logic
# ─────────────────────────────────────────────────────────────────────────────

class SystemMonitor:
    """
    Collects system resource data via psutil.
    Keeps the previous I/O counters to compute delta rates.
    All state is private; only `collect()` is public API.
    """

    def __init__(self) -> None:
        self._prev_net_io:  Optional[psutil._common.snetio]  = None
        self._prev_disk_io: Optional[dict]                   = None
        self._prev_time:    float                            = time.monotonic()
        # Warm-up: seed interval counters without blocking
        self._prev_net_io  = psutil.net_io_counters()
        self._prev_disk_io = self._disk_io_by_path()

    # ── public API ────────────────────────────────────────────────────

    def collect(self, cpu_interval: float = 0.5) -> SystemMetrics:
        """
        Gather a full system snapshot.
        `cpu_interval` is the blocking interval for cpu_percent accuracy.
        Pass 0 for non-blocking (less accurate but instant).
        """
        now        = datetime.now()
        elapsed    = max(time.monotonic() - self._prev_time, 0.001)

        cpu_pct    = self._get_cpu_overall(cpu_interval)
        cpu_cores  = self._get_cpu_per_core()
        mem        = self._get_memory()
        swap       = self._get_swap()
        disks      = self._get_disks(elapsed)
        network    = self._get_network(elapsed)
        processes  = len(psutil.pids())
        load       = self._get_load_avg()

        self._prev_time = time.monotonic()

        return SystemMetrics(
            timestamp        = now,
            cpu_percent      = cpu_pct,
            cpu_per_core     = cpu_cores,
            mem_total_gb     = mem["total"],
            mem_used_gb      = mem["used"],
            mem_available_gb = mem["available"],
            mem_percent      = mem["percent"],
            swap_total_gb    = swap["total"],
            swap_used_gb     = swap["used"],
            swap_percent     = swap["percent"],
            disks            = disks,
            network          = network,
            process_count    = processes,
            load_avg         = load,
        )

    # ── private helpers ───────────────────────────────────────────────

    @staticmethod
    def _get_cpu_overall(interval: float) -> float:
        try:
            return psutil.cpu_percent(interval=interval if interval > 0 else None)
        except Exception:
            return 0.0

    @staticmethod
    def _get_cpu_per_core() -> tuple[float, ...]:
        try:
            return tuple(psutil.cpu_percent(percpu=True))
        except Exception:
            return ()

    @staticmethod
    def _to_gb(val: int) -> float:
        return round(val / (1024 ** 3), 2)

    def _get_memory(self) -> dict:
        try:
            vm = psutil.virtual_memory()
            return {
                "total":     self._to_gb(vm.total),
                "used":      self._to_gb(vm.used),
                "available": self._to_gb(vm.available),
                "percent":   vm.percent,
            }
        except Exception:
            return {"total": 0, "used": 0, "available": 0, "percent": 0}

    def _get_swap(self) -> dict:
        try:
            sw = psutil.swap_memory()
            return {
                "total":   self._to_gb(sw.total),
                "used":    self._to_gb(sw.used),
                "percent": sw.percent,
            }
        except Exception:
            return {"total": 0, "used": 0, "percent": 0}

    @staticmethod
    def _disk_io_by_path() -> dict:
        """Return disk I/O counters keyed by device path."""
        try:
            return {k: v for k, v in psutil.disk_io_counters(perdisk=True).items()}
        except Exception:
            return {}

    def _get_disks(self, elapsed: float) -> tuple[DiskStats, ...]:
        disks: list[DiskStats] = []
        current_io = self._disk_io_by_path()

        try:
            partitions = psutil.disk_partitions(all=False)
        except Exception:
            partitions = []

        seen_devices: set[str] = set()
        for part in partitions:
            if part.device in seen_devices:
                continue
            seen_devices.add(part.device)
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue
            except Exception:
                continue

            # Compute read/write rates
            device_key = os.path.basename(part.device)
            read_bps  = 0.0
            write_bps = 0.0
            if (self._prev_disk_io and device_key in current_io
                    and device_key in self._prev_disk_io):
                prev = self._prev_disk_io[device_key]
                curr = current_io[device_key]
                read_bps  = max(curr.read_bytes  - prev.read_bytes,  0) / elapsed
                write_bps = max(curr.write_bytes - prev.write_bytes, 0) / elapsed

            disks.append(DiskStats(
                path      = part.mountpoint,
                total_gb  = self._to_gb(usage.total),
                used_gb   = self._to_gb(usage.used),
                free_gb   = self._to_gb(usage.free),
                percent   = usage.percent,
                read_bps  = read_bps,
                write_bps = write_bps,
            ))

        self._prev_disk_io = current_io
        return tuple(disks)

    def _get_network(self, elapsed: float) -> NetworkStats:
        try:
            curr = psutil.net_io_counters()
            send_rate = recv_rate = 0.0
            if self._prev_net_io:
                send_rate = max(curr.bytes_sent - self._prev_net_io.bytes_sent, 0) / elapsed
                recv_rate = max(curr.bytes_recv - self._prev_net_io.bytes_recv, 0) / elapsed
            self._prev_net_io = curr
            return NetworkStats(
                bytes_sent   = curr.bytes_sent,
                bytes_recv   = curr.bytes_recv,
                packets_sent = curr.packets_sent,
                packets_recv = curr.packets_recv,
                send_rate_bps = send_rate,
                recv_rate_bps = recv_rate,
            )
        except Exception:
            return NetworkStats(0, 0, 0, 0)

    @staticmethod
    def _get_load_avg() -> tuple[float, float, float]:
        try:
            la = psutil.getloadavg()
            return (round(la[0], 2), round(la[1], 2), round(la[2], 2))
        except AttributeError:
            # Windows does not support getloadavg
            return (0.0, 0.0, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
#  MonitoringManager  – orchestration, history, background polling
# ─────────────────────────────────────────────────────────────────────────────

class MonitoringManager:
    """
    Manages the polling loop (background thread), stores history,
    and exposes the public CLI interface.
    """

    _MAX_HISTORY = 1000   # cap stored snapshots

    def __init__(self, poll_interval: float = 2.0) -> None:
        self._monitor:       SystemMonitor      = SystemMonitor()
        self._history:       list[SystemMetrics] = []
        self._poll_interval: float              = max(poll_interval, 0.5)
        self._running:       bool               = False
        self._thread:        Optional[threading.Thread] = None
        self._lock:          threading.Lock     = threading.Lock()

    # ── start / stop ──────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            print("  ⚠  Monitoring is already running.")
            return
        self._running = True
        self._thread  = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print(f"  ✓  Monitoring started (interval: {self._poll_interval}s).")

    def stop(self) -> None:
        if not self._running:
            print("  ⚠  Monitoring is not running.")
            return
        self._running = False
        print("  ✓  Monitoring stopped.")

    def is_running(self) -> bool:
        return self._running

    # ── data access ───────────────────────────────────────────────────

    def latest(self) -> Optional[SystemMetrics]:
        with self._lock:
            return self._history[-1] if self._history else None

    def history(self) -> list[SystemMetrics]:
        with self._lock:
            return list(self._history)

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()
        print("  ✓  History cleared.")

    def collect_once(self) -> SystemMetrics:
        """Collect a single snapshot synchronously (no background thread needed)."""
        m = self._monitor.collect(cpu_interval=0.5)
        with self._lock:
            self._history.append(m)
            if len(self._history) > self._MAX_HISTORY:
                self._history.pop(0)
        return m

    def summary_stats(self) -> Optional[dict]:
        """Aggregate statistics over the entire session history."""
        hist = self.history()
        if len(hist) < 2:
            return None
        cpu_vals  = [m.cpu_percent  for m in hist]
        mem_vals  = [m.mem_percent  for m in hist]
        return {
            "samples":      len(hist),
            "duration_min": round((hist[-1].timestamp - hist[0].timestamp).total_seconds() / 60, 2),
            "cpu_avg":      round(statistics.mean(cpu_vals), 2),
            "cpu_max":      round(max(cpu_vals), 2),
            "cpu_min":      round(min(cpu_vals), 2),
            "mem_avg":      round(statistics.mean(mem_vals), 2),
            "mem_max":      round(max(mem_vals), 2),
            "mem_min":      round(min(mem_vals), 2),
        }

    # ── background loop ───────────────────────────────────────────────

    def _poll_loop(self) -> None:
        while self._running:
            try:
                m = self._monitor.collect(cpu_interval=0)
                with self._lock:
                    self._history.append(m)
                    if len(self._history) > self._MAX_HISTORY:
                        self._history.pop(0)
            except Exception:
                pass
            time.sleep(self._poll_interval)


# ─────────────────────────────────────────────────────────────────────────────
#  Display helpers
# ─────────────────────────────────────────────────────────────────────────────

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_CYAN   = "\033[96m"
_BLUE   = "\033[94m"
_DIM    = "\033[2m"


def _colour_pct(pct: float) -> str:
    if pct < 60:
        colour = _GREEN
    elif pct < 85:
        colour = _YELLOW
    else:
        colour = _RED
    return f"{colour}{pct:5.1f}%{_RESET}"


def _bar(pct: float, width: int = 20) -> str:
    filled = int(round(pct / 100 * width))
    empty  = width - filled
    if pct < 60:
        colour = _GREEN
    elif pct < 85:
        colour = _YELLOW
    else:
        colour = _RED
    return f"{colour}{'█' * filled}{'░' * empty}{_RESET}"


def _fmt_bytes(b: float, suffix: str = "B") -> str:
    for unit in ("", "K", "M", "G", "T"):
        if abs(b) < 1024.0:
            return f"{b:6.1f} {unit}{suffix}"
        b /= 1024.0
    return f"{b:.1f} P{suffix}"


def _fmt_rate(bps: float) -> str:
    return _fmt_bytes(bps, "B/s")


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _hr(char: str = "─", width: int = 62) -> str:
    return char * width


# ─────────────────────────────────────────────────────────────────────────────
#  Display functions
# ─────────────────────────────────────────────────────────────────────────────

def display_snapshot(m: SystemMetrics, clear: bool = False) -> None:
    if clear:
        _clear()

    lines: list[str] = []
    W = 62
    lines.append(f"\n{_BOLD}{'─'*W}{_RESET}")
    lines.append(
        f"{_BOLD}  System Snapshot  {_DIM}{m.timestamp.strftime('%Y-%m-%d %H:%M:%S')}{_RESET}"
        f"   {_DIM}Processes: {m.process_count}{_RESET}"
    )
    lines.append(f"{_BOLD}{'─'*W}{_RESET}")

    # ── CPU ──────────────────────────────────────────────────────────
    lines.append(f"\n  {_CYAN}{_BOLD}CPU{_RESET}")
    lines.append(f"    Overall  {_bar(m.cpu_percent)}  {_colour_pct(m.cpu_percent)}")
    if m.cpu_per_core:
        for i, pct in enumerate(m.cpu_per_core):
            lines.append(f"    Core {i:<3}  {_bar(pct, 16)}  {_colour_pct(pct)}")
    lines.append(
        f"    Load avg (1/5/15 min): "
        f"{m.load_avg[0]} / {m.load_avg[1]} / {m.load_avg[2]}"
    )

    # ── Memory ───────────────────────────────────────────────────────
    lines.append(f"\n  {_CYAN}{_BOLD}Memory{_RESET}")
    lines.append(
        f"    RAM      {_bar(m.mem_percent)}  {_colour_pct(m.mem_percent)}"
        f"   {m.mem_used_gb:.2f} / {m.mem_total_gb:.2f} GB"
    )
    lines.append(
        f"    Avail    {m.mem_available_gb:.2f} GB"
    )
    if m.swap_total_gb > 0:
        lines.append(
            f"    Swap     {_bar(m.swap_percent)}  {_colour_pct(m.swap_percent)}"
            f"   {m.swap_used_gb:.2f} / {m.swap_total_gb:.2f} GB"
        )

    # ── Disk ─────────────────────────────────────────────────────────
    lines.append(f"\n  {_CYAN}{_BOLD}Disk{_RESET}")
    for d in m.disks:
        lines.append(
            f"    {d.path:<12}  {_bar(d.percent)}  {_colour_pct(d.percent)}"
            f"   {d.used_gb:.1f} / {d.total_gb:.1f} GB  free: {d.free_gb:.1f} GB"
        )
        if d.read_bps > 0 or d.write_bps > 0:
            lines.append(
                f"    {'':12}  Read: {_fmt_rate(d.read_bps):<14}"
                f"  Write: {_fmt_rate(d.write_bps)}"
            )

    # ── Network ──────────────────────────────────────────────────────
    n = m.network
    lines.append(f"\n  {_CYAN}{_BOLD}Network{_RESET}")
    lines.append(
        f"    ↑ Sent     {_fmt_bytes(n.bytes_sent):<14}"
        f"  Rate: {_fmt_rate(n.send_rate_bps)}"
    )
    lines.append(
        f"    ↓ Received {_fmt_bytes(n.bytes_recv):<14}"
        f"  Rate: {_fmt_rate(n.recv_rate_bps)}"
    )
    lines.append(
        f"    Packets   sent {n.packets_sent:,}  /  recv {n.packets_recv:,}"
    )

    lines.append(f"\n{_BOLD}{'─'*W}{_RESET}\n")
    print("\n".join(lines))


def display_history_table(history: list[SystemMetrics]) -> None:
    if not history:
        print("\n  No history recorded yet.\n")
        return

    W = 68
    print(f"\n{_BOLD}{'─'*W}{_RESET}")
    print(f"{_BOLD}  Metric History  ({len(history)} samples){_RESET}")
    print(f"{_BOLD}{'─'*W}{_RESET}")
    print(f"  {'Time':<10}  {'CPU%':>6}  {'MEM%':>6}  {'Disk%':>6}  {'Net↑ (KB/s)':>12}  {'Net↓ (KB/s)':>12}")
    print(f"  {'─'*8}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*12}  {'─'*12}")

    # Show last 30 entries
    for m in history[-30:]:
        disk_pct = m.disks[0].percent if m.disks else 0.0
        up_kbps  = m.network.send_rate_bps / 1024
        dn_kbps  = m.network.recv_rate_bps / 1024
        ts       = m.timestamp.strftime("%H:%M:%S")
        print(
            f"  {ts:<10}"
            f"  {_colour_pct(m.cpu_percent)}"
            f"  {_colour_pct(m.mem_percent)}"
            f"  {_colour_pct(disk_pct)}"
            f"  {up_kbps:>12.1f}"
            f"  {dn_kbps:>12.1f}"
        )

    if len(history) > 30:
        print(f"  {_DIM}… {len(history) - 30} earlier entries omitted{_RESET}")
    print(f"{_BOLD}{'─'*W}{_RESET}\n")


def display_summary(stats: Optional[dict]) -> None:
    if not stats:
        print("\n  Not enough data for summary (need ≥ 2 samples).\n")
        return
    W = 52
    print(f"\n{_BOLD}{'─'*W}{_RESET}")
    print(f"{_BOLD}  Session Summary{_RESET}")
    print(f"{_BOLD}{'─'*W}{_RESET}")
    print(f"  Samples collected : {stats['samples']}")
    print(f"  Duration          : {stats['duration_min']} minutes")
    print(f"\n  CPU Usage  — avg {stats['cpu_avg']:5.1f}%  "
          f"min {stats['cpu_min']:5.1f}%  max {stats['cpu_max']:5.1f}%")
    print(f"  MEM Usage  — avg {stats['mem_avg']:5.1f}%  "
          f"min {stats['mem_min']:5.1f}%  max {stats['mem_max']:5.1f}%")
    print(f"{_BOLD}{'─'*W}{_RESET}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────

BANNER = f"""
{_BOLD}╔══════════════════════════════════════════════════════════════╗
║            System Monitoring Tool  v1.0                      ║
║    Real-time CPU · Memory · Disk · Network monitoring        ║
╚══════════════════════════════════════════════════════════════╝{_RESET}"""

MENU = f"""
  {_BOLD}[1]{_RESET} Take a single snapshot
  {_BOLD}[2]{_RESET} Start continuous monitoring (background)
  {_BOLD}[3]{_RESET} Stop continuous monitoring
  {_BOLD}[4]{_RESET} View latest snapshot
  {_BOLD}[5]{_RESET} View metric history table
  {_BOLD}[6]{_RESET} View session summary / statistics
  {_BOLD}[7]{_RESET} Live dashboard (auto-refresh, press Enter to stop)
  {_BOLD}[8]{_RESET} Clear history
  {_BOLD}[Q]{_RESET} Quit
"""

HELP_TEXT = f"""
  {_BOLD}── What is monitored ────────────────────────────────────────{_RESET}
  CPU      overall % + per-core + 1/5/15-min load averages
  Memory   RAM used/available + swap usage
  Disk     used/free/total per partition + R/W byte rates
  Network  total bytes sent/received + live KB/s rates
  Misc     process count, collection timestamp

  {_BOLD}── Colour guide ─────────────────────────────────────────────{_RESET}
  {_GREEN}Green{_RESET}   < 60%   normal usage
  {_YELLOW}Yellow{_RESET}  60–85%  elevated usage
  {_RED}Red{_RESET}     > 85%   high / critical usage
"""


def _get_choice(prompt: str, valid: set[str]) -> str:
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid:
            return choice
        print(f"  ⚠  Please choose one of: {', '.join(sorted(valid))}")


def _get_float(prompt: str, default: float, lo: float, hi: float) -> float:
    raw = input(prompt).strip()
    if not raw:
        return default
    try:
        val = float(raw)
        if lo <= val <= hi:
            return val
    except ValueError:
        pass
    print(f"  ⚠  Using default {default}.")
    return default


def action_live_dashboard(mgr: MonitoringManager) -> None:
    print("\n  Live dashboard — press Enter at any time to return to menu.\n")
    stop_event = threading.Event()

    def _listener():
        input()
        stop_event.set()

    t = threading.Thread(target=_listener, daemon=True)
    t.start()

    while not stop_event.is_set():
        m = mgr.collect_once()
        display_snapshot(m, clear=True)
        print(f"  {_DIM}Press Enter to stop…{_RESET}")
        stop_event.wait(timeout=2.0)


def main() -> None:
    print(BANNER)

    interval = _get_float(
        f"  Poll interval in seconds [{_BOLD}2.0{_RESET}]: ",
        default=2.0, lo=0.5, hi=60.0,
    )
    mgr = MonitoringManager(poll_interval=interval)

    # Collect an initial snapshot on startup
    print("\n  Collecting initial snapshot…")
    mgr.collect_once()

    while True:
        status = f"{_GREEN}● running{_RESET}" if mgr.is_running() else f"{_DIM}○ idle{_RESET}"
        print(f"\n{MENU}  Status: {status}")
        choice = _get_choice("  Your choice: ", {"1","2","3","4","5","6","7","8","h","q"})

        if choice == "1":
            print("\n  Collecting snapshot…")
            m = mgr.collect_once()
            display_snapshot(m)

        elif choice == "2":
            mgr.start()

        elif choice == "3":
            mgr.stop()

        elif choice == "4":
            m = mgr.latest()
            if m:
                display_snapshot(m)
            else:
                print("\n  No snapshot available yet — choose [1] first.\n")

        elif choice == "5":
            display_history_table(mgr.history())

        elif choice == "6":
            display_summary(mgr.summary_stats())

        elif choice == "7":
            action_live_dashboard(mgr)

        elif choice == "8":
            mgr.clear_history()

        elif choice == "h":
            print(HELP_TEXT)

        elif choice == "q":
            if mgr.is_running():
                mgr.stop()
            print(f"\n  {_BOLD}Goodbye!{_RESET} 👋\n")
            break


if __name__ == "__main__":
    main()