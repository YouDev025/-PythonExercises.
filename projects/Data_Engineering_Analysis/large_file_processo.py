"""
large_file_processor.py
=======================
A memory-efficient CLI tool for processing large CSV and JSON files.
Supports streaming/chunked reads, filtering, field extraction, progress
reporting, gzip decompression, and structured logging — using only the
Python standard library.

Run:
    python large_file_processor.py
"""

import csv
import json
import os
import sys
import gzip
import logging
import time
import io
from typing import Generator, Dict, Any, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHUNK_SIZE = 1_000          # Records between progress updates
FILTER_FIELD  = "status"    # Field name used for filtering
FILTER_VALUE  = "error"     # Value that triggers inclusion in output
EXTRACT_FIELDS: List[str] = ["timestamp", "ip", "event_type", "status"]

OUTPUT_CSV  = "filtered_output.csv"
OUTPUT_JSON = "filtered_output.json"


# ===========================================================================
# Utility helpers
# ===========================================================================

def open_file(path: str):
    """
    Open a regular or gzip-compressed file transparently.
    Returns a text-mode file object.
    """
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def file_size_mb(path: str) -> float:
    """Return file size in MB (works for .gz too — reports compressed size)."""
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except OSError:
        return 0.0


def detect_file_type(path: str) -> Optional[str]:
    """
    Detect file type from extension.
    Strips a trailing .gz before checking so 'data.csv.gz' → 'csv'.
    Returns 'csv', 'json', or None.
    """
    base = path.lower()
    if base.endswith(".gz"):
        base = base[:-3]
    if base.endswith(".csv"):
        return "csv"
    if base.endswith(".json"):
        return "json"
    return None


def print_separator(char: str = "─", width: int = 60) -> None:
    print(char * width)


def format_duration(seconds: float) -> str:
    """Human-readable duration string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


# ===========================================================================
# Progress tracker
# ===========================================================================

class ProgressTracker:
    """
    Lightweight progress reporter.
    Prints a running counter / percentage to stdout without flooding logs.
    """

    def __init__(self, total_bytes: int = 0, label: str = "Processing"):
        self.count        = 0
        self.filtered     = 0
        self.total_bytes  = total_bytes
        self.label        = label
        self._start       = time.time()
        self._last_print  = -1

    def update(self, matched: bool = False, bytes_read: int = 0) -> None:
        self.count += 1
        if matched:
            self.filtered += 1

        # Print every CHUNK_SIZE records
        chunk_index = self.count // CHUNK_SIZE
        if chunk_index != self._last_print:
            self._last_print = chunk_index
            self._print_progress(bytes_read)

    def _print_progress(self, bytes_read: int) -> None:
        elapsed = time.time() - self._start
        rate    = self.count / elapsed if elapsed > 0 else 0

        if self.total_bytes and bytes_read:
            pct = min(bytes_read / self.total_bytes * 100, 100)
            print(
                f"\r  {self.label}: {self.count:,} records "
                f"| {pct:.1f}% of file "
                f"| {rate:,.0f} rec/s",
                end="",
                flush=True,
            )
        else:
            print(
                f"\r  {self.label}: {self.count:,} records "
                f"| {rate:,.0f} rec/s",
                end="",
                flush=True,
            )

    def finish(self) -> None:
        """Print a final newline and summary."""
        elapsed = time.time() - self._start
        print()   # end the \r line
        logger.info(
            "Done — %s records read, %s matched filter '%s=%s' in %s.",
            f"{self.count:,}",
            f"{self.filtered:,}",
            FILTER_FIELD,
            FILTER_VALUE,
            format_duration(elapsed),
        )


# ===========================================================================
# Record helpers
# ===========================================================================

def extract_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return only the fields listed in EXTRACT_FIELDS.
    Missing fields are stored as empty string so the schema stays consistent.
    """
    return {field: record.get(field, "") for field in EXTRACT_FIELDS}


def passes_filter(record: Dict[str, Any]) -> bool:
    """Return True when the record's FILTER_FIELD equals FILTER_VALUE."""
    return str(record.get(FILTER_FIELD, "")).strip().lower() == FILTER_VALUE.lower()


# ===========================================================================
# CSV processing
# ===========================================================================

