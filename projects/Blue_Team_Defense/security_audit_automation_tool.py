#!/usr/bin/env python3
"""
Security Audit Automation Tool
Performs basic security checks on a local system and generates audit reports.
Compatible with Python 3.6+ and runs on Windows, Linux, and macOS.
"""

import os
import sys
import socket
import subprocess
import hashlib
import platform
import json
import datetime
import stat
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

COMMON_PORTS = [21, 22, 23, 80, 443, 3306, 3389, 5432, 5900, 8080]
PORT_SERVICE_MAP = {
    21: "FTP", 22: "SSH", 23: "Telnet", 80: "HTTP", 443: "HTTPS",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 8080: "HTTP-Alt"
}

SUSPICIOUS_PROCESSES = [
    "nc.exe", "netcat", "nmap", "hydra", "john", "sqlmap", "mimikatz",
    "meterpreter", "reverse_shell", "backdoor", "keylogger"
]

SENSITIVE_FILES = [
    "passwd", "shadow", "config.ini", "config.json", ".env", "id_rsa",
    "web.config", "appsettings.json", "credentials", "secret"
]

HIGH_RISK_PERMISSIONS = [0o777, 0o666, 0o755]  # Permissions that are too permissive


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_timestamp() -> str:
    """Return current timestamp in YYYYMMDD_HHMMSS format."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def get_report_filename(format_type: str = "txt") -> str:
    """Generate a timestamped report filename."""
    if format_type == "json":
        return f"audit_report_{get_timestamp()}.json"
    return f"audit_report_{get_timestamp()}.txt"


def print_header(title: str) -> None:
    """Print a formatted section header to console."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_finding(severity: str, message: str) -> None:
    """Print a finding with color-coded severity."""
    severity_upper = severity.upper()
    if severity_upper == "HIGH":
        print(f"  [🔴 {severity_upper}] {message}")
    elif severity_upper == "MEDIUM":
        print(f"  [🟡 {severity_upper}] {message}")
    elif severity_upper == "LOW":
        print(f"  [🟢 {severity_upper}] {message}")
    else:
        print(f"  [ℹ️ {severity_upper}] {message}")


# ============================================================================
# AUDIT CHECK FUNCTIONS
# ============================================================================

def check_system_info() -> Dict:
    """
    Collect system information including OS, hostname, and IP addresses.
    Returns dictionary with findings and recommendations.
    """
    findings = []
    recommendations = []

    # OS Information
    os_info = f"{platform.system()} {platform.release()} {platform.version()}"
    hostname = socket.gethostname()

    # IP Addresses
    ip_addresses = []
    try:
        host_ip = socket.gethostbyname(hostname)
        ip_addresses.append(host_ip)
    except socket.gaierror:
        ip_addresses.append("Unable to resolve")

    # Get all IP addresses (more comprehensive)
    try:
        if platform.system() != "Windows":
            # Linux/macOS
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
            if result.stdout:
                ips = result.stdout.strip().split()
                ip_addresses.extend([ip for ip in ips if ip not in ip_addresses])
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    findings.append({
        "category": "System Information",
        "severity": "INFO",
        "message": f"OS: {os_info}",
        "detail": f"Hostname: {hostname}\nIP Addresses: {', '.join(ip_addresses)}"
    })

    return {
        "os_info": os_info,
        "hostname": hostname,
        "ip_addresses": ip_addresses,
        "findings": findings,
        "recommendations": recommendations
    }


def check_open_ports(timeout: float = 0.5) -> Dict:
    """
    Scan common ports to detect open services.
    Returns dictionary with findings and recommendations.
    """
    findings = []
    recommendations = []
    open_ports = []

    print("  Scanning ports...")

    for port in COMMON_PORTS:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            service = PORT_SERVICE_MAP.get(port, "Unknown")
            open_ports.append((port, service))
            severity = "HIGH" if port in [23, 21] else "MEDIUM"
            findings.append({
                "category": "Open Ports",
                "severity": severity,
                "message": f"Port {port} ({service}) is open",
                "detail": f"Service listening on port {port}"
            })
        sock.close()

    if open_ports:
        recommendations.append(
            "Close unnecessary ports and restrict access to essential services. "
            "Use firewalls to limit exposure."
        )
    else:
        findings.append({
            "category": "Open Ports",
            "severity": "INFO",
            "message": "No common ports found open",
            "detail": "Common service ports are closed"
        })

    return {
        "open_ports": open_ports,
        "findings": findings,
        "recommendations": recommendations
    }


