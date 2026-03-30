"""
buffer_overflow_simulator.py

An educational simulation of buffer overflow vulnerabilities.
Demonstrates safe vs unsafe memory writes in a controlled Python environment.
No real system memory is accessed or corrupted — everything is simulated.

Run in PyCharm with "Emulate terminal in output console" enabled for colours.
"""

from __future__ import annotations

import os
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ══════════════════════════════════════════════════════════════════════
# ANSI colour helpers
# ══════════════════════════════════════════════════════════════════════

def _ansi_ok() -> bool:
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True

_CLR = _ansi_ok()

class C:
    RESET  = "\033[0m"  if _CLR else ""
    BOLD   = "\033[1m"  if _CLR else ""
    RED    = "\033[91m" if _CLR else ""
    GREEN  = "\033[92m" if _CLR else ""
    YELLOW = "\033[93m" if _CLR else ""
    BLUE   = "\033[94m" if _CLR else ""
    MAGENTA= "\033[95m" if _CLR else ""
    CYAN   = "\033[96m" if _CLR else ""
    WHITE  = "\033[97m" if _CLR else ""
    GREY   = "\033[90m" if _CLR else ""
    BG_RED = "\033[41m" if _CLR else ""
    BG_GRN = "\033[42m" if _CLR else ""
    BG_YLW = "\033[43m" if _CLR else ""

def red(s):     return f"{C.RED}{s}{C.RESET}"
def green(s):   return f"{C.GREEN}{s}{C.RESET}"
def yellow(s):  return f"{C.YELLOW}{s}{C.RESET}"
def blue(s):    return f"{C.BLUE}{s}{C.RESET}"
def cyan(s):    return f"{C.CYAN}{s}{C.RESET}"
def magenta(s): return f"{C.MAGENTA}{s}{C.RESET}"
def grey(s):    return f"{C.GREY}{s}{C.RESET}"
def bold(s):    return f"{C.BOLD}{s}{C.RESET}"
def white(s):   return f"{C.WHITE}{s}{C.RESET}"
def bg_red(s):  return f"{C.BG_RED}{C.WHITE}{s}{C.RESET}"
def bg_grn(s):  return f"{C.BG_GRN}{C.WHITE}{s}{C.RESET}"
def bg_ylw(s):  return f"{C.BG_YLW}{C.WHITE}{s}{C.RESET}"


# ══════════════════════════════════════════════════════════════════════
# Enumerations
# ══════════════════════════════════════════════════════════════════════

class WriteStatus(str, Enum):
    SUCCESS   = "SUCCESS"
    OVERFLOW  = "OVERFLOW"
    TRUNCATED = "TRUNCATED"
    REJECTED  = "REJECTED"

class MemoryRegionType(str, Enum):
    STACK        = "STACK"
    HEAP         = "HEAP"
    CODE_SEGMENT = "CODE"
    DATA_SEGMENT = "DATA"


# ══════════════════════════════════════════════════════════════════════
# SimulatedMemoryRegion  — adjacent "memory" that can be overwritten
# ══════════════════════════════════════════════════════════════════════

class SimulatedMemoryRegion:
    """
    Represents a region of simulated adjacent memory (e.g. return address,
    saved frame pointer, local variables) that sits next to the buffer.
    """

    def __init__(
        self,
        name: str,
        region_type: MemoryRegionType,
        original_value: str,
        base_address: int,
    ) -> None:
        self.name           = name
        self.region_type    = region_type
        self.original_value = original_value
        self.current_value  = original_value
        self.base_address   = base_address
        self.corrupted      = False

    def overwrite(self, data: str) -> None:
        self.current_value = data[:len(self.original_value)]  # same width
        self.corrupted     = (self.current_value != self.original_value)

    def restore(self) -> None:
        self.current_value = self.original_value
        self.corrupted     = False

    def display(self) -> str:
        addr = hex(self.base_address)
        if self.corrupted:
            val  = bg_red(f" {self.current_value:<20} ")
            flag = red("  ← CORRUPTED")
        else:
            val  = bg_grn(f" {self.current_value:<20} ")
            flag = green("  ✓ intact")
        return (
            f"    {grey(addr):<16} {cyan(f'{self.name:<22}')}"
            f" {grey(self.region_type.value):<8} {val}{flag}"
        )


# ══════════════════════════════════════════════════════════════════════
# MemoryBuffer
# ══════════════════════════════════════════════════════════════════════

