"""
network_latency_tester.py
=========================
A modular, OOP-based network latency testing tool.
Measures ping latency using raw ICMP sockets (Unix/macOS) with a
graceful fallback to the system `ping` command on all platforms.
"""

from __future__ import annotations

import os
import re
import select
import socket
import struct
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean, stdev
from typing import List, Optional


# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class PingRequest:
    """Encapsulates the parameters for a single ICMP echo request."""
    target_host: str
    packet_size: int = 56          # bytes of payload (classic default)
    timeout: float = 2.0           # seconds to wait for a reply
    sequence_number: int = 0

    def __post_init__(self) -> None:
        if not self.target_host:
            raise ValueError("target_host must not be empty.")
        if not (1 <= self.packet_size <= 65_507):
            raise ValueError("packet_size must be between 1 and 65 507 bytes.")
        if self.timeout <= 0:
            raise ValueError("timeout must be a positive number.")
        if self.sequence_number < 0:
            raise ValueError("sequence_number must be non-negative.")


@dataclass
class PingResult:
    """Stores the outcome of a single ping attempt."""
    sequence_number: int
    status: str                          # "success" | "timeout" | "error"
    response_time: Optional[float]       # milliseconds, None on failure
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: str = ""

    @property
    def success(self) -> bool:
        return self.status == "success"

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        if self.success:
            return (f"[{ts}] seq={self.sequence_number:>3}  "
                    f"time={self.response_time:7.3f} ms  ✓")
        return (f"[{ts}] seq={self.sequence_number:>3}  "
                f"{self.status.upper()}"
                + (f" – {self.error_message}" if self.error_message else ""))


# ─────────────────────────────────────────────────────────────
# ICMP helpers (raw-socket path)
# ─────────────────────────────────────────────────────────────

def _checksum(data: bytes) -> int:
    """Internet checksum (RFC 1071)."""
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return ~total & 0xFFFF


