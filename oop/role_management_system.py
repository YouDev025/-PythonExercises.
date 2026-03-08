"""
Role Management System
An OOP-based system for managing users, roles, and permissions via a CLI menu.
"""

import os
from datetime import datetime


# ─────────────────────────────────────────────
#  ROLE CLASS
# ─────────────────────────────────────────────

class Role:
    """Represents a role with a set of permissions."""

    # Master catalogue of recognised permissions
    ALL_PERMISSIONS = {
        "read", "write", "delete", "update",
        "manage_users", "manage_roles", "view_reports",
        "export_data", "import_data", "audit_logs",
    }

    def __init__(self, role_name: str, permissions: set[str] | None = None):
        self.__role_name: str       = self._clean_name(role_name)
        self.__permissions: set[str] = set()
        self.__created_at: str      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if permissions:
            for p in permissions:
                self._add_permission(p)

    # ── Validation helpers ──────────────────────

    @staticmethod
    def _clean_name(name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Role name cannot be empty.")
        if len(name) > 40:
            raise ValueError("Role name must be 40 characters or fewer.")
        return name

    def _add_permission(self, perm: str) -> bool:
        perm = perm.strip().lower()
        if perm not in self.ALL_PERMISSIONS:
            return False
        self.__permissions.add(perm)
        return True

    # ── Read-only properties ────────────────────

    @property
    def role_name(self) -> str:
        return self.__role_name

    @property
    def permissions(self) -> frozenset[str]:
        return frozenset(self.__permissions)

    @property
    def created_at(self) -> str:
        return self.__created_at

    # ── Permission mutation ─────────────────────

    def add_permissions(self, perms: set[str]) -> tuple[set, set]:
        """Add permissions. Returns (added, invalid)."""
        added, invalid = set(), set()
        for p in perms:
            if self._add_permission(p):
                added.add(p)
            else:
                invalid.add(p)
        return added, invalid

    def remove_permissions(self, perms: set[str]) -> tuple[set, set]:
        """Remove permissions. Returns (removed, not_found)."""
        removed, not_found = set(), set()
        for p in perms:
            p = p.strip().lower()
            if p in self.__permissions:
                self.__permissions.discard(p)
                removed.add(p)
            else:
                not_found.add(p)
        return removed, not_found

    def has_permission(self, perm: str) -> bool:
        return perm.strip().lower() in self.__permissions

    def clear_permissions(self):
        self.__permissions.clear()

    # ── Display ─────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "Role Name":   self.__role_name,
            "Permissions": sorted(self.__permissions) or ["(none)"],
            "Created At":  self.__created_at,
        }

    def __repr__(self) -> str:
        return f"Role(name='{self.__role_name}', permissions={sorted(self.__permissions)})"


# ─────────────────────────────────────────────
#  USER CLASS
# ─────────────────────────────────────────────

class User:
    """Represents a system user with an assigned role."""

    def __init__(self, user_id: int, username: str, role: Role):
        self.__user_id: int    = user_id
        self.__username: str   = self._clean_username(username)
        self.__role: Role      = role
        self.__created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Validation ──────────────────────────────

    @staticmethod
    def _clean_username(name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Username cannot be empty.")
        if len(name) > 30:
            raise ValueError("Username must be 30 characters or fewer.")
        if not all(c.isalnum() or c in "_-" for c in name):
            raise ValueError("Username may only contain letters, digits, hyphens, and underscores.")
        return name

    # ── Read-only properties ────────────────────

    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def role(self) -> Role:
        return self.__role

    @property
    def created_at(self) -> str:
        return self.__created_at

    # ── Role mutation ───────────────────────────

    def assign_role(self, role: Role):
        self.__role = role

    def has_permission(self, perm: str) -> bool:
        return self.__role.has_permission(perm)

    # ── Display ─────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "User ID":     self.__user_id,
            "Username":    self.__username,
            "Role":        self.__role.role_name,
            "Permissions": sorted(self.__role.permissions) or ["(none)"],
            "Created At":  self.__created_at,
        }

    def __repr__(self) -> str:
        return f"User(id={self.__user_id}, username='{self.__username}', role='{self.__role.role_name}')"


# ─────────────────────────────────────────────
#  ROLE MANAGER CLASS
# ─────────────────────────────────────────────

