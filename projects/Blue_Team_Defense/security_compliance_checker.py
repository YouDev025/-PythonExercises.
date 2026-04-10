#!/usr/bin/env python3
"""
Security Compliance Checker
A modular tool for simulating security compliance checks against basic CIS-like policies.
Compatible with Python 3.6+ using only standard library modules.
"""

import os
import sys
import json
import socket
import platform
import datetime
import stat
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict


class Severity(Enum):
    """Enumeration for check severity levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Status(Enum):
    """Enumeration for compliance check status."""
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    WARNING = "Warning"
    ERROR = "Error"
    NOT_APPLICABLE = "N/A"


@dataclass
class ComplianceCheck:
    """Represents a single compliance check result."""
    check_id: str
    category: str
    description: str
    status: Status
    severity: Severity
    recommendation: str
    details: Optional[str] = None
    risk_score: float = 0.0

    def __post_init__(self):
        """Calculate risk score based on severity and status."""
        severity_weights = {
            Severity.CRITICAL: 10.0,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 2.5
        }

        if self.status == Status.NON_COMPLIANT:
            self.risk_score = severity_weights.get(self.severity, 0.0)
        elif self.status == Status.WARNING:
            self.risk_score = severity_weights.get(self.severity, 0.0) * 0.5
        else:
            self.risk_score = 0.0


class SecurityComplianceChecker:
    """
    Main security compliance checker class that orchestrates all compliance checks
    and manages reporting.
    """

    def __init__(self):
        """Initialize the compliance checker with default configuration."""
        self.checks: List[ComplianceCheck] = []
        self.config = self._load_simulated_config()
        self.system_info = self._gather_system_info()

    def _load_simulated_config(self) -> Dict[str, Any]:
        """
        Simulate loading configuration from a file or environment.
        In production, this would read from actual config sources.
        """
        return {
            "password_policy": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special": True,
                "max_age_days": 90,
                "history_count": 5
            },
            "network": {
                "allowed_ports": [22, 80, 443, 3306, 5432],
                "max_open_ports": 10,
                "blocked_ports": [23, 21, 25, 135, 139, 445]
            },
            "file_permissions": {
                "sensitive_paths": ["/etc/passwd", "/etc/shadow", "/etc/ssh/"],
                "max_permission": 0o644,
                "check_world_writable": True
            },
            "system": {
                "debug_mode": False,
                "default_credentials_changed": True,
                "selinux_enforcing": True,
                "firewall_enabled": True
            }
        }

    def _gather_system_info(self) -> Dict[str, str]:
        """Gather basic system information for context."""
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": sys.version,
            "timestamp": datetime.datetime.now().isoformat(),
            "user": os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
        }

    def _simulate_password_policy_check(self) -> ComplianceCheck:
        """
        Check password policy compliance.
        In production, this would read /etc/login.defs or PAM configuration.
        """
        check_id = "PASS-001"
        category = "password_policy"
        description = "Password minimum length requirement"

        # Simulate checking current password policy
        simulated_current_length = 8  # Simulate current setting
        required_length = self.config["password_policy"]["min_length"]

        if simulated_current_length >= required_length:
            status = Status.COMPLIANT
            recommendation = "Password length policy meets requirements"
            details = f"Current min length: {simulated_current_length}, Required: {required_length}"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = f"Increase password minimum length to at least {required_length} characters"
            details = f"Current min length: {simulated_current_length}, Required: {required_length}"
            severity = Severity.HIGH

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def _simulate_password_complexity_check(self) -> ComplianceCheck:
        """Check password complexity requirements."""
        check_id = "PASS-002"
        category = "password_policy"
        description = "Password complexity requirements"

        # Simulate current complexity settings
        simulated_complexity = {
            "uppercase": True,
            "lowercase": True,
            "numbers": False,
            "special": False
        }

        required = self.config["password_policy"]
        missing_requirements = []

        if required["require_uppercase"] and not simulated_complexity["uppercase"]:
            missing_requirements.append("uppercase letters")
        if required["require_lowercase"] and not simulated_complexity["lowercase"]:
            missing_requirements.append("lowercase letters")
        if required["require_numbers"] and not simulated_complexity["numbers"]:
            missing_requirements.append("numbers")
        if required["require_special"] and not simulated_complexity["special"]:
            missing_requirements.append("special characters")

        if not missing_requirements:
            status = Status.COMPLIANT
            recommendation = "Password complexity requirements are properly configured"
            details = "All complexity requirements met"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = f"Enable password complexity requirements: {', '.join(missing_requirements)}"
            details = f"Missing requirements: {', '.join(missing_requirements)}"
            severity = Severity.MEDIUM

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def _simulate_password_age_check(self) -> ComplianceCheck:
        """Check password aging policy."""
        check_id = "PASS-003"
        category = "password_policy"
        description = "Password maximum age policy"

        # Simulate current password aging setting
        simulated_max_age = 180  # days
        required_max_age = self.config["password_policy"]["max_age_days"]

        if simulated_max_age <= required_max_age:
            status = Status.COMPLIANT
            recommendation = "Password aging policy is properly configured"
            details = f"Current max age: {simulated_max_age} days, Maximum allowed: {required_max_age} days"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = f"Reduce password maximum age to {required_max_age} days or less"
            details = f"Current max age: {simulated_max_age} days, Maximum allowed: {required_max_age} days"
            severity = Severity.MEDIUM

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def _simulate_open_ports_check(self) -> ComplianceCheck:
        """Check for unnecessary open ports."""
        check_id = "NET-001"
        category = "network"
        description = "Unnecessary open network ports"

        # Simulate currently open ports
        simulated_open_ports = [22, 80, 443, 8080, 3306, 5432, 6379, 27017]
        allowed_ports = self.config["network"]["allowed_ports"]

        unexpected_ports = [port for port in simulated_open_ports if port not in allowed_ports]

        if not unexpected_ports:
            status = Status.COMPLIANT
            recommendation = "No unexpected open ports detected"
            details = f"Open ports: {simulated_open_ports}"
            severity = Severity.LOW
        else:
            # Check for high-risk ports
            high_risk_ports = [23, 21, 3389, 5900]
            has_high_risk = any(port in high_risk_ports for port in unexpected_ports)

            status = Status.NON_COMPLIANT
            recommendation = f"Close or restrict access to unexpected ports: {unexpected_ports}"
            details = f"Unexpected open ports: {unexpected_ports}"
            severity = Severity.HIGH if has_high_risk else Severity.MEDIUM

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def _simulate_firewall_check(self) -> ComplianceCheck:
        """Check if firewall is enabled."""
        check_id = "NET-002"
        category = "network"
        description = "Firewall status check"

        # Simulate firewall status
        firewall_enabled = True

        if firewall_enabled:
            status = Status.COMPLIANT
            recommendation = "Firewall is properly enabled"
            details = "Firewall is active and enforcing rules"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = "Enable the system firewall to protect against unauthorized access"
            details = "Firewall is currently disabled"
            severity = Severity.CRITICAL

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def _simulate_file_permissions_check(self) -> List[ComplianceCheck]:
        """Check for insecure file permissions."""
        checks = []

        # Check for world-writable files
        check_id = "FILE-001"
        category = "files"
        description = "World-writable files and directories"

        # Simulate scanning for world-writable files
        simulated_world_writable = [
            "/tmp/public_script.sh",
            "/var/www/html/config.php",
            "/home/user/shared_data/"
        ]

        if not simulated_world_writable:
            status = Status.COMPLIANT
            recommendation = "No world-writable files or directories found"
            details = "All files have appropriate permissions"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = "Review and restrict permissions on world-writable files"
            details = f"World-writable paths found: {simulated_world_writable}"
            severity = Severity.HIGH

        checks.append(ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        ))

        # Check sensitive file permissions
        check_id = "FILE-002"
        category = "files"
        description = "Sensitive file permissions"

        # Simulate checking /etc/passwd permissions
        simulated_passwd_perms = "644"

        if simulated_passwd_perms in ["644", "640", "600"]:
            status = Status.COMPLIANT
            recommendation = "Sensitive files have appropriate permissions"
            details = "/etc/passwd permissions are properly restricted"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = "Restrict permissions on /etc/passwd to 644 or more restrictive"
            details = f"Current permissions: {simulated_passwd_perms}"
            severity = Severity.HIGH

        checks.append(ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        ))

        return checks

    def _simulate_debug_mode_check(self) -> ComplianceCheck:
        """Check if debug mode is enabled in production."""
        check_id = "SYS-001"
        category = "system"
        description = "Debug mode in production environment"

        # Simulate checking debug mode status
        debug_enabled = False

        if not debug_enabled:
            status = Status.COMPLIANT
            recommendation = "Debug mode is properly disabled"
            details = "Application is running in production mode"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = "Disable debug mode in production environments"
            details = "Debug mode is currently enabled, exposing sensitive information"
            severity = Severity.CRITICAL

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def _simulate_default_credentials_check(self) -> ComplianceCheck:
        """Check for default credentials in use."""
        check_id = "SYS-002"
        category = "system"
        description = "Default credentials usage"

        # Simulate checking for default credentials
        default_creds_changed = True

        if default_creds_changed:
            status = Status.COMPLIANT
            recommendation = "Default credentials have been changed"
            details = "No default credentials detected in use"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = "Change all default credentials immediately"
            details = "Default credentials found in use - critical security risk"
            severity = Severity.CRITICAL

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def _simulate_selinux_check(self) -> ComplianceCheck:
        """Check SELinux/AppArmor status."""
        check_id = "SYS-003"
        category = "system"
        description = "Mandatory Access Control (SELinux/AppArmor) status"

        # Simulate SELinux status
        selinux_enforcing = False  # Simulate disabled SELinux

        if selinux_enforcing:
            status = Status.COMPLIANT
            recommendation = "SELinux is properly configured and enforcing"
            details = "Mandatory Access Control is active"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = "Enable SELinux or AppArmor in enforcing mode"
            details = "Mandatory Access Control is currently disabled"
            severity = Severity.HIGH

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def _simulate_ssh_config_check(self) -> ComplianceCheck:
        """Check SSH server configuration."""
        check_id = "SYS-004"
        category = "system"
        description = "SSH server security configuration"

        # Simulate SSH configuration check
        root_login_disabled = True
        password_auth_disabled = False  # Simulate password auth still enabled

        issues = []
        if not root_login_disabled:
            issues.append("root login allowed")
        if not password_auth_disabled:
            issues.append("password authentication enabled (key-based recommended)")

        if not issues:
            status = Status.COMPLIANT
            recommendation = "SSH configuration follows security best practices"
            details = "Root login disabled, key-based authentication enforced"
            severity = Severity.LOW
        else:
            status = Status.NON_COMPLIANT
            recommendation = f"Secure SSH configuration: {', '.join(issues)}"
            details = f"Configuration issues: {', '.join(issues)}"
            severity = Severity.HIGH

        return ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            recommendation=recommendation,
            details=details
        )

    def run_all_checks(self) -> None:
        """Execute all compliance checks and store results."""
        self.checks = []

        # Password policy checks
        self.checks.append(self._simulate_password_policy_check())
        self.checks.append(self._simulate_password_complexity_check())
        self.checks.append(self._simulate_password_age_check())

        # Network checks
        self.checks.append(self._simulate_open_ports_check())
        self.checks.append(self._simulate_firewall_check())

        # File permission checks
        self.checks.extend(self._simulate_file_permissions_check())

        # System configuration checks
        self.checks.append(self._simulate_debug_mode_check())
        self.checks.append(self._simulate_default_credentials_check())
        self.checks.append(self._simulate_selinux_check())
        self.checks.append(self._simulate_ssh_config_check())

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate compliance statistics from check results."""
        total = len(self.checks)
        compliant = sum(1 for check in self.checks if check.status == Status.COMPLIANT)
        non_compliant = sum(1 for check in self.checks if check.status == Status.NON_COMPLIANT)
        warning = sum(1 for check in self.checks if check.status == Status.WARNING)
        error = sum(1 for check in self.checks if check.status == Status.ERROR)
        na = sum(1 for check in self.checks if check.status == Status.NOT_APPLICABLE)

        high_risk = sum(1 for check in self.checks
                        if check.status == Status.NON_COMPLIANT
                        and check.severity in [Severity.HIGH, Severity.CRITICAL])

        critical_risk = sum(1 for check in self.checks
                            if check.status == Status.NON_COMPLIANT
                            and check.severity == Severity.CRITICAL)

        total_risk_score = sum(check.risk_score for check in self.checks)
        max_possible_score = sum(10.0 for check in self.checks)
        compliance_score = max(0,
                               100 - (total_risk_score / max_possible_score * 100)) if max_possible_score > 0 else 100

        return {
            "total_checks": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "warning": warning,
            "error": error,
            "not_applicable": na,
            "high_risk_issues": high_risk,
            "critical_risk_issues": critical_risk,
            "total_risk_score": round(total_risk_score, 2),
            "compliance_score": round(compliance_score, 2),
            "pass_rate": round((compliant / total * 100) if total > 0 else 0, 2)
        }

    def display_results(self) -> None:
        """Display compliance check results in a formatted table."""
        if not self.checks:
            print("\n[!] No compliance checks have been run yet. Please run a scan first.")
            return

        print("\n" + "=" * 120)
        print("SECURITY COMPLIANCE CHECK REPORT")
        print("=" * 120)
        print(f"System: {self.system_info['hostname']} ({self.system_info['platform']})")
        print(f"Scan Time: {self.system_info['timestamp']}")
        print("=" * 120)

        # Group checks by category
        checks_by_category = defaultdict(list)
        for check in self.checks:
            checks_by_category[check.category].append(check)

        for category, checks in checks_by_category.items():
            print(f"\n📁 Category: {category.upper().replace('_', ' ')}")
            print("-" * 100)
            print(f"{'Check ID':<12} {'Status':<15} {'Severity':<10} {'Description':<40} {'Risk Score':<10}")
            print("-" * 100)

            for check in checks:
                status_icon = "✓" if check.status == Status.COMPLIANT else "✗" if check.status == Status.NON_COMPLIANT else "⚠" if check.status == Status.WARNING else "?"
                status_display = f"{status_icon} {check.status.value}"

                severity_color = ""
                if check.severity == Severity.CRITICAL:
                    severity_display = f"❗ {check.severity.value}"
                elif check.severity == Severity.HIGH:
                    severity_display = f"🔴 {check.severity.value}"
                elif check.severity == Severity.MEDIUM:
                    severity_display = f"🟡 {check.severity.value}"
                else:
                    severity_display = f"🟢 {check.severity.value}"

                print(
                    f"{check.check_id:<12} {status_display:<15} {severity_display:<10} {check.description[:37]:<40} {check.risk_score:<10.2f}")

                if check.details and check.status != Status.COMPLIANT:
                    print(f"{'':12} {'→ Details: ' + check.details}")

                if check.status == Status.NON_COMPLIANT:
                    print(f"{'':12} {'→ Fix: ' + check.recommendation}")

        # Display statistics
        stats = self.get_statistics()
        print("\n" + "=" * 120)
        print("COMPLIANCE SUMMARY")
        print("=" * 120)
        print(f"Total Checks:        {stats['total_checks']}")
        print(f"✓ Compliant:         {stats['compliant']} ({stats['pass_rate']:.1f}%)")
        print(f"✗ Non-Compliant:     {stats['non_compliant']}")
        print(f"⚠ Warnings:          {stats['warning']}")
        print(f"❌ Errors:            {stats['error']}")
        print(f"🔴 High Risk Issues:  {stats['high_risk_issues']}")
        print(f"❗ Critical Issues:   {stats['critical_risk_issues']}")
        print(f"📊 Compliance Score:  {stats['compliance_score']:.1f}/100")
        print(f"🎯 Risk Score:        {stats['total_risk_score']:.2f}")
        print("=" * 120)

        # Highlight critical findings
        critical_findings = [c for c in self.checks
                             if c.status == Status.NON_COMPLIANT
                             and c.severity == Severity.CRITICAL]

        if critical_findings:
            print("\n⚠️  CRITICAL SECURITY FINDINGS - Immediate Action Required:")
            print("-" * 60)
            for finding in critical_findings:
                print(f"  • {finding.check_id}: {finding.description}")
                print(f"    → {finding.recommendation}")

    def save_report_to_file(self, filename: str = "compliance_report.txt") -> None:
        """Save the compliance report to a text file."""
        if not self.checks:
            print("\n[!] No compliance checks have been run yet.")
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 120 + "\n")
                f.write("SECURITY COMPLIANCE CHECK REPORT\n")
                f.write("=" * 120 + "\n")
                f.write(f"System: {self.system_info['hostname']} ({self.system_info['platform']})\n")
                f.write(f"Scan Time: {self.system_info['timestamp']}\n")
                f.write(f"Generated by: {self.system_info['user']}\n")
                f.write("=" * 120 + "\n\n")

                # Write detailed findings
                for check in self.checks:
                    f.write(f"[{check.check_id}] {check.description}\n")
                    f.write(f"Category: {check.category}\n")
                    f.write(f"Status: {check.status.value}\n")
                    f.write(f"Severity: {check.severity.value}\n")
                    f.write(f"Risk Score: {check.risk_score:.2f}\n")
                    if check.details:
                        f.write(f"Details: {check.details}\n")
                    if check.status == Status.NON_COMPLIANT:
                        f.write(f"Recommendation: {check.recommendation}\n")
                    f.write("-" * 80 + "\n")

                # Write summary statistics
                stats = self.get_statistics()
                f.write("\n" + "=" * 120 + "\n")
                f.write("COMPLIANCE SUMMARY STATISTICS\n")
                f.write("=" * 120 + "\n")
                for key, value in stats.items():
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")

                # Write non-compliant items list
                f.write("\n" + "=" * 120 + "\n")
                f.write("NON-COMPLIANT ITEMS\n")
                f.write("=" * 120 + "\n")
                non_compliant = [c for c in self.checks if c.status == Status.NON_COMPLIANT]
                if non_compliant:
                    for check in sorted(non_compliant, key=lambda x: x.severity.value, reverse=True):
                        f.write(f"[{check.severity.value}] {check.check_id}: {check.description}\n")
                        f.write(f"    → {check.recommendation}\n")
                else:
                    f.write("No non-compliant items found.\n")

            print(f"\n[✓] Report saved successfully to: {filename}")

        except Exception as e:
            print(f"\n[✗] Error saving report: {e}")

    def export_to_json(self, filename: str = "compliance_report.json") -> None:
        """Export compliance results to JSON format."""
        if not self.checks:
            print("\n[!] No compliance checks have been run yet.")
            return

        try:
            report_data = {
                "metadata": {
                    "scan_timestamp": self.system_info['timestamp'],
                    "system_info": self.system_info,
                    "checker_version": "1.0.0"
                },
                "statistics": self.get_statistics(),
                "checks": []
            }

            for check in self.checks:
                check_dict = {
                    "check_id": check.check_id,
                    "category": check.category,
                    "description": check.description,
                    "status": check.status.value,
                    "severity": check.severity.value,
                    "recommendation": check.recommendation,
                    "details": check.details,
                    "risk_score": check.risk_score
                }
                report_data["checks"].append(check_dict)

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            print(f"\n[✓] JSON report exported successfully to: {filename}")

        except Exception as e:
            print(f"\n[✗] Error exporting JSON report: {e}")

    def show_menu(self) -> None:
        """Display interactive CLI menu."""
        while True:
            print("\n" + "=" * 60)
            print("SECURITY COMPLIANCE CHECKER - MAIN MENU")
            print("=" * 60)
            print("1. Run Full Compliance Scan")
            print("2. View Current Report")
            print("3. Save Report to Text File")
            print("4. Export Report to JSON")
            print("5. Show Compliance Statistics")
            print("6. Exit")
            print("=" * 60)

            choice = input("\nEnter your choice (1-6): ").strip()

            if choice == "1":
                print("\n[→] Running compliance scan...")
                self.run_all_checks()
                print("[✓] Scan completed successfully!")
                self.display_results()

            elif choice == "2":
                self.display_results()

            elif choice == "3":
                if not self.checks:
                    print("\n[!] No scan results available. Please run a scan first.")
                else:
                    filename = input("Enter filename (default: compliance_report.txt): ").strip()
                    if not filename:
                        filename = "compliance_report.txt"
                    self.save_report_to_file(filename)

            elif choice == "4":
                if not self.checks:
                    print("\n[!] No scan results available. Please run a scan first.")
                else:
                    filename = input("Enter filename (default: compliance_report.json): ").strip()
                    if not filename:
                        filename = "compliance_report.json"
                    self.export_to_json(filename)

            elif choice == "5":
                if not self.checks:
                    print("\n[!] No scan results available. Please run a scan first.")
                else:
                    stats = self.get_statistics()
                    print("\n" + "=" * 60)
                    print("COMPLIANCE STATISTICS")
                    print("=" * 60)
                    for key, value in stats.items():
                        print(f"{key.replace('_', ' ').title():25}: {value}")

            elif choice == "6":
                print("\n[✓] Exiting Security Compliance Checker. Goodbye!")
                sys.exit(0)

            else:
                print("\n[!] Invalid choice. Please enter a number between 1 and 6.")