def _build_icmp_packet(pid: int, seq: int, payload_size: int) -> bytes:
    """Build an ICMP echo-request packet."""
    header = struct.pack("!BBHHH", 8, 0, 0, pid & 0xFFFF, seq)
    payload = bytes(range(payload_size % 256)) * (payload_size // 256 + 1)
    payload = payload[:payload_size]
    chk = _checksum(header + payload)
    header = struct.pack("!BBHHH", 8, 0, chk, pid & 0xFFFF, seq)
    return header + payload


# ─────────────────────────────────────────────────────────────
# LatencyTester
# ─────────────────────────────────────────────────────────────

class LatencyTester:
    """
    Sends ICMP echo requests and collects PingResult objects.

    Strategy
    --------
    1. Try a raw ICMP socket (requires root/CAP_NET_RAW on Linux).
    2. Fall back to the system `ping` command if raw sockets fail.
    """

    def __init__(self) -> None:
        self._pid = os.getpid()

    # ── public API ──────────────────────────────────────────

    def ping(self, request: PingRequest) -> PingResult:
        """Send a single ping and return a PingResult."""
        try:
            return self._raw_ping(request)
        except PermissionError:
            return self._system_ping(request)
        except OSError as exc:
            return PingResult(
                sequence_number=request.sequence_number,
                status="error",
                response_time=None,
                error_message=str(exc),
            )

    def run_session(
        self,
        request_template: PingRequest,
        count: int,
        interval: float = 0.5,
        progress_cb=None,
    ) -> List[PingResult]:
        """
        Send `count` pings based on *request_template*, returning all results.

        Parameters
        ----------
        progress_cb : callable(result) | None
            Called after each ping so callers can print live output.
        """
        results: List[PingResult] = []
        for i in range(count):
            req = PingRequest(
                target_host=request_template.target_host,
                packet_size=request_template.packet_size,
                timeout=request_template.timeout,
                sequence_number=i + 1,
            )
            result = self.ping(req)
            results.append(result)
            if progress_cb:
                progress_cb(result)
            if i < count - 1:
                time.sleep(interval)
        return results

    # ── raw socket path ─────────────────────────────────────

    def _raw_ping(self, request: PingRequest) -> PingResult:
        try:
            sock = socket.socket(
                socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP
            )
        except PermissionError:
            raise                          # bubble up to trigger fallback
        except OSError as exc:
            raise OSError(f"Cannot create raw socket: {exc}") from exc

        sock.settimeout(request.timeout)
        dest_ip = socket.gethostbyname(request.target_host)
        packet = _build_icmp_packet(self._pid, request.sequence_number,
                                    request.packet_size)
        send_time = time.perf_counter()
        try:
            sock.sendto(packet, (dest_ip, 0))
            deadline = send_time + request.timeout
            while True:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    return PingResult(
                        sequence_number=request.sequence_number,
                        status="timeout",
                        response_time=None,
                    )
                ready = select.select([sock], [], [], remaining)
                if not ready[0]:
                    return PingResult(
                        sequence_number=request.sequence_number,
                        status="timeout",
                        response_time=None,
                    )
                recv_time = time.perf_counter()
                raw_data, _ = sock.recvfrom(1024)
                icmp_header = raw_data[20:28]
                icmp_type, _, _, r_pid, r_seq = struct.unpack(
                    "!BBHHH", icmp_header
                )
                if icmp_type == 0 and r_pid == (self._pid & 0xFFFF):
                    rtt_ms = (recv_time - send_time) * 1000
                    return PingResult(
                        sequence_number=request.sequence_number,
                        status="success",
                        response_time=round(rtt_ms, 3),
                    )
        except socket.timeout:
            return PingResult(
                sequence_number=request.sequence_number,
                status="timeout",
                response_time=None,
            )
        finally:
            sock.close()

    # ── system ping fallback ─────────────────────────────────

    def _system_ping(self, request: PingRequest) -> PingResult:
        """Parse one RTT from the OS `ping` command."""
        import subprocess
        is_win = sys.platform.startswith("win")
        cmd = (
            ["ping", "-n", "1",
             "-w", str(int(request.timeout * 1000)), request.target_host]
            if is_win else
            ["ping", "-c", "1",
             "-W", str(int(request.timeout)), request.target_host]
        )
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=request.timeout + 2
            )
            output = proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            return PingResult(
                sequence_number=request.sequence_number,
                status="timeout",
                response_time=None,
            )
        except FileNotFoundError:
            return PingResult(
                sequence_number=request.sequence_number,
                status="error",
                response_time=None,
                error_message="'ping' command not found on this system.",
            )

        # Extract RTT: works on Linux ("time=1.23 ms") and Windows ("1ms")
        match = re.search(r"[Tt]ime[=<](\d+(?:\.\d+)?)\s*ms", output)
        if match:
            rtt_ms = float(match.group(1))
            return PingResult(
                sequence_number=request.sequence_number,
                status="success",
                response_time=round(rtt_ms, 3),
            )

        # Detect timeout/unreachable
        if any(k in output.lower() for k in
               ("request timeout", "100% packet loss",
                "unreachable", "timed out")):
            return PingResult(
                sequence_number=request.sequence_number,
                status="timeout",
                response_time=None,
            )

        return PingResult(
            sequence_number=request.sequence_number,
            status="error",
            response_time=None,
            error_message="Unexpected ping output.",
        )


# ─────────────────────────────────────────────────────────────
# Statistics helper
# ─────────────────────────────────────────────────────────────

