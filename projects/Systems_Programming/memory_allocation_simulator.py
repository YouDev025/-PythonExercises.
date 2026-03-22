"""
╔══════════════════════════════════════════════════════════════════╗
║         Memory Allocation Simulator  –  Python OOP              ║
║                                                                  ║
║  Classes:                                                        ║
║    MemoryBlock       – unit of memory (free or allocated)        ║
║    Process           – a process that needs memory               ║
║    MemoryManager     – manages blocks; First/Best/Worst Fit      ║
║    SimulationManager – runs scenarios, tracks history, reports   ║
║    Shell             – interactive REPL                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# Enums & Constants
# ═══════════════════════════════════════════════════════════════

class BlockStatus(Enum):
    FREE      = "FREE"
    ALLOCATED = "ALLOCATED"


class Strategy(Enum):
    FIRST_FIT = "First Fit"
    BEST_FIT  = "Best Fit"
    WORST_FIT = "Worst Fit"


# ANSI colour helpers
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GREY    = "\033[90m"

    @staticmethod
    def color(text: str, *codes: str) -> str:
        return "".join(codes) + text + C.RESET


# ═══════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════

class MemoryError_(Exception):
    """Base simulator exception."""

class AllocationError(MemoryError_):
    pass

class DeallocationError(MemoryError_):
    pass

class InvalidInputError(MemoryError_):
    pass


# ═══════════════════════════════════════════════════════════════
# MemoryBlock
# ═══════════════════════════════════════════════════════════════

@dataclass
class MemoryBlock:
    """
    A contiguous region of memory.

    Attributes
    ----------
    block_id   : unique integer identifier
    start      : starting address (KB)
    size       : capacity in KB
    status     : FREE or ALLOCATED
    process_id : ID of the occupying process (None if free)
    """
    block_id:   int
    start:      int
    size:       int
    status:     BlockStatus        = BlockStatus.FREE
    process_id: Optional[str]      = None

    @property
    def end(self) -> int:
        return self.start + self.size - 1

    @property
    def is_free(self) -> bool:
        return self.status == BlockStatus.FREE

    def allocate(self, process_id: str) -> None:
        self.status     = BlockStatus.ALLOCATED
        self.process_id = process_id

    def free(self) -> None:
        self.status     = BlockStatus.FREE
        self.process_id = None

    def split(self, required: int, next_id: int) -> Optional["MemoryBlock"]:
        """
        Split this block into one of *required* KB and a remainder.
        Returns the new free remainder block, or None if no split needed.
        """
        remainder = self.size - required
        if remainder <= 0:
            return None
        self.size = required
        leftover = MemoryBlock(
            block_id = next_id,
            start    = self.start + required,
            size     = remainder,
        )
        return leftover

    def __repr__(self) -> str:
        pid = self.process_id or "–"
        return (f"Block[{self.block_id:02d}] "
                f"{self.start:>5}–{self.end:<5} KB  "
                f"{self.size:>5} KB  {self.status.value:<10}  PID={pid}")


# ═══════════════════════════════════════════════════════════════
# Process
# ═══════════════════════════════════════════════════════════════

@dataclass
class Process:
    """
    A process that consumes a fixed amount of memory.

    Attributes
    ----------
    process_id      : unique string identifier (e.g. "P1")
    required_memory : memory needed in KB
    name            : human-readable label
    created_at      : timestamp
    allocated_at    : timestamp of successful allocation (None until then)
    block_id        : which block this process was placed in
    """
    process_id:      str
    required_memory: int
    name:            str           = ""
    created_at:      datetime      = field(default_factory=datetime.now)
    allocated_at:    Optional[datetime] = field(default=None, init=False)
    block_id:        Optional[int]      = field(default=None, init=False)

    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"Process {self.process_id}"
        if self.required_memory <= 0:
            raise InvalidInputError("required_memory must be > 0.")

    @property
    def is_allocated(self) -> bool:
        return self.block_id is not None

    def __repr__(self) -> str:
        status = f"in Block {self.block_id}" if self.is_allocated else "not allocated"
        return f"Process({self.process_id}, {self.required_memory} KB, {status})"


# ═══════════════════════════════════════════════════════════════
# MemoryManager
# ═══════════════════════════════════════════════════════════════

class MemoryManager:
    """
    Manages a list of MemoryBlocks and supports three placement strategies.

    Methods
    -------
    allocate(process, strategy) – find a block and place the process
    deallocate(process_id)      – free the block held by a process
    merge_free_blocks()         – coalesce adjacent free blocks
    status_report()             – summary dict of current state
    """

    def __init__(self, total_memory: int, block_sizes: Optional[List[int]] = None) -> None:
        """
        Parameters
        ----------
        total_memory : total RAM in KB
        block_sizes  : list of initial partition sizes (must sum to total_memory).
                       If None, memory is treated as a single contiguous block.
        """
        self._validate_init(total_memory, block_sizes)
        self.total_memory = total_memory
        self._next_id     = 0
        self.blocks: List[MemoryBlock] = self._build_blocks(block_sizes)

    # ── init helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _validate_init(total: int, sizes: Optional[List[int]]) -> None:
        if total <= 0:
            raise InvalidInputError("total_memory must be > 0.")
        if sizes and sum(sizes) != total:
            raise InvalidInputError(
                f"Block sizes sum ({sum(sizes)}) != total_memory ({total}).")
        if sizes and any(s <= 0 for s in sizes):
            raise InvalidInputError("All block sizes must be > 0.")

    def _build_blocks(self, sizes: Optional[List[int]]) -> List[MemoryBlock]:
        if not sizes:
            blk = MemoryBlock(self._next_id, 0, self.total_memory)
            self._next_id += 1
            return [blk]
        blocks, addr = [], 0
        for s in sizes:
            blocks.append(MemoryBlock(self._next_id, addr, s))
            self._next_id += 1
            addr += s
        return blocks

    # ── allocation ────────────────────────────────────────────────────────────
    def allocate(self, process: Process, strategy: Strategy) -> MemoryBlock:
        """
        Find a free block using *strategy* and place *process* in it.
        Splits the block if there is surplus space.

        Returns the block that was allocated.
        Raises AllocationError if no suitable block exists.
        """
        candidate = self._find_block(process.required_memory, strategy)
        if candidate is None:
            raise AllocationError(
                f"No free block found for {process.process_id} "
                f"({process.required_memory} KB) using {strategy.value}.")

        # Split surplus
        remainder = candidate.split(process.required_memory, self._next_id)
        if remainder:
            self._next_id += 1
            idx = self.blocks.index(candidate)
            self.blocks.insert(idx + 1, remainder)

        candidate.allocate(process.process_id)
        process.block_id     = candidate.block_id
        process.allocated_at = datetime.now()
        return candidate

    def _find_block(self, size: int, strategy: Strategy) -> Optional[MemoryBlock]:
        free = [b for b in self.blocks if b.is_free and b.size >= size]
        if not free:
            return None
        if strategy == Strategy.FIRST_FIT:
            return free[0]
        if strategy == Strategy.BEST_FIT:
            return min(free, key=lambda b: b.size)
        if strategy == Strategy.WORST_FIT:
            return max(free, key=lambda b: b.size)
        return None   # unreachable

    # ── deallocation ──────────────────────────────────────────────────────────
    def deallocate(self, process: Process) -> MemoryBlock:
        """Free the block held by *process*. Returns the freed block."""
        if not process.is_allocated:
            raise DeallocationError(
                f"{process.process_id} is not currently allocated.")
        blk = self._get_block_by_id(process.block_id)
        if blk is None:
            raise DeallocationError(
                f"Block {process.block_id} not found for {process.process_id}.")
        blk.free()
        process.block_id     = None
        process.allocated_at = None
        self.merge_free_blocks()
        return blk

    def _get_block_by_id(self, block_id: int) -> Optional[MemoryBlock]:
        for b in self.blocks:
            if b.block_id == block_id:
                return b
        return None

    # ── merging ───────────────────────────────────────────────────────────────
    def merge_free_blocks(self) -> int:
        """
        Coalesce contiguous free blocks (compaction).
        Returns the number of merges performed.
        """
        merges = 0
        i = 0
        while i < len(self.blocks) - 1:
            cur, nxt = self.blocks[i], self.blocks[i + 1]
            if cur.is_free and nxt.is_free and cur.end + 1 == nxt.start:
                cur.size += nxt.size
                self.blocks.pop(i + 1)
                merges += 1
            else:
                i += 1
        return merges

    # ── statistics ────────────────────────────────────────────────────────────
    def status_report(self) -> Dict:
        free_blocks  = [b for b in self.blocks if b.is_free]
        alloc_blocks = [b for b in self.blocks if not b.is_free]
        total_free   = sum(b.size for b in free_blocks)
        total_alloc  = sum(b.size for b in alloc_blocks)
        frag_index   = (len(free_blocks) - 1) / max(len(free_blocks), 1)
        return {
            "total_memory":       self.total_memory,
            "allocated_memory":   total_alloc,
            "free_memory":        total_free,
            "utilisation_pct":    round(total_alloc / self.total_memory * 100, 1),
            "total_blocks":       len(self.blocks),
            "free_blocks":        len(free_blocks),
            "allocated_blocks":   len(alloc_blocks),
            "largest_free_block": max((b.size for b in free_blocks), default=0),
            "fragmentation_idx":  round(frag_index, 3),
        }


# ═══════════════════════════════════════════════════════════════
# SimulationManager
# ═══════════════════════════════════════════════════════════════

@dataclass
class AllocationEvent:
    """One entry in the simulation history log."""
    timestamp:  datetime
    event_type: str            # "ALLOCATE" | "DEALLOCATE" | "FAIL"
    process_id: str
    size:       int
    strategy:   str
    block_id:   Optional[int]
    utilisation: float


class SimulationManager:
    """
    Orchestrates processes, drives MemoryManager, and keeps an audit log.
    """

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.mm:        MemoryManager              = memory_manager
        self.processes: Dict[str, Process]         = {}
        self.history:   List[AllocationEvent]      = []
        self.strategy:  Strategy                   = Strategy.FIRST_FIT
        self._pid_ctr:  int                        = 1

    # ── process factory ───────────────────────────────────────────────────────
    def create_process(self, size: int, name: str = "",
                       pid: Optional[str] = None) -> Process:
        if pid is None:
            pid = f"P{self._pid_ctr}"
            self._pid_ctr += 1
        if pid in self.processes:
            raise InvalidInputError(f"Process ID '{pid}' already exists.")
        p = Process(process_id=pid, required_memory=size, name=name)
        self.processes[pid] = p
        return p

    # ── allocation ────────────────────────────────────────────────────────────
    def allocate(self, pid: str) -> MemoryBlock:
        p = self._get_process(pid)
        if p.is_allocated:
            raise AllocationError(f"{pid} is already allocated (Block {p.block_id}).")
        try:
            blk = self.mm.allocate(p, self.strategy)
            self._log("ALLOCATE", p, blk.block_id)
            return blk
        except AllocationError as e:
            self._log("FAIL", p, None)
            raise

    def deallocate(self, pid: str) -> MemoryBlock:
        p = self._get_process(pid)
        blk = self.mm.deallocate(p)
        self._log("DEALLOCATE", p, blk.block_id)
        return blk

    def auto_run(self, process_sizes: List[int]) -> None:
        """
        Convenience: create & allocate processes for each size in the list.
        Silently records failures without raising.
        """
        for size in process_sizes:
            p = self.create_process(size)
            try:
                self.allocate(p.process_id)
            except AllocationError:
                pass   # already logged as FAIL

    # ── strategy ──────────────────────────────────────────────────────────────
    def set_strategy(self, strategy: Strategy) -> None:
        self.strategy = strategy

    # ── helpers ───────────────────────────────────────────────────────────────
    def _get_process(self, pid: str) -> Process:
        if pid not in self.processes:
            raise InvalidInputError(f"Unknown process ID: '{pid}'.")
        return self.processes[pid]

    def _log(self, event_type: str, process: Process,
             block_id: Optional[int]) -> None:
        util = self.mm.status_report()["utilisation_pct"]
        self.history.append(AllocationEvent(
            timestamp   = datetime.now(),
            event_type  = event_type,
            process_id  = process.process_id,
            size        = process.required_memory,
            strategy    = self.strategy.value,
            block_id    = block_id,
            utilisation = util,
        ))

    # ── reporting ─────────────────────────────────────────────────────────────
    def summary(self) -> Dict:
        total   = len(self.history)
        allocs  = sum(1 for e in self.history if e.event_type == "ALLOCATE")
        fails   = sum(1 for e in self.history if e.event_type == "FAIL")
        deallocs= sum(1 for e in self.history if e.event_type == "DEALLOCATE")
        peak    = max((e.utilisation for e in self.history), default=0.0)
        return {
            "total_events":   total,
            "allocations":    allocs,
            "deallocations":  deallocs,
            "failures":       fails,
            "peak_utilisation": f"{peak:.1f}%",
        }


# ═══════════════════════════════════════════════════════════════
# Visualiser helpers
# ═══════════════════════════════════════════════════════════════

def _bar(used: int, total: int, width: int = 50) -> str:
    """Horizontal bar showing memory utilisation."""
    filled = round(used / total * width) if total else 0
    pct = used / total * 100 if total else 0
    bar = "█" * filled + "░" * (width - filled)
    colour = C.GREEN if pct < 60 else C.YELLOW if pct < 85 else C.RED
    return C.color(f"[{bar}]", colour) + f"  {pct:.1f}%"


def _memory_map(blocks: List[MemoryBlock], total: int, width: int = 60) -> str:
    """
    Render each block as a proportional segment of a single-line map.

        [████PPPP████░░░░░░░░]
         ^allocated  ^free
    """
    CHARS = {BlockStatus.FREE: "░", BlockStatus.ALLOCATED: "█"}
    COLOURS = {BlockStatus.FREE: C.GREY, BlockStatus.ALLOCATED: C.CYAN}

    segments = []
    for b in blocks:
        chars = max(1, round(b.size / total * width))
        ch    = CHARS[b.status]
        col   = COLOURS[b.status]
        label = b.process_id[:2] if (b.process_id and chars >= 2) else ch
        inner = (label.center(chars, ch) if chars > 2 else ch * chars)
        segments.append(C.color(inner, col))
    return "[" + "".join(segments) + "]"


def _block_table(blocks: List[MemoryBlock]) -> str:
    """Pretty-print a table of all memory blocks."""
    header = (f"  {'ID':>3}  {'Start':>6}  {'End':>6}  {'Size':>6}  "
              f"{'Status':<11}  {'Process':<10}")
    sep    = "  " + "─" * (len(header) - 2)
    rows   = [header, sep]
    for b in blocks:
        pid = b.process_id or "–"
        status_str = (C.color(b.status.value, C.GREEN) if b.is_free
                      else C.color(b.status.value, C.CYAN))
        rows.append(
            f"  {b.block_id:>3}  {b.start:>5}K  {b.end:>5}K  "
            f"{b.size:>5}K  {status_str:<20}  {pid:<10}"
        )
    return "\n".join(rows)


def _history_table(events: List[AllocationEvent], last_n: int = 15) -> str:
    shown  = events[-last_n:]
    header = (f"  {'#':>3}  {'Time':>8}  {'Type':<12}  {'PID':<6}  "
              f"{'Size':>6}  {'Block':>5}  {'Strategy':<12}  {'Util':>5}")
    sep    = "  " + "─" * (len(header) - 2)
    rows   = [header, sep]
    for i, e in enumerate(shown, start=max(1, len(events) - last_n + 1)):
        t     = e.timestamp.strftime("%H:%M:%S")
        blk   = str(e.block_id) if e.block_id is not None else "–"
        type_col = {
            "ALLOCATE":   C.color(e.event_type, C.GREEN),
            "DEALLOCATE": C.color(e.event_type, C.YELLOW),
            "FAIL":       C.color(e.event_type, C.RED),
        }.get(e.event_type, e.event_type)
        rows.append(
            f"  {i:>3}  {t}  {type_col:<21}  {e.process_id:<6}  "
            f"{e.size:>5}K  {blk:>5}  {e.strategy:<12}  {e.utilisation:>4.1f}%"
        )
    return "\n".join(rows)


# ═══════════════════════════════════════════════════════════════
# Shell (REPL)
# ═══════════════════════════════════════════════════════════════

class Shell:
    """
    Interactive console for the Memory Allocation Simulator.

    Commands
    --------
    status              – memory map + block table
    create <size> [name] [pid]  – create a process
    alloc  <pid>        – allocate memory for a process
    free   <pid>        – deallocate process memory
    processes           – list all processes
    strategy <name>     – set First | Best | Worst
    history [n]         – show last n events (default 15)
    summary             – simulation statistics
    reset               – wipe and restart
    demo                – run a built-in demonstration
    help                – show this help
    exit                – quit
    """

    BANNER = r"""
 ╔══════════════════════════════════════════════════════════════╗
 ║       Memory Allocation Simulator  –  Python OOP  v1.0      ║
 ╠══════════════════════════════════════════════════════════════╣
 ║  Strategies: First Fit  |  Best Fit  |  Worst Fit           ║
 ║  Type  help  for commands.   Type  demo  to see it in action.║
 ╚══════════════════════════════════════════════════════════════╝
