"""
distributed_chat_system.py
A simulation of a distributed chat system using Python OOP.
Features: multi-server routing, load balancing, fault tolerance, chat history.
"""

from __future__ import annotations
import uuid
import time
import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict
from enum import Enum, auto


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class ConnectionStatus(Enum):
    ONLINE  = auto()
    OFFLINE = auto()
    AWAY    = auto()


class ServerStatus(Enum):
    ONLINE  = auto()
    OFFLINE = auto()
    OVERLOAD = auto()


class DeliveryStatus(Enum):
    SENT      = "SENT"
    DELIVERED = "DELIVERED"
    FAILED    = "FAILED"
    QUEUED    = "QUEUED"


# ──────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────

class ChatSystemError(Exception):
    """Base exception for the chat system."""

class UserNotFoundError(ChatSystemError):
    pass

class ServerUnavailableError(ChatSystemError):
    pass

class UserAlreadyExistsError(ChatSystemError):
    pass

class InvalidMessageError(ChatSystemError):
    pass


# ──────────────────────────────────────────────
# User
# ──────────────────────────────────────────────

class User:
    """Represents a chat participant."""

    def __init__(self, username: str):
        if not username or not username.strip():
            raise ValueError("Username cannot be empty.")
        self.user_id: str          = str(uuid.uuid4())[:8]
        self.username: str         = username.strip()
        self.connection_status: ConnectionStatus = ConnectionStatus.OFFLINE
        self._server_id: Optional[str] = None
        self._inbox: list[Message] = []

    # ── properties ──────────────────────────────

    @property
    def server_id(self) -> Optional[str]:
        return self._server_id

    @server_id.setter
    def server_id(self, sid: Optional[str]) -> None:
        self._server_id = sid

    @property
    def is_online(self) -> bool:
        return self.connection_status == ConnectionStatus.ONLINE

    # ── public API ──────────────────────────────

    def connect(self, server_id: str) -> None:
        self._server_id        = server_id
        self.connection_status = ConnectionStatus.ONLINE

    def disconnect(self) -> None:
        self._server_id        = None
        self.connection_status = ConnectionStatus.OFFLINE

    def receive_message(self, message: "Message") -> None:
        self._inbox.append(message)

    def get_inbox(self) -> list["Message"]:
        return list(self._inbox)

    def __repr__(self) -> str:
        status = self.connection_status.name
        srv    = f" @ {self._server_id}" if self._server_id else ""
        return f"User({self.username!r} [{self.user_id}] {status}{srv})"


# ──────────────────────────────────────────────
# Message
# ──────────────────────────────────────────────

class Message:
    """Immutable chat message."""

    MAX_CONTENT_LENGTH = 2000

    def __init__(self, sender: str, receiver: str, content: str):
        if not sender or not receiver:
            raise InvalidMessageError("Sender and receiver must be provided.")
        if not content or not content.strip():
            raise InvalidMessageError("Message content cannot be empty.")
        if len(content) > self.MAX_CONTENT_LENGTH:
            raise InvalidMessageError(
                f"Content exceeds {self.MAX_CONTENT_LENGTH} characters."
            )
        self.message_id: str         = str(uuid.uuid4())[:12]
        self.sender: str             = sender
        self.receiver: str           = receiver
        self.content: str            = content.strip()
        self.timestamp: datetime     = datetime.now()
        self.delivery_status: DeliveryStatus = DeliveryStatus.SENT
        self._hops: list[str]        = []   # server IDs the message passed through

    # ── helpers ─────────────────────────────────

    def add_hop(self, server_id: str) -> None:
        self._hops.append(server_id)

    def mark_delivered(self) -> None:
        self.delivery_status = DeliveryStatus.DELIVERED

    def mark_failed(self) -> None:
        self.delivery_status = DeliveryStatus.FAILED

    def mark_queued(self) -> None:
        self.delivery_status = DeliveryStatus.QUEUED

    @property
    def route_info(self) -> str:
        return " → ".join(self._hops) if self._hops else "direct"

    def formatted(self) -> str:
        ts  = self.timestamp.strftime("%H:%M:%S")
        tag = f"[{self.delivery_status.value}]"
        return (
            f"  [{ts}] {tag} {self.sender} → {self.receiver}: {self.content}\n"
            f"         (route: {self.route_info})"
        )

    def __repr__(self) -> str:
        return (
            f"Message(id={self.message_id}, "
            f"{self.sender}→{self.receiver}, "
            f"{self.delivery_status.value})"
        )


