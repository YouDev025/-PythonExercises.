"""
messaging_system.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A command-line Messaging Platform built with Python OOP.

Features
  • Register & manage user accounts
  • Send / receive messages between users
  • Inbox with unread badge counts
  • Mark individual or all messages as read
  • Delete messages (soft-delete with trash / purge)
  • Sent-items folder per user
  • Search messages by keyword
  • Conversation thread view
  • Platform-wide statistics dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────
#  ANSI COLOUR PALETTE
# ─────────────────────────────────────────────────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

ACCENT = [CYAN, GREEN, MAGENTA, BLUE, YELLOW]

STATUS_UNREAD = "unread"
STATUS_READ   = "read"
STATUS_DELETED = "deleted"


# ─────────────────────────────────────────────────────────────
#  MESSAGE
# ─────────────────────────────────────────────────────────────
class Message:
    """Represents a single message between two users."""

    _id_counter = 1

    def __init__(self, sender: str, receiver: str, content: str):
        if not content.strip():
            raise ValueError("Message content cannot be empty.")

        self._message_id = f"MSG-{Message._id_counter:06d}"
        Message._id_counter += 1

        self._sender    = sender
        self._receiver  = receiver
        self._content   = content.strip()
        self._timestamp = datetime.now()
        self._status    = STATUS_UNREAD   # receiver's perspective
        self._deleted_by: set[str] = set()  # usernames who soft-deleted

    # ── read-only properties ──────────────────────────────────
    @property
    def message_id(self) -> str:   return self._message_id
    @property
    def sender(self) -> str:       return self._sender
    @property
    def receiver(self) -> str:     return self._receiver
    @property
    def content(self) -> str:      return self._content
    @property
    def status(self) -> str:       return self._status
    @property
    def timestamp(self) -> datetime: return self._timestamp
    @property
    def is_read(self) -> bool:     return self._status == STATUS_READ
    @property
    def is_unread(self) -> bool:   return self._status == STATUS_UNREAD

    def mark_read(self):
        if self._status == STATUS_UNREAD:
            self._status = STATUS_READ

    def soft_delete(self, username: str):
        """Mark deleted for one user without removing from the other's view."""
        self._deleted_by.add(username)

    def is_deleted_by(self, username: str) -> bool:
        return username in self._deleted_by

    def timestamp_str(self, fmt: str = "%Y-%m-%d %H:%M") -> str:
        return self._timestamp.strftime(fmt)

    # ── display helpers ───────────────────────────────────────
    def preview(self, viewer: str, colour: str = CYAN, index: int = 0) -> str:
        """One-line summary row for inbox/sent lists."""
        other    = self._sender if viewer == self._receiver else self._receiver
        role_tag = f"{DIM}from{RESET}" if viewer == self._receiver else f"{DIM}to{RESET}"
        unread_dot = f" {YELLOW}●{RESET}" if self.is_unread and viewer == self._receiver else ""
        snippet  = self._content[:45].replace("\n", " ")
        if len(self._content) > 45:
            snippet += "…"
        return (
            f"  {DIM}{index:>3}.{RESET}  "
            f"{colour}{self._message_id}{RESET}  "
            f"{role_tag} {BOLD}{other:<18}{RESET}  "
            f"{DIM}{self.timestamp_str()}{RESET}  "
            f"{snippet}{unread_dot}"
        )

    def full_view(self) -> str:
        """Detailed multi-line card."""
        sep = f"  {'─' * 62}"
        status_tag = (f"{YELLOW}● Unread{RESET}" if self.is_unread
                      else f"{GREEN}✓ Read{RESET}")
        return "\n".join([
            sep,
            f"  {BOLD}{CYAN}{self._message_id}{RESET}  {status_tag}",
            f"  {BOLD}From      :{RESET} {self._sender}",
            f"  {BOLD}To        :{RESET} {self._receiver}",
            f"  {BOLD}Sent      :{RESET} {self.timestamp_str('%A, %d %B %Y at %H:%M')}",
            sep,
            "",
            f"  {self._content}",
            "",
            sep,
        ])

    def __repr__(self) -> str:
        return f"Message({self._message_id!r}, {self._sender!r}→{self._receiver!r})"


