"""
┌─────────────────────────────────────────────────────────────────────────────┐
│           ARP POISONING EDUCATIONAL LAB SIMULATOR                           │
│           A Hands-On Cybersecurity Learning Environment                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Run      : python arp_poisoning_lab_simulator.py                           │
│  Requires : Python 3.10+  (standard library only)                           │
│  Purpose  : Interactive lab teaching ARP poisoning, MITM, and defenses      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ⚠  LEGAL NOTICE                                                            │
│  This program sends NO real network packets and performs NO actual attacks. │
│  Performing ARP poisoning on networks without written permission is         │
│  illegal under the Computer Fraud and Abuse Act (CFAA) and equivalent      │
│  laws worldwide. This simulator exists solely for education.                │
└─────────────────────────────────────────────────────────────────────────────┘
"""

# ──────────────────────────────────────────────────────────────────────────────
# Imports  (standard library only)
# ──────────────────────────────────────────────────────────────────────────────
import os
import sys
import time
import random
import hashlib
import textwrap
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from copy import deepcopy


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 ── Terminal styling engine
# ══════════════════════════════════════════════════════════════════════════════

class Ansi:
    """ANSI escape codes for terminal colour and formatting."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDER   = "\033[4m"

    BLACK   = "\033[30m";  BLACK_B  = "\033[90m"
    RED     = "\033[31m";  RED_B    = "\033[91m"
    GREEN   = "\033[32m";  GREEN_B  = "\033[92m"
    YELLOW  = "\033[33m";  YELLOW_B = "\033[93m"
    BLUE    = "\033[34m";  BLUE_B   = "\033[94m"
    MAGENTA = "\033[35m";  MAGENTA_B= "\033[95m"
    CYAN    = "\033[36m";  CYAN_B   = "\033[96m"
    WHITE   = "\033[37m";  WHITE_B  = "\033[97m"

    BG_BLACK = "\033[40m";  BG_RED    = "\033[41m"
    BG_GREEN = "\033[42m";  BG_YELLOW = "\033[43m"
    BG_BLUE  = "\033[44m";  BG_MAGENTA= "\033[45m"
    BG_CYAN  = "\033[46m";  BG_WHITE  = "\033[47m"


# Shorthand wrappers
def R(s):  return f"{Ansi.RED_B}{s}{Ansi.RESET}"
def G(s):  return f"{Ansi.GREEN_B}{s}{Ansi.RESET}"
def Y(s):  return f"{Ansi.YELLOW_B}{s}{Ansi.RESET}"
def B(s):  return f"{Ansi.BLUE_B}{s}{Ansi.RESET}"
def C(s):  return f"{Ansi.CYAN_B}{s}{Ansi.RESET}"
def M(s):  return f"{Ansi.MAGENTA_B}{s}{Ansi.RESET}"
def W(s):  return f"{Ansi.WHITE_B}{s}{Ansi.RESET}"
def D(s):  return f"{Ansi.DIM}{s}{Ansi.RESET}"
def BD(s): return f"{Ansi.BOLD}{s}{Ansi.RESET}"
def IT(s): return f"{Ansi.ITALIC}{s}{Ansi.RESET}"

WIDTH = 80


def hr(char: str = "─", colour: str = Ansi.CYAN, width: int = WIDTH) -> str:
    return f"{colour}{'  ' + char * (width - 2)}{Ansi.RESET}"


def banner(title: str, subtitle: str = "", colour: str = Ansi.CYAN_B) -> None:
    """Full-width decorative banner."""
    inner = WIDTH - 4
    print(f"\n{colour}{Ansi.BOLD}┌{'─' * (WIDTH - 2)}┐{Ansi.RESET}")
    t_pad = (inner - len(title)) // 2
    print(f"{colour}{Ansi.BOLD}│{'':>{t_pad}}{title}{'':>{inner - t_pad - len(title)}}  │{Ansi.RESET}")
    if subtitle:
        s_pad = (inner - len(subtitle)) // 2
        print(f"{colour}│{Ansi.DIM}{'':>{s_pad}}{subtitle}{'':>{inner - s_pad - len(subtitle)}}  {colour}│{Ansi.RESET}")
    print(f"{colour}{Ansi.BOLD}└{'─' * (WIDTH - 2)}┘{Ansi.RESET}\n")


def section(title: str, colour: str = Ansi.YELLOW_B) -> None:
    pad = WIDTH - len(title) - 6
    print(f"\n{colour}{Ansi.BOLD}  ╔══ {title} {'═' * max(0, pad)}╗{Ansi.RESET}")


def endsection(colour: str = Ansi.YELLOW_B) -> None:
    print(f"{colour}{Ansi.BOLD}  ╚{'═' * (WIDTH - 4)}╝{Ansi.RESET}")


def info(msg: str)    -> None: print(f"  {C('ℹ')}  {msg}")
def ok(msg: str)      -> None: print(f"  {G('✔')}  {G(msg)}")
def warn(msg: str)    -> None: print(f"  {Y('⚠')}  {Y(msg)}")
def alert(msg: str)   -> None: print(f"  {R('✖')}  {R(Ansi.BOLD + msg + Ansi.RESET)}")
def label(k, v)       -> None: print(f"  {D(k + ':'): <22} {v}")


def wait(prompt: str = "  ↵  Press Enter to continue…") -> None:
    input(f"\n{D(prompt)}")


def ts() -> str:
    """Return current timestamp string."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def typewrite(text: str, delay: float = 0.018) -> None:
    """Print text character-by-character for dramatic effect."""
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()


def clear() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 ── Packet types and event log
# ══════════════════════════════════════════════════════════════════════════════

class PktType(Enum):
    """All simulated packet / event types used in this lab."""
    ARP_REQ     = auto()   # Who has <IP>? Tell <IP>
    ARP_REP     = auto()   # <IP> is at <MAC>  (legitimate)
    ARP_POISON  = auto()   # <IP> is at <MAC>  (spoofed/malicious)
    ARP_GRAT    = auto()   # Unsolicited gratuitous ARP (also used for poisoning)
    DATA        = auto()   # Application-layer data frame
    MITM        = auto()   # Data intercepted by MITM
    ALERT       = auto()   # IDS/detection event
    FORWARD     = auto()   # Attacker re-forwarding packet


@dataclass
class Packet:
    """
    Represents one simulated network packet.

    In a real network this would be a binary Ethernet frame;
    here it's a Python object carrying the same logical fields.
    """
    ptype   : PktType
    src_ip  : str
    dst_ip  : str
    src_mac : str
    dst_mac : str
    payload : str       = ""
    spoofed : bool      = False
    note    : str       = ""
    created : str       = field(default_factory=ts)

    def colour(self) -> str:
        mapping = {
            PktType.ARP_REQ    : Ansi.BLUE_B,
            PktType.ARP_REP    : Ansi.GREEN_B,
            PktType.ARP_POISON : Ansi.RED_B,
            PktType.ARP_GRAT   : Ansi.RED,
            PktType.DATA       : Ansi.WHITE_B,
            PktType.MITM       : Ansi.MAGENTA_B,
            PktType.ALERT      : Ansi.YELLOW_B,
            PktType.FORWARD    : Ansi.CYAN_B,
        }
        return mapping.get(self.ptype, Ansi.WHITE)

    def short_type(self) -> str:
        return self.ptype.name.replace("_", " ")

    def __str__(self) -> str:
        spf = R(" ⚠ SPOOFED") if self.spoofed else ""
        return (f"{self.colour()}{self.short_type():<12}{Ansi.RESET}{spf}  "
                f"{self.src_ip}({self.src_mac[-5:]:>5}) → "
                f"{self.dst_ip}({self.dst_mac[-5:]:>5})  {D(self.payload[:48])}")


