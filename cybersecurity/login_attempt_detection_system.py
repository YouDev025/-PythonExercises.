"""
login_attempt_detection_system.py
==================================
Monitors and detects suspicious login activity.
Built with Python OOP: encapsulation, abstraction, and modularity.
"""

import uuid
import random
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


def _now() -> datetime:
    return datetime.now()

def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def _short(uid: str) -> str:
    return uid[:8].upper()


# ─────────────────────────────────────────────────────────────
# LoginAttempt Class
# ─────────────────────────────────────────────────────────────

class LoginAttempt:
    """
    Immutable record of a single login attempt.
    All data is private; accessed through read-only properties.
    """

    def __init__(
        self,
        username: str,
        source_ip: str,
        success: bool,
        timestamp: Optional[datetime] = None,
        user_agent: str = "unknown",
    ):
        if not username or not isinstance(username, str):
            raise ValueError("username must be a non-empty string.")
        if not source_ip or not isinstance(source_ip, str):
            raise ValueError("source_ip must be a non-empty string.")
        if not isinstance(success, bool):
            raise TypeError("success must be a bool.")

        self.__attempt_id  = str(uuid.uuid4())
        self.__username    = username.strip().lower()
        self.__source_ip   = source_ip.strip()
        self.__success     = success
        self.__timestamp   = timestamp if timestamp else _now()
        self.__user_agent  = user_agent.strip()

    @property
    def attempt_id(self)  -> str:       return self.__attempt_id
    @property
    def username(self)    -> str:       return self.__username
    @property
    def source_ip(self)   -> str:       return self.__source_ip
    @property
    def success(self)     -> bool:      return self.__success
    @property
    def timestamp(self)   -> datetime:  return self.__timestamp
    @property
    def user_agent(self)  -> str:       return self.__user_agent

    @property
    def status_label(self) -> str:
        return f"{Color.GREEN}SUCCESS{Color.RESET}" if self.__success \
               else f"{Color.RED}FAILED {Color.RESET}"

    def __repr__(self) -> str:
        status = "OK" if self.__success else "FAIL"
        return (f"LoginAttempt({_short(self.__attempt_id)} | "
                f"{self.__username} | {self.__source_ip} | {status})")


# ─────────────────────────────────────────────────────────────
# SecurityAlert Class
# ─────────────────────────────────────────────────────────────

class SecurityAlert:
    """Represents a security alert triggered by suspicious login behaviour."""

    TYPES = {
        "BRUTE_FORCE_USER":    ("HIGH",     "Brute-force attack against user account"),
        "BRUTE_FORCE_IP":      ("HIGH",     "Brute-force attack from single IP"),
        "ACCOUNT_LOCKED":      ("CRITICAL", "Account locked after threshold exceeded"),
        "DISTRIBUTED_ATTACK":  ("MEDIUM",   "Distributed login attack across multiple IPs"),
        "CREDENTIAL_STUFFING": ("HIGH",     "Credential stuffing — many users from one IP"),
        "IMPOSSIBLE_TRAVEL":   ("CRITICAL", "Impossible travel — login from two distant IPs"),
        "SUCCESS_AFTER_FAILS": ("MEDIUM",   "Successful login after repeated failures"),
    }

    _SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}

    def __init__(self, alert_type: str, username: str, source_ip: str, detail: str):
        if alert_type not in self.TYPES:
            raise ValueError(f"Unknown alert type: {alert_type}")
        self.__alert_id   = str(uuid.uuid4())
        self.__alert_type = alert_type
        self.__username   = username
        self.__source_ip  = source_ip
        self.__detail     = detail
        self.__severity, self.__description = self.TYPES[alert_type]
        self.__timestamp  = _now()
        self.__acknowledged = False

    @property
    def alert_id(self)    -> str:  return self.__alert_id
    @property
    def alert_type(self)  -> str:  return self.__alert_type
    @property
    def username(self)    -> str:  return self.__username
    @property
    def source_ip(self)   -> str:  return self.__source_ip
    @property
    def severity(self)    -> str:  return self.__severity
    @property
    def description(self) -> str:  return self.__description
    @property
    def detail(self)      -> str:  return self.__detail
    @property
    def timestamp(self)   -> datetime: return self.__timestamp
    @property
    def acknowledged(self)-> bool: return self.__acknowledged

    @property
    def severity_rank(self) -> int:
        return self._SEVERITY_ORDER.get(self.__severity, 0)

    def acknowledge(self) -> None:
        self.__acknowledged = True

    def __repr__(self) -> str:
        return (f"SecurityAlert({_short(self.__alert_id)} | "
                f"{self.__alert_type} | {self.__severity})")


