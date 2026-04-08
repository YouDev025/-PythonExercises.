#!/usr/bin/env python3
"""
Risk Scoring Engine
A comprehensive risk scoring system for security events, users, and IP addresses.

Calculates individual and aggregated risk scores based on event severity,
asset value, frequency, and recency.

Compatible with PyCharm - uses only Python standard library.
"""

import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import hashlib


class RiskLevel(Enum):
    """Risk levels with associated numeric values."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def weight(self) -> float:
        """Return base weight for calculations."""
        weights = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 2.5,
            RiskLevel.HIGH: 5.0,
            RiskLevel.CRITICAL: 8.0,
        }
        return weights[self]

    @classmethod
    def from_string(cls, value: str) -> 'RiskLevel':
        """Convert string to RiskLevel."""
        value_upper = value.upper()
        for level in cls:
            if level.name == value_upper:
                return level
        return cls.LOW


class EventType(Enum):
    """Security event types with associated risk factors."""
    LOGIN_FAILURE = ("Failed Login", 1.5)
    LOGIN_SUCCESS = ("Successful Login", 0.5)
    PASSWORD_CHANGE = ("Password Change", 1.0)
    PRIVILEGE_ESCALATION = ("Privilege Escalation", 4.5)
    FILE_ACCESS = ("File Access", 1.2)
    FILE_DELETE = ("File Delete", 2.5)
    CONFIG_CHANGE = ("Config Change", 3.0)
    NETWORK_SCAN = ("Network Scan", 2.0)
    DATA_EXPORT = ("Data Export", 3.5)
    API_CALL = ("API Call", 0.8)
    ADMIN_ACTION = ("Admin Action", 2.8)
    MALWARE_DETECTION = ("Malware Detection", 5.0)
    POLICY_VIOLATION = ("Policy Violation", 2.2)
    SUSPICIOUS_PROCESS = ("Suspicious Process", 3.8)

    def __init__(self, display_name: str, base_risk: float):
        self.display_name = display_name
        self.base_risk = base_risk


class AssetType(Enum):
    """Asset types with associated criticality values."""
    WORKSTATION = ("Workstation", 1.0)
    SERVER = ("Server", 2.5)
    DATABASE = ("Database", 4.0)
    DOMAIN_CONTROLLER = ("Domain Controller", 5.0)
    FILE_SERVER = ("File Server", 3.0)
    WEB_SERVER = ("Web Server", 2.8)
    FIREWALL = ("Firewall", 4.5)
    ROUTER = ("Router", 3.5)
    CLOUD_INSTANCE = ("Cloud Instance", 3.0)
    IOT_DEVICE = ("IoT Device", 1.5)

    def __init__(self, display_name: str, criticality: float):
        self.display_name = display_name
        self.criticality = criticality


@dataclass
class SecurityEvent:
    """Represents a single security event."""
    event_id: str
    timestamp: datetime
    source_ip: str
    user_id: Optional[str]
    event_type: EventType
    severity: RiskLevel
    asset_value: RiskLevel
    asset_type: AssetType
    description: str
    event_score: float = 0.0

    def __hash__(self) -> int:
        return hash(self.event_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecurityEvent):
            return False
        return self.event_id == other.event_id

    def get_entity_identifier(self) -> str:
        """Get primary entity identifier (IP or user)."""
        if self.user_id:
            return f"user:{self.user_id}"
        return f"ip:{self.source_ip}"


@dataclass
class EntityRiskProfile:
    """Aggregated risk profile for an entity (IP or user)."""
    entity_id: str
    entity_type: str  # 'ip' or 'user'
    total_events: int = 0
    aggregated_score: float = 0.0
    normalized_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    events: List[SecurityEvent] = field(default_factory=list)
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    peak_severity: RiskLevel = RiskLevel.LOW
    unique_event_types: Set[EventType] = field(default_factory=set)


class RiskScoringEngine:
    """
    Core risk scoring engine that calculates individual and aggregated risk scores.
    """

    def __init__(self, config: Optional[Dict[str, float]] = None):
        """
        Initialize scoring engine with configurable weights.

        Args:
            config: Optional dictionary of scoring weights
        """
        self.config = {
            'severity_weight': 0.30,
            'asset_weight': 0.25,
            'event_type_weight': 0.20,
            'frequency_weight': 0.15,
            'recency_weight': 0.10,
            'max_recency_hours': 72.0,
            'frequency_decay_factor': 0.8,
            'max_score': 100.0,
        }
        if config:
            self.config.update(config)

        # Cache for frequency calculations
        self._frequency_cache: Dict[str, int] = defaultdict(int)
        self._entity_event_cache: Dict[str, List[SecurityEvent]] = defaultdict(list)

    def calculate_event_score(self, event: SecurityEvent,
                            all_events: List[SecurityEvent]) -> float:
        """
        Calculate individual risk score for a single event.

        Args:
            event: Security event to score
            all_events: All events for context

        Returns:
            Event risk score (0-100 scale)
        """
        # Severity component (0-100 scale)
        severity_score = (event.severity.weight / RiskLevel.CRITICAL.weight) * 100

        # Asset value component
        asset_score = (event.asset_value.weight / RiskLevel.CRITICAL.weight) * 100

        # Event type component
        type_score = (event.event_type.base_risk / 5.0) * 100

        # Frequency component (based on same entity)
        entity_events = self._get_entity_events(event.get_entity_identifier(), all_events)
        frequency = len(entity_events)
        frequency_score = min(100.0, frequency * 10) * self.config['frequency_decay_factor']

        # Recency component
        recency_score = self._calculate_recency_score(event.timestamp)

        # Weighted combination
        event_score = (
            severity_score * self.config['severity_weight'] +
            asset_score * self.config['asset_weight'] +
            type_score * self.config['event_type_weight'] +
            frequency_score * self.config['frequency_weight'] +
            recency_score * self.config['recency_weight']
        )

        # Normalize to 0-100 range
        return min(self.config['max_score'], max(0.0, event_score))

    def calculate_entity_risk(self, entity_id: str,
                            events: List[SecurityEvent]) -> EntityRiskProfile:
        """
        Calculate aggregated risk score for an entity.

        Args:
            entity_id: Entity identifier (IP or user)
            events: All events for this entity

        Returns:
            EntityRiskProfile with aggregated scores
        """
        if not events:
            return EntityRiskProfile(
                entity_id=entity_id,
                entity_type='ip' if entity_id.startswith('ip:') else 'user'
            )

        profile = EntityRiskProfile(
            entity_id=entity_id,
            entity_type='ip' if entity_id.startswith('ip:') else 'user',
            total_events=len(events),
            events=sorted(events, key=lambda e: e.timestamp, reverse=True),
            first_seen=min(e.timestamp for e in events),
            last_seen=max(e.timestamp for e in events),
        )

        # Calculate components
        severity_component = self._calculate_severity_component(events)
        frequency_component = self._calculate_frequency_component(events)
        recency_component = self._calculate_recency_component(events)
        diversity_component = self._calculate_diversity_component(events)
        trend_component = self._calculate_trend_component(events)

        # Store breakdown
        profile.score_breakdown = {
            'severity': severity_component,
            'frequency': frequency_component,
            'recency': recency_component,
            'diversity': diversity_component,
            'trend': trend_component,
        }

        # Calculate weighted aggregate score
        weights = {
            'severity': 0.30,
            'frequency': 0.25,
            'recency': 0.20,
            'diversity': 0.15,
            'trend': 0.10,
        }

        profile.aggregated_score = sum(
            profile.score_breakdown[component] * weights[component]
            for component in weights.keys()
        )

        # Normalize to 0-100
        profile.normalized_score = min(100.0, max(0.0, profile.aggregated_score))

        # Determine risk level
        profile.risk_level = self._score_to_risk_level(profile.normalized_score)

        # Additional metadata
        profile.peak_severity = max((e.severity for e in events),
                                   key=lambda s: s.weight, default=RiskLevel.LOW)
        profile.unique_event_types = {e.event_type for e in events}

        return profile

    def _get_entity_events(self, entity_id: str,
                          all_events: List[SecurityEvent]) -> List[SecurityEvent]:
        """Get all events for a specific entity."""
        if not self._entity_event_cache:
            for event in all_events:
                self._entity_event_cache[event.get_entity_identifier()].append(event)
        return self._entity_event_cache.get(entity_id, [])

    def _calculate_recency_score(self, timestamp: datetime) -> float:
        """Calculate recency score based on how recent the event is."""
        now = datetime.now()
        time_diff = now - timestamp
        hours_passed = time_diff.total_seconds() / 3600

        if hours_passed <= 1:
            return 100.0
        elif hours_passed >= self.config['max_recency_hours']:
            return 0.0

        # Exponential decay
        decay_rate = 3.0 / self.config['max_recency_hours']
        return 100.0 * (2.71828 ** (-decay_rate * hours_passed))

    def _calculate_severity_component(self, events: List[SecurityEvent]) -> float:
        """Calculate severity-based risk component."""
        if not events:
            return 0.0

        # Weighted average with emphasis on high severity
        severity_weights = [e.severity.weight for e in events]
        avg_severity = sum(severity_weights) / len(severity_weights)
        max_severity = max(severity_weights)

        # Combine average and maximum (70% max, 30% avg)
        combined = (0.7 * max_severity + 0.3 * avg_severity)

        # Normalize to 0-100
        return (combined / RiskLevel.CRITICAL.weight) * 100

    def _calculate_frequency_component(self, events: List[SecurityEvent]) -> float:
        """Calculate frequency-based risk component."""
        if len(events) < 2:
            return 10.0 if events else 0.0

        # Calculate events per hour rate
        time_span = (events[0].timestamp - events[-1].timestamp).total_seconds() / 3600
        if time_span == 0:
            events_per_hour = len(events) * 10  # High rate for same timestamp
        else:
            events_per_hour = len(events) / max(1.0, time_span)

        # Sigmoid function to map frequency to score
        score = 100.0 / (1.0 + 2.71828 ** (-0.5 * (events_per_hour - 5.0)))

        return min(100.0, score)

    def _calculate_recency_component(self, events: List[SecurityEvent]) -> float:
        """Calculate recency-based risk component for entity."""
        if not events:
            return 0.0

        # Get events from last 24 hours
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_events = [e for e in events if e.timestamp > recent_cutoff]

        if not recent_events:
            return 0.0

        # Weight recent events by recency
        scores = []
        for event in recent_events:
            score = self._calculate_recency_score(event.timestamp)
            scores.append(score)

        # Average with emphasis on most recent
        if scores:
            return (0.6 * max(scores) + 0.4 * (sum(scores) / len(scores)))
        return 0.0

    def _calculate_diversity_component(self, events: List[SecurityEvent]) -> float:
        """Calculate diversity-based risk (variety of event types)."""
        if not events:
            return 0.0

        unique_types = len({e.event_type for e in events})
        unique_assets = len({e.asset_type for e in events})
        unique_ips = len({e.source_ip for e in events})

        # More diversity = higher risk
        diversity_score = (
            min(100, unique_types * 25) * 0.4 +
            min(100, unique_assets * 20) * 0.3 +
            min(100, unique_ips * 15) * 0.3
        )

        return diversity_score

    def _calculate_trend_component(self, events: List[SecurityEvent]) -> float:
        """Calculate trend-based risk (increasing severity over time)."""
        if len(events) < 3:
            return 50.0  # Neutral trend

        sorted_events = sorted(events, key=lambda e: e.timestamp)
        mid_point = len(sorted_events) // 2

        first_half = sorted_events[:mid_point]
        second_half = sorted_events[mid_point:]

        if not first_half or not second_half:
            return 50.0

        avg_first = sum(e.severity.weight for e in first_half) / len(first_half)
        avg_second = sum(e.severity.weight for e in second_half) / len(second_half)

        # Calculate trend (-1 to 1 range)
        if avg_first == 0:
            trend = 1.0 if avg_second > 0 else 0.0
        else:
            trend = (avg_second - avg_first) / avg_first

        # Map trend to 0-100 score
        # Positive trend = higher risk
        return 50.0 + (trend * 50.0)

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level."""
        if score >= 75:
            return RiskLevel.CRITICAL
        elif score >= 50:
            return RiskLevel.HIGH
        elif score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def score_all_events(self, events: List[SecurityEvent]) -> List[SecurityEvent]:
        """Calculate scores for all events."""
        scored_events = []
        for event in events:
            event.event_score = self.calculate_event_score(event, events)
            scored_events.append(event)
        return scored_events

    def aggregate_entity_risks(self,
                               events: List[SecurityEvent]) -> Dict[str, EntityRiskProfile]:
        """
        Calculate risk profiles for all entities.

        Args:
            events: List of all security events

        Returns:
            Dictionary mapping entity IDs to risk profiles
        """
        # Group events by entity
        entity_events: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for event in events:
            entity_events[event.get_entity_identifier()].append(event)

        # Calculate profiles
        profiles = {}
        for entity_id, entity_event_list in entity_events.items():
            profiles[entity_id] = self.calculate_entity_risk(entity_id, entity_event_list)

        return profiles

    def get_top_risky_entities(self, profiles: Dict[str, EntityRiskProfile],
                              limit: int = 10) -> List[EntityRiskProfile]:
        """Get top risky entities sorted by score."""
        sorted_profiles = sorted(
            profiles.values(),
            key=lambda p: p.normalized_score,
            reverse=True
        )
        return sorted_profiles[:limit]