class MemoryBuffer:
    """
    Simulates a fixed-size memory buffer on the stack.

    Attributes
    ----------
    name         : label for this buffer (e.g. "username_buf")
    max_capacity : allocated size in bytes
    content      : current byte-string content of the buffer
    base_address : simulated starting memory address
    """

    def __init__(
        self,
        name: str,
        max_capacity: int,
        base_address: Optional[int] = None,
    ) -> None:
        if not name.strip():
            raise ValueError("Buffer name must not be empty.")
        if max_capacity < 1:
            raise ValueError("Buffer capacity must be at least 1 byte.")

        self.name         = name.strip()
        self.max_capacity = max_capacity
        self.content      = bytearray(max_capacity)   # zero-initialised
        self.base_address = base_address or random.randint(0xBF_FF_0000, 0xBF_FF_F000)
        self._write_count = 0

    # ── properties ───────────────────────────────────────────────────

    @property
    def size(self) -> int:
        """Number of bytes currently written (up to first null terminator)."""
        try:
            return self.content.index(0)
        except ValueError:
            return self.max_capacity

    @property
    def is_full(self) -> bool:
        return self.size >= self.max_capacity

    @property
    def free_bytes(self) -> int:
        return max(0, self.max_capacity - self.size)

    @property
    def utilisation(self) -> float:
        return self.size / self.max_capacity

    # ── operations ───────────────────────────────────────────────────

    def clear(self) -> None:
        """Zero out the buffer."""
        self.content = bytearray(self.max_capacity)

    def safe_write(self, data: str) -> tuple[WriteStatus, int]:
        """
        Bounds-checked write — truncates if data exceeds capacity.
        Returns (status, bytes_written).
        """
        encoded = data.encode("latin-1", errors="replace")
        if len(encoded) == 0:
            return WriteStatus.SUCCESS, 0

        if len(encoded) <= self.max_capacity:
            self.content = bytearray(self.max_capacity)
            self.content[: len(encoded)] = encoded
            self._write_count += 1
            return WriteStatus.SUCCESS, len(encoded)
        else:
            truncated = encoded[: self.max_capacity]
            self.content = bytearray(truncated)
            self._write_count += 1
            return WriteStatus.TRUNCATED, self.max_capacity

    def unsafe_write(self, data: str) -> tuple[WriteStatus, int, bytes]:
        """
        Bounds-UNCHECKED write — simulates strcpy / gets behaviour.
        Returns (status, bytes_written, overflow_bytes).
        """
        encoded = data.encode("latin-1", errors="replace")
        if len(encoded) <= self.max_capacity:
            self.content = bytearray(self.max_capacity)
            self.content[: len(encoded)] = encoded
            self._write_count += 1
            return WriteStatus.SUCCESS, len(encoded), b""
        else:
            # Fill buffer completely, return the spill
            self.content = bytearray(encoded[: self.max_capacity])
            overflow     = encoded[self.max_capacity :]
            self._write_count += 1
            return WriteStatus.OVERFLOW, len(encoded), overflow

    # ── display ──────────────────────────────────────────────────────

    def hex_dump(self, cols: int = 16) -> str:
        lines = [f"    {grey('Offset')}  {grey('Hex bytes'.ljust(cols*3-1))}  {grey('ASCII')}"]
        for i in range(0, self.max_capacity, cols):
            chunk = self.content[i : i + cols]
            hex_part = " ".join(
                (red if b != 0 else grey)(f"{b:02x}") for b in chunk
            )
            asc_part = "".join(
                (red if b != 0 else grey)(chr(b) if 32 <= b < 127 else ".")
                for b in chunk
            )
            lines.append(
                f"    {grey(f'{i:04x}')}    {hex_part:<{cols*3-1}}  {asc_part}"
            )
        return "\n".join(lines)

    def visual_bar(self, width: int = 40) -> str:
        filled = int(self.utilisation * width)
        bar    = "█" * filled + "░" * (width - filled)
        colour = green if self.utilisation < 0.7 else (
                 yellow if self.utilisation < 1.0 else red)
        return (
            f"  [{colour(bar)}] "
            f"{colour(f'{self.size}/{self.max_capacity} bytes')} "
            f"({colour(f'{self.utilisation*100:.0f}%')})"
        )

    def __str__(self) -> str:
        return (
            f"{cyan(self.name)} @ {grey(hex(self.base_address))} "
            f"cap={white(str(self.max_capacity))}B "
            f"used={white(str(self.size))}B"
        )


