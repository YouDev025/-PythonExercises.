#!/usr/bin/env python3
"""
User Behavior Monitoring System
A comprehensive user behavior analytics and anomaly detection system.

Monitors user activities, builds behavioral baselines, and detects
suspicious activities through pattern analysis and deviation detection.

Compatible with PyCharm - uses only Python standard library.
"""

import json
import random
import sys
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set, Any, DefaultDict
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import math


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def display_color(self) -> str:
        """Get ANSI color code for severity."""
        colors = {
            AlertSeverity.LOW: '\033[92m',      # Green
            AlertSeverity.MEDIUM: '\033[93m',    # Yellow
            AlertSeverity.HIGH: '\033[91m',      # Red
            AlertSeverity.CRITICAL: '\033[95m',  # Magenta
        }
        return colors[self]


class ActionType(Enum):
    """User action types with associated risk factors."""
    LOGIN = ("Login", 0.5)
    LOGOUT = ("Logout", 0.1)
    FILE_ACCESS = ("File Access", 1.0)
    FILE_DOWNLOAD = ("File Download", 1.5)
    FILE_DELETE = ("File Delete", 2.5)
    COMMAND_EXEC = ("Command Execution", 2.0)
    API_REQUEST = ("API Request", 0.8)
    CONFIG_CHANGE = ("Config Change", 3.0)
    USER_CREATE = ("User Create", 3.5)
    PERMISSION_CHANGE = ("Permission Change", 4.0)
    DATA_EXPORT = ("Data Export", 3.0)
    PASSWORD_CHANGE = ("Password Change", 2.0)

    def __init__(self, display_name: str, base_risk: float):
        self.display_name = display_name
        self.base_risk = base_risk


class ResourceType(Enum):
    """Resource types with sensitivity levels."""
    PUBLIC = ("Public", 0.1)
    INTERNAL = ("Internal", 0.5)
    CONFIDENTIAL = ("Confidential", 1.0)
    RESTRICTED = ("Restricted", 2.0)
    SECRET = ("Secret", 3.0)
    CRITICAL = ("Critical", 4.0)

    def __init__(self, display_name: str, sensitivity: float):
        self.display_name = display_name
        self.sensitivity = sensitivity


@dataclass
class UserActivity:
    """Represents a single user activity event."""
    activity_id: str
    timestamp: datetime
    user_id: str
    action: ActionType
    resource: str
    resource_type: ResourceType
    status: str  # 'success' or 'failure'
    source_ip: str
    session_id: str
    details: str

    def __hash__(self) -> int:
        return hash(self.activity_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserActivity):
            return False
        return self.activity_id == other.activity_id

    @property
    def hour_of_day(self) -> int:
        """Get hour of day (0-23)."""
        return self.timestamp.hour

    @property
    def is_business_hours(self) -> bool:
        """Check if activity occurred during business hours (8-18)."""
        return 8 <= self.hour_of_day <= 18

    @property
    def is_success(self) -> bool:
        """Check if activity was successful."""
        return self.status.lower() == 'success'


@dataclass
class UserProfile:
    """Behavioral profile for a user."""
    user_id: str
    total_activities: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    # Login patterns
    login_success_count: int = 0
    login_failure_count: int = 0
    avg_daily_logins: float = 0.0
    login_hours: List[int] = field(default_factory=list)

    # Activity patterns
    action_counts: DefaultDict[ActionType, int] = field(default_factory=lambda: defaultdict(int))
    hourly_activity: DefaultDict[int, int] = field(default_factory=lambda: defaultdict(int))
    daily_activity: DefaultDict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Resource access
    resources_accessed: Set[str] = field(default_factory=set)
    sensitive_resource_count: int = 0
    resource_type_counts: DefaultDict[ResourceType, int] = field(default_factory=lambda: defaultdict(int))

    # Session info
    avg_session_duration: float = 0.0
    ip_addresses: Set[str] = field(default_factory=set)

    # Risk metrics
    baseline_established: bool = False
    risk_score: float = 0.0
    anomaly_count: int = 0

    # Statistical baselines
    mean_hourly_rate: float = 0.0
    std_hourly_rate: float = 0.0
    normal_login_hours: Set[int] = field(default_factory=set)


@dataclass
class SecurityAlert:
    """Security alert generated from behavior analysis."""
    alert_id: str
    timestamp: datetime
    user_id: str
    alert_type: str
    severity: AlertSeverity
    description: str
    evidence: Dict[str, Any]
    risk_contribution: float = 0.0

    def __lt__(self, other: 'SecurityAlert') -> bool:
        return self.severity.value < other.severity.value


