"""
process_scheduler_simulator.py
================================
A fully-featured CPU scheduling algorithm simulator using OOP.

Supported Algorithms
--------------------
  1. FCFS  – First Come First Served (non-preemptive)
  2. SJF   – Shortest Job First     (non-preemptive)
  3. SRTF  – Shortest Remaining Time First (preemptive SJF)
  4. RR    – Round Robin            (preemptive, configurable quantum)
  5. PRIORITY_NP – Priority Scheduling (non-preemptive, lower number = higher priority)
  6. PRIORITY_P  – Priority Scheduling (preemptive)

Output
------
  • Per-process table: AT, BT, Priority, CT, TAT, WT, RT
  • Averages: TAT, WT, RT, CPU utilisation, throughput
  • ASCII Gantt chart with timeline
"""

from __future__ import annotations

import copy
import math
import os
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ──────────────────────────────────────────────
# ANSI colour helpers
# ──────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    MAGENTA= "\033[95m"
    WHITE  = "\033[97m"
    GREY   = "\033[90m"
    BG_DARK= "\033[40m"

    # 6 rotating colours for Gantt blocks
    GANTT  = ["\033[42m", "\033[44m", "\033[45m", "\033[43m", "\033[46m", "\033[41m"]

def col(text: str, colour: str) -> str:
    return f"{colour}{text}{C.RESET}"

def ok(msg: str)   -> None: print(col(f"  ✔  {msg}", C.GREEN))
def err(msg: str)  -> None: print(col(f"  ✖  {msg}", C.RED))
def info(msg: str) -> None: print(col(f"  ℹ  {msg}", C.CYAN))
def warn(msg: str) -> None: print(col(f"  ⚠  {msg}", C.YELLOW))


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class Algorithm(Enum):
    FCFS        = "FCFS"
    SJF         = "SJF"
    SRTF        = "SRTF"
    RR          = "RR"
    PRIORITY_NP = "PRIORITY_NP"
    PRIORITY_P  = "PRIORITY_P"

    def label(self) -> str:
        labels = {
            Algorithm.FCFS:        "First Come First Served (FCFS)",
            Algorithm.SJF:         "Shortest Job First – Non-Preemptive (SJF)",
            Algorithm.SRTF:        "Shortest Remaining Time First – Preemptive (SRTF)",
            Algorithm.RR:          "Round Robin (RR)",
            Algorithm.PRIORITY_NP: "Priority – Non-Preemptive",
            Algorithm.PRIORITY_P:  "Priority – Preemptive",
        }
        return labels[self]


class ProcessStatus(Enum):
    NEW       = auto()
    READY     = auto()
    RUNNING   = auto()
    WAITING   = auto()
    TERMINATED= auto()


# ──────────────────────────────────────────────
# Process
# ──────────────────────────────────────────────

@dataclass
class Process:
    """
    Represents a single OS process with scheduling metadata.

    Attributes
    ----------
    process_id    : unique string identifier (e.g. "P1")
    arrival_time  : time at which the process enters the ready queue
    burst_time    : total CPU time required
    priority      : integer priority (lower value = higher priority)
    status        : current ProcessStatus
    """

    process_id  : str
    arrival_time: int
    burst_time  : int
    priority    : int = 1
    status      : ProcessStatus = field(default=ProcessStatus.NEW, compare=False)

    # ── Result fields (filled after simulation) ──
    completion_time: int  = field(default=0,  compare=False, repr=False)
    waiting_time   : int  = field(default=0,  compare=False, repr=False)
    turnaround_time: int  = field(default=0,  compare=False, repr=False)
    response_time  : int  = field(default=-1, compare=False, repr=False)

    # ── Internal scheduling state ──
    _remaining_time: int  = field(default=0,  compare=False, repr=False, init=False)
    _started       : bool = field(default=False, compare=False, repr=False, init=False)

    def __post_init__(self) -> None:
        self._validate()
        self._remaining_time = self.burst_time

    # ── Validation ───────────────────────────

    def _validate(self) -> None:
        pid = str(self.process_id).strip()
        if not pid:
            raise ValueError("process_id must not be empty.")
        if not isinstance(self.arrival_time, int) or self.arrival_time < 0:
            raise ValueError(f"[{pid}] arrival_time must be a non-negative integer.")
        if not isinstance(self.burst_time, int) or self.burst_time <= 0:
            raise ValueError(f"[{pid}] burst_time must be a positive integer.")
        if not isinstance(self.priority, int) or self.priority < 1:
            raise ValueError(f"[{pid}] priority must be a positive integer (1 = highest).")

    # ── Helpers ──────────────────────────────

    def reset(self) -> None:
        """Restore to pre-simulation state."""
        self.status          = ProcessStatus.NEW
        self.completion_time = 0
        self.waiting_time    = 0
        self.turnaround_time = 0
        self.response_time   = -1
        self._remaining_time = self.burst_time
        self._started        = False

    def __repr__(self) -> str:
        return (f"Process(id={self.process_id!r}, AT={self.arrival_time}, "
                f"BT={self.burst_time}, P={self.priority})")