def main():
    """Main entry point for the Security Compliance Checker."""
    try:
        # Check Python version compatibility
        if sys.version_info < (3, 6):
            print("Error: This script requires Python 3.6 or higher")
            sys.exit(1)

        # Initialize and run the compliance checker
        checker = SecurityComplianceChecker()

        # Check for command line arguments
        if len(sys.argv) > 1:
            arg = sys.argv[1].lower()
            if arg in ["--scan", "-s"]:
                print("[→] Running automated compliance scan...")
                checker.run_all_checks()
                checker.display_results()
                checker.save_report_to_file()
                checker.export_to_json()
            elif arg in ["--help", "-h"]:
                print("\nSecurity Compliance Checker Usage:")
                print("  python security_compliance_checker.py          - Interactive mode")
                print("  python security_compliance_checker.py --scan   - Automated scan and report")
                print("  python security_compliance_checker.py --help   - Show this help message")
            else:
                print(f"Unknown argument: {arg}")
                print("Use --help for usage information")
        else:
            # Interactive mode
            print("\n🔒 Security Compliance Checker v1.0.0")
            print(f"System: {checker.system_info['hostname']}")
            print(f"Platform: {checker.system_info['platform']}")
            checker.show_menu()

    except KeyboardInterrupt:
        print("\n\n[!] Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[✗] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()