# ──────────────────────────────────────────────
# ChatServer
# ──────────────────────────────────────────────

class ChatServer:
    """
    A single chat server node responsible for:
    - Maintaining connected users
    - Routing messages locally or flagging cross-server delivery
    - Storing per-session chat history
    """

    MAX_CAPACITY = 10

    def __init__(self, server_id: str, name: str):
        if not server_id or not name:
            raise ValueError("server_id and name are required.")
        self.server_id: str   = server_id
        self.name: str        = name
        self.status: ServerStatus = ServerStatus.ONLINE
        self._users: dict[str, User]         = {}   # username → User
        self._history: list[Message]         = []
        self._peer_servers: dict[str, "ChatServer"] = {}

    # ── capacity / status ───────────────────────

    @property
    def is_available(self) -> bool:
        return (
            self.status == ServerStatus.ONLINE
            and len(self._users) < self.MAX_CAPACITY
        )

    @property
    def load(self) -> int:
        return len(self._users)

    def set_status(self, status: ServerStatus) -> None:
        self.status = status
        if status != ServerStatus.ONLINE:
            print(
                f"  ⚠  Server [{self.name}] is now {status.name}. "
                f"Disconnecting {len(self._users)} user(s)."
            )
            for user in list(self._users.values()):
                user.disconnect()
            self._users.clear()

    # ── peer management ─────────────────────────

    def add_peer(self, server: "ChatServer") -> None:
        if server.server_id != self.server_id:
            self._peer_servers[server.server_id] = server

    # ── user management ─────────────────────────

    def connect_user(self, user: User) -> None:
        if self.status != ServerStatus.ONLINE:
            raise ServerUnavailableError(
                f"Server {self.name} is {self.status.name}."
            )
        if len(self._users) >= self.MAX_CAPACITY:
            raise ServerUnavailableError(
                f"Server {self.name} is at capacity."
            )
        self._users[user.username] = user
        user.connect(self.server_id)

    def disconnect_user(self, username: str) -> None:
        user = self._users.pop(username, None)
        if user:
            user.disconnect()

    def has_user(self, username: str) -> bool:
        return username in self._users

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def list_users(self) -> list[str]:
        return list(self._users.keys())

    # ── message routing ─────────────────────────

    def route_message(self, message: Message) -> DeliveryStatus:
        """
        Try to deliver a message.
        1. If receiver is local → deliver directly.
        2. Otherwise → forward to a peer that has the receiver.
        3. If no route found → mark FAILED.
        """
        if self.status != ServerStatus.ONLINE:
            message.mark_failed()
            return DeliveryStatus.FAILED

        message.add_hop(self.server_id)

        # local delivery
        if self.has_user(message.receiver):
            receiver = self._users[message.receiver]
            receiver.receive_message(message)
            message.mark_delivered()
            self._history.append(message)
            return DeliveryStatus.DELIVERED

        # cross-server forwarding
        for peer in self._peer_servers.values():
            if peer.status == ServerStatus.ONLINE and peer.has_user(message.receiver):
                self._history.append(message)
                return peer.route_message(message)

        # no route
        message.mark_failed()
        self._history.append(message)
        return DeliveryStatus.FAILED

    # ── history ─────────────────────────────────

    def get_history(self) -> list[Message]:
        return list(self._history)

    # ── display ─────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"ChatServer({self.name!r} [{self.server_id}] "
            f"{self.status.name} users={self.load}/{self.MAX_CAPACITY})"
        )


