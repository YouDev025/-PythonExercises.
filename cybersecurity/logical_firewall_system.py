"""
Logical Firewall System - Network Packet Filtering Simulation
A comprehensive OOP-based firewall simulation with rule management and logging
"""

import ipaddress
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re


class Action(Enum):
    """Enum for firewall rule actions"""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class Protocol(Enum):
    """Enum for supported network protocols"""
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"
    ANY = "ANY"


class NetworkPacket:
    """Represents a network packet with its attributes"""

    def __init__(self, source_ip: str, destination_ip: str, protocol: str,
                 port: int, packet_size: int):
        """
        Initialize a network packet with validation

        Args:
            source_ip: Source IP address
            destination_ip: Destination IP address
            protocol: Network protocol (TCP, UDP, ICMP, ANY)
            port: Port number (0-65535)
            packet_size: Size of packet in bytes
        """
        self.source_ip = self._validate_ip(source_ip, "Source IP")
        self.destination_ip = self._validate_ip(destination_ip, "Destination IP")
        self.protocol = self._validate_protocol(protocol)
        self.port = self._validate_port(port)
        self.packet_size = self._validate_packet_size(packet_size)
        self.timestamp = datetime.now()
        self.packet_id = self._generate_packet_id()

    def _validate_ip(self, ip: str, field_name: str) -> str:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValueError(f"{field_name}: Invalid IP address format - {ip}")

    def _validate_protocol(self, protocol: str) -> str:
        """Validate and normalize protocol"""
        protocol = protocol.upper()
        try:
            Protocol(protocol)
            return protocol
        except ValueError:
            raise ValueError(f"Invalid protocol: {protocol}. Supported: {[p.value for p in Protocol]}")

    def _validate_port(self, port: int) -> int:
        """Validate port number range"""
        if not isinstance(port, int) or port < 0 or port > 65535:
            raise ValueError(f"Invalid port number: {port}. Must be between 0 and 65535")
        return port

    def _validate_packet_size(self, size: int) -> int:
        """Validate packet size"""
        if not isinstance(size, int) or size <= 0 or size > 1500:  # Max Ethernet MTU
            raise ValueError(f"Invalid packet size: {size}. Must be between 1 and 1500 bytes")
        return size

    def _generate_packet_id(self) -> str:
        """Generate unique packet ID"""
        return f"PKT_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    def __str__(self) -> str:
        return (f"Packet[ID: {self.packet_id}, {self.source_ip}:{self.port} -> "
                f"{self.destination_ip}:{self.port}, Protocol: {self.protocol}, "
                f"Size: {self.packet_size} bytes]")


class FirewallRule:
    """Represents a firewall filtering rule"""

    def __init__(self, rule_id: str, source_ip: Optional[str], destination_ip: Optional[str],
                 protocol: Optional[str], port: Optional[int], action: Action,
                 priority: int = 100, description: str = ""):
        """
        Initialize a firewall rule with validation

        Args:
            rule_id: Unique rule identifier
            source_ip: Source IP (None for any)
            destination_ip: Destination IP (None for any)
            protocol: Protocol (None for any)
            port: Port number (None for any)
            action: ALLOW or BLOCK
            priority: Rule priority (lower number = higher priority)
            description: Rule description
        """
        self.rule_id = rule_id
        self.source_ip = self._validate_ip(source_ip) if source_ip else None
        self.destination_ip = self._validate_ip(destination_ip) if destination_ip else None
        self.protocol = self._validate_protocol(protocol) if protocol else None
        self.port = self._validate_port(port) if port is not None else None
        self.action = action if isinstance(action, Action) else Action(action.upper())
        self.priority = self._validate_priority(priority)
        self.description = description
        self.created_at = datetime.now()
        self.hit_count = 0

    def _validate_ip(self, ip: str) -> str:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            # Check if it's a subnet
            try:
                ipaddress.ip_network(ip, strict=False)
                return ip
            except ValueError:
                raise ValueError(f"Invalid IP address or subnet: {ip}")

    def _validate_protocol(self, protocol: str) -> str:
        """Validate protocol"""
        try:
            return Protocol(protocol.upper()).value
        except ValueError:
            raise ValueError(f"Invalid protocol: {protocol}")

    def _validate_port(self, port: int) -> int:
        """Validate port"""
        if port < 0 or port > 65535:
            raise ValueError(f"Invalid port: {port}")
        return port

    def _validate_priority(self, priority: int) -> int:
        """Validate priority"""
        if priority < 0 or priority > 1000:
            raise ValueError("Priority must be between 0 and 1000")
        return priority

    def matches_packet(self, packet: NetworkPacket) -> bool:
        """
        Check if this rule matches a given packet

        Args:
            packet: Network packet to check

        Returns:
            True if rule matches the packet
        """
        # Check each attribute (None means any value matches)
        if self.source_ip and packet.source_ip != self.source_ip:
            return False

        if self.destination_ip and packet.destination_ip != self.destination_ip:
            return False

        if self.protocol and packet.protocol != self.protocol:
            return False

        if self.port is not None and packet.port != self.port:
            return False

        return True

    def increment_hit_count(self):
        """Increment the rule hit counter"""
        self.hit_count += 1

    def __str__(self) -> str:
        src = self.source_ip or "ANY"
        dst = self.destination_ip or "ANY"
        proto = self.protocol or "ANY"
        port_str = str(self.port) if self.port is not None else "ANY"

        return (f"Rule[{self.rule_id}: {self.action.value} {src} -> {dst}, "
                f"Protocol: {proto}, Port: {port_str}, Priority: {self.priority}, "
                f"Hits: {self.hit_count}]")