@dataclass
class LogEntry:
    """One entry in the lab event journal."""
    timestamp : str
    actor     : str
    event     : str
    detail    : str
    severity  : str  = "INFO"   # INFO | WARN | ATTACK | DEFENSE | DETECT


class EventLog:
    """
    Append-only event journal for the simulation session.
    Think of it as a combined syslog + IDS alert feed.
    """

    def __init__(self):
        self._entries: list[LogEntry] = []

    def add(self, actor: str, event: str, detail: str = "", severity: str = "INFO") -> None:
        self._entries.append(LogEntry(ts(), actor, event, detail, severity))

    def print_all(self, filter_severity: Optional[str] = None) -> None:
        section("Event Journal")
        colours = {
            "INFO"   : Ansi.CYAN,
            "WARN"   : Ansi.YELLOW_B,
            "ATTACK" : Ansi.RED_B,
            "DEFENSE": Ansi.GREEN_B,
            "DETECT" : Ansi.MAGENTA_B,
        }
        printed = 0
        for e in self._entries:
            if filter_severity and e.severity != filter_severity:
                continue
            col = colours.get(e.severity, Ansi.WHITE)
            sev = f"{col}{e.severity:<7}{Ansi.RESET}"
            print(f"  {D(e.timestamp)}  {sev}  {BD(e.actor):<12}  {e.event:<28}  {D(e.detail)}")
            printed += 1
        if not printed:
            print(f"  {D('(no matching entries)')}")
        endsection()

    def count_attacks(self) -> int:
        return sum(1 for e in self._entries if e.severity == "ATTACK")

    def count_detections(self) -> int:
        return sum(1 for e in self._entries if e.severity == "DETECT")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 ── Network device models
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ARPEntry:
    """
    A single row in an ARP cache.

    Fields mirror the Linux arp / ip neigh output:
      ip         : IP address
      mac        : Ethernet MAC address
      entry_type : 'dynamic' | 'static' | 'incomplete'
      ttl        : simulated time-to-live in seconds (cosmetic)
    """
    ip         : str
    mac        : str
    entry_type : str = "dynamic"
    ttl        : int = field(default_factory=lambda: random.randint(120, 1200))

    def is_static(self) -> bool:
        return self.entry_type == "static"


class ARPTable:
    """
    A device's ARP cache — maps IP addresses to MAC addresses.

    Key behaviours simulated here:
    • Dynamic entries can be overwritten (the root cause of ARP poisoning).
    • Static entries are pinned and resist overwriting.
    • The table fires a callback when a poisoning attempt is detected.
    """

    def __init__(self, owner_name: str, ids_enabled: bool = False):
        self._table       : dict[str, ARPEntry] = {}
        self.owner        : str  = owner_name
        self.ids_enabled  : bool = ids_enabled
        self.alerts       : list[str] = []
        # Callback invoked when a spoof is detected: fn(ip, old_mac, new_mac)
        self.on_detect    = None

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def set(self, ip: str, mac: str, entry_type: str = "dynamic") -> tuple[bool, str]:
        """
        Insert or update an ARP entry.

        Returns (accepted: bool, reason: str).
        Dynamic entries can overwrite other dynamic entries freely.
        Static entries block all overwrites.
        IDS mode triggers an alert when a MAC changes for a known IP.
        """
        existing = self._table.get(ip)

        # Defend: static entries are immutable
        if existing and existing.is_static():
            return False, f"BLOCKED — static entry for {ip} cannot be overwritten"

        # IDS: detect MAC change for a known IP
        if existing and existing.mac != mac and self.ids_enabled:
            alert_msg = (f"MAC CHANGE DETECTED  {ip}: "
                         f"{existing.mac} → {mac}")
            self.alerts.append(alert_msg)
            if self.on_detect:
                self.on_detect(ip, existing.mac, mac)

        self._table[ip] = ARPEntry(ip=ip, mac=mac, entry_type=entry_type)
        return True, "OK"

    def get(self, ip: str) -> Optional[ARPEntry]:
        return self._table.get(ip)

    def mac_for(self, ip: str) -> Optional[str]:
        entry = self._table.get(ip)
        return entry.mac if entry else None

    def pin_static(self, ip: str, mac: str) -> None:
        """Force-set a static (immutable) entry."""
        self._table[ip] = ARPEntry(ip=ip, mac=mac, entry_type="static")

    def remove(self, ip: str) -> None:
        self._table.pop(ip, None)

    def snapshot(self) -> dict[str, ARPEntry]:
        return deepcopy(self._table)

    def all_entries(self) -> list[ARPEntry]:
        return list(self._table.values())

    # ── Display ──────────────────────────────────────────────────────────────

    def display(self, highlight_ip: Optional[str] = None) -> None:
        """Render the ARP table as a formatted text table."""
        if not self._table:
            print(f"    {D('(empty — no entries)')}")
            return
        print(f"    {'IP Address':<20}{'MAC Address':<22}{'Type':<11}{'TTL':>6}")
        print(f"    {'─'*20}{'─'*22}{'─'*11}{'─'*6}")
        for ip, entry in sorted(self._table.items()):
            type_col = G(f"{'STATIC':<11}") if entry.is_static() else D(f"{'dynamic':<11}")
            ip_col   = Y(f"{ip:<20}") if ip == highlight_ip else f"{ip:<20}"
            mac_col  = entry.mac

            # Highlight poisoned entries (set from outside by comparing to real MAC)
            if getattr(entry, "_poisoned", False):
                mac_col = R(f"{entry.mac:<22}") + R(" ← POISONED!")
            else:
                mac_col = f"{mac_col:<22}"

            ttl_str = D(str(entry.ttl))
            print(f"    {ip_col}{mac_col}{type_col}{ttl_str:>6}")


class NetworkDevice:
    """
    Represents any networked host.

    Attributes that mirror a real machine:
      name      : hostname
      ip        : IPv4 address
      mac       : 48-bit Ethernet MAC address
      arp_cache : this device's ARP table
      inbox     : received (simulated) packets this session
      role      : victim | gateway | attacker | server
    """

    ICONS = {
        "victim"  : "💻",
        "gateway" : "🌐",
        "attacker": "👾",
        "server"  : "🖧",
    }

    def __init__(self, name: str, ip: str, mac: str,
                 role: str = "generic", ids_enabled: bool = False):
        self.name        = name
        self.ip          = ip
        self.mac         = mac
        self.role        = role
        self.arp_cache   = ARPTable(owner_name=name, ids_enabled=ids_enabled)
        self.inbox       : list[Packet] = []
        self.sent        : list[Packet] = []

    @property
    def icon(self) -> str:
        return self.ICONS.get(self.role, "🔲")

    def receive(self, pkt: Packet) -> None:
        """Accept a simulated packet into this device's inbox."""
        self.inbox.append(pkt)

    def send_packet(self, pkt: Packet) -> None:
        """Record a packet as sent by this device."""
        self.sent.append(pkt)

    def display_header(self) -> None:
        print(f"\n  {self.icon}  {BD(self.name)}")
        label("IP",   C(self.ip))
        label("MAC",  Y(self.mac))
        label("Role", self.role.upper())

    def __repr__(self) -> str:
        return f"<{self.role.upper()} {self.name} {self.ip}/{self.mac}>"


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 ── Simulated network bus and ARP protocol engine
# ══════════════════════════════════════════════════════════════════════════════

