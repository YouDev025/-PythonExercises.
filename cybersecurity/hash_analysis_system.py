"""
Hash Analysis System
====================
A modular OOP-based system for generating, storing, verifying,
and comparing cryptographic hashes of strings and files.
"""

import hashlib
import os
import re
import json
from datetime import datetime
from typing import Optional


# ═══════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════

SUPPORTED_ALGORITHMS = ["MD5", "SHA-1", "SHA-224", "SHA-256", "SHA-384", "SHA-512"]

# Expected hex-digest lengths per algorithm
HASH_LENGTHS: dict[str, int] = {
    "MD5":     32,
    "SHA-1":   40,
    "SHA-224": 56,
    "SHA-256": 64,
    "SHA-384": 96,
    "SHA-512": 128,
}

# hashlib internal names
HASHLIB_NAMES: dict[str, str] = {
    "MD5":     "md5",
    "SHA-1":   "sha1",
    "SHA-224": "sha224",
    "SHA-256": "sha256",
    "SHA-384": "sha384",
    "SHA-512": "sha512",
}

LINE  = "─" * 68
DLINE = "═" * 68

ALG_ICON = {
    "MD5":     "🔵",
    "SHA-1":   "🟡",
    "SHA-224": "🟢",
    "SHA-256": "🔷",
    "SHA-384": "🟣",
    "SHA-512": "💎",
}


# ═══════════════════════════════════════════════════════════
#  HashSample  (result record)
# ═══════════════════════════════════════════════════════════