class RoleManager:
    """Central manager for roles and users."""

    def __init__(self):
        self.__roles: dict[str, Role] = {}           # role_name (lower) → Role
        self.__users: dict[str, User] = {}           # username  (lower) → User
        self.__next_user_id: int      = 1
        self._seed_defaults()

    # ── Internal helpers ────────────────────────

    def _next_id(self) -> int:
        uid = self.__next_user_id
        self.__next_user_id += 1
        return uid

    def _get_role(self, name: str) -> "Role | None":
        return self.__roles.get(name.strip().lower())

    def _get_user(self, username: str) -> "User | None":
        return self.__users.get(username.strip().lower())

    def _seed_defaults(self):
        """Seed sensible default roles."""
        defaults = {
            "Admin":     Role.ALL_PERMISSIONS,
            "Editor":    {"read", "write", "update", "view_reports"},
            "Viewer":    {"read", "view_reports"},
            "Moderator": {"read", "write", "delete", "audit_logs"},
            "Guest":     {"read"},
        }
        for name, perms in defaults.items():
            self.create_role(name, perms, _silent=True)

    # ── Role operations ─────────────────────────

    def create_role(self, role_name: str, permissions: set[str] | None = None,
                    _silent: bool = False) -> "Role | None":
        key = role_name.strip().lower()
        if not key:
            if not _silent:
                print("  [!] Role name cannot be empty.")
            return None
        if key in self.__roles:
            if not _silent:
                print(f"  [!] Role '{role_name}' already exists.")
            return None
        try:
            role = Role(role_name, permissions or set())
            self.__roles[key] = role
            if not _silent:
                print(f"  [✓] Role '{role.role_name}' created with permissions: "
                      f"{sorted(role.permissions) or ['(none)']}")
            return role
        except ValueError as exc:
            if not _silent:
                print(f"  [!] {exc}")
            return None

    def remove_role(self, role_name: str) -> bool:
        key  = role_name.strip().lower()
        role = self.__roles.get(key)
        if not role:
            print(f"  [!] Role '{role_name}' does not exist.")
            return False
        # Prevent deletion if users are assigned
        assigned = [u for u in self.__users.values() if u.role.role_name.lower() == key]
        if assigned:
            names = ", ".join(u.username for u in assigned)
            print(f"  [!] Cannot delete '{role_name}' — assigned to: {names}.")
            print("  [~] Re-assign those users first, then delete the role.")
            return False
        del self.__roles[key]
        print(f"  [✓] Role '{role_name}' removed.")
        return True

    def add_permissions_to_role(self, role_name: str, perms: set[str]) -> bool:
        role = self._get_role(role_name)
        if not role:
            print(f"  [!] Role '{role_name}' not found.")
            return False
        added, invalid = role.add_permissions(perms)
        if added:
            print(f"  [✓] Added to '{role.role_name}': {sorted(added)}")
        if invalid:
            print(f"  [~] Not recognised (ignored): {sorted(invalid)}")
            print(f"  [~] Valid permissions: {sorted(Role.ALL_PERMISSIONS)}")
        return True

    def remove_permissions_from_role(self, role_name: str, perms: set[str]) -> bool:
        role = self._get_role(role_name)
        if not role:
            print(f"  [!] Role '{role_name}' not found.")
            return False
        removed, not_found = role.remove_permissions(perms)
        if removed:
            print(f"  [✓] Removed from '{role.role_name}': {sorted(removed)}")
        if not_found:
            print(f"  [~] Not in role (skipped): {sorted(not_found)}")
        return True

    def clear_role_permissions(self, role_name: str) -> bool:
        role = self._get_role(role_name)
        if not role:
            print(f"  [!] Role '{role_name}' not found.")
            return False
        role.clear_permissions()
        print(f"  [✓] All permissions cleared for '{role.role_name}'.")
        return True

    # ── User operations ─────────────────────────

    def create_user(self, username: str, role_name: str) -> "User | None":
        key  = username.strip().lower()
        if key in self.__users:
            print(f"  [!] Username '{username}' already exists.")
            return None
        role = self._get_role(role_name)
        if not role:
            print(f"  [!] Role '{role_name}' not found. Create it first.")
            return None
        try:
            user = User(self._next_id(), username, role)
            self.__users[key] = user
            print(f"  [✓] User '{user.username}' created with role '{role.role_name}'.")
            return user
        except ValueError as exc:
            print(f"  [!] {exc}")
            return None

    def assign_role_to_user(self, username: str, role_name: str) -> bool:
        user = self._get_user(username)
        if not user:
            print(f"  [!] User '{username}' not found.")
            return False
        role = self._get_role(role_name)
        if not role:
            print(f"  [!] Role '{role_name}' not found.")
            return False
        old = user.role.role_name
        user.assign_role(role)
        print(f"  [✓] '{username}' role changed: '{old}' → '{role.role_name}'.")
        return True

    def remove_user(self, username: str) -> bool:
        key = username.strip().lower()
        if key not in self.__users:
            print(f"  [!] User '{username}' not found.")
            return False
        del self.__users[key]
        print(f"  [✓] User '{username}' removed.")
        return True

    def check_user_permission(self, username: str, perm: str) -> bool | None:
        user = self._get_user(username)
        if not user:
            print(f"  [!] User '{username}' not found.")
            return None
        result = user.has_permission(perm)
        icon   = "✅" if result else "❌"
        print(f"  {icon}  '{username}' {'has' if result else 'does NOT have'} "
              f"permission: '{perm}'.")
        return result

    # ── Display operations ──────────────────────

    def display_all_roles(self):
        if not self.__roles:
            print("  [~] No roles defined.")
            return
        print(f"\n  ┌─ All Roles ({len(self.__roles)}) {'─' * 40}")
        for role in self.__roles.values():
            perms = ", ".join(sorted(role.permissions)) or "(none)"
            print(f"  │")
            print(f"  │  🏷️  {role.role_name}")
            print(f"  │       Permissions : {perms}")
            print(f"  │       Created     : {role.created_at}")
        print("  └" + "─" * 55)

    def display_all_users(self):
        if not self.__users:
            print("  [~] No users registered.")
            return
        print(f"\n  ┌─ All Users ({len(self.__users)}) {'─' * 40}")
        for user in self.__users.values():
            perms = ", ".join(sorted(user.role.permissions)) or "(none)"
            print(f"  │")
            print(f"  │  👤 [{user.user_id:>3}] {user.username:<20}  role: {user.role.role_name}")
            print(f"  │        Permissions : {perms}")
            print(f"  │        Created     : {user.created_at}")
        print("  └" + "─" * 55)

    def display_user(self, username: str):
        user = self._get_user(username)
        if not user:
            print(f"  [!] User '{username}' not found.")
            return
        d    = user.to_dict()
        perms = ", ".join(d["Permissions"])
        print(f"""
  ┌─ User Detail {'─' * 40}
  │   User ID    : {d['User ID']}
  │   Username   : {d['Username']}
  │   Role       : {d['Role']}
  │   Permissions: {perms}
  │   Created At : {d['Created At']}
  └{'─' * 54}""")

    def display_role(self, role_name: str):
        role = self._get_role(role_name)
        if not role:
            print(f"  [!] Role '{role_name}' not found.")
            return
        assigned = [u.username for u in self.__users.values()
                    if u.role.role_name.lower() == role_name.strip().lower()]
        perms = ", ".join(sorted(role.permissions)) or "(none)"
        print(f"""
  ┌─ Role Detail {'─' * 40}
  │   Role Name  : {role.role_name}
  │   Permissions: {perms}
  │   Users      : {', '.join(assigned) or '(none)'}
  │   Created At : {role.created_at}
  └{'─' * 54}""")

    def display_summary(self):
        print(f"""
  ┌─ System Summary {'─' * 36}
  │   Roles  : {len(self.__roles)}   ({', '.join(r.role_name for r in self.__roles.values())})
  │   Users  : {len(self.__users)}
  └{'─' * 54}""")

    # ── Listing helpers for menus ───────────────

    def list_role_names(self) -> list[str]:
        return [r.role_name for r in self.__roles.values()]

    def list_usernames(self) -> list[str]:
        return [u.username for u in self.__users.values()]


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
    print("  " + "─" * 52)

