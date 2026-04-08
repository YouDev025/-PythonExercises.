#!/usr/bin/env python3
"""
Alert Prioritization System
A cybersecurity alert prioritization tool that ranks security alerts based on
severity, frequency, type, and recency.

Compatible with PyCharm - uses only Python standard library.
"""

import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Alert severity levels with associated weights."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4  # Extended severity for high-risk situations

    @property
    def weight(self) -> float:
        """Return base weight for severity calculation."""
        weights = {
            Severity.LOW: 1.0,
            Severity.MEDIUM: 2.5,
            Severity.HIGH: 5.0,
            Severity.CRITICAL: 8.0,
        }
        return weights[self]


class AlertType(Enum):
    """Alert types with associated risk factors."""
    SCAN = ("Port Scan", 1.0)
    PROBE = ("Service Probe", 1.2)
    BRUTE_FORCE = ("Brute Force", 3.0)
    MALWARE = ("Malware Detected", 4.0)
    DATA_EXFIL = ("Data Exfiltration", 5.0)
    PRIV_ESCALATION = ("Privilege Escalation", 4.5)
    DOS = ("Denial of Service", 3.5)
    SUSPICIOUS_LOGIN = ("Suspicious Login", 2.8)
    POLICY_VIOLATION = ("Policy Violation", 1.5)

    def __init__(self, display_name: str, risk_factor: float):
        self.display_name = display_name
        self.risk_factor = risk_factor


@dataclass
class Alert:
    """Represents a single security alert."""
    alert_id: str
    timestamp: datetime
    source_ip: str
    alert_type: AlertType
    severity: Severity
    description: str
    risk_score: float = 0.0
    frequency_count: int = 0

    def __hash__(self) -> int:
        return hash(self.alert_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Alert):
            return False
        return self.alert_id == other.alert_id


class AlertPrioritizer:
    """
    Handles alert prioritization logic including risk score calculation
    and alert ranking.
    """

    def __init__(self, config: Optional[Dict[str, float]] = None):
        """
        Initialize prioritizer with configurable weights.

        Args:
            config: Optional dictionary of scoring weights
        """
        self.config = {
            'severity_weight': 0.35,
            'frequency_weight': 0.25,
            'type_weight': 0.25,
            'recency_weight': 0.15,
            'max_recency_hours': 24.0,
        }
        if config:
            self.config.update(config)

        # Cache for frequency calculations
        self._frequency_cache: Dict[str, int] = defaultdict(int)

    def calculate_risk_score(self, alert: Alert, all_alerts: List[Alert]) -> float:
        """
        Calculate comprehensive risk score for an alert.

        Args:
            alert: Alert to score
            all_alerts: All alerts for frequency context

        Returns:
            Calculated risk score (0-10 scale)
        """
        # Severity component (0-10 scale)
        severity_score = (alert.severity.weight / Severity.CRITICAL.weight) * 10

        # Frequency component
        frequency = self._calculate_ip_frequency(alert.source_ip, all_alerts)
        frequency_score = min(10.0, frequency * 1.5)

        # Alert type component
        type_score = (alert.alert_type.risk_factor / 5.0) * 10

        # Recency component (newer = higher score)
        recency_score = self._calculate_recency_score(alert.timestamp)

        # Weighted combination
        risk_score = (
            severity_score * self.config['severity_weight'] +
            frequency_score * self.config['frequency_weight'] +
            type_score * self.config['type_weight'] +
            recency_score * self.config['recency_weight']
        )

        # Normalize to 0-10 range
        return min(10.0, max(0.0, risk_score))

    def _calculate_ip_frequency(self, source_ip: str, all_alerts: List[Alert]) -> int:
        """
        Calculate frequency of alerts from a specific IP address.

        Args:
            source_ip: IP address to check
            all_alerts: All alerts in the system

        Returns:
            Number of alerts from this IP
        """
        if not self._frequency_cache:
            for alert in all_alerts:
                self._frequency_cache[alert.source_ip] += 1
        return self._frequency_cache.get(source_ip, 0)

    def _calculate_recency_score(self, timestamp: datetime) -> float:
        """
        Calculate recency score based on how recent the alert is.

        Args:
            timestamp: Alert timestamp

        Returns:
            Recency score (0-10 scale)
        """
        now = datetime.now()
        time_diff = now - timestamp
        hours_passed = time_diff.total_seconds() / 3600

        if hours_passed <= 0:
            return 10.0
        elif hours_passed >= self.config['max_recency_hours']:
            return 0.0

        # Linear decay
        return 10.0 * (1 - hours_passed / self.config['max_recency_hours'])

    def prioritize_alerts(self, alerts: List[Alert]) -> List[Alert]:
        """
        Sort and rank alerts by risk score.

        Args:
            alerts: List of alerts to prioritize

        Returns:
            Sorted list of alerts (highest risk first)
        """
        if not alerts:
            return []

        # Deduplicate alerts
        unique_alerts = list({alert.alert_id: alert for alert in alerts}.values())

        # Calculate risk scores
        for alert in unique_alerts:
            alert.risk_score = self.calculate_risk_score(alert, unique_alerts)
            alert.frequency_count = self._calculate_ip_frequency(
                alert.source_ip, unique_alerts
            )

        # Sort by risk score (descending)
        return sorted(unique_alerts, key=lambda x: x.risk_score, reverse=True)

    def group_by_ip(self, alerts: List[Alert]) -> Dict[str, List[Alert]]:
        """
        Group prioritized alerts by source IP.

        Args:
            alerts: List of alerts (prioritized)

        Returns:
            Dictionary mapping IPs to lists of alerts
        """
        grouped = defaultdict(list)
        for alert in alerts:
            grouped[alert.source_ip].append(alert)

        # Sort alerts within each group by risk score
        for ip in grouped:
            grouped[ip].sort(key=lambda x: x.risk_score, reverse=True)

        return dict(grouped)

    def get_top_alerts(self, alerts: List[Alert], count: int = 10) -> List[Alert]:
        """
        Get top N highest priority alerts.

        Args:
            alerts: Prioritized list of alerts
            count: Number of top alerts to return

        Returns:
            Top N alerts
        """
        return alerts[:min(count, len(alerts))]


