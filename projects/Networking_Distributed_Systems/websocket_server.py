"""
websocket_server.py
===================
A from-scratch WebSocket server (RFC 6455) with:
  • Multi-client support via threading
  • WebSocketClient / WebSocketMessage / WebSocketServer / ConnectionManager
  • Broadcast, private messaging (@username), and /commands
  • Built-in terminal dashboard (no curses, plain ANSI)
  • Zero third-party dependencies

Usage
-----
    python websocket_server.py               # default port 8765
    python websocket_server.py --port 9000

Connect with any WS client, e.g.:
    wscat  -c ws://localhost:8765
    websocat ws://localhost:8765
    Or open the bundled browser test page printed on startup.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import re
import socket
import struct
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Deque, Dict, List, Optional, Set


# ═══════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ws")


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

WS_MAGIC  = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
FRAME_FIN = 0x80
OP_TEXT   = 0x01
OP_BINARY = 0x02
OP_CLOSE  = 0x08
OP_PING   = 0x09
OP_PONG   = 0x0A
MAX_MSG   = 1024 * 64   # 64 KB per message
RECV_BUF  = 4096


# ═══════════════════════════════════════════════════════════════
# Enumerations
# ═══════════════════════════════════════════════════════════════

class ClientState(Enum):
    CONNECTING   = auto()
    CONNECTED    = auto()
    DISCONNECTED = auto()


# ═══════════════════════════════════════════════════════════════
# WebSocketMessage
# ═══════════════════════════════════════════════════════════════

class MessageType(Enum):
    CHAT      = "chat"
    SYSTEM    = "system"
    PRIVATE   = "private"
    COMMAND   = "command"
    ERROR     = "error"


@dataclass
class WebSocketMessage:
    sender:    str
    content:   str
    msg_type:  MessageType = MessageType.CHAT
    recipient: str         = ""          # filled for private messages
    timestamp: datetime    = field(default_factory=datetime.now)
    msg_id:    str         = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_json(self) -> str:
        return json.dumps({
            "id":        self.msg_id,
            "type":      self.msg_type.value,
            "sender":    self.sender,
            "recipient": self.recipient,
            "content":   self.content,
            "timestamp": self.timestamp.isoformat(timespec="milliseconds"),
        })

    @classmethod
    def system(cls, content: str) -> "WebSocketMessage":
        return cls(sender="SERVER", content=content,
                   msg_type=MessageType.SYSTEM)

    @classmethod
    def error(cls, content: str) -> "WebSocketMessage":
        return cls(sender="SERVER", content=content,
                   msg_type=MessageType.ERROR)

    def __str__(self) -> str:
        ts  = self.timestamp.strftime("%H:%M:%S")
        tag = f"[{self.msg_type.value.upper()}]"
        if self.msg_type == MessageType.PRIVATE:
            return f"{ts} {tag} {self.sender} → {self.recipient}: {self.content}"
        return f"{ts} {tag} {self.sender}: {self.content}"


# ═══════════════════════════════════════════════════════════════
# WebSocket frame codec
# ═══════════════════════════════════════════════════════════════

class FrameDecodeError(Exception):
    pass


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes or raise ConnectionError."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed mid-receive.")
        buf += chunk
    return buf


def decode_frame(sock: socket.socket) -> tuple[int, bytes]:
    """
    Parse one WebSocket frame from *sock*.
    Returns (opcode, payload_bytes).
    Raises FrameDecodeError / ConnectionError on problems.
    """
    header = _recv_exact(sock, 2)
    fin    = (header[0] & 0x80) != 0
    opcode = header[0] & 0x0F
    masked = (header[1] & 0x80) != 0
    length = header[1] & 0x7F

    if length == 126:
        length = struct.unpack("!H", _recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact(sock, 8))[0]

    if length > MAX_MSG:
        raise FrameDecodeError(f"Frame too large: {length} bytes.")

    mask_key = _recv_exact(sock, 4) if masked else b""
    payload  = bytearray(_recv_exact(sock, length))

    if masked:
        for i in range(length):
            payload[i] ^= mask_key[i % 4]

    return opcode, bytes(payload)


def encode_frame(opcode: int, payload: bytes) -> bytes:
    """Build a server-side (unmasked) WebSocket frame."""
    length = len(payload)
    header = bytearray([FRAME_FIN | opcode])
    if length < 126:
        header.append(length)
    elif length < 65536:
        header.append(126)
        header += struct.pack("!H", length)
    else:
        header.append(127)
        header += struct.pack("!Q", length)
    return bytes(header) + payload


# ═══════════════════════════════════════════════════════════════
# WebSocketClient
# ═══════════════════════════════════════════════════════════════

class WebSocketClient:
    """
    Represents one connected browser/client.

    Attributes
    ----------
    client_id   : short hex UUID
    connection  : raw TCP socket
    address     : (host, port) tuple
    username    : display name (set during handshake or via /nick)
    state       : ClientState
    joined_at   : datetime of connection
    msg_count   : number of messages sent by this client
    """

    def __init__(self, connection: socket.socket, address: tuple) -> None:
        self.client_id  = uuid.uuid4().hex[:6]
        self.connection = connection
        self.address    = address
        self.username   = f"user_{self.client_id}"
        self.state      = ClientState.CONNECTING
        self.joined_at  = datetime.now()
        self.msg_count  = 0
        self._send_lock = threading.Lock()

    # ── transport ─────────────────────────────────────────────

    def send(self, message: WebSocketMessage) -> bool:
        """Encode and send a message frame.  Returns False on error."""
        if self.state != ClientState.CONNECTED:
            return False
        frame = encode_frame(OP_TEXT, message.to_json().encode())
        with self._send_lock:
            try:
                self.connection.sendall(frame)
                return True
            except OSError:
                return False

    def send_raw(self, opcode: int, payload: bytes = b"") -> bool:
        frame = encode_frame(opcode, payload)
        with self._send_lock:
            try:
                self.connection.sendall(frame)
                return True
            except OSError:
                return False

    def close(self, code: int = 1000, reason: str = "Normal closure") -> None:
        try:
            payload = struct.pack("!H", code) + reason.encode()
            self.send_raw(OP_CLOSE, payload)
        except Exception:
            pass
        finally:
            self.state = ClientState.DISCONNECTED
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.connection.close()
            except Exception:
                pass

    # ── info ──────────────────────────────────────────────────

    def uptime(self) -> str:
        secs = int((datetime.now() - self.joined_at).total_seconds())
        h, r = divmod(secs, 3600)
        m, s = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def __repr__(self) -> str:
        return (f"<WebSocketClient id={self.client_id} "
                f"nick={self.username} state={self.state.name}>")


# ═══════════════════════════════════════════════════════════════
# ConnectionManager
# ═══════════════════════════════════════════════════════════════

class ConnectionManager:
    """
    Thread-safe registry of all live WebSocketClient instances.

    Responsibilities
    ----------------
    • Track connected/disconnected clients
    • Enforce unique usernames
    • Deliver broadcast and unicast messages
    • Maintain a scrolling message log
    """

    def __init__(self, log_size: int = 200) -> None:
        self._clients:   Dict[str, WebSocketClient] = {}
        self._lock       = threading.RLock()
        self._msg_log:   Deque[WebSocketMessage] = deque(maxlen=log_size)
        self._msg_count  = 0

    # ── registration ──────────────────────────────────────────

    def register(self, client: WebSocketClient) -> None:
        with self._lock:
            self._clients[client.client_id] = client
            client.state = ClientState.CONNECTED
        log.info("+ Connected  %s  (%s:%s)",
                 client.username, *client.address)

    def unregister(self, client: WebSocketClient) -> None:
        with self._lock:
            self._clients.pop(client.client_id, None)
        client.state = ClientState.DISCONNECTED
        log.info("− Disconnected  %s", client.username)

    # ── username management ───────────────────────────────────

    def set_username(self, client: WebSocketClient, new_name: str) -> tuple[bool, str]:
        """
        Attempt to rename *client* to *new_name*.
        Returns (success, message).
        """
        new_name = new_name.strip()
        if not re.fullmatch(r"[A-Za-z0-9_\-]{2,20}", new_name):
            return False, ("Username must be 2-20 chars, "
                           "letters/digits/underscore/dash only.")
        with self._lock:
            taken = any(
                c.username == new_name and c.client_id != client.client_id
                for c in self._clients.values()
            )
            if taken:
                return False, f"Username '{new_name}' is already taken."
            old = client.username
            client.username = new_name
        return True, old

    # ── lookup ────────────────────────────────────────────────

    def find_by_username(self, username: str) -> Optional[WebSocketClient]:
        with self._lock:
            for c in self._clients.values():
                if c.username == username:
                    return c
        return None

    def all_clients(self) -> List[WebSocketClient]:
        with self._lock:
            return list(self._clients.values())

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._clients)

    # ── messaging ─────────────────────────────────────────────

    def broadcast(self, message: WebSocketMessage,
                  exclude: Optional[Set[str]] = None) -> int:
        """Send to all connected clients.  Returns delivery count."""
        exclude = exclude or set()
        sent = 0
        self._log(message)
        for client in self.all_clients():
            if client.client_id in exclude:
                continue
            if client.send(message):
                sent += 1
        return sent

    def send_to(self, client: WebSocketClient,
                message: WebSocketMessage) -> bool:
        self._log(message)
        return client.send(message)

    def _log(self, message: WebSocketMessage) -> None:
        self._msg_log.append(message)
        self._msg_count += 1

    def message_log(self) -> List[WebSocketMessage]:
        return list(self._msg_log)

    @property
    def total_messages(self) -> int:
        return self._msg_count


# ═══════════════════════════════════════════════════════════════
# Command handler
# ═══════════════════════════════════════════════════════════════

class CommandHandler:
    """
    Parses and executes /commands sent by clients.

    Supported commands
    ------------------
    /nick <name>        — change display name
    /who                — list connected users
    /pm <user> <msg>    — private message
    /help               — command list
    /quit               — disconnect
    """

    def __init__(self, manager: ConnectionManager) -> None:
        self._mgr = manager

    def handle(self, raw: str, client: WebSocketClient
               ) -> Optional[WebSocketMessage]:
        """
        Returns a WebSocketMessage to send back to *client*, or None
        if the command caused a broadcast (handled internally).
        """
        parts = raw.strip().split(None, 2)
        cmd   = parts[0].lower() if parts else ""

        if cmd == "/nick":
            return self._cmd_nick(parts, client)
        if cmd == "/who":
            return self._cmd_who(client)
        if cmd == "/pm":
            return self._cmd_pm(parts, client)
        if cmd == "/help":
            return self._cmd_help(client)
        if cmd == "/quit":
            return self._cmd_quit(client)
        return WebSocketMessage.error(f"Unknown command '{cmd}'. Type /help.")

    # ── individual commands ───────────────────────────────────

    def _cmd_nick(self, parts: List[str], client: WebSocketClient
                  ) -> WebSocketMessage:
        if len(parts) < 2:
            return WebSocketMessage.error("Usage: /nick <new_username>")
        ok, info = self._mgr.set_username(client, parts[1])
        if ok:
            old_name = info
            notice = WebSocketMessage.system(
                f"'{old_name}' is now known as '{client.username}'."
            )
            self._mgr.broadcast(notice)
            return None                    # broadcast already sent
        return WebSocketMessage.error(info)

    def _cmd_who(self, client: WebSocketClient) -> WebSocketMessage:
        names = [c.username for c in self._mgr.all_clients()]
        body  = "Online (%d): %s" % (len(names), ", ".join(names))
        return WebSocketMessage.system(body)

    def _cmd_pm(self, parts: List[str], client: WebSocketClient
                ) -> Optional[WebSocketMessage]:
        if len(parts) < 3:
            return WebSocketMessage.error("Usage: /pm <username> <message>")
        target_name, text = parts[1], parts[2]
        target = self._mgr.find_by_username(target_name)
        if target is None:
            return WebSocketMessage.error(
                f"User '{target_name}' not found.")
        pm = WebSocketMessage(
            sender=client.username, content=text,
            msg_type=MessageType.PRIVATE, recipient=target_name,
        )
        self._mgr.send_to(target, pm)
        # echo to sender
        echo = WebSocketMessage(
            sender=client.username, content=f"[PM → {target_name}] {text}",
            msg_type=MessageType.PRIVATE, recipient=target_name,
        )
        self._mgr.send_to(client, echo)
        return None

    def _cmd_help(self, _client: WebSocketClient) -> WebSocketMessage:
        lines = [
            "/nick <name>      — change your display name",
            "/who              — list online users",
            "/pm <user> <msg>  — send a private message",
            "/help             — show this help",
            "/quit             — disconnect",
        ]
        return WebSocketMessage.system("\n".join(lines))

    def _cmd_quit(self, client: WebSocketClient) -> WebSocketMessage:
        client.close(1000, "Client requested disconnect.")
        return None


# ═══════════════════════════════════════════════════════════════
# HTTP upgrade / handshake
# ═══════════════════════════════════════════════════════════════

class HandshakeError(Exception):
    pass


def perform_handshake(conn: socket.socket) -> str:
    """
    Read the HTTP upgrade request, validate it, and send the 101
    Switching Protocols response.
    Returns the requested path (e.g. '/').
    Raises HandshakeError on invalid requests.
    """
    raw = b""
    while b"\r\n\r\n" not in raw:
        chunk = conn.recv(RECV_BUF)
        if not chunk:
            raise HandshakeError("Client disconnected during handshake.")
        raw += chunk
        if len(raw) > 8192:
            raise HandshakeError("HTTP headers too large.")

    headers_raw, _, _ = raw.partition(b"\r\n\r\n")
    lines   = headers_raw.decode(errors="replace").split("\r\n")
    headers = {}
    path    = "/"

    if lines:
        m = re.match(r"GET (\S+) HTTP/1\.[01]", lines[0])
        if not m:
            raise HandshakeError("Not a valid HTTP GET request.")
        path = m.group(1)

    for line in lines[1:]:
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()

    upgrade = headers.get("upgrade", "").lower()
    if upgrade != "websocket":
        raise HandshakeError(f"Unexpected Upgrade header: '{upgrade}'.")

    ws_key = headers.get("sec-websocket-key", "")
    if not ws_key:
        raise HandshakeError("Missing Sec-WebSocket-Key.")

    accept = base64.b64encode(
        hashlib.sha1((ws_key + WS_MAGIC).encode()).digest()
    ).decode()

    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        "\r\n"
    )
    conn.sendall(response.encode())
    return path


# ═══════════════════════════════════════════════════════════════
# WebSocketServer
# ═══════════════════════════════════════════════════════════════

class WebSocketServer:
    """
    Listens for TCP connections, performs the WS handshake, and
    spawns a dedicated thread for each connected client.

    Parameters
    ----------
    host        : bind address  (default "0.0.0.0")
    port        : TCP port      (default 8765)
    backlog     : listen backlog
    """

    def __init__(
        self,
        host:    str = "0.0.0.0",
        port:    int = 8765,
        backlog: int = 10,
    ) -> None:
        self.host    = host
        self.port    = port
        self._backlog = backlog
        self._mgr    = ConnectionManager()
        self._cmd    = CommandHandler(self._mgr)
        self._sock:  Optional[socket.socket] = None
        self._running = threading.Event()
        self._threads: List[threading.Thread] = []

    # ── properties ────────────────────────────────────────────

    @property
    def manager(self) -> ConnectionManager:
        return self._mgr

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    # ── lifecycle ─────────────────────────────────────────────

    def start(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(self._backlog)
        self._sock.settimeout(1.0)          # allows clean shutdown checks
        self._running.set()
        log.info("WebSocket server listening on ws://%s:%d", self.host, self.port)
        self._accept_loop()

    def stop(self) -> None:
        self._running.clear()
        # Disconnect all clients
        for client in self._mgr.all_clients():
            client.close(1001, "Server shutting down.")
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        for t in self._threads:
            t.join(timeout=2)
        log.info("Server stopped.")

    # ── accept loop ───────────────────────────────────────────

    def _accept_loop(self) -> None:
        while self._running.is_set():
            try:
                conn, addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(
                target=self._client_session,
                args=(conn, addr),
                daemon=True,
            )
            self._threads.append(t)
            t.start()

    # ── per-client session ────────────────────────────────────

    def _client_session(self, conn: socket.socket, addr: tuple) -> None:
        client = WebSocketClient(conn, addr)
        try:
            perform_handshake(conn)
        except HandshakeError as exc:
            log.warning("Handshake failed %s: %s", addr, exc)
            conn.close()
            return

        self._mgr.register(client)
        welcome = WebSocketMessage.system(
            f"Welcome! You are '{client.username}'. "
            "Type /help for available commands."
        )
        self._mgr.send_to(client, welcome)
        self._mgr.broadcast(
            WebSocketMessage.system(f"'{client.username}' joined the chat."),
            exclude={client.client_id},
        )

        try:
            self._recv_loop(client)
        finally:
            self._mgr.unregister(client)
            client.close()
            self._mgr.broadcast(
                WebSocketMessage.system(
                    f"'{client.username}' left the chat."
                )
            )

    def _recv_loop(self, client: WebSocketClient) -> None:
        conn = client.connection
        while client.state == ClientState.CONNECTED:
            try:
                opcode, payload = decode_frame(conn)
            except (ConnectionError, OSError):
                break
            except FrameDecodeError as exc:
                log.warning("Bad frame from %s: %s", client.username, exc)
                break

            if opcode == OP_CLOSE:
                client.send_raw(OP_CLOSE, payload)
                break
            if opcode == OP_PING:
                client.send_raw(OP_PONG, payload)
                continue
            if opcode == OP_PONG:
                continue
            if opcode in (OP_TEXT, OP_BINARY):
                text = payload.decode(errors="replace").strip()
                if not text:
                    continue
                self._dispatch(text, client)

    def _dispatch(self, text: str, client: WebSocketClient) -> None:
        """Route a text message: command or broadcast."""
        if text.startswith("/"):
            reply = self._cmd.handle(text, client)
            if reply:
                self._mgr.send_to(client, reply)
        else:
            client.msg_count += 1
            msg = WebSocketMessage(sender=client.username, content=text)
            self._mgr.broadcast(msg)
            log.info("MSG  %s: %s", client.username, text[:80])


# ═══════════════════════════════════════════════════════════════
# Console dashboard
# ═══════════════════════════════════════════════════════════════

C = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "red":     "\033[31m",
    "cyan":    "\033[36m",
    "blue":    "\033[34m",
    "magenta": "\033[35m",
    "grey":    "\033[90m",
}

def cc(text: str, color: str) -> str:
    return f"{C.get(color, '')}{text}{C['reset']}"


BANNER = r"""
  ╔══════════════════════════════════════════════════════╗
  ║          Python WebSocket Server  v1.0              ║
  ╚══════════════════════════════════════════════════════╝"""


MENU = """
  ┌─ Server Console ──────────────────────────────────┐
  │  1  Show connected clients                        │
  │  2  Show message log                              │
  │  3  Broadcast server message                      │
  │  4  Kick a client                                 │
  │  5  Show statistics                               │
  │  6  Stop server & exit                            │
  └───────────────────────────────────────────────────┘"""


def show_clients(server: WebSocketServer) -> None:
    clients = server.manager.all_clients()
    print(f"\n  {cc('Connected Clients', 'bold')}  ({len(clients)} online)")
    print("  " + "─" * 62)
    hdr = f"  {'ID':<8} {'Username':<20} {'Address':<22} {'Uptime':<10} {'Msgs'}"
    print(cc(hdr, "grey"))
    print("  " + "─" * 62)
    if not clients:
        print(cc("  (no clients connected)", "grey"))
    for c in clients:
        addr = f"{c.address[0]}:{c.address[1]}"
        print(f"  {c.client_id:<8} {cc(c.username, 'cyan'):<28} "
              f"{addr:<22} {c.uptime():<10} {c.msg_count}")


def show_log(server: WebSocketServer, limit: int = 20) -> None:
    msgs = server.manager.message_log()[-limit:]
    print(f"\n  {cc('Message Log', 'bold')}  (last {len(msgs)} of "
          f"{server.manager.total_messages} total)")
    print("  " + "─" * 70)
    for m in msgs:
        ts  = m.timestamp.strftime("%H:%M:%S")
        col = {"chat": "reset", "system": "yellow",
               "private": "magenta", "error": "red"}.get(m.msg_type.value, "reset")
        tag = f"[{m.msg_type.value.upper():<7}]"
        print(f"  {cc(ts, 'grey')}  {cc(tag, col)}  "
              f"{cc(m.sender, 'cyan')}: {m.content[:70]}")
    if not msgs:
        print(cc("  (no messages yet)", "grey"))


def show_stats(server: WebSocketServer) -> None:
    mgr = server.manager
    print(f"\n  {cc('Statistics', 'bold')}")
    print("  " + "─" * 40)
    rows = [
        ("Clients online",  cc(str(mgr.count), "green")),
        ("Total messages",  str(mgr.total_messages)),
        ("Server address",  f"ws://{server.host}:{server.port}"),
    ]
    for label, val in rows:
        print(f"  {label:<22} {val}")


def broadcast_from_console(server: WebSocketServer) -> None:
    text = input("  Message to broadcast: ").strip()
    if not text:
        return
    msg  = WebSocketMessage.system(f"[ADMIN] {text}")
    sent = server.manager.broadcast(msg)
    print(cc(f"  ✓ Delivered to {sent} client(s).", "green"))


def kick_client(server: WebSocketServer) -> None:
    clients = server.manager.all_clients()
    if not clients:
        print(cc("  No clients connected.", "yellow"))
        return
    show_clients(server)
    name = input("\n  Enter username or ID to kick: ").strip()
    target = (server.manager.find_by_username(name) or
              next((c for c in clients if c.client_id == name), None))
    if target is None:
        print(cc(f"  ✗ Client '{name}' not found.", "red"))
        return
    server.manager.broadcast(
        WebSocketMessage.system(f"'{target.username}' was kicked by admin.")
    )
    target.close(1008, "Kicked by server admin.")
    server.manager.unregister(target)
    print(cc(f"  ✓ {target.username} kicked.", "green"))


def print_test_page(port: int) -> None:
    """Print a self-contained HTML snippet the user can open locally."""
    html = f"""<!DOCTYPE html><html><head><title>WS Test</title></head><body>
