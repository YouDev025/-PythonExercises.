"""
Secure Password Generator
A robust, OOP-based password generation and management system.
"""

import secrets
import string
import json
import os
from datetime import datetime
from typing import Optional


# ──────────────────────────────────────────────
# Custom Exceptions
# ──────────────────────────────────────────────

class PasswordGeneratorError(Exception):
    """Raised when password generation fails due to invalid configuration."""
    pass


class PasswordManagerError(Exception):
    """Raised for errors in PasswordManager operations."""
    pass


# ──────────────────────────────────────────────
# PasswordGenerator Class
# ──────────────────────────────────────────────

class PasswordGenerator:
    """
    Generates cryptographically strong passwords based on user-defined criteria.

    Attributes:
        password_length        (int):  Number of characters in the password.
        include_uppercase      (bool): Include A–Z characters.
        include_lowercase      (bool): Include a–z characters.
        include_digits         (bool): Include 0–9 characters.
        include_special_chars  (bool): Include special/punctuation characters.
    """

    MIN_LENGTH: int = 6
    MAX_LENGTH: int = 128

    UPPERCASE:      str = string.ascii_uppercase          # A-Z
    LOWERCASE:      str = string.ascii_lowercase          # a-z
    DIGITS:         str = string.digits                   # 0-9
    SPECIAL_CHARS:  str = string.punctuation              # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~

    def __init__(
        self,
        password_length:       int  = 16,
        include_uppercase:     bool = True,
        include_lowercase:     bool = True,
        include_digits:        bool = True,
        include_special_chars: bool = True,
    ) -> None:
        self.password_length       = password_length
        self.include_uppercase     = include_uppercase
        self.include_lowercase     = include_lowercase
        self.include_digits        = include_digits
        self.include_special_chars = include_special_chars

    # ── Properties with validation ──────────────

    @property
    def password_length(self) -> int:
        return self._password_length

    @password_length.setter
    def password_length(self, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise PasswordGeneratorError("Password length must be an integer.")
        if not (self.MIN_LENGTH <= value <= self.MAX_LENGTH):
            raise PasswordGeneratorError(
                f"Password length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH}."
            )
        self._password_length = value

    # ── Core generation logic ────────────────────

    def _build_character_pool(self) -> str:
        """Combine enabled character sets into one pool."""
        pool = ""
        if self.include_uppercase:
            pool += self.UPPERCASE
        if self.include_lowercase:
            pool += self.LOWERCASE
        if self.include_digits:
            pool += self.DIGITS
        if self.include_special_chars:
            pool += self.SPECIAL_CHARS
        return pool

    def _guarantee_characters(self) -> list[str]:
        """
        Return a list containing at least one character from every
        enabled character set (ensures policy compliance).
        """
        guaranteed: list[str] = []
        if self.include_uppercase:
            guaranteed.append(secrets.choice(self.UPPERCASE))
        if self.include_lowercase:
            guaranteed.append(secrets.choice(self.LOWERCASE))
        if self.include_digits:
            guaranteed.append(secrets.choice(self.DIGITS))
        if self.include_special_chars:
            guaranteed.append(secrets.choice(self.SPECIAL_CHARS))
        return guaranteed

    def generate(self) -> str:
        """
        Generate a cryptographically secure password.

        Returns:
            A password string satisfying all enabled character-type requirements.

        Raises:
            PasswordGeneratorError: If no character types are enabled or the
                                    length is too short for the required sets.
        """
        pool = self._build_character_pool()
        if not pool:
            raise PasswordGeneratorError(
                "At least one character type must be selected."
            )

        guaranteed = self._guarantee_characters()

        if len(guaranteed) > self.password_length:
            raise PasswordGeneratorError(
                f"Password length ({self.password_length}) is too short to include "
                f"one character from each of the {len(guaranteed)} enabled types. "
                f"Increase length to at least {len(guaranteed)}."
            )

        # Fill remaining slots from the full pool
        remaining_count = self.password_length - len(guaranteed)
        remaining = [secrets.choice(pool) for _ in range(remaining_count)]

        # Shuffle with cryptographically secure RNG
        password_chars = guaranteed + remaining
        secrets.SystemRandom().shuffle(password_chars)

        return "".join(password_chars)

    def __repr__(self) -> str:
        return (
            f"PasswordGenerator(length={self.password_length}, "
            f"upper={self.include_uppercase}, lower={self.include_lowercase}, "
            f"digits={self.include_digits}, special={self.include_special_chars})"
        )


# ──────────────────────────────────────────────
# PasswordEntry (data container)
# ──────────────────────────────────────────────

class PasswordEntry:
    """Stores a generated password together with its label and timestamp."""

    def __init__(self, label: str, password: str) -> None:
        self.label:      str = label
        self.password:   str = password
        self.created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "label":      self.label,
            "password":   self.password,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PasswordEntry":
        entry = cls(data["label"], data["password"])
        entry.created_at = data.get("created_at", "N/A")
        return entry

    def __str__(self) -> str:
        return f"[{self.created_at}]  {self.label:<30}  {self.password}"


# ──────────────────────────────────────────────
# PasswordManager Class
# ──────────────────────────────────────────────

class PasswordManager:
    """
    Orchestrates password generation requests and manages stored entries.

    Responsibilities:
        - Accept generation parameters and delegate to PasswordGenerator.
        - Store PasswordEntry objects in memory with optional persistence.
        - Load / save entries to a JSON file.
    """

    def __init__(self, storage_file: Optional[str] = None) -> None:
        self._entries:      list[PasswordEntry] = []
        self._storage_file: Optional[str]       = storage_file

        if self._storage_file:
            self._load()

    # ── Generation ───────────────────────────────

    def generate_password(
        self,
        length:               int  = 16,
        include_uppercase:    bool = True,
        include_lowercase:    bool = True,
        include_digits:       bool = True,
        include_special_chars:bool = True,
    ) -> str:
        """Create a PasswordGenerator, validate config, and return a password."""
        generator = PasswordGenerator(
            password_length       = length,
            include_uppercase     = include_uppercase,
            include_lowercase     = include_lowercase,
            include_digits        = include_digits,
            include_special_chars = include_special_chars,
        )
        return generator.generate()

    # ── Storage ──────────────────────────────────

    def save_entry(self, label: str, password: str) -> PasswordEntry:
        """Store a password with the given label and return the entry."""
        if not label.strip():
            raise PasswordManagerError("Label cannot be empty.")
        entry = PasswordEntry(label.strip(), password)
        self._entries.append(entry)
        if self._storage_file:
            self._save()
        return entry

    def list_entries(self) -> list[PasswordEntry]:
        """Return all stored entries (read-only view)."""
        return list(self._entries)

    def delete_entry(self, index: int) -> PasswordEntry:
        """Remove and return the entry at the given 1-based index."""
        if not (1 <= index <= len(self._entries)):
            raise PasswordManagerError(
                f"Index {index} is out of range. Valid range: 1–{len(self._entries)}."
            )
        removed = self._entries.pop(index - 1)
        if self._storage_file:
            self._save()
        return removed

    def clear_entries(self) -> None:
        """Delete all stored entries."""
        self._entries.clear()
        if self._storage_file:
            self._save()

    # ── Persistence ──────────────────────────────

    def _save(self) -> None:
        try:
            with open(self._storage_file, "w", encoding="utf-8") as fh:
                json.dump(
                    [e.to_dict() for e in self._entries],
                    fh,
                    indent=2,
                    ensure_ascii=False,
                )
        except OSError as exc:
            raise PasswordManagerError(f"Could not save passwords: {exc}") from exc

    def _load(self) -> None:
        if not os.path.exists(self._storage_file):
            return
        try:
            with open(self._storage_file, "r", encoding="utf-8") as fh:
                content = fh.read().strip()
            if not content:          # empty file → start fresh
                return
            data = json.loads(content)
            self._entries = [PasswordEntry.from_dict(d) for d in data]
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            raise PasswordManagerError(f"Could not load passwords: {exc}") from exc

    def __len__(self) -> int:
        return len(self._entries)


# ──────────────────────────────────────────────
# CLI Helpers
# ──────────────────────────────────────────────

DIVIDER = "─" * 56

def _print_header(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

def _ask_yes_no(prompt: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        raw = input(f"  {prompt} {hint}: ").strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Please enter y or n.")

def _ask_int(prompt: str, lo: int, hi: int, default: Optional[int] = None) -> int:
    hint = f"({lo}–{hi})" + (f" [default: {default}]" if default is not None else "")
    while True:
        raw = input(f"  {prompt} {hint}: ").strip()
        if raw == "" and default is not None:
            return default
        if raw.isdigit():
            value = int(raw)
            if lo <= value <= hi:
                return value
        print(f"  Please enter a whole number between {lo} and {hi}.")

def _collect_generation_params() -> dict:
    """Prompt the user for all generation parameters and return as a dict."""
    _print_header("Password Configuration")
    length = _ask_int(
        "Password length",
        PasswordGenerator.MIN_LENGTH,
        PasswordGenerator.MAX_LENGTH,
        default=16,
    )
    print()
    upper   = _ask_yes_no("Include uppercase letters (A–Z)?",  default=True)
    lower   = _ask_yes_no("Include lowercase letters (a–z)?",  default=True)
    digits  = _ask_yes_no("Include digits (0–9)?",             default=True)
    special = _ask_yes_no("Include special characters (!@#…)?", default=True)

    return dict(
        length               = length,
        include_uppercase    = upper,
        include_lowercase    = lower,
        include_digits       = digits,
        include_special_chars= special,
    )


# ──────────────────────────────────────────────
# Menu Actions
# ──────────────────────────────────────────────

def action_generate(manager: PasswordManager) -> None:
    """Generate (and optionally save) a new password."""
    try:
        params = _collect_generation_params()
        password = manager.generate_password(**params)
    except PasswordGeneratorError as exc:
        print(f"\n  ✖  {exc}")
        return

    _print_header("Generated Password")
    print(f"\n  ➤  {password}\n")

    if _ask_yes_no("Save this password with a label?", default=False):
        label = input("  Label (e.g. Gmail, GitHub): ").strip()
        try:
            entry = manager.save_entry(label, password)
            print(f"\n  ✔  Saved as: {entry.label}")
        except PasswordManagerError as exc:
            print(f"\n  ✖  {exc}")


def action_view_saved(manager: PasswordManager) -> None:
    """Display all saved passwords."""
    _print_header("Saved Passwords")
    entries = manager.list_entries()
    if not entries:
        print("\n  No passwords saved yet.\n")
        return

    print(f"\n  {'#':<4} {'Date & Time':<21} {'Label':<30} Password")
    print(f"  {'─'*4} {'─'*20} {'─'*30} {'─'*20}")
    for i, entry in enumerate(entries, start=1):
        print(f"  {i:<4} {entry.created_at:<21} {entry.label:<30} {entry.password}")
    print()


def action_delete_saved(manager: PasswordManager) -> None:
    """Remove a saved password by index."""
    _print_header("Delete Saved Password")
    entries = manager.list_entries()
    if not entries:
        print("\n  No passwords saved yet.\n")
        return

    action_view_saved(manager)
    idx = _ask_int("Enter the number to delete", 1, len(entries))
    try:
        removed = manager.delete_entry(idx)
        print(f"\n  ✔  Deleted entry: {removed.label}\n")
    except PasswordManagerError as exc:
        print(f"\n  ✖  {exc}")


def action_quick_generate(manager: PasswordManager) -> None:
    """Generate a password with sensible defaults (no prompting)."""
    try:
        password = manager.generate_password()
        _print_header("Quick Password (defaults)")
        print(f"\n  ➤  {password}\n")
    except PasswordGeneratorError as exc:
        print(f"\n  ✖  {exc}")


# ──────────────────────────────────────────────
# Main CLI Loop
# ──────────────────────────────────────────────

MENU_ITEMS = [
    ("Generate new password",           action_generate),
    ("Quick generate (default settings)", action_quick_generate),
    ("View saved passwords",            action_view_saved),
    ("Delete a saved password",         action_delete_saved),
]

def run_cli() -> None:
    """Entry point for the interactive command-line interface."""
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║          🔐  Secure Password Generator v1.0          ║")
    print("╚══════════════════════════════════════════════════════╝")

    storage_file = "passwords.json"
    try:
        manager = PasswordManager(storage_file=storage_file)
        if len(manager) > 0:
            print(f"\n  ✔  Loaded {len(manager)} saved password(s) from {storage_file}")
    except PasswordManagerError as exc:
        print(f"\n  ⚠  Could not load saved passwords: {exc}")
        manager = PasswordManager()

    while True:
        _print_header("Main Menu")
        for i, (label, _) in enumerate(MENU_ITEMS, start=1):
            print(f"  {i}. {label}")
        print(f"  0. Exit")
        print()

        raw = input("  Select an option: ").strip()
        if raw == "0":
            print("\n  Goodbye! Stay secure. 🔒\n")
            break
        if raw.isdigit() and 1 <= int(raw) <= len(MENU_ITEMS):
            _, action = MENU_ITEMS[int(raw) - 1]
            action(manager)
        else:
            print(f"\n  Invalid choice. Please enter 0–{len(MENU_ITEMS)}.")


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    run_cli()