class BehaviorAnalyzer:
    """
    Analyzes user behavior and detects anomalies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize behavior analyzer with configuration."""
        self.config = {
            'failed_login_threshold': 5,
            'unusual_hour_threshold': 2.5,  # Standard deviations
            'activity_spike_threshold': 3.0,  # Standard deviations
            'sensitive_resource_threshold': 10,
            'new_ip_threshold': 3,
            'baseline_days': 7,
            'min_activities_for_baseline': 20,
            'session_timeout_minutes': 30,
            'anomaly_lookback_hours': 24,
        }
        if config:
            self.config.update(config)

        self.alerts: List[SecurityAlert] = []
        self._alert_counter = 0

    def build_profile(self, user_id: str,
                     activities: List[UserActivity]) -> UserProfile:
        """
        Build a behavioral profile for a user.

        Args:
            user_id: User identifier
            activities: List of user's activities

        Returns:
            UserProfile with behavioral patterns
        """
        if not activities:
            return UserProfile(user_id=user_id)

        profile = UserProfile(user_id=user_id)
        profile.total_activities = len(activities)

        # Sort activities by timestamp
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)
        profile.first_seen = sorted_activities[0].timestamp
        profile.last_seen = sorted_activities[-1].timestamp

        # Track sessions
        sessions = self._extract_sessions(sorted_activities)

        # Analyze patterns
        for activity in sorted_activities:
            # Login tracking
            if activity.action == ActionType.LOGIN:
                if activity.is_success:
                    profile.login_success_count += 1
                else:
                    profile.login_failure_count += 1

            # Action counts
            profile.action_counts[activity.action] += 1

            # Hourly patterns
            profile.hourly_activity[activity.hour_of_day] += 1

            # Daily patterns
            day_key = activity.timestamp.strftime('%Y-%m-%d')
            profile.daily_activity[day_key] += 1

            # Resource tracking
            profile.resources_accessed.add(activity.resource)
            profile.resource_type_counts[activity.resource_type] += 1
            if activity.resource_type.sensitivity >= 2.0:
                profile.sensitive_resource_count += 1

            # IP tracking
            profile.ip_addresses.add(activity.source_ip)

            # Login hours for normal pattern
            if activity.action == ActionType.LOGIN and activity.is_success:
                profile.login_hours.append(activity.hour_of_day)

        # Calculate baselines if enough data
        if profile.total_activities >= self.config['min_activities_for_baseline']:
            profile.baseline_established = True

            # Calculate hourly statistics
            hourly_values = list(profile.hourly_activity.values())
            if hourly_values:
                profile.mean_hourly_rate = sum(hourly_values) / 24
                profile.std_hourly_rate = self._calculate_std(hourly_values, profile.mean_hourly_rate)

            # Determine normal login hours
            if profile.login_hours:
                hour_counts = defaultdict(int)
                for hour in profile.login_hours:
                    hour_counts[hour] += 1

                avg_logins_per_hour = len(profile.login_hours) / 24
                for hour, count in hour_counts.items():
                    if count >= avg_logins_per_hour * 0.5:
                        profile.normal_login_hours.add(hour)

            # Calculate average daily logins
            days_span = (profile.last_seen - profile.first_seen).days + 1
            if days_span > 0:
                profile.avg_daily_logins = profile.login_success_count / days_span

            # Average session duration
            if sessions:
                durations = [s['duration'] for s in sessions if s['duration'] > 0]
                if durations:
                    profile.avg_session_duration = sum(durations) / len(durations)

        return profile

    def _extract_sessions(self,
                         activities: List[UserActivity]) -> List[Dict[str, Any]]:
        """Extract user sessions from activities."""
        sessions = []
        current_session = None

        for activity in activities:
            if not current_session:
                current_session = {
                    'start': activity.timestamp,
                    'end': activity.timestamp,
                    'session_id': activity.session_id,
                    'activities': [activity],
                }
            elif (activity.timestamp - current_session['end']).total_seconds() / 60 > self.config['session_timeout_minutes']:
                # Session ended
                current_session['duration'] = (current_session['end'] - current_session['start']).total_seconds() / 60
                sessions.append(current_session)

                # Start new session
                current_session = {
                    'start': activity.timestamp,
                    'end': activity.timestamp,
                    'session_id': activity.session_id,
                    'activities': [activity],
                }
            else:
                current_session['end'] = activity.timestamp
                current_session['activities'].append(activity)

        if current_session:
            current_session['duration'] = (current_session['end'] - current_session['start']).total_seconds() / 60
            sessions.append(current_session)

        return sessions

    def _calculate_std(self, values: List[float], mean: float) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0

        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def detect_anomalies(self, user_id: str, profile: UserProfile,
                        recent_activities: List[UserActivity]) -> List[SecurityAlert]:
        """
        Detect anomalies in user behavior.

        Args:
            user_id: User identifier
            profile: User's behavioral profile
            recent_activities: Recent activities to analyze

        Returns:
            List of security alerts
        """
        alerts = []

        if not recent_activities:
            return alerts

        # Check for multiple failed logins
        failed_logins = [a for a in recent_activities
                        if a.action == ActionType.LOGIN and not a.is_success]
        if len(failed_logins) >= self.config['failed_login_threshold']:
            alerts.append(self._create_alert(
                user_id=user_id,
                alert_type="Multiple Failed Logins",
                severity=AlertSeverity.HIGH,
                description=f"{len(failed_logins)} failed login attempts detected",
                evidence={
                    'failed_attempts': len(failed_logins),
                    'threshold': self.config['failed_login_threshold'],
                    'timeframe': f"Last {self.config['anomaly_lookback_hours']} hours"
                },
                risk_contribution=len(failed_logins) * 5
            ))

        # Check for unusual login hours
        if profile.baseline_established:
            for activity in recent_activities:
                if activity.action == ActionType.LOGIN and activity.is_success:
                    if (profile.normal_login_hours and
                        activity.hour_of_day not in profile.normal_login_hours):
                        alerts.append(self._create_alert(
                            user_id=user_id,
                            alert_type="Unusual Login Hour",
                            severity=AlertSeverity.MEDIUM,
                            description=f"Login at unusual hour: {activity.hour_of_day}:00",
                            evidence={
                                'login_hour': activity.hour_of_day,
                                'normal_hours': list(profile.normal_login_hours),
                                'source_ip': activity.source_ip
                            },
                            risk_contribution=15
                        ))

        # Check for activity spikes
        if profile.baseline_established and profile.std_hourly_rate > 0:
            recent_hourly = defaultdict(int)
            cutoff_time = datetime.now() - timedelta(hours=self.config['anomaly_lookback_hours'])
            recent_filtered = [a for a in recent_activities if a.timestamp > cutoff_time]

            for activity in recent_filtered:
                recent_hourly[activity.hour_of_day] += 1

            for hour, count in recent_hourly.items():
                z_score = (count - profile.mean_hourly_rate) / profile.std_hourly_rate
                if z_score > self.config['activity_spike_threshold']:
                    alerts.append(self._create_alert(
                        user_id=user_id,
                        alert_type="Activity Spike",
                        severity=AlertSeverity.MEDIUM,
                        description=f"Unusual activity spike at hour {hour}:00",
                        evidence={
                            'hour': hour,
                            'activity_count': count,
                            'expected': profile.mean_hourly_rate,
                            'z_score': z_score,
                        },
                        risk_contribution=10 * z_score
                    ))

        # Check for sensitive resource access
        sensitive_activities = [a for a in recent_activities
                               if a.resource_type.sensitivity >= 2.0]
        if len(sensitive_activities) > self.config['sensitive_resource_threshold']:
            alerts.append(self._create_alert(
                user_id=user_id,
                alert_type="Excessive Sensitive Resource Access",
                severity=AlertSeverity.HIGH,
                description=f"Accessed {len(sensitive_activities)} sensitive resources",
                evidence={
                    'sensitive_access_count': len(sensitive_activities),
                    'threshold': self.config['sensitive_resource_threshold'],
                    'resources': list(set(a.resource for a in sensitive_activities))[:5]
                },
                risk_contribution=len(sensitive_activities) * 3
            ))

        # Check for new IP addresses
        recent_ips = set(a.source_ip for a in recent_activities)
        new_ips = recent_ips - profile.ip_addresses
        if len(new_ips) >= self.config['new_ip_threshold']:
            alerts.append(self._create_alert(
                user_id=user_id,
                alert_type="Multiple New IP Addresses",
                severity=AlertSeverity.MEDIUM,
                description=f"Activity from {len(new_ips)} new IP addresses",
                evidence={
                    'new_ip_count': len(new_ips),
                    'threshold': self.config['new_ip_threshold'],
                    'ips': list(new_ips)[:5]
                },
                risk_contribution=len(new_ips) * 8
            ))

        # Check for high-risk actions
        high_risk_actions = [a for a in recent_activities
                            if a.action.base_risk >= 2.5]
        if high_risk_actions:
            for action in high_risk_actions[:3]:  # Alert on first few
                alerts.append(self._create_alert(
                    user_id=user_id,
                    alert_type="High-Risk Action",
                    severity=AlertSeverity.HIGH if action.action.base_risk >= 3.5 else AlertSeverity.MEDIUM,
                    description=f"High-risk action: {action.action.display_name}",
                    evidence={
                        'action': action.action.display_name,
                        'resource': action.resource,
                        'resource_type': action.resource_type.display_name,
                        'timestamp': action.timestamp.isoformat(),
                    },
                    risk_contribution=action.action.base_risk * 10
                ))

        return alerts

    def _create_alert(self, user_id: str, alert_type: str, severity: AlertSeverity,
                     description: str, evidence: Dict[str, Any],
                     risk_contribution: float) -> SecurityAlert:
        """Create a security alert."""
        self._alert_counter += 1
        alert_id = f"ALERT-{self._alert_counter:04d}-{hashlib.md5(user_id.encode()).hexdigest()[:6]}"

        return SecurityAlert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            description=description,
            evidence=evidence,
            risk_contribution=risk_contribution
        )

    def calculate_risk_score(self, profile: UserProfile,
                            alerts: List[SecurityAlert]) -> float:
        """
        Calculate overall risk score for a user.

        Args:
            profile: User profile
            alerts: Recent alerts for user

        Returns:
            Risk score (0-100)
        """
        score = 0.0

        # Base score from profile metrics
        if profile.login_failure_count > 0:
            failure_ratio = profile.login_failure_count / max(profile.login_success_count, 1)
            score += min(30, failure_ratio * 20)

        # Sensitive resource access
        if profile.total_activities > 0:
            sensitive_ratio = profile.sensitive_resource_count / profile.total_activities
            score += min(20, sensitive_ratio * 40)

        # IP diversity
        if len(profile.ip_addresses) > 5:
            score += min(15, (len(profile.ip_addresses) - 5) * 2)

        # Alert contributions
        for alert in alerts:
            score += alert.risk_contribution

        # Normalize to 0-100
        return min(100.0, score)


