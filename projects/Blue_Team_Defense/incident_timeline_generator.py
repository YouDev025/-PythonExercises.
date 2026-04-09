#!/usr/bin/env python3
"""
Incident Timeline Generator
A comprehensive tool for reconstructing security incident timelines from event logs,
identifying attack patterns, and visualizing the sequence of security events.

Author: Senior Python Developer & Cybersecurity Engineer
Version: 1.0.0
"""

import json
import sys
import random
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib


class EventSeverity(Enum):
    """Security event severity levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    def __lt__(self, other):
        """Allow severity comparison for sorting."""
        order = {EventSeverity.LOW: 1, EventSeverity.MEDIUM: 2,
                 EventSeverity.HIGH: 3, EventSeverity.CRITICAL: 4}
        return order[self] < order[other]


class EventType(Enum):
    """Types of security events in incident timeline."""
    LOGIN_SUCCESS = "Login Success"
    LOGIN_FAILURE = "Login Failure"
    FILE_ACCESS = "File Access"
    FILE_MODIFY = "File Modify"
    FILE_DELETE = "File Delete"
    NETWORK_CONNECTION = "Network Connection"
    ALERT = "Security Alert"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    PROCESS_EXECUTION = "Process Execution"
    REGISTRY_CHANGE = "Registry Change"
    DATA_EXFILTRATION = "Data Exfiltration"
    RECONNAISSANCE = "Reconnaissance"
    EXPLOIT_ATTEMPT = "Exploit Attempt"
    PERSISTENCE = "Persistence Setup"
    COMMAND_EXECUTION = "Command Execution"
    MALWARE_DETECTED = "Malware Detected"


class IncidentPhase(Enum):
    """Phases of a security incident based on Cyber Kill Chain."""
    INITIAL_ACCESS = "Initial Access"
    RECONNAISSANCE = "Reconnaissance"
    EXPLOITATION = "Exploitation"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    PERSISTENCE = "Persistence"
    LATERAL_MOVEMENT = "Lateral Movement"
    COLLECTION = "Collection"
    EXFILTRATION = "Exfiltration"
    IMPACT = "Impact"
    UNKNOWN = "Unknown"


@dataclass
class SecurityEvent:
    """Represents a single security event in the timeline."""
    timestamp: datetime
    source: str
    source_ip: str
    event_type: EventType
    description: str
    severity: EventSeverity
    target: Optional[str] = None
    incident_id: Optional[str] = None
    phase: IncidentPhase = IncidentPhase.UNKNOWN
    event_hash: str = field(default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])

    def __post_init__(self):
        """Validate and convert types after initialization."""
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if isinstance(self.event_type, str):
            self.event_type = EventType(self.event_type)
        if isinstance(self.severity, str):
            self.severity = EventSeverity(self.severity)
        if isinstance(self.phase, str):
            self.phase = IncidentPhase(self.phase)

    def to_dict(self) -> Dict:
        """Convert event to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['phase'] = self.phase.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'SecurityEvent':
        """Create event from dictionary."""
        return cls(**data)

    def get_time_str(self, include_date: bool = True) -> str:
        """Get formatted timestamp string."""
        if include_date:
            return self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return self.timestamp.strftime('%H:%M:%S')

    def is_suspicious(self) -> bool:
        """Check if event is suspicious based on type and severity."""
        suspicious_types = {
            EventType.LOGIN_FAILURE,
            EventType.EXPLOIT_ATTEMPT,
            EventType.PRIVILEGE_ESCALATION,
            EventType.MALWARE_DETECTED,
            EventType.DATA_EXFILTRATION
        }
        return (self.event_type in suspicious_types or
                self.severity in [EventSeverity.HIGH, EventSeverity.CRITICAL])


