"""
Object Authentication System
A secure user authentication system using OOP principles.
"""

import hashlib
import os
import re
from datetime import datetime


# ─────────────────────────────────────────────
#  USER CLASS
# ─────────────────────────────────────────────

class User:
    """Represents a registered user with encapsulated credentials."""

    VALID_ROLES = {"admin", "moderator", "user"}

    def __init__(self, user_id: int, username: str, password: str, role: str = "user"):
        self.__user_id: int = user_id
        self.__username: str = username
        self.__password_hash: str = self._hash_password(password)
        self.__role: str = self._validate_role(role)
        self.__created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.__is_active: bool = True

    # ── Static / class helpers ──────────────────

    @staticmethod
    def _hash_password(password: str) -> str:
        """Return a salted SHA-256 hash of the given password."""
        salt = "auth_sys_salt_2024"
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

    @staticmethod
    def _validate_role(role: str) -> str:
        role = role.lower().strip()
        if role not in User.VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {User.VALID_ROLES}")
        return role

    # ── Read-only properties ────────────────────

    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def role(self) -> str:
        return self.__role

    @property
    def created_at(self) -> str:
        return self.__created_at

    @property
    def is_active(self) -> bool:
        return self.__is_active

    # ── Credential verification ─────────────────

    def verify_password(self, password: str) -> bool:
        """Return True if the supplied password matches the stored hash."""
        return self.__password_hash == self._hash_password(password)

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change the password after verifying the old one."""
        if not self.verify_password(old_password):
            return False
        is_valid, msg = AuthenticationSystem.validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(msg)
        self.__password_hash = self._hash_password(new_password)
        return True

    def deactivate(self):
        self.__is_active = False

    def activate(self):
        self.__is_active = True

    # ── Display ─────────────────────────────────

    def get_info(self) -> dict:
        """Return a safe (password-free) snapshot of user data."""
        return {
            "User ID":    self.__user_id,
            "Username":   self.__username,
            "Role":       self.__role,
            "Status":     "Active" if self.__is_active else "Inactive",
            "Created At": self.__created_at,
        }

    def __repr__(self) -> str:
        return f"User(id={self.__user_id}, username='{self.__username}', role='{self.__role}')"


# ─────────────────────────────────────────────
#  AUTHENTICATION SYSTEM CLASS
# ─────────────────────────────────────────────

class AuthenticationSystem:
    """Manages user accounts and authentication sessions."""

    MAX_LOGIN_ATTEMPTS = 3

    def __init__(self):
        self.__users: dict[str, User] = {}          # username → User
        self.__logged_in_user: User | None = None
        self.__next_id: int = 1
        self.__failed_attempts: dict[str, int] = {} # username → attempt count
        self._seed_admin()

    # ── Internal helpers ────────────────────────

    def _seed_admin(self):
        """Create a default admin account on first run."""
        self._register("admin", "Admin@1234", role="admin", _silent=True)

    def _get_next_id(self) -> int:
        uid = self.__next_id
        self.__next_id += 1
        return uid

    # ── Public static helpers ───────────────────

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """Username must be 3-20 alphanumeric/underscore characters."""
        if not (3 <= len(username) <= 20):
            return False, "Username must be between 3 and 20 characters."
        if not re.match(r"^\w+$", username):
            return False, "Username may only contain letters, digits, and underscores."
        return True, "OK"

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Enforce minimum password complexity."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter."
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter."
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character."
        return True, "OK"

    # ── Core operations ─────────────────────────

    def _register(self, username: str, password: str,
                  role: str = "user", _silent: bool = False) -> bool:
        """Internal registration used by both public register() and seeding."""
        username = username.strip()

        valid_u, msg_u = self.validate_username(username)
        if not valid_u:
            if not _silent:
                print(f"  [!] {msg_u}")
            return False

        valid_p, msg_p = self.validate_password_strength(password)
        if not valid_p:
            if not _silent:
                print(f"  [!] {msg_p}")
            return False

        if username.lower() in (u.lower() for u in self.__users):
            if not _silent:
                print("  [!] Username already exists.")
            return False

        try:
            user = User(self._get_next_id(), username, password, role)
        except ValueError as exc:
            if not _silent:
                print(f"  [!] {exc}")
            return False

        self.__users[username] = user
        if not _silent:
            print(f"  [✓] Account '{username}' created successfully (role: {role}).")
        return True

    def register(self, username: str, password: str, role: str = "user") -> bool:
        """Public registration entry-point."""
        return self._register(username, password, role)

    def login(self, username: str, password: str) -> bool:
        """Authenticate a user; enforces lock-out after repeated failures."""
        if self.__logged_in_user:
            print(f"  [!] Already logged in as '{self.__logged_in_user.username}'. Please log out first.")
            return False

        user = self.__users.get(username)

        if user is None:
            print("  [!] Invalid username or password.")
            return False

        if not user.is_active:
            print("  [!] This account has been deactivated.")
            return False

        attempts = self.__failed_attempts.get(username, 0)
        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            print(f"  [!] Account '{username}' is temporarily locked due to too many failed attempts.")
            return False

        if not user.verify_password(password):
            self.__failed_attempts[username] = attempts + 1
            remaining = self.MAX_LOGIN_ATTEMPTS - self.__failed_attempts[username]
            if remaining > 0:
                print(f"  [!] Invalid username or password. {remaining} attempt(s) remaining.")
            else:
                print(f"  [!] Account '{username}' has been locked. Contact an administrator.")
            return False

        # Successful login
        self.__failed_attempts.pop(username, None)
        self.__logged_in_user = user
        print(f"  [✓] Welcome back, {username}! (role: {user.role})")
        return True

    def logout(self) -> bool:
        if not self.__logged_in_user:
            print("  [!] No user is currently logged in.")
            return False
        name = self.__logged_in_user.username
        self.__logged_in_user = None
        print(f"  [✓] '{name}' has been logged out successfully.")
        return True

    # ── Session helpers ─────────────────────────

    @property
    def current_user(self) -> User | None:
        return self.__logged_in_user

    def is_logged_in(self) -> bool:
        return self.__logged_in_user is not None

    def require_login(self) -> bool:
        if not self.is_logged_in():
            print("  [!] You must be logged in to perform this action.")
            return False
        return True

    def require_admin(self) -> bool:
        if not self.require_login():
            return False
        if self.__logged_in_user.role != "admin":
            print("  [!] Administrator privileges required.")
            return False
        return True

    # ── Account management ──────────────────────

    def display_current_user_info(self):
        if not self.require_login():
            return
        info = self.__logged_in_user.get_info()
        print("\n  ┌─ Your Account Info " + "─" * 30)
        for key, val in info.items():
            print(f"  │  {key:<15}: {val}")
        print("  └" + "─" * 50)

    def change_password(self):
        if not self.require_login():
            return
        old_pw  = _get_password("  Enter current password: ")
        new_pw  = _get_password("  Enter new password:     ")
        new_pw2 = _get_password("  Confirm new password:   ")
        if new_pw != new_pw2:
            print("  [!] Passwords do not match.")
            return
        try:
            if self.__logged_in_user.change_password(old_pw, new_pw):
                print("  [✓] Password changed successfully.")
            else:
                print("  [!] Current password is incorrect.")
        except ValueError as exc:
            print(f"  [!] {exc}")

    # ── Admin-only operations ───────────────────

    def list_all_users(self):
        if not self.require_admin():
            return
        print(f"\n  ┌─ All Users ({len(self.__users)}) " + "─" * 35)
        for user in self.__users.values():
            info = user.get_info()
            status = "🟢" if info["Status"] == "Active" else "🔴"
            print(f"  │  [{info['User ID']:>3}] {info['Username']:<20} "
                  f"role={info['Role']:<12} {status} {info['Status']}")
        print("  └" + "─" * 55)

    def unlock_account(self, username: str):
        if not self.require_admin():
            return
        if username not in self.__users:
            print(f"  [!] User '{username}' not found.")
            return
        self.__failed_attempts.pop(username, None)
        self.__users[username].activate()
        print(f"  [✓] Account '{username}' has been unlocked.")

    def deactivate_account(self, username: str):
        if not self.require_admin():
            return
        if username not in self.__users:
            print(f"  [!] User '{username}' not found.")
            return
        if username == self.__logged_in_user.username:
            print("  [!] You cannot deactivate your own account.")
            return
        self.__users[username].deactivate()
        print(f"  [✓] Account '{username}' has been deactivated.")


# ─────────────────────────────────────────────
#  UI HELPERS
# ─────────────────────────────────────────────

def _clear():
    os.system("cls" if os.name == "nt" else "clear")

def _get_input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""

def _get_password(prompt: str) -> str:
    """Read a password as plain visible input."""
    return _get_input(prompt)

def _banner():
    print("""