# ──────────────────────────────────────────────
# ServerNode  (thin wrapper kept for OOP design)
# ──────────────────────────────────────────────

class ServerNode(ChatServer):
    """
    Extends ChatServer with geographic / zone metadata,
    simulating a real distributed node.
    """

    def __init__(self, server_id: str, name: str, region: str = "default"):
        super().__init__(server_id, name)
        self.region: str = region

    def simulate_failure(self) -> None:
        """Randomly bring the node offline to test fault tolerance."""
        self.set_status(ServerStatus.OFFLINE)

    def restore(self) -> None:
        self.set_status(ServerStatus.ONLINE)

    def __repr__(self) -> str:
        base = super().__repr__()
        return base.replace("ChatServer", f"ServerNode[{self.region}]")


# ──────────────────────────────────────────────
# LoadBalancer / Router
# ──────────────────────────────────────────────

class LoadBalancer:
    """
    Distributes incoming users across available servers using
    a least-connections strategy with round-robin tie-breaking.
    """

    def __init__(self):
        self._servers: list[ServerNode]  = []
        self._rr_index: int              = 0

    def register_server(self, server: ServerNode) -> None:
        self._servers.append(server)

    def get_best_server(self) -> Optional[ServerNode]:
        available = [s for s in self._servers if s.is_available]
        if not available:
            return None
        # least-load first; break ties with round-robin order
        return min(available, key=lambda s: s.load)

    def get_server_for_user(self, username: str) -> Optional[ServerNode]:
        """Find which server a user is currently on."""
        for s in self._servers:
            if s.has_user(username):
                return s
        return None

    def list_servers(self) -> list[ServerNode]:
        return list(self._servers)

    def print_status(self) -> None:
        print("\n  ── Load Balancer Status ──────────────────")
        for s in self._servers:
            bar   = "█" * s.load + "░" * (ServerNode.MAX_CAPACITY - s.load)
            users = ", ".join(s.list_users()) or "none"
            print(
                f"  {s.name:12} [{s.status.name:7}] "
                f"[{bar}] {s.load}/{ServerNode.MAX_CAPACITY}  users: {users}"
            )
        print()


# ──────────────────────────────────────────────
# ChatManager
# ──────────────────────────────────────────────

