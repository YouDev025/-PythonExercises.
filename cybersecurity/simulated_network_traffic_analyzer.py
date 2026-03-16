import random
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import ipaddress
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class NetworkPacket:
    """Represents a network packet with relevant attributes."""

    # Valid protocols for validation
    VALID_PROTOCOLS = {'TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'DNS', 'FTP', 'SSH'}

    # Suspicious ports (well-known ports often targeted by attacks)
    SUSPICIOUS_PORTS = {22, 23, 3389, 445, 1433, 3306, 5432, 27017, 6379}

    def __init__(self, source_ip: str, destination_ip: str, protocol: str,
                 port: int, packet_size: int, timestamp: Optional[datetime] = None):
        """
        Initialize a network packet with validation.

        Args:
            source_ip: Source IP address
            destination_ip: Destination IP address
            protocol: Network protocol
            port: Destination port number
            packet_size: Size of packet in bytes
            timestamp: Packet timestamp (defaults to current time)
        """
        self.source_ip = self._validate_ip(source_ip, "source_ip")
        self.destination_ip = self._validate_ip(destination_ip, "destination_ip")
        self.protocol = self._validate_protocol(protocol)
        self.port = self._validate_port(port)
        self.packet_size = self._validate_packet_size(packet_size)
        self.timestamp = timestamp or datetime.now()

    @staticmethod
    def _validate_ip(ip: str, field_name: str) -> str:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValueError(f"Invalid IP address for {field_name}: {ip}")

    @classmethod
    def _validate_protocol(cls, protocol: str) -> str:
        """Validate protocol is in allowed list."""
        protocol = protocol.upper()
        if protocol not in cls.VALID_PROTOCOLS:
            raise ValueError(f"Invalid protocol: {protocol}. Must be one of {cls.VALID_PROTOCOLS}")
        return protocol

    @staticmethod
    def _validate_port(port: int) -> int:
        """Validate port number is within range."""
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f"Invalid port number: {port}. Must be between 1 and 65535")
        return port

    @staticmethod
    def _validate_packet_size(size: int) -> int:
        """Validate packet size is positive and within reasonable limits."""
        if not isinstance(size, int) or size < 1 or size > 1500:  # MTU typically 1500
            raise ValueError(f"Invalid packet size: {size}. Must be between 1 and 1500 bytes")
        return size

    def is_suspicious_port(self) -> bool:
        """Check if packet uses a suspicious port."""
        return self.port in self.SUSPICIOUS_PORTS

    def __str__(self) -> str:
        """String representation of the packet."""
        return (f"Packet({self.source_ip} -> {self.destination_ip} | "
                f"Proto:{self.protocol} | Port:{self.port} | Size:{self.packet_size} | "
                f"Time:{self.timestamp.strftime('%H:%M:%S')})")

    def __repr__(self) -> str:
        return self.__str__()


