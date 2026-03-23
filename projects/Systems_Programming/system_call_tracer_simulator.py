"""
system_call_tracer_simulator.py
A Python OOP simulation of a system-call tracer (strace-like).
"""

from __future__ import annotations

import random
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Callable, Optional


# ══════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════

class CallStatus(Enum):
    SUCCESS = "success"
    ERROR   = "error"
    PENDING = "pending"


class CallCategory(Enum):
    FILE_IO    = "File I/O"
    PROCESS    = "Process"
    NETWORK    = "Network"
    MEMORY     = "Memory"
    SIGNAL     = "Signal"
    IPC        = "IPC"
    TIME       = "Time"
    SECURITY   = "Security"
    DEVICE     = "Device"


class ProcessState(Enum):
    RUNNING  = "running"
    SLEEPING = "sleeping"
    STOPPED  = "stopped"
    ZOMBIE   = "zombie"


# ══════════════════════════════════════════════════════════════
# Custom exceptions
# ══════════════════════════════════════════════════════════════

class TracerError(Exception):
    """Base tracer exception."""

class ProcessNotFoundError(TracerError):
    """Raised when a process_id is not registered."""

class DuplicateProcessError(TracerError):
    """Raised when registering a PID that already exists."""

class ValidationError(TracerError):
    """Raised for invalid user input."""


# ══════════════════════════════════════════════════════════════
# Syscall catalogue
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SyscallSpec:
    name:          str
    category:      CallCategory
    arg_templates: tuple
    success_codes: tuple
    error_codes:   tuple
    error_rate:    float = 0.12


