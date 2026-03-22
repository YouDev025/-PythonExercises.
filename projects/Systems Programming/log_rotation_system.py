"""
log_rotation_system.py
A simulated log rotation manager built with Python OOP.
Supports size-based and time-based rotation policies, archiving,
backup pruning, and a rich command-line interface.
"""

from __future__ import annotations

import gzip
import math
import random
import re
import shutil
import string
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ══════════════════════════════════════════════════════════════════════════════
# ANSI helpers
# ══════════════════════════════════════════════════════════════════════════════

def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"

def _ok  (msg: str) -> None: print(_c(f"  ✔  {msg}", "32"))
def _err (msg: str) -> None: print(_c(f"  ✘  {msg}", "31"))
def _info(msg: str) -> None: print(_c(f"  ℹ  {msg}", "36"))
def _warn(msg: str) -> None: print(_c(f"  ⚠  {msg}", "33"))
def _head(msg: str) -> None: print(_c(msg, "1;34"))
def _dim (msg: str) -> None: print(_c(msg, "2"))


# ══════════════════════════════════════════════════════════════════════════════
# Enums & Exceptions
# ══════════════════════════════════════════════════════════════════════════════

class RotationType(Enum):
    SIZE_BASED = "size"
    TIME_BASED = "time"
    HYBRID     = "hybrid"      # rotate on EITHER condition


class CompressionFormat(Enum):
    NONE = "none"
    GZIP = "gz"


class LogRotationError(Exception):
    """Base exception for all log-rotation errors."""