class ActivityGenerator:
    """Generates realistic user activity logs."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize activity generator."""
        if seed:
            random.seed(seed)

        self.actions = list(ActionType)
        self.resource_types = list(ResourceType)
        self.users = self._generate_users(20)
        self.ips = self._generate_ip_pool(50)

        self.resources = {
            ResourceType.PUBLIC: ['/public/docs', '/public/images', '/blog/post'],
            ResourceType.INTERNAL: ['/internal/wiki', '/internal/hr', '/internal/projects'],
            ResourceType.CONFIDENTIAL: ['/confidential/finance', '/confidential/strategy',
                                       '/confidential/legal'],
            ResourceType.RESTRICTED: ['/restricted/admin', '/restricted/security',
                                     '/restricted/audit'],
            ResourceType.SECRET: ['/secret/keys', '/secret/credentials', '/secret/certificates'],
            ResourceType.CRITICAL: ['/critical/database', '/critical/payment',
                                  '/critical/infrastructure'],
        }

        self._activity_counter = 0
        self._session_counter = 0

    def _generate_users(self, count: int) -> List[Dict[str, Any]]:
        """Generate user pool with roles."""
        roles = ['admin', 'developer', 'analyst', 'manager', 'support', 'auditor']
        users = []

        for i in range(count):
            role = random.choice(roles)
            username = f"{role}{random.randint(100, 999)}"

            # Assign typical working hours based on role
            if role == 'admin':
                typical_hours = list(range(7, 20))
            elif role == 'developer':
                typical_hours = list(range(9, 19))
            elif role == 'support':
                typical_hours = list(range(8, 22))
            else:
                typical_hours = list(range(8, 18))

            users.append({
                'user_id': username,
                'role': role,
                'typical_hours': typical_hours,
                'access_level': random.choice([1, 2, 3, 4]),
            })

        return users

    def _generate_ip_pool(self, count: int) -> List[str]:
        """Generate IP address pool."""
        ips = []
        for _ in range(count):
            if random.random() < 0.7:
                # Internal corporate IPs
                ip = f"10.{random.randint(10, 50)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
            else:
                # External/VPN IPs
                ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 254)}"
            ips.append(ip)
        return ips

    def generate_activity(self, user_info: Optional[Dict[str, Any]] = None,
                         base_time: Optional[datetime] = None) -> UserActivity:
        """Generate a single user activity."""
        self._activity_counter += 1

        if not user_info:
            user_info = random.choice(self.users)

        # Generate timestamp
        if base_time:
            timestamp = base_time + timedelta(minutes=random.randint(1, 30))
        else:
            hours_ago = random.uniform(0, 168)  # Last 7 days
            timestamp = datetime.now() - timedelta(hours=hours_ago)

            # Adjust for typical working hours
            if random.random() < 0.8:  # 80% during working hours
                typical_hour = random.choice(user_info['typical_hours'])
                timestamp = timestamp.replace(hour=typical_hour)

        # Select action based on user role
        if user_info['role'] == 'admin':
            action_weights = {
                ActionType.LOGIN: 15,
                ActionType.COMMAND_EXEC: 20,
                ActionType.CONFIG_CHANGE: 10,
                ActionType.USER_CREATE: 5,
                ActionType.FILE_ACCESS: 20,
            }
        elif user_info['role'] == 'developer':
            action_weights = {
                ActionType.LOGIN: 20,
                ActionType.COMMAND_EXEC: 25,
                ActionType.FILE_ACCESS: 25,
                ActionType.API_REQUEST: 15,
            }
        else:
            action_weights = {
                ActionType.LOGIN: 30,
                ActionType.FILE_ACCESS: 30,
                ActionType.API_REQUEST: 20,
                ActionType.LOGOUT: 10,
            }

        action = random.choices(
            list(action_weights.keys()),
            weights=list(action_weights.values())
        )[0]

        # Determine status
        if action == ActionType.LOGIN:
            status = 'failure' if random.random() < 0.05 else 'success'
        else:
            status = 'failure' if random.random() < 0.02 else 'success'

        # Select resource based on user access level
        available_types = []
        for rt in ResourceType:
            if rt.sensitivity <= user_info['access_level']:
                available_types.append(rt)

        if not available_types:
            available_types = [ResourceType.PUBLIC]

        resource_type = random.choice(available_types)
        resource = random.choice(self.resources[resource_type])

        # Add user-specific path
        resource = f"{resource}/{user_info['user_id']}" if random.random() < 0.3 else resource

        # Generate session
        self._session_counter += 1
        session_id = f"SESS-{user_info['user_id']}-{self._session_counter}"

        # Generate details
        details = self._generate_details(action, resource, status)

        return UserActivity(
            activity_id=f"ACT-{self._activity_counter:06d}",
            timestamp=timestamp,
            user_id=user_info['user_id'],
            action=action,
            resource=resource,
            resource_type=resource_type,
            status=status,
            source_ip=random.choice(self.ips),
            session_id=session_id,
            details=details
        )

    def _generate_details(self, action: ActionType, resource: str,
                         status: str) -> str:
        """Generate activity details."""
        details_templates = {
            ActionType.LOGIN: f"Login attempt to system - {status}",
            ActionType.FILE_ACCESS: f"Accessed file: {resource}",
            ActionType.COMMAND_EXEC: f"Executed command on {resource}",
            ActionType.CONFIG_CHANGE: f"Modified configuration: {resource}",
            ActionType.API_REQUEST: f"API call to endpoint: {resource}",
        }

        return details_templates.get(action, f"Action: {action.display_name}")

    def generate_user_activities(self, user_info: Dict[str, Any],
                                count: int = 50) -> List[UserActivity]:
        """Generate activities for a specific user."""
        activities = []
        base_time = datetime.now() - timedelta(days=7)

        for _ in range(count):
            activity = self.generate_activity(user_info, base_time)
            activities.append(activity)

            # Advance time realistically
            base_time = activity.timestamp

        return activities

    def generate_all_activities(self, activities_per_user: int = 50) -> List[UserActivity]:
        """Generate activities for all users."""
        all_activities = []

        for user_info in self.users:
            user_activities = self.generate_user_activities(user_info, activities_per_user)
            all_activities.extend(user_activities)

        # Add some suspicious activities for specific users
        suspicious_users = random.sample(self.users, min(3, len(self.users)))
        for user_info in suspicious_users:
            suspicious_activities = self._generate_suspicious_activities(user_info)
            all_activities.extend(suspicious_activities)

        return sorted(all_activities, key=lambda a: a.timestamp)

    def _generate_suspicious_activities(self,
                                       user_info: Dict[str, Any]) -> List[UserActivity]:
        """Generate suspicious activities for testing detection."""
        activities = []

        # Multiple failed logins
        base_time = datetime.now() - timedelta(hours=2)
        for i in range(8):
            activity = self.generate_activity(user_info, base_time)
            activity.action = ActionType.LOGIN
            activity.status = 'failure'
            activity.details = f"Failed login attempt #{i+1}"
            activities.append(activity)
            base_time += timedelta(minutes=2)

        # Unusual hour login
        unusual_activity = self.generate_activity(user_info, base_time)
        unusual_activity.timestamp = unusual_activity.timestamp.replace(hour=3)
        unusual_activity.action = ActionType.LOGIN
        unusual_activity.status = 'success'
        activities.append(unusual_activity)

        # Sensitive resource access
        sensitive_activity = self.generate_activity(user_info, base_time)
        sensitive_activity.resource_type = ResourceType.CRITICAL
        sensitive_activity.resource = '/critical/database/admin_credentials'
        sensitive_activity.action = ActionType.FILE_ACCESS
        activities.append(sensitive_activity)

        return activities


