"""
permission_management_system.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A command-line Permission Management System built with Python OOP.

Features
  • Create / update / delete permissions
  • Create / update / delete users
  • Assign & revoke permissions for users
  • Role-based grouping of permissions
  • Permission inheritance via roles
  • Audit log of all changes
  • Search users by permission
  • Statistics dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────
#  ANSI COLOURS
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

# ─────────────────────────────────────────────────────────────
#  AUDIT LOG
# ─────────────────────────────────────────────────────────────
class AuditLog:
    """Append-only log of all system changes."""

    def __init__(self):
        self._entries: list[dict] = []

    def record(self, action: str, actor: str, target: str, detail: str = ""):
        self._entries.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action":    action,
            "actor":     actor,
            "target":    target,
            "detail":    detail,
        })

    def recent(self, n: int = 20) -> list[dict]:
        return list(reversed(self._entries[-n:]))

    def all_entries(self) -> list[dict]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


# ─────────────────────────────────────────────────────────────
#  PERMISSION
# ─────────────────────────────────────────────────────────────
class Permission:
    """A named capability that can be assigned to users."""

    _id_counter = 1

    # Common permission categories for validation hints
    CATEGORIES = ("read", "write", "delete", "admin", "execute",
                  "manage", "view", "export", "import", "custom")

    def __init__(self, name: str, description: str = "", category: str = "custom"):
        name = name.strip().lower().replace(" ", "_")
        if not name:
            raise ValueError("Permission name cannot be empty.")
        if not name.replace("_", "").replace(".", "").isalnum():
            raise ValueError(
                "Permission name may only contain letters, numbers, underscores, and dots."
            )
        if category not in self.CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. "
                f"Choose from: {', '.join(self.CATEGORIES)}."
            )

        self._permission_id = f"PRM-{Permission._id_counter:04d}"
        Permission._id_counter += 1
        self._name        = name
        self._description = description.strip()
        self._category    = category
        self._created_at  = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── properties ───────────────────────────────────────────
    @property
    def permission_id(self) -> str:  return self._permission_id
    @property
    def name(self) -> str:           return self._name
    @property
    def description(self) -> str:    return self._description
    @property
    def category(self) -> str:       return self._category
    @property
    def created_at(self) -> str:     return self._created_at

    # ── controlled update ─────────────────────────────────────
    def update(self, description: Optional[str] = None,
               category: Optional[str] = None):
        if description is not None:
            self._description = description.strip()
        if category is not None:
            if category not in self.CATEGORIES:
                raise ValueError(
                    f"Invalid category. Choose from: {', '.join(self.CATEGORIES)}."
                )
            self._category = category

    # ── display ──────────────────────────────────────────────
    def _cat_colour(self) -> str:
        return {
            "admin":   RED,
            "write":   YELLOW,
            "delete":  RED,
            "execute": MAGENTA,
            "manage":  CYAN,
            "read":    GREEN,
            "view":    GREEN,
            "export":  BLUE,
            "import":  BLUE,
        }.get(self._category, DIM)

    def badge(self) -> str:
        c = self._cat_colour()
        return f"{c}[{self._name}]{RESET}"

    def summary_row(self, colour: str = CYAN, index: int = 0) -> str:
        cat_c = self._cat_colour()
        return (
            f"  {DIM}{index:>3}.{RESET}  "
            f"{colour}{self._permission_id}{RESET}  "
            f"{BOLD}{self._name:<28}{RESET}  "
            f"{cat_c}{self._category:<10}{RESET}  "
            f"{DIM}{self._description[:40] or '—'}{RESET}"
        )

    def detail_card(self) -> str:
        sep = f"  {'─' * 58}"
        cat_c = self._cat_colour()
        return "\n".join([
            sep,
            f"  {BOLD}{CYAN}{self._permission_id}{RESET}",
            f"  {BOLD}Name        :{RESET} {self._name}",
            f"  {BOLD}Category    :{RESET} {cat_c}{self._category}{RESET}",
            f"  {BOLD}Description :{RESET} {self._description or '—'}",
            f"  {BOLD}Created     :{RESET} {self._created_at}",
            sep,
        ])

    def __str__(self) -> str:
        return self.detail_card()

    def __repr__(self) -> str:
        return f"Permission({self._permission_id!r}, {self._name!r})"


# ─────────────────────────────────────────────────────────────
#  ROLE  (named collection of permissions)
# ─────────────────────────────────────────────────────────────
class Role:
    """A named group of permissions that can be assigned wholesale to users."""

    _id_counter = 1

    def __init__(self, name: str, description: str = ""):
        name = name.strip().lower().replace(" ", "_")
        if not name:
            raise ValueError("Role name cannot be empty.")
        self._role_id    = f"ROL-{Role._id_counter:04d}"
        Role._id_counter += 1
        self._name       = name
        self._description= description.strip()
        self._permissions: dict[str, Permission] = {}   # perm_id → Permission
        self._created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    @property
    def role_id(self) -> str:     return self._role_id
    @property
    def name(self) -> str:        return self._name
    @property
    def description(self) -> str: return self._description
    @property
    def created_at(self) -> str:  return self._created_at

    def add_permission(self, perm: Permission):
        self._permissions[perm.permission_id] = perm

    def remove_permission(self, perm_id: str) -> bool:
        return self._permissions.pop(perm_id.upper(), None) is not None

    def get_permissions(self) -> list[Permission]:
        return list(self._permissions.values())

    def has_permission(self, perm_id: str) -> bool:
        return perm_id.upper() in self._permissions

    def summary_row(self, colour: str = CYAN, index: int = 0) -> str:
        badges = "  ".join(p.badge() for p in list(self._permissions.values())[:5])
        extra  = (f" {DIM}+{len(self._permissions)-5} more{RESET}"
                  if len(self._permissions) > 5 else "")
        return (
            f"  {DIM}{index:>3}.{RESET}  "
            f"{colour}{self._role_id}{RESET}  "
            f"{BOLD}{self._name:<22}{RESET}  "
            f"{len(self._permissions):>3} perm(s)  "
            f"{badges}{extra}"
        )

    def detail_card(self) -> str:
        sep = f"  {'─' * 60}"
        lines = [
            sep,
            f"  {BOLD}{CYAN}{self._role_id}{RESET}",
            f"  {BOLD}Name       :{RESET} {self._name}",
            f"  {BOLD}Description:{RESET} {self._description or '—'}",
            f"  {BOLD}Created    :{RESET} {self._created_at}",
            f"  {BOLD}Permissions:{RESET} ({len(self._permissions)})",
        ]
        for p in self._permissions.values():
            lines.append(f"    • {p.badge()}  {DIM}{p.description[:40]}{RESET}")
        lines.append(sep)
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Role({self._role_id!r}, {self._name!r})"


# ─────────────────────────────────────────────────────────────
#  USER
# ─────────────────────────────────────────────────────────────
class User:
    """A system user with directly-assigned permissions and/or roles."""

    _id_counter = 1

    def __init__(self, username: str, display_name: str = "",
                 email: str = ""):
        username = username.strip().lower()
        if not username:
            raise ValueError("Username cannot be empty.")
        if not username.replace("_", "").replace(".", "").isalnum():
            raise ValueError(
                "Username may only contain letters, numbers, underscores, and dots."
            )
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            raise ValueError(f"Invalid email: '{email}'.")

        self._user_id     = f"USR-{User._id_counter:04d}"
        User._id_counter += 1
        self._username    = username
        self._display_name= display_name.strip() or username
        self._email       = email.strip().lower()
        self._is_active   = True
        self._created_at  = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Direct permissions (perm_id → Permission)
        self._permissions: dict[str, Permission] = {}
        # Assigned roles (role_id → Role)
        self._roles: dict[str, Role] = {}

    # ── properties ───────────────────────────────────────────
    @property
    def user_id(self) -> str:       return self._user_id
    @property
    def username(self) -> str:      return self._username
    @property
    def display_name(self) -> str:  return self._display_name
    @property
    def email(self) -> str:         return self._email
    @property
    def is_active(self) -> bool:    return self._is_active
    @property
    def created_at(self) -> str:    return self._created_at

    # ── update ───────────────────────────────────────────────
    def update(self, display_name: Optional[str] = None,
               email: Optional[str] = None, is_active: Optional[bool] = None):
        if display_name is not None:
            self._display_name = display_name.strip() or self._username
        if email is not None:
            if email and ("@" not in email or "." not in email.split("@")[-1]):
                raise ValueError(f"Invalid email: '{email}'.")
            self._email = email.strip().lower()
        if is_active is not None:
            self._is_active = is_active

    # ── direct permissions ────────────────────────────────────
    def grant(self, perm: Permission) -> bool:
        """Grant a direct permission. Returns False if already held."""
        if perm.permission_id in self._permissions:
            return False
        self._permissions[perm.permission_id] = perm
        return True

    def revoke(self, perm_id: str) -> bool:
        """Remove a direct permission. Returns False if not found."""
        return self._permissions.pop(perm_id.upper(), None) is not None

    def direct_permissions(self) -> list[Permission]:
        return list(self._permissions.values())

    # ── roles ─────────────────────────────────────────────────
    def assign_role(self, role: Role) -> bool:
        if role.role_id in self._roles:
            return False
        self._roles[role.role_id] = role
        return True

    def unassign_role(self, role_id: str) -> bool:
        return self._roles.pop(role_id.upper(), None) is not None

    def get_roles(self) -> list[Role]:
        return list(self._roles.values())

    # ── effective permissions (direct + via roles) ────────────
    def effective_permissions(self) -> list[Permission]:
        """Union of direct permissions and all role permissions."""
        merged: dict[str, Permission] = dict(self._permissions)
        for role in self._roles.values():
            for p in role.get_permissions():
                merged[p.permission_id] = p
        return list(merged.values())

    def has_permission(self, perm_id: str) -> bool:
        perm_id = perm_id.upper()
        if perm_id in self._permissions:
            return True
        return any(role.has_permission(perm_id) for role in self._roles.values())

    def has_permission_by_name(self, name: str) -> bool:
        name = name.lower()
        return any(p.name == name for p in self.effective_permissions())

    # ── display ──────────────────────────────────────────────
    def _status_tag(self) -> str:
        return f"{GREEN}● Active{RESET}" if self._is_active else f"{RED}○ Inactive{RESET}"

    def summary_row(self, colour: str = CYAN, index: int = 0) -> str:
        eff   = self.effective_permissions()
        badges= "  ".join(p.badge() for p in eff[:4])
        extra = (f" {DIM}+{len(eff)-4} more{RESET}" if len(eff) > 4 else "")
        status= f"{GREEN}●{RESET}" if self._is_active else f"{RED}○{RESET}"
        return (
            f"  {DIM}{index:>3}.{RESET}  "
            f"{colour}{self._user_id}{RESET}  "
            f"{status} {BOLD}@{self._username:<20}{RESET}  "
            f"{self._display_name:<20}  "
            f"{badges}{extra}"
        )

    def detail_card(self) -> str:
        sep  = f"  {'─' * 64}"
        eff  = self.effective_permissions()
        lines = [
            sep,
            f"  {BOLD}{CYAN}{self._user_id}{RESET}  {self._status_tag()}",
            f"  {BOLD}Username     :{RESET} @{self._username}",
            f"  {BOLD}Display Name :{RESET} {self._display_name}",
            f"  {BOLD}Email        :{RESET} {self._email or '—'}",
            f"  {BOLD}Created      :{RESET} {self._created_at}",
        ]

        # Roles
        if self._roles:
            lines.append(f"  {BOLD}Roles        :{RESET} ({len(self._roles)})")
            for r in self._roles.values():
                lines.append(f"    • {CYAN}{r.role_id}{RESET}  {BOLD}{r.name}{RESET}")
        else:
            lines.append(f"  {BOLD}Roles        :{RESET} {DIM}none{RESET}")

        # Direct permissions
        if self._permissions:
            lines.append(
                f"  {BOLD}Direct Perms :{RESET} ({len(self._permissions)})"
            )
            for p in self._permissions.values():
                lines.append(
                    f"    • {p.badge()}  {DIM}{p.description[:40]}{RESET}"
                )
        else:
            lines.append(f"  {BOLD}Direct Perms :{RESET} {DIM}none{RESET}")

        # Effective (union)
        lines.append(f"  {BOLD}Effective    :{RESET} ({len(eff)} total)")
        for p in eff:
            source = "(direct)" if p.permission_id in self._permissions else "(via role)"
            lines.append(
                f"    {p.badge()}  {DIM}{source}{RESET}"
            )

        lines.append(sep)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.detail_card()

    def __repr__(self) -> str:
        return f"User({self._user_id!r}, {self._username!r})"


# ─────────────────────────────────────────────────────────────
#  PERMISSION MANAGER
# ─────────────────────────────────────────────────────────────
class PermissionManager:
    """Central coordinator for users, permissions, roles and the audit log."""

    def __init__(self, system_name: str = "PermSys"):
        self._name        = system_name
        self._users:       dict[str, User]       = {}  # username → User
        self._permissions: dict[str, Permission] = {}  # perm_id → Permission
        self._roles:       dict[str, Role]       = {}  # role_id → Role
        self._perm_names:  dict[str, str]        = {}  # perm_name → perm_id
        self._role_names:  dict[str, str]        = {}  # role_name → role_id
        self._audit        = AuditLog()

    # ══ PERMISSION CRUD ═══════════════════════════════════════
    def create_permission(self, name: str, description: str = "",
                          category: str = "custom",
                          actor: str = "system") -> Permission:
        norm = name.strip().lower().replace(" ", "_")
        if norm in self._perm_names:
            raise ValueError(f"Permission '{norm}' already exists.")
        perm = Permission(name, description, category)
        self._permissions[perm.permission_id] = perm
        self._perm_names[perm.name] = perm.permission_id
        self._audit.record("CREATE_PERMISSION", actor, perm.permission_id,
                           f"name={perm.name} category={perm.category}")
        return perm

    def get_permission(self, perm_id: str) -> Optional[Permission]:
        return self._permissions.get(perm_id.upper())

    def get_permission_by_name(self, name: str) -> Optional[Permission]:
        pid = self._perm_names.get(name.strip().lower().replace(" ", "_"))
        return self._permissions.get(pid) if pid else None

    def update_permission(self, perm_id: str, description: Optional[str] = None,
                          category: Optional[str] = None,
                          actor: str = "system") -> Permission:
        perm = self._require_permission(perm_id)
        perm.update(description, category)
        self._audit.record("UPDATE_PERMISSION", actor, perm.permission_id,
                           f"description={description!r} category={category!r}")
        return perm

    def delete_permission(self, perm_id: str,
                          actor: str = "system") -> Permission:
        perm = self._require_permission(perm_id)
        # Revoke from all users
        for user in self._users.values():
            user.revoke(perm.permission_id)
        # Remove from all roles
        for role in self._roles.values():
            role.remove_permission(perm.permission_id)
        del self._permissions[perm.permission_id]
        self._perm_names.pop(perm.name, None)
        self._audit.record("DELETE_PERMISSION", actor, perm.permission_id,
                           f"name={perm.name}")
        return perm

    def all_permissions(self) -> list[Permission]:
        return sorted(self._permissions.values(), key=lambda p: p.name)

    # ══ ROLE CRUD ════════════════════════════════════════════
    def create_role(self, name: str, description: str = "",
                    actor: str = "system") -> Role:
        norm = name.strip().lower().replace(" ", "_")
        if norm in self._role_names:
            raise ValueError(f"Role '{norm}' already exists.")
        role = Role(name, description)
        self._roles[role.role_id] = role
        self._role_names[role.name] = role.role_id
        self._audit.record("CREATE_ROLE", actor, role.role_id,
                           f"name={role.name}")
        return role

    def get_role(self, role_id: str) -> Optional[Role]:
        return self._roles.get(role_id.upper())

    def get_role_by_name(self, name: str) -> Optional[Role]:
        rid = self._role_names.get(name.strip().lower().replace(" ", "_"))
        return self._roles.get(rid) if rid else None

    def delete_role(self, role_id: str, actor: str = "system") -> Role:
        role = self._require_role(role_id)
        for user in self._users.values():
            user.unassign_role(role.role_id)
        del self._roles[role.role_id]
        self._role_names.pop(role.name, None)
        self._audit.record("DELETE_ROLE", actor, role.role_id,
                           f"name={role.name}")
        return role

    def add_permission_to_role(self, role_id: str, perm_id: str,
                               actor: str = "system"):
        role = self._require_role(role_id)
        perm = self._require_permission(perm_id)
        role.add_permission(perm)
        self._audit.record("ROLE_ADD_PERM", actor, role.role_id,
                           f"perm={perm.name}")

    def remove_permission_from_role(self, role_id: str, perm_id: str,
                                    actor: str = "system"):
        role = self._require_role(role_id)
        perm = self._require_permission(perm_id)
        if not role.remove_permission(perm.permission_id):
            raise KeyError(
                f"Permission '{perm_id}' not found in role '{role.name}'."
            )
        self._audit.record("ROLE_REMOVE_PERM", actor, role.role_id,
                           f"perm={perm.name}")

    def all_roles(self) -> list[Role]:
        return sorted(self._roles.values(), key=lambda r: r.name)

    # ══ USER CRUD ════════════════════════════════════════════
    def create_user(self, username: str, display_name: str = "",
                    email: str = "", actor: str = "system") -> User:
        uname = username.strip().lower()
        if uname in self._users:
            raise ValueError(f"Username '{uname}' is already taken.")
        user = User(username, display_name, email)
        self._users[user.username] = user
        self._audit.record("CREATE_USER", actor, user.user_id,
                           f"username={user.username}")
        return user

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username.strip().lower())

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        uid = user_id.upper()
        return next((u for u in self._users.values()
                     if u.user_id == uid), None)

    def update_user(self, username: str, actor: str = "system",
                    **kwargs) -> User:
        user = self._require_user(username)
        user.update(**kwargs)
        self._audit.record("UPDATE_USER", actor, user.user_id,
                           str(kwargs))
        return user

    def delete_user(self, username: str, actor: str = "system") -> User:
        user = self._require_user(username)
        del self._users[username.strip().lower()]
        self._audit.record("DELETE_USER", actor, user.user_id,
                           f"username={user.username}")
        return user

    def all_users(self) -> list[User]:
        return sorted(self._users.values(), key=lambda u: u.username)

    # ══ ASSIGNMENT ═══════════════════════════════════════════
    def grant_permission(self, username: str, perm_id: str,
                         actor: str = "system") -> bool:
        user = self._require_user(username)
        perm = self._require_permission(perm_id)
        result = user.grant(perm)
        if result:
            self._audit.record("GRANT_PERM", actor, user.user_id,
                               f"perm={perm.name}")
        return result

    def revoke_permission(self, username: str, perm_id: str,
                          actor: str = "system") -> bool:
        user = self._require_user(username)
        perm = self._require_permission(perm_id)
        result = user.revoke(perm.permission_id)
        if result:
            self._audit.record("REVOKE_PERM", actor, user.user_id,
                               f"perm={perm.name}")
        return result

    def assign_role(self, username: str, role_id: str,
                    actor: str = "system") -> bool:
        user = self._require_user(username)
        role = self._require_role(role_id)
        result = user.assign_role(role)
        if result:
            self._audit.record("ASSIGN_ROLE", actor, user.user_id,
                               f"role={role.name}")
        return result

    def unassign_role(self, username: str, role_id: str,
                      actor: str = "system") -> bool:
        user = self._require_user(username)
        role = self._require_role(role_id)
        result = user.unassign_role(role.role_id)
        if result:
            self._audit.record("UNASSIGN_ROLE", actor, user.user_id,
                               f"role={role.name}")
        return result

    # ══ QUERIES ══════════════════════════════════════════════
    def users_with_permission(self, perm_id: str) -> list[User]:
        return [u for u in self._users.values()
                if u.has_permission(perm_id)]

    def users_with_role(self, role_id: str) -> list[User]:
        return [u for u in self._users.values()
                if any(r.role_id == role_id for r in u.get_roles())]

    def check_permission(self, username: str, perm_name: str) -> bool:
        user = self.get_user(username)
        return user.has_permission_by_name(perm_name) if user else False

    # ══ STATISTICS ═══════════════════════════════════════════
    def statistics(self) -> dict:
        total_users   = len(self._users)
        active_users  = sum(1 for u in self._users.values() if u.is_active)
        users_no_perm = sum(1 for u in self._users.values()
                            if not u.effective_permissions())
        return {
            "total_users":        total_users,
            "active_users":       active_users,
            "inactive_users":     total_users - active_users,
            "total_permissions":  len(self._permissions),
            "total_roles":        len(self._roles),
            "users_no_perm":      users_no_perm,
            "audit_entries":      len(self._audit),
        }

    def audit_log(self, n: int = 20) -> list[dict]:
        return self._audit.recent(n)

    # ══ PRIVATE HELPERS ══════════════════════════════════════
    def _require_user(self, username: str) -> User:
        user = self.get_user(username)
        if not user:
            raise KeyError(f"User '{username}' not found.")
        return user

    def _require_permission(self, perm_id: str) -> Permission:
        perm = self.get_permission(perm_id)
        if not perm:
            raise KeyError(f"Permission '{perm_id.upper()}' not found.")
        return perm

    def _require_role(self, role_id: str) -> Role:
        role = self.get_role(role_id)
        if not role:
            raise KeyError(f"Role '{role_id.upper()}' not found.")
        return role


# ─────────────────────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────────────────────
def _sep(char: str = "═", width: int = 68):
    print(char * width)

def _header(title: str):
    _sep()
    print(f"  {BOLD}{title}{RESET}")
    _sep()

def _inp(prompt: str) -> str:
    return input(f"  {prompt}").strip()

def _inp_optional(prompt: str, current: str = "") -> Optional[str]:
    hint = f" [{current}]" if current else ""
    raw  = input(f"  {prompt}{hint}: ").strip()
    return raw if raw else None

def _display_permissions_table(perms: list[Permission],
                                heading: str = "Permissions"):
    if not perms:
        print(f"  {DIM}No permissions found.{RESET}"); return
    _header(heading)
    print(f"  {BOLD}{'#':>3}   {'ID':<10}  {'Name':<28}  "
          f"{'Category':<12}  Description{RESET}")
    print(f"  {'─' * 85}")
    for i, p in enumerate(perms, 1):
        print(p.summary_row(ACCENT[i % len(ACCENT)], i))

def _display_roles_table(roles: list[Role], heading: str = "Roles"):
    if not roles:
        print(f"  {DIM}No roles found.{RESET}"); return
    _header(heading)
    print(f"  {BOLD}{'#':>3}   {'ID':<10}  {'Name':<22}  "
          f"{'Perms':>5}  Permissions{RESET}")
    print(f"  {'─' * 85}")
    for i, r in enumerate(roles, 1):
        print(r.summary_row(ACCENT[i % len(ACCENT)], i))

def _display_users_table(users: list[User], heading: str = "Users"):
    if not users:
        print(f"  {DIM}No users found.{RESET}"); return
    _header(heading)
    print(f"  {BOLD}{'#':>3}   {'ID':<10}  {'S':<2} {'Username':<22}  "
          f"{'Display Name':<20}  Permissions{RESET}")
    print(f"  {'─' * 100}")
    for i, u in enumerate(users, 1):
        print(u.summary_row(ACCENT[i % len(ACCENT)], i))

def _pick_permission(mgr: PermissionManager,
                     prompt: str = "Permission ID") -> Optional[Permission]:
    """Show permission table then ask for an ID."""
    _display_permissions_table(mgr.all_permissions(), "Available Permissions")
    pid = _inp(f"\n{prompt}: ").upper()
    perm = mgr.get_permission(pid)
    if not perm:
        print(f"  {RED}✖  Permission '{pid}' not found.{RESET}")
    return perm

def _pick_role(mgr: PermissionManager,
               prompt: str = "Role ID") -> Optional[Role]:
    _display_roles_table(mgr.all_roles(), "Available Roles")
    rid = _inp(f"\n{prompt}: ").upper()
    role = mgr.get_role(rid)
    if not role:
        print(f"  {RED}✖  Role '{rid}' not found.{RESET}")
    return role

def _pick_user(mgr: PermissionManager,
               prompt: str = "Username") -> Optional[User]:
    _display_users_table(mgr.all_users(), "All Users")
    uname = _inp(f"\n{prompt}: ").lower()
    user  = mgr.get_user(uname)
    if not user:
        print(f"  {RED}✖  User '@{uname}' not found.{RESET}")
    return user


# ─────────────────────────────────────────────────────────────
#  MENU ACTIONS — PERMISSIONS
# ─────────────────────────────────────────────────────────────
def action_create_permission(mgr: PermissionManager):
    _header("Create New Permission")
    name  = _inp("Permission name (e.g. view_reports) : ")
    desc  = _inp("Description                         : ")
    print(f"  Categories: {', '.join(Permission.CATEGORIES)}")
    cat   = _inp("Category                            : ").lower() or "custom"
    try:
        perm = mgr.create_permission(name, desc, cat)
        print(f"\n  {GREEN}✔  Permission created — {perm.permission_id}  [{perm.name}]{RESET}")
    except ValueError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_update_permission(mgr: PermissionManager):
    _header("Update Permission")
    perm = _pick_permission(mgr)
    if not perm:
        return
    print(f"\n{perm.detail_card()}")
    print(f"  {DIM}Leave blank to keep current value.{RESET}\n")
    raw_desc = _inp_optional("New description ", perm.description)
    raw_cat  = _inp_optional("New category    ", perm.category)
    try:
        mgr.update_permission(perm.permission_id, raw_desc, raw_cat)
        print(f"\n  {GREEN}✔  {perm.permission_id} updated.{RESET}")
    except (KeyError, ValueError) as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_delete_permission(mgr: PermissionManager):
    _header("Delete Permission")
    perm = _pick_permission(mgr)
    if not perm:
        return
    confirm = _inp(f"Type permission name to confirm deletion [{perm.name}]: ")
    if confirm.strip().lower() != perm.name:
        print(f"  {YELLOW}Deletion cancelled.{RESET}"); return
    try:
        mgr.delete_permission(perm.permission_id)
        print(f"\n  {GREEN}✔  Permission '{perm.name}' deleted and revoked from all users.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_list_permissions(mgr: PermissionManager):
    _display_permissions_table(mgr.all_permissions(), "All Permissions")


# ─────────────────────────────────────────────────────────────
#  MENU ACTIONS — ROLES
# ─────────────────────────────────────────────────────────────
def action_create_role(mgr: PermissionManager):
    _header("Create New Role")
    name = _inp("Role name (e.g. editor): ")
    desc = _inp("Description            : ")
    try:
        role = mgr.create_role(name, desc)
        print(f"\n  {GREEN}✔  Role created — {role.role_id}  [{role.name}]{RESET}")
    except ValueError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_add_perm_to_role(mgr: PermissionManager):
    _header("Add Permission to Role")
    role = _pick_role(mgr, "Role ID")
    if not role:
        return
    perm = _pick_permission(mgr, "Permission ID to add")
    if not perm:
        return
    try:
        mgr.add_permission_to_role(role.role_id, perm.permission_id)
        print(f"\n  {GREEN}✔  [{perm.name}] added to role '{role.name}'.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_remove_perm_from_role(mgr: PermissionManager):
    _header("Remove Permission from Role")
    role = _pick_role(mgr, "Role ID")
    if not role:
        return
    print(f"\n{role.detail_card()}")
    perm = _pick_permission(mgr, "Permission ID to remove")
    if not perm:
        return
    try:
        mgr.remove_permission_from_role(role.role_id, perm.permission_id)
        print(f"\n  {GREEN}✔  [{perm.name}] removed from role '{role.name}'.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_delete_role(mgr: PermissionManager):
    _header("Delete Role")
    role = _pick_role(mgr, "Role ID")
    if not role:
        return
    confirm = _inp(f"Type role name to confirm [{role.name}]: ")
    if confirm.strip().lower() != role.name:
        print(f"  {YELLOW}Deletion cancelled.{RESET}"); return
    try:
        mgr.delete_role(role.role_id)
        print(f"\n  {GREEN}✔  Role '{role.name}' deleted and unassigned from all users.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_list_roles(mgr: PermissionManager):
    roles = mgr.all_roles()
    _display_roles_table(roles, "All Roles")
    if roles:
        show = _inp("\nView role detail? (role ID or blank to skip): ").upper()
        if show:
            role = mgr.get_role(show)
            if role:
                print(f"\n{role.detail_card()}")
            else:
                print(f"  {RED}✖  Role '{show}' not found.{RESET}")


# ─────────────────────────────────────────────────────────────
#  MENU ACTIONS — USERS
# ─────────────────────────────────────────────────────────────
def action_create_user(mgr: PermissionManager):
    _header("Create New User")
    uname   = _inp("Username (3+ chars)  : ")
    display = _inp("Display name (opt)   : ")
    email   = _inp("Email (opt)          : ")
    try:
        user = mgr.create_user(uname, display, email)
        print(f"\n  {GREEN}✔  User created — {user.user_id}  @{user.username}{RESET}")
    except ValueError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_update_user(mgr: PermissionManager):
    _header("Update User")
    user = _pick_user(mgr)
    if not user:
        return
    print(f"\n{user.detail_card()}")
    print(f"  {DIM}Leave blank to keep current value.{RESET}\n")
    raw_display = _inp_optional("New display name ", user.display_name)
    raw_email   = _inp_optional("New email        ", user.email)
    raw_active  = _inp_optional("Active? (y/n)    ",
                                "y" if user.is_active else "n")
    kwargs: dict = {}
    if raw_display: kwargs["display_name"] = raw_display
    if raw_email:   kwargs["email"]        = raw_email
    if raw_active:  kwargs["is_active"]    = raw_active.lower() == "y"
    try:
        mgr.update_user(user.username, **kwargs)
        print(f"\n  {GREEN}✔  @{user.username} updated.{RESET}")
    except (KeyError, ValueError) as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_delete_user(mgr: PermissionManager):
    _header("Delete User")
    user = _pick_user(mgr)
    if not user:
        return
    confirm = _inp(f"Type username to confirm [@{user.username}]: ").lower()
    if confirm != user.username:
        print(f"  {YELLOW}Deletion cancelled.{RESET}"); return
    try:
        mgr.delete_user(user.username)
        print(f"\n  {GREEN}✔  @{user.username} deleted.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_view_user(mgr: PermissionManager):
    _header("View User Detail")
    user = _pick_user(mgr)
    if user:
        print()
        print(user.detail_card())


def action_list_users(mgr: PermissionManager):
    _display_users_table(mgr.all_users(), "All Users")


# ─────────────────────────────────────────────────────────────
#  MENU ACTIONS — ASSIGNMENTS
# ─────────────────────────────────────────────────────────────
def action_grant_permission(mgr: PermissionManager):
    _header("Grant Permission to User")
    user = _pick_user(mgr, "Username")
    if not user:
        return
    perm = _pick_permission(mgr, "Permission ID to grant")
    if not perm:
        return
    try:
        ok = mgr.grant_permission(user.username, perm.permission_id)
        if ok:
            print(f"\n  {GREEN}✔  [{perm.name}] granted to @{user.username}.{RESET}")
        else:
            print(f"\n  {YELLOW}⚠  @{user.username} already has [{perm.name}].{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_revoke_permission(mgr: PermissionManager):
    _header("Revoke Permission from User")
    user = _pick_user(mgr, "Username")
    if not user:
        return

    direct = user.direct_permissions()
    if not direct:
        print(f"\n  {YELLOW}@{user.username} has no directly-assigned permissions.{RESET}")
        return

    print(f"\n  {BOLD}Direct permissions for @{user.username}:{RESET}")
    for i, p in enumerate(direct, 1):
        print(f"    {i}. {p.badge()}  {p.permission_id}  {DIM}{p.description[:40]}{RESET}")

    pid = _inp("Permission ID to revoke: ").upper()
    try:
        ok = mgr.revoke_permission(user.username, pid)
        perm = mgr.get_permission(pid)
        pname = perm.name if perm else pid
        if ok:
            print(f"\n  {GREEN}✔  [{pname}] revoked from @{user.username}.{RESET}")
        else:
            print(f"\n  {YELLOW}⚠  @{user.username} did not have [{pname}] directly.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_assign_role(mgr: PermissionManager):
    _header("Assign Role to User")
    user = _pick_user(mgr, "Username")
    if not user:
        return
    role = _pick_role(mgr, "Role ID to assign")
    if not role:
        return
    try:
        ok = mgr.assign_role(user.username, role.role_id)
        if ok:
            print(f"\n  {GREEN}✔  Role '{role.name}' assigned to @{user.username}.{RESET}")
        else:
            print(f"\n  {YELLOW}⚠  @{user.username} already has role '{role.name}'.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_unassign_role(mgr: PermissionManager):
    _header("Unassign Role from User")
    user = _pick_user(mgr, "Username")
    if not user:
        return

    roles = user.get_roles()
    if not roles:
        print(f"\n  {YELLOW}@{user.username} has no roles assigned.{RESET}")
        return

    print(f"\n  {BOLD}Roles for @{user.username}:{RESET}")
    for i, r in enumerate(roles, 1):
        print(f"    {i}. {CYAN}{r.role_id}{RESET}  {BOLD}{r.name}{RESET}")

    rid = _inp("Role ID to unassign: ").upper()
    try:
        role = mgr.get_role(rid)
        ok   = mgr.unassign_role(user.username, rid)
        rname = role.name if role else rid
        if ok:
            print(f"\n  {GREEN}✔  Role '{rname}' removed from @{user.username}.{RESET}")
        else:
            print(f"\n  {YELLOW}⚠  @{user.username} did not have role '{rname}'.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


# ─────────────────────────────────────────────────────────────
#  MENU ACTIONS — QUERIES & REPORTS
# ─────────────────────────────────────────────────────────────
def action_check_permission(mgr: PermissionManager):
    _header("Check User Permission")
    uname = _inp("Username    : ").lower()
    pname = _inp("Permission  : ").lower()
    result = mgr.check_permission(uname, pname)
    user   = mgr.get_user(uname)
    if not user:
        print(f"\n  {RED}✖  User '@{uname}' not found.{RESET}"); return
    if result:
        print(f"\n  {GREEN}✔  @{uname} HAS permission '{pname}'.{RESET}")
    else:
        print(f"\n  {RED}✖  @{uname} does NOT have permission '{pname}'.{RESET}")


def action_users_with_permission(mgr: PermissionManager):
    _header("Users with a Specific Permission")
    perm = _pick_permission(mgr)
    if not perm:
        return
    users = mgr.users_with_permission(perm.permission_id)
    _display_users_table(users, f"Users with [{perm.name}]")


def action_audit_log(mgr: PermissionManager):
    _header("Audit Log (Recent 20 Entries)")
    entries = mgr.audit_log(20)
    if not entries:
        print(f"  {DIM}No audit entries yet.{RESET}"); return
    print(f"  {BOLD}{'Timestamp':<22}  {'Action':<22}  {'Actor':<14}  "
          f"{'Target':<12}  Detail{RESET}")
    print(f"  {'─' * 95}")
    action_colours = {
        "CREATE": GREEN, "GRANT": GREEN, "ASSIGN": GREEN,
        "DELETE": RED,   "REVOKE": RED,  "UNASSIGN": RED,
        "UPDATE": YELLOW,
    }
    for e in entries:
        c = next((v for k, v in action_colours.items()
                  if e["action"].startswith(k)), DIM)
        print(
            f"  {DIM}{e['timestamp']}{RESET}  "
            f"{c}{e['action']:<22}{RESET}  "
            f"{e['actor']:<14}  "
            f"{CYAN}{e['target']:<12}{RESET}  "
            f"{DIM}{e['detail'][:40]}{RESET}"
        )


def action_statistics(mgr: PermissionManager):
    _header("System Statistics")
    s = mgr.statistics()
    rows = [
        ("Total users",             s["total_users"],       CYAN),
        ("Active users",            s["active_users"],      GREEN),
        ("Inactive users",          s["inactive_users"],    DIM),
        ("Users with no permissions", s["users_no_perm"],   YELLOW if s["users_no_perm"] else GREEN),
        ("Total permissions",       s["total_permissions"], MAGENTA),
        ("Total roles",             s["total_roles"],       BLUE),
        ("Audit log entries",       s["audit_entries"],     DIM),
    ]
    for label, val, colour in rows:
        bar = "█" * min(val, 40)
        print(f"  {label:<30} {colour}{val:>5}  {bar}{RESET}")


# ─────────────────────────────────────────────────────────────
#  DEMO SEED DATA
# ─────────────────────────────────────────────────────────────
def seed_demo_data(mgr: PermissionManager):
    # Permissions
    perms_data = [
        ("view_dashboard",    "View the main dashboard",        "view"),
        ("view_reports",      "View analytics reports",         "view"),
        ("export_reports",    "Export reports to CSV/PDF",      "export"),
        ("manage_users",      "Create, update, delete users",   "manage"),
        ("edit_content",      "Create and edit content",        "write"),
        ("delete_content",    "Delete existing content",        "delete"),
        ("admin_panel",       "Access the admin control panel", "admin"),
        ("api_access",        "Call protected API endpoints",   "execute"),
        ("import_data",       "Import external data sources",   "import"),
        ("audit_logs",        "View the system audit log",      "read"),
    ]
    for name, desc, cat in perms_data:
        try:
            mgr.create_permission(name, desc, cat)
        except ValueError:
            pass

    # Roles
    roles_data = [
        ("viewer",    "Read-only access to dashboards and reports"),
        ("editor",    "Content creation and editing"),
        ("manager",   "User management and reporting"),
        ("admin",     "Full system access"),
    ]
    for rname, rdesc in roles_data:
        try:
            mgr.create_role(rname, rdesc)
        except ValueError:
            pass

    # Add permissions to roles
    role_perm_map = {
        "viewer":  ["view_dashboard", "view_reports"],
        "editor":  ["view_dashboard", "edit_content", "view_reports"],
        "manager": ["view_dashboard", "view_reports", "export_reports",
                    "manage_users", "audit_logs"],
        "admin":   ["view_dashboard", "view_reports", "export_reports",
                    "manage_users", "edit_content", "delete_content",
                    "admin_panel", "api_access", "import_data", "audit_logs"],
    }
    for rname, pnames in role_perm_map.items():
        role = mgr.get_role_by_name(rname)
        if role:
            for pname in pnames:
                perm = mgr.get_permission_by_name(pname)
                if perm:
                    mgr.add_permission_to_role(role.role_id, perm.permission_id)

    # Users
    users_data = [
        ("alice",   "Alice Johnson",  "alice@example.com"),
        ("bob",     "Bob Martinez",   "bob@example.com"),
        ("carol",   "Carol Williams", "carol@example.com"),
        ("dave",    "Dave Chen",      "dave@example.com"),
        ("eve",     "Eve Torres",     "eve@example.com"),
    ]
    for uname, display, email in users_data:
        try:
            mgr.create_user(uname, display, email)
        except ValueError:
            pass

    # Assign roles
    role_user_map = {
        "admin":   ["alice"],
        "manager": ["bob"],
        "editor":  ["carol", "dave"],
        "viewer":  ["eve"],
    }
    for rname, unames in role_user_map.items():
        role = mgr.get_role_by_name(rname)
        if role:
            for uname in unames:
                user = mgr.get_user(uname)
                if user:
                    mgr.assign_role(uname, role.role_id)

    # Also give bob a direct permission beyond his role
    perm = mgr.get_permission_by_name("api_access")
    if perm:
        mgr.grant_permission("bob", perm.permission_id)


# ─────────────────────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────────────────────
MENU = f"""
  {BOLD}┌─────────────────────────────────────────────────────┐
  │         PERMISSION MANAGEMENT SYSTEM                │
  ├─────────────────────────────────────────────────────┤
  │  {CYAN}PERMISSIONS{RESET}{BOLD}                                          │
  │{RESET}    1.  Create Permission                             {BOLD}│
  │{RESET}    2.  Update Permission                            {BOLD}│
  │{RESET}    3.  Delete Permission                            {BOLD}│
  │{RESET}    4.  List All Permissions                         {BOLD}│
  │  {CYAN}ROLES{RESET}{BOLD}                                               │
  │{RESET}    5.  Create Role                                  {BOLD}│
  │{RESET}    6.  Add Permission to Role                       {BOLD}│
  │{RESET}    7.  Remove Permission from Role                  {BOLD}│
  │{RESET}    8.  Delete Role                                  {BOLD}│
  │{RESET}    9.  List All Roles                               {BOLD}│
  │  {CYAN}USERS{RESET}{BOLD}                                               │
  │{RESET}   10.  Create User                                  {BOLD}│
  │{RESET}   11.  Update User                                  {BOLD}│
  │{RESET}   12.  Delete User                                  {BOLD}│
  │{RESET}   13.  View User Detail                             {BOLD}│
  │{RESET}   14.  List All Users                               {BOLD}│
  │  {CYAN}ASSIGNMENTS{RESET}{BOLD}                                         │
  │{RESET}   15.  Grant Permission to User                     {BOLD}│
  │{RESET}   16.  Revoke Permission from User                  {BOLD}│
  │{RESET}   17.  Assign Role to User                          {BOLD}│
  │{RESET}   18.  Unassign Role from User                      {BOLD}│
  │  {CYAN}QUERIES & REPORTS{RESET}{BOLD}                                   │
  │{RESET}   19.  Check User Permission                        {BOLD}│
  │{RESET}   20.  Users with a Permission                      {BOLD}│
  │{RESET}   21.  Audit Log                                    {BOLD}│
  │{RESET}   22.  Statistics Dashboard                         {BOLD}│
  │{RESET}    0.  Exit                                         {BOLD}│
  └─────────────────────────────────────────────────────┘{RESET}"""

ACTIONS = {
    "1":  action_create_permission,
    "2":  action_update_permission,
    "3":  action_delete_permission,
    "4":  action_list_permissions,
    "5":  action_create_role,
    "6":  action_add_perm_to_role,
    "7":  action_remove_perm_from_role,
    "8":  action_delete_role,
    "9":  action_list_roles,
    "10": action_create_user,
    "11": action_update_user,
    "12": action_delete_user,
    "13": action_view_user,
    "14": action_list_users,
    "15": action_grant_permission,
    "16": action_revoke_permission,
    "17": action_assign_role,
    "18": action_unassign_role,
    "19": action_check_permission,
    "20": action_users_with_permission,
    "21": action_audit_log,
    "22": action_statistics,
}


def _banner():
    print()
    _sep("═")
    print(f"""
  {BOLD}{CYAN}
  ██████╗ ███████╗██████╗ ███╗   ███╗
  ██╔══██╗██╔════╝██╔══██╗████╗ ████║
  ██████╔╝█████╗  ██████╔╝██╔████╔██║
  ██╔═══╝ ██╔══╝  ██╔══██╗██║╚██╔╝██║
  ██║     ███████╗██║  ██║██║ ╚═╝ ██║
  ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝{RESET}
  {BOLD}  P E R M I S S I O N   M A N A G E M E N T{RESET}
  {DIM}  Control who can do what, and prove it.{RESET}
""")
    _sep("═")
    print()


def main():
    _banner()
    sname = _inp("System / organisation name: ") or "PermSys"
    mgr   = PermissionManager(sname)

    load = _inp("Load demo data? (y/n): ").lower()
    if load == "y":
        seed_demo_data(mgr)
        s = mgr.statistics()
        print(
            f"\n  {GREEN}✔  Demo loaded — "
            f"{s['total_users']} users, "
            f"{s['total_permissions']} permissions, "
            f"{s['total_roles']} roles, "
            f"{s['audit_entries']} audit entries.{RESET}\n"
        )

    while True:
        print(MENU)
        choice = _inp("Select option: ")
        if choice == "0":
            print(f"\n  {CYAN}Goodbye! Access denied to nothing. 👋{RESET}\n")
            break
        elif choice in ACTIONS:
            print()
            ACTIONS[choice](mgr)
            input(f"\n  {DIM}Press Enter to return to menu…{RESET}")
        else:
            print(f"  {RED}✖  Unrecognised option.{RESET}")


if __name__ == "__main__":
    main()