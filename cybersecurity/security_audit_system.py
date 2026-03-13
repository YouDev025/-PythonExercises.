"""
Security Audit System
=====================
A modular OOP-based system that simulates a security audit process,
running checks across password policy, ports, file permissions, and
configuration — then generating actionable reports.
"""

import random
import os
import json
from datetime import datetime
from typing import Optional
from collections import defaultdict
import textwrap


# ═══════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════

SEVERITIES  = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
STATUSES    = ["PASS", "FAIL", "WARNING", "SKIPPED"]

SEV_ICON = {
    "INFO":     "ℹ️ ",
    "LOW":      "🔵",
    "MEDIUM":   "🟡",
    "HIGH":     "🔴",
    "CRITICAL": "💀",
}
STA_ICON = {
    "PASS":    "✅",
    "FAIL":    "❌",
    "WARNING": "⚠️ ",
    "SKIPPED": "⏭️ ",
}

LINE  = "─" * 68
DLINE = "═" * 68

# Simulated environment values (static seed for reproducibility demo)
_ENV = {
    "min_password_length":   8,          # compliant threshold: 12
    "password_complexity":   True,
    "password_expiry_days":  120,        # compliant threshold: 90
    "mfa_enabled":           False,
    "open_ports":            [22, 80, 443, 3306, 8080, 23, 6379],
    "dangerous_ports":       {23: "Telnet", 6379: "Redis (no auth)", 3306: "MySQL"},
    "world_writable_files":  ["/tmp/config.bak", "/var/log/app.log"],
    "suid_files":            ["/usr/bin/passwd", "/tmp/exploit_bin"],
    "ssh_root_login":        True,
    "ssh_password_auth":     True,
    "firewall_enabled":      False,
    "tls_version":           "TLS 1.1",  # compliant: TLS 1.2+
    "default_credentials":   True,
    "audit_logging":         False,
    "os_patches_pending":    7,
    "encryption_at_rest":    False,
    "session_timeout_mins":  60,         # compliant threshold: 15
}


# ═══════════════════════════════════════════════════════════
#  AuditCheck  (result record)
# ═══════════════════════════════════════════════════════════