# ─────────────────────────────────────────────────────────────
#  USER
# ─────────────────────────────────────────────────────────────
class User:
    """A registered messaging-platform user."""

    _id_counter = 1

    def __init__(self, username: str, display_name: str = ""):
        username = username.strip().lower()
        if not username:
            raise ValueError("Username cannot be empty.")
        if not username.replace("_", "").replace(".", "").isalnum():
            raise ValueError(
                "Username may only contain letters, numbers, underscores, and dots."
            )
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters.")

        self._user_id      = f"USR-{User._id_counter:04d}"
        User._id_counter  += 1
        self._username     = username
        self._display_name = display_name.strip() or username
        self._joined       = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Message storage: message_id → Message
        self._inbox:  dict[str, Message] = {}
        self._sent:   dict[str, Message] = {}
        self._trash:  dict[str, Message] = {}

    # ── properties ───────────────────────────────────────────
    @property
    def user_id(self) -> str:       return self._user_id
    @property
    def username(self) -> str:      return self._username
    @property
    def display_name(self) -> str:  return self._display_name
    @property
    def joined(self) -> str:        return self._joined

    @property
    def unread_count(self) -> int:
        return sum(1 for m in self._inbox.values() if m.is_unread)

    @property
    def inbox_count(self) -> int:   return len(self._inbox)
    @property
    def sent_count(self) -> int:    return len(self._sent)
    @property
    def trash_count(self) -> int:   return len(self._trash)

    # ── inbox management ─────────────────────────────────────
    def deliver(self, message: Message):
        """Drop an incoming message into this user's inbox."""
        self._inbox[message.message_id] = message

    def record_sent(self, message: Message):
        """Store a copy in the sent folder."""
        self._sent[message.message_id] = message

    def get_inbox(self, unread_only: bool = False) -> list[Message]:
        msgs = list(self._inbox.values())
        if unread_only:
            msgs = [m for m in msgs if m.is_unread]
        return sorted(msgs, key=lambda m: m.timestamp, reverse=True)

    def get_sent(self) -> list[Message]:
        return sorted(self._sent.values(), key=lambda m: m.timestamp, reverse=True)

    def get_trash(self) -> list[Message]:
        return sorted(self._trash.values(), key=lambda m: m.timestamp, reverse=True)

    def get_message(self, message_id: str) -> Optional[Message]:
        mid = message_id.upper()
        return self._inbox.get(mid) or self._sent.get(mid) or self._trash.get(mid)

    def delete_message(self, message_id: str) -> Optional[Message]:
        """Move from inbox to trash."""
        mid = message_id.upper()
        msg = self._inbox.pop(mid, None)
        if msg:
            msg.soft_delete(self._username)
            self._trash[mid] = msg
            return msg
        return None

    def purge_message(self, message_id: str) -> Optional[Message]:
        """Permanently remove from trash."""
        return self._trash.pop(message_id.upper(), None)

    def restore_message(self, message_id: str) -> Optional[Message]:
        """Move from trash back to inbox."""
        mid = message_id.upper()
        msg = self._trash.pop(mid, None)
        if msg:
            self._inbox[mid] = msg
            return msg
        return None

    def mark_all_read(self):
        for m in self._inbox.values():
            m.mark_read()

    def search(self, keyword: str) -> list[Message]:
        kw = keyword.lower()
        results = []
        for folder in (self._inbox, self._sent):
            for m in folder.values():
                if kw in m.content.lower() or kw in m.sender.lower() or kw in m.receiver.lower():
                    results.append(m)
        return sorted(results, key=lambda m: m.timestamp, reverse=True)

    def conversation_with(self, other_username: str) -> list[Message]:
        """All messages exchanged with a specific user, chronological."""
        other = other_username.lower()
        msgs = []
        for folder in (self._inbox, self._sent):
            for m in folder.values():
                if m.sender == other or m.receiver == other:
                    msgs.append(m)
        # deduplicate by message_id
        seen = set()
        unique = []
        for m in msgs:
            if m.message_id not in seen:
                seen.add(m.message_id)
                unique.append(m)
        return sorted(unique, key=lambda m: m.timestamp)

    # ── display ──────────────────────────────────────────────
    def profile_card(self) -> str:
        unread = self.unread_count
        badge  = f" {YELLOW}({unread} unread){RESET}" if unread else ""
        sep    = f"  {'─' * 50}"
        return "\n".join([
            sep,
            f"  {BOLD}{CYAN}{self._user_id}{RESET}",
            f"  {BOLD}Username     :{RESET} {self._username}",
            f"  {BOLD}Display name :{RESET} {self._display_name}",
            f"  {BOLD}Joined       :{RESET} {self._joined}",
            f"  {BOLD}Inbox        :{RESET} {self.inbox_count} message(s){badge}",
            f"  {BOLD}Sent         :{RESET} {self.sent_count} message(s)",
            f"  {BOLD}Trash        :{RESET} {self.trash_count} message(s)",
            sep,
        ])

    def __str__(self) -> str:
        return self.profile_card()

    def __repr__(self) -> str:
        return f"User({self._user_id!r}, {self._username!r})"