def stream_csv(path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields one dict per CSV row.
    Uses csv.DictReader for automatic header mapping.
    Skips blank lines; logs malformed rows without aborting.
    """
    with open_file(path) as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("CSV file appears to be empty or has no header row.")
        logger.info("CSV columns detected: %s", list(reader.fieldnames))
        for line_no, row in enumerate(reader, start=2):   # row 1 = header
            try:
                # DictReader can produce None keys for short rows; clean them.
                clean = {k: v for k, v in row.items() if k is not None}
                yield clean
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping malformed row %d: %s", line_no, exc)


def process_csv(path: str) -> Tuple[int, int]:
    """
    Stream-process a CSV file, write matching records to OUTPUT_CSV.
    Returns (total_records, filtered_records).
    """
    total_bytes = os.path.getsize(path)
    tracker     = ProgressTracker(total_bytes=total_bytes, label="CSV")
    bytes_read  = 0

    output_path = OUTPUT_CSV
    first_write = True

    with open(output_path, "w", newline="", encoding="utf-8") as out_fh:
        writer: Optional[csv.DictWriter] = None

        for record in stream_csv(path):
            matched = passes_filter(record)
            # Approximate bytes consumed (re-encode extracted slice)
            bytes_read += sum(len(str(v)) for v in record.values()) + len(record)
            tracker.update(matched=matched, bytes_read=bytes_read)

            if matched:
                extracted = extract_fields(record)
                if first_write:
                    writer = csv.DictWriter(
                        out_fh,
                        fieldnames=list(extracted.keys()),
                        lineterminator="\n",
                    )
                    writer.writeheader()
                    first_write = False
                writer.writerow(extracted)  # type: ignore[union-attr]

    tracker.finish()
    return tracker.count, tracker.filtered


# ===========================================================================
# JSON processing
# ===========================================================================

def stream_json_array(path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Memory-efficient streaming parser for a top-level JSON array.

    Strategy
    --------
    Read the file character by character, accumulating a buffer.  When the
    bracket depth returns to 1 (i.e. we are directly inside the top-level
    array) and we encounter a comma or the closing ']', we attempt to parse
    the accumulated buffer as a JSON object.  This avoids loading the whole
    array into memory.

    Handles:
    * Nested objects / arrays inside each element
    * String literals containing '{', '}', '[', ']', or escaped quotes
    * Whitespace / pretty-printed files
    """
    BUFSIZE = 65_536   # read from disk in 64 KB chunks for I/O efficiency

    with open_file(path) as fh:
        # --- locate the opening '[' of the top-level array -----------------
        found_array_start = False
        preamble_buf      = ""
        while not found_array_start:
            chunk = fh.read(BUFSIZE)
            if not chunk:
                raise ValueError("No top-level JSON array '[' found in file.")
            preamble_buf += chunk
            idx = preamble_buf.find("[")
            if idx != -1:
                # Push back everything after '[' into a "remainder" string
                remainder = preamble_buf[idx + 1:]
                found_array_start = True

        # --- streaming parse ------------------------------------------------
        depth        = 1        # we are inside the top-level '['
        obj_buf      = []       # character accumulator for current element
        in_string    = False
        escape_next  = False

        def iter_chars():
            """Yield characters from remainder, then the rest of the file."""
            yield from remainder
            while True:
                chunk = fh.read(BUFSIZE)
                if not chunk:
                    return
                yield from chunk

        for ch in iter_chars():
            # --- string literal tracking ------------------------------------
            if escape_next:
                obj_buf.append(ch)
                escape_next = False
                continue

            if ch == "\\" and in_string:
                obj_buf.append(ch)
                escape_next = True
                continue

            if ch == '"':
                in_string = not in_string
                obj_buf.append(ch)
                continue

            if in_string:
                obj_buf.append(ch)
                continue

            # --- structural characters --------------------------------------
            if ch in ("{", "["):
                depth += 1
                obj_buf.append(ch)
                continue

            if ch in ("}", "]"):
                depth -= 1
                if depth == 0:
                    # Closing ']' of the top-level array — we are done.
                    break
                obj_buf.append(ch)
                if depth == 1:
                    # Closed an element at depth 1 → parse it
                    raw = "".join(obj_buf).strip()
                    obj_buf.clear()
                    if raw:
                        try:
                            yield json.loads(raw)
                        except json.JSONDecodeError as exc:
                            logger.warning("Skipping malformed JSON element: %s", exc)
                continue

            if ch == "," and depth == 1:
                # Separator between elements at the top level — try to parse
                # whatever we have buffered (handles both object and primitive
                # elements, though we only care about dicts).
                raw = "".join(obj_buf).strip()
                obj_buf.clear()
                if raw:
                    try:
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict):
                            yield parsed
                    except json.JSONDecodeError as exc:
                        logger.warning("Skipping malformed JSON element: %s", exc)
                continue

            obj_buf.append(ch)

        # Flush any remaining buffer (last element before ']')
        raw = "".join(obj_buf).strip().rstrip(",")
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    yield parsed
            except json.JSONDecodeError:
                pass   # already warned above