# ══════════════════════════════════════════════════════════════════════
# Process
# ══════════════════════════════════════════════════════════════════════

class Process:
    """
    Simulates a running process with a stack containing one MemoryBuffer
    and several adjacent memory regions (return address, saved registers, etc.)
    """

    # Typical stack layout (high → low address):  ret_addr | saved_rbp | locals | buffer
    _REGION_TEMPLATES = [
        ("return_address",  MemoryRegionType.STACK,        "0xdeadbeef"),
        ("saved_rbp",       MemoryRegionType.STACK,        "0xcafebabe"),
        ("saved_rsi",       MemoryRegionType.STACK,        "0x00000000"),
        ("local_var_auth",  MemoryRegionType.DATA_SEGMENT, "0x00000000"),  # auth flag
        ("canary_value",    MemoryRegionType.STACK,        "0x12345678"),
    ]

    def __init__(self, name: str, buffer: MemoryBuffer) -> None:
        if not name.strip():
            raise ValueError("Process name must not be empty.")
        self.name    = name.strip()
        self.pid     = random.randint(1000, 9999)
        self.buffer  = buffer
        self._build_adjacent_regions()

    def _build_adjacent_regions(self) -> None:
        """Lay out adjacent simulated memory regions just above the buffer."""
        addr  = self.buffer.base_address + self.buffer.max_capacity
        self.adjacent_regions: list[SimulatedMemoryRegion] = []
        for rname, rtype, rval in self._REGION_TEMPLATES:
            self.adjacent_regions.append(
                SimulatedMemoryRegion(rname, rtype, rval, addr)
            )
            addr += 8   # each region is 8 bytes wide (64-bit word)

    def reset(self) -> None:
        """Restore buffer and all adjacent regions to pristine state."""
        self.buffer.clear()
        for region in self.adjacent_regions:
            region.restore()

    def _apply_overflow(self, overflow_bytes: bytes) -> None:
        """
        Simulate overflow bytes spilling into adjacent regions in order.
        Each region 'absorbs' up to len(original_value) bytes of overflow.
        """
        spill = overflow_bytes
        for region in self.adjacent_regions:
            if not spill:
                break
            chunk        = spill[: len(region.original_value)].decode("latin-1", errors="replace")
            spill        = spill[len(region.original_value) :]
            region.overwrite(chunk)

    def write(self, data: str, safe: bool) -> "WriteResult":
        if safe:
            status, n_written = self.buffer.safe_write(data)
            overflow_bytes    = b""
        else:
            status, n_written, overflow_bytes = self.buffer.unsafe_write(data)
            if overflow_bytes:
                self._apply_overflow(overflow_bytes)

        return WriteResult(
            process_name  = self.name,
            pid           = self.pid,
            input_data    = data,
            input_length  = len(data.encode("latin-1", errors="replace")),
            buffer_cap    = self.buffer.max_capacity,
            status        = status,
            bytes_written = n_written,
            overflow_len  = len(overflow_bytes),
            safe_mode     = safe,
            timestamp     = datetime.now(),
        )

    def stack_layout(self) -> str:
        W = 60
        sep   = grey("│")
        lines = [
            grey("  ┌" + "─" * W + "┐"),
            f"  {sep}  {bold('STACK FRAME')} — {cyan(self.name)} (PID {white(str(self.pid))})".ljust(W + 12) + f"  {sep}",
            grey("  ├" + "─" * W + "┤"),
        ]
        for region in reversed(self.adjacent_regions):
            tag = (bg_red if region.corrupted else bg_grn)(f" {region.current_value:<14} ")
            lbl = f"  {sep}  {red('▲') if region.corrupted else green('▲')}  {cyan(region.name):<22} {tag}"
            lines.append(lbl.ljust(W + 20) + f"  {sep}")

        lines.append(grey("  ├" + "─" * W + "┤  ← buffer ends here"))
        # Buffer rows
        content_str = self.buffer.content.decode("latin-1", errors="replace")
        for i in range(0, self.buffer.max_capacity, 16):
            chunk = content_str[i : i + 16]
            coloured = "".join(
                (red if c != "\x00" else grey)(c if c.isprintable() and c != "\x00" else ".")
                for c in chunk
            )
            offset = grey(f"+{i:04x}")
            lines.append(f"  {sep}  {offset}  {cyan(self.buffer.name):<18} [{coloured:<16}]  {sep}")

        lines.append(grey("  └" + "─" * W + "┘"))
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# WriteResult
# ══════════════════════════════════════════════════════════════════════