class SimBus:
    """
    The simulated Layer-2 broadcast domain (Ethernet segment / virtual switch).

    In the real world a switch would forward frames based on its MAC table.
    Here we simply route packets between named device objects and maintain a
    Wireshark-style packet capture log.
    """

    def __init__(self):
        self._devices  : dict[str, NetworkDevice] = {}
        self.capture   : list[Packet] = []

    def attach(self, *devices: NetworkDevice) -> None:
        for dev in devices:
            self._devices[dev.name] = dev

    def device_by_ip(self, ip: str) -> Optional[NetworkDevice]:
        for d in self._devices.values():
            if d.ip == ip:
                return d
        return None

    def unicast(self, pkt: Packet, to_name: str) -> None:
        """Deliver a packet to one named device."""
        self.capture.append(pkt)
        target = self._devices.get(to_name)
        if target:
            target.receive(pkt)

    def broadcast(self, pkt: Packet, from_name: str) -> None:
        """Deliver to all devices except the sender (like a broadcast frame)."""
        self.capture.append(pkt)
        for name, dev in self._devices.items():
            if name != from_name:
                dev.receive(pkt)

    def print_capture(self, last_n: int = 0, title: str = "Packet Capture") -> None:
        """Print captured packets like a simplified Wireshark view."""
        section(title)
        entries = self.capture[-last_n:] if last_n else self.capture
        if not entries:
            print(f"    {D('(no packets captured yet)')}")
            endsection()
            return
        print(f"  {'#':<4} {'Time':<13} {'Type':<14} {'From':<24} {'To':<24} {'Payload'}")
        print(f"  {'─'*4} {'─'*13} {'─'*14} {'─'*24} {'─'*24} {'─'*22}")
        for i, pkt in enumerate(entries, 1):
            col  = pkt.colour()
            spf  = R("⚠") if pkt.spoofed else " "
            src  = f"{pkt.src_ip}({pkt.src_mac[-5:]})"
            dst  = f"{pkt.dst_ip}({pkt.dst_mac[-5:]})"
            pay  = pkt.payload[:22] + "…" if len(pkt.payload) > 22 else pkt.payload
            print(f"  {D(str(i)):<4} {D(pkt.created):<13} "
                  f"{col}{pkt.short_type():<14}{Ansi.RESET}{spf} "
                  f"{src:<24} {dst:<24} {D(pay)}")
        endsection()


class ARPProtocol:
    """
    Implements the ARP protocol state machine on top of SimBus.

    Covers:
    ├── Normal ARP: request → reply → cache update
    ├── ARP poisoning: unsolicited fake reply → cache corruption
    └── Gratuitous ARP: self-announcement (legitimate and malicious uses)

    No real packets are crafted or sent at any point.
    """

    def __init__(self, bus: SimBus, event_log: EventLog):
        self.bus = bus
        self.log = event_log

    # ── Normal ARP ────────────────────────────────────────────────────────────

    def request(self, requester: NetworkDevice, target_ip: str) -> Packet:
        """Broadcast an ARP request: 'Who has <target_ip>? Tell <requester.ip>'"""
        pkt = Packet(
            ptype   = PktType.ARP_REQ,
            src_ip  = requester.ip,
            dst_ip  = target_ip,
            src_mac = requester.mac,
            dst_mac = "FF:FF:FF:FF:FF:FF",
            payload = f"Who has {target_ip}? Tell {requester.ip}",
        )
        self.bus.broadcast(pkt, from_name=requester.name)
        requester.send_packet(pkt)
        self.log.add(requester.name, "ARP REQUEST",
                     f"broadcast: who has {target_ip}?")
        return pkt

    def reply(self, responder: NetworkDevice, requester: NetworkDevice) -> Packet:
        """Send a legitimate ARP reply: '<responder.ip> is at <responder.mac>'"""
        pkt = Packet(
            ptype   = PktType.ARP_REP,
            src_ip  = responder.ip,
            dst_ip  = requester.ip,
            src_mac = responder.mac,
            dst_mac = requester.mac,
            payload = f"{responder.ip} is at {responder.mac}",
        )
        self.bus.unicast(pkt, to_name=requester.name)
        responder.send_packet(pkt)
        # Requester learns from the reply
        accepted, reason = requester.arp_cache.set(responder.ip, responder.mac)
        self.log.add(responder.name, "ARP REPLY",
                     f"→ {requester.name}: {responder.ip} is at {responder.mac}")
        if accepted:
            self.log.add(requester.name, "ARP CACHE UPDATE",
                         f"learned {responder.ip} → {responder.mac}")
        return pkt

    def resolve(self, requester: NetworkDevice, target_ip: str) -> Optional[str]:
        """
        Full ARP resolution cycle: check cache → request → reply → cache.
        Returns the resolved MAC address.
        """
        cached = requester.arp_cache.mac_for(target_ip)
        if cached:
            self.log.add(requester.name, "ARP CACHE HIT",
                         f"{target_ip} → {cached} (from cache)")
            return cached

        self.request(requester, target_ip)
        target = self.bus.device_by_ip(target_ip)
        if not target:
            self.log.add(requester.name, "ARP FAILURE",
                         f"no device answers for {target_ip}", "WARN")
            return None

        self.reply(target, requester)
        return requester.arp_cache.mac_for(target_ip)

    def gratuitous(self, sender: NetworkDevice) -> Packet:
        """
        Send a gratuitous ARP — a self-announcement broadcast.
        Legitimate uses: IP conflict detection, NIC failover.
        Malicious use: poisoning neighbour caches without any request.
        """
        pkt = Packet(
            ptype   = PktType.ARP_GRAT,
            src_ip  = sender.ip,
            dst_ip  = sender.ip,
            src_mac = sender.mac,
            dst_mac = "FF:FF:FF:FF:FF:FF",
            payload = f"[GARP] {sender.ip} is at {sender.mac}",
        )
        self.bus.broadcast(pkt, from_name=sender.name)
        sender.send_packet(pkt)
        self.log.add(sender.name, "GRATUITOUS ARP",
                     f"broadcast: {sender.ip} is at {sender.mac}")
        return pkt

    # ── Poisoning ─────────────────────────────────────────────────────────────

    def poison(
        self,
        attacker      : NetworkDevice,
        victim        : NetworkDevice,
        impersonate_ip: str,
    ) -> Packet:
        """
        Craft and deliver a spoofed ARP reply to the victim.

        The attacker claims that <impersonate_ip> lives at its own MAC.
        If the victim accepts this (dynamic entry), its ARP cache is poisoned
        and future frames to <impersonate_ip> will be sent to the attacker.

        Returns the spoofed packet.
        """
        pkt = Packet(
            ptype   = PktType.ARP_POISON,
            src_ip  = impersonate_ip,       # LYING — attacker claims this IP
            dst_ip  = victim.ip,
            src_mac = attacker.mac,         # attacker's real MAC
            dst_mac = victim.mac,
            payload = f"[FAKE] {impersonate_ip} is at {attacker.mac}",
            spoofed = True,
            note    = f"sent by {attacker.name}",
        )
        self.bus.unicast(pkt, to_name=victim.name)
        attacker.send_packet(pkt)

        # Victim processes the reply
        accepted, reason = victim.arp_cache.set(impersonate_ip, attacker.mac)

        self.log.add(
            attacker.name, "ARP POISON",
            f"→ {victim.name}: claim {impersonate_ip} = {attacker.mac}",
            "ATTACK",
        )
        if accepted:
            self.log.add(
                victim.name, "CACHE POISONED",
                f"{impersonate_ip} now wrongly maps to {attacker.mac}",
                "ATTACK",
            )
        else:
            self.log.add(
                victim.name, "POISON BLOCKED",
                f"static entry for {impersonate_ip} rejected spoof",
                "DEFENSE",
            )

        return pkt

    # ── Data transfer ─────────────────────────────────────────────────────────

    def send_data(
        self,
        sender   : NetworkDevice,
        dst_ip   : str,
        payload  : str,
        attacker : Optional[NetworkDevice] = None,
    ) -> Packet:
        """
        Simulate an application-layer data frame from sender toward dst_ip.

        If the sender's ARP cache has been poisoned the frame physically
        travels to the attacker, who can read it before forwarding.
        """
        dst_mac = sender.arp_cache.mac_for(dst_ip)
        if not dst_mac:
            dst_mac = "??"
            self.log.add(sender.name, "NO ROUTE",
                         f"ARP cache has no entry for {dst_ip}", "WARN")

        real_dst = self.bus.device_by_ip(dst_ip)
        intercepted = (
            attacker is not None
            and dst_mac == attacker.mac
            and real_dst is not None
            and real_dst.mac != attacker.mac
        )

        ptype = PktType.MITM if intercepted else PktType.DATA
        pkt   = Packet(
            ptype   = ptype,
            src_ip  = sender.ip,
            dst_ip  = dst_ip,
            src_mac = sender.mac,
            dst_mac = dst_mac,
            payload = payload,
            spoofed = intercepted,
        )

        if intercepted and attacker and real_dst:
            self.bus.unicast(pkt, to_name=attacker.name)
            sender.send_packet(pkt)

            self.log.add(attacker.name, "INTERCEPT",
                         f"captured from {sender.name}: \"{payload[:50]}\"",
                         "ATTACK")

            # Transparent relay — attacker forwards to real destination
            fwd = Packet(
                ptype   = PktType.FORWARD,
                src_ip  = sender.ip,
                dst_ip  = dst_ip,
                src_mac = attacker.mac,
                dst_mac = real_dst.mac,
                payload = payload,
                note    = "forwarded by attacker",
            )
            self.bus.unicast(fwd, to_name=real_dst.name)
            self.log.add(attacker.name, "FORWARD",
                         f"relayed to {real_dst.name} transparently")
        else:
            if real_dst:
                self.bus.unicast(pkt, to_name=real_dst.name)
            sender.send_packet(pkt)
            self.log.add(sender.name, "DATA SENT",
                         f"→ {dst_ip}: \"{payload[:50]}\"")

        return pkt


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5 ── IDS (Intrusion Detection Subsystem)
# ══════════════════════════════════════════════════════════════════════════════