_SYSCALL_SPECS = [
    # File I/O
    SyscallSpec("open",     CallCategory.FILE_IO, ('"{path}"','O_RDONLY','O_WRONLY|O_CREAT'), (3,4,5,6,7), (-2,-13,-24), 0.15),
    SyscallSpec("close",    CallCategory.FILE_IO, ("fd={fd}",), (0,), (-9,)),
    SyscallSpec("read",     CallCategory.FILE_IO, ("fd={fd}","buf=0x{addr:x}","count={count}"), (0,128,512,1024,4096), (-9,-11,-14), 0.10),
    SyscallSpec("write",    CallCategory.FILE_IO, ("fd={fd}","buf=0x{addr:x}","count={count}"), (1,64,512,1024), (-9,-22,-28), 0.10),
    SyscallSpec("stat",     CallCategory.FILE_IO, ('"{path}"',"statbuf=0x{addr:x}"), (0,), (-2,-13)),
    SyscallSpec("lseek",    CallCategory.FILE_IO, ("fd={fd}","offset={count}","whence=SEEK_SET"), (0,128,4096), (-9,-29)),
    SyscallSpec("unlink",   CallCategory.FILE_IO, ('"{path}"',), (0,), (-2,-13,-16), 0.18),
    SyscallSpec("mkdir",    CallCategory.FILE_IO, ('"{path}"',"mode=0755"), (0,), (-13,-17), 0.20),
    SyscallSpec("rename",   CallCategory.FILE_IO, ('"{path}"','"{path2}"'), (0,), (-2,-13,-16), 0.12),
    SyscallSpec("chmod",    CallCategory.FILE_IO, ('"{path}"',"mode=0{mode:o}"), (0,), (-1,-13), 0.08),
    # Process
    SyscallSpec("fork",     CallCategory.PROCESS, (), (0,1234,5678,9012), (-11,-12), 0.05),
    SyscallSpec("execve",   CallCategory.PROCESS, ('"{path}"',"argv=[...]","envp=[...]"), (0,), (-2,-13,-8), 0.10),
    SyscallSpec("exit",     CallCategory.PROCESS, ("status={status}",), (0,), ()),
    SyscallSpec("wait4",    CallCategory.PROCESS, ("pid={pid}","options=0"), (0,1111), (-4,-10)),
    SyscallSpec("getpid",   CallCategory.PROCESS, (), (100,200,300,1024,2048), ()),
    SyscallSpec("kill",     CallCategory.PROCESS, ("pid={pid}","sig=SIGTERM"), (0,), (-1,-3), 0.08),
    SyscallSpec("clone",    CallCategory.PROCESS, ("flags=CLONE_VM|CLONE_FS","stack=0x{addr:x}"), (0,1234), (-11,-12), 0.08),
    # Network
    SyscallSpec("socket",   CallCategory.NETWORK, ("domain=AF_INET","type=SOCK_STREAM","protocol=0"), (3,4,5), (-22,-24), 0.10),
    SyscallSpec("connect",  CallCategory.NETWORK, ("fd={fd}",'addr="{ip}:{port}"',"addrlen=16"), (0,), (-111,-113,-99), 0.20),
    SyscallSpec("bind",     CallCategory.NETWORK, ("fd={fd}",'addr="0.0.0.0:{port}"',"addrlen=16"), (0,), (-98,-13), 0.12),
    SyscallSpec("listen",   CallCategory.NETWORK, ("fd={fd}","backlog=128"), (0,), (-22,-88)),
    SyscallSpec("accept",   CallCategory.NETWORK, ("fd={fd}","addr=0x{addr:x}","addrlen=0x{addr2:x}"), (3,4,5,6), (-11,-4), 0.15),
    SyscallSpec("send",     CallCategory.NETWORK, ("fd={fd}","buf=0x{addr:x}","len={count}","flags=0"), (64,256,512,1024), (-32,-9), 0.10),
    SyscallSpec("recv",     CallCategory.NETWORK, ("fd={fd}","buf=0x{addr:x}","len={count}","flags=0"), (64,256,512), (-11,-9,-104), 0.12),
    # Memory
    SyscallSpec("mmap",     CallCategory.MEMORY, ("addr=NULL","length={length}","prot=PROT_READ|PROT_WRITE","flags=MAP_PRIVATE","fd=-1","offset=0"), (0x7f000000,0x7f100000), (-12,-22), 0.05),
    SyscallSpec("munmap",   CallCategory.MEMORY, ("addr=0x{addr:x}","length={length}"), (0,), (-22,)),
    SyscallSpec("mprotect", CallCategory.MEMORY, ("addr=0x{addr:x}","len={length}","prot=PROT_READ"), (0,), (-13,-22), 0.05),
    SyscallSpec("brk",      CallCategory.MEMORY, ("addr=0x{addr:x}",), (0x601000,0x602000), (-12,)),
    # Signal
    SyscallSpec("sigaction",    CallCategory.SIGNAL, ("signum=SIGINT","act=0x{addr:x}","oldact=NULL"), (0,), (-22,)),
    SyscallSpec("sigprocmask",  CallCategory.SIGNAL, ("how=SIG_BLOCK","set=0x{addr:x}","oldset=NULL"), (0,), (-22,)),
    SyscallSpec("pause",        CallCategory.SIGNAL, (), (-1,), (-4,)),
    # IPC
    SyscallSpec("pipe",   CallCategory.IPC, ("pipefd[2]=0x{addr:x}",), (0,), (-24,-23)),
    SyscallSpec("shmget", CallCategory.IPC, ("key=0x{addr:x}","size={length}","shmflg=0666|IPC_CREAT"), (1,2,3), (-12,-13), 0.12),
    SyscallSpec("msgget", CallCategory.IPC, ("key=0x{addr:x}","msgflg=0666|IPC_CREAT"), (0,1,2), (-13,-28), 0.10),
    # Time
    SyscallSpec("gettimeofday", CallCategory.TIME, ("tv=0x{addr:x}","tz=NULL"), (0,), (-14,)),
    SyscallSpec("nanosleep",    CallCategory.TIME, ("req={{tv_sec=0,tv_nsec={count}}}","rem=NULL"), (0,), (-4,-22)),
    SyscallSpec("clock_gettime",CallCategory.TIME, ("clk_id=CLOCK_MONOTONIC","tp=0x{addr:x}"), (0,), (-22,)),
    # Security
    SyscallSpec("getuid",  CallCategory.SECURITY, (), (0,1000,1001), ()),
    SyscallSpec("setuid",  CallCategory.SECURITY, ("uid={uid}",), (0,), (-1,-22), 0.15),
    SyscallSpec("getcwd",  CallCategory.SECURITY, ("buf=0x{addr:x}","size=4096"), (4096,), (-2,-34)),
    SyscallSpec("chroot",  CallCategory.SECURITY, ('"{path}"',), (0,), (-1,-13), 0.20),
    # Device
    SyscallSpec("ioctl",  CallCategory.DEVICE, ("fd={fd}","request=0x{addr:x}","argp=0x{addr2:x}"), (0,), (-9,-22,-25), 0.15),
    SyscallSpec("poll",   CallCategory.DEVICE, ("fds=0x{addr:x}","nfds={count}","timeout={count}"), (0,1,2), (-4,-14)),
    SyscallSpec("select", CallCategory.DEVICE, ("nfds={count}","readfds=0x{addr:x}","writefds=NULL","exceptfds=NULL","timeout=0x{addr2:x}"), (0,1,2), (-4,-9)),
]