# ─────────────────────────────────────────────────────────────
#  MESSAGING SYSTEM
# ─────────────────────────────────────────────────────────────
class MessagingSystem:
    """Central hub managing all users and message routing."""

    def __init__(self, platform_name: str = "PyMessenger"):
        self._name  = platform_name
        self._users: dict[str, User] = {}      # username → User

    # ── user management ──────────────────────────────────────
    def register(self, username: str, display_name: str = "") -> User:
        uname = username.strip().lower()
        if uname in self._users:
            raise ValueError(f"Username '{uname}' is already taken.")
        user = User(uname, display_name)
        self._users[uname] = user
        return user

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username.strip().lower())

    def all_users(self) -> list[User]:
        return sorted(self._users.values(), key=lambda u: u.username)

    def user_exists(self, username: str) -> bool:
        return username.strip().lower() in self._users

    # ── messaging ────────────────────────────────────────────
    def send_message(self, sender_name: str, receiver_name: str,
                     content: str) -> Message:
        sender   = self._require_user(sender_name)
        receiver = self._require_user(receiver_name)
        if sender.username == receiver.username:
            raise ValueError("You cannot send a message to yourself.")

        msg = Message(sender.username, receiver.username, content)
        receiver.deliver(msg)
        sender.record_sent(msg)
        return msg

    def mark_message_read(self, username: str, message_id: str) -> Message:
        user = self._require_user(username)
        msg  = user.get_message(message_id)
        if not msg:
            raise KeyError(f"Message '{message_id.upper()}' not found.")
        msg.mark_read()
        return msg

    def delete_message(self, username: str, message_id: str) -> Message:
        user = self._require_user(username)
        msg  = user.delete_message(message_id)
        if not msg:
            raise KeyError(
                f"Message '{message_id.upper()}' not found in inbox."
            )
        return msg

    def purge_message(self, username: str, message_id: str) -> Message:
        user = self._require_user(username)
        msg  = user.purge_message(message_id)
        if not msg:
            raise KeyError(
                f"Message '{message_id.upper()}' not found in trash."
            )
        return msg

    def restore_message(self, username: str, message_id: str) -> Message:
        user = self._require_user(username)
        msg  = user.restore_message(message_id)
        if not msg:
            raise KeyError(
                f"Message '{message_id.upper()}' not found in trash."
            )
        return msg

    # ── statistics ───────────────────────────────────────────
    def statistics(self) -> dict:
        total_users   = len(self._users)
        total_inbox   = sum(u.inbox_count for u in self._users.values())
        total_unread  = sum(u.unread_count for u in self._users.values())
        total_sent    = sum(u.sent_count   for u in self._users.values())
        total_trash   = sum(u.trash_count  for u in self._users.values())
        active_users  = [u for u in self._users.values()
                         if u.inbox_count + u.sent_count > 0]
        return {
            "total_users":   total_users,
            "active_users":  len(active_users),
            "total_messages_in_inboxes": total_inbox,
            "total_unread":  total_unread,
            "total_sent":    total_sent,
            "total_trash":   total_trash,
        }

    # ── private helpers ──────────────────────────────────────
    def _require_user(self, username: str) -> User:
        user = self.get_user(username)
        if not user:
            raise KeyError(f"User '{username}' not found.")
        return user


# ─────────────────────────────────────────────────────────────
#  SESSION  (tracks the currently logged-in user)
# ─────────────────────────────────────────────────────────────
class Session:
    """Lightweight context holding the active user."""

    def __init__(self):
        self._user: Optional[User] = None

    @property
    def user(self) -> Optional[User]:
        return self._user

    @property
    def is_logged_in(self) -> bool:
        return self._user is not None

    @property
    def username(self) -> str:
        return self._user.username if self._user else ""

    def login(self, user: User):
        self._user = user

    def logout(self):
        self._user = None


# ─────────────────────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────────────────────
def _sep(char: str = "═", width: int = 66):
    print(char * width)

