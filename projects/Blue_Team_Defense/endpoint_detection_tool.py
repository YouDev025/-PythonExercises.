#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════
  Endpoint Detection Tool  (Basic EDR Simulation)
  Author  : Senior Python / Cybersecurity Engineer
  Python  : 3.8+  |  Dependencies : stdlib only
  Run     : python endpoint_detection_tool.py
════════════════════════════════════════════════════════════════════

Architecture
────────────
  ProcessMonitor   – queries running processes via OS commands
  FileMonitor      – SHA-256 based directory integrity checks
  NetworkMonitor   – reads /proc/net/tcp* (Linux) or netstat (cross-platform)
  DetectionEngine  – evaluates raw observations against rule-set
  AlertManager     – stores, scores, displays, and logs alerts
  EDRDaemon        – orchestrates all monitors in background threads
  CLI              – interactive menu (curses-free, pure input/print)
"""

# ── Standard library imports ──────────────────────────────────────────────────
import argparse
import hashlib
import json
import logging
import os
import platform
import queue
import re
import subprocess
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 0 – Global constants & ANSI helpers
# ══════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"

# Detect ANSI support (Windows needs ANSI mode enabled or falls back to plain)
_ANSI = sys.platform != "win32" or os.environ.get("TERM") or os.environ.get("WT_SESSION")

def _a(code: str) -> str:
    return code if _ANSI else ""

C = {
    "red":    _a("\033[91m"),
    "yellow": _a("\033[93m"),
    "green":  _a("\033[92m"),
    "cyan":   _a("\033[96m"),
    "blue":   _a("\033[94m"),
    "magenta":_a("\033[95m"),
    "bold":   _a("\033[1m"),
    "dim":    _a("\033[2m"),
    "reset":  _a("\033[0m"),
    "ul":     _a("\033[4m"),
}

SEV_COLOUR = {
    "CRITICAL": C["red"]    + C["bold"],
    "HIGH":     C["red"],
    "MEDIUM":   C["yellow"],
    "LOW":      C["cyan"],
    "INFO":     C["dim"],
}

SEV_SCORE = {"INFO": 1, "LOW": 3, "MEDIUM": 6, "HIGH": 9, "CRITICAL": 12}

PLATFORM = platform.system()   # "Linux", "Darwin", "Windows"

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – Alert data model
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Alert:
    """Immutable alert record produced by the detection engine."""
    alert_id:   int
    timestamp:  str
    alert_type: str          # PROCESS | FILE | NETWORK | BEHAVIORAL
    severity:   str          # INFO | LOW | MEDIUM | HIGH | CRITICAL
    title:      str
    description: str
    affected:   str          # process name / file path / connection
    score:      int          # risk score (cumulative from SEV_SCORE)
    response:   str = ""     # simulated response action taken

    def to_dict(self) -> dict:
        return asdict(self)

    def to_log_line(self) -> str:
        return (
            f"[{self.timestamp}] "
            f"ID={self.alert_id:04d} "
            f"TYPE={self.alert_type:<10} "
            f"SEV={self.severity:<8} "
            f"SCORE={self.score:>3} "
            f"TITLE={self.title!r} "
            f"AFFECTED={self.affected!r}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – Detection rule-set
# ══════════════════════════════════════════════════════════════════════════════

# ── Suspicious / blacklisted process names (case-insensitive) ─────────────────
BLACKLISTED_PROCESSES: Set[str] = {
    # Classic attack tools
    "mimikatz", "meterpreter", "cobalt", "empire",
    "metasploit", "shellcode", "exploitdb", "powersploit",
    # Reverse shells / loaders
    "nc", "ncat", "netcat", "socat", "ncrack",
    "psexec", "wce", "fgdump", "pwdump",
    # Crypto-miners
    "xmrig", "minerd", "cpuminer", "ethminer",
    # Ransomware indicators (process names observed in the wild)
    "wbadmin", "vssadmin", "bcdedit", "cipher",
    # Recon tools
    "nmap", "masscan", "zmap", "shodan", "gobuster",
    "dirb", "nikto", "sqlmap", "hydra", "medusa",
}

# ── Suspicious command-line patterns (regex) ─────────────────────────────────
SUSPICIOUS_CMD_PATTERNS: List[re.Pattern] = [
    re.compile(r"base64\s+-d",        re.I),   # base64 decode piped execution
    re.compile(r"powershell.*-enc",   re.I),   # encoded PS command
    re.compile(r"curl.*\|\s*bash",    re.I),   # curl-pipe-bash
    re.compile(r"wget.*\|\s*sh",      re.I),   # wget-pipe-sh
    re.compile(r"/dev/tcp/",          re.I),   # bash tcp redirect
    re.compile(r"chmod\s+\+x",        re.I),   # make executable
    re.compile(r"\.\.\/\.\.\/\.\.",   re.I),   # deep path traversal
    re.compile(r"rm\s+-rf\s+/",       re.I),   # destructive rm
    re.compile(r"dd\s+if=",           re.I),   # disk wipe indicator
    re.compile(r"nohup.*&\s*$",       re.I),   # background persistence
    re.compile(r"crontab\s+-e",       re.I),   # cron modification
]

# ── Suspicious file extensions to flag on creation ───────────────────────────
SUSPICIOUS_EXTENSIONS: Set[str] = {
    ".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js",
    ".jar", ".sh", ".elf", ".bin", ".dll", ".so",
    ".py",  ".rb",  ".pl",  ".php", ".asp", ".aspx",
}

# ── Suspicious network destinations (IPs/ports – simulated) ──────────────────
SUSPICIOUS_PORTS: Set[int] = {
    4444, 4445, 5555, 1337, 31337,   # common reverse-shell ports
    6666, 6667, 6668, 6669,           # IRC C2
    8080, 8443, 9090,                 # alt-HTTP C2
}

# ── Behavioural thresholds ────────────────────────────────────────────────────
FILE_CHANGE_BURST_WINDOW  = 15    # seconds
FILE_CHANGE_BURST_LIMIT   = 10    # changes within window → HIGH alert
PROCESS_SCAN_INTERVAL     = 8     # seconds between process sweeps
FILE_SCAN_INTERVAL        = 6     # seconds between file sweeps
NETWORK_SCAN_INTERVAL     = 12    # seconds between network sweeps

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – Alert Manager
# ══════════════════════════════════════════════════════════════════════════════

class AlertManager:
    """
    Central store for all alerts.

    Thread-safe via a threading.Lock.  Provides:
      • add()          – persist a new alert and write to log
      • get_all()      – return a snapshot list
      • get_summary()  – severity / type breakdown
      • risk_score()   – cumulative session risk score
    """

    def __init__(self, log_file: str = "edr_alerts.log") -> None:
        self._lock    = threading.Lock()
        self._alerts: List[Alert] = []
        self._counter = 0
        self._log_file = log_file
        self._setup_file_logger()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _setup_file_logger(self) -> None:
        self._logger = logging.getLogger("EDR.Alerts")
        self._logger.setLevel(logging.DEBUG)
        if not self._logger.handlers:
            fh = logging.FileHandler(self._log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(fh)

    def _next_id(self) -> int:
        self._counter += 1
        return self._counter

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, alert_type: str, severity: str, title: str,
            description: str, affected: str, response: str = "") -> Alert:
        """Create, store, and log a new Alert; return it."""
        with self._lock:
            alert = Alert(
                alert_id   = self._next_id(),
                timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                alert_type = alert_type,
                severity   = severity,
                title      = title,
                description= description,
                affected   = affected,
                score      = SEV_SCORE.get(severity, 1),
                response   = response,
            )
            self._alerts.append(alert)
            self._logger.warning(alert.to_log_line())
            return alert

    def get_all(self) -> List[Alert]:
        with self._lock:
            return list(self._alerts)

    def get_recent(self, n: int = 20) -> List[Alert]:
        with self._lock:
            return list(self._alerts[-n:])

    def risk_score(self) -> int:
        with self._lock:
            return sum(a.score for a in self._alerts)

    def get_summary(self) -> dict:
        with self._lock:
            sev_count  = defaultdict(int)
            type_count = defaultdict(int)
            for a in self._alerts:
                sev_count[a.severity]   += 1
                type_count[a.alert_type] += 1
            return {
                "total":      len(self._alerts),
                "by_severity": dict(sev_count),
                "by_type":    dict(type_count),
                "risk_score": sum(a.score for a in self._alerts),
            }

    def clear(self) -> None:
        with self._lock:
            self._alerts.clear()
            self._counter = 0


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 – Process Monitor
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProcessInfo:
    pid:     str
    name:    str
    cmdline: str
    user:    str = "unknown"
    cpu:     str = "0.0"


def _get_processes_unix() -> List[ProcessInfo]:
    """Use `ps` to list running processes on Linux / macOS."""
    procs: List[ProcessInfo] = []
    try:
        result = subprocess.run(
            ["ps", "axo", "pid,user,pcpu,comm,args"],
            capture_output=True, text=True, timeout=10,
        )
        lines = result.stdout.strip().splitlines()
        for line in lines[1:]:          # skip header
            parts = line.split(None, 4)
            if len(parts) < 4:
                continue
            pid  = parts[0]
            user = parts[1]
            cpu  = parts[2]
            name = parts[3]
            cmd  = parts[4] if len(parts) > 4 else name
            procs.append(ProcessInfo(pid=pid, name=name, cmdline=cmd,
                                     user=user, cpu=cpu))
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return procs


def _get_processes_windows() -> List[ProcessInfo]:
    """Use `tasklist` on Windows."""
    procs: List[ProcessInfo] = []
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().splitlines():
            # CSV: "name","pid","session","#","mem"
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2:
                name = parts[0]
                pid  = parts[1]
                procs.append(ProcessInfo(pid=pid, name=name, cmdline=name))
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return procs


def get_processes() -> List[ProcessInfo]:
    """Cross-platform process list."""
    if PLATFORM == "Windows":
        return _get_processes_windows()
    return _get_processes_unix()


class ProcessMonitor:
    """
    Scans running processes and emits raw observations to the shared queue.

    Checks
    ──────
    1. Blacklisted process name
    2. Suspicious command-line pattern match
    3. Unusually high CPU (>90 %)
    4. New process appeared since last scan (informational)
    """

    def __init__(self, obs_queue: queue.Queue) -> None:
        self._queue     = obs_queue
        self._seen_pids: Set[str] = set()   # pids observed in previous scan
        self._lock      = threading.Lock()

    def scan(self) -> None:
        """Perform one process sweep and push observations to queue."""
        procs = get_processes()
        current_pids = {p.pid for p in procs}

        for proc in procs:
            name_lower = proc.name.lower()
            # Strip path separators to get base name
            base_name  = Path(proc.name).stem.lower()

            # ── Rule 1: blacklisted name ──────────────────────────────────
            if base_name in BLACKLISTED_PROCESSES or name_lower in BLACKLISTED_PROCESSES:
                self._queue.put({
                    "source":   "PROCESS",
                    "rule":     "BLACKLIST_HIT",
                    "severity": "CRITICAL",
                    "proc":     proc,
                    "detail":   f"Blacklisted process name: {proc.name}",
                })

            # ── Rule 2: suspicious command-line ───────────────────────────
            for pattern in SUSPICIOUS_CMD_PATTERNS:
                if pattern.search(proc.cmdline):
                    self._queue.put({
                        "source":   "PROCESS",
                        "rule":     "SUSPICIOUS_CMD",
                        "severity": "HIGH",
                        "proc":     proc,
                        "detail":   f"Matched pattern {pattern.pattern!r} in cmdline",
                    })
                    break   # one hit per process per scan is enough

            # ── Rule 3: high CPU ──────────────────────────────────────────
            try:
                if float(proc.cpu) > 90.0:
                    self._queue.put({
                        "source":   "PROCESS",
                        "rule":     "HIGH_CPU",
                        "severity": "MEDIUM",
                        "proc":     proc,
                        "detail":   f"CPU usage {proc.cpu}% exceeds threshold",
                    })
            except ValueError:
                pass

            # ── Rule 4: new process ───────────────────────────────────────
            with self._lock:
                if self._seen_pids and proc.pid not in self._seen_pids:
                    self._queue.put({
                        "source":   "PROCESS",
                        "rule":     "NEW_PROCESS",
                        "severity": "INFO",
                        "proc":     proc,
                        "detail":   f"New process spawned: {proc.name} (PID {proc.pid})",
                    })

        with self._lock:
            self._seen_pids = current_pids


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 – File Monitor  (lightweight FIM)
# ══════════════════════════════════════════════════════════════════════════════

def _sha256(filepath: str) -> Optional[str]:
    """Return SHA-256 hex-digest of a file, or None on error."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as fh:
            while chunk := fh.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, FileNotFoundError, OSError):
        return None


