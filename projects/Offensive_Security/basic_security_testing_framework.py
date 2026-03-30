"""
basic_security_testing_framework_interactive.py

Interactive console application for the Security Testing Framework.
No external dependencies — runs on Python 3.8+ with stdlib only.
All tests are purely SIMULATED; no real network connections are made.

How to run in PyCharm:
    Right-click the file → Run, or press Shift+F10.
    Make sure "Emulate terminal in output console" is checked in:
    Run > Edit Configurations > Execution > Emulate terminal in output console
"""

from __future__ import annotations

import os
import random
import textwrap
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional


# ══════════════════════════════════════════════════════════════════════
# ANSI colour helpers  (auto-disabled on Windows without ANSI support)
# ══════════════════════════════════════════════════════════════════════

def _ansi_supported() -> bool:
    if os.name == "nt":
        # Windows 10 1511+ supports ANSI via ENABLE_VIRTUAL_TERMINAL_PROCESSING
        try:
            import ctypes
            kernel = ctypes.windll.kernel32
            kernel.SetConsoleMode(kernel.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True

_USE_COLOR = _ansi_supported()

class C:
    """ANSI colour codes."""
    RESET  = "\033[0m"  if _USE_COLOR else ""
    BOLD   = "\033[1m"  if _USE_COLOR else ""
    RED    = "\033[91m" if _USE_COLOR else ""
    GREEN  = "\033[92m" if _USE_COLOR else ""
    YELLOW = "\033[93m" if _USE_COLOR else ""
    BLUE   = "\033[94m" if _USE_COLOR else ""
    CYAN   = "\033[96m" if _USE_COLOR else ""
    GREY   = "\033[90m" if _USE_COLOR else ""
    WHITE  = "\033[97m" if _USE_COLOR else ""

def red(s):    return f"{C.RED}{s}{C.RESET}"
def green(s):  return f"{C.GREEN}{s}{C.RESET}"
def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
def blue(s):   return f"{C.BLUE}{s}{C.RESET}"
def cyan(s):   return f"{C.CYAN}{s}{C.RESET}"
def grey(s):   return f"{C.GREY}{s}{C.RESET}"
def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
def white(s):  return f"{C.WHITE}{s}{C.RESET}"


# ══════════════════════════════════════════════════════════════════════
# Domain enumerations
# ══════════════════════════════════════════════════════════════════════

class ServiceType(str, Enum):
    HTTP    = "HTTP"
    FTP     = "FTP"
    SSH     = "SSH"
    SMTP    = "SMTP"
    DNS     = "DNS"
    UNKNOWN = "UNKNOWN"

class VulnStatus(str, Enum):
    VULNERABLE     = "VULNERABLE"
    NOT_VULNERABLE = "NOT VULNERABLE"
    ERROR          = "ERROR"


# ══════════════════════════════════════════════════════════════════════
# Target
# ══════════════════════════════════════════════════════════════════════

class Target:
    """Represents a network host/service to be assessed."""

    def __init__(
        self,
        address: str,
        port: int,
        service_type: ServiceType = ServiceType.UNKNOWN,
        target_id: Optional[str] = None,
    ) -> None:
        self.target_id: str   = target_id or str(uuid.uuid4())[:8]
        self.address: str     = self._validate_address(address)
        self.port: int        = self._validate_port(port)
        self.service_type     = service_type

    @staticmethod
    def _validate_address(address: str) -> str:
        address = address.strip()
        if not address:
            raise ValueError("Address must not be empty.")
        return address

    @staticmethod
    def _validate_port(port: int) -> int:
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be 1–65535, got {port}.")
        return port

    def __str__(self) -> str:
        svc_color = {
            ServiceType.HTTP: cyan, ServiceType.FTP:  red,
            ServiceType.SSH:  blue, ServiceType.DNS:  yellow,
            ServiceType.SMTP: green,
        }.get(self.service_type, grey)
        return (
            f"{grey('['+self.target_id+']')} "
            f"{white(self.address)}:{white(str(self.port))} "
            f"({svc_color(self.service_type.value)})"
        )

    def plain(self) -> str:
        return f"[{self.target_id}] {self.address}:{self.port} ({self.service_type.value})"


# ══════════════════════════════════════════════════════════════════════
# Result
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Result:
    """Stores the outcome of one module run against one target."""

    result_id:   str        = field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_id:   str        = ""
    module_name: str        = ""
    status:      VulnStatus = VulnStatus.NOT_VULNERABLE
    details:     str        = ""
    timestamp:   datetime   = field(default_factory=datetime.now)

    def display(self, indent: int = 4) -> str:
        pad = " " * indent
        if self.status == VulnStatus.VULNERABLE:
            icon   = red("●")
            status = red(f"{self.status.value:<15}")
        elif self.status == VulnStatus.NOT_VULNERABLE:
            icon   = green("●")
            status = green(f"{self.status.value:<15}")
        else:
            icon   = yellow("●")
            status = yellow(f"{self.status.value:<15}")

        return (
            f"{pad}{icon} {grey('['+self.result_id+']')} "
            f"{cyan(f'{self.module_name:<22}')} {status} "
            f"{grey(self.timestamp.strftime('%H:%M:%S'))}\n"
            f"{pad}  {grey('↳')} {self.details}"
        )


# ══════════════════════════════════════════════════════════════════════
# TestModule
# ══════════════════════════════════════════════════════════════════════

class TestModule:
    """Wraps a named security test with pluggable logic."""

    def __init__(
        self,
        module_name: str,
        description: str,
        test_logic: Callable[[Target], Result],
    ) -> None:
        if not module_name.strip():
            raise ValueError("Module name must not be empty.")
        self.module_name: str = module_name.strip()
        self.description: str = description.strip()
        self.test_logic       = test_logic

    def run(self, target: Target) -> Result:
        try:
            result = self.test_logic(target)
            result.module_name = self.module_name
            result.target_id   = target.target_id
            return result
        except Exception as exc:
            return Result(
                target_id=target.target_id,
                module_name=self.module_name,
                status=VulnStatus.ERROR,
                details=f"Unexpected error: {exc}",
            )


# ══════════════════════════════════════════════════════════════════════
# ModuleManager
# ══════════════════════════════════════════════════════════════════════

class ModuleManager:
    """Registers and executes TestModules."""

    def __init__(self) -> None:
        self._modules: dict[str, TestModule] = {}

    def load_module(self, module: TestModule) -> None:
        if module.module_name in self._modules:
            raise ValueError(f"Module '{module.module_name}' already loaded.")
        self._modules[module.module_name] = module

    def unload_module(self, name: str) -> None:
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found.")
        del self._modules[name]

    def list_modules(self) -> list[TestModule]:
        return list(self._modules.values())

    def get_module(self, name: str) -> TestModule:
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found.")
        return self._modules[name]

    def run_module(self, name: str, target: Target) -> Result:
        return self.get_module(name).run(target)

    def run_all(self, target: Target) -> list[Result]:
        return [m.run(target) for m in self._modules.values()]


# ══════════════════════════════════════════════════════════════════════
# FrameworkManager
# ══════════════════════════════════════════════════════════════════════

class FrameworkManager:
    """Top-level coordinator: targets, modules, results, reports."""

    def __init__(self, name: str = "SecurityTestFramework") -> None:
        self.name           = name
        self._targets: dict[str, Target] = {}
        self.module_manager = ModuleManager()
        self._results: list[Result]      = []

    # ── targets ─────────────────────────────────────────────────────

    def add_target(self, target: Target) -> None:
        if target.target_id in self._targets:
            raise ValueError(f"Target ID '{target.target_id}' already exists.")
        self._targets[target.target_id] = target

    def remove_target(self, target_id: str) -> None:
        if target_id not in self._targets:
            raise KeyError(f"Target '{target_id}' not found.")
        del self._targets[target_id]
        self._results = [r for r in self._results if r.target_id != target_id]

    def get_target(self, target_id: str) -> Target:
        if target_id not in self._targets:
            raise KeyError(f"Target '{target_id}' not found.")
        return self._targets[target_id]

    def list_targets(self) -> list[Target]:
        return list(self._targets.values())

    # ── execution ────────────────────────────────────────────────────

    def run_module_on_target(self, module_name: str, target_id: str) -> Result:
        target = self.get_target(target_id)
        result = self.module_manager.run_module(module_name, target)
        self._results.append(result)
        return result

    def run_all_on_target(self, target_id: str) -> list[Result]:
        target  = self.get_target(target_id)
        results = self.module_manager.run_all(target)
        self._results.extend(results)
        return results

    def run_all_on_all(self) -> list[Result]:
        all_results: list[Result] = []
        for tid in list(self._targets):
            all_results.extend(self.run_all_on_target(tid))
        return all_results

    # ── results ──────────────────────────────────────────────────────

    def get_results(
        self,
        target_id: Optional[str] = None,
        status: Optional[VulnStatus] = None,
    ) -> list[Result]:
        out = self._results
        if target_id:
            out = [r for r in out if r.target_id == target_id]
        if status:
            out = [r for r in out if r.status == status]
        return out

    def clear_results(self) -> None:
        self._results.clear()

    # ── report ───────────────────────────────────────────────────────

    def generate_report(self) -> str:
        sep  = "═" * 68
        dash = "─" * 68
        lines = [
            sep,
            f"  {bold(self.name.upper())} — VULNERABILITY ASSESSMENT REPORT",
            f"  {grey('Generated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}",
            sep,
            f"  Targets : {len(self._targets)}   "
            f"Modules : {len(self.module_manager.list_modules())}   "
            f"Results : {len(self._results)}",
            "",
        ]
        for t in self._targets.values():
            t_res   = self.get_results(target_id=t.target_id)
            n_vuln  = sum(1 for r in t_res if r.status == VulnStatus.VULNERABLE)
            vuln_lbl = red(str(n_vuln)) if n_vuln else green("0")
            lines.append(f"  {dash}")
            lines.append(f"  Target : {t}")
            lines.append(f"  Findings : {vuln_lbl} vulnerable / {len(t_res)} tests")
            for r in t_res:
                lines.append(r.display(indent=4))
        lines.append(f"  {sep}")

        total_v = sum(1 for r in self._results if r.status == VulnStatus.VULNERABLE)
        total_s = sum(1 for r in self._results if r.status == VulnStatus.NOT_VULNERABLE)
        total_e = sum(1 for r in self._results if r.status == VulnStatus.ERROR)
        lines += [
            f"  {bold('SUMMARY')}",
            f"  {red('Vulnerable'    ):<30} {total_v}",
            f"  {green('Not Vulnerable'):<30} {total_s}",
            f"  {yellow('Error'         ):<30} {total_e}",
            sep,
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# Built-in simulated modules
# ══════════════════════════════════════════════════════════════════════

def _make_banner_grab() -> TestModule:
    def logic(t: Target) -> Result:
        banners = {
            ServiceType.HTTP: "Apache/2.2.34 (vulnerable)",
            ServiceType.FTP:  "vsftpd 2.3.4 (backdoor known)",
            ServiceType.SSH:  "OpenSSH 4.3 (legacy ciphers)",
        }
        if t.service_type in banners and random.random() < 0.6:
            return Result(status=VulnStatus.VULNERABLE,
                          details="Banner exposed: " + banners[t.service_type])
        return Result(status=VulnStatus.NOT_VULNERABLE,
                      details="No sensitive banner information detected.")
    return TestModule("BannerGrab",
                      "Checks whether the service exposes version/banner info.",
                      logic)

def _make_default_creds() -> TestModule:
    CREDS = {
        ServiceType.FTP:  "anonymous / ''",
        ServiceType.SSH:  "root / root",
        ServiceType.HTTP: "admin / admin",
        ServiceType.SMTP: "mail / mail",
    }
    def logic(t: Target) -> Result:
        cred = CREDS.get(t.service_type)
        if cred and random.random() < 0.45:
            return Result(status=VulnStatus.VULNERABLE,
                          details=f"Default credentials accepted: {cred}")
        return Result(status=VulnStatus.NOT_VULNERABLE,
                      details="No default credentials accepted.")
    return TestModule("DefaultCredentials",
                      "Attempts common default username/password pairs.",
                      logic)

def _make_ssl_audit() -> TestModule:
    def logic(t: Target) -> Result:
        if t.service_type != ServiceType.HTTP:
            return Result(status=VulnStatus.NOT_VULNERABLE,
                          details="SSL check not applicable for this service.")
        issues = []
        if random.random() < 0.4:  issues.append("TLS 1.0 still enabled")
        if random.random() < 0.3:  issues.append("Self-signed certificate")
        if random.random() < 0.25: issues.append("Weak cipher: RC4")
        if issues:
            return Result(status=VulnStatus.VULNERABLE,
                          details="SSL/TLS issues: " + "; ".join(issues))
        return Result(status=VulnStatus.NOT_VULNERABLE,
                      details="SSL/TLS configuration looks secure.")
    return TestModule("SSLAudit",
                      "Inspects SSL/TLS configuration for weaknesses.",
                      logic)

def _make_open_redirect() -> TestModule:
    def logic(t: Target) -> Result:
        if t.service_type != ServiceType.HTTP:
            return Result(status=VulnStatus.NOT_VULNERABLE,
                          details="Open redirect check only applies to HTTP.")
        if random.random() < 0.35:
            return Result(status=VulnStatus.VULNERABLE,
                          details=f"Open redirect at http://{t.address}/redirect?url=")
        return Result(status=VulnStatus.NOT_VULNERABLE,
                      details="No open redirect vulnerability found.")
    return TestModule("OpenRedirect",
                      "Tests for unvalidated URL redirect endpoints.",
                      logic)

def _make_dns_zone_transfer() -> TestModule:
    def logic(t: Target) -> Result:
        if t.service_type != ServiceType.DNS:
            return Result(status=VulnStatus.NOT_VULNERABLE,
                          details="Zone transfer check only applies to DNS.")
        if random.random() < 0.5:
            return Result(status=VulnStatus.VULNERABLE,
                          details=f"AXFR permitted — {t.address} leaked zone data.")
        return Result(status=VulnStatus.NOT_VULNERABLE,
                      details="Zone transfer refused. Correctly configured.")
    return TestModule("DNSZoneTransfer",
                      "Checks if the DNS server allows unrestricted AXFR.",
                      logic)

def _make_port_scan() -> TestModule:
    RISKY = [21, 23, 445, 3389, 5900]
    def logic(t: Target) -> Result:
        open_ports = [p for p in RISKY if p != t.port and random.random() < 0.3]
        if open_ports:
            return Result(status=VulnStatus.VULNERABLE,
                          details="Risky ports open: " + ", ".join(map(str, open_ports)))
        return Result(status=VulnStatus.NOT_VULNERABLE,
                      details="No unexpected high-risk ports detected.")
    return TestModule("PortScan",
                      "Scans for unexpected high-risk open ports.",
                      logic)

ALL_MODULE_FACTORIES = [
    _make_banner_grab,
    _make_default_creds,
    _make_ssl_audit,
    _make_open_redirect,
    _make_dns_zone_transfer,
    _make_port_scan,
]


# ══════════════════════════════════════════════════════════════════════
# Interactive CLI
# ══════════════════════════════════════════════════════════════════════

WIDTH = 68

def _hr(char="─"):   print(grey(char * WIDTH))
def _title(t: str):  print(f"\n{bold(cyan(t))}"); _hr()
def _ok(msg: str):   print(f"  {green('✓')} {msg}")
def _err(msg: str):  print(f"  {red('✗')} {msg}")
def _info(msg: str): print(f"  {blue('ℹ')} {msg}")

def _prompt(msg: str) -> str:
    try:
        return input(f"\n{cyan('?')} {msg} {grey('›')} ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""

def _pick_target(fw: FrameworkManager) -> Optional[Target]:
    targets = fw.list_targets()
    if not targets:
        _err("No targets registered. Add one first.")
        return None
    print()
    for i, t in enumerate(targets, 1):
        print(f"  {grey(str(i)+'.')} {t}")
    choice = _prompt(f"Select target [1-{len(targets)}]")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(targets):
            return targets[idx]
    except ValueError:
        pass
    _err("Invalid selection.")
    return None

def _pick_module(fw: FrameworkManager) -> Optional[str]:
    modules = fw.module_manager.list_modules()
    if not modules:
        _err("No modules loaded.")
        return None
    print()
    for i, m in enumerate(modules, 1):
        print(f"  {grey(str(i)+'.')} {cyan(m.module_name):<30} {grey(m.description[:40])}")
    choice = _prompt(f"Select module [1-{len(modules)}]")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(modules):
            return modules[idx].module_name
    except ValueError:
        pass
    _err("Invalid selection.")
    return None


# ── menu handlers ────────────────────────────────────────────────────

def menu_list_targets(fw: FrameworkManager) -> None:
    _title("Registered Targets")
    targets = fw.list_targets()
    if not targets:
        _info("No targets yet.")
        return
    for i, t in enumerate(targets, 1):
        print(f"  {grey(str(i)+'.')} {t}")

def menu_add_target(fw: FrameworkManager) -> None:
    _title("Add Target")
    addr = _prompt("Address (IP or hostname)")
    if not addr:
        _err("Address cannot be empty."); return

    port_str = _prompt("Port")
    try:
        port = int(port_str)
    except ValueError:
        _err("Port must be an integer."); return

    print(f"\n  Service types: " +
          "  ".join(f"{i+1}.{s.value}" for i, s in enumerate(ServiceType)))
    svc_str = _prompt("Select service type [1-6]")
    try:
        svc = list(ServiceType)[int(svc_str) - 1]
    except (ValueError, IndexError):
        svc = ServiceType.UNKNOWN

    try:
        t = Target(address=addr, port=port, service_type=svc)
        fw.add_target(t)
        _ok(f"Target added: {t}")
    except ValueError as e:
        _err(str(e))

def menu_remove_target(fw: FrameworkManager) -> None:
    _title("Remove Target")
    t = _pick_target(fw)
    if not t: return
    confirm = _prompt(f"Remove {t.plain()}? [y/N]")
    if confirm.lower() == "y":
        fw.remove_target(t.target_id)
        _ok(f"Target {t.target_id} removed.")
    else:
        _info("Cancelled.")

def menu_list_modules(fw: FrameworkManager) -> None:
    _title("Loaded Modules")
    modules = fw.module_manager.list_modules()
    if not modules:
        _info("No modules loaded.")
        return
    for m in modules:
        print(f"  {cyan(f'{m.module_name:<24}')} {grey(m.description)}")

def menu_run_single(fw: FrameworkManager) -> None:
    _title("Run Single Module")
    t = _pick_target(fw)
    if not t: return
    name = _pick_module(fw)
    if not name: return
    _info(f"Running {cyan(name)} against {t} …")
    try:
        result = fw.run_module_on_target(name, t.target_id)
        print(result.display())
    except KeyError as e:
        _err(str(e))

def menu_run_all_on_target(fw: FrameworkManager) -> None:
    _title("Run All Modules on Target")
    t = _pick_target(fw)
    if not t: return
    _info(f"Running all modules against {t} …\n")
    results = fw.run_all_on_target(t.target_id)
    for r in results:
        print(r.display())
        print()

def menu_run_all_on_all(fw: FrameworkManager) -> None:
    _title("Full Assessment — All Modules × All Targets")
    if not fw.list_targets():
        _err("No targets registered."); return
    confirm = _prompt(f"Run all modules on all {len(fw.list_targets())} targets? [y/N]")
    if confirm.lower() != "y":
        _info("Cancelled."); return
    _info("Starting full assessment …\n")
    for t in fw.list_targets():
        print(f"  {bold(cyan('▶ Target:'))} {t}")
        results = fw.run_all_on_target(t.target_id)
        for r in results:
            print(r.display())
        print()
    _ok("Full assessment complete.")

def menu_view_results(fw: FrameworkManager) -> None:
    _title("View Results")
    print(f"  Filter options:\n"
          f"  {grey('1.')} All results\n"
          f"  {grey('2.')} By target\n"
          f"  {grey('3.')} Vulnerable only\n"
          f"  {grey('4.')} Not Vulnerable only")
    choice = _prompt("Select filter [1-4]")

    if choice == "1":
        results = fw.get_results()
    elif choice == "2":
        t = _pick_target(fw)
        if not t: return
        results = fw.get_results(target_id=t.target_id)
    elif choice == "3":
        results = fw.get_results(status=VulnStatus.VULNERABLE)
    elif choice == "4":
        results = fw.get_results(status=VulnStatus.NOT_VULNERABLE)
    else:
        _err("Invalid choice."); return

    if not results:
        _info("No results match the filter."); return

    print(f"\n  {grey(f'{len(results)} result(s) found')}\n")
    for r in results:
        print(r.display())
        print()

def menu_report(fw: FrameworkManager) -> None:
    _title("Generate Report")
    if not fw.get_results():
        _info("No results yet. Run some tests first."); return
    print()
    print(fw.generate_report())

def menu_clear_results(fw: FrameworkManager) -> None:
    _title("Clear All Results")
    confirm = _prompt("This will delete all stored results. Continue? [y/N]")
    if confirm.lower() == "y":
        fw.clear_results()
        _ok("All results cleared.")
    else:
        _info("Cancelled.")

def menu_load_defaults(fw: FrameworkManager) -> None:
    """Pre-load default targets and modules for quick demonstration."""
    _title("Load Demo Defaults")

    # Modules
    loaded = 0
    for factory in ALL_MODULE_FACTORIES:
        mod = factory()
        try:
            fw.module_manager.load_module(mod)
            loaded += 1
        except ValueError:
            pass
    _ok(f"{loaded} module(s) loaded.")

    # Targets
    defaults = [
        ("192.168.1.10", 80,  ServiceType.HTTP),
        ("192.168.1.20", 21,  ServiceType.FTP),
        ("10.0.0.5",     22,  ServiceType.SSH),
        ("10.0.0.12",    53,  ServiceType.DNS),
        ("203.0.113.5",  25,  ServiceType.SMTP),
    ]
    added = 0
    for addr, port, svc in defaults:
        try:
            fw.add_target(Target(address=addr, port=port, service_type=svc))
            added += 1
        except ValueError:
            pass
    _ok(f"{added} default target(s) added.")


# ══════════════════════════════════════════════════════════════════════
# Main menu loop
# ══════════════════════════════════════════════════════════════════════

MENU = [
    ("Load demo defaults (targets + modules)",  menu_load_defaults),
    ("List targets",                            menu_list_targets),
    ("Add target",                              menu_add_target),
    ("Remove target",                           menu_remove_target),
    ("List modules",                            menu_list_modules),
    ("Run single module on target",             menu_run_single),
    ("Run all modules on one target",           menu_run_all_on_target),
    ("Run full assessment (all × all)",         menu_run_all_on_all),
    ("View results",                            menu_view_results),
    ("Generate report",                         menu_report),
    ("Clear all results",                       menu_clear_results),
    ("Exit",                                    None),
]

def _banner() -> None:
    print(f"\n{bold(cyan('═' * WIDTH))}")
    print(bold(cyan("  BASIC SECURITY TESTING FRAMEWORK  —  Interactive Console")))
    print(grey("  All tests are purely simulated. No real connections are made."))
    print(bold(cyan('═' * WIDTH)))

def main() -> None:
    _banner()
    fw = FrameworkManager(name="InteractiveSecFramework")

    while True:
        # Summary line
        n_targets = len(fw.list_targets())
        n_modules = len(fw.module_manager.list_modules())
        n_results = len(fw.get_results())
        n_vulns   = len(fw.get_results(status=VulnStatus.VULNERABLE))

        print(f"\n  {grey('Targets:')} {white(str(n_targets))}  "
              f"{grey('Modules:')} {white(str(n_modules))}  "
              f"{grey('Results:')} {white(str(n_results))}  "
              f"{grey('Vulns:')} {(red if n_vulns else green)(str(n_vulns))}")
        _hr()

        # Print menu
        for i, (label, _) in enumerate(MENU, 1):
            num = grey(f"{i:>2}.")
            if i == len(MENU):
                print(f"  {num} {red(label)}")
            else:
                print(f"  {num} {label}")

        choice = _prompt(f"Select option [1-{len(MENU)}]")

        try:
            idx = int(choice) - 1
            if not (0 <= idx < len(MENU)):
                raise ValueError
        except ValueError:
            _err(f"Please enter a number between 1 and {len(MENU)}.")
            continue

        label, handler = MENU[idx]

        if handler is None:          # Exit
            print(f"\n{cyan('  Goodbye!')} Framework session ended.\n")
            break

        try:
            handler(fw)
        except KeyboardInterrupt:
            _info("Interrupted.")
        except Exception as exc:
            _err(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()