class ARPWatcher:
    """
    Passive ARP monitor — analogous to real tools like arpwatch or XArp.

    Monitors all packets on the bus and raises alerts when:
    ① A MAC address changes for a known IP (cache poisoning indicator)
    ② Unexpected gratuitous ARPs appear
    ③ An IP appears with two different MACs in the same window

    In this simulation the watcher observes the bus capture list directly.
    """

    def __init__(self, bus: SimBus, event_log: EventLog):
        self.bus       = bus
        self.log       = event_log
        self._known    : dict[str, str] = {}   # ip → first-seen MAC
        self._alerts   : list[str] = []

    def scan(self) -> int:
        """
        Scan all captured packets for anomalies.
        Returns the number of alerts raised this scan.
        """
        new_alerts = 0
        for pkt in self.bus.capture:
            if pkt.ptype not in (PktType.ARP_REP, PktType.ARP_POISON,
                                 PktType.ARP_GRAT):
                continue
            ip  = pkt.src_ip
            mac = pkt.src_mac

            if ip in self._known:
                if self._known[ip] != mac:
                    msg = (f"MAC CHANGE — {ip}: "
                           f"{self._known[ip]} → {mac}  (POSSIBLE POISONING)")
                    self._alerts.append(msg)
                    self.log.add("ARPWatcher", "ANOMALY DETECTED", msg, "DETECT")
                    new_alerts += 1
            else:
                self._known[ip] = mac

            if pkt.ptype == PktType.ARP_GRAT and pkt.src_mac not in self._known.values():
                msg = f"Unexpected GARP from unknown MAC {mac} claiming {ip}"
                self._alerts.append(msg)
                self.log.add("ARPWatcher", "GARP ANOMALY", msg, "DETECT")
                new_alerts += 1

        return new_alerts

    def print_report(self) -> None:
        section("ARPWatcher — IDS Report")
        if not self._alerts:
            ok("No anomalies detected — network appears clean.")
        else:
            alert(f"{len(self._alerts)} anomaly(ies) detected!\n")
            for i, a in enumerate(self._alerts, 1):
                print(f"  {R(str(i)+'.')}  {Y(a)}")
        endsection()


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6 ── Lab scenario builder
# ══════════════════════════════════════════════════════════════════════════════

def build_lab() -> tuple:
    """
    Construct the default lab environment.

    Topology
    ─────────
       192.168.10.5  (Alice — victim laptop)
       192.168.10.1  (Router — gateway to Internet)
       192.168.10.77 (Eve — attacker)
       192.168.10.20 (WebServer — internal HTTP server)

    All on the same /24 Ethernet segment (same broadcast domain).
    Returns: (bus, arp_proto, ids, event_log, alice, router, eve, webserver)
    """
    bus   = SimBus()
    elog  = EventLog()
    ids   = ARPWatcher(bus, elog)
    proto = ARPProtocol(bus, elog)

    alice     = NetworkDevice("Alice",     "192.168.10.5",  "A1:IC:E0:00:05:AA", role="victim")
    router    = NetworkDevice("Router",    "192.168.10.1",  "R0:UT:ER:00:01:BB", role="gateway")
    eve       = NetworkDevice("Eve",       "192.168.10.77", "EV:11:77:00:77:CC", role="attacker")
    webserver = NetworkDevice("WebServer", "192.168.10.20", "WE:B5:RV:00:20:DD", role="server")

    bus.attach(alice, router, eve, webserver)
    return bus, proto, ids, elog, alice, router, eve, webserver


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 7 ── ARP table diff renderer
# ══════════════════════════════════════════════════════════════════════════════

