"""
disk_usage_analyzer.py
A Python OOP program that analyzes disk usage of directories and files.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Iterator, Optional


# ══════════════════════════════════════════════════════════════
# Enums & Constants
# ══════════════════════════════════════════════════════════════

class ItemType(Enum):
    FILE      = auto()
    DIRECTORY = auto()
    SYMLINK   = auto()
    OTHER     = auto()


class SortKey(Enum):
    SIZE = "size"
    NAME = "name"
    EXT  = "extension"

    @classmethod
    def from_str(cls, s: str) -> "SortKey":
        mapping = {"size": cls.SIZE, "name": cls.NAME, "ext": cls.EXT}
        key = mapping.get(s.lower())
        if key is None:
            raise ValueError(f"Unknown sort key '{s}'. Choose: size | name | ext")
        return key


# Friendly size thresholds
_KB = 1_024
_MB = _KB * 1_024
_GB = _MB * 1_024

# Extension → category map
EXT_CATEGORIES: dict[str, str] = {
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".xls": "Documents", ".xlsx": "Documents", ".ppt": "Documents",
    ".pptx": "Documents", ".txt": "Documents", ".md": "Documents",
    ".odt": "Documents", ".ods": "Documents", ".csv": "Documents",
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    ".bmp": "Images", ".svg": "Images", ".webp": "Images", ".ico": "Images",
    ".tiff": "Images", ".tif": "Images", ".heic": "Images",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio", ".aac": "Audio",
    ".ogg": "Audio", ".m4a": "Audio", ".wma": "Audio",
    # Video
    ".mp4": "Video", ".mkv": "Video", ".avi": "Video", ".mov": "Video",
    ".wmv": "Video", ".flv": "Video", ".webm": "Video", ".m4v": "Video",
    # Code / Scripts
    ".py": "Code", ".js": "Code", ".ts": "Code", ".html": "Code",
    ".css": "Code", ".java": "Code", ".c": "Code", ".cpp": "Code",
    ".h": "Code", ".go": "Code", ".rs": "Code", ".rb": "Code",
    ".php": "Code", ".sh": "Code", ".bat": "Code", ".ps1": "Code",
    ".sql": "Code", ".r": "Code", ".swift": "Code", ".kt": "Code",
    # Archives
    ".zip": "Archives", ".tar": "Archives", ".gz": "Archives",
    ".bz2": "Archives", ".xz": "Archives", ".7z": "Archives",
    ".rar": "Archives", ".tgz": "Archives",
    # Data
    ".json": "Data", ".xml": "Data", ".yaml": "Data", ".yml": "Data",
    ".toml": "Data", ".ini": "Data", ".cfg": "Data", ".log": "Data",
    ".db": "Data", ".sqlite": "Data",
    # Executables / Binaries
    ".exe": "Executables", ".dll": "Executables", ".so": "Executables",
    ".bin": "Executables", ".dmg": "Executables", ".apk": "Executables",
}


# ══════════════════════════════════════════════════════════════
# Custom Exceptions
# ══════════════════════════════════════════════════════════════

class ScanError(Exception):
    """Raised when a directory cannot be scanned."""


class ValidationError(Exception):
    """Raised for invalid user input."""


# ══════════════════════════════════════════════════════════════
# FileItem  — data model
# ══════════════════════════════════════════════════════════════

@dataclass
class FileItem:
    """
    Represents a single filesystem entry (file, directory, symlink).
    """
    name:      str
    path:      Path
    size:      int          # bytes; for directories, the recursive total
    item_type: ItemType
    extension: str = ""     # lower-case, empty for directories
    depth:     int = 0      # nesting level relative to root scan path

    # ── Factories ────────────────────────────────────────────

    @classmethod
    def from_path(cls, p: Path, size: int, depth: int = 0) -> "FileItem":
        if p.is_symlink():
            itype = ItemType.SYMLINK
        elif p.is_dir():
            itype = ItemType.DIRECTORY
        elif p.is_file():
            itype = ItemType.FILE
        else:
            itype = ItemType.OTHER
        ext = p.suffix.lower() if itype == ItemType.FILE else ""
        return cls(
            name=p.name,
            path=p,
            size=size,
            item_type=itype,
            extension=ext,
            depth=depth,
        )

    # ── Helpers ──────────────────────────────────────────────

    @property
    def category(self) -> str:
        """Human-readable file category derived from extension."""
        if self.item_type == ItemType.DIRECTORY:
            return "Directory"
        if self.item_type == ItemType.SYMLINK:
            return "Symlink"
        return EXT_CATEGORIES.get(self.extension, "Other")

    def human_size(self) -> str:
        return _fmt_size(self.size)

    def __str__(self) -> str:
        marker = "📁" if self.item_type == ItemType.DIRECTORY else "📄"
        return f"{marker} {self.name}  ({self.human_size()})"


# ══════════════════════════════════════════════════════════════
# DirectoryScanner
# ══════════════════════════════════════════════════════════════

class DirectoryScanner:
    """
    Recursively walks a directory tree and collects FileItem objects.

    Attributes:
        root           -- the top-level Path being scanned
        follow_symlinks -- whether to follow symbolic links
        skip_hidden     -- whether to skip dot-files/dot-dirs
        max_depth       -- maximum recursion depth (None = unlimited)
    """

    def __init__(
        self,
        root: str | Path,
        follow_symlinks: bool = False,
        skip_hidden:     bool = False,
        max_depth:       Optional[int] = None,
    ):
        self.root           = Path(root).resolve()
        self.follow_symlinks = follow_symlinks
        self.skip_hidden    = skip_hidden
        self.max_depth      = max_depth

        self._items:       list[FileItem] = []
        self._errors:      list[str]      = []
        self._scan_time:   float          = 0.0
        self._total_files: int            = 0
        self._total_dirs:  int            = 0

    # ── Public API ───────────────────────────────────────────

    def scan(self) -> list[FileItem]:
        """
        Perform the scan and return the list of collected FileItem objects.
        Clears any previous scan results.
        """
        if not self.root.exists():
            raise ScanError(f"Path does not exist: {self.root}")
        if not self.root.is_dir():
            raise ScanError(f"Path is not a directory: {self.root}")
        if not os.access(self.root, os.R_OK):
            raise ScanError(f"No read permission for: {self.root}")

        self._items.clear()
        self._errors.clear()
        self._total_files = 0
        self._total_dirs  = 0

        t0 = time.perf_counter()
        self._walk(self.root, depth=0)
        self._scan_time = time.perf_counter() - t0
        return self._items

    @property
    def items(self) -> list[FileItem]:
        return self._items

    @property
    def errors(self) -> list[str]:
        return self._errors

    @property
    def scan_time(self) -> float:
        return self._scan_time

    @property
    def total_files(self) -> int:
        return self._total_files

    @property
    def total_dirs(self) -> int:
        return self._total_dirs

    # ── Private helpers ──────────────────────────────────────

    def _walk(self, directory: Path, depth: int) -> int:
        """
        Recursively walk *directory*, accumulate FileItems, and return the
        total byte size of the subtree.
        """
        if self.max_depth is not None and depth > self.max_depth:
            return 0

        subtree_size = 0

        try:
            entries = list(directory.iterdir())
        except PermissionError:
            self._errors.append(f"Permission denied: {directory}")
            return 0
        except OSError as exc:
            self._errors.append(f"OS error scanning {directory}: {exc}")
            return 0

        for entry in entries:
            if self.skip_hidden and entry.name.startswith("."):
                continue

            if entry.is_symlink() and not self.follow_symlinks:
                # Record the symlink but don't follow it
                try:
                    sz = entry.lstat().st_size
                except OSError:
                    sz = 0
                item = FileItem.from_path(entry, sz, depth)
                self._items.append(item)
                subtree_size += sz
                continue

            if entry.is_dir():
                dir_size = self._walk(entry, depth + 1)
                item = FileItem.from_path(entry, dir_size, depth)
                self._items.append(item)
                subtree_size  += dir_size
                self._total_dirs += 1

            elif entry.is_file():
                try:
                    sz = entry.stat().st_size
                except OSError:
                    sz = 0
                item = FileItem.from_path(entry, sz, depth)
                self._items.append(item)
                subtree_size  += sz
                self._total_files += 1

        return subtree_size


# ══════════════════════════════════════════════════════════════
# UsageAnalyzer
# ══════════════════════════════════════════════════════════════

class UsageAnalyzer:
    """
    Processes a list of FileItem objects and produces analysis results:
      - Total disk usage
      - Largest files / directories
      - Usage grouped by file type / category
      - Distribution by size bucket
    """

    def __init__(self, items: list[FileItem], root: Path):
        self._items = items
        self._root  = root

    # ── Totals ───────────────────────────────────────────────

    @property
    def total_size(self) -> int:
        """Total bytes consumed by all *files* (not double-counting dirs)."""
        return sum(i.size for i in self._items if i.item_type == ItemType.FILE)

    @property
    def total_items(self) -> int:
        return len(self._items)

    @property
    def file_count(self) -> int:
        return sum(1 for i in self._items if i.item_type == ItemType.FILE)

    @property
    def dir_count(self) -> int:
        return sum(1 for i in self._items if i.item_type == ItemType.DIRECTORY)

    # ── Top N lists ──────────────────────────────────────────

    def largest_files(self, n: int = 10, sort: SortKey = SortKey.SIZE) -> list[FileItem]:
        files = [i for i in self._items if i.item_type == ItemType.FILE]
        return self._sort(files, sort)[:n]

    def largest_directories(self, n: int = 10, sort: SortKey = SortKey.SIZE) -> list[FileItem]:
        dirs = [i for i in self._items if i.item_type == ItemType.DIRECTORY]
        return self._sort(dirs, sort)[:n]

    def all_items_sorted(self, sort: SortKey = SortKey.SIZE) -> list[FileItem]:
        return self._sort(self._items, sort)

    # ── Groupings ────────────────────────────────────────────

    def usage_by_category(self) -> dict[str, dict]:
        """
        Returns a dict keyed by category name with keys:
            size   (total bytes)
            count  (file count)
            pct    (percentage of total)
        Sorted descending by size.
        """
        totals: dict[str, list[int]] = {}   # cat → [size_sum, count]
        grand = self.total_size or 1

        for item in self._items:
            if item.item_type != ItemType.FILE:
                continue
            cat = item.category
            if cat not in totals:
                totals[cat] = [0, 0]
            totals[cat][0] += item.size
            totals[cat][1] += 1

        result = {}
        for cat, (sz, cnt) in sorted(totals.items(), key=lambda x: x[1][0], reverse=True):
            result[cat] = {"size": sz, "count": cnt, "pct": sz / grand * 100}
        return result

    def usage_by_extension(self) -> dict[str, dict]:
        """Same as usage_by_category but keyed by raw extension."""
        totals: dict[str, list[int]] = {}
        grand = self.total_size or 1

        for item in self._items:
            if item.item_type != ItemType.FILE:
                continue
            ext = item.extension or "(no ext)"
            if ext not in totals:
                totals[ext] = [0, 0]
            totals[ext][0] += item.size
            totals[ext][1] += 1

        result = {}
        for ext, (sz, cnt) in sorted(totals.items(), key=lambda x: x[1][0], reverse=True):
            result[ext] = {"size": sz, "count": cnt, "pct": sz / grand * 100}
        return result

    def size_distribution(self) -> dict[str, int]:
        """Count files in human-readable size buckets."""
        buckets = {
            "< 1 KB":        0,
            "1 KB – 100 KB": 0,
            "100 KB – 1 MB": 0,
            "1 MB – 100 MB": 0,
            "100 MB – 1 GB": 0,
            "> 1 GB":        0,
        }
        for item in self._items:
            if item.item_type != ItemType.FILE:
                continue
            sz = item.size
            if sz < _KB:
                buckets["< 1 KB"] += 1
            elif sz < 100 * _KB:
                buckets["1 KB – 100 KB"] += 1
            elif sz < _MB:
                buckets["100 KB – 1 MB"] += 1
            elif sz < 100 * _MB:
                buckets["1 MB – 100 MB"] += 1
            elif sz < _GB:
                buckets["100 MB – 1 GB"] += 1
            else:
                buckets["> 1 GB"] += 1
        return buckets

    # ── Internal ─────────────────────────────────────────────

    @staticmethod
    def _sort(items: list[FileItem], key: SortKey) -> list[FileItem]:
        if key == SortKey.SIZE:
            return sorted(items, key=lambda i: i.size, reverse=True)
        if key == SortKey.NAME:
            return sorted(items, key=lambda i: i.name.lower())
        if key == SortKey.EXT:
            return sorted(items, key=lambda i: (i.extension, i.size), reverse=True)
        return items


# ══════════════════════════════════════════════════════════════
# ReportGenerator
# ══════════════════════════════════════════════════════════════

_COL = 72          # total report width
_BAR = 30          # max bar chart width


class ReportGenerator:
    """
    Formats UsageAnalyzer results and prints them to stdout (or a stream).
    """

    def __init__(self, analyzer: UsageAnalyzer, scanner: DirectoryScanner, stream=None):
        self._a  = analyzer
        self._sc = scanner
        self._out = stream or sys.stdout

    # ── Public: full report ──────────────────────────────────

    def print_full_report(
        self,
        top_n:    int     = 10,
        sort_key: SortKey = SortKey.SIZE,
        show_ext: bool    = False,
    ) -> None:
        self._header("DISK USAGE REPORT")
        self._summary()
        self._separator()
        self._section_largest_files(top_n, sort_key)
        self._separator()
        self._section_largest_dirs(top_n, sort_key)
        self._separator()
        self._section_category_breakdown()
        if show_ext:
            self._separator()
            self._section_extension_breakdown(top_n)
        self._separator()
        self._section_size_distribution()
        self._separator()
        if self._sc.errors:
            self._section_errors()
        self._footer()

    # ── Sections ─────────────────────────────────────────────

    def _summary(self) -> None:
        a  = self._a
        sc = self._sc
        self._line(f"  Root path   : {sc.root}")
        self._line(f"  Scan time   : {sc.scan_time:.3f}s")
        self._line(f"  Files       : {a.file_count:,}")
        self._line(f"  Directories : {a.dir_count:,}")
        self._line(f"  Total size  : {_fmt_size(a.total_size)}  ({a.total_size:,} bytes)")
        if sc.errors:
            self._line(f"  Skipped     : {len(sc.errors)} item(s) (permission denied / errors)")

    def _section_largest_files(self, n: int, sort: SortKey) -> None:
        self._subheader(f"TOP {n} LARGEST FILES  [sorted by {sort.value}]")
        files = self._a.largest_files(n, sort)
        if not files:
            self._line("  (no files found)")
            return
        self._item_table(files)

    def _section_largest_dirs(self, n: int, sort: SortKey) -> None:
        self._subheader(f"TOP {n} LARGEST DIRECTORIES  [sorted by {sort.value}]")
        dirs = self._a.largest_directories(n, sort)
        if not dirs:
            self._line("  (no subdirectories found)")
            return
        self._item_table(dirs)

    def _section_category_breakdown(self) -> None:
        self._subheader("USAGE BY FILE CATEGORY")
        cats = self._a.usage_by_category()
        if not cats:
            self._line("  (no files found)")
            return
        max_sz = max(v["size"] for v in cats.values()) or 1
        for cat, info in cats.items():
            bar = _bar(info["size"], max_sz, _BAR)
            self._line(
                f"  {cat:<16} {_fmt_size(info['size']):>10}  "
                f"{info['pct']:5.1f}%  {bar}  ({info['count']:,} files)"
            )

    def _section_extension_breakdown(self, n: int) -> None:
        self._subheader(f"TOP {n} EXTENSIONS BY USAGE")
        exts = self._a.usage_by_extension()
        items = list(exts.items())[:n]
        if not items:
            self._line("  (no files found)")
            return
        max_sz = items[0][1]["size"] if items else 1
        for ext, info in items:
            bar = _bar(info["size"], max_sz, _BAR)
            self._line(
                f"  {ext:<12} {_fmt_size(info['size']):>10}  "
                f"{info['pct']:5.1f}%  {bar}  ({info['count']:,} files)"
            )

    def _section_size_distribution(self) -> None:
        self._subheader("FILE SIZE DISTRIBUTION")
        dist   = self._a.size_distribution()
        total  = self._a.file_count or 1
        max_ct = max(dist.values()) or 1
        for bucket, cnt in dist.items():
            bar = _bar(cnt, max_ct, _BAR)
            pct = cnt / total * 100
            self._line(f"  {bucket:<18} {cnt:>6,} files  {pct:5.1f}%  {bar}")

    def _section_errors(self) -> None:
        self._subheader("SCAN WARNINGS / ERRORS")
        for err in self._sc.errors[:20]:
            self._line(f"  ⚠  {err}")
        if len(self._sc.errors) > 20:
            self._line(f"  … and {len(self._sc.errors) - 20} more.")

    # ── Formatting helpers ───────────────────────────────────

    def _item_table(self, items: list[FileItem]) -> None:
        total = self._a.total_size or 1
        for rank, item in enumerate(items, 1):
            pct    = item.size / total * 100
            marker = "📁" if item.item_type == ItemType.DIRECTORY else "📄"
            # Truncate long paths for readability
            rel = _truncate(str(item.path), 44)
            self._line(
                f"  {rank:>2}. {marker} {_fmt_size(item.size):>10}  "
                f"{pct:5.1f}%  {rel}"
            )

    def _header(self, title: str) -> None:
        self._line("═" * _COL)
        self._line(f"  {title}")
        self._line("═" * _COL)

    def _footer(self) -> None:
        self._line("═" * _COL)

    def _subheader(self, title: str) -> None:
        self._line(f"\n  ── {title} ──")

    def _separator(self) -> None:
        self._line("─" * _COL)

    def _line(self, text: str = "") -> None:
        print(text, file=self._out)


# ══════════════════════════════════════════════════════════════
# Utility functions
# ══════════════════════════════════════════════════════════════

def _fmt_size(n: int) -> str:
    """Return a human-readable file size string."""
    if n < _KB:
        return f"{n} B"
    if n < _MB:
        return f"{n / _KB:.1f} KB"
    if n < _GB:
        return f"{n / _MB:.1f} MB"
    return f"{n / _GB:.2f} GB"


def _bar(value: int, maximum: int, width: int) -> str:
    """Draw a simple ASCII bar proportional to value/maximum."""
    if maximum == 0:
        filled = 0
    else:
        filled = round(value / maximum * width)
    return "█" * filled + "░" * (width - filled)


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    keep = max_len - 3
    return "…" + s[-keep:]


def _prompt(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"  {msg}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return val or default


def _prompt_int(msg: str, default: int, lo: int = 1, hi: int = 100) -> int:
    while True:
        raw = _prompt(msg, str(default))
        try:
            val = int(raw)
            if lo <= val <= hi:
                return val
            print(f"  ⚠  Enter a number between {lo} and {hi}.")
        except ValueError:
            print("  ⚠  Please enter a valid integer.")


def _prompt_bool(msg: str, default: bool = False) -> bool:
    d = "y" if default else "n"
    raw = _prompt(f"{msg} (y/n)", d).lower()
    return raw in ("y", "yes", "1", "true")


# ══════════════════════════════════════════════════════════════
# Interactive console application
# ══════════════════════════════════════════════════════════════

BANNER = r"""
╔══════════════════════════════════════════════════════════════════════╗
║                    Disk Usage Analyzer  🗂                           ║
║        Scan directories, find heavy hitters, reclaim space.          ║
╚══════════════════════════════════════════════════════════════════════╝
"""


def _configure_scan() -> tuple[Path, dict]:
    """Interactive wizard to configure a scan. Returns (root_path, options)."""
    print("\n  ── Scan Configuration ──\n")

    # Root directory
    while True:
        raw = _prompt("Directory to analyze", str(Path.home()))
        p = Path(raw).expanduser().resolve()
        if p.exists() and p.is_dir():
            break
        print(f"  ⚠  '{p}' is not a valid directory. Try again.")

    # Options
    top_n        = _prompt_int("How many top items to show", 10, 1, 50)
    sort_raw     = _prompt("Sort by (size / name / ext)", "size")
    try:
        sort_key = SortKey.from_str(sort_raw)
    except ValueError as exc:
        print(f"  ⚠  {exc}  — defaulting to size.")
        sort_key = SortKey.SIZE

    max_depth_raw = _prompt("Max depth (leave blank for unlimited)", "")
    max_depth: Optional[int] = None
    if max_depth_raw:
        try:
            d = int(max_depth_raw)
            if d >= 0:
                max_depth = d
            else:
                print("  ⚠  Depth must be ≥ 0 — using unlimited.")
        except ValueError:
            print("  ⚠  Invalid depth — using unlimited.")

    skip_hidden  = _prompt_bool("Skip hidden files/directories?", True)
    follow_links = _prompt_bool("Follow symbolic links?", False)
    show_ext     = _prompt_bool("Show extension breakdown?", False)

    return p, {
        "top_n":        top_n,
        "sort_key":     sort_key,
        "max_depth":    max_depth,
        "skip_hidden":  skip_hidden,
        "follow_links": follow_links,
        "show_ext":     show_ext,
    }


def _run_analysis(root: Path, opts: dict) -> None:
    print(f"\n  ⏳  Scanning '{root}' …  (this may take a moment)\n")

    scanner = DirectoryScanner(
        root,
        follow_symlinks=opts["follow_links"],
        skip_hidden=opts["skip_hidden"],
        max_depth=opts["max_depth"],
    )

    try:
        items = scanner.scan()
    except ScanError as exc:
        print(f"\n  ✘  Scan failed: {exc}")
        return

    if not items:
        print("  ℹ  No items found in the specified directory.")
        return

    analyzer  = UsageAnalyzer(items, root)
    reporter  = ReportGenerator(analyzer, scanner)

    print()
    reporter.print_full_report(
        top_n=opts["top_n"],
        sort_key=opts["sort_key"],
        show_ext=opts["show_ext"],
    )


def _main_menu() -> str:
    print("\n  ── Main Menu ──")
    print("    1. Analyze a directory")
    print("    2. Quick scan (current working directory, defaults)")
    print("    0. Exit")
    try:
        return input("\n  Choose an option: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def main() -> None:
    print(BANNER)

    while True:
        choice = _main_menu()

        if choice == "0":
            print("\n  Goodbye. 👋\n")
            break

        elif choice == "1":
            try:
                root, opts = _configure_scan()
                _run_analysis(root, opts)
            except KeyboardInterrupt:
                print("\n\n  Scan interrupted.")

        elif choice == "2":
            root = Path.cwd()
            opts = {
                "top_n":       10,
                "sort_key":    SortKey.SIZE,
                "max_depth":   None,
                "skip_hidden": True,
                "follow_links": False,
                "show_ext":    False,
            }
            try:
                _run_analysis(root, opts)
            except KeyboardInterrupt:
                print("\n\n  Scan interrupted.")

        else:
            print("  ⚠  Unknown option. Please enter 0, 1, or 2.")


if __name__ == "__main__":
    main()