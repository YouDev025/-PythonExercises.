#!/usr/bin/env python3
"""
process_manager.py
A console-based Task Manager simulation using OOP and psutil.

Classes
-------
Process        – Snapshot of a single process's metrics.
SystemStats    – Snapshot of overall CPU / memory / disk / network usage.
ProcessMonitor – Thin wrapper around psutil for live data retrieval.
ProcessManager – Business logic: list, search, sort, kill, watch.
UI             – Menu-driven console interface.
"""

import os
import sys
import time
import signal
import shutil
from datetime import datetime, timedelta
from typing import Optional

try:
    import psutil
except ImportError:
    sys.exit(
        "[error] psutil is required.  Install it with:  pip install psutil"
    )


# ─────────────────────────────────────────────────────────────────
#  ANSI helpers
# ─────────────────────────────────────────────────────────────────

class _Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"
    BG_DARK = "\033[48;5;236m"

C = _Color()


def _colored(text: str, *codes: str) -> str:
    return "".join(codes) + str(text) + C.RESET


def _bar(value: float, width: int = 20, color: str = C.GREEN) -> str:
    """Return a filled ASCII progress bar."""
    filled = int(round(value / 100 * width))
    filled = max(0, min(filled, width))
    bar    = "█" * filled + "░" * (width - filled)
    if value >= 80:
        color = C.RED
    elif value >= 50:
        color = C.YELLOW
    return f"[{color}{bar}{C.RESET}] {value:5.1f}%"


