"""
password_policy_manager.py
===========================
Manages and enforces password security policies for users.
Built with Python OOP: encapsulation, abstraction, and modularity.
"""

import hashlib
import secrets
import string
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional


# ─────────────────────────────────────────────────────────────
# ANSI Colour Helpers
# ─────────────────────────────────────────────────────────────

class Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    ORANGE  = "\033[38;5;208m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    CYAN    = "\033[96m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    GREY    = "\033[90m"
    WHITE   = "\033[97m"

    @staticmethod
    def ok(text: str)   -> str: return f"{Color.GREEN}{text}{Color.RESET}"
    @staticmethod
    def fail(text: str) -> str: return f"{Color.RED}{text}{Color.RESET}"
    @staticmethod
    def warn(text: str) -> str: return f"{Color.YELLOW}{text}{Color.RESET}"
    @staticmethod
    def hi(text: str)   -> str: return f"{Color.CYAN}{text}{Color.RESET}"
    @staticmethod
    def bold(text: str) -> str: return f"{Color.BOLD}{text}{Color.RESET}"


def _now() -> datetime:
    return datetime.now()

def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")

def _short(uid: str) -> str:
    return uid[:8].upper()


# ─────────────────────────────────────────────────────────────
# PasswordPolicy Class
# ─────────────────────────────────────────────────────────────

class PasswordPolicy:
    """
    Defines the rules that all passwords must satisfy.
    Encapsulates every policy attribute with validation on set.
    """

    SPECIAL_CHARS = r"""!@#$%^&*()_+-=[]{}|;':\",./<>?"""

    def __init__(
        self,
        minimum_length:            int  = 12,
        require_uppercase:         bool = True,
        require_lowercase:         bool = True,
        require_digits:            bool = True,
        require_special_characters:bool = True,
        password_expiration_days:  int  = 90,
        max_length:                int  = 128,
        min_unique_chars:          int  = 5,
        disallow_username_in_pass: bool = True,
        disallow_common_passwords: bool = True,
        max_repeated_chars:        int  = 3,
    ):
        # Use setters for all fields so validation runs at init too
        self.minimum_length             = minimum_length
        self.require_uppercase          = require_uppercase
        self.require_lowercase          = require_lowercase
        self.require_digits             = require_digits
        self.require_special_characters = require_special_characters
        self.password_expiration_days   = password_expiration_days
        self.max_length                 = max_length
        self.min_unique_chars           = min_unique_chars
        self.disallow_username_in_pass  = disallow_username_in_pass
        self.disallow_common_passwords  = disallow_common_passwords
        self.max_repeated_chars         = max_repeated_chars

    # ── Validated setters ────────────────────

    @property
    def minimum_length(self) -> int:
        return self.__minimum_length

    @minimum_length.setter
    def minimum_length(self, v: int):
        if not isinstance(v, int) or v < 4:
            raise ValueError("minimum_length must be an integer >= 4.")
        self.__minimum_length = v

    @property
    def max_length(self) -> int:
        return self.__max_length

    @max_length.setter
    def max_length(self, v: int):
        if not isinstance(v, int) or v < 8:
            raise ValueError("max_length must be an integer >= 8.")
        self.__max_length = v

    @property
    def require_uppercase(self) -> bool:
        return self.__require_uppercase

    @require_uppercase.setter
    def require_uppercase(self, v: bool):
        if not isinstance(v, bool):
            raise TypeError("require_uppercase must be bool.")
        self.__require_uppercase = v

    @property
    def require_lowercase(self) -> bool:
        return self.__require_lowercase

    @require_lowercase.setter
    def require_lowercase(self, v: bool):
        if not isinstance(v, bool):
            raise TypeError("require_lowercase must be bool.")
        self.__require_lowercase = v

    @property
    def require_digits(self) -> bool:
        return self.__require_digits

    @require_digits.setter
    def require_digits(self, v: bool):
        if not isinstance(v, bool):
            raise TypeError("require_digits must be bool.")
        self.__require_digits = v

    @property
    def require_special_characters(self) -> bool:
        return self.__require_special_characters

    @require_special_characters.setter
    def require_special_characters(self, v: bool):
        if not isinstance(v, bool):
            raise TypeError("require_special_characters must be bool.")
        self.__require_special_characters = v

    @property
    def password_expiration_days(self) -> int:
        return self.__password_expiration_days

    @password_expiration_days.setter
    def password_expiration_days(self, v: int):
        if not isinstance(v, int) or v < 0:
            raise ValueError("password_expiration_days must be a non-negative integer.")
        self.__password_expiration_days = v

    @property
    def min_unique_chars(self) -> int:
        return self.__min_unique_chars

    @min_unique_chars.setter
    def min_unique_chars(self, v: int):
        if not isinstance(v, int) or v < 1:
            raise ValueError("min_unique_chars must be an integer >= 1.")
        self.__min_unique_chars = v

    @property
    def disallow_username_in_pass(self) -> bool:
        return self.__disallow_username_in_pass

    @disallow_username_in_pass.setter
    def disallow_username_in_pass(self, v: bool):
        if not isinstance(v, bool):
            raise TypeError("disallow_username_in_pass must be bool.")
        self.__disallow_username_in_pass = v

    @property
    def disallow_common_passwords(self) -> bool:
        return self.__disallow_common_passwords

    @disallow_common_passwords.setter
    def disallow_common_passwords(self, v: bool):
        if not isinstance(v, bool):
            raise TypeError("disallow_common_passwords must be bool.")
        self.__disallow_common_passwords = v

    @property
    def max_repeated_chars(self) -> int:
        return self.__max_repeated_chars

    @max_repeated_chars.setter
    def max_repeated_chars(self, v: int):
        if not isinstance(v, int) or v < 1:
            raise ValueError("max_repeated_chars must be an integer >= 1.")
        self.__max_repeated_chars = v

    def to_dict(self) -> dict:
        return {
            "minimum_length":             self.__minimum_length,
            "max_length":                 self.__max_length,
            "require_uppercase":          self.__require_uppercase,
            "require_lowercase":          self.__require_lowercase,
            "require_digits":             self.__require_digits,
            "require_special_characters": self.__require_special_characters,
            "password_expiration_days":   self.__password_expiration_days,
            "min_unique_chars":           self.__min_unique_chars,
            "disallow_username_in_pass":  self.__disallow_username_in_pass,
            "disallow_common_passwords":  self.__disallow_common_passwords,
            "max_repeated_chars":         self.__max_repeated_chars,
        }

    def __repr__(self) -> str:
        return (f"PasswordPolicy(min={self.__minimum_length}, "
                f"expiry={self.__password_expiration_days}d)")


# ─────────────────────────────────────────────────────────────
# User Class
# ─────────────────────────────────────────────────────────────

class User:
    """
    Represents a registered user account.
    Password is stored only as a salted SHA-256 hash — never in plaintext.
    """

    def __init__(self, username: str, password_hash: str, salt: str):
        if not username.strip():
            raise ValueError("username cannot be empty.")
        self.__user_id              = str(uuid.uuid4())
        self.__username             = username.strip().lower()
        self.__password_hash        = password_hash
        self.__salt                 = salt
        self.__last_password_change = _now()
        self.__created_at           = _now()
        self.__active               = True
        self.__password_history:list[str] = [password_hash]  # hashes only

    # ── Read-only properties ─────────────────

    @property
    def user_id(self)               -> str:      return self.__user_id
    @property
    def username(self)              -> str:      return self.__username
    @property
    def last_password_change(self)  -> datetime: return self.__last_password_change
    @property
    def created_at(self)            -> datetime: return self.__created_at
    @property
    def active(self)                -> bool:     return self.__active

    def deactivate(self) -> None:
        self.__active = False

    def activate(self) -> None:
        self.__active = True

    def verify_password(self, plaintext: str) -> bool:
        """Return True if plaintext matches the stored hash."""
        candidate = hashlib.sha256((self.__salt + plaintext).encode()).hexdigest()
        return candidate == self.__password_hash

    def update_password(self, new_hash: str) -> None:
        """Replace stored hash with new_hash and record change time."""
        self.__password_hash        = new_hash
        self.__last_password_change = _now()
        self.__password_history.append(new_hash)
        # Keep last 10 hashes for history checks
        if len(self.__password_history) > 10:
            self.__password_history = self.__password_history[-10:]

    def hash_in_history(self, candidate_hash: str) -> bool:
        """True if candidate_hash appears in the recent password history."""
        return candidate_hash in self.__password_history

    def days_since_change(self) -> int:
        return (_now() - self.__last_password_change).days

    def __repr__(self) -> str:
        status = "active" if self.__active else "inactive"
        return f"User({_short(self.__user_id)} | {self.__username} | {status})"


# ─────────────────────────────────────────────────────────────
# PolicyValidator Class
# ─────────────────────────────────────────────────────────────

class ValidationResult:
    """Carries the outcome of a policy validation run."""

    def __init__(self):
        self.__passed:  list[str] = []
        self.__failed:  list[str] = []
        self.__warnings:list[str] = []

    def add_pass(self, msg: str)    -> None: self.__passed.append(msg)
    def add_fail(self, msg: str)    -> None: self.__failed.append(msg)
    def add_warning(self, msg: str) -> None: self.__warnings.append(msg)

    @property
    def passed(self)   -> list: return list(self.__passed)
    @property
    def failed(self)   -> list: return list(self.__failed)
    @property
    def warnings(self) -> list: return list(self.__warnings)
    @property
    def is_valid(self) -> bool: return len(self.__failed) == 0

    def score(self) -> int:
        """Rough strength score 0-100."""
        total = len(self.__passed) + len(self.__failed)
        if total == 0:
            return 0
        return int(len(self.__passed) / total * 100)


# Top-200 most common passwords (sample subset for demo)
_COMMON_PASSWORDS = {
    "password", "password1", "123456", "12345678", "123456789",
    "1234567890", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou",
    "master", "sunshine", "ashley", "bailey", "passw0rd",
    "shadow", "123123", "654321", "superman", "michael",
    "football", "jesus", "password2", "welcome", "login",
    "admin", "admin123", "root", "toor", "pass",
    "test", "guest", "hello", "1q2w3e4r", "qwertyuiop",
    "mustang", "access", "2000", "2023", "2024", "2025",
}


class PolicyValidator:
    """
    Stateless validator — applies every rule in the given PasswordPolicy
    to a candidate plaintext password and returns a ValidationResult.
    """

    @classmethod
    def validate(
        cls,
        password: str,
        policy: PasswordPolicy,
        username: str = "",
        existing_hash: Optional[str] = None,
        salt: Optional[str] = None,
    ) -> ValidationResult:
        result = ValidationResult()

        # 1. Minimum length
        if len(password) >= policy.minimum_length:
            result.add_pass(f"Length >= {policy.minimum_length} characters ({len(password)} chars)")
        else:
            result.add_fail(f"Too short: {len(password)} chars (minimum {policy.minimum_length})")

        # 2. Maximum length
        if len(password) <= policy.max_length:
            result.add_pass(f"Length <= {policy.max_length} characters")
        else:
            result.add_fail(f"Too long: {len(password)} chars (maximum {policy.max_length})")

        # 3. Uppercase
        if policy.require_uppercase:
            if any(c.isupper() for c in password):
                result.add_pass("Contains uppercase letter(s)")
            else:
                result.add_fail("Missing uppercase letter(s)")

        # 4. Lowercase
        if policy.require_lowercase:
            if any(c.islower() for c in password):
                result.add_pass("Contains lowercase letter(s)")
            else:
                result.add_fail("Missing lowercase letter(s)")

        # 5. Digits
        if policy.require_digits:
            if any(c.isdigit() for c in password):
                result.add_pass("Contains digit(s)")
            else:
                result.add_fail("Missing digit(s)")

        # 6. Special characters
        if policy.require_special_characters:
            if any(c in PasswordPolicy.SPECIAL_CHARS for c in password):
                result.add_pass("Contains special character(s)")
            else:
                result.add_fail(f"Missing special character(s)  [{PasswordPolicy.SPECIAL_CHARS[:20]}…]")

        # 7. Unique characters
        unique_count = len(set(password))
        if unique_count >= policy.min_unique_chars:
            result.add_pass(f"Contains {unique_count} unique characters (min {policy.min_unique_chars})")
        else:
            result.add_fail(f"Too few unique characters: {unique_count} (min {policy.min_unique_chars})")

        # 8. Repeated characters
        max_run = cls._max_run(password)
        if max_run <= policy.max_repeated_chars:
            result.add_pass(f"No character repeated more than {policy.max_repeated_chars} times in a row")
        else:
            result.add_fail(
                f"Character repeated {max_run} times consecutively "
                f"(max {policy.max_repeated_chars})"
            )

        # 9. Username in password
        if policy.disallow_username_in_pass and username:
            if username.lower() in password.lower():
                result.add_fail(f"Password must not contain the username '{username}'")
            else:
                result.add_pass("Password does not contain username")

        # 10. Common passwords
        if policy.disallow_common_passwords:
            if password.lower() in _COMMON_PASSWORDS:
                result.add_fail("Password is in the list of commonly used passwords")
            else:
                result.add_pass("Password is not a known common password")

        # 11. Password reuse (if hash info provided)
        if existing_hash is not None and salt is not None:
            candidate = hashlib.sha256((salt + password).encode()).hexdigest()
            if candidate == existing_hash:
                result.add_fail("New password must differ from the current password")
            else:
                result.add_pass("Password differs from current password")

        # 12. Entropy warning
        entropy = cls._estimate_entropy(password)
        if entropy < 40:
            result.add_warning(f"Low entropy ({entropy:.0f} bits) — consider a longer, more varied password")
        elif entropy < 60:
            result.add_warning(f"Moderate entropy ({entropy:.0f} bits) — passphrase recommended for higher security")
        else:
            result.add_pass(f"Good entropy ({entropy:.0f} bits)")

        return result

    # ── Private helpers ──────────────────────

    @staticmethod
    def _max_run(password: str) -> int:
        if not password:
            return 0
        max_r = cur_r = 1
        for i in range(1, len(password)):
            if password[i] == password[i - 1]:
                cur_r += 1
                max_r = max(max_r, cur_r)
            else:
                cur_r = 1
        return max_r

    @staticmethod
    def _estimate_entropy(password: str) -> float:
        """Shannon entropy estimate based on character pool size."""
        import math
        pool = 0
        if any(c.islower() for c in password):    pool += 26
        if any(c.isupper() for c in password):    pool += 26
        if any(c.isdigit() for c in password):    pool += 10
        if any(c in PasswordPolicy.SPECIAL_CHARS for c in password): pool += 32
        if pool == 0:
            return 0.0
        return len(password) * math.log2(pool)


# ─────────────────────────────────────────────────────────────
# PolicyManager Class
# ─────────────────────────────────────────────────────────────

class PolicyManager:
    """
    Central manager: holds the active PasswordPolicy, manages Users,
    orchestrates validation, and enforces compliance.
    """

    def __init__(self, policy: Optional[PasswordPolicy] = None):
        self.__policy  = policy if policy else PasswordPolicy()
        self.__users:  dict[str, User] = {}   # username → User
        self.__audit_log: list[dict]   = []

    # ── Policy management ────────────────────

    @property
    def policy(self) -> PasswordPolicy:
        return self.__policy

    def update_policy(self, **kwargs) -> list[str]:
        """
        Update one or more policy attributes.
        Returns list of changes made.  Raises ValueError on invalid values.
        """
        changes = []
        for key, value in kwargs.items():
            if not hasattr(self.__policy, key):
                raise ValueError(f"Unknown policy attribute: '{key}'")
            old = getattr(self.__policy, key)
            setattr(self.__policy, key, value)
            changes.append(f"{key}: {old} → {value}")
        self.__log("POLICY_UPDATED", "system", f"Changes: {'; '.join(changes)}")
        return changes

    def replace_policy(self, new_policy: PasswordPolicy) -> None:
        if not isinstance(new_policy, PasswordPolicy):
            raise TypeError("Must pass a PasswordPolicy instance.")
        self.__policy = new_policy
        self.__log("POLICY_REPLACED", "system", "Policy fully replaced.")

    # ── User registration ────────────────────

    def register_user(self, username: str, password: str) -> User:
        uname = username.strip().lower()
        if not uname:
            raise ValueError("Username cannot be empty.")
        if uname in self.__users:
            raise ValueError(f"Username '{uname}' is already registered.")

        result = PolicyValidator.validate(password, self.__policy, username=uname)
        if not result.is_valid:
            raise ValueError(
                "Password does not meet policy requirements:\n" +
                "\n".join(f"  • {f}" for f in result.failed)
            )

        salt, hashed = self._hash_password(password)
        user = User(uname, hashed, salt)
        self.__users[uname] = user
        self.__log("USER_REGISTERED", uname, "Account created.")
        return user

    def deactivate_user(self, username: str) -> None:
        user = self._get_user(username)
        user.deactivate()
        self.__log("USER_DEACTIVATED", username.lower(), "Account deactivated.")

    def activate_user(self, username: str) -> None:
        user = self._get_user(username)
        user.activate()
        self.__log("USER_ACTIVATED", username.lower(), "Account reactivated.")

    # ── Password operations ──────────────────

    def validate_password_for_user(
        self, username: str, password: str
    ) -> ValidationResult:
        """Run full policy validation for an existing user (includes reuse check)."""
        user = self._get_user(username)
        # Peek at current hash via verify_password helper
        # We pass None so the validator skips reuse check; we do it separately
        result = PolicyValidator.validate(
            password, self.__policy, username=user.username
        )
        # Manual reuse check
        salt, candidate_hash = self._hash_password_with_known_salt(password, user)
        if user.hash_in_history(candidate_hash):
            result.add_fail("Password was recently used — choose a different password.")
        else:
            result.add_pass("Password not found in recent password history.")
        return result

    def change_password(
        self, username: str, current_password: str, new_password: str
    ) -> ValidationResult:
        """Verify current password then apply new one if it passes policy."""
        user = self._get_user(username)
        if not user.active:
            raise PermissionError(f"Account '{username}' is inactive.")
        if not user.verify_password(current_password):
            self.__log("AUTH_FAILED", username.lower(), "Wrong current password during change.")
            raise ValueError("Current password is incorrect.")

        result = self.validate_password_for_user(username, new_password)
        if not result.is_valid:
            self.__log("PASSWORD_CHANGE_FAILED", username.lower(),
                       f"Validation failures: {len(result.failed)}")
            return result

        salt, new_hash = self._hash_password(new_password)
        # Rebuild user with new salt and hash
        user._User__salt = salt          # controlled internal update
        user.update_password(new_hash)
        self.__log("PASSWORD_CHANGED", username.lower(), "Password updated successfully.")
        return result

    def authenticate(self, username: str, password: str) -> bool:
        """Return True if credentials are correct and account is active."""
        try:
            user = self._get_user(username)
        except ValueError:
            return False
        if not user.active:
            return False
        ok = user.verify_password(password)
        self.__log(
            "AUTH_SUCCESS" if ok else "AUTH_FAILED",
            username.lower(),
            "Login attempt."
        )
        return ok

    def check_expiry(self, username: str) -> dict:
        """Return expiry status for a user."""
        user = self._get_user(username)
        exp  = self.__policy.password_expiration_days
        days = user.days_since_change()
        if exp == 0:
            return {"expired": False, "days_since_change": days,
                    "days_remaining": None, "expiry_enabled": False}
        remaining = exp - days
        return {
            "expired":          remaining <= 0,
            "days_since_change":days,
            "days_remaining":   max(0, remaining),
            "expiry_enabled":   True,
        }

    def compliance_report(self) -> list[dict]:
        """Return expiry compliance status for all active users."""
        rows = []
        for user in self.__users.values():
            if not user.active:
                continue
            info = self.check_expiry(user.username)
            rows.append({
                "username":          user.username,
                "last_change":       _fmt(user.last_password_change),
                "days_since_change": info["days_since_change"],
                "days_remaining":    info.get("days_remaining"),
                "expired":           info["expired"],
                "expiry_enabled":    info["expiry_enabled"],
            })
        return sorted(rows, key=lambda r: r["days_since_change"], reverse=True)

    # ── Getters ──────────────────────────────

    def get_user(self, username: str) -> User:
        return self._get_user(username)

    def all_users(self) -> list:
        return list(self.__users.values())

    def audit_log(self, n: int = 50) -> list:
        return self.__audit_log[-n:]

    # ── Password generation helper ───────────

    def generate_compliant_password(self, length: Optional[int] = None) -> str:
        """Generate a random password guaranteed to pass the current policy."""
        target_len = max(
            length or self.__policy.minimum_length,
            self.__policy.minimum_length,
        )
        pool = string.ascii_lowercase
        required_chars = []

        if self.__policy.require_uppercase:
            pool += string.ascii_uppercase
            required_chars.append(secrets.choice(string.ascii_uppercase))
        if self.__policy.require_digits:
            pool += string.digits
            required_chars.append(secrets.choice(string.digits))
        if self.__policy.require_special_characters:
            sc = "!@#$%^&*()_+-="
            pool += sc
            required_chars.append(secrets.choice(sc))
        if self.__policy.require_lowercase:
            required_chars.append(secrets.choice(string.ascii_lowercase))

        remaining = target_len - len(required_chars)
        filler    = [secrets.choice(pool) for _ in range(remaining)]
        combined  = required_chars + filler
        secrets.SystemRandom().shuffle(combined)
        return "".join(combined)

    # ── Private helpers ──────────────────────

    def _get_user(self, username: str) -> User:
        uname = username.strip().lower()
        if uname not in self.__users:
            raise ValueError(f"User '{uname}' not found.")
        return self.__users[uname]

    @staticmethod
    def _hash_password(password: str) -> tuple[str, str]:
        salt   = secrets.token_hex(16)
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        return salt, hashed

    @staticmethod
    def _hash_password_with_known_salt(password: str, user: User) -> tuple[str, str]:
        """Re-derive hash using the user's stored salt (via internal access)."""
        salt   = user._User__salt
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        return salt, hashed

    def __log(self, event: str, actor: str, detail: str) -> None:
        self.__audit_log.append({
            "timestamp": _fmt(_now()),
            "event":     event,
            "actor":     actor,
            "detail":    detail,
        })
        if len(self.__audit_log) > 500:
            self.__audit_log = self.__audit_log[-500:]


# ─────────────────────────────────────────────────────────────
# Display Helpers
# ─────────────────────────────────────────────────────────────

_W = 70

def _sep():   print(f"  {'─' * (_W - 2)}")
def _head():  print(f"  {'═' * (_W - 2)}")


def print_banner():
    print(f"""
{Color.BLUE}  {'▓' * (_W - 2)}{Color.RESET}
{Color.BOLD}{Color.BLUE}  {'PASSWORD POLICY MANAGER':^{_W-2}}{Color.RESET}
{Color.GREY}  {'Enterprise Security Policy Enforcement  v1.0':^{_W-2}}{Color.RESET}
{Color.BLUE}  {'▓' * (_W - 2)}{Color.RESET}
""")


def print_menu():
    sections = [
        ("POLICY", [
            ("1", "View current password policy"),
            ("2", "Update policy setting"),
            ("3", "Reset policy to defaults"),
        ]),
        ("USERS", [
            ("4", "Register a new user"),
            ("5", "List all users"),
            ("6", "View user details & expiry status"),
            ("7", "Activate / deactivate user"),
        ]),
        ("PASSWORDS", [
            ("8", "Check password against policy"),
            ("9", "Change a user's password"),
            ("A", "Authenticate (test login)"),
            ("G", "Generate a compliant password"),
        ]),
        ("REPORTS", [
            ("C", "Compliance report (expiry status)"),
            ("L", "View audit log"),
        ]),
    ]
    _head()
    print(f"  {Color.bold('  MAIN MENU')}")
    for section, opts in sections:
        _sep()
        print(f"  {Color.GREY}  {section}{Color.RESET}")
        for key, label in opts:
            print(f"    {Color.BLUE}[{key}]{Color.RESET}  {label}")
    _sep()
    print(f"    {Color.BLUE}[X]{Color.RESET}  Exit")
    _head()


def print_policy(policy: PasswordPolicy) -> None:
    pd = policy.to_dict()
    _head()
    print(f"  {Color.bold('  ACTIVE PASSWORD POLICY')}")
    _sep()

    def _row(label, value, note=""):
        v_str = Color.ok(str(value)) if isinstance(value, bool) and value \
                else Color.warn(str(value)) if isinstance(value, bool) \
                else Color.hi(str(value))
        note_str = f"  {Color.GREY}{note}{Color.RESET}" if note else ""
        print(f"  {label:<34} {v_str}{note_str}")

    _row("Minimum length",              pd["minimum_length"],             "characters")
    _row("Maximum length",              pd["max_length"],                 "characters")
    _row("Require uppercase",           pd["require_uppercase"])
    _row("Require lowercase",           pd["require_lowercase"])
    _row("Require digits",              pd["require_digits"])
    _row("Require special characters",  pd["require_special_characters"],
         PasswordPolicy.SPECIAL_CHARS[:16] + "…")
    _row("Minimum unique characters",   pd["min_unique_chars"])
    _row("Max consecutive repeated",    pd["max_repeated_chars"],        "chars in a row")
    _row("Disallow username in password",pd["disallow_username_in_pass"])
    _row("Block common passwords",      pd["disallow_common_passwords"])
    exp = pd["password_expiration_days"]
    _row("Password expiration",         f"{exp} days" if exp > 0 else "Never")
    _head()


def print_validation_result(result: ValidationResult, title: str = "VALIDATION RESULT") -> None:
    _head()
    status = Color.ok("  PASSED") if result.is_valid else Color.fail("  FAILED")
    print(f"  {Color.bold(title)}  {status}  {Color.GREY}(score {result.score()}/100){Color.RESET}")
    _sep()

    if result.passed:
        print(f"  {Color.ok('Checks passed:')}")
        for p in result.passed:
            print(f"    {Color.GREEN}✓{Color.RESET}  {p}")
    if result.failed:
        print(f"\n  {Color.fail('Checks failed:')}")
        for f in result.failed:
            print(f"    {Color.RED}✗{Color.RESET}  {f}")
    if result.warnings:
        print(f"\n  {Color.warn('Warnings:')}")
        for w in result.warnings:
            print(f"    {Color.YELLOW}⚠{Color.RESET}  {w}")

    bar_len = 30
    filled  = int(result.score() / 100 * bar_len)
    bar_col = Color.GREEN if result.score() >= 70 else Color.YELLOW if result.score() >= 40 else Color.RED
    bar     = f"{bar_col}{'█' * filled}{Color.GREY}{'░' * (bar_len - filled)}{Color.RESET}"
    print(f"\n  Strength: {bar}  {result.score()}/100")
    _head()


def print_user_table(users: list) -> None:
    if not users:
        print(f"\n  {Color.GREY}No users registered yet.{Color.RESET}\n")
        return
    _head()
    print(f"  {Color.bold(f'  REGISTERED USERS  ({len(users)})')}")
    _sep()
    print(f"  {'Username':<18} {'Created':<17} {'Last Change':<17} {'Status':<10} {'ID'}")
    _sep()
    for u in users:
        status = Color.ok("Active") if u.active else Color.fail("Inactive")
        print(f"  {u.username:<18} {_fmt(u.created_at):<17} "
              f"{_fmt(u.last_password_change):<17} {status:<20} {_short(u.user_id)}")
    _head()


def print_user_detail(user: User, expiry: dict) -> None:
    _head()
    print(f"  {Color.bold('  USER DETAIL')}")
    _sep()
    print(f"  User ID       : {Color.hi(_short(user.user_id))}")
    print(f"  Username      : {Color.bold(user.username)}")
    status = Color.ok("Active") if user.active else Color.fail("Inactive")
    print(f"  Status        : {status}")
    print(f"  Created       : {_fmt(user.created_at)}")
    print(f"  Last Pwd Chg  : {_fmt(user.last_password_change)}")
    print(f"  Days Since Chg: {expiry['days_since_change']}")
    if expiry["expiry_enabled"]:
        rem = expiry["days_remaining"]
        exp = expiry["expired"]
        rem_str = Color.fail("EXPIRED") if exp else (
            Color.warn(f"{rem} days") if rem < 14 else Color.ok(f"{rem} days")
        )
        print(f"  Days Remaining: {rem_str}")
    else:
        print(f"  Expiration    : {Color.GREY}Disabled{Color.RESET}")
    _head()


def print_compliance(rows: list) -> None:
    _head()
    print(f"  {Color.bold('  COMPLIANCE REPORT — PASSWORD EXPIRY')}")
    _sep()
    if not rows:
        print(f"  {Color.GREY}No active users.{Color.RESET}")
        _head()
        return
    print(f"  {'Username':<18} {'Last Change':<17} {'Days Old':<10} {'Remaining':<12} {'Status'}")
    _sep()
    for r in rows:
        if not r["expiry_enabled"]:
            rem_str   = f"{Color.GREY}N/A{Color.RESET}"
            status_str = f"{Color.GREY}No expiry{Color.RESET}"
        elif r["expired"]:
            rem_str    = Color.fail("0")
            status_str = Color.fail("EXPIRED")
        else:
            rem = r["days_remaining"]
            rem_str    = Color.warn(str(rem)) if rem < 14 else Color.ok(str(rem))
            status_str = Color.ok("OK")
        print(f"  {r['username']:<18} {r['last_change']:<17} "
              f"{str(r['days_since_change']):<10} {rem_str:<20} {status_str}")
    _head()


def print_audit_log(entries: list) -> None:
    if not entries:
        print(f"\n  {Color.GREY}Audit log is empty.{Color.RESET}\n")
        return
    _head()
    print(f"  {Color.bold(f'  AUDIT LOG  (last {len(entries)} entries)')}")
    _sep()
    event_colors = {
        "AUTH_SUCCESS":        Color.GREEN,
        "AUTH_FAILED":         Color.RED,
        "USER_REGISTERED":     Color.CYAN,
        "USER_DEACTIVATED":    Color.YELLOW,
        "USER_ACTIVATED":      Color.GREEN,
        "PASSWORD_CHANGED":    Color.GREEN,
        "PASSWORD_CHANGE_FAILED": Color.ORANGE,
        "POLICY_UPDATED":      Color.MAGENTA,
        "POLICY_REPLACED":     Color.MAGENTA,
    }
    for e in entries:
        col = event_colors.get(e["event"], Color.GREY)
        print(f"  {Color.GREY}{e['timestamp']}{Color.RESET}  "
              f"{col}{e['event']:<26}{Color.RESET}  "
              f"{Color.YELLOW}{e['actor']:<18}{Color.RESET}  "
              f"{Color.GREY}{e['detail']}{Color.RESET}")
    _head()


# ─────────────────────────────────────────────────────────────
# CLI Helpers
# ─────────────────────────────────────────────────────────────

def _prompt(msg: str) -> str:
    return input(f"\n  {Color.BLUE}>{Color.RESET} {msg} ").strip()


def _prompt_password(msg: str = "Password:") -> str:
    """Read password without echoing it (falls back to normal input)."""
    import getpass
    try:
        return getpass.getpass(f"\n  > {msg} ")
    except Exception:
        return input(f"\n  > {msg} ").strip()


def _bool_prompt(msg: str, current: bool) -> bool:
    raw = _prompt(f"{msg} [current: {'yes' if current else 'no'}] (y/n):").lower()
    if raw in ("y", "yes"):
        return True
    if raw in ("n", "no"):
        return False
    return current


def _int_prompt(msg: str, current: int, min_val: int = 0) -> int:
    raw = _prompt(f"{msg} [current: {current}]:")
    if not raw:
        return current
    try:
        v = int(raw)
        if v < min_val:
            print(f"  {Color.fail(f'[!] Must be >= {min_val}. Keeping {current}.')}")
            return current
        return v
    except ValueError:
        print(f"  {Color.fail(f'[!] Invalid number. Keeping {current}.')}")
        return current


# ─────────────────────────────────────────────────────────────
# Menu Action Functions
# ─────────────────────────────────────────────────────────────

def cmd_view_policy(manager: PolicyManager) -> None:
    print_policy(manager.policy)


def cmd_update_policy(manager: PolicyManager) -> None:
    p = manager.policy
    pd = p.to_dict()
    print(f"\n  {Color.bold('-- Update Policy --')}")
    print(f"  {Color.GREY}Press ENTER to keep current value.{Color.RESET}\n")

    updates = {}

    new_min = _int_prompt("Minimum password length", pd["minimum_length"], min_val=4)
    if new_min != pd["minimum_length"]:
        updates["minimum_length"] = new_min

    new_max = _int_prompt("Maximum password length", pd["max_length"], min_val=8)
    if new_max != pd["max_length"]:
        updates["max_length"] = new_max

    for attr, label in [
        ("require_uppercase",          "Require uppercase letters"),
        ("require_lowercase",          "Require lowercase letters"),
        ("require_digits",             "Require digits"),
        ("require_special_characters", "Require special characters"),
        ("disallow_username_in_pass",  "Disallow username in password"),
        ("disallow_common_passwords",  "Block common passwords"),
    ]:
        new_val = _bool_prompt(label, pd[attr])
        if new_val != pd[attr]:
            updates[attr] = new_val

    new_uniq = _int_prompt("Minimum unique characters", pd["min_unique_chars"], min_val=1)
    if new_uniq != pd["min_unique_chars"]:
        updates["min_unique_chars"] = new_uniq

    new_rep = _int_prompt("Max consecutive repeated chars", pd["max_repeated_chars"], min_val=1)
    if new_rep != pd["max_repeated_chars"]:
        updates["max_repeated_chars"] = new_rep

    new_exp = _int_prompt("Password expiration (days, 0=never)", pd["password_expiration_days"], min_val=0)
    if new_exp != pd["password_expiration_days"]:
        updates["password_expiration_days"] = new_exp

    if not updates:
        print(f"  {Color.GREY}No changes made.{Color.RESET}")
        return

    try:
        changes = manager.update_policy(**updates)
        print(f"\n  {Color.ok('[OK]')} Policy updated:")
        for c in changes:
            print(f"    {Color.CYAN}•{Color.RESET}  {c}")
    except (ValueError, TypeError) as e:
        print(f"  {Color.fail(f'[!] {e}')}")


def cmd_reset_policy(manager: PolicyManager) -> None:
    confirm = _prompt("Reset policy to secure defaults? (y/n):")
    if confirm.lower() == "y":
        manager.replace_policy(PasswordPolicy())
        print(f"  {Color.ok('[OK]')} Policy reset to defaults.")
    else:
        print("  Cancelled.")


def cmd_register_user(manager: PolicyManager) -> None:
    print(f"\n  {Color.bold('-- Register New User --')}")
    username = _prompt("Username:")
    if not username:
        print(f"  {Color.fail('[!] Username cannot be empty.')}")
        return

    password = _prompt_password("Password (hidden):")
    if not password:
        print(f"  {Color.fail('[!] Password cannot be empty.')}")
        return

    # Show preview validation first
    result = PolicyValidator.validate(password, manager.policy, username=username)
    print_validation_result(result, "REGISTRATION PASSWORD CHECK")

    if not result.is_valid:
        print(f"  {Color.fail('[!] Password does not meet policy. User not registered.')}")
        suggest = _prompt("Generate a compliant password suggestion? (y/n):")
        if suggest.lower() == "y":
            suggestion = manager.generate_compliant_password()
            print(f"\n  {Color.ok('Suggested password:')}  {Color.bold(suggestion)}")
            print(f"  {Color.GREY}(Copy this — it will not be shown again){Color.RESET}")
        return

    try:
        user = manager.register_user(username, password)
        print(f"\n  {Color.ok('[+]')} User {Color.bold(user.username)} registered. "
              f"ID: {Color.hi(_short(user.user_id))}")
    except ValueError as e:
        print(f"  {Color.fail(f'[!] {e}')}")


def cmd_list_users(manager: PolicyManager) -> None:
    print_user_table(manager.all_users())


def cmd_user_detail(manager: PolicyManager) -> None:
    username = _prompt("Username:")
    try:
        user   = manager.get_user(username)
        expiry = manager.check_expiry(username)
        print_user_detail(user, expiry)
    except ValueError as e:
        print(f"  {Color.fail(f'[!] {e}')}")


def cmd_toggle_user(manager: PolicyManager) -> None:
    username = _prompt("Username:")
    try:
        user = manager.get_user(username)
        if user.active:
            confirm = _prompt(f"Deactivate '{user.username}'? (y/n):")
            if confirm.lower() == "y":
                manager.deactivate_user(username)
                print(f"  {Color.warn('[OK]')} User deactivated.")
        else:
            confirm = _prompt(f"Activate '{user.username}'? (y/n):")
            if confirm.lower() == "y":
                manager.activate_user(username)
                print(f"  {Color.ok('[OK]')} User activated.")
    except ValueError as e:
        print(f"  {Color.fail(f'[!] {e}')}")


def cmd_check_password(manager: PolicyManager) -> None:
    print(f"\n  {Color.bold('-- Check Password Against Policy --')}")
    username = _prompt("Username (optional, for username-in-password check, or ENTER to skip):")
    password = _prompt_password("Password to check (hidden):")
    if not password:
        print(f"  {Color.fail('[!] Password cannot be empty.')}")
        return
    result = PolicyValidator.validate(password, manager.policy, username=username)
    print_validation_result(result, "PASSWORD POLICY CHECK")


def cmd_change_password(manager: PolicyManager) -> None:
    print(f"\n  {Color.bold('-- Change Password --')}")
    username = _prompt("Username:")
    try:
        manager.get_user(username)   # existence check
    except ValueError as e:
        print(f"  {Color.fail(f'[!] {e}')}")
        return

    current_pw = _prompt_password("Current password (hidden):")
    new_pw     = _prompt_password("New password (hidden):")

    if not current_pw or not new_pw:
        print(f"  {Color.fail('[!] Both passwords are required.')}")
        return

    try:
        result = manager.change_password(username, current_pw, new_pw)
        print_validation_result(result, "NEW PASSWORD VALIDATION")
        if result.is_valid:
            print(f"  {Color.ok('[OK]')} Password changed successfully.")
        else:
            print(f"  {Color.fail('[!]')} Password change failed — see issues above.")
    except (ValueError, PermissionError) as e:
        print(f"  {Color.fail(f'[!] {e}')}")


def cmd_authenticate(manager: PolicyManager) -> None:
    print(f"\n  {Color.bold('-- Authenticate User --')}")
    username = _prompt("Username:")
    password = _prompt_password("Password (hidden):")
    ok = manager.authenticate(username, password)
    if ok:
        print(f"  {Color.ok('[✓] Authentication successful.')}")
        exp = manager.check_expiry(username)
        if exp["expiry_enabled"] and exp["expired"]:
            print(f"  {Color.fail('[!] WARNING: Password has expired. Please change it.')}")
        elif exp["expiry_enabled"] and exp["days_remaining"] is not None and exp["days_remaining"] < 14:
            days_left = exp["days_remaining"]
            print(f"  {Color.warn(f'[!] Password expires in {days_left} days.')}")
    else:
        print(f"  {Color.fail('[✗] Authentication failed.')}")


def cmd_generate_password(manager: PolicyManager) -> None:
    raw = _prompt("Desired length (ENTER for policy minimum):")
    try:
        length = int(raw) if raw else None
    except ValueError:
        length = None
    pw = manager.generate_compliant_password(length)
    print(f"\n  {Color.ok('Generated password:')}  {Color.bold(pw)}")
    print(f"  {Color.GREY}Length: {len(pw)} chars  — This is shown only once.{Color.RESET}")
    result = PolicyValidator.validate(pw, manager.policy)
    print(f"  Strength score: {Color.hi(str(result.score()))}/100")


def cmd_compliance(manager: PolicyManager) -> None:
    rows = manager.compliance_report()
    print_compliance(rows)


def cmd_audit_log(manager: PolicyManager) -> None:
    raw = _prompt("How many recent entries? [default 30]:")
    try:
        n = int(raw) if raw else 30
    except ValueError:
        n = 30
    entries = manager.audit_log(n)
    print_audit_log(entries)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    print_banner()
    manager = PolicyManager()

    VALID = {"1","2","3","4","5","6","7","8","9","A","G","C","L","X"}
    DISPATCH = {
        "1": lambda: cmd_view_policy(manager),
        "2": lambda: cmd_update_policy(manager),
        "3": lambda: cmd_reset_policy(manager),
        "4": lambda: cmd_register_user(manager),
        "5": lambda: cmd_list_users(manager),
        "6": lambda: cmd_user_detail(manager),
        "7": lambda: cmd_toggle_user(manager),
        "8": lambda: cmd_check_password(manager),
        "9": lambda: cmd_change_password(manager),
        "A": lambda: cmd_authenticate(manager),
        "G": lambda: cmd_generate_password(manager),
        "C": lambda: cmd_compliance(manager),
        "L": lambda: cmd_audit_log(manager),
    }

    while True:
        n_users = len(manager.all_users())
        expired = sum(
            1 for r in manager.compliance_report()
            if r["expired"]
        )
        exp_str = f"  {Color.fail(f'Expired: {expired}')}" if expired else ""
        print(f"\n  {Color.GREY}Policy: min={manager.policy.minimum_length}  "
              f"expiry={manager.policy.password_expiration_days}d  |  "
              f"Users: {n_users}{exp_str}{Color.RESET}")

        print_menu()

        choice = ""
        while choice not in VALID:
            choice = _prompt("Select option:").upper()
            if choice not in VALID:
                print(f"  {Color.fail(f'[!] Invalid. Options: {chr(32).join(sorted(VALID))}')}")

        if choice == "X":
            print(f"\n  {Color.BLUE}[*] Exiting Password Policy Manager. Stay secure.{Color.RESET}\n")
            break

        try:
            DISPATCH[choice]()
        except Exception as exc:
            print(f"\n  {Color.fail(f'[ERROR] Unexpected error: {exc}')}")


if __name__ == "__main__":
    main()