<h2>WebSocket Test Client</h2>
<div id="log" style="height:200px;overflow:auto;border:1px solid #ccc;padding:8px;font-family:monospace"></div>
<input id="msg" placeholder="Type a message…" style="width:300px">
<button onclick="send()">Send</button>
<script>
const ws = new WebSocket("ws://localhost:{port}");
const log = document.getElementById("log");
ws.onmessage = e => {{ const d = JSON.parse(e.data);
  log.innerHTML += `<b>[${{d.type}}]</b> ${{d.sender}}: ${{d.content}}<br>`;
  log.scrollTop = log.scrollHeight; }};
function send() {{
  const m = document.getElementById("msg");
  ws.send(m.value); m.value = ""; }}
</script></body></html>"""
    path = f"/tmp/ws_test_{port}.html"
    try:
        with open(path, "w") as f:
            f.write(html)
        print(cc(f"  Browser test page saved → {path}", "cyan"))
        print(cc(f"  Open it with:  xdg-open {path}  (or drag into browser)", "grey"))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Python WebSocket Server")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765,
                        help="TCP port (default: 8765)")
    args = parser.parse_args()

    print(cc(BANNER, "cyan"))
    print()

    server = WebSocketServer(host=args.host, port=args.port)
    server_thread = threading.Thread(target=server.start, daemon=True,
                                     name="WSAcceptor")
    server_thread.start()
    time.sleep(0.2)   # let the socket bind

    print(cc(f"  ✓ Listening on  ws://127.0.0.1:{args.port}", "green"))
    print(cc(f"  Connect with:   wscat -c ws://localhost:{args.port}", "grey"))
    print(cc(f"  Or install websocat and run: websocat ws://localhost:{args.port}", "grey"))
    print_test_page(args.port)

    while True:
        print(MENU)
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            show_clients(server)
        elif choice == "2":
            show_log(server)
        elif choice == "3":
            broadcast_from_console(server)
        elif choice == "4":
            kick_client(server)
        elif choice == "5":
            show_stats(server)
        elif choice == "6":
            print(cc("\n  Stopping server …", "yellow"))
            server.stop()
            print(cc("  Goodbye!\n", "green"))
            break
        else:
            print(cc("  ✗ Enter 1–6.", "red"))


if __name__ == "__main__":
    main()