def process_json(path: str) -> Tuple[int, int]:
    """
    Stream-process a JSON file, write matching records to OUTPUT_JSON.
    Returns (total_records, filtered_records).
    """
    total_bytes = os.path.getsize(path)
    tracker     = ProgressTracker(total_bytes=total_bytes, label="JSON")
    bytes_read  = 0

    output_path  = OUTPUT_JSON
    filtered_out: List[Dict[str, Any]] = []   # batch before writing
    WRITE_BATCH  = 500                         # flush to disk every N records

    # Start the output file with '['
    with open(output_path, "w", encoding="utf-8") as out_fh:
        out_fh.write("[\n")
        first_record = True

        def flush_batch(batch: List[Dict[str, Any]]) -> None:
            nonlocal first_record
            for item in batch:
                if not first_record:
                    out_fh.write(",\n")
                out_fh.write("  " + json.dumps(item, ensure_ascii=False))
                first_record = False

        for record in stream_json_array(path):
            matched = passes_filter(record)
            bytes_read += len(json.dumps(record))   # approximate
            tracker.update(matched=matched, bytes_read=bytes_read)

            if matched:
                filtered_out.append(extract_fields(record))
                if len(filtered_out) >= WRITE_BATCH:
                    flush_batch(filtered_out)
                    filtered_out.clear()

        # Flush any remaining records
        if filtered_out:
            flush_batch(filtered_out)

        out_fh.write("\n]\n")

    tracker.finish()
    return tracker.count, tracker.filtered


# ===========================================================================
# Sample file generator  (for demo / testing)
# ===========================================================================

def generate_sample_csv(path: str = "sample_data.csv", rows: int = 50_000) -> None:
    """Generate a sample CSV with mixed statuses for testing."""
    import random
    statuses   = ["ok", "error", "warning", "ok", "ok"]   # ~20 % errors
    event_types = ["login", "logout", "purchase", "view", "error_event"]
    ips         = [f"192.168.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(20)]

    logger.info("Generating sample CSV → %s (%d rows) …", path, rows)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["timestamp", "ip", "event_type", "status", "extra"],
            lineterminator="\n",
        )
        writer.writeheader()
        for i in range(rows):
            writer.writerow({
                "timestamp":  f"2024-01-01T{(i // 3600) % 24:02d}:{(i // 60) % 60:02d}:{i % 60:02d}Z",
                "ip":         random.choice(ips),
                "event_type": random.choice(event_types),
                "status":     random.choice(statuses),
                "extra":      f"payload_{i}",
            })
    logger.info("Sample CSV ready: %s (%.2f MB)", path, file_size_mb(path))


