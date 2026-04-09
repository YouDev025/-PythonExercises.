#!/usr/bin/env python3
"""
=====================================================================
  Secure Configuration Checker
  Author : Senior Python / Cybersecurity Engineer
  Purpose: Analyse a running system and surface insecure settings
  Run    : python secure_configuration_checker.py
  Deps   : Standard-library only (Python 3.8+)
=====================================================================
"""

import os
import sys
import json
import stat
import socket
import platform
import datetime
import textwrap
from pathlib import Path
from typing import List, Dict, Optional

# ──────────────────────────────────────────────────────────────────
# ANSI colour helpers (gracefully disabled on Windows if needed)
# ──────────────────────────────────────────────────────────────────
_USE_COLOR = sys.stdout.isatty() and platform.system() != "Windows"

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

def red(t):    return _c("91", t)
def yellow(t): return _c("93", t)
def green(t):  return _c("92", t)
def cyan(t):   return _c("96", t)
def bold(t):   return _c("1",  t)
def dim(t):    return _c("2",  t)


# ──────────────────────────────────────────────────────────────────
# Finding data-class
# ──────────────────────────────────────────────────────────────────
SEVERITY_SCORE = {"Low": 1, "Medium": 2, "High": 3}

class Finding:
    """Represents a single security finding."""

    def __init__(
        self,
        check: str,
        name: str,
        severity: str,          # "Low" | "Medium" | "High"
        description: str,
        recommendation: str,
        extra: Optional[Dict] = None,
    ):
        self.check          = check
        self.name           = name
        self.severity       = severity
        self.score          = SEVERITY_SCORE.get(severity, 0)
        self.description    = description
        self.recommendation = recommendation
        self.extra          = extra or {}
        self.timestamp      = datetime.datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict:
        return {
            "check":          self.check,
            "name":           self.name,
            "severity":       self.severity,
            "score":          self.score,
            "description":    self.description,
            "recommendation": self.recommendation,
            "extra":          self.extra,
            "timestamp":      self.timestamp,
        }

    # ── pretty terminal print ──
    def print(self) -> None:
        sev_color = {"Low": yellow, "Medium": yellow, "High": red}.get(
            self.severity, lambda x: x
        )
        bar = "─" * 60
        print(f"\n  {bar}")
        print(f"  {bold('Issue')}      : {self.name}")
        print(f"  {bold('Severity')}   : {sev_color(self.severity)}  (risk score: {self.score})")
        print(f"  {bold('Check')}      : {dim(self.check)}")
        print(f"  {bold('Description')}: {self._wrap(self.description)}")
        print(f"  {bold('Fix')}        : {green(self._wrap(self.recommendation))}")
        if self.extra:
            print(f"  {bold('Details')}    : {self.extra}")

    @staticmethod
    def _wrap(text: str, width: int = 72, indent: int = 16) -> str:
        lines = textwrap.wrap(text, width)
        pad   = " " * indent
        return ("\n" + pad).join(lines)


# ──────────────────────────────────────────────────────────────────
# Individual check modules
# ──────────────────────────────────────────────────────────────────

class CheckBase:
    """Abstract base class for all checks."""

    name: str = "BaseCheck"

    def run(self) -> List[Finding]:
        raise NotImplementedError


# ── 1. System Information ─────────────────────────────────────────
class SystemInfoCheck(CheckBase):
    name = "System Information"

    def run(self) -> List[Finding]:
        findings: List[Finding] = []
        info = {
            "os":       platform.system(),
            "release":  platform.release(),
            "version":  platform.version(),
            "machine":  platform.machine(),
            "hostname": socket.gethostname(),
            "python":   platform.python_version(),
        }

        print(f"\n  {cyan('[ System Info ]')}")
        for k, v in info.items():
            print(f"    {k:<12}: {v}")

        # Flag end-of-life / very old kernel hints (heuristic)
        ver = platform.release().lower()
        if any(old in ver for old in ("2.6", "3.10", "3.12", "xp", "vista", "7")):
            findings.append(Finding(
                check=self.name,
                name="Potentially outdated OS / kernel",
                severity="High",
                description=(
                    f"Detected kernel/OS version '{platform.release()}' which "
                    "may be end-of-life and no longer receive security patches."
                ),
                recommendation=(
                    "Upgrade to a supported OS or kernel version and apply all "
                    "available security patches immediately."
                ),
                extra={"detected_release": platform.release()},
            ))

        # Generic info finding (always present, Low severity – informational)
        findings.append(Finding(
            check=self.name,
            name="System information collected",
            severity="Low",
            description="System metadata was successfully enumerated.",
            recommendation="Review collected information for unintended data exposure.",
            extra=info,
        ))
        return findings