def calculate_file_hash(filepath: Path, algorithm: str = "sha256") -> Optional[str]:
    """
    Calculate hash of a file for integrity checking.
    Returns hash string or None if error.
    """
    try:
        hasher = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (IOError, OSError, PermissionError):
        return None


def check_file_integrity(directory: str = None, max_files: int = 50) -> Dict:
    """
    Scan a directory and generate file hashes for integrity baseline.
    Returns dictionary with findings and recommendations.
    """
    findings = []
    recommendations = []
    file_hashes = {}

    if directory is None:
        directory = os.getcwd()

    if not os.path.exists(directory):
        findings.append({
            "category": "File Integrity",
            "severity": "LOW",
            "message": f"Directory '{directory}' does not exist",
            "detail": "Cannot perform file integrity check"
        })
        return {"file_hashes": {}, "findings": findings, "recommendations": recommendations}

    print(f"  Scanning directory: {directory}")
    files_processed = 0

    try:
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and system directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]

            for file in files[:max_files - files_processed]:
                filepath = Path(root) / file
                if filepath.is_file() and os.path.getsize(filepath) < 10 * 1024 * 1024:  # Skip files >10MB
                    file_hash = calculate_file_hash(filepath)
                    if file_hash:
                        file_hashes[str(filepath)] = file_hash
                        files_processed += 1

                        # Check for sensitive files
                        if any(sensitive in file.lower() for sensitive in SENSITIVE_FILES):
                            findings.append({
                                "category": "Sensitive Files",
                                "severity": "MEDIUM",
                                "message": f"Sensitive file found: {filepath}",
                                "detail": "File may contain credentials or configuration data"
                            })

                    if files_processed >= max_files:
                        break

            if files_processed >= max_files:
                break

    except PermissionError:
        findings.append({
            "category": "File Integrity",
            "severity": "LOW",
            "message": "Permission denied accessing some directories",
            "detail": "Run with elevated privileges for full scan"
        })

    if file_hashes:
        recommendations.append(
            "Establish a baseline of file hashes and regularly verify integrity "
            "to detect unauthorized changes."
        )

    findings.append({
        "category": "File Integrity",
        "severity": "INFO",
        "message": f"Processed {len(file_hashes)} files",
        "detail": "Hash baseline created for integrity monitoring"
    })

    return {
        "file_hashes": file_hashes,
        "findings": findings,
        "recommendations": recommendations
    }


def check_running_processes() -> Dict:
    """
    List running processes and highlight suspicious ones.
    Returns dictionary with findings and recommendations.
    """
    findings = []
    recommendations = []
    suspicious_procs = []
    all_processes = []

    try:
        if platform.system() == "Windows":
            result = subprocess.run(['tasklist'], capture_output=True, text=True, timeout=10)
            lines = result.stdout.splitlines()
            for line in lines[3:]:  # Skip header lines
                if line.strip():
                    parts = line.split()
                    if parts:
                        proc_name = parts[0].lower()
                        all_processes.append(proc_name)
                        if any(susp in proc_name for susp in SUSPICIOUS_PROCESSES):
                            suspicious_procs.append(proc_name)
                            findings.append({
                                "category": "Processes",
                                "severity": "HIGH",
                                "message": f"Suspicious process detected: {proc_name}",
                                "detail": "Process name matches known security tools or malware patterns"
                            })
        else:
            # Linux/macOS
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
            lines = result.stdout.splitlines()
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) > 10:
                    proc_name = parts[10].lower() if len(parts) > 10 else ""
                    all_processes.append(proc_name)
                    if any(susp in proc_name for susp in SUSPICIOUS_PROCESSES):
                        suspicious_procs.append(proc_name)
                        findings.append({
                            "category": "Processes",
                            "severity": "HIGH",
                            "message": f"Suspicious process detected: {proc_name}",
                            "detail": "Process name matches known security tools or malware patterns"
                        })
    except (subprocess.SubprocessError, FileNotFoundError, IndexError) as e:
        findings.append({
            "category": "Processes",
            "severity": "LOW",
            "message": f"Could not list processes: {str(e)}",
            "detail": "Permission or system call error"
        })

    if suspicious_procs:
        recommendations.append(
            "Investigate suspicious processes immediately. Run antivirus scan and "
            "verify process legitimacy."
        )
    else:
        findings.append({
            "category": "Processes",
            "severity": "INFO",
            "message": f"No known suspicious processes found among {len(all_processes)} processes",
            "detail": "Running processes appear normal"
        })

    return {
        "suspicious_processes": suspicious_procs,
        "total_processes": len(all_processes),
        "findings": findings,
        "recommendations": recommendations
    }