# ─────────────────────────────────────────────────────────────
# LoginAnalyzer Class
# ─────────────────────────────────────────────────────────────

class LoginAnalyzer:
    """
    Analyses a list of LoginAttempt objects to detect suspicious patterns.
    Stateless — receives attempts and returns alerts.
    """

    FAIL_THRESHOLD_USER    = 5
    FAIL_THRESHOLD_IP      = 10
    ANALYSIS_WINDOW_MINS   = 15
    STUFFING_THRESHOLD     = 4
    DISTRIBUTED_IPS        = 4
    SUCCESS_AFTER_N_FAILS  = 3

    @classmethod
    def analyze(
        cls,
        attempts: list,
        locked_accounts: set,
    ) -> list:
        if not attempts:
            return []

        from collections import defaultdict
        cutoff = _now() - timedelta(minutes=cls.ANALYSIS_WINDOW_MINS)
        recent = [a for a in attempts if a.timestamp >= cutoff]
        alerts = []
        seen_keys: set = set()

        def _add(atype, user, ip, detail):
            key = (atype, user, ip)
            if key not in seen_keys:
                seen_keys.add(key)
                alerts.append(SecurityAlert(atype, user, ip, detail))

        fails_by_user = defaultdict(list)
        fails_by_ip   = defaultdict(list)

        for a in recent:
            if not a.success:
                fails_by_user[a.username].append(a)
                fails_by_ip[a.source_ip].append(a)

        # R1: Brute-force per user
        for user, fa in fails_by_user.items():
            if len(fa) >= cls.FAIL_THRESHOLD_USER:
                _add("BRUTE_FORCE_USER", user, fa[-1].source_ip,
                     f"{len(fa)} failed attempts for '{user}' in {cls.ANALYSIS_WINDOW_MINS} min.")

        # R2: Brute-force per IP
        for ip, fa in fails_by_ip.items():
            if len(fa) >= cls.FAIL_THRESHOLD_IP:
                users = {a.username for a in fa}
                _add("BRUTE_FORCE_IP", fa[0].username, ip,
                     f"{len(fa)} failed attempts from {ip} targeting {len(users)} account(s).")

        # R3: Credential stuffing
        for ip, fa in fails_by_ip.items():
            distinct_users = {a.username for a in fa}
            if len(distinct_users) >= cls.STUFFING_THRESHOLD:
                _add("CREDENTIAL_STUFFING", "multiple", ip,
                     f"IP {ip} hit {len(distinct_users)} distinct accounts with failures.")

        # R4: Distributed attack
        for user, fa in fails_by_user.items():
            distinct_ips = {a.source_ip for a in fa}
            if len(distinct_ips) >= cls.DISTRIBUTED_IPS:
                _add("DISTRIBUTED_ATTACK", user, "multiple",
                     f"User '{user}' attacked from {len(distinct_ips)} distinct IPs.")

        # R5: Account locked
        for user in locked_accounts:
            _add("ACCOUNT_LOCKED", user, "N/A",
                 f"Account '{user}' has been locked due to repeated failures.")

        # R6: Success after repeated failures
        users_seen = {a.username for a in recent}
        for user in users_seen:
            user_attempts = sorted(
                [a for a in recent if a.username == user],
                key=lambda x: x.timestamp,
            )
            fail_streak = 0
            for a in user_attempts:
                if not a.success:
                    fail_streak += 1
                else:
                    if fail_streak >= cls.SUCCESS_AFTER_N_FAILS:
                        _add("SUCCESS_AFTER_FAILS", user, a.source_ip,
                             f"Login succeeded for '{user}' after {fail_streak} consecutive failures.")
                    fail_streak = 0

        return sorted(alerts, key=lambda x: x.severity_rank, reverse=True)


