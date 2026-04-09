#!/usr/bin/env python3
"""
Patch Management Tracker
A comprehensive tool for tracking system patches, identifying vulnerabilities,
and managing patch compliance across multiple systems.

Author: Senior Python Developer & Cybersecurity Engineer
Version: 1.0.0
"""

import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum


class Severity(Enum):
    """Patch severity levels based on CVSS scoring."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    def __lt__(self, other):
        """Allow severity comparison for sorting."""
        order = {Severity.LOW: 1, Severity.MEDIUM: 2,
                 Severity.HIGH: 3, Severity.CRITICAL: 4}
        return order[self] < order[other]


class PatchStatus(Enum):
    """Installation status of a patch."""
    INSTALLED = "Installed"
    MISSING = "Missing"
    PENDING = "Pending"
    FAILED = "Failed"


@dataclass
class Patch:
    """Represents a security patch or system update."""
    patch_id: str
    system_name: str
    description: str
    severity: Severity
    release_date: datetime
    status: PatchStatus
    installed_date: Optional[datetime] = None
    cve_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate and convert types after initialization."""
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity)
        if isinstance(self.status, str):
            self.status = PatchStatus(self.status)
        if isinstance(self.release_date, str):
            self.release_date = datetime.fromisoformat(self.release_date)
        if self.installed_date and isinstance(self.installed_date, str):
            self.installed_date = datetime.fromisoformat(self.installed_date)

    def to_dict(self) -> Dict:
        """Convert patch to dictionary for serialization."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['status'] = self.status.value
        data['release_date'] = self.release_date.isoformat()
        if self.installed_date:
            data['installed_date'] = self.installed_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Patch':
        """Create patch from dictionary."""
        return cls(**data)

    def is_critical_missing(self) -> bool:
        """Check if patch is critical and missing."""
        return (self.severity == Severity.CRITICAL and
                self.status == PatchStatus.MISSING)

    def is_high_priority(self) -> bool:
        """Check if patch requires immediate attention."""
        return ((self.severity in [Severity.CRITICAL, Severity.HIGH]) and
                self.status == PatchStatus.MISSING)

    def days_since_release(self) -> int:
        """Calculate days since patch release."""
        return (datetime.now() - self.release_date).days


class SystemRiskAnalyzer:
    """Analyzes risk levels for individual systems."""

    @staticmethod
    def calculate_risk_score(patches: List[Patch]) -> float:
        """
        Calculate risk score for a system based on missing patches.
        Formula: Sum of (severity_weight * age_factor) for missing patches
        """
        severity_weights = {
            Severity.CRITICAL: 10.0,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 2.5
        }

        total_score = 0.0
        missing_patches = [p for p in patches if p.status == PatchStatus.MISSING]

        for patch in missing_patches:
            base_weight = severity_weights[patch.severity]
            # Age factor: increases by 10% for every 30 days past release
            days_old = max(0, patch.days_since_release())
            age_factor = 1.0 + (days_old / 30) * 0.1
            total_score += base_weight * age_factor

        return round(total_score, 2)

    @staticmethod
    def get_risk_level(score: float) -> Tuple[str, str]:
        """Determine risk level based on score."""
        if score >= 50:
            return "CRITICAL", "🔴"
        elif score >= 30:
            return "HIGH", "🟠"
        elif score >= 15:
            return "MEDIUM", "🟡"
        elif score > 0:
            return "LOW", "🟢"
        else:
            return "NONE", "⚪"


class PatchManager:
    """Manages patch inventory and tracking."""

    def __init__(self):
        self.patches: List[Patch] = []
        self.patch_history: Dict[str, List[Dict]] = defaultdict(list)

    def add_patch(self, patch: Patch) -> bool:
        """Add a new patch to the tracker."""
        # Check for duplicates
        for existing in self.patches:
            if (existing.patch_id == patch.patch_id and
                    existing.system_name == patch.system_name):
                return False

        self.patches.append(patch)
        self._record_history(patch, "added")
        return True

    def update_patch_status(self, patch_id: str, system_name: str,
                            new_status: PatchStatus) -> bool:
        """Update the status of an existing patch."""
        for patch in self.patches:
            if patch.patch_id == patch_id and patch.system_name == system_name:
                old_status = patch.status
                patch.status = new_status
                if new_status == PatchStatus.INSTALLED:
                    patch.installed_date = datetime.now()
                self._record_history(patch, f"status_changed",
                                     f"{old_status.value} -> {new_status.value}")
                return True
        return False

    def _record_history(self, patch: Patch, action: str, details: str = ""):
        """Record patch history for auditing."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "patch_id": patch.patch_id,
            "system": patch.system_name,
            "action": action,
            "details": details,
            "severity": patch.severity.value,
            "status": patch.status.value
        }
        self.patch_history[f"{patch.system_name}:{patch.patch_id}"].append(entry)

    def get_missing_patches(self) -> List[Patch]:
        """Get all missing patches."""
        return [p for p in self.patches if p.status == PatchStatus.MISSING]

    def get_critical_missing(self) -> List[Patch]:
        """Get critical patches that are missing."""
        return [p for p in self.patches if p.is_critical_missing()]

    def get_high_priority_patches(self) -> List[Patch]:
        """Get high priority patches (Critical/High severity missing)."""
        return [p for p in self.patches if p.is_high_priority()]

    def get_patches_by_system(self, system_name: str) -> List[Patch]:
        """Get all patches for a specific system."""
        return [p for p in self.patches if p.system_name == system_name]

    def get_systems(self) -> Set[str]:
        """Get unique system names."""
        return {p.system_name for p in self.patches}

    def get_system_statistics(self, system_name: str) -> Dict:
        """Get comprehensive statistics for a system."""
        patches = self.get_patches_by_system(system_name)
        if not patches:
            return {}

        total = len(patches)
        installed = len([p for p in patches if p.status == PatchStatus.INSTALLED])
        missing = total - installed

        severity_counts = defaultdict(int)
        for patch in patches:
            if patch.status == PatchStatus.MISSING:
                severity_counts[patch.severity.value] += 1

        risk_score = SystemRiskAnalyzer.calculate_risk_score(patches)
        risk_level, risk_icon = SystemRiskAnalyzer.get_risk_level(risk_score)

        return {
            "system_name": system_name,
            "total_patches": total,
            "installed": installed,
            "missing": missing,
            "compliance_rate": round((installed / total) * 100, 1) if total > 0 else 0,
            "missing_by_severity": dict(severity_counts),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_icon": risk_icon
        }

    def generate_sample_data(self):
        """Generate sample patch data for demonstration."""
        systems = ["WEB-SRV-01", "DB-SRV-02", "APP-SRV-03", "FILE-SRV-04", "AD-SRV-05"]
        severities = list(Severity)
        statuses = list(PatchStatus)

        patch_templates = [
            ("KB5021234", "Windows Security Update"),
            ("KB5022235", "Cumulative Update for .NET Framework"),
            ("CVE-2024-1234", "Apache Log4j2 Security Patch"),
            ("CVE-2024-5678", "OpenSSL Security Advisory"),
            ("KB5023346", "Windows Defender Update"),
            ("CVE-2024-9012", "Kernel Privilege Escalation Fix"),
            ("KB5024457", "SQL Server Security Update"),
            ("CVE-2024-3456", "Remote Code Execution Fix"),
            ("KB5025568", "Active Directory Security Patch"),
            ("CVE-2024-7890", "Cross-Site Scripting Vulnerability Fix"),
        ]

        patch_id = 1
        base_date = datetime.now() - timedelta(days=180)

        for system in systems:
            num_patches = 8 + (hash(system) % 5)  # 8-12 patches per system

            for i in range(num_patches):
                template_idx = (patch_id + i) % len(patch_templates)
                patch_base_id, desc_template = patch_templates[template_idx]

                # Create unique patch ID
                unique_id = f"{patch_base_id}-{system}-{patch_id:03d}"

                # Determine severity with weighted distribution
                severity_roll = (hash(unique_id) % 100)
                if severity_roll < 10:
                    severity = Severity.CRITICAL
                elif severity_roll < 30:
                    severity = Severity.HIGH
                elif severity_roll < 60:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW

                # Determine status with realistic distribution
                status_roll = (hash(unique_id + "status") % 100)
                if severity == Severity.CRITICAL:
                    # Critical patches are more likely to be installed
                    status = PatchStatus.INSTALLED if status_roll < 80 else PatchStatus.MISSING
                elif severity == Severity.HIGH:
                    status = PatchStatus.INSTALLED if status_roll < 70 else PatchStatus.MISSING
                else:
                    status = PatchStatus.INSTALLED if status_roll < 60 else PatchStatus.MISSING

                # Release date between 1 and 180 days ago
                days_ago = 5 + (hash(unique_id) % 175)
                release_date = base_date + timedelta(days=days_ago)

                # Installed date (if applicable)
                installed_date = None
                if status == PatchStatus.INSTALLED:
                    install_delay = 2 + (hash(unique_id + "install") % 30)
                    installed_date = release_date + timedelta(days=install_delay)
                    if installed_date > datetime.now():
                        installed_date = datetime.now() - timedelta(days=1)

                # Generate CVE IDs for security patches
                cve_ids = []
                if "CVE" in patch_base_id:
                    cve_ids = [patch_base_id]
                elif severity in [Severity.CRITICAL, Severity.HIGH]:
                    cve_ids = [f"CVE-2024-{1000 + (hash(unique_id) % 9000):04d}"]

                patch = Patch(
                    patch_id=unique_id,
                    system_name=system,
                    description=f"{desc_template} for {system}",
                    severity=severity,
                    release_date=release_date,
                    status=status,
                    installed_date=installed_date,
                    cve_ids=cve_ids
                )

                self.add_patch(patch)
                patch_id += 1

    def get_summary(self) -> Dict:
        """Generate overall summary statistics."""
        total = len(self.patches)
        installed = len([p for p in self.patches if p.status == PatchStatus.INSTALLED])
        missing = total - installed

        severity_counts = defaultdict(int)
        for patch in self.patches:
            if patch.status == PatchStatus.MISSING:
                severity_counts[patch.severity.value] += 1

        critical_missing = len(self.get_critical_missing())
        high_missing = severity_counts.get("High", 0)

        return {
            "total_patches": total,
            "installed": installed,
            "missing": missing,
            "compliance_rate": round((installed / total) * 100, 1) if total > 0 else 0,
            "missing_by_severity": dict(severity_counts),
            "critical_missing": critical_missing,
            "high_priority_missing": critical_missing + high_missing,
            "systems_count": len(self.get_systems())
        }

    def export_report(self, filename: str = "patch_report.txt") -> str:
        """Export comprehensive report to file."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PATCH MANAGEMENT REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Overall Summary
        summary = self.get_summary()
        report_lines.append("OVERALL SUMMARY:")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Systems: {summary['systems_count']}")
        report_lines.append(f"Total Patches: {summary['total_patches']}")
        report_lines.append(f"Installed: {summary['installed']} ({summary['compliance_rate']}%)")
        report_lines.append(f"Missing: {summary['missing']}")
        report_lines.append(f"High Priority Missing: {summary['high_priority_missing']}")
        report_lines.append("")

        # Missing by Severity
        report_lines.append("MISSING PATCHES BY SEVERITY:")
        report_lines.append("-" * 40)
        for severity, count in summary['missing_by_severity'].items():
            report_lines.append(f"  {severity}: {count}")
        report_lines.append("")

        # System Details
        report_lines.append("SYSTEM DETAILS:")
        report_lines.append("-" * 40)
        for system in sorted(self.get_systems()):
            stats = self.get_system_statistics(system)
            report_lines.append(f"\n{system}:")
            report_lines.append(f"  Risk Score: {stats['risk_score']} ({stats['risk_level']})")
            report_lines.append(
                f"  Compliance: {stats['compliance_rate']}% ({stats['installed']}/{stats['total_patches']})")
            if stats['missing_by_severity']:
                report_lines.append("  Missing Patches:")
                for sev, count in stats['missing_by_severity'].items():
                    report_lines.append(f"    - {sev}: {count}")

        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")

        report_content = "\n".join(report_lines)

        try:
            with open(filename, 'w') as f:
                f.write(report_content)
            return f"Report exported successfully to {filename}"
        except Exception as e:
            return f"Error exporting report: {e}"

    def export_json(self, filename: str = "patch_data.json") -> str:
        """Export all patch data to JSON format."""
        try:
            data = {
                "export_date": datetime.now().isoformat(),
                "summary": self.get_summary(),
                "patches": [p.to_dict() for p in self.patches],
                "systems": {
                    system: self.get_system_statistics(system)
                    for system in self.get_systems()
                }
            }

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return f"JSON data exported successfully to {filename}"
        except Exception as e:
            return f"Error exporting JSON: {e}"


class CLI:
    """Command Line Interface for Patch Management Tracker."""

    def __init__(self):
        self.manager = PatchManager()
        self.running = True

    def clear_screen(self):
        """Clear terminal screen."""
        print("\033[2J\033[H", end="")

    def print_header(self, title: str):
        """Print formatted header."""
        print("\n" + "=" * 80)
        print(f" {title:^76} ")
        print("=" * 80)

    def print_menu(self):
        """Display main menu options."""
        self.clear_screen()
        self.print_header("PATCH MANAGEMENT TRACKER")
        print("\n📋 MAIN MENU:")
        print("-" * 40)
        print("  1. Generate Sample Data")
        print("  2. View Patch Status Summary")
        print("  3. List Missing Patches")
        print("  4. View High Priority Patches")
        print("  5. System Risk Analysis")
        print("  6. Filter Patches by Severity")
        print("  7. View System Details")
        print("  8. Export Report (TXT)")
        print("  9. Export Data (JSON)")
        print("  0. Exit")
        print("-" * 40)

    def display_summary(self):
        """Display overall summary statistics."""
        self.clear_screen()
        self.print_header("PATCH STATUS SUMMARY")

        summary = self.manager.get_summary()

        if summary['total_patches'] == 0:
            print("\n⚠️  No patch data available. Please generate sample data first.")
            return

        print(f"\n📊 OVERALL STATISTICS:")
        print("-" * 40)
        print(f"  Systems Monitored: {summary['systems_count']}")
        print(f"  Total Patches: {summary['total_patches']}")
        print(f"  ✅ Installed: {summary['installed']} ({summary['compliance_rate']}%)")
        print(f"  ❌ Missing: {summary['missing']}")
        print(f"  🔴 Critical Missing: {summary['critical_missing']}")
        print(f"  🟠 High Priority Missing: {summary['high_priority_missing']}")

        print(f"\n📈 MISSING PATCHES BY SEVERITY:")
        print("-" * 40)
        if summary['missing_by_severity']:
            for severity in ['Critical', 'High', 'Medium', 'Low']:
                count = summary['missing_by_severity'].get(severity, 0)
                icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
                print(f"  {icon} {severity}: {count}")
        else:
            print("  No missing patches!")

    def display_missing_patches(self, limit: int = 20):
        """Display list of missing patches."""
        self.clear_screen()
        self.print_header("MISSING PATCHES")

        missing = self.manager.get_missing_patches()

        if not missing:
            print("\n✅ No missing patches found!")
            return

        # Sort by severity (Critical first) and then by release date
        missing.sort(key=lambda p: (p.severity, p.release_date), reverse=True)

        print(f"\n🔍 Found {len(missing)} missing patches (showing first {min(limit, len(missing))}):\n")
        print(f"{'Severity':<10} {'Patch ID':<30} {'System':<15} {'Days Old':<10} {'Description'}")
        print("-" * 100)

        for patch in missing[:limit]:
            severity_icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(patch.severity.value, '⚪')
            print(f"{severity_icon} {patch.severity.value:<7} {patch.patch_id:<30} {patch.system_name:<15} "
                  f"{patch.days_since_release():<10} {patch.description[:40]}")

    def display_high_priority(self):
        """Display high priority patches requiring immediate attention."""
        self.clear_screen()
        self.print_header("HIGH PRIORITY PATCHES (CRITICAL/HIGH MISSING)")

        high_priority = self.manager.get_high_priority_patches()

        if not high_priority:
            print("\n✅ No high priority patches found!")
            return

        # Sort by severity and days old
        high_priority.sort(key=lambda p: (p.severity, p.days_since_release()), reverse=True)

        print(f"\n🚨 {len(high_priority)} high priority patches require immediate attention:\n")
        print(f"{'Priority':<10} {'Patch ID':<35} {'System':<15} {'Days Old':<10} {'CVE IDs'}")
        print("-" * 100)

        for patch in high_priority:
            priority = "CRITICAL" if patch.severity == Severity.CRITICAL else "HIGH"
            icon = '🔴' if priority == "CRITICAL" else '🟠'
            cve_str = ", ".join(patch.cve_ids[:2]) if patch.cve_ids else "N/A"
            print(f"{icon} {priority:<7} {patch.patch_id:<35} {patch.system_name:<15} "
                  f"{patch.days_since_release():<10} {cve_str}")

    def display_system_risk_analysis(self):
        """Display risk analysis for all systems."""
        self.clear_screen()
        self.print_header("SYSTEM RISK ANALYSIS")

        systems = self.manager.get_systems()

        if not systems:
            print("\n⚠️  No systems found. Please generate sample data first.")
            return

        system_stats = []
        for system in systems:
            stats = self.manager.get_system_statistics(system)
            system_stats.append(stats)

        # Sort by risk score (highest first)
        system_stats.sort(key=lambda x: x['risk_score'], reverse=True)

        print("\n🎯 SYSTEMS AT RISK:\n")
        print(f"{'Risk':<8} {'Score':<8} {'System':<15} {'Compliance':<12} {'Missing Patches':<15} {'Critical':<10}")
        print("-" * 80)

        for stats in system_stats:
            risk_display = f"{stats['risk_icon']} {stats['risk_level']:<5}"
            critical_missing = stats['missing_by_severity'].get('Critical', 0)

            print(f"{risk_display:<8} {stats['risk_score']:<8.1f} {stats['system_name']:<15} "
                  f"{stats['compliance_rate']:<11.1f}% {stats['missing']:<15} {critical_missing:<10}")

        # Show detailed breakdown for high-risk systems
        high_risk_systems = [s for s in system_stats if s['risk_level'] in ['CRITICAL', 'HIGH']]

        if high_risk_systems:
            print("\n⚠️  HIGH RISK SYSTEM DETAILS:")
            print("-" * 80)
            for stats in high_risk_systems:
                print(f"\n{stats['risk_icon']} {stats['system_name']} - Risk Score: {stats['risk_score']}")
                print(f"   Missing Patches by Severity:")
                for severity in ['Critical', 'High', 'Medium', 'Low']:
                    count = stats['missing_by_severity'].get(severity, 0)
                    if count > 0:
                        print(f"     - {severity}: {count}")

    def filter_by_severity(self):
        """Filter and display patches by severity level."""
        self.clear_screen()
        self.print_header("FILTER PATCHES BY SEVERITY")

        print("\nSelect severity level:")
        print("  1. Critical")
        print("  2. High")
        print("  3. Medium")
        print("  4. Low")
        print("  5. All (Missing only)")

        try:
            choice = input("\nEnter choice (1-5): ").strip()

            severity_map = {
                '1': Severity.CRITICAL,
                '2': Severity.HIGH,
                '3': Severity.MEDIUM,
                '4': Severity.LOW,
                '5': None
            }

            if choice not in severity_map:
                print("Invalid choice!")
                return

            severity = severity_map[choice]

            self.clear_screen()

            if severity:
                self.print_header(f"{severity.value.upper()} SEVERITY PATCHES")
                patches = [p for p in self.manager.patches if p.severity == severity]
            else:
                self.print_header("ALL MISSING PATCHES")
                patches = self.manager.get_missing_patches()

            if not patches:
                print(f"\nNo patches found!")
                return

            print(f"\n{'Status':<10} {'Patch ID':<35} {'System':<15} {'Days Old':<10} {'Description'}")
            print("-" * 100)

            for patch in sorted(patches, key=lambda p: p.days_since_release(), reverse=True)[:30]:
                status_icon = '✅' if patch.status == PatchStatus.INSTALLED else '❌'
                print(f"{status_icon} {patch.status.value:<7} {patch.patch_id:<35} {patch.system_name:<15} "
                      f"{patch.days_since_release():<10} {patch.description[:40]}")

            if len(patches) > 30:
                print(f"\n... and {len(patches) - 30} more patches")

        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled.")

    def view_system_details(self):
        """View detailed information for a specific system."""
        self.clear_screen()
        self.print_header("SYSTEM DETAILS")

        systems = sorted(self.manager.get_systems())

        if not systems:
            print("\n⚠️  No systems found. Please generate sample data first.")
            return

        print("\nAvailable Systems:")
        for i, system in enumerate(systems, 1):
            stats = self.manager.get_system_statistics(system)
            print(f"  {i}. {system} {stats['risk_icon']} (Risk: {stats['risk_level']}, "
                  f"Compliance: {stats['compliance_rate']}%)")

        try:
            choice = input(f"\nSelect system (1-{len(systems)}) or 0 to cancel: ").strip()
            if choice == '0':
                return

            idx = int(choice) - 1
            if 0 <= idx < len(systems):
                system = systems[idx]
                self.display_single_system_details(system)
            else:
                print("Invalid selection!")

        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled.")

    def display_single_system_details(self, system_name: str):
        """Display comprehensive details for a single system."""
        self.clear_screen()
        self.print_header(f"SYSTEM DETAILS: {system_name}")

        stats = self.manager.get_system_statistics(system_name)
        patches = self.manager.get_patches_by_system(system_name)

        print(f"\n📊 SYSTEM OVERVIEW:")
        print("-" * 40)
        print(f"  Risk Level: {stats['risk_icon']} {stats['risk_level']} (Score: {stats['risk_score']})")
        print(f"  Compliance Rate: {stats['compliance_rate']}%")
        print(f"  Total Patches: {stats['total_patches']}")
        print(f"  Installed: {stats['installed']}")
        print(f"  Missing: {stats['missing']}")

        print(f"\n📈 MISSING PATCHES BY SEVERITY:")
        print("-" * 40)
        if stats['missing_by_severity']:
            for severity in ['Critical', 'High', 'Medium', 'Low']:
                count = stats['missing_by_severity'].get(severity, 0)
                if count > 0:
                    icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
                    print(f"  {icon} {severity}: {count}")
        else:
            print("  No missing patches!")

        print(f"\n📋 PATCH HISTORY (Last 10 events):")
        print("-" * 40)
        history_key = f"{system_name}:"
        system_history = []
        for key, events in self.manager.patch_history.items():
            if key.startswith(history_key):
                system_history.extend(events)

        if system_history:
            system_history.sort(key=lambda x: x['timestamp'], reverse=True)
            for event in system_history[:10]:
                timestamp = datetime.fromisoformat(event['timestamp']).strftime('%Y-%m-%d %H:%M')
                print(f"  [{timestamp}] {event['patch_id']}: {event['action']}")
        else:
            print("  No history available")

    def run(self):
        """Main CLI loop."""
        while self.running:
            self.print_menu()

            try:
                choice = input("\nEnter your choice (0-9): ").strip()

                if choice == '1':
                    self.manager.generate_sample_data()
                    print("\n✅ Sample data generated successfully!")
                    print(f"   Created {len(self.manager.patches)} patches across "
                          f"{len(self.manager.get_systems())} systems.")

                elif choice == '2':
                    self.display_summary()

                elif choice == '3':
                    self.display_missing_patches()

                elif choice == '4':
                    self.display_high_priority()

                elif choice == '5':
                    self.display_system_risk_analysis()

                elif choice == '6':
                    self.filter_by_severity()

                elif choice == '7':
                    self.view_system_details()

                elif choice == '8':
                    if self.manager.patches:
                        result = self.manager.export_report()
                        print(f"\n📄 {result}")
                    else:
                        print("\n⚠️  No data to export. Generate sample data first.")

                elif choice == '9':
                    if self.manager.patches:
                        result = self.manager.export_json()
                        print(f"\n💾 {result}")
                    else:
                        print("\n⚠️  No data to export. Generate sample data first.")

                elif choice == '0':
                    self.running = False
                    print("\n👋 Thank you for using Patch Management Tracker. Goodbye!")

                else:
                    print("\n❌ Invalid choice! Please enter a number between 0 and 9.")

                if choice != '0':
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\n⚠️  Operation cancelled by user.")
                input("Press Enter to continue...")
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                input("Press Enter to continue...")


def main():
    """Entry point for the application."""
    cli = CLI()

    # Check if running with Python 3
    if sys.version_info[0] < 3:
        print("Error: This program requires Python 3.6 or higher.")
        sys.exit(1)

    cli.run()


if __name__ == "__main__":
    main()