"""
basic_dns_resolver.py
Simulates a DNS resolver with caching (TTL), a local zone database,
recursive stub resolution, query logging, and an interactive console.
"""

from __future__ import annotations
import time
import re
import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto


# ══════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════

class RecordType(Enum):
    A     = "A"       # IPv4
    AAAA  = "AAAA"    # IPv6
    CNAME = "CNAME"   # Canonical name alias
    MX    = "MX"      # Mail exchange
    TXT   = "TXT"     # Text record
    NS    = "NS"      # Name server


class QueryResult(Enum):
    CACHE_HIT  = auto()
    CACHE_MISS = auto()
    NOT_FOUND  = auto()
    ERROR      = auto()


# ══════════════════════════════════════════════════════════════
# Exceptions
# ══════════════════════════════════════════════════════════════

class DNSError(Exception):
    """Base DNS exception."""

class InvalidDomainError(DNSError):
    pass

class RecordNotFoundError(DNSError):
    pass

class InvalidRecordTypeError(DNSError):
    pass


# ══════════════════════════════════════════════════════════════
# DNSRecord
# ══════════════════════════════════════════════════════════════

@dataclass
class DNSRecord:
    """Represents a single DNS resource record."""
    domain_name: str
    record_type: RecordType
    value:       str          # IP address, CNAME target, MX host, etc.
    ttl:         int = 300    # seconds; 0 = no expiry (static zone entries)

    def __post_init__(self) -> None:
        self.domain_name = self.domain_name.lower().rstrip(".")
        if not self.domain_name:
            raise InvalidDomainError("domain_name cannot be empty.")
        if not self.value.strip():
            raise DNSError("Record value cannot be empty.")

    def __repr__(self) -> str:
        return (
            f"DNSRecord({self.domain_name!r} "
            f"{self.record_type.value} {self.value!r} "
            f"ttl={self.ttl})"
        )


# ══════════════════════════════════════════════════════════════
# CacheEntry  (internal wrapper used by DNSCache)
# ══════════════════════════════════════════════════════════════

@dataclass
class CacheEntry:
    record:     DNSRecord
    cached_at:  float = field(default_factory=time.time)

    @property
    def expires_at(self) -> Optional[float]:
        if self.record.ttl == 0:
            return None
        return self.cached_at + self.record.ttl

    @property
    def is_expired(self) -> bool:
        if self.record.ttl == 0:
            return False
        return time.time() > (self.cached_at + self.record.ttl)

    @property
    def remaining_ttl(self) -> int:
        if self.record.ttl == 0:
            return 0   # static
        remaining = self.expires_at - time.time()
        return max(0, int(remaining))

    def age_str(self) -> str:
        age = int(time.time() - self.cached_at)
        return f"{age}s ago"


# ══════════════════════════════════════════════════════════════
# DNSCache
# ══════════════════════════════════════════════════════════════