# ─────────────────────────────────────────────────────────────
# LoginSecurityManager Class
# ─────────────────────────────────────────────────────────────

class LoginSecurityManager:
    """
    Central manager: records attempts, manages locks, triggers analysis, stores alerts.
    """

    LOCK_THRESHOLD = 6
    MAX_HISTORY    = 1000

    def __init__(self):
        self.__attempts:        list           = []
        self.__alerts:          dict           = {}
        self.__locked_accounts: set            = set()
        self.__fail_streaks:    dict           = {}

    def record_attempt(self, attempt: LoginAttempt) -> list:
        if not isinstance(attempt, LoginAttempt):
            raise TypeError("Must pass a LoginAttempt instance.")

        if len(self.__attempts) >= self.MAX_HISTORY:
            self.__attempts = self.__attempts[-(self.MAX_HISTORY // 2):]

        self.__attempts.append(attempt)
        self.__update_streak(attempt)
        self.__check_auto_lock(attempt.username)

        new_alerts = LoginAnalyzer.analyze(self.__attempts, self.__locked_accounts)
        added = []
        existing_keys = {
            f"{a.alert_type}:{a.username}:{a.source_ip}"
            for a in self.__alerts.values()
        }
        for alert in new_alerts:
            key = f"{alert.alert_type}:{alert.username}:{alert.source_ip}"
            if key not in existing_keys:
                self.__alerts[alert.alert_id] = alert
                added.append(alert)
                existing_keys.add(key)

        return added

    def unlock_account(self, username: str) -> bool:
        uname = username.strip().lower()
        if uname in self.__locked_accounts:
            self.__locked_accounts.discard(uname)
            self.__fail_streaks[uname] = 0
            # Remove ACCOUNT_LOCKED alerts for this user
            to_remove = [
                aid for aid, a in self.__alerts.items()
                if a.alert_type == "ACCOUNT_LOCKED" and a.username == uname
            ]
            for aid in to_remove:
                del self.__alerts[aid]
            return True
        return False

    def acknowledge_alert(self, alert_id_prefix: str) -> Optional[SecurityAlert]:
        alert = self._find_alert(alert_id_prefix)
        if alert:
            alert.acknowledge()
        return alert

    def acknowledge_all(self) -> int:
        count = 0
        for a in self.__alerts.values():
            if not a.acknowledged:
                a.acknowledge()
                count += 1
        return count

    def all_attempts(self)    -> list: return list(self.__attempts)
    def all_alerts(self)      -> list: return list(self.__alerts.values())
    def locked_accounts(self) -> set:  return set(self.__locked_accounts)

    def is_locked(self, username: str) -> bool:
        return username.strip().lower() in self.__locked_accounts

    def active_alerts(self) -> list:
        return sorted(
            [a for a in self.__alerts.values() if not a.acknowledged],
            key=lambda x: x.severity_rank, reverse=True,
        )

    def attempts_for_user(self, username: str) -> list:
        return [a for a in self.__attempts if a.username == username.strip().lower()]

    def attempts_for_ip(self, ip: str) -> list:
        return [a for a in self.__attempts if a.source_ip == ip.strip()]

    def stats(self) -> dict:
        total     = len(self.__attempts)
        failed    = sum(1 for a in self.__attempts if not a.success)
        succeeded = total - failed
        return {
            "total":         total,
            "succeeded":     succeeded,
            "failed":        failed,
            "unique_users":  len({a.username for a in self.__attempts}),
            "unique_ips":    len({a.source_ip for a in self.__attempts}),
            "locked":        len(self.__locked_accounts),
            "total_alerts":  len(self.__alerts),
            "active_alerts": len(self.active_alerts()),
        }

    def _find_alert(self, prefix: str) -> Optional[SecurityAlert]:
        prefix = prefix.strip().lower()
        for aid, alert in self.__alerts.items():
            if aid.lower().startswith(prefix):
                return alert
        return None

    def __update_streak(self, attempt: LoginAttempt) -> None:
        user = attempt.username
        if attempt.success:
            self.__fail_streaks[user] = 0
        else:
            self.__fail_streaks[user] = self.__fail_streaks.get(user, 0) + 1

    def __check_auto_lock(self, username: str) -> None:
        if self.__fail_streaks.get(username, 0) >= self.LOCK_THRESHOLD:
            self.__locked_accounts.add(username)


# ─────────────────────────────────────────────────────────────
# Simulator
# ─────────────────────────────────────────────────────────────

class LoginSimulator:
    """Generates realistic synthetic login attempts."""

    _USERS = [
        "alice", "bob", "charlie", "diana", "eve",
        "frank", "grace", "hank", "iris", "john",
    ]
    _IPS_LEGIT = [
        "192.168.1.10", "192.168.1.25", "10.0.0.55",
        "10.10.1.100",  "172.16.0.42",
    ]
    _IPS_ATTACKER = [
        "185.220.101.47", "91.108.4.188", "45.142.212.99",
        "203.0.113.77",   "198.51.100.12",
    ]
    _AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0)",
        "curl/7.68.0",
        "python-requests/2.28.0",
        "Mozilla/5.0 (Linux; Android 11)",
        "PostmanRuntime/7.29.0",
    ]

    @classmethod
    def random_attempt(cls) -> LoginAttempt:
        user      = random.choice(cls._USERS)
        is_attack = random.random() < 0.35
        ip        = random.choice(cls._IPS_ATTACKER if is_attack else cls._IPS_LEGIT)
        success   = False if is_attack else random.random() > 0.30
        return LoginAttempt(user, ip, success, user_agent=random.choice(cls._AGENTS))

    @classmethod
    def brute_force_scenario(cls, username: str, attacker_ip: str, n: int = 8) -> list:
        attempts = []
        base = _now() - timedelta(minutes=10)
        for i in range(n):
            ts = base + timedelta(seconds=i * 5)
            attempts.append(LoginAttempt(username, attacker_ip, False,
                                         timestamp=ts, user_agent="python-requests/2.28.0"))
        attempts.append(LoginAttempt(username, attacker_ip, True,
                                     timestamp=base + timedelta(seconds=n * 5),
                                     user_agent="python-requests/2.28.0"))
        return attempts

    @classmethod
    def credential_stuffing_scenario(cls, attacker_ip: str) -> list:
        attempts = []
        base = _now() - timedelta(minutes=8)
        for i, user in enumerate(cls._USERS):
            ts = base + timedelta(seconds=i * 12)
            attempts.append(LoginAttempt(user, attacker_ip, False,
                                         timestamp=ts, user_agent="curl/7.68.0"))
        return attempts