# ──────────────────────────────────────────────
# Gantt segment
# ──────────────────────────────────────────────

@dataclass
class GanttSegment:
    pid  : str   # process ID or "IDLE"
    start: int
    end  : int

    @property
    def duration(self) -> int:
        return self.end - self.start


# ──────────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────────

class Scheduler:
    """
    Implements CPU scheduling algorithms.
    Each public method accepts a *deep-copied* list of Process objects,
    runs the simulation, and returns (results_list, gantt_chart).
    """

    # ── Public dispatch ──────────────────────

    def run(
        self,
        processes: list[Process],
        algorithm: Algorithm,
        quantum: int = 2,
    ) -> tuple[list[Process], list[GanttSegment]]:
        """
        Simulate scheduling and return (scheduled_processes, gantt_segments).
        Processes are deep-copied internally; caller's objects are untouched.
        """
        if not processes:
            raise ValueError("No processes to schedule.")
        procs = [copy.deepcopy(p) for p in processes]
        for p in procs:
            p.reset()

        dispatch = {
            Algorithm.FCFS:        self._fcfs,
            Algorithm.SJF:         self._sjf,
            Algorithm.SRTF:        self._srtf,
            Algorithm.RR:          self._rr,
            Algorithm.PRIORITY_NP: self._priority_np,
            Algorithm.PRIORITY_P:  self._priority_p,
        }
        fn = dispatch[algorithm]
        if algorithm == Algorithm.RR:
            return fn(procs, quantum)
        return fn(procs)

    # ── FCFS ─────────────────────────────────

    def _fcfs(self, procs: list[Process]) -> tuple[list[Process], list[GanttSegment]]:
        procs.sort(key=lambda p: (p.arrival_time, p.process_id))
        gantt: list[GanttSegment] = []
        time = 0
        for p in procs:
            if time < p.arrival_time:
                gantt.append(GanttSegment("IDLE", time, p.arrival_time))
                time = p.arrival_time
            p.response_time = time - p.arrival_time
            gantt.append(GanttSegment(p.process_id, time, time + p.burst_time))
            time += p.burst_time
            p.completion_time = time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time    = p.turnaround_time - p.burst_time
            p.status          = ProcessStatus.TERMINATED
        return procs, gantt

    # ── SJF (non-preemptive) ─────────────────

    def _sjf(self, procs: list[Process]) -> tuple[list[Process], list[GanttSegment]]:
        gantt: list[GanttSegment] = []
        remaining = list(procs)
        time      = 0
        done: list[Process] = []

        while remaining:
            available = [p for p in remaining if p.arrival_time <= time]
            if not available:
                next_at = min(p.arrival_time for p in remaining)
                gantt.append(GanttSegment("IDLE", time, next_at))
                time = next_at
                continue
            p = min(available, key=lambda x: (x.burst_time, x.arrival_time, x.process_id))
            remaining.remove(p)
            p.response_time = time - p.arrival_time
            gantt.append(GanttSegment(p.process_id, time, time + p.burst_time))
            time += p.burst_time
            p.completion_time = time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time    = p.turnaround_time - p.burst_time
            p.status          = ProcessStatus.TERMINATED
            done.append(p)
        return done, gantt

    # ── SRTF (preemptive SJF) ────────────────

    def _srtf(self, procs: list[Process]) -> tuple[list[Process], list[GanttSegment]]:
        gantt:     list[GanttSegment] = []
        remaining = list(procs)
        time      = 0
        current:  Optional[Process] = None
        seg_start = 0

        all_done_time = max(p.arrival_time + p.burst_time for p in procs) + 1

        while any(p._remaining_time > 0 for p in remaining):
            available = [p for p in remaining
                         if p.arrival_time <= time and p._remaining_time > 0]
            if not available:
                if current:
                    gantt.append(GanttSegment(current.process_id, seg_start, time))
                    current = None
                next_at = min(p.arrival_time for p in remaining if p._remaining_time > 0)
                gantt.append(GanttSegment("IDLE", time, next_at))
                time     = next_at
                seg_start= time
                continue

            best = min(available, key=lambda p: (p._remaining_time, p.arrival_time, p.process_id))

            if best is not current:
                if current:
                    gantt.append(GanttSegment(current.process_id, seg_start, time))
                current   = best
                seg_start = time
                if not current._started:
                    current.response_time = time - current.arrival_time
                    current._started      = True

            current._remaining_time -= 1
            time += 1

            if current._remaining_time == 0:
                current.completion_time = time
                current.turnaround_time = current.completion_time - current.arrival_time
                current.waiting_time    = current.turnaround_time - current.burst_time
                current.status          = ProcessStatus.TERMINATED
                gantt.append(GanttSegment(current.process_id, seg_start, time))
                current   = None
                seg_start = time

        # Merge consecutive identical segments for cleaner Gantt
        gantt = self._merge_gantt(gantt)
        return procs, gantt

    # ── Round Robin ──────────────────────────

    def _rr(self, procs: list[Process], quantum: int) -> tuple[list[Process], list[GanttSegment]]:
        if quantum < 1:
            raise ValueError("Quantum must be ≥ 1.")
        gantt: list[GanttSegment] = []
        queue:  list[Process]     = []
        remaining = sorted(procs, key=lambda p: p.arrival_time)
        time      = 0
        idx       = 0                    # next process to enqueue

        # Seed queue with processes that arrive at time 0
        while idx < len(remaining) and remaining[idx].arrival_time <= time:
            queue.append(remaining[idx])
            idx += 1

        while queue or idx < len(remaining):
            if not queue:
                # CPU is idle
                next_at = remaining[idx].arrival_time
                gantt.append(GanttSegment("IDLE", time, next_at))
                time = next_at
                while idx < len(remaining) and remaining[idx].arrival_time <= time:
                    queue.append(remaining[idx])
                    idx += 1

            p = queue.pop(0)
            if not p._started:
                p.response_time = time - p.arrival_time
                p._started      = True

            run_time = min(quantum, p._remaining_time)
            gantt.append(GanttSegment(p.process_id, time, time + run_time))
            time               += run_time
            p._remaining_time  -= run_time

            # Enqueue newly arrived processes (arrived during this slice)
            new_arrivals: list[Process] = []
            while idx < len(remaining) and remaining[idx].arrival_time <= time:
                new_arrivals.append(remaining[idx])
                idx += 1

            if p._remaining_time > 0:
                queue.extend(new_arrivals)
                queue.append(p)          # re-queue current at tail
            else:
                p.completion_time = time
                p.turnaround_time = p.completion_time - p.arrival_time
                p.waiting_time    = p.turnaround_time - p.burst_time
                p.status          = ProcessStatus.TERMINATED
                queue.extend(new_arrivals)

        return procs, gantt

    # ── Priority NP ──────────────────────────

    def _priority_np(self, procs: list[Process]) -> tuple[list[Process], list[GanttSegment]]:
        gantt: list[GanttSegment] = []
        remaining = list(procs)
        time      = 0
        done: list[Process] = []

        while remaining:
            available = [p for p in remaining if p.arrival_time <= time]
            if not available:
                next_at = min(p.arrival_time for p in remaining)
                gantt.append(GanttSegment("IDLE", time, next_at))
                time = next_at
                continue
            p = min(available, key=lambda x: (x.priority, x.arrival_time, x.process_id))
            remaining.remove(p)
            p.response_time = time - p.arrival_time
            gantt.append(GanttSegment(p.process_id, time, time + p.burst_time))
            time += p.burst_time
            p.completion_time = time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time    = p.turnaround_time - p.burst_time
            p.status          = ProcessStatus.TERMINATED
            done.append(p)
        return done, gantt

    # ── Priority P ───────────────────────────

    def _priority_p(self, procs: list[Process]) -> tuple[list[Process], list[GanttSegment]]:
        gantt:     list[GanttSegment] = []
        remaining = list(procs)
        time      = 0
        current:  Optional[Process] = None
        seg_start = 0

        while any(p._remaining_time > 0 for p in remaining):
            available = [p for p in remaining
                         if p.arrival_time <= time and p._remaining_time > 0]
            if not available:
                if current:
                    gantt.append(GanttSegment(current.process_id, seg_start, time))
                    current = None
                next_at  = min(p.arrival_time for p in remaining if p._remaining_time > 0)
                gantt.append(GanttSegment("IDLE", time, next_at))
                time      = next_at
                seg_start = time
                continue

            best = min(available, key=lambda p: (p.priority, p.arrival_time, p.process_id))

            if best is not current:
                if current:
                    gantt.append(GanttSegment(current.process_id, seg_start, time))
                current   = best
                seg_start = time
                if not current._started:
                    current.response_time = time - current.arrival_time
                    current._started      = True

            current._remaining_time -= 1
            time += 1

            if current._remaining_time == 0:
                current.completion_time = time
                current.turnaround_time = current.completion_time - current.arrival_time
                current.waiting_time    = current.turnaround_time - current.burst_time
                current.status          = ProcessStatus.TERMINATED
                gantt.append(GanttSegment(current.process_id, seg_start, time))
                current   = None
                seg_start = time

        gantt = self._merge_gantt(gantt)
        return procs, gantt

    # ── Helpers ──────────────────────────────

    @staticmethod
    def _merge_gantt(gantt: list[GanttSegment]) -> list[GanttSegment]:
        """Merge adjacent identical segments."""
        if not gantt:
            return gantt
        merged = [gantt[0]]
        for seg in gantt[1:]:
            if seg.pid == merged[-1].pid:
                merged[-1] = GanttSegment(merged[-1].pid, merged[-1].start, seg.end)
            else:
                merged.append(seg)
        return merged