# ── 2. Password Policy ────────────────────────────────────────────
class PasswordPolicyCheck(CheckBase):
    """
    On Linux   : parses /etc/login.defs for PASS_* directives.
    On Windows  : calls `net accounts` via subprocess (read-only).
    On macOS    : checks pwpolicy (best-effort).
    Falls back to a simulated/default policy if nothing is readable.
    """
    name = "Password Policy"

    # Thresholds considered secure
    MIN_LEN_THRESHOLD    = 12
    MAX_AGE_THRESHOLD    = 90   # days

    def run(self) -> List[Finding]:
        findings: List[Finding] = []
        policy   = self._read_policy()

        print(f"\n  {cyan('[ Password Policy ]')}")
        for k, v in policy.items():
            print(f"    {k:<22}: {v}")

        # ── check minimum length ──
        min_len = policy.get("min_length", 0)
        if isinstance(min_len, int) and min_len < self.MIN_LEN_THRESHOLD:
            findings.append(Finding(
                check=self.name,
                name="Weak minimum password length",
                severity="High" if min_len < 8 else "Medium",
                description=(
                    f"Minimum password length is set to {min_len} characters, "
                    f"below the recommended {self.MIN_LEN_THRESHOLD}."
                ),
                recommendation=(
                    f"Set the minimum password length to at least "
                    f"{self.MIN_LEN_THRESHOLD} characters in your password policy."
                ),
                extra={"current_min_length": min_len},
            ))

        # ── check max age ──
        max_age = policy.get("max_age_days", 0)
        if isinstance(max_age, int):
            if max_age == 0 or max_age > 365:
                findings.append(Finding(
                    check=self.name,
                    name="Password never expires or expiry too long",
                    severity="Medium",
                    description=(
                        f"Maximum password age is set to '{max_age}' days. "
                        "Passwords that never expire increase breach risk."
                    ),
                    recommendation=(
                        f"Configure a maximum password age of {self.MAX_AGE_THRESHOLD} "
                        "days and enforce regular rotation."
                    ),
                    extra={"max_age_days": max_age},
                ))

        # ── complexity (simulated) ──
        if not policy.get("complexity_enabled", False):
            findings.append(Finding(
                check=self.name,
                name="Password complexity not enforced",
                severity="High",
                description=(
                    "No password complexity requirements detected. "
                    "Users may set trivially guessable passwords."
                ),
                recommendation=(
                    "Enable complexity requirements: uppercase, lowercase, digits, "
                    "and special characters."
                ),
            ))

        if not findings:
            print(f"    {green('No policy weaknesses detected.')}")

        return findings

    # ── helpers ──
    def _read_policy(self) -> Dict:
        """Return a normalised dict with password-policy values."""
        os_name = platform.system()
        if os_name == "Linux":
            return self._parse_login_defs()
        elif os_name == "Windows":
            return self._parse_net_accounts()
        elif os_name == "Darwin":
            return self._parse_pwpolicy_macos()
        return self._simulated_policy()

    def _parse_login_defs(self) -> Dict:
        path = Path("/etc/login.defs")
        policy = self._simulated_policy()
        if not path.exists():
            return policy
        try:
            for line in path.read_text(errors="replace").splitlines():
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                key, val = parts[0], parts[1]
                if key == "PASS_MIN_LEN":
                    policy["min_length"] = int(val)
                elif key == "PASS_MAX_DAYS":
                    policy["max_age_days"] = int(val)
                elif key == "PASS_MIN_DAYS":
                    policy["min_age_days"] = int(val)
                elif key == "PASS_WARN_AGE":
                    policy["warn_age_days"] = int(val)
        except Exception:
            pass
        return policy

    def _parse_net_accounts(self) -> Dict:
        import subprocess
        policy = self._simulated_policy()
        try:
            out = subprocess.check_output(
                ["net", "accounts"], stderr=subprocess.DEVNULL, text=True
            )
            for line in out.splitlines():
                line = line.strip()
                if "Minimum password length" in line:
                    val = line.split(":")[-1].strip()
                    policy["min_length"] = int(val) if val.isdigit() else 0
                elif "Maximum password age" in line:
                    val = line.split(":")[-1].strip().split()[0]
                    policy["max_age_days"] = int(val) if val.isdigit() else 0
                elif "Password complexity" in line:
                    policy["complexity_enabled"] = "enabled" in line.lower()
        except Exception:
            pass
        return policy

    def _parse_pwpolicy_macos(self) -> Dict:
        return self._simulated_policy()   # macOS pwpolicy needs root

    @staticmethod
    def _simulated_policy() -> Dict:
        """Safe defaults for when no real policy can be read."""
        return {
            "min_length":        8,
            "max_age_days":      0,
            "min_age_days":      0,
            "warn_age_days":     7,
            "complexity_enabled": False,
            "source":            "simulated/default",
        }