# ─────────────────────────────────────────────────────────────
# Display Helpers
# ─────────────────────────────────────────────────────────────

_W = 72

def _sep(ch="─"):   print(f"  {ch * (_W - 2)}")
def _head(ch="="):  print(f"  {ch * (_W - 2)}")


def _sev_color(sev: str) -> str:
    return {
        "CRITICAL": Color.RED,
        "HIGH":     Color.ORANGE,
        "MEDIUM":   Color.YELLOW,
        "LOW":      Color.GREEN,
        "INFO":     Color.CYAN,
    }.get(sev, Color.RESET)


def print_banner():
    print(f"""
{Color.BLUE}  {'#' * (_W - 2)}{Color.RESET}
{Color.BOLD}{Color.BLUE}  {'LOGIN ATTEMPT DETECTION SYSTEM':^{_W-2}}{Color.RESET}
{Color.GREY}  {'Intrusion Monitor  v1.0':^{_W-2}}{Color.RESET}
{Color.BLUE}  {'#' * (_W - 2)}{Color.RESET}
""")


def print_menu():
    opts = [
        ("1", "Simulate random login attempt(s)"),
        ("2", "Simulate brute-force scenario"),
        ("3", "Simulate credential-stuffing scenario"),
        ("4", "Manually record a login attempt"),
        ("5", "View login history"),
        ("6", "View active security alerts"),
        ("7", "View all alerts (incl. acknowledged)"),
        ("8", "Acknowledge an alert"),
        ("9", "Acknowledge all alerts"),
        ("L", "View / unlock locked accounts"),
        ("U", "View attempts by username"),
        ("I", "View attempts by IP address"),
        ("S", "Statistics dashboard"),
        ("X", "Exit"),
    ]
    _head()
    print(f"  {Color.BOLD}  MAIN MENU{Color.RESET}")
    _sep()
    for key, label in opts:
        print(f"    {Color.CYAN}[{key}]{Color.RESET}  {label}")
    _head()