# ──────────────────────────────────────────────
# Results
# ──────────────────────────────────────────────

@dataclass
class SimulationResult:
    algorithm       : Algorithm
    quantum         : int
    processes       : list[Process]
    gantt           : list[GanttSegment]
    avg_tat         : float
    avg_wt          : float
    avg_rt          : float
    cpu_utilisation : float
    throughput      : float          # processes per unit time


# ──────────────────────────────────────────────
# SimulationManager
# ──────────────────────────────────────────────

class SimulationManager:
    """
    Manages the process list, runs simulations, and displays results.
    """

    def __init__(self) -> None:
        self._processes : list[Process]         = []
        self._scheduler : Scheduler             = Scheduler()
        self._results   : list[SimulationResult]= []

    # ── Process management ───────────────────

    def add_process(
        self,
        process_id  : str,
        arrival_time: int,
        burst_time  : int,
        priority    : int = 1,
    ) -> Process:
        pid = str(process_id).strip().upper()
        if any(p.process_id == pid for p in self._processes):
            raise ValueError(f"Process '{pid}' already exists.")
        p = Process(pid, arrival_time, burst_time, priority)
        self._processes.append(p)
        return p

    def remove_process(self, process_id: str) -> bool:
        pid = process_id.strip().upper()
        before = len(self._processes)
        self._processes = [p for p in self._processes if p.process_id != pid]
        return len(self._processes) < before

    def clear_processes(self) -> None:
        self._processes.clear()

    def get_processes(self) -> list[Process]:
        return list(self._processes)

    def has_processes(self) -> bool:
        return bool(self._processes)

    # ── Simulation ───────────────────────────

    def run(
        self,
        algorithm: Algorithm,
        quantum  : int = 2,
    ) -> SimulationResult:
        if not self._processes:
            raise RuntimeError("No processes loaded. Add at least one process first.")
        if quantum < 1:
            raise ValueError("Quantum must be ≥ 1.")

        procs, gantt = self._scheduler.run(self._processes, algorithm, quantum)

        # Aggregate statistics
        n           = len(procs)
        total_tat   = sum(p.turnaround_time for p in procs)
        total_wt    = sum(p.waiting_time    for p in procs)
        total_rt    = sum(p.response_time   for p in procs if p.response_time >= 0)
        total_span  = max(p.completion_time for p in procs) - min(p.arrival_time for p in procs)
        busy_time   = sum(s.duration for s in gantt if s.pid != "IDLE")
        cpu_util    = (busy_time / total_span * 100) if total_span else 100.0
        throughput  = n / total_span if total_span else float("inf")

        result = SimulationResult(
            algorithm       = algorithm,
            quantum         = quantum,
            processes       = procs,
            gantt           = gantt,
            avg_tat         = total_tat / n,
            avg_wt          = total_wt  / n,
            avg_rt          = total_rt  / n,
            cpu_utilisation = cpu_util,
            throughput      = throughput,
        )
        self._results.append(result)
        return result

    def run_all_algorithms(self, quantum: int = 2) -> list[SimulationResult]:
        return [self.run(algo, quantum) for algo in Algorithm]

    def get_history(self) -> list[SimulationResult]:
        return list(self._results)

    def clear_history(self) -> None:
        self._results.clear()

    # ── Display helpers ──────────────────────

    def display_processes(self) -> None:
        if not self._processes:
            warn("No processes defined.")
            return
        header = (f"  {'PID':<6} {'Arrival':>7} {'Burst':>6} {'Priority':>9}  Status")
        sep    = "  " + "─" * 44
        print(col(f"\n  ── Process List ({len(self._processes)}) ──", C.BOLD))
        print(col(header, C.CYAN))
        print(col(sep, C.GREY))
        for p in sorted(self._processes, key=lambda x: x.arrival_time):
            status_col = C.GREEN if p.status == ProcessStatus.TERMINATED else C.YELLOW
            print(f"  {col(p.process_id, C.BOLD):<15} "
                  f"{p.arrival_time:>7}  {p.burst_time:>6}  {p.priority:>9}  "
                  f"{col(p.status.name, status_col)}")
        print()

    def display_result(self, result: SimulationResult) -> None:
        self._print_header(result)
        self._print_process_table(result)
        self._print_statistics(result)
        self._print_gantt(result)

    def display_comparison(self, results: list[SimulationResult]) -> None:
        print(col("\n  ══ Algorithm Comparison ══", C.BOLD))
        hdr = (f"  {'Algorithm':<26} {'Avg TAT':>8} {'Avg WT':>8} "
               f"{'Avg RT':>8} {'CPU Util':>9} {'Throughput':>11}")
        sep = "  " + "─" * 74
        print(col(hdr, C.CYAN))
        print(col(sep, C.GREY))

        best_wt  = min(r.avg_wt for r in results)
        best_tat = min(r.avg_tat for r in results)

        for r in results:
            name   = r.algorithm.value
            if r.algorithm == Algorithm.RR:
                name += f"(q={r.quantum})"
            wt_col  = C.GREEN if r.avg_wt  == best_wt  else C.RESET
            tat_col = C.GREEN if r.avg_tat == best_tat else C.RESET
            print(f"  {col(name, C.BOLD):<35} "
                  f"{col(f'{r.avg_tat:8.2f}', tat_col)} "
                  f"{col(f'{r.avg_wt:8.2f}', wt_col)} "
                  f"{r.avg_rt:8.2f} "
                  f"{r.cpu_utilisation:8.1f}% "
                  f"{r.throughput:11.4f}")
        print()

    # ── Internal display helpers ─────────────

    @staticmethod
    def _print_header(result: SimulationResult) -> None:
        name = result.algorithm.label()
        if result.algorithm == Algorithm.RR:
            name += f"  (quantum = {result.quantum})"
        line = f"  Algorithm: {name}"
        print(col("\n" + "═" * 70, C.BOLD))
        print(col(line, C.BOLD + C.CYAN))
        print(col("═" * 70, C.BOLD))

    @staticmethod
    def _print_process_table(result: SimulationResult) -> None:
        procs = sorted(result.processes, key=lambda p: p.process_id)
        header = (f"  {'PID':<6} {'AT':>4} {'BT':>4} {'Pri':>4} "
                  f"{'CT':>5} {'TAT':>5} {'WT':>5} {'RT':>5}")
        sep = "  " + "─" * 44
        print(col("\n  ── Process Results ──", C.BOLD))
        print(col(header, C.CYAN))
        print(col(sep, C.GREY))
        for p in procs:
            rt = str(p.response_time) if p.response_time >= 0 else "N/A"
            print(f"  {col(p.process_id, C.BOLD):<15} "
                  f"{p.arrival_time:>4} {p.burst_time:>4} {p.priority:>4} "
                  f"{p.completion_time:>5} {p.turnaround_time:>5} "
                  f"{p.waiting_time:>5} {rt:>5}")
        print()

    @staticmethod
    def _print_statistics(result: SimulationResult) -> None:
        print(col("  ── Statistics ──", C.BOLD))
        stats = [
            ("Average Turnaround Time", f"{result.avg_tat:.2f}"),
            ("Average Waiting Time",    f"{result.avg_wt:.2f}"),
            ("Average Response Time",   f"{result.avg_rt:.2f}"),
            ("CPU Utilisation",         f"{result.cpu_utilisation:.1f}%"),
            ("Throughput",              f"{result.throughput:.4f} proc/unit"),
        ]
        for label, value in stats:
            print(f"  {col(label + ':', C.GREY):<42} {col(value, C.YELLOW)}")
        print()

    @staticmethod
    def _print_gantt(result: SimulationResult) -> None:
        """Render a text-based Gantt chart, scaled to terminal width."""
        gantt = result.gantt
        if not gantt:
            return

        total_time = gantt[-1].end
        # Collect unique PIDs for colour mapping
        pids = list(dict.fromkeys(s.pid for s in gantt if s.pid != "IDLE"))
        pid_colour = {pid: C.GANTT[i % len(C.GANTT)] for i, pid in enumerate(pids)}

        print(col("  ── Gantt Chart ──", C.BOLD))

        try:
            term_w = os.get_terminal_size().columns - 4
        except OSError:
            term_w = 76

        CELL_W = 3      # minimum characters per time unit

        # Scale: fit into terminal width
        scale = max(1, math.ceil(total_time * CELL_W / term_w))
        # One display unit = `scale` time units

        def time_to_disp(t: int) -> int:
            return (t + scale - 1) // scale if scale > 0 else t

        disp_len = time_to_disp(total_time)
        bar_w    = max(disp_len * CELL_W, 1)

        # ── Top border ──
        top = "  ┌" + "─" * bar_w + "┐"
        print(col(top, C.GREY))

        # ── Process row ──
        bar = "  │"
        for seg in gantt:
            seg_disp = max(1, time_to_disp(seg.end) - time_to_disp(seg.start))
            cell_w   = seg_disp * CELL_W
            label    = seg.pid.center(cell_w)[:cell_w]
            if seg.pid == "IDLE":
                bar += col(label, C.GREY)
            else:
                colour = pid_colour.get(seg.pid, C.RESET)
                bar += col(label, colour + C.BOLD)
        bar += col("│", C.GREY)
        print(bar)

        # ── Bottom border ──
        bot = "  └" + "─" * bar_w + "┘"
        print(col(bot, C.GREY))

        # ── Timeline ──
        # Print tick marks at each segment boundary
        ticks_displayed: set[int] = set()
        tick_row   = "   "
        label_row  = "   "
        cursor     = 0

        for seg in gantt:
            seg_disp = max(1, time_to_disp(seg.end) - time_to_disp(seg.start))
            cell_w   = seg_disp * CELL_W

            # Start tick of this segment
            if seg.start not in ticks_displayed:
                t_str = str(seg.start)
                tick_row  += "│" + " " * (cell_w - 1)
                label_row += t_str.ljust(cell_w)
                ticks_displayed.add(seg.start)
            else:
                tick_row  += " " * cell_w
                label_row += " " * cell_w

        # Final tick (end of last segment)
        tick_row  += "│"
        label_row += str(total_time)

        print(col(tick_row,  C.GREY))
        print(col(label_row, C.GREY))
        print()

        # ── Legend ──
        legend = "  "
        for pid, colour in pid_colour.items():
            legend += col(f"  {pid} ", colour + C.BOLD) + "  "
        if any(s.pid == "IDLE" for s in gantt):
            legend += col("  IDLE  ", C.GREY) + "  "
        print(legend)
        print()