class TrafficAnalyzer:
    """Analyzes network traffic patterns and detects anomalies."""

    def __init__(self):
        self.anomalies = []
        self.packet_count = 0
        self.total_bytes = 0
        self.ip_traffic = defaultdict(int)  # Count packets per source IP
        self.protocol_counts = defaultdict(int)
        self.port_usage = defaultdict(int)
        self.packet_sizes = []

        # Thresholds for anomaly detection
        self.HIGH_TRAFFIC_THRESHOLD = 10  # Packets per second from single IP
        self.SUSPICIOUS_PORT_THRESHOLD = 5  # Connections to suspicious port
        self.ABNORMAL_SIZE_LOW = 50  # Bytes - too small
        self.ABNORMAL_SIZE_HIGH = 1400  # Bytes - too large

    def analyze_packet(self, packet: NetworkPacket) -> List[str]:
        """
        Analyze a single packet for anomalies.

        Args:
            packet: NetworkPacket object to analyze

        Returns:
            List of anomaly descriptions found
        """
        self.packet_count += 1
        self.total_bytes += packet.packet_size
        self.ip_traffic[packet.source_ip] += 1
        self.protocol_counts[packet.protocol] += 1
        self.port_usage[packet.port] += 1
        self.packet_sizes.append(packet.packet_size)

        anomalies = []

        # Check for suspicious port usage
        if packet.is_suspicious_port():
            anomaly = f"Suspicious port usage: {packet.port} from {packet.source_ip}"
            anomalies.append(anomaly)
            self.anomalies.append((datetime.now(), anomaly, packet))

        # Check for abnormal packet size
        if packet.packet_size < self.ABNORMAL_SIZE_LOW:
            anomaly = f"Abnormally small packet ({packet.packet_size} bytes) from {packet.source_ip}"
            anomalies.append(anomaly)
            self.anomalies.append((datetime.now(), anomaly, packet))
        elif packet.packet_size > self.ABNORMAL_SIZE_HIGH:
            anomaly = f"Abnormally large packet ({packet.packet_size} bytes) from {packet.source_ip}"
            anomalies.append(anomaly)
            self.anomalies.append((datetime.now(), anomaly, packet))

        return anomalies

    def analyze_batch(self, packets: List[NetworkPacket], time_window_seconds: int = 1) -> Dict:
        """
        Analyze a batch of packets for patterns.

        Args:
            packets: List of packets to analyze
            time_window_seconds: Time window for rate-based analysis

        Returns:
            Dictionary containing analysis results
        """
        batch_anomalies = []

        # Check for high traffic from single IP in time window
        if packets:
            time_start = packets[0].timestamp
            time_end = packets[-1].timestamp
            duration = (time_end - time_start).total_seconds() or 1

            ip_counts = Counter(p.source_ip for p in packets)
            for ip, count in ip_counts.items():
                rate = count / duration
                if rate > self.HIGH_TRAFFIC_THRESHOLD:
                    anomaly = (f"High traffic from {ip}: {count} packets in "
                               f"{duration:.2f} seconds ({rate:.2f} packets/sec)")
                    batch_anomalies.append(anomaly)
                    self.anomalies.append((datetime.now(), anomaly, None))

        # Check for excessive connections to same suspicious port
        port_counts = Counter(p.port for p in packets if p.is_suspicious_port())
        for port, count in port_counts.items():
            if count > self.SUSPICIOUS_PORT_THRESHOLD:
                anomaly = f"Multiple connections ({count}) to suspicious port {port}"
                batch_anomalies.append(anomaly)
                self.anomalies.append((datetime.now(), anomaly, None))

        return {
            'anomalies': batch_anomalies,
            'packet_count': len(packets),
            'unique_ips': len(ip_counts),
            'total_bytes': sum(p.packet_size for p in packets)
        }

    def get_statistics(self) -> Dict:
        """Get comprehensive traffic statistics."""
        if not self.packet_sizes:
            return {'error': 'No packets analyzed yet'}

        avg_size = sum(self.packet_sizes) / len(self.packet_sizes)
        return {
            'total_packets': self.packet_count,
            'total_bytes': self.total_bytes,
            'avg_packet_size': round(avg_size, 2),
            'min_packet_size': min(self.packet_sizes),
            'max_packet_size': max(self.packet_sizes),
            'unique_source_ips': len(self.ip_traffic),
            'protocol_distribution': dict(self.protocol_counts),
            'top_talkers': dict(sorted(self.ip_traffic.items(),
                                       key=lambda x: x[1], reverse=True)[:5]),
            'suspicious_ports_detected': {port: count for port, count in self.port_usage.items()
                                          if port in NetworkPacket.SUSPICIOUS_PORTS}
        }

    def get_anomalies(self, limit: Optional[int] = None) -> List[Tuple]:
        """Get detected anomalies, optionally limited to most recent."""
        sorted_anomalies = sorted(self.anomalies, key=lambda x: x[0], reverse=True)
        if limit:
            return sorted_anomalies[:limit]
        return sorted_anomalies

    def clear_anomalies(self):
        """Clear all detected anomalies."""
        self.anomalies.clear()
        logging.info("Anomaly history cleared")