def print_attempt_table(attempts: list, title: str = "LOGIN HISTORY") -> None:
    if not attempts:
        print(f"\n  {Color.GREY}No attempts to display.{Color.RESET}\n")
        return
    _head()
    print(f"  {Color.BOLD}  {title}  ({len(attempts)} records){Color.RESET}")
    _sep()
    print(f"  {'Time':<20} {'Username':<14} {'Source IP':<18} {'Agent':<22} {'Result'}")
    _sep()
    for a in attempts[-40:]:
        agent_short = a.user_agent[:20]
        print(f"  {_fmt(a.timestamp):<20} {a.username:<14} {a.source_ip:<18} "
              f"{agent_short:<22} {a.status_label}")
    if len(attempts) > 40:
        print(f"\n  {Color.GREY}  ... showing last 40 of {len(attempts)}.{Color.RESET}")
    _head()


def print_alert_table(alerts: list, title: str = "ALERTS") -> None:
    if not alerts:
        print(f"\n  {Color.GREEN}No alerts to display.{Color.RESET}\n")
        return
    _head()
    print(f"  {Color.BOLD}  {title}  ({len(alerts)} total){Color.RESET}")
    _sep()
    print(f"  {'ID':<10} {'Time':<20} {'SEV':<10} {'Type':<26} {'User'}")
    _sep()
    for a in alerts:
        sc    = _sev_color(a.severity)
        ack   = f"{Color.GREY}[ACK]{Color.RESET} " if a.acknowledged else "      "
        sev_s = f"{sc}{a.severity:<9}{Color.RESET}"
        print(f"  {ack}{_short(a.alert_id):<10} {_fmt(a.timestamp):<20} "
              f"{sev_s} {a.alert_type:<26} {a.username}")
    _head()


def print_alert_detail(alert: SecurityAlert) -> None:
    sc = _sev_color(alert.severity)
    _head()
    print(f"  {Color.BOLD}  ALERT DETAIL{Color.RESET}")
    _sep()
    print(f"  Alert ID    : {Color.CYAN}{_short(alert.alert_id)}{Color.RESET}  ({alert.alert_id})")
    print(f"  Type        : {alert.alert_type}")
    print(f"  Severity    : {sc}{Color.BOLD}{alert.severity}{Color.RESET}")
    print(f"  Description : {alert.description}")
    print(f"  Username    : {Color.YELLOW}{alert.username}{Color.RESET}")
    print(f"  Source IP   : {Color.YELLOW}{alert.source_ip}{Color.RESET}")
    print(f"  Triggered   : {_fmt(alert.timestamp)}")
    print(f"  Detail      : {alert.detail}")
    ack_s = f"{Color.GREEN}Yes{Color.RESET}" if alert.acknowledged else f"{Color.RED}No{Color.RESET}"
    print(f"  Acknowledged: {ack_s}")
    _head()