class HashSample:
    """
    Immutable record capturing one hash operation.
    """

    _id_counter = 0

    def __init__(
        self,
        original_data: str,
        hash_value: str,
        hash_type: str,
        source: str = "text",       # "text" | "file:<path>"
    ):
        HashSample._id_counter += 1
        self._sample_id    = HashSample._id_counter
        self._original_data = original_data
        self._hash_value   = hash_value.lower()
        self._hash_type    = hash_type.upper()
        self._source       = source
        self._timestamp    = datetime.now()

    # ── Properties ────────────────────────────
    @property
    def sample_id(self)     -> int:      return self._sample_id
    @property
    def original_data(self) -> str:      return self._original_data
    @property
    def hash_value(self)    -> str:      return self._hash_value
    @property
    def hash_type(self)     -> str:      return self._hash_type
    @property
    def source(self)        -> str:      return self._source
    @property
    def timestamp(self)     -> datetime: return self._timestamp

    # ── Display ───────────────────────────────
    def display(self, compact: bool = False) -> None:
        icon = ALG_ICON.get(self._hash_type, "🔑")
        ts   = self._timestamp.strftime("%Y-%m-%d %H:%M:%S")

        if compact:
            preview = (self._original_data[:28] + "…") \
                if len(self._original_data) > 30 else self._original_data
            short_hash = self._hash_value[:16] + "…"
            print(
                f"  #{self._sample_id:04d}  {icon} {self._hash_type:<8}  "
                f"{short_hash}  [{preview}]"
            )
            return

        print(DLINE)
        print(f"  Sample ID   : #{self._sample_id:04d}")
        print(f"  Algorithm   : {icon} {self._hash_type}")
        print(f"  Source      : {self._source}")
        print(f"  Timestamp   : {ts}")
        # Show input data (truncate if large)
        data_display = (
            self._original_data[:80] + "…"
            if len(self._original_data) > 80
            else self._original_data
        )
        print(f"  Input data  : {data_display}")
        # Break hash into groups of 8 for readability
        chunks = [self._hash_value[i:i+8] for i in range(0, len(self._hash_value), 8)]
        grouped = " ".join(chunks)
        print(f"  Hash value  : {grouped}")
        print(DLINE)

    def to_dict(self) -> dict:
        return {
            "sample_id":    self._sample_id,
            "hash_type":    self._hash_type,
            "hash_value":   self._hash_value,
            "source":       self._source,
            "original_data": self._original_data,
            "timestamp":    self._timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════
#  HashAnalyzer  (stateless engine)
# ═══════════════════════════════════════════════════════════

class HashAnalyzer:
    """
    Stateless utility class for hash generation, identification,
    comparison, and integrity validation.
    """

    # ── Hash generation ───────────────────────
    @staticmethod
    def hash_text(text: str, algorithm: str) -> str:
        """Return the hex digest of *text* using *algorithm*."""
        alg = algorithm.upper()
        if alg not in SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm '{algorithm}'. "
                f"Choose from: {', '.join(SUPPORTED_ALGORITHMS)}"
            )
        h = hashlib.new(HASHLIB_NAMES[alg])
        h.update(text.encode("utf-8"))
        return h.hexdigest()

    @staticmethod
    def hash_file(filepath: str, algorithm: str, chunk_size: int = 8192) -> str:
        """Stream-hash a file and return its hex digest."""
        alg = algorithm.upper()
        if alg not in SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm '{algorithm}'."
            )
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: '{filepath}'")

        h = hashlib.new(HASHLIB_NAMES[alg])
        with open(filepath, "rb") as fh:
            while chunk := fh.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def hash_all(text: str) -> dict[str, str]:
        """Generate hashes of *text* for every supported algorithm."""
        results: dict[str, str] = {}
        for alg in SUPPORTED_ALGORITHMS:
            results[alg] = HashAnalyzer.hash_text(text, alg)
        return results

    # ── Identification ────────────────────────
    @staticmethod
    def identify(hash_string: str) -> list[str]:
        """
        Return a list of algorithms whose digest length matches
        the given hash string. An empty list means unrecognised.
        """
        h = hash_string.strip().lower()
        if not re.fullmatch(r"[0-9a-f]+", h):
            return []
        length = len(h)
        return [alg for alg, ln in HASH_LENGTHS.items() if ln == length]

    # ── Comparison ────────────────────────────
    @staticmethod
    def compare(hash_a: str, hash_b: str) -> bool:
        """Constant-time comparison of two hex digest strings."""
        return hmac_compare(hash_a.strip().lower(), hash_b.strip().lower())

    # ── Integrity verification ─────────────────
    @staticmethod
    def verify_text(text: str, expected_hash: str, algorithm: str) -> bool:
        """Hash *text* and compare against *expected_hash*."""
        computed = HashAnalyzer.hash_text(text, algorithm)
        return HashAnalyzer.compare(computed, expected_hash)

    @staticmethod
    def verify_file(filepath: str, expected_hash: str, algorithm: str) -> bool:
        """Hash *filepath* and compare against *expected_hash*."""
        computed = HashAnalyzer.hash_file(filepath, algorithm)
        return HashAnalyzer.compare(computed, expected_hash)

    # ── Avalanche effect demo ──────────────────
    @staticmethod
    def avalanche_demo(text: str, algorithm: str) -> dict:
        """
        Show how a 1-character change drastically changes the hash
        (avalanche effect illustration).
        """
        original  = HashAnalyzer.hash_text(text, algorithm)
        modified  = HashAnalyzer.hash_text(text + ".", algorithm)
        # Count differing hex characters
        diff_chars = sum(a != b for a, b in zip(original, modified))
        diff_pct   = diff_chars / len(original) * 100
        return {
            "original_text":  text,
            "modified_text":  text + ".",
            "original_hash":  original,
            "modified_hash":  modified,
            "different_chars": diff_chars,
            "total_chars":    len(original),
            "diff_percent":   round(diff_pct, 1),
        }


# ── Constant-time string compare (no hmac import needed) ──
def hmac_compare(a: str, b: str) -> bool:
    """
    Timing-safe string equality. Equivalent to hmac.compare_digest
    but avoids importing hmac for simplicity in this module.
    """
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a.encode(), b.encode()):
        result |= x ^ y
    return result == 0


# ═══════════════════════════════════════════════════════════
#  HashManager
# ═══════════════════════════════════════════════════════════