def print_arp_diff(
    before  : dict[str, ARPEntry],
    after   : dict[str, ARPEntry],
    device  : NetworkDevice,
    real_map: dict[str, str],       # ip → correct MAC
) -> None:
    """
    Side-by-side diff of an ARP table before and after an attack.
    Highlights poisoned entries in red.
    """
    section(f"ARP Table Diff — {device.name}")
    all_ips = sorted(set(before) | set(after))
    print(f"  {'IP':<22}{'BEFORE (correct)':<26}{'AFTER':<26}{'Status'}")
    print(f"  {'─'*22}{'─'*26}{'─'*26}{'─'*14}")
    for ip in all_ips:
        b_mac = before[ip].mac  if ip in before else "(none)"
        a_mac = after[ip].mac   if ip in after  else "(none)"
        real  = real_map.get(ip, b_mac)

        if a_mac == real:
            status = G("  ✔ CLEAN")
            a_col  = a_mac
        else:
            status = R("  ✖ POISONED")
            a_col  = R(a_mac)

        changed = "→" if b_mac != a_mac else " "
        print(f"  {ip:<22}{b_mac:<26}{a_col:<26}{changed} {status}")
    endsection()


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 8 ── ASCII topology diagram
# ══════════════════════════════════════════════════════════════════════════════

def draw_topology(
    alice    : NetworkDevice,
    router   : NetworkDevice,
    eve      : NetworkDevice,
    webserver: NetworkDevice,
    poisoned : bool = False,
) -> None:
    """Render an ASCII network diagram reflecting current trust state."""
    section("Network Topology")
    gw_mac  = alice.arp_cache.mac_for(router.ip) or "?"
    correct = gw_mac == router.mac
    arrow   = f"──────────────────" if correct else R("──── EVE (MITM) ───")
    status  = G("CLEAN") if correct else R("POISONED — MITM ACTIVE")

    print(f"""
   ┌────────────────────────────────────────────────────────────┐
   │                    LOCAL NETWORK SEGMENT                   │
   │                                                            │
   │   {alice.icon} Alice (Victim)              {router.icon} Router (Gateway)    │
   │   {C(alice.ip):<28} {C(router.ip):<20}   │
   │   MAC: {Y(alice.mac):<22} MAC: {Y(router.mac):<14}   │
   │         │                                   │              │
   │         └──── {arrow} ────┘              │
   │                       ↕                                    │
   │              Traffic status: {status:<20}           │
   │                                                            │
   │   {eve.icon} Eve (Attacker)             {webserver.icon} WebServer           │
   │   {R(eve.ip):<28} {C(webserver.ip):<20}   │
   │   MAC: {R(eve.mac):<22} MAC: {Y(webserver.mac):<14}   │
   └────────────────────────────────────────────────────────────┘
""")
    endsection()


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 9 ── Guided lab steps
# ══════════════════════════════════════════════════════════════════════════════

def lab_step_initial_state(
    bus      : SimBus,
    proto    : ARPProtocol,
    alice    : NetworkDevice,
    router   : NetworkDevice,
    eve      : NetworkDevice,
    webserver: NetworkDevice,
    elog     : EventLog,
) -> None:
    """
    LAB STEP 1 — Populate initial ARP caches (pre-attack state).

    In real life hosts learn ARP entries through normal traffic.
    Here we fast-forward by running ARP resolutions for all pairs.
    """
    banner("LAB STEP 1 — Initial Network State", Ansi.GREEN_B)
    print(textwrap.dedent(f"""
    {BD('Objective:')}
    Observe the network in its {G('clean, normal state')} before any attack.
    All ARP caches hold correct IP → MAC mappings.

    {BD('What ARP does:')}
    Ethernet frames are addressed by MAC, not IP.  Before Alice can
    send a packet to the Router she must discover its MAC address.
    She broadcasts an {B('ARP REQUEST')} and the Router sends back an
    {G('ARP REPLY')}.  Alice caches the result in her ARP table.
    """))
    wait("  ↵  Press Enter to run initial ARP resolution…")

    section("Populating ARP Caches via Normal ARP Exchange")

    # Alice learns router and webserver
    info(f"Alice resolves Router ({router.ip})…")
    proto.resolve(alice, router.ip)

    info(f"Alice resolves WebServer ({webserver.ip})…")
    proto.resolve(alice, webserver.ip)

    # Router learns Alice
    info(f"Router resolves Alice ({alice.ip})…")
    proto.resolve(router, alice.ip)

    # Webserver learns Alice
    info(f"WebServer resolves Alice ({alice.ip})…")
    proto.resolve(webserver, alice.ip)

    section("ARP Tables — All Devices")
    for dev in (alice, router, eve, webserver):
        dev.display_header()
        dev.arp_cache.display()
        print()

    draw_topology(alice, router, eve, webserver, poisoned=False)
    bus.print_capture(title="Packet Capture — Step 1")
    wait()


def lab_step_normal_comms(
    bus  : SimBus,
    proto: ARPProtocol,
    alice: NetworkDevice,
    router: NetworkDevice,
    eve  : NetworkDevice,
    webserver: NetworkDevice,
    elog : EventLog,
) -> None:
    """
    LAB STEP 2 — Normal data communication.
    Alice sends HTTP requests to the gateway and web server.
    No interception yet — traffic flows cleanly.
    """
    banner("LAB STEP 2 — Normal Communication", Ansi.GREEN_B)
    print(textwrap.dedent(f"""
    {BD('Objective:')}
    Watch normal data frames flow from Alice to the Gateway and
    WebServer.  Eve is on the network but {G('not yet attacking')}.

    Notice that each frame reaches its {G('correct destination')}.
    """))
    wait("  ↵  Press Enter to send normal traffic…")

    section("Alice → Router (normal HTTP)")
    proto.send_data(alice, router.ip,    "GET / HTTP/1.1  Host: example.com")
    proto.send_data(alice, router.ip,    "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9")
    proto.send_data(alice, webserver.ip, "GET /dashboard  Cookie: session=ABCDEF")
    proto.send_data(alice, webserver.ip, "POST /transfer  amount=1000&to=bob")

    section("Router → Alice (response)")
    proto.send_data(router, alice.ip, "HTTP/1.1 200 OK  Content-Type: text/html")

    section("Packet Capture — Step 2 (last 8 packets)")
    bus.print_capture(last_n=8, title="Clean Traffic")

    ok("All packets reached their intended destinations.")
    ok("Eve captured nothing — attack not yet started.")
    wait()