class AuditCheck:
    """
    Immutable-ish result record for a single security check.
    Status and details are set once by the checker; thereafter read-only.
    """

    def __init__(
        self,
        check_id:    str,
        check_name:  str,
        description: str,
        severity:    str,
        category:    str,
    ):
        self._check_id    = check_id
        self._check_name  = check_name
        self._description = description
        self._severity    = self._validate_severity(severity)
        self._category    = category
        self._status:  Optional[str] = None
        self._details: str = ""
        self._remediation: str = ""
        self._executed_at: Optional[datetime] = None

    # ── Validators ────────────────────────────
    @staticmethod
    def _validate_severity(v: str) -> str:
        v = v.upper()
        if v not in SEVERITIES:
            raise ValueError(f"Invalid severity '{v}'. Choose: {SEVERITIES}")
        return v

    # ── Setters (called once by checker) ──────
    def _set_result(
        self,
        status: str,
        details: str = "",
        remediation: str = "",
    ) -> None:
        s = status.upper()
        if s not in STATUSES:
            raise ValueError(f"Invalid status '{s}'.")
        self._status       = s
        self._details      = details
        self._remediation  = remediation
        self._executed_at  = datetime.now()

    # ── Properties ────────────────────────────
    @property
    def check_id(self)     -> str:  return self._check_id
    @property
    def check_name(self)   -> str:  return self._check_name
    @property
    def description(self)  -> str:  return self._description
    @property
    def severity(self)     -> str:  return self._severity
    @property
    def category(self)     -> str:  return self._category
    @property
    def status(self)       -> Optional[str]: return self._status
    @property
    def details(self)      -> str:  return self._details
    @property
    def remediation(self)  -> str:  return self._remediation
    @property
    def executed_at(self)  -> Optional[datetime]: return self._executed_at
    @property
    def passed(self)       -> bool: return self._status == "PASS"
    @property
    def failed(self)       -> bool: return self._status == "FAIL"
    @property
    def warned(self)       -> bool: return self._status == "WARNING"
    @property
    def ran(self)          -> bool: return self._status is not None

    # ── Display ───────────────────────────────
    def display(self, compact: bool = False) -> None:
        sta_icon = STA_ICON.get(self._status or "SKIPPED", "?")
        sev_icon = SEV_ICON.get(self._severity, "?")

        if compact:
            status_str = (self._status or "NOT RUN").ljust(7)
            print(
                f"  {self._check_id:<8}  {sta_icon} {status_str}  "
                f"{sev_icon} {self._severity:<8}  {self._check_name}"
            )
            return

        ts = self._executed_at.strftime("%Y-%m-%d %H:%M:%S") if self._executed_at else "—"
        print(DLINE)
        print(f"  Check ID    : {self._check_id}")
        print(f"  Name        : {self._check_name}")
        print(f"  Category    : {self._category}")
        print(f"  Severity    : {sev_icon} {self._severity}")
        print(f"  Status      : {sta_icon} {self._status or 'NOT RUN'}")
        print(f"  Run at      : {ts}")
        # Word-wrap long text
        def _wrap(label: str, text: str) -> None:
            if not text:
                return
            wrapped = textwrap.fill(
                text, width=54,
                initial_indent="              ",
                subsequent_indent="              ",
            )
            print(f"  {label:<12}: {wrapped.strip()}")
        _wrap("Description",  self._description)
        _wrap("Details",      self._details)
        _wrap("Remediation",  self._remediation)
        print(DLINE)


# ═══════════════════════════════════════════════════════════
#  SecurityAudit  (check catalogue + execution)
# ═══════════════════════════════════════════════════════════