class HashManager:
    """
    Manages a collection of HashSamples and coordinates
    analysis operations through HashAnalyzer.
    """

    def __init__(self):
        self._samples: list[HashSample] = []
        self._analyzer = HashAnalyzer()

    # ── Storage ───────────────────────────────
    @property
    def samples(self) -> list[HashSample]:
        return list(self._samples)

    @property
    def count(self) -> int:
        return len(self._samples)

    def get(self, sample_id: int) -> HashSample:
        for s in self._samples:
            if s.sample_id == sample_id:
                return s
        raise KeyError(f"Sample #{sample_id:04d} not found.")

    def clear(self) -> None:
        self._samples.clear()

    # ── Hash operations ───────────────────────
    def hash_text(self, text: str, algorithm: str) -> HashSample:
        value  = self._analyzer.hash_text(text, algorithm)
        sample = HashSample(text, value, algorithm, source="text")
        self._samples.append(sample)
        return sample

    def hash_file(self, filepath: str, algorithm: str) -> HashSample:
        value    = self._analyzer.hash_file(filepath, algorithm)
        filename = os.path.basename(filepath)
        sample   = HashSample(
            f"<file: {filename}>", value, algorithm,
            source=f"file:{filepath}"
        )
        self._samples.append(sample)
        return sample

    def hash_text_all(self, text: str) -> list[HashSample]:
        results = self._analyzer.hash_all(text)
        samples = []
        for alg, value in results.items():
            sample = HashSample(text, value, alg, source="text")
            self._samples.append(sample)
            samples.append(sample)
        return samples

    # ── Comparison / verification ──────────────
    def compare_two(self, id_a: int, id_b: int) -> dict:
        s_a = self.get(id_a)
        s_b = self.get(id_b)
        match = self._analyzer.compare(s_a.hash_value, s_b.hash_value)
        return {
            "sample_a": s_a,
            "sample_b": s_b,
            "match":    match,
        }

    def verify_text_against(self, text: str, expected: str, algorithm: str) -> dict:
        computed = self._analyzer.hash_text(text, algorithm)
        match    = self._analyzer.compare(computed, expected)
        return {
            "algorithm": algorithm,
            "input":     text,
            "expected":  expected,
            "computed":  computed,
            "match":     match,
        }

    def verify_file_against(self, filepath: str, expected: str, algorithm: str) -> dict:
        computed = self._analyzer.hash_file(filepath, algorithm)
        match    = self._analyzer.compare(computed, expected)
        return {
            "algorithm": algorithm,
            "filepath":  filepath,
            "expected":  expected,
            "computed":  computed,
            "match":     match,
        }

    # ── Identification ────────────────────────
    @staticmethod
    def identify_hash(hash_string: str) -> list[str]:
        return HashAnalyzer.identify(hash_string)

    # ── Avalanche ─────────────────────────────
    @staticmethod
    def avalanche_demo(text: str, algorithm: str) -> dict:
        return HashAnalyzer.avalanche_demo(text, algorithm)

    # ── Display helpers ───────────────────────
    def display_all(self, algorithm_filter: Optional[str] = None) -> None:
        samples = self._samples
        if algorithm_filter:
            samples = [s for s in samples if s.hash_type == algorithm_filter.upper()]
        if not samples:
            print("\n  No hash samples stored.\n")
            return
        label = f" [{algorithm_filter}]" if algorithm_filter else ""
        print(f"\n{LINE}")
        print(f"  HASH SAMPLES{label}  ({len(samples)} record(s))")
        print(LINE)
        for s in samples:
            s.display(compact=True)
        print(f"{LINE}\n")

    def display_statistics(self) -> None:
        if not self._samples:
            print("\n  No samples to summarise.\n")
            return
        from collections import Counter
        counts = Counter(s.hash_type for s in self._samples)
        print(f"\n{LINE}")
        print("  HASH SAMPLE STATISTICS")
        print(LINE)
        print(f"  Total samples : {self.count}")
        print("\n  By Algorithm:")
        for alg in SUPPORTED_ALGORITHMS:
            n   = counts.get(alg, 0)
            bar = "█" * n
            icon = ALG_ICON.get(alg, "🔑")
            print(f"    {icon} {alg:<8}  {bar} ({n})")
        print(f"{LINE}\n")

    # ── Export ────────────────────────────────
    def export_json(self, filepath: str) -> None:
        if not self._samples:
            raise ValueError("No samples to export.")
        data = {
            "exported_at": datetime.now().isoformat(),
            "total":       self.count,
            "samples":     [s.to_dict() for s in self._samples],
        }
        with open(filepath, "w") as fh:
            json.dump(data, fh, indent=2)


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════

BANNER = r"""
  ╔═══════════════════════════════════════════════════════╗
  ║          HASH  ANALYSIS  SYSTEM  v1.0                 ║
  ║    Generate · Verify · Compare · Identify             ║
  ╚═══════════════════════════════════════════════════════╝
"""

MENU = """
  ┌────────────────────────────────────────────────────────┐
  │  GENERATE                                              │
  │   1. Hash a text string                                │
  │   2. Hash a text string (all algorithms)               │
  │   3. Hash a file                                       │
  │                                                        │
  │  VERIFY & COMPARE                                      │
  │   4. Verify text against a known hash                  │
  │   5. Verify file against a known hash                  │
  │   6. Compare two stored samples                        │
  │                                                        │
  │  IDENTIFY & ANALYSE                                    │
  │   7. Identify hash type from string                    │
  │   8. Avalanche effect demonstration                    │
  │                                                        │
  │  RECORDS                                               │
  │   9. View all stored samples                           │
  │  10. View sample details                               │
  │  11. Statistics                                        │
  │  12. Export samples to JSON                            │
  │  13. Clear all samples                                 │
  │                                                        │
  │   0. Exit                                              │
  └────────────────────────────────────────────────────────┘
  Choice: """