_SPEC_BY_NAME = {s.name: s for s in _SYSCALL_SPECS}

_ERRNO_MSGS = {
    -1:"EPERM",-2:"ENOENT",-3:"ESRCH",-4:"EINTR",-8:"ENOEXEC",
    -9:"EBADF",-10:"ECHILD",-11:"EAGAIN",-12:"ENOMEM",-13:"EACCES",
    -14:"EFAULT",-16:"EBUSY",-17:"EEXIST",-22:"EINVAL",-23:"ENFILE",
    -24:"EMFILE",-25:"ENOTTY",-28:"ENOSPC",-29:"ESPIPE",-32:"EPIPE",
    -34:"ERANGE",-88:"ENOTSOCK",-98:"EADDRINUSE",-99:"EADDRNOTAVAIL",
    -104:"ECONNRESET",-111:"ECONNREFUSED",-113:"EHOSTUNREACH",
}

_PATHS = [
    "/etc/passwd","/var/log/syslog","/home/user/.bashrc","/tmp/tmpXXXXX",
    "/usr/lib/libssl.so","/dev/null","/proc/self/fd","/run/lock/file.lock",
    "/opt/app/config.json","/home/user/data.bin",
]
_IPS  = ["127.0.0.1","192.168.1.100","10.0.0.1","8.8.8.8","172.16.0.5"]
_PROC_NAMES = [
    "bash","python3","nginx","postgres","redis-server","systemd",
    "sshd","curl","gcc","vim","top","ls","cat","grep","awk","find","tar","wget",
]

def _fake(key):
    return {
        "path":   lambda: random.choice(_PATHS),
        "path2":  lambda: random.choice(_PATHS),
        "fd":     lambda: random.randint(3, 20),
        "addr":   lambda: random.randint(0x400000, 0x7FFFFFFF),
        "addr2":  lambda: random.randint(0x400000, 0x7FFFFFFF),
        "count":  lambda: random.choice([16,64,128,512,1024,4096]),
        "length": lambda: random.choice([4096,8192,65536,1048576]),
        "port":   lambda: random.choice([80,443,8080,3306,5432,6379,22]),
        "ip":     lambda: random.choice(_IPS),
        "pid":    lambda: random.randint(1, 65535),
        "uid":    lambda: random.choice([0,1000,1001]),
        "status": lambda: random.choice([0,1,127]),
        "mode":   lambda: random.choice([0o644,0o755,0o600]),
    }[key]()


def _render_args(spec: SyscallSpec) -> list:
    result = []
    for tmpl in spec.arg_templates:
        vals = {}
        for key in ("path","path2","fd","addr","addr2","count","length","port","ip","pid","uid","status","mode"):
            if "{" + key in tmpl:
                vals[key] = _fake(key)
        result.append(tmpl.format_map(vals))
    return result


def _generate_syscall(spec: SyscallSpec, pid: int) -> "SystemCall":
    args     = _render_args(spec)
    is_error = random.random() < spec.error_rate and spec.error_codes
    if is_error:
        retval = random.choice(spec.error_codes)
        status = CallStatus.ERROR
    elif spec.success_codes:
        retval = random.choice(spec.success_codes)
        status = CallStatus.SUCCESS
    else:
        retval = 0
        status = CallStatus.SUCCESS
    return SystemCall(call_name=spec.name, arguments=args, return_value=retval,
                      process_id=pid, category=spec.category, status=status)


# ══════════════════════════════════════════════════════════════
# SystemCall
# ══════════════════════════════════════════════════════════════

@dataclass
class SystemCall:
    call_name:    str
    arguments:    list
    return_value: int
    process_id:   int
    category:     CallCategory
    status:       CallStatus
    timestamp:    datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @property
    def errno_label(self) -> str:
        return _ERRNO_MSGS.get(self.return_value, f"E{abs(self.return_value)}") if self.status == CallStatus.ERROR else ""

    def format_strace(self) -> str:
        ts   = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        args = ", ".join(self.arguments)
        ret  = str(self.return_value)
        if self.status == CallStatus.ERROR:
            ret += f" {self.errno_label}"
        return f"[{ts}] [{self.process_id:>5}] {self.call_name}({args}) = {ret}"

    def __str__(self) -> str:
        return self.format_strace()


