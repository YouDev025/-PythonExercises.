#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         Data Cleaning Automation Tool                            ║
║         Pure Python · No External Dependencies                   ║
╚══════════════════════════════════════════════════════════════════╝

Run with:  python data_cleaning_automation_tool.py
"""

import re
import json
import copy
import hashlib
import os
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════════════════════
# ANSI COLOUR HELPERS
# ══════════════════════════════════════════════════════════════════════════════

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"

def c(text: str, *codes: str) -> str:
    return "".join(codes) + str(text) + RESET

def hr(char: str = "─", width: int = 70, colour: str = DIM) -> str:
    return c(char * width, colour)

# ══════════════════════════════════════════════════════════════════════════════
# SAMPLE DIRTY DATA GENERATION
# ══════════════════════════════════════════════════════════════════════════════

# A deliberately messy dataset that exercises every cleaning rule.
RAW_RECORDS: List[Dict] = [
    # ── clean-ish baseline ────────────────────────────────────────────────────
    {"timestamp": "2024-03-15 08:22:11", "source": "auth-service",
     "event_type": "LOGIN_SUCCESS", "user_ip": "192.168.1.10",
     "status": "success", "message": "User authenticated."},

    # ── extra whitespace in values + inconsistent field name (ip vs user_ip) ──
    {"timestamp": "  2024-03-15 09:05:33  ", "source": "  web-app  ",
     "event_type": "  login_failure  ", "ip": "10.0.0.5",
     "status": "  FAILURE  ", "message": "  Bad credentials.  "},

    # ── completely missing required fields ────────────────────────────────────
    {"timestamp": "", "source": "firewall",
     "event_type": "PORT_SCAN", "user_ip": "203.0.113.7",
     "status": "blocked", "message": ""},

    # ── duplicate of record 0 ─────────────────────────────────────────────────
    {"timestamp": "2024-03-15 08:22:11", "source": "auth-service",
     "event_type": "LOGIN_SUCCESS", "user_ip": "192.168.1.10",
     "status": "success", "message": "User authenticated."},

    # ── malformed timestamp ───────────────────────────────────────────────────
    {"timestamp": "15/03/2024 10:30", "source": "ids",
     "event_type": "BRUTE_FORCE", "user_ip": "10.0.0.9",
     "status": "warning", "message": "Multiple failures."},

    # ── invalid IP address ────────────────────────────────────────────────────
    {"timestamp": "2024-03-15 11:00:00", "source": "vpn-gateway",
     "event_type": "LOGOUT", "user_ip": "999.999.999.999",
     "status": "success", "message": "Session ended."},

    # ── None values for several fields ───────────────────────────────────────
    {"timestamp": None, "source": None,
     "event_type": "FILE_ACCESS", "user_ip": "192.168.1.15",
     "status": None, "message": None},

    # ── alternative field aliases ─────────────────────────────────────────────
    {"ts": "2024-03-15 12:45:00", "src": "db-server",
     "type": "SQL_INJECTION", "addr": "203.0.113.3",
     "state": "blocked", "msg": "SQLi payload detected."},

    # ── status uses numeric code instead of string ────────────────────────────
    {"timestamp": "2024-03-15 13:10:05", "source": "web-app",
     "event_type": "XSS_ATTEMPT", "user_ip": "192.168.1.20",
     "status": "200", "message": "XSS filtered."},

    # ── excessive noise / non-printable chars in message ─────────────────────
    {"timestamp": "2024-03-15 14:00:00", "source": "mail-server",
     "event_type": "SPAM_DETECTED", "user_ip": "10.0.0.3",
     "status": "blocked", "message": "\t\n Spam\x00 detected\x01.\n\t"},

    # ── missing source + event_type ───────────────────────────────────────────
    {"timestamp": "2024-03-15 14:30:00", "source": "",
     "event_type": "", "user_ip": "192.168.1.5",
     "status": "pending", "message": "Unclassified event."},

    # ── duplicate of record 4 (after field normalisation it will match) ───────
    {"timestamp": "15/03/2024 10:30", "source": "ids",
     "event_type": "brute_force", "user_ip": "10.0.0.9",
     "status": "WARNING", "message": "Multiple failures."},

    # ── extra unknown fields that should be stripped ──────────────────────────
    {"timestamp": "2024-03-15 15:00:00", "source": "file-server",
     "event_type": "FILE_DELETE", "user_ip": "192.168.1.8",
     "status": "success", "message": "File removed.",
     "DEBUG_raw": "kernel panic", "internal_ref": "TKT-4821"},

    # ── entirely empty record ─────────────────────────────────────────────────
    {},

    # ── event_type mixed-case noise ───────────────────────────────────────────
    {"timestamp": "2024-03-16 07:00:00", "source": "auth-service",
     "event_type": "  Login_Success ", "user_ip": "192.168.1.1",
     "status": "success", "message": "Admin login."},
]

# ══════════════════════════════════════════════════════════════════════════════
# CANONICAL SCHEMA
# ══════════════════════════════════════════════════════════════════════════════

# Defines the target field names and which "dirty" aliases map to each one.
FIELD_ALIASES: Dict[str, List[str]] = {
    "timestamp":  ["ts", "time", "datetime", "date_time", "log_time"],
    "source":     ["src", "host", "hostname", "origin", "service"],
    "event_type": ["type", "event", "log_type", "category"],
    "user_ip":    ["ip", "addr", "address", "client_ip", "remote_ip", "src_ip"],
    "status":     ["state", "result", "outcome", "http_status"],
    "message":    ["msg", "description", "detail", "details", "info"],
}

REQUIRED_FIELDS = {"timestamp", "source", "event_type", "user_ip", "status"}

# Valid canonical status values
STATUS_MAP: Dict[str, str] = {
    # string variants
    "success":  "SUCCESS", "ok":       "SUCCESS", "pass":    "SUCCESS",
    "failure":  "FAILURE", "fail":     "FAILURE", "error":   "FAILURE",
    "warning":  "WARNING", "warn":     "WARNING",
    "blocked":  "BLOCKED", "block":    "BLOCKED", "deny":    "BLOCKED",
    "pending":  "PENDING", "unknown":  "PENDING",
    # common HTTP status codes that appear in logs
    "200": "SUCCESS", "201": "SUCCESS", "204": "SUCCESS",
    "400": "FAILURE", "401": "FAILURE", "403": "BLOCKED",
    "404": "FAILURE", "500": "FAILURE", "503": "FAILURE",
}

# Timestamp formats to try when parsing a raw timestamp string
TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%d-%m-%Y %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
]

CANONICAL_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# ══════════════════════════════════════════════════════════════════════════════
# METRICS TRACKER
# ══════════════════════════════════════════════════════════════════════════════

class Metrics:
    """Accumulates counts of every fix applied during cleaning."""

    def __init__(self):
        self._counts: Dict[str, int] = {}
        self._examples: Dict[str, List[str]] = {}

    def record(self, key: str, example: str = "") -> None:
        self._counts[key] = self._counts.get(key, 0) + 1
        if example:
            bucket = self._examples.setdefault(key, [])
            if len(bucket) < 3:          # keep at most 3 examples per rule
                bucket.append(example)

    def total(self) -> int:
        return sum(self._counts.values())

    def items(self) -> List[Tuple[str, int, List[str]]]:
        return [
            (k, v, self._examples.get(k, []))
            for k, v in sorted(self._counts.items(), key=lambda x: -x[1])
        ]

    def __repr__(self) -> str:
        return f"Metrics(total={self.total()}, rules={len(self._counts)})"

# ══════════════════════════════════════════════════════════════════════════════
# INDIVIDUAL CLEANING RULES
# ══════════════════════════════════════════════════════════════════════════════
# Each rule is a function: (record, metrics) -> record | None
# Returning None signals that the record should be dropped entirely.
# ──────────────────────────────────────────────────────────────────────────────

def rule_drop_empty(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """Drop records that are completely empty or contain only None/blank values."""
    meaningful = {
        k: v for k, v in record.items()
        if v is not None and str(v).strip() != ""
    }
    if not meaningful:
        metrics.record("drop_empty_record", "record had no meaningful fields")
        return None
    return record


def rule_normalize_field_names(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """
    Rename aliased field names to their canonical equivalents.
    Unknown extra fields (e.g. DEBUG_raw) are removed.
    """
    canonical: Dict[str, Any] = {}

    # Build a reverse lookup: alias -> canonical name
    alias_to_canonical: Dict[str, str] = {}
    for canon, aliases in FIELD_ALIASES.items():
        alias_to_canonical[canon] = canon          # identity mapping
        for alias in aliases:
            alias_to_canonical[alias.lower()] = canon

    for raw_key, value in record.items():
        mapped = alias_to_canonical.get(raw_key.lower().strip())
        if mapped:
            if mapped in canonical:
                # Prefer the value already stored (earlier / canonical key wins)
                pass
            else:
                canonical[mapped] = value
                if raw_key.lower().strip() != mapped:
                    metrics.record(
                        "field_renamed",
                        f'"{raw_key}" → "{mapped}"',
                    )
        else:
            # Unknown field — drop it
            metrics.record("unknown_field_dropped", f'"{raw_key}"')

    return canonical


def rule_trim_whitespace(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """Strip leading/trailing whitespace and collapse internal runs."""
    cleaned: Dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, str):
            stripped = value.strip()
            # Remove non-printable / control characters (keep newline-like only in message)
            if key != "message":
                stripped = re.sub(r"[\x00-\x1f\x7f]", "", stripped)
            else:
                stripped = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", stripped)
                stripped = stripped.strip()
            if stripped != value:
                metrics.record("whitespace_trimmed", f'{key}: {repr(value)[:40]}')
            cleaned[key] = stripped
        else:
            cleaned[key] = value
    return cleaned


def rule_handle_missing_values(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """
    Replace None / empty string with sensible sentinel values.
    Required fields that cannot be filled will be flagged.
    """
    DEFAULTS = {
        "source":     "UNKNOWN_SOURCE",
        "event_type": "UNKNOWN_EVENT",
        "user_ip":    "0.0.0.0",
        "status":     "PENDING",
        "message":    "(no message)",
        "timestamp":  None,         # handled separately
    }

    out = dict(record)
    for field, default in DEFAULTS.items():
        raw = out.get(field)
        if raw is None or (isinstance(raw, str) and raw.strip() == ""):
            out[field] = default
            metrics.record("missing_value_filled", f'{field} → "{default}"')

    return out


def rule_normalize_timestamp(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """
    Parse any recognisable timestamp string and reformat to
    YYYY-MM-DD HH:MM:SS.  Malformed timestamps are replaced with a
    sentinel rather than dropped so the record is not lost.
    """
    raw = record.get("timestamp")
    if not raw or (isinstance(raw, str) and raw.strip() == ""):
        record["timestamp"] = "1970-01-01 00:00:00"
        metrics.record("timestamp_missing_sentinel", "replaced empty timestamp")
        return record

    ts_str = str(raw).strip()

    # Already in canonical format?
    try:
        dt = datetime.strptime(ts_str, CANONICAL_TIMESTAMP_FORMAT)
        return record          # nothing to do
    except ValueError:
        pass

    # Try other known formats
    for fmt in TIMESTAMP_FORMATS:
        try:
            dt = datetime.strptime(ts_str, fmt)
            new_ts = dt.strftime(CANONICAL_TIMESTAMP_FORMAT)
            metrics.record("timestamp_reformatted", f'"{ts_str}" → "{new_ts}"')
            record["timestamp"] = new_ts
            return record
        except ValueError:
            continue

    # Nothing matched
    metrics.record("timestamp_malformed_sentinel",
                   f'"{ts_str}" could not be parsed')
    record["timestamp"] = "1970-01-01 00:00:00"
    return record


def rule_normalize_status(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """Map raw status values to one of SUCCESS / FAILURE / WARNING / BLOCKED / PENDING."""
    raw = str(record.get("status", "")).strip().lower()
    mapped = STATUS_MAP.get(raw)
    if mapped and mapped != record.get("status"):
        metrics.record("status_normalized", f'"{record["status"]}" → "{mapped}"')
        record["status"] = mapped
    elif not mapped:
        metrics.record("status_unknown_pending", f'"{record.get("status")}" → "PENDING"')
        record["status"] = "PENDING"
    return record


def rule_normalize_event_type(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """Upper-case and strip the event_type field."""
    raw = str(record.get("event_type", "")).strip()
    normalised = raw.upper().replace(" ", "_")
    if normalised != raw:
        metrics.record("event_type_normalised", f'"{raw}" → "{normalised}"')
    record["event_type"] = normalised
    return record


def rule_validate_ip(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """
    Check user_ip is a valid IPv4 address.
    Invalid IPs are replaced with 0.0.0.0 rather than dropping the record.
    """
    ip = str(record.get("user_ip", "")).strip()
    parts = ip.split(".")
    valid = (
        len(parts) == 4
        and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
    )
    if not valid:
        metrics.record("invalid_ip_replaced", f'"{ip}" → "0.0.0.0"')
        record["user_ip"] = "0.0.0.0"
    return record


def rule_ensure_required_fields(record: Dict, metrics: Metrics) -> Optional[Dict]:
    """
    Final gate: if any required field is still missing or blank after all
    other rules, mark the record as malformed but keep it for review.
    """
    missing = [
        f for f in REQUIRED_FIELDS
        if not record.get(f) or str(record[f]).strip() in ("", "None")
    ]
    if missing:
        metrics.record(
            "record_flagged_incomplete",
            f'missing: {missing}',
        )
        record["_flags"] = record.get("_flags", []) + [f"missing:{','.join(missing)}"]
    return record


# ══════════════════════════════════════════════════════════════════════════════
# DUPLICATE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def _record_fingerprint(record: Dict) -> str:
    """
    Produce a stable hash of the canonical fields, ignoring internal _flags.
    Used to identify duplicates after normalisation.
    """
    key_fields = {
        k: record.get(k, "")
        for k in ("timestamp", "source", "event_type", "user_ip", "status")
    }
    serialised = json.dumps(key_fields, sort_keys=True, default=str)
    return hashlib.md5(serialised.encode()).hexdigest()


def remove_duplicates(
    records: List[Dict],
    metrics: Metrics,
) -> List[Dict]:
    """Deduplicate by fingerprint, keeping the first occurrence."""
    seen: set = set()
    out: List[Dict] = []
    for rec in records:
        fp = _record_fingerprint(rec)
        if fp in seen:
            metrics.record("duplicate_removed",
                           f'ts={rec.get("timestamp")} src={rec.get("source")}')
        else:
            seen.add(fp)
            out.append(rec)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# CLEANING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

# Ordered list of per-record cleaning rules.
CLEANING_RULES: List[Callable[[Dict, Metrics], Optional[Dict]]] = [
    rule_drop_empty,
    rule_normalize_field_names,
    rule_trim_whitespace,
    rule_handle_missing_values,
    rule_normalize_timestamp,
    rule_normalize_status,
    rule_normalize_event_type,
    rule_validate_ip,
    rule_ensure_required_fields,
]


def run_pipeline(
    raw: List[Dict],
    custom_rules: Optional[List[Callable]] = None,
) -> Tuple[List[Dict], Metrics]:
    """
    Run the full cleaning pipeline over *raw* records.

    Returns:
        (cleaned_records, metrics)
    """
    metrics = Metrics()
    rules = CLEANING_RULES + (custom_rules or [])
    intermediate: List[Dict] = []

    for i, raw_rec in enumerate(raw):
        rec = copy.deepcopy(raw_rec)      # never mutate the original
        for rule in rules:
            if rec is None:
                break
            rec = rule(rec, metrics)
        if rec is not None:
            intermediate.append(rec)

    # Deduplication is done as a post-pass (requires normalised values)
    cleaned = remove_duplicates(intermediate, metrics)
    return cleaned, metrics


# ══════════════════════════════════════════════════════════════════════════════
# DISPLAY / FORMATTING
# ══════════════════════════════════════════════════════════════════════════════

# Colours for status badges
_STATUS_COLOURS = {
    "SUCCESS": GREEN, "FAILURE": RED, "WARNING": YELLOW,
    "BLOCKED": MAGENTA, "PENDING": DIM,
}

_EVENT_COLOURS = {
    "PORT_SCAN":     RED,   "BRUTE_FORCE":   RED,
    "SQL_INJECTION": RED,   "XSS_ATTEMPT":   RED,
    "PRIVILEGE_ESC": MAGENTA, "LOGIN_FAILURE": YELLOW,
    "CONFIG_CHANGE": YELLOW,  "SPAM_DETECTED": YELLOW,
}


def _badge(text: str, colour_map: Dict) -> str:
    col = colour_map.get(text.upper(), CYAN)
    return c(f" {text} ", col, BOLD)


def _truncate(text: str, width: int = 35) -> str:
    s = str(text) if text is not None else ""
    return s if len(s) <= width else s[: width - 1] + "…"


def print_records(records: List[Dict], title: str, max_rows: int = 30) -> None:
    """Render records as a compact table."""
    print()
    print(c(f"  {'━' * 66}", BOLD + CYAN))
    print(c(f"  {title}", BOLD + CYAN))
    print(c(f"  {'━' * 66}", BOLD + CYAN))

    if not records:
        print(c("  (empty)", DIM))
        return

    # Header
    print(
        c(
            f"  {'#':<4} {'Timestamp':<21} {'Source':<14} {'Event Type':<18} "
            f"{'IP':<17} {'Status':<10}",
            BOLD,
        )
    )
    print(c("  " + "─" * 86, DIM))

    for idx, rec in enumerate(records[:max_rows], 1):
        ts    = _truncate(rec.get("timestamp", ""), 20)
        src   = _truncate(rec.get("source", ""),    13)
        etype = _truncate(rec.get("event_type", ""), 17)
        ip    = _truncate(rec.get("user_ip", ""),   16)
        st    = str(rec.get("status", ""))
        flags = rec.get("_flags", [])

        status_str = c(f"{st:<10}", _STATUS_COLOURS.get(st, RESET))
        event_str  = c(f"{etype:<18}", _EVENT_COLOURS.get(etype.upper(), CYAN))
        flag_str   = c(" ⚑ " + "; ".join(flags), RED) if flags else ""

        print(
            f"  {idx:<4} {ts:<21} {src:<14} {event_str} {ip:<17} {status_str}{flag_str}"
        )

    if len(records) > max_rows:
        print(c(f"  … {len(records) - max_rows} more rows not shown", DIM))

    print(c("  " + "─" * 86, DIM))
    print(c(f"  Rows: {len(records)}", DIM))


def print_raw_dict(records: List[Dict], title: str, max_rows: int = 15) -> None:
    """Dump raw records as compact indented dicts for the 'before' view."""
    print()
    print(c(f"  {'━' * 66}", BOLD + YELLOW))
    print(c(f"  {title}", BOLD + YELLOW))
    print(c(f"  {'━' * 66}", BOLD + YELLOW))

    for idx, rec in enumerate(records[:max_rows], 1):
        print(c(f"\n  [{idx}]", BOLD + YELLOW), end=" ")
        if not rec:
            print(c("{}", RED))
            continue
        parts = []
        for k, v in rec.items():
            key_s = c(k, BLUE)
            val_s = c(repr(_truncate(str(v) if v is not None else "None", 40)), DIM)
            parts.append(f"{key_s}: {val_s}")
        print("{ " + ",  ".join(parts) + " }")

    if len(records) > max_rows:
        print(c(f"\n  … {len(records) - max_rows} more raw records not shown", DIM))

    print()


def print_metrics(metrics: Metrics, raw_count: int, clean_count: int) -> None:
    """Print the cleaning summary report."""
    print()
    print(c("  ╔══════════════════════════════════════════════════════════╗", BOLD + GREEN))
    print(c("  ║              Cleaning Summary Report                     ║", BOLD + GREEN))
    print(c("  ╚══════════════════════════════════════════════════════════╝", BOLD + GREEN))

    print(f"\n  {c('Input records : ', BOLD)}{c(raw_count,   YELLOW)}")
    print(f"  {c('Output records: ', BOLD)}{c(clean_count, GREEN)}")
    dropped = raw_count - clean_count
    print(f"  {c('Dropped       : ', BOLD)}{c(dropped, RED if dropped else DIM)}")
    print(f"  {c('Total fixes   : ', BOLD)}{c(metrics.total(), CYAN, BOLD)}")

    if not metrics.items():
        print(c("\n  (no fixes recorded)", DIM))
        return

    print()
    print(c("  ┌─ Fix Breakdown ───────────────────────────────────────────┐", BOLD))

    # Bar chart scaled to terminal width
    max_count = max(count for _, count, _ in metrics.items())
    bar_width  = 25

    for rule, count, examples in metrics.items():
        frac = count / max_count if max_count else 0
        bar  = "█" * max(1, int(frac * bar_width))
        rule_label = rule.replace("_", " ").title()
        print(
            f"  │  {c(f'{rule_label:<35}', CYAN)}"
            f"  {c(f'{count:>4}', BOLD)}  {c(bar, GREEN)}"
        )
        for ex in examples:
            print(f"  │      {c('↳ ' + ex[:60], DIM)}")

    print(c("  └────────────────────────────────────────────────────────────┘", BOLD))


def print_diff_summary(raw: List[Dict], cleaned: List[Dict]) -> None:
    """
    Side-by-side snapshot: pick a few representative records and show
    what changed.
    """
    print()
    print(c("  ── Before / After Spot-Check ──────────────────────────────────", BOLD + MAGENTA))

    # Match raw → cleaned by original index position (best-effort; dupes shift things)
    snapshot_indices = [1, 4, 7]  # indices into raw that have interesting changes

    for ri in snapshot_indices:
        if ri >= len(raw):
            continue
        r = raw[ri]
        # Find the closest cleaned record that shares the same event_type
        target_et = str(r.get("event_type", r.get("type", ""))).strip().upper()
        match = next(
            (cr for cr in cleaned
             if cr.get("event_type", "").upper() == target_et),
            None,
        )
        print()
        print(c(f"  Record #{ri + 1} (raw):", BOLD + YELLOW))
        for k, v in r.items():
            print(f"    {c(k, BLUE)}: {c(repr(v)[:60], DIM)}")
        if match:
            print(c(f"  → After cleaning:", BOLD + GREEN))
            for k, v in match.items():
                if k.startswith("_"):
                    continue
                print(f"    {c(k, BLUE)}: {c(repr(v)[:60], GREEN)}")
        else:
            print(c("  → (record was dropped)", RED))


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def export_to_json(records: List[Dict], filename: str) -> str:
    path = os.path.abspath(filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, default=str)
    return path


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM RULE BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def make_keyword_filter(
    field: str,
    keywords: List[str],
    replacement: str = "(redacted)",
) -> Callable[[Dict, Metrics], Optional[Dict]]:
    """
    Factory: returns a rule that replaces *keywords* found in *field*
    with *replacement* (useful for scrubbing PII / secrets from messages).
    """
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(kw) for kw in keywords) + r")\b",
        re.IGNORECASE,
    )

    def _rule(record: Dict, metrics: Metrics) -> Optional[Dict]:
        val = str(record.get(field, ""))
        new_val, n = pattern.subn(replacement, val)
        if n:
            metrics.record(f"keyword_redacted_{field}",
                           f'{n} occurrence(s) in record')
            record[field] = new_val
        return record

    _rule.__name__ = f"rule_keyword_filter_{field}"
    return _rule


# ══════════════════════════════════════════════════════════════════════════════
# STATE CONTAINER
# ══════════════════════════════════════════════════════════════════════════════

class AppState:
    def __init__(self):
        self.raw:     Optional[List[Dict]] = None
        self.cleaned: Optional[List[Dict]] = None
        self.metrics: Optional[Metrics]    = None
        self.custom_rules: List[Callable]  = []


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

BANNER = f"""
{BOLD}{CYAN}
  ╔══════════════════════════════════════════════════════════════╗
  ║       🧹  Data Cleaning Automation Tool                      ║
  ║           Pure Python · Zero Dependencies                    ║
  ╚══════════════════════════════════════════════════════════════╝
{RESET}"""

MENU = f"""
{BOLD}  ┌─ Main Menu ──────────────────────────────────────────────────┐{RESET}
  │  {c('1', BOLD)}  Generate sample dirty data                              │
  │  {c('2', BOLD)}  Run cleaning pipeline                                   │
  │  {c('3', BOLD)}  View raw  data                                          │
  │  {c('4', BOLD)}  View cleaned data                                       │
  │  {c('5', BOLD)}  View cleaning metrics / summary                         │
  │  {c('6', BOLD)}  Before / after spot-check                               │
  │  {c('7', BOLD)}  Add custom keyword-redaction rule                       │
  │  {c('8', BOLD)}  Export cleaned data to JSON                             │
  │  {c('0', BOLD)}  Exit                                                    │
{BOLD}  └──────────────────────────────────────────────────────────────┘{RESET}
"""


def prompt(msg: str) -> str:
    return input(f"\n  {YELLOW}▶ {msg}{RESET} ").strip()


def require_raw(state: AppState) -> bool:
    if state.raw is None:
        print(c("\n  ⚠  No data loaded. Run option 1 first.", YELLOW))
        return False
    return True


def require_cleaned(state: AppState) -> bool:
    if state.cleaned is None:
        print(c("\n  ⚠  Data not yet cleaned. Run option 2 first.", YELLOW))
        return False
    return True


def run_cli() -> None:
    print(BANNER)
    state = AppState()

    while True:
        print(MENU)
        choice = prompt("Select an option:") or ""

        # ── 1. Generate dirty data ────────────────────────────────────────────
        if choice == "1":
            n_str = prompt("How many extra random noisy records to append? [0]:") or "0"
            try:
                extra = max(0, int(n_str))
            except ValueError:
                extra = 0
            state.raw = copy.deepcopy(RAW_RECORDS)
            # Append extra randomly mangled records
            import random, string
            for _ in range(extra):
                state.raw.append({
                    "timestamp": random.choice([
                        "2024-03-17 09:00:00",
                        "17/03/2024 09:00",
                        "",
                        None,
                    ]),
                    random.choice(["source", "src", "host"]): "".join(
                        random.choices(string.ascii_lowercase, k=6)
                    ),
                    random.choice(["event_type", "type"]): random.choice(
                        ["LOGIN_FAILURE", "port_scan", "  XSS_attempt  ", ""]
                    ),
                    random.choice(["user_ip", "ip", "addr"]): ".".join(
                        str(random.randint(0, 310)) for _ in range(4)
                    ),
                    random.choice(["status", "state"]): random.choice(
                        ["200", "failure", "WARN", "blocked", ""]
                    ),
                    "message": "  " + "".join(
                        random.choices(string.printable[:70], k=30)
                    ) + "  ",
                })
            state.cleaned = None
            state.metrics = None
            print(c(f"\n  ✔ Loaded {len(state.raw)} raw records ({len(RAW_RECORDS)} built-in + {extra} random).", GREEN))

        # ── 2. Run pipeline ───────────────────────────────────────────────────
        elif choice == "2":
            if not require_raw(state):
                continue
            state.cleaned, state.metrics = run_pipeline(
                state.raw, custom_rules=state.custom_rules
            )
            print(c(
                f"\n  ✔ Cleaning complete: "
                f"{len(state.raw)} → {len(state.cleaned)} records, "
                f"{state.metrics.total()} fixes applied.",
                GREEN,
            ))

        # ── 3. View raw data ──────────────────────────────────────────────────
        elif choice == "3":
            if not require_raw(state):
                continue
            print_raw_dict(state.raw, f"Raw Data  ({len(state.raw)} records)")

        # ── 4. View cleaned data ──────────────────────────────────────────────
        elif choice == "4":
            if not require_cleaned(state):
                continue
            print_records(state.cleaned, f"Cleaned Data  ({len(state.cleaned)} records)")

        # ── 5. Metrics ────────────────────────────────────────────────────────
        elif choice == "5":
            if not require_cleaned(state):
                continue
            print_metrics(state.metrics, len(state.raw), len(state.cleaned))

        # ── 6. Before / after spot-check ──────────────────────────────────────
        elif choice == "6":
            if not require_cleaned(state):
                continue
            print_diff_summary(state.raw, state.cleaned)

        # ── 7. Custom keyword-redaction rule ──────────────────────────────────
        elif choice == "7":
            field = prompt("Field to apply redaction to [message]:") or "message"
            kw_raw = prompt("Comma-separated keywords to redact:")
            if not kw_raw:
                print(c("  No keywords entered.", YELLOW))
                continue
            keywords = [kw.strip() for kw in kw_raw.split(",") if kw.strip()]
            repl = prompt("Replacement text [(redacted)]:") or "(redacted)"
            rule = make_keyword_filter(field, keywords, repl)
            state.custom_rules.append(rule)
            print(c(
                f"\n  ✔ Redaction rule added: {len(keywords)} keyword(s) in '{field}' → '{repl}'.\n"
                f"    Re-run option 2 to apply.",
                GREEN,
            ))

        # ── 8. Export ─────────────────────────────────────────────────────────
        elif choice == "8":
            if not require_cleaned(state):
                continue
            fname = prompt("Output filename [cleaned_data.json]:") or "cleaned_data.json"
            path = export_to_json(state.cleaned, fname)
            print(c(f"\n  ✔ Exported {len(state.cleaned)} records → {path}", GREEN))

        # ── 0. Exit ───────────────────────────────────────────────────────────
        elif choice == "0":
            print(c("\n  Goodbye! 👋\n", CYAN))
            sys.exit(0)

        else:
            print(c("\n  Unknown option.", YELLOW))


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print(c("\n\n  Interrupted. Exiting cleanly.\n", YELLOW))
        sys.exit(0)