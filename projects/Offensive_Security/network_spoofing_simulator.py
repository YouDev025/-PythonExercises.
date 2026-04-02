"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         NETWORK SPOOFING EDUCATIONAL SIMULATOR                               ║
║         ARP Spoofing / Man-in-the-Middle Attack — Pure Simulation            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Author  : Senior Python / Cybersecurity Instructor                          ║
║  Run     : python network_spoofing_simulator.py                              ║
║  Purpose : Teach ARP spoofing and MITM concepts safely, with zero real       ║
║            network interaction. Everything is in-memory Python objects.      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ⚠  EDUCATIONAL USE ONLY — No real packets are crafted or transmitted.      ║
║     ARP spoofing real networks without permission is illegal.                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
# Standard-library imports only
# ─────────────────────────────────────────────────────────────────────────────
import time
import textwrap
from copy import deepcopy
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# ANSI colour helpers (degrade gracefully if terminal doesn't support them)
# ─────────────────────────────────────────────────────────────────────────────

class C:
    """Terminal colour / style constants."""
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    BG_RED = "\033[41m"
    BG_DARK= "\033[40m"

def red(s):     return f"{C.RED}{s}{C.RESET}"
def green(s):   return f"{C.GREEN}{s}{C.RESET}"
def yellow(s):  return f"{C.YELLOW}{s}{C.RESET}"
def blue(s):    return f"{C.BLUE}{s}{C.RESET}"
def cyan(s):    return f"{C.CYAN}{s}{C.RESET}"
def magenta(s): return f"{C.MAGENTA}{s}{C.RESET}"
def bold(s):    return f"{C.BOLD}{s}{C.RESET}"
def dim(s):     return f"{C.DIM}{s}{C.RESET}"

# ─────────────────────────────────────────────────────────────────────────────
# UI helper utilities
# ─────────────────────────────────────────────────────────────────────────────

TERM_WIDTH = 78

def banner(title: str, colour=C.CYAN) -> None:
    """Print a full-width section banner."""
    pad = max(0, TERM_WIDTH - len(title) - 4)
    left  = pad // 2
    right = pad - left
    print(f"\n{colour}{C.BOLD}{'═' * TERM_WIDTH}{C.RESET}")
    print(f"{colour}{C.BOLD}  {'─' * left} {title} {'─' * right}{C.RESET}")
    print(f"{colour}{C.BOLD}{'═' * TERM_WIDTH}{C.RESET}")

def section(title: str) -> None:
    """Print a lighter sub-section header."""
    print(f"\n{C.YELLOW}{C.BOLD}  ┌─ {title} {'─' * max(0, TERM_WIDTH - len(title) - 5)}┐{C.RESET}")

