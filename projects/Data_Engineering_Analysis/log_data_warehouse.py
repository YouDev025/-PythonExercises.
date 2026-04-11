#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          Log Data Warehouse — Security Log Manager           ║
║  SQLite (default) with optional PostgreSQL support           ║
╚══════════════════════════════════════════════════════════════╝

Run with:  python log_data_warehouse.py
"""

import sqlite3
import json
import random
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

# ── Optional PostgreSQL support ───────────────────────────────────────────────
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# ── Colour helpers (no external deps) ─────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
MAGENTA= "\033[95m"
DIM    = "\033[2m"

def c(text: str, colour: str) -> str:
    """Wrap text in ANSI colour codes."""
    return f"{colour}{text}{RESET}"

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE LAYER
# ══════════════════════════════════════════════════════════════════════════════

class DatabaseAdapter:
    """
    Thin adapter that normalises the API differences between sqlite3 and
    psycopg2 so the rest of the code can stay database-agnostic.
    """

    PLACEHOLDER: str = "?"          # overridden for PostgreSQL

    def __init__(self):
        self.conn = None

    # ── Connection helpers ────────────────────────────────────────────────────

    def connect_sqlite(self, db_path: str = "security_logs.db") -> None:
        """Open (or create) a local SQLite database file."""
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row   # dict-like rows
        self.PLACEHOLDER = "?"
        print(c(f"  ✔ Connected to SQLite database: {db_path}", GREEN))

    def connect_postgres(self, dsn: str) -> None:
        """
        Connect to a PostgreSQL server using a DSN string, e.g.:
          host=localhost dbname=logs user=postgres password=secret
        Raises RuntimeError if psycopg2 is not installed.
        """
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 is not installed. Run: pip install psycopg2-binary")
        self.conn = psycopg2.connect(dsn)
        self.PLACEHOLDER = "%s"     # PostgreSQL uses %s placeholders
        print(c("  ✔ Connected to PostgreSQL database.", GREEN))

    def close(self) -> None:
        if self.conn:
            self.conn.close()

    # ── Cursor helpers ────────────────────────────────────────────────────────

    def cursor(self):
        return self.conn.cursor()

    def commit(self) -> None:
        self.conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> Any:
        """Execute a single statement and return the cursor."""
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql: str, params_list: List[tuple]) -> None:
        """Batch-execute a statement."""
        cur = self.cursor()
        cur.executemany(sql, params_list)

    def fetchall(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Return all rows as a list of plain dicts."""
        cur = self.execute(sql, params)
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        """Return the first matching row as a plain dict, or None."""
        cur = self.execute(sql, params)
        columns = [d[0] for d in cur.description]
        row = cur.fetchone()
        return dict(zip(columns, row)) if row else None

    # ── SQL dialect helper ────────────────────────────────────────────────────

    def ph(self, n: int = 1) -> str:
        """Return comma-separated placeholders, e.g. ph(3) → '?, ?, ?'."""
        return ", ".join([self.PLACEHOLDER] * n)


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMA & INDEX SETUP
# ══════════════════════════════════════════════════════════════════════════════