def _header(title: str):
    _sep()
    print(f"  {BOLD}{title}{RESET}")
    _sep()

def _inp(prompt: str) -> str:
    return input(f"  {prompt}").strip()

def _display_message_list(messages: list[Message], heading: str,
                           viewer: str):
    if not messages:
        print(f"  {DIM}No messages.{RESET}")
        return
    _header(heading)
    print(f"  {BOLD}{'#':>3}   {'ID':<12}  {'Direction':<25}  "
          f"{'Date':<17}  Preview{RESET}")
    print(f"  {'─' * 95}")
    for i, msg in enumerate(messages, 1):
        colour = ACCENT[i % len(ACCENT)]
        print(msg.preview(viewer, colour, i))


# ─────────────────────────────────────────────────────────────
#  MENU ACTION FUNCTIONS
# ─────────────────────────────────────────────────────────────

# ─── AUTH ────────────────────────────────────────────────────
def action_register(system: MessagingSystem, session: Session):
    _header("Register New Account")
    uname   = _inp("Choose username     : ")
    display = _inp("Display name (opt)  : ")
    try:
        user = system.register(uname, display)
        print(f"\n  {GREEN}✔  Account created — {user.user_id}  (@{user.username}){RESET}")
        auto = _inp("Log in as this user now? (y/n): ").lower()
        if auto == "y":
            session.login(user)
            print(f"  {GREEN}✔  Logged in as @{user.username}{RESET}")
    except ValueError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_login(system: MessagingSystem, session: Session):
    _header("Log In")
    if session.is_logged_in:
        print(f"  {YELLOW}Already logged in as @{session.username}.{RESET}")
        sw = _inp("Switch account? (y/n): ").lower()
        if sw != "y":
            return
    uname = _inp("Username: ").lower()
    user  = system.get_user(uname)
    if not user:
        print(f"\n  {RED}✖  User '@{uname}' not found.{RESET}")
        return
    session.login(user)
    unread = user.unread_count
    badge  = f"  {YELLOW}You have {unread} unread message(s).{RESET}" if unread else ""
    print(f"\n  {GREEN}✔  Welcome back, {user.display_name}!{RESET}{badge}")


def action_logout(session: Session):
    if not session.is_logged_in:
        print(f"  {YELLOW}You are not logged in.{RESET}")
        return
    name = session.username
    session.logout()
    print(f"  {GREEN}✔  @{name} logged out.{RESET}")


# ─── MESSAGING ───────────────────────────────────────────────
def action_send_message(system: MessagingSystem, session: Session):
    _header("Send Message")
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return

    # Show registered users (excluding self)
    others = [u for u in system.all_users() if u.username != session.username]
    if not others:
        print(f"  {YELLOW}No other users registered yet.{RESET}"); return

    print(f"  {BOLD}Registered users:{RESET}")
    for u in others:
        unread_tag = f"  {DIM}({u.unread_count} unread){RESET}" if u.unread_count else ""
        print(f"    {CYAN}@{u.username:<18}{RESET} {u.display_name}{unread_tag}")

    receiver = _inp("\nSend to (@username): ").lower().lstrip("@")

    print(f"\n  {DIM}Type your message below. Press Enter twice to send.{RESET}")
    lines = []
    while True:
        line = input("  > ")
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    content = "\n".join(lines).strip()

    if not content:
        print(f"  {YELLOW}Empty message — cancelled.{RESET}"); return

    try:
        msg = system.send_message(session.username, receiver, content)
        print(f"\n  {GREEN}✔  Message sent to @{receiver}  ({msg.message_id}){RESET}")
    except (KeyError, ValueError) as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_view_inbox(system: MessagingSystem, session: Session):
    _header("Inbox")
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return

    user = system.get_user(session.username)
    unread = user.unread_count
    print(f"  {BOLD}@{user.username}{RESET}  |  "
          f"{user.inbox_count} message(s)"
          + (f"  {YELLOW}● {unread} unread{RESET}" if unread else "  ✓ all read"))

    print(f"\n  1. All messages")
    print(f"  2. Unread only")
    sub = _inp("Show: ")
    msgs = user.get_inbox(unread_only=(sub == "2"))
    _display_message_list(msgs, "Inbox", session.username)


def action_view_sent(system: MessagingSystem, session: Session):
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return
    user = system.get_user(session.username)
    msgs = user.get_sent()
    _display_message_list(msgs, f"Sent — @{user.username}", session.username)