def _banner(rm: RoleManager):
    roles  = rm.list_role_names()
    users  = rm.list_usernames()
    print(f"""
╔══════════════════════════════════════════════════════╗
║          🛡️   Role Management System                 ║
╚══════════════════════════════════════════════════════╝
  Roles ({len(roles)}): {', '.join(roles) or '—'}
  Users ({len(users)}): {', '.join(users) or '—'}""")

def _pick_from(label: str, options: list[str]) -> str:
    """Show a numbered list and return the chosen item or raw input."""
    if options:
        print(f"  Available {label}: " + ", ".join(f"[{i+1}] {o}" for i, o in enumerate(options)))
    raw = _inp(f"  {label}: ")
    # Allow numeric shortcut
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    return raw

def _pick_permissions(prompt: str = "Permissions") -> set[str]:
    print(f"  Available: {', '.join(sorted(Role.ALL_PERMISSIONS))}")
    raw = _inp(f"  {prompt} (comma-separated): ")
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


# ─────────────────────────────────────────────
#  MENU HANDLERS
# ─────────────────────────────────────────────

def menu_role_management(rm: RoleManager):
    while True:
        print("""
  ── Role Management ──────────────────────────────
    [1] Create role
    [2] Remove role
    [3] Add permissions to role
    [4] Remove permissions from role
    [5] Clear all permissions from role
    [6] View all roles
    [7] View role detail
    [0] Back""")
        choice = _inp("  Choice: ")
        print()

        if choice == "1":
            name  = _inp("  Role name    : ")
            perms = _pick_permissions("Permissions")
            rm.create_role(name, perms)

        elif choice == "2":
            name = _pick_from("Role", rm.list_role_names())
            confirm = _inp(f"  Remove role '{name}'? (y/n): ").lower()
            if confirm == "y":
                rm.remove_role(name)
            else:
                print("  [~] Cancelled.")

        elif choice == "3":
            name  = _pick_from("Role", rm.list_role_names())
            perms = _pick_permissions("Permissions to add")
            rm.add_permissions_to_role(name, perms)

        elif choice == "4":
            name  = _pick_from("Role", rm.list_role_names())
            perms = _pick_permissions("Permissions to remove")
            rm.remove_permissions_from_role(name, perms)

        elif choice == "5":
            name = _pick_from("Role", rm.list_role_names())
            confirm = _inp(f"  Clear ALL permissions from '{name}'? (y/n): ").lower()
            if confirm == "y":
                rm.clear_role_permissions(name)
            else:
                print("  [~] Cancelled.")

        elif choice == "6":
            rm.display_all_roles()

        elif choice == "7":
            name = _pick_from("Role", rm.list_role_names())
            rm.display_role(name)

        elif choice == "0":
            break
        else:
            print("  [!] Invalid option.")

        _pause()


