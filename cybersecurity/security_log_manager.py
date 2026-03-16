import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from collections import Counter, defaultdict


class SeverityLevel(Enum):
    """Enumeration for log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Enumeration for security event types."""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    FILE_ACCESS = "FILE_ACCESS"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    AUTH_FAILURE = "AUTH_FAILURE"
    NETWORK_CONNECTION = "NETWORK_CONNECTION"
    PROCESS_CREATION = "PROCESS_CREATION"
    SERVICE_STATE = "SERVICE_STATE"
    FIREWALL_ACTION = "FIREWALL_ACTION"
    MALWARE_DETECTION = "MALWARE_DETECTION"
    SYSTEM_UPDATE = "SYSTEM_UPDATE"
    BACKUP_OPERATION = "BACKUP_OPERATION"
    USER_MANAGEMENT = "USER_MANAGEMENT"
    UNKNOWN = "UNKNOWN"


class LogEntry:
    """Represents a single security log entry."""

    def __init__(self, event_type: EventType, source: str, message: str,
                 user: str = "SYSTEM", severity: SeverityLevel = SeverityLevel.INFO,
                 timestamp: Optional[datetime] = None):
        """
        Initialize a log entry.

        Args:
            event_type: Type of security event
            source: Source component/service generating the log
            message: Log message content
            user: User associated with the event
            severity: Severity level of the event
            timestamp: Timestamp of the event (defaults to now)
        """
        self.timestamp = timestamp or datetime.now()
        self.event_type = self._validate_event_type(event_type)
        self.source = self._validate_source(source)
        self.user = self._validate_user(user)
        self.severity = self._validate_severity(severity)
        self.message = self._validate_message(message)
        self.log_id = self._generate_log_id()
        self.metadata = {}
        self.parsed_data = {}

    def _validate_event_type(self, event_type: EventType) -> EventType:
        """Validate event type."""
        if not isinstance(event_type, EventType):
            raise ValueError("Event type must be an EventType enum value")
        return event_type

    def _validate_source(self, source: str) -> str:
        """Validate source name."""
        if not source or not isinstance(source, str):
            raise ValueError("Source must be a non-empty string")
        return source.strip()

    def _validate_user(self, user: str) -> str:
        """Validate username."""
        if not user or not isinstance(user, str):
            raise ValueError("User must be a non-empty string")
        return user.strip()

    def _validate_severity(self, severity: SeverityLevel) -> SeverityLevel:
        """Validate severity level."""
        if not isinstance(severity, SeverityLevel):
            raise ValueError("Severity must be a SeverityLevel enum value")
        return severity

    def _validate_message(self, message: str) -> str:
        """Validate log message."""
        if not message or not isinstance(message, str):
            raise ValueError("Message must be a non-empty string")
        return message.strip()

    def _generate_log_id(self) -> str:
        """Generate a unique log entry ID."""
        timestamp = self.timestamp.strftime("%Y%m%d%H%M%S")
        random_part = hash(f"{self.source}{self.user}{self.message}") % 10000
        return f"LOG-{timestamp}-{random_part:04d}"

    def add_metadata(self, key: str, value: Any) -> None:
        """Add custom metadata to the log entry."""
        self.metadata[key] = value

    def parse_message(self) -> Dict[str, str]:
        """
        Attempt to parse structured information from the message.
        This is a simple implementation - can be extended for specific formats.
        """
        parsed = {}

        # Look for IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, self.message)
        if ips:
            parsed['ips'] = ips

        # Look for file paths
        file_pattern = r'(?:[a-zA-Z]:)?[\\/][\w\\.-]+(?:[\\/][\w\\.-]+)*'
        files = re.findall(file_pattern, self.message)
        if files:
            parsed['files'] = files

        # Look for port numbers
        port_pattern = r'\bport\s+(\d+)\b|\b:(\d+)\b'
        ports = re.findall(port_pattern, self.message.lower())
        if ports:
            parsed['ports'] = [p[0] or p[1] for p in ports if any(p)]

        self.parsed_data = parsed
        return parsed

    def to_dict(self) -> Dict:
        """Convert log entry to dictionary."""
        return {
            'log_id': self.log_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'source': self.source,
            'user': self.user,
            'severity': self.severity.value,
            'message': self.message,
            'metadata': self.metadata,
            'parsed_data': self.parsed_data
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'LogEntry':
        """Create a log entry from a dictionary."""
        entry = cls(
            event_type=EventType(data['event_type']),
            source=data['source'],
            message=data['message'],
            user=data['user'],
            severity=SeverityLevel(data['severity']),
            timestamp=datetime.fromisoformat(data['timestamp'])
        )
        entry.log_id = data['log_id']
        entry.metadata = data.get('metadata', {})
        entry.parsed_data = data.get('parsed_data', {})
        return entry

    def __str__(self) -> str:
        """String representation of the log entry."""
        severity_colors = {
            SeverityLevel.DEBUG: "⚪",
            SeverityLevel.INFO: "🔵",
            SeverityLevel.WARNING: "🟡",
            SeverityLevel.ERROR: "🟠",
            SeverityLevel.CRITICAL: "🔴"
        }
        icon = severity_colors.get(self.severity, "⚪")

        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"{icon} [{time_str}] {self.severity.value:8} | {self.event_type.value:16} | {self.source:20} | {self.user:15} | {self.message[:50]}"


class SecurityLog:
    """Manages and stores multiple log entries."""

    def __init__(self, max_size: int = 10000):
        """
        Initialize the security log.

        Args:
            max_size: Maximum number of log entries to store (rotation threshold)
        """
        self.entries: List[LogEntry] = []
        self.max_size = max_size
        self.archived_count = 0
        self.indices = {
            'by_event_type': defaultdict(list),
            'by_severity': defaultdict(list),
            'by_user': defaultdict(list),
            'by_source': defaultdict(list),
            'by_date': defaultdict(list)
        }

    def add_entry(self, entry: LogEntry) -> None:
        """Add a log entry to the security log."""
        self.entries.append(entry)

        # Update indices
        self.indices['by_event_type'][entry.event_type.value].append(entry)
        self.indices['by_severity'][entry.severity.value].append(entry)
        self.indices['by_user'][entry.user].append(entry)
        self.indices['by_source'][entry.source].append(entry)

        date_key = entry.timestamp.date().isoformat()
        self.indices['by_date'][date_key].append(entry)

        # Rotate if needed
        if len(self.entries) > self.max_size:
            self._rotate_logs()

    def add_entries(self, entries: List[LogEntry]) -> None:
        """Add multiple log entries."""
        for entry in entries:
            self.add_entry(entry)

    def _rotate_logs(self) -> None:
        """Rotate old logs out of memory."""
        remove_count = len(self.entries) - self.max_size
        if remove_count > 0:
            # Remove oldest entries
            removed = self.entries[:remove_count]
            self.entries = self.entries[remove_count:]
            self.archived_count += len(removed)

            # Rebuild indices (simpler than removing from all indices)
            self._rebuild_indices()

    def _rebuild_indices(self) -> None:
        """Rebuild all indices."""
        self.indices = {
            'by_event_type': defaultdict(list),
            'by_severity': defaultdict(list),
            'by_user': defaultdict(list),
            'by_source': defaultdict(list),
            'by_date': defaultdict(list)
        }

        for entry in self.entries:
            self.indices['by_event_type'][entry.event_type.value].append(entry)
            self.indices['by_severity'][entry.severity.value].append(entry)
            self.indices['by_user'][entry.user].append(entry)
            self.indices['by_source'][entry.source].append(entry)

            date_key = entry.timestamp.date().isoformat()
            self.indices['by_date'][date_key].append(entry)

    def get_all_entries(self) -> List[LogEntry]:
        """Get all log entries."""
        return self.entries.copy()

    def get_entry_count(self) -> int:
        """Get total number of entries."""
        return len(self.entries)

    def get_statistics(self) -> Dict:
        """Get log statistics."""
        return {
            'total_entries': len(self.entries),
            'archived_entries': self.archived_count,
            'unique_users': len(set(e.user for e in self.entries)),
            'unique_sources': len(set(e.source for e in self.entries)),
            'event_types': len(set(e.event_type.value for e in self.entries)),
            'date_range': {
                'first': min(e.timestamp for e in self.entries).isoformat() if self.entries else None,
                'last': max(e.timestamp for e in self.entries).isoformat() if self.entries else None
            }
        }

    def clear(self) -> None:
        """Clear all log entries."""
        self.entries.clear()
        self.indices = defaultdict(list)
        self.archived_count = 0


class LogAnalyzer:
    """Analyzes security logs with filtering and summary capabilities."""

    def __init__(self, security_log: SecurityLog):
        """
        Initialize the log analyzer.

        Args:
            security_log: SecurityLog instance to analyze
        """
        self.security_log = security_log
        self.analysis_history = []

    def filter_by_date_range(self, start_date: datetime, end_date: datetime) -> List[LogEntry]:
        """Filter logs within a date range."""
        filtered = []
        for entry in self.security_log.entries:
            if start_date <= entry.timestamp <= end_date:
                filtered.append(entry)
        return filtered

    def filter_by_date(self, date: datetime) -> List[LogEntry]:
        """Filter logs for a specific date."""
        date_str = date.date().isoformat()
        return self.security_log.indices['by_date'].get(date_str, []).copy()

    def filter_by_severity(self, severity: SeverityLevel) -> List[LogEntry]:
        """Filter logs by severity level."""
        return self.security_log.indices['by_severity'].get(severity.value, []).copy()

    def filter_by_severity_minimum(self, min_severity: SeverityLevel) -> List[LogEntry]:
        """Filter logs with severity >= minimum level."""
        severity_order = {
            SeverityLevel.DEBUG: 0,
            SeverityLevel.INFO: 1,
            SeverityLevel.WARNING: 2,
            SeverityLevel.ERROR: 3,
            SeverityLevel.CRITICAL: 4
        }
        min_level = severity_order[min_severity]

        filtered = []
        for entry in self.security_log.entries:
            if severity_order[entry.severity] >= min_level:
                filtered.append(entry)
        return filtered

    def filter_by_event_type(self, event_type: EventType) -> List[LogEntry]:
        """Filter logs by event type."""
        return self.security_log.indices['by_event_type'].get(event_type.value, []).copy()

    def filter_by_user(self, user: str) -> List[LogEntry]:
        """Filter logs by user."""
        return self.security_log.indices['by_user'].get(user, []).copy()

    def filter_by_source(self, source: str) -> List[LogEntry]:
        """Filter logs by source."""
        return self.security_log.indices['by_source'].get(source, []).copy()

    def filter_by_keyword(self, keyword: str, case_sensitive: bool = False) -> List[LogEntry]:
        """Filter logs containing a keyword in the message."""
        keyword = keyword if case_sensitive else keyword.lower()
        filtered = []

        for entry in self.security_log.entries:
            message = entry.message if case_sensitive else entry.message.lower()
            if keyword in message:
                filtered.append(entry)

        return filtered

    def filter_by_ip(self, ip_address: str) -> List[LogEntry]:
        """Filter logs mentioning a specific IP address."""
        filtered = []
        ip_pattern = re.compile(r'\b' + re.escape(ip_address) + r'\b')

        for entry in self.security_log.entries:
            if ip_pattern.search(entry.message):
                filtered.append(entry)

        return filtered

    def generate_summary(self, entries: Optional[List[LogEntry]] = None) -> Dict:
        """
        Generate a summary of log entries.

        Args:
            entries: List of entries to summarize (uses all if None)
        """
        if entries is None:
            entries = self.security_log.entries

        if not entries:
            return {"error": "No entries to summarize"}

        # Count by severity
        severity_counts = Counter(entry.severity.value for entry in entries)

        # Count by event type
        event_type_counts = Counter(entry.event_type.value for entry in entries)

        # Count by user
        user_counts = Counter(entry.user for entry in entries)

        # Count by source
        source_counts = Counter(entry.source for entry in entries)

        # Timeline analysis
        timeline = defaultdict(int)
        for entry in entries:
            hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00")
            timeline[hour_key] += 1

        # Most recent critical events
        critical_events = [
            entry for entry in entries
            if entry.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]
        ]
        critical_events.sort(key=lambda e: e.timestamp, reverse=True)

        summary = {
            'total_entries': len(entries),
            'time_range': {
                'start': min(e.timestamp for e in entries).isoformat(),
                'end': max(e.timestamp for e in entries).isoformat()
            },
            'severity_breakdown': dict(severity_counts),
            'event_type_breakdown': dict(event_type_counts),
            'user_breakdown': dict(user_counts.most_common(10)),
            'source_breakdown': dict(source_counts.most_common(10)),
            'timeline': dict(sorted(timeline.items())),
            'recent_critical': [e.to_dict() for e in critical_events[:5]],
            'unique_users': len(user_counts),
            'unique_sources': len(source_counts)
        }

        # Add to analysis history
        self.analysis_history.append({
            'timestamp': datetime.now().isoformat(),
            'entries_analyzed': len(entries),
            'summary': summary
        })

        return summary

    def generate_daily_report(self, date: datetime) -> Dict:
        """Generate a daily security report."""
        day_entries = self.filter_by_date(date)

        if not day_entries:
            return {"error": f"No entries for {date.date()}"}

        summary = self.generate_summary(day_entries)

        report = {
            'date': date.date().isoformat(),
            'summary': summary,
            'security_score': self._calculate_security_score(day_entries),
            'top_events': self._get_top_events(day_entries),
            'user_activity': self._analyze_user_activity(day_entries)
        }

        return report

    def _calculate_security_score(self, entries: List[LogEntry]) -> int:
        """Calculate a security score based on log entries."""
        score = 100

        for entry in entries:
            if entry.severity == SeverityLevel.CRITICAL:
                score -= 10
            elif entry.severity == SeverityLevel.ERROR:
                score -= 5
            elif entry.severity == SeverityLevel.WARNING:
                score -= 2

            # Specific event type penalties
            if entry.event_type == EventType.AUTH_FAILURE:
                score -= 3
            elif entry.event_type == EventType.PERMISSION_CHANGE:
                score -= 2

        return max(0, score)

    def _get_top_events(self, entries: List[LogEntry]) -> List[Dict]:
        """Get the most significant events."""
        # Sort by severity and recency
        sorted_entries = sorted(
            entries,
            key=lambda e: (
                list(SeverityLevel).index(e.severity),
                e.timestamp
            ),
            reverse=True
        )

        return [e.to_dict() for e in sorted_entries[:10]]

    def _analyze_user_activity(self, entries: List[LogEntry]) -> Dict:
        """Analyze user activity patterns."""
        user_events = defaultdict(list)

        for entry in entries:
            user_events[entry.user].append(entry)

        activity = {}
        for user, user_entries in user_events.items():
            activity[user] = {
                'total_events': len(user_entries),
                'first_seen': min(e.timestamp for e in user_entries).isoformat(),
                'last_seen': max(e.timestamp for e in user_entries).isoformat(),
                'critical_events': sum(1 for e in user_entries if e.severity == SeverityLevel.CRITICAL)
            }

        return activity

    def detect_anomalies(self) -> List[Dict]:
        """Detect potential security anomalies."""
        anomalies = []
        entries = self.security_log.entries

        if len(entries) < 10:
            return anomalies

        # Check for rapid failed login attempts
        auth_failures = [e for e in entries if e.event_type == EventType.AUTH_FAILURE]
        if len(auth_failures) > 5:
            time_window = auth_failures[-1].timestamp - auth_failures[0].timestamp
            if time_window.total_seconds() < 300:  # 5 minutes
                anomalies.append({
                    'type': 'BRUTE_FORCE_ATTEMPT',
                    'description': f'{len(auth_failures)} failed logins in {time_window.total_seconds():.0f} seconds',
                    'severity': 'HIGH',
                    'timestamp': datetime.now().isoformat()
                })

        # Check for unusual hours activity
        late_night_events = [e for e in entries if e.timestamp.hour < 5 or e.timestamp.hour > 22]
        if len(late_night_events) > 10:
            anomalies.append({
                'type': 'UNUSUAL_HOURS_ACTIVITY',
                'description': f'{len(late_night_events)} events outside normal business hours',
                'severity': 'MEDIUM',
                'timestamp': datetime.now().isoformat()
            })

        # Check for privilege escalation attempts
        perm_changes = [e for e in entries if e.event_type == EventType.PERMISSION_CHANGE]
        if len(perm_changes) > 3:
            anomalies.append({
                'type': 'PRIVILEGE_ESCALATION',
                'description': f'{len(perm_changes)} permission changes detected',
                'severity': 'HIGH',
                'timestamp': datetime.now().isoformat()
            })

        return anomalies