class TrafficManager:
    """Manages packet generation, analysis, and storage."""

    # Common IP addresses for simulation
    SOURCE_IPS = [
        '192.168.1.10', '192.168.1.20', '192.168.1.30', '10.0.0.5',
        '10.0.0.10', '172.16.0.2', '172.16.0.3', '8.8.8.8', '1.1.1.1'
    ]

    DESTINATION_IPS = [
        '192.168.1.100', '192.168.1.200', '10.0.0.50', '10.0.0.100',
        '172.16.0.100', '8.8.4.4', '208.67.222.222', '192.168.1.1'
    ]

    PROTOCOLS = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'DNS']

    COMMON_PORTS = [80, 443, 53, 22, 25, 110, 143, 993, 995, 8080]
    SUSPICIOUS_PORTS = list(NetworkPacket.SUSPICIOUS_PORTS)

    def __init__(self):
        self.analyzer = TrafficAnalyzer()
        self.packets: List[NetworkPacket] = []
        self.generation_count = 0
        self.anomaly_mode = False  # Toggle for generating more anomalies

    def generate_packet(self) -> NetworkPacket:
        """
        Generate a single simulated packet.

        Returns:
            A new NetworkPacket object
        """
        # Sometimes use suspicious ports for anomaly simulation
        if self.anomaly_mode and random.random() < 0.2:  # 20% chance in anomaly mode
            port = random.choice(self.SUSPICIOUS_PORTS)
            protocol = random.choice(['TCP', 'UDP'])
            size = random.choice([random.randint(1, 40), random.randint(1400, 1500)])  # Extreme sizes
        else:
            port = random.choice(self.COMMON_PORTS + [random.randint(1024, 65535)])
            protocol = random.choice(self.PROTOCOLS)
            size = random.randint(64, 1400)

        # Generate anomalous packet sizes occasionally
        if random.random() < 0.05:  # 5% chance of anomalous size
            size = random.choice([random.randint(1, 40), random.randint(1400, 1500)])

        source_ip = random.choice(self.SOURCE_IPS)
        dest_ip = random.choice(self.DESTINATION_IPS)

        # Add some timestamp variation
        timestamp = datetime.now() + timedelta(seconds=random.uniform(-5, 5))

        try:
            packet = NetworkPacket(
                source_ip=source_ip,
                destination_ip=dest_ip,
                protocol=protocol,
                port=port,
                packet_size=size,
                timestamp=timestamp
            )
            return packet
        except ValueError as e:
            logging.error(f"Error generating packet: {e}")
            # Recursively try again with valid values
            return self.generate_packet()

    def generate_traffic(self, count: int = 10) -> List[NetworkPacket]:
        """
        Generate multiple simulated packets.

        Args:
            count: Number of packets to generate

        Returns:
            List of generated packets
        """
        new_packets = []
        for _ in range(count):
            try:
                packet = self.generate_packet()
                new_packets.append(packet)
                self.packets.append(packet)
                self.generation_count += 1
            except Exception as e:
                logging.error(f"Failed to generate packet: {e}")

        logging.info(f"Generated {len(new_packets)} new packets")
        return new_packets

    def analyze_traffic(self, packet_count: Optional[int] = None) -> Dict:
        """
        Analyze recent or all packets.

        Args:
            packet_count: Number of most recent packets to analyze (None for all)

        Returns:
            Analysis results
        """
        packets_to_analyze = self.packets
        if packet_count:
            packets_to_analyze = self.packets[-packet_count:]

        if not packets_to_analyze:
            return {'error': 'No packets to analyze'}

        # Analyze each packet individually
        individual_anomalies = []
        for packet in packets_to_analyze:
            anomalies = self.analyzer.analyze_packet(packet)
            if anomalies:
                individual_anomalies.extend(anomalies)

        # Batch analysis for patterns
        batch_results = self.analyzer.analyze_batch(packets_to_analyze)

        return {
            'packets_analyzed': len(packets_to_analyze),
            'individual_anomalies': individual_anomalies,
            'batch_anomalies': batch_results['anomalies'],
            'total_anomalies': len(individual_anomalies) + len(batch_results['anomalies'])
        }

    def toggle_anomaly_mode(self):
        """Toggle anomaly generation mode."""
        self.anomaly_mode = not self.anomaly_mode
        status = "enabled" if self.anomaly_mode else "disabled"
        logging.info(f"Anomaly generation mode {status}")
        return self.anomaly_mode

    def clear_packets(self, older_than_minutes: Optional[int] = None):
        """
        Clear packet history.

        Args:
            older_than_minutes: If provided, only clear packets older than this
        """
        if older_than_minutes:
            cutoff = datetime.now() - timedelta(minutes=older_than_minutes)
            self.packets = [p for p in self.packets if p.timestamp >= cutoff]
            logging.info(f"Cleared packets older than {older_than_minutes} minutes")
        else:
            self.packets.clear()
            logging.info("Cleared all packets")

    def get_traffic_summary(self) -> Dict:
        """Get a summary of managed traffic."""
        return {
            'total_generated': self.generation_count,
            'packets_in_memory': len(self.packets),
            'anomaly_mode': self.anomaly_mode,
            'oldest_packet': min(p.timestamp for p in self.packets) if self.packets else None,
            'newest_packet': max(p.timestamp for p in self.packets) if self.packets else None
        }