def action_read_message(system: MessagingSystem, session: Session):
    _header("Read Message")
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return

    user = system.get_user(session.username)
    msgs = user.get_inbox()
    _display_message_list(msgs, "Inbox", session.username)

    mid = _inp("\nMessage ID (e.g. MSG-000001): ").upper()
    msg = user.get_message(mid)
    if not msg:
        print(f"  {RED}✖  Message '{mid}' not found.{RESET}"); return

    print()
    print(msg.full_view())
    if msg.is_unread and msg.receiver == session.username:
        msg.mark_read()
        print(f"  {DIM}Marked as read.{RESET}")


def action_mark_read(system: MessagingSystem, session: Session):
    _header("Mark Messages as Read")
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return

    user = system.get_user(session.username)
    unread = user.unread_count
    if unread == 0:
        print(f"  {GREEN}✔  All messages are already read.{RESET}"); return

    print(f"  1. Mark a specific message as read")
    print(f"  2. Mark ALL {unread} unread message(s) as read")
    sub = _inp("Choice: ")

    if sub == "1":
        mid = _inp("Message ID: ").upper()
        try:
            system.mark_message_read(session.username, mid)
            print(f"  {GREEN}✔  {mid} marked as read.{RESET}")
        except KeyError as e:
            print(f"  {RED}✖  {e}{RESET}")
    elif sub == "2":
        user.mark_all_read()
        print(f"  {GREEN}✔  All {unread} message(s) marked as read.{RESET}")
    else:
        print(f"  {RED}✖  Invalid choice.{RESET}")