class EventGenerator:
    """Generates realistic sample security events."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize event generator with optional random seed."""
        if seed:
            random.seed(seed)

        self.event_types = list(EventType)
        self.severities = list(RiskLevel)
        self.asset_values = list(RiskLevel)
        self.asset_types = list(AssetType)
        self.ips = self._generate_ip_pool(100)
        self.users = self._generate_user_pool(30)

        self.descriptions = {
            EventType.LOGIN_FAILURE: [
                "Multiple failed login attempts",
                "Invalid credentials provided",
                "Account lockout threshold reached",
            ],
            EventType.LOGIN_SUCCESS: [
                "User logged in successfully",
                "Remote desktop connection established",
                "SSH authentication successful",
            ],
            EventType.PRIVILEGE_ESCALATION: [
                "User attempted to elevate privileges",
                "Sudo command executed",
                "Admin role assigned",
            ],
            EventType.FILE_ACCESS: [
                "Sensitive file accessed",
                "Document retrieved from shared drive",
                "Configuration file read",
            ],
            EventType.DATA_EXPORT: [
                "Large data export detected",
                "Database dump executed",
                "File transfer to external location",
            ],
            EventType.MALWARE_DETECTION: [
                "Malware signature detected",
                "Suspicious process behavior",
                "Known bad hash identified",
            ],
        }

        self._event_counter = 0

    def _generate_ip_pool(self, count: int) -> List[str]:
        """Generate a pool of IP addresses."""
        ips = []
        for _ in range(count):
            if random.random() < 0.4:
                # Internal IPs
                ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            elif random.random() < 0.7:
                # DMZ IPs
                ip = f"172.16.{random.randint(0, 255)}.{random.randint(1, 254)}"
            else:
                # External IPs
                ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 254)}"
            ips.append(ip)
        return ips

    def _generate_user_pool(self, count: int) -> List[str]:
        """Generate a pool of usernames."""
        prefixes = ['admin', 'user', 'service', 'system', 'backup', 'db', 'web', 'app']
        users = []
        for _ in range(count):
            prefix = random.choice(prefixes)
            suffix = random.randint(100, 999)
            users.append(f"{prefix}{suffix}")
        return users

    def generate_event(self) -> SecurityEvent:
        """Generate a single random security event."""
        self._event_counter += 1
        event_id = hashlib.md5(f"event_{self._event_counter}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        event_type = random.choice(self.event_types)

        # Adjust severity based on event type
        if event_type in [EventType.MALWARE_DETECTION, EventType.PRIVILEGE_ESCALATION]:
            severity = random.choices(
                [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.MEDIUM],
                weights=[0.5, 0.3, 0.2]
            )[0]
        elif event_type in [EventType.DATA_EXPORT, EventType.CONFIG_CHANGE]:
            severity = random.choices(
                [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.LOW],
                weights=[0.5, 0.3, 0.2]
            )[0]
        else:
            severity = random.choices(
                [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH],
                weights=[0.5, 0.3, 0.2]
            )[0]

        # Asset value assignment
        if random.random() < 0.2:
            asset_value = RiskLevel.HIGH
        elif random.random() < 0.5:
            asset_value = RiskLevel.MEDIUM
        else:
            asset_value = RiskLevel.LOW

        asset_type = random.choice(self.asset_types)

        # Adjust asset criticality for certain types
        if asset_type in [AssetType.DOMAIN_CONTROLLER, AssetType.DATABASE]:
            asset_value = random.choices(
                [RiskLevel.HIGH, RiskLevel.CRITICAL],
                weights=[0.6, 0.4]
            )[0]

        # Generate timestamp within last 7 days
        hours_ago = random.uniform(0, 168)  # 7 days
        timestamp = datetime.now() - timedelta(hours=hours_ago)

        # Decide if event has a user ID
        has_user = random.random() < 0.7
        user_id = random.choice(self.users) if has_user else None

        description = random.choice(self.descriptions.get(
            event_type, ["Security event detected"]
        ))

        # Add context to description
        if user_id:
            description += f" by {user_id}"
        description += f" on {asset_type.display_name}"

        return SecurityEvent(
            event_id=event_id,
            timestamp=timestamp,
            source_ip=random.choice(self.ips),
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            asset_value=asset_value,
            asset_type=asset_type,
            description=description,
        )

    def generate_events(self, count: int = 50) -> List[SecurityEvent]:
        """Generate multiple random events."""
        events = []
        for _ in range(count):
            events.append(self.generate_event())

        # Create clusters of related events for realism
        if count > 20:
            # Pick a few "suspicious" entities
            suspicious_ips = random.sample(self.ips, min(3, len(self.ips)))
            suspicious_users = random.sample(self.users, min(2, len(self.users)))

            for ip in suspicious_ips:
                for _ in range(random.randint(3, 8)):
                    event = self.generate_event()
                    event.source_ip = ip
                    event.severity = random.choices(
                        [RiskLevel.HIGH, RiskLevel.MEDIUM],
                        weights=[0.7, 0.3]
                    )[0]
                    events.append(event)

            for user in suspicious_users:
                for _ in range(random.randint(2, 6)):
                    event = self.generate_event()
                    event.user_id = user
                    event.event_type = random.choice([
                        EventType.LOGIN_FAILURE,
                        EventType.PRIVILEGE_ESCALATION,
                        EventType.FILE_ACCESS
                    ])
                    events.append(event)

        return events


class RiskDisplay:
    """Handles formatted display of risk scores and profiles."""

    @staticmethod
    def _get_risk_color(score: float) -> str:
        """Get ANSI color code based on risk score."""
        if score >= 75:
            return '\033[91m'  # Red
        elif score >= 50:
            return '\033[93m'  # Yellow
        elif score >= 25:
            return '\033[94m'  # Blue
        else:
            return '\033[92m'  # Green

    @staticmethod
    def _get_risk_bar(score: float, width: int = 30) -> str:
        """Generate visual risk bar."""
        filled = int((score / 100) * width)
        return '█' * filled + '░' * (width - filled)

    def display_entity_risks(self, profiles: List[EntityRiskProfile],
                           title: str = "ENTITY RISK PROFILES"):
        """Display entity risk profiles in a formatted table."""
        if not profiles:
            print("\n" + "=" * 100)
            print("No risk profiles to display")
            print("=" * 100)
            return

        print("\n" + "=" * 120)
        print(f"{title:^120}")
        print("=" * 120)

        # Header
        print(f"{'Rank':<6} {'Score':<7} {'Bar':<32} {'Entity ID':<25} "
              f"{'Type':<6} {'Events':<7} {'Level':<10} {'Peak':<8}")
        print("-" * 120)

        # Rows
        for rank, profile in enumerate(profiles, 1):
            color = self._get_risk_color(profile.normalized_score)
            reset = '\033[0m'
            bar = self._get_risk_bar(profile.normalized_score, 30)

            entity_display = profile.entity_id.replace('ip:', '').replace('user:', '')[:24]
            entity_type = profile.entity_type.upper()

            print(f"{color}{rank:<6} {profile.normalized_score:<6.1f} {bar:<32} "
                  f"{entity_display:<25} {entity_type:<6} {profile.total_events:<7} "
                  f"{profile.risk_level.name:<10} {profile.peak_severity.name:<8}{reset}")

        print("=" * 120)

    def display_profile_detail(self, profile: EntityRiskProfile):
        """Display detailed risk profile for a single entity."""
        color = self._get_risk_color(profile.normalized_score)
        reset = '\033[0m'

        print("\n" + "=" * 80)
        print(f"{color}ENTITY RISK PROFILE - {profile.entity_id}{reset}".center(80))
        print("=" * 80)

        # Summary
        print(f"\n{color}Overall Risk Score: {profile.normalized_score:.1f}/100{reset}")
        print(f"Risk Level: {profile.risk_level.name}")
        print(f"Risk Bar: {self._get_risk_bar(profile.normalized_score, 50)}")

        # Statistics
        print(f"\n{'Statistics':-^40}")
        print(f"  Total Events:     {profile.total_events}")
        print(f"  First Seen:       {profile.first_seen.strftime('%Y-%m-%d %H:%M') if profile.first_seen else 'N/A'}")
        print(f"  Last Seen:        {profile.last_seen.strftime('%Y-%m-%d %H:%M') if profile.last_seen else 'N/A'}")
        print(f"  Peak Severity:    {profile.peak_severity.name}")
        print(f"  Unique Event Types: {len(profile.unique_event_types)}")

        # Score Breakdown
        print(f"\n{'Score Breakdown':-^40}")
        for component, score in profile.score_breakdown.items():
            bar = self._get_risk_bar(score, 20)
            print(f"  {component.capitalize():<12}: {score:>5.1f} {bar}")

        # Recent Events
        if profile.events:
            print(f"\n{'Recent Events (Top 3)':-^40}")
            for event in profile.events[:3]:
                time_str = event.timestamp.strftime("%m-%d %H:%M")
                print(f"  [{time_str}] {event.event_type.display_name} - "
                      f"Score: {event.event_score:.1f}")

    def display_score_breakdown_chart(self, profiles: List[EntityRiskProfile]):
        """Display a visual breakdown chart of risk components."""
        if not profiles:
            return

        print("\n" + "=" * 80)
        print("RISK COMPONENT BREAKDOWN CHART".center(80))
        print("=" * 80)

        components = ['severity', 'frequency', 'recency', 'diversity', 'trend']
        colors = ['\033[91m', '\033[93m', '\033[94m', '\033[92m', '\033[95m']

        for profile in profiles[:5]:  # Top 5 entities
            entity_short = profile.entity_id.replace('ip:', '').replace('user:', '')[:20]
            print(f"\n{entity_short}:")

            for i, component in enumerate(components):
                score = profile.score_breakdown.get(component, 0)
                bar = self._get_risk_bar(score, 40)
                color = colors[i % len(colors)]
                reset = '\033[0m'
                print(f"  {color}{component.capitalize():<12}: {bar} {score:.1f}{reset}")

    def display_event_table(self, events: List[SecurityEvent],
                          title: str = "SECURITY EVENTS", limit: int = 20):
        """Display security events in a table."""
        if not events:
            print("\n" + "=" * 100)
            print("No events to display")
            print("=" * 100)
            return

        print("\n" + "=" * 130)
        print(f"{title:^130}")
        print("=" * 130)

        # Header
        print(f"{'Time':<18} {'Event Type':<20} {'Entity':<22} "
              f"{'Severity':<9} {'Asset Value':<11} {'Score':<7}")
        print("-" * 130)

        # Sort by score and show limited number
        sorted_events = sorted(events, key=lambda e: e.event_score, reverse=True)[:limit]

        for event in sorted_events:
            color = self._get_risk_color(event.event_score)
            reset = '\033[0m'

            time_str = event.timestamp.strftime("%m-%d %H:%M")
            entity = event.user_id if event.user_id else event.source_ip

            print(f"{color}{time_str:<18} {event.event_type.display_name:<20} "
                  f"{entity:<22} {event.severity.name:<9} {event.asset_value.name:<11} "
                  f"{event.event_score:<6.1f}{reset}")

        if len(events) > limit:
            print(f"\n... and {len(events) - limit} more events")

        print("=" * 130)

    def export_to_json(self, events: List[SecurityEvent],
                      profiles: Dict[str, EntityRiskProfile],
                      filename: str = "risk_scores.json"):
        """Export risk scores and events to JSON file."""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'summary': {
                    'total_events': len(events),
                    'total_entities': len(profiles),
                    'average_risk_score': sum(p.normalized_score for p in profiles.values()) / len(profiles) if profiles else 0,
                },
                'entity_profiles': [],
                'events': []
            }

            # Export profiles
            for profile in sorted(profiles.values(),
                                key=lambda p: p.normalized_score,
                                reverse=True):
                export_data['entity_profiles'].append({
                    'entity_id': profile.entity_id,
                    'entity_type': profile.entity_type,
                    'total_events': profile.total_events,
                    'normalized_score': profile.normalized_score,
                    'risk_level': profile.risk_level.name,
                    'score_breakdown': profile.score_breakdown,
                    'first_seen': profile.first_seen.isoformat() if profile.first_seen else None,
                    'last_seen': profile.last_seen.isoformat() if profile.last_seen else None,
                    'peak_severity': profile.peak_severity.name,
                })

            # Export events (top 100 by score)
            top_events = sorted(events, key=lambda e: e.event_score, reverse=True)[:100]
            for event in top_events:
                export_data['events'].append({
                    'event_id': event.event_id,
                    'timestamp': event.timestamp.isoformat(),
                    'source_ip': event.source_ip,
                    'user_id': event.user_id,
                    'event_type': event.event_type.display_name,
                    'severity': event.severity.name,
                    'asset_value': event.asset_value.name,
                    'asset_type': event.asset_type.display_name,
                    'description': event.description,
                    'event_score': event.event_score,
                })

            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)

            print(f"\n✓ Risk data exported to '{filename}'")
        except IOError as e:
            print(f"\n✗ Error exporting to file: {e}")
        except Exception as e:
            print(f"\n✗ Error during JSON serialization: {e}")


