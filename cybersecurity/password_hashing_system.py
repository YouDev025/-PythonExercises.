"""
Password Hashing System  v1.1
─────────────────────────────
A secure, OOP-based system for hashing and verifying user passwords,
with user registration, authentication, and optional JSON persistence.

Bug fixes vs v1.0
─────────────────
• getpass crash / silent empty string in non-TTY terminals (VS Code,
  PyCharm, Thonny, Jupyter …) — replaced with a safe_getpass() wrapper
  that always falls back to visible input() when getpass is unavailable.
• Added TTY detection so the warning is shown only once, not per keystroke.
• Added --test flag to run the built-in test suite without starting the CLI.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


# ──────────────────────────────────────────────
# Safe password-input helper  (fixes the main bug)
# ──────────────────────────────────────────────

def _safe_getpass(prompt: str = "  Password: ") -> str:
    """
    Read a password from the user without any warnings or freezing.

    Strategy:
      - Real terminal (isatty=True)  : suppress-echo via getpass (input hidden)
      - IDE / non-TTY (isatty=False) : use input() directly — simple and reliable
    This avoids ALL warnings and the tty.setraw() freeze in pseudo-terminals.
    """
    import getpass as _gp, warnings, io

    if sys.stdin.isatty():
        # Genuine terminal — use getpass to hide the input
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
            # Redirect getpass stderr to devnull so no warnings leak
            with open(os.devnull, "w") as devnull:
                return _gp.getpass(prompt, stream=devnull)
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception:
            pass

    # Non-TTY (IDE, pipe, redirect) — plain input, zero side-effects
    return input(prompt)


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class HashAlgorithm(Enum):
    SHA256 = "sha256"
    SHA512 = "sha512"
    BCRYPT = "bcrypt"


class AuthResult(Enum):
    SUCCESS           = "success"
    INVALID_PASSWORD  = "invalid_password"
    USER_NOT_FOUND    = "user_not_found"


# ──────────────────────────────────────────────
# Custom Exceptions
# ──────────────────────────────────────────────

class PasswordHashingError(Exception):
    """Raised when hashing or verification fails."""

class UserManagerError(Exception):
    """Raised for registration / login validation errors."""


# ──────────────────────────────────────────────
# PasswordHasher
# ──────────────────────────────────────────────

class PasswordHasher:
    """
    Hashes and verifies passwords using configurable algorithms.

    Supported algorithms
    ────────────────────
    SHA256 / SHA512  PBKDF2-HMAC with a random 32-byte salt and 600 000
                     iterations (NIST SP 800-132).
    BCRYPT           Uses the bcrypt library (work factor 12) when
                     available; falls back to SHA-512 automatically.

    Stored hash format (self-describing — no out-of-band metadata needed)
    ──────────────────────────────────────────────────────────────────────
    SHA256/512:  <algo>$<iterations>$<hex-salt>$<hex-digest>
    BCRYPT:      bcrypt$<bcrypt-hash>
    """

    PBKDF2_ITERATIONS = 600_000
    SALT_BYTES        = 32
    BCRYPT_ROUNDS     = 12

    def __init__(self, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> None:
        self._algorithm = algorithm
        self._bcrypt_ok = self._check_bcrypt()

        if algorithm == HashAlgorithm.BCRYPT and not self._bcrypt_ok:
            print(
                "  ⚠  bcrypt not installed — using SHA-512 + PBKDF2 instead.\n"
                "     Run:  pip install bcrypt"
            )
            self._algorithm = HashAlgorithm.SHA512

    # ── Public API ───────────────────────────────

    def hash_password(self, plain: str) -> str:
        """Hash plain and return a self-describing hash string."""
        if not plain:
            raise PasswordHashingError("Password must not be empty.")
        try:
            if self._algorithm == HashAlgorithm.BCRYPT:
                return self._hash_bcrypt(plain)
            return self._hash_pbkdf2(plain)
        except Exception as exc:
            raise PasswordHashingError(f"Hashing failed: {exc}") from exc

    def verify_password(self, plain: str, stored_hash: str) -> bool:
        """
        Verify plain against stored_hash.
        Uses constant-time comparison to prevent timing attacks.
        Returns True on match, False otherwise.
        """
        if not plain or not stored_hash:
            return False
        try:
            if stored_hash.startswith("bcrypt$"):
                return self._verify_bcrypt(plain, stored_hash)
            return self._verify_pbkdf2(plain, stored_hash)
        except Exception as exc:
            raise PasswordHashingError(f"Verification failed: {exc}") from exc

    @property
    def algorithm(self) -> HashAlgorithm:
        return self._algorithm

    # ── PBKDF2 ──────────────────────────────────

    def _hash_pbkdf2(self, password: str) -> str:
        algo   = self._algorithm.value
        salt   = secrets.token_bytes(self.SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            algo, password.encode(), salt, self.PBKDF2_ITERATIONS
        )
        return f"{algo}${self.PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"

    @staticmethod
    def _verify_pbkdf2(password: str, stored: str) -> bool:
        parts = stored.split("$")
        if len(parts) != 4:
            raise PasswordHashingError("Malformed hash string.")
        algo, iters, salt_hex, digest_hex = parts
        salt     = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual   = hashlib.pbkdf2_hmac(algo, password.encode(), salt, int(iters))
        return hmac.compare_digest(actual, expected)

    # ── bcrypt ───────────────────────────────────

    def _hash_bcrypt(self, password: str) -> str:
        import bcrypt  # type: ignore
        h = bcrypt.hashpw(password.encode(), bcrypt.gensalt(self.BCRYPT_ROUNDS))
        return f"bcrypt${h.decode()}"

    @staticmethod
    def _verify_bcrypt(password: str, stored: str) -> bool:
        import bcrypt  # type: ignore
        h = stored[len("bcrypt$"):].encode()
        return bcrypt.checkpw(password.encode(), h)

    @staticmethod
    def _check_bcrypt() -> bool:
        try:
            import bcrypt  # noqa: F401
            return True
        except ImportError:
            return False


# ──────────────────────────────────────────────
# User
# ──────────────────────────────────────────────

class User:
    """
    Represents a registered user.

    Sensitive fields are name-mangled (__) and only accessible
    through read-only @property accessors.
    """

    def __init__(self, user_id: str, username: str, hashed_password: str) -> None:
        self.__user_id          = user_id
        self.__username         = username.lower().strip()
        self.__hashed_password  = hashed_password
        self.__created_at       = datetime.now().isoformat(timespec="seconds")
        self.__last_login: Optional[str] = None

    # ── Read-only properties ─────────────────────

    @property
    def user_id(self) -> str:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def hashed_password(self) -> str:
        return self.__hashed_password

    @property
    def created_at(self) -> str:
        return self.__created_at

    @property
    def last_login(self) -> Optional[str]:
        return self.__last_login

    # ── Controlled mutations (UserManager only) ──

    def _update_last_login(self) -> None:
        self.__last_login = datetime.now().isoformat(timespec="seconds")

    def _update_password(self, new_hash: str) -> None:
        self.__hashed_password = new_hash

    # ── Serialisation ────────────────────────────

    def to_dict(self) -> dict:
        return {
            "user_id":         self.__user_id,
            "username":        self.__username,
            "hashed_password": self.__hashed_password,
            "created_at":      self.__created_at,
            "last_login":      self.__last_login,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        u = cls(data["user_id"], data["username"], data["hashed_password"])
        u._User__created_at = data.get("created_at", u.created_at)
        u._User__last_login = data.get("last_login")
        return u

    def __repr__(self) -> str:
        return f"User(id={self.__user_id!r}, username={self.__username!r})"


# ──────────────────────────────────────────────
# PasswordPolicy
# ──────────────────────────────────────────────

@dataclass
class PasswordPolicy:
    """
    Configurable rules applied when a password is created or changed.
    Returns a list of human-readable violation strings (empty list = OK).
    """
    min_length:      int  = 8
    require_upper:   bool = True
    require_lower:   bool = True
    require_digit:   bool = True
    require_special: bool = True

    def validate(self, password: str) -> list[str]:
        v: list[str] = []
        if len(password) < self.min_length:
            v.append(f"Must be at least {self.min_length} characters long.")
        if self.require_upper and not re.search(r"[A-Z]", password):
            v.append("Must contain at least one uppercase letter (A-Z).")
        if self.require_lower and not re.search(r"[a-z]", password):
            v.append("Must contain at least one lowercase letter (a-z).")
        if self.require_digit and not re.search(r"\d", password):
            v.append("Must contain at least one digit (0-9).")
        if self.require_special and not re.search(r"[^A-Za-z0-9]", password):
            v.append("Must contain at least one special character (!@#$...).")
        return v


# ──────────────────────────────────────────────
# UserManager
# ──────────────────────────────────────────────

class UserManager:
    """
    Manages user registration, authentication, and optional persistence.

    Args:
        hasher       - PasswordHasher (SHA-256 PBKDF2 by default).
        policy       - PasswordPolicy.
        storage_file - JSON file for persistence (None = in-memory only).
    """

    _USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{3,32}$")

    def __init__(
        self,
        hasher:       Optional[PasswordHasher] = None,
        policy:       Optional[PasswordPolicy] = None,
        storage_file: Optional[str]            = None,
    ) -> None:
        self._hasher       = hasher or PasswordHasher()
        self._policy       = policy or PasswordPolicy()
        self._storage_file = storage_file
        self._users: dict[str, User] = {}

        if self._storage_file:
            self._load()

    # ── Registration ────────────────────────────

    def register(self, username: str, password: str) -> User:
        """
        Register a new user.

        Raises:
            UserManagerError - duplicate username, bad format, or weak password.
        """
        self._validate_username_format(username)
        key = username.lower().strip()

        if key in self._users:
            raise UserManagerError(f"Username '{username}' is already taken.")

        violations = self._policy.validate(password)
        if violations:
            raise UserManagerError(
                "Password does not meet the requirements:\n"
                + "\n".join(f"  - {v}" for v in violations)
            )

        hashed = self._hasher.hash_password(password)
        user   = User(secrets.token_hex(8), username, hashed)
        self._users[key] = user
        if self._storage_file:
            self._save()
        return user

    # ── Authentication ───────────────────────────

    def authenticate(
        self, username: str, password: str
    ) -> tuple[AuthResult, Optional[User]]:
        """
        Verify credentials.

        Returns:
            (SUCCESS, user)          - correct credentials
            (USER_NOT_FOUND, None)   - unknown username
            (INVALID_PASSWORD, None) - wrong password
        """
        key  = username.lower().strip()
        user = self._users.get(key)

        if user is None:
            return AuthResult.USER_NOT_FOUND, None

        try:
            ok = self._hasher.verify_password(password, user.hashed_password)
        except PasswordHashingError:
            return AuthResult.INVALID_PASSWORD, None

        if not ok:
            return AuthResult.INVALID_PASSWORD, None

        user._update_last_login()
        if self._storage_file:
            self._save()
        return AuthResult.SUCCESS, user

    # ── Password change ──────────────────────────

    def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> None:
        """
        Change a user's password after verifying the current one.

        Raises:
            UserManagerError - auth failure or policy violation.
        """
        result, user = self.authenticate(username, old_password)
        if result == AuthResult.USER_NOT_FOUND:
            raise UserManagerError("User not found.")
        if result == AuthResult.INVALID_PASSWORD:
            raise UserManagerError("Current password is incorrect.")

        violations = self._policy.validate(new_password)
        if violations:
            raise UserManagerError(
                "New password does not meet requirements:\n"
                + "\n".join(f"  - {v}" for v in violations)
            )

        user._update_password(self._hasher.hash_password(new_password))  # type: ignore[union-attr]
        if self._storage_file:
            self._save()

    # ── Helpers ──────────────────────────────────

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username.lower().strip())

    def list_users(self) -> list[User]:
        return list(self._users.values())

    def _validate_username_format(self, username: str) -> None:
        if not self._USERNAME_RE.match(username):
            raise UserManagerError(
                "Username must be 3-32 characters and contain only "
                "letters, digits, underscores, dots, or hyphens."
            )

    # ── Persistence ──────────────────────────────

    def _save(self) -> None:
        try:
            with open(self._storage_file, "w", encoding="utf-8") as fh:
                json.dump(
                    [u.to_dict() for u in self._users.values()],
                    fh, indent=2, ensure_ascii=False,
                )
        except OSError as exc:
            raise UserManagerError(f"Could not save: {exc}") from exc

    def _load(self) -> None:
        if not os.path.exists(self._storage_file):
            return
        try:
            with open(self._storage_file, "r", encoding="utf-8") as fh:
                raw = fh.read().strip()
            if not raw:
                return
            for d in json.loads(raw):
                u = User.from_dict(d)
                self._users[u.username] = u
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            raise UserManagerError(f"Could not load: {exc}") from exc

    def __len__(self) -> int:
        return len(self._users)


# ──────────────────────────────────────────────
# CLI Helpers
# ──────────────────────────────────────────────

DIVIDER = "-" * 58


def _header(title: str) -> None:
    print(f"\n{DIVIDER}\n  {title}\n{DIVIDER}")


def _prompt(label: str, secret: bool = False) -> str:
    """Read a non-empty value, retrying until the user types something."""
    while True:
        try:
            if secret:
                value = _safe_getpass(f"  {label}: ")
            else:
                value = input(f"  {label}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Interrupted — returning to menu.")
            return ""
        if value.strip():
            return value.strip()
        print("  !  This field cannot be empty. Please try again.")


def _print_user_card(user: User) -> None:
    print(f"\n  +- Account Details " + "-" * 38)
    print(f"  |  ID         : {user.user_id}")
    print(f"  |  Username   : {user.username}")
    print(f"  |  Registered : {user.created_at}")
    print(f"  |  Last login : {user.last_login or 'Never'}")
    print(f"  +" + "-" * 55)


# ──────────────────────────────────────────────
# Menu Actions
# ──────────────────────────────────────────────

def action_register(manager: UserManager) -> None:
    _header("Register New User")
    print("  Username : 3-32 chars; letters, digits, _ . -")
    print("  Password : min 8 chars, upper + lower + digit + special\n")

    username = _prompt("Username")
    if not username:
        return

    password = _prompt("Password", secret=True)
    if not password:
        return

    confirm = _prompt("Confirm password", secret=True)
    if not confirm:
        return

    if password != confirm:
        print("\n  !  Passwords do not match. Please try again.\n")
        return

    try:
        user = manager.register(username, password)
        print("\n  [OK]  Registered successfully!")
        _print_user_card(user)
    except UserManagerError as exc:
        print(f"\n  !  Registration failed:\n{exc}\n")


def action_login(manager: UserManager) -> None:
    _header("Log In")

    username = _prompt("Username")
    if not username:
        return

    password = _prompt("Password", secret=True)
    if not password:
        return

    result, user = manager.authenticate(username, password)

    if result == AuthResult.SUCCESS:
        print(f"\n  [OK]  Welcome back, {user.username}!")
        _print_user_card(user)
    elif result == AuthResult.USER_NOT_FOUND:
        print(f"\n  !  No account found for '{username}'.")
        print("     Tip: register first using option 1 from the menu.\n")
    else:
        print("\n  !  Incorrect password. Please try again.\n")


def action_change_password(manager: UserManager) -> None:
    _header("Change Password")

    username = _prompt("Username")
    if not username:
        return

    old_pw = _prompt("Current password", secret=True)
    if not old_pw:
        return

    new_pw = _prompt("New password", secret=True)
    if not new_pw:
        return

    confirm = _prompt("Confirm new password", secret=True)
    if not confirm:
        return

    if new_pw != confirm:
        print("\n  !  New passwords do not match. Please try again.\n")
        return

    try:
        manager.change_password(username, old_pw, new_pw)
        print("\n  [OK]  Password changed successfully.\n")
    except UserManagerError as exc:
        print(f"\n  !  {exc}\n")


def action_list_users(manager: UserManager) -> None:
    _header("Registered Users")
    users = manager.list_users()
    if not users:
        print("\n  No users registered yet.\n")
        return
    print(f"\n  {'#':<4} {'Username':<22} {'Registered':<22} Last Login")
    print(f"  {'-'*4} {'-'*22} {'-'*21} {'-'*20}")
    for i, u in enumerate(users, 1):
        ll = u.last_login or "-"
        print(f"  {i:<4} {u.username:<22} {u.created_at:<22} {ll}")
    print()


def action_verify_hash(manager: UserManager) -> None:
    _header("Verify Password Against Stored Hash")

    username = _prompt("Username")
    if not username:
        return

    user = manager.get_user(username)
    if user is None:
        print(f"\n  !  No account found for '{username}'.\n")
        return

    password = _prompt("Password to verify", secret=True)
    if not password:
        return

    result, _ = manager.authenticate(username, password)
    if result == AuthResult.SUCCESS:
        print("\n  [OK]  Password matches the stored hash.\n")
    else:
        print("\n  !  Password does NOT match the stored hash.\n")


# ──────────────────────────────────────────────
# Built-in Test Suite
# ──────────────────────────────────────────────

def _run_tests() -> None:
    """
    Full self-contained test suite.
    Run with:  python password_hashing_system.py --test
    """
    import tempfile

    results: list[tuple[str, bool]] = []

    def check(label: str, cond: bool) -> None:
        results.append((label, cond))
        icon = "PASS" if cond else "FAIL"
        print(f"  [{icon}]  {label}")

    print("\n" + "=" * 58)
    print("  Running built-in test suite ...")
    print("=" * 58)

    # ── PasswordHasher ───────────────────────────
    print("\n  PasswordHasher (SHA-256)")
    h      = PasswordHasher(HashAlgorithm.SHA256)
    hashed = h.hash_password("SecurePass1!")
    check("SHA-256 hash has correct prefix",    hashed.startswith("sha256$"))
    check("SHA-256 correct password verifies",  h.verify_password("SecurePass1!", hashed))
    check("SHA-256 wrong password rejected",    not h.verify_password("WrongPass1!", hashed))
    check("SHA-256 empty plain -> False",       not h.verify_password("", hashed))
    check("Two hashes of same pwd differ",
          h.hash_password("SecurePass1!") != h.hash_password("SecurePass1!"))

    print("\n  PasswordHasher (SHA-512)")
    h512 = PasswordHasher(HashAlgorithm.SHA512)
    h5   = h512.hash_password("Hello@World9")
    check("SHA-512 hash has correct prefix",    h5.startswith("sha512$"))
    check("SHA-512 correct password verifies",  h512.verify_password("Hello@World9", h5))

    try:
        h.hash_password("")
        check("Empty password raises PasswordHashingError", False)
    except PasswordHashingError:
        check("Empty password raises PasswordHashingError", True)

    # ── PasswordPolicy ───────────────────────────
    print("\n  PasswordPolicy")
    p = PasswordPolicy()
    check("Strong password passes",          p.validate("SecurePass1!") == [])
    check("Too-short password fails",        len(p.validate("Sh0!")) > 0)
    check("No-uppercase fails",              len(p.validate("nouppercase1!")) > 0)
    check("No-lowercase fails",              len(p.validate("NOLOWERCASE1!")) > 0)
    check("No-digit fails",                  len(p.validate("NoDigitHere!")) > 0)
    check("No-special fails",               len(p.validate("NoSpecial1A")) > 0)

    # ── UserManager ──────────────────────────────
    print("\n  UserManager (in-memory)")
    mgr  = UserManager()
    user = mgr.register("alice", "SecurePass1!")
    check("register() returns User",         isinstance(user, User))
    check("Username normalised lowercase",   user.username == "alice")
    check("User stored",                     mgr.get_user("alice") is not None)
    check("list_users() returns 1 user",     len(mgr.list_users()) == 1)

    try:
        mgr.register("Alice", "SecurePass1!")
        check("Duplicate username rejected", False)
    except UserManagerError:
        check("Duplicate username rejected", True)

    try:
        mgr.register("x", "SecurePass1!")
        check("Too-short username rejected", False)
    except UserManagerError:
        check("Too-short username rejected", True)

    try:
        mgr.register("bob", "weak")
        check("Weak password rejected on register", False)
    except UserManagerError:
        check("Weak password rejected on register", True)

    # ── Authentication ───────────────────────────
    print("\n  Authentication")
    r, u = mgr.authenticate("alice", "SecurePass1!")
    check("Correct credentials -> SUCCESS",  r == AuthResult.SUCCESS)
    check("Returned user is correct",        u is not None and u.username == "alice")
    check("last_login updated",              u is not None and u.last_login is not None)

    r2, _ = mgr.authenticate("alice", "WrongPass9!")
    check("Wrong password -> INVALID_PASSWORD",  r2 == AuthResult.INVALID_PASSWORD)

    r3, _ = mgr.authenticate("ghost", "SecurePass1!")
    check("Unknown user -> USER_NOT_FOUND",  r3 == AuthResult.USER_NOT_FOUND)

    # ── Change password ──────────────────────────
    print("\n  Change Password")
    mgr.change_password("alice", "SecurePass1!", "NewPass99@!")
    r4, _ = mgr.authenticate("alice", "NewPass99@!")
    check("New password works after change",     r4 == AuthResult.SUCCESS)
    r5, _ = mgr.authenticate("alice", "SecurePass1!")
    check("Old password rejected after change",  r5 == AuthResult.INVALID_PASSWORD)

    try:
        mgr.change_password("alice", "NewPass99@!", "weak")
        check("Weak new password rejected", False)
    except UserManagerError:
        check("Weak new password rejected", True)

    try:
        mgr.change_password("alice", "WrongPass9!", "AnotherPass1!")
        check("Wrong current password rejected", False)
    except UserManagerError:
        check("Wrong current password rejected", True)

    # ── Persistence ──────────────────────────────
    print("\n  JSON Persistence")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp = f.name

    try:
        mgr2 = UserManager(storage_file=tmp)
        mgr2.register("bob", "BobPass99@!")
        r6, _ = mgr2.authenticate("bob", "BobPass99@!")
        check("Auth works before reload",        r6 == AuthResult.SUCCESS)

        mgr3 = UserManager(storage_file=tmp)
        check("User survives JSON reload",       mgr3.get_user("bob") is not None)
        r7, _ = mgr3.authenticate("bob", "BobPass99@!")
        check("Auth works after JSON reload",    r7 == AuthResult.SUCCESS)

        # Empty-file edge case
        open(tmp, "w").close()
        mgr4 = UserManager(storage_file=tmp)
        check("Empty JSON file handled gracefully", len(mgr4) == 0)
    finally:
        os.unlink(tmp)

    # ── Encapsulation ────────────────────────────
    print("\n  User Encapsulation")
    u2 = mgr.get_user("alice")
    check("hashed_password is not plain text",
          u2 is not None and u2.hashed_password != "NewPass99@!")
    check("hashed_password is self-describing string",
          u2 is not None and "$" in u2.hashed_password)
    try:
        _ = u2.__username  # type: ignore[attr-defined]
        check("__username is name-mangled (inaccessible)", False)
    except AttributeError:
        check("__username is name-mangled (inaccessible)", True)

    # ── Summary ──────────────────────────────────
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    failed = [lbl for lbl, ok in results if not ok]

    print("\n" + "=" * 58)
    print(f"  Results: {passed}/{total} passed")
    if failed:
        print("\n  FAILURES:")
        for lbl in failed:
            print(f"    [FAIL]  {lbl}")
        print("=" * 58)
        sys.exit(1)
    else:
        print("  All tests passed!")
        print("=" * 58 + "\n")


# ──────────────────────────────────────────────
# Main CLI Loop
# ──────────────────────────────────────────────

MENU_ITEMS = [
    ("Register a new user",           action_register),
    ("Log in",                        action_login),
    ("Change password",               action_change_password),
    ("Verify password against hash",  action_verify_hash),
    ("List registered users",         action_list_users),
]


def run_cli() -> None:
    print("\n+----------------------------------------------------------+")
    print("|          Password Hashing System  v1.1                   |")
    print("+----------------------------------------------------------+")
    print("  Passwords are hashed with PBKDF2-HMAC-SHA256 (600,000 iter).")
    print("  User data is saved to  users.json  in the current directory.")
    print("  Run with --test to execute the built-in test suite.\n")

    try:
        manager = UserManager(storage_file="users.json")
        if len(manager):
            print(f"  [OK]  Loaded {len(manager)} user(s) from users.json")
    except UserManagerError as exc:
        print(f"\n  [!]  Could not load users.json: {exc}")
        manager = UserManager()

    while True:
        _header("Main Menu")
        for i, (label, _) in enumerate(MENU_ITEMS, 1):
            print(f"  {i}. {label}")
        print("  0. Exit\n")

        try:
            choice = input("  Select an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Goodbye! Stay secure.\n")
            break

        if choice == "0":
            print("\n  Goodbye! Stay secure.\n")
            break

        if choice.isdigit() and 1 <= int(choice) <= len(MENU_ITEMS):
            _, action = MENU_ITEMS[int(choice) - 1]
            action(manager)
        else:
            print(f"\n  !  Invalid choice. Please enter a number between 0 and {len(MENU_ITEMS)}.")


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if "--test" in sys.argv:
        _run_tests()
    else:
        run_cli()