def print_menu():
    """Display the main menu."""
    print("\n" + "=" * 50)
    print("NETWORK TRAFFIC ANALYZER")
    print("=" * 50)
    print("1. Generate simulated traffic")
    print("2. Analyze traffic")
    print("3. View anomalies")
    print("4. View traffic statistics")
    print("5. Toggle anomaly generation mode")
    print("6. Clear data")
    print("7. Show recent packets")
    print("8. Help")
    print("9. Exit")
    print("-" * 50)


def print_help():
    """Display help information."""
    print("\n" + "=" * 50)
    print("HELP")
    print("=" * 50)
    print("This program simulates network traffic and detects anomalies.")
    print("\nFeatures:")
    print("- Generate realistic network packets with various protocols")
    print("- Detect suspicious port usage (e.g., SSH, RDP, database ports)")
    print("- Identify abnormal packet sizes (too small or too large)")
    print("- Find high traffic patterns from single IP addresses")
    print("- Track protocol distribution and top talkers")
    print("\nAnomaly Generation Mode:")
    print("- When enabled, generates packets with more suspicious patterns")
    print("- Helps test the detection capabilities")
    print("\nCommands:")
    print("1. Generate traffic - Create new simulated packets")
    print("2. Analyze - Run detection on all packets")
    print("3. View anomalies - See all detected suspicious activities")
    print("4. Statistics - View traffic metrics and distributions")
    print("\nPress Enter to continue...")
    input()