class Incident:
    """Represents a security incident composed of related events."""

    def __init__(self, incident_id: str, name: str):
        self.incident_id = incident_id
        self.name = name
        self.events: List[SecurityEvent] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.affected_systems: Set[str] = set()
        self.affected_ips: Set[str] = set()
        self.primary_source: Optional[str] = None

    def add_event(self, event: SecurityEvent):
        """Add event to incident and update metadata."""
        self.events.append(event)
        event.incident_id = self.incident_id

        # Update time boundaries
        if not self.start_time or event.timestamp < self.start_time:
            self.start_time = event.timestamp
        if not self.end_time or event.timestamp > self.end_time:
            self.end_time = event.timestamp

        # Track affected systems
        self.affected_systems.add(event.source)
        if event.target:
            self.affected_systems.add(event.target)
        self.affected_ips.add(event.source_ip)

        # Determine primary source
        if not self.primary_source:
            self.primary_source = event.source_ip

    def get_duration(self) -> Optional[timedelta]:
        """Get incident duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def get_phase_sequence(self) -> List[IncidentPhase]:
        """Get ordered sequence of incident phases."""
        phases = []
        for event in sorted(self.events, key=lambda e: e.timestamp):
            if event.phase != IncidentPhase.UNKNOWN and (not phases or phases[-1] != event.phase):
                phases.append(event.phase)
        return phases

    def get_severity_summary(self) -> Dict[str, int]:
        """Get count of events by severity."""
        summary = defaultdict(int)
        for event in self.events:
            summary[event.severity.value] += 1
        return dict(summary)

    def get_high_severity_count(self) -> int:
        """Get count of high/critical severity events."""
        return sum(1 for e in self.events
                   if e.severity in [EventSeverity.HIGH, EventSeverity.CRITICAL])


class EventCorrelator:
    """Correlates security events into incidents based on patterns."""

    def __init__(self):
        self.incident_counter = 1

    def correlate_events(self, events: List[SecurityEvent]) -> List[Incident]:
        """
        Group events into incidents based on:
        - Common source IP
        - Temporal proximity
        - Related targets
        - Attack patterns
        """
        if not events:
            return []

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Initialize clustering
        incidents: List[Incident] = []
        assigned_events: Set[str] = set()

        # First pass: group by source IP within time windows
        time_window = timedelta(hours=2)

        for event in sorted_events:
            if event.event_hash in assigned_events:
                continue

            # Find or create incident for this source
            incident = self._find_matching_incident(event, incidents, time_window)

            if not incident:
                incident = self._create_new_incident(event)
                incidents.append(incident)

            # Add event and find related events
            self._add_related_events(event, sorted_events, incident,
                                     assigned_events, time_window)

        # Second pass: merge overlapping incidents
        incidents = self._merge_overlapping_incidents(incidents)

        # Assign incident IDs and names
        for i, incident in enumerate(incidents, 1):
            if not incident.incident_id:
                incident.incident_id = f"INC-{i:03d}"
            if not incident.name:
                incident.name = self._generate_incident_name(incident)

        return incidents

    def _find_matching_incident(self, event: SecurityEvent,
                                incidents: List[Incident],
                                time_window: timedelta) -> Optional[Incident]:
        """Find incident matching the event based on source and time."""
        for incident in incidents:
            # Check source IP match
            if event.source_ip in incident.affected_ips:
                # Check temporal proximity
                if incident.end_time and event.timestamp <= incident.end_time + time_window:
                    return incident

            # Check source system match
            if event.source in incident.affected_systems:
                if incident.end_time and event.timestamp <= incident.end_time + time_window:
                    return incident

        return None

    def _create_new_incident(self, event: SecurityEvent) -> Incident:
        """Create a new incident from an event."""
        incident_id = f"INC-{self.incident_counter:03d}"
        self.incident_counter += 1
        return Incident(incident_id, f"Security Incident {incident_id}")

    def _add_related_events(self, seed_event: SecurityEvent,
                            all_events: List[SecurityEvent],
                            incident: Incident,
                            assigned_events: Set[str],
                            time_window: timedelta):
        """Add events related to the seed event to the incident."""
        incident.add_event(seed_event)
        assigned_events.add(seed_event.event_hash)

        # Look for related events
        for event in all_events:
            if event.event_hash in assigned_events:
                continue

            # Check if related
            is_related = False

            # Same source IP
            if event.source_ip == seed_event.source_ip:
                is_related = True

            # Same source system
            elif event.source == seed_event.source:
                is_related = True

            # Target matches source
            elif event.target and event.target in incident.affected_systems:
                is_related = True

            # Temporal proximity to incident
            elif (incident.start_time and incident.end_time and
                  incident.start_time - time_window <= event.timestamp <= incident.end_time + time_window and
                  (event.source_ip in incident.affected_ips or event.source in incident.affected_systems)):
                is_related = True

            if is_related:
                incident.add_event(event)
                assigned_events.add(event.event_hash)

                # Recursively find more related events
                self._add_related_events(event, all_events, incident,
                                         assigned_events, time_window)

    def _merge_overlapping_incidents(self, incidents: List[Incident]) -> List[Incident]:
        """Merge incidents that share systems/IPs and overlap in time."""
        if len(incidents) <= 1:
            return incidents

        merged = []
        used = set()

        for i, incident1 in enumerate(incidents):
            if i in used:
                continue

            current = Incident(incident1.incident_id, incident1.name)
            for event in incident1.events:
                current.add_event(event)

            # Look for overlapping incidents
            for j, incident2 in enumerate(incidents[i + 1:], i + 1):
                if j in used:
                    continue

                # Check overlap
                if self._incidents_overlap(current, incident2):
                    for event in incident2.events:
                        current.add_event(event)
                    used.add(j)

            merged.append(current)
            used.add(i)

        return merged

    def _incidents_overlap(self, inc1: Incident, inc2: Incident) -> bool:
        """Check if two incidents overlap in time and share resources."""
        if not inc1.start_time or not inc1.end_time or not inc2.start_time or not inc2.end_time:
            return False

        # Check time overlap
        time_overlap = (inc1.start_time <= inc2.end_time and inc2.start_time <= inc1.end_time)

        # Check resource overlap
        resource_overlap = (bool(inc1.affected_ips & inc2.affected_ips) or
                            bool(inc1.affected_systems & inc2.affected_systems))

        return time_overlap and resource_overlap

    def _generate_incident_name(self, incident: Incident) -> str:
        """Generate descriptive name for incident based on events."""
        phases = incident.get_phase_sequence()
        high_sev_count = incident.get_high_severity_count()

        if not phases:
            return f"Suspicious Activity from {incident.primary_source}"

        if IncidentPhase.EXFILTRATION in phases:
            return f"Data Exfiltration Incident - {incident.primary_source}"
        elif IncidentPhase.EXPLOITATION in phases:
            return f"Exploitation Attempt - {incident.primary_source}"
        elif IncidentPhase.PERSISTENCE in phases:
            return f"Persistence Mechanism Detected - {incident.primary_source}"
        elif IncidentPhase.RECONNAISSANCE in phases:
            return f"Reconnaissance Activity - {incident.primary_source}"
        elif high_sev_count > 3:
            return f"High Severity Security Incident - {incident.primary_source}"
        else:
            return f"Security Event Cluster - {incident.primary_source}"


class PhaseClassifier:
    """Classifies events into incident phases based on event type and patterns."""

    @staticmethod
    def classify_event(event: SecurityEvent) -> IncidentPhase:
        """Determine the incident phase for a given event."""
        event_type = event.event_type

        # Initial Access
        if event_type in [EventType.LOGIN_SUCCESS, EventType.LOGIN_FAILURE]:
            return IncidentPhase.INITIAL_ACCESS

        # Reconnaissance
        elif event_type in [EventType.RECONNAISSANCE, EventType.NETWORK_CONNECTION]:
            if "scan" in event.description.lower() or "probe" in event.description.lower():
                return IncidentPhase.RECONNAISSANCE
            return IncidentPhase.RECONNAISSANCE

        # Exploitation
        elif event_type in [EventType.EXPLOIT_ATTEMPT, EventType.ALERT]:
            if "exploit" in event.description.lower() or "vulnerability" in event.description.lower():
                return IncidentPhase.EXPLOITATION
            return IncidentPhase.EXPLOITATION

        # Privilege Escalation
        elif event_type == EventType.PRIVILEGE_ESCALATION:
            return IncidentPhase.PRIVILEGE_ESCALATION

        # Persistence
        elif event_type in [EventType.PERSISTENCE, EventType.REGISTRY_CHANGE]:
            return IncidentPhase.PERSISTENCE

        # Lateral Movement
        elif event_type in [EventType.NETWORK_CONNECTION, EventType.COMMAND_EXECUTION]:
            if "lateral" in event.description.lower() or "remote" in event.description.lower():
                return IncidentPhase.LATERAL_MOVEMENT
            return IncidentPhase.UNKNOWN

        # Collection
        elif event_type in [EventType.FILE_ACCESS, EventType.FILE_MODIFY]:
            return IncidentPhase.COLLECTION

        # Exfiltration
        elif event_type in [EventType.DATA_EXFILTRATION, EventType.FILE_DELETE]:
            return IncidentPhase.EXFILTRATION

        # Impact
        elif event_type in [EventType.MALWARE_DETECTED, EventType.ALERT]:
            if event.severity == EventSeverity.CRITICAL:
                return IncidentPhase.IMPACT
            return IncidentPhase.UNKNOWN

        else:
            return IncidentPhase.UNKNOWN


class TimelineGenerator:
    """Generates and manages security incident timelines."""

    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.incidents: List[Incident] = []
        self.correlator = EventCorrelator()

    def add_event(self, event: SecurityEvent):
        """Add a security event to the timeline."""
        # Classify phase if not set
        if event.phase == IncidentPhase.UNKNOWN:
            event.phase = PhaseClassifier.classify_event(event)

        self.events.append(event)

    def generate_timeline(self):
        """Generate incidents from events."""
        if not self.events:
            return

        # Sort events
        self.events.sort(key=lambda e: e.timestamp)

        # Correlate into incidents
        self.incidents = self.correlator.correlate_events(self.events)

        # Sort incidents by start time
        self.incidents.sort(key=lambda i: i.start_time if i.start_time else datetime.max)

    def generate_sample_events(self, num_events: int = 50):
        """Generate realistic sample security events."""

        # Sample data pools
        source_ips = [
            "192.168.1.100", "10.0.0.15", "172.16.0.22",
            "203.0.113.45", "198.51.100.78", "185.142.53.129",
            "45.155.205.233", "103.145.12.88"
        ]

        systems = [
            "WEB-SRV-01", "DB-SRV-02", "AD-DC-01", "FILE-SRV-03",
            "APP-SRV-04", "JUMP-BOX-01", "WORKSTATION-15"
        ]

        users = ["admin", "jsmith", "mwilson", "system", "backup_svc", "sql_agent"]

        # Create base timeline starting 24 hours ago
        base_time = datetime.now() - timedelta(hours=24)

        # Generate different types of incidents
        self._generate_reconnaissance_incident(base_time, source_ips, systems, users)
        self._generate_exploitation_incident(base_time + timedelta(hours=2), source_ips, systems, users)
        self._generate_data_exfiltration_incident(base_time + timedelta(hours=4), source_ips, systems, users)
        self._generate_persistence_incident(base_time + timedelta(hours=6), source_ips, systems, users)

        # Add some random legitimate events
        for i in range(20):
            timestamp = base_time + timedelta(minutes=random.randint(0, 1440))
            source_system = random.choice(systems)
            source_ip = random.choice(["192.168.1.50", "10.0.0.10", "172.16.0.5"])

            event = SecurityEvent(
                timestamp=timestamp,
                source=f"{random.choice(users)}@{source_system}",
                source_ip=source_ip,
                event_type=random.choice([EventType.LOGIN_SUCCESS, EventType.FILE_ACCESS,
                                          EventType.NETWORK_CONNECTION]),
                description=f"Normal {random.choice(['user activity', 'system process', 'scheduled task'])}",
                severity=EventSeverity.LOW,
                target=random.choice(systems)
            )
            self.add_event(event)

    def _generate_reconnaissance_incident(self, base_time: datetime,
                                          source_ips: List[str],
                                          systems: List[str],
                                          users: List[str]):
        """Generate reconnaissance phase events."""
        attacker_ip = "185.142.53.129"

        events = [
            (base_time + timedelta(minutes=5), EventType.NETWORK_CONNECTION,
             "Port scan detected on multiple ports", EventSeverity.MEDIUM),
            (base_time + timedelta(minutes=8), EventType.RECONNAISSANCE,
             "Web server fingerprinting attempt", EventSeverity.MEDIUM),
            (base_time + timedelta(minutes=12), EventType.LOGIN_FAILURE,
             "Failed SSH login attempt - user: root", EventSeverity.LOW),
            (base_time + timedelta(minutes=15), EventType.NETWORK_CONNECTION,
             "Directory enumeration detected", EventSeverity.MEDIUM),
            (base_time + timedelta(minutes=20), EventType.ALERT,
             "Multiple failed login attempts detected", EventSeverity.MEDIUM),
        ]

        for timestamp, event_type, desc, severity in events:
            event = SecurityEvent(
                timestamp=timestamp,
                source=f"external@{attacker_ip}",
                source_ip=attacker_ip,
                event_type=event_type,
                description=desc,
                severity=severity,
                target="WEB-SRV-01"
            )
            self.add_event(event)

    def _generate_exploitation_incident(self, base_time: datetime,
                                        source_ips: List[str],
                                        systems: List[str],
                                        users: List[str]):
        """Generate exploitation phase events."""
        attacker_ip = "185.142.53.129"

        events = [
            (base_time, EventType.EXPLOIT_ATTEMPT,
             "SQL injection attempt detected", EventSeverity.HIGH),
            (base_time + timedelta(minutes=3), EventType.ALERT,
             "Potential remote code execution", EventSeverity.HIGH),
            (base_time + timedelta(minutes=7), EventType.PRIVILEGE_ESCALATION,
             "Privilege escalation attempt via CVE-2024-1234", EventSeverity.CRITICAL),
            (base_time + timedelta(minutes=10), EventType.PROCESS_EXECUTION,
             "Suspicious process spawned: cmd.exe from web server", EventSeverity.HIGH),
            (base_time + timedelta(minutes=12), EventType.COMMAND_EXECUTION,
             "PowerShell command with encoded parameters", EventSeverity.HIGH),
        ]

        for timestamp, event_type, desc, severity in events:
            event = SecurityEvent(
                timestamp=timestamp,
                source=f"WEB-SRV-01\\IIS_APPPOOL",
                source_ip="192.168.1.100",
                event_type=event_type,
                description=desc,
                severity=severity,
                target="WEB-SRV-01"
            )
            self.add_event(event)

    def _generate_data_exfiltration_incident(self, base_time: datetime,
                                             source_ips: List[str],
                                             systems: List[str],
                                             users: List[str]):
        """Generate data exfiltration phase events."""

        events = [
            (base_time, EventType.FILE_ACCESS,
             "Access to sensitive database file", EventSeverity.MEDIUM),
            (base_time + timedelta(minutes=5), EventType.FILE_MODIFY,
             "Database dump created: customers.sql", EventSeverity.HIGH),
            (base_time + timedelta(minutes=15), EventType.NETWORK_CONNECTION,
             "Large outbound connection to 45.155.205.233:443", EventSeverity.HIGH),
            (base_time + timedelta(minutes=20), EventType.DATA_EXFILTRATION,
             "Suspicious data transfer: 2.4GB to external IP", EventSeverity.CRITICAL),
            (base_time + timedelta(minutes=25), EventType.FILE_DELETE,
             "Log file deletion detected", EventSeverity.HIGH),
        ]

        for timestamp, event_type, desc, severity in events:
            event = SecurityEvent(
                timestamp=timestamp,
                source="DB-SRV-02\\SQLSERVER",
                source_ip="10.0.0.15",
                event_type=event_type,
                description=desc,
                severity=severity,
                target="45.155.205.233"
            )
            self.add_event(event)

    def _generate_persistence_incident(self, base_time: datetime,
                                       source_ips: List[str],
                                       systems: List[str],
                                       users: List[str]):
        """Generate persistence mechanism events."""

        events = [
            (base_time, EventType.REGISTRY_CHANGE,
             "New Run key added: WindowsUpdate", EventSeverity.HIGH),
            (base_time + timedelta(minutes=2), EventType.PERSISTENCE,
             "Scheduled task created: SystemMaintenance", EventSeverity.HIGH),
            (base_time + timedelta(minutes=5), EventType.FILE_MODIFY,
             "New service binary written to System32", EventSeverity.CRITICAL),
            (base_time + timedelta(minutes=8), EventType.PROCESS_EXECUTION,
             "Persistence mechanism triggered", EventSeverity.HIGH),
        ]

        for timestamp, event_type, desc, severity in events:
            event = SecurityEvent(
                timestamp=timestamp,
                source="WORKSTATION-15\\SYSTEM",
                source_ip="192.168.1.150",
                event_type=event_type,
                description=desc,
                severity=severity,
                target="WORKSTATION-15"
            )
            self.add_event(event)

    def get_all_events_sorted(self) -> List[SecurityEvent]:
        """Get all events sorted by timestamp."""
        return sorted(self.events, key=lambda e: e.timestamp)

    def format_timeline_display(self, incident: Optional[Incident] = None) -> str:
        """Format timeline for display."""
        if incident:
            events_to_show = sorted(incident.events, key=lambda e: e.timestamp)
            title = f"INCIDENT TIMELINE: {incident.name} ({incident.incident_id})"
        else:
            events_to_show = self.get_all_events_sorted()
            title = "COMPLETE EVENT TIMELINE"

        lines = []
        lines.append("=" * 120)
        lines.append(f"{title:^120}")
        lines.append("=" * 120)

        if incident:
            duration = incident.get_duration()
            if duration:
                lines.append(f"Duration: {duration}")
            lines.append(f"Affected Systems: {', '.join(incident.affected_systems)}")
            lines.append(f"Source IPs: {', '.join(incident.affected_ips)}")
            lines.append("-" * 120)

        # Table header
        lines.append(
            f"{'Timestamp':<20} {'Phase':<20} {'Event Type':<25} {'Source':<20} {'Severity':<10} {'Description'}")
        lines.append("-" * 120)

        current_date = None

        for event in events_to_show:
            # Add date separator if date changes
            event_date = event.timestamp.strftime('%Y-%m-%d')
            if event_date != current_date:
                current_date = event_date
                lines.append(f"\n{'=' * 40} {current_date} {'=' * 40}\n")

            # Format severity with color indicators
            severity_str = event.severity.value
            if event.severity == EventSeverity.CRITICAL:
                severity_str = f"🔴 {severity_str}"
            elif event.severity == EventSeverity.HIGH:
                severity_str = f"🟠 {severity_str}"
            elif event.severity == EventSeverity.MEDIUM:
                severity_str = f"🟡 {severity_str}"
            else:
                severity_str = f"🟢 {severity_str}"

            # Format phase
            phase_str = event.phase.value if event.phase != IncidentPhase.UNKNOWN else "-"

            # Truncate long strings
            source = event.source[:18] + ".." if len(event.source) > 20 else event.source
            desc = event.description[:30] + ".." if len(event.description) > 32 else event.description

            line = (f"{event.get_time_str():<20} {phase_str:<20} {event.event_type.value:<25} "
                    f"{source:<20} {severity_str:<10} {desc}")
            lines.append(line)

        lines.append("=" * 120)

        if incident:
            # Add summary
            lines.append(f"\nINCIDENT SUMMARY:")
            lines.append(f"  Total Events: {len(incident.events)}")
            severity_summary = incident.get_severity_summary()
            lines.append(f"  Severity Breakdown: {severity_summary}")
            phases = incident.get_phase_sequence()
            if phases:
                lines.append(f"  Attack Phases: {' → '.join([p.value for p in phases])}")

        return "\n".join(lines)

    def format_incidents_summary(self) -> str:
        """Format summary of all incidents."""
        lines = []
        lines.append("=" * 100)
        lines.append(f"{'INCIDENTS OVERVIEW':^100}")
        lines.append("=" * 100)
        lines.append("")

        if not self.incidents:
            lines.append("No incidents identified. Generate sample data first.")
            return "\n".join(lines)

        lines.append(f"{'ID':<10} {'Name':<35} {'Start Time':<20} {'Events':<8} {'High Sev':<10} {'Systems':<15}")
        lines.append("-" * 100)

        for incident in self.incidents:
            id_str = incident.incident_id
            name = incident.name[:33] + ".." if len(incident.name) > 35 else incident.name
            start_time = incident.start_time.strftime('%Y-%m-%d %H:%M') if incident.start_time else "N/A"
            events_count = len(incident.events)
            high_sev = incident.get_high_severity_count()
            systems = len(incident.affected_systems)

            lines.append(f"{id_str:<10} {name:<35} {start_time:<20} {events_count:<8} {high_sev:<10} {systems:<15}")

        lines.append("=" * 100)

        return "\n".join(lines)

    def export_timeline(self, filename: str = "incident_timeline.txt") -> str:
        """Export complete timeline to file."""
        try:
            with open(filename, 'w') as f:
                # Write header
                f.write("SECURITY INCIDENT TIMELINE REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 120 + "\n\n")

                # Write incidents summary
                f.write(self.format_incidents_summary())
                f.write("\n\n")

                # Write detailed timeline for each incident
                for incident in self.incidents:
                    f.write(self.format_timeline_display(incident))
                    f.write("\n\n")

                # Write orphaned events (not in any incident)
                incident_events = set()
                for incident in self.incidents:
                    incident_events.update(e.event_hash for e in incident.events)

                orphaned = [e for e in self.events if e.event_hash not in incident_events]
                if orphaned:
                    f.write("=" * 120 + "\n")
                    f.write("UNCORRELATED EVENTS\n")
                    f.write("=" * 120 + "\n")
                    for event in sorted(orphaned, key=lambda e: e.timestamp):
                        f.write(f"{event.get_time_str()} - {event.event_type.value} - {event.description}\n")

            return f"Timeline exported successfully to {filename}"
        except Exception as e:
            return f"Error exporting timeline: {e}"

    def export_json(self, filename: str = "incident_timeline.json") -> str:
        """Export timeline data to JSON."""
        try:
            data = {
                "export_date": datetime.now().isoformat(),
                "events": [e.to_dict() for e in self.events],
                "incidents": [
                    {
                        "incident_id": inc.incident_id,
                        "name": inc.name,
                        "start_time": inc.start_time.isoformat() if inc.start_time else None,
                        "end_time": inc.end_time.isoformat() if inc.end_time else None,
                        "affected_systems": list(inc.affected_systems),
                        "affected_ips": list(inc.affected_ips),
                        "primary_source": inc.primary_source,
                        "events": [e.event_hash for e in inc.events],
                        "phase_sequence": [p.value for p in inc.get_phase_sequence()],
                        "severity_summary": inc.get_severity_summary()
                    }
                    for inc in self.incidents
                ]
            }

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            return f"JSON data exported successfully to {filename}"
        except Exception as e:
            return f"Error exporting JSON: {e}"


class CLI:
    """Command Line Interface for Incident Timeline Generator."""

    def __init__(self):
        self.generator = TimelineGenerator()
        self.running = True

    def clear_screen(self):
        """Clear terminal screen."""
        print("\033[2J\033[H", end="")

    def print_header(self, title: str):
        """Print formatted header."""
        print("\n" + "=" * 100)
        print(f" {title:^96} ")
        print("=" * 100)

    def print_menu(self):
        """Display main menu options."""
        self.clear_screen()
        self.print_header("INCIDENT TIMELINE GENERATOR")
        print("\n📋 MAIN MENU:")
        print("-" * 50)
        print("  1. Generate Sample Security Events")
        print("  2. Build Incident Timeline")
        print("  3. View All Incidents Summary")
        print("  4. View Complete Event Timeline")
        print("  5. View Specific Incident Timeline")
        print("  6. Analyze Attack Patterns")
        print("  7. View High Severity Events")
        print("  8. Export Timeline Report (TXT)")
        print("  9. Export Timeline Data (JSON)")
        print("  0. Exit")
        print("-" * 50)
        print(f"\n📊 Current Status: {len(self.generator.events)} events, "
              f"{len(self.generator.incidents)} incidents")

    def display_incidents_summary(self):
        """Display summary of all incidents."""
        self.clear_screen()

        if not self.generator.incidents:
            self.print_header("NO INCIDENTS FOUND")
            print("\n⚠️  No incidents have been generated yet.")
            print("   Please generate sample events and build timeline first.")
            return

        print(self.generator.format_incidents_summary())

    def display_complete_timeline(self):
        """Display complete event timeline."""
        self.clear_screen()

        if not self.generator.events:
            self.print_header("NO EVENTS FOUND")
            print("\n⚠️  No events available. Generate sample data first.")
            return

        timeline = self.generator.format_timeline_display()
        print(timeline)

    def display_incident_timeline(self):
        """Display timeline for a specific incident."""
        self.clear_screen()

        if not self.generator.incidents:
            self.print_header("NO INCIDENTS FOUND")
            print("\n⚠️  No incidents available. Build timeline first.")
            return

        self.print_header("SELECT INCIDENT")

        for i, incident in enumerate(self.generator.incidents, 1):
            events_count = len(incident.events)
            high_sev = incident.get_high_severity_count()
            start_time = incident.start_time.strftime('%Y-%m-%d %H:%M') if incident.start_time else "N/A"

            print(f"\n  {i}. {incident.name}")
            print(f"     ID: {incident.incident_id} | Start: {start_time} | "
                  f"Events: {events_count} | High Sev: {high_sev}")

        try:
            choice = input(f"\nSelect incident (1-{len(self.generator.incidents)}) or 0 to cancel: ").strip()

            if choice == '0':
                return

            idx = int(choice) - 1
            if 0 <= idx < len(self.generator.incidents):
                self.clear_screen()
                incident = self.generator.incidents[idx]
                timeline = self.generator.format_timeline_display(incident)
                print(timeline)
            else:
                print("\n❌ Invalid selection!")

        except (ValueError, KeyboardInterrupt):
            print("\n❌ Operation cancelled.")

    def analyze_attack_patterns(self):
        """Analyze and display attack patterns across incidents."""
        self.clear_screen()
        self.print_header("ATTACK PATTERN ANALYSIS")

        if not self.generator.incidents:
            print("\n⚠️  No incidents available for analysis.")
            return

        print("\n🔍 ATTACK CHAIN ANALYSIS:\n")

        for incident in self.generator.incidents:
            print(f"\n📌 {incident.name} ({incident.incident_id})")
            print("-" * 80)

            phases = incident.get_phase_sequence()
            if phases:
                print("  Attack Progression:")
                for i, phase in enumerate(phases):
                    arrow = "└─" if i == len(phases) - 1 else "├─"
                    print(f"    {arrow} {phase.value}")

            # Identify suspicious sequences
            events = sorted(incident.events, key=lambda e: e.timestamp)

            # Check for rapid fire events
            if len(events) > 5:
                time_span = (events[-1].timestamp - events[0].timestamp).total_seconds()
                if time_span < 300:  # Less than 5 minutes
                    print(f"  ⚠️  Rapid event sequence: {len(events)} events in {time_span:.1f} seconds")

            # Check for privilege escalation followed by persistence
            has_priv_esc = any(e.phase == IncidentPhase.PRIVILEGE_ESCALATION for e in events)
            has_persistence = any(e.phase == IncidentPhase.PERSISTENCE for e in events)
            if has_priv_esc and has_persistence:
                print("  ⚠️  Privilege escalation followed by persistence - Critical finding!")

            # Check for data exfiltration
            has_exfil = any(e.phase == IncidentPhase.EXFILTRATION for e in events)
            if has_exfil:
                print("  🔴 DATA EXFILTRATION DETECTED - Immediate action required!")

        print("\n" + "=" * 80)

    def display_high_severity_events(self):
        """Display high and critical severity events."""
        self.clear_screen()
        self.print_header("HIGH SEVERITY EVENTS")

        high_events = [e for e in self.generator.events
                       if e.severity in [EventSeverity.HIGH, EventSeverity.CRITICAL]]

        if not high_events:
            print("\n✅ No high severity events found.")
            return

        high_events.sort(key=lambda e: (e.severity, e.timestamp), reverse=True)

        print(f"\n🚨 Found {len(high_events)} high/critical severity events:\n")
        print(f"{'Timestamp':<20} {'Severity':<12} {'Event Type':<25} {'Source':<25} {'Description'}")
        print("-" * 120)

        for event in high_events[:30]:
            severity_str = event.severity.value
            icon = '🔴' if event.severity == EventSeverity.CRITICAL else '🟠'

            print(f"{event.get_time_str():<20} {icon} {severity_str:<9} "
                  f"{event.event_type.value:<25} {event.source[:23]:<25} {event.description[:40]}")

        if len(high_events) > 30:
            print(f"\n... and {len(high_events) - 30} more high severity events")

    def run(self):
        """Main CLI loop."""
        while self.running:
            self.print_menu()

            try:
                choice = input("\nEnter your choice (0-9): ").strip()

                if choice == '1':
                    self.generator.generate_sample_events()
                    print(f"\n✅ Generated {len(self.generator.events)} sample security events!")
                    print("   Use option 2 to build the incident timeline.")

                elif choice == '2':
                    if not self.generator.events:
                        print("\n⚠️  No events available. Generate sample data first.")
                    else:
                        self.generator.generate_timeline()
                        print(f"\n✅ Timeline built successfully!")
                        print(f"   Identified {len(self.generator.incidents)} distinct incidents.")

                elif choice == '3':
                    self.display_incidents_summary()

                elif choice == '4':
                    self.display_complete_timeline()

                elif choice == '5':
                    self.display_incident_timeline()

                elif choice == '6':
                    self.analyze_attack_patterns()

                elif choice == '7':
                    self.display_high_severity_events()

                elif choice == '8':
                    if not self.generator.events:
                        print("\n⚠️  No data to export. Generate sample data first.")
                    else:
                        result = self.generator.export_timeline()
                        print(f"\n📄 {result}")

                elif choice == '9':
                    if not self.generator.events:
                        print("\n⚠️  No data to export. Generate sample data first.")
                    else:
                        result = self.generator.export_json()
                        print(f"\n💾 {result}")

                elif choice == '0':
                    self.running = False
                    print("\n👋 Thank you for using Incident Timeline Generator. Stay secure!")

                else:
                    print("\n❌ Invalid choice! Please enter a number between 0 and 9.")

                if choice != '0':
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\n⚠️  Operation cancelled by user.")
                input("Press Enter to continue...")
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                import traceback
                traceback.print_exc()
                input("Press Enter to continue...")


def main():
    """Entry point for the application."""
    cli = CLI()

    # Check Python version
    if sys.version_info[0] < 3:
        print("Error: This program requires Python 3.6 or higher.")
        sys.exit(1)

    cli.run()


if __name__ == "__main__":
    main()