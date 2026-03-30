"""
╔══════════════════════════════════════════════════════════════╗
║         PASSWORD SPRAYING SIMULATOR — EDUCATIONAL TOOL       ║
║     For Cybersecurity Awareness & Defense Mechanism Study    ║
╚══════════════════════════════════════════════════════════════╝

PURPOSE: Simulates password spraying attacks in a SAFE, controlled,
         offline environment to help security teams understand how
         attackers operate and how detection systems respond.

⚠  WARNING: This tool is strictly for educational and defensive
   purposes. Password spraying against real systems without explicit
   written authorization is illegal and unethical.
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
#  ANSI COLOR HELPERS
# ─────────────────────────────────────────────
class Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"

def c(text: str, *codes: str) -> str:
    """Wrap text in ANSI colour codes."""
    return "".join(codes) + str(text) + Color.RESET


# ─────────────────────────────────────────────
#  DOMAIN MODELS
# ─────────────────────────────────────────────
class UserAccount:
    """Represents a user account with authentication state."""

    MAX_FAILED_ATTEMPTS: int = 5

    def __init__(self, username: str, password: str, role: str = "user"):
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string.")
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string.")

        self.username: str = username.strip().lower()
        self._password_hash: str = self._hash(password)
        self.role: str = role
        self.lock_status: bool = False
        self.failed_attempts: int = 0
        self.last_failed_at: Optional[datetime] = None

    # ── private ──────────────────────────────
    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # ── public ───────────────────────────────
    def verify_password(self, password_try: str) -> bool:
        return self._hash(password_try) == self._password_hash

    def record_failed_attempt(self) -> None:
        self.failed_attempts += 1
        self.last_failed_at = datetime.now()
        if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.lock_status = True

    def reset_failed_attempts(self) -> None:
        self.failed_attempts = 0
        self.last_failed_at = None

    def unlock(self) -> None:
        self.lock_status = False
        self.reset_failed_attempts()

    def is_locked(self) -> bool:
        return self.lock_status

    def __repr__(self) -> str:
        status = c("LOCKED", Color.RED) if self.lock_status else c("active", Color.GREEN)
        return (f"UserAccount(username={self.username!r}, role={self.role!r}, "
                f"status={status}, failed_attempts={self.failed_attempts})")


@dataclass
class SprayAttempt:
    """Immutable record of a single login attempt."""
    username: str
    password_try: str
    timestamp: datetime = field(default_factory=datetime.now)
    result: str = "PENDING"          # SUCCESS | FAILURE | LOCKED
    source_ip: str = "192.168.1.100" # simulated source IP

    def to_log_line(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        icon = {"SUCCESS": "✓", "FAILURE": "✗", "LOCKED": "⊘"}.get(self.result, "?")
        colour = {
            "SUCCESS": Color.GREEN,
            "FAILURE": Color.RED,
            "LOCKED":  Color.YELLOW,
        }.get(self.result, Color.WHITE)
        return (f"  [{ts}] {c(icon, colour)} "
                f"user={c(self.username, Color.CYAN):<22} "
                f"password={c(repr(self.password_try), Color.DIM):<20} "
                f"result={c(self.result, colour)}")


# ─────────────────────────────────────────────
#  AUTHENTICATION SYSTEM
# ─────────────────────────────────────────────
class AuthenticationSystem:
    """Handles login attempts and enforces account-lockout policy."""

    def __init__(self):
        self._accounts: dict[str, UserAccount] = {}

    # ── account management ───────────────────
    def register(self, account: UserAccount) -> None:
        if account.username in self._accounts:
            raise ValueError(f"Account '{account.username}' already exists.")
        self._accounts[account.username] = account

    def get_account(self, username: str) -> Optional[UserAccount]:
        return self._accounts.get(username.strip().lower())

    def all_accounts(self) -> list[UserAccount]:
        return list(self._accounts.values())

    def unlock_account(self, username: str) -> bool:
        acc = self.get_account(username)
        if acc:
            acc.unlock()
            return True
        return False

    # ── authentication ───────────────────────
    def attempt_login(self, username: str, password_try: str) -> SprayAttempt:
        attempt = SprayAttempt(username=username, password_try=password_try)
        acc = self.get_account(username)

        if acc is None:
            attempt.result = "FAILURE"          # unknown user → same response (no enumeration)
            return attempt

        if acc.is_locked():
            attempt.result = "LOCKED"
            return attempt

        if acc.verify_password(password_try):
            acc.reset_failed_attempts()
            attempt.result = "SUCCESS"
        else:
            acc.record_failed_attempt()
            attempt.result = "LOCKED" if acc.is_locked() else "FAILURE"

        return attempt

    def stats(self) -> dict:
        accs = self.all_accounts()
        return {
            "total": len(accs),
            "locked": sum(1 for a in accs if a.is_locked()),
            "active": sum(1 for a in accs if not a.is_locked()),
        }


# ─────────────────────────────────────────────
#  SPRAY SIMULATOR
# ─────────────────────────────────────────────
class SpraySimulator:
    """
    Performs a classic password-spray attack:
    tries one password at a time across ALL accounts
    to avoid per-account lockout thresholds.
    """

    DEFAULT_PASSWORDS: list[str] = [
        "Password1", "Welcome1", "Summer2024", "Company123",
        "Passw0rd", "Qwerty123", "January2024", "Admin1234",
        "LetMeIn1", "Monday123",
    ]

    def __init__(
        self,
        auth_system: AuthenticationSystem,
        passwords: Optional[list[str]] = None,
        delay_ms: int = 0,
    ):
        self.auth_system = auth_system
        self.passwords: list[str] = passwords or self.DEFAULT_PASSWORDS
        self.delay_ms: int = max(0, delay_ms)
        self._attempts: list[SprayAttempt] = []

    def run(
        self,
        usernames: Optional[list[str]] = None,
        password_subset: Optional[list[str]] = None,
        verbose: bool = True,
    ) -> list[SprayAttempt]:
        """
        Spray each password across every target username.
        Returns the list of SprayAttempt records.
        """
        targets   = usernames       or [a.username for a in self.auth_system.all_accounts()]
        pwd_list  = password_subset or self.passwords
        self._attempts.clear()

        if verbose:
            print(c("\n[*] Starting spray campaign…", Color.YELLOW, Color.BOLD))
            print(c(f"    Targets   : {len(targets)} accounts", Color.DIM))
            print(c(f"    Passwords : {len(pwd_list)}", Color.DIM))
            print(c(f"    Total tries: {len(targets) * len(pwd_list)}", Color.DIM))
            print()

        for pwd in pwd_list:
            if verbose:
                print(c(f"  ▸ Trying password: {pwd!r}", Color.MAGENTA))
            random.shuffle(targets)          # randomise order per round
            for uname in targets:
                attempt = self.auth_system.attempt_login(uname, pwd)
                self._attempts.append(attempt)
                if verbose:
                    print(attempt.to_log_line())
                if self.delay_ms > 0:
                    time.sleep(self.delay_ms / 1000)
            if verbose:
                print()

        return self._attempts

    def successful_logins(self) -> list[SprayAttempt]:
        return [a for a in self._attempts if a.result == "SUCCESS"]

    def all_attempts(self) -> list[SprayAttempt]:
        return list(self._attempts)


# ─────────────────────────────────────────────
#  SECURITY MANAGER  (detection + logging)
# ─────────────────────────────────────────────
class SecurityManager:
    """
    Analyses SprayAttempt logs for spray indicators and raises alerts.

    Detection heuristics used:
      1. High failure rate across DISTINCT accounts in a short window
         → horizontal spray pattern
      2. Repeated failures from the same source IP
      3. Multiple accounts locked in the same session
      4. Any successful login after a string of failures
    """

    FAILURE_THRESHOLD: int   = 5    # ≥ N failures across distinct accounts → alert
    LOCK_THRESHOLD:    int   = 2    # ≥ N accounts locked                   → alert
    SUCCESS_AFTER_N:   int   = 3    # success after ≥ N prior failures      → alert

    def __init__(self):
        self._log: list[SprayAttempt]  = []
        self._alerts: list[str]        = []

    # ── ingestion ────────────────────────────
    def ingest(self, attempts: list[SprayAttempt]) -> None:
        self._log.extend(attempts)

    def clear(self) -> None:
        self._log.clear()
        self._alerts.clear()

    # ── analysis ─────────────────────────────
    def analyse(self) -> list[str]:
        """Run all detection heuristics and return list of alert strings."""
        self._alerts.clear()
        self._detect_horizontal_spray()
        self._detect_ip_volume()
        self._detect_mass_lockout()
        self._detect_success_after_failures()
        return list(self._alerts)

    def _detect_horizontal_spray(self) -> None:
        failures = [a for a in self._log if a.result in ("FAILURE", "LOCKED")]
        distinct_targets = {a.username for a in failures}
        if len(distinct_targets) >= self.FAILURE_THRESHOLD:
            self._alerts.append(
                f"🚨 SPRAY PATTERN DETECTED — {len(failures)} failures across "
                f"{len(distinct_targets)} distinct accounts. "
                f"Classic horizontal password-spray signature."
            )

    def _detect_ip_volume(self) -> None:
        ip_counts: dict[str, int] = {}
        for a in self._log:
            ip_counts[a.source_ip] = ip_counts.get(a.source_ip, 0) + 1
        for ip, count in ip_counts.items():
            if count >= self.FAILURE_THRESHOLD:
                self._alerts.append(
                    f"⚠  HIGH-VOLUME SOURCE — IP {ip} made {count} authentication "
                    f"requests. Consider rate-limiting or blocking."
                )

    def _detect_mass_lockout(self) -> None:
        locked = [a for a in self._log if a.result == "LOCKED"]
        distinct = {a.username for a in locked}
        if len(distinct) >= self.LOCK_THRESHOLD:
            self._alerts.append(
                f"🔒 MASS LOCKOUT EVENT — {len(distinct)} accounts triggered "
                f"lockout. Possible DoS side-effect of spray attack."
            )

    def _detect_success_after_failures(self) -> None:
        failures_seen = 0
        for a in self._log:
            if a.result in ("FAILURE", "LOCKED"):
                failures_seen += 1
            elif a.result == "SUCCESS" and failures_seen >= self.SUCCESS_AFTER_N:
                self._alerts.append(
                    f"🔑 CREDENTIAL COMPROMISE — Successful login for "
                    f"'{a.username}' after {failures_seen} prior failures. "
                    f"Attacker may have found valid credentials."
                )

    # ── reporting ────────────────────────────
    def print_report(self, auth_system: AuthenticationSystem) -> None:
        width = 70
        line  = c("─" * width, Color.DIM)

        print(c("\n" + "═" * width, Color.CYAN))
        print(c("  SECURITY MANAGER — POST-SPRAY REPORT", Color.CYAN, Color.BOLD))
        print(c("═" * width, Color.CYAN))

        # ── summary stats ──
        total    = len(self._log)
        success  = sum(1 for a in self._log if a.result == "SUCCESS")
        failure  = sum(1 for a in self._log if a.result == "FAILURE")
        locked   = sum(1 for a in self._log if a.result == "LOCKED")

        print(c("\n  📊 ATTEMPT SUMMARY", Color.BOLD))
        print(line)
        print(f"  Total attempts  : {c(total, Color.WHITE, Color.BOLD)}")
        print(f"  Successes       : {c(success, Color.GREEN, Color.BOLD)}")
        print(f"  Failures        : {c(failure, Color.RED)}")
        print(f"  Hit locked acct : {c(locked, Color.YELLOW)}")

        # ── account state ──
        stats = auth_system.stats()
        print(c("\n  👤 ACCOUNT STATE", Color.BOLD))
        print(line)
        print(f"  Total accounts  : {stats['total']}")
        print(f"  Active accounts : {c(stats['active'], Color.GREEN)}")
        print(f"  Locked accounts : {c(stats['locked'], Color.RED)}")

        for acc in auth_system.all_accounts():
            lock_tag = c(" [LOCKED]", Color.RED, Color.BOLD) if acc.is_locked() else ""
            print(f"    • {c(acc.username, Color.CYAN)}{lock_tag} "
                  f"— {acc.failed_attempts} failed attempt(s)")

        # ── successful logins ──
        wins = [a for a in self._log if a.result == "SUCCESS"]
        if wins:
            print(c("\n  🔑 COMPROMISED CREDENTIALS", Color.GREEN, Color.BOLD))
            print(line)
            for w in wins:
                print(f"    • {c(w.username, Color.CYAN)} → password: "
                      f"{c(repr(w.password_try), Color.GREEN)}")
        else:
            print(c("\n  ✓ No credentials compromised in this run.", Color.GREEN))

        # ── alerts ──
        alerts = self.analyse()
        print(c("\n  🚨 DETECTION ALERTS", Color.BOLD))
        print(line)
        if alerts:
            for alert in alerts:
                print(f"  {c(alert, Color.RED)}")
        else:
            print(c("  No alerts triggered.", Color.GREEN))

        # ── defence recommendations ──
        print(c("\n  🛡  DEFENCE RECOMMENDATIONS", Color.BOLD))
        print(line)
        recs = [
            "Enforce MFA (Multi-Factor Authentication) on all accounts.",
            "Deploy a SIEM to correlate cross-account failure bursts.",
            "Implement adaptive rate-limiting and IP reputation scoring.",
            "Require strong, unique passwords and block common ones.",
            "Alert on >= 5 failures across >= 3 accounts within 60 seconds.",
            "Unlock locked accounts only through out-of-band verification.",
            "Regularly audit authentication logs for spray signatures.",
        ]
        for rec in recs:
            print(f"  {c('▸', Color.CYAN)} {rec}")

        print(c("\n" + "═" * width + "\n", Color.CYAN))


# ─────────────────────────────────────────────
#  CONSOLE UI
# ─────────────────────────────────────────────
class ConsoleUI:
    """Drives the interactive console application."""

    BANNER = r"""
  ██████╗ ███████╗██████╗ ██████╗  █████╗ ██╗   ██╗
  ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝
  ██████╔╝███████╗██████╔╝██████╔╝███████║ ╚████╔╝ 
  ██╔═══╝ ╚════██║██╔═══╝ ██╔══██╗██╔══██║  ╚██╔╝  
  ██║     ███████║██║     ██║  ██║██║  ██║   ██║   
  ╚═╝     ╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
   SPRAYING SIMULATOR  •  Educational Tool Only
    """

    def __init__(self):
        self.auth   = AuthenticationSystem()
        self.sec    = SecurityManager()
        self.sim: Optional[SpraySimulator] = None
        self._running = True

    # ── helpers ──────────────────────────────
    @staticmethod
    def _prompt(msg: str, default: str = "") -> str:
        val = input(c(f"  {msg}", Color.CYAN)).strip()
        return val if val else default

    @staticmethod
    def _divider(char: str = "─", width: int = 60) -> None:
        print(c(char * width, Color.DIM))

    # ── seed data ────────────────────────────
    def _load_demo_accounts(self) -> None:
        demo = [
            ("alice",   "Summer2024",  "user"),
            ("bob",     "Str0ng#Pass!", "user"),
            ("carol",   "Welcome1",    "user"),
            ("dave",    "Password1",   "user"),
            ("eve",     "Qwerty123",   "user"),
            ("frank",   "Secure@99",   "admin"),
            ("grace",   "Company123",  "user"),
            ("heidi",   "R@nd0mP@ss",  "user"),
        ]
        for uname, pwd, role in demo:
            try:
                self.auth.register(UserAccount(uname, pwd, role))
            except ValueError:
                pass
        print(c(f"  ✓ {len(demo)} demo accounts loaded.", Color.GREEN))

    # ── menu actions ─────────────────────────
    def _menu_add_account(self) -> None:
        print(c("\n  ── ADD USER ACCOUNT ──", Color.BOLD))
        username = self._prompt("Username : ")
        password = self._prompt("Password : ")
        role     = self._prompt("Role [user/admin] : ", "user")
        if role not in ("user", "admin"):
            print(c("  Invalid role, defaulting to 'user'.", Color.YELLOW))
            role = "user"
        try:
            self.auth.register(UserAccount(username, password, role))
            print(c(f"  ✓ Account '{username}' registered.", Color.GREEN))
        except ValueError as exc:
            print(c(f"  ✗ Error: {exc}", Color.RED))

    def _menu_list_accounts(self) -> None:
        accounts = self.auth.all_accounts()
        if not accounts:
            print(c("  No accounts registered yet.", Color.YELLOW))
            return
        print(c(f"\n  ── REGISTERED ACCOUNTS ({len(accounts)}) ──", Color.BOLD))
        self._divider()
        for acc in accounts:
            lock = c(" [LOCKED]", Color.RED, Color.BOLD) if acc.is_locked() else ""
            print(f"  {c(acc.username, Color.CYAN):<22} role={acc.role:<7} "
                  f"failed={acc.failed_attempts}{lock}")
        self._divider()

    def _menu_configure_spray(self) -> None:
        print(c("\n  ── CONFIGURE SPRAY CAMPAIGN ──", Color.BOLD))
        print(c("  Default password list:", Color.DIM))
        for i, p in enumerate(SpraySimulator.DEFAULT_PASSWORDS, 1):
            print(c(f"    {i:2}. {p}", Color.DIM))
        choice = self._prompt("\n  Use default list? [Y/n]: ", "y").lower()
        if choice == "n":
            raw = self._prompt("  Enter passwords (comma-separated): ")
            passwords = [p.strip() for p in raw.split(",") if p.strip()]
            if not passwords:
                print(c("  No valid passwords entered; using defaults.", Color.YELLOW))
                passwords = None
        else:
            passwords = None

        delay_str = self._prompt("  Delay between attempts (ms) [0]: ", "0")
        try:
            delay = int(delay_str)
        except ValueError:
            delay = 0

        self.sim = SpraySimulator(self.auth, passwords=passwords, delay_ms=delay)
        print(c("  ✓ Spray simulator configured.", Color.GREEN))

    def _menu_run_spray(self) -> None:
        if not self.auth.all_accounts():
            print(c("  ✗ No accounts to spray. Add accounts first.", Color.RED))
            return
        if self.sim is None:
            print(c("  ℹ Spray not configured; using defaults.", Color.YELLOW))
            self.sim = SpraySimulator(self.auth)

        print(c("\n  ── RUNNING SPRAY CAMPAIGN ──", Color.BOLD))
        print(c("  ⚠  This is a simulated attack for educational purposes only.", Color.YELLOW))
        confirm = self._prompt("  Proceed? [y/N]: ", "n").lower()
        if confirm != "y":
            print(c("  Campaign aborted.", Color.DIM))
            return

        attempts = self.sim.run(verbose=True)
        self.sec.ingest(attempts)
        print(c(f"\n  ✓ Campaign complete — {len(attempts)} attempts logged.", Color.GREEN))
        print(c("  Run 'View Security Report' to see detection results.", Color.DIM))

    def _menu_view_report(self) -> None:
        self.sec.print_report(self.auth)

    def _menu_unlock_account(self) -> None:
        self._menu_list_accounts()
        username = self._prompt("  Username to unlock: ")
        if self.auth.unlock_account(username):
            print(c(f"  ✓ Account '{username}' unlocked.", Color.GREEN))
        else:
            print(c(f"  ✗ Account '{username}' not found.", Color.RED))

    def _menu_manual_login(self) -> None:
        print(c("\n  ── MANUAL LOGIN TEST ──", Color.BOLD))
        username = self._prompt("  Username : ")
        password = self._prompt("  Password : ")
        attempt  = self.auth.attempt_login(username, password)
        self.sec.ingest([attempt])
        print(attempt.to_log_line())

    def _menu_reset_simulation(self) -> None:
        confirm = self._prompt("  Reset ALL accounts and logs? [y/N]: ", "n").lower()
        if confirm == "y":
            self.auth   = AuthenticationSystem()
            self.sec    = SecurityManager()
            self.sim    = None
            print(c("  ✓ Simulation reset.", Color.GREEN))

    # ── main loop ────────────────────────────
    def run(self) -> None:
        print(c(self.BANNER, Color.CYAN, Color.BOLD))
        print(c("  ⚠  FOR EDUCATIONAL AND DEFENSIVE USE ONLY ⚠", Color.RED, Color.BOLD))
        print(c("  Unauthorized use against real systems is illegal.\n", Color.DIM))

        # offer to pre-load demo data
        choice = self._prompt("  Load demo accounts to get started? [Y/n]: ", "y").lower()
        if choice != "n":
            self._load_demo_accounts()

        menu = [
            ("Add user account",          self._menu_add_account),
            ("List accounts",             self._menu_list_accounts),
            ("Configure spray campaign",  self._menu_configure_spray),
            ("Run spray campaign",        self._menu_run_spray),
            ("Manual login test",         self._menu_manual_login),
            ("Unlock account",            self._menu_unlock_account),
            ("View security report",      self._menu_view_report),
            ("Reset simulation",          self._menu_reset_simulation),
            ("Exit",                      None),
        ]

        while self._running:
            print(c("\n  ── MAIN MENU ──", Color.BOLD))
            for idx, (label, _) in enumerate(menu, 1):
                icon = "⏻" if label == "Exit" else "▸"
                print(f"  {c(icon, Color.CYAN)} {idx}. {label}")
            raw = self._prompt("\n  Select option: ")
            try:
                choice = int(raw)
                if not (1 <= choice <= len(menu)):
                    raise ValueError
            except ValueError:
                print(c("  Invalid selection.", Color.RED))
                continue

            label, handler = menu[choice - 1]
            if handler is None:
                print(c("\n  Goodbye — stay secure! 🔐\n", Color.GREEN, Color.BOLD))
                break
            handler()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    ConsoleUI().run()