class SecurityAudit:
    """
    Owns the full catalogue of security checks and runs them
    against the simulated environment (_ENV).

    Each check_* method sets the result on an AuditCheck object
    using the protected _set_result() method.
    """

    # Category labels
    CAT_PASSWORD = "Password Policy"
    CAT_NETWORK  = "Network & Ports"
    CAT_FILES    = "File Permissions"
    CAT_CONFIG   = "Configuration"
    CAT_PATCH    = "Patching"
    CAT_CRYPTO   = "Cryptography"
    CAT_LOGGING  = "Logging & Audit"

    def __init__(self):
        self._checks: list[AuditCheck] = []
        self._build_catalogue()

    def _build_catalogue(self) -> None:
        """Register every check — order determines display order."""
        defs = [
            # (id,      name,                                    description,                                          severity,   category)
            ("PWD-001", "Minimum Password Length",               "Password must be at least 12 characters.",          "HIGH",     self.CAT_PASSWORD),
            ("PWD-002", "Password Complexity Requirements",      "Passwords must include upper, lower, digit, symbol.","MEDIUM",   self.CAT_PASSWORD),
            ("PWD-003", "Password Expiry Policy",                "Passwords should expire within 90 days.",           "MEDIUM",   self.CAT_PASSWORD),
            ("PWD-004", "Multi-Factor Authentication",           "MFA must be enabled for all privileged accounts.",  "CRITICAL", self.CAT_PASSWORD),
            ("PWD-005", "Default Credentials Check",             "Default usernames/passwords must be changed.",      "CRITICAL", self.CAT_PASSWORD),
            ("NET-001", "Dangerous Open Ports",                  "Insecure services (Telnet, Redis) should be closed.","HIGH",     self.CAT_NETWORK),
            ("NET-002", "Firewall Status",                       "Host-based firewall must be active.",                "HIGH",     self.CAT_NETWORK),
            ("NET-003", "SSH Root Login",                        "Direct root login over SSH must be disabled.",      "HIGH",     self.CAT_NETWORK),
            ("NET-004", "SSH Password Authentication",           "Key-based auth only; password auth must be off.",   "MEDIUM",   self.CAT_NETWORK),
            ("FIL-001", "World-Writable Files",                  "No world-writable files outside /tmp.",             "HIGH",     self.CAT_FILES),
            ("FIL-002", "Suspicious SUID Binaries",              "Only system binaries should have SUID bit set.",    "CRITICAL", self.CAT_FILES),
            ("CFG-001", "TLS Version",                           "Only TLS 1.2 or higher should be accepted.",        "HIGH",     self.CAT_CRYPTO),
            ("CFG-002", "Encryption at Rest",                    "Sensitive data stores must be encrypted at rest.",  "HIGH",     self.CAT_CRYPTO),
            ("CFG-003", "Session Timeout",                       "Idle sessions must time out within 15 minutes.",    "MEDIUM",   self.CAT_CONFIG),
            ("LOG-001", "Audit Logging Enabled",                 "System audit logging (auditd/syslog) must be on.",  "HIGH",     self.CAT_LOGGING),
            ("PAT-001", "Pending OS Patches",                    "All critical OS patches must be applied.",          "CRITICAL", self.CAT_PATCH),
        ]
        for check_id, name, desc, sev, cat in defs:
            self._checks.append(AuditCheck(check_id, name, desc, sev, cat))

    # ── Catalogue access ──────────────────────
    @property
    def checks(self) -> list[AuditCheck]:
        return list(self._checks)

    def get_check(self, check_id: str) -> Optional[AuditCheck]:
        for c in self._checks:
            if c.check_id == check_id.upper():
                return c
        return None

    # ── Individual check runners ──────────────
    def _run_pwd001(self, c: AuditCheck) -> None:
        length = _ENV["min_password_length"]
        if length >= 12:
            c._set_result("PASS", f"Min length is {length} characters.")
        else:
            c._set_result(
                "FAIL",
                f"Min length is only {length} characters (required: 12).",
                "Set PasswordMinimumLength=12 in your password policy.",
            )

    def _run_pwd002(self, c: AuditCheck) -> None:
        if _ENV["password_complexity"]:
            c._set_result("PASS", "Complexity rules are enforced.")
        else:
            c._set_result(
                "FAIL",
                "Password complexity is not enforced.",
                "Enable complexity rules requiring upper, lower, digit, and symbol.",
            )

    def _run_pwd003(self, c: AuditCheck) -> None:
        days = _ENV["password_expiry_days"]
        if days <= 90:
            c._set_result("PASS", f"Expiry set to {days} days.")
        elif days <= 180:
            c._set_result(
                "WARNING",
                f"Expiry is {days} days (recommended ≤ 90).",
                "Reduce PASS_MAX_DAYS to 90 in /etc/login.defs.",
            )
        else:
            c._set_result(
                "FAIL",
                f"Expiry is {days} days — far too long.",
                "Set PASS_MAX_DAYS=90 immediately.",
            )

    def _run_pwd004(self, c: AuditCheck) -> None:
        if _ENV["mfa_enabled"]:
            c._set_result("PASS", "MFA is active for privileged accounts.")
        else:
            c._set_result(
                "FAIL",
                "MFA is NOT enabled.",
                "Integrate TOTP/FIDO2 MFA for all admin accounts.",
            )

    def _run_pwd005(self, c: AuditCheck) -> None:
        if _ENV["default_credentials"]:
            c._set_result(
                "FAIL",
                "Default credentials detected on one or more services.",
                "Change all default passwords immediately; run 'passwd' for each service account.",
            )
        else:
            c._set_result("PASS", "No default credentials detected.")

    def _run_net001(self, c: AuditCheck) -> None:
        found = {p: svc for p, svc in _ENV["dangerous_ports"].items()
                 if p in _ENV["open_ports"]}
        if not found:
            c._set_result("PASS", "No dangerous ports are open.")
        else:
            detail = ", ".join(f"{p}/{svc}" for p, svc in found.items())
            c._set_result(
                "FAIL",
                f"Dangerous open ports: {detail}.",
                "Disable or firewall these services immediately.",
            )

    def _run_net002(self, c: AuditCheck) -> None:
        if _ENV["firewall_enabled"]:
            c._set_result("PASS", "Host firewall is active.")
        else:
            c._set_result(
                "FAIL",
                "No host-based firewall detected.",
                "Enable ufw/firewalld and restrict inbound traffic to required ports only.",
            )

    def _run_net003(self, c: AuditCheck) -> None:
        if _ENV["ssh_root_login"]:
            c._set_result(
                "FAIL",
                "PermitRootLogin is enabled in sshd_config.",
                "Set PermitRootLogin no in /etc/ssh/sshd_config and restart sshd.",
            )
        else:
            c._set_result("PASS", "Root SSH login is disabled.")

    def _run_net004(self, c: AuditCheck) -> None:
        if _ENV["ssh_password_auth"]:
            c._set_result(
                "WARNING",
                "SSH password authentication is still enabled.",
                "Set PasswordAuthentication no after deploying SSH keys for all users.",
            )
        else:
            c._set_result("PASS", "SSH password authentication is disabled.")

    def _run_fil001(self, c: AuditCheck) -> None:
        bad = [f for f in _ENV["world_writable_files"]
               if not f.startswith("/tmp")]
        if bad:
            c._set_result(
                "FAIL",
                f"World-writable files outside /tmp: {bad}",
                "Run 'chmod o-w <file>' on each listed path.",
            )
        elif _ENV["world_writable_files"]:
            c._set_result(
                "WARNING",
                f"World-writable files in /tmp: {_ENV['world_writable_files']}",
                "Review /tmp contents and apply sticky bit: chmod +t /tmp.",
            )
        else:
            c._set_result("PASS", "No unexpected world-writable files found.")

    def _run_fil002(self, c: AuditCheck) -> None:
        suspicious = [f for f in _ENV["suid_files"]
                      if not f.startswith("/usr") and not f.startswith("/bin")]
        if suspicious:
            c._set_result(
                "FAIL",
                f"Suspicious SUID binaries: {suspicious}",
                "Run 'chmod u-s <file>' on unexpected SUID binaries immediately.",
            )
        else:
            c._set_result("PASS", "All SUID binaries are in expected system paths.")

    def _run_cfg001(self, c: AuditCheck) -> None:
        tls = _ENV["tls_version"]
        if tls in ("TLS 1.2", "TLS 1.3"):
            c._set_result("PASS", f"Configured TLS version: {tls}.")
        else:
            c._set_result(
                "FAIL",
                f"Weak TLS version in use: {tls}.",
                "Disable TLS 1.0 and 1.1; configure SSLProtocol TLSv1.2+.",
            )

    def _run_cfg002(self, c: AuditCheck) -> None:
        if _ENV["encryption_at_rest"]:
            c._set_result("PASS", "Encryption at rest is enabled.")
        else:
            c._set_result(
                "FAIL",
                "Data stores are NOT encrypted at rest.",
                "Enable LUKS/dm-crypt for disk encryption or database-level TDE.",
            )

    def _run_cfg003(self, c: AuditCheck) -> None:
        timeout = _ENV["session_timeout_mins"]
        if timeout <= 15:
            c._set_result("PASS", f"Session timeout is {timeout} minutes.")
        elif timeout <= 30:
            c._set_result(
                "WARNING",
                f"Session timeout is {timeout} min (recommended ≤ 15).",
                "Reduce TMOUT environment variable or web session timeout.",
            )
        else:
            c._set_result(
                "FAIL",
                f"Session timeout is {timeout} minutes — too long.",
                "Set TMOUT=900 (15 min) in /etc/profile.d/timeout.sh.",
            )

    def _run_log001(self, c: AuditCheck) -> None:
        if _ENV["audit_logging"]:
            c._set_result("PASS", "Audit logging is active.")
        else:
            c._set_result(
                "FAIL",
                "Audit logging is disabled.",
                "Install and enable auditd; configure rules in /etc/audit/rules.d/.",
            )

    def _run_pat001(self, c: AuditCheck) -> None:
        pending = _ENV["os_patches_pending"]
        if pending == 0:
            c._set_result("PASS", "No outstanding OS patches.")
        elif pending <= 3:
            c._set_result(
                "WARNING",
                f"{pending} patch(es) pending — apply soon.",
                "Run 'apt upgrade' or 'yum update' at next maintenance window.",
            )
        else:
            c._set_result(
                "FAIL",
                f"{pending} OS patches are outstanding.",
                "Apply patches immediately: 'apt upgrade -y' or 'yum update -y'.",
            )

    # ── Dispatch map ──────────────────────────
    _RUNNERS = {
        "PWD-001": _run_pwd001, "PWD-002": _run_pwd002,
        "PWD-003": _run_pwd003, "PWD-004": _run_pwd004,
        "PWD-005": _run_pwd005,
        "NET-001": _run_net001, "NET-002": _run_net002,
        "NET-003": _run_net003, "NET-004": _run_net004,
        "FIL-001": _run_fil001, "FIL-002": _run_fil002,
        "CFG-001": _run_cfg001, "CFG-002": _run_cfg002,
        "CFG-003": _run_cfg003,
        "LOG-001": _run_log001,
        "PAT-001": _run_pat001,
    }

    # ── Public run interface ──────────────────
    def run_check(self, check_id: str) -> AuditCheck:
        """Run a single check by ID; return the updated AuditCheck."""
        c = self.get_check(check_id)
        if c is None:
            raise KeyError(f"Check '{check_id}' not found in catalogue.")
        runner = self._RUNNERS.get(check_id)
        if runner is None:
            c._set_result("SKIPPED", "No runner implemented for this check.")
        else:
            runner(self, c)
        return c

    def run_all(self, progress: bool = False) -> list[AuditCheck]:
        """Run every check and return the full list."""
        for c in self._checks:
            if progress:
                print(f"  ⏳  Running {c.check_id}: {c.check_name} …", end="\r")
            self.run_check(c.check_id)
        if progress:
            print(" " * 70, end="\r")     # clear progress line
        return list(self._checks)

    def run_category(self, category: str) -> list[AuditCheck]:
        """Run all checks in a given category."""
        subset = [c for c in self._checks if c.category == category]
        if not subset:
            raise ValueError(f"No checks found for category '{category}'.")
        for c in subset:
            self.run_check(c.check_id)
        return subset