def generate_sample_json(path: str = "sample_data.json", records: int = 50_000) -> None:
    """Generate a sample JSON array with mixed statuses for testing."""
    import random
    statuses    = ["ok", "error", "warning", "ok", "ok"]
    event_types = ["login", "logout", "purchase", "view", "error_event"]
    ips         = [f"10.0.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(20)]

    logger.info("Generating sample JSON → %s (%d records) …", path, records)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("[\n")
        for i in range(records):
            record = {
                "timestamp":  f"2024-01-01T{(i // 3600) % 24:02d}:{(i // 60) % 60:02d}:{i % 60:02d}Z",
                "ip":         random.choice(ips),
                "event_type": random.choice(event_types),
                "status":     random.choice(statuses),
                "extra":      f"payload_{i}",
            }
            suffix = ",\n" if i < records - 1 else "\n"
            fh.write("  " + json.dumps(record) + suffix)
        fh.write("]\n")
    logger.info("Sample JSON ready: %s (%.2f MB)", path, file_size_mb(path))


# ===========================================================================
# Results display
# ===========================================================================

def display_summary(
    file_path:  str,
    file_type:  str,
    total:      int,
    filtered:   int,
    output_path: str,
    elapsed:    float,
) -> None:
    print()
    print_separator("═")
    print("  PROCESSING SUMMARY")
    print_separator("═")
    print(f"  Input file    : {file_path}")
    print(f"  File type     : {file_type.upper()}")
    print(f"  File size     : {file_size_mb(file_path):.2f} MB")
    print_separator()
    print(f"  Total records : {total:,}")
    print(f"  Filtered      : {filtered:,}  "
          f"({filtered / total * 100:.1f}% match '{FILTER_FIELD}={FILTER_VALUE}')"
          if total else f"  Filtered      : {filtered:,}")
    print(f"  Output file   : {output_path}")
    print(f"  Output size   : {file_size_mb(output_path):.2f} MB")
    print(f"  Elapsed time  : {format_duration(elapsed)}")
    print_separator("═")
    print()


# ===========================================================================
# CLI menu
# ===========================================================================

def prompt_file_path(file_type: str) -> str:
    """
    Ask the user for a file path.
    Offers to generate a sample file if the provided path does not exist.
    """
    while True:
        path = input(f"\n  Enter path to {file_type.upper()} file: ").strip()
        if not path:
            print("  [!] Path cannot be empty.")
            continue

        if os.path.isfile(path):
            return path

        print(f"  [!] File not found: {path}")
        gen = input("  Generate a sample file for testing? [y/N]: ").strip().lower()
        if gen == "y":
            sample_path = f"sample_data.{file_type}"
            if file_type == "csv":
                generate_sample_csv(sample_path)
            else:
                generate_sample_json(sample_path)
            return sample_path


def run_csv_workflow() -> None:
    """Full CSV processing workflow."""
    path = prompt_file_path("csv")
    print()
    logger.info("Starting CSV processing: %s (%.2f MB)", path, file_size_mb(path))
    start = time.time()
    try:
        total, filtered = process_csv(path)
    except Exception as exc:
        logger.error("CSV processing failed: %s", exc)
        return
    elapsed = time.time() - start
    display_summary(path, "csv", total, filtered, OUTPUT_CSV, elapsed)


def run_json_workflow() -> None:
    """Full JSON processing workflow."""
    path = prompt_file_path("json")
    print()
    logger.info("Starting JSON processing: %s (%.2f MB)", path, file_size_mb(path))
    start = time.time()
    try:
        total, filtered = process_json(path)
    except Exception as exc:
        logger.error("JSON processing failed: %s", exc)
        return
    elapsed = time.time() - start
    display_summary(path, "json", total, filtered, OUTPUT_JSON, elapsed)


def main_menu() -> None:
    """Interactive CLI main menu."""
    print_separator("═")
    print("  LARGE FILE PROCESSOR  (memory-efficient | pure Python)")
    print_separator("═")
    print(f"  Filter    : records where  {FILTER_FIELD} == '{FILTER_VALUE}'")
    print(f"  Extracts  : {EXTRACT_FIELDS}")
    print_separator()
    print("  [1]  Process a CSV  file")
    print("  [2]  Process a JSON file")
    print("  [3]  Exit")
    print_separator("═")

    while True:
        choice = input("  Select option [1/2/3]: ").strip()
        if choice == "1":
            run_csv_workflow()
        elif choice == "2":
            run_json_workflow()
        elif choice == "3":
            print("\n  Goodbye!\n")
            sys.exit(0)
        else:
            print("  [!] Invalid option. Please enter 1, 2, or 3.")

        # After processing, show menu again
        print_separator("═")
        print("  [1]  Process another CSV")
        print("  [2]  Process another JSON")
        print("  [3]  Exit")
        print_separator("═")


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    # Optional: accept file path as a CLI argument for non-interactive use.
    # Usage:  python large_file_processor.py mydata.csv
    #         python large_file_processor.py mydata.json
    if len(sys.argv) == 2:
        arg_path = sys.argv[1]
        arg_type = detect_file_type(arg_path)
        if arg_type is None:
            print(f"[ERROR] Cannot determine file type for: {arg_path}")
            print("        Expected a .csv, .json, .csv.gz, or .json.gz file.")
            sys.exit(1)
        if not os.path.isfile(arg_path):
            print(f"[ERROR] File not found: {arg_path}")
            sys.exit(1)
        start = time.time()
        if arg_type == "csv":
            total, filtered = process_csv(arg_path)
            output = OUTPUT_CSV
        else:
            total, filtered = process_json(arg_path)
            output = OUTPUT_JSON
        display_summary(arg_path, arg_type, total, filtered, output, time.time() - start)
    else:
        main_menu()