def check_file_permissions(directory: str = None, max_files: int = 100) -> Dict:
    """
    Check for weak file permissions.
    Returns dictionary with findings and recommendations.
    """
    findings = []
    recommendations = []
    risky_files = []

    if directory is None:
        directory = os.getcwd()

    print(f"  Checking permissions in: {directory}")

    try:
        for root, dirs, files in os.walk(directory):
            # Skip system directories
            if any(skip in root for skip in ['/proc', '/sys', '/dev', 'C:\\Windows', '/System']):
                continue

            for name in files + dirs:
                path = Path(root) / name
                try:
                    mode = os.stat(path).st_mode
                    perm = stat.S_IMODE(mode)

                    if perm in HIGH_RISK_PERMISSIONS or perm & 0o002:  # World writable
                        risky_files.append(str(path))
                        severity = "HIGH" if perm in [0o777, 0o666] else "MEDIUM"
                        findings.append({
                            "category": "File Permissions",
                            "severity": severity,
                            "message": f"Weak permissions ({oct(perm)}) on: {path}",
                            "detail": f"File is {oct(perm)} which allows unauthorized access"
                        })

                        if len(risky_files) >= max_files:
                            break
                except (PermissionError, OSError):
                    continue

            if len(risky_files) >= max_files:
                break

    except Exception as e:
        findings.append({
            "category": "File Permissions",
            "severity": "LOW",
            "message": f"Permission check error: {str(e)}",
            "detail": "Some files/directories could not be accessed"
        })

    if risky_files:
        recommendations.append(
            "Review and fix weak file permissions. Use 'chmod 750' or similar "
            "restrictive permissions for sensitive files."
        )
    else:
        findings.append({
            "category": "File Permissions",
            "severity": "INFO",
            "message": "No weak file permissions detected",
            "detail": "Files and directories have appropriate permissions"
        })

    return {
        "risky_files": risky_files[:max_files],
        "findings": findings,
        "recommendations": recommendations
    }


# ============================================================================
# RISK SCORING
# ============================================================================

def calculate_risk_score(findings: List[Dict]) -> Tuple[int, str]:
    """
    Calculate overall risk score based on findings.
    Returns score (0-100) and risk level.
    """
    weights = {"HIGH": 10, "MEDIUM": 5, "LOW": 2, "INFO": 0}
    total_score = sum(weights.get(finding["severity"], 0) for finding in findings)

    # Cap at 100
    score = min(total_score, 100)

    if score >= 70:
        risk_level = "CRITICAL"
    elif score >= 40:
        risk_level = "HIGH"
    elif score >= 20:
        risk_level = "MEDIUM"
    elif score > 0:
        risk_level = "LOW"
    else:
        risk_level = "NONE"

    return score, risk_level


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_txt_report(all_results: Dict, timestamp: str, risk_score: int, risk_level: str) -> str:
    """Generate text format report."""
    report = []
    report.append("=" * 80)
    report.append("SECURITY AUDIT REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {timestamp}")
    report.append(f"Risk Score: {risk_score}/100 ({risk_level})")
    report.append("=" * 80)
    report.append("")

    for category, data in all_results.items():
        report.append(f"\n{'=' * 80}")
        report.append(f"[{category.upper()}]")
        report.append(f"{'=' * 80}")

        # Findings
        if data.get("findings"):
            report.append("\nFINDINGS:")
            for finding in data["findings"]:
                report.append(f"  [{finding['severity']}] {finding['message']}")
                if finding.get("detail"):
                    report.append(f"    Details: {finding['detail']}")

        # Recommendations
        if data.get("recommendations"):
            report.append("\nRECOMMENDATIONS:")
            for rec in data["recommendations"]:
                report.append(f"  • {rec}")

        report.append("")

    # Summary section
    report.append("\n" + "=" * 80)
    report.append("SUMMARY")
    report.append("=" * 80)

    all_findings = []
    for data in all_results.values():
        all_findings.extend(data.get("findings", []))

    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for finding in all_findings:
        severity_counts[finding["severity"]] += 1

    report.append(f"Total Findings: {len(all_findings)}")
    report.append(f"  - HIGH: {severity_counts['HIGH']}")
    report.append(f"  - MEDIUM: {severity_counts['MEDIUM']}")
    report.append(f"  - LOW: {severity_counts['LOW']}")
    report.append(f"  - INFO: {severity_counts['INFO']}")

    report.append("\nRECOMMENDATIONS SUMMARY:")
    report.append("  1. Review all HIGH severity findings immediately")
    report.append("  2. Implement fixes for MEDIUM severity issues")
    report.append("  3. Document and monitor LOW severity items")
    report.append("  4. Run regular security audits (weekly recommended)")

    report.append("\n" + "=" * 80)
    report.append("End of Report")
    report.append("=" * 80)

    return "\n".join(report)


