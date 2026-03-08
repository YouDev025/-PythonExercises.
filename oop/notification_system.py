"""
Notification Management System
A clean OOP-based notification system with encapsulation and a CLI menu.
"""

import os
from datetime import datetime


# ─────────────────────────────────────────────
#  NOTIFICATION CLASS
# ─────────────────────────────────────────────

class Notification:
    """Represents a single notification with encapsulated data."""

    STATUS_UNREAD = "Unread"
    STATUS_READ   = "Read"

    def __init__(self, notification_id: int, message: str,
                 sender: str, receiver: str):
        self.__notification_id: int  = notification_id
        self.__message: str          = message
        self.__sender: str           = sender
        self.__receiver: str         = receiver
        self.__timestamp: str        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.__status: str           = self.STATUS_UNREAD

    # ── Read-only properties ────────────────────

    @property
    def notification_id(self) -> int:
        return self.__notification_id

    @property
    def message(self) -> str:
        return self.__message

    @property
    def sender(self) -> str:
        return self.__sender

    @property
    def receiver(self) -> str:
        return self.__receiver

    @property
    def timestamp(self) -> str:
        return self.__timestamp

    @property
    def status(self) -> str:
        return self.__status

    @property
    def is_read(self) -> bool:
        return self.__status == self.STATUS_READ

    # ── State mutation ──────────────────────────

    def mark_as_read(self):
        self.__status = self.STATUS_READ

    def mark_as_unread(self):
        self.__status = self.STATUS_UNREAD

    # ── Display ─────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "ID":        self.__notification_id,
            "From":      self.__sender,
            "To":        self.__receiver,
            "Message":   self.__message,
            "Timestamp": self.__timestamp,
            "Status":    self.__status,
        }

    def __repr__(self) -> str:
        return (f"Notification(id={self.__notification_id}, "
                f"from='{self.__sender}', to='{self.__receiver}', "
                f"status='{self.__status}')")


# ─────────────────────────────────────────────
#  NOTIFICATION MANAGER CLASS
# ─────────────────────────────────────────────