╔══════════════════════════════════════════════════╗
║         🔐  Object Authentication System         ║
╚══════════════════════════════════════════════════╝""")

def _divider():
    print("  " + "─" * 48)


# ─────────────────────────────────────────────
#  MENU FUNCTIONS
# ─────────────────────────────────────────────

def menu_register(auth: AuthenticationSystem):
    print("\n  ── Register New Account ──")
    username = _get_input("  Username : ")
    password = _get_password("  Password : ")
    confirm  = _get_password("  Confirm  : ")
    if password != confirm:
        print("  [!] Passwords do not match.")
        return
    role = _get_input("  Role (user/moderator) [default: user]: ").lower() or "user"
    auth.register(username, password, role)


def menu_login(auth: AuthenticationSystem):
    print("\n  ── Login ──")
    username = _get_input("  Username : ")
    password = _get_password("  Password : ")
    auth.login(username, password)


def menu_admin(auth: AuthenticationSystem):
    while True:
        print("""
  ── Admin Panel ──────────────────────────
    [1] List all users
    [2] Unlock / reactivate account
    [3] Deactivate account
    [0] Back
  ─────────────────────────────────────────""")
        choice = _get_input("  Choice: ")
        if choice == "1":
            auth.list_all_users()
        elif choice == "2":
            u = _get_input("  Username to unlock: ")
            auth.unlock_account(u)
        elif choice == "3":
            u = _get_input("  Username to deactivate: ")
            auth.deactivate_account(u)
        elif choice == "0":
            break
        else:
            print("  [!] Invalid option.")


def main():
    auth = AuthenticationSystem()

    while True:
        _banner()

        if auth.is_logged_in():
            user = auth.current_user
            print(f"  Logged in as: {user.username}  [{user.role}]\n")
            print("  [1] View my info")
            print("  [2] Change password")
            if user.role == "admin":
                print("  [3] Admin panel")
            print("  [L] Logout")
            print("  [0] Exit")
        else:
            print("  [1] Register")
            print("  [2] Login")
            print("  [0] Exit")

        _divider()
        choice = _get_input("  Choice: ").upper()
        print()

        if not auth.is_logged_in():
            if choice == "1":
                menu_register(auth)
            elif choice == "2":
                menu_login(auth)
            elif choice == "0":
                print("  Goodbye! 👋\n")
                break
            else:
                print("  [!] Invalid option. Please try again.")
        else:
            if choice == "1":
                auth.display_current_user_info()
            elif choice == "2":
                auth.change_password()
            elif choice == "3" and auth.current_user.role == "admin":
                menu_admin(auth)
            elif choice == "L":
                auth.logout()
            elif choice == "0":
                auth.logout()
                print("  Goodbye! 👋\n")
                break
            else:
                print("  [!] Invalid option. Please try again.")

        input("\n  Press Enter to continue...")
        _clear()


if __name__ == "__main__":
    main()