def lab_step_attack(
    bus      : SimBus,
    proto    : ARPProtocol,
    alice    : NetworkDevice,
    router   : NetworkDevice,
    eve      : NetworkDevice,
    webserver: NetworkDevice,
    elog     : EventLog,
) -> dict:
    """
    LAB STEP 3 — Execute the ARP poisoning attack.

    Eve sends four spoofed ARP replies:
    ① → Alice   : "Router    is at Eve's MAC"
    ② → Alice   : "WebServer is at Eve's MAC"
    ③ → Router  : "Alice     is at Eve's MAC"
    ④ → WebServer: "Alice    is at Eve's MAC"

    After poisoning, Eve sits between all conversations.
    """
    banner("LAB STEP 3 — ARP Poisoning Attack", Ansi.RED_B)
    print(textwrap.dedent(f"""
    {BD(R('Attack Scenario:'))}
    Eve ({R(eve.ip)} / {R(eve.mac)}) is on the same LAN.
    She will send {R('unsolicited (fake) ARP replies')} to Alice and the
    Router/WebServer, convincing each that the other's IP maps to
    {R("Eve's MAC address")}.

    ARP has {R('NO AUTHENTICATION')} — victims blindly accept replies and
    overwrite their caches.  No handshake or confirmation is required.

    {BD(Y('Attack plan:'))}
      Step A — Poison Alice's   cache:  Router IP    → Eve's MAC
      Step B — Poison Alice's   cache:  WebServer IP → Eve's MAC
      Step C — Poison Router's  cache:  Alice IP     → Eve's MAC
      Step D — Poison Server's  cache:  Alice IP     → Eve's MAC
    """))
    wait("  ↵  Press Enter to execute the attack…")

    # Snapshot before attack
    before_alice  = alice.arp_cache.snapshot()
    before_router = router.arp_cache.snapshot()

    section("Step A — Poisoning Alice's cache (Router IP → Eve's MAC)")
    proto.poison(eve, alice, router.ip)
    print()

    section("Step B — Poisoning Alice's cache (WebServer IP → Eve's MAC)")
    proto.poison(eve, alice, webserver.ip)
    print()

    section("Step C — Poisoning Router's cache (Alice IP → Eve's MAC)")
    proto.poison(eve, router, alice.ip)
    print()

    section("Step D — Poisoning WebServer's cache (Alice IP → Eve's MAC)")
    proto.poison(eve, webserver, alice.ip)
    print()

    after_alice  = alice.arp_cache.snapshot()
    after_router = router.arp_cache.snapshot()

    # Build real-MAC reference map
    real_mac = {
        router.ip    : router.mac,
        webserver.ip : webserver.mac,
        alice.ip     : alice.mac,
        eve.ip       : eve.mac,
    }

    section("ARP Cache Diff — Alice")
    print_arp_diff(before_alice, after_alice, alice, real_mac)

    section("ARP Cache Diff — Router")
    print_arp_diff(before_router, after_router, router, real_mac)

    draw_topology(alice, router, eve, webserver, poisoned=True)

    alert("ARP caches successfully poisoned!  Eve is now a transparent MITM.")
    wait()
    return {"before_alice": before_alice, "before_router": before_router}


def lab_step_intercept(
    bus      : SimBus,
    proto    : ARPProtocol,
    alice    : NetworkDevice,
    router   : NetworkDevice,
    eve      : NetworkDevice,
    webserver: NetworkDevice,
    elog     : EventLog,
) -> None:
    """
    LAB STEP 4 — Show live traffic interception.

    Alice retransmits the same requests as Step 2.
    Because her ARP cache is poisoned, frames go to Eve first.
    Eve reads the payload, then transparently forwards to the real host.
    Alice and the router/server notice NOTHING.
    """
    banner("LAB STEP 4 — Live Traffic Interception (MITM)", Ansi.MAGENTA_B)
    print(textwrap.dedent(f"""
    {BD(M('Man-in-the-Middle Active'))}
    Alice's ARP cache says:
      • Router     ({router.ip})    → {R(eve.mac)}  ← WRONG (Eve's MAC)
      • WebServer  ({webserver.ip}) → {R(eve.mac)}  ← WRONG (Eve's MAC)

    When Alice sends a frame "to the Router" she actually addresses it
    to Eve's MAC.  The switch delivers it to Eve.  Eve reads the
    payload, then re-sends it to the real Router — {IT('completely silently')}.
    Alice and the Router have no indication anything is wrong.
    """))
    wait("  ↵  Press Enter to replay Alice's traffic through Eve…")

    section("Intercepted Traffic — Alice → Router (via Eve)")
    proto.send_data(alice, router.ip, "GET / HTTP/1.1  Host: bank.example.com", attacker=eve)
    proto.send_data(alice, router.ip, "Cookie: auth_token=SECRET_BEARER_TOKEN", attacker=eve)
    proto.send_data(alice, router.ip, "POST /api/transfer  body={to:bob,amt:5000}", attacker=eve)

    section("Intercepted Traffic — Alice → WebServer (via Eve)")
    proto.send_data(alice, webserver.ip, "GET /admin  Cookie: admin_session=XYZ99", attacker=eve)
    proto.send_data(alice, webserver.ip, "POST /login  user=alice&password=p4ssw0rd!", attacker=eve)

    section("Eve's Inbox — Intercepted Packets")
    if eve.inbox:
        print(f"\n  {'#':<4} {'Type':<14} {'Payload'}")
        print(f"  {'─'*4} {'─'*14} {'─'*52}")
        for i, pkt in enumerate(eve.inbox, 1):
            if pkt.ptype in (PktType.MITM, PktType.DATA):
                print(f"  {D(str(i)):<4} {M(pkt.short_type()):<14} {R(pkt.payload)}")
    else:
        print(f"  {D('(no data packets intercepted)')}")

    section("Packet Capture — Last 14 packets")
    bus.print_capture(last_n=14, title="MITM Traffic")

    alert("Eve silently captured credentials, session tokens, and financial data.")
    info("Alice and the Router experienced NO errors or delays.")
    wait()


def lab_step_defense(
    bus      : SimBus,
    proto    : ARPProtocol,
    alice    : NetworkDevice,
    router   : NetworkDevice,
    eve      : NetworkDevice,
    webserver: NetworkDevice,
    elog     : EventLog,
    ids      : ARPWatcher,
) -> None:
    """
    LAB STEP 5 — Apply defenses and verify they work.

    Defenses demonstrated:
    ① Static ARP entries on Alice (blocks cache poisoning)
    ② ARPWatcher IDS (detects MAC changes in traffic)
    ③ Re-running the attack to show it fails
    """
    banner("LAB STEP 5 — Defense Mechanisms", Ansi.GREEN_B)
    print(textwrap.dedent(f"""
    {BD(G('Defenses we will apply:'))}

    {G('① Static ARP entries')}
       Pin the correct IP→MAC mapping in Alice's cache.
       Any spoofed reply trying to overwrite it will be {G('silently rejected')}.

    {G('② ARPWatcher IDS')}
       Monitor the network for MAC address changes on known IPs.
       Raises alerts when ARP poisoning patterns are observed.

    {G('③ Re-run the attack')}
       Eve will attempt the same poison as Step 3.
       We will verify the defenses hold.
    """))
    wait("  ↵  Press Enter to reset and apply defenses…")

    # ── Reset state ─────────────────────────────────────────────────────────
    section("Resetting Alice's ARP Cache")
    alice.arp_cache = ARPTable(owner_name="Alice", ids_enabled=True)
    alice.arp_cache.on_detect = lambda ip, old, new: alert(
        f"ARPWatcher (Alice): MAC change for {ip}!  {old} → {new}")
    info("ARP cache wiped.  Re-learning via normal ARP…")
    proto.resolve(alice, router.ip)
    proto.resolve(alice, webserver.ip)
    ok(f"Learned {router.ip} → {router.mac}")
    ok(f"Learned {webserver.ip} → {webserver.mac}")

    # ── Apply static entries ─────────────────────────────────────────────────
    section("Applying Static ARP Entries")
    alice.arp_cache.pin_static(router.ip,    router.mac)
    alice.arp_cache.pin_static(webserver.ip, webserver.mac)
    ok(f"Pinned (STATIC): {router.ip} → {router.mac}")
    ok(f"Pinned (STATIC): {webserver.ip} → {webserver.mac}")

    # ── Enable ARPWatcher on router ──────────────────────────────────────────
    section("Enabling ARPWatcher IDS on Router")
    router.arp_cache.ids_enabled = True
    router.arp_cache.on_detect = lambda ip, old, new: alert(
        f"ARPWatcher (Router): MAC change for {ip}!  {old} → {new}")
    ok("Router IDS monitoring enabled.")

    wait("  ↵  Press Enter to re-run Eve's attack…")

    # ── Eve re-attacks ───────────────────────────────────────────────────────
    section("Eve Attempts ARP Poisoning — Round 2")
    warn("Eve sending spoofed ARP replies…")
    proto.poison(eve, alice,  router.ip)
    proto.poison(eve, alice,  webserver.ip)
    proto.poison(eve, router, alice.ip)

    # ── Verify results ───────────────────────────────────────────────────────
    section("Alice's ARP Cache After Defense")
    alice.arp_cache.display()

    section("Router's ARP Cache After Defense")
    router.arp_cache.display()

    # ── IDS scan ─────────────────────────────────────────────────────────────
    section("ARPWatcher IDS Scan — Full Packet Capture")
    n_alerts = ids.scan()
    ids.print_report()

    # ── Traffic test ─────────────────────────────────────────────────────────
    section("Sending Data — Are We Still Intercepted?")
    eve.inbox.clear()
    proto.send_data(alice, router.ip,    "GET /  (post-defense)", attacker=eve)
    proto.send_data(alice, webserver.ip, "POST /login  (post-defense)", attacker=eve)

    if not [p for p in eve.inbox if p.ptype == PktType.MITM]:
        ok("Eve's inbox contains NO intercepted data packets!")
        ok("Static ARP defense successfully blocked the MITM attack.")
    else:
        warn("Eve still intercepted packets — check defense configuration.")

    draw_topology(alice, router, eve, webserver, poisoned=False)
    wait()