def log(tag: str, msg: str, colour=C.WHITE) -> None:
    """Timestamped log line."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"  {dim(ts)}  {colour}{C.BOLD}[{tag:^10}]{C.RESET}  {colour}{msg}{C.RESET}")

def pause(prompt: str = "  Press Enter to continue…") -> None:
    input(f"\n{dim(prompt)}")

def slow_print(text: str, delay: float = 0.025) -> None:
    """Print a string character-by-character for dramatic effect."""
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def box(lines: list[str], title: str = "", width: int = TERM_WIDTH) -> None:
    """Render a Unicode box around a list of strings."""
    inner = width - 2
    top_title = f" {title} " if title else ""
    title_pad = inner - len(top_title)
    tl = f"╔{'═' * (len(top_title))}{'═' * title_pad}╗"
    print(f"  {C.CYAN}{C.BOLD}╔{'═' * (inner)}╗{C.RESET}")
    if title:
        print(f"  {C.CYAN}{C.BOLD}║{C.YELLOW} {title} {C.CYAN}{'═' * (inner - len(title) - 2)}║{C.RESET}")
        print(f"  {C.CYAN}{C.BOLD}╠{'═' * inner}╣{C.RESET}")
    for line in lines:
        stripped = line  # keep colour codes but pad on visible length
        visible_len = len(line.encode("ascii", errors="ignore"))
        pad = max(0, inner - len(line) + (len(line) - visible_len))
        # Simpler: just truncate/pad raw string
        print(f"  {C.CYAN}{C.BOLD}║{C.RESET} {line:<{inner-2}} {C.CYAN}{C.BOLD}║{C.RESET}")
    print(f"  {C.CYAN}{C.BOLD}╚{'═' * inner}╝{C.RESET}")

# ─────────────────────────────────────────────────────────────────────────────
# Core data models
# ─────────────────────────────────────────────────────────────────────────────

class NetworkDevice:
    """
    Represents a generic network device (host, router, or attacker).

    Attributes
    ----------
    name        : human-readable label
    ip          : simulated IPv4 address
    mac         : simulated MAC address
    arp_table   : dict mapping IP → MAC  (the device's ARP cache)
    static_arp  : set of IPs whose ARP entries are pinned and cannot be updated
    inbox       : list of received SimPacket objects this session
    role        : 'victim' | 'gateway' | 'attacker' | 'generic'
    """

    def __init__(self, name: str, ip: str, mac: str, role: str = "generic"):
        self.name       = name
        self.ip         = ip
        self.mac        = mac
        self.role       = role
        self.arp_table  : dict[str, str]  = {}   # ip → mac
        self.static_arp : set[str]        = set()
        self.inbox      : list            = []

    # ── ARP table management ──────────────────────────────────────────────

    def learn_arp(self, ip: str, mac: str, forced: bool = False) -> bool:
        """
        Update ARP table entry for ip → mac.
        Returns False (and ignores update) if the entry is pinned as static,
        UNLESS forced=True (used for initial static population).
        """
        if ip in self.static_arp and not forced:
            return False          # Static entry — update rejected
        self.arp_table[ip] = mac
        return True

    def set_static_arp(self, ip: str, mac: str) -> None:
        """Pin a static ARP entry that cannot be overwritten by spoofed replies."""
        self.arp_table[ip]  = mac
        self.static_arp.add(ip)

    def lookup_mac(self, ip: str) -> str | None:
        """Return the MAC address for a given IP, or None if not cached."""
        return self.arp_table.get(ip)

    # ── Packet I/O (simulation only) ─────────────────────────────────────

    def receive(self, packet) -> None:
        """Accept a simulated packet into the inbox."""
        self.inbox.append(packet)

    def role_icon(self) -> str:
        icons = {
            "victim"  : "💻",
            "gateway" : "🌐",
            "attacker": "👾",
            "generic" : "🔲",
        }
        return icons.get(self.role, "🔲")

    def __repr__(self) -> str:
        return (f"<Device {self.name} | {self.ip} | {self.mac} | "
                f"ARP entries: {len(self.arp_table)}>")


class SimPacket:
    """
    Represents a simulated network packet flowing between two devices.

    Fields mirror real packet concepts:
      - ptype : 'ARP_REQUEST' | 'ARP_REPLY' | 'ARP_SPOOF' | 'DATA' | 'INTERCEPTED'
      - src_ip / dst_ip  : layer-3 addresses
      - src_mac / dst_mac: layer-2 addresses (may be spoofed in spoof packets)
      - payload : human-readable string describing the data
    """

    def __init__(
        self,
        ptype   : str,
        src_ip  : str,
        dst_ip  : str,
        src_mac : str,
        dst_mac : str,
        payload : str = "",
        spoofed : bool = False,
    ):
        self.ptype    = ptype
        self.src_ip   = src_ip
        self.dst_ip   = dst_ip
        self.src_mac  = src_mac
        self.dst_mac  = dst_mac
        self.payload  = payload
        self.spoofed  = spoofed
        self.ts       = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def label_colour(self) -> str:
        colours = {
            "ARP_REQUEST" : C.BLUE,
            "ARP_REPLY"   : C.GREEN,
            "ARP_SPOOF"   : C.RED,
            "DATA"        : C.WHITE,
            "INTERCEPTED" : C.MAGENTA,
        }
        return colours.get(self.ptype, C.WHITE)

    def __repr__(self) -> str:
        spoof_flag = " [SPOOFED]" if self.spoofed else ""
        return (f"[{self.ptype}{spoof_flag}] "
                f"{self.src_ip}({self.src_mac}) → {self.dst_ip}({self.dst_mac}) "
                f"| {self.payload}")


# ─────────────────────────────────────────────────────────────────────────────
# Simulated Network (the "wire")
# ─────────────────────────────────────────────────────────────────────────────

class SimulatedNetwork:
    """
    Acts as the Layer-2 broadcast domain (think: a switch/hub).

    Responsibilities
    ----------------
    - Deliver packets between devices
    - Maintain a packet capture log (like Wireshark)
    - Provide ARP table snapshots for before/after comparisons
    """

    def __init__(self):
        self.devices      : dict[str, NetworkDevice] = {}  # name → device
        self.packet_log   : list[SimPacket]          = []
        self.capture_on   : bool                     = True

    def add_device(self, device: NetworkDevice) -> None:
        self.devices[device.name] = device

    def get_by_ip(self, ip: str) -> NetworkDevice | None:
        for d in self.devices.values():
            if d.ip == ip:
                return d
        return None

    # ── Packet delivery ──────────────────────────────────────────────────

    def send(self, packet: SimPacket, recipient_name: str) -> None:
        """Deliver packet to a named device and capture it."""
        if self.capture_on:
            self.packet_log.append(packet)
        target = self.devices.get(recipient_name)
        if target:
            target.receive(packet)

    def broadcast(self, packet: SimPacket, sender_name: str) -> None:
        """Broadcast packet to all devices except the sender."""
        if self.capture_on:
            self.packet_log.append(packet)
        for name, device in self.devices.items():
            if name != sender_name:
                device.receive(packet)

    # ── ARP snapshot ─────────────────────────────────────────────────────

    def snapshot_arp_tables(self) -> dict[str, dict]:
        """Return a deep copy of all ARP tables for comparison."""
        return {
            name: deepcopy(dev.arp_table)
            for name, dev in self.devices.items()
        }

    # ── Display helpers ──────────────────────────────────────────────────

    def print_arp_table(self, device: NetworkDevice) -> None:
        """Pretty-print one device's ARP cache."""
        icon  = device.role_icon()
        title = f"{icon}  {device.name}  ({device.ip} / {device.mac})"
        print(f"\n  {C.BOLD}{title}{C.RESET}")
        print(f"  {'─' * 50}")
        print(f"  {'IP Address':<18} {'MAC Address':<22} {'Type':<10}")
        print(f"  {'─' * 18} {'─' * 22} {'─' * 10}")
        if not device.arp_table:
            print(f"  {dim('(empty)')}")
        for ip, mac in device.arp_table.items():
            entry_type = "STATIC" if ip in device.static_arp else "dynamic"
            colour     = C.GREEN if entry_type == "STATIC" else C.WHITE
            poison_mark = ""
            # Detect if a victim entry has been poisoned (MAC != what gateway/real device has)
            real_dev = self.get_by_ip(ip)
            if real_dev and real_dev.mac != mac and entry_type != "STATIC":
                colour     = C.RED
                poison_mark = " ← POISONED"
            print(f"  {colour}{ip:<18} {mac:<22} {entry_type}{poison_mark}{C.RESET}")
        print()

    def print_all_arp_tables(self) -> None:
        section("ARP Cache Tables — All Devices")
        for device in self.devices.values():
            self.print_arp_table(device)

    def print_packet_log(self, last_n: int = 0) -> None:
        """Print the simulated packet capture log."""
        section("Packet Capture Log")
        entries = self.packet_log[-last_n:] if last_n else self.packet_log
        if not entries:
            print(f"  {dim('(no packets captured)')}")
            return
        print(f"  {'#':<4} {'Time':<14} {'Type':<14} {'Source':<22} {'Destination':<22} {'Payload'}")
        print(f"  {'─'*4} {'─'*14} {'─'*14} {'─'*22} {'─'*22} {'─'*20}")
        for i, pkt in enumerate(entries, 1):
            col   = pkt.label_colour()
            spoof = red(" ⚠SPOOF") if pkt.spoofed else ""
            src   = f"{pkt.src_ip}({pkt.src_mac[-5:]})"
            dst   = f"{pkt.dst_ip}({pkt.dst_mac[-5:]})"
            pay   = pkt.payload[:28] + "…" if len(pkt.payload) > 28 else pkt.payload
            print(f"  {dim(str(i)):<4} {dim(pkt.ts):<14} "
                  f"{col}{pkt.ptype:<14}{C.RESET}{spoof}  "
                  f"{src:<22} {dst:<22} {dim(pay)}")
        print()


# ─────────────────────────────────────────────────────────────────────────────
# ARP Protocol Simulation Engine
# ─────────────────────────────────────────────────────────────────────────────

class ARPEngine:
    """
    Simulates the ARP (Address Resolution Protocol) workflow.

    Real ARP in a nutshell
    ─────────────────────
    1. Host A wants to send data to 192.168.1.1 but doesn't know its MAC.
    2. A broadcasts: "Who has 192.168.1.1?  Tell 192.168.0.5"
    3. The owner of 192.168.1.1 unicasts back: "192.168.1.1 is at AA:BB:CC:DD:EE:FF"
    4. Host A caches IP→MAC and sends the frame.

    ARP has NO authentication — any host can reply to any request (or
    send unsolicited "gratuitous ARP" replies), enabling spoofing.
    """

    def __init__(self, network: SimulatedNetwork):
        self.net = network

    # ── Normal ARP flow ──────────────────────────────────────────────────

    def arp_request(self, requester: NetworkDevice, target_ip: str) -> SimPacket:
        """Broadcast an ARP request on behalf of requester."""
        pkt = SimPacket(
            ptype   = "ARP_REQUEST",
            src_ip  = requester.ip,
            dst_ip  = target_ip,
            src_mac = requester.mac,
            dst_mac = "FF:FF:FF:FF:FF:FF",   # broadcast
            payload = f"Who has {target_ip}? Tell {requester.ip}",
        )
        log("ARP REQ", pkt.payload, C.BLUE)
        self.net.broadcast(pkt, sender_name=requester.name)
        return pkt

    def arp_reply(self, responder: NetworkDevice, requester: NetworkDevice) -> SimPacket:
        """Send a legitimate ARP reply from responder to requester."""
        pkt = SimPacket(
            ptype   = "ARP_REPLY",
            src_ip  = responder.ip,
            dst_ip  = requester.ip,
            src_mac = responder.mac,
            dst_mac = requester.mac,
            payload = f"{responder.ip} is at {responder.mac}",
        )
        log("ARP REP", pkt.payload, C.GREEN)
        self.net.send(pkt, requester.name)
        # Requester learns the mapping
        updated = requester.learn_arp(responder.ip, responder.mac)
        if updated:
            log("ARP LRN", f"{requester.name} cached: {responder.ip} → {responder.mac}", C.GREEN)
        return pkt

    def resolve(self, requester: NetworkDevice, target_ip: str) -> str | None:
        """
        Full ARP resolution: request → reply → cache.
        Returns the resolved MAC, or None if the target doesn't exist.
        """
        # Check cache first
        cached = requester.lookup_mac(target_ip)
        if cached:
            log("ARP HIT", f"{requester.name} cache hit: {target_ip} → {cached}", C.DIM)
            return cached
        # Broadcast request
        self.arp_request(requester, target_ip)
        # Find the target device and have it reply
        target = self.net.get_by_ip(target_ip)
        if not target:
            log("ARP ERR", f"No device found for {target_ip}", C.RED)
            return None
        self.arp_reply(target, requester)
        return requester.lookup_mac(target_ip)

    # ── Spoofed ARP (attacker) ────────────────────────────────────────────

    def spoof_arp_reply(
        self,
        attacker : NetworkDevice,
        victim   : NetworkDevice,
        impersonate_ip: str,
    ) -> SimPacket:
        """
        Craft and send a spoofed ARP reply.

        The attacker claims to be impersonate_ip while advertising its own MAC.
        Victim receives this and (unless protected) updates its ARP cache,
        sending future traffic destined for impersonate_ip to the attacker instead.
        """
        pkt = SimPacket(
            ptype   = "ARP_SPOOF",
            src_ip  = impersonate_ip,      # Lying about source IP
            dst_ip  = victim.ip,
            src_mac = attacker.mac,        # Real attacker MAC
            dst_mac = victim.mac,
            payload = (f"[FAKE] {impersonate_ip} is at {attacker.mac}  "
                       f"(sent by {attacker.name})"),
            spoofed = True,
        )
        log("SPOOF", pkt.payload, C.RED)
        self.net.send(pkt, victim.name)

        # Victim processes the reply — will it accept it?
        accepted = victim.learn_arp(impersonate_ip, attacker.mac)
        if accepted:
            log("POISONED", f"{victim.name} ARP cache now maps "
                            f"{impersonate_ip} → {attacker.mac}  ← WRONG!", C.RED)
        else:
            log("BLOCKED",  f"{victim.name} rejected spoof (static ARP protection)", C.GREEN)
        return pkt

    # ── Data transfer simulation ──────────────────────────────────────────

    def send_data(
        self,
        sender   : NetworkDevice,
        dst_ip   : str,
        payload  : str,
        network  : SimulatedNetwork,
        attacker : NetworkDevice | None = None,
    ) -> None:
        """
        Simulate a data packet being sent from sender toward dst_ip.

        If sender's ARP table maps dst_ip to attacker's MAC (poisoned),
        the traffic is intercepted by the attacker who can read/modify it
        before optionally forwarding it.
        """
        # Resolve MAC for destination
        dst_mac = sender.lookup_mac(dst_ip)
        if not dst_mac:
            log("DATA", f"{sender.name} has no ARP entry for {dst_ip} — dropping", C.YELLOW)
            return

        real_dst = network.get_by_ip(dst_ip)
        intercepted = (
            attacker is not None
            and dst_mac == attacker.mac
            and real_dst is not None
            and real_dst.mac != attacker.mac
        )

        ptype = "INTERCEPTED" if intercepted else "DATA"
        colour = C.MAGENTA if intercepted else C.WHITE

        pkt = SimPacket(
            ptype   = ptype,
            src_ip  = sender.ip,
            dst_ip  = dst_ip,
            src_mac = sender.mac,
            dst_mac = dst_mac,
            payload = payload,
            spoofed = intercepted,
        )

        if intercepted:
            log("MITM ⚠", f"Packet from {sender.name} → {dst_ip} "
                           f"INTERCEPTED by {attacker.name}!", C.MAGENTA)
            log("MITM ⚠", f"Attacker reads: \"{payload}\"", C.MAGENTA)
            attacker.receive(pkt)
            # Attacker forwards (transparent relay) — real MITM behaviour
            log("MITM FW", f"{attacker.name} forwards packet to real {dst_ip}", C.YELLOW)
            forward_pkt = SimPacket(
                ptype   = "DATA",
                src_ip  = sender.ip,
                dst_ip  = dst_ip,
                src_mac = attacker.mac,
                dst_mac = real_dst.mac,
                payload = payload + " [forwarded by attacker]",
            )
            network.send(forward_pkt, real_dst.name)
        else:
            log("DATA", f"{sender.name} → {dst_ip}: \"{payload}\"", colour)
            if real_dst:
                network.send(pkt, real_dst.name)


# ─────────────────────────────────────────────────────────────────────────────
# Topology builder
# ─────────────────────────────────────────────────────────────────────────────

def build_default_network() -> tuple[SimulatedNetwork, NetworkDevice, NetworkDevice, NetworkDevice]:
    """
    Create the default simulated network:

        192.168.1.10  (Victim)  ──┐
                                  ├── [Switch] ── 192.168.1.254 (Gateway)
        192.168.1.99  (Attacker)──┘

    Returns (network, victim, gateway, attacker).
    """
    net = SimulatedNetwork()

    victim   = NetworkDevice("Victim",   "192.168.1.10",  "AA:BB:CC:11:22:33", role="victim")
    gateway  = NetworkDevice("Gateway",  "192.168.1.254", "DE:AD:BE:EF:00:01", role="gateway")
    attacker = NetworkDevice("Attacker", "192.168.1.99",  "CA:FE:BA:BE:00:FF", role="attacker")

    net.add_device(victim)
    net.add_device(gateway)
    net.add_device(attacker)

    return net, victim, gateway, attacker


# ─────────────────────────────────────────────────────────────────────────────
# ASCII Network Diagram
# ─────────────────────────────────────────────────────────────────────────────

def print_topology(victim: NetworkDevice, gateway: NetworkDevice, attacker: NetworkDevice,
                   poisoned: bool = False) -> None:
    """Render an ASCII diagram of the current network state."""
    section("Network Topology")

    v_mac = victim.lookup_mac(gateway.ip) or "(unknown)"
    a_mac = victim.lookup_mac(attacker.ip) or "(unknown)"

    arrow_v_gw = red("▶ ATTACKER ◀") if poisoned else green("─────────────")
    poison_note = red("  ← POISONED (thinks GW is attacker)") if poisoned else ""

    print(f"""
  {cyan('╔══════════════════════════════════════════════════════════╗')}
  {cyan('║')}  {victim.role_icon()}  VICTIM                                          {cyan('║')}
  {cyan('║')}  IP  : {green(victim.ip):<16}  MAC: {yellow(victim.mac)}   {cyan('║')}
  {cyan('║')}  ARP : GW({gateway.ip}) → {yellow(v_mac)}{poison_note}
  {cyan('╠══════════════════════════════════════════════════════════╣')}
  {cyan('║')}                                                          {cyan('║')}
  {cyan('║')}  Traffic path to Gateway:                               {cyan('║')}
  {cyan('║')}  Victim {arrow_v_gw}  {gateway.role_icon()} Gateway  {cyan('║')}
  {cyan('║')}                                                          {cyan('║')}
  {cyan('╠══════════════════════════════════════════════════════════╣')}
  {cyan('║')}  {gateway.role_icon()}  GATEWAY                                         {cyan('║')}
  {cyan('║')}  IP  : {green(gateway.ip):<16}  MAC: {yellow(gateway.mac)} {cyan('║')}
  {cyan('╠══════════════════════════════════════════════════════════╣')}
  {cyan('║')}  {attacker.role_icon()}  ATTACKER                                        {cyan('║')}
  {cyan('║')}  IP  : {red(attacker.ip):<16}  MAC: {red(attacker.mac)} {cyan('║')}
  {cyan('╚══════════════════════════════════════════════════════════╝')}
""")


# ─────────────────────────────────────────────────────────────────────────────
# Concept explainer screens
# ─────────────────────────────────────────────────────────────────────────────

def explain_arp() -> None:
    banner("CONCEPT: What is ARP?", C.CYAN)
    text = textwrap.dedent(f"""
    {bold('ARP — Address Resolution Protocol')}  (RFC 826, 1982)

    Every device on a LAN has two addresses:
      • {cyan('IP address')}  — Layer 3, logical  (e.g. 192.168.1.10)
      • {yellow('MAC address')} — Layer 2, physical (e.g. AA:BB:CC:11:22:33)

    Ethernet frames carry data between MACs, not IPs.
    ARP bridges the gap:

    {blue('  [Host A]')} wants to send to IP 192.168.1.254
         │
         ▼
    {blue('  ARP REQUEST (broadcast)')}
    "Who has 192.168.1.254?  Tell 192.168.1.10"
         │  (sent to FF:FF:FF:FF:FF:FF — everyone hears this)
         ▼
    {green('  ARP REPLY (unicast)')}
    "192.168.1.254 is at DE:AD:BE:EF:00:01"
         │
         ▼
    {green('  [Host A] caches')} 192.168.1.254 → DE:AD:BE:EF:00:01
    and can now send frames directly.

    {bold(yellow('The critical weakness:'))}
    ARP has {red('NO AUTHENTICATION')}. Any host can send an ARP reply
    claiming any IP, and most operating systems will accept it.
    """)
    print(text)
    pause()


def explain_spoofing() -> None:
    banner("CONCEPT: ARP Spoofing / MITM", C.RED)
    text = textwrap.dedent(f"""
    {bold(red('ARP Spoofing (ARP Poisoning)'))}

    The attacker exploits the lack of ARP authentication to send
    {red('unsolicited (gratuitous) ARP replies')} to victims, lying about
    which MAC address owns the gateway IP.

    Attack flow:

    1.  Attacker sends to Victim:
        {red('FAKE: "192.168.1.254 (Gateway) is at CA:FE:BA:BE:00:FF"')}
        Victim's ARP cache is now {red('poisoned')}.

    2.  Attacker sends to Gateway:
        {red('FAKE: "192.168.1.10 (Victim) is at CA:FE:BA:BE:00:FF"')}
        Gateway's ARP cache is also poisoned.

    3.  {bold('Man-in-the-Middle established:')}

         Victim ──▶ Attacker ──▶ Gateway
                        │
                   {magenta('reads / modifies')}
                   {magenta('data silently')}

    {bold(yellow('Why it is dangerous:'))}
    • Credential theft (HTTP logins, API keys)
    • Session hijacking
    • SSL stripping (downgrade HTTPS to HTTP)
    • DNS spoofing over poisoned traffic
    • Ransomware delivery via modified downloads
    """)
    print(text)
    pause()


def explain_defenses() -> None:
    banner("CONCEPT: Defenses Against ARP Spoofing", C.GREEN)
    text = textwrap.dedent(f"""
    {bold(green('Defense Mechanisms'))}

    {green('1. Static ARP Entries')}
       Manually pin IP→MAC mappings in the OS ARP cache.
       Spoofed replies cannot overwrite them.
       • Command (Linux): {cyan('arp -s 192.168.1.254 DE:AD:BE:EF:00:01')}
       • Limitation: doesn't scale on large networks.

    {green('2. Dynamic ARP Inspection (DAI)')}
       Managed switches validate ARP packets against a trusted
       DHCP snooping table. Untrusted ports drop invalid ARPs.
       This is the enterprise-grade solution.

    {green('3. XArp / ArpWatch')}
       Software that monitors ARP traffic and alerts on
       MAC address changes for existing IP entries.

    {green('4. VPNs and Encryption (TLS/HTTPS)')}
       Even if traffic is intercepted, end-to-end encryption
       means the attacker sees only ciphertext — useless without keys.

    {green('5. IPv6 + SEND (Secure Neighbour Discovery)')}
       IPv6 replaces ARP with NDP; SEND adds cryptographic
       authentication to neighbour discovery messages.

    {green('6. 802.1X Port-based Authentication')}
       Only authenticated devices may connect; rogue devices
       cannot participate in the network to begin with.
    """)
    print(text)
    pause()


# ─────────────────────────────────────────────────────────────────────────────
# Simulation steps (the guided lab)
# ─────────────────────────────────────────────────────────────────────────────

def step_normal_comms(
    net     : SimulatedNetwork,
    arp     : ARPEngine,
    victim  : NetworkDevice,
    gateway : NetworkDevice,
    attacker: NetworkDevice,
) -> None:
    """Step 1 — Demonstrate normal, legitimate ARP and data exchange."""
    banner("STEP 1 — Normal Network Communication", C.GREEN)
    print(textwrap.dedent(f"""
    {bold('What we are doing:')}
    The Victim needs to send data to the Internet via the Gateway.
    It first performs an {cyan('ARP resolution')} to discover the Gateway's MAC,
    then transmits a simulated data packet.

    Devices on this network:
      {victim.role_icon()}  {bold(victim.name):<10}  IP: {green(victim.ip):<18}  MAC: {yellow(victim.mac)}
      {gateway.role_icon()}  {bold(gateway.name):<10}  IP: {green(gateway.ip):<18}  MAC: {yellow(gateway.mac)}
      {attacker.role_icon()}  {bold(attacker.name):<10}  IP: {red(attacker.ip):<18}  MAC: {red(attacker.mac)}
    """))
    pause("  Press Enter to start normal ARP resolution…")

    section("ARP Resolution: Victim → Gateway")
    arp.resolve(victim, gateway.ip)

    section("ARP Resolution: Gateway → Victim (reverse path)")
    arp.resolve(gateway, victim.ip)

    section("ARP Tables (after normal resolution)")
    net.print_arp_table(victim)
    net.print_arp_table(gateway)

    print_topology(victim, gateway, attacker, poisoned=False)

    pause("  Press Enter to send data…")
    section("Normal Data Transfer: Victim → Gateway")
    arp.send_data(victim, gateway.ip, "GET /index.html HTTP/1.1", net)
    arp.send_data(victim, gateway.ip, "Authorization: Bearer token_abc123", net)

    section("Packet Capture (so far)")
    net.print_packet_log()
    pause()


def step_arp_spoof(
    net     : SimulatedNetwork,
    arp     : ARPEngine,
    victim  : NetworkDevice,
    gateway : NetworkDevice,
    attacker: NetworkDevice,
) -> dict:
    """Step 2 — Perform the ARP spoofing attack."""
    banner("STEP 2 — ARP Spoofing Attack", C.RED)
    print(textwrap.dedent(f"""
    {bold(red('Attack scenario:'))}
    The Attacker ({red(attacker.ip)} / {red(attacker.mac)}) is on the same LAN segment.
    It will now send {red('two spoofed ARP replies')}:

      1. Tell Victim   → "Gateway ({gateway.ip}) is at {red(attacker.mac)}"
      2. Tell Gateway  → "Victim  ({victim.ip}) is at {red(attacker.mac)}"

    Once both caches are poisoned, {bold(red('all traffic flows through the attacker'))}.
    This is the classic {bold('Man-in-the-Middle (MITM)')} attack.
    """))
    pause("  Press Enter to execute the spoofing attack…")

    before = net.snapshot_arp_tables()

    section("Spoofing Victim — Poisoning victim's ARP cache")
    arp.spoof_arp_reply(attacker, victim, gateway.ip)

    print()
    section("Spoofing Gateway — Poisoning gateway's ARP cache")
    arp.spoof_arp_reply(attacker, gateway, victim.ip)

    after = net.snapshot_arp_tables()

    section("ARP Cache Comparison: Before vs After Attack")
    _print_arp_diff(before, after, net, victim, gateway, attacker)

    print_topology(victim, gateway, attacker, poisoned=True)
    pause()
    return {"before": before, "after": after}


def step_intercept(
    net     : SimulatedNetwork,
    arp     : ARPEngine,
    victim  : NetworkDevice,
    gateway : NetworkDevice,
    attacker: NetworkDevice,
) -> None:
    """Step 3 — Show data interception after poisoning."""
    banner("STEP 3 — Traffic Interception (MITM in action)", C.MAGENTA)
    print(textwrap.dedent(f"""
    {bold('What happens now:')}
    The Victim believes the Gateway is at {red(attacker.mac)} (poisoned cache).
    Any packet it sends "to the Gateway" actually lands on the Attacker first.
    The Attacker reads it, then forwards it — {bold('victim and gateway notice nothing')}.
    """))
    pause("  Press Enter to send traffic through the poisoned network…")

    section("Intercepted Traffic: Victim → (intended) Gateway")
    arp.send_data(victim, gateway.ip, "POST /login  user=alice&pass=s3cr3t!", net, attacker=attacker)
    arp.send_data(victim, gateway.ip, "Cookie: session_id=ABCDEF012345",      net, attacker=attacker)
    arp.send_data(victim, gateway.ip, "GET /api/transfer?amount=5000",         net, attacker=attacker)

    section("Attacker's Inbox (captured packets)")
    if attacker.inbox:
        print(f"  {'#':<4} {'Type':<14} {'Payload'}")
        print(f"  {'─'*4} {'─'*14} {'─'*40}")
        for i, pkt in enumerate(attacker.inbox, 1):
            print(f"  {dim(str(i)):<4} {red(pkt.ptype):<14} {magenta(pkt.payload)}")
    else:
        print(f"  {dim('(no packets captured by attacker)')}")

    print()
    section("Full Packet Capture Log")
    net.print_packet_log(last_n=12)
    pause()


def step_defense(
    net     : SimulatedNetwork,
    arp     : ARPEngine,
    victim  : NetworkDevice,
    gateway : NetworkDevice,
    attacker: NetworkDevice,
) -> None:
    """Step 4 — Enable static ARP protection and re-attempt the attack."""
    banner("STEP 4 — Defense: Static ARP Entries", C.GREEN)
    print(textwrap.dedent(f"""
    {bold(green('Protection mechanism: Static ARP'))}

    We will now {green('reset and re-arm')} the simulation with static ARP entries
    on the Victim's machine, pinning the real Gateway MAC.

    Static ARP entries {green('cannot be overwritten')} by unsolicited ARP replies.
    Even if the Attacker sends spoofed packets, the Victim will reject them.
    """))
    pause("  Press Enter to apply static ARP protection and retry attack…")

    # Reset victim ARP cache and apply static entry
    victim.arp_table   = {}
    victim.static_arp  = set()
    attacker.inbox     = []
    net.packet_log     = []

    section("Applying static ARP entry on Victim")
    victim.set_static_arp(gateway.ip, gateway.mac)
    log("STATIC", f"Pinned: {gateway.ip} → {gateway.mac}  (cannot be overwritten)", C.GREEN)

    section("Re-running ARP resolution (static entry used)")
    # Victim already has static entry — no broadcast needed
    mac = victim.lookup_mac(gateway.ip)
    log("ARP HIT", f"Static cache hit: {gateway.ip} → {mac}", C.GREEN)

    section("Attacker attempts to poison Victim again")
    arp.spoof_arp_reply(attacker, victim, gateway.ip)

    section("ARP Table After Spoof Attempt")
    net.print_arp_table(victim)

    section("Data Transfer After Protection Applied")
    arp.send_data(victim, gateway.ip, "GET /index.html HTTP/1.1", net, attacker=attacker)

    section("Attacker's Inbox (should be empty this time)")
    if attacker.inbox:
        print(f"  {red('Attack partially succeeded — review your setup.')}")
    else:
        print(f"  {green('  ✔  Attacker captured nothing. Static ARP protection worked!')}\n")

    net.print_packet_log()
    pause()


# ─────────────────────────────────────────────────────────────────────────────
# Helper: ARP diff table
# ─────────────────────────────────────────────────────────────────────────────

def _print_arp_diff(
    before  : dict,
    after   : dict,
    net     : SimulatedNetwork,
    victim  : NetworkDevice,
    gateway : NetworkDevice,
    attacker: NetworkDevice,
) -> None:
    """Print a side-by-side diff of ARP tables before and after the attack."""
    print(f"\n  {'Device':<12} {'IP':<18} {'MAC  (before)':<26} {'MAC  (after)':<26} {'Changed?'}")
    print(f"  {'─'*12} {'─'*18} {'─'*26} {'─'*26} {'─'*10}")
    for dev_name, b_table in before.items():
        a_table = after.get(dev_name, {})
        all_ips = set(b_table) | set(a_table)
        for ip in sorted(all_ips):
            b_mac = b_table.get(ip, "(none)")
            a_mac = a_table.get(ip, "(none)")
            changed = b_mac != a_mac
            change_str = red("⚠  CHANGED") if changed else green("  unchanged")
            a_display  = red(a_mac) if changed else a_mac
            print(f"  {dev_name:<12} {ip:<18} {b_mac:<26} {a_display:<26} {change_str}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Full guided scenario (runs all steps in sequence)
# ─────────────────────────────────────────────────────────────────────────────

def run_full_scenario(
    net     : SimulatedNetwork,
    victim  : NetworkDevice,
    gateway : NetworkDevice,
    attacker: NetworkDevice,
) -> None:
    arp = ARPEngine(net)
    step_normal_comms(net, arp, victim, gateway, attacker)
    step_arp_spoof   (net, arp, victim, gateway, attacker)
    step_intercept   (net, arp, victim, gateway, attacker)
    step_defense     (net, arp, victim, gateway, attacker)
    banner("Simulation Complete", C.GREEN)
    print(f"""
  {bold(green('All four steps finished.'))}

  You have witnessed:
    ✔  Normal ARP resolution and data flow
    ✔  ARP cache poisoning by an attacker
    ✔  Silent traffic interception (MITM)
    ✔  Static ARP as a countermeasure

  {bold(yellow('Remember:'))} Performing ARP spoofing on real networks
  without explicit written permission is {bold(red('illegal'))} in most
  jurisdictions and may result in criminal prosecution.
""")
    pause("  Press Enter to return to main menu…")


# ─────────────────────────────────────────────────────────────────────────────
# Interactive menu
# ─────────────────────────────────────────────────────────────────────────────

MENU = f"""
  {bold('─── Main Menu ───────────────────────────────────────────────')}

   {cyan('1')}  {bold('Run Full Guided Scenario')}   (all 4 steps, recommended first)
   {cyan('2')}  Step 1 — Normal Communication
   {cyan('3')}  Step 2 — ARP Spoofing Attack
   {cyan('4')}  Step 3 — Traffic Interception (MITM)
   {cyan('5')}  Step 4 — Static ARP Defense
   {cyan('─' * 50)}
   {yellow('6')}  What is ARP?  (concept explainer)
   {yellow('7')}  How ARP Spoofing works  (concept explainer)
   {yellow('8')}  Defense mechanisms  (concept explainer)
   {cyan('─' * 50)}
   {cyan('9')}  Print current ARP tables
   {cyan('0')}  Print packet capture log
   {cyan('R')}  {red('Reset simulation')}
   {cyan('Q')}  Quit

  {bold('─────────────────────────────────────────────────────────────')}
  Choice: """


def main() -> None:
    banner("NETWORK SPOOFING EDUCATIONAL SIMULATOR", C.CYAN)
    print(textwrap.dedent(f"""
    {bold('Welcome to the ARP Spoofing / MITM Educational Lab')}

    This simulator demonstrates how ARP spoofing attacks work using
    {green('pure Python in-memory objects')} — no real packets are ever sent.

    {red(bold('⚠  WARNING:'))} ARP spoofing real networks without permission
       is {bold('ILLEGAL')}. This tool is for learning purposes only.

    You will simulate a small LAN with three devices:
      {cyan('💻 Victim')}   — 192.168.1.10   AA:BB:CC:11:22:33
      {cyan('🌐 Gateway')}  — 192.168.1.254  DE:AD:BE:EF:00:01
      {cyan('👾 Attacker')} — 192.168.1.99   CA:FE:BA:BE:00:FF
    """))
    pause("  Press Enter to continue to the main menu…")

    net, victim, gateway, attacker = build_default_network()
    arp = ARPEngine(net)

    while True:
        print(MENU, end="")
        choice = input().strip().upper()

        if choice == "1":
            # Reset before full run
            net, victim, gateway, attacker = build_default_network()
            arp = ARPEngine(net)
            run_full_scenario(net, victim, gateway, attacker)

        elif choice == "2":
            step_normal_comms(net, arp, victim, gateway, attacker)

        elif choice == "3":
            step_arp_spoof(net, arp, victim, gateway, attacker)

        elif choice == "4":
            step_intercept(net, arp, victim, gateway, attacker)

        elif choice == "5":
            step_defense(net, arp, victim, gateway, attacker)

        elif choice == "6":
            explain_arp()

        elif choice == "7":
            explain_spoofing()

        elif choice == "8":
            explain_defenses()

        elif choice == "9":
            net.print_all_arp_tables()

        elif choice == "0":
            net.print_packet_log()
            pause()

        elif choice == "R":
            net, victim, gateway, attacker = build_default_network()
            arp = ARPEngine(net)
            log("RESET", "Simulation state cleared — fresh network instantiated.", C.YELLOW)
            pause()

        elif choice == "Q":
            banner("Goodbye", C.CYAN)
            print(f"  {dim('Stay curious. Stay ethical.')}\n")
            break

        else:
            print(f"  {yellow('Unknown option. Please enter a number or letter from the menu.')}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()