def generate_json_report(all_results: Dict, timestamp: str, risk_score: int, risk_level: str) -> str:
    """Generate JSON format report."""
    report_data = {
        "report_metadata": {
            "timestamp": timestamp,
            "tool": "Security Audit Automation Tool",
            "version": "1.0.0",
            "risk_score": risk_score,
            "risk_level": risk_level
        },
        "audit_results": all_results
    }
    return json.dumps(report_data, indent=2, default=str)


def save_report(report_content: str, filename: str) -> bool:
    """Save report to file and return success status."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        return True
    except IOError as e:
        print(f"Error saving report: {e}")
        return False


# ============================================================================
# MAIN AUDIT FUNCTION
# ============================================================================

def run_full_audit(directory_to_scan: str = None) -> Dict:
    """
    Execute all security audit checks.
    Returns dictionary with all results.
    """
    print_header("RUNNING FULL SECURITY AUDIT")

    results = {}

    # System Information
    print("\n[1/5] Collecting system information...")
    results["system_info"] = check_system_info()

    # Open Ports
    print("\n[2/5] Checking open ports...")
    results["open_ports"] = check_open_ports()

    # Running Processes
    print("\n[3/5] Analyzing running processes...")
    results["processes"] = check_running_processes()

    # File Integrity
    print("\n[4/5] Scanning files for integrity baseline...")
    results["file_integrity"] = check_file_integrity(directory_to_scan)

    # File Permissions
    print("\n[5/5] Checking file permissions...")
    results["file_permissions"] = check_file_permissions(directory_to_scan)

    return results


# ============================================================================
# CLI MENU SYSTEM
# ============================================================================

def display_menu() -> None:
    """Display the main menu."""
    print("\n" + "=" * 50)
    print("  SECURITY AUDIT AUTOMATION TOOL")
    print("=" * 50)
    print("  1. Run Full Audit")
    print("  2. Run Specific Checks")
    print("  3. About")
    print("  4. Exit")
    print("=" * 50)


def display_specific_checks_menu() -> None:
    """Display menu for specific checks."""
    print("\n" + "-" * 40)
    print("  Select checks to run:")
    print("-" * 40)
    print("  1. System Information")
    print("  2. Open Ports")
    print("  3. Running Processes")
    print("  4. File Integrity (current directory)")
    print("  5. File Permissions (current directory)")
    print("  6. Run All Selected")
    print("  7. Back to Main Menu")
    print("-" * 40)


def run_specific_checks() -> Dict:
    """
    Interactive menu for running specific audit checks.
    Returns dictionary with results.
    """
    results = {}
    checks_to_run = []

    while True:
        display_specific_checks_menu()
        choice = input("\nYour choice (1-7): ").strip()

        if choice == '1':
            checks_to_run.append(('system_info', 'System Information'))
            print("✓ Added: System Information")
        elif choice == '2':
            checks_to_run.append(('open_ports', 'Open Ports'))
            print("✓ Added: Open Ports")
        elif choice == '3':
            checks_to_run.append(('processes', 'Running Processes'))
            print("✓ Added: Running Processes")
        elif choice == '4':
            checks_to_run.append(('file_integrity', 'File Integrity'))
            print("✓ Added: File Integrity")
        elif choice == '5':
            checks_to_run.append(('file_permissions', 'File Permissions'))
            print("✓ Added: File Permissions")
        elif choice == '6':
            if not checks_to_run:
                print("❌ No checks selected. Please select at least one check.")
                continue

            print_header("RUNNING SELECTED CHECKS")
            for check_key, check_name in checks_to_run:
                print(f"\nRunning: {check_name}...")
                if check_key == 'system_info':
                    results[check_key] = check_system_info()
                elif check_key == 'open_ports':
                    results[check_key] = check_open_ports()
                elif check_key == 'processes':
                    results[check_key] = check_running_processes()
                elif check_key == 'file_integrity':
                    results[check_key] = check_file_integrity()
                elif check_key == 'file_permissions':
                    results[check_key] = check_file_permissions()

            print("\n✅ Selected checks completed!")
            return results

        elif choice == '7':
            print("Returning to main menu...")
            return None
        else:
            print("❌ Invalid choice. Please try again.")


def about() -> None:
    """Display about information."""
    print_header("ABOUT")
    print("Security Audit Automation Tool v1.0")
    print("\nPurpose:")
    print("  Automates basic security checks on local systems")
    print("  to identify potential vulnerabilities and misconfigurations.")
    print("\nFeatures:")
    print("  • System information collection")
    print("  • Open port scanning")
    print("  • Process analysis and suspicious process detection")
    print("  • File integrity monitoring (hash baseline)")
    print("  • File permission analysis")
    print("  • Risk scoring")
    print("  • Multiple report formats (TXT/JSON)")
    print("\nCompatibility:")
    print("  • Windows, Linux, macOS")
    print("  • Python 3.6+")
    print("\nSecurity Notice:")
    print("  This tool performs READ-ONLY operations only.")
    print("  No modifications are made to the system.")
    input("\nPress Enter to continue...")


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """Main program entry point."""
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == '1':
            # Run full audit
            results = run_full_audit()

            # Collect all findings for risk scoring
            all_findings = []
            for data in results.values():
                all_findings.extend(data.get("findings", []))

            # Calculate risk score
            risk_score, risk_level = calculate_risk_score(all_findings)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Generate and save reports
            print_header("GENERATING REPORTS")

            # TXT Report
            txt_report = generate_txt_report(results, timestamp, risk_score, risk_level)
            txt_filename = get_report_filename("txt")
            if save_report(txt_report, txt_filename):
                print(f"✅ Text report saved: {txt_filename}")

            # JSON Report
            json_report = generate_json_report(results, timestamp, risk_score, risk_level)
            json_filename = get_report_filename("json")
            if save_report(json_report, json_filename):
                print(f"✅ JSON report saved: {json_filename}")

            # Display brief summary
            print_header("AUDIT COMPLETED")
            print(f"Risk Score: {risk_score}/100 ({risk_level})")
            print(f"Total Findings: {len(all_findings)}")
            print("\nHigh severity findings require immediate attention!")

            input("\nPress Enter to continue...")

        elif choice == '2':
            # Run specific checks
            results = run_specific_checks()
            if results and len(results) > 0:
                # Collect findings and generate report
                all_findings = []
                for data in results.values():
                    all_findings.extend(data.get("findings", []))

                risk_score, risk_level = calculate_risk_score(all_findings)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                txt_report = generate_txt_report(results, timestamp, risk_score, risk_level)
                txt_filename = get_report_filename("txt")
                if save_report(txt_report, txt_filename):
                    print(f"\n✅ Report saved: {txt_filename}")

                print_header("SELECTED CHECKS COMPLETED")
                print(f"Risk Score: {risk_score}/100 ({risk_level})")
                input("\nPress Enter to continue...")

        elif choice == '3':
            about()

        elif choice == '4':
            print("\n👋 Exiting Security Audit Tool. Stay secure!")
            sys.exit(0)

        else:
            print("\n❌ Invalid choice. Please enter 1, 2, 3, or 4.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Audit interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please ensure you have necessary permissions to run this tool.")
        sys.exit(1)