def print_stats(stats: dict, locked: set) -> None:
    _head()
    print(f"  {Color.BOLD}  STATISTICS DASHBOARD{Color.RESET}")
    _sep()
    total  = stats["total"] or 1
    s_pct  = stats["succeeded"] / total * 100
    f_pct  = stats["failed"]    / total * 100

    def _bar(pct, width=28) -> str:
        filled = int(pct / 100 * width)
        return "█" * filled + "░" * (width - filled)

    print(f"  Total Attempts  : {Color.CYAN}{stats['total']}{Color.RESET}")
    print(f"  {Color.GREEN}Succeeded       : {stats['succeeded']}  {_bar(s_pct)}{Color.RESET}  {s_pct:.1f}%")
    print(f"  {Color.RED}Failed          : {stats['failed']}  {_bar(f_pct)}{Color.RESET}  {f_pct:.1f}%")
    _sep()
    print(f"  Unique Users    : {stats['unique_users']}")
    print(f"  Unique IPs      : {stats['unique_ips']}")
    print(f"  Locked Accounts : {Color.RED}{stats['locked']}{Color.RESET}")
    _sep()
    print(f"  {Color.BOLD}  Alerts{Color.RESET}")
    print(f"  Total Generated : {stats['total_alerts']}")
    print(f"  Active (unacked): {Color.RED}{stats['active_alerts']}{Color.RESET}")
    if locked:
        _sep()
        print(f"  {Color.BOLD}  Locked Accounts{Color.RESET}")
        for u in sorted(locked):
            print(f"    {Color.RED}[X]  {u}{Color.RESET}")
    _head()


# ─────────────────────────────────────────────────────────────
# CLI Helpers
# ─────────────────────────────────────────────────────────────

def _prompt(prompt: str) -> str:
    return input(f"\n  > {prompt} ").strip()


def _print_new_alerts(new_alerts: list) -> None:
    for alert in new_alerts:
        sc = _sev_color(alert.severity)
        print(f"  *** NEW ALERT  "
              f"{sc}[{alert.severity}]{Color.RESET}  "
              f"{alert.alert_type}  --  {alert.detail}")


def _ingest_and_report(manager: LoginSecurityManager, attempt: LoginAttempt) -> None:
    locked_before = manager.is_locked(attempt.username)
    new_alerts    = manager.record_attempt(attempt)
    status_str    = f"{Color.GREEN}SUCCESS{Color.RESET}" if attempt.success \
                    else f"{Color.RED}FAILED{Color.RESET}"
    locked_str    = ""
    if not locked_before and manager.is_locked(attempt.username):
        locked_str = f"  {Color.RED}[ACCOUNT LOCKED]{Color.RESET}"
    print(f"  {Color.GREY}[{_fmt(attempt.timestamp)}]{Color.RESET}  "
          f"{Color.YELLOW}{attempt.username}{Color.RESET}@{attempt.source_ip}  "
          f"->  {status_str}{locked_str}")
    _print_new_alerts(new_alerts)


# ─────────────────────────────────────────────────────────────
# Menu Action Functions
# ─────────────────────────────────────────────────────────────

def cmd_simulate_random(manager: LoginSecurityManager) -> None:
    raw = _prompt("How many attempts to simulate? [1-50, default 5]:")
    try:
        n = int(raw) if raw else 5
        if not 1 <= n <= 50:
            raise ValueError
    except ValueError:
        print(f"  {Color.RED}[!] Enter a number 1-50.{Color.RESET}")
        return
    print(f"\n  -- Simulating {n} random attempt(s) --")
    for _ in range(n):
        _ingest_and_report(manager, LoginSimulator.random_attempt())
    print()


def cmd_brute_force(manager: LoginSecurityManager) -> None:
    print(f"\n  -- Brute-Force Scenario --")
    username = _prompt("Target username [default: alice]:") or "alice"
    attacker = _prompt("Attacker IP [default: 185.220.101.47]:") or "185.220.101.47"
    raw_n    = _prompt("Failed attempts before success [default: 8]:")
    try:
        n = int(raw_n) if raw_n else 8
        if not 1 <= n <= 30:
            raise ValueError
    except ValueError:
        print(f"  {Color.RED}[!] Enter a number 1-30.{Color.RESET}")
        return
    attempts = LoginSimulator.brute_force_scenario(username, attacker, n)
    print(f"\n  Replaying {len(attempts)} attempts...")
    for a in attempts:
        _ingest_and_report(manager, a)
    print()