def main():
    """Main program loop."""
    manager = TrafficManager()

    # Generate some initial packets
    print("Initializing traffic analyzer...")
    manager.generate_traffic(20)

    while True:
        try:
            print_menu()
            choice = input("Enter your choice (1-9): ").strip()

            if choice == '1':
                try:
                    count = int(input("How many packets to generate? (default 10): ") or "10")
                    if count <= 0 or count > 1000:
                        print("Please enter a number between 1 and 1000")
                        continue
                    packets = manager.generate_traffic(count)
                    print(f"\n✅ Generated {len(packets)} packets")
                    if manager.anomaly_mode:
                        print("⚠️  Anomaly generation mode is ON - packets may contain suspicious patterns")
                except ValueError:
                    print("❌ Invalid number. Please enter a valid integer.")

            elif choice == '2':
                print("\nAnalyzing traffic...")
                results = manager.analyze_traffic()

                if 'error' in results:
                    print(f"❌ {results['error']}")
                else:
                    print(f"\n📊 Analysis Results:")
                    print(f"   Packets analyzed: {results['packets_analyzed']}")
                    print(f"   Total anomalies found: {results['total_anomalies']}")

                    if results['individual_anomalies']:
                        print("\n   🚨 Individual Packet Anomalies:")
                        for anomaly in results['individual_anomalies'][:5]:  # Show first 5
                            print(f"      • {anomaly}")
                        if len(results['individual_anomalies']) > 5:
                            print(f"      ... and {len(results['individual_anomalies']) - 5} more")

                    if results['batch_anomalies']:
                        print("\n   📈 Pattern Anomalies:")
                        for anomaly in results['batch_anomalies']:
                            print(f"      • {anomaly}")

            elif choice == '3':
                anomalies = manager.analyzer.get_anomalies(limit=20)
                if not anomalies:
                    print("\n✅ No anomalies detected")
                else:
                    print(f"\n🚨 Detected Anomalies ({len(anomalies)} total, showing most recent):")
                    for i, (timestamp, desc, packet) in enumerate(anomalies[:20], 1):
                        print(f"{i:2}. [{timestamp.strftime('%H:%M:%S')}] {desc}")
                        if packet:
                            print(f"     └─ {packet}")

            elif choice == '4':
                stats = manager.analyzer.get_statistics()
                if 'error' in stats:
                    print(f"\n❌ {stats['error']}")
                else:
                    print("\n📈 Traffic Statistics:")
                    print(f"   Total Packets: {stats['total_packets']}")
                    print(f"   Total Bytes: {stats['total_bytes']:,} bytes")
                    print(f"   Avg Packet Size: {stats['avg_packet_size']} bytes")
                    print(f"   Min/Max Size: {stats['min_packet_size']}/{stats['max_packet_size']} bytes")
                    print(f"   Unique Source IPs: {stats['unique_source_ips']}")

                    print("\n   Protocol Distribution:")
                    for proto, count in stats['protocol_distribution'].items():
                        print(f"      • {proto}: {count} packets")

                    if stats['top_talkers']:
                        print("\n   Top Talkers (by packets):")
                        for ip, count in stats['top_talkers'].items():
                            print(f"      • {ip}: {count} packets")

                    if stats['suspicious_ports_detected']:
                        print("\n   🚨 Suspicious Ports Detected:")
                        for port, count in stats['suspicious_ports_detected'].items():
                            print(f"      • Port {port}: {count} connections")

            elif choice == '5':
                new_mode = manager.toggle_anomaly_mode()
                status = "ENABLED" if new_mode else "DISABLED"
                print(f"\n🔔 Anomaly generation mode: {status}")

            elif choice == '6':
                print("\nClear options:")
                print("1. Clear all packets")
                print("2. Clear anomaly history only")
                print("3. Clear both")
                clear_choice = input("Enter choice (1-3): ").strip()

                if clear_choice == '1':
                    manager.clear_packets()
                    print("✅ All packets cleared")
                elif clear_choice == '2':
                    manager.analyzer.clear_anomalies()
                    print("✅ Anomaly history cleared")
                elif clear_choice == '3':
                    manager.clear_packets()
                    manager.analyzer.clear_anomalies()
                    print("✅ All data cleared")
                else:
                    print("❌ Invalid choice")

            elif choice == '7':
                summary = manager.get_traffic_summary()
                print("\n📦 Traffic Summary:")
                print(f"   Total packets generated: {summary['total_generated']}")
                print(f"   Packets in memory: {summary['packets_in_memory']}")
                print(f"   Anomaly mode: {'ON' if summary['anomaly_mode'] else 'OFF'}")

                if summary['packets_in_memory'] > 0:
                    print(f"   Time range: {summary['oldest_packet'].strftime('%H:%M:%S')} - "
                          f"{summary['newest_packet'].strftime('%H:%M:%S')}")

                    print("\n   Recent Packets (last 5):")
                    for packet in manager.packets[-5:]:
                        print(f"      • {packet}")

            elif choice == '8':
                print_help()

            elif choice == '9':
                print("\n👋 Exiting Network Traffic Analyzer. Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter a number between 1 and 9.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()