"""
unix_file_permission_system.py
A Python OOP simulation of a UNIX-like file permission system.
"""

from __future__ import annotations
import re
import sys
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────

class PermissionError_(Exception):
    """Raised when a user lacks the required permission."""


class FileNotFoundError_(Exception):
    """Raised when a file does not exist in the registry."""


class UserNotFoundError(Exception):
    """Raised when a user is not found in the registry."""


class ValidationError(Exception):
    """Raised for invalid input values."""


# ──────────────────────────────────────────────
# Permission
# ──────────────────────────────────────────────

class Permission:
    """
    Represents a three-character permission triplet: r, w, x.

    Internally stored as three booleans; can be constructed from
    an octal digit (0-7) or an rwx string.
    """

    def __init__(self, read: bool = False, write: bool = False, execute: bool = False):
        self.read = read
        self.write = write
        self.execute = execute

    # ── Factory helpers ──────────────────────

    @classmethod
    def from_octal(cls, digit: int) -> "Permission":
        """Create a Permission from a single octal digit (0-7)."""
        if not (0 <= digit <= 7):
            raise ValidationError(f"Octal digit must be 0-7, got {digit}.")
        return cls(
            read=bool(digit & 4),
            write=bool(digit & 2),
            execute=bool(digit & 1),
        )

    @classmethod
    def from_rwx(cls, rwx: str) -> "Permission":
        """Create a Permission from a 3-char rwx string, e.g. 'rwx', 'r--'."""
        if len(rwx) != 3:
            raise ValidationError(f"rwx string must be exactly 3 characters, got '{rwx}'.")
        read    = rwx[0] == "r"
        write   = rwx[1] == "w"
        execute = rwx[2] == "x"
        # Validate characters
        valid = {"r": ("r", "-"), "w": ("w", "-"), "x": ("x", "-")}
        if rwx[0] not in valid["r"] or rwx[1] not in valid["w"] or rwx[2] not in valid["x"]:
            raise ValidationError(f"Invalid rwx string: '{rwx}'.")
        return cls(read=read, write=write, execute=execute)

    # ── Conversions ──────────────────────────

    def to_octal(self) -> int:
        return (4 if self.read else 0) | (2 if self.write else 0) | (1 if self.execute else 0)

    def __str__(self) -> str:
        return (
            ("r" if self.read    else "-") +
            ("w" if self.write   else "-") +
            ("x" if self.execute else "-")
        )

    def __repr__(self) -> str:
        return f"Permission('{self}')"


# ──────────────────────────────────────────────
# User
# ──────────────────────────────────────────────

class User:
    """Represents a system user with a unique ID, username, and group."""

    def __init__(self, user_id: int, username: str, group: str):
        if not isinstance(user_id, int) or user_id < 0:
            raise ValidationError("user_id must be a non-negative integer.")
        if not username or not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            raise ValidationError(
                f"Invalid username '{username}'. Use letters, digits, '_', '-', '.'.")
        if not group or not re.match(r"^[a-zA-Z0-9_.-]+$", group):
            raise ValidationError(
                f"Invalid group name '{group}'. Use letters, digits, '_', '-', '.'.")

        self.user_id  = user_id
        self.username = username
        self.group    = group

    def __str__(self) -> str:
        return f"{self.username}(uid={self.user_id}, group={self.group})"

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id}, username='{self.username}', group='{self.group}')"


# ──────────────────────────────────────────────
# File
# ──────────────────────────────────────────────