class CLI:

    def __init__(self):
        self._mgr = HashManager()

    # ── Helpers ───────────────────────────────
    @staticmethod
    def _ask(prompt: str, required: bool = True) -> str:
        while True:
            val = input(f"  {prompt}").strip()
            if val or not required:
                return val
            print("  [!] This field is required.")

    @staticmethod
    def _choose_algorithm(prompt: str = "Algorithm") -> str:
        display = " / ".join(SUPPORTED_ALGORITHMS)
        while True:
            val = input(f"  {prompt} [{display}]: ").strip().upper()
            # Accept shorthand e.g. "256" → SHA-256
            shortcuts = {"256": "SHA-256", "512": "SHA-512",
                         "1": "SHA-1", "224": "SHA-224",
                         "384": "SHA-384", "MD5": "MD5"}
            val = shortcuts.get(val, val)
            if val in SUPPORTED_ALGORITHMS:
                return val
            print(f"  [!] Enter one of: {display}")

    @staticmethod
    def _print_verify_result(match: bool, computed: str, expected: str) -> None:
        if match:
            print(f"\n  ✅  INTEGRITY VERIFIED — hashes match.")
        else:
            print(f"\n  ❌  INTEGRITY FAILURE — hashes do NOT match.")
            print(f"  Expected : {expected}")
            print(f"  Computed : {computed}")
        print()

    # ── Menu actions ──────────────────────────
    def _hash_text(self) -> None:
        text = self._ask("Enter text to hash: ")
        alg  = self._choose_algorithm()
        sample = self._mgr.hash_text(text, alg)
        print(f"\n  ✔  Hash generated and stored as sample #{sample.sample_id:04d}:\n")
        sample.display()

    def _hash_text_all(self) -> None:
        text    = self._ask("Enter text to hash (all algorithms): ")
        samples = self._mgr.hash_text_all(text)
        print(f"\n  ✔  {len(samples)} hashes generated:\n")
        print(f"  Input : {text}\n")
        for s in samples:
            icon   = ALG_ICON.get(s.hash_type, "🔑")
            chunks = [s.hash_value[i:i+8] for i in range(0, len(s.hash_value), 8)]
            print(f"  {icon} {s.hash_type:<8}  {' '.join(chunks)}")
        print()

    def _hash_file(self) -> None:
        filepath = self._ask("File path: ")
        if not os.path.isfile(filepath):
            print(f"\n  [!] File not found: '{filepath}'\n")
            return
        alg = self._choose_algorithm()
        try:
            sample = self._mgr.hash_file(filepath, alg)
            print(f"\n  ✔  File hashed, stored as sample #{sample.sample_id:04d}:\n")
            sample.display()
        except (FileNotFoundError, PermissionError) as exc:
            print(f"\n  [!] {exc}\n")

    def _verify_text(self) -> None:
        text     = self._ask("Text to verify: ")
        expected = self._ask("Expected hash  : ")
        alg      = self._choose_algorithm()
        try:
            result = self._mgr.verify_text_against(text, expected, alg)
            self._print_verify_result(result["match"], result["computed"], result["expected"])
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")

    def _verify_file(self) -> None:
        filepath = self._ask("File path      : ")
        expected = self._ask("Expected hash  : ")
        alg      = self._choose_algorithm()
        try:
            result = self._mgr.verify_file_against(filepath, expected, alg)
            self._print_verify_result(result["match"], result["computed"], result["expected"])
        except (FileNotFoundError, ValueError) as exc:
            print(f"\n  [!] {exc}\n")

    def _compare_two(self) -> None:
        if self._mgr.count < 2:
            print("\n  [!] Need at least 2 stored samples to compare.\n")
            return
        self._mgr.display_all()
        try:
            id_a = int(self._ask("First sample ID  : #"))
            id_b = int(self._ask("Second sample ID : #"))
            result = self._mgr.compare_two(id_a, id_b)
            s_a, s_b = result["sample_a"], result["sample_b"]
            print(f"\n  Sample A  #{s_a.sample_id:04d}  [{s_a.hash_type}]  {s_a.hash_value[:32]}…")
            print(f"  Sample B  #{s_b.sample_id:04d}  [{s_b.hash_type}]  {s_b.hash_value[:32]}…")
            if result["match"]:
                print(f"\n  ✅  MATCH — both samples have identical hash values.\n")
            else:
                print(f"\n  ❌  MISMATCH — hash values differ.\n")
        except (ValueError, KeyError) as exc:
            print(f"\n  [!] {exc}\n")

    def _identify_hash(self) -> None:
        h = self._ask("Enter hash string to identify: ")
        candidates = self._mgr.identify_hash(h)
        print()
        if not candidates:
            print("  [!] Unrecognised hash format (not a valid hex string "
                  "or unknown length).\n")
        else:
            print(f"  Hash length : {len(h)} hex chars")
            print(f"  Possible algorithm(s):")
            for alg in candidates:
                icon = ALG_ICON.get(alg, "🔑")
                print(f"    {icon} {alg}  ({HASH_LENGTHS[alg]} chars)")
            print()

    def _avalanche_demo(self) -> None:
        text = self._ask("Enter base text: ")
        alg  = self._choose_algorithm()
        try:
            r = self._mgr.avalanche_demo(text, alg)
            print(f"\n  {DLINE}")
            print(f"  AVALANCHE EFFECT DEMO  [{alg}]")
            print(f"  {DLINE}")
            print(f"  Original text   : {r['original_text']}")
            print(f"  Modified text   : {r['modified_text']}  (added one '.')")
            # Group for readability
            def grp(h: str) -> str:
                return " ".join(h[i:i+8] for i in range(0, len(h), 8))
            print(f"\n  Original hash   : {grp(r['original_hash'])}")
            print(f"  Modified hash   : {grp(r['modified_hash'])}")
            print(f"\n  Differing chars : {r['different_chars']} / {r['total_chars']}"
                  f"  ({r['diff_percent']}% changed)")
            bar = "█" * int(r['diff_percent'] / 2)
            print(f"  Diff visual     : [{bar:<50}] {r['diff_percent']}%")
            print(f"  {DLINE}\n")
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")

    def _view_detail(self) -> None:
        if not self._mgr.count:
            print("\n  No samples stored.\n")
            return
        self._mgr.display_all()
        try:
            sample_id = int(self._ask("Sample ID to view: #"))
            sample = self._mgr.get(sample_id)
            print()
            sample.display()
        except (ValueError, KeyError) as exc:
            print(f"\n  [!] {exc}\n")

    def _export_json(self) -> None:
        filepath = self._ask("Output file path [hash_records.json]: ")
        if not filepath:
            filepath = "hash_records.json"
        try:
            self._mgr.export_json(filepath)
            print(f"\n  ✔  {self._mgr.count} sample(s) exported to '{filepath}'.\n")
        except (ValueError, OSError) as exc:
            print(f"\n  [!] {exc}\n")

    def _clear_samples(self) -> None:
        if not self._mgr.count:
            print("\n  Nothing to clear.\n")
            return
        confirm = self._ask(
            f"Clear all {self._mgr.count} sample(s)? (yes/no): "
        ).lower()
        if confirm in ("yes", "y"):
            self._mgr.clear()
            print("  ✔  All samples cleared.\n")
        else:
            print("  Cancelled.\n")

    # ── Main loop ─────────────────────────────
    def run(self) -> None:
        print(BANNER)

        dispatch = {
            "1":  self._hash_text,
            "2":  self._hash_text_all,
            "3":  self._hash_file,
            "4":  self._verify_text,
            "5":  self._verify_file,
            "6":  self._compare_two,
            "7":  self._identify_hash,
            "8":  self._avalanche_demo,
            "9":  self._mgr.display_all,
            "10": self._view_detail,
            "11": self._mgr.display_statistics,
            "12": self._export_json,
            "13": self._clear_samples,
        }

        while True:
            try:
                choice = input(MENU).strip()
                if choice == "0":
                    print("\n  Hash Analysis System shutdown. Goodbye!\n")
                    break
                action = dispatch.get(choice)
                if action is None:
                    print("  [!] Invalid choice. Enter 0–13.")
                else:
                    action()
            except KeyboardInterrupt:
                print("\n\n  Interrupted. Goodbye!\n")
                break
            except Exception as exc:
                print(f"\n  [!] Unexpected error: {exc}\n")


# ═══════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    CLI().run()