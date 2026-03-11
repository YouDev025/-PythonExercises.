"""
Log Analyzer
============
A modular, OOP-based tool for parsing and analyzing log files.

Supported log format (one entry per line):
    2024-01-15 08:23:11 [INFO]    AuthService   User 'admin' logged in successfully.
    2024-01-15 08:23:45 [WARNING] Database      Connection pool at 80% capacity.
    2024-01-15 08:24:02 [ERROR]   PaymentAPI    Timeout while contacting payment gateway.

Any line that does not match this format is collected as a parse warning and skipped.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────────────────────────────────────

class LogEntry:
    """Represents a single parsed log line."""

    VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def __init__(
        self,
        timestamp: datetime,
        log_level: str,
        source: str,
        message: str,
    ) -> None:
        self.__timestamp = timestamp
        self.__log_level = log_level.upper()
        self.__source = source.strip()
        self.__message = message.strip()

    # ── read-only properties ────────────────────────────────────────────────

    @property
    def timestamp(self) -> datetime:
        return self.__timestamp

    @property
    def log_level(self) -> str:
        return self.__log_level

    @property
    def source(self) -> str:
        return self.__source

    @property
    def message(self) -> str:
        return self.__message

    # ── helpers ─────────────────────────────────────────────────────────────

    def contains_keyword(self, keyword: str) -> bool:
        """Case-insensitive keyword search across source and message."""
        kw = keyword.lower()
        return kw in self.__message.lower() or kw in self.__source.lower()

    def __str__(self) -> str:
        ts = self.__timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{ts}  [{self.__log_level:<8}]  "
            f"{self.__source:<20}  {self.__message}"
        )

    def __repr__(self) -> str:
        return (
            f"LogEntry(timestamp={self.__timestamp!r}, "
            f"level={self.__log_level!r}, source={self.__source!r})"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Parser
# ─────────────────────────────────────────────────────────────────────────────

class LogParser:
    """
    Converts raw text lines into LogEntry objects.

    Expected format:
        YYYY-MM-DD HH:MM:SS [LEVEL] Source  Message text here
    """

    # Allow any amount of whitespace between fields; level is inside brackets.
    _PATTERN = re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"
        r"\s+\[(?P<level>[A-Z]+)\]"
        r"\s+(?P<source>\S+)"
        r"\s+(?P<message>.+)$"
    )
    _TS_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def parse_line(cls, line: str) -> LogEntry | None:
        """
        Parse a single log line.
        Returns a LogEntry on success, or None if the line does not match.
        """
        line = line.rstrip("\n").rstrip()
        if not line or line.startswith("#"):
            return None

        match = cls._PATTERN.match(line)
        if not match:
            return None

        try:
            timestamp = datetime.strptime(match["ts"].strip(), cls._TS_FORMAT)
        except ValueError:
            return None

        return LogEntry(
            timestamp=timestamp,
            log_level=match["level"],
            source=match["source"],
            message=match["message"].strip(),
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Analyzer
# ─────────────────────────────────────────────────────────────────────────────

class LogAnalyzer:
    """
    Loads a log file, stores parsed entries, and exposes analysis methods.
    """

    def __init__(self) -> None:
        self.__entries: list[LogEntry] = []
        self.__file_path: Path | None = None
        self.__parse_warnings: list[str] = []

    # ── properties ──────────────────────────────────────────────────────────

    @property
    def entry_count(self) -> int:
        return len(self.__entries)

    @property
    def file_path(self) -> Path | None:
        return self.__file_path

    @property
    def parse_warnings(self) -> list[str]:
        return list(self.__parse_warnings)

    # ── file loading ─────────────────────────────────────────────────────────

    def load(self, path: str | Path) -> None:
        """
        Read and parse a log file.  Replaces any previously loaded data.
        Raises FileNotFoundError or PermissionError on I/O problems.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: '{path}'")
        if not path.is_file():
            raise ValueError(f"Path is not a regular file: '{path}'")

        entries: list[LogEntry] = []
        warnings: list[str] = []

        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for lineno, raw in enumerate(fh, start=1):
                entry = LogParser.parse_line(raw)
                if entry is not None:
                    entries.append(entry)
                elif raw.strip() and not raw.strip().startswith("#"):
                    warnings.append(f"  Line {lineno:>5}: {raw.rstrip()}")

        self.__entries = entries
        self.__file_path = path
        self.__parse_warnings = warnings

    # ── query methods ────────────────────────────────────────────────────────

    def all_entries(self) -> list[LogEntry]:
        """Return a copy of all parsed log entries."""
        return list(self.__entries)

    def filter_by_level(self, level: str) -> list[LogEntry]:
        """Return entries whose log level matches (case-insensitive)."""
        level = level.upper()
        return [e for e in self.__entries if e.log_level == level]

    def search(self, keyword: str) -> list[LogEntry]:
        """Return entries whose source or message contains the keyword."""
        return [e for e in self.__entries if e.contains_keyword(keyword)]

    def level_counts(self) -> Counter:
        """Return a Counter mapping log level → occurrence count."""
        return Counter(e.log_level for e in self.__entries)

    def available_levels(self) -> list[str]:
        """Return the sorted list of distinct log levels found in the file."""
        return sorted(self.level_counts().keys())