class FileMonitor:
    """
    Monitors a directory for integrity changes (create / modify / delete).

    Additional EDR-specific rules
    ─────────────────────────────
    • Suspicious extension on new file
    • Burst detection: >N changes in <W seconds → potential ransomware / wiper
    """

    def __init__(self, obs_queue: queue.Queue, directory: str = "./monitored") -> None:
        self._queue     = obs_queue
        self.directory  = os.path.abspath(directory)
        self._baseline: Dict[str, str] = {}       # path → sha256
        self._change_times: deque = deque()        # timestamps of recent changes
        self._initialized = False

        # Always ignore these sub-directories
        self._ignore_dirs: Set[str] = {
            "__pycache__", ".git", ".svn", ".hg", "node_modules",
        }

    # ── Public ────────────────────────────────────────────────────────────────

    def set_directory(self, path: str) -> None:
        self.directory    = os.path.abspath(path)
        self._baseline    = {}
        self._initialized = False

    def rebuild_baseline(self) -> int:
        """Re-scan directory and reset baseline. Returns file count."""
        self._baseline    = self._snapshot()
        self._initialized = True
        return len(self._baseline)

    def scan(self) -> None:
        """Diff current state vs baseline; push observations to queue."""
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory, exist_ok=True)

        if not self._initialized:
            self.rebuild_baseline()
            return                  # first scan builds baseline silently

        current = self._snapshot()
        now     = time.time()

        base_paths    = set(self._baseline.keys())
        current_paths = set(current.keys())

        # Deleted
        for path in base_paths - current_paths:
            self._record_change()
            self._queue.put({
                "source":   "FILE",
                "rule":     "FILE_DELETED",
                "severity": "HIGH",
                "path":     path,
                "old_hash": self._baseline[path],
                "new_hash": None,
                "detail":   f"File deleted: {path}",
            })

        # Created
        for path in current_paths - base_paths:
            self._record_change()
            ext      = Path(path).suffix.lower()
            severity = "HIGH" if ext in SUSPICIOUS_EXTENSIONS else "MEDIUM"
            self._queue.put({
                "source":   "FILE",
                "rule":     "FILE_CREATED",
                "severity": severity,
                "path":     path,
                "old_hash": None,
                "new_hash": current[path],
                "detail":   (
                    f"Suspicious executable file created: {path}"
                    if ext in SUSPICIOUS_EXTENSIONS
                    else f"New file created: {path}"
                ),
            })

        # Modified
        for path in base_paths & current_paths:
            if self._baseline[path] != current[path]:
                self._record_change()
                self._queue.put({
                    "source":   "FILE",
                    "rule":     "FILE_MODIFIED",
                    "severity": "MEDIUM",
                    "path":     path,
                    "old_hash": self._baseline[path],
                    "new_hash": current[path],
                    "detail":   f"File modified: {path}",
                })

        # Burst detection
        self._prune_change_times(now)
        if len(self._change_times) >= FILE_CHANGE_BURST_LIMIT:
            self._queue.put({
                "source":   "FILE",
                "rule":     "BURST_DETECTED",
                "severity": "CRITICAL",
                "path":     self.directory,
                "old_hash": None,
                "new_hash": None,
                "detail":   (
                    f"BURST: {len(self._change_times)} file changes "
                    f"in {FILE_CHANGE_BURST_WINDOW}s — possible ransomware/wiper"
                ),
            })

        self._baseline = current

    # ── Private ───────────────────────────────────────────────────────────────

    def _snapshot(self) -> Dict[str, str]:
        snap: Dict[str, str] = {}
        if not os.path.isdir(self.directory):
            return snap
        for root, dirs, files in os.walk(self.directory):
            dirs[:] = [d for d in dirs if d not in self._ignore_dirs]
            for fname in files:
                fpath  = os.path.abspath(os.path.join(root, fname))
                digest = _sha256(fpath)
                if digest:
                    snap[fpath] = digest
        return snap

    def _record_change(self) -> None:
        self._change_times.append(time.time())

    def _prune_change_times(self, now: float) -> None:
        cutoff = now - FILE_CHANGE_BURST_WINDOW
        while self._change_times and self._change_times[0] < cutoff:
            self._change_times.popleft()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 – Network Monitor
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Connection:
    local_addr:  str
    remote_addr: str
    state:       str
    pid:         str = ""