# ── 3. File Permissions ───────────────────────────────────────────
class FilePermissionsCheck(CheckBase):
    name = "File Permissions"

    IS_WINDOWS = platform.system() == "Windows"

    # File name / suffix patterns considered sensitive
    SENSITIVE_PATTERNS = (
        ".env", ".env.local", ".env.production", ".env.staging",
        "config.ini", "config.cfg", "settings.py", "settings.ini",
        "*.bak", "*.backup", "*.sql", "*.dump",
        "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
        "*.pem", "*.key", "*.p12", "*.pfx",
        "passwd", "shadow", "htpasswd",
        "wp-config.php", "database.yml", "secrets.yml",
        "*.sqlite", "*.db",
    )

    # ── Directories to scan – deliberately shallow on Windows ─────
    # We use targeted, small directories instead of rglob over home.
    @property
    def SCAN_DIRS(self) -> List[Path]:
        cwd = Path(os.getcwd())
        if self.IS_WINDOWS:
            # On Windows: only scan the current project folder +
            # a few well-known sensitive spots (all shallow)
            candidates = [
                cwd,
                Path(os.environ.get("USERPROFILE", "C:/Users/Public")),
                Path("C:/inetpub/wwwroot"),
                Path("C:/xampp/htdocs"),
                Path("C:/wamp64/www"),
                Path("C:/ProgramData"),
            ]
        else:
            candidates = [
                cwd,
                Path.home(),
                Path("/etc"),
                Path("/tmp"),
                Path("/var/www"),
            ]
        return [p for p in candidates if p.exists()]

    # Hard limits to prevent runaway scanning
    MAX_FILES_PER_DIR = 800    # stop scanning a single directory after N files
    MAX_DEPTH         = 4      # maximum folder depth to recurse into
    MAX_TOTAL_FILES   = 2000   # absolute ceiling across all directories

    def run(self) -> List[Finding]:
        findings: List[Finding] = []
        total_scanned = 0
        dirs_scanned  = 0

        print(f"\n  {cyan('[ File Permissions ]')}")
        if self.IS_WINDOWS:
            print(f"    {dim('Windows mode: depth-limited scan (max depth 4, max 2000 files)')}")

        for base_dir in self.SCAN_DIRS:
            remaining = self.MAX_TOTAL_FILES - total_scanned
            if remaining <= 0:
                print(f"    {yellow('File limit reached – stopping early.')}")
                break
            print(f"    Scanning: {dim(str(base_dir))} … ", end="", flush=True)
            new_findings, count = self._scan_directory(
                base_dir,
                max_files=min(self.MAX_FILES_PER_DIR, remaining),
            )
            findings     += new_findings
            total_scanned += count
            dirs_scanned  += 1
            print(f"{count} file(s) checked, {len(new_findings)} issue(s) found.")

        print(f"    Total: {total_scanned} file(s) across {dirs_scanned} director(ies).")
        if not findings:
            print(f"    {green('No permission issues found.')}")

        return findings

    # ── recursive scanner with depth + count limits ───────────────
    def _scan_directory(
        self,
        directory: Path,
        max_files: int,
        _depth: int = 0,
        _counter: Optional[List[int]] = None,
    ):
        """
        Walk *directory* up to MAX_DEPTH levels deep.
        Returns (findings_list, files_checked_count).
        Uses a mutable list as a shared counter across recursion levels.
        """
        if _counter is None:
            _counter = [0]   # shared mutable counter

        findings: List[Finding] = []

        # ── skip large "noise" subtrees on Windows ────────────────
        skip_suffixes = ()
        if self.IS_WINDOWS:
            skip_names_lower = {
                "appdata", "application data", "local settings",
                "temp", "tmp", "cache", "thumbnails",
                "windows", "system32", "syswow64",
                "microsoft", "windowsapps", "node_modules",
                ".git", "__pycache__", "site-packages",
            }
            if directory.name.lower() in skip_names_lower:
                return findings, _counter[0]

        try:
            with os.scandir(directory) as it:
                entries = list(it)
        except (PermissionError, OSError):
            return findings, _counter[0]

        for entry in entries:
            if _counter[0] >= max_files:
                break
            try:
                if entry.is_file(follow_symlinks=False):
                    _counter[0] += 1
                    findings += self._check_file(Path(entry.path))

                elif entry.is_dir(follow_symlinks=False) and _depth < self.MAX_DEPTH:
                    sub_findings, _ = self._scan_directory(
                        Path(entry.path),
                        max_files=max_files,
                        _depth=_depth + 1,
                        _counter=_counter,
                    )
                    findings += sub_findings

            except (PermissionError, OSError):
                continue

        return findings, _counter[0]

    # ── per-file checks ───────────────────────────────────────────
    def _check_file(self, path: Path) -> List[Finding]:
        findings: List[Finding] = []
        try:
            file_stat = path.stat()
            mode      = file_stat.st_mode
        except (PermissionError, OSError):
            return findings

        if self.IS_WINDOWS:
            # On Windows the POSIX permission bits are minimal / unreliable.
            # Focus on: sensitive file existence & basic readable-by-all hint.
            if self._is_sensitive(path):
                findings.append(Finding(
                    check=self.name,
                    name="Sensitive file detected",
                    severity="Medium",
                    description=(
                        f"Sensitive file found at '{path}'. "
                        "Ensure it is not accessible to unauthorised users."
                    ),
                    recommendation=(
                        "Right-click → Properties → Security and restrict "
                        "access to the owner / service account only. "
                        "Never commit this file to version control."
                    ),
                    extra={"path": str(path)},
                ))
        else:
            # ── POSIX: world-writable ──
            if mode & stat.S_IWOTH:
                findings.append(Finding(
                    check=self.name,
                    name="World-writable file detected",
                    severity="High",
                    description=(
                        f"File '{path}' is writable by any user "
                        f"(mode: {oct(mode)})."
                    ),
                    recommendation=f"Run: chmod o-w \"{path}\"",
                    extra={"path": str(path), "mode": oct(mode)},
                ))

            # ── POSIX: sensitive file others-readable ──
            if self._is_sensitive(path) and (mode & stat.S_IROTH):
                findings.append(Finding(
                    check=self.name,
                    name="Sensitive file readable by others",
                    severity="High",
                    description=(
                        f"Sensitive file '{path}' is readable by all users "
                        f"(mode: {oct(mode)})."
                    ),
                    recommendation=f"Run: chmod 600 \"{path}\"",
                    extra={"path": str(path), "mode": oct(mode)},
                ))

            # ── POSIX: SUID / SGID ──
            if mode & (stat.S_ISUID | stat.S_ISGID):
                findings.append(Finding(
                    check=self.name,
                    name="SUID/SGID bit set",
                    severity="Medium",
                    description=(
                        f"File '{path}' has SUID/SGID bit set "
                        f"(mode: {oct(mode)}). May enable privilege escalation."
                    ),
                    recommendation=(
                        f"Review necessity. Remove if not required: "
                        f"chmod u-s,g-s \"{path}\""
                    ),
                    extra={"path": str(path), "mode": oct(mode)},
                ))

        return findings

    def _is_sensitive(self, path: Path) -> bool:
        name = path.name.lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            else:
                if name == pattern.lower():
                    return True
        return False