@dataclass
class LatencyStats:
    """Aggregate statistics computed from a list of PingResults."""
    total: int
    received: int
    lost: int
    packet_loss_pct: float
    rtt_min: Optional[float]
    rtt_max: Optional[float]
    rtt_avg: Optional[float]
    rtt_stddev: Optional[float]

    @classmethod
    def from_results(cls, results: List[PingResult]) -> "LatencyStats":
        total = len(results)
        rtts = [r.response_time for r in results if r.success]
        received = len(rtts)
        lost = total - received
        loss_pct = (lost / total * 100) if total else 0.0
        return cls(
            total=total,
            received=received,
            lost=lost,
            packet_loss_pct=round(loss_pct, 1),
            rtt_min=round(min(rtts), 3) if rtts else None,
            rtt_max=round(max(rtts), 3) if rtts else None,
            rtt_avg=round(mean(rtts), 3) if rtts else None,
            rtt_stddev=round(stdev(rtts), 3) if len(rtts) >= 2 else None,
        )


# ─────────────────────────────────────────────────────────────
# TestManager
# ─────────────────────────────────────────────────────────────

class TestSession:
    """A single named test run with its results and stats."""

    def __init__(self, session_id: int, host: str) -> None:
        self.session_id = session_id
        self.host = host
        self.started_at: datetime = datetime.now()
        self.results: List[PingResult] = []
        self.stats: Optional[LatencyStats] = None

    def finalise(self) -> None:
        self.stats = LatencyStats.from_results(self.results)


class TestManager:
    """
    Orchestrates test sessions: builds requests, drives LatencyTester,
    stores sessions, and renders reports.
    """

    def __init__(self) -> None:
        self._tester = LatencyTester()
        self._sessions: List[TestSession] = []
        self._next_id = 1

    # ── public API ──────────────────────────────────────────

    def run(
        self,
        host: str,
        count: int,
        timeout: float,
        packet_size: int = 56,
        interval: float = 0.5,
    ) -> TestSession:
        """Run a full test session and return it."""
        session = TestSession(self._next_id, host)
        self._next_id += 1
        self._sessions.append(session)

        template = PingRequest(
            target_host=host,
            packet_size=packet_size,
            timeout=timeout,
        )

        print(f"\n  Pinging {host}  ·  {count} packets  ·  "
              f"timeout {timeout}s  ·  payload {packet_size}B\n")

        def _on_result(r: PingResult) -> None:
            print(f"  {r}")
            session.results.append(r)

        # run_session appends via callback; we capture here instead
        session.results = []
        self._tester.run_session(
            template, count, interval=interval, progress_cb=_on_result
        )
        # results were appended inside _on_result; avoid double-append
        session.finalise()
        return session

    def display_report(self, session: TestSession) -> None:
        """Print a formatted report for a completed session."""
        s = session.stats
        if s is None:
            print("  No statistics available (session not finalised).")
            return

        width = 54
        bar = "─" * width
        print(f"\n  ┌{bar}┐")
        print(f"  │{'  Latency Report':^{width}}│")
        print(f"  ├{bar}┤")
        print(f"  │  {'Session':<22} #{session.session_id:<{width-25}}│")
        print(f"  │  {'Host':<22} {session.host:<{width-25}}│")
        print(f"  │  {'Started':<22} "
              f"{session.started_at.strftime('%Y-%m-%d %H:%M:%S'):<{width-25}}│")
        print(f"  ├{bar}┤")
        print(f"  │  {'Packets sent':<22} {s.total:<{width-25}}│")
        print(f"  │  {'Received':<22} {s.received:<{width-25}}│")
        print(f"  │  {'Lost':<22} {s.lost:<{width-25}}│")
        loss_str = f"{s.packet_loss_pct}%"
        print(f"  │  {'Packet loss':<22} {loss_str:<{width-25}}│")
        print(f"  ├{bar}┤")
        if s.rtt_avg is not None:
            print(f"  │  {'RTT min':<22} {s.rtt_min} ms{'':<{width-28}}│")
            print(f"  │  {'RTT max':<22} {s.rtt_max} ms{'':<{width-28}}│")
            print(f"  │  {'RTT avg':<22} {s.rtt_avg} ms{'':<{width-28}}│")
            stddev_str = (f"{s.rtt_stddev} ms" if s.rtt_stddev is not None
                          else "N/A")
            print(f"  │  {'RTT std dev':<22} {stddev_str:<{width-25}}│")
        else:
            print(f"  │  {'RTT stats':<22} {'N/A (all packets lost)':<{width-25}}│")
        print(f"  └{bar}┘\n")

    def list_sessions(self) -> None:
        """Print a summary table of all stored sessions."""
        if not self._sessions:
            print("  No sessions recorded yet.")
            return
        print(f"\n  {'ID':>3}  {'Host':<30}  {'Sent':>5}  "
              f"{'Loss':>6}  {'Avg RTT':>9}")
        print("  " + "─" * 60)
        for sess in self._sessions:
            if sess.stats:
                s = sess.stats
                avg = f"{s.rtt_avg} ms" if s.rtt_avg is not None else "N/A"
                print(f"  {sess.session_id:>3}  {sess.host:<30}  "
                      f"{s.total:>5}  {s.packet_loss_pct:>5}%  {avg:>9}")
        print()