def lab_step_summary(elog: EventLog, ids: ARPWatcher) -> None:
    """
    LAB STEP 6 — Print the complete event journal and a knowledge quiz.
    """
    banner("LAB STEP 6 — Session Summary", Ansi.CYAN_B)
    elog.print_all()

    section("Lab Statistics")
    label("Total attack events",    str(elog.count_attacks()))
    label("Total IDS detections",   str(elog.count_detections()))
    label("IDS alerts raised",      str(len(ids._alerts)))
    print()

    section("Key Takeaways")
    takeaways = [
        ("ARP has no authentication",
         "Any host can claim ownership of any IP address."),
        ("Dynamic entries are the weakness",
         "Caches accept replies without verifying the requester's identity."),
        ("MITM is invisible to victims",
         "The attacker silently relays traffic — no errors, no delays."),
        ("Static ARP prevents poisoning",
         "Pinned entries cannot be overwritten by spoofed replies."),
        ("IDS tools detect the anomaly",
         "arpwatch / XArp / DAI detect MAC changes on known IPs."),
        ("Encryption limits the damage",
         "TLS/HTTPS means intercepted data is ciphertext — not plaintext."),
    ]
    for i, (point, detail) in enumerate(takeaways, 1):
        print(f"\n  {C(str(i)+'.')}  {BD(point)}")
        print(f"       {D(detail)}")

    print(f"\n{hr()}")
    print(textwrap.dedent(f"""
    {BD(Y('Legal Reminder:'))}
    ARP poisoning real networks without {BD('explicit written permission')}
    is a criminal offence under the CFAA (US), Computer Misuse Act (UK),
    and equivalent legislation worldwide.  This simulator exists ONLY
    for education in controlled lab environments.
    """))
    wait()


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 10 ── Quick-reference concept screens
# ══════════════════════════════════════════════════════════════════════════════

def concept_what_is_arp() -> None:
    banner("CONCEPT — What is ARP?", Ansi.CYAN_B)
    print(textwrap.dedent(f"""
    {BD('Address Resolution Protocol')}  (RFC 826, published 1982)

    Every device on an Ethernet LAN has two identifiers:

      {C('IP address')}  — Logical,  layer 3  (e.g.  192.168.10.5)
      {Y('MAC address')} — Physical, layer 2  (e.g.  A1:IC:E0:00:05:AA)

    IP packets are routed by IP address.  Ethernet frames are forwarded
    by MAC address.  ARP bridges the gap.

    {BD('Normal flow:')}

      1.  Alice wants to send to {C('192.168.10.1')} (the gateway).
      2.  She checks her ARP cache — {Y('no entry')}.
      3.  She broadcasts:   {B('"Who has 192.168.10.1?  Tell 192.168.10.5"')}
          (destination MAC  FF:FF:FF:FF:FF:FF — everyone hears this)
      4.  Router replies:   {G('"192.168.10.1 is at R0:UT:ER:00:01:BB"')}
          (unicast, direct response)
      5.  Alice caches the mapping and sends her Ethernet frame.

    {BD(R('The critical flaw:'))}
    Step 4 has {R('NO AUTHENTICATION')}.  The router is not required to
    prove it owns that IP.  Any host can send that reply — and most
    operating systems will cache it without question.
    """))
    wait()


def concept_how_poisoning_works() -> None:
    banner("CONCEPT — How ARP Poisoning Works", Ansi.RED_B)
    print(textwrap.dedent(f"""
    {BD(R('ARP Poisoning / ARP Spoofing / ARP Cache Poisoning'))}

    The attacker exploits the lack of ARP authentication to corrupt
    the ARP caches of one or more victims.

    {BD('Classic MITM setup — two poison packets are enough:')}

    Packet ①  → Alice:
        {R('"Router (192.168.10.1) is at EV:11:77:00:77:CC"')}
        Alice now thinks the gateway is at Eve's MAC.

    Packet ②  → Router:
        {R('"Alice (192.168.10.5) is at EV:11:77:00:77:CC"')}
        Router now thinks Alice is at Eve's MAC.

    {BD('Result:')}

        Alice ──→ Eve ──→ Router   (Alice thinks she talks to Router)
        Router ──→ Eve ──→ Alice   (Router thinks it talks to Alice)

        Eve sits in the middle, {M('reading and optionally modifying')}
        every packet.  She must keep re-sending the fake ARPs every
        ~30–60 seconds to prevent the real entries from re-learning.

    {BD(Y('What Eve can do with this position:'))}
      • Steal passwords, cookies, session tokens (HTTP)
      • Perform SSL stripping (downgrade HTTPS → HTTP)
      • Inject malicious JavaScript into web pages
      • Redirect DNS queries
      • Deliver ransomware / malware payloads
      • Perform session hijacking
    """))
    wait()