"""

    DEFAULT_TOTAL  = 1024   # KB
    DEFAULT_BLOCKS = [64, 128, 96, 256, 64, 192, 128, 96]  # sums to 1024

    def __init__(self) -> None:
        self.sim      = self._build_sim()
        self._running = True

    # ── factory ───────────────────────────────────────────────────────────────
    def _build_sim(self) -> SimulationManager:
        mm = MemoryManager(self.DEFAULT_TOTAL, self.DEFAULT_BLOCKS)
        return SimulationManager(mm)

    # ── REPL ──────────────────────────────────────────────────────────────────
    def run(self) -> None:
        print(self.BANNER)
        self._print_status()
        while self._running:
            try:
                raw = input(C.color("\nmem-sim", C.BOLD, C.CYAN) +
                            C.color(f"[{self.sim.strategy.value}]", C.YELLOW) +
                            C.color(" > ", C.BOLD)).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting…")
                break
            if not raw:
                continue
            parts = raw.split()
            self._dispatch(parts[0].lower(), parts[1:])

    def _dispatch(self, cmd: str, args: List[str]) -> None:
        table = {
            "status":    self._cmd_status,
            "create":    self._cmd_create,
            "alloc":     self._cmd_alloc,
            "free":      self._cmd_free,
            "processes": self._cmd_processes,
            "strategy":  self._cmd_strategy,
            "history":   self._cmd_history,
            "summary":   self._cmd_summary,
            "reset":     self._cmd_reset,
            "demo":      self._cmd_demo,
            "help":      self._cmd_help,
            "exit":      self._cmd_exit,
            "quit":      self._cmd_exit,
        }
        fn = table.get(cmd)
        if fn is None:
            self._err(f"Unknown command '{cmd}'. Type 'help' for help.")
        else:
            try:
                fn(args)
            except (MemoryError_, InvalidInputError, ValueError) as e:
                self._err(str(e))

    # ── commands ──────────────────────────────────────────────────────────────

    def _cmd_status(self, _args: List[str]) -> None:
        self._print_status()

    def _cmd_create(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: create <size_KB> [name] [pid]")
            return
        size = self._parse_int(args[0], "size")
        name = args[1] if len(args) > 1 else ""
        pid  = args[2] if len(args) > 2 else None
        p    = self.sim.create_process(size, name=name, pid=pid)
        print(C.color(f"  ✔ Created {p.process_id} ({p.name}, {p.required_memory} KB)", C.GREEN))

    def _cmd_alloc(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: alloc <pid>")
            return
        pid = args[0].upper()
        blk = self.sim.allocate(pid)
        p   = self.sim.processes[pid]
        print(C.color(
            f"  ✔ {pid} ({p.required_memory} KB) → Block {blk.block_id} "
            f"[{blk.start}K–{blk.end}K]  ({self.sim.strategy.value})", C.GREEN))
        self._print_map()

    def _cmd_free(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: free <pid>")
            return
        pid = args[0].upper()
        blk = self.sim.deallocate(pid)
        print(C.color(f"  ✔ {pid} freed from Block {blk.block_id}", C.YELLOW))
        self._print_map()

    def _cmd_processes(self, _args: List[str]) -> None:
        procs = list(self.sim.processes.values())
        if not procs:
            print("  No processes defined.")
            return
        header = (f"  {'PID':<6}  {'Name':<20}  {'Size':>6}  "
                  f"{'Block':>5}  {'Status':<12}  {'Allocated At'}")
        sep    = "  " + "─" * 65
        print(header)
        print(sep)
        for p in procs:
            blk_str  = str(p.block_id) if p.block_id is not None else "–"
            alloc_t  = p.allocated_at.strftime("%H:%M:%S") if p.allocated_at else "–"
            status   = (C.color("ALLOCATED", C.CYAN) if p.is_allocated
                        else C.color("WAITING",   C.GREY))
            print(f"  {p.process_id:<6}  {p.name:<20}  {p.required_memory:>5}K  "
                  f"{blk_str:>5}  {status:<21}  {alloc_t}")

    def _cmd_strategy(self, args: List[str]) -> None:
        if not args:
            options = " | ".join(s.value for s in Strategy)
            self._err(f"Usage: strategy <{options}>")
            return
        choice = args[0].lower()
        mapping = {
            "first": Strategy.FIRST_FIT,
            "firstfit": Strategy.FIRST_FIT,
            "first_fit": Strategy.FIRST_FIT,
            "best":  Strategy.BEST_FIT,
            "bestfit": Strategy.BEST_FIT,
            "best_fit": Strategy.BEST_FIT,
            "worst": Strategy.WORST_FIT,
            "worstfit": Strategy.WORST_FIT,
            "worst_fit": Strategy.WORST_FIT,
        }
        strat = mapping.get(choice)
        if strat is None:
            self._err(f"Unknown strategy '{args[0]}'. Choose: first | best | worst")
            return
        self.sim.set_strategy(strat)
        print(C.color(f"  ✔ Strategy set to: {strat.value}", C.GREEN))

    def _cmd_history(self, args: List[str]) -> None:
        n = self._parse_int(args[0], "n") if args else 15
        if not self.sim.history:
            print("  No events yet.")
            return
        print(_history_table(self.sim.history, last_n=n))

    def _cmd_summary(self, _args: List[str]) -> None:
        s  = self.sim.summary()
        mm = self.sim.mm.status_report()
        print()
        print(C.color("  ── Simulation Summary ────────────────────────────────", C.BOLD))
        for k, v in {**s, **mm}.items():
            label = k.replace("_", " ").title()
            print(f"  {label:<26} {v}")
        print()

    def _cmd_reset(self, _args: List[str]) -> None:
        self.sim = self._build_sim()
        print(C.color("  ✔ Simulation reset to initial state.", C.YELLOW))
        self._print_status()

    def _cmd_demo(self, _args: List[str]) -> None:
        """Run a built-in demonstration across all three strategies."""
        print(C.color("\n  ══ DEMO: Running all three strategies ══", C.BOLD, C.MAGENTA))
        sizes = [200, 75, 150, 300, 50, 120]
        for strat in Strategy:
            print(C.color(f"\n  ─── {strat.value} ───", C.BOLD, C.CYAN))
            self.sim = self._build_sim()
            self.sim.set_strategy(strat)
            for s in sizes:
                p = self.sim.create_process(s)
                try:
                    blk = self.sim.allocate(p.process_id)
                    print(f"  {p.process_id} ({s:>3} KB) → Block {blk.block_id:>2} "
                          f"[{blk.start:>4}K–{blk.end:<4}K]")
                except AllocationError as e:
                    print(C.color(f"  FAIL: {e}", C.RED))
                time.sleep(0.05)

            rpt = self.sim.mm.status_report()
            print(f"\n  Utilisation : {rpt['utilisation_pct']}%")
            print(f"  Free memory : {rpt['free_memory']} KB  "
                  f"({rpt['free_blocks']} free block(s))")
            print(f"  Largest free: {rpt['largest_free_block']} KB")
            print(f"  Fragmentation index: {rpt['fragmentation_idx']}")
            print(f"\n  Memory Map:")
            print(f"  {_memory_map(self.sim.mm.blocks, self.sim.mm.total_memory)}")

        # Restore a fresh sim for interactive use
        self.sim = self._build_sim()
        print(C.color("\n  Demo complete. Simulator reset.", C.YELLOW))

    def _cmd_help(self, _args: List[str]) -> None:
        print(textwrap.dedent("""\

         ┌──────────────────────────────────────────────────────────────┐
         │                   Available Commands                         │
         ├──────────────────────────────┬───────────────────────────────┤
         │  status                      │ Memory map + block table      │
         │  create <KB> [name] [pid]    │ Define a new process          │
         │  alloc  <pid>                │ Allocate memory for a process │
         │  free   <pid>                │ Deallocate process memory     │
         │  processes                   │ List all processes            │
         │  strategy first|best|worst   │ Choose placement strategy     │
         │  history [n]                 │ Show last n events (def. 15)  │
         │  summary                     │ Simulation statistics         │
         │  reset                       │ Reset everything              │
         │  demo                        │ Run built-in demo             │
         │  help                        │ This help message             │
         │  exit / quit                 │ Leave the simulator           │
         └──────────────────────────────┴───────────────────────────────┘

         Strategies explained:
           First Fit  – allocates the FIRST block large enough
           Best Fit   – allocates the SMALLEST sufficient block
           Worst Fit  – allocates the LARGEST available block

         Example session:
           strategy best
           create 200 WebServer P1
           create 100 Database  P2
           alloc P1
           alloc P2
           free  P1
           status
        """))

    def _cmd_exit(self, _args: List[str]) -> None:
        print("  Goodbye! 👋")
        self._running = False

    # ── display helpers ───────────────────────────────────────────────────────

    def _print_status(self) -> None:
        mm  = self.sim.mm
        rpt = mm.status_report()
        print()
        print(C.color("  ── Memory Status ─────────────────────────────────────", C.BOLD))
        print(f"  Total  : {rpt['total_memory']:>6} KB")
        print(f"  Used   : {rpt['allocated_memory']:>6} KB  "
              + _bar(rpt['allocated_memory'], rpt['total_memory']))
        print(f"  Free   : {rpt['free_memory']:>6} KB  "
              f"({rpt['free_blocks']} block(s), largest = {rpt['largest_free_block']} KB)")
        print(f"  Strategy: {self.sim.strategy.value}")
        print()
        print(f"  Memory Map (1 char ≈ {mm.total_memory // 60} KB):")
        print(f"  {_memory_map(mm.blocks, mm.total_memory)}")
        print()
        print(_block_table(mm.blocks))
        print()

    def _print_map(self) -> None:
        mm = self.sim.mm
        print(f"  {_memory_map(mm.blocks, mm.total_memory)}")

    # ── input validation ──────────────────────────────────────────────────────
    @staticmethod
    def _parse_int(value: str, label: str) -> int:
        try:
            n = int(value)
        except ValueError:
            raise InvalidInputError(f"'{label}' must be an integer, got '{value}'.")
        if n <= 0:
            raise InvalidInputError(f"'{label}' must be > 0.")
        return n

    @staticmethod
    def _err(msg: str) -> None:
        print(C.color(f"  Error: {msg}", C.RED))


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":

    Shell().run()