class AlertGenerator:
    """Generates realistic sample security alerts."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize alert generator with optional random seed."""
        if seed:
            random.seed(seed)

        self.alert_types = list(AlertType)
        self.severities = list(Severity)
        self.ips = self._generate_ip_pool(50)

        self.descriptions = {
            AlertType.BRUTE_FORCE: [
                "Multiple failed login attempts",
                "SSH brute force attack detected",
                "RDP authentication failures",
            ],
            AlertType.SCAN: [
                "Port scan detected from external source",
                "Network reconnaissance activity",
                "Vulnerability scanning detected",
            ],
            AlertType.MALWARE: [
                "Malware signature detected in network traffic",
                "Suspicious executable download",
                "C2 communication detected",
            ],
            AlertType.DATA_EXFIL: [
                "Large data transfer to unknown destination",
                "Suspicious outbound connection",
                "Database dump detected",
            ],
            AlertType.SUSPICIOUS_LOGIN: [
                "Login from unusual location",
                "Off-hours administrative login",
                "Multiple concurrent sessions",
            ],
        }

    def _generate_ip_pool(self, count: int) -> List[str]:
        """Generate a pool of IP addresses for alert simulation."""
        ips = []
        for _ in range(count):
            # Mix of private and public IPs
            if random.random() < 0.3:
                # Private IP ranges
                ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
            elif random.random() < 0.6:
                # Public IPs (simulated)
                ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            else:
                # RFC 1918 ranges
                ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            ips.append(ip)
        return ips

    def generate_alert(self, alert_id: Optional[str] = None) -> Alert:
        """
        Generate a single random alert.

        Args:
            alert_id: Optional specific alert ID

        Returns:
            Generated Alert object
        """
        if not alert_id:
            alert_id = f"ALERT-{random.randint(10000, 99999)}"

        alert_type = random.choice(self.alert_types)
        severity = random.choice(self.severities)

        # Adjust severity based on alert type (make it more realistic)
        if alert_type in [AlertType.BRUTE_FORCE, AlertType.MALWARE, AlertType.DATA_EXFIL]:
            severity = random.choices(
                [Severity.HIGH, Severity.MEDIUM, Severity.CRITICAL],
                weights=[0.5, 0.3, 0.2]
            )[0]
        elif alert_type in [AlertType.SCAN, AlertType.PROBE]:
            severity = random.choices(
                [Severity.LOW, Severity.MEDIUM],
                weights=[0.6, 0.4]
            )[0]

        description = random.choice(self.descriptions.get(
            alert_type, ["Security alert detected"]
        ))

        # Generate timestamp within last 48 hours
        hours_ago = random.uniform(0, 48)
        timestamp = datetime.now() - timedelta(hours=hours_ago)

        return Alert(
            alert_id=alert_id,
            timestamp=timestamp,
            source_ip=random.choice(self.ips),
            alert_type=alert_type,
            severity=severity,
            description=description,
        )

    def generate_alerts(self, count: int = 20) -> List[Alert]:
        """
        Generate multiple random alerts.

        Args:
            count: Number of alerts to generate

        Returns:
            List of generated alerts
        """
        alerts = []
        for i in range(count):
            alert = self.generate_alert(f"ALERT-{10000 + i}")
            alerts.append(alert)

        # Add some duplicate IPs to simulate attack patterns
        if count > 5:
            target_ip = random.choice(self.ips)
            for _ in range(random.randint(2, 5)):
                alert = self.generate_alert()
                alert.source_ip = target_ip
                alerts.append(alert)

        return alerts