# ═══════════════════════════════════════════════════════════
#  AuditManager
# ═══════════════════════════════════════════════════════════

class AuditManager:
    """
    Orchestrates SecurityAudit runs, stores results, and produces reports.
    """

    def __init__(self):
        self._audit      = SecurityAudit()
        self._scan_time: Optional[datetime] = None
        self._scan_count = 0

    # ── Scan control ──────────────────────────
    def run_full_scan(self, verbose: bool = True) -> None:
        print(f"\n  {DLINE}")
        print("  🔍  FULL SECURITY AUDIT SCAN STARTING …")
        print(f"  {DLINE}\n")
        self._audit.run_all(progress=True)
        self._scan_time  = datetime.now()
        self._scan_count += 1
        total = len(self._audit.checks)
        passed   = sum(1 for c in self._audit.checks if c.passed)
        failed   = sum(1 for c in self._audit.checks if c.failed)
        warnings = sum(1 for c in self._audit.checks if c.warned)
        print(f"  ✔  Scan complete — {total} checks: "
              f"{passed} passed, {failed} failed, {warnings} warnings.\n")

    def run_category_scan(self, category: str) -> None:
        try:
            results = self._audit.run_category(category)
            self._scan_time = datetime.now()
            print(f"\n  ✔  Category '{category}' — {len(results)} check(s) run.\n")
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")

    def run_single_check(self, check_id: str) -> None:
        try:
            c = self._audit.run_check(check_id)
            print()
            c.display()
        except KeyError as exc:
            print(f"\n  [!] {exc}\n")

    # ── Queries ───────────────────────────────
    @property
    def checks(self) -> list[AuditCheck]:
        return self._audit.checks

    def failed_checks(self) -> list[AuditCheck]:
        return [c for c in self._audit.checks if c.failed]

    def warned_checks(self) -> list[AuditCheck]:
        return [c for c in self._audit.checks if c.warned]

    def checks_by_severity(self, severity: str) -> list[AuditCheck]:
        s = severity.upper()
        if s not in SEVERITIES:
            raise ValueError(f"Unknown severity '{severity}'.")
        return [c for c in self._audit.checks if c.severity == s]

    def checks_by_category(self, category: str) -> list[AuditCheck]:
        return [c for c in self._audit.checks if c.category == category]

    def categories(self) -> list[str]:
        seen: list[str] = []
        for c in self._audit.checks:
            if c.category not in seen:
                seen.append(c.category)
        return seen

    # ── Risk score ────────────────────────────
    def _risk_score(self) -> tuple[int, str]:
        """Return (0-100 score, label). Higher = worse."""
        weights = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 2, "INFO": 0}
        max_score = sum(weights[c.severity] for c in self._audit.checks)
        actual    = sum(
            weights[c.severity]
            for c in self._audit.checks
            if c.ran and c.failed
        )
        warn_penalty = sum(
            weights[c.severity] // 2
            for c in self._audit.checks
            if c.ran and c.warned
        )
        score = min(100, int((actual + warn_penalty) / max(max_score, 1) * 100))
        label = (
            "CRITICAL RISK" if score >= 70 else
            "HIGH RISK"     if score >= 45 else
            "MEDIUM RISK"   if score >= 25 else
            "LOW RISK"      if score >= 10 else
            "SECURE"
        )
        return score, label

    # ── Display ───────────────────────────────
    def display_all_results(self) -> None:
        checks = self._audit.checks
        if not any(c.ran for c in checks):
            print("\n  [!] No checks have been run yet. Run a scan first.\n")
            return
        print(f"\n{LINE}")
        print(f"  {'ID':<8}  {'STATUS':<10}  {'SEVERITY':<10}  CHECK NAME")
        print(LINE)
        by_cat: dict[str, list[AuditCheck]] = defaultdict(list)
        for c in checks:
            by_cat[c.category].append(c)
        for cat, items in by_cat.items():
            print(f"\n  ── {cat} ──")
            for c in items:
                c.display(compact=True)
        print(f"\n{LINE}\n")

    def display_failed(self) -> None:
        failed = self.failed_checks()
        if not failed:
            print("\n  ✅  No failed checks.\n")
            return
        print(f"\n{DLINE}")
        print(f"  ❌  FAILED CHECKS  ({len(failed)})")
        print(DLINE)
        for c in sorted(failed, key=lambda x: SEVERITIES.index(x.severity), reverse=True):
            c.display()

    def generate_report(self) -> None:
        """Print a formatted executive summary report."""
        checks   = self._audit.checks
        ran      = [c for c in checks if c.ran]
        if not ran:
            print("\n  [!] No results to report. Run a scan first.\n")
            return

        passed   = [c for c in ran if c.passed]
        failed   = [c for c in ran if c.failed]
        warnings = [c for c in ran if c.warned]
        skipped  = [c for c in ran if c.status == "SKIPPED"]
        score, label = self._risk_score()
        ts = self._scan_time.strftime("%Y-%m-%d %H:%M:%S") if self._scan_time else "—"

        risk_icon = (
            "💀" if score >= 70 else
            "🔴" if score >= 45 else
            "🟡" if score >= 25 else
            "🔵" if score >= 10 else
            "✅"
        )

        print(f"\n{DLINE}")
        print("  SECURITY AUDIT REPORT")
        print(DLINE)
        print(f"  Scan timestamp  : {ts}")
        print(f"  Total checks    : {len(ran)}")
        print(f"  Passed          : ✅  {len(passed)}")
        print(f"  Failed          : ❌  {len(failed)}")
        print(f"  Warnings        : ⚠️   {len(warnings)}")
        print(f"  Skipped         : ⏭️   {len(skipped)}")
        print(f"\n  Risk Score      : {score}/100  {risk_icon} {label}")
        print(DLINE)

        # Category breakdown
        print("\n  RESULTS BY CATEGORY\n")
        for cat in self.categories():
            items   = self.checks_by_category(cat)
            ran_cat = [c for c in items if c.ran]
            p = sum(1 for c in ran_cat if c.passed)
            f = sum(1 for c in ran_cat if c.failed)
            w = sum(1 for c in ran_cat if c.warned)
            bar_p = "█" * p
            bar_f = "▓" * f
            bar_w = "░" * w
            print(f"  {cat:<22}  ✅{p} ❌{f} ⚠️{w}  [{bar_p}{bar_f}{bar_w}]")

        # Critical failures
        crit_fail = [c for c in failed if c.severity == "CRITICAL"]
        if crit_fail:
            print(f"\n{LINE}")
            print(f"  ⚠️  CRITICAL FAILURES REQUIRING IMMEDIATE ACTION ({len(crit_fail)})")
            print(LINE)
            for c in crit_fail:
                print(f"\n  {c.check_id}  {c.check_name}")
                print(f"  Details      : {c.details}")
                print(f"  Remediation  : {c.remediation}")

        # Top remediations
        high_and_above = [c for c in failed
                          if c.severity in ("HIGH", "CRITICAL")]
        if high_and_above:
            print(f"\n{LINE}")
            print("  TOP REMEDIATION ACTIONS")
            print(LINE)
            for i, c in enumerate(
                sorted(high_and_above,
                       key=lambda x: SEVERITIES.index(x.severity),
                       reverse=True),
                1,
            ):
                sev_icon = SEV_ICON[c.severity]
                print(f"\n  {i}. {sev_icon} [{c.severity}] {c.check_name}")
                print(f"     → {c.remediation}")

        print(f"\n{DLINE}\n")

    def export_json(self, filepath: str) -> None:
        """Export results to a JSON file."""
        ran = [c for c in self._audit.checks if c.ran]
        if not ran:
            raise ValueError("No results to export.")
        data = {
            "scan_time": self._scan_time.isoformat() if self._scan_time else None,
            "total":     len(ran),
            "checks": [
                {
                    "check_id":    c.check_id,
                    "check_name":  c.check_name,
                    "category":    c.category,
                    "severity":    c.severity,
                    "status":      c.status,
                    "details":     c.details,
                    "remediation": c.remediation,
                    "executed_at": c.executed_at.isoformat() if c.executed_at else None,
                }
                for c in ran
            ],
        }
        with open(filepath, "w") as fh:
            json.dump(data, fh, indent=2)


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════