class DNSCache:
    """
    In-memory cache for DNS records with TTL-based expiration.
    Keys: (domain_name, record_type)
    """

    def __init__(self):
        self._store: dict[tuple[str, RecordType], CacheEntry] = {}

    # ── public API ──────────────────────────────────────────────

    def put(self, record: DNSRecord) -> None:
        key = (record.domain_name, record.record_type)
        self._store[key] = CacheEntry(record=record)

    def get(
        self, domain: str, rtype: RecordType
    ) -> Optional[tuple[DNSRecord, int]]:
        """
        Returns (record, remaining_ttl) on hit, None on miss/expired.
        Expired entries are purged automatically.
        """
        domain = domain.lower().rstrip(".")
        key    = (domain, rtype)
        entry  = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired:
            del self._store[key]
            return None
        return entry.record, entry.remaining_ttl

    def invalidate(self, domain: str, rtype: Optional[RecordType] = None) -> int:
        """Remove one or all record types for a domain. Returns count removed."""
        domain  = domain.lower().rstrip(".")
        removed = 0
        keys    = list(self._store.keys())
        for k in keys:
            if k[0] == domain and (rtype is None or k[1] == rtype):
                del self._store[k]
                removed += 1
        return removed

    def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count

    def purge_expired(self) -> int:
        expired = [k for k, e in self._store.items() if e.is_expired]
        for k in expired:
            del self._store[k]
        return len(expired)

    def all_entries(self) -> list[CacheEntry]:
        self.purge_expired()
        return list(self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"DNSCache({len(self._store)} entries)"


# ══════════════════════════════════════════════════════════════
# Simulated zone database (replaces a real upstream resolver)
# ══════════════════════════════════════════════════════════════

_ZONE_DB: list[DNSRecord] = [
    # A records
    DNSRecord("google.com",       RecordType.A,     "142.250.80.46",    ttl=300),
    DNSRecord("www.google.com",   RecordType.CNAME, "google.com",       ttl=300),
    DNSRecord("youtube.com",      RecordType.A,     "142.250.80.78",    ttl=300),
    DNSRecord("github.com",       RecordType.A,     "140.82.121.4",     ttl=60),
    DNSRecord("stackoverflow.com",RecordType.A,     "151.101.193.69",   ttl=120),
    DNSRecord("wikipedia.org",    RecordType.A,     "208.80.154.224",   ttl=600),
    DNSRecord("python.org",       RecordType.A,     "151.101.0.223",    ttl=300),
    DNSRecord("example.com",      RecordType.A,     "93.184.216.34",    ttl=86400),
    DNSRecord("localhost",        RecordType.A,     "127.0.0.1",        ttl=0),
    DNSRecord("api.example.com",  RecordType.CNAME, "example.com",      ttl=300),
    # AAAA records
    DNSRecord("google.com",       RecordType.AAAA,  "2607:f8b0:4004:c09::64", ttl=300),
    DNSRecord("github.com",       RecordType.AAAA,  "2606:50c0:8000::153",    ttl=60),
    # MX records
    DNSRecord("google.com",       RecordType.MX,    "10 smtp.google.com",     ttl=3600),
    DNSRecord("example.com",      RecordType.MX,    "10 mail.example.com",    ttl=3600),
    # TXT records
    DNSRecord("google.com",       RecordType.TXT,   "v=spf1 include:_spf.google.com ~all", ttl=3600),
    DNSRecord("example.com",      RecordType.TXT,   "v=spf1 -all",            ttl=3600),
    # NS records
    DNSRecord("google.com",       RecordType.NS,    "ns1.google.com",         ttl=21600),
    DNSRecord("example.com",      RecordType.NS,    "a.iana-servers.net",     ttl=21600),
    DNSRecord("python.org",       RecordType.NS,    "ns1.python.org",         ttl=21600),
]

def _zone_lookup(domain: str, rtype: RecordType) -> Optional[DNSRecord]:
    domain = domain.lower().rstrip(".")
    for rec in _ZONE_DB:
        if rec.domain_name == domain and rec.record_type == rtype:
            return rec
    return None


# ══════════════════════════════════════════════════════════════
# QueryLog entry
# ══════════════════════════════════════════════════════════════

@dataclass
class QueryLog:
    query_id:    int
    domain:      str
    record_type: RecordType
    result:      QueryResult
    answer:      Optional[str]       # resolved value or None
    source:      str                 # "cache" | "zone_db" | "not_found" | "error"
    latency_ms:  float
    timestamp:   datetime = field(default_factory=datetime.now)
    note:        str = ""

    def display(self) -> str:
        icon = {
            QueryResult.CACHE_HIT:  "⚡",
            QueryResult.CACHE_MISS: "🔍",
            QueryResult.NOT_FOUND:  "✘",
            QueryResult.ERROR:      "⚠",
        }[self.result]
        ts      = self.timestamp.strftime("%H:%M:%S")
        answer  = self.answer or "–"
        latency = f"{self.latency_ms:.1f}ms"
        return (
            f"  [{ts}] #{self.query_id:04d} {icon} "
            f"{self.domain:<30} {self.record_type.value:<5} "
            f"{answer:<40} [{self.source:<8}] {latency}"
            + (f"  {self.note}" if self.note else "")
        )


# ══════════════════════════════════════════════════════════════
# DNSResolver
# ══════════════════════════════════════════════════════════════

class DNSResolver:
    """
    Performs DNS resolution:
    1. Check cache → return immediately on hit.
    2. Query zone DB → store in cache, return on hit.
    3. Follow CNAME chain (max 5 hops) if needed.
    4. Return NOT_FOUND if nothing matches.
    """

    MAX_CNAME_DEPTH = 5

    def __init__(self, cache: DNSCache):
        self._cache = cache

    def resolve(
        self,
        domain: str,
        rtype: RecordType = RecordType.A,
    ) -> tuple[Optional[DNSRecord], QueryResult, str, float]:
        """
        Returns (record, result_enum, source_str, latency_ms).
        Simulates network latency for zone_db lookups.
        """
        start = time.perf_counter()
        domain = domain.lower().rstrip(".")

        record, result, source = self._resolve_with_cname(domain, rtype, depth=0)

        latency = (time.perf_counter() - start) * 1000
        return record, result, source, latency

    # ── private ─────────────────────────────────────────────────

    def _resolve_with_cname(
        self, domain: str, rtype: RecordType, depth: int
    ) -> tuple[Optional[DNSRecord], QueryResult, str]:

        if depth > self.MAX_CNAME_DEPTH:
            return None, QueryResult.ERROR, "cname_loop"

        # 1. Cache check
        hit = self._cache.get(domain, rtype)
        if hit:
            rec, _ = hit
            return rec, QueryResult.CACHE_HIT, "cache"

        # 2. Zone DB lookup (simulate ~5–40 ms upstream delay)
        time.sleep(random.uniform(0.005, 0.04))
        rec = _zone_lookup(domain, rtype)
        if rec:
            self._cache.put(rec)
            return rec, QueryResult.CACHE_MISS, "zone_db"

        # 3. If looking for A/AAAA, try following a CNAME
        if rtype in (RecordType.A, RecordType.AAAA):
            cname_hit = self._cache.get(domain, RecordType.CNAME)
            if cname_hit:
                cname_rec, _ = cname_hit
            else:
                cname_rec = _zone_lookup(domain, RecordType.CNAME)
                if cname_rec:
                    self._cache.put(cname_rec)

            if cname_rec:
                return self._resolve_with_cname(
                    cname_rec.value, rtype, depth + 1
                )

        return None, QueryResult.NOT_FOUND, "not_found"


# ══════════════════════════════════════════════════════════════
# ResolverManager
# ══════════════════════════════════════════════════════════════

class ResolverManager:
    """
    Public-facing coordinator:
    - Accepts query requests
    - Manages the cache and resolver
    - Maintains a query log
    - Provides display helpers
    """

    _DOMAIN_RE = re.compile(
        r"^(?:[a-zA-Z0-9]"
        r"(?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
        r"\.)*[a-zA-Z0-9]"
        r"(?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
    )

    def __init__(self):
        self._cache    = DNSCache()
        self._resolver = DNSResolver(self._cache)
        self._log:   list[QueryLog] = []
        self._seq:   int = 0

    # ── query ────────────────────────────────────────────────────

    def query(
        self,
        domain: str,
        record_type: str | RecordType = "A",
    ) -> Optional[DNSRecord]:
        domain = domain.strip().lower().rstrip(".")

        # validate domain
        if not self._DOMAIN_RE.match(domain):
            self._log_entry(domain, RecordType.A, QueryResult.ERROR,
                            None, "error", 0.0, "Invalid domain name")
            raise InvalidDomainError(
                f"'{domain}' is not a valid domain name."
            )

        # validate / coerce record type
        if isinstance(record_type, str):
            try:
                rtype = RecordType[record_type.upper()]
            except KeyError:
                valid = ", ".join(r.value for r in RecordType)
                raise InvalidRecordTypeError(
                    f"Unknown record type '{record_type}'. Valid: {valid}"
                )
        else:
            rtype = record_type

        record, result, source, latency = self._resolver.resolve(domain, rtype)

        note = ""
        if result == QueryResult.CACHE_HIT and record is not None:
            hit = self._cache.get(record.domain_name, rtype)
            if hit:
                _, remaining = hit
                note = f"TTL remaining: {remaining}s"

        self._log_entry(
            domain, rtype, result,
            record.value if record else None,
            source, latency, note,
        )
        return record

    # ── cache management ─────────────────────────────────────────

    def clear_cache(self) -> int:
        n = self._cache.clear()
        print(f"  🗑  Cache cleared ({n} entries removed).")
        return n

    def purge_expired(self) -> int:
        n = self._cache.purge_expired()
        print(f"  ♻  Purged {n} expired cache entry(ies).")
        return n

    def invalidate(self, domain: str, rtype_str: Optional[str] = None) -> int:
        rtype = RecordType[rtype_str.upper()] if rtype_str else None
        n = self._cache.invalidate(domain, rtype)
        label = f"{rtype.value} " if rtype else ""
        print(f"  🗑  Invalidated {n} {label}record(s) for '{domain}'.")
        return n

    # ── display ──────────────────────────────────────────────────

    def show_cache(self) -> None:
        entries = self._cache.all_entries()
        print(f"\n  {'─'*68}")
        print(f"  DNS Cache  ({len(entries)} entry(ies))")
        print(f"  {'─'*68}")
        if not entries:
            print("  (empty)")
        else:
            header = (
                f"  {'Domain':<32} {'Type':<6} {'Value':<38} {'TTL':>8}"
            )
            print(header)
            print(f"  {'─'*68}")
            for e in sorted(entries, key=lambda x: x.record.domain_name):
                ttl_str = f"{e.remaining_ttl}s" if e.record.ttl > 0 else "static"
                print(
                    f"  {e.record.domain_name:<32} "
                    f"{e.record.record_type.value:<6} "
                    f"{e.record.value:<38} "
                    f"{ttl_str:>8}"
                )
        print(f"  {'─'*68}\n")

    def show_log(self, last_n: int = 0) -> None:
        entries = self._log[-last_n:] if last_n > 0 else self._log
        print(f"\n  {'─'*80}")
        print(f"  Query Log  ({len(self._log)} total, showing {len(entries)})")
        print(f"  {'─'*80}")
        if not entries:
            print("  (no queries yet)")
        else:
            print(
                f"  {'Time':>8}  {'#':>4}  "
                f"{'':2}  {'Domain':<30} {'Type':<5} "
                f"{'Answer':<40} {'Source':<8}  {'Latency'}"
            )
            print(f"  {'─'*80}")
            for entry in entries:
                print(entry.display())
        print(f"  {'─'*80}\n")

    def show_stats(self) -> None:
        total  = len(self._log)
        hits   = sum(1 for e in self._log if e.result == QueryResult.CACHE_HIT)
        misses = sum(1 for e in self._log if e.result == QueryResult.CACHE_MISS)
        nf     = sum(1 for e in self._log if e.result == QueryResult.NOT_FOUND)
        errs   = sum(1 for e in self._log if e.result == QueryResult.ERROR)
        hr     = hits / total * 100 if total else 0
        avg_ms = (
            sum(e.latency_ms for e in self._log) / total if total else 0
        )
        print(f"\n  ── Resolver Statistics {'─'*40}")
        print(f"  Total queries  : {total}")
        print(f"  Cache hits     : {hits}  ({hr:.1f}%)")
        print(f"  Cache misses   : {misses}")
        print(f"  Not found      : {nf}")
        print(f"  Errors         : {errs}")
        print(f"  Avg latency    : {avg_ms:.2f} ms")
        print(f"  Cache size     : {len(self._cache)} entries")
        print(f"  {'─'*62}\n")

    # ── private ─────────────────────────────────────────────────

    def _log_entry(
        self,
        domain: str,
        rtype: RecordType,
        result: QueryResult,
        answer: Optional[str],
        source: str,
        latency: float,
        note: str,
    ) -> None:
        self._seq += 1
        self._log.append(
            QueryLog(
                query_id    = self._seq,
                domain      = domain,
                record_type = rtype,
                result      = result,
                answer      = answer,
                source      = source,
                latency_ms  = latency,
                note        = note,
            )
        )


# ══════════════════════════════════════════════════════════════
# Interactive console
# ══════════════════════════════════════════════════════════════

def _print_result(record: Optional[DNSRecord], log: QueryLog) -> None:
    icons = {
        QueryResult.CACHE_HIT:  ("⚡", "CACHE HIT"),
        QueryResult.CACHE_MISS: ("🔍", "RESOLVED"),
        QueryResult.NOT_FOUND:  ("✘", "NOT FOUND"),
        QueryResult.ERROR:      ("⚠", "ERROR"),
    }
    icon, label = icons[log.result]
    print(f"\n  {icon}  [{label}]  {log.domain}  ({log.record_type.value})")
    if record:
        print(f"     Value   : {record.value}")
        print(f"     TTL     : {record.ttl}s" + (" (static)" if record.ttl == 0 else ""))
    print(f"     Source  : {log.source}")
    print(f"     Latency : {log.latency_ms:.2f} ms")
    if log.note:
        print(f"     Note    : {log.note}")
    print()


HELP_TEXT = """
  ┌──────────────────────────────────────────────────────────┐
  │  Basic DNS Resolver – Commands                           │
  ├──────────────────────────────────────────────────────────┤
  │  resolve <domain> [type]  Resolve a domain (A by default)│
  │  cache                    Show current cache contents    │
  │  log [n]                  Show query log (last n entries)│
  │  stats                    Show resolver statistics       │
  │  purge                    Remove expired cache entries   │
  │  clear                    Clear entire cache             │
  │  invalidate <domain> [T]  Remove domain from cache       │
  │  demo                     Run the built-in demo          │
  │  help                     Show this help                 │
  │  quit                     Exit the program               │
  └──────────────────────────────────────────────────────────┘
  Record types: A, AAAA, CNAME, MX, TXT, NS
"""


def run_demo(mgr: ResolverManager) -> None:
    """Built-in demo showcasing all major features."""
    print("\n" + "═" * 62)
    print("  DEMO MODE")
    print("═" * 62)

    scenarios = [
        # (label, domain, type, note)
        ("Initial A lookup (cache miss)",      "google.com",        "A",    ""),
        ("Repeat lookup (cache hit)",           "google.com",        "A",    ""),
        ("CNAME chain: www → google.com → A",  "www.google.com",    "A",    ""),
        ("AAAA record",                         "google.com",        "AAAA", ""),
        ("MX record",                           "google.com",        "MX",   ""),
        ("TXT record",                          "example.com",       "TXT",  ""),
        ("NS record",                           "python.org",        "NS",   ""),
        ("Short TTL domain",                    "github.com",        "A",    ""),
        ("Static (no-expiry) record",           "localhost",         "A",    ""),
        ("Non-existent domain",                 "doesnotexist.xyz",  "A",    ""),
        ("Second new domain (cache miss→hit)",  "stackoverflow.com", "A",    ""),
        ("Repeat → should be cached",           "stackoverflow.com", "A",    ""),
    ]

    for label, domain, rtype, _ in scenarios:
        print(f"  ── {label}")
        try:
            record = mgr.query(domain, rtype)
            log    = mgr._log[-1]
            _print_result(record, log)
        except (InvalidDomainError, InvalidRecordTypeError) as exc:
            print(f"  ⚠  {exc}\n")

    mgr.show_cache()
    mgr.show_log()
    mgr.show_stats()


def interactive_loop(mgr: ResolverManager) -> None:
    print("=" * 62)
    print("  Basic DNS Resolver  –  Interactive Console")
    print("=" * 62)
    print(HELP_TEXT)

    while True:
        try:
            raw = input("dns> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye.")
            break

        if not raw:
            continue

        parts = raw.split()
        cmd   = parts[0].lower()

        if cmd in ("quit", "exit", "q"):
            print("  Goodbye.")
            break

        elif cmd == "help":
            print(HELP_TEXT)

        elif cmd == "demo":
            run_demo(mgr)

        elif cmd == "resolve":
            if len(parts) < 2:
                print("  Usage: resolve <domain> [type]\n")
                continue
            domain = parts[1]
            rtype  = parts[2] if len(parts) > 2 else "A"
            try:
                record = mgr.query(domain, rtype)
                log    = mgr._log[-1]
                _print_result(record, log)
            except (InvalidDomainError, InvalidRecordTypeError, DNSError) as exc:
                print(f"  ⚠  {exc}\n")

        elif cmd == "cache":
            mgr.show_cache()

        elif cmd == "log":
            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            mgr.show_log(n)

        elif cmd == "stats":
            mgr.show_stats()

        elif cmd == "purge":
            mgr.purge_expired()

        elif cmd == "clear":
            mgr.clear_cache()

        elif cmd == "invalidate":
            if len(parts) < 2:
                print("  Usage: invalidate <domain> [type]\n")
                continue
            domain = parts[1]
            rtype  = parts[2] if len(parts) > 2 else None
            try:
                mgr.invalidate(domain, rtype)
            except (KeyError, InvalidRecordTypeError) as exc:
                print(f"  ⚠  {exc}\n")

        else:
            print(f"  Unknown command: '{cmd}'. Type 'help' for options.\n")


# ══════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    manager = ResolverManager()

    import sys
    if "--demo" in sys.argv:
        run_demo(manager)
    else:
        # Auto-run demo first, then enter interactive mode
        run_demo(manager)
        print("\n  Entering interactive mode (type 'help' for commands).\n")
        interactive_loop(manager)