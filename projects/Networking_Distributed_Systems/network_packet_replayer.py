"""
network_packet_replayer.py
A Python OOP simulation of replaying captured network packets.
"""

import time
import threading
import random
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class Protocol(Enum):
    TCP  = "TCP"
    UDP  = "UDP"
    ICMP = "ICMP"
    HTTP = "HTTP"
    DNS  = "DNS"


class ReplaySpeed(Enum):
    SLOW   = 2.0   # 2× slower
    NORMAL = 1.0   # real-time
    FAST   = 0.25  # 4× faster


class ReplayState(Enum):
    IDLE    = "IDLE"
    RUNNING = "RUNNING"
    PAUSED  = "PAUSED"
    STOPPED = "STOPPED"


# ─────────────────────────────────────────────
# NetworkPacket
# ─────────────────────────────────────────────

@dataclass
class NetworkPacket:
    source_ip:      str
    destination_ip: str
    protocol:       Protocol
    port:           int
    payload:        str
    timestamp:      datetime
    packet_id:      int = field(default_factory=lambda: random.randint(1000, 9999))

    def __post_init__(self):
        self._validate()

    def _validate(self):
        for label, ip in [("source_ip", self.source_ip),
                          ("destination_ip", self.destination_ip)]:
            parts = ip.split(".")
            if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255
                                          for p in parts):
                raise ValueError(f"Invalid IP address for {label}: {ip!r}")
        if not isinstance(self.protocol, Protocol):
            raise TypeError(f"protocol must be a Protocol enum, got {type(self.protocol)}")
        if not (0 <= self.port <= 65535):
            raise ValueError(f"Port must be 0–65535, got {self.port}")
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime object")

    def summary(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        return (f"[{ts}] PKT#{self.packet_id}  "
                f"{self.source_ip}:{self.port} → {self.destination_ip}  "
                f"Protocol={self.protocol.value:<4}  "
                f"Payload={self.payload!r}")


# ─────────────────────────────────────────────
# PacketCapture  – loads / stores packets
# ─────────────────────────────────────────────

class PacketCapture:
    """Loads and stores a collection of NetworkPacket objects."""

    def __init__(self, name: str = "capture"):
        if not name or not isinstance(name, str):
            raise ValueError("Capture name must be a non-empty string.")
        self.name: str = name
        self._packets: list[NetworkPacket] = []

    # ── loading ──────────────────────────────

    def load_from_dataset(self, packets: list[NetworkPacket]) -> None:
        """Load from an existing list of NetworkPacket objects."""
        if not packets:
            raise ValueError("Dataset is empty.")
        if not all(isinstance(p, NetworkPacket) for p in packets):
            raise TypeError("All items must be NetworkPacket instances.")
        self._packets = sorted(packets, key=lambda p: p.timestamp)
        print(f"  ✔  Loaded {len(self._packets)} packets into capture '{self.name}'.")

    def load_simulated(self, count: int = 20) -> None:
        """Generate a realistic simulated packet capture."""
        if count < 1:
            raise ValueError("count must be ≥ 1.")
        print(f"  ⟳  Generating {count} simulated packets …")
        hosts = ["192.168.1.10", "192.168.1.20", "10.0.0.5",
                 "172.16.0.3",  "8.8.8.8",       "1.1.1.1"]
        port_map = {Protocol.TCP: 443, Protocol.UDP: 53,
                    Protocol.HTTP: 80, Protocol.DNS: 53, Protocol.ICMP: 0}
        payloads = [
            "GET /index.html HTTP/1.1", "DNS query: example.com",
            "TLS ClientHello",          "ACK seq=1024",
            "ICMP echo request",        "POST /api/data",
            "UDP datagram",             "SYN packet",
        ]
        base_time = datetime.now()
        packets = []
        for i in range(count):
            proto  = random.choice(list(Protocol))
            src    = random.choice(hosts)
            dst    = random.choice([h for h in hosts if h != src])
            port   = port_map[proto] + random.randint(0, 5)
            delay  = timedelta(milliseconds=random.randint(10, 600))
            ts     = base_time + delay * i
            pkt    = NetworkPacket(
                source_ip=src, destination_ip=dst,
                protocol=proto, port=port,
                payload=random.choice(payloads), timestamp=ts,
            )
            packets.append(pkt)
        self._packets = sorted(packets, key=lambda p: p.timestamp)
        print(f"  ✔  Simulated capture ready — {len(self._packets)} packets.")

    # ── accessors ────────────────────────────

    @property
    def packets(self) -> list[NetworkPacket]:
        return list(self._packets)

    def __len__(self) -> int:
        return len(self._packets)

    def __repr__(self) -> str:
        return f"PacketCapture(name={self.name!r}, packets={len(self._packets)})"


# ─────────────────────────────────────────────
# ReplayController  – start / pause / resume / stop
# ─────────────────────────────────────────────

class ReplayController:
    """Thread-safe state machine for replay control."""

    def __init__(self):
        self._state = ReplayState.IDLE
        self._lock  = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()   # not paused initially

    # ── public commands ──────────────────────

    def start(self) -> bool:
        with self._lock:
            if self._state not in (ReplayState.IDLE, ReplayState.STOPPED):
                print(f"  ✗  Cannot start: already {self._state.value}.")
                return False
            self._state = ReplayState.RUNNING
            self._pause_event.set()
            print("  ▶  Replay STARTED.")
            return True

    def pause(self) -> bool:
        with self._lock:
            if self._state != ReplayState.RUNNING:
                print(f"  ✗  Cannot pause: state is {self._state.value}.")
                return False
            self._state = ReplayState.PAUSED
            self._pause_event.clear()
            print("  ⏸  Replay PAUSED.")
            return True

    def resume(self) -> bool:
        with self._lock:
            if self._state != ReplayState.PAUSED:
                print(f"  ✗  Cannot resume: state is {self._state.value}.")
                return False
            self._state = ReplayState.RUNNING
            self._pause_event.set()
            print("  ▶  Replay RESUMED.")
            return True

    def stop(self) -> bool:
        with self._lock:
            if self._state == ReplayState.STOPPED:
                print("  ✗  Already stopped.")
                return False
            self._state = ReplayState.STOPPED
            self._pause_event.set()   # unblock any waiting thread
            print("  ⏹  Replay STOPPED.")
            return True

    def reset(self) -> None:
        with self._lock:
            self._state = ReplayState.IDLE
            self._pause_event.set()

    # ── queries ──────────────────────────────

    @property
    def state(self) -> ReplayState:
        with self._lock:
            return self._state

    def wait_if_paused(self) -> None:
        """Block caller until not paused (or stopped)."""
        self._pause_event.wait()

    def is_running(self) -> bool:
        return self.state == ReplayState.RUNNING

    def is_stopped(self) -> bool:
        return self.state == ReplayState.STOPPED


# ─────────────────────────────────────────────
# PacketReplayer  – replays packets with timing
# ─────────────────────────────────────────────

class PacketReplayer:
    """Replays packets preserving inter-packet timing."""

    def __init__(self, controller: ReplayController,
                 speed: ReplaySpeed = ReplaySpeed.NORMAL):
        if not isinstance(controller, ReplayController):
            raise TypeError("controller must be a ReplayController.")
        if not isinstance(speed, ReplaySpeed):
            raise TypeError("speed must be a ReplaySpeed enum.")
        self._controller  = controller
        self._speed       = speed
        self._replayed    : list[NetworkPacket] = []
        self._start_wall  : Optional[float]     = None
        self._on_packet   = None   # optional callback

    # ── configuration ────────────────────────

    @property
    def speed(self) -> ReplaySpeed:
        return self._speed

    @speed.setter
    def speed(self, value: ReplaySpeed) -> None:
        if not isinstance(value, ReplaySpeed):
            raise TypeError("speed must be a ReplaySpeed enum.")
        self._speed = value

    def set_packet_callback(self, fn) -> None:
        """Register a callable(NetworkPacket) invoked on each replayed packet."""
        if not callable(fn):
            raise TypeError("Callback must be callable.")
        self._on_packet = fn

    # ── replay ───────────────────────────────

    def replay(self, packets: list[NetworkPacket]) -> None:
        """Replay a list of packets (blocking call)."""
        if not packets:
            raise ValueError("No packets to replay.")

        self._replayed   = []
        self._start_wall = time.time()
        multiplier       = self._speed.value   # pause-time multiplier

        prev_ts: Optional[datetime] = None

        for pkt in packets:
            # ── check for stop ──
            if self._controller.is_stopped():
                print("\n  ⏹  Replay aborted mid-stream.")
                break

            # ── honour pause ──
            self._controller.wait_if_paused()
            if self._controller.is_stopped():
                break

            # ── timing ──
            if prev_ts is not None:
                gap_s = (pkt.timestamp - prev_ts).total_seconds()
                sleep_s = max(0.0, gap_s * multiplier)
                if sleep_s > 0:
                    time.sleep(sleep_s)

            # ── emit packet ──
            self._replayed.append(pkt)
            print(f"  → {pkt.summary()}")
            if self._on_packet:
                self._on_packet(pkt)

            prev_ts = pkt.timestamp

    # ── stats ────────────────────────────────

    @property
    def replayed_count(self) -> int:
        return len(self._replayed)

    @property
    def elapsed_seconds(self) -> float:
        if self._start_wall is None:
            return 0.0
        return time.time() - self._start_wall

    def replayed_packets(self) -> list[NetworkPacket]:
        return list(self._replayed)


# ─────────────────────────────────────────────
# ReplayManager  – orchestrates everything
# ─────────────────────────────────────────────

class ReplayManager:
    """Manages datasets, speed, and high-level replay lifecycle."""

    def __init__(self):
        self._captures  : dict[str, PacketCapture] = {}
        self._active    : Optional[str]             = None
        self._controller = ReplayController()
        self._replayer  : Optional[PacketReplayer]  = None
        self._speed      = ReplaySpeed.NORMAL
        self._thread    : Optional[threading.Thread] = None

    # ── dataset management ───────────────────

    def add_capture(self, capture: PacketCapture) -> None:
        if not isinstance(capture, PacketCapture):
            raise TypeError("capture must be a PacketCapture.")
        self._captures[capture.name] = capture
        print(f"  ✔  Capture '{capture.name}' added to manager "
              f"({len(capture)} packets).")

    def select_capture(self, name: str) -> None:
        if name not in self._captures:
            raise KeyError(f"No capture named {name!r}. "
                           f"Available: {list(self._captures)}")
        self._active = name
        print(f"  ✔  Active capture set to '{name}'.")

    def list_captures(self) -> None:
        if not self._captures:
            print("  (no captures loaded)")
            return
        print("  Loaded captures:")
        for name, cap in self._captures.items():
            marker = " ◀ active" if name == self._active else ""
            print(f"    • {name}  ({len(cap)} packets){marker}")

    # ── speed control ────────────────────────

    def set_speed(self, speed: ReplaySpeed) -> None:
        if not isinstance(speed, ReplaySpeed):
            raise TypeError("speed must be a ReplaySpeed enum.")
        self._speed = speed
        label = {ReplaySpeed.SLOW: "SLOW (0.5×)",
                 ReplaySpeed.NORMAL: "NORMAL (1×)",
                 ReplaySpeed.FAST: "FAST (4×)"}[speed]
        print(f"  ✔  Replay speed set to {label}.")

    # ── lifecycle ────────────────────────────

    def start_replay(self, blocking: bool = True) -> None:
        if self._active is None:
            raise RuntimeError("No capture selected. Call select_capture() first.")

        packets = self._captures[self._active].packets
        if not packets:
            raise RuntimeError("Selected capture has no packets.")

        self._controller.reset()
        self._replayer = PacketReplayer(self._controller, self._speed)

        if not self._controller.start():
            return

        def _run():
            self._replayer.replay(packets)
            if not self._controller.is_stopped():
                self._controller.stop()
            self.print_statistics()

        self._thread = threading.Thread(target=_run, daemon=True, name="ReplayThread")
        self._thread.start()

        if blocking:
            self._thread.join()

    def pause(self)  -> None: self._controller.pause()
    def resume(self) -> None: self._controller.resume()
    def stop(self)   -> None:
        self._controller.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    # ── statistics ───────────────────────────

    def print_statistics(self) -> None:
        print("\n" + "═" * 58)
        print("  REPLAY STATISTICS")
        print("═" * 58)
        if self._replayer is None:
            print("  No replay has been run yet.")
        else:
            total    = len(self._captures.get(self._active or "", []))
            replayed = self._replayer.replayed_count
            elapsed  = self._replayer.elapsed_seconds
            pkts     = self._replayer.replayed_packets()

            proto_counts: dict[str, int] = {}
            for p in pkts:
                proto_counts[p.protocol.value] = \
                    proto_counts.get(p.protocol.value, 0) + 1

            print(f"  Capture        : {self._active}")
            print(f"  Speed          : {self._speed.name}")
            print(f"  Total packets  : {total}")
            print(f"  Replayed       : {replayed}")
            print(f"  Elapsed time   : {elapsed:.2f}s")
            if pkts:
                span = (pkts[-1].timestamp - pkts[0].timestamp).total_seconds()
                print(f"  Traffic span   : {span:.3f}s")
                rate = replayed / elapsed if elapsed > 0 else 0
                print(f"  Replay rate    : {rate:.1f} pkt/s")
            print("  Protocol breakdown:")
            for proto, cnt in sorted(proto_counts.items()):
                bar = "█" * cnt
                print(f"    {proto:<6} {cnt:>3}  {bar}")
        print("═" * 58)


# ─────────────────────────────────────────────
# Demo / main
# ─────────────────────────────────────────────

def _demo_interactive() -> None:
    """Demonstrate pause / resume / stop on a background thread."""
    print("\n" + "─" * 58)
    print("  INTERACTIVE CONTROL DEMO  (background replay)")
    print("─" * 58)

    cap = PacketCapture("interactive_demo")
    cap.load_simulated(count=30)

    mgr = ReplayManager()
    mgr.add_capture(cap)
    mgr.select_capture("interactive_demo")
    mgr.set_speed(ReplaySpeed.FAST)

    # start in background
    mgr.start_replay(blocking=False)
    time.sleep(0.4)

    mgr.pause()
    print("  … (paused for 0.8 s) …")
    time.sleep(0.8)

    mgr.resume()
    time.sleep(0.5)

    mgr.stop()


def main() -> None:
    separator = "═" * 58

    print(separator)
    print("       NETWORK PACKET REPLAYER  –  Demo")
    print(separator)

    # ── 1. Simulated capture, normal speed ──────────────────
    print("\n[1/3]  Normal-speed replay of simulated capture")
    print("─" * 58)

    cap_normal = PacketCapture("capture_normal")
    cap_normal.load_simulated(count=8)

    mgr = ReplayManager()
    mgr.add_capture(cap_normal)
    mgr.select_capture("capture_normal")
    mgr.set_speed(ReplaySpeed.NORMAL)
    mgr.list_captures()
    print()
    mgr.start_replay(blocking=True)

    # ── 2. Fast-speed replay ─────────────────────────────────
    print("\n[2/3]  Fast-speed replay (4×)")
    print("─" * 58)

    cap_fast = PacketCapture("capture_fast")
    cap_fast.load_simulated(count=10)

    mgr.add_capture(cap_fast)
    mgr.select_capture("capture_fast")
    mgr.set_speed(ReplaySpeed.FAST)
    print()
    mgr.start_replay(blocking=True)

    # ── 3. Manual dataset + interactive pause/resume/stop ───
    print("\n[3/3]  Manual dataset  +  pause / resume / stop demo")
    print("─" * 58)

    base_ts = datetime.now()
    manual_packets = [
        NetworkPacket("10.0.0.1", "10.0.0.2", Protocol.TCP,  443,
                      "TLS handshake",    base_ts + timedelta(milliseconds=0)),
        NetworkPacket("10.0.0.2", "10.0.0.1", Protocol.TCP,  443,
                      "TLS ServerHello",  base_ts + timedelta(milliseconds=120)),
        NetworkPacket("10.0.0.1", "8.8.8.8",  Protocol.DNS,   53,
                      "DNS query",        base_ts + timedelta(milliseconds=250)),
        NetworkPacket("8.8.8.8",  "10.0.0.1", Protocol.DNS,   53,
                      "DNS response",     base_ts + timedelta(milliseconds=310)),
        NetworkPacket("10.0.0.1", "10.0.0.5", Protocol.HTTP,  80,
                      "GET /api/health",  base_ts + timedelta(milliseconds=400)),
        NetworkPacket("10.0.0.5", "10.0.0.1", Protocol.HTTP,  80,
                      "200 OK",           base_ts + timedelta(milliseconds=520)),
        NetworkPacket("10.0.0.1", "10.0.0.2", Protocol.ICMP,   0,
                      "ping",             base_ts + timedelta(milliseconds=650)),
        NetworkPacket("10.0.0.2", "10.0.0.1", Protocol.ICMP,   0,
                      "pong",             base_ts + timedelta(milliseconds=700)),
    ]

    cap_manual = PacketCapture("manual_capture")
    cap_manual.load_from_dataset(manual_packets)

    mgr.add_capture(cap_manual)
    mgr.select_capture("manual_capture")
    mgr.set_speed(ReplaySpeed.FAST)
    print()
    mgr.start_replay(blocking=True)

    # ── Interactive control demo ─────────────────────────────
    _demo_interactive()

    print("\n" + separator)
    print("  All demos complete.")
    print(separator)


if __name__ == "__main__":
    main()