# ══════════════════════════════════════════════════════════════
# Process
# ══════════════════════════════════════════════════════════════

class Process:
    _next_pid: int = 1000

    def __init__(self, name: str, process_id: Optional[int] = None, parent_pid: Optional[int] = None):
        if not name or not name.strip():
            raise ValidationError("Process name cannot be empty.")
        if process_id is not None and (not isinstance(process_id, int) or process_id <= 0):
            raise ValidationError("process_id must be a positive integer.")
        self.process_id  = process_id if process_id is not None else Process._alloc_pid()
        self.name        = name.strip()
        self.parent_pid  = parent_pid
        self.state       = ProcessState.RUNNING
        self.created_at  = datetime.now(tz=timezone.utc)
        self._call_count = 0

    @classmethod
    def _alloc_pid(cls) -> int:
        pid = cls._next_pid; cls._next_pid += 1; return pid

    def increment_call_count(self) -> None: self._call_count += 1

    @property
    def call_count(self) -> int: return self._call_count

    def __str__(self) -> str:
        return f"Process(pid={self.process_id}, name='{self.name}', state={self.state.value})"


# ══════════════════════════════════════════════════════════════
# Tracer
# ══════════════════════════════════════════════════════════════

class Tracer:
    def __init__(self, verbose: bool = False):
        self._log:      list = []
        self._attached: set  = set()
        self.verbose         = verbose
        self._paused         = False

    def attach(self, pid: int)  -> None: self._attached.add(pid)
    def detach(self, pid: int)  -> None: self._attached.discard(pid)
    def is_attached(self, pid)  -> bool: return pid in self._attached
    def pause(self)  -> None: self._paused = True
    def resume(self) -> None: self._paused = False

    def capture(self, syscall: SystemCall) -> None:
        if self._paused: return
        if self._attached and syscall.process_id not in self._attached: return
        self._log.append(syscall)
        if self.verbose:
            icon = "✘" if syscall.status == CallStatus.ERROR else " "
            print(f"  {icon} {syscall.format_strace()}")

    def capture_many(self, calls: list) -> None:
        for c in calls: self.capture(c)

    @property
    def log(self) -> list: return list(self._log)

    @property
    def total_captured(self) -> int: return len(self._log)

    def clear(self) -> None: self._log.clear()


# ══════════════════════════════════════════════════════════════
# TraceAnalyzer
# ══════════════════════════════════════════════════════════════

class TraceAnalyzer:
    def __init__(self, log: list):
        self._log = log

    def filter_by_pid(self, pid: int)               -> list: return [c for c in self._log if c.process_id == pid]
    def filter_by_call(self, name: str)              -> list: return [c for c in self._log if c.call_name.lower() == name.lower()]
    def filter_by_category(self, cat: CallCategory) -> list: return [c for c in self._log if c.category == cat]
    def filter_by_status(self, st: CallStatus)       -> list: return [c for c in self._log if c.status == st]

    def filter_by_time_range(self, start=None, end=None) -> list:
        result = self._log
        if start: result = [c for c in result if c.timestamp >= start]
        if end:   result = [c for c in result if c.timestamp <= end]
        return result

    def filter_combined(self, pid=None, call=None, category=None, status=None) -> list:
        r = self._log
        if pid      is not None: r = [c for c in r if c.process_id == pid]
        if call     is not None: r = [c for c in r if c.call_name.lower() == call.lower()]
        if category is not None: r = [c for c in r if c.category == category]
        if status   is not None: r = [c for c in r if c.status == status]
        return r

    def most_frequent_calls(self, n: int = 10) -> list: return Counter(c.call_name for c in self._log).most_common(n)
    def error_calls(self)  -> list:  return [c for c in self._log if c.status == CallStatus.ERROR]
    def error_rate(self)   -> float: return len(self.error_calls()) / len(self._log) * 100 if self._log else 0.0
    def unique_call_names(self) -> list: return sorted({c.call_name for c in self._log})

    def calls_per_process(self) -> dict:
        counts: dict = defaultdict(int)
        for c in self._log: counts[c.process_id] += 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def calls_per_category(self) -> dict:
        counts: dict = defaultdict(int)
        for c in self._log: counts[c.category.value] += 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def most_common_errors(self, n: int = 10) -> list:
        errs = [f"{c.call_name}={c.errno_label}" for c in self._log if c.status == CallStatus.ERROR]
        return Counter(errs).most_common(n)

    def timeline_buckets(self) -> dict:
        buckets: dict = defaultdict(int)
        for c in self._log: buckets[c.timestamp.strftime("%H:%M:%S")] += 1
        return dict(sorted(buckets.items()))

    def summary(self) -> dict:
        return {"total": len(self._log), "errors": len(self.error_calls()),
                "error_rate": self.error_rate(), "unique_calls": len(self.unique_call_names()),
                "processes": len(self.calls_per_process())}