# ──────────────────────────────────────────────
# Interactive Console UI
# ──────────────────────────────────────────────

BANNER = r"""
  ____  ____ _   _    ____       _               _       _
 / ___||  _ \ | | |  / ___|  ___| |__   ___   __| |_   _| | ___ _ __
| |    | |_) | | | | \___ \ / __| '_ \ / _ \ / _` | | | | |/ _ \ '__|
| |___ |  __/| |_| |  ___) | (__| | | |  __/| (_| | |_| | |  __/ |
 \____||_|    \___/  |____/ \___|_| |_|\___| \__,_|\__,_|_|\___|_|

           S I M U L A T O R    v1.0
"""

MENU = """
{BOLD}──────────────────────────────────────────────────────────{RESET}
  {CYAN}1{RESET}  Add process(es)
  {CYAN}2{RESET}  View / remove processes
  {CYAN}3{RESET}  Run a scheduling algorithm
  {CYAN}4{RESET}  Run ALL algorithms (comparison)
  {CYAN}5{RESET}  Load demo processes
  {CYAN}6{RESET}  View last result history
  {CYAN}7{RESET}  Clear processes
  {CYAN}0{RESET}  Exit
{BOLD}──────────────────────────────────────────────────────────{RESET}
"""

ALGO_MENU = """
{BOLD}  Select algorithm:{RESET}
  {CYAN}1{RESET}  FCFS          – First Come First Served
  {CYAN}2{RESET}  SJF           – Shortest Job First (non-preemptive)
  {CYAN}3{RESET}  SRTF          – Shortest Remaining Time First (preemptive)
  {CYAN}4{RESET}  RR            – Round Robin
  {CYAN}5{RESET}  PRIORITY_NP   – Priority (non-preemptive)
  {CYAN}6{RESET}  PRIORITY_P    – Priority (preemptive)
  {CYAN}0{RESET}  Cancel
"""