# ─────────────────────────────────────────────────────────────
# Input helpers
# ─────────────────────────────────────────────────────────────

def _prompt(msg: str, default=None, cast=str, validator=None):
    """Generic prompt with optional default and validation."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"  {msg}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            value = cast(raw)
        except (ValueError, TypeError):
            print(f"  ✗ Invalid input. Expected {cast.__name__}.")
            continue
        if validator and not validator(value):
            print(f"  ✗ Value out of allowed range.")
            continue
        return value


def _resolve_host(host: str) -> Optional[str]:
    """Return the resolved IP or None on failure."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


# ─────────────────────────────────────────────────────────────
# Main CLI
# ─────────────────────────────────────────────────────────────

BANNER = r"""
  ╔══════════════════════════════════════════════════╗
  ║         Network Latency Tester  v1.0             ║
  ╚══════════════════════════════════════════════════╝
"""

MENU = """
  ┌─ Menu ──────────────────────────┐
  │  1  Run a new ping test         │
  │  2  View all session summaries  │
  │  3  Re-display last report      │
  │  4  Exit                        │
  └─────────────────────────────────┘
"""


def main() -> None:
    print(BANNER)
    manager = TestManager()
    last_session: Optional[TestSession] = None

    while True:
        print(MENU)
        choice = input("  Choice: ").strip()

        if choice == "1":
            # ── gather inputs ──────────────────────────
            print()
            host = _prompt("Target host (IP or hostname)", default="8.8.8.8")
            ip = _resolve_host(host)
            if ip is None:
                print(f"  ✗ Cannot resolve '{host}'. Check the hostname.\n")
                continue
            if ip != host:
                print(f"  ✓ Resolved to {ip}")

            count = _prompt(
                "Number of pings", default=5, cast=int,
                validator=lambda v: 1 <= v <= 1000
            )
            timeout = _prompt(
                "Timeout per ping (seconds)", default=2.0, cast=float,
                validator=lambda v: 0.1 <= v <= 30.0
            )
            pkt_size = _prompt(
                "Payload size (bytes)", default=56, cast=int,
                validator=lambda v: 1 <= v <= 65_507
            )
            interval = _prompt(
                "Interval between pings (seconds)", default=0.5, cast=float,
                validator=lambda v: 0.0 <= v <= 60.0
            )

            # ── run ────────────────────────────────────
            try:
                last_session = manager.run(
                    host=host,
                    count=count,
                    timeout=timeout,
                    packet_size=pkt_size,
                    interval=interval,
                )
                manager.display_report(last_session)
            except KeyboardInterrupt:
                print("\n  ⚡ Interrupted by user.\n")
            except Exception as exc:
                print(f"\n  ✗ Unexpected error: {exc}\n")

        elif choice == "2":
            manager.list_sessions()

        elif choice == "3":
            if last_session:
                manager.display_report(last_session)
            else:
                print("  No test has been run yet.\n")

        elif choice == "4":
            print("  Goodbye!\n")
            break

        else:
            print("  ✗ Unknown option. Please enter 1–4.\n")


if __name__ == "__main__":
    main()