BANNER = r"""
  ╔═══════════════════════════════════════════════════════╗
  ║         SECURITY  AUDIT  SYSTEM  v1.0                 ║
  ║   Simulate · Analyse · Report · Remediate             ║
  ╚═══════════════════════════════════════════════════════╝
"""

MENU = """
  ┌────────────────────────────────────────────────────────┐
  │  SCANNING                                              │
  │   1. Run full security audit                           │
  │   2. Run audit by category                             │
  │   3. Run a single check                                │
  │                                                        │
  │  RESULTS                                               │
  │   4. Display all check results                         │
  │   5. List failed checks only                           │
  │   6. List warnings only                                │
  │   7. Filter checks by severity                         │
  │                                                        │
  │  REPORTS                                               │
  │   8. Generate full audit report                        │
  │   9. Export results to JSON                            │
  │                                                        │
  │   0. Exit                                              │
  └────────────────────────────────────────────────────────┘
  Choice: """


class CLI:

    def __init__(self):
        self._mgr = AuditManager()

    @staticmethod
    def _ask(prompt: str) -> str:
        return input(f"  {prompt}").strip()

    @staticmethod
    def _choose(prompt: str, options: list[str]) -> str:
        display = " / ".join(options)
        while True:
            val = input(f"  {prompt} [{display}]: ").strip().upper()
            if val in options:
                return val
            print(f"  [!] Enter one of: {display}")

    # ── Menu actions ──────────────────────────
    def _run_full(self) -> None:
        self._mgr.run_full_scan(verbose=True)

    def _run_category(self) -> None:
        cats = self._mgr.categories()
        print("\n  Available categories:")
        for i, cat in enumerate(cats, 1):
            print(f"    {i}. {cat}")
        raw = self._ask("Category number: ")
        try:
            idx = int(raw) - 1
            if not (0 <= idx < len(cats)):
                raise ValueError
            self._mgr.run_category_scan(cats[idx])
        except (ValueError, IndexError):
            print("  [!] Invalid selection.\n")

    def _run_single(self) -> None:
        check_id = self._ask("Check ID (e.g. PWD-001): ").upper()
        self._mgr.run_single_check(check_id)

    def _filter_severity(self) -> None:
        sev = self._choose("Severity", SEVERITIES)
        results = self._mgr.checks_by_severity(sev)
        ran = [c for c in results if c.ran]
        if not ran:
            print(f"\n  No ran checks with severity {sev}.\n")
            return
        print(f"\n{LINE}")
        print(f"  Checks with severity {SEV_ICON[sev]} {sev}  ({len(ran)} found)")
        print(LINE)
        for c in ran:
            c.display(compact=True)
        print(f"{LINE}\n")

    def _display_warnings(self) -> None:
        warned = self._mgr.warned_checks()
        if not warned:
            print("\n  No warnings raised.\n")
            return
        print(f"\n{DLINE}")
        print(f"  ⚠️  WARNINGS  ({len(warned)})")
        print(DLINE)
        for c in warned:
            c.display()

    def _export_json(self) -> None:
        filepath = self._ask("Output file path [audit_results.json]: ")
        if not filepath:
            filepath = "audit_results.json"
        try:
            self._mgr.export_json(filepath)
            print(f"\n  ✔  Results exported to '{filepath}'.\n")
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")
        except OSError as exc:
            print(f"\n  [!] File error: {exc}\n")

    # ── Main loop ─────────────────────────────
    def run(self) -> None:
        print(BANNER)

        dispatch = {
            "1": self._run_full,
            "2": self._run_category,
            "3": self._run_single,
            "4": self._mgr.display_all_results,
            "5": self._mgr.display_failed,
            "6": self._display_warnings,
            "7": self._filter_severity,
            "8": self._mgr.generate_report,
            "9": self._export_json,
        }

        while True:
            try:
                choice = input(MENU).strip()
                if choice == "0":
                    print("\n  Audit system shutdown. Goodbye!\n")
                    break
                action = dispatch.get(choice)
                if action is None:
                    print("  [!] Invalid choice. Enter 0-9.")
                else:
                    action()
            except KeyboardInterrupt:
                print("\n\n  Interrupted. Goodbye!\n")
                break
            except Exception as exc:
                print(f"\n  [!] Unexpected error: {exc}\n")


# ═══════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    CLI().run()