# ══════════════════════════════════════════════════════════════
# TraceManager
# ══════════════════════════════════════════════════════════════

class TraceManager:
    def __init__(self):
        self._processes: dict = {}
        self.tracer = Tracer(verbose=False)

    def create_process(self, name: str, pid: Optional[int] = None,
                       parent_pid: Optional[int] = None, auto_attach: bool = True) -> Process:
        proc = Process(name, pid, parent_pid)
        if proc.process_id in self._processes:
            raise DuplicateProcessError(f"PID {proc.process_id} already registered.")
        self._processes[proc.process_id] = proc
        if auto_attach: self.tracer.attach(proc.process_id)
        return proc

    def get_process(self, pid: int) -> Process:
        if pid not in self._processes: raise ProcessNotFoundError(f"No process with PID {pid}.")
        return self._processes[pid]

    def terminate_process(self, pid: int) -> None:
        proc = self.get_process(pid)
        proc.state = ProcessState.ZOMBIE
        self.tracer.detach(pid)

    def list_processes(self) -> list: return list(self._processes.values())

    @property
    def active_processes(self) -> list:
        return [p for p in self._processes.values() if p.state == ProcessState.RUNNING]

    def generate_calls(self, pid: int, count: int = 10, categories=None) -> list:
        proc = self.get_process(pid)
        if proc.state != ProcessState.RUNNING:
            raise TracerError(f"Process {pid} is {proc.state.value} and cannot generate calls.")
        pool = _SYSCALL_SPECS
        if categories:
            pool = [s for s in _SYSCALL_SPECS if s.category in categories]
        if not pool: raise ValidationError("No specs for selected categories.")
        calls = []
        for _ in range(count):
            spec = random.choice(pool)
            call = _generate_syscall(spec, pid)
            proc.increment_call_count()
            calls.append(call)
        self.tracer.capture_many(calls)
        return calls

    def generate_calls_all(self, count_each: int = 5) -> dict:
        result = {}
        for proc in self.active_processes:
            result[proc.process_id] = self.generate_calls(proc.process_id, count_each)
        return result

    def analyzer(self) -> TraceAnalyzer: return TraceAnalyzer(self.tracer.log)

    def clear_traces(self) -> None:
        self.tracer.clear()
        for p in self._processes.values(): p._call_count = 0


# ══════════════════════════════════════════════════════════════
# Display helpers
# ══════════════════════════════════════════════════════════════

_W = 76

def _hr(ch="─"): print(ch * _W)
def _title(t):   print("═"*_W); print(f"  {t}"); print("═"*_W)
def _section(t): print(f"\n  ── {t} ──")
def _bar(v, mx, w=28): filled = round(v/mx*w) if mx else 0; return "█"*filled + "░"*(w-filled)
def _ok(m):  print(f"\n  ✔  {m}")
def _err(m): print(f"\n  ✘  {m}")


def print_log(calls: list, limit: int = 50) -> None:
    _section(f"SYSTEM CALL LOG  ({min(len(calls), limit)} of {len(calls)} entries)")
    _hr()
    if not calls: print("  (no calls captured)"); return
    for c in calls[-limit:]:
        icon = "✘" if c.status == CallStatus.ERROR else " "
        print(f"  {icon} {c.format_strace()}")
    if len(calls) > limit: print(f"\n  … {len(calls)-limit} older entries not shown.")