@dataclass
class WriteResult:
    process_name : str
    pid          : int
    input_data   : str
    input_length : int
    buffer_cap   : int
    status       : WriteStatus
    bytes_written: int
    overflow_len : int
    safe_mode    : bool
    timestamp    : datetime = field(default_factory=datetime.now)

    @property
    def overflowed(self) -> bool:
        return self.status == WriteStatus.OVERFLOW

    def summary_line(self) -> str:
        mode = green("SAFE  ") if self.safe_mode else red("UNSAFE")
        stat_map = {
            WriteStatus.SUCCESS:   green(f"{'SUCCESS':<10}"),
            WriteStatus.OVERFLOW:  bg_red(f" {'OVERFLOW':<10}"),
            WriteStatus.TRUNCATED: yellow(f"{'TRUNCATED':<10}"),
            WriteStatus.REJECTED:  red(f"{'REJECTED':<10}"),
        }
        ovf = red(f"+{self.overflow_len}B spilled") if self.overflow_len else green("no overflow")
        return (
            f"  [{grey(self.timestamp.strftime('%H:%M:%S'))}] "
            f"Mode:{mode} "
            f"Input:{white(str(self.input_length)+'B'):<8} "
            f"Cap:{white(str(self.buffer_cap)+'B'):<8} "
            f"Status:{stat_map[self.status]} "
            f"{ovf}"
        )

    def detailed(self) -> str:
        lines = [
            f"  {grey('Process  :')} {cyan(self.process_name)} (PID {self.pid})",
            f"  {grey('Input    :')} {white(repr(self.input_data[:60]) + ('…' if len(self.input_data)>60 else ''))}",
            f"  {grey('Length   :')} {white(str(self.input_length))} bytes",
            f"  {grey('Buf cap  :')} {white(str(self.buffer_cap))} bytes",
            f"  {grey('Written  :')} {white(str(self.bytes_written))} bytes",
            f"  {grey('Mode     :')} {'bounds-checked (safe)' if self.safe_mode else red('NO bounds check (unsafe)')}",
        ]
        if self.status == WriteStatus.OVERFLOW:
            lines += [
                f"  {grey('Overflow :')} {red(str(self.overflow_len)+' bytes spilled into adjacent memory')}",
                f"  {red('⚠  Adjacent memory regions may be corrupted!')}",
            ]
        elif self.status == WriteStatus.TRUNCATED:
            lines.append(f"  {yellow('⚠  Input was truncated to fit the buffer (data loss).')}")
        else:
            lines.append(f"  {green('✓  Write completed within bounds.')}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# VulnerabilitySimulator
# ══════════════════════════════════════════════════════════════════════

class VulnerabilitySimulator:
    """
    Core educational engine.
    Demonstrates safe vs unsafe writes and explains the consequences.
    """

    EDUCATION_NOTES = {
        WriteStatus.SUCCESS: (
            "The write stayed within bounds. "
            "Proper bounds checking protects adjacent memory regions."
        ),
        WriteStatus.TRUNCATED: (
            "Input was cut off at the buffer boundary. "
            "While this prevents overflow, truncation can cause logic bugs "
            "(e.g. passwords silently shortened)."
        ),
        WriteStatus.OVERFLOW: (
            "Input exceeded the buffer capacity and bytes spilled into adjacent "
            "memory. In a real system this can overwrite the saved return address, "
            "allowing an attacker to redirect execution to arbitrary code "
            "(classic stack-smashing / EIP/RIP control)."
        ),
        WriteStatus.REJECTED: (
            "The write was rejected entirely — the safest outcome."
        ),
    }

    def __init__(self, process: Process) -> None:
        self.process    = process
        self.history: list[WriteResult] = []

    def run_safe(self, data: str) -> WriteResult:
        self.process.reset()
        result = self.process.write(data, safe=True)
        self.history.append(result)
        return result

    def run_unsafe(self, data: str) -> WriteResult:
        self.process.reset()
        result = self.process.write(data, safe=False)
        self.history.append(result)
        return result

    def compare(self, data: str) -> tuple[WriteResult, WriteResult]:
        """Run the same input through both safe and unsafe paths."""
        safe_r   = self.run_safe(data)
        unsafe_r = self.run_unsafe(data)
        return safe_r, unsafe_r

    def explain(self, result: WriteResult) -> str:
        return self.EDUCATION_NOTES.get(result.status, "No notes available.")

    def memory_map(self) -> str:
        """Render the current state of the process memory."""
        return self.process.stack_layout()

    def hex_dump(self) -> str:
        return self.process.buffer.hex_dump()

    def visual_bar(self) -> str:
        return self.process.buffer.visual_bar()


# ══════════════════════════════════════════════════════════════════════
# SimulationManager
# ══════════════════════════════════════════════════════════════════════

class SimulationManager:
    """
    Orchestrates multiple named scenarios and maintains a history
    of all write results for reporting.
    """

    def __init__(self) -> None:
        self._simulators: dict[str, VulnerabilitySimulator] = {}
        self._active_key: Optional[str] = None
        self.all_results: list[WriteResult] = []

    # ── simulator registry ───────────────────────────────────────────

    def create_simulator(
        self,
        key: str,
        buffer_name: str,
        capacity: int,
        process_name: str,
    ) -> VulnerabilitySimulator:
        buf  = MemoryBuffer(buffer_name, capacity)
        proc = Process(process_name, buf)
        sim  = VulnerabilitySimulator(proc)
        self._simulators[key] = sim
        self._active_key      = key
        return sim

    def get_simulator(self, key: Optional[str] = None) -> VulnerabilitySimulator:
        k = key or self._active_key
        if k is None or k not in self._simulators:
            raise KeyError(f"Simulator '{k}' not found.")
        return self._simulators[k]

    def list_simulators(self) -> list[str]:
        return list(self._simulators.keys())

    def set_active(self, key: str) -> None:
        if key not in self._simulators:
            raise KeyError(f"Simulator '{key}' not found.")
        self._active_key = key

    # ── scenario runners ─────────────────────────────────────────────

    def run_scenario(
        self,
        data: str,
        safe: bool,
        key: Optional[str] = None,
    ) -> WriteResult:
        sim = self.get_simulator(key)
        result = sim.run_safe(data) if safe else sim.run_unsafe(data)
        self.all_results.append(result)
        return result

    def run_comparison(
        self,
        data: str,
        key: Optional[str] = None,
    ) -> tuple[WriteResult, WriteResult]:
        sim = self.get_simulator(key)
        safe_r, unsafe_r = sim.compare(data)
        self.all_results.extend([safe_r, unsafe_r])
        return safe_r, unsafe_r

    # ── reporting ────────────────────────────────────────────────────

    def summary_report(self) -> str:
        if not self.all_results:
            return "  No results recorded yet."
        sep = "═" * 68
        lines = [
            sep,
            bold("  BUFFER OVERFLOW SIMULATION — SESSION SUMMARY"),
            grey(f"  Generated: {datetime.now():%Y-%m-%d %H:%M:%S}"),
            sep,
            f"  Total operations : {white(str(len(self.all_results)))}",
            f"  Overflows        : {red(str(sum(1 for r in self.all_results if r.overflowed)))}",
            f"  Safe writes      : {green(str(sum(1 for r in self.all_results if r.status==WriteStatus.SUCCESS)))}",
            f"  Truncations      : {yellow(str(sum(1 for r in self.all_results if r.status==WriteStatus.TRUNCATED)))}",
            "",
        ]
        for i, r in enumerate(self.all_results, 1):
            lines.append(f"  {grey(str(i)+'.')} {r.summary_line()}")
        lines.append(sep)
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# UI helpers
# ══════════════════════════════════════════════════════════════════════

W = 68

def _hr(char="─"):   print(grey(char * W))
def _title(t: str):
    print(f"\n{bold(cyan(t))}")
    _hr()

def _ok(msg):   print(f"  {green('✓')} {msg}")
def _err(msg):  print(f"  {red('✗')} {msg}")
def _info(msg): print(f"  {blue('ℹ')} {msg}")
def _warn(msg): print(f"  {yellow('⚠')} {msg}")

def _prompt(msg: str) -> str:
    try:
        return input(f"\n{cyan('?')} {msg} {grey('›')} ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""

def _pause():
    try:
        input(f"\n  {grey('Press Enter to continue…')}")
    except (EOFError, KeyboardInterrupt):
        pass

def _render_result(result: WriteResult, sim: VulnerabilitySimulator) -> None:
    """Full educational render of a single write result."""
    print()
    _hr("─")
    print(result.detailed())
    _hr("─")

    print(f"\n  {bold('Buffer fill:')}")
    print(sim.visual_bar())

    print(f"\n  {bold('Hex dump of buffer:')}")
    print(sim.hex_dump())

    print(f"\n  {bold('Stack / memory layout:')}")
    print(sim.memory_map())

    print(f"\n  {bold(cyan('Educational note:'))}")
    note = sim.explain(result)
    for line in note.split(". "):
        if line.strip():
            print(f"  {grey('→')} {line.strip()}.")

    print()


# ══════════════════════════════════════════════════════════════════════
# Menu actions
# ══════════════════════════════════════════════════════════════════════

def action_new_simulator(mgr: SimulationManager) -> None:
    _title("Create New Simulator")
    key   = _prompt("Simulator name (e.g. login_form)")
    if not key:
        _err("Name required."); return

    bname = _prompt("Buffer name (e.g. username_buf)") or "buffer"
    cap_s = _prompt("Buffer capacity in bytes (e.g. 16)")
    try:
        cap = int(cap_s)
        if cap < 1: raise ValueError
    except ValueError:
        _err("Capacity must be a positive integer."); return

    pname = _prompt("Process name (e.g. login_server)") or "process"
    try:
        sim = mgr.create_simulator(key, bname, cap, pname)
        _ok(f"Simulator '{key}' created — buffer {sim.process.buffer}")
    except ValueError as e:
        _err(str(e))


def action_list_simulators(mgr: SimulationManager) -> None:
    _title("Simulators")
    keys = mgr.list_simulators()
    if not keys:
        _info("No simulators yet. Create one first."); return
    for k in keys:
        sim  = mgr._simulators[k]
        proc = sim.process
        mark = cyan(" ← active") if k == mgr._active_key else ""
        print(f"  {grey('•')} {white(k)}{mark}")
        print(f"      Process : {cyan(proc.name)} PID {proc.pid}")
        print(f"      Buffer  : {proc.buffer}")


def action_select_simulator(mgr: SimulationManager) -> None:
    _title("Select Active Simulator")
    keys = mgr.list_simulators()
    if not keys:
        _info("No simulators available."); return
    for i, k in enumerate(keys, 1):
        print(f"  {grey(str(i)+'.')} {white(k)}")
    choice = _prompt(f"Select [1-{len(keys)}]")
    try:
        idx = int(choice) - 1
        if not (0 <= idx < len(keys)): raise ValueError
        mgr.set_active(keys[idx])
        _ok(f"Active simulator: {keys[idx]}")
    except ValueError:
        _err("Invalid selection.")


def action_safe_write(mgr: SimulationManager) -> None:
    _title("Safe Write (bounds-checked)")
    _info("Simulates a C-style strncpy / snprintf — input is clamped to buffer size.")
    try:
        sim = mgr.get_simulator()
    except KeyError as e:
        _err(str(e)); return

    data = _prompt("Enter input string")
    result = mgr.run_scenario(data, safe=True)
    _render_result(result, sim)


def action_unsafe_write(mgr: SimulationManager) -> None:
    _title("Unsafe Write (NO bounds check)")
    _warn("Simulates a vulnerable C-style strcpy / gets — no length limit enforced.")
    try:
        sim = mgr.get_simulator()
    except KeyError as e:
        _err(str(e)); return

    data = _prompt("Enter input string (try something longer than the buffer!)")
    result = mgr.run_scenario(data, safe=False)
    _render_result(result, sim)

    if result.overflowed:
        print(f"  {bg_red('  OVERFLOW DETECTED  ')}")
        print(f"\n  {red('Adjacent memory was corrupted:')}")
        for region in sim.process.adjacent_regions:
            if region.corrupted:
                print(f"  {red('▶')} {region.display()}")
        _warn(
            "In a real exploit the 'return_address' field above would be replaced\n"
            "  with an attacker-controlled value, redirecting execution to shellcode."
        )


def action_compare(mgr: SimulationManager) -> None:
    _title("Side-by-Side Comparison: Safe vs Unsafe")
    try:
        sim = mgr.get_simulator()
    except KeyError as e:
        _err(str(e)); return

    data = _prompt("Enter input string to test both paths")
    safe_r, unsafe_r = mgr.run_comparison(data)

    print(f"\n  {'─'*30} SAFE PATH {'─'*28}")
    print(safe_r.detailed())
    print(f"  {bold(cyan('Note:'))} {sim.explain(safe_r)}")

    print(f"\n  {'─'*29} UNSAFE PATH {'─'*27}")
    print(unsafe_r.detailed())
    print(f"  {bold(red('Note:'))} {sim.explain(unsafe_r)}")

    if unsafe_r.overflowed and not safe_r.overflowed:
        print(f"\n  {bg_red('  KEY TAKEAWAY  ')}")
        print(
            f"  {red('The same input caused NO overflow with bounds checking,')}\n"
            f"  {red('but CORRUPTED adjacent memory without it.')}\n"
            f"  {yellow('→ Always validate input length before writing to a buffer.')}"
        )


def action_auto_overflow(mgr: SimulationManager) -> None:
    _title("Automatic Overflow Demo (pre-built payloads)")
    try:
        sim = mgr.get_simulator()
    except KeyError as e:
        _err(str(e)); return

    cap = sim.process.buffer.max_capacity
    payloads = [
        ("Exact fit",           "A" * cap),
        ("1 byte over",         "A" * (cap + 1)),
        ("8 bytes over",        "A" * (cap + 8)),
        ("Full overflow",       "A" * (cap + 40)),
        ("Shellcode marker",    "A" * cap + "\\x90\\x90\\xeb\\x18\\x31\\xc0"),
        ("Return addr spoof",   "A" * cap + "BBBBBBBB"),  # overwrites ret addr
    ]

    print(f"  Buffer capacity: {white(str(cap))} bytes\n")
    for i, (label, payload) in enumerate(payloads, 1):
        print(f"  {grey(str(i)+'.')} {label:<25} ({len(payload)} bytes)")

    choice = _prompt(f"Select payload [1-{len(payloads)}]")
    try:
        idx   = int(choice) - 1
        label, payload = payloads[idx]
    except (ValueError, IndexError):
        _err("Invalid selection."); return

    _info(f"Payload: {label} — {len(payload)} bytes — unsafe write")
    result = mgr.run_scenario(payload, safe=False)
    _render_result(result, sim)


def action_education_mode(mgr: SimulationManager) -> None:
    _title("Educational Walkthrough")
    cap = 12
    _info("Creating a fresh simulator: buffer=12B, process='vulnerable_app'")
    mgr.create_simulator("edu_demo", "input_buf", cap, "vulnerable_app")
    sim = mgr.get_simulator("edu_demo")

    steps = [
        (
            "Step 1 — Normal safe input",
            "Hello",
            True,
            "A short string well within the 12-byte buffer. No issues.",
        ),
        (
            "Step 2 — Safe input at the boundary",
            "A" * cap,
            True,
            "Exactly fills the buffer. Still safe.",
        ),
        (
            "Step 3 — Unsafe input within limits",
            "Hello",
            False,
            "Unsafe write but data fits, so no overflow occurs here.",
        ),
        (
            "Step 4 — Unsafe overflow (the dangerous case)",
            "A" * cap + "BBBBBBBB",
            False,
            "8 extra bytes spill past the buffer and overwrite adjacent memory.",
        ),
        (
            "Step 5 — Exploiting the overflow (return address control)",
            "A" * cap + "\\xef\\xbe\\xad\\xde",
            False,
            "Attacker replaces the return address with 0xdeadbeef — code hijacked.",
        ),
    ]

    for step_label, payload, safe, explanation in steps:
        print(f"\n  {bold(yellow(step_label))}")
        print(f"  {grey(explanation)}")
        print(f"  Input  : {repr(payload)}")
        print(f"  Mode   : {'safe (strncpy)' if safe else red('UNSAFE (strcpy)')}")

        result = sim.run_safe(payload) if safe else sim.run_unsafe(payload)
        mgr.all_results.append(result)

        print(f"  Status : {result.summary_line()}")
        print(f"  Buffer : {sim.visual_bar()}")

        if result.overflowed:
            print(f"\n  {red('Adjacent regions after overflow:')}")
            for region in sim.process.adjacent_regions:
                print(f"  {region.display()}")

        print(f"\n  {cyan('→')} {sim.explain(result)}")
        _pause()


def action_view_results(mgr: SimulationManager) -> None:
    _title("Session History")
    if not mgr.all_results:
        _info("No results recorded yet."); return
    for i, r in enumerate(mgr.all_results, 1):
        print(f"  {grey(str(i)+'.')} {r.summary_line()}")


def action_report(mgr: SimulationManager) -> None:
    _title("Session Report")
    print(mgr.summary_report())


def action_reset(mgr: SimulationManager) -> None:
    _title("Reset Active Simulator")
    try:
        sim = mgr.get_simulator()
        sim.process.reset()
        _ok("Buffer and adjacent memory restored to pristine state.")
    except KeyError as e:
        _err(str(e))


# ══════════════════════════════════════════════════════════════════════
# Main menu loop
# ══════════════════════════════════════════════════════════════════════

MENU = [
    ("Create new simulator",                  action_new_simulator),
    ("List simulators",                       action_list_simulators),
    ("Select active simulator",               action_select_simulator),
    ("Safe write  (bounds-checked)",          action_safe_write),
    ("Unsafe write  (NO bounds check)",       action_unsafe_write),
    ("Side-by-side comparison",               action_compare),
    ("Auto overflow demo  (payloads)",        action_auto_overflow),
    ("Educational walkthrough  (guided)",     action_education_mode),
    ("View session history",                  action_view_results),
    ("Generate session report",               action_report),
    ("Reset active simulator",                action_reset),
    ("Exit",                                  None),
]

def _banner() -> None:
    print(bold(red("═" * W)))
    print(bold(red("  BUFFER OVERFLOW SIMULATOR  —  Educational Console")))
    print(grey("  All memory operations are SIMULATED. No real memory is modified."))
    print(bold(red("═" * W)))
    print(f"\n  {yellow('What is a buffer overflow?')}")
    print(grey(
        "  A buffer overflow occurs when a program writes more data to a\n"
        "  fixed-size buffer than it can hold, overwriting adjacent memory.\n"
        "  This is one of the oldest and most exploited vulnerability classes."
    ))


def _status_bar(mgr: SimulationManager) -> None:
    try:
        sim     = mgr.get_simulator()
        proc    = sim.process
        buf     = proc.buffer
        active  = white(mgr._active_key or "none")
        filled  = f"{buf.size}/{buf.max_capacity}B"
        corrupted = sum(1 for r in proc.adjacent_regions if r.corrupted)
        cor_str = (red(f"{corrupted} corrupted") if corrupted else green("0 corrupted"))
    except KeyError:
        active, filled, cor_str = grey("none"), grey("—"), grey("—")

    total_ovf = sum(1 for r in mgr.all_results if r.overflowed)
    print(
        f"\n  {grey('Simulator:')} {active}  "
        f"{grey('Buffer:')} {white(filled)}  "
        f"{grey('Adjacent mem:')} {cor_str}  "
        f"{grey('Total overflows:')} {(red if total_ovf else green)(str(total_ovf))}"
    )


def main() -> None:
    _banner()
    mgr = SimulationManager()

    # Create a default simulator so users can start immediately
    mgr.create_simulator("default", "input_buf", 16, "target_process")
    _ok("Default simulator ready: buffer=16B, process='target_process'")

    while True:
        _status_bar(mgr)
        _hr()

        for i, (label, _) in enumerate(MENU, 1):
            num = grey(f"{i:>2}.")
            if i == len(MENU):
                print(f"  {num} {red(label)}")
            elif "unsafe" in label.lower() or "overflow" in label.lower():
                print(f"  {num} {yellow(label)}")
            elif "educational" in label.lower() or "walkthrough" in label.lower():
                print(f"  {num} {magenta(label)}")
            else:
                print(f"  {num} {label}")

        choice = _prompt(f"Select option [1-{len(MENU)}]")

        try:
            idx = int(choice) - 1
            if not (0 <= idx < len(MENU)):
                raise ValueError
        except ValueError:
            _err(f"Enter a number between 1 and {len(MENU)}."); continue

        _, handler = MENU[idx]
        if handler is None:
            print(f"\n{cyan('  Goodbye!')} Stay secure.\n"); break

        try:
            handler(mgr)
        except KeyboardInterrupt:
            _info("Interrupted.")
        except Exception as exc:
            _err(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()