class RiskScoringSystem:
    """Main risk scoring system controller."""

    def __init__(self):
        """Initialize the risk scoring system."""
        self.generator = EventGenerator()
        self.engine = RiskScoringEngine()
        self.display = RiskDisplay()
        self.events: List[SecurityEvent] = []
        self.entity_profiles: Dict[str, EntityRiskProfile] = {}
        self.scored_events: List[SecurityEvent] = []

    def generate_sample_events(self, count: int = 50):
        """Generate sample security events."""
        print(f"\n→ Generating {count} sample security events...")
        self.events = self.generator.generate_events(count)
        print(f"✓ Generated {len(self.events)} events")
        self._calculate_scores()

    def _calculate_scores(self):
        """Internal method to calculate all risk scores."""
        if self.events:
            self.scored_events = self.engine.score_all_events(self.events)
            self.entity_profiles = self.engine.aggregate_entity_risks(self.scored_events)
            print(f"✓ Calculated risk scores for {len(self.entity_profiles)} entities")

    def view_all_events(self):
        """Display all security events."""
        self.display.display_event_table(self.scored_events, "ALL SECURITY EVENTS")

    def view_entity_risks(self):
        """Display entity risk profiles."""
        if not self.entity_profiles:
            print("\n⚠ No risk profiles available. Generate events first.")
            return

        top_profiles = self.engine.get_top_risky_entities(self.entity_profiles, 20)
        self.display.display_entity_risks(top_profiles)

    def view_top_risks(self):
        """Display top risky entities with details."""
        if not self.entity_profiles:
            print("\n⚠ No risk profiles available. Generate events first.")
            return

        top_profiles = self.engine.get_top_risky_entities(self.entity_profiles, 5)

        print("\n" + "=" * 80)
        print("TOP RISK ENTITIES".center(80))
        print("=" * 80)

        for i, profile in enumerate(top_profiles, 1):
            self.display.display_profile_detail(profile)

            if i < len(top_profiles):
                print("\n" + "-" * 80)

    def view_breakdown_chart(self):
        """Display risk component breakdown chart."""
        if not self.entity_profiles:
            print("\n⚠ No risk profiles available. Generate events first.")
            return

        top_profiles = self.engine.get_top_risky_entities(self.entity_profiles, 5)
        self.display.display_score_breakdown_chart(top_profiles)

    def search_entity(self):
        """Search for a specific entity and display its profile."""
        if not self.entity_profiles:
            print("\n⚠ No risk profiles available. Generate events first.")
            return

        search_term = input("\nEnter IP address or username to search: ").strip()

        # Try both ip: and user: prefixes
        found = False
        for prefix in ['ip:', 'user:']:
            entity_id = f"{prefix}{search_term}"
            if entity_id in self.entity_profiles:
                self.display.display_profile_detail(self.entity_profiles[entity_id])
                found = True
                break

        if not found:
            print(f"\n✗ Entity '{search_term}' not found")

    def export_results(self):
        """Export results to JSON file."""
        if not self.events:
            print("\n⚠ No data available to export.")
            return

        filename = input("\nEnter filename [risk_scores.json]: ").strip()
        if not filename:
            filename = "risk_scores.json"

        self.display.export_to_json(self.scored_events, self.entity_profiles, filename)

    def adjust_weights(self):
        """Interactive weight adjustment."""
        print("\n" + "=" * 60)
        print("ADJUST SCORING WEIGHTS".center(60))
        print("=" * 60)
        print("\nCurrent weights:")
        for key, value in self.engine.config.items():
            if key.endswith('_weight'):
                print(f"  {key}: {value}")

        print("\nEnter new weights (press Enter to keep current):")

        try:
            new_severity = input(f"Severity weight [{self.engine.config['severity_weight']}]: ").strip()
            if new_severity:
                self.engine.config['severity_weight'] = float(new_severity)

            new_asset = input(f"Asset weight [{self.engine.config['asset_weight']}]: ").strip()
            if new_asset:
                self.engine.config['asset_weight'] = float(new_asset)

            new_type = input(f"Event type weight [{self.engine.config['event_type_weight']}]: ").strip()
            if new_type:
                self.engine.config['event_type_weight'] = float(new_type)

            new_freq = input(f"Frequency weight [{self.engine.config['frequency_weight']}]: ").strip()
            if new_freq:
                self.engine.config['frequency_weight'] = float(new_freq)

            new_recency = input(f"Recency weight [{self.engine.config['recency_weight']}]: ").strip()
            if new_recency:
                self.engine.config['recency_weight'] = float(new_recency)

            # Normalize weights to sum to 1.0
            weight_keys = ['severity_weight', 'asset_weight', 'event_type_weight',
                          'frequency_weight', 'recency_weight']
            total = sum(self.engine.config[key] for key in weight_keys)

            if abs(total - 1.0) > 0.001:
                print(f"\n⚠ Weights sum to {total:.3f}, normalizing to 1.0")
                for key in weight_keys:
                    self.engine.config[key] /= total

            print("\n✓ Weights updated. Recalculating scores...")
            self._calculate_scores()

        except ValueError:
            print("\n✗ Invalid input. Weights unchanged.")

    def show_statistics(self):
        """Display comprehensive statistics."""
        if not self.events:
            print("\n⚠ No data available.")
            return

        print("\n" + "=" * 60)
        print("RISK STATISTICS".center(60))
        print("=" * 60)

        # Event statistics
        print("\n📊 Event Statistics:")
        print(f"  Total Events: {len(self.events)}")
        print(f"  Unique IPs: {len(set(e.source_ip for e in self.events))}")
        print(f"  Unique Users: {len(set(e.user_id for e in self.events if e.user_id))}")

        # Severity distribution
        severity_count = defaultdict(int)
        for event in self.events:
            severity_count[event.severity.name] += 1

        print("\n  Severity Distribution:")
        for severity, count in sorted(severity_count.items()):
            bar_length = int((count / len(self.events)) * 30)
            bar = '█' * bar_length
            print(f"    {severity:<10}: {count:>4} {bar}")

        # Risk profile statistics
        if self.entity_profiles:
            profiles = list(self.entity_profiles.values())
            scores = [p.normalized_score for p in profiles]

            print("\n🎯 Risk Profile Statistics:")
            print(f"  Total Entities: {len(profiles)}")
            print(f"  Average Risk Score: {sum(scores)/len(scores):.1f}")
            print(f"  Highest Risk Score: {max(scores):.1f}")
            print(f"  Lowest Risk Score: {min(scores):.1f}")

            # Risk level distribution
            level_count = defaultdict(int)
            for profile in profiles:
                level_count[profile.risk_level.name] += 1

            print("\n  Risk Level Distribution:")
            for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                count = level_count.get(level, 0)
                if count > 0:
                    bar_length = int((count / len(profiles)) * 30)
                    bar = '█' * bar_length
                    print(f"    {level:<10}: {count:>4} {bar}")

        # Top event types
        type_count = defaultdict(int)
        for event in self.events:
            type_count[event.event_type.display_name] += 1

        print("\n📈 Top Event Types:")
        for event_type, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {event_type:<20}: {count:>4}")

    def run(self):
        """Main CLI interface loop."""
        while True:
            print("\n" + "=" * 60)
            print("🎯 RISK SCORING ENGINE".center(60))
            print("=" * 60)
            print(f"Total Events: {len(self.events)} | Entities: {len(self.entity_profiles)}")
            print("-" * 60)
            print("1. Generate Sample Events")
            print("2. View All Security Events")
            print("3. View Entity Risk Profiles")
            print("4. View Top Risk Entities (Detailed)")
            print("5. View Risk Component Breakdown")
            print("6. Search Entity Profile")
            print("7. Export Results to JSON")
            print("8. Adjust Scoring Weights")
            print("9. View Statistics")
            print("10. Exit")
            print("-" * 60)

            choice = input("Select option (1-10): ").strip()

            if choice == '1':
                try:
                    count = input("Number of events to generate [50]: ").strip()
                    count = int(count) if count else 50
                    self.generate_sample_events(count)
                except ValueError:
                    print("✗ Invalid number. Using default 50.")
                    self.generate_sample_events(50)

            elif choice == '2':
                self.view_all_events()

            elif choice == '3':
                self.view_entity_risks()

            elif choice == '4':
                self.view_top_risks()

            elif choice == '5':
                self.view_breakdown_chart()

            elif choice == '6':
                self.search_entity()

            elif choice == '7':
                self.export_results()

            elif choice == '8':
                self.adjust_weights()

            elif choice == '9':
                self.show_statistics()

            elif choice == '10':
                print("\nExiting Risk Scoring Engine. Stay secure! 🎯")
                sys.exit(0)

            else:
                print("\n✗ Invalid option. Please select 1-10.")

            input("\nPress Enter to continue...")


def main():
    """Entry point for the risk scoring engine."""
    try:
        system = RiskScoringSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\nExiting Risk Scoring Engine. Stay secure! 🎯")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()