# ── 4. Open Ports ─────────────────────────────────────────────────
class OpenPortsCheck(CheckBase):
    name = "Open Ports"

    # (port, service_label, notes)
    COMMON_PORTS = [
        (21,    "FTP",         "Transmits credentials in plaintext."),
        (22,    "SSH",         "Ensure key-based auth; disable root login."),
        (23,    "Telnet",      "Plaintext protocol – replace with SSH."),
        (25,    "SMTP",        "Verify relay restrictions."),
        (53,    "DNS",         "Restrict recursive queries if public."),
        (80,    "HTTP",        "Redirect all traffic to HTTPS."),
        (110,   "POP3",        "Plaintext mail retrieval – use POP3S."),
        (135,   "RPC",         "Common attack surface on Windows."),
        (139,   "NetBIOS",     "Legacy protocol; disable if unused."),
        (143,   "IMAP",        "Plaintext – enforce STARTTLS/IMAPS."),
        (443,   "HTTPS",       "Verify TLS version and cipher suite."),
        (445,   "SMB",         "Restrict external access; patch promptly."),
        (1433,  "MSSQL",       "Do not expose to the public internet."),
        (3306,  "MySQL",       "Do not expose to the public internet."),
        (3389,  "RDP",         "Limit to VPN; enable NLA."),
        (5432,  "PostgreSQL",  "Do not expose to the public internet."),
        (5900,  "VNC",         "Encrypt traffic; require strong passwords."),
        (6379,  "Redis",       "Never expose without auth/firewall."),
        (8080,  "HTTP-Alt",    "Ensure this is intentional."),
        (8443,  "HTTPS-Alt",   "Verify certificate and access controls."),
        (27017, "MongoDB",     "Auth required; avoid public exposure."),
    ]

    # Ports that are high-risk if open
    HIGH_RISK = {21, 23, 135, 139, 445, 3389, 5900, 6379, 27017}
    MEDIUM_RISK = {80, 3306, 5432, 1433, 8080}

    TIMEOUT = 0.5   # seconds per port

    def run(self) -> List[Finding]:
        findings: List[Finding] = []
        open_ports: List[tuple] = []

        print(f"\n  {cyan('[ Open Ports ]')}")
        print(f"    Scanning {len(self.COMMON_PORTS)} common ports on localhost …")

        for port, service, note in self.COMMON_PORTS:
            is_open = self._is_port_open("127.0.0.1", port)
            status  = green("closed")
            if is_open:
                status = red("OPEN")
                open_ports.append((port, service, note))
            print(f"    Port {port:<6} {service:<14} {status}")

        for port, service, note in open_ports:
            if port in self.HIGH_RISK:
                sev = "High"
            elif port in self.MEDIUM_RISK:
                sev = "Medium"
            else:
                sev = "Low"

            findings.append(Finding(
                check=self.name,
                name=f"Open port detected: {port}/{service}",
                severity=sev,
                description=(
                    f"Port {port} ({service}) is listening on this host. {note}"
                ),
                recommendation=(
                    "If this service is not needed, disable it. "
                    "If required, ensure it is properly secured, "
                    "firewall-restricted, and running an up-to-date version."
                ),
                extra={"port": port, "service": service},
            ))

        if not findings:
            print(f"\n    {green('No concerning open ports found.')}")

        return findings

    @staticmethod
    def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False