class NotificationManager:
    """Manages all notifications across users."""

    def __init__(self):
        # storage: receiver_username → list[Notification]
        self.__store: dict[str, list[Notification]] = {}
        self.__next_id: int = 1

    # ── Internal helpers ────────────────────────

    def _next_id(self) -> int:
        uid = self.__next_id
        self.__next_id += 1
        return uid

    def _all_notifications(self) -> list[Notification]:
        """Flat list of every notification across all users."""
        return [n for notes in self.__store.values() for n in notes]

    def _find_by_id(self, notification_id: int) -> tuple["Notification | None", "str | None"]:
        """Return (notification, receiver_key) or (None, None)."""
        for receiver, notes in self.__store.items():
            for n in notes:
                if n.notification_id == notification_id:
                    return n, receiver
        return None, None

    @staticmethod
    def _validate_name(name: str, label: str) -> tuple[bool, str]:
        name = name.strip()
        if not name:
            return False, f"{label} cannot be empty."
        if len(name) > 50:
            return False, f"{label} must be 50 characters or fewer."
        return True, "OK"

    @staticmethod
    def _validate_message(message: str) -> tuple[bool, str]:
        message = message.strip()
        if not message:
            return False, "Message cannot be empty."
        if len(message) > 500:
            return False, "Message must be 500 characters or fewer."
        return True, "OK"

    # ── Core operations ─────────────────────────

    def send_notification(self, sender: str, receiver: str, message: str) -> bool:
        """Create and deliver a new notification."""
        sender   = sender.strip()
        receiver = receiver.strip()
        message  = message.strip()

        ok, msg = self._validate_name(sender, "Sender")
        if not ok:
            print(f"  [!] {msg}")
            return False

        ok, msg = self._validate_name(receiver, "Receiver")
        if not ok:
            print(f"  [!] {msg}")
            return False

        ok, msg = self._validate_message(message)
        if not ok:
            print(f"  [!] {msg}")
            return False

        notification = Notification(self._next_id(), message, sender, receiver)
        self.__store.setdefault(receiver, []).append(notification)
        print(f"  [✓] Notification #{notification.notification_id} sent to '{receiver}'.")
        return True

    def mark_as_read(self, notification_id: int) -> bool:
        """Mark a single notification as read by its ID."""
        n, _ = self._find_by_id(notification_id)
        if n is None:
            print(f"  [!] Notification #{notification_id} not found.")
            return False
        if n.is_read:
            print(f"  [~] Notification #{notification_id} is already marked as read.")
            return True
        n.mark_as_read()
        print(f"  [✓] Notification #{notification_id} marked as read.")
        return True

    def mark_all_read_for_user(self, receiver: str) -> bool:
        """Mark all notifications for a user as read."""
        receiver = receiver.strip()
        notes = self.__store.get(receiver)
        if not notes:
            print(f"  [!] No notifications found for '{receiver}'.")
            return False
        count = sum(1 for n in notes if not n.is_read)
        for n in notes:
            n.mark_as_read()
        print(f"  [✓] {count} notification(s) marked as read for '{receiver}'.")
        return True

    def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification by its ID."""
        n, receiver = self._find_by_id(notification_id)
        if n is None:
            print(f"  [!] Notification #{notification_id} not found.")
            return False
        self.__store[receiver].remove(n)
        print(f"  [✓] Notification #{notification_id} deleted.")
        return True

    def delete_all_for_user(self, receiver: str) -> bool:
        """Delete all notifications for a specific user."""
        receiver = receiver.strip()
        if receiver not in self.__store or not self.__store[receiver]:
            print(f"  [!] No notifications found for '{receiver}'.")
            return False
        count = len(self.__store[receiver])
        self.__store[receiver].clear()
        print(f"  [✓] {count} notification(s) deleted for '{receiver}'.")
        return True

    # ── Display operations ──────────────────────

    def display_for_user(self, receiver: str, filter_status: str = "all"):
        """
        Print notifications for a specific user.
        filter_status: 'all' | 'unread' | 'read'
        """
        receiver = receiver.strip()
        notes = self.__store.get(receiver, [])

        if filter_status == "unread":
            notes = [n for n in notes if not n.is_read]
            label = "Unread"
        elif filter_status == "read":
            notes = [n for n in notes if n.is_read]
            label = "Read"
        else:
            label = "All"

        if not notes:
            print(f"  [~] No {label.lower()} notifications for '{receiver}'.")
            return

        print(f"\n  ┌─ {label} Notifications for '{receiver}' ({len(notes)}) " + "─" * 20)
        for n in notes:
            icon = "📬" if not n.is_read else "📭"
            print(f"  │")
            print(f"  │  {icon} ID #{n.notification_id}  [{n.status}]  •  {n.timestamp}")
            print(f"  │     From    : {n.sender}")
            print(f"  │     Message : {n.message}")
        print("  └" + "─" * 55)

    def display_all(self):
        """Print every notification in the system (admin view)."""
        all_notes = self._all_notifications()
        if not all_notes:
            print("  [~] No notifications in the system.")
            return
        print(f"\n  ┌─ All Notifications in System ({len(all_notes)}) " + "─" * 20)
        for n in all_notes:
            icon = "📬" if not n.is_read else "📭"
            print(f"  │")
            print(f"  │  {icon} ID #{n.notification_id}  [{n.status}]  •  {n.timestamp}")
            print(f"  │     From → To : {n.sender} → {n.receiver}")
            print(f"  │     Message   : {n.message}")
        print("  └" + "─" * 55)

    def summary(self) -> dict:
        """Return system-wide counts."""
        all_notes = self._all_notifications()
        return {
            "total":   len(all_notes),
            "unread":  sum(1 for n in all_notes if not n.is_read),
            "read":    sum(1 for n in all_notes if n.is_read),
            "users":   len(self.__store),
        }

    def list_users(self) -> list[str]:
        return list(self.__store.keys())


# ─────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────

def _clear():
    os.system("cls" if os.name == "nt" else "clear")

def _inp(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""

def _pause():
    input("\n  Press Enter to continue...")

def _divider():
    print("  " + "─" * 50)

def _banner(mgr: NotificationManager):
    s = mgr.summary()
    print("""
