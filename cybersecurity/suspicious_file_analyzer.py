"""
Suspicious File Analyzer
========================
Analyzes files for potentially suspicious characteristics using
heuristic checks: magic bytes, entropy, extension mismatches,
unusual sizes, embedded PE headers, and more.

Built with Python OOP: encapsulation, single-responsibility classes,
clean public APIs, and immutable result objects.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import stat
import struct
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Enums & constants
# ─────────────────────────────────────────────────────────────────────────────

class ThreatLevel(Enum):
    CLEAN       = "CLEAN"
    LOW         = "LOW"
    MEDIUM      = "MEDIUM"
    HIGH        = "HIGH"
    CRITICAL    = "CRITICAL"

    def score(self) -> int:
        return {"CLEAN": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}[self.value]


# Severity weights used by individual flags
SEVERITY_WEIGHT = {"info": 1, "low": 2, "medium": 4, "high": 7, "critical": 12}

# Thresholds: cumulative weight → ThreatLevel
_THRESHOLDS = [
    (0,  ThreatLevel.CLEAN),
    (2,  ThreatLevel.LOW),
    (5,  ThreatLevel.MEDIUM),
    (12, ThreatLevel.HIGH),
    (20, ThreatLevel.CRITICAL),
]


def _classify(total_weight: int) -> ThreatLevel:
    level = ThreatLevel.CLEAN
    for threshold, threat in _THRESHOLDS:
        if total_weight >= threshold:
            level = threat
    return level


# ─────────────────────────────────────────────────────────────────────────────
#  Known signatures
# ─────────────────────────────────────────────────────────────────────────────

# Magic bytes: (offset, bytes) → label
MAGIC_SIGNATURES: dict[tuple[int, bytes], str] = {
    (0, b"\x4d\x5a"):           "Windows PE/MZ executable",
    (0, b"\x7fELF"):            "ELF executable (Linux/Unix)",
    (0, b"\xca\xfe\xba\xbe"):   "Mach-O fat binary (macOS)",
    (0, b"\xfe\xed\xfa\xce"):   "Mach-O 32-bit binary",
    (0, b"\xfe\xed\xfa\xcf"):   "Mach-O 64-bit binary",
    (0, b"\x50\x4b\x03\x04"):   "ZIP archive",
    (0, b"\x52\x61\x72\x21"):   "RAR archive",
    (0, b"\x1f\x8b"):           "GZIP compressed data",
    (0, b"\x42\x5a\x68"):       "BZIP2 compressed data",
    (0, b"\x25\x50\x44\x46"):   "PDF document",
    (0, b"\x89\x50\x4e\x47"):   "PNG image",
    (0, b"\xff\xd8\xff"):       "JPEG image",
    (0, b"\x47\x49\x46\x38"):   "GIF image",
    (0, b"\x49\x49\x2a\x00"):   "TIFF image (little-endian)",
    (0, b"\x4d\x4d\x00\x2a"):   "TIFF image (big-endian)",
    (0, b"\xd0\xcf\x11\xe0"):   "Microsoft OLE2 (Office doc/xls/ppt)",
    (0, b"PK\x03\x04"):         "OOXML / Office Open XML (docx/xlsx)",
    (0, b"\x7b\x5c\x72\x74"):   "RTF document",
    (0, b"#!/"):                 "Shell script (shebang)",
    (0, b"#!"):                  "Script with shebang",
    (0, b"\x00\x00\x01\x00"):   "Windows ICO file",
    (0, b"MSCF"):               "Microsoft Cabinet (.cab)",
    (0, b"\x4c\x00\x00\x00"):   "Windows LNK shortcut",
}

# Extensions considered inherently executable / dangerous
DANGEROUS_EXTENSIONS: frozenset[str] = frozenset({
    ".exe", ".dll", ".sys", ".drv", ".scr", ".com", ".pif",
    ".bat", ".cmd", ".ps1", ".psm1", ".psd1", ".vbs", ".vbe",
    ".js",  ".jse", ".wsf", ".wsh", ".msi", ".msp", ".msc",
    ".hta", ".cpl", ".reg", ".inf", ".lnk", ".jar", ".app",
    ".sh",  ".bash", ".zsh", ".fish", ".rb",  ".py",
    ".elf", ".bin", ".run", ".deb", ".rpm",
})

# Extensions that should almost never be large files
SMALL_FILE_EXTENSIONS: frozenset[str] = frozenset({
    ".txt", ".cfg", ".ini", ".conf", ".log", ".csv", ".json",
    ".xml", ".yaml", ".yml", ".toml", ".md", ".rst",
})

# Double-extension patterns (e.g. invoice.pdf.exe)
_DOUBLE_EXT_RE = re.compile(
    r"\.(pdf|doc|docx|xls|xlsx|txt|jpg|jpeg|png|gif|zip)\.(exe|bat|cmd|vbs|ps1|scr|com|pif|js|jar)$",
    re.IGNORECASE,
)

# Suspicious strings to search in file bytes (first 64 KB)
SUSPICIOUS_BYTE_PATTERNS: list[tuple[bytes, str, str]] = [
    (b"cmd.exe",            "CMD shell reference",              "medium"),
    (b"powershell",         "PowerShell reference",             "medium"),
    (b"WScript.Shell",      "WScript.Shell COM object",         "high"),
    (b"HKEY_",              "Registry key reference",           "medium"),
    (b"CreateRemoteThread", "Remote thread injection API",      "high"),
    (b"VirtualAlloc",       "Memory allocation API",            "medium"),
    (b"ShellExecute",       "ShellExecute API",                 "medium"),
    (b"URLDownloadToFile",  "File download from URL",           "high"),
    (b"socket",             "Network socket reference",         "low"),
    (b"eval(",              "Dynamic code evaluation",          "medium"),
    (b"exec(",              "Dynamic execution call",           "medium"),
    (b"base64",             "Base64 encoding reference",        "low"),
    (b"mimikatz",           "Mimikatz credential harvester",    "critical"),
    (b"metasploit",         "Metasploit framework reference",   "critical"),
    (b"meterpreter",        "Meterpreter payload string",       "critical"),
    (b"/etc/shadow",        "Unix shadow password file path",   "high"),
    (b"/etc/passwd",        "Unix passwd file path",            "medium"),
]


# ─────────────────────────────────────────────────────────────────────────────
#  SuspicionFlag  – single detected indicator
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SuspicionFlag:
    code:        str
    description: str
    severity:    str   # "info" | "low" | "medium" | "high" | "critical"

    @property
    def weight(self) -> int:
        return SEVERITY_WEIGHT.get(self.severity, 1)

    def __str__(self) -> str:
        sev = self.severity.upper()
        return f"[{sev}] {self.description}"


# ─────────────────────────────────────────────────────────────────────────────
#  FileSample  – encapsulated file metadata
# ─────────────────────────────────────────────────────────────────────────────

class FileSample:
    """
    Immutable snapshot of a file's metadata.
    All attributes are private; access via read-only properties.
    """

    def __init__(self, file_path: str | Path) -> None:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: '{file_path}'")
        if not path.is_file():
            raise ValueError(f"Path is not a regular file: '{file_path}'")

        stat_result = path.stat()

        self._file_path:  Path     = path
        self._file_name:  str      = path.name
        self._extension:  str      = path.suffix.lower()
        self._file_size:  int      = stat_result.st_size        # bytes
        self._created_at: float    = stat_result.st_ctime
        self._modified_at: float   = stat_result.st_mtime
        self._is_hidden:  bool     = path.name.startswith(".")
        self._is_executable: bool  = bool(stat_result.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        self._permissions: str     = oct(stat_result.st_mode)[-4:]
        self._hash_md5:   str      = ""
        self._hash_sha1:  str      = ""
        self._hash_sha256: str     = ""
        self._magic_label: str     = ""
        self._entropy:    float    = 0.0
        self._header_bytes: bytes  = b""

    # ── read-only properties ─────────────────────────────────────────
    @property
    def file_path(self) -> Path:        return self._file_path
    @property
    def file_name(self) -> str:         return self._file_name
    @property
    def extension(self) -> str:         return self._extension
    @property
    def file_size(self) -> int:         return self._file_size
    @property
    def created_at(self) -> float:      return self._created_at
    @property
    def modified_at(self) -> float:     return self._modified_at
    @property
    def is_hidden(self) -> bool:        return self._is_hidden
    @property
    def is_executable(self) -> bool:    return self._is_executable
    @property
    def permissions(self) -> str:       return self._permissions
    @property
    def hash_md5(self) -> str:          return self._hash_md5
    @property
    def hash_sha1(self) -> str:         return self._hash_sha1
    @property
    def hash_sha256(self) -> str:       return self._hash_sha256
    @property
    def magic_label(self) -> str:       return self._magic_label
    @property
    def entropy(self) -> float:         return self._entropy
    @property
    def header_bytes(self) -> bytes:    return self._header_bytes

    def size_human(self) -> str:
        """Human-readable file size."""
        size = self._file_size
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def age_days(self) -> float:
        return (time.time() - self._modified_at) / 86400

    def __repr__(self) -> str:
        return f"FileSample(name={self._file_name!r}, size={self.size_human()})"


# ─────────────────────────────────────────────────────────────────────────────
#  AnalysisResult  – immutable result from FileAnalyzer
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AnalysisResult:
    sample:       FileSample
    threat_level: ThreatLevel
    total_weight: int
    flags:        tuple[SuspicionFlag, ...]
    analysed_at:  datetime = field(default_factory=datetime.now)

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        s = self.sample
        lines.append(f"  File        : {s.file_path}")
        lines.append(f"  Size        : {s.size_human()}  ({s.file_size:,} bytes)")
        lines.append(f"  Extension   : {s.extension or '(none)'}")
        lines.append(f"  Magic type  : {s.magic_label or '(unrecognised)'}")
        lines.append(f"  Entropy     : {s.entropy:.4f}  {'⚠ high randomness' if s.entropy > 7.2 else ''}")
        lines.append(f"  SHA-256     : {s.hash_sha256}")
        lines.append(f"  MD5         : {s.hash_md5}")
        lines.append(f"  Permissions : {s.permissions}  {'[executable]' if s.is_executable else ''}")
        lines.append(f"  Hidden file : {'Yes' if s.is_hidden else 'No'}")
        mod_str = datetime.fromtimestamp(s.modified_at).strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"  Modified    : {mod_str}  ({s.age_days():.0f} days ago)")
        lines.append("")
        lines.append(f"  Threat level: {self.threat_level.value}  (score {self.total_weight})")
        lines.append(f"  Flags ({len(self.flags)}):")
        if self.flags:
            for f in self.flags:
                lines.append(f"    {f}")
        else:
            lines.append("    None — no suspicious indicators detected.")
        return lines


# ─────────────────────────────────────────────────────────────────────────────
#  FileAnalyzer  – all analysis logic
# ─────────────────────────────────────────────────────────────────────────────

class FileAnalyzer:
    """
    Scans a FileSample and returns an AnalysisResult.

    Checks performed:
    1. Hash computation (MD5 / SHA-1 / SHA-256)
    2. Magic-byte identification
    3. Shannon entropy calculation
    4. Dangerous / double extension detection
    5. Extension ↔ magic-byte mismatch
    6. Suspicious byte-string patterns
    7. File size anomalies
    8. Executable bit & hidden file flags
    9. Embedded PE header in non-executable file
    10. Very recent creation time (< 10 seconds ago)
    """

    _CHUNK = 65_536   # 64 KB read chunk for hashing

    # ── public API ────────────────────────────────────────────────────

    def scan(self, sample: FileSample) -> AnalysisResult:
        """Read the file, populate sample internals, run all checks."""
        try:
            raw = self._read_file(sample)
        except (PermissionError, OSError) as exc:
            flags = (SuspicionFlag("READ_ERROR", f"Cannot read file: {exc}", "info"),)
            return AnalysisResult(sample, ThreatLevel.CLEAN, 0, flags)

        self._populate_hashes(sample, raw)
        self._populate_magic(sample, raw)
        self._populate_entropy(sample, raw)
        sample._header_bytes = raw[:32]

        flags = list(self._check_extension(sample))
        flags += self._check_magic_mismatch(sample)
        flags += self._check_entropy(sample)
        flags += self._check_size(sample)
        flags += self._check_byte_patterns(sample, raw)
        flags += self._check_permissions(sample)
        flags += self._check_embedded_pe(sample, raw)
        flags += self._check_age(sample)

        weight = sum(f.weight for f in flags)
        level  = _classify(weight)

        return AnalysisResult(
            sample=sample,
            threat_level=level,
            total_weight=weight,
            flags=tuple(flags),
        )

    # ── file reading ──────────────────────────────────────────────────

    def _read_file(self, sample: FileSample) -> bytes:
        """Read up to 10 MB for analysis; store full size separately."""
        max_bytes = 10 * 1024 * 1024
        with open(sample.file_path, "rb") as fh:
            return fh.read(max_bytes)

    # ── hash computation ──────────────────────────────────────────────

    def _populate_hashes(self, sample: FileSample, raw: bytes) -> None:
        sample._hash_md5    = hashlib.md5(raw).hexdigest()
        sample._hash_sha1   = hashlib.sha1(raw).hexdigest()
        sample._hash_sha256 = hashlib.sha256(raw).hexdigest()

    # ── magic bytes ───────────────────────────────────────────────────

    def _populate_magic(self, sample: FileSample, raw: bytes) -> None:
        for (offset, sig), label in MAGIC_SIGNATURES.items():
            if raw[offset:offset + len(sig)] == sig:
                sample._magic_label = label
                return
        sample._magic_label = ""

    # ── Shannon entropy ───────────────────────────────────────────────

    @staticmethod
    def _populate_entropy(sample: FileSample, raw: bytes) -> None:
        if not raw:
            sample._entropy = 0.0
            return
        counts = Counter(raw)
        length = len(raw)
        entropy = -sum(
            (c / length) * math.log2(c / length)
            for c in counts.values() if c
        )
        sample._entropy = round(entropy, 6)

    # ── individual checks ─────────────────────────────────────────────

    def _check_extension(self, sample: FileSample) -> list[SuspicionFlag]:
        flags: list[SuspicionFlag] = []
        ext = sample.extension

        if ext in DANGEROUS_EXTENSIONS:
            flags.append(SuspicionFlag(
                "DANGEROUS_EXT",
                f"File has a dangerous/executable extension: '{ext}'",
                "medium",
            ))

        if _DOUBLE_EXT_RE.search(sample.file_name):
            flags.append(SuspicionFlag(
                "DOUBLE_EXTENSION",
                f"Double extension detected (masquerading technique): '{sample.file_name}'",
                "high",
            ))

        if not ext:
            flags.append(SuspicionFlag(
                "NO_EXTENSION",
                "File has no extension — unusual for most document types.",
                "low",
            ))

        return flags

    def _check_magic_mismatch(self, sample: FileSample) -> list[SuspicionFlag]:
        flags: list[SuspicionFlag] = []
        magic = sample.magic_label
        ext   = sample.extension

        if not magic:
            return flags

        # Image extension but executable magic
        if ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico"}:
            if any(k in magic for k in ("executable", "ELF", "Mach-O", "binary", "PE")):
                flags.append(SuspicionFlag(
                    "MAGIC_MISMATCH_IMAGE_EXE",
                    f"Image extension '{ext}' but file appears to be: {magic}",
                    "critical",
                ))

        # Document extension but executable magic
        if ext in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv"}:
            if any(k in magic for k in ("executable", "ELF", "Mach-O", "PE/MZ")):
                flags.append(SuspicionFlag(
                    "MAGIC_MISMATCH_DOC_EXE",
                    f"Document extension '{ext}' but file appears to be: {magic}",
                    "critical",
                ))

        # Archive claiming to be something else
        if ext not in {".zip", ".jar", ".apk", ".docx", ".xlsx", ".pptx", ".ooxml"}:
            if "ZIP" in magic or "RAR" in magic:
                flags.append(SuspicionFlag(
                    "MAGIC_MISMATCH_ARCHIVE",
                    f"Extension '{ext}' but file is actually an archive: {magic}",
                    "medium",
                ))

        return flags

    def _check_entropy(self, sample: FileSample) -> list[SuspicionFlag]:
        flags: list[SuspicionFlag] = []
        ent = sample.entropy

        # Very high entropy → packed/encrypted/compressed
        if ent > 7.8:
            flags.append(SuspicionFlag(
                "HIGH_ENTROPY_CRITICAL",
                f"Extremely high entropy ({ent:.4f}/8.0) — likely encrypted or packed payload.",
                "high",
            ))
        elif ent > 7.2:
            flags.append(SuspicionFlag(
                "HIGH_ENTROPY",
                f"High byte entropy ({ent:.4f}/8.0) — possible encryption or compression.",
                "medium",
            ))

        # Very low entropy on an "executable" → suspicious (all-zero padding?)
        if ent < 0.5 and sample.file_size > 512:
            flags.append(SuspicionFlag(
                "LOW_ENTROPY_LARGE",
                f"Very low entropy ({ent:.4f}) for a {sample.size_human()} file — unusual.",
                "low",
            ))

        return flags

    def _check_size(self, sample: FileSample) -> list[SuspicionFlag]:
        flags: list[SuspicionFlag] = []
        size = sample.file_size
        ext  = sample.extension

        if size == 0:
            flags.append(SuspicionFlag(
                "ZERO_SIZE",
                "File is empty (0 bytes).",
                "info",
            ))
            return flags

        # Suspiciously large for a text-like file
        if ext in SMALL_FILE_EXTENSIONS and size > 50 * 1024 * 1024:
            flags.append(SuspicionFlag(
                "OVERSIZED_TEXT",
                f"Text-like file is unexpectedly large: {sample.size_human()}",
                "medium",
            ))

        # Executable that is suspiciously tiny
        if ext in {".exe", ".dll", ".sys"} and size < 1024:
            flags.append(SuspicionFlag(
                "TINY_EXECUTABLE",
                f"Executable is suspiciously small: {sample.size_human()} "
                "(may be a dropper stub).",
                "high",
            ))

        # Extremely large file
        if size > 500 * 1024 * 1024:
            flags.append(SuspicionFlag(
                "VERY_LARGE_FILE",
                f"File is very large: {sample.size_human()} — unusual for most file types.",
                "info",
            ))

        return flags

    def _check_byte_patterns(self, sample: FileSample, raw: bytes) -> list[SuspicionFlag]:
        flags: list[SuspicionFlag] = []
        raw_lower = raw[:65536].lower()

        for pattern, description, severity in SUSPICIOUS_BYTE_PATTERNS:
            if pattern.lower() in raw_lower:
                flags.append(SuspicionFlag(
                    f"BYTE_PATTERN_{pattern.decode(errors='replace').upper()[:20]}",
                    f"Suspicious string found in file content: '{description}'",
                    severity,
                ))

        return flags

    def _check_permissions(self, sample: FileSample) -> list[SuspicionFlag]:
        flags: list[SuspicionFlag] = []

        if sample.is_hidden:
            flags.append(SuspicionFlag(
                "HIDDEN_FILE",
                f"File is hidden (name starts with '.'): '{sample.file_name}'",
                "low",
            ))

        if sample.is_executable and sample.extension not in DANGEROUS_EXTENSIONS:
            flags.append(SuspicionFlag(
                "UNEXPECTED_EXEC_BIT",
                f"Non-executable extension '{sample.extension}' has the executable bit set.",
                "medium",
            ))

        return flags

    def _check_embedded_pe(self, sample: FileSample, raw: bytes) -> list[SuspicionFlag]:
        """Detect 'MZ' PE header embedded at a non-zero offset."""
        flags: list[SuspicionFlag] = []
        # Skip if the file IS already an executable
        if sample.extension in {".exe", ".dll", ".sys", ".scr", ".com"}:
            return flags
        # Search for MZ after byte 0
        idx = raw.find(b"\x4d\x5a", 2)  # 'MZ' after header
        if idx != -1:
            flags.append(SuspicionFlag(
                "EMBEDDED_PE_HEADER",
                f"Embedded Windows PE header found at offset {idx} inside non-executable file.",
                "critical",
            ))
        return flags

    def _check_age(self, sample: FileSample) -> list[SuspicionFlag]:
        flags: list[SuspicionFlag] = []
        age_seconds = time.time() - sample.modified_at
        if 0 <= age_seconds < 10:
            flags.append(SuspicionFlag(
                "VERY_RECENT",
                "File was modified less than 10 seconds ago — may be actively written.",
                "info",
            ))
        return flags


# ─────────────────────────────────────────────────────────────────────────────
#  AnalysisManager  – orchestration + history
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisManager:
    """
    Manages the full scan workflow and stores all past results.
    """

    def __init__(self) -> None:
        self._analyzer: FileAnalyzer         = FileAnalyzer()
        self._history:  list[AnalysisResult] = []

    # ── public API ────────────────────────────────────────────────────

    def analyze_file(self, file_path: str | Path) -> AnalysisResult:
        """Create a FileSample, scan it, store and return the result."""
        sample = FileSample(file_path)
        result = self._analyzer.scan(sample)
        self._history.append(result)
        return result

    @property
    def history(self) -> list[AnalysisResult]:
        return list(self._history)

    def stats(self) -> dict[str, int]:
        counts: dict[str, int] = {level.value: 0 for level in ThreatLevel}
        for r in self._history:
            counts[r.threat_level.value] += 1
        counts["TOTAL"] = len(self._history)
        return counts

    def clear_history(self) -> None:
        self._history.clear()

    def find_by_hash(self, sha256: str) -> list[AnalysisResult]:
        """Return all results whose SHA-256 matches the given value."""
        return [r for r in self._history if r.sample.hash_sha256 == sha256.lower()]


# ─────────────────────────────────────────────────────────────────────────────
#  CLI helpers
# ─────────────────────────────────────────────────────────────────────────────

BANNER = r"""
╔══════════════════════════════════════════════════════╗
║       Suspicious File Analyzer  v1.0                 ║
║   Heuristic static analysis for threat detection     ║
╚══════════════════════════════════════════════════════╝
"""

MENU = """
  [1] Analyze a file
  [2] View scan history
  [3] Session statistics
  [4] Lookup file by SHA-256
  [5] Clear history
  [H] Help
  [Q] Quit