class AlertDisplay:
    """Handles formatted display of prioritized alerts."""

    @staticmethod
    def _get_risk_color(risk_score: float) -> str:
        """Get color code based on risk score (for terminal output)."""
        if risk_score >= 7.5:
            return '\033[91m'  # Red
        elif risk_score >= 5.0:
            return '\033[93m'  # Yellow
        elif risk_score >= 2.5:
            return '\033[94m'  # Blue
        else:
            return '\033[92m'  # Green

    @staticmethod
    def _get_risk_bar(risk_score: float, width: int = 20) -> str:
        """Generate visual risk bar."""
        filled = int((risk_score / 10) * width)
        bar = '█' * filled + '░' * (width - filled)
        return bar

    def display_alert_table(self, alerts: List[Alert], title: str = "PRIORITIZED ALERTS"):
        """Display alerts in a formatted table."""
        if not alerts:
            print("\n" + "=" * 100)
            print("No alerts to display")
            print("=" * 100)
            return

        print("\n" + "=" * 120)
        print(f"{title:^120}")
        print("=" * 120)

        # Header
        print(f"{'Rank':<6} {'Risk':<6} {'Bar':<22} {'Alert ID':<12} {'Time':<20} "
              f"{'Source IP':<16} {'Type':<18} {'Severity':<9} {'Freq':<5}")
        print("-" * 120)

        # Rows
        for rank, alert in enumerate(alerts, 1):
            color = self._get_risk_color(alert.risk_score)
            reset = '\033[0m'
            bar = self._get_risk_bar(alert.risk_score)

            time_str = alert.timestamp.strftime("%Y-%m-%d %H:%M")
            type_str = alert.alert_type.display_name[:17]

            print(f"{color}{rank:<6} {alert.risk_score:<5.1f} {bar:<22} "
                  f"{alert.alert_id:<12} {time_str:<20} {alert.source_ip:<16} "
                  f"{type_str:<18} {alert.severity.name:<9} {alert.frequency_count:<5}{reset}")

        print("=" * 120)

    def display_grouped_alerts(self, grouped: Dict[str, List[Alert]]):
        """Display alerts grouped by source IP."""
        print("\n" + "=" * 100)
        print(f"{'ALERTS GROUPED BY SOURCE IP':^100}")
        print("=" * 100)

        # Sort IPs by highest risk alert
        sorted_ips = sorted(
            grouped.keys(),
            key=lambda ip: max(a.risk_score for a in grouped[ip]),
            reverse=True
        )

        for ip in sorted_ips:
            alerts = grouped[ip]
            total_risk = sum(a.risk_score for a in alerts)
            avg_risk = total_risk / len(alerts)
            max_risk = max(a.risk_score for a in alerts)

            color = self._get_risk_color(max_risk)
            reset = '\033[0m'

            print(f"\n{color}IP: {ip} | Alerts: {len(alerts)} | "
                  f"Avg Risk: {avg_risk:.1f} | Max Risk: {max_risk:.1f}{reset}")
            print("-" * 80)

            for alert in alerts[:3]:  # Show top 3 per IP
                print(f"  [{alert.risk_score:.1f}] {alert.alert_id} - "
                      f"{alert.alert_type.display_name} - {alert.description[:40]}")

    def display_top_critical(self, alerts: List[Alert], count: int = 5):
        """Display top critical alerts with detailed information."""
        top_alerts = alerts[:min(count, len(alerts))]

        print("\n" + "=" * 100)
        print(f"{'TOP CRITICAL ALERTS':^100}")
        print("=" * 100)

        for rank, alert in enumerate(top_alerts, 1):
            color = self._get_risk_color(alert.risk_score)
            reset = '\033[0m'

            print(f"\n{color}╔══ RANK #{rank} - RISK SCORE: {alert.risk_score:.1f} ══╗{reset}")
            print(f"║ Alert ID:      {alert.alert_id}")
            print(f"║ Timestamp:     {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"║ Source IP:     {alert.source_ip} (Frequency: {alert.frequency_count})")
            print(f"║ Alert Type:    {alert.alert_type.display_name}")
            print(f"║ Severity:      {alert.severity.name}")
            print(f"║ Description:   {alert.description}")
            print(f"║ Risk Bar:      {self._get_risk_bar(alert.risk_score, 40)}")
            print(f"{'╚' + '═' * 38 + '╝'}")

    def export_to_file(self, alerts: List[Alert], filename: str = "alerts_priority.txt"):
        """Export prioritized alerts to a text file."""
        try:
            with open(filename, 'w') as f:
                f.write("=" * 100 + "\n")
                f.write("ALERT PRIORITIZATION REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 100 + "\n\n")

                f.write(f"{'Rank':<6} {'Risk':<6} {'Alert ID':<12} {'Timestamp':<20} "
                        f"{'Source IP':<16} {'Type':<20} {'Severity':<9} {'Freq':<5}\n")
                f.write("-" * 100 + "\n")

                for rank, alert in enumerate(alerts, 1):
                    time_str = alert.timestamp.strftime("%Y-%m-%d %H:%M")
                    f.write(f"{rank:<6} {alert.risk_score:<5.1f} {alert.alert_id:<12} "
                            f"{time_str:<20} {alert.source_ip:<16} "
                            f"{alert.alert_type.display_name:<20} {alert.severity.name:<9} "
                            f"{alert.frequency_count:<5}\n")

                f.write("\n" + "=" * 100 + "\n")
                f.write(f"Total Alerts: {len(alerts)}\n")
                if alerts:
                    f.write(f"Highest Risk: {alerts[0].risk_score:.1f}\n")
                    f.write(f"Average Risk: {sum(a.risk_score for a in alerts) / len(alerts):.1f}\n")

            print(f"\n✓ Alerts exported to '{filename}'")
        except IOError as e:
            print(f"\n✗ Error exporting to file: {e}")


class AlertSystem:
    """Main alert prioritization system controller."""

    def __init__(self):
        """Initialize the alert system."""
        self.generator = AlertGenerator()
        self.prioritizer = AlertPrioritizer()
        self.display = AlertDisplay()
        self.alerts: List[Alert] = []
        self.prioritized_alerts: List[Alert] = []

    def generate_sample_alerts(self, count: int = 20):
        """Generate sample alerts."""
        print(f"\n→ Generating {count} sample alerts...")
        self.alerts = self.generator.generate_alerts(count)
        print(f"✓ Generated {len(self.alerts)} alerts")
        self._prioritize()

    def _prioritize(self):
        """Internal method to prioritize alerts."""
        if self.alerts:
            self.prioritized_alerts = self.prioritizer.prioritize_alerts(self.alerts)
            print(f"✓ Prioritized {len(self.prioritized_alerts)} alerts")

    def view_all_alerts(self):
        """Display all prioritized alerts."""
        self.display.display_alert_table(self.prioritized_alerts)

    def view_top_critical(self):
        """Display top critical alerts."""
        if not self.prioritized_alerts:
            print("\n⚠ No alerts available. Generate alerts first.")
            return

        top_count = min(5, len(self.prioritized_alerts))
        self.display.display_top_critical(self.prioritized_alerts, top_count)

    def view_grouped_by_ip(self):
        """Display alerts grouped by IP."""
        if not self.prioritized_alerts:
            print("\n⚠ No alerts available. Generate alerts first.")
            return

        grouped = self.prioritizer.group_by_ip(self.prioritized_alerts)
        self.display.display_grouped_alerts(grouped)

    def export_alerts(self):
        """Export prioritized alerts to file."""
        if not self.prioritized_alerts:
            print("\n⚠ No alerts available to export.")
            return

        self.display.export_to_file(self.prioritized_alerts)

    def adjust_weights(self):
        """Interactive weight adjustment."""
        print("\n" + "=" * 60)
        print("ADJUST SCORING WEIGHTS".center(60))
        print("=" * 60)
        print("\nCurrent weights:")
        for key, value in self.prioritizer.config.items():
            print(f"  {key}: {value}")

        print("\nEnter new weights (press Enter to keep current):")

        try:
            new_severity = input(f"Severity weight [{self.prioritizer.config['severity_weight']}]: ").strip()
            if new_severity:
                self.prioritizer.config['severity_weight'] = float(new_severity)

            new_frequency = input(f"Frequency weight [{self.prioritizer.config['frequency_weight']}]: ").strip()
            if new_frequency:
                self.prioritizer.config['frequency_weight'] = float(new_frequency)

            new_type = input(f"Type weight [{self.prioritizer.config['type_weight']}]: ").strip()
            if new_type:
                self.prioritizer.config['type_weight'] = float(new_type)

            new_recency = input(f"Recency weight [{self.prioritizer.config['recency_weight']}]: ").strip()
            if new_recency:
                self.prioritizer.config['recency_weight'] = float(new_recency)

            # Normalize weights to sum to 1.0
            total = (self.prioritizer.config['severity_weight'] +
                     self.prioritizer.config['frequency_weight'] +
                     self.prioritizer.config['type_weight'] +
                     self.prioritizer.config['recency_weight'])

            if abs(total - 1.0) > 0.001:
                print(f"\n⚠ Weights sum to {total:.3f}, normalizing to 1.0")
                for key in ['severity_weight', 'frequency_weight', 'type_weight', 'recency_weight']:
                    self.prioritizer.config[key] /= total

            print("\n✓ Weights updated. Reprioritizing alerts...")
            self._prioritize()

        except ValueError:
            print("\n✗ Invalid input. Weights unchanged.")

    def show_statistics(self):
        """Display alert statistics."""
        if not self.alerts:
            print("\n⚠ No alerts available.")
            return

        print("\n" + "=" * 60)
        print("ALERT STATISTICS".center(60))
        print("=" * 60)

        # Severity distribution
        severity_count = defaultdict(int)
        type_count = defaultdict(int)

        for alert in self.alerts:
            severity_count[alert.severity.name] += 1
            type_count[alert.alert_type.display_name] += 1

        print("\nSeverity Distribution:")
        for severity, count in sorted(severity_count.items()):
            bar_length = int((count / len(self.alerts)) * 40)
            bar = '█' * bar_length
            print(f"  {severity:<10}: {count:>3} {bar}")

        print("\nAlert Type Distribution:")
        for alert_type, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {alert_type:<20}: {count:>3}")

        if self.prioritized_alerts:
            scores = [a.risk_score for a in self.prioritized_alerts]
            print(f"\nRisk Score Statistics:")
            print(f"  Highest: {max(scores):.1f}")
            print(f"  Lowest:  {min(scores):.1f}")
            print(f"  Average: {sum(scores)/len(scores):.1f}")

    def run(self):
        """Main CLI interface loop."""
        while True:
            print("\n" + "=" * 60)
            print("🔒 ALERT PRIORITIZATION SYSTEM".center(60))
            print("=" * 60)
            print(f"Total Alerts: {len(self.alerts)} | Prioritized: {len(self.prioritized_alerts)}")
            print("-" * 60)
            print("1. Generate Sample Alerts")
            print("2. View All Prioritized Alerts")
            print("3. View Top Critical Alerts")
            print("4. View Alerts Grouped by IP")
            print("5. Export Alerts to File")
            print("6. Adjust Scoring Weights")
            print("7. View Statistics")
            print("8. Exit")
            print("-" * 60)

            choice = input("Select option (1-8): ").strip()

            if choice == '1':
                try:
                    count = input("Number of alerts to generate [20]: ").strip()
                    count = int(count) if count else 20
                    self.generate_sample_alerts(count)
                except ValueError:
                    print("✗ Invalid number. Using default 20.")
                    self.generate_sample_alerts(20)

            elif choice == '2':
                self.view_all_alerts()

            elif choice == '3':
                self.view_top_critical()

            elif choice == '4':
                self.view_grouped_by_ip()

            elif choice == '5':
                self.export_alerts()

            elif choice == '6':
                self.adjust_weights()

            elif choice == '7':
                self.show_statistics()

            elif choice == '8':
                print("\nExiting Alert Prioritization System. Stay secure! 🔒")
                sys.exit(0)

            else:
                print("\n✗ Invalid option. Please select 1-8.")

            input("\nPress Enter to continue...")


def main():
    """Entry point for the alert prioritization system."""
    try:
        system = AlertSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\nExiting Alert Prioritization System. Stay secure! 🔒")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()