class File:
    """
    Represents a file in the simulated filesystem.

    Permissions are stored as three Permission objects:
        owner_perm, group_perm, others_perm
    """

    def __init__(
        self,
        file_name:   str,
        owner:       User,
        group:       str,
        owner_perm:  Permission,
        group_perm:  Permission,
        others_perm: Permission,
    ):
        if not file_name or not re.match(r"^[\w.\-]+$", file_name):
            raise ValidationError(
                f"Invalid file name '{file_name}'. Use letters, digits, '.', '_', '-'.")
        if not group or not re.match(r"^[a-zA-Z0-9_.-]+$", group):
            raise ValidationError(f"Invalid group name '{group}'.")

        self.file_name   = file_name
        self.owner       = owner
        self.group       = group
        self.owner_perm  = owner_perm
        self.group_perm  = group_perm
        self.others_perm = others_perm

    # ── Display ──────────────────────────────

    def permission_string(self) -> str:
        """Return the classic ls-style permission string, e.g. '-rwxr-xr--'."""
        return f"-{self.owner_perm}{self.group_perm}{self.others_perm}"

    def octal_string(self) -> str:
        return (
            str(self.owner_perm.to_octal())
            + str(self.group_perm.to_octal())
            + str(self.others_perm.to_octal())
        )

    def __str__(self) -> str:
        return (
            f"{self.permission_string()}  "
            f"{self.owner.username}  {self.group}  {self.file_name}"
        )


# ──────────────────────────────────────────────
# PermissionManager
# ──────────────────────────────────────────────

class PermissionManager:
    """
    Central manager for file permissions, ownership, and access checks.

    Acts as the single source of truth for registered users and files.
    """

    def __init__(self):
        self._users: dict[str, User] = {}   # username → User
        self._files: dict[str, File] = {}   # file_name → File

    # ── Registry helpers ─────────────────────

    def add_user(self, user: User) -> None:
        if user.username in self._users:
            raise ValidationError(f"User '{user.username}' already exists.")
        self._users[user.username] = user

    def get_user(self, username: str) -> User:
        if username not in self._users:
            raise UserNotFoundError(f"User '{username}' not found.")
        return self._users[username]

    def add_file(self, file: File) -> None:
        if file.file_name in self._files:
            raise ValidationError(f"File '{file.file_name}' already exists.")
        self._files[file.file_name] = file

    def get_file(self, file_name: str) -> File:
        if file_name not in self._files:
            raise FileNotFoundError_(f"File '{file_name}' not found.")
        return self._files[file_name]

    def list_users(self) -> list[User]:
        return list(self._users.values())

    def list_files(self) -> list[File]:
        return list(self._files.values())

    # ── Access determination ─────────────────

    def _resolve_permission(self, user: User, file: File) -> Permission:
        """Return the effective Permission triplet for *user* on *file*."""
        if user.username == file.owner.username:
            return file.owner_perm
        if user.group == file.group:
            return file.group_perm
        return file.others_perm

    def can_read(self, username: str, file_name: str) -> bool:
        user = self.get_user(username)
        file = self.get_file(file_name)
        return self._resolve_permission(user, file).read

    def can_write(self, username: str, file_name: str) -> bool:
        user = self.get_user(username)
        file = self.get_file(file_name)
        return self._resolve_permission(user, file).write

    def can_execute(self, username: str, file_name: str) -> bool:
        user = self.get_user(username)
        file = self.get_file(file_name)
        return self._resolve_permission(user, file).execute

    def check_access(self, username: str, file_name: str) -> dict[str, bool]:
        """Return a dict with read/write/execute booleans for the user."""
        return {
            "read":    self.can_read(username, file_name),
            "write":   self.can_write(username, file_name),
            "execute": self.can_execute(username, file_name),
        }

    # ── chmod ────────────────────────────────

    def chmod(self, requestor: str, file_name: str, octal_mode: str) -> None:
        """
        Change file permissions.  Only the file owner may chmod.
        *octal_mode* must be a 3-digit string like '755' or '644'.
        """
        user = self.get_user(requestor)
        file = self.get_file(file_name)

        if file.owner.username != user.username:
            raise PermissionError_(
                f"'{requestor}' is not the owner of '{file_name}' and cannot chmod it.")

        if not re.fullmatch(r"[0-7]{3}", octal_mode):
            raise ValidationError(
                f"Octal mode must be a 3-digit string (0-7 each), got '{octal_mode}'.")

        file.owner_perm  = Permission.from_octal(int(octal_mode[0]))
        file.group_perm  = Permission.from_octal(int(octal_mode[1]))
        file.others_perm = Permission.from_octal(int(octal_mode[2]))

    # ── chown ────────────────────────────────

    def chown(
        self,
        requestor:    str,
        file_name:    str,
        new_owner:    Optional[str] = None,
        new_group:    Optional[str] = None,
    ) -> None:
        """
        Change file ownership.  Only the current owner may chown.
        Pass *new_owner* and/or *new_group*; omit to leave unchanged.
        """
        user = self.get_user(requestor)
        file = self.get_file(file_name)

        if file.owner.username != user.username:
            raise PermissionError_(
                f"'{requestor}' is not the owner of '{file_name}' and cannot chown it.")

        if new_owner is not None:
            new_owner_user = self.get_user(new_owner)   # validates existence
            file.owner = new_owner_user

        if new_group is not None:
            if not re.match(r"^[a-zA-Z0-9_.-]+$", new_group):
                raise ValidationError(f"Invalid group name '{new_group}'.")
            file.group = new_group