# ── 5. Environment Checks ─────────────────────────────────────────
class EnvironmentCheck(CheckBase):
    name = "Environment"

    # Known default / weak credentials to detect
    DEFAULT_CREDS = [
        ("admin",    "admin"),
        ("admin",    "password"),
        ("root",     "root"),
        ("root",     "toor"),
        ("user",     "user"),
        ("postgres", "postgres"),
        ("mysql",    "mysql"),
        ("redis",    ""),
        ("guest",    "guest"),
        ("test",     "test"),
    ]

    # ENV variables that hint at debug / insecure mode
    DEBUG_VARS = {
        "DEBUG", "FLASK_DEBUG", "DJANGO_DEBUG", "APP_DEBUG",
        "NODE_ENV", "RAILS_ENV", "APP_ENV", "ENVIRONMENT",
    }

    # ENV variables that should NEVER appear in production
    SENSITIVE_ENV_VARS = {
        "SECRET_KEY", "DB_PASSWORD", "DATABASE_URL", "AWS_SECRET_ACCESS_KEY",
        "PRIVATE_KEY", "API_KEY", "JWT_SECRET", "STRIPE_SECRET_KEY",
        "GITHUB_TOKEN", "SLACK_TOKEN", "SENDGRID_API_KEY",
    }

    def run(self) -> List[Finding]:
        findings: List[Finding] = []
        env = os.environ

        print(f"\n  {cyan('[ Environment Checks ]')}")

        # ── debug mode ──
        for var in self.DEBUG_VARS:
            val = env.get(var, "").lower()
            if val in ("1", "true", "yes", "debug", "development", "dev"):
                findings.append(Finding(
                    check=self.name,
                    name=f"Debug/development mode active ({var})",
                    severity="High",
                    description=(
                        f"Environment variable {var}={env[var]!r} suggests the "
                        "application is running in debug or development mode. "
                        "This may expose stack traces, verbose errors, or internal "
                        "endpoints to attackers."
                    ),
                    recommendation=(
                        f"Set {var} to a production value (e.g., 'production' / "
                        "'false' / '0') before deploying."
                    ),
                    extra={"variable": var, "value": env[var]},
                ))
                print(f"    {red('WARN')} Debug mode: {var}={env[var]!r}")

        # ── sensitive env vars exposed ──
        for var in self.SENSITIVE_ENV_VARS:
            if var in env:
                # Show only first 4 chars, mask the rest
                masked = env[var][:4] + "****" if len(env[var]) > 4 else "****"
                findings.append(Finding(
                    check=self.name,
                    name=f"Sensitive secret in environment: {var}",
                    severity="High",
                    description=(
                        f"Environment variable {var} contains what appears to be "
                        "a secret or credential. Secrets stored in environment "
                        "variables are accessible to all processes and may be "
                        "leaked through crash dumps or logs."
                    ),
                    recommendation=(
                        "Use a dedicated secrets manager (e.g., HashiCorp Vault, "
                        "AWS Secrets Manager) instead of plain environment variables."
                    ),
                    extra={"variable": var, "masked_value": masked},
                ))
                print(f"    {red('WARN')} Sensitive var found: {var}={masked}")

        # ── default credentials simulation ──
        print(f"    Checking for well-known default credential patterns …")
        findings += self._check_default_credentials()

        # ── PATH integrity ──
        findings += self._check_path_integrity()

        # ── temp / world-writable PATH entries ──
        if not findings:
            print(f"    {green('No critical environment issues detected.')}")

        return findings

    def _check_default_credentials(self) -> List[Finding]:
        findings = []
        # Simulate: check if any default-cred pair is present as env vars
        # (real-world: would probe service endpoints)
        for user, pwd in self.DEFAULT_CREDS:
            env_user = os.environ.get("DB_USER", "").lower()
            env_pass = os.environ.get("DB_PASSWORD", "").lower()
            if env_user == user and env_pass == pwd:
                findings.append(Finding(
                    check=self.name,
                    name="Default credentials detected in environment",
                    severity="High",
                    description=(
                        f"Default credentials ({user}/{pwd}) found in environment "
                        "variables DB_USER / DB_PASSWORD."
                    ),
                    recommendation=(
                        "Replace default credentials with strong, unique passwords "
                        "and store them in a secrets manager."
                    ),
                    extra={"username": user},
                ))

        # Additionally check for common default patterns in MYSQL_ROOT_PASSWORD etc.
        db_pass_vars = [
            "MYSQL_ROOT_PASSWORD", "POSTGRES_PASSWORD",
            "MONGO_INITDB_ROOT_PASSWORD",
        ]
        weak_values = {"", "root", "toor", "password", "admin", "123456", "test"}
        for var in db_pass_vars:
            if var in os.environ:
                val = os.environ[var]
                if val.lower() in weak_values:
                    findings.append(Finding(
                        check=self.name,
                        name=f"Weak/default DB password in {var}",
                        severity="High",
                        description=(
                            f"{var} is set to a well-known default or trivial value."
                        ),
                        recommendation=(
                            "Use a randomly generated, high-entropy password and "
                            "rotate it regularly."
                        ),
                        extra={"variable": var},
                    ))
                    print(f"    {red('WARN')} Weak DB password: {var}")

        return findings

    def _check_path_integrity(self) -> List[Finding]:
        findings = []
        path_var  = os.environ.get("PATH", "")
        entries   = path_var.split(os.pathsep)

        # Check for empty string or "." in PATH (relative path hijack)
        for entry in entries:
            if entry in ("", "."):
                findings.append(Finding(
                    check=self.name,
                    name="Unsafe PATH entry: relative directory",
                    severity="High",
                    description=(
                        "The PATH environment variable contains an empty string or "
                        "'.' (current directory). This allows an attacker who can "
                        "write to the working directory to shadow system binaries."
                    ),
                    recommendation=(
                        "Remove '' and '.' from PATH. "
                        "Absolute paths only should appear in PATH."
                    ),
                    extra={"path_entry": repr(entry)},
                ))
                print(f"    {red('WARN')} Unsafe PATH entry: {entry!r}")
                break

        # World-writable directories in PATH
        if platform.system() != "Windows":
            for entry in entries:
                p = Path(entry)
                if p.exists() and p.is_dir():
                    try:
                        mode = p.stat().st_mode
                        if mode & stat.S_IWOTH:
                            findings.append(Finding(
                                check=self.name,
                                name=f"World-writable directory in PATH: {entry}",
                                severity="High",
                                description=(
                                    f"Directory '{entry}' is in PATH and is "
                                    "world-writable. Any user can plant malicious "
                                    "executables there."
                                ),
                                recommendation=(
                                    f"Remove world-write permission: "
                                    f"`chmod o-w {entry}`"
                                ),
                                extra={"path_entry": entry, "mode": oct(mode)},
                            ))
                    except OSError:
                        pass

        return findings