def cmd_credential_stuffing(manager: LoginSecurityManager) -> None:
    print(f"\n  -- Credential Stuffing Scenario --")
    attacker = _prompt("Attacker IP [default: 203.0.113.77]:") or "203.0.113.77"
    attempts = LoginSimulator.credential_stuffing_scenario(attacker)
    print(f"\n  Replaying {len(attempts)} attempts across {len(LoginSimulator._USERS)} accounts...")
    for a in attempts:
        _ingest_and_report(manager, a)
    print()


def cmd_manual_attempt(manager: LoginSecurityManager) -> None:
    print(f"\n  -- Manual Login Attempt --")
    username = _prompt("Username:")
    if not username:
        print(f"  {Color.RED}[!] Username required.{Color.RESET}")
        return
    source_ip = _prompt("Source IP [default: 127.0.0.1]:") or "127.0.0.1"
    raw_s     = _prompt("Success? (y/n) [default: n]:").lower()
    success   = raw_s == "y"
    agent     = _prompt("User-agent [default: manual]:") or "manual"

    if manager.is_locked(username):
        print(f"  {Color.RED}[X] Account '{username}' is LOCKED. Attempt recorded but access denied.{Color.RESET}")
        success = False

    try:
        attempt = LoginAttempt(username, source_ip, success, user_agent=agent)
        _ingest_and_report(manager, attempt)
    except (ValueError, TypeError) as e:
        print(f"  {Color.RED}[!] Error: {e}{Color.RESET}")


def cmd_view_history(manager: LoginSecurityManager) -> None:
    print_attempt_table(manager.all_attempts())


def cmd_active_alerts(manager: LoginSecurityManager) -> None:
    alerts = manager.active_alerts()
    print_alert_table(alerts, "ACTIVE ALERTS (UNACKNOWLEDGED)")
    if alerts:
        detail = _prompt("Enter Alert ID for full detail (or ENTER to skip):")
        if detail:
            found = manager._find_alert(detail)
            if found:
                print_alert_detail(found)
            else:
                print(f"  {Color.RED}[!] Alert not found.{Color.RESET}")


def cmd_all_alerts(manager: LoginSecurityManager) -> None:
    print_alert_table(manager.all_alerts(), "ALL ALERTS")


def cmd_acknowledge(manager: LoginSecurityManager) -> None:
    active = manager.active_alerts()
    if not active:
        print(f"\n  {Color.GREEN}No unacknowledged alerts.{Color.RESET}")
        return
    print_alert_table(active, "UNACKNOWLEDGED ALERTS")
    aid = _prompt("Enter Alert ID prefix to acknowledge:")
    alert = manager.acknowledge_alert(aid)
    if alert:
        print(f"  {Color.GREEN}[OK] Alert {_short(alert.alert_id)} acknowledged.{Color.RESET}")
    else:
        print(f"  {Color.RED}[!] Alert not found.{Color.RESET}")


def cmd_acknowledge_all(manager: LoginSecurityManager) -> None:
    n = manager.acknowledge_all()
    print(f"\n  {Color.GREEN}[OK] {n} alert(s) acknowledged.{Color.RESET}")


def cmd_locked_accounts(manager: LoginSecurityManager) -> None:
    locked = manager.locked_accounts()
    print(f"\n  -- Locked Accounts --")
    if not locked:
        print(f"  {Color.GREEN}No accounts are currently locked.{Color.RESET}\n")
        return
    for u in sorted(locked):
        print(f"  {Color.RED}[LOCKED]  {u}{Color.RESET}")
    print()
    choice = _prompt("Enter username to UNLOCK (or ENTER to cancel):").lower()
    if not choice:
        return
    if manager.unlock_account(choice):
        print(f"  {Color.GREEN}[OK] Account '{choice}' unlocked.{Color.RESET}")
    else:
        print(f"  {Color.YELLOW}[!] '{choice}' is not locked or not found.{Color.RESET}")