# ──────────────────────────────────────────────
# Console UI helpers
# ──────────────────────────────────────────────

BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║         UNIX-like File Permission System Simulator       ║
╚══════════════════════════════════════════════════════════╝
"""

MENU = """
┌─────────────────────────────────────┐
│  1. Add user                        │
│  2. List users                      │
│  3. Create file                     │
│  4. List files                      │
│  5. chmod  (change permissions)     │
│  6. chown  (change ownership)       │
│  7. Check access rights             │
│  0. Exit                            │
└─────────────────────────────────────┘
"""


def _input(prompt: str) -> str:
    """Thin wrapper so we can intercept EOF gracefully."""
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        sys.exit(0)


def _ok(msg: str)  -> None: print(f"  ✔  {msg}")
def _err(msg: str) -> None: print(f"  ✘  {msg}")


# ──────────────────────────────────────────────
# Individual menu actions
# ──────────────────────────────────────────────

def action_add_user(pm: PermissionManager) -> None:
    print("\n── Add User ──")
    uid_raw  = _input("  user_id  : ")
    username = _input("  username : ")
    group    = _input("  group    : ")
    try:
        uid = int(uid_raw)
    except ValueError:
        _err("user_id must be an integer.")
        return
    try:
        user = User(uid, username, group)
        pm.add_user(user)
        _ok(f"User {user} added.")
    except (ValidationError, Exception) as exc:
        _err(str(exc))


def action_list_users(pm: PermissionManager) -> None:
    users = pm.list_users()
    if not users:
        print("  (no users registered)")
        return
    print(f"\n  {'UID':<6} {'Username':<16} {'Group'}")
    print("  " + "─" * 36)
    for u in users:
        print(f"  {u.user_id:<6} {u.username:<16} {u.group}")


def action_create_file(pm: PermissionManager) -> None:
    print("\n── Create File ──")
    file_name = _input("  file name      : ")
    owner_name = _input("  owner username : ")
    group      = _input("  group          : ")
    print("  Enter permissions as a 3-digit octal (e.g. 755 = rwxr-xr-x).")
    octal = _input("  octal mode     : ")

    if not re.fullmatch(r"[0-7]{3}", octal):
        _err("Octal mode must be exactly 3 digits (0-7 each).")
        return
    try:
        owner = pm.get_user(owner_name)
        perm_owner  = Permission.from_octal(int(octal[0]))
        perm_group  = Permission.from_octal(int(octal[1]))
        perm_others = Permission.from_octal(int(octal[2]))
        f = File(file_name, owner, group, perm_owner, perm_group, perm_others)
        pm.add_file(f)
        _ok(f"File created: {f}")
    except (UserNotFoundError, FileNotFoundError_, ValidationError, Exception) as exc:
        _err(str(exc))


def action_list_files(pm: PermissionManager) -> None:
    files = pm.list_files()
    if not files:
        print("  (no files registered)")
        return
    print(f"\n  {'Permissions':<12} {'Owner':<12} {'Group':<12} {'Name'}")
    print("  " + "─" * 52)
    for f in files:
        print(f"  {f.permission_string():<12} {f.owner.username:<12} {f.group:<12} {f.file_name}")


def action_chmod(pm: PermissionManager) -> None:
    print("\n── chmod ──")
    requestor = _input("  your username  : ")
    file_name = _input("  file name      : ")
    octal     = _input("  new octal mode : ")
    try:
        pm.chmod(requestor, file_name, octal)
        f = pm.get_file(file_name)
        _ok(f"Permissions updated: {f.permission_string()}  ({f.octal_string()})")
    except (PermissionError_, FileNotFoundError_, UserNotFoundError, ValidationError) as exc:
        _err(str(exc))


def action_chown(pm: PermissionManager) -> None:
    print("\n── chown ──  (leave blank to keep unchanged)")
    requestor = _input("  your username    : ")
    file_name = _input("  file name        : ")
    new_owner = _input("  new owner (user) : ") or None
    new_group = _input("  new group        : ") or None
    try:
        pm.chown(requestor, file_name, new_owner, new_group)
        f = pm.get_file(file_name)
        _ok(f"Ownership updated → owner: {f.owner.username}, group: {f.group}")
    except (PermissionError_, FileNotFoundError_, UserNotFoundError, ValidationError) as exc:
        _err(str(exc))


def action_check_access(pm: PermissionManager) -> None:
    print("\n── Check Access Rights ──")
    username  = _input("  username  : ")
    file_name = _input("  file name : ")
    try:
        access = pm.check_access(username, file_name)
        f    = pm.get_file(file_name)
        user = pm.get_user(username)

        # Determine which permission set is being applied
        if user.username == f.owner.username:
            role = "owner"
        elif user.group == f.group:
            role = "group member"
        else:
            role = "others"

        print(f"\n  File  : {f.file_name}  [{f.permission_string()}]")
        print(f"  User  : {user}  (matched as: {role})")
        print(f"\n  {'Permission':<10} {'Allowed'}")
        print("  " + "─" * 22)
        for perm, allowed in access.items():
            icon = "✔" if allowed else "✘"
            print(f"  {perm:<10} {icon}")
    except (UserNotFoundError, FileNotFoundError_) as exc:
        _err(str(exc))


# ──────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────

def _seed_demo(pm: PermissionManager) -> None:
    """Pre-populate with a tiny demo dataset so the user can explore immediately."""
    root  = User(0,    "root",  "root")
    alice = User(1001, "alice", "staff")
    bob   = User(1002, "bob",   "staff")
    carol = User(1003, "carol", "guests")

    for u in (root, alice, bob, carol):
        pm.add_user(u)

    # -rwxr-xr-- root:root
    pm.add_file(File("script.sh", root, "root",
                     Permission.from_octal(7),
                     Permission.from_octal(5),
                     Permission.from_octal(4)))

    # -rw-r--r-- alice:staff
    pm.add_file(File("report.txt", alice, "staff",
                     Permission.from_octal(6),
                     Permission.from_octal(4),
                     Permission.from_octal(4)))

    # -rwxrwx--- alice:staff
    pm.add_file(File("shared.py", alice, "staff",
                     Permission.from_octal(7),
                     Permission.from_octal(7),
                     Permission.from_octal(0)))

    print("  Demo data loaded: users (root, alice, bob, carol) and files"
          " (script.sh, report.txt, shared.py).")


def main() -> None:
    pm = PermissionManager()
    print(BANNER)

    seed = _input("Load demo data? [Y/n]: ")
    if seed.lower() != "n":
        _seed_demo(pm)

    dispatch = {
        "1": action_add_user,
        "2": action_list_users,
        "3": action_create_file,
        "4": action_list_files,
        "5": action_chmod,
        "6": action_chown,
        "7": action_check_access,
    }

    while True:
        print(MENU)
        choice = _input("Select an option: ")
        if choice == "0":
            print("Goodbye.")
            break
        handler = dispatch.get(choice)
        if handler:
            handler(pm)
        else:
            _err(f"Unknown option '{choice}'. Please choose 0-7.")


if __name__ == "__main__":
    main()