class ChatManager:
    """
    Top-level coordinator.
    Manages users, servers, load balancing, message delivery,
    and provides the public API for the simulation.
    """

    def __init__(self):
        self._users:         dict[str, User]       = {}   # username → User
        self._servers:       dict[str, ServerNode] = {}   # server_id → ServerNode
        self._load_balancer: LoadBalancer          = LoadBalancer()
        self._global_log:    list[Message]         = []

    # ── server management ───────────────────────

    def add_server(self, name: str, region: str = "default") -> ServerNode:
        sid    = f"srv-{str(uuid.uuid4())[:6]}"
        server = ServerNode(sid, name, region)
        self._servers[sid] = server
        self._load_balancer.register_server(server)

        # mesh-connect to all existing peers
        for existing in self._servers.values():
            if existing.server_id != sid:
                existing.add_peer(server)
                server.add_peer(existing)

        print(f"  ✚  Server added: {server}")
        return server

    def get_server_by_name(self, name: str) -> Optional[ServerNode]:
        return next(
            (s for s in self._servers.values() if s.name == name), None
        )

    # ── user management ─────────────────────────

    def register_user(self, username: str) -> User:
        if username in self._users:
            raise UserAlreadyExistsError(f"User {username!r} already exists.")
        user = User(username)
        self._users[username] = user
        print(f"  ✚  Registered: {user}")
        return user

    def connect_user(self, username: str, server_name: Optional[str] = None) -> None:
        user = self._get_user(username)
        if user.is_online:
            print(f"  ℹ  {username} is already connected.")
            return

        if server_name:
            server = self.get_server_by_name(server_name)
            if not server:
                raise ServerUnavailableError(
                    f"No server named {server_name!r} found."
                )
            if not server.is_available:
                raise ServerUnavailableError(
                    f"Server {server_name!r} is not available."
                )
        else:
            server = self._load_balancer.get_best_server()
            if not server:
                raise ServerUnavailableError("No servers available right now.")

        server.connect_user(user)
        print(
            f"  ✔  {username} connected to server [{server.name}] "
            f"(load {server.load}/{server.MAX_CAPACITY})"
        )

    def disconnect_user(self, username: str) -> None:
        user   = self._get_user(username)
        server = self._load_balancer.get_server_for_user(username)
        if server:
            server.disconnect_user(username)
        else:
            user.disconnect()
        print(f"  ✖  {username} disconnected.")

    # ── messaging ───────────────────────────────

    def send_message(
        self, sender_name: str, receiver_name: str, content: str
    ) -> Message:
        sender   = self._get_user(sender_name)
        _        = self._get_user(receiver_name)   # validate receiver exists

        if not sender.is_online:
            raise ChatSystemError(
                f"{sender_name} is not connected. Cannot send message."
            )

        msg     = Message(sender_name, receiver_name, content)
        srv     = self._load_balancer.get_server_for_user(sender_name)
        if not srv:
            raise ServerUnavailableError(
                f"No server found for sender {sender_name!r}."
            )

        status  = srv.route_message(msg)
        self._global_log.append(msg)

        icon = {"DELIVERED": "✉", "FAILED": "✘", "QUEUED": "⏳", "SENT": "↗"}
        print(
            f"  {icon.get(status.value, '?')}  "
            f"{sender_name} → {receiver_name}: "
            f"{content[:60]!r}  [{status.value}]"
        )
        return msg

    # ── fault tolerance ─────────────────────────

    def simulate_server_failure(self, server_name: str) -> None:
        server = self.get_server_by_name(server_name)
        if not server:
            print(f"  ⚠  Server {server_name!r} not found.")
            return
        print(f"\n  💥  Simulating failure on [{server_name}] ...")
        server.simulate_failure()

    def restore_server(self, server_name: str) -> None:
        server = self.get_server_by_name(server_name)
        if not server:
            print(f"  ⚠  Server {server_name!r} not found.")
            return
        server.restore()
        print(f"  ✔  Server [{server_name}] restored.")

    # ── history / display ───────────────────────

    def print_inbox(self, username: str) -> None:
        user = self._get_user(username)
        msgs = user.get_inbox()
        print(f"\n  📥 Inbox for {username} ({len(msgs)} message(s)):")
        if not msgs:
            print("     (empty)")
        for m in msgs:
            print(m.formatted())

    def print_server_history(self, server_name: str) -> None:
        server = self.get_server_by_name(server_name)
        if not server:
            print(f"  ⚠  Server {server_name!r} not found.")
            return
        msgs = server.get_history()
        print(
            f"\n  📋 History on [{server_name}] ({len(msgs)} message(s)):"
        )
        if not msgs:
            print("     (empty)")
        for m in msgs:
            print(m.formatted())

    def print_global_log(self) -> None:
        print(f"\n  📜 Global message log ({len(self._global_log)} total):")
        for m in self._global_log:
            print(m.formatted())

    def print_load_balancer(self) -> None:
        self._load_balancer.print_status()

    def list_online_users(self) -> None:
        online = [u for u in self._users.values() if u.is_online]
        print(f"\n  👥 Online users ({len(online)}):")
        for u in online:
            print(f"     {u}")

    # ── private helpers ─────────────────────────

    def _get_user(self, username: str) -> User:
        user = self._users.get(username)
        if not user:
            raise UserNotFoundError(f"User {username!r} not found.")
        return user


