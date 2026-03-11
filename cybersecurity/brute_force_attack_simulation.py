"""
Brute Force Attack Simulation
==============================
An educational, OOP-based simulation of how brute-force password
cracking works.  No real systems are targeted — the "account" lives
entirely in memory.

⚠  FOR EDUCATIONAL USE ONLY  ⚠
This tool exists to demonstrate why short, simple passwords are
dangerous.  Never use brute-force techniques against real accounts
or systems you do not own.

Classes
-------
TargetAccount        – Stores credentials; validates guesses securely.
BruteForceSimulator  – Generates and tests password combinations.
SimulationResult     – Immutable summary of a completed attack run.
AttackManager        – CLI orchestration, display, and session history.
"""

from __future__ import annotations

import hashlib
import itertools
import string
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator


# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

# Character sets available for brute-force attempts
CHARSET_LOWER   = string.ascii_lowercase           # a-z
CHARSET_UPPER   = string.ascii_uppercase           # A-Z
CHARSET_DIGITS  = string.digits                    # 0-9
CHARSET_SYMBOLS = "!@#$%^&*"                       # common symbols
CHARSET_ALPHA   = CHARSET_LOWER + CHARSET_UPPER
CHARSET_ALNUM   = CHARSET_ALPHA + CHARSET_DIGITS
CHARSET_FULL    = CHARSET_ALNUM + CHARSET_SYMBOLS

# Safety cap — prevents runaway simulations
MAX_ATTEMPTS = 10_000_000

# Progress display interval (print every N attempts)
PROGRESS_INTERVAL = 50_000


# ─────────────────────────────────────────────────────────────────────────────
#  TargetAccount
# ─────────────────────────────────────────────────────────────────────────────

class TargetAccount:
    """
    Represents a user account whose password we are trying to crack.

    The plain-text password is never stored after initialisation;
    only its SHA-256 digest is kept, mirroring real-world password
    storage and preventing accidental leakage.
    """

    def __init__(self, username: str, password: str) -> None:
        if not username.strip():
            raise ValueError("Username cannot be empty.")
        self.__username: str = username.strip()
        self.__password_hash: str = self._hash(password)
        self.__password_length: int = len(password)  # exposed for hint only

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # ── properties ────────────────────────────────────────────────────────────

    @property
    def username(self) -> str:
        return self.__username

    @property
    def password_length(self) -> int:
        """Length of the target password (a realistic attacker might know this
        from a leaked hash + metadata; we expose it so demos finish quickly)."""
        return self.__password_length

    # ── public methods ────────────────────────────────────────────────────────

    def check_password(self, attempt: str) -> bool:
        """Return True if *attempt* matches the stored password hash."""
        return self._hash(attempt) == self.__password_hash

    def __str__(self) -> str:
        return f"TargetAccount(username={self.__username!r})"


# ─────────────────────────────────────────────────────────────────────────────
#  SimulationResult
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SimulationResult:
    """Immutable record of a completed brute-force run."""

    target_username: str
    charset_name:    str
    charset_size:    int
    password_length: int
    attempts:        int
    elapsed_seconds: float
    cracked:         bool
    found_password:  str = field(default="")
    timestamp:       str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    @property
    def attempts_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return float("inf")
        return self.attempts / self.elapsed_seconds

    @property
    def theoretical_max(self) -> int:
        """Total combinations for this charset × length."""
        return self.charset_size ** self.password_length

    def summary(self) -> str:
        lines = [
            "─" * 56,
            f"  {'SIMULATION RESULT':^54}",
            "─" * 56,
            f"  Target account   : {self.target_username}",
            f"  Charset          : {self.charset_name} ({self.charset_size} chars)",
            f"  Password length  : {self.password_length}",
            f"  Total attempts   : {self.attempts:,}",
            f"  Time elapsed     : {self.elapsed_seconds:.3f}s",
            f"  Speed            : {self.attempts_per_second:,.0f} attempts/sec",
            f"  Theoretical max  : {self.theoretical_max:,}",
        ]
        if self.cracked:
            lines += [
                f"  Status           : ✅  CRACKED",
                f"  Password found   : '{self.found_password}'",
            ]
        else:
            lines.append("  Status           : ❌  NOT CRACKED (limit reached)")
        lines.append("─" * 56)
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  BruteForceSimulator
# ─────────────────────────────────────────────────────────────────────────────