def cmd_by_user(manager: LoginSecurityManager) -> None:
    username = _prompt("Enter username:")
    if not username:
        return
    attempts = manager.attempts_for_user(username)
    if not attempts:
        print(f"  {Color.GREY}No attempts found for '{username}'.{Color.RESET}")
    else:
        fails  = sum(1 for a in attempts if not a.success)
        oks    = len(attempts) - fails
        locked = f"  {Color.RED}[LOCKED]{Color.RESET}" if manager.is_locked(username) else ""
        print(f"\n  User: {Color.YELLOW}{username}{Color.RESET}{locked}  "
              f"| Total: {len(attempts)}  "
              f"| {Color.GREEN}OK: {oks}{Color.RESET}  "
              f"| {Color.RED}Fail: {fails}{Color.RESET}")
        print_attempt_table(attempts, f"ATTEMPTS FOR '{username.upper()}'")


def cmd_by_ip(manager: LoginSecurityManager) -> None:
    ip = _prompt("Enter source IP:")
    if not ip:
        return
    attempts = manager.attempts_for_ip(ip)
    if not attempts:
        print(f"  {Color.GREY}No attempts found from '{ip}'.{Color.RESET}")
    else:
        fails = sum(1 for a in attempts if not a.success)
        users = len({a.username for a in attempts})
        print(f"\n  IP: {Color.YELLOW}{ip}{Color.RESET}  "
              f"| Total: {len(attempts)}  "
              f"| {Color.RED}Fail: {fails}{Color.RESET}  "
              f"| Unique users: {users}")
        print_attempt_table(attempts, f"ATTEMPTS FROM {ip}")


def cmd_stats(manager: LoginSecurityManager) -> None:
    print_stats(manager.stats(), manager.locked_accounts())


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    print_banner()
    manager = LoginSecurityManager()

    VALID = {"1","2","3","4","5","6","7","8","9","L","U","I","S","X"}
    DISPATCH = {
        "1": lambda: cmd_simulate_random(manager),
        "2": lambda: cmd_brute_force(manager),
        "3": lambda: cmd_credential_stuffing(manager),
        "4": lambda: cmd_manual_attempt(manager),
        "5": lambda: cmd_view_history(manager),
        "6": lambda: cmd_active_alerts(manager),
        "7": lambda: cmd_all_alerts(manager),
        "8": lambda: cmd_acknowledge(manager),
        "9": lambda: cmd_acknowledge_all(manager),
        "L": lambda: cmd_locked_accounts(manager),
        "U": lambda: cmd_by_user(manager),
        "I": lambda: cmd_by_ip(manager),
        "S": lambda: cmd_stats(manager),
    }

    while True:
        s = manager.stats()
        print(f"\n  Attempts: {s['total']}  |  "
              f"{Color.RED}Active Alerts: {s['active_alerts']}{Color.RESET}  |  "
              f"{Color.RED}Locked: {s['locked']}{Color.RESET}  |  "
              f"{Color.GREEN}Succeeded: {s['succeeded']}{Color.RESET}  |  "
              f"{Color.RED}Failed: {s['failed']}{Color.RESET}")

        print_menu()
        choice = ""
        while choice not in VALID:
            choice = _prompt("Select option:").upper()
            if choice not in VALID:
                print(f"  {Color.RED}[!] Invalid. Options: {', '.join(sorted(VALID))}{Color.RESET}")

        if choice == "X":
            print(f"\n  {Color.CYAN}[*] Shutting down detection system. Stay secure.{Color.RESET}\n")
            break

        try:
            DISPATCH[choice]()
        except Exception as exc:
            print(f"\n  {Color.RED}[ERROR] {exc}{Color.RESET}")


if __name__ == "__main__":
    main()