class MonitoringDisplay:
    """Handles formatted display of monitoring results."""

    @staticmethod
    def _get_severity_color(severity: AlertSeverity) -> str:
        """Get color code for severity."""
        return severity.display_color

    @staticmethod
    def _get_risk_bar(score: float, width: int = 20) -> str:
        """Generate visual risk bar."""
        filled = int((score / 100) * width)
        return '█' * filled + '░' * (width - filled)

    def display_user_profiles(self, profiles: Dict[str, UserProfile]):
        """Display user behavioral profiles."""
        if not profiles:
            print("\n" + "=" * 100)
            print("No user profiles available")
            print("=" * 100)
            return

        print("\n" + "=" * 120)
        print(f"{'USER BEHAVIORAL PROFILES':^120}")
        print("=" * 120)

        # Header
        print(f"{'User ID':<20} {'Activities':<10} {'Login Succ/Fail':<15} "
              f"{'Sensitive':<10} {'Risk Score':<12} {'Baseline':<10}")
        print("-" * 120)

        for user_id, profile in sorted(profiles.items()):
            color = '\033[92m' if profile.risk_score < 30 else '\033[93m' if profile.risk_score < 60 else '\033[91m'
            reset = '\033[0m'

            login_str = f"{profile.login_success_count}/{profile.login_failure_count}"
            sensitive_str = str(profile.sensitive_resource_count)
            baseline_str = "✓" if profile.baseline_established else "✗"

            print(f"{color}{user_id:<20} {profile.total_activities:<10} {login_str:<15} "
                  f"{sensitive_str:<10} {profile.risk_score:<11.1f} {baseline_str:<10}{reset}")

        print("=" * 120)

    def display_alerts(self, alerts: List[SecurityAlert]):
        """Display security alerts."""
        if not alerts:
            print("\n" + "=" * 80)
            print("✓ No security alerts detected")
            print("=" * 80)
            return

        print("\n" + "=" * 130)
        print(f"{'SECURITY ALERTS':^130}")
        print("=" * 130)

        # Header
        print(f"{'Alert ID':<15} {'Time':<20} {'User':<15} {'Type':<25} "
              f"{'Severity':<10} {'Description':<40}")
        print("-" * 130)

        # Sort by severity and time
        sorted_alerts = sorted(alerts, key=lambda a: (a.severity.value, a.timestamp), reverse=True)

        for alert in sorted_alerts:
            color = self._get_severity_color(alert.severity)
            reset = '\033[0m'

            time_str = alert.timestamp.strftime("%Y-%m-%d %H:%M")
            desc_short = alert.description[:38]

            print(f"{color}{alert.alert_id:<15} {time_str:<20} {alert.user_id:<15} "
                  f"{alert.alert_type:<25} {alert.severity.name:<10} {desc_short:<40}{reset}")

        print("=" * 130)
        print(f"Total Alerts: {len(alerts)}")

    def display_alert_detail(self, alert: SecurityAlert):
        """Display detailed alert information."""
        color = self._get_severity_color(alert.severity)
        reset = '\033[0m'

        print(f"\n{color}{'=' * 80}{reset}")
        print(f"{color}ALERT DETAIL: {alert.alert_id}{reset}")
        print(f"{color}{'=' * 80}{reset}")

        print(f"\n  Severity:     {color}{alert.severity.name}{reset}")
        print(f"  Type:         {alert.alert_type}")
        print(f"  User:         {alert.user_id}")
        print(f"  Time:         {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Description:  {alert.description}")
        print(f"  Risk Impact:  +{alert.risk_contribution:.1f}")

        print("\n  Evidence:")
        for key, value in alert.evidence.items():
            if isinstance(value, list):
                print(f"    • {key}: {', '.join(map(str, value[:3]))}")
            else:
                print(f"    • {key}: {value}")

    def display_user_details(self, profile: UserProfile,
                            alerts: List[SecurityAlert],
                            recent_activities: List[UserActivity]):
        """Display detailed user information."""
        print("\n" + "=" * 80)
        print(f"USER DETAILS: {profile.user_id}".center(80))
        print("=" * 80)

        # Risk score
        color = '\033[92m' if profile.risk_score < 30 else '\033[93m' if profile.risk_score < 60 else '\033[91m'
        reset = '\033[0m'
        print(f"\n  Risk Score: {color}{profile.risk_score:.1f}/100{reset}")
        print(f"  Risk Bar:   {self._get_risk_bar(profile.risk_score, 40)}")

        # Statistics
        print(f"\n  📊 Statistics:")
        print(f"    • Total Activities: {profile.total_activities}")
        print(f"    • First Seen: {profile.first_seen.strftime('%Y-%m-%d %H:%M') if profile.first_seen else 'N/A'}")
        print(f"    • Last Seen: {profile.last_seen.strftime('%Y-%m-%d %H:%M') if profile.last_seen else 'N/A'}")
        print(f"    • Login Success/Failure: {profile.login_success_count}/{profile.login_failure_count}")
        print(f"    • IP Addresses Used: {len(profile.ip_addresses)}")
        print(f"    • Sensitive Resources: {profile.sensitive_resource_count}")

        # Baseline info
        print(f"\n  📈 Baseline:")
        print(f"    • Established: {'✓' if profile.baseline_established else '✗'}")
        if profile.baseline_established:
            print(f"    • Avg Daily Logins: {profile.avg_daily_logins:.1f}")
            print(f"    • Normal Login Hours: {sorted(profile.normal_login_hours)}")
            print(f"    • Avg Session Duration: {profile.avg_session_duration:.1f} min")

        # Recent alerts
        user_alerts = [a for a in alerts if a.user_id == profile.user_id]
        if user_alerts:
            print(f"\n  🚨 Recent Alerts ({len(user_alerts)}):")
            for alert in user_alerts[:3]:
                print(f"    • {alert.alert_type} - {alert.severity.name}")

        # Recent activities
        if recent_activities:
            print(f"\n  📝 Recent Activities:")
            for activity in recent_activities[:5]:
                time_str = activity.timestamp.strftime("%m-%d %H:%M")
                status_icon = "✓" if activity.is_success else "✗"
                print(f"    [{time_str}] {activity.action.display_name} - "
                      f"{activity.resource} ({status_icon})")

    def export_alerts_json(self, alerts: List[SecurityAlert],
                          filename: str = "security_alerts.json"):
        """Export alerts to JSON file."""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_alerts': len(alerts),
                'alerts': []
            }

            for alert in alerts:
                export_data['alerts'].append({
                    'alert_id': alert.alert_id,
                    'timestamp': alert.timestamp.isoformat(),
                    'user_id': alert.user_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity.name,
                    'description': alert.description,
                    'risk_contribution': alert.risk_contribution,
                    'evidence': alert.evidence,
                })

            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)

            print(f"\n✓ Alerts exported to '{filename}'")
        except IOError as e:
            print(f"\n✗ Error exporting to file: {e}")