class BruteForceSimulator:
    """
    Systematically generates password candidates and tests them against
    a TargetAccount.

    The attack is *incremental*: it starts from length 1 and works up to
    *max_length*, testing every combination in lexicographic order.
    If *fixed_length* is provided, only that length is attempted.
    """

    CHARSETS = {
        "1": ("Lowercase letters (a-z)",           CHARSET_LOWER),
        "2": ("Lowercase + digits",                CHARSET_LOWER + CHARSET_DIGITS),
        "3": ("Lowercase + uppercase (a-zA-Z)",    CHARSET_ALPHA),
        "4": ("Alphanumeric (a-zA-Z0-9)",          CHARSET_ALNUM),
        "5": ("Full (alphanumeric + symbols)",     CHARSET_FULL),
    }

    def __init__(
        self,
        target:       TargetAccount,
        charset:      str,
        max_length:   int,
        fixed_length: int | None = None,
        show_live:    bool = True,
    ) -> None:
        if not charset:
            raise ValueError("Charset cannot be empty.")
        if max_length < 1 or max_length > 12:
            raise ValueError("max_length must be between 1 and 12.")

        self.__target       = target
        self.__charset      = charset
        self.__max_length   = max_length
        self.__fixed_length = fixed_length
        self.__show_live    = show_live

        # Mutable state (reset on each run)
        self.__attempts  = 0
        self.__found     = ""
        self.__cracked   = False

    # ── private helpers ───────────────────────────────────────────────────────

    def _candidate_stream(self) -> Iterator[str]:
        """Yield every candidate string for the configured length range."""
        start = self.__fixed_length or 1
        stop  = (self.__fixed_length or self.__max_length) + 1
        for length in range(start, stop):
            for combo in itertools.product(self.__charset, repeat=length):
                yield "".join(combo)

    def _print_progress(self, candidate: str) -> None:
        bar_done  = int(30 * self.__attempts / MAX_ATTEMPTS)
        bar_left  = 30 - bar_done
        bar       = "█" * bar_done + "░" * bar_left
        print(
            f"\r  [{bar}]  #{self.__attempts:>9,}  trying: {candidate:<14}",
            end="",
            flush=True,
        )

    # ── public API ────────────────────────────────────────────────────────────

    def run(self) -> SimulationResult:
        """Execute the brute-force attack and return a SimulationResult."""
        self.__attempts = 0
        self.__found    = ""
        self.__cracked  = False

        print(f"\n  🔓  Attack started on account '{self.__target.username}'")
        print(f"      Charset size : {len(self.__charset)} characters")
        if self.__fixed_length:
            print(f"      Fixed length : {self.__fixed_length}")
        else:
            print(f"      Max length   : {self.__max_length}")
        print(f"      Attempt cap  : {MAX_ATTEMPTS:,}\n")

        t_start = time.perf_counter()

        for candidate in self._candidate_stream():
            self.__attempts += 1

            if self.__show_live and self.__attempts % PROGRESS_INTERVAL == 0:
                self._print_progress(candidate)

            if self.__target.check_password(candidate):
                self.__cracked = True
                self.__found   = candidate
                break

            if self.__attempts >= MAX_ATTEMPTS:
                break

        elapsed = time.perf_counter() - t_start

        if self.__show_live:
            print("\r" + " " * 70 + "\r", end="")  # clear progress line

        return SimulationResult(
            target_username=self.__target.username,
            charset_name=self._charset_label(),
            charset_size=len(self.__charset),
            password_length=self.__target.password_length,
            attempts=self.__attempts,
            elapsed_seconds=round(elapsed, 6),
            cracked=self.__cracked,
            found_password=self.__found,
        )

    def _charset_label(self) -> str:
        for _key, (label, chars) in self.CHARSETS.items():
            if chars == self.__charset:
                return label
        return f"custom ({len(self.__charset)} chars)"


# ─────────────────────────────────────────────────────────────────────────────
#  AttackManager  – CLI orchestration
# ─────────────────────────────────────────────────────────────────────────────