# ─────────────────────────────────────────────────────────────────────────────
#  CLI helpers
# ─────────────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════╗
║            Log Analyzer  v1.0                        ║
║  Load and explore system / application log files.    ║
╚══════════════════════════════════════════════════════╝
"""

MENU = """
  [1]  Load a log file
  [2]  Display all log entries
  [3]  Filter by log level
  [4]  Search by keyword
  [5]  Show log-level counts
  [6]  Show unrecognised lines
  [q]  Quit
"""

DIVIDER = "─" * 70


def _print_entries(entries: list[LogEntry], label: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {label}  ({len(entries)} entr{'y' if len(entries) == 1 else 'ies'})")
    print(DIVIDER)
    if not entries:
        print("  (no matching entries)")
    else:
        for entry in entries:
            print(f"  {entry}")
    print(DIVIDER)


def _require_loaded(analyzer: LogAnalyzer) -> bool:
    if analyzer.file_path is None:
        print("\n  ⚠  No file loaded yet.  Choose option [1] first.\n")
        return False
    return True


def run_cli() -> None:
    print(BANNER)
    analyzer = LogAnalyzer()

    while True:
        print(MENU)
        try:
            choice = input("  Choose an option: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Goodbye!")
            break

        # ── 1: load file ──────────────────────────────────────────────────
        if choice == "1":
            raw_path = input("  Enter path to log file: ").strip()
            try:
                analyzer.load(raw_path)
                print(
                    f"\n  ✅  Loaded '{analyzer.file_path}'  —  "
                    f"{analyzer.entry_count} entries parsed."
                )
                if analyzer.parse_warnings:
                    print(
                        f"  ⚠   {len(analyzer.parse_warnings)} line(s) could not "
                        "be parsed (see option [6])."
                    )
            except (FileNotFoundError, ValueError, PermissionError) as exc:
                print(f"\n  ❌  {exc}\n")

        # ── 2: display all ────────────────────────────────────────────────
        elif choice == "2":
            if _require_loaded(analyzer):
                _print_entries(analyzer.all_entries(), "All log entries")

        # ── 3: filter by level ────────────────────────────────────────────
        elif choice == "3":
            if _require_loaded(analyzer):
                levels = analyzer.available_levels()
                if not levels:
                    print("\n  (no entries loaded)\n")
                    continue
                print(f"\n  Available levels: {', '.join(levels)}")
                level = input("  Enter log level to filter by: ").strip().upper()
                results = analyzer.filter_by_level(level)
                _print_entries(results, f"Entries with level [{level}]")

        # ── 4: keyword search ─────────────────────────────────────────────
        elif choice == "4":
            if _require_loaded(analyzer):
                keyword = input("  Enter keyword to search for: ").strip()
                if not keyword:
                    print("\n  ⚠  Keyword cannot be empty.\n")
                    continue
                results = analyzer.search(keyword)
                _print_entries(results, f"Entries matching '{keyword}'")

        # ── 5: level counts ───────────────────────────────────────────────
        elif choice == "5":
            if _require_loaded(analyzer):
                counts = analyzer.level_counts()
                total = sum(counts.values())
                print(f"\n{DIVIDER}")
                print(f"  Log-level summary  (total: {total})")
                print(DIVIDER)
                for level, count in sorted(counts.items()):
                    bar = "█" * min(count, 40)
                    print(f"  {level:<10}  {count:>5}  {bar}")
                print(DIVIDER)

        # ── 6: parse warnings ─────────────────────────────────────────────
        elif choice == "6":
            if _require_loaded(analyzer):
                warnings = analyzer.parse_warnings
                print(f"\n{DIVIDER}")
                print(f"  Unrecognised lines  ({len(warnings)})")
                print(DIVIDER)
                if not warnings:
                    print("  (all lines parsed successfully)")
                else:
                    for w in warnings:
                        print(w)
                print(DIVIDER)

        # ── quit ──────────────────────────────────────────────────────────
        elif choice in {"q", "quit", "exit"}:
            print("\n  Goodbye!\n")
            break

        else:
            print("\n  ⚠  Unrecognised option.  Please enter 1–6 or q.\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_cli()