def print_summary(analyzer: TraceAnalyzer, manager: TraceManager) -> None:
    s = analyzer.summary()
    _section("TRACE SUMMARY"); _hr()
    print(f"  Total calls captured : {s['total']:,}")
    print(f"  Error calls          : {s['errors']:,}  ({s['error_rate']:.1f}%)")
    print(f"  Unique syscall names : {s['unique_calls']}")
    print(f"  Processes traced     : {s['processes']}")
    print(f"  Log entries          : {manager.tracer.total_captured:,}")


def print_top_calls(analyzer: TraceAnalyzer, n: int = 10) -> None:
    top = analyzer.most_frequent_calls(n)
    _section(f"TOP {n} MOST FREQUENT SYSCALLS"); _hr()
    if not top: print("  (no data)"); return
    mx = top[0][1]
    for rank, (name, count) in enumerate(top, 1):
        print(f"  {rank:>2}. {name:<16} {count:>5}  {_bar(count, mx)}")


def print_errors(analyzer: TraceAnalyzer, limit: int = 20) -> None:
    errs = analyzer.error_calls()
    _section(f"ERROR CALLS  ({len(errs)} total)"); _hr()
    if not errs: print("  No error calls recorded. 🎉"); return
    for c in errs[-limit:]:
        print(f"  ✘ [{c.process_id:>5}] {c.call_name}({', '.join(c.arguments)}) = {c.return_value} {c.errno_label}")
    if len(errs) > limit: print(f"\n  … {len(errs)-limit} earlier errors not shown.")


def print_per_category(analyzer: TraceAnalyzer) -> None:
    cats = analyzer.calls_per_category()
    _section("CALLS BY CATEGORY"); _hr()
    if not cats: print("  (no data)"); return
    mx = max(cats.values())
    for cat, cnt in cats.items():
        print(f"  {cat:<16} {cnt:>5}  {_bar(cnt, mx)}")


def print_per_process(analyzer: TraceAnalyzer, manager: TraceManager) -> None:
    cpp = analyzer.calls_per_process()
    _section("CALLS PER PROCESS"); _hr()
    if not cpp: print("  (no data)"); return
    mx = max(cpp.values())
    for pid, cnt in cpp.items():
        try:   name = manager.get_process(pid).name
        except ProcessNotFoundError: name = "?"
        print(f"  PID {pid:>5}  {name:<18} {cnt:>5}  {_bar(cnt, mx)}")


def print_process_list(manager: TraceManager) -> None:
    procs = manager.list_processes()
    _section(f"REGISTERED PROCESSES  ({len(procs)} total)"); _hr()
    if not procs: print("  (none)"); return
    print(f"  {'PID':>6}  {'Name':<18} {'State':<10} {'Calls':>6}  {'Attached'}")
    _hr("·")
    for p in procs:
        att = "✔" if manager.tracer.is_attached(p.process_id) else "✘"
        print(f"  {p.process_id:>6}  {p.name:<18} {p.state.value:<10} {p.call_count:>6}  {att}")


def print_timeline(analyzer: TraceAnalyzer) -> None:
    tl = analyzer.timeline_buckets()
    _section("ACTIVITY TIMELINE  (calls per second)"); _hr()
    if not tl: print("  (no data)"); return
    mx = max(tl.values()) or 1
    for ts, cnt in tl.items():
        print(f"  {ts}  {_bar(cnt, mx, 40)}  {cnt}")


# ══════════════════════════════════════════════════════════════
# Interactive console
# ══════════════════════════════════════════════════════════════