╔══════════════════════════════════════════════════╗
║        🔔  Notification Management System        ║
╚══════════════════════════════════════════════════╝""")
    print(f"  System  →  Total: {s['total']}  |  "
          f"Unread: {s['unread']}  |  "
          f"Read: {s['read']}  |  "
          f"Users: {s['users']}")

def _get_id(label: str = "Notification ID") -> int | None:
    raw = _inp(f"  {label}: ")
    if not raw.isdigit():
        print("  [!] Please enter a valid numeric ID.")
        return None
    return int(raw)


# ─────────────────────────────────────────────
#  MENU HANDLERS
# ─────────────────────────────────────────────

def menu_send(mgr: NotificationManager):
    print("\n  ── Send Notification ──────────────────────")
    sender   = _inp("  From (sender)   : ")
    receiver = _inp("  To   (receiver) : ")
    message  = _inp("  Message         : ")
    mgr.send_notification(sender, receiver, message)


def menu_view_user(mgr: NotificationManager):
    print("\n  ── View Notifications for User ────────────")
    users = mgr.list_users()
    if users:
        print(f"  Known users: {', '.join(users)}")
    receiver = _inp("  Username : ")
    print("  Filter  →  [1] All  [2] Unread  [3] Read")
    flt = _inp("  Choice   : ")
    mapping = {"1": "all", "2": "unread", "3": "read"}
    mgr.display_for_user(receiver, mapping.get(flt, "all"))


def menu_mark_read(mgr: NotificationManager):
    print("\n  ── Mark as Read ───────────────────────────")
    print("  [1] Mark single notification")
    print("  [2] Mark all for a user")
    choice = _inp("  Choice : ")
    if choice == "1":
        nid = _get_id()
        if nid is not None:
            mgr.mark_as_read(nid)
    elif choice == "2":
        users = mgr.list_users()
        if users:
            print(f"  Known users: {', '.join(users)}")
        receiver = _inp("  Username : ")
        mgr.mark_all_read_for_user(receiver)
    else:
        print("  [!] Invalid choice.")


def menu_delete(mgr: NotificationManager):
    print("\n  ── Delete Notification ────────────────────")
    print("  [1] Delete single notification")
    print("  [2] Delete all for a user")
    choice = _inp("  Choice : ")
    if choice == "1":
        nid = _get_id()
        if nid is not None:
            confirm = _inp(f"  Delete notification #{nid}? (y/n): ").lower()
            if confirm == "y":
                mgr.delete_notification(nid)
            else:
                print("  [~] Cancelled.")
    elif choice == "2":
        users = mgr.list_users()
        if users:
            print(f"  Known users: {', '.join(users)}")
        receiver = _inp("  Username : ")
        confirm  = _inp(f"  Delete ALL notifications for '{receiver}'? (y/n): ").lower()
        if confirm == "y":
            mgr.delete_all_for_user(receiver)
        else:
            print("  [~] Cancelled.")
    else:
        print("  [!] Invalid choice.")


def menu_all(mgr: NotificationManager):
    print()
    mgr.display_all()


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

MENU = """
  ── Main Menu ──────────────────────────────
    [1] Send a notification
    [2] View notifications for a user
    [3] Mark notification(s) as read
    [4] Delete notification(s)
    [5] View all notifications (system-wide)
    [0] Exit
  ───────────────────────────────────────────"""

def main():
    mgr = NotificationManager()

    # Seed a few demo notifications so the system isn't empty on first run
    mgr.send_notification("system",  "alice", "Welcome to the platform! 🎉")
    mgr.send_notification("bob",     "alice", "Hey Alice, can we meet tomorrow?")
    mgr.send_notification("alice",   "bob",   "Sure Bob, 10 AM works for me.")
    mgr.send_notification("system",  "bob",   "Your password was changed successfully.")

    while True:
        _clear()
        _banner(mgr)
        print(MENU)
        _divider()
        choice = _inp("  Choice: ")
        print()

        if   choice == "1": menu_send(mgr)
        elif choice == "2": menu_view_user(mgr)
        elif choice == "3": menu_mark_read(mgr)
        elif choice == "4": menu_delete(mgr)
        elif choice == "5": menu_all(mgr)
        elif choice == "0":
            print("  Goodbye! 👋\n")
            break
        else:
            print("  [!] Invalid option. Please choose from the menu.")

        _pause()


if __name__ == "__main__":
    main()