def _fmt_bytes(n: int) -> str:
    """Human-readable byte string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _fmt_uptime(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    h, rem = divmod(td.seconds, 3600)
    m, s   = divmod(rem, 60)
    days   = td.days
    parts  = []
    if days:  parts.append(f"{days}d")
    if h:     parts.append(f"{h}h")
    parts.append(f"{m:02d}m{s:02d}s")
    return " ".join(parts)


# ─────────────────────────────────────────────────────────────────
#  Process
# ─────────────────────────────────────────────────────────────────

class Process:
    """
    Immutable snapshot of one OS process at the moment of sampling.

    Attributes
    ----------
    process_id   : OS PID.
    name         : Executable name.
    cpu_usage    : CPU % (sampled over a short interval by psutil).
    memory_usage : RSS memory in bytes.
    memory_pct   : RSS as a percentage of total RAM.
    status       : 'running', 'sleeping', 'stopped', 'zombie', etc.
    username     : Owner of the process.
    num_threads  : Number of threads.
    create_time  : Unix timestamp of process creation.
    cmdline      : Full command-line string (may be empty for kernel threads).
    """

    __slots__ = (
        "process_id", "name", "cpu_usage", "memory_usage", "memory_pct",
        "status", "username", "num_threads", "create_time", "cmdline",
    )

    def __init__(
        self,
        process_id:   int,
        name:         str,
        cpu_usage:    float,
        memory_usage: int,
        memory_pct:   float,
        status:       str,
        username:     str,
        num_threads:  int,
        create_time:  float,
        cmdline:      str,
    ) -> None:
        self.process_id   = process_id
        self.name         = name
        self.cpu_usage    = cpu_usage
        self.memory_usage = memory_usage
        self.memory_pct   = memory_pct
        self.status       = status
        self.username     = username
        self.num_threads  = num_threads
        self.create_time  = create_time
        self.cmdline      = cmdline

    # ── helpers ─────────────────────────────────

    @property
    def uptime(self) -> str:
        return _fmt_uptime(time.time() - self.create_time)

    @property
    def status_colored(self) -> str:
        mapping = {
            "running":  C.GREEN,
            "sleeping": C.CYAN,
            "stopped":  C.YELLOW,
            "zombie":   C.RED,
            "dead":     C.RED,
            "idle":     C.BLUE,
            "disk-sleep": C.MAGENTA,
        }
        color = mapping.get(self.status, C.WHITE)
        return _colored(f"{self.status:<10}", color)

    def __repr__(self) -> str:
        return (
            f"Process(pid={self.process_id}, name={self.name!r}, "
            f"cpu={self.cpu_usage:.1f}%, mem={_fmt_bytes(self.memory_usage)}, "
            f"status={self.status!r})"
        )


# ─────────────────────────────────────────────────────────────────
#  SystemStats
# ─────────────────────────────────────────────────────────────────

class SystemStats:
    """
    Snapshot of system-wide resource usage.

    Attributes
    ----------
    cpu_pct         : Overall CPU utilisation (%).
    cpu_per_core    : Per-core CPU utilisation list.
    cpu_freq_mhz    : Current CPU frequency in MHz.
    cpu_count       : Logical CPU count.
    mem_total       : Total RAM in bytes.
    mem_used        : Used RAM in bytes.
    mem_pct         : RAM utilisation (%).
    swap_total      : Total swap in bytes.
    swap_used       : Used swap in bytes.
    swap_pct        : Swap utilisation (%).
    disk_total      : Root-partition total bytes.
    disk_used       : Root-partition used bytes.
    disk_pct        : Root-partition utilisation (%).
    net_bytes_sent  : Cumulative bytes sent.
    net_bytes_recv  : Cumulative bytes received.
    boot_time       : Unix timestamp of last boot.
    process_count   : Total number of running processes.
    """

    def __init__(self) -> None:
        # CPU
        self.cpu_pct:      float      = psutil.cpu_percent(interval=0.3)
        self.cpu_per_core: list[float] = psutil.cpu_percent(interval=0, percpu=True)
        freq = psutil.cpu_freq()
        self.cpu_freq_mhz: float      = freq.current if freq else 0.0
        self.cpu_count:    int        = psutil.cpu_count(logical=True)

        # Memory
        vm = psutil.virtual_memory()
        self.mem_total: int   = vm.total
        self.mem_used:  int   = vm.used
        self.mem_pct:   float = vm.percent

        sw = psutil.swap_memory()
        self.swap_total: int   = sw.total
        self.swap_used:  int   = sw.used
        self.swap_pct:   float = sw.percent

        # Disk (root / first partition)
        try:
            disk = psutil.disk_usage("/")
            self.disk_total: int   = disk.total
            self.disk_used:  int   = disk.used
            self.disk_pct:   float = disk.percent
        except Exception:
            self.disk_total = self.disk_used = 0
            self.disk_pct   = 0.0

        # Network
        net = psutil.net_io_counters()
        self.net_bytes_sent: int = net.bytes_sent
        self.net_bytes_recv: int = net.bytes_recv

        # Misc
        self.boot_time:      float = psutil.boot_time()
        self.process_count:  int   = len(psutil.pids())

    @property
    def uptime(self) -> str:
        return _fmt_uptime(time.time() - self.boot_time)


# ─────────────────────────────────────────────────────────────────
#  ProcessMonitor
# ─────────────────────────────────────────────────────────────────

class ProcessMonitor:
    """
    Retrieves live process data from the OS via psutil.

    This class is a thin adapter: it knows about psutil but the rest
    of the application never imports psutil directly.
    """

    # Fields we always try to read in one go (avoids repeated syscalls)
    _ATTRS = [
        "pid", "name", "cpu_percent", "memory_info", "memory_percent",
        "status", "username", "num_threads", "create_time", "cmdline",
    ]

    def snapshot(self) -> list[Process]:
        """Return a fresh list of :class:`Process` snapshots."""
        processes: list[Process] = []

        for proc in psutil.process_iter(self._ATTRS):
            try:
                info = proc.info                           # dict from attrs
                mem_info = info.get("memory_info") or None
                mem_rss  = mem_info.rss if mem_info else 0

                cmd = info.get("cmdline") or []
                cmdline = " ".join(cmd) if cmd else info.get("name", "")

                processes.append(Process(
                    process_id   = info["pid"],
                    name         = info.get("name") or "?",
                    cpu_usage    = info.get("cpu_percent") or 0.0,
                    memory_usage = mem_rss,
                    memory_pct   = info.get("memory_percent") or 0.0,
                    status       = info.get("status") or "unknown",
                    username     = info.get("username") or "?",
                    num_threads  = info.get("num_threads") or 0,
                    create_time  = info.get("create_time") or time.time(),
                    cmdline      = cmdline,
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied,
                    psutil.ZombieProcess):
                continue

        return processes

    def get_by_pid(self, pid: int) -> Optional[Process]:
        """Return a single :class:`Process` by PID, or None."""
        try:
            p    = psutil.Process(pid)
            info = p.as_dict(attrs=self._ATTRS)
            mem_info = info.get("memory_info") or None
            mem_rss  = mem_info.rss if mem_info else 0
            cmd  = info.get("cmdline") or []
            return Process(
                process_id   = info["pid"],
                name         = info.get("name") or "?",
                cpu_usage    = info.get("cpu_percent") or 0.0,
                memory_usage = mem_rss,
                memory_pct   = info.get("memory_percent") or 0.0,
                status       = info.get("status") or "unknown",
                username     = info.get("username") or "?",
                num_threads  = info.get("num_threads") or 0,
                create_time  = info.get("create_time") or time.time(),
                cmdline      = " ".join(cmd) if cmd else (info.get("name") or ""),
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    @staticmethod
    def kill(pid: int, force: bool = False) -> str:
        """
        Terminate a process.

        Parameters
        ----------
        pid   : Target PID.
        force : If True, send SIGKILL; otherwise SIGTERM.

        Returns a human-readable result string.
        """
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            if force:
                proc.kill()
                return f"Process {pid} ({name}) killed (SIGKILL)."
            else:
                proc.terminate()
                return f"Process {pid} ({name}) terminated (SIGTERM)."
        except psutil.NoSuchProcess:
            return f"PID {pid} does not exist."
        except psutil.AccessDenied:
            return f"PID {pid}: access denied (try running as root/admin)."


# ─────────────────────────────────────────────────────────────────
#  ProcessManager
# ─────────────────────────────────────────────────────────────────

_SORT_KEYS = {
    "pid":    lambda p: p.process_id,
    "name":   lambda p: p.name.lower(),
    "cpu":    lambda p: p.cpu_usage,
    "mem":    lambda p: p.memory_usage,
    "status": lambda p: p.status,
}

class ProcessManager:
    """
    High-level process management: list, search, sort, terminate, watch.

    Uses :class:`ProcessMonitor` for raw data and caches the last snapshot
    to avoid redundant OS calls within the same menu loop.
    """

    def __init__(self) -> None:
        self._monitor  = ProcessMonitor()
        self._cache:   list[Process] = []
        self._fetched: float = 0.0

    # ── snapshot management ─────────────────────

    def refresh(self) -> list[Process]:
        """Force a fresh snapshot from the OS."""
        self._cache   = self._monitor.snapshot()
        self._fetched = time.time()
        return self._cache

    def processes(self, max_age: float = 5.0) -> list[Process]:
        """Return cached snapshot, refreshing if older than *max_age* seconds."""
        if time.time() - self._fetched > max_age:
            self.refresh()
        return self._cache

    # ── listing ─────────────────────────────────

    def list_processes(
        self,
        sort_by:  str  = "cpu",
        reverse:  bool = True,
        limit:    int  = 50,
        status_filter: Optional[str] = None,
    ) -> list[Process]:
        procs = self.processes()
        if status_filter:
            procs = [p for p in procs if p.status == status_filter]
        key = _SORT_KEYS.get(sort_by, _SORT_KEYS["cpu"])
        procs = sorted(procs, key=key, reverse=reverse)
        return procs[:limit]

    # ── search ───────────────────────────────────

    def search_by_name(self, query: str) -> list[Process]:
        q = query.lower()
        return [p for p in self.processes() if q in p.name.lower()]

    def search_by_pid(self, pid: int) -> Optional[Process]:
        for p in self.processes():
            if p.process_id == pid:
                return p
        return None

    # ── termination ─────────────────────────────

    def terminate(self, pid: int, force: bool = False) -> str:
        return self._monitor.kill(pid, force=force)

    # ── statistics ──────────────────────────────

    def top_cpu(self, n: int = 5) -> list[Process]:
        return sorted(self.processes(), key=lambda p: p.cpu_usage, reverse=True)[:n]

    def top_mem(self, n: int = 5) -> list[Process]:
        return sorted(self.processes(), key=lambda p: p.memory_usage, reverse=True)[:n]

    def count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for p in self.processes():
            counts[p.status] = counts.get(p.status, 0) + 1
        return counts

    # ── system stats ────────────────────────────

    @staticmethod
    def system_stats() -> SystemStats:
        return SystemStats()


# ─────────────────────────────────────────────────────────────────
#  UI  (console interface)
# ─────────────────────────────────────────────────────────────────

class UI:
    """
    Menu-driven console interface for :class:`ProcessManager`.

    Menus
    -----
    1. List processes          (sortable, filterable, paginated)
    2. Search process          (by name or PID)
    3. Process details         (full info for one PID)
    4. Terminate process       (SIGTERM or SIGKILL)
    5. System statistics       (CPU, RAM, Disk, Network)
    6. Live monitor            (auto-refresh top-N table)
    7. Resource summary        (top CPU / top MEM leaders)
    0. Exit
    """

    _TERM_WIDTH = shutil.get_terminal_size((100, 30)).columns

    def __init__(self) -> None:
        self._mgr = ProcessManager()

    # ── REPL ────────────────────────────────────

    def run(self) -> None:
        self._banner()
        while True:
            self._main_menu()
            choice = self._prompt_choice(
                "Choose an option", list("1234567890") + [""]
            )
            if choice in ("0", "q", ""):
                self._exit()
                break
            dispatch = {
                "1": self._menu_list,
                "2": self._menu_search,
                "3": self._menu_details,
                "4": self._menu_terminate,
                "5": self._menu_system_stats,
                "6": self._menu_live_monitor,
                "7": self._menu_resource_summary,
            }
            handler = dispatch.get(choice)
            if handler:
                handler()
            else:
                self._warn("Invalid option.")

    # ── menus ────────────────────────────────────

    def _menu_list(self) -> None:
        self._section("List Processes")
        sort_by = self._prompt_select(
            "Sort by", ["cpu", "mem", "pid", "name", "status"], default="cpu"
        )
        limit_s = self._prompt_input("Max rows to show [30]", default="30")
        limit   = int(limit_s) if limit_s.isdigit() else 30
        status  = self._prompt_input(
            "Filter by status (running/sleeping/zombie/… or blank for all)", default=""
        )

        self._mgr.refresh()
        procs = self._mgr.list_processes(
            sort_by=sort_by,
            limit=limit,
            status_filter=status or None,
        )
        self._render_process_table(procs, title=f"Processes (sorted by {sort_by})")
        self._pause()

    def _menu_search(self) -> None:
        self._section("Search Process")
        mode = self._prompt_select("Search by", ["name", "pid"], default="name")
        self._mgr.refresh()

        if mode == "name":
            query  = self._prompt_input("Enter name (partial match)")
            results = self._mgr.search_by_name(query)
            if results:
                self._render_process_table(results, title=f"Results for '{query}'")
            else:
                self._warn(f"No processes matching '{query}'.")

        else:
            pid_s = self._prompt_input("Enter PID")
            if not pid_s.isdigit():
                self._warn("PID must be a number.")
                return
            proc = self._mgr.search_by_pid(int(pid_s))
            if proc:
                self._render_process_detail(proc)
            else:
                self._warn(f"PID {pid_s} not found in cache – try refreshing.")

        self._pause()

    def _menu_details(self) -> None:
        self._section("Process Details")
        pid_s = self._prompt_input("Enter PID")
        if not pid_s.isdigit():
            self._warn("PID must be a number.")
            return
        proc = self._mgr._monitor.get_by_pid(int(pid_s))
        if proc:
            self._render_process_detail(proc)
        else:
            self._warn(f"PID {pid_s} not found (may have exited or access denied).")
        self._pause()

    def _menu_terminate(self) -> None:
        self._section("Terminate Process")
        pid_s = self._prompt_input("Enter PID to terminate")
        if not pid_s.isdigit():
            self._warn("PID must be a number.")
            return
        pid = int(pid_s)

        # Show a quick preview
        proc = self._mgr._monitor.get_by_pid(pid)
        if proc:
            print(f"\n  Target: {_colored(proc.name, C.BOLD, C.CYAN)}  "
                  f"PID={pid}  CPU={proc.cpu_usage:.1f}%  "
                  f"MEM={_fmt_bytes(proc.memory_usage)}")
        else:
            self._warn(f"PID {pid} not found.")
            return

        force_s = self._prompt_select(
            "Signal", ["SIGTERM (graceful)", "SIGKILL (force)"],
            default="SIGTERM (graceful)"
        )
        force = "SIGKILL" in force_s

        confirm = self._prompt_input(
            f"Type 'yes' to confirm termination of PID {pid}", default="no"
        )
        if confirm.strip().lower() != "yes":
            print("  Aborted.")
            self._pause()
            return

        result = self._mgr.terminate(pid, force=force)
        self._ok(result)
        self._pause()

    def _menu_system_stats(self) -> None:
        self._section("System Statistics")
        print(_colored("  Sampling … (0.3 s)", C.DIM))
        stats = self._mgr.system_stats()
        self._render_system_stats(stats)
        self._pause()

    def _menu_live_monitor(self) -> None:
        self._section("Live Monitor")
        rows_s    = self._prompt_input("Rows to display [15]", default="15")
        interval_s = self._prompt_input("Refresh interval seconds [2]", default="2")
        rows     = int(rows_s)     if rows_s.isdigit()     else 15
        interval = float(interval_s) if interval_s.replace(".", "", 1).isdigit() else 2.0

        print(_colored(f"\n  Live monitor  (top {rows} by CPU) — press Ctrl-C to stop\n",
                       C.BOLD))
        time.sleep(0.4)

        try:
            while True:
                self._mgr.refresh()
                procs = self._mgr.list_processes(sort_by="cpu", limit=rows)
                stats = self._mgr.system_stats()

                # Move cursor up to overwrite previous output
                if hasattr(self, "_live_lines") and self._live_lines:
                    print(f"\033[{self._live_lines}A", end="")

                lines = self._render_live(procs, stats)
                self._live_lines = lines
                time.sleep(interval)

        except KeyboardInterrupt:
            self._live_lines = 0
            print(_colored("\n  Monitor stopped.", C.YELLOW))
            self._pause()

    def _menu_resource_summary(self) -> None:
        self._section("Resource Summary")
        self._mgr.refresh()
        stats   = self._mgr.system_stats()
        top_cpu = self._mgr.top_cpu(8)
        top_mem = self._mgr.top_mem(8)
        by_status = self._mgr.count_by_status()

        # Status distribution
        w = self._TERM_WIDTH
        print(_colored("\n  Process Status Distribution", C.BOLD, C.CYAN))
        total = sum(by_status.values()) or 1
        for status, cnt in sorted(by_status.items(), key=lambda x: -x[1]):
            pct = cnt / total * 100
            print(f"    {status:<14} {cnt:>5}  {_bar(pct, width=15)}")

        # Top CPU
        print(_colored("\n  Top CPU Consumers", C.BOLD, C.CYAN))
        self._render_mini_table(top_cpu, metric="cpu")

        # Top Memory
        print(_colored("\n  Top Memory Consumers", C.BOLD, C.CYAN))
        self._render_mini_table(top_mem, metric="mem")

        self._pause()

    # ── renderers ────────────────────────────────

    def _render_process_table(
        self, procs: list[Process], title: str = "Processes"
    ) -> None:
        w = min(self._TERM_WIDTH, 130)
        hdr = (
            f"  {'PID':>7}  {'NAME':<22}  {'CPU%':>6}  "
            f"{'MEM':>9}  {'MEM%':>5}  {'STATUS':<12}  {'THREADS':>7}  "
            f"{'USER':<12}  UPTIME"
        )
        sep = "─" * (w - 2)

        print(f"\n  {_colored(title, C.BOLD, C.CYAN)}")
        print(_colored(f"  {sep}", C.DIM))
        print(_colored(hdr, C.BOLD))
        print(_colored(f"  {sep}", C.DIM))

        for p in procs:
            cpu_col = (
                _colored(f"{p.cpu_usage:6.1f}", C.RED)   if p.cpu_usage >= 50 else
                _colored(f"{p.cpu_usage:6.1f}", C.YELLOW) if p.cpu_usage >= 20 else
                f"{p.cpu_usage:6.1f}"
            )
            mem_col = (
                _colored(_fmt_bytes(p.memory_usage).rjust(9), C.RED)
                if p.memory_pct >= 10 else
                _fmt_bytes(p.memory_usage).rjust(9)
            )
            name = p.name[:22].ljust(22)
            user = p.username[:12].ljust(12)
            print(
                f"  {p.process_id:>7}  {name}  {cpu_col}  "
                f"{mem_col}  {p.memory_pct:5.1f}  {p.status_colored}  "
                f"{p.num_threads:>7}  {user}  {p.uptime}"
            )

        print(_colored(f"  {sep}", C.DIM))
        print(f"  {_colored(str(len(procs)), C.BOLD)} processes shown.\n")

    def _render_process_detail(self, p: Process) -> None:
        print(f"\n  {'─'*50}")
        print(f"  {_colored('Process Detail', C.BOLD, C.CYAN)}")
        print(f"  {'─'*50}")
        rows = [
            ("PID",          str(p.process_id)),
            ("Name",         p.name),
            ("Status",       p.status),
            ("CPU Usage",    f"{p.cpu_usage:.2f}%"),
            ("Memory (RSS)", _fmt_bytes(p.memory_usage)),
            ("Memory %",     f"{p.memory_pct:.2f}%"),
            ("Threads",      str(p.num_threads)),
            ("User",         p.username),
            ("Running for",  p.uptime),
            ("Command",      (p.cmdline or "(kernel thread)")[:80]),
        ]
        for label, value in rows:
            print(f"  {_colored(label + ':', C.BOLD):<30} {value}")
        print(f"  {'─'*50}\n")

    def _render_system_stats(self, s: SystemStats) -> None:
        print()
        # Header
        print(f"  {_colored('System Statistics', C.BOLD, C.CYAN)}")
        print(f"  {'─'*60}")
        print(f"  {_colored('System uptime:', C.BOLD):<30} {s.uptime}")
        print(f"  {_colored('Processes running:', C.BOLD):<30} {s.process_count}")
        print(f"  {_colored('CPU cores (logical):', C.BOLD):<30} {s.cpu_count}")
        print(f"  {_colored('CPU frequency:', C.BOLD):<30} {s.cpu_freq_mhz:.0f} MHz")
        print()

        # Overall CPU
        print(f"  {_colored('CPU Usage:', C.BOLD):<30} {_bar(s.cpu_pct)}")

        # Per-core (up to 16)
        cores = s.cpu_per_core[:16]
        cols  = 4
        print(f"\n  {_colored('Per-core CPU:', C.BOLD)}")
        for i in range(0, len(cores), cols):
            row = cores[i:i + cols]
            cells = "  ".join(
                f"  Core {i+j:>2}: {_bar(v, width=10)}" for j, v in enumerate(row)
            )
            print(cells)

        print()
        print(f"  {_colored('RAM Usage:', C.BOLD):<30} {_bar(s.mem_pct)}  "
              f"({_fmt_bytes(s.mem_used)} / {_fmt_bytes(s.mem_total)})")
        print(f"  {_colored('Swap Usage:', C.BOLD):<30} {_bar(s.swap_pct)}  "
              f"({_fmt_bytes(s.swap_used)} / {_fmt_bytes(s.swap_total)})")
        print(f"  {_colored('Disk Usage (/):', C.BOLD):<30} {_bar(s.disk_pct)}  "
              f"({_fmt_bytes(s.disk_used)} / {_fmt_bytes(s.disk_total)})")
        print()
        print(f"  {_colored('Net sent:', C.BOLD):<30} {_fmt_bytes(s.net_bytes_sent)}")
        print(f"  {_colored('Net received:', C.BOLD):<30} {_fmt_bytes(s.net_bytes_recv)}")
        print()

    def _render_mini_table(self, procs: list[Process], metric: str) -> None:
        hdr = f"  {'PID':>7}  {'NAME':<22}  {'CPU%':>6}  {'MEM':>10}  STATUS"
        print(_colored(hdr, C.BOLD))
        print(_colored(f"  {'─'*65}", C.DIM))
        for p in procs:
            bar = (
                _bar(p.cpu_usage, width=12) if metric == "cpu"
                else _bar(p.memory_pct, width=12)
            )
            print(
                f"  {p.process_id:>7}  {p.name[:22]:<22}  "
                f"{p.cpu_usage:6.1f}  {_fmt_bytes(p.memory_usage):>10}  "
                f"{p.status_colored}  {bar}"
            )

    def _render_live(self, procs: list[Process], stats: SystemStats) -> int:
        """Render live-monitor frame; return number of printed lines."""
        lines = 0
        ts = datetime.now().strftime("%H:%M:%S")

        header = (
            f"  {_colored('⟳ Live Monitor', C.BOLD, C.CYAN)}  "
            f"{_colored(ts, C.DIM)}   "
            f"CPU: {_bar(stats.cpu_pct, width=12)}  "
            f"RAM: {_bar(stats.mem_pct, width=12)}"
        )
        print(header); lines += 1

        sep = _colored(f"  {'─'*100}", C.DIM)
        hdr = _colored(
            f"  {'PID':>7}  {'NAME':<22}  {'CPU%':>6}  {'MEM':>9}  "
            f"{'MEM%':>5}  {'STATUS':<12}  THREADS  USER",
            C.BOLD,
        )
        print(sep); lines += 1
        print(hdr); lines += 1
        print(sep); lines += 1

        for p in procs:
            cpu_s = (
                _colored(f"{p.cpu_usage:6.1f}", C.RED)    if p.cpu_usage >= 50 else
                _colored(f"{p.cpu_usage:6.1f}", C.YELLOW) if p.cpu_usage >= 20 else
                f"{p.cpu_usage:6.1f}"
            )
            print(
                f"  {p.process_id:>7}  {p.name[:22]:<22}  {cpu_s}  "
                f"{_fmt_bytes(p.memory_usage):>9}  {p.memory_pct:5.1f}  "
                f"{p.status_colored}  {p.num_threads:>7}  {p.username[:10]:<10}"
            )
            lines += 1

        print(sep); lines += 1
        print(
            _colored(f"  {len(procs)} processes  |  "
                     f"total: {stats.process_count}  |  "
                     f"Ctrl-C to stop", C.DIM)
        )
        lines += 1
        return lines

    # ── UI helpers ────────────────────────────────

    def _banner(self) -> None:
        w = min(self._TERM_WIDTH, 80)
        print(_colored("═" * w, C.CYAN))
        title = "PROCESS MANAGER"
        pad   = (w - len(title)) // 2
        print(_colored(" " * pad + title, C.BOLD, C.CYAN))
        sub   = "Python Task Manager  •  powered by psutil"
        pad2  = (w - len(sub)) // 2
        print(_colored(" " * pad2 + sub, C.DIM))
        print(_colored("═" * w, C.CYAN))
        print()

    def _main_menu(self) -> None:
        print(_colored("  ┌─ MAIN MENU ────────────────────────────┐", C.CYAN))
        items = [
            ("1", "List processes"),
            ("2", "Search process"),
            ("3", "Process details  (by PID)"),
            ("4", "Terminate process"),
            ("5", "System statistics"),
            ("6", "Live monitor"),
            ("7", "Resource summary"),
            ("0", "Exit"),
        ]
        for key, label in items:
            print(
                f"  {_colored('│', C.CYAN)}  "
                f"{_colored(key, C.BOLD, C.YELLOW)}  {label}"
            )
        print(_colored("  └────────────────────────────────────────┘", C.CYAN))

    def _prompt_input(self, prompt: str, default: str = "") -> str:
        hint = f" [{_colored(default, C.DIM)}]" if default else ""
        try:
            val = input(f"\n  {_colored('?', C.BOLD, C.YELLOW)} {prompt}{hint}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return default
        return val if val else default

    def _prompt_choice(self, prompt: str, valid: list[str]) -> str:
        while True:
            val = self._prompt_input(prompt)
            if val in valid:
                return val
            self._warn(f"Please enter one of: {', '.join(v for v in valid if v)}")

    def _prompt_select(self, prompt: str, options: list[str], default: str = "") -> str:
        opts_str = "  /  ".join(
            _colored(o, C.BOLD, C.CYAN) if o == default else o for o in options
        )
        print(f"\n  {_colored('?', C.BOLD, C.YELLOW)} {prompt}: {opts_str}")
        for i, opt in enumerate(options, 1):
            print(f"    {_colored(str(i), C.YELLOW)}  {opt}")
        choice_s = self._prompt_input(f"Enter number [default: {default!r}]", default=default)
        if choice_s.isdigit():
            idx = int(choice_s) - 1
            if 0 <= idx < len(options):
                return options[idx]
        return default

    @staticmethod
    def _warn(msg: str) -> None:
        print(_colored(f"\n  ⚠  {msg}", C.YELLOW))

    @staticmethod
    def _ok(msg: str) -> None:
        print(_colored(f"\n  ✓  {msg}", C.GREEN))

    @staticmethod
    def _section(title: str) -> None:
        print()
        print(_colored(f"  ── {title} {'─' * max(0, 40 - len(title))}", C.BOLD, C.BLUE))

    @staticmethod
    def _pause() -> None:
        try:
            input(_colored("\n  Press Enter to continue…", C.DIM))
        except (KeyboardInterrupt, EOFError):
            print()

    @staticmethod
    def _exit() -> None:
        print(_colored("\n  Goodbye!\n", C.BOLD, C.CYAN))


# ─────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────

def main() -> None:
    # On Windows, enable ANSI colour support
    if sys.platform == "win32":
        os.system("color")

    try:
        UI().run()
    except KeyboardInterrupt:
        print(_colored("\n  Interrupted. Goodbye!\n", C.YELLOW))
        sys.exit(0)


if __name__ == "__main__":
    main()