class AttackManager:
    """Manages the interactive brute-force simulation session."""

    def __init__(self) -> None:
        self.__history: list[SimulationResult] = []

    # ── input helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _input(prompt: str) -> str:
        return input(f"  {prompt}").strip()

    @staticmethod
    def _divider(char: str = "─", width: int = 56) -> str:
        return char * width

    def _prompt_account(self) -> TargetAccount:
        print(f"\n{self._divider()}")
        print("  Configure Target Account")
        print(self._divider())

        username = self._input("Username [target_user]: ") or "target_user"

        while True:
            password = self._input("Target password (max 8 chars recommended): ")
            if not password:
                print("  ⚠  Password cannot be empty.")
                continue
            if len(password) > 8:
                print("  ⚠  Passwords longer than 8 chars may take very long.  "
                      "Trim to ≤ 8 for a quick demo.")
                confirm = self._input("Continue anyway? [y/N]: ").lower()
                if confirm != "y":
                    continue
            break

        return TargetAccount(username, password)

    def _prompt_charset(self) -> tuple[str, str]:
        print(f"\n{self._divider()}")
        print("  Select Character Set")
        print(self._divider())
        for key, (label, chars) in BruteForceSimulator.CHARSETS.items():
            print(f"  [{key}]  {label}  (e.g. '{chars[:6]}…')")
        print()

        while True:
            choice = self._input("Charset [1]: ") or "1"
            if choice in BruteForceSimulator.CHARSETS:
                label, chars = BruteForceSimulator.CHARSETS[choice]
                return label, chars
            print("  ⚠  Enter a number from 1 to 5.")

    def _prompt_max_length(self, password_length: int) -> int:
        print(f"\n  (Target password length is {password_length} chars)")
        while True:
            raw = self._input(f"Max length to try [{password_length}]: ") or str(password_length)
            if raw.isdigit() and 1 <= int(raw) <= 12:
                return int(raw)
            print("  ⚠  Enter a number between 1 and 12.")

    def _prompt_live(self) -> bool:
        raw = self._input("Show live attempts? [Y/n]: ").lower()
        return raw != "n"

    # ── display helpers ───────────────────────────────────────────────────────

    def _show_history(self) -> None:
        print(f"\n{self._divider('═')}")
        print("  Session History")
        print(self._divider())
        if not self.__history:
            print("  (no simulations run yet)")
        else:
            for i, r in enumerate(self.__history, 1):
                status = "CRACKED ✅" if r.cracked else "FAILED ❌"
                print(
                    f"  [{i}] {r.timestamp}  {r.target_username:<16}"
                    f"  {r.attempts:>9,} attempts  {r.elapsed_seconds:.3f}s  {status}"
                )
        print(self._divider('═'))

    @staticmethod
    def _educational_note(result: SimulationResult) -> None:
        print("\n  💡  Educational Takeaway")
        print("  " + "─" * 54)
        if result.cracked and result.password_length <= 4:
            print("  Short passwords are cracked almost instantly.")
            print("  Use at least 12 characters in real passwords.")
        elif result.cracked and result.elapsed_seconds < 1:
            print("  Even with a good charset, short passwords fall quickly.")
        elif result.cracked:
            print(f"  The password was found in {result.elapsed_seconds:.2f}s at")
            print(f"  {result.attempts_per_second:,.0f} guesses/sec.")
            print("  Longer passwords grow search space exponentially.")
        else:
            print("  The cap was hit before the password was found.")
            print("  Real attackers use distributed GPUs — even long")
            print("  passwords must use high-entropy characters.")
        print(f"\n  Theoretical space: {result.theoretical_max:,} combinations")
        print(f"  Searched:          {result.attempts:,} ({100*result.attempts/result.theoretical_max:.4f}%)")
        print("  " + "─" * 54)

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        banner = r"""
 ____  ____  _   _ ____    _____
| __ )|  _ \| | | |  _ \  |  ___|__  _ __ ___ ___
|  _ \| |_) | | | | |_) | | |_ / _ \| '__/ __/ _ \
| |_) |  _ <| |_| |  __/  |  _| (_) | | | (_|  __/
|____/|_| \_\\___/|_|     |_|  \___/|_|  \___\___|

  Brute Force Attack Simulation  v1.0
  ⚠  Educational use only — never target real systems ⚠
"""
        menu = """
  [1]  Run a new simulation
  [2]  View session history
  [q]  Quit
"""
        print(banner)

        while True:
            print(menu)
            try:
                choice = input("  Choose an option: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Goodbye!\n")
                break

            if choice == "1":
                try:
                    account = self._prompt_account()
                    _label, charset = self._prompt_charset()
                    max_len = self._prompt_max_length(account.password_length)
                    live    = self._prompt_live()

                    simulator = BruteForceSimulator(
                        target=account,
                        charset=charset,
                        max_length=max_len,
                        fixed_length=None,
                        show_live=live,
                    )

                    result = simulator.run()
                    print(result.summary())
                    self._educational_note(result)
                    self.__history.append(result)

                except (ValueError, KeyboardInterrupt) as exc:
                    if isinstance(exc, KeyboardInterrupt):
                        print("\n\n  ⚠  Simulation interrupted by user.\n")
                    else:
                        print(f"\n  ❌  {exc}\n")

            elif choice == "2":
                self._show_history()

            elif choice in {"q", "quit", "exit"}:
                print("\n  Goodbye!\n")
                break

            else:
                print("\n  ⚠  Unrecognised option.  Enter 1, 2, or q.\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    AttackManager().run()