def _parse_proc_net(path: str) -> List[Connection]:
    """Parse /proc/net/tcp or /proc/net/tcp6 on Linux."""
    conns: List[Connection] = []
    try:
        with open(path, "r") as fh:
            lines = fh.readlines()[1:]   # skip header
        for line in lines:
            parts = line.split()
            if len(parts) < 4:
                continue
            local_hex  = parts[1]
            remote_hex = parts[2]
            state_hex  = parts[3]

            def decode_addr(hex_addr: str) -> str:
                try:
                    addr_part, port_part = hex_addr.split(":")
                    # Linux stores IPv4 in little-endian hex
                    ip_int = int(addr_part, 16)
                    ip_str = ".".join(str((ip_int >> (8 * i)) & 0xFF) for i in range(4))
                    port   = int(port_part, 16)
                    return f"{ip_str}:{port}"
                except (ValueError, IndexError):
                    return hex_addr

            state_map = {
                "01": "ESTABLISHED", "02": "SYN_SENT", "03": "SYN_RECV",
                "04": "FIN_WAIT1",   "05": "FIN_WAIT2","06": "TIME_WAIT",
                "07": "CLOSE",       "08": "CLOSE_WAIT","09": "LAST_ACK",
                "0A": "LISTEN",      "0B": "CLOSING",
            }
            state = state_map.get(state_hex.upper(), state_hex)
            conns.append(Connection(
                local_addr  = decode_addr(local_hex),
                remote_addr = decode_addr(remote_hex),
                state       = state,
            ))
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return conns


def _get_connections_netstat() -> List[Connection]:
    """Fallback: parse `netstat` output (cross-platform)."""
    conns: List[Connection] = []
    try:
        if PLATFORM == "Windows":
            args = ["netstat", "-ano"]
        else:
            args = ["netstat", "-tnp"]

        result = subprocess.run(
            args, capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            # Typical format: Proto  Local  Foreign  State  [PID]
            if len(parts) >= 4 and parts[0].upper() in ("TCP", "TCP6"):
                local  = parts[1]
                remote = parts[2]
                state  = parts[3] if len(parts) > 3 else ""
                pid    = parts[-1] if PLATFORM == "Windows" else ""
                conns.append(Connection(
                    local_addr=local, remote_addr=remote,
                    state=state,      pid=pid,
                ))
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return conns


def get_connections() -> List[Connection]:
    """Return active TCP connections using the best available method."""
    if PLATFORM == "Linux":
        conns = _parse_proc_net("/proc/net/tcp") + _parse_proc_net("/proc/net/tcp6")
        return conns if conns else _get_connections_netstat()
    return _get_connections_netstat()


class NetworkMonitor:
    """
    Checks active connections for:
      1. Connections to known suspicious ports
      2. High volume of outbound connections (potential beaconing / C2)
      3. Connections to 0.0.0.0 or loopback on suspicious ports
    """

    def __init__(self, obs_queue: queue.Queue) -> None:
        self._queue          = obs_queue
        self._seen_suspicious: Set[str] = set()   # de-dupe already alerted
        self._connection_history: deque = deque() # (timestamp, remote) tuples
        self._beacon_window  = 60   # seconds
        self._beacon_limit   = 20   # unique remotes in window → beaconing alert

    def scan(self) -> None:
        """Inspect current connections and push observations."""
        conns = get_connections()
        now   = time.time()

        for conn in conns:
            if conn.state not in ("ESTABLISHED", "SYN_SENT", "CLOSE_WAIT"):
                continue

            remote = conn.remote_addr
            try:
                port = int(remote.rsplit(":", 1)[-1])
            except (ValueError, IndexError):
                continue

            # ── Rule 1: suspicious port ───────────────────────────────────
            if port in SUSPICIOUS_PORTS:
                key = f"{remote}:{conn.state}"
                if key not in self._seen_suspicious:
                    self._seen_suspicious.add(key)
                    self._queue.put({
                        "source":   "NETWORK",
                        "rule":     "SUSPICIOUS_PORT",
                        "severity": "HIGH",
                        "conn":     conn,
                        "detail":   (
                            f"Connection to suspicious port {port} "
                            f"({conn.local_addr} → {remote}) [{conn.state}]"
                        ),
                    })

            # Record for beaconing detection
            if conn.state == "ESTABLISHED":
                self._connection_history.append((now, remote))

        # ── Rule 2: beaconing / high-volume outbound ──────────────────────
        cutoff = now - self._beacon_window
        while self._connection_history and self._connection_history[0][0] < cutoff:
            self._connection_history.popleft()

        unique_remotes = {r for _, r in self._connection_history}
        if len(unique_remotes) > self._beacon_limit:
            self._queue.put({
                "source":   "NETWORK",
                "rule":     "BEACONING",
                "severity": "HIGH",
                "conn":     None,
                "detail":   (
                    f"Beaconing detected: {len(unique_remotes)} unique remote "
                    f"connections in last {self._beacon_window}s"
                ),
            })


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 – Detection Engine
# ══════════════════════════════════════════════════════════════════════════════

class DetectionEngine:
    """
    Consumes raw observations from the queue and converts them
    into structured Alert objects via the AlertManager.

    Also runs a behavioural correlation layer:
      • If the same process is flagged 3+ times in 60 s → escalate to CRITICAL
    """

    def __init__(self, obs_queue: queue.Queue, alert_manager: AlertManager) -> None:
        self._queue   = obs_queue
        self._am      = alert_manager
        # Track how often each process has been flagged for escalation
        self._proc_hit_times: Dict[str, deque] = defaultdict(deque)
        self._burst_notified: Set[str] = set()   # de-dupe burst alerts

    def process_observations(self, max_per_tick: int = 50) -> None:
        """Drain up to *max_per_tick* observations and emit alerts."""
        processed = 0
        while processed < max_per_tick:
            try:
                obs = self._queue.get_nowait()
            except queue.Empty:
                break
            self._dispatch(obs)
            processed += 1

    # ── Internal dispatch ─────────────────────────────────────────────────────

    def _dispatch(self, obs: dict) -> None:
        source = obs.get("source", "UNKNOWN")
        if   source == "PROCESS": self._handle_process(obs)
        elif source == "FILE":    self._handle_file(obs)
        elif source == "NETWORK": self._handle_network(obs)

    # ── Process observations ──────────────────────────────────────────────────

    def _handle_process(self, obs: dict) -> None:
        rule = obs["rule"]
        proc: ProcessInfo = obs["proc"]

        # Escalation tracking
        self._track_process_hits(proc.name, obs["severity"])

        if rule == "BLACKLIST_HIT":
            response = (
                f"[SIMULATED] Process '{proc.name}' (PID {proc.pid}) "
                "would be TERMINATED and quarantined."
            )
            self._am.add(
                alert_type  = "PROCESS",
                severity    = "CRITICAL",
                title       = "Blacklisted Process Detected",
                description = obs["detail"],
                affected    = f"{proc.name} (PID {proc.pid}, user={proc.user})",
                response    = response,
            )

        elif rule == "SUSPICIOUS_CMD":
            self._am.add(
                alert_type  = "PROCESS",
                severity    = "HIGH",
                title       = "Suspicious Command-Line Pattern",
                description = obs["detail"],
                affected    = f"{proc.name} (PID {proc.pid})",
                response    = "[SIMULATED] Process flagged for human review.",
            )

        elif rule == "HIGH_CPU":
            self._am.add(
                alert_type  = "PROCESS",
                severity    = "MEDIUM",
                title       = "High CPU Process",
                description = obs["detail"],
                affected    = f"{proc.name} (PID {proc.pid})",
                response    = "[SIMULATED] Resource usage logged.",
            )

        elif rule == "NEW_PROCESS":
            self._am.add(
                alert_type  = "PROCESS",
                severity    = "INFO",
                title       = "New Process Spawned",
                description = obs["detail"],
                affected    = f"{proc.name} (PID {proc.pid})",
            )

    def _track_process_hits(self, name: str, severity: str) -> None:
        """
        Escalate to CRITICAL if the same process is flagged 3+ times in 60 s.
        """
        if severity == "INFO":
            return
        now    = time.time()
        times  = self._proc_hit_times[name]
        times.append(now)
        cutoff = now - 60
        while times and times[0] < cutoff:
            times.popleft()

        key = f"ESCALATE:{name}"
        if len(times) >= 3 and key not in self._burst_notified:
            self._burst_notified.add(key)
            self._am.add(
                alert_type  = "BEHAVIORAL",
                severity    = "CRITICAL",
                title       = "Repeated Process Alerts – Escalated",
                description = (
                    f"Process '{name}' triggered {len(times)} alerts "
                    "within 60 seconds. Possible persistence / evasion."
                ),
                affected    = name,
                response    = "[SIMULATED] Incident ticket would be auto-created.",
            )

    # ── File observations ─────────────────────────────────────────────────────

    def _handle_file(self, obs: dict) -> None:
        rule = obs["rule"]
        path = obs.get("path", "unknown")

        if rule == "FILE_DELETED":
            self._am.add(
                alert_type  = "FILE",
                severity    = "HIGH",
                title       = "File Deleted",
                description = obs["detail"],
                affected    = path,
                response    = "[SIMULATED] Deletion event logged for forensics.",
            )

        elif rule == "FILE_CREATED":
            ext  = Path(path).suffix.lower()
            sus  = ext in SUSPICIOUS_EXTENSIONS
            self._am.add(
                alert_type  = "FILE",
                severity    = obs["severity"],
                title       = "Suspicious Executable Created" if sus else "New File Created",
                description = obs["detail"],
                affected    = path,
                response    = (
                    "[SIMULATED] Executable quarantined pending review."
                    if sus else ""
                ),
            )

        elif rule == "FILE_MODIFIED":
            old = obs.get("old_hash", "")[:12] if obs.get("old_hash") else "N/A"
            new = obs.get("new_hash", "")[:12] if obs.get("new_hash") else "N/A"
            self._am.add(
                alert_type  = "FILE",
                severity    = "MEDIUM",
                title       = "File Modified",
                description = f"{obs['detail']}  [hash: {old}… → {new}…]",
                affected    = path,
            )

        elif rule == "BURST_DETECTED":
            key = f"BURST:{self._am.risk_score()}"   # rough de-dupe key
            self._am.add(
                alert_type  = "BEHAVIORAL",
                severity    = "CRITICAL",
                title       = "File Change Burst – Possible Ransomware/Wiper",
                description = obs["detail"],
                affected    = path,
                response    = (
                    "[SIMULATED] All write operations in monitored directory "
                    "would be SUSPENDED and snapshots triggered."
                ),
            )

    # ── Network observations ──────────────────────────────────────────────────

    def _handle_network(self, obs: dict) -> None:
        rule = obs["rule"]
        conn: Optional[Connection] = obs.get("conn")
        affected = f"{conn.local_addr} → {conn.remote_addr}" if conn else "network"

        if rule == "SUSPICIOUS_PORT":
            self._am.add(
                alert_type  = "NETWORK",
                severity    = "HIGH",
                title       = "Suspicious Outbound Connection",
                description = obs["detail"],
                affected    = affected,
                response    = "[SIMULATED] Connection would be BLOCKED by host firewall.",
            )

        elif rule == "BEACONING":
            self._am.add(
                alert_type  = "NETWORK",
                severity    = "HIGH",
                title       = "Beaconing / C2 Pattern Detected",
                description = obs["detail"],
                affected    = "network (multiple remotes)",
                response    = "[SIMULATED] Network isolation mode would be triggered.",
            )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 – EDR Daemon  (orchestrator)
# ══════════════════════════════════════════════════════════════════════════════

class EDRDaemon:
    """
    Runs all monitors in background threads.

    Thread layout
    ─────────────
    • process_thread  – calls ProcessMonitor.scan() every PROCESS_SCAN_INTERVAL s
    • file_thread     – calls FileMonitor.scan()    every FILE_SCAN_INTERVAL s
    • network_thread  – calls NetworkMonitor.scan() every NETWORK_SCAN_INTERVAL s
    • engine_thread   – drains obs queue and calls DetectionEngine every 2 s
    """

    def __init__(self, monitored_dir: str = "./monitored",
                 log_file: str = "edr_alerts.log") -> None:
        self._obs_queue     = queue.Queue(maxsize=4096)
        self.alert_manager  = AlertManager(log_file=log_file)
        self._proc_monitor  = ProcessMonitor(self._obs_queue)
        self._file_monitor  = FileMonitor(self._obs_queue, monitored_dir)
        self._net_monitor   = NetworkMonitor(self._obs_queue)
        self._engine        = DetectionEngine(self._obs_queue, self.alert_manager)
        self._running       = threading.Event()
        self._threads: List[threading.Thread] = []

    # ── Configuration ─────────────────────────────────────────────────────────

    def set_monitored_dir(self, path: str) -> None:
        self._file_monitor.set_directory(path)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        self._threads = [
            threading.Thread(target=self._loop_process, daemon=True, name="proc-mon"),
            threading.Thread(target=self._loop_file,    daemon=True, name="file-mon"),
            threading.Thread(target=self._loop_network, daemon=True, name="net-mon"),
            threading.Thread(target=self._loop_engine,  daemon=True, name="det-eng"),
        ]
        for t in self._threads:
            t.start()

    def stop(self) -> None:
        self._running.clear()

    def is_running(self) -> bool:
        return self._running.is_set()

    def rebuild_file_baseline(self) -> int:
        return self._file_monitor.rebuild_baseline()

    # ── Thread targets ────────────────────────────────────────────────────────

    def _loop_process(self) -> None:
        while self._running.is_set():
            try:
                self._proc_monitor.scan()
            except Exception as exc:
                self.alert_manager.add(
                    "PROCESS", "LOW", "Process Monitor Error",
                    str(exc), "process_monitor",
                )
            time.sleep(PROCESS_SCAN_INTERVAL)

    def _loop_file(self) -> None:
        while self._running.is_set():
            try:
                self._file_monitor.scan()
            except Exception as exc:
                self.alert_manager.add(
                    "FILE", "LOW", "File Monitor Error",
                    str(exc), "file_monitor",
                )
            time.sleep(FILE_SCAN_INTERVAL)

    def _loop_network(self) -> None:
        while self._running.is_set():
            try:
                self._net_monitor.scan()
            except Exception as exc:
                self.alert_manager.add(
                    "NETWORK", "LOW", "Network Monitor Error",
                    str(exc), "network_monitor",
                )
            time.sleep(NETWORK_SCAN_INTERVAL)

    def _loop_engine(self) -> None:
        while self._running.is_set():
            self._engine.process_observations()
            time.sleep(2)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 – CLI / Interactive Menu
# ══════════════════════════════════════════════════════════════════════════════

def _clear() -> None:
    os.system("cls" if sys.platform == "win32" else "clear")


def _bar(width: int = 68) -> str:
    return C["dim"] + "─" * width + C["reset"]


def _header(subtitle: str = "") -> None:
    _clear()
    print(C["bold"] + C["cyan"] + "═" * 68 + C["reset"])
    print(C["bold"] + C["cyan"] +
          f"  {'ENDPOINT DETECTION TOOL  (EDR Simulation)':^64}" + C["reset"])
    if subtitle:
        print(C["dim"] + f"  {subtitle:^64}" + C["reset"])
    print(C["bold"] + C["cyan"] + "═" * 68 + C["reset"])


def _risk_colour(score: int) -> str:
    if score >= 100: return C["red"]   + C["bold"]
    if score >= 50:  return C["red"]
    if score >= 20:  return C["yellow"]
    return C["green"]


def _print_alert_row(alert: Alert, index: Optional[int] = None) -> None:
    sev_c  = SEV_COLOUR.get(alert.severity, "")
    idx    = f"{C['dim']}[{index:>4}]{C['reset']} " if index is not None else ""
    print(
        f"  {idx}"
        f"{sev_c}{alert.severity:<8}{C['reset']} "
        f"{C['cyan']}{alert.alert_type:<10}{C['reset']} "
        f"{C['dim']}{alert.timestamp}{C['reset']}  "
        f"{C['bold']}{alert.title}{C['reset']}"
    )
    print(f"  {'':>18}{C['dim']}{alert.affected[:60]}{C['reset']}")
    if alert.description != alert.title:
        print(f"  {'':>18}{alert.description[:72]}")
    if alert.response:
        print(f"  {'':>18}{C['yellow']}{alert.response[:72]}{C['reset']}")
    print()


def _status_bar(daemon: EDRDaemon) -> None:
    summary = daemon.alert_manager.get_summary()
    score   = summary["risk_score"]
    sc      = _risk_colour(score)
    running = (C["green"] + "● RUNNING" if daemon.is_running()
               else C["red"] + "● STOPPED") + C["reset"]
    print(_bar())
    print(
        f"  Status: {running}   "
        f"Risk Score: {sc}{score}{C['reset']}   "
        f"Alerts: {C['bold']}{summary['total']}{C['reset']}"
    )
    by_sev = summary.get("by_severity", {})
    parts  = [
        f"{SEV_COLOUR.get(s,'')}{s}={v}{C['reset']}"
        for s, v in sorted(by_sev.items(), key=lambda x: SEV_SCORE.get(x[0], 0), reverse=True)
    ]
    if parts:
        print(f"  Severity breakdown: {'  '.join(parts)}")
    print(_bar())


def menu_main(daemon: EDRDaemon) -> None:
    """Top-level interactive menu."""
    while True:
        _header("Main Menu")
        _status_bar(daemon)
        print(f"""
  {C['bold']}1.{C['reset']}  {'Start monitoring' if not daemon.is_running() else 'Stop  monitoring'}
  {C['bold']}2.{C['reset']}  View alerts
  {C['bold']}3.{C['reset']}  Configure monitored directory
  {C['bold']}4.{C['reset']}  Rebuild file baseline
  {C['bold']}5.{C['reset']}  Clear alert history
  {C['bold']}6.{C['reset']}  Export alerts to JSON
  {C['bold']}7.{C['reset']}  Live alert feed  (press Enter to return)
  {C['bold']}0.{C['reset']}  Exit
""")
        choice = input("  Select option: ").strip()

        if choice == "1":
            if daemon.is_running():
                daemon.stop()
                print(f"\n  {C['yellow']}Monitoring stopped.{C['reset']}")
            else:
                daemon.start()
                print(f"\n  {C['green']}Monitoring started.{C['reset']}")
            time.sleep(1)

        elif choice == "2":
            menu_view_alerts(daemon)

        elif choice == "3":
            menu_configure_directory(daemon)

        elif choice == "4":
            count = daemon.rebuild_file_baseline()
            print(f"\n  {C['green']}Baseline rebuilt: {count} file(s) indexed.{C['reset']}")
            time.sleep(1.5)

        elif choice == "5":
            confirm = input("  Clear ALL alerts? (yes/no): ").strip().lower()
            if confirm == "yes":
                daemon.alert_manager.clear()
                print(f"  {C['yellow']}Alert history cleared.{C['reset']}")
                time.sleep(1)

        elif choice == "6":
            menu_export_json(daemon)

        elif choice == "7":
            menu_live_feed(daemon)

        elif choice == "0":
            daemon.stop()
            print(f"\n  {C['cyan']}EDR Daemon stopped. Goodbye.{C['reset']}\n")
            sys.exit(0)


def menu_view_alerts(daemon: EDRDaemon) -> None:
    """Paginated alert viewer with severity filter."""
    PAGE   = 5
    offset = 0
    filt   = None   # None = all severities

    while True:
        _header("Alert Viewer")
        all_alerts = daemon.alert_manager.get_all()

        # Apply filter
        if filt:
            visible = [a for a in all_alerts if a.severity == filt]
        else:
            visible = all_alerts

        total = len(visible)
        page  = visible[offset: offset + PAGE]

        if not page:
            print(f"\n  {C['dim']}No alerts to display.{C['reset']}\n")
        else:
            print(f"\n  Showing {offset+1}–{min(offset+PAGE, total)} of {total}  "
                  f"{'(filter: ' + filt + ')' if filt else ''}\n")
            for i, alert in enumerate(page, start=offset + 1):
                _print_alert_row(alert, index=alert.alert_id)

        print(_bar())
        print(
            f"  [n]ext  [p]rev  "
            f"[f]ilter ({filt or 'none'})  "
            f"[a]ll  [b]ack"
        )
        cmd = input("  > ").strip().lower()

        if cmd == "n":
            if offset + PAGE < total:
                offset += PAGE
        elif cmd == "p":
            offset = max(0, offset - PAGE)
        elif cmd == "f":
            filt   = input("  Severity (INFO/LOW/MEDIUM/HIGH/CRITICAL): ").strip().upper()
            filt   = filt if filt in SEV_SCORE else None
            offset = 0
        elif cmd == "a":
            filt   = None
            offset = 0
        elif cmd == "b":
            return


def menu_configure_directory(daemon: EDRDaemon) -> None:
    _header("Configure Monitored Directory")
    current = daemon._file_monitor.directory
    print(f"\n  Current directory: {C['cyan']}{current}{C['reset']}\n")
    new_dir = input("  Enter new directory path (blank to keep current): ").strip()
    if new_dir:
        if not os.path.isdir(new_dir):
            try:
                os.makedirs(new_dir, exist_ok=True)
                print(f"  {C['yellow']}Directory created: {new_dir}{C['reset']}")
            except OSError as exc:
                print(f"  {C['red']}Error: {exc}{C['reset']}")
                time.sleep(1.5)
                return
        daemon.set_monitored_dir(new_dir)
        print(f"  {C['green']}Monitoring directory set to: {new_dir}{C['reset']}")
    time.sleep(1.5)


def menu_export_json(daemon: EDRDaemon) -> None:
    path = input("  Export path (default: edr_alerts_export.json): ").strip()
    path = path or "edr_alerts_export.json"
    try:
        data = {
            "exported_at": datetime.now().isoformat(),
            "summary":     daemon.alert_manager.get_summary(),
            "alerts":      [a.to_dict() for a in daemon.alert_manager.get_all()],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        print(f"  {C['green']}Exported {len(data['alerts'])} alerts → {path}{C['reset']}")
    except OSError as exc:
        print(f"  {C['red']}Export failed: {exc}{C['reset']}")
    time.sleep(1.5)


def menu_live_feed(daemon: EDRDaemon) -> None:
    """
    Continuously refresh showing the most recent alerts.
    Press Enter to return to main menu.
    """
    # Use a non-blocking input trick via a thread
    stop_feed = threading.Event()

    def _wait_enter() -> None:
        input()
        stop_feed.set()

    input_thread = threading.Thread(target=_wait_enter, daemon=True)
    input_thread.start()

    last_count = 0
    while not stop_feed.is_set():
        alerts = daemon.alert_manager.get_recent(12)
        count  = daemon.alert_manager.get_summary()["total"]

        _header("Live Alert Feed  –  press Enter to return")
        _status_bar(daemon)

        if alerts:
            print(f"\n  {C['bold']}Recent Alerts:{C['reset']}\n")
            for a in alerts:
                _print_alert_row(a, index=a.alert_id)
        else:
            print(f"\n  {C['dim']}Waiting for alerts…{C['reset']}\n")

        if count != last_count:
            last_count = count

        time.sleep(3)

    stop_feed.set()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 – CLI argument parsing & entry point
# ══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="endpoint_detection_tool",
        description="Basic EDR Simulation – pure Python stdlib",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--dir",      default="./monitored",  metavar="PATH",
                   help="Directory to monitor for file changes (default: ./monitored)")
    p.add_argument("--log-file", default="edr_alerts.log", metavar="PATH",
                   help="Alert log file path (default: edr_alerts.log)")
    p.add_argument("--autostart", action="store_true",
                   help="Start monitoring immediately without waiting for menu input")
    p.add_argument("--version",  action="version", version=f"EDR Tool v{VERSION}")
    return p.parse_args()


def main() -> None:
    args   = parse_args()
    daemon = EDRDaemon(monitored_dir=args.dir, log_file=args.log_file)

    # Ensure monitored directory exists
    os.makedirs(args.dir, exist_ok=True)

    if args.autostart:
        daemon.start()
        print(f"{C['green']}EDR monitoring auto-started.{C['reset']}")

    try:
        menu_main(daemon)
    except KeyboardInterrupt:
        daemon.stop()
        print(f"\n\n{C['cyan']}Interrupted – EDR Daemon stopped.{C['reset']}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()