class BehaviorMonitoringSystem:
    """Main user behavior monitoring system controller."""

    def __init__(self):
        """Initialize the monitoring system."""
        self.generator = ActivityGenerator()
        self.analyzer = BehaviorAnalyzer()
        self.display = MonitoringDisplay()

        self.activities: List[UserActivity] = []
        self.profiles: Dict[str, UserProfile] = {}
        self.alerts: List[SecurityAlert] = []

    def generate_activities(self, count_per_user: int = 50):
        """Generate sample user activities."""
        print(f"\n→ Generating activities for {len(self.generator.users)} users...")
        self.activities = self.generator.generate_all_activities(count_per_user)
        print(f"✓ Generated {len(self.activities)} activities")
        self._build_profiles()

    def _build_profiles(self):
        """Build behavioral profiles for all users."""
        if not self.activities:
            print("\n⚠ No activities available. Generate activities first.")
            return

        print("\n→ Building user behavioral profiles...")

        # Group activities by user
        user_activities = defaultdict(list)
        for activity in self.activities:
            user_activities[activity.user_id].append(activity)

        # Build profile for each user
        self.profiles = {}
        for user_id, activities in user_activities.items():
            self.profiles[user_id] = self.analyzer.build_profile(user_id, activities)

        print(f"✓ Built profiles for {len(self.profiles)} users")

    def run_detection(self):
        """Run anomaly detection on recent activities."""
        if not self.activities or not self.profiles:
            print("\n⚠ No profiles available. Build profiles first.")
            return

        print("\n→ Running anomaly detection...")

        # Get recent activities (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_activities = [a for a in self.activities if a.timestamp > cutoff_time]

        # Group recent activities by user
        recent_by_user = defaultdict(list)
        for activity in recent_activities:
            recent_by_user[activity.user_id].append(activity)

        # Detect anomalies
        self.alerts = []
        for user_id, profile in self.profiles.items():
            user_recent = recent_by_user.get(user_id, [])
            if user_recent:
                user_alerts = self.analyzer.detect_anomalies(user_id, profile, user_recent)
                self.alerts.extend(user_alerts)

        # Calculate risk scores
        for user_id, profile in self.profiles.items():
            user_alerts = [a for a in self.alerts if a.user_id == user_id]
            profile.risk_score = self.analyzer.calculate_risk_score(profile, user_alerts)
            profile.anomaly_count = len(user_alerts)

        print(f"✓ Detection complete. Found {len(self.alerts)} alerts")

    def view_profiles(self):
        """Display all user profiles."""
        self.display.display_user_profiles(self.profiles)

    def view_alerts(self):
        """Display all security alerts."""
        self.display.display_alerts(self.alerts)

    def view_user_details(self):
        """View detailed information for a specific user."""
        if not self.profiles:
            print("\n⚠ No profiles available.")
            return

        user_id = input("\nEnter user ID to view: ").strip()

        if user_id not in self.profiles:
            print(f"\n✗ User '{user_id}' not found")
            return

        profile = self.profiles[user_id]
        user_activities = [a for a in self.activities if a.user_id == user_id]
        recent_activities = sorted(user_activities, key=lambda a: a.timestamp, reverse=True)[:10]

        self.display.display_user_details(profile, self.alerts, recent_activities)

    def view_alert_details(self):
        """View detailed information for a specific alert."""
        if not self.alerts:
            print("\n⚠ No alerts available.")
            return

        alert_id = input("\nEnter alert ID to view: ").strip()

        for alert in self.alerts:
            if alert.alert_id == alert_id:
                self.display.display_alert_detail(alert)
                return

        print(f"\n✗ Alert '{alert_id}' not found")

    def export_alerts(self):
        """Export alerts to JSON file."""
        if not self.alerts:
            print("\n⚠ No alerts available to export.")
            return

        filename = input("\nEnter filename [security_alerts.json]: ").strip()
        if not filename:
            filename = "security_alerts.json"

        self.display.export_alerts_json(self.alerts, filename)

    def adjust_thresholds(self):
        """Adjust detection thresholds."""
        print("\n" + "=" * 60)
        print("ADJUST DETECTION THRESHOLDS".center(60))
        print("=" * 60)
        print("\nCurrent thresholds:")
        for key, value in self.analyzer.config.items():
            print(f"  {key}: {value}")

        print("\nEnter new thresholds (press Enter to keep current):")

        try:
            new_failed = input(f"Failed login threshold [{self.analyzer.config['failed_login_threshold']}]: ").strip()
            if new_failed:
                self.analyzer.config['failed_login_threshold'] = int(new_failed)

            new_hour = input(f"Unusual hour threshold (std dev) [{self.analyzer.config['unusual_hour_threshold']}]: ").strip()
            if new_hour:
                self.analyzer.config['unusual_hour_threshold'] = float(new_hour)

            new_spike = input(f"Activity spike threshold (std dev) [{self.analyzer.config['activity_spike_threshold']}]: ").strip()
            if new_spike:
                self.analyzer.config['activity_spike_threshold'] = float(new_spike)

            new_sensitive = input(f"Sensitive resource threshold [{self.analyzer.config['sensitive_resource_threshold']}]: ").strip()
            if new_sensitive:
                self.analyzer.config['sensitive_resource_threshold'] = int(new_sensitive)

            print("\n✓ Thresholds updated. Rerun detection to apply changes.")

        except ValueError:
            print("\n✗ Invalid input. Thresholds unchanged.")

    def show_statistics(self):
        """Display monitoring statistics."""
        if not self.activities:
            print("\n⚠ No data available.")
            return

        print("\n" + "=" * 60)
        print("MONITORING STATISTICS".center(60))
        print("=" * 60)

        # Activity statistics
        print(f"\n📊 Activity Statistics:")
        print(f"  Total Activities: {len(self.activities)}")
        print(f"  Unique Users: {len(self.profiles)}")
        print(f"  Time Range: {self.activities[0].timestamp.strftime('%Y-%m-%d')} to {self.activities[-1].timestamp.strftime('%Y-%m-%d')}")

        # Action distribution
        action_counts = defaultdict(int)
        for activity in self.activities:
            action_counts[activity.action.display_name] += 1

        print("\n  Action Distribution:")
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    • {action}: {count}")

        # Alert statistics
        if self.alerts:
            print(f"\n🚨 Alert Statistics:")
            print(f"  Total Alerts: {len(self.alerts)}")

            severity_counts = defaultdict(int)
            for alert in self.alerts:
                severity_counts[alert.severity.name] += 1

            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    print(f"    • {severity}: {count}")

            alert_types = defaultdict(int)
            for alert in self.alerts:
                alert_types[alert.alert_type] += 1

            print("\n  Top Alert Types:")
            for alert_type, count in sorted(alert_types.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"    • {alert_type}: {count}")

        # Risk score distribution
        if self.profiles:
            scores = [p.risk_score for p in self.profiles.values()]
            print(f"\n📈 Risk Score Distribution:")
            print(f"  Average: {sum(scores)/len(scores):.1f}")
            print(f"  Highest: {max(scores):.1f}")
            print(f"  Lowest: {min(scores):.1f}")

            high_risk = sum(1 for s in scores if s >= 60)
            medium_risk = sum(1 for s in scores if 30 <= s < 60)
            low_risk = sum(1 for s in scores if s < 30)

            print(f"  High Risk (>60): {high_risk} users")
            print(f"  Medium Risk (30-60): {medium_risk} users")
            print(f"  Low Risk (<30): {low_risk} users")

    def run(self):
        """Main CLI interface loop."""
        while True:
            print("\n" + "=" * 60)
            print("👤 USER BEHAVIOR MONITORING SYSTEM".center(60))
            print("=" * 60)
            print(f"Activities: {len(self.activities)} | Users: {len(self.profiles)} | Alerts: {len(self.alerts)}")
            print("-" * 60)
            print("1. Generate Sample Activities")
            print("2. Build User Profiles")
            print("3. Run Anomaly Detection")
            print("4. View User Profiles")
            print("5. View Security Alerts")
            print("6. View User Details")
            print("7. View Alert Details")
            print("8. Export Alerts to JSON")
            print("9. Adjust Detection Thresholds")
            print("10. View Statistics")
            print("11. Exit")
            print("-" * 60)

            choice = input("Select option (1-11): ").strip()

            if choice == '1':
                try:
                    count = input("Activities per user [50]: ").strip()
                    count = int(count) if count else 50
                    self.generate_activities(count)
                except ValueError:
                    print("✗ Invalid number. Using default 50.")
                    self.generate_activities(50)

            elif choice == '2':
                self._build_profiles()

            elif choice == '3':
                self.run_detection()

            elif choice == '4':
                self.view_profiles()

            elif choice == '5':
                self.view_alerts()

            elif choice == '6':
                self.view_user_details()

            elif choice == '7':
                self.view_alert_details()

            elif choice == '8':
                self.export_alerts()

            elif choice == '9':
                self.adjust_thresholds()

            elif choice == '10':
                self.show_statistics()

            elif choice == '11':
                print("\nExiting User Behavior Monitoring System. Stay vigilant! 👁")
                sys.exit(0)

            else:
                print("\n✗ Invalid option. Please select 1-11.")

            input("\nPress Enter to continue...")


def main():
    """Entry point for the user behavior monitoring system."""
    try:
        system = BehaviorMonitoringSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\nExiting User Behavior Monitoring System. Stay vigilant! 👁")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()