BANNER = r"""
╔══════════════════════════════════════════════════════════════════════════╗
║          System Call Tracer Simulator  🔬                                ║
║     Simulate processes, capture syscalls, analyse trace logs.            ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

MAIN_MENU = """
┌──────────────────────────────────────────────────────┐
│  Process Management                                  │
│    1.  Create a new process                          │
│    2.  List all processes                            │
│    3.  Terminate a process                           │
│                                                      │
│  Syscall Generation                                  │
│    4.  Generate syscalls  (single process)           │
│    5.  Generate syscalls  (all running processes)    │
│    6.  Toggle live output (verbose mode)             │
│                                                      │
│  Trace Logs & Filtering                              │
│    7.  View full trace log                           │
│    8.  Filter by PID                                 │
│    9.  Filter by call name                           │
│   10.  Filter by category                            │
│   11.  Filter by status  (success / error)           │
│                                                      │
│  Analysis & Reports                                  │
│   12.  Summary report                                │
│   13.  Top N most frequent calls                     │
│   14.  Error calls                                   │
│   15.  Calls by category                             │
│   16.  Calls per process                             │
│   17.  Activity timeline                             │
│   18.  Most common error types                       │
│                                                      │
│  Utilities                                           │
│   19.  Clear all traces                              │
│   20.  Load demo scenario                            │
│    0.  Exit                                          │
└──────────────────────────────────────────────────────┘"""


def _inp(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        return input(f"  {prompt}{suffix}: ").strip() or default
    except (EOFError, KeyboardInterrupt):
        print(); sys.exit(0)


def _inp_int(prompt: str, default: int, lo: int = 1, hi: int = 10_000) -> int:
    while True:
        raw = _inp(prompt, str(default))
        try:
            v = int(raw)
            if lo <= v <= hi: return v
            print(f"  ⚠  Enter a number between {lo} and {hi}.")
        except ValueError:
            print("  ⚠  Not a valid integer.")


def action_create_process(mgr: TraceManager) -> None:
    print("\n── Create Process ──")
    name    = _inp("Process name", random.choice(_PROC_NAMES))
    pid_raw = _inp("PID (blank = auto)", "")
    pid     = int(pid_raw) if pid_raw.isdigit() else None
    try:
        proc = mgr.create_process(name, pid)
        _ok(f"Created {proc}")
    except (ValidationError, DuplicateProcessError, TracerError) as e:
        _err(str(e))


def action_list_processes(mgr: TraceManager) -> None:
    print_process_list(mgr)


def action_terminate(mgr: TraceManager) -> None:
    print("\n── Terminate Process ──")
    pid = _inp_int("PID to terminate", 1000)
    try:
        mgr.terminate_process(pid)
        _ok(f"PID {pid} set to ZOMBIE and detached from tracer.")
    except ProcessNotFoundError as e:
        _err(str(e))


def action_generate_single(mgr: TraceManager) -> None:
    print("\n── Generate Syscalls (single process) ──")
    if not mgr.active_processes:
        _err("No running processes. Create one first (option 1)."); return
    print_process_list(mgr)
    pid   = _inp_int("PID", mgr.active_processes[0].process_id)
    count = _inp_int("How many syscalls", 10, 1, 500)
    print("\n  Categories (blank = all):")
    cats_list = list(CallCategory)
    for i, c in enumerate(cats_list, 1): print(f"    {i}. {c.value}")
    raw  = _inp("Category numbers e.g. 1,3", "").strip()
    cats = None
    if raw:
        cats = []
        for tok in raw.split(","):
            try: cats.append(cats_list[int(tok.strip())-1])
            except (ValueError, IndexError): pass
        if not cats: cats = None
    try:
        calls  = mgr.generate_calls(pid, count, cats)
        errors = sum(1 for c in calls if c.status == CallStatus.ERROR)
        _ok(f"Generated {len(calls)} syscalls for PID {pid}.  Errors: {errors}/{len(calls)}")
    except (ProcessNotFoundError, ValidationError, TracerError) as e:
        _err(str(e))


def action_generate_all(mgr: TraceManager) -> None:
    print("\n── Generate Syscalls (all running processes) ──")
    if not mgr.active_processes: _err("No running processes."); return
    count  = _inp_int("Syscalls per process", 5, 1, 200)
    result = mgr.generate_calls_all(count)
    for pid, calls in result.items():
        errs = sum(1 for c in calls if c.status == CallStatus.ERROR)
        print(f"  PID {pid}: {len(calls)} calls  ({errs} errors)")
    _ok(f"Done. Total captured: {mgr.tracer.total_captured}.")


def action_toggle_verbose(mgr: TraceManager) -> None:
    mgr.tracer.verbose = not mgr.tracer.verbose
    state = "ON" if mgr.tracer.verbose else "OFF"
    _ok(f"Live output is now {state}.")


def action_view_log(mgr: TraceManager) -> None:
    limit = _inp_int("Recent entries to show", 40, 1, 500)
    print_log(mgr.tracer.log, limit)


def action_filter_pid(mgr: TraceManager) -> None:
    pid     = _inp_int("Filter by PID", 1000)
    results = mgr.analyzer().filter_by_pid(pid)
    print_log(results, 60)
    print(f"\n  Total matching: {len(results)}")


def action_filter_call(mgr: TraceManager) -> None:
    name    = _inp("Syscall name (e.g. open, mmap)", "read")
    results = mgr.analyzer().filter_by_call(name)
    print_log(results, 60)
    print(f"\n  Total matching: {len(results)}")


def action_filter_category(mgr: TraceManager) -> None:
    cats = list(CallCategory)
    print("\n  Categories:")
    for i, c in enumerate(cats, 1): print(f"    {i}. {c.value}")
    idx     = _inp_int("Select number", 1, 1, len(cats))
    results = mgr.analyzer().filter_by_category(cats[idx-1])
    print_log(results, 60)
    print(f"\n  Total matching: {len(results)}")


def action_filter_status(mgr: TraceManager) -> None:
    choice  = _inp("1=Success  2=Error", "1")
    status  = CallStatus.ERROR if choice == "2" else CallStatus.SUCCESS
    results = mgr.analyzer().filter_by_status(status)
    print_log(results, 60)
    print(f"\n  Total matching: {len(results)}")


def action_summary(mgr: TraceManager)     -> None: print_summary(mgr.analyzer(), mgr)
def action_top_calls(mgr: TraceManager)   -> None: print_top_calls(mgr.analyzer(), _inp_int("Top N calls", 10, 1, 40))
def action_errors(mgr: TraceManager)      -> None: print_errors(mgr.analyzer())
def action_by_category(mgr: TraceManager) -> None: print_per_category(mgr.analyzer())
def action_by_process(mgr: TraceManager)  -> None: print_per_process(mgr.analyzer(), mgr)
def action_timeline(mgr: TraceManager)    -> None: print_timeline(mgr.analyzer())


def action_common_errors(mgr: TraceManager) -> None:
    n   = _inp_int("Error types to show", 10, 1, 40)
    top = mgr.analyzer().most_common_errors(n)
    _section(f"TOP {n} ERROR TYPES"); _hr()
    if not top: print("  No errors recorded."); return
    mx = top[0][1]
    for rank, (label, cnt) in enumerate(top, 1):
        print(f"  {rank:>2}. {label:<30} {cnt:>4}  {_bar(cnt, mx)}")


def action_clear(mgr: TraceManager) -> None:
    if _inp("Clear ALL trace data? (yes/no)", "no").lower() in ("yes","y"):
        mgr.clear_traces(); _ok("All trace data cleared.")
    else:
        print("  Cancelled.")


def action_demo(mgr: TraceManager) -> None:
    print("\n  Loading demo scenario …")
    demo = [("nginx",None),("python3",None),("postgres",None),("redis-server",None),("sshd",None)]
    created = []
    for name, pid in demo:
        try:
            proc = mgr.create_process(name, pid)
            created.append(proc)
            print(f"  + {proc}")
        except DuplicateProcessError:
            pass
    print(f"\n  Generating syscalls across {len(created)} processes …")
    for proc in created:
        mgr.generate_calls(proc.process_id, random.randint(15, 40))
    _ok(f"Demo ready!  {mgr.tracer.total_captured} syscalls captured across {len(created)} processes.")
    print("  Tip: try options 12–18 to explore the analysis views.")


_DISPATCH: dict = {
    "1": action_create_process, "2": action_list_processes, "3": action_terminate,
    "4": action_generate_single,"5": action_generate_all,   "6": action_toggle_verbose,
    "7": action_view_log,       "8": action_filter_pid,     "9": action_filter_call,
    "10": action_filter_category,"11": action_filter_status,"12": action_summary,
    "13": action_top_calls,     "14": action_errors,        "15": action_by_category,
    "16": action_by_process,    "17": action_timeline,      "18": action_common_errors,
    "19": action_clear,         "20": action_demo,
}


def main() -> None:
    random.seed()
    mgr = TraceManager()
    print(BANNER)
    if input("  Load demo scenario now? [Y/n]: ").strip().lower() != "n":
        action_demo(mgr)
    while True:
        print(MAIN_MENU)
        choice = _inp("Select option", "0")
        if choice == "0":
            print("\n  Goodbye. 👋\n"); break
        handler = _DISPATCH.get(choice)
        if handler:
            try: handler(mgr)
            except KeyboardInterrupt: print("\n  (interrupted)")
        else:
            _err(f"Unknown option '{choice}'. Choose 0–20.")


if __name__ == "__main__":
    main()