def action_delete_message(system: MessagingSystem, session: Session):
    _header("Delete Message")
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return

    user = system.get_user(session.username)
    msgs = user.get_inbox()
    _display_message_list(msgs, "Inbox", session.username)

    mid = _inp("\nMessage ID to delete: ").upper()
    try:
        msg = system.delete_message(session.username, mid)
        print(f"\n  {GREEN}✔  Message {mid} moved to trash.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_trash(system: MessagingSystem, session: Session):
    _header("Trash")
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return

    user = system.get_user(session.username)
    msgs = user.get_trash()
    _display_message_list(msgs, f"Trash — @{user.username}", session.username)

    if not msgs:
        return

    print(f"\n  1. Restore a message to inbox")
    print(f"  2. Permanently delete a message")
    print(f"  3. Back")
    sub = _inp("Choice: ")

    if sub in ("1", "2"):
        mid = _inp("Message ID: ").upper()
        try:
            if sub == "1":
                system.restore_message(session.username, mid)
                print(f"  {GREEN}✔  {mid} restored to inbox.{RESET}")
            else:
                confirm = _inp("Permanently delete? This cannot be undone. (y/n): ").lower()
                if confirm == "y":
                    system.purge_message(session.username, mid)
                    print(f"  {GREEN}✔  {mid} permanently deleted.{RESET}")
                else:
                    print(f"  Cancelled.")
        except KeyError as e:
            print(f"  {RED}✖  {e}{RESET}")


def action_search(system: MessagingSystem, session: Session):
    _header("Search Messages")
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return

    user    = system.get_user(session.username)
    keyword = _inp("Search keyword: ")
    results = user.search(keyword)
    _display_message_list(results, f'Results for "{keyword}"', session.username)


def action_conversation(system: MessagingSystem, session: Session):
    _header("Conversation Thread")
    if not session.is_logged_in:
        print(f"  {RED}✖  Please log in first.{RESET}"); return

    others = [u for u in system.all_users() if u.username != session.username]
    if not others:
        print(f"  {YELLOW}No other users yet.{RESET}"); return

    print(f"  {BOLD}Users:{RESET}")
    for u in others:
        print(f"    {CYAN}@{u.username:<18}{RESET} {u.display_name}")

    other = _inp("\n@Username to view thread with: ").lower().lstrip("@")
    if not system.user_exists(other):
        print(f"  {RED}✖  User '@{other}' not found.{RESET}"); return

    user = system.get_user(session.username)
    msgs = user.conversation_with(other)

    if not msgs:
        print(f"  {DIM}No messages exchanged with @{other} yet.{RESET}"); return

    _header(f"Thread: @{session.username}  ↔  @{other}")
    for msg in msgs:
        is_mine = msg.sender == session.username
        arrow   = f"{CYAN}  ▶ You → @{other}{RESET}" if is_mine else \
                  f"{GREEN}  ◀ @{other} → You{RESET}"
        print(f"\n{arrow}  {DIM}{msg.timestamp_str()}{RESET}")
        print(f"  {msg.content}")
        print(f"  {DIM}[{msg.message_id}]{RESET}")
        if msg.is_unread and not is_mine:
            msg.mark_read()


def action_list_users(system: MessagingSystem):
    _header("Registered Users")
    users = system.all_users()
    if not users:
        print(f"  {DIM}No users registered yet.{RESET}"); return
    print(f"  {BOLD}{'#':>3}   {'ID':<10}  {'Username':<20}  {'Display Name':<22}  "
          f"{'Inbox':>6}  {'Unread':>6}  Joined{RESET}")
    print(f"  {'─' * 92}")
    for i, u in enumerate(users, 1):
        colour = ACCENT[i % len(ACCENT)]
        unread_col = YELLOW if u.unread_count else DIM
        print(
            f"  {DIM}{i:>3}.{RESET}  "
            f"{colour}{u.user_id}{RESET}  "
            f"@{u.username:<20}  "
            f"{u.display_name:<22}  "
            f"{DIM}{u.inbox_count:>6}{RESET}  "
            f"{unread_col}{u.unread_count:>6}{RESET}  "
            f"{DIM}{u.joined}{RESET}"
        )


def action_statistics(system: MessagingSystem):
    _header("Platform Statistics")
    s = system.statistics()
    rows = [
        ("Registered users",        s["total_users"],          CYAN),
        ("Active users",            s["active_users"],         GREEN),
        ("Messages in inboxes",     s["total_messages_in_inboxes"], MAGENTA),
        ("Unread messages",         s["total_unread"],         YELLOW if s["total_unread"] else GREEN),
        ("Total sent",              s["total_sent"],           BLUE),
        ("Messages in trash",       s["total_trash"],          DIM),
    ]
    for label, val, colour in rows:
        bar = "█" * min(val, 40)
        print(f"  {label:<30} {colour}{val:>5}  {bar}{RESET}")


# ─────────────────────────────────────────────────────────────
#  DEMO SEED DATA
# ─────────────────────────────────────────────────────────────
def seed_demo_data(system: MessagingSystem):
    users = [
        ("alice",   "Alice Johnson"),
        ("bob",     "Bob Martinez"),
        ("carol",   "Carol Williams"),
        ("dave",    "Dave Chen"),
    ]
    for uname, display in users:
        if not system.user_exists(uname):
            system.register(uname, display)

    convos = [
        ("alice", "bob",   "Hey Bob! Are you joining the team meeting tomorrow?"),
        ("bob",   "alice", "Hi Alice! Yes, I'll be there. What time does it start?"),
        ("alice", "bob",   "It starts at 10 AM. Don't forget to review the agenda beforehand."),
        ("carol", "alice", "Alice, I've finished the project report. Want me to send it over?"),
        ("alice", "carol", "Yes please, Carol! That would be great."),
        ("dave",  "bob",   "Bob, can you review my pull request when you get a chance?"),
        ("bob",   "dave",  "Sure, I'll take a look this afternoon."),
        ("carol", "dave",  "Hi Dave! The design mockups are ready for your review."),
    ]
    for sender, receiver, content in convos:
        system.send_message(sender, receiver, content)

    # Mark some messages as read
    alice = system.get_user("alice")
    if alice:
        inbox = alice.get_inbox()
        for msg in inbox[:1]:
            msg.mark_read()


# ─────────────────────────────────────────────────────────────
#  MENUS
# ─────────────────────────────────────────────────────────────
MENU_LOGGED_OUT = f"""
  {BOLD}┌─────────────────────────────────────────────┐
  │            PyMessenger                      │
  ├─────────────────────────────────────────────┤
  │{RESET}   1.  Register New Account                  {BOLD}│
  │{RESET}   2.  Log In                                {BOLD}│
  │{RESET}   3.  List Users                            {BOLD}│
  │{RESET}   4.  Platform Statistics                   {BOLD}│
  │{RESET}   0.  Exit                                  {BOLD}│
  └─────────────────────────────────────────────┘{RESET}"""

def _build_menu_logged_in(user: User) -> str:
    unread = user.unread_count
    badge  = f" {YELLOW}({unread} unread){RESET}" if unread else ""
    return f"""
  {BOLD}┌─────────────────────────────────────────────┐
  │  PyMessenger  —  @{user.username:<24}{BOLD}│
  ├─────────────────────────────────────────────┤
  │  {CYAN}MESSAGES{RESET}{BOLD}                                    │
  │{RESET}   1.  Send Message                          {BOLD}│
  │{RESET}   2.  View Inbox{badge:<5}                       {BOLD}│
  │{RESET}   3.  View Sent                             {BOLD}│
  │{RESET}   4.  Read a Message                        {BOLD}│
  │{RESET}   5.  Mark as Read                          {BOLD}│
  │{RESET}   6.  Delete Message (→ Trash)              {BOLD}│
  │{RESET}   7.  Trash                                 {BOLD}│
  │{RESET}   8.  Search Messages                       {BOLD}│
  │{RESET}   9.  Conversation Thread                   {BOLD}│
  │  {CYAN}ACCOUNT{RESET}{BOLD}                                    │
  │{RESET}  10.  List All Users                        {BOLD}│
  │{RESET}  11.  Platform Statistics                   {BOLD}│
  │{RESET}  12.  Switch Account / Log Out              {BOLD}│
  │{RESET}   0.  Exit                                  {BOLD}│
  └─────────────────────────────────────────────┘{RESET}"""


def _banner(platform_name: str):
    print()
    _sep("═")
    print(f"""
  {BOLD}{CYAN}
  ███╗   ███╗███████╗ ██████╗ ███████╗███████╗███╗   ██╗
  ████╗ ████║██╔════╝██╔════╝ ██╔════╝██╔════╝████╗  ██║
  ██╔████╔██║█████╗  ███████╗ ███████╗█████╗  ██╔██╗ ██║
  ██║╚██╔╝██║██╔══╝  ██╔═══██╗╚════██║██╔══╝  ██║╚██╗██║
  ██║ ╚═╝ ██║███████╗╚██████╔╝███████║███████╗██║ ╚████║
  ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝{RESET}
  {BOLD}  {platform_name}  —  Simple. Fast. Private.{RESET}
""")
    _sep("═")
    print()


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────
def main():
    system  = MessagingSystem("PyMessenger")
    session = Session()

    _banner("PyMessenger")

    load = _inp("Load demo data? (y/n): ").lower()
    if load == "y":
        seed_demo_data(system)
        s = system.statistics()
        print(
            f"\n  {GREEN}✔  Demo loaded — "
            f"{s['total_users']} users, "
            f"{s['total_messages_in_inboxes']} messages delivered, "
            f"{s['total_unread']} unread.{RESET}"
        )
        print(f"  {DIM}Demo accounts: alice, bob, carol, dave  (no passwords){RESET}\n")

    # ── dispatcher maps ──────────────────────────────────────
    LOGGED_OUT_ACTIONS = {
        "1": lambda: action_register(system, session),
        "2": lambda: action_login(system, session),
        "3": lambda: action_list_users(system),
        "4": lambda: action_statistics(system),
    }

    LOGGED_IN_ACTIONS = {
        "1":  lambda: action_send_message(system, session),
        "2":  lambda: action_view_inbox(system, session),
        "3":  lambda: action_view_sent(system, session),
        "4":  lambda: action_read_message(system, session),
        "5":  lambda: action_mark_read(system, session),
        "6":  lambda: action_delete_message(system, session),
        "7":  lambda: action_trash(system, session),
        "8":  lambda: action_search(system, session),
        "9":  lambda: action_conversation(system, session),
        "10": lambda: action_list_users(system),
        "11": lambda: action_statistics(system),
        "12": lambda: action_logout(session),
    }

    while True:
        if session.is_logged_in:
            print(_build_menu_logged_in(session.user))
            actions = LOGGED_IN_ACTIONS
        else:
            print(MENU_LOGGED_OUT)
            actions = LOGGED_OUT_ACTIONS

        choice = _inp("Select option: ")

        if choice == "0":
            name = f"@{session.username}" if session.is_logged_in else "stranger"
            print(f"\n  {CYAN}Goodbye, {name}! Stay connected. 👋{RESET}\n")
            break
        elif choice in actions:
            print()
            actions[choice]()
            input(f"\n  {DIM}Press Enter to return to menu…{RESET}")
        else:
            print(f"  {RED}✖  Unrecognised option. Please try again.{RESET}")


if __name__ == "__main__":
    main()