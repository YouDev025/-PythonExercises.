"""
Local Port Scanner
==================
A modular, OOP-based tool for scanning ports on the local machine
(or any reachable host) using Python's socket library.

Classes
-------
ScanResult      – Immutable result record for a single port probe.
PortScanner     – Low-level socket probing; scans one or many ports.
ScannerManager  – Orchestrates scans, stores history, drives the CLI.
"""

from __future__ import annotations

import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_HOST    = "127.0.0.1"
DEFAULT_TIMEOUT = 0.5          # seconds per port probe
MAX_WORKERS     = 200          # concurrent threads
PORT_MIN        = 1
PORT_MAX        = 65535

# Well-known service names (best-effort; shown alongside open ports)
KNOWN_SERVICES: dict[int, str] = {
    21: "FTP",       22: "SSH",       23: "Telnet",    25: "SMTP",
    53: "DNS",       80: "HTTP",      110: "POP3",     119: "NNTP",
    123: "NTP",      143: "IMAP",     194: "IRC",      443: "HTTPS",
    445: "SMB",      465: "SMTPS",    587: "SMTP/MSA", 631: "IPP",
    993: "IMAPS",    995: "POP3S",   1433: "MSSQL",   1521: "Oracle",
    2049: "NFS",    3000: "Dev/HTTP",3306: "MySQL",   3389: "RDP",
    5000: "Dev/Flask",5432: "PostgreSQL",5900: "VNC", 6379: "Redis",
    6443: "K8s API", 8080: "HTTP-Alt",8443: "HTTPS-Alt",
    8888: "Jupyter", 9000: "PHP-FPM", 9200: "Elasticsearch",
    9300: "ES Cluster",27017: "MongoDB",
}


# ─────────────────────────────────────────────────────────────────────────────
#  ScanResult  – value object
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ScanResult:
    """Immutable record describing the state of one scanned port."""

    port:    int
    is_open: bool
    host:    str
    service: str = field(default="")

    @property
    def status(self) -> str:
        return "OPEN" if self.is_open else "closed"

    def __str__(self) -> str:
        svc = f"  ← {self.service}" if self.service else ""
        return f"  Port {self.port:<6}  {self.status:<7}{svc}"


# ─────────────────────────────────────────────────────────────────────────────
#  PortScanner  – low-level socket probing
# ─────────────────────────────────────────────────────────────────────────────