def create_schema(db: DatabaseAdapter) -> None:
    """
    Create the 'logs' table plus performance indexes.
    Uses IF NOT EXISTS so it is safe to call multiple times.
    """
    db.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            source      TEXT    NOT NULL,
            event_type  TEXT    NOT NULL,
            user_ip     TEXT,
            status      TEXT    NOT NULL,
            message     TEXT
        )
    """)

    # Performance indexes on the most-queried columns
    for idx_name, col in [
        ("idx_logs_event_type", "event_type"),
        ("idx_logs_user_ip",    "user_ip"),
        ("idx_logs_status",     "status"),
        ("idx_logs_timestamp",  "timestamp"),
    ]:
        db.execute(
            f"CREATE INDEX IF NOT EXISTS {idx_name} ON logs ({col})"
        )

    db.commit()
    print(c("  ✔ Schema and indexes created (or already exist).", GREEN))


# ══════════════════════════════════════════════════════════════════════════════
# SAMPLE DATA GENERATION
# ══════════════════════════════════════════════════════════════════════════════

# Pools used to generate realistic-looking log entries
_EVENT_TYPES = [
    "LOGIN_SUCCESS", "LOGIN_FAILURE", "LOGOUT",
    "FILE_ACCESS",   "FILE_DELETE",   "FILE_UPLOAD",
    "PORT_SCAN",     "BRUTE_FORCE",   "SQL_INJECTION",
    "XSS_ATTEMPT",   "PRIVILEGE_ESC", "CONFIG_CHANGE",
]

_SOURCES = [
    "auth-service", "file-server", "web-app",
    "firewall",     "ids",         "vpn-gateway",
    "db-server",    "mail-server",
]

_STATUSES = ["SUCCESS", "FAILURE", "WARNING", "BLOCKED", "PENDING"]

_IP_POOL = [
    "192.168.1.{}".format(i) for i in range(1, 21)
] + [
    "10.0.0.{}".format(i) for i in range(1, 11)
] + [
    "203.0.113.{}".format(i) for i in range(1, 6)    # external / attacker IPs
]

_MESSAGES = {
    "LOGIN_SUCCESS":  "User authenticated successfully.",
    "LOGIN_FAILURE":  "Invalid credentials provided.",
    "LOGOUT":         "User session terminated normally.",
    "FILE_ACCESS":    "Read access granted to sensitive file.",
    "FILE_DELETE":    "File deletion event detected.",
    "FILE_UPLOAD":    "New file uploaded to server.",
    "PORT_SCAN":      "Suspicious port scan detected from source IP.",
    "BRUTE_FORCE":    "Multiple failed login attempts — possible brute-force.",
    "SQL_INJECTION":  "Malicious SQL payload detected in request.",
    "XSS_ATTEMPT":    "Cross-site scripting attempt blocked.",
    "PRIVILEGE_ESC":  "Privilege escalation attempt detected.",
    "CONFIG_CHANGE":  "System configuration modified.",
}


def _random_timestamp(days_back: int = 30) -> str:
    """Return a random ISO-8601 timestamp within the last *days_back* days."""
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%d %H:%M:%S")


def generate_sample_logs(n: int = 100) -> List[Tuple]:
    """
    Generate *n* random log tuples ready for batch insertion.
    Tuple order: (timestamp, source, event_type, user_ip, status, message)
    """
    rows = []
    for _ in range(n):
        event = random.choice(_EVENT_TYPES)
        rows.append((
            _random_timestamp(),
            random.choice(_SOURCES),
            event,
            random.choice(_IP_POOL),
            random.choice(_STATUSES),
            _MESSAGES.get(event, "System event recorded."),
        ))
    return rows


def insert_sample_logs(db: DatabaseAdapter, n: int = 100) -> None:
    """Batch-insert *n* randomly generated log entries."""
    rows = generate_sample_logs(n)
    sql = (
        "INSERT INTO logs (timestamp, source, event_type, user_ip, status, message) "
        f"VALUES ({db.ph(6)})"
    )
    db.executemany(sql, rows)
    db.commit()
    print(c(f"  ✔ Inserted {n} sample log entries.", GREEN))


# ══════════════════════════════════════════════════════════════════════════════
# QUERY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def fetch_all_logs(db: DatabaseAdapter, limit: int = 50) -> List[Dict]:
    """Return the most recent *limit* log entries."""
    return db.fetchall(
        "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,)
    )


def filter_by_event_type(db: DatabaseAdapter, event_type: str) -> List[Dict]:
    """Return all logs matching the given event_type (case-insensitive)."""
    return db.fetchall(
        "SELECT * FROM logs WHERE UPPER(event_type) = UPPER(?) ORDER BY timestamp DESC",
        (event_type,),
    )


def filter_by_ip(db: DatabaseAdapter, ip: str) -> List[Dict]:
    """Return all logs originating from the given IP address."""
    return db.fetchall(
        "SELECT * FROM logs WHERE user_ip = ? ORDER BY timestamp DESC",
        (ip,),
    )


def filter_by_status(db: DatabaseAdapter, status: str) -> List[Dict]:
    """Return all logs with the given status (case-insensitive)."""
    return db.fetchall(
        "SELECT * FROM logs WHERE UPPER(status) = UPPER(?) ORDER BY timestamp DESC",
        (status,),
    )


def filter_by_time_range(
    db: DatabaseAdapter,
    start: str,
    end: str,
) -> List[Dict]:
    """
    Return logs whose timestamp falls within [start, end].
    Both arguments must be strings formatted as 'YYYY-MM-DD HH:MM:SS'
    or 'YYYY-MM-DD'.
    """
    return db.fetchall(
        "SELECT * FROM logs WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC",
        (start, end),
    )


# ══════════════════════════════════════════════════════════════════════════════
# AGGREGATION / STATISTICS
# ══════════════════════════════════════════════════════════════════════════════

def count_by_event_type(db: DatabaseAdapter) -> List[Dict]:
    """Return event counts grouped by event_type, highest first."""
    return db.fetchall(
        "SELECT event_type, COUNT(*) AS count FROM logs "
        "GROUP BY event_type ORDER BY count DESC"
    )


def top_active_ips(db: DatabaseAdapter, top_n: int = 10) -> List[Dict]:
    """Return the *top_n* most active source IPs."""
    return db.fetchall(
        "SELECT user_ip, COUNT(*) AS count FROM logs "
        "GROUP BY user_ip ORDER BY count DESC LIMIT ?",
        (top_n,),
    )


def status_breakdown(db: DatabaseAdapter) -> List[Dict]:
    """Return event counts grouped by status."""
    return db.fetchall(
        "SELECT status, COUNT(*) AS count FROM logs "
        "GROUP BY status ORDER BY count DESC"
    )


def total_log_count(db: DatabaseAdapter) -> int:
    row = db.fetchone("SELECT COUNT(*) AS cnt FROM logs")
    return row["cnt"] if row else 0


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def export_to_json(rows: List[Dict], filename: str) -> str:
    """Serialise *rows* to a JSON file and return the absolute path."""
    path = os.path.abspath(filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, default=str)
    return path


# ══════════════════════════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

# Status colour mapping
_STATUS_COLOURS = {
    "SUCCESS": GREEN,
    "FAILURE": RED,
    "WARNING": YELLOW,
    "BLOCKED": MAGENTA,
    "PENDING": DIM,
}

# Event-type colour mapping (highlight threats)
_EVENT_COLOURS = {
    "PORT_SCAN":     RED,
    "BRUTE_FORCE":   RED,
    "SQL_INJECTION": RED,
    "XSS_ATTEMPT":   RED,
    "PRIVILEGE_ESC": MAGENTA,
    "LOGIN_FAILURE": YELLOW,
    "CONFIG_CHANGE": YELLOW,
}


def _colour_status(status: str) -> str:
    return c(status, _STATUS_COLOURS.get(status.upper(), RESET))


def _colour_event(event: str) -> str:
    return c(event, _EVENT_COLOURS.get(event.upper(), CYAN))


def print_logs(rows: List[Dict], title: str = "Query Results") -> None:
    """Pretty-print a list of log rows in a table."""
    if not rows:
        print(c("  (no results)", DIM))
        return

    # Dynamic column widths
    w_src  = max(len(r.get("source",     "") or "") for r in rows)
    w_evt  = max(len(r.get("event_type", "") or "") for r in rows)
    w_ip   = max(len(r.get("user_ip",    "") or "") for r in rows)
    w_stat = max(len(r.get("status",     "") or "") for r in rows)

    w_src  = max(w_src,  6)
    w_evt  = max(w_evt,  10)
    w_ip   = max(w_ip,   15)
    w_stat = max(w_stat, 7)

    sep = (
        f"  +{'─'*6}+{'─'*20}+{'─'*(w_src+2)}+"
        f"{'─'*(w_evt+2)}+{'─'*(w_ip+2)}+{'─'*(w_stat+2)}+{'─'*42}+"
    )

    header = (
        f"  │{'ID':^6}│{'Timestamp':^20}│{'Source':^{w_src+2}}│"
        f"{'Event Type':^{w_evt+2}}│{'IP':^{w_ip+2}}│{'Status':^{w_stat+2}}│"
        f"{'Message':^42}│"
    )

    print()
    print(c(f"  ── {title} ({'─' * (len(sep) - len(title) - 7)})", BOLD + CYAN))
    print(sep)
    print(c(header, BOLD))
    print(sep)

    for r in rows:
        msg = (r.get("message") or "")[:40]
        row_str = (
            f"  │{str(r.get('id','')):<6}│"
            f"{(r.get('timestamp') or ''):<20}│"
            f"{(r.get('source') or ''):<{w_src+2}}│"
        )
        # coloured columns printed separately so ANSI codes don't break width
        print(
            f"  │{str(r.get('id','')):<6}"
            f"│{(r.get('timestamp') or ''):<20}"
            f"│{(r.get('source') or ''):<{w_src+2}}"
            f"│{_colour_event(r.get('event_type','')):<{w_evt+2+10}}"   # +10 for ANSI codes
            f"│{(r.get('user_ip') or ''):<{w_ip+2}}"
            f"│{_colour_status(r.get('status','')):<{w_stat+2+10}}"
            f"│{msg:<42}│"
        )

    print(sep)
    print(c(f"  Total rows shown: {len(rows)}", DIM))


def print_stats_table(rows: List[Dict], key_col: str, val_col: str, title: str) -> None:
    """Print a two-column statistics table."""
    if not rows:
        print(c("  (no data)", DIM))
        return

    w_key = max(len(str(r.get(key_col, ""))) for r in rows)
    w_key = max(w_key, len(key_col)) + 2

    bar_max = max(r.get(val_col, 0) for r in rows)
    bar_width = 30

    print()
    print(c(f"  ── {title} ──", BOLD + CYAN))
    print(f"  {'─' * (w_key + bar_width + 16)}")
    print(c(f"  {'':2}{key_col:<{w_key}} {'Count':>8}  {'Bar':<{bar_width}}", BOLD))
    print(f"  {'─' * (w_key + bar_width + 16)}")

    for r in rows:
        key  = str(r.get(key_col, ""))
        val  = r.get(val_col, 0)
        frac = val / bar_max if bar_max else 0
        bar  = "█" * int(frac * bar_width)
        colour = _EVENT_COLOURS.get(key.upper(), _STATUS_COLOURS.get(key.upper(), CYAN))
        print(f"  {c(key, colour):<{w_key + 12}} {val:>8}  {c(bar, colour)}")

    print(f"  {'─' * (w_key + bar_width + 16)}")


# ══════════════════════════════════════════════════════════════════════════════
# CLI MENU
# ══════════════════════════════════════════════════════════════════════════════

BANNER = f"""
{BOLD}{CYAN}
  ╔══════════════════════════════════════════════════════════╗
  ║         🔐 Security Log Data Warehouse                   ║
  ║         SQLite · Optional PostgreSQL                     ║
  ╚══════════════════════════════════════════════════════════╝
{RESET}"""

MENU = f"""
{BOLD}  ┌─ Main Menu ─────────────────────────────────────────────┐{RESET}
  │  {c('1','BOLD')}  Initialize database & schema                          │
  │  {c('2','BOLD')}  Insert sample logs (100 rows)                         │
  │  {c('3','BOLD')}  View recent logs   (last 20)                          │
  │  {c('4','BOLD')}  Filter by event type                                  │
  │  {c('5','BOLD')}  Filter by IP address                                  │
  │  {c('6','BOLD')}  Filter by status                                      │
  │  {c('7','BOLD')}  Filter by time range                                  │
  │  {c('8','BOLD')}  View statistics                                       │
  │  {c('9','BOLD')}  Export last query to JSON                             │
  │  {c('0','BOLD')}  Exit                                                  │
{BOLD}  └─────────────────────────────────────────────────────────┘{RESET}
"""


def prompt(msg: str) -> str:
    return input(f"\n  {YELLOW}▶ {msg}{RESET} ").strip()


def run_cli() -> None:
    """Main interactive CLI loop."""
    print(BANNER)

    # ── Database selection ────────────────────────────────────────────────────
    db_type = "sqlite"
    if PSYCOPG2_AVAILABLE:
        choice = prompt("Use [1] SQLite (default) or [2] PostgreSQL? [1/2]:") or "1"
        if choice == "2":
            db_type = "postgres"

    db  = DatabaseAdapter()
    dsn = ""
    if db_type == "postgres":
        dsn = prompt("Enter PostgreSQL DSN (e.g. host=localhost dbname=logs user=postgres password=secret):")
        try:
            db.connect_postgres(dsn)
        except Exception as exc:
            print(c(f"  ✘ PostgreSQL connection failed: {exc}", RED))
            print(c("  ↩ Falling back to SQLite.", YELLOW))
            db.connect_sqlite()
    else:
        db.connect_sqlite()

    last_results: List[Dict] = []   # remember last query for JSON export

    while True:
        print(MENU)
        choice = prompt("Select an option:") or ""

        # ── 1. Initialise ─────────────────────────────────────────────────────
        if choice == "1":
            print()
            create_schema(db)

        # ── 2. Insert sample logs ─────────────────────────────────────────────
        elif choice == "2":
            print()
            n_str = prompt("How many sample logs to insert? [default 100]:") or "100"
            try:
                n = int(n_str)
            except ValueError:
                n = 100
            insert_sample_logs(db, n)

        # ── 3. View recent logs ───────────────────────────────────────────────
        elif choice == "3":
            rows = fetch_all_logs(db, limit=20)
            last_results = rows
            print_logs(rows, title="Recent Logs (latest 20)")

        # ── 4. Filter by event type ───────────────────────────────────────────
        elif choice == "4":
            # Show available event types first
            stats = count_by_event_type(db)
            if stats:
                types = ", ".join(c(r["event_type"], CYAN) for r in stats)
                print(f"\n  Available types: {types}")
            et = prompt("Enter event type (e.g. LOGIN_FAILURE):").upper()
            if et:
                rows = filter_by_event_type(db, et)
                last_results = rows
                print_logs(rows, title=f"Logs with event_type = {et}")

        # ── 5. Filter by IP ───────────────────────────────────────────────────
        elif choice == "5":
            ip = prompt("Enter IP address (e.g. 192.168.1.5):")
            if ip:
                rows = filter_by_ip(db, ip)
                last_results = rows
                print_logs(rows, title=f"Logs from IP {ip}")

        # ── 6. Filter by status ───────────────────────────────────────────────
        elif choice == "6":
            avail = ", ".join(c(s, _STATUS_COLOURS.get(s, RESET)) for s in _STATUSES)
            print(f"\n  Available statuses: {avail}")
            status = prompt("Enter status:").upper()
            if status:
                rows = filter_by_status(db, status)
                last_results = rows
                print_logs(rows, title=f"Logs with status = {status}")

        # ── 7. Time range ──────────────────────────────────────────────────────
        elif choice == "7":
            print(c("\n  Format: YYYY-MM-DD  or  YYYY-MM-DD HH:MM:SS", DIM))
            # Suggest a sensible default range
            end_def   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            start_def = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
            start = prompt(f"Start datetime [{start_def}]:") or start_def
            end   = prompt(f"End datetime   [{end_def}]:") or end_def
            rows  = filter_by_time_range(db, start, end)
            last_results = rows
            print_logs(rows, title=f"Logs from {start} to {end}")

        # ── 8. Statistics ──────────────────────────────────────────────────────
        elif choice == "8":
            total = total_log_count(db)
            print(f"\n  {BOLD}Total logs in warehouse: {c(str(total), CYAN)}{RESET}")

            # Events per type
            by_type = count_by_event_type(db)
            print_stats_table(by_type, "event_type", "count", "Events per Type")

            # Top IPs
            top_ips = top_active_ips(db, top_n=10)
            print_stats_table(top_ips, "user_ip", "count", "Top 10 Most Active IPs")

            # Status breakdown
            by_status = status_breakdown(db)
            print_stats_table(by_status, "status", "count", "Status Breakdown")

            last_results = by_type   # handy to export

        # ── 9. Export to JSON ──────────────────────────────────────────────────
        elif choice == "9":
            if not last_results:
                print(c("\n  No results in buffer. Run a query first.", YELLOW))
            else:
                fname = prompt("Filename [default: export.json]:") or "export.json"
                path  = export_to_json(last_results, fname)
                print(c(f"\n  ✔ Exported {len(last_results)} rows → {path}", GREEN))

        # ── 0. Exit ────────────────────────────────────────────────────────────
        elif choice == "0":
            print(c("\n  Goodbye! 👋\n", CYAN))
            db.close()
            sys.exit(0)

        else:
            print(c("\n  Unknown option. Please choose from the menu.", YELLOW))


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print(c("\n\n  Interrupted. Exiting cleanly.\n", YELLOW))
        sys.exit(0)