# ──────────────────────────────────────────────
# Demo / Simulation
# ──────────────────────────────────────────────

def _separator(title: str = "") -> None:
    line = "─" * 60
    if title:
        print(f"\n{'─'*4}  {title}  {'─'*(52 - len(title))}")
    else:
        print(f"\n{line}")


def run_simulation() -> None:
    print("=" * 62)
    print("  DISTRIBUTED CHAT SYSTEM  –  Simulation")
    print("=" * 62)

    manager = ChatManager()

    # ── 1. Create servers ────────────────────────────────────────
    _separator("Step 1 · Spin up servers")
    s_alpha = manager.add_server("Alpha",   region="us-east")
    s_beta  = manager.add_server("Beta",    region="us-west")
    s_gamma = manager.add_server("Gamma",   region="eu-central")

    # ── 2. Register users ────────────────────────────────────────
    _separator("Step 2 · Register users")
    for name in ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"]:
        manager.register_user(name)

    # ── 3. Connect users (load balancer assigns servers) ─────────
    _separator("Step 3 · Connect users (auto load-balance)")
    for name in ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"]:
        try:
            manager.connect_user(name)
        except ServerUnavailableError as exc:
            print(f"  ⚠  Could not connect {name}: {exc}")

    manager.print_load_balancer()
    manager.list_online_users()

    # ── 4. Same-server messaging ─────────────────────────────────
    _separator("Step 4 · Same-server messaging")
    manager.send_message("Alice", "Bob",   "Hey Bob, are you there?")
    manager.send_message("Bob",   "Alice", "Yes! What's up, Alice?")

    # ── 5. Cross-server messaging ────────────────────────────────
    _separator("Step 5 · Cross-server messaging")
    manager.send_message("Alice", "Dave",  "Hi Dave, this crosses servers!")
    manager.send_message("Carol", "Frank", "Carol→Frank, different nodes.")
    manager.send_message("Eve",   "Bob",   "Eve to Bob – routed via mesh.")

    # ── 6. View inboxes ──────────────────────────────────────────
    _separator("Step 6 · Inboxes")
    manager.print_inbox("Alice")
    manager.print_inbox("Bob")
    manager.print_inbox("Dave")

    # ── 7. Fault tolerance – server failure ──────────────────────
    _separator("Step 7 · Fault tolerance")
    # Identify which server Alice is on
    alice_srv = manager._load_balancer.get_server_for_user("Alice")
    if alice_srv:
        manager.simulate_server_failure(alice_srv.name)

    manager.print_load_balancer()

    # Alice (now offline) tries to send → should fail gracefully
    try:
        manager.send_message("Alice", "Carol", "Can you hear me after failure?")
    except ChatSystemError as exc:
        print(f"  ✘  Expected error: {exc}")

    # Bob (still online) messages Carol
    manager.send_message("Bob", "Carol", "Checking in while Alpha is down.")

    # ── 8. Reconnect Alice to a healthy server ───────────────────
    _separator("Step 8 · Reconnect Alice")
    healthy = manager._load_balancer.get_best_server()
    if healthy:
        try:
            manager.connect_user("Alice", server_name=healthy.name)
            manager.send_message("Alice", "Carol", "I'm back online!")
        except ChatSystemError as exc:
            print(f"  ⚠  {exc}")
    else:
        print("  ⚠  No healthy servers available for reconnect.")

    # ── 9. Server restore ────────────────────────────────────────
    _separator("Step 9 · Restore failed server")
    if alice_srv:
        manager.restore_server(alice_srv.name)
    manager.print_load_balancer()

    # ── 10. Final logs ───────────────────────────────────────────
    _separator("Step 10 · Server histories & global log")
    for srv_name in ["Alpha", "Beta", "Gamma"]:
        manager.print_server_history(srv_name)

    manager.print_global_log()

    _separator()
    print("  Simulation complete.")
    print("=" * 62)


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    run_simulation()