def concept_defenses() -> None:
    banner("CONCEPT — Defense Mechanisms", Ansi.GREEN_B)
    print(textwrap.dedent(f"""
    {BD(G('Defenses Against ARP Poisoning'))}

    {G('1. Static ARP Entries')}
       Manually pin IP→MAC in the OS cache.
       Linux: {C('sudo arp -s 192.168.10.1 R0:UT:ER:00:01:BB')}
       Windows: {C('netsh interface ip add neighbors "Ethernet" 192.168.10.1 R0-UT-ER-00-01-BB')}
       ✔ Simple, free    ✖ Doesn't scale, high admin overhead

    {G('2. Dynamic ARP Inspection (DAI)')}
       Enterprise managed switches intercept all ARP traffic and
       validate replies against a DHCP snooping table.
       Packets with invalid IP→MAC pairs are {G('silently dropped')}.
       ✔ Transparent, scalable    ✖ Requires managed switch hardware

    {G('3. ARPWatch / XArp')}
       Daemon monitors ARP traffic and alerts when a known IP is
       seen with a new MAC (arpwatch sends email; XArp has GUI).
       ✔ Easy to deploy    ✖ Alerts after the fact, doesn't prevent

    {G('4. 802.1X Port Authentication')}
       Devices must authenticate before the switch allows any traffic.
       A rogue attacker who cannot authenticate cannot participate.
       ✔ Prevents rogue devices entirely    ✖ Complex PKI setup

    {G('5. End-to-End Encryption (TLS / HTTPS)')}
       Even if traffic is intercepted the payload is ciphertext.
       SSL certificate validation prevents silent SSL stripping.
       ✔ Protects data even if MITM occurs    ✖ Not a network fix

    {G('6. IPv6 + SEND (Secure Neighbour Discovery)')}
       NDP (IPv6's ARP replacement) with SEND adds cryptographic
       proof-of-ownership via RSA keys for each IP claim.
       ✔ Authentication baked in    ✖ Complex, limited adoption
    """))
    wait()


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 11 ── Interactive CLI menu
# ══════════════════════════════════════════════════════════════════════════════

def print_menu(lab_state: dict) -> None:
    ran = lab_state.get("steps_run", set())
    def done(n): return G(" ✔") if n in ran else "  "

    print(f"""
{Ansi.CYAN_B}{Ansi.BOLD}  ╔══════════════════════════════════════════════════════╗
  ║        ARP POISONING LAB — MAIN MENU                 ║
  ╠══════════════════════════════════════════════════════╣{Ansi.RESET}
  {D('─── Guided Lab Steps ───────────────────────────────────')}
  {C('  1 ')}  Initial State & ARP Cache Population             {done(1)}
  {C('  2 ')}  Normal Communication (clean traffic)            {done(2)}
  {C('  3 ')}  ARP Poisoning Attack                            {done(3)}
  {C('  4 ')}  Live Interception Demo (MITM)                   {done(4)}
  {C('  5 ')}  Defense Mechanisms & Verification               {done(5)}
  {C('  6 ')}  Session Summary & Event Journal                 {done(6)}
  {D('─── Concept Explainers ─────────────────────────────────')}
  {Y('  A ')}  What is ARP?
  {Y('  B ')}  How ARP Poisoning Works
  {Y('  C ')}  Defense Mechanisms
  {D('─── Lab Tools ──────────────────────────────────────────')}
  {B('  T ')}  Print ARP tables (current state)
  {B('  P ')}  Print full packet capture log
  {B('  E ')}  Print event journal
  {B('  D ')}  Draw network topology
  {B('  R ')}  Reset simulation to clean state
  {D('─────────────────────────────────────────────────────────')}
  {R('  Q ')}  Quit
{Ansi.CYAN_B}{Ansi.BOLD}  ╚══════════════════════════════════════════════════════╝{Ansi.RESET}
  Choice: """, end="")


def run_lab() -> None:
    """Main entry point — interactive CLI lab menu."""

    # ── Splash screen ────────────────────────────────────────────────────────
    clear()
    banner(
        "ARP POISONING EDUCATIONAL LAB",
        "A Hands-On Cybersecurity Simulator  •  Pure Python  •  No Real Packets",
        Ansi.CYAN_B,
    )
    print(textwrap.dedent(f"""
    {BD('Welcome to the ARP Poisoning Lab!')}

    This interactive simulator walks you through a complete ARP poisoning
    attack — from clean network state, through the attack itself, all the
    way to detection and defense — using nothing but Python objects.

    {BD(Y('Lab network:'))}
      {B('💻 Alice     ')}  192.168.10.5   A1:IC:E0:00:05:AA  (victim laptop)
      {B('🌐 Router    ')}  192.168.10.1   R0:UT:ER:00:01:BB  (gateway)
      {B('👾 Eve       ')}  192.168.10.77  EV:11:77:00:77:CC  (attacker)
      {B('🖧 WebServer ')}  192.168.10.20  WE:B5:RV:00:20:DD  (internal server)

    {BD(Y('Recommended order:'))}  Steps 1 → 2 → 3 → 4 → 5 → 6

    {R(BD('⚠  Legal Notice:'))}  This program performs NO real network operations.
    Attacking real networks without written permission is {R('ILLEGAL')}.
    """))
    wait("  ↵  Press Enter to open the main menu…")

    # ── Build lab ────────────────────────────────────────────────────────────
    bus, proto, ids, elog, alice, router, eve, webserver = build_lab()
    lab_state = {"steps_run": set()}

    def reset_lab():
        nonlocal bus, proto, ids, elog, alice, router, eve, webserver
        bus, proto, ids, elog, alice, router, eve, webserver = build_lab()
        lab_state["steps_run"] = set()
        ok("Simulation reset — all state cleared.")
        wait()

    # ── Main loop ────────────────────────────────────────────────────────────
    while True:
        clear()
        print_menu(lab_state)
        choice = input().strip().upper()

        if choice == "1":
            lab_step_initial_state(bus, proto, alice, router, eve, webserver, elog)
            lab_state["steps_run"].add(1)
        elif choice == "2":
            lab_step_normal_comms(bus, proto, alice, router, eve, webserver, elog)
            lab_state["steps_run"].add(2)
        elif choice == "3":
            lab_step_attack(bus, proto, alice, router, eve, webserver, elog)
            lab_state["steps_run"].add(3)
        elif choice == "4":
            lab_step_intercept(bus, proto, alice, router, eve, webserver, elog)
            lab_state["steps_run"].add(4)
        elif choice == "5":
            lab_step_defense(bus, proto, alice, router, eve, webserver, elog, ids)
            lab_state["steps_run"].add(5)
        elif choice == "6":
            lab_step_summary(elog, ids)
            lab_state["steps_run"].add(6)
        elif choice == "A":
            concept_what_is_arp()
        elif choice == "B":
            concept_how_poisoning_works()
        elif choice == "C":
            concept_defenses()
        elif choice == "T":
            section("Current ARP Tables")
            for dev in (alice, router, eve, webserver):
                dev.display_header()
                dev.arp_cache.display()
                print()
            wait()
        elif choice == "P":
            clear()
            bus.print_capture(title="Full Packet Capture Log")
            wait()
        elif choice == "E":
            clear()
            elog.print_all()
            wait()
        elif choice == "D":
            poisoned = (alice.arp_cache.mac_for(router.ip) == eve.mac)
            draw_topology(alice, router, eve, webserver, poisoned=poisoned)
            wait()
        elif choice == "R":
            reset_lab()
        elif choice == "Q":
            clear()
            banner("Goodbye", "Stay curious. Stay ethical. Stay legal.", Ansi.CYAN)
            sys.exit(0)
        else:
            warn(f"Unknown option '{choice}' — please enter a number or letter from the menu.")
            time.sleep(1)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_lab()