# ──────────────────────────────────────────────────────────────────
# Scanner – orchestrates all checks
# ──────────────────────────────────────────────────────────────────
class Scanner:
    """Run one or more checks and aggregate results."""

    CHECKS: Dict[str, CheckBase] = {
        "1": SystemInfoCheck(),
        "2": PasswordPolicyCheck(),
        "3": FilePermissionsCheck(),
        "4": OpenPortsCheck(),
        "5": EnvironmentCheck(),
    }

    CHECK_LABELS = {
        "1": "System Information",
        "2": "Password Policy",
        "3": "File Permissions",
        "4": "Open Ports",
        "5": "Environment Checks",
    }

    def __init__(self):
        self.findings: List[Finding] = []

    def run(self, keys: Optional[List[str]] = None) -> List[Finding]:
        """
        Run checks identified by *keys*. Pass None to run all.
        Returns a fresh findings list each time.
        """
        self.findings = []
        targets = keys if keys else list(self.CHECKS.keys())

        for key in targets:
            check = self.CHECKS.get(key)
            if check is None:
                print(f"  {yellow(f'Unknown check key: {key}')}")
                continue
            print(f"\n{bold('══ Running: ' + check.name + ' ══')}")
            try:
                result = check.run()
                self.findings.extend(result)
            except Exception as exc:
                print(f"  {red(f'Check failed: {exc}')}")

        return self.findings

    # ── risk score ──
    def total_score(self) -> int:
        return sum(f.score for f in self.findings)

    def risk_label(self) -> str:
        score = self.total_score()
        if score == 0:
            return green("None")
        elif score <= 5:
            return green("Low")
        elif score <= 12:
            return yellow("Medium")
        else:
            return red("High / Critical")