def _fmt(text: str) -> str:
    return text.format(
        BOLD=C.BOLD, RESET=C.RESET, CYAN=C.CYAN,
        GREEN=C.GREEN, YELLOW=C.YELLOW, GREY=C.GREY,
    )


def _input(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"  {col(prompt + suffix + ': ', C.CYAN)}").strip()
    except (EOFError, KeyboardInterrupt):
        val = ""
    return val or default


def _int_input(prompt: str, default: int, min_val: int = 0, max_val: int = 10_000) -> int:
    while True:
        raw = _input(prompt, str(default))
        try:
            v = int(raw)
            if min_val <= v <= max_val:
                return v
            err(f"Value must be between {min_val} and {max_val}.")
        except ValueError:
            err("Please enter a valid integer.")


class ConsoleApp:

    DEMO_SETS = {
        "basic": [
            ("P1", 0, 6, 2),
            ("P2", 1, 4, 1),
            ("P3", 2, 8, 3),
            ("P4", 3, 3, 2),
            ("P5", 4, 5, 1),
        ],
        "burst": [
            ("P1", 0, 10, 1),
            ("P2", 0, 1,  2),
            ("P3", 2, 5,  3),
            ("P4", 3, 2,  1),
        ],
        "priority": [
            ("P1", 0, 5, 3),
            ("P2", 1, 3, 1),
            ("P3", 2, 8, 2),
            ("P4", 3, 2, 1),
            ("P5", 4, 4, 4),
        ],
    }

    def __init__(self) -> None:
        self.manager = SimulationManager()

    def run(self) -> None:
        print(col(BANNER, C.CYAN))
        actions = {
            "1": self._add_processes,
            "2": self._view_remove,
            "3": self._run_algorithm,
            "4": self._run_all,
            "5": self._load_demo,
            "6": self._view_history,
            "7": self._clear_processes,
        }
        while True:
            print(_fmt(MENU))
            choice = _input("Select option").strip()
            if choice == "0":
                print(col("\n  Goodbye!\n", C.GREEN))
                break
            fn = actions.get(choice)
            if fn:
                try:
                    fn()
                except Exception as exc:
                    err(f"Unexpected error: {exc}")
            else:
                warn("Unknown option — please choose from the menu.")

    # ── Menu actions ─────────────────────────

    def _add_processes(self) -> None:
        print(col("\n  ── Add Processes ──", C.BOLD))
        info("Enter process details. Press Enter with empty PID to stop.")
        while True:
            pid = _input("Process ID (e.g. P1, empty to stop)", "")
            if not pid:
                break
            at  = _int_input("Arrival Time",      0, 0, 9999)
            bt  = _int_input("Burst Time",         1, 1, 9999)
            pri = _int_input("Priority (1=high)",  1, 1, 100)
            try:
                p = self.manager.add_process(pid, at, bt, pri)
                ok(f"Added {col(p.process_id, C.BOLD)}")
            except ValueError as exc:
                err(str(exc))

    def _view_remove(self) -> None:
        self.manager.display_processes()
        if not self.manager.has_processes():
            return
        pid = _input("Remove process by ID (empty to skip)", "")
        if pid:
            if self.manager.remove_process(pid):
                ok(f"Removed '{pid.upper()}'.")
            else:
                err(f"Process '{pid.upper()}' not found.")

    def _run_algorithm(self) -> None:
        if not self.manager.has_processes():
            warn("No processes defined. Add processes first (option 1).")
            return
        print(_fmt(ALGO_MENU))
        algo_map = {
            "1": Algorithm.FCFS,
            "2": Algorithm.SJF,
            "3": Algorithm.SRTF,
            "4": Algorithm.RR,
            "5": Algorithm.PRIORITY_NP,
            "6": Algorithm.PRIORITY_P,
        }
        choice = _input("Algorithm").strip()
        if choice == "0":
            return
        algo = algo_map.get(choice)
        if not algo:
            err("Invalid choice.")
            return

        quantum = 2
        if algo == Algorithm.RR:
            quantum = _int_input("Time Quantum", 2, 1, 999)

        try:
            result = self.manager.run(algo, quantum)
            self.manager.display_result(result)
        except Exception as exc:
            err(str(exc))

    def _run_all(self) -> None:
        if not self.manager.has_processes():
            warn("No processes defined.")
            return
        quantum = _int_input("Time Quantum for Round Robin", 2, 1, 999)
        print(col("\n  Running all algorithms…", C.CYAN))
        results = []
        for algo in Algorithm:
            try:
                r = self.manager.run(algo, quantum)
                results.append(r)
                ok(f"{algo.value:<14} done")
            except Exception as exc:
                err(f"{algo.value}: {exc}")
        if results:
            self.manager.display_comparison(results)
            # Show full details for each
            show = _input("Show full detail for each algorithm? (yes/no)", "no").lower()
            if show in ("y", "yes"):
                for r in results:
                    self.manager.display_result(r)

    def _load_demo(self) -> None:
        print(col("\n  Demo sets:", C.BOLD))
        sets = list(self.DEMO_SETS.keys())
        for i, name in enumerate(sets, 1):
            procs = self.DEMO_SETS[name]
            print(f"  {col(str(i), C.CYAN)}  {name}  ({len(procs)} processes)")
        choice = _input("Choose set", "1")
        try:
            idx  = int(choice) - 1
            name = sets[idx]
        except (ValueError, IndexError):
            err("Invalid selection.")
            return

        self.manager.clear_processes()
        for pid, at, bt, pri in self.DEMO_SETS[name]:
            self.manager.add_process(pid, at, bt, pri)
        ok(f"Loaded demo set '{name}' ({len(self.DEMO_SETS[name])} processes).")
        self.manager.display_processes()

    def _view_history(self) -> None:
        history = self.manager.get_history()
        if not history:
            info("No simulations have been run yet.")
            return
        print(col(f"\n  ── Simulation History ({len(history)} runs) ──", C.BOLD))
        for i, r in enumerate(history, 1):
            name = r.algorithm.value
            if r.algorithm == Algorithm.RR:
                name += f"(q={r.quantum})"
            print(f"  {col(str(i), C.CYAN)}  {name:<22}  "
                  f"AvgWT={r.avg_wt:.2f}  AvgTAT={r.avg_tat:.2f}")
        idx_str = _input("Show detail for run # (empty to skip)", "")
        if idx_str:
            try:
                idx = int(idx_str) - 1
                self.manager.display_result(history[idx])
            except (ValueError, IndexError):
                err("Invalid selection.")

    def _clear_processes(self) -> None:
        confirm = _input("Clear ALL processes? (yes/no)", "no").lower()
        if confirm in ("y", "yes"):
            self.manager.clear_processes()
            self.manager.clear_history()
            ok("Processes and history cleared.")
        else:
            info("Cancelled.")


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def main() -> None:
    app = ConsoleApp()
    app.run()



if __name__ == "__main__":
    main()