"""

HELP_TEXT = """
  ── Checks performed ─────────────────────────────────
  • SHA-256 / SHA-1 / MD5 hash generation
  • Magic-byte identification (30+ file types)
  • Shannon byte-entropy (packing / encryption detection)
  • Dangerous & double-extension detection
  • Extension ↔ magic-byte mismatch
  • 16 suspicious byte-string patterns
  • File size anomalies (tiny executables, huge text files)
  • Executable bit & hidden-file flags
  • Embedded PE (Windows executable) header detection
  • Very-recent modification timestamp

  ── Threat levels ────────────────────────────────────
    CLEAN    (score 0)
    LOW      (score 2–4)
    MEDIUM   (score 5–11)
    HIGH     (score 12–19)
    CRITICAL (score 20+)
  ─────────────────────────────────────────────────────
"""

_COLOURS = {
    ThreatLevel.CLEAN:    "\033[92m",
    ThreatLevel.LOW:      "\033[96m",
    ThreatLevel.MEDIUM:   "\033[93m",
    ThreatLevel.HIGH:     "\033[91m",
    ThreatLevel.CRITICAL: "\033[95m",
}
_RESET = "\033[0m"


def _colour(text: str, level: ThreatLevel) -> str:
    return f"{_COLOURS[level]}{text}{_RESET}"


def _get_input(prompt: str, required: bool = True) -> str:
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("  ⚠  Input cannot be empty.")


def _get_choice(prompt: str, valid: set[str]) -> str:
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid:
            return choice
        print(f"  ⚠  Please choose: {', '.join(sorted(valid))}")


# ── menu actions ──────────────────────────────────────────────────────────────

def action_analyze(manager: AnalysisManager) -> None:
    print("\n── Analyze File ─────────────────────────────────────")
    path_str = _get_input("  File path: ")
    print("  Scanning…")
    try:
        result = manager.analyze_file(path_str)
    except FileNotFoundError as exc:
        print(f"\n  ✗ {exc}\n")
        return
    except ValueError as exc:
        print(f"\n  ✗ {exc}\n")
        return

    label = _colour(f"  ► THREAT LEVEL: {result.threat_level.value}", result.threat_level)
    print(f"\n{'─'*56}")
    print(label)
    for line in result.summary_lines():
        print(line)
    print(f"{'─'*56}\n")


def action_history(manager: AnalysisManager) -> None:
    history = manager.history
    if not history:
        print("\n  No scans recorded yet.\n")
        return
    print(f"\n── Scan History ({len(history)} entries) ─────────────────────────")
    for i, r in enumerate(history, 1):
        ts    = r.analysed_at.strftime("%H:%M:%S")
        label = _colour(r.threat_level.value, r.threat_level)
        name  = r.sample.file_name[:45]
        print(f"  {i:>3}. [{ts}] {label:<22}  {name}  ({r.sample.size_human()})")
    print()


def action_stats(manager: AnalysisManager) -> None:
    stats = manager.stats()
    print("\n── Session Statistics ────────────────────────────────")
    print(f"  Total scanned : {stats['TOTAL']}")
    for level in ThreatLevel:
        count = stats[level.value]
        bar   = "█" * count
        print(f"  {level.value:<10}: {count:>3}  {_colour(bar, level)}")
    print()


def action_lookup(manager: AnalysisManager) -> None:
    sha256 = _get_input("  Enter SHA-256 hash: ").lower()
    results = manager.find_by_hash(sha256)
    if not results:
        print("\n  No matching file found in history.\n")
    else:
        print(f"\n  Found {len(results)} match(es):")
        for r in results:
            print(f"    {r.sample.file_name}  —  {r.threat_level.value}")
        print()


def action_clear(manager: AnalysisManager) -> None:
    confirm = _get_choice("  Clear all history? [y/n]: ", {"y", "n"})
    if confirm == "y":
        manager.clear_history()
        print("  ✓ History cleared.\n")
    else:
        print("  Cancelled.\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print(BANNER)
    manager = AnalysisManager()

    while True:
        print(MENU)
        choice = _get_choice("  Your choice: ", {"1", "2", "3", "4", "5", "h", "q"})

        if choice == "1":
            action_analyze(manager)
        elif choice == "2":
            action_history(manager)
        elif choice == "3":
            action_stats(manager)
        elif choice == "4":
            action_lookup(manager)
        elif choice == "5":
            action_clear(manager)
        elif choice == "h":
            print(HELP_TEXT)
        elif choice == "q":
            print("\n  Stay vigilant!  Goodbye. 👋\n")
            break


if __name__ == "__main__":
    main()