class LogManager:
    """Main manager class that handles all log operations."""

    def __init__(self, log_name: str = "security_log"):
        """
        Initialize the log manager.

        Args:
            log_name: Name for this log collection
        """
        self.log_name = log_name
        self.security_log = SecurityLog()
        self.analyzer = LogAnalyzer(self.security_log)
        self.sources = set()
        self.users = set()

    def add_log_entry(self, event_type: EventType, source: str, message: str,
                      user: str = "SYSTEM", severity: SeverityLevel = SeverityLevel.INFO,
                      timestamp: Optional[datetime] = None) -> LogEntry:
        """
        Create and add a new log entry.

        Returns:
            The created LogEntry
        """
        try:
            entry = LogEntry(event_type, source, message, user, severity, timestamp)
            entry.parse_message()

            self.security_log.add_entry(entry)
            self.sources.add(source)
            self.users.add(user)

            print(f"✅ Added log entry: {entry.log_id}")
            return entry

        except ValueError as e:
            print(f"❌ Error creating log entry: {e}")
            raise

    def add_log_entry_interactive(self) -> Optional[LogEntry]:
        """Interactive method to add a log entry."""
        print("\n--- Add New Log Entry ---")

        # Event type selection
        print("\nEvent Types:")
        event_types = list(EventType)
        for i, et in enumerate(event_types, 1):
            print(f"{i:2}. {et.value}")

        et_choice = input(f"Select event type (1-{len(event_types)}): ").strip()
        try:
            event_type = event_types[int(et_choice) - 1]
        except (ValueError, IndexError):
            print("Invalid selection, using UNKNOWN")
            event_type = EventType.UNKNOWN

        # Source
        source = input("Source (e.g., 'auth.log', 'firewall', 'app'): ").strip()
        if not source:
            print("Source cannot be empty")
            return None

        # Message
        message = input("Log message: ").strip()
        if not message:
            print("Message cannot be empty")
            return None

        # User (optional)
        user = input("User (default: SYSTEM): ").strip() or "SYSTEM"

        # Severity selection
        print("\nSeverity Levels:")
        severities = list(SeverityLevel)
        for i, sv in enumerate(severities, 1):
            print(f"{i:2}. {sv.value}")

        sv_choice = input(f"Select severity (1-{len(severities)}, default: 2 - INFO): ").strip()
        try:
            severity = severities[int(sv_choice) - 1] if sv_choice else SeverityLevel.INFO
        except (ValueError, IndexError):
            severity = SeverityLevel.INFO

        # Timestamp (optional)
        custom_time = input("Use custom timestamp? (y/n): ").lower() == 'y'
        timestamp = None
        if custom_time:
            time_str = input("Enter timestamp (YYYY-MM-DD HH:MM:SS): ").strip()
            try:
                timestamp = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print("Invalid timestamp format, using current time")

        return self.add_log_entry(event_type, source, message, user, severity, timestamp)

    def view_logs(self, entries: Optional[List[LogEntry]] = None) -> None:
        """Display log entries."""
        if entries is None:
            entries = self.security_log.entries

        if not entries:
            print("No log entries to display.")
            return

        print("\n" + "=" * 100)
        print(f"📋 LOG ENTRIES ({len(entries)} total)")
        print("=" * 100)

        for entry in entries[-50:]:  # Show last 50
            print(entry)

    def search_logs(self) -> None:
        """Interactive log search interface."""
        print("\n🔍 SEARCH LOGS")
        print("-" * 50)
        print("Search by:")
        print("1. Date range")
        print("2. Severity level")
        print("3. Event type")
        print("4. User")
        print("5. Source")
        print("6. Keyword in message")
        print("7. IP address")
        print("8. Custom filter")

        choice = input("Select search type (1-8): ").strip()

        results = []

        try:
            if choice == '1':
                start_str = input("Start date (YYYY-MM-DD): ").strip()
                end_str = input("End date (YYYY-MM-DD): ").strip()

                start = datetime.strptime(start_str, "%Y-%m-%d")
                end = datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)

                results = self.analyzer.filter_by_date_range(start, end)

            elif choice == '2':
                print("Severity levels:")
                for i, sv in enumerate(SeverityLevel, 1):
                    print(f"{i}. {sv.value}")

                sv_choice = input("Select severity: ").strip()
                severity = list(SeverityLevel)[int(sv_choice) - 1]
                results = self.analyzer.filter_by_severity(severity)

            elif choice == '3':
                print("Event types:")
                for i, et in enumerate(EventType, 1):
                    print(f"{i}. {et.value}")

                et_choice = input("Select event type: ").strip()
                event_type = list(EventType)[int(et_choice) - 1]
                results = self.analyzer.filter_by_event_type(event_type)

            elif choice == '4':
                user = input("Enter username: ").strip()
                results = self.analyzer.filter_by_user(user)

            elif choice == '5':
                source = input("Enter source: ").strip()
                results = self.analyzer.filter_by_source(source)

            elif choice == '6':
                keyword = input("Enter keyword: ").strip()
                case = input("Case sensitive? (y/n): ").lower() == 'y'
                results = self.analyzer.filter_by_keyword(keyword, case)

            elif choice == '7':
                ip = input("Enter IP address: ").strip()
                results = self.analyzer.filter_by_ip(ip)

            elif choice == '8':
                print("\nCustom filter options:")
                print("You can combine multiple criteria")

                filters = {}
                if input("Filter by severity? (y/n): ").lower() == 'y':
                    print("Severities:", [sv.value for sv in SeverityLevel])
                    filters['severity'] = input("Enter severity: ").upper()

                if input("Filter by event type? (y/n): ").lower() == 'y':
                    filters['event_type'] = input("Enter event type: ").upper()

                if input("Filter by user? (y/n): ").lower() == 'y':
                    filters['user'] = input("Enter user: ").strip()

                if input("Filter by source? (y/n): ").lower() == 'y':
                    filters['source'] = input("Enter source: ").strip()

                # Apply filters
                results = self.security_log.entries.copy()

                if 'severity' in filters:
                    results = [e for e in results if e.severity.value == filters['severity']]
                if 'event_type' in filters:
                    results = [e for e in results if e.event_type.value == filters['event_type']]
                if 'user' in filters:
                    results = [e for e in results if e.user == filters['user']]
                if 'source' in filters:
                    results = [e for e in results if e.source == filters['source']]

            # Display results
            if results:
                print(f"\n✅ Found {len(results)} matching entries:")
                self.view_logs(results)

                # Option to save results
                if input("\nSave these results? (y/n): ").lower() == 'y':
                    filename = input("Enter filename: ").strip()
                    self.export_logs(results, filename)
            else:
                print("❌ No matching entries found.")

        except Exception as e:
            print(f"❌ Search error: {e}")

    def generate_report(self) -> None:
        """Generate and display a security report."""
        print("\n📊 SECURITY LOG REPORT")
        print("=" * 50)

        # Basic statistics
        stats = self.security_log.get_statistics()
        print(f"Total Entries: {stats['total_entries']}")
        print(f"Unique Users: {stats['unique_users']}")
        print(f"Unique Sources: {stats['unique_sources']}")

        if stats['date_range']['first']:
            print(f"Date Range: {stats['date_range']['first'][:10]} to {stats['date_range']['last'][:10]}")

        # Generate summary
        summary = self.analyzer.generate_summary()

        print("\n📈 Event Summary:")
        print(f"  Total: {summary['total_entries']}")
        print("\n  By Severity:")
        for severity, count in summary['severity_breakdown'].items():
            icon = {
                'DEBUG': '⚪', 'INFO': '🔵', 'WARNING': '🟡',
                'ERROR': '🟠', 'CRITICAL': '🔴'
            }.get(severity, '⚪')
            print(f"    {icon} {severity}: {count}")

        print("\n  Top 5 Event Types:")
        for event_type, count in list(summary['event_type_breakdown'].items())[:5]:
            print(f"    • {event_type}: {count}")

        print("\n  Top 5 Active Users:")
        for user, count in list(summary['user_breakdown'].items())[:5]:
            print(f"    • {user}: {count} events")

        # Anomaly detection
        anomalies = self.analyzer.detect_anomalies()
        if anomalies:
            print("\n⚠️  DETECTED ANOMALIES:")
            for anomaly in anomalies:
                severity_icon = {
                    'LOW': '🟢',
                    'MEDIUM': '🟡',
                    'HIGH': '🟠',
                    'CRITICAL': '🔴'
                }.get(anomaly['severity'], '⚪')
                print(f"  {severity_icon} {anomaly['type']}: {anomaly['description']}")

    def export_logs(self, entries: Optional[List[LogEntry]] = None,
                    filename: Optional[str] = None) -> None:
        """Export logs to JSON file."""
        if entries is None:
            entries = self.security_log.entries

        if not entries:
            print("No logs to export.")
            return

        if not filename:
            filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            'log_name': self.log_name,
            'export_time': datetime.now().isoformat(),
            'total_entries': len(entries),
            'entries': [e.to_dict() for e in entries]
        }

        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Exported {len(entries)} logs to {filename}")
        except Exception as e:
            print(f"❌ Error exporting logs: {e}")

    def import_logs(self, filename: str) -> int:
        """Import logs from JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            imported = 0
            for entry_data in data.get('entries', []):
                try:
                    entry = LogEntry.from_dict(entry_data)
                    self.security_log.add_entry(entry)
                    imported += 1
                except Exception as e:
                    print(f"⚠️  Error importing entry: {e}")

            print(f"✅ Imported {imported} logs from {filename}")
            return imported

        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON file: {filename}")
        except Exception as e:
            print(f"❌ Error importing logs: {e}")

        return 0

    def get_log_statistics(self) -> None:
        """Display detailed log statistics."""
        stats = self.security_log.get_statistics()

        print("\n📊 LOG STATISTICS")
        print("=" * 50)
        print(f"Log Name: {self.log_name}")
        print(f"Total Entries: {stats['total_entries']}")
        print(f"Archived Entries: {stats['archived_entries']}")
        print(f"Unique Users: {stats['unique_users']}")
        print(f"Unique Sources: {stats['unique_sources']}")

        if stats['date_range']['first']:
            print(f"First Entry: {stats['date_range']['first']}")
            print(f"Last Entry: {stats['date_range']['last']}")

        # Show top users
        summary = self.analyzer.generate_summary()
        if 'user_breakdown' in summary:
            print("\nTop Users by Activity:")
            for user, count in list(summary['user_breakdown'].items())[:5]:
                print(f"  • {user}: {count} events")


def generate_sample_logs(manager: LogManager, count: int = 20) -> None:
    """Generate sample log entries for demonstration."""
    import random

    sources = ['auth.log', 'syslog', 'firewall', 'web_server', 'database', 'app_server']
    users = ['admin', 'john.doe', 'jane.smith', 'system', 'backup_user', 'auditor']

    messages = {
        EventType.LOGIN: [
            "User logged in successfully",
            "Login attempt from IP {ip}",
            "SSH login from {ip}"
        ],
        EventType.AUTH_FAILURE: [
            "Failed login attempt",
            "Invalid password for user",
            "Authentication failure from {ip}"
        ],
        EventType.FILE_ACCESS: [
            "File {file} accessed",
            "Directory listing of {dir}",
            "Configuration file modified"
        ],
        EventType.NETWORK_CONNECTION: [
            "Connection from {ip}:{port}",
            "Outbound connection to {ip}",
            "Firewall blocked connection from {ip}"
        ]
    }

    ips = ['192.168.1.100', '10.0.0.50', '172.16.0.25', '203.0.113.45', '198.51.100.67']
    files = ['/etc/passwd', '/var/log/auth.log', '/etc/ssh/sshd_config', '/etc/hosts']

    start_date = datetime.now() - timedelta(days=7)

    for i in range(count):
        # Random event type with weights
        event_type = random.choice(
            [EventType.LOGIN, EventType.LOGOUT, EventType.AUTH_FAILURE,
             EventType.FILE_ACCESS, EventType.NETWORK_CONNECTION]
        )

        source = random.choice(sources)
        user = random.choice(users)

        # Random severity with weights
        severity = random.choices(
            list(SeverityLevel),
            weights=[10, 50, 25, 10, 5]
        )[0]

        # Generate message
        if event_type in messages:
            message_template = random.choice(messages[event_type])
            message = message_template.format(
                ip=random.choice(ips),
                port=random.randint(1024, 65535),
                file=random.choice(files),
                dir='/'.join(random.choice(files).split('/')[:-1])
            )
        else:
            message = f"Sample {event_type.value} event"

        # Random timestamp within last week
        timestamp = start_date + timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        manager.add_log_entry(event_type, source, message, user, severity, timestamp)

    print(f"✅ Generated {count} sample log entries")


def main():
    """Main function to run the security log manager."""

    print("=" * 80)
    print("🔐 SECURITY LOG MANAGER")
    print("=" * 80)
    print("A system for managing and analyzing security logs")

    # Initialize the system
    log_name = input("\nEnter log collection name (default: 'security_log'): ").strip()
    if not log_name:
        log_name = "security_log"

    manager = LogManager(log_name)

    # Ask to generate sample logs
    if input("\nGenerate sample logs for demonstration? (y/n): ").lower() == 'y':
        count = int(input("Number of sample logs (default: 20): ") or "20")
        generate_sample_logs(manager, count)

    # Interactive menu
    while True:
        print("\n" + "=" * 50)
        print(f"📌 MAIN MENU - {manager.log_name}")
        print("=" * 50)
        print("1. Add new log entry")
        print("2. View all logs")
        print("3. Search/filter logs")
        print("4. Generate summary report")
        print("5. View log statistics")
        print("6. Detect anomalies")
        print("7. Export logs to file")
        print("8. Import logs from file")
        print("9. Clear all logs")
        print("10. Exit")
        print("-" * 50)
        print(f"Current logs: {manager.security_log.get_entry_count()} entries")

        choice = input("Enter your choice (1-10): ").strip()

        try:
            if choice == '1':
                manager.add_log_entry_interactive()

            elif choice == '2':
                manager.view_logs()

            elif choice == '3':
                manager.search_logs()

            elif choice == '4':
                manager.generate_report()

            elif choice == '5':
                manager.get_log_statistics()

            elif choice == '6':
                anomalies = manager.analyzer.detect_anomalies()
                if anomalies:
                    print("\n⚠️  DETECTED ANOMALIES:")
                    for anomaly in anomalies:
                        severity_icon = {
                            'LOW': '🟢',
                            'MEDIUM': '🟡',
                            'HIGH': '🟠',
                            'CRITICAL': '🔴'
                        }.get(anomaly['severity'], '⚪')
                        print(f"\n{severity_icon} [{anomaly['severity']}] {anomaly['type']}")
                        print(f"   {anomaly['description']}")
                        print(f"   Time: {anomaly['timestamp']}")
                else:
                    print("✅ No anomalies detected.")

            elif choice == '7':
                print("\nExport options:")
                print("1. All logs")
                print("2. Filtered logs")

                export_choice = input("Select (1-2): ").strip()

                if export_choice == '1':
                    manager.export_logs()
                elif export_choice == '2':
                    print("Please use search first to filter logs")
                    manager.search_logs()

                    if input("\nExport these results? (y/n): ").lower() == 'y':
                        filename = input("Enter filename: ").strip()
                        manager.export_logs(None, filename)

            elif choice == '8':
                filename = input("Enter filename to import: ").strip()
                manager.import_logs(filename)

            elif choice == '9':
                confirm = input("Are you sure you want to clear all logs? (yes/no): ").lower()
                if confirm == 'yes':
                    manager.security_log.clear()
                    print("✅ All logs cleared.")

            elif choice == '10':
                print("\n👋 Exiting Security Log Manager. Stay secure!")
                break

            else:
                print("❌ Invalid choice. Please enter a number between 1 and 10.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
            break
        except ValueError as e:
            print(f"❌ Input error: {e}")
        except Exception as e:
            print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()