def menu_user_management(rm: RoleManager):
    while True:
        print("""
  ── User Management ──────────────────────────────
    [1] Create user
    [2] Remove user
    [3] Assign / change role
    [4] Check user permission
    [5] View all users
    [6] View user detail
    [0] Back""")
        choice = _inp("  Choice: ")
        print()

        if choice == "1":
            username = _inp("  Username : ")
            role     = _pick_from("Role", rm.list_role_names())
            rm.create_user(username, role)

        elif choice == "2":
            username = _pick_from("User", rm.list_usernames())
            confirm  = _inp(f"  Remove user '{username}'? (y/n): ").lower()
            if confirm == "y":
                rm.remove_user(username)
            else:
                print("  [~] Cancelled.")

        elif choice == "3":
            username = _pick_from("User", rm.list_usernames())
            role     = _pick_from("Role", rm.list_role_names())
            rm.assign_role_to_user(username, role)

        elif choice == "4":
            username = _pick_from("User", rm.list_usernames())
            perm     = _inp("  Permission to check: ")
            rm.check_user_permission(username, perm)

        elif choice == "5":
            rm.display_all_users()

        elif choice == "6":
            username = _pick_from("User", rm.list_usernames())
            rm.display_user(username)

        elif choice == "0":
            break
        else:
            print("  [!] Invalid option.")

        _pause()


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

MAIN_MENU = """
  ── Main Menu ──────────────────────────────────
    [1] Role management
    [2] User management
    [3] System summary
    [0] Exit
  ───────────────────────────────────────────────"""

def _seed_users(rm: RoleManager):
    users = [
        ("alice",   "Admin"),
        ("bob",     "Editor"),
        ("carol",   "Viewer"),
        ("dave",    "Moderator"),
        ("eve",     "Guest"),
    ]
    for username, role in users:
        rm.create_user(username, role)


def main():
    rm = RoleManager()
    _seed_users(rm)

    while True:
        _clear()
        _banner(rm)
        print(MAIN_MENU)
        _divider()
        choice = _inp("  Choice: ")
        print()

        if   choice == "1": menu_role_management(rm)
        elif choice == "2": menu_user_management(rm)
        elif choice == "3": rm.display_summary()
        elif choice == "0":
            print("  Goodbye! 👋\n")
            break
        else:
            print("  [!] Invalid option. Please choose from the menu.")

        if choice not in ("1", "2"):
            _pause()


if __name__ == "__main__":
    main()