class FirewallEngine:
    """Core engine that processes packets against rules"""

    def __init__(self):
        self.rules: List[FirewallRule] = []
        self.default_action = Action.BLOCK  # Default deny

    def add_rule(self, rule: FirewallRule):
        """Add a rule to the engine"""
        self.rules.append(rule)
        # Sort rules by priority (lower number = higher priority)
        self.rules.sort(key=lambda r: r.priority)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID"""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        return len(self.rules) < initial_count

    def process_packet(self, packet: NetworkPacket) -> Tuple[Action, Optional[FirewallRule]]:
        """
        Process a packet against the rule set

        Args:
            packet: Network packet to process

        Returns:
            Tuple of (action, matching_rule)
        """
        # Check rules in priority order
        for rule in self.rules:
            if rule.matches_packet(packet):
                rule.increment_hit_count()
                return rule.action, rule

        # No matching rule, apply default action
        return self.default_action, None

    def clear_rules(self):
        """Clear all rules"""
        self.rules.clear()

    def get_rule_count(self) -> int:
        """Get number of rules"""
        return len(self.rules)


class FirewallLogger:
    """Handles logging of firewall events"""

    def __init__(self):
        self.log_entries: List[Dict] = []
        self.stats = {
            'total_packets': 0,
            'allowed_packets': 0,
            'blocked_packets': 0,
            'unique_sources': set(),
            'unique_destinations': set(),
            'protocols': {},
            'ports': {}
        }

        # Configure logging to file
        logging.basicConfig(
            filename='firewall.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def log_decision(self, packet: NetworkPacket, action: Action, rule: Optional[FirewallRule]):
        """Log a firewall decision"""
        log_entry = {
            'timestamp': datetime.now(),
            'packet_id': packet.packet_id,
            'source_ip': packet.source_ip,
            'destination_ip': packet.destination_ip,
            'protocol': packet.protocol,
            'port': packet.port,
            'packet_size': packet.packet_size,
            'action': action.value,
            'rule_id': rule.rule_id if rule else 'DEFAULT',
            'rule_description': rule.description if rule else 'Default Action'
        }

        self.log_entries.append(log_entry)
        self._update_stats(packet, action)

        # Log to file
        log_message = (f"{action.value}: {packet.source_ip}:{packet.port} -> "
                       f"{packet.destination_ip}:{packet.port} "
                       f"[{packet.protocol}] (Rule: {log_entry['rule_id']})")

        if action == Action.ALLOW:
            self.logger.info(log_message)
        else:
            self.logger.warning(log_message)

    def _update_stats(self, packet: NetworkPacket, action: Action):
        """Update statistics"""
        self.stats['total_packets'] += 1

        if action == Action.ALLOW:
            self.stats['allowed_packets'] += 1
        else:
            self.stats['blocked_packets'] += 1

        self.stats['unique_sources'].add(packet.source_ip)
        self.stats['unique_destinations'].add(packet.destination_ip)

        # Update protocol count
        proto = packet.protocol
        self.stats['protocols'][proto] = self.stats['protocols'].get(proto, 0) + 1

        # Update port count
        port = packet.port
        self.stats['ports'][port] = self.stats['ports'].get(port, 0) + 1

    def get_logs(self, limit: Optional[int] = None) -> List[Dict]:
        """Get log entries"""
        if limit:
            return self.log_entries[-limit:]
        return self.log_entries

    def get_statistics(self) -> Dict:
        """Get firewall statistics"""
        stats = self.stats.copy()
        stats['unique_sources'] = len(stats['unique_sources'])
        stats['unique_destinations'] = len(stats['unique_destinations'])
        return stats

    def clear_logs(self):
        """Clear all logs"""
        self.log_entries.clear()
        self.stats = {
            'total_packets': 0,
            'allowed_packets': 0,
            'blocked_packets': 0,
            'unique_sources': set(),
            'unique_destinations': set(),
            'protocols': {},
            'ports': {}
        }


class FirewallManager:
    """Main firewall management interface"""

    def __init__(self):
        self.engine = FirewallEngine()
        self.logger = FirewallLogger()
        self.running = False
        self.next_rule_id = 1

    def start(self):
        """Start the firewall manager"""
        self.running = True
        print("\n" + "=" * 60)
        print("Logical Firewall System Started")
        print("=" * 60)

    def stop(self):
        """Stop the firewall manager"""
        self.running = False
        print("\n" + "=" * 60)
        print("Firewall System Stopped")
        print("=" * 60)

    def add_rule(self, source_ip: Optional[str] = None,
                 destination_ip: Optional[str] = None,
                 protocol: Optional[str] = None,
                 port: Optional[int] = None,
                 action: str = "BLOCK",
                 priority: int = 100,
                 description: str = "") -> str:
        """
        Add a new firewall rule

        Returns:
            Rule ID of the created rule
        """
        rule_id = f"RULE_{self.next_rule_id:04d}"
        self.next_rule_id += 1

        try:
            rule = FirewallRule(
                rule_id=rule_id,
                source_ip=source_ip,
                destination_ip=destination_ip,
                protocol=protocol,
                port=port,
                action=Action(action.upper()),
                priority=priority,
                description=description
            )

            self.engine.add_rule(rule)
            print(f"✓ Rule added: {rule}")
            return rule_id

        except ValueError as e:
            print(f"✗ Error adding rule: {e}")
            return ""

    def remove_rule(self, rule_id: str):
        """Remove a rule by ID"""
        if self.engine.remove_rule(rule_id):
            print(f"✓ Rule {rule_id} removed")
        else:
            print(f"✗ Rule {rule_id} not found")

    def list_rules(self):
        """List all firewall rules"""
        if not self.engine.rules:
            print("No rules configured")
            return

        print("\n" + "-" * 80)
        print("CONFIGURED FIREWALL RULES")
        print("-" * 80)
        for rule in sorted(self.engine.rules, key=lambda r: r.priority):
            print(rule)
        print(f"Total rules: {self.engine.get_rule_count()}")

    def simulate_packet(self, source_ip: str, destination_ip: str,
                        protocol: str, port: int, size: int = 512):
        """
        Simulate a packet arriving at the firewall
        """
        try:
            packet = NetworkPacket(source_ip, destination_ip, protocol, port, size)

            print(f"\n📦 Processing packet: {packet}")

            # Process through firewall engine
            action, matching_rule = self.engine.process_packet(packet)

            # Log the decision
            self.logger.log_decision(packet, action, matching_rule)

            # Display result
            if action == Action.ALLOW:
                print(f"✅ Packet ALLOWED (Rule: {matching_rule.rule_id if matching_rule else 'Default'})")
            else:
                print(f"❌ Packet BLOCKED (Rule: {matching_rule.rule_id if matching_rule else 'Default'})")

        except ValueError as e:
            print(f"✗ Error creating packet: {e}")

    def show_logs(self, limit: int = 20):
        """Display recent firewall logs"""
        logs = self.logger.get_logs(limit)

        if not logs:
            print("No logs available")
            return

        print("\n" + "-" * 100)
        print(f"RECENT FIREWALL LOGS (last {len(logs)} entries)")
        print("-" * 100)

        for log in logs:
            timestamp = log['timestamp'].strftime("%H:%M:%S")
            icon = "✅" if log['action'] == "ALLOW" else "❌"
            print(f"{icon} [{timestamp}] {log['packet_id']}: {log['source_ip']}:{log['port']} -> "
                  f"{log['destination_ip']}:{log['port']} [{log['protocol']}] "
                  f"({log['action']} by {log['rule_id']})")

    def show_statistics(self):
        """Display firewall statistics"""
        stats = self.logger.get_statistics()

        print("\n" + "=" * 60)
        print("FIREWALL STATISTICS")
        print("=" * 60)
        print(f"Total packets processed: {stats['total_packets']}")
        print(f"✅ Allowed: {stats['allowed_packets']}")
        print(f"❌ Blocked: {stats['blocked_packets']}")
        print(f"Unique source IPs: {stats['unique_sources']}")
        print(f"Unique destination IPs: {stats['unique_destinations']}")

        if stats['protocols']:
            print("\nProtocol distribution:")
            for proto, count in stats['protocols'].items():
                print(f"  {proto}: {count}")

        if stats['ports']:
            print("\nTop ports:")
            sorted_ports = sorted(stats['ports'].items(), key=lambda x: x[1], reverse=True)[:5]
            for port, count in sorted_ports:
                print(f"  Port {port}: {count}")

    def clear_all_rules(self):
        """Clear all firewall rules"""
        self.engine.clear_rules()
        print("✓ All rules cleared")

    def clear_logs(self):
        """Clear all logs"""
        self.logger.clear_logs()
        print("✓ Logs cleared")

    def add_default_rules(self):
        """Add some default security rules"""
        print("\nAdding default security rules...")

        # Block all traffic from suspicious subnet
        self.add_rule(
            source_ip="10.0.0.0/24",
            action="BLOCK",
            priority=50,
            description="Block suspicious subnet"
        )

        # Allow web traffic
        self.add_rule(
            destination_ip="192.168.1.100",
            protocol="TCP",
            port=80,
            action="ALLOW",
            priority=100,
            description="Allow HTTP to web server"
        )

        self.add_rule(
            destination_ip="192.168.1.100",
            protocol="TCP",
            port=443,
            action="ALLOW",
            priority=100,
            description="Allow HTTPS to web server"
        )

        # Allow DNS
        self.add_rule(
            protocol="UDP",
            port=53,
            action="ALLOW",
            priority=150,
            description="Allow DNS queries"
        )

        # Allow SSH from management network
        self.add_rule(
            source_ip="192.168.1.0/24",
            protocol="TCP",
            port=22,
            action="ALLOW",
            priority=80,
            description="Allow SSH from management network"
        )


def main():
    """Main program loop"""
    firewall = FirewallManager()
    firewall.start()

    # Add default rules
    firewall.add_default_rules()

    while firewall.running:
        print("\n" + "=" * 60)
        print("LOGICAL FIREWALL SYSTEM")
        print("=" * 60)
        print("1. Add firewall rule")
        print("2. Remove firewall rule")
        print("3. List all rules")
        print("4. Simulate packet")
        print("5. Show logs")
        print("6. Show statistics")
        print("7. Add default rules")
        print("8. Clear all rules")
        print("9. Clear logs")
        print("0. Exit")

        choice = input("\nEnter your choice (0-9): ").strip()

        if choice == '1':
            print("\n--- Add Firewall Rule ---")
            print("(Leave fields empty for ANY)")

            src_ip = input("Source IP (e.g., 192.168.1.100 or 10.0.0.0/24): ").strip() or None
            dst_ip = input("Destination IP: ").strip() or None

            print(f"Protocol options: {[p.value for p in Protocol]}")
            protocol = input("Protocol: ").strip().upper() or None

            port_str = input("Port (1-65535): ").strip()
            port = int(port_str) if port_str else None

            action = input("Action (ALLOW/BLOCK) [BLOCK]: ").strip().upper() or "BLOCK"

            priority_str = input("Priority (0-1000, lower=higher) [100]: ").strip()
            priority = int(priority_str) if priority_str else 100

            description = input("Description: ").strip()

            firewall.add_rule(src_ip, dst_ip, protocol, port, action, priority, description)

        elif choice == '2':
            rule_id = input("Enter rule ID to remove: ").strip()
            firewall.remove_rule(rule_id)

        elif choice == '3':
            firewall.list_rules()

        elif choice == '4':
            print("\n--- Simulate Packet ---")
            try:
                src_ip = input("Source IP: ").strip()
                dst_ip = input("Destination IP: ").strip()
                protocol = input("Protocol (TCP/UDP/ICMP): ").strip().upper()
                port = int(input("Port: ").strip())
                size = input("Packet size (1-1500) [512]: ").strip()
                size = int(size) if size else 512

                firewall.simulate_packet(src_ip, dst_ip, protocol, port, size)
            except ValueError as e:
                print(f"✗ Invalid input: {e}")

        elif choice == '5':
            limit_str = input("Number of logs to show [20]: ").strip()
            limit = int(limit_str) if limit_str else 20
            firewall.show_logs(limit)

        elif choice == '6':
            firewall.show_statistics()

        elif choice == '7':
            firewall.add_default_rules()

        elif choice == '8':
            confirm = input("Are you sure you want to clear all rules? (yes/no): ").strip()
            if confirm.lower() == 'yes':
                firewall.clear_all_rules()

        elif choice == '9':
            confirm = input("Are you sure you want to clear all logs? (yes/no): ").strip()
            if confirm.lower() == 'yes':
                firewall.clear_logs()

        elif choice == '0':
            firewall.stop()

        else:
            print("Invalid choice. Please try again.")

    print("\nFirewall system terminated.")


if __name__ == "__main__":
    main()