class PortScanner:
    """
    Probes TCP ports on *target_host* between *start_port* and *end_port*
    (both inclusive).

    All raw network state is private; results are surfaced via
    scan_port() / scan_range() return values only.
    """

    def __init__(
        self,
        target_host: str = DEFAULT_HOST,
        start_port:  int = 1,
        end_port:    int = 1024,
        timeout:     float = DEFAULT_TIMEOUT,
    ) -> None:
        self.__target_host = self._resolve(target_host)
        self.__start_port  = start_port
        self.__end_port    = end_port
        self.__timeout     = timeout

    # ── public properties ────────────────────────────────────────────────────

    @property
    def target_host(self) -> str:
        return self.__target_host

    @property
    def start_port(self) -> int:
        return self.__start_port

    @property
    def end_port(self) -> int:
        return self.__end_port

    @property
    def timeout(self) -> float:
        return self.__timeout

    @property
    def port_count(self) -> int:
        return self.__end_port - self.__start_port + 1

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _resolve(host: str) -> str:
        """Resolve hostname → IP string; raises ValueError on failure."""
        try:
            return socket.gethostbyname(host.strip())
        except socket.gaierror as exc:
            raise ValueError(f"Cannot resolve host '{host}': {exc}") from exc

    def _probe(self, port: int) -> bool:
        """Return True if the TCP port is open, False otherwise."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.__timeout)
            return sock.connect_ex((self.__target_host, port)) == 0

    # ── public API ────────────────────────────────────────────────────────────

    def scan_port(self, port: int) -> ScanResult:
        """Probe a single port and return a ScanResult."""
        is_open = self._probe(port)
        return ScanResult(
            port=port,
            is_open=is_open,
            host=self.__target_host,
            service=KNOWN_SERVICES.get(port, "") if is_open else "",
        )

    def scan_range(
        self,
        progress_cb: "((int, int) -> None) | None" = None,
    ) -> list[ScanResult]:
        """
        Scan all ports in [start_port, end_port] concurrently.

        progress_cb(completed, total) is called after each port finishes
        (from a worker thread — keep it thread-safe / lightweight).
        """
        ports   = range(self.__start_port, self.__end_port + 1)
        total   = len(ports)
        results: list[ScanResult] = []
        done    = 0

        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, total)) as pool:
            future_map = {pool.submit(self.scan_port, p): p for p in ports}
            for future in as_completed(future_map):
                results.append(future.result())
                done += 1
                if progress_cb:
                    progress_cb(done, total)

        # Sort by port number for predictable output
        results.sort(key=lambda r: r.port)
        return results


# ─────────────────────────────────────────────────────────────────────────────
#  ScannerManager  – orchestration + CLI
# ─────────────────────────────────────────────────────────────────────────────

class ScannerManager:
    """
    Manages the interactive scan workflow:
      - collects and validates user input
      - drives PortScanner
      - stores scan history
      - displays results
    """

    def __init__(self) -> None:
        self.__history: list[dict] = []   # list of completed scan summaries

    # ── display helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _divider(char: str = "─", width: int = 60) -> str:
        return char * width

    @staticmethod
    def _progress_bar(done: int, total: int, width: int = 30) -> str:
        filled = int(width * done / total) if total else 0
        bar    = "█" * filled + "░" * (width - filled)
        pct    = int(100 * done / total) if total else 0
        return f"\r  [{bar}] {pct:3d}%  ({done}/{total})"

    def _display_results(
        self,
        results:     list[ScanResult],
        host:        str,
        elapsed:     float,
        start_port:  int,
        end_port:    int,
    ) -> None:
        open_ports = [r for r in results if r.is_open]

        print(f"\n{self._divider('═')}")
        print(f"  Scan complete  ·  Host: {host}")
        print(f"  Ports scanned: {start_port}–{end_port}  "
              f"({end_port - start_port + 1} total)  "
              f"·  Time: {elapsed:.2f}s")
        print(self._divider())

        if not open_ports:
            print("  No open ports found in this range.")
        else:
            print(f"  {len(open_ports)} open port(s) found:\n")
            for r in open_ports:
                print(r)

        print(self._divider('═'))

    # ── input helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _prompt_host() -> str:
        raw = input(f"  Target host [{DEFAULT_HOST}]: ").strip()
        return raw if raw else DEFAULT_HOST

    @staticmethod
    def _prompt_port(label: str, default: int) -> int:
        while True:
            raw = input(f"  {label} [{default}]: ").strip()
            if not raw:
                return default
            if raw.isdigit() and PORT_MIN <= int(raw) <= PORT_MAX:
                return int(raw)
            print(f"  ⚠  Enter a number between {PORT_MIN} and {PORT_MAX}.")

    @staticmethod
    def _prompt_timeout() -> float:
        while True:
            raw = input(f"  Timeout per port in seconds [{DEFAULT_TIMEOUT}]: ").strip()
            if not raw:
                return DEFAULT_TIMEOUT
            try:
                val = float(raw)
                if 0.05 <= val <= 10.0:
                    return val
            except ValueError:
                pass
            print("  ⚠  Enter a value between 0.05 and 10.0.")

    # ── scan workflow ─────────────────────────────────────────────────────────

    def run_scan(self) -> None:
        """Prompt the user, execute a scan, and display results."""
        print(f"\n{self._divider()}")
        print("  Configure scan")
        print(self._divider())

        # ── collect parameters ──
        try:
            host = self._prompt_host()
            # Validate / resolve early so we fail fast
            resolved = socket.gethostbyname(host)
        except socket.gaierror:
            print(f"\n  ❌  Cannot resolve host '{host}'.  Scan aborted.\n")
            return

        start = self._prompt_port("Start port", 1)
        end   = self._prompt_port("End port",   1024)

        if start > end:
            print("  ⚠  Start port must be ≤ end port.  Swapping values.")
            start, end = end, start

        timeout = self._prompt_timeout()

        # ── build scanner ──
        try:
            scanner = PortScanner(
                target_host=host,
                start_port=start,
                end_port=end,
                timeout=timeout,
            )
        except ValueError as exc:
            print(f"\n  ❌  {exc}\n")
            return

        total = scanner.port_count
        print(f"\n  Scanning {resolved} · ports {start}–{end} "
              f"({total} port{'s' if total != 1 else ''}) …\n")

        # Thread-safe progress counter via a mutable container
        state = {"done": 0}

        def on_progress(done: int, _total: int) -> None:
            state["done"] = done
            print(self._progress_bar(done, _total), end="", flush=True)

        t0      = time.perf_counter()
        results = scanner.scan_range(progress_cb=on_progress)
        elapsed = time.perf_counter() - t0

        print()  # newline after progress bar

        self._display_results(results, resolved, elapsed, start, end)

        # Store in history
        self.__history.append({
            "host":        resolved,
            "start":       start,
            "end":         end,
            "scanned_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed":     round(elapsed, 2),
            "open_ports":  [r.port for r in results if r.is_open],
        })

    def show_history(self) -> None:
        """Display a summary of all scans performed this session."""
        print(f"\n{self._divider('═')}")
        print("  Scan history this session")
        print(self._divider())

        if not self.__history:
            print("  (no scans performed yet)")
        else:
            for i, h in enumerate(self.__history, start=1):
                open_str = (
                    ", ".join(str(p) for p in h["open_ports"])
                    if h["open_ports"] else "none"
                )
                print(
                    f"  [{i}] {h['scanned_at']}  {h['host']}"
                    f"  ports {h['start']}–{h['end']}"
                    f"  ({h['elapsed']}s)"
                    f"\n       Open: {open_str}"
                )
        print(self._divider('═'))

    # ── CLI loop ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Main interactive loop."""
        banner = """
╔══════════════════════════════════════════════════════════╗
║           Local Port Scanner  v1.0                       ║
║  Scan TCP ports on localhost or any reachable host.      ║
╚══════════════════════════════════════════════════════════╝"""
        menu = """
  [1]  New scan
  [2]  View scan history
  [q]  Quit
"""
        print(banner)

        while True:
            print(menu)
            try:
                choice = input("  Choose an option: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Goodbye!")
                break

            if choice == "1":
                self.run_scan()
            elif choice == "2":
                self.show_history()
            elif choice in {"q", "quit", "exit"}:
                print("\n  Goodbye!\n")
                break
            else:
                print("\n  ⚠  Unrecognised option.  Enter 1, 2, or q.\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ScannerManager().run()