# ──────────────────────────────────────────────────────────────────
# Report writers
# ──────────────────────────────────────────────────────────────────
REPORT_TXT  = "config_audit.txt"
REPORT_JSON = "config_audit.json"


def save_text_report(findings: List[Finding], scanner: Scanner) -> str:
    """Write a human-readable text report; return the file path."""
    lines = [
        "=" * 70,
        "  SECURE CONFIGURATION CHECKER – AUDIT REPORT",
        f"  Generated : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Host      : {socket.gethostname()}",
        f"  OS        : {platform.system()} {platform.release()}",
        "=" * 70,
        "",
        f"  Total findings : {len(findings)}",
        f"  Risk score     : {scanner.total_score()}",
        "",
    ]

    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    for f in sorted(findings, key=lambda x: severity_order.get(x.severity, 9)):
        lines += [
            "─" * 70,
            f"  Issue     : {f.name}",
            f"  Severity  : {f.severity}  (score: {f.score})",
            f"  Check     : {f.check}",
            f"  Timestamp : {f.timestamp}",
            "",
            f"  Description:",
            *[f"    {l}" for l in textwrap.wrap(f.description, 64)],
            "",
            f"  Recommendation:",
            *[f"    {l}" for l in textwrap.wrap(f.recommendation, 64)],
        ]
        if f.extra:
            lines.append(f"  Details   : {f.extra}")
        lines.append("")

    lines += ["=" * 70, "  END OF REPORT", "=" * 70]

    with open(REPORT_TXT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return REPORT_TXT


def save_json_report(findings: List[Finding], scanner: Scanner) -> str:
    """Write a machine-readable JSON report; return the file path."""
    payload = {
        "meta": {
            "generated":   datetime.datetime.now().isoformat(),
            "hostname":    socket.gethostname(),
            "os":          f"{platform.system()} {platform.release()}",
            "total_score": scanner.total_score(),
        },
        "findings": [f.to_dict() for f in findings],
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return REPORT_JSON


# ──────────────────────────────────────────────────────────────────
# Terminal UI helpers
# ──────────────────────────────────────────────────────────────────
BANNER = r"""
 ____  _____ ____ _   _ ____  ___ _______   __
/ ___|| ____/ ___| | | |  _ \|_ _|_   _\ \ / /
\___ \|  _|| |   | | | | |_) || |  | |  \ V /
 ___) | |__| |___| |_| |  _ < | |  | |   | |
|____/|_____\____|\___/|_| \_\___| |_|   |_|

     C O N F I G U R A T I O N   C H E C K E R
"""


def print_banner() -> None:
    print(cyan(BANNER))
    print(dim("  Version 1.0  |  Python " + platform.python_version()))
    print(dim("  For authorised use only – no destructive actions performed.\n"))


def print_summary(findings: List[Finding], scanner: Scanner) -> None:
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    print(f"\n{'═' * 62}")
    print(bold("  SCAN SUMMARY"))
    print(f"{'─' * 62}")
    print(f"  Total findings  : {bold(str(len(findings)))}")
    print(f"  {red('High')}            : {counts['High']}")
    print(f"  {yellow('Medium')}          : {counts['Medium']}")
    print(f"  {green('Low')}             : {counts['Low']}")
    print(f"  Aggregate risk  : {scanner.risk_label()}")
    print(f"{'═' * 62}\n")


def print_findings(findings: List[Finding]) -> None:
    if not findings:
        print(f"\n  {green('No findings to display.')}")
        return
    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_findings = sorted(findings, key=lambda x: severity_order.get(x.severity, 9))
    print(bold("\n  ── Detailed Findings ──"))
    for f in sorted_findings:
        f.print()
    print()


def print_menu() -> None:
    print(f"\n{'═' * 50}")
    print(bold("  MAIN MENU"))
    print(f"{'─' * 50}")
    print("  [1]  Run Full Scan")
    print("  [2]  Run Specific Checks")
    print("  [3]  View Last Findings")
    print("  [4]  Save Text Report  (config_audit.txt)")
    print("  [5]  Save JSON Report  (config_audit.json)")
    print("  [6]  Exit")
    print(f"{'═' * 50}")


def select_checks() -> List[str]:
    print(f"\n  Available checks:")
    scanner = Scanner()
    for k, label in scanner.CHECK_LABELS.items():
        print(f"    [{k}] {label}")
    raw = input("\n  Enter check numbers separated by commas (e.g. 1,3,4): ").strip()
    selected = [x.strip() for x in raw.split(",") if x.strip() in scanner.CHECKS]
    if not selected:
        print(f"  {yellow('No valid selection – running all checks.')}")
        return list(scanner.CHECKS.keys())
    return selected


# ──────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────
def main() -> None:
    print_banner()
    scanner  = Scanner()
    findings: List[Finding] = []

    while True:
        print_menu()
        choice = input(bold("  Enter choice: ")).strip()

        if choice == "1":
            # ── Full scan ──
            findings = scanner.run()
            print_findings(findings)
            print_summary(findings, scanner)

        elif choice == "2":
            # ── Targeted scan ──
            keys     = select_checks()
            findings = scanner.run(keys)
            print_findings(findings)
            print_summary(findings, scanner)

        elif choice == "3":
            # ── Re-display last findings ──
            if not findings:
                print(f"\n  {yellow('No scan has been run yet. Please run a scan first.')}")
            else:
                print_findings(findings)
                print_summary(findings, scanner)

        elif choice == "4":
            # ── Text report ──
            if not findings:
                print(f"\n  {yellow('Run a scan first before saving a report.')}")
            else:
                path = save_text_report(findings, scanner)
                print(f"\n  {green('Text report saved:')} {bold(path)}")

        elif choice == "5":
            # ── JSON report ──
            if not findings:
                print(f"\n  {yellow('Run a scan first before saving a report.')}")
            else:
                path = save_json_report(findings, scanner)
                print(f"\n  {green('JSON report saved:')} {bold(path)}")

        elif choice == "6":
            print(f"\n  {green('Goodbye. Stay secure!')}\n")
            sys.exit(0)

        else:
            print(f"\n  {yellow('Invalid option. Please choose 1–6.')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {yellow('Interrupted by user. Exiting cleanly.')}\n")
        sys.exit(0)