class LogFileNotFoundError(LogRotationError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Log file '{name}' is not registered.")

class LogFileAlreadyExistsError(LogRotationError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Log file '{name}' is already registered.")

class RotationError(LogRotationError):
    pass

class ValidationError(LogRotationError):
    pass


# ══════════════════════════════════════════════════════════════════════════════
# Utility helpers
# ══════════════════════════════════════════════════════════════════════════════

def _fmt_bytes(n: int) -> str:
    """Human-readable byte count."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def _parse_bytes(value: str) -> int:
    """Parse '10MB', '512 KB', '1 GB' → int bytes. Raises ValidationError."""
    value = value.strip().upper().replace(" ", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(B|KB|MB|GB|TB)?", value)
    if not m:
        raise ValidationError(f"Cannot parse size '{value}'. Use e.g. 10MB, 512KB, 1GB.")
    num   = float(m.group(1))
    unit  = m.group(2) or "B"
    mult  = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}[unit]
    return int(num * mult)

def _parse_interval(value: str) -> timedelta:
    """Parse '1h', '30m', '7d', '1w' → timedelta. Raises ValidationError."""
    value = value.strip().lower()
    m = re.fullmatch(r"(\d+)(s|m|h|d|w)", value)
    if not m:
        raise ValidationError(
            f"Cannot parse interval '{value}'. Use e.g. 30m, 1h, 7d, 2w."
        )
    n    = int(m.group(1))
    unit = m.group(2)
    secs = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[unit]
    return timedelta(seconds=n * secs)

def _progress_bar(current: int, maximum: int, width: int = 30) -> str:
    """Return a coloured ASCII progress bar string."""
    pct   = min(current / maximum, 1.0) if maximum else 0.0
    filled = int(pct * width)
    bar    = "█" * filled + "░" * (width - filled)
    colour = "32" if pct < 0.7 else ("33" if pct < 0.9 else "31")
    return _c(f"[{bar}]", colour) + f" {pct*100:.1f}%"


# ══════════════════════════════════════════════════════════════════════════════
# RotationPolicy
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RotationPolicy:
    """
    Defines when and how a log file should be rotated.

    Attributes
    ----------
    rotation_type   : SIZE_BASED | TIME_BASED | HYBRID
    max_size        : maximum file size in bytes  (size-based / hybrid)
    rotation_interval : rotate after this much simulated time (time-based / hybrid)
    backup_count    : how many rotated copies to keep (0 = unlimited)
    compress        : archive format applied to rotated files
    """
    rotation_type     : RotationType      = RotationType.SIZE_BASED
    max_size          : int               = 10 * 1024 * 1024   # 10 MB
    rotation_interval : timedelta         = timedelta(days=1)
    backup_count      : int               = 5
    compress          : CompressionFormat = CompressionFormat.GZIP

    # ── validation ────────────────────────────────────────────────────────────
    def __post_init__(self) -> None:
        if self.max_size < 1024:
            raise ValidationError("max_size must be ≥ 1 KB.")
        if self.backup_count < 0:
            raise ValidationError("backup_count must be ≥ 0.")

    # ── predicate ─────────────────────────────────────────────────────────────
    def should_rotate(self, log_file: "LogFile") -> Tuple[bool, str]:
        """Return (should_rotate, reason)."""
        size_ok = (
            self.rotation_type in (RotationType.SIZE_BASED, RotationType.HYBRID)
            and log_file.current_size >= self.max_size
        )
        time_ok = (
            self.rotation_type in (RotationType.TIME_BASED, RotationType.HYBRID)
            and log_file.age >= self.rotation_interval
        )
        if size_ok and time_ok:
            return True, f"size ({_fmt_bytes(log_file.current_size)}) AND interval elapsed"
        if size_ok:
            return True, f"size limit reached ({_fmt_bytes(log_file.current_size)} ≥ {_fmt_bytes(self.max_size)})"
        if time_ok:
            elapsed = str(log_file.age).split(".")[0]
            return True, f"rotation interval elapsed ({elapsed})"
        return False, ""

    def summary(self) -> str:
        compress_lbl = self.compress.value.upper() if self.compress != CompressionFormat.NONE else "none"
        parts = [f"type={self.rotation_type.value}"]
        if self.rotation_type in (RotationType.SIZE_BASED, RotationType.HYBRID):
            parts.append(f"max={_fmt_bytes(self.max_size)}")
        if self.rotation_type in (RotationType.TIME_BASED, RotationType.HYBRID):
            parts.append(f"interval={self.rotation_interval}")
        parts.append(f"backups={self.backup_count or '∞'}")
        parts.append(f"compress={compress_lbl}")
        return "  ".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# RotationRecord  (immutable archive entry)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RotationRecord:
    archive_name   : str
    original_name  : str
    rotated_at     : datetime
    original_size  : int
    compressed_size: int
    reason         : str
    sequence       : int        # 1-based rotation number for this log

    @property
    def compression_ratio(self) -> float:
        if self.original_size == 0:
            return 1.0
        return self.compressed_size / self.original_size

    def one_line(self) -> str:
        ts    = self.rotated_at.strftime("%Y-%m-%d %H:%M:%S")
        ratio = f"{self.compression_ratio*100:.0f}%" if self.compressed_size != self.original_size else "—"
        return (
            f"  #{self.sequence:<4} {ts}  {self.archive_name:<40}"
            f"  orig:{_fmt_bytes(self.original_size):<10}"
            f"  arch:{_fmt_bytes(self.compressed_size):<10}"
            f"  ratio:{ratio:<6}  {self.reason}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# LogFile
# ══════════════════════════════════════════════════════════════════════════════

class LogFile:
    """
    Represents a single monitored log file (in-memory simulation).

    Attributes
    ----------
    file_name       : logical name, e.g. 'app.log'
    current_size    : current size in bytes
    creation_date   : when this 'instance' of the log was created/last rotated
    policy          : the RotationPolicy governing this file
    rotation_records: list of past RotationRecord entries for this file
    _lines          : simulated log content (list of strings)
    """

    _VALID_RE = re.compile(r"^[\w.\-]{1,64}$")

    def __init__(self, file_name: str, policy: RotationPolicy) -> None:
        self._validate_name(file_name)
        self.file_name         : str               = file_name
        self.policy            : RotationPolicy    = policy
        self.creation_date     : datetime          = datetime.now()
        self.current_size      : int               = 0
        self._lines            : List[str]         = []
        self.rotation_records  : List[RotationRecord] = []
        self._rotation_seq     : int               = 0
        self._simulated_time   : datetime          = datetime.now()

    # ── validation ────────────────────────────────────────────────────────────
    @classmethod
    def _validate_name(cls, name: str) -> None:
        if not cls._VALID_RE.match(name):
            raise ValidationError(
                f"Invalid log file name '{name}'. "
                "Use letters, digits, dots, hyphens, underscores (max 64 chars)."
            )

    # ── time simulation ───────────────────────────────────────────────────────
    @property
    def age(self) -> timedelta:
        return self._simulated_time - self.creation_date

    def advance_time(self, delta: timedelta) -> None:
        """Advance the simulated clock for this log file."""
        self._simulated_time += delta

    # ── log writing ───────────────────────────────────────────────────────────
    def write(self, message: str) -> None:
        ts   = self._simulated_time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}\n"
        self._lines.append(line)
        self.current_size += len(line.encode())

    def write_bulk(self, n: int) -> int:
        """Write *n* random log lines; return bytes added."""
        before = self.current_size
        levels  = ["INFO", "DEBUG", "WARN", "ERROR", "CRITICAL"]
        modules = ["auth", "db", "api", "cache", "scheduler", "worker", "gateway"]
        for _ in range(n):
            lvl = random.choice(levels)
            mod = random.choice(modules)
            msg = "".join(random.choices(string.ascii_lowercase + " ", k=random.randint(20, 80)))
            self.write(f"{lvl:<8} [{mod}] {msg}")
            self.advance_time(timedelta(seconds=random.randint(1, 30)))
        return self.current_size - before

    def clear(self) -> None:
        """Reset content (called after rotation)."""
        self._lines.clear()
        self.current_size  = 0
        self.creation_date = self._simulated_time

    # ── rotation record ───────────────────────────────────────────────────────
    def add_rotation_record(self, record: RotationRecord) -> None:
        self.rotation_records.append(record)
        self._rotation_seq = record.sequence

    # ── display ───────────────────────────────────────────────────────────────
    @property
    def fill_bar(self) -> str:
        return _progress_bar(self.current_size, self.policy.max_size)

    def status_line(self) -> str:
        age_str = str(self.age).split(".")[0]
        return (
            f"  {self.file_name:<28}"
            f"  size:{_fmt_bytes(self.current_size):<12}"
            f"  {self.fill_bar}"
            f"  age:{age_str:<16}"
            f"  rotations:{self._rotation_seq}"
        )

    def detail_block(self) -> str:
        return textwrap.dedent(f"""\
            File name     : {self.file_name}
            Current size  : {_fmt_bytes(self.current_size)} / {_fmt_bytes(self.policy.max_size)}
            Created at    : {self.creation_date.strftime('%Y-%m-%d %H:%M:%S')}
            Simulated now : {self._simulated_time.strftime('%Y-%m-%d %H:%M:%S')}
            Age           : {str(self.age).split('.')[0]}
            Line count    : {len(self._lines)}
            Rotations     : {self._rotation_seq}
            Policy        : {self.policy.summary()}
        """)

    def __repr__(self) -> str:
        return f"LogFile(name={self.file_name!r}, size={_fmt_bytes(self.current_size)})"


# ══════════════════════════════════════════════════════════════════════════════
# LogRotator
# ══════════════════════════════════════════════════════════════════════════════

class LogRotator:
    """
    Monitors a single LogFile and executes rotation when the policy fires.
    Produces RotationRecord objects; does NOT manage archives or backup pruning.
    """

    def check(self, log_file: LogFile) -> Tuple[bool, str]:
        """Return (needs_rotation, reason)."""
        return log_file.policy.should_rotate(log_file)

    def rotate(self, log_file: LogFile, reason: str) -> RotationRecord:
        """
        Perform rotation:
          1. Build an archive name with timestamp + sequence number.
          2. Simulate compression (size reduction).
          3. Clear the live log file.
          4. Return a RotationRecord.
        Raises RotationError if the file is empty.
        """
        if log_file.current_size == 0:
            raise RotationError(
                f"Cannot rotate '{log_file.file_name}': file is empty."
            )

        seq       = log_file._rotation_seq + 1
        ts_str    = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext       = "." + log_file.policy.compress.value \
                    if log_file.policy.compress != CompressionFormat.NONE else ""
        archive   = f"{log_file.file_name}.{seq:04d}.{ts_str}{ext}"

        orig_size = log_file.current_size
        # Simulate compression: GZIP typically achieves ~70–90 % reduction on text
        if log_file.policy.compress == CompressionFormat.GZIP:
            ratio      = random.uniform(0.08, 0.25)
            comp_size  = max(512, int(orig_size * ratio))
        else:
            comp_size  = orig_size

        record = RotationRecord(
            archive_name    = archive,
            original_name   = log_file.file_name,
            rotated_at      = datetime.now(),
            original_size   = orig_size,
            compressed_size = comp_size,
            reason          = reason,
            sequence        = seq,
        )

        log_file.add_rotation_record(record)
        log_file.clear()
        return record


# ══════════════════════════════════════════════════════════════════════════════
# RotationManager
# ══════════════════════════════════════════════════════════════════════════════

class RotationManager:
    """
    Top-level coordinator:
      - Maintains the registry of log files.
      - Delegates rotation to LogRotator.
      - Manages the global archive store.
      - Enforces backup_count limits (pruning oldest archives).
      - Provides query / reporting methods.
    """

    def __init__(self) -> None:
        self._files  : Dict[str, LogFile]    = {}
        self._rotator: LogRotator            = LogRotator()
        self._archive: List[RotationRecord]  = []     # global archive, newest last
        self._event_log: List[str]           = []

    # ── event log ─────────────────────────────────────────────────────────────
    def _log(self, msg: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._event_log.append(f"[{ts}] {msg}")

    # ── registry ──────────────────────────────────────────────────────────────
    def register(
        self,
        file_name  : str,
        policy     : Optional[RotationPolicy] = None,
    ) -> LogFile:
        if file_name in self._files:
            raise LogFileAlreadyExistsError(file_name)
        lf = LogFile(file_name, policy or RotationPolicy())
        self._files[file_name] = lf
        self._log(f"REGISTER  {file_name}  policy=[{lf.policy.summary()}]")
        return lf

    def deregister(self, file_name: str) -> LogFile:
        lf = self._get(file_name)
        del self._files[file_name]
        self._log(f"DEREGISTER {file_name}")
        return lf

    def _get(self, name: str) -> LogFile:
        if name not in self._files:
            raise LogFileNotFoundError(name)
        return self._files[name]

    # ── write / grow ──────────────────────────────────────────────────────────
    def append_lines(self, file_name: str, n: int) -> int:
        lf    = self._get(file_name)
        added = lf.write_bulk(n)
        self._log(f"WRITE     {file_name}  +{n} lines (+{_fmt_bytes(added)})")
        return added

    def advance_time(self, file_name: str, delta: timedelta) -> None:
        lf = self._get(file_name)
        lf.advance_time(delta)
        self._log(f"TIMESKIP  {file_name}  +{delta}")

    # ── rotation ──────────────────────────────────────────────────────────────
    def rotate(self, file_name: str, *, force: bool = False) -> RotationRecord:
        lf     = self._get(file_name)
        needs, reason = self._rotator.check(lf)

        if not needs and not force:
            raise RotationError(
                f"'{file_name}' does not meet rotation criteria yet. "
                f"Use --force to rotate anyway."
            )
        if force and not needs:
            reason = "forced by operator"

        record = self._rotator.rotate(lf, reason)
        self._archive.append(record)
        self._prune_backups(lf)
        self._log(
            f"ROTATE    {file_name}  #{record.sequence}  "
            f"{_fmt_bytes(record.original_size)} → {_fmt_bytes(record.compressed_size)}  [{reason}]"
        )
        return record

    def check_and_rotate_all(self) -> List[Tuple[str, RotationRecord]]:
        """Scan all files and rotate those that meet their policy."""
        rotated: List[Tuple[str, RotationRecord]] = []
        for name, lf in list(self._files.items()):
            needs, reason = self._rotator.check(lf)
            if needs:
                if lf.current_size == 0:
                    self._log(f"AUTO-ROTATE SKIP {name}  (empty file, resetting timer)")
                    lf.clear()   # reset creation_date so timer starts fresh
                    continue
                rec = self._rotator.rotate(lf, reason)
                self._archive.append(rec)
                self._prune_backups(lf)
                self._log(
                    f"AUTO-ROTATE {name}  #{rec.sequence}  [{reason}]"
                )
                rotated.append((name, rec))
        return rotated

    def _prune_backups(self, lf: LogFile) -> None:
        limit = lf.policy.backup_count
        if limit == 0:
            return   # unlimited
        # Gather this file's archives from global store, oldest first
        file_archives = [r for r in self._archive if r.original_name == lf.file_name]
        excess = len(file_archives) - limit
        if excess > 0:
            to_remove = {r.archive_name for r in file_archives[:excess]}
            pruned = len(to_remove)
            self._archive = [r for r in self._archive if r.archive_name not in to_remove]
            self._log(f"PRUNE     {lf.file_name}  removed {pruned} old backup(s)")

    # ── queries ───────────────────────────────────────────────────────────────
    def get_file(self, name: str) -> LogFile:
        return self._get(name)

    def all_files(self) -> List[LogFile]:
        return sorted(self._files.values(), key=lambda f: f.file_name)

    def archives_for(self, file_name: str) -> List[RotationRecord]:
        self._get(file_name)    # raises if not found
        return [r for r in self._archive if r.original_name == file_name]

    def all_archives(self) -> List[RotationRecord]:
        return list(self._archive)

    def event_log(self, limit: int = 40) -> List[str]:
        return self._event_log[-limit:]

    def stats(self) -> Dict:
        total_size  = sum(f.current_size for f in self._files.values())
        total_arch  = sum(r.compressed_size for r in self._archive)
        total_saved = sum(r.original_size - r.compressed_size for r in self._archive)
        return {
            "files"           : len(self._files),
            "archives"        : len(self._archive),
            "total_live_size" : total_size,
            "total_arch_size" : total_arch,
            "total_saved"     : total_saved,
            "total_rotations" : len(self._archive),
        }


# ══════════════════════════════════════════════════════════════════════════════
# Pre-built seed data
# ══════════════════════════════════════════════════════════════════════════════

def _seed(mgr: RotationManager) -> None:
    configs = [
        ("app.log",       RotationType.SIZE_BASED, "5MB",  "1d",  5, CompressionFormat.GZIP),
        ("access.log",    RotationType.SIZE_BASED, "10MB", "1d",  7, CompressionFormat.GZIP),
        ("error.log",     RotationType.SIZE_BASED, "2MB",  "12h", 10,CompressionFormat.GZIP),
        ("debug.log",     RotationType.HYBRID,     "8MB",  "6h",  3, CompressionFormat.GZIP),
        ("audit.log",     RotationType.TIME_BASED, "20MB", "1d",  30,CompressionFormat.NONE),
        ("worker.log",    RotationType.SIZE_BASED, "3MB",  "1d",  5, CompressionFormat.GZIP),
        ("scheduler.log", RotationType.TIME_BASED, "15MB", "12h", 7, CompressionFormat.GZIP),
    ]
    for name, rtype, max_s, interval, bc, comp in configs:
        policy = RotationPolicy(
            rotation_type     = rtype,
            max_size          = _parse_bytes(max_s),
            rotation_interval = _parse_interval(interval),
            backup_count      = bc,
            compress          = comp,
        )
        mgr.register(name, policy)

    # Grow files and do some early rotations so the demo has history
    for name, lines_per_batch, batches in [
        ("app.log",    400, 3),
        ("access.log", 600, 2),
        ("error.log",  200, 4),
        ("worker.log", 300, 2),
    ]:
        for _ in range(batches):
            mgr.append_lines(name, lines_per_batch)
            lf = mgr.get_file(name)
            needs, _ = mgr._rotator.check(lf)
            if needs:
                mgr.rotate(name)

    # Partially fill some files to show variety
    mgr.append_lines("app.log",    150)
    mgr.append_lines("access.log", 200)
    mgr.append_lines("debug.log",   50)
    mgr.advance_time("audit.log",   _parse_interval("20h"))
    mgr.advance_time("scheduler.log", _parse_interval("14h"))


# ══════════════════════════════════════════════════════════════════════════════
# CLI screens
# ══════════════════════════════════════════════════════════════════════════════

BANNER = textwrap.dedent("""\
    ╔══════════════════════════════════════════════════════════════╗
    ║         log_rotation_system  v1.0  (in-memory sim)          ║
    ║   A Python OOP log rotation manager with policy engine      ║
    ╚══════════════════════════════════════════════════════════════╝
""")

MENU = """\
{head}
  1.   List all log files
  2.   Show file details
  3.   Create / register a log file
  4.   Delete / deregister a log file
  5.   Simulate log growth  (write N lines)
  6.   Advance simulated time
  7.   Rotate a file  (manual / forced)
  8.   Auto-scan & rotate all eligible files
  9.   View archives for a file
 10.   View global archive list
 11.   Update rotation policy for a file
 12.   Dashboard & statistics
 13.   View event log
  0.   Exit
"""


def _prompt(label: str, allow_empty: bool = False) -> str:
    while True:
        v = input(_c(f"  {label}: ", "1;33")).strip()
        if v or allow_empty:
            return v
        _warn("Input cannot be empty.")

def _confirm(q: str) -> bool:
    return input(_c(f"  {q} [y/N] ", "1;31")).strip().lower() in ("y", "yes")

def _choose(label: str, options: List[str]) -> int:
    """Display numbered choices; return 0-based index."""
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        raw = input(_c(f"  {label} [1-{len(options)}]: ", "1;33")).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        _warn("Invalid choice.")


# ── individual screens ────────────────────────────────────────────────────────

def scr_list(mgr: RotationManager) -> None:
    files = mgr.all_files()
    _head(f"\n  Registered Log Files ({len(files)})\n")
    print("  " + "─" * 90)
    if not files:
        _info("No log files registered.")
    else:
        for lf in files:
            print(lf.status_line())
    print()


def scr_detail(mgr: RotationManager) -> None:
    name = _prompt("Log file name")
    try:
        lf = mgr.get_file(name)
        _head(f"\n  ── Details: {lf.file_name} ──\n")
        for line in lf.detail_block().splitlines():
            print(f"    {line}")
        print()
    except LogRotationError as e:
        _err(str(e))


def scr_create(mgr: RotationManager) -> None:
    _head("\n  ── Register New Log File ──\n")
    name = _prompt("File name (e.g. myapp.log)")

    print("\n  Rotation type:")
    rtype_idx = _choose("Choose", ["Size-based", "Time-based", "Hybrid (either)"])
    rtype = [RotationType.SIZE_BASED, RotationType.TIME_BASED, RotationType.HYBRID][rtype_idx]

    max_size  = _parse_bytes(_prompt("Max size (e.g. 10MB, 512KB)"))  if rtype != RotationType.TIME_BASED  else 10*1024*1024
    interval  = _parse_interval(_prompt("Rotation interval (e.g. 1h, 12h, 7d)")) if rtype != RotationType.SIZE_BASED else timedelta(days=1)

    bc_raw = _prompt("Backup count (0 = unlimited)")
    if not bc_raw.isdigit():
        _err("Backup count must be an integer."); return
    bc = int(bc_raw)

    print("\n  Compression:")
    comp_idx = _choose("Choose", ["GZIP (recommended)", "None"])
    comp = [CompressionFormat.GZIP, CompressionFormat.NONE][comp_idx]

    try:
        policy = RotationPolicy(
            rotation_type     = rtype,
            max_size          = max_size,
            rotation_interval = interval,
            backup_count      = bc,
            compress          = comp,
        )
        lf = mgr.register(name, policy)
        _ok(f"Registered '{lf.file_name}'  |  {policy.summary()}")
    except (ValidationError, LogRotationError) as e:
        _err(str(e))


def scr_delete(mgr: RotationManager) -> None:
    name = _prompt("Log file name to deregister")
    if not _confirm(f"Remove '{name}' from the registry (archives kept)?"):
        _info("Cancelled."); return
    try:
        mgr.deregister(name)
        _ok(f"'{name}' deregistered.")
    except LogRotationError as e:
        _err(str(e))


def scr_grow(mgr: RotationManager) -> None:
    name = _prompt("Log file name")
    raw  = _prompt("Number of lines to write")
    if not raw.isdigit() or int(raw) < 1:
        _err("Enter a positive integer."); return
    n = int(raw)
    try:
        added = mgr.append_lines(name, n)
        lf    = mgr.get_file(name)
        _ok(f"Wrote {n} lines (+{_fmt_bytes(added)})  →  total {_fmt_bytes(lf.current_size)}")
        # Helpful hint
        needs, reason = mgr._rotator.check(lf)
        if needs:
            _warn(f"Rotation criteria met: {reason}. Run option 7 to rotate.")
    except LogRotationError as e:
        _err(str(e))


def scr_timeskip(mgr: RotationManager) -> None:
    name = _prompt("Log file name (or 'ALL' for all files)")
    raw  = _prompt("Time to advance (e.g. 30m, 2h, 1d, 1w)")
    try:
        delta = _parse_interval(raw)
    except ValidationError as e:
        _err(str(e)); return

    targets = mgr.all_files() if name.upper() == "ALL" else []
    if name.upper() != "ALL":
        try:
            targets = [mgr.get_file(name)]
        except LogRotationError as e:
            _err(str(e)); return

    for lf in targets:
        mgr.advance_time(lf.file_name, delta)
        needs, reason = mgr._rotator.check(lf)
        status = _c(f"⚡ rotation due: {reason}", "33") if needs else "ok"
        _ok(f"'{lf.file_name}' advanced {delta}  [{status}]")


def scr_rotate(mgr: RotationManager) -> None:
    name  = _prompt("Log file name")
    force = _confirm("Force rotation even if policy not met?")
    try:
        rec = mgr.rotate(name, force=force)
        _ok(f"Rotated → {rec.archive_name}")
        _ok(f"  Original: {_fmt_bytes(rec.original_size)}  "
            f"Archived: {_fmt_bytes(rec.compressed_size)}  "
            f"Savings: {_fmt_bytes(rec.original_size - rec.compressed_size)}")
    except (LogRotationError, RotationError) as e:
        _err(str(e))


def scr_autorotate(mgr: RotationManager) -> None:
    rotated = mgr.check_and_rotate_all()
    if not rotated:
        _info("No files currently meet their rotation criteria.")
    else:
        _head(f"\n  Auto-rotated {len(rotated)} file(s):\n")
        for fname, rec in rotated:
            _ok(f"{fname:<28} → {rec.archive_name}  [{rec.reason}]")
    print()


def scr_file_archives(mgr: RotationManager) -> None:
    name = _prompt("Log file name")
    try:
        records = mgr.archives_for(name)
    except LogRotationError as e:
        _err(str(e)); return

    _head(f"\n  Archives for '{name}'  ({len(records)} entries)\n")
    if not records:
        _info("No archives yet."); return
    print("  " + "─" * 100)
    for r in reversed(records):     # newest first
        print(r.one_line())
    total_orig = sum(r.original_size for r in records)
    total_arch = sum(r.compressed_size for r in records)
    print("  " + "─" * 100)
    _dim(f"  Total original: {_fmt_bytes(total_orig)}   "
         f"Total archived: {_fmt_bytes(total_arch)}   "
         f"Space saved: {_fmt_bytes(total_orig - total_arch)}")
    print()


def scr_all_archives(mgr: RotationManager) -> None:
    records = mgr.all_archives()
    _head(f"\n  Global Archive  ({len(records)} entries)\n")
    if not records:
        _info("No archives yet."); return
    print("  " + "─" * 100)
    for r in reversed(records):
        print(r.one_line())
    print()


def scr_update_policy(mgr: RotationManager) -> None:
    name = _prompt("Log file name")
    try:
        lf = mgr.get_file(name)
    except LogRotationError as e:
        _err(str(e)); return

    _info(f"Current policy: {lf.policy.summary()}")
    _info("Leave a field blank to keep the current value.\n")

    def _ask(label: str, current: str) -> str:
        v = input(_c(f"  {label} [{current}]: ", "1;33")).strip()
        return v or current

    try:
        rtype_map = {"size": RotationType.SIZE_BASED,
                     "time": RotationType.TIME_BASED,
                     "hybrid": RotationType.HYBRID}
        rtype_raw = _ask("Rotation type [size/time/hybrid]", lf.policy.rotation_type.value).lower()
        rtype     = rtype_map.get(rtype_raw, lf.policy.rotation_type)

        ms_raw  = _ask("Max size",            _fmt_bytes(lf.policy.max_size).replace(" ", ""))
        max_s   = _parse_bytes(ms_raw)

        iv_raw  = _ask("Rotation interval",   str(lf.policy.rotation_interval))
        try:
            interval = _parse_interval(iv_raw)
        except ValidationError:
            interval = lf.policy.rotation_interval

        bc_raw  = _ask("Backup count",        str(lf.policy.backup_count))
        bc      = int(bc_raw) if bc_raw.isdigit() else lf.policy.backup_count

        comp_raw = _ask("Compression [gz/none]", lf.policy.compress.value).lower()
        comp     = CompressionFormat.GZIP if comp_raw == "gz" else CompressionFormat.NONE

        lf.policy = RotationPolicy(
            rotation_type     = rtype,
            max_size          = max_s,
            rotation_interval = interval,
            backup_count      = bc,
            compress          = comp,
        )
        _ok(f"Policy updated: {lf.policy.summary()}")
    except (ValidationError, ValueError) as e:
        _err(str(e))


def scr_dashboard(mgr: RotationManager) -> None:
    st    = mgr.stats()
    files = mgr.all_files()
    due   = [lf for lf in files if mgr._rotator.check(lf)[0]]

    _head("\n  ╔═══════════════════════ Dashboard ═══════════════════════╗\n")
    print(f"    Registered files   : {st['files']}")
    print(f"    Total live size    : {_fmt_bytes(st['total_live_size'])}")
    print(f"    Total archives     : {st['archives']}")
    print(f"    Total archive size : {_fmt_bytes(st['total_arch_size'])}")
    print(_c(f"    Space saved (gzip) : {_fmt_bytes(st['total_saved'])}", "32"))

    if due:
        _head(f"\n  Files due for rotation ({len(due)}):")
        for lf in due:
            _, reason = mgr._rotator.check(lf)
            print(_c(f"    ⚡ {lf.file_name:<28} {reason}", "33"))

    _head("\n  Fill levels:")
    for lf in files:
        print(f"    {lf.file_name:<28} {lf.fill_bar}")
    print()


def scr_eventlog(mgr: RotationManager) -> None:
    entries = mgr.event_log(40)
    _head(f"\n  Event Log  (last {len(entries)} entries, newest first)\n")
    print("  " + "─" * 80)
    for e in reversed(entries):
        print(f"    {e}")
    print()


# ── dispatch ──────────────────────────────────────────────────────────────────

SCREENS = {
    "1" : scr_list,
    "2" : scr_detail,
    "3" : scr_create,
    "4" : scr_delete,
    "5" : scr_grow,
    "6" : scr_timeskip,
    "7" : scr_rotate,
    "8" : scr_autorotate,
    "9" : scr_file_archives,
    "10": scr_all_archives,
    "11": scr_update_policy,
    "12": scr_dashboard,
    "13": scr_eventlog,
}


def main() -> None:
    print(_c(BANNER, "1;36"))
    mgr = RotationManager()
    _seed(mgr)
    st = mgr.stats()
    _info(
        f"Loaded {st['files']} log files  |  "
        f"{st['archives']} existing archive(s)  |  "
        f"total live size {_fmt_bytes(st['total_live_size'])}"
    )

    while True:
        print(MENU.format(head=_c("  Main Menu", "1;34")))
        try:
            choice = input(_c("  Choose an option: ", "1;32")).strip()
        except (EOFError, KeyboardInterrupt):
            print(); _info("Exiting. Goodbye!"); break

        if choice == "0":
            _info("Exiting. Goodbye!"); break

        handler = SCREENS.get(choice)
        if handler:
            handler(mgr)
        else:
            _warn(f"Unknown option '{choice}'. Enter 0–13.")


if __name__ == "__main__":
    main()