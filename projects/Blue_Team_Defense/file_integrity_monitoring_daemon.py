#!/usr/bin/env python3
"""
============================================================
  File Integrity Monitoring (FIM) Daemon
  Author : Senior Python / Cybersecurity Engineer
  Python : 3.8+  |  Dependencies : stdlib only
============================================================

Usage
-----
  python file_integrity_monitoring_daemon.py [OPTIONS]

Options
-------
  --dir       <path>    Directory to monitor      (default: ./monitored)
  --interval  <secs>    Scan interval in seconds  (default: 5)
  --baseline            Rebuild the baseline and exit
  --baseline-file <p>   Path to JSON baseline     (default: ./fim_baseline.json)
  --log-file  <path>    Path to alert log file    (default: ./alerts.log)
  --ignore-ext <exts>   Comma-separated extensions to ignore  e.g. .tmp,.log
  --ignore-dir <dirs>   Comma-separated sub-dirs  to ignore   e.g. __pycache__,.git
  --no-save             Do NOT persist baseline to disk
  --help                Show this help message

Examples
--------
  # First run – creates baseline and starts monitoring
  python file_integrity_monitoring_daemon.py

  # Monitor a custom directory every 10 seconds
  python file_integrity_monitoring_daemon.py --dir /etc --interval 10

  # Re-build baseline only (no monitoring loop)
  python file_integrity_monitoring_daemon.py --baseline

  # Ignore temp files and the cache directory
  python file_integrity_monitoring_daemon.py --ignore-ext .tmp,.bak --ignore-dir __pycache__
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
VERSION          = "1.0.0"
DEFAULT_DIR      = "./monitored"
DEFAULT_INTERVAL = 5          # seconds between scans
DEFAULT_BASELINE = "./fim_baseline.json"
DEFAULT_LOG      = "./alerts.log"
HASH_ALGO        = "sha256"
BUFFER_SIZE      = 65_536     # 64 KiB – efficient for large files

# ANSI colour codes (gracefully degrade on Windows without ANSI support)
_ANSI = sys.platform != "win32" or os.environ.get("TERM")
RED    = "\033[91m" if _ANSI else ""
YELLOW = "\033[93m" if _ANSI else ""
GREEN  = "\033[92m" if _ANSI else ""
CYAN   = "\033[96m" if _ANSI else ""
BOLD   = "\033[1m"  if _ANSI else ""
RESET  = "\033[0m"  if _ANSI else ""
DIM    = "\033[2m"  if _ANSI else ""

# Event types
EVT_MODIFIED = "MODIFIED"
EVT_CREATED  = "CREATED"
EVT_DELETED  = "DELETED"

# ──────────────────────────────────────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────────────────────────────────────

def setup_logger(log_file: str) -> logging.Logger:
    """
    Configure a dual-output logger:
      • StreamHandler  → console  (INFO level, plain text)
      • FileHandler    → log_file (DEBUG level, timestamped)
    """
    logger = logging.getLogger("FIM")
    logger.setLevel(logging.DEBUG)

    # Console handler – we do our own coloured printing, so silence it
    # (alerts are printed via _alert(); this handler covers internal debug msgs)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(logging.Formatter("%(message)s"))

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s",
                          datefmt="%Y-%m-%d %H:%M:%S")
    )

    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


# Module-level placeholder; replaced in main()
log: logging.Logger = logging.getLogger("FIM")

# ──────────────────────────────────────────────────────────────────────────────
# Hashing
# ──────────────────────────────────────────────────────────────────────────────

def compute_hash(filepath: str) -> Optional[str]:
    """
    Compute the SHA-256 hash of a file.

    Returns
    -------
    str  – hex-digest string on success
    None – if the file cannot be read (permission error, race condition, etc.)
    """
    h = hashlib.new(HASH_ALGO)
    try:
        with open(filepath, "rb") as fh:
            while chunk := fh.read(BUFFER_SIZE):
                h.update(chunk)
        return h.hexdigest()
    except PermissionError:
        log.warning("Permission denied: %s", filepath)
    except FileNotFoundError:
        pass          # file disappeared between directory walk and open
    except OSError as exc:
        log.warning("OS error reading %s: %s", filepath, exc)
    return None

# ──────────────────────────────────────────────────────────────────────────────
# Directory scanning
# ──────────────────────────────────────────────────────────────────────────────

def should_ignore(
    path: str,
    ignore_exts: Set[str],
    ignore_dirs: Set[str],
    monitored_root: str,
) -> bool:
    """
    Return True when *path* matches any ignore rule.

    Ignore rules
    ------------
    • ignore_exts : file extension is in the set  (e.g. {'.tmp', '.log'})
    • ignore_dirs : any path component matches    (e.g. {'__pycache__', '.git'})
    """
    p = Path(path)

    # Extension filter
    if p.suffix.lower() in ignore_exts:
        return True

    # Directory component filter – check every part of the relative path
    try:
        relative = p.relative_to(monitored_root)
    except ValueError:
        relative = p

    for part in relative.parts[:-1]:   # exclude filename itself
        if part in ignore_dirs:
            return True

    return False


def scan_directory(
    directory: str,
    ignore_exts: Set[str],
    ignore_dirs: Set[str],
) -> Dict[str, str]:
    """
    Recursively walk *directory* and return a mapping of
    ``{absolute_path: sha256_hex}``.

    Files that cannot be hashed are skipped with a warning.
    """
    snapshot: Dict[str, str] = {}

    if not os.path.isdir(directory):
        log.error("Monitored directory does not exist: %s", directory)
        return snapshot

    for root, dirs, files in os.walk(directory):
        # Prune ignored sub-directories in-place (prevents descent)
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for filename in files:
            filepath = os.path.abspath(os.path.join(root, filename))

            if should_ignore(filepath, ignore_exts, ignore_dirs, directory):
                continue

            digest = compute_hash(filepath)
            if digest is not None:
                snapshot[filepath] = digest

    return snapshot

# ──────────────────────────────────────────────────────────────────────────────
# Baseline persistence
# ──────────────────────────────────────────────────────────────────────────────

def save_baseline(snapshot: Dict[str, str], baseline_file: str) -> None:
    """Persist the baseline snapshot to a JSON file."""
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "algorithm":  HASH_ALGO,
        "files":      snapshot,
    }
    try:
        with open(baseline_file, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        log.info("Baseline saved → %s  (%d file(s))", baseline_file, len(snapshot))
    except OSError as exc:
        log.error("Cannot write baseline file %s: %s", baseline_file, exc)


def load_baseline(baseline_file: str) -> Optional[Dict[str, str]]:
    """
    Load a previously saved baseline from disk.

    Returns the ``{path: hash}`` dict, or None if the file is missing/corrupt.
    """
    if not os.path.isfile(baseline_file):
        return None
    try:
        with open(baseline_file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        files = payload.get("files", {})
        log.info(
            "Baseline loaded ← %s  (%d file(s), created %s)",
            baseline_file,
            len(files),
            payload.get("created_at", "unknown"),
        )
        return files
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Baseline file corrupt or unreadable: %s", exc)
        return None

# ──────────────────────────────────────────────────────────────────────────────
# Change detection
# ──────────────────────────────────────────────────────────────────────────────

def compare_snapshots(
    baseline: Dict[str, str],
    current: Dict[str, str],
) -> list:
    """
    Diff two snapshots and return a list of change events.

    Each event is a dict with keys:
      event_type : str          – MODIFIED | CREATED | DELETED
      path       : str          – absolute file path
      old_hash   : str | None   – previous hash (None for CREATED)
      new_hash   : str | None   – current hash  (None for DELETED)
      timestamp  : str          – ISO-8601 timestamp
    """
    events = []
    ts = datetime.now().isoformat(timespec="seconds")

    baseline_paths = set(baseline.keys())
    current_paths  = set(current.keys())

    # ── Deleted files ────────────────────────────────────────────────────────
    for path in baseline_paths - current_paths:
        events.append({
            "event_type": EVT_DELETED,
            "path":       path,
            "old_hash":   baseline[path],
            "new_hash":   None,
            "timestamp":  ts,
        })

    # ── New files ────────────────────────────────────────────────────────────
    for path in current_paths - baseline_paths:
        events.append({
            "event_type": EVT_CREATED,
            "path":       path,
            "old_hash":   None,
            "new_hash":   current[path],
            "timestamp":  ts,
        })

    # ── Modified files ───────────────────────────────────────────────────────
    for path in baseline_paths & current_paths:
        if baseline[path] != current[path]:
            events.append({
                "event_type": EVT_MODIFIED,
                "path":       path,
                "old_hash":   baseline[path],
                "new_hash":   current[path],
                "timestamp":  ts,
            })

    return events

# ──────────────────────────────────────────────────────────────────────────────
# Alert rendering
# ──────────────────────────────────────────────────────────────────────────────

_EVENT_COLOUR = {
    EVT_MODIFIED: YELLOW,
    EVT_CREATED:  GREEN,
    EVT_DELETED:  RED,
}
_EVENT_ICON = {
    EVT_MODIFIED: "✎",
    EVT_CREATED:  "+",
    EVT_DELETED:  "✗",
}


def _format_hash(h: Optional[str]) -> str:
    """Return a short display form of a hash, or N/A."""
    return h[:16] + "…" if h else "N/A"


def print_alert(event: dict) -> None:
    """Print a coloured alert to stdout."""
    colour    = _EVENT_COLOUR.get(event["event_type"], "")
    icon      = _EVENT_ICON.get(event["event_type"], "?")
    evt_label = f"{colour}{BOLD}[{icon} {event['event_type']:8s}]{RESET}"

    print(
        f"  {evt_label}  "
        f"{DIM}{event['timestamp']}{RESET}  "
        f"{CYAN}{event['path']}{RESET}"
    )

    if event["event_type"] == EVT_MODIFIED:
        print(
            f"             "
            f"old: {DIM}{_format_hash(event['old_hash'])}{RESET}  "
            f"new: {BOLD}{_format_hash(event['new_hash'])}{RESET}"
        )


def log_alert(event: dict) -> None:
    """Write a structured alert line to the log file via the logger."""
    if event["event_type"] == EVT_MODIFIED:
        msg = (
            f"[{event['event_type']}] {event['path']} | "
            f"old={event['old_hash']} | new={event['new_hash']}"
        )
    elif event["event_type"] == EVT_CREATED:
        msg = f"[{event['event_type']}] {event['path']} | hash={event['new_hash']}"
    else:  # DELETED
        msg = f"[{event['event_type']}] {event['path']} | last_hash={event['old_hash']}"

    # Use WARNING level so it stands out in the log file
    log.warning(msg)

# ──────────────────────────────────────────────────────────────────────────────
# Terminal UI helpers
# ──────────────────────────────────────────────────────────────────────────────

def clear_screen() -> None:
    """Cross-platform terminal clear."""
    os.system("cls" if sys.platform == "win32" else "clear")


def print_header(
    monitored_dir: str,
    interval: int,
    baseline_file: str,
    scan_count: int,
    last_scan: str,
) -> None:
    """Print the persistent status header at the top of each scan."""
    width = 70
    bar   = "─" * width
    print(f"{BOLD}{CYAN}{'FIM DAEMON':^{width}}{RESET}")
    print(f"{DIM}{bar}{RESET}")
    print(f"  {'Directory':<18} {CYAN}{monitored_dir}{RESET}")
    print(f"  {'Baseline file':<18} {DIM}{baseline_file}{RESET}")
    print(f"  {'Interval':<18} {interval}s")
    print(f"  {'Scan #':<18} {scan_count}")
    print(f"  {'Last scan':<18} {DIM}{last_scan}{RESET}")
    print(f"{DIM}{bar}{RESET}\n")


def print_status(file_count: int, alert_count: int) -> None:
    """Print a scan-summary footer line."""
    colour = RED if alert_count else GREEN
    status = f"{colour}{BOLD}{alert_count} alert(s){RESET}"
    print(
        f"\n  {DIM}Files monitored: {file_count}  │  {RESET}{status}"
        f"  {DIM}(Ctrl-C to stop){RESET}\n"
    )

# ──────────────────────────────────────────────────────────────────────────────
# Core daemon logic
# ──────────────────────────────────────────────────────────────────────────────

def build_baseline(
    directory: str,
    baseline_file: str,
    ignore_exts: Set[str],
    ignore_dirs: Set[str],
    persist: bool,
) -> Dict[str, str]:
    """
    Scan *directory*, optionally save to disk, and return the snapshot.
    """
    print(f"\n{BOLD}Building baseline for:{RESET} {CYAN}{directory}{RESET}\n")
    snapshot = scan_directory(directory, ignore_exts, ignore_dirs)

    if not snapshot:
        print(f"{YELLOW}  Warning: no files found in {directory!r}.{RESET}")
    else:
        print(f"  {GREEN}✔{RESET}  Hashed {len(snapshot)} file(s).\n")

    if persist:
        save_baseline(snapshot, baseline_file)

    return snapshot


def run_monitoring_loop(
    directory: str,
    baseline: Dict[str, str],
    baseline_file: str,
    interval: int,
    ignore_exts: Set[str],
    ignore_dirs: Set[str],
    persist: bool,
) -> None:
    """
    Main monitoring loop.

    1. Wait *interval* seconds.
    2. Scan the directory.
    3. Compare with baseline.
    4. Print / log any alerts.
    5. Update baseline to current snapshot (rolling baseline).
    6. Repeat.
    """
    scan_count  = 0
    total_alerts = 0

    print(
        f"\n{BOLD}Monitoring started.{RESET}  "
        f"Press {BOLD}Ctrl-C{RESET} to stop.\n"
    )
    time.sleep(1)   # brief pause so user can read the startup message

    try:
        while True:
            time.sleep(interval)
            scan_count += 1
            last_scan  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # ── Scan ─────────────────────────────────────────────────────────
            current = scan_directory(directory, ignore_exts, ignore_dirs)

            # ── Diff ─────────────────────────────────────────────────────────
            events = compare_snapshots(baseline, current)

            # ── Render ───────────────────────────────────────────────────────
            clear_screen()
            print_header(
                monitored_dir=directory,
                interval=interval,
                baseline_file=baseline_file,
                scan_count=scan_count,
                last_scan=last_scan,
            )

            if events:
                total_alerts += len(events)
                for evt in events:
                    print_alert(evt)
                    log_alert(evt)
            else:
                print(f"  {GREEN}✔  No changes detected.{RESET}")

            print_status(file_count=len(current), alert_count=len(events))

            # ── Roll baseline forward ─────────────────────────────────────
            # Using a rolling baseline means we track *incremental* changes
            # rather than always comparing to the original state.
            # Remove the next two lines if you want a fixed baseline.
            baseline = current
            if persist and events:
                save_baseline(baseline, baseline_file)

    except KeyboardInterrupt:
        print(
            f"\n\n{BOLD}FIM Daemon stopped.{RESET}  "
            f"Total alerts raised this session: {BOLD}{total_alerts}{RESET}\n"
        )

# ──────────────────────────────────────────────────────────────────────────────
# CLI argument parsing
# ──────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="file_integrity_monitoring_daemon",
        description="File Integrity Monitoring (FIM) Daemon – pure Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        add_help=False,   # we add our own --help so it prints nicer
    )

    parser.add_argument(
        "--dir", default=DEFAULT_DIR, metavar="PATH",
        help=f"Directory to monitor (default: {DEFAULT_DIR})",
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL, metavar="SECS",
        help=f"Seconds between scans (default: {DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "--baseline", action="store_true",
        help="Rebuild baseline snapshot and exit (no monitoring loop)",
    )
    parser.add_argument(
        "--baseline-file", default=DEFAULT_BASELINE, metavar="PATH",
        help=f"JSON file to persist baseline (default: {DEFAULT_BASELINE})",
    )
    parser.add_argument(
        "--log-file", default=DEFAULT_LOG, metavar="PATH",
        help=f"Alert log file (default: {DEFAULT_LOG})",
    )
    parser.add_argument(
        "--ignore-ext", default="", metavar="EXTS",
        help="Comma-separated file extensions to ignore, e.g. .tmp,.bak",
    )
    parser.add_argument(
        "--ignore-dir", default="", metavar="DIRS",
        help="Comma-separated directory names to ignore, e.g. __pycache__,.git",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Do NOT persist the baseline to disk",
    )
    parser.add_argument(
        "--version", action="version", version=f"FIM Daemon v{VERSION}",
    )
    parser.add_argument(
        "--help", "-h", action="help",
        help="Show this help message and exit",
    )

    return parser.parse_args()


def normalise_set(raw: str, lower: bool = True) -> Set[str]:
    """Split a comma-separated string into a set, stripping whitespace."""
    if not raw.strip():
        return set()
    items = {s.strip() for s in raw.split(",") if s.strip()}
    return {s.lower() for s in items} if lower else items

# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    # ── Bootstrap logger ─────────────────────────────────────────────────────
    global log
    log = setup_logger(args.log_file)

    # ── Normalise ignore sets ─────────────────────────────────────────────────
    ignore_exts = normalise_set(args.ignore_ext, lower=True)
    ignore_dirs = normalise_set(args.ignore_dir, lower=False)

    # Add default developer noise
    ignore_dirs |= {"__pycache__", ".git", ".svn", ".hg", "node_modules", ".idea"}

    # ── Ensure monitored directory exists ────────────────────────────────────
    monitored_dir = os.path.abspath(args.dir)
    if not os.path.isdir(monitored_dir):
        print(
            f"{YELLOW}Directory {monitored_dir!r} not found – creating it.{RESET}"
        )
        os.makedirs(monitored_dir, exist_ok=True)

    persist = not args.no_save

    # ──────────────────────────────────────────────────────────────────────────
    # Mode: rebuild baseline only
    # ──────────────────────────────────────────────────────────────────────────
    if args.baseline:
        build_baseline(
            directory=monitored_dir,
            baseline_file=args.baseline_file,
            ignore_exts=ignore_exts,
            ignore_dirs=ignore_dirs,
            persist=persist,
        )
        return

    # ──────────────────────────────────────────────────────────────────────────
    # Mode: monitor (default)
    # ──────────────────────────────────────────────────────────────────────────
    clear_screen()

    # ── Attempt to load existing baseline from disk ───────────────────────────
    baseline = load_baseline(args.baseline_file) if persist else None

    # ── Build baseline if none available ─────────────────────────────────────
    if baseline is None:
        print(
            f"{YELLOW}No baseline found.{RESET}  "
            "Performing initial scan …\n"
        )
        baseline = build_baseline(
            directory=monitored_dir,
            baseline_file=args.baseline_file,
            ignore_exts=ignore_exts,
            ignore_dirs=ignore_dirs,
            persist=persist,
        )

    # ── Start the monitoring loop ─────────────────────────────────────────────
    run_monitoring_loop(
        directory=monitored_dir,
        baseline=baseline,
        baseline_file=args.baseline_file,
        interval=args.interval,
        ignore_exts=ignore_exts,
        ignore_dirs=ignore_dirs,
        persist=persist,
    )


if __name__ == "__main__":
    main()