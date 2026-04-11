#!/usr/bin/env python3
"""
Mini Data Pipeline for Security Log Processing
Author: Senior Python Developer & Data Engineer
Description: A complete, runnable data pipeline that processes security logs
             through ingestion, cleaning, normalization, transformation, and output.
Compatibility: Python 3.6+ (standard library only)
Usage: python mini_data_pipeline.py
"""

import json
import random
import re
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter


class SecurityLogPipeline:
    """
    A complete data pipeline for processing security logs with multiple stages.
    All operations are performed in-memory using standard library only.
    """

    def __init__(self):
        """Initialize pipeline with empty state and configuration."""
        self.raw_logs: List[str] = []
        self.cleaned_logs: List[Dict[str, Any]] = []
        self.normalized_logs: List[Dict[str, Any]] = []
        self.enriched_logs: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            'ingested_count': 0,
            'cleaned_count': 0,
            'normalized_count': 0,
            'enriched_count': 0,
            'invalid_entries': 0,
            'anomalies_detected': 0,
            'processing_time': 0
        }

        # Suspicious patterns for anomaly detection
        self.suspicious_patterns = {
            'ip': [r'192\.168\.', r'10\.', r'172\.(1[6-9]|2[0-9]|3[0-1])\.'],  # Internal IPs
            'user': [r'admin', r'root', r'system'],
            'event': [r'failed', r'invalid', r'error', r'denied', r'blocked'],
            'status': [r'4\d{2}', r'5\d{2}']  # HTTP error codes
        }

        # Anomaly thresholds
        self.anomaly_thresholds = {
            'failed_login_attempts': 3,
            'suspicious_ip_count': 2
        }

    def generate_sample_logs(self, count: int = 20) -> List[str]:
        """
        Generate realistic sample security logs for demonstration.

        Args:
            count: Number of log entries to generate

        Returns:
            List of raw log strings
        """
        log_templates = {
            'web': [
                '{timestamp} {source} {method} {endpoint} {status} {response_time}ms - {user} from {ip}',
                '{timestamp} {source} WARNING: Suspicious request to {endpoint} from {ip}',
                '{timestamp} {source} ERROR: Authentication failed for user {user} from {ip}'
            ],
            'auth': [
                '{timestamp} {source} {event}: User {user} logged in from {ip}',
                '{timestamp} {source} {event}: Failed password for {user} from {ip}',
                '{timestamp} {source} {event}: Account locked for {user} after multiple failures'
            ],
            'system': [
                '{timestamp} {source} {event}: Service {service} restarted',
                '{timestamp} {source} {event}: High memory usage detected ({memory}%)',
                '{timestamp} {source} {event}: Unauthorized access attempt to {resource}'
            ]
        }

        sources = ['web-server-01', 'auth-service', 'system-monitor', 'firewall', 'proxy']
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        endpoints = ['/api/login', '/admin', '/api/users', '/dashboard', '/config']
        statuses = ['200', '301', '403', '404', '500', '502']
        users = ['john.doe', 'admin', 'service-account', 'backup-user', 'root', 'unknown']
        ips = ['192.168.1.100', '10.0.0.50', '172.16.0.25', '203.0.113.45', '198.51.100.78']
        events = ['SUCCESS', 'FAILURE', 'WARNING', 'INFO', 'ERROR']
        services = ['nginx', 'postgresql', 'redis', 'ssh', 'docker']
        resources = ['/etc/passwd', '/var/log', 'database', 'config.yaml']

        logs = []
        base_time = datetime.now() - timedelta(hours=1)

        for i in range(count):
            # Generate timestamp with increment
            timestamp = (base_time + timedelta(minutes=i * 3)).strftime('%Y-%m-%d %H:%M:%S')

            # Randomly select log type and template
            log_type = random.choice(list(log_templates.keys()))
            template = random.choice(log_templates[log_type])

            # Prepare variables for template
            variables = {
                'timestamp': timestamp,
                'source': random.choice(sources),
                'method': random.choice(methods),
                'endpoint': random.choice(endpoints),
                'status': random.choice(statuses),
                'response_time': random.randint(10, 500),
                'user': random.choice(users),
                'ip': random.choice(ips),
                'event': random.choice(events),
                'service': random.choice(services),
                'memory': random.randint(60, 95),
                'resource': random.choice(resources)
            }

            # Occasionally create malformed log for testing cleaning
            if random.random() < 0.05:  # 5% chance of malformed log
                log_entry = f"INVALID_LOG_FORMAT {timestamp} missing fields"
            elif random.random() < 0.05:
                log_entry = ""  # Empty log
            else:
                log_entry = template.format(**variables)

            logs.append(log_entry)

        return logs

    def ingest_data(self, use_sample: bool = True) -> List[str]:
        """
        Ingest raw log data from sample generator.
        In production, this could read from files, APIs, or message queues.

        Args:
            use_sample: Whether to generate sample data (True) or use empty list (False)

        Returns:
            List of raw log strings
        """
        print("\n[STAGE 1] DATA INGESTION")
        print("-" * 50)

        if use_sample:
            self.raw_logs = self.generate_sample_logs(25)
            print(f"✓ Generated {len(self.raw_logs)} sample log entries")
        else:
            self.raw_logs = []
            print("✓ Initialized empty log collection")

        self.metrics['ingested_count'] = len(self.raw_logs)

        # Display first 5 raw logs as preview
        print("\n📋 Raw Logs Preview (first 5):")
        for i, log in enumerate(self.raw_logs[:5], 1):
            print(f"  {i}. {log[:80]}{'...' if len(log) > 80 else ''}")

        return self.raw_logs

    def clean_data(self, logs: List[str]) -> List[Dict[str, Any]]:
        """
        Clean raw logs by removing empty entries and invalid formats.
        Convert string logs to structured dictionaries.

        Args:
            logs: List of raw log strings

        Returns:
            List of cleaned log dictionaries
        """
        print("\n[STAGE 2] DATA CLEANING")
        print("-" * 50)

        cleaned = []
        invalid_count = 0

        for log in logs:
            # Skip empty logs
            if not log or log.strip() == "":
                invalid_count += 1
                continue

            # Skip logs with "INVALID_LOG_FORMAT"
            if "INVALID_LOG_FORMAT" in log:
                invalid_count += 1
                continue

            # Parse log into basic structure
            parsed_log = self._parse_log_line(log)

            if parsed_log:
                cleaned.append(parsed_log)
            else:
                invalid_count += 1

        self.cleaned_logs = cleaned
        self.metrics['cleaned_count'] = len(cleaned)
        self.metrics['invalid_entries'] = invalid_count

        print(f"✓ Cleaned {len(cleaned)} valid log entries")
        print(f"✗ Removed {invalid_count} invalid/malformed entries")

        # Show sample of cleaned data
        if cleaned:
            print("\n📋 Cleaned Logs Preview (first 3):")
            for i, log in enumerate(cleaned[:3], 1):
                print(f"  {i}. {json.dumps(log, default=str)[:100]}...")

        return cleaned

    def _parse_log_line(self, log: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single log line into structured dictionary.
        Uses regex patterns to extract common log formats.

        Args:
            log: Raw log string

        Returns:
            Parsed log dictionary or None if parsing fails
        """
        # Pattern 1: Timestamp at start YYYY-MM-DD HH:MM:SS
        timestamp_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        timestamp_match = re.match(timestamp_pattern, log)

        if not timestamp_match:
            return None

        timestamp = timestamp_match.group(1)
        remaining = log[len(timestamp):].strip()

        # Extract source (first word after timestamp)
        source_pattern = r'^(\S+)'
        source_match = re.match(source_pattern, remaining)
        source = source_match.group(1) if source_match else 'unknown'

        if source_match:
            remaining = remaining[len(source):].strip()

        # Build basic structure
        parsed = {
            'timestamp': timestamp,
            'source': source,
            'raw_message': log,
            'event_type': 'unknown',
            'user': None,
            'ip': None,
            'status': None,
            'message': remaining
        }

        # Extract IP address if present
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ip_match = re.search(ip_pattern, log)
        if ip_match:
            parsed['ip'] = ip_match.group(0)

        # Extract username if present (simplified pattern)
        user_pattern = r'(?:user|for)\s+(\S+)'
        user_match = re.search(user_pattern, log, re.IGNORECASE)
        if user_match:
            parsed['user'] = user_match.group(1)

        # Extract event type
        if 'failed' in log.lower() or 'error' in log.lower():
            parsed['event_type'] = 'error'
        elif 'warning' in log.lower():
            parsed['event_type'] = 'warning'
        elif 'success' in log.lower():
            parsed['event_type'] = 'success'
        elif 'info' in log.lower():
            parsed['event_type'] = 'info'

        # Extract status code if present
        status_pattern = r'\b([1-5][0-9]{2})\b'
        status_match = re.search(status_pattern, log)
        if status_match:
            parsed['status'] = status_match.group(1)

        return parsed

    def normalize_data(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize logs to unified structure with consistent fields.

        Args:
            logs: List of cleaned log dictionaries

        Returns:
            List of normalized log dictionaries
        """
        print("\n[STAGE 3] DATA NORMALIZATION")
        print("-" * 50)

        normalized = []

        for log in logs:
            # Create unified structure
            unified_log = {
                'timestamp': log.get('timestamp'),
                'source': log.get('source', 'unknown'),
                'event_type': log.get('event_type', 'unknown'),
                'user': log.get('user', 'anonymous'),
                'ip': log.get('ip', '0.0.0.0'),
                'status': log.get('status', 'N/A'),
                'message': log.get('message', ''),
                'severity': self._calculate_severity(log)
            }

            # Convert timestamp to datetime object for consistency
            try:
                unified_log['timestamp_dt'] = datetime.strptime(
                    unified_log['timestamp'], '%Y-%m-%d %H:%M:%S'
                )
            except (ValueError, TypeError):
                unified_log['timestamp_dt'] = datetime.now()

            normalized.append(unified_log)

        self.normalized_logs = normalized
        self.metrics['normalized_count'] = len(normalized)

        print(f"✓ Normalized {len(normalized)} log entries to unified schema")
        print("\n📊 Field Coverage Statistics:")

        # Calculate field coverage
        field_coverage = {
            'timestamp': sum(1 for l in normalized if l['timestamp']),
            'source': sum(1 for l in normalized if l['source'] != 'unknown'),
            'user': sum(1 for l in normalized if l['user'] != 'anonymous'),
            'ip': sum(1 for l in normalized if l['ip'] != '0.0.0.0'),
            'status': sum(1 for l in normalized if l['status'] != 'N/A')
        }

        for field, count in field_coverage.items():
            percentage = (count / len(normalized)) * 100 if normalized else 0
            print(f"  • {field}: {count}/{len(normalized)} ({percentage:.1f}%)")

        return normalized

    def _calculate_severity(self, log: Dict[str, Any]) -> str:
        """
        Calculate severity level based on log content.

        Args:
            log: Parsed log dictionary

        Returns:
            Severity string: 'low', 'medium', 'high', or 'critical'
        """
        message = log.get('message', '').lower()
        event_type = log.get('event_type', '').lower()
        status = log.get('status', '')

        # Critical conditions
        if 'unauthorized' in message or 'attack' in message:
            return 'critical'
        if status in ['500', '502', '503', '504']:
            return 'critical'

        # High severity
        if event_type == 'error' or 'failed' in message:
            return 'high'
        if status in ['403', '401']:
            return 'high'

        # Medium severity
        if event_type == 'warning' or 'suspicious' in message:
            return 'medium'
        if status in ['404', '405']:
            return 'medium'

        # Low severity (default)
        return 'low'

    def transform_data(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform and enrich logs with additional metadata and tags.
        Detect anomalies and add suspicious flags.

        Args:
            logs: List of normalized log dictionaries

        Returns:
            List of enriched log dictionaries
        """
        print("\n[STAGE 4] DATA TRANSFORMATION & ENRICHMENT")
        print("-" * 50)

        enriched = []
        anomalies_detected = 0

        # Collect statistics for anomaly detection
        ip_counter = Counter()
        failed_attempts = Counter()

        for log in logs:
            if log['event_type'] == 'error' or 'failed' in log['message'].lower():
                if log['user'] and log['user'] != 'anonymous':
                    failed_attempts[log['user']] += 1
                if log['ip'] and log['ip'] != '0.0.0.0':
                    ip_counter[log['ip']] += 1

        # Enrich each log entry
        for log in logs:
            enriched_log = log.copy()

            # Add enrichment fields
            enriched_log['tags'] = []
            enriched_log['is_suspicious'] = False
            enriched_log['anomaly_reasons'] = []

            # Tag based on event type
            if log['event_type'] == 'error':
                enriched_log['tags'].append('error_event')
            elif log['event_type'] == 'warning':
                enriched_log['tags'].append('warning_event')
            elif log['event_type'] == 'success':
                enriched_log['tags'].append('successful_event')

            # Tag based on source
            if 'auth' in log['source'].lower():
                enriched_log['tags'].append('authentication')
            elif 'web' in log['source'].lower():
                enriched_log['tags'].append('web_traffic')
            elif 'system' in log['source'].lower():
                enriched_log['tags'].append('system_event')
            elif 'firewall' in log['source'].lower():
                enriched_log['tags'].append('network_security')

            # Anomaly detection
            # Check for internal IP patterns (potential lateral movement)
            if log['ip'] and log['ip'] != '0.0.0.0':
                for pattern in self.suspicious_patterns['ip']:
                    if re.match(pattern, log['ip']):
                        enriched_log['is_suspicious'] = True
                        enriched_log['anomaly_reasons'].append('internal_ip_activity')
                        anomalies_detected += 1
                        break

            # Check for failed login attempts
            if log['user'] and log['user'] != 'anonymous':
                if failed_attempts[log['user']] >= self.anomaly_thresholds['failed_login_attempts']:
                    enriched_log['is_suspicious'] = True
                    reason = f"multiple_failed_attempts_{failed_attempts[log['user']]}"
                    if reason not in enriched_log['anomaly_reasons']:
                        enriched_log['anomaly_reasons'].append(reason)
                        anomalies_detected += 1

            # Check for suspicious status codes
            if log['status'] and log['status'] in ['403', '401', '500']:
                enriched_log['is_suspicious'] = True
                enriched_log['anomaly_reasons'].append(f'error_status_{log["status"]}')
                anomalies_detected += 1

            # Add severity score (0-100)
            severity_score = 0
            if enriched_log['severity'] == 'critical':
                severity_score = 100
            elif enriched_log['severity'] == 'high':
                severity_score = 75
            elif enriched_log['severity'] == 'medium':
                severity_score = 50
            elif enriched_log['severity'] == 'low':
                severity_score = 25

            if enriched_log['is_suspicious']:
                severity_score += 15

            enriched_log['severity_score'] = min(severity_score, 100)

            # Add processing timestamp
            enriched_log['processed_at'] = datetime.now().isoformat()

            enriched.append(enriched_log)

        self.enriched_logs = enriched
        self.metrics['enriched_count'] = len(enriched)
        self.metrics['anomalies_detected'] = anomalies_detected

        print(f"✓ Transformed and enriched {len(enriched)} log entries")
        print(f"⚠ Anomalies detected: {anomalies_detected}")

        # Show sample of enriched data
        if enriched:
            print("\n📋 Enriched Logs Preview (first 3):")
            for i, log in enumerate(enriched[:3], 1):
                preview = {
                    'timestamp': log['timestamp'],
                    'source': log['source'],
                    'severity': log['severity'],
                    'tags': log['tags'],
                    'suspicious': log['is_suspicious']
                }
                print(f"  {i}. {json.dumps(preview, default=str)}")

        return enriched

    def output_data(self, logs: List[Dict[str, Any]], export_json: bool = True) -> None:
        """
        Output processed data to terminal and optionally export to JSON file.

        Args:
            logs: List of enriched log dictionaries
            export_json: Whether to export to JSON file
        """
        print("\n[STAGE 5] DATA OUTPUT")
        print("-" * 50)

        if not logs:
            print("⚠ No data to output")
            return

        # Display summary statistics
        print("\n📊 Pipeline Summary Statistics:")
        print(f"  • Total logs processed: {len(logs)}")
        print(f"  • Unique sources: {len(set(l['source'] for l in logs))}")
        print(f"  • Unique IPs: {len(set(l['ip'] for l in logs if l['ip'] != '0.0.0.0'))}")
        print(f"  • Unique users: {len(set(l['user'] for l in logs if l['user'] != 'anonymous'))}")

        # Severity distribution
        severity_dist = Counter(l['severity'] for l in logs)
        print("\n📈 Severity Distribution:")
        for severity, count in sorted(severity_dist.items()):
            bar_length = int((count / len(logs)) * 40)
            bar = '█' * bar_length
            print(f"  {severity:8s}: {count:3d} {bar}")

        # Event type distribution
        event_dist = Counter(l['event_type'] for l in logs)
        print("\n📈 Event Type Distribution:")
        for event_type, count in sorted(event_dist.items()):
            print(f"  • {event_type}: {count}")

        # Suspicious activity summary
        suspicious_count = sum(1 for l in logs if l['is_suspicious'])
        print(f"\n🚨 Suspicious Activity: {suspicious_count} events flagged")

        if suspicious_count > 0:
            print("  Anomaly reasons:")
            reasons = Counter()
            for log in logs:
                if log['is_suspicious']:
                    for reason in log['anomaly_reasons']:
                        reasons[reason] += 1

            for reason, count in reasons.most_common(5):
                print(f"    - {reason}: {count}")

        # Display final dataset sample
        print("\n📋 Final Dataset Sample (first 5 entries):")
        for i, log in enumerate(logs[:5], 1):
            print(f"\n  Entry {i}:")
            print(f"    Timestamp: {log['timestamp']}")
            print(f"    Source: {log['source']}")
            print(f"    Event Type: {log['event_type']}")
            print(f"    User: {log['user']}")
            print(f"    IP: {log['ip']}")
            print(f"    Status: {log['status']}")
            print(f"    Severity: {log['severity']} (Score: {log['severity_score']})")
            print(f"    Tags: {', '.join(log['tags'])}")
            print(f"    Suspicious: {'Yes' if log['is_suspicious'] else 'No'}")
            if log['anomaly_reasons']:
                print(f"    Reasons: {', '.join(log['anomaly_reasons'])}")

        # Export to JSON if requested
        if export_json:
            output_file = "security_logs_output.json"
            try:
                # Prepare data for JSON export (remove datetime objects)
                json_logs = []
                for log in logs:
                    json_log = log.copy()
                    if 'timestamp_dt' in json_log:
                        del json_log['timestamp_dt']
                    json_logs.append(json_log)

                output_data = {
                    'pipeline_metrics': self.metrics,
                    'summary': {
                        'total_logs': len(logs),
                        'suspicious_events': suspicious_count,
                        'severity_distribution': dict(severity_dist),
                        'event_type_distribution': dict(event_dist)
                    },
                    'logs': json_logs
                }

                with open(output_file, 'w') as f:
                    json.dump(output_data, f, indent=2, default=str)

                print(f"\n✓ Data exported to '{output_file}'")
            except Exception as e:
                print(f"\n✗ Failed to export JSON: {e}")

    def run_full_pipeline(self) -> None:
        """
        Execute the complete data pipeline from ingestion to output.
        """
        print("\n" + "=" * 60)
        print("SECURITY LOG DATA PIPELINE - FULL EXECUTION")
        print("=" * 60)

        start_time = datetime.now()

        # Stage 1: Ingestion
        self.ingest_data(use_sample=True)

        # Stage 2: Cleaning
        self.clean_data(self.raw_logs)

        # Stage 3: Normalization
        self.normalize_data(self.cleaned_logs)

        # Stage 4: Transformation
        self.transform_data(self.normalized_logs)

        # Stage 5: Output
        self.output_data(self.enriched_logs, export_json=True)

        # Calculate total processing time
        end_time = datetime.now()
        self.metrics['processing_time'] = (end_time - start_time).total_seconds()

        print("\n" + "=" * 60)
        print(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
        print(f"⏱ Processing Time: {self.metrics['processing_time']:.3f} seconds")
        print("=" * 60)

    def view_stage(self, stage: str) -> None:
        """
        View a specific pipeline stage output.

        Args:
            stage: Stage name ('raw', 'cleaned', 'normalized', 'enriched')
        """
        stage_map = {
            'raw': ('Raw Logs', self.raw_logs),
            'cleaned': ('Cleaned Logs', self.cleaned_logs),
            'normalized': ('Normalized Logs', self.normalized_logs),
            'enriched': ('Enriched Logs', self.enriched_logs)
        }

        if stage not in stage_map:
            print(f"✗ Invalid stage: {stage}")
            return

        title, data = stage_map[stage]

        print(f"\n{'=' * 60}")
        print(f"VIEWING STAGE: {title.upper()}")
        print(f"{'=' * 60}")

        if not data:
            print(f"⚠ No data available for {title}. Run pipeline first.")
            return

        print(f"\n📊 Count: {len(data)} entries\n")

        if stage == 'raw':
            for i, log in enumerate(data, 1):
                print(f"{i:3d}. {log}")
                if i >= 10:
                    print(f"    ... and {len(data) - 10} more entries")
                    break
        else:
            for i, log in enumerate(data[:5], 1):
                print(f"\n--- Entry {i} ---")
                for key, value in log.items():
                    if key not in ['raw_message', 'message'] or i <= 2:
                        print(f"  {key}: {value}")

            if len(data) > 5:
                print(f"\n... and {len(data) - 5} more entries")


def display_menu() -> None:
    """Display the CLI menu options."""
    print("\n" + "=" * 60)
    print("SECURITY LOG DATA PIPELINE - MAIN MENU")
    print("=" * 60)
    print("1. Run Full Pipeline")
    print("2. View Raw Logs")
    print("3. View Cleaned Logs")
    print("4. View Normalized Logs")
    print("5. View Enriched Logs")
    print("6. View Pipeline Metrics")
    print("7. Export to JSON")
    print("8. Exit")
    print("-" * 60)


def main():
    """
    Main entry point with interactive CLI menu.
    """
    pipeline = SecurityLogPipeline()

    print("\n🔒 MINI DATA PIPELINE FOR SECURITY LOG PROCESSING")
    print("A complete ETL pipeline with anomaly detection")

    while True:
        display_menu()

        try:
            choice = input("\nEnter your choice (1-8): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting pipeline. Goodbye!")
            sys.exit(0)

        if choice == '1':
            pipeline.run_full_pipeline()

        elif choice == '2':
            if not pipeline.raw_logs:
                print("\n⚠ No raw logs available. Run pipeline first or choose option 1.")
            else:
                pipeline.view_stage('raw')

        elif choice == '3':
            if not pipeline.cleaned_logs:
                print("\n⚠ No cleaned logs available. Run pipeline first.")
            else:
                pipeline.view_stage('cleaned')

        elif choice == '4':
            if not pipeline.normalized_logs:
                print("\n⚠ No normalized logs available. Run pipeline first.")
            else:
                pipeline.view_stage('normalized')

        elif choice == '5':
            if not pipeline.enriched_logs:
                print("\n⚠ No enriched logs available. Run pipeline first.")
            else:
                pipeline.view_stage('enriched')

        elif choice == '6':
            print("\n" + "=" * 60)
            print("PIPELINE METRICS")
            print("=" * 60)
            if not pipeline.metrics:
                print("No metrics available. Run pipeline first.")
            else:
                for key, value in pipeline.metrics.items():
                    print(f"  • {key.replace('_', ' ').title()}: {value}")

        elif choice == '7':
            if not pipeline.enriched_logs:
                print("\n⚠ No enriched logs available. Run pipeline first.")
            else:
                pipeline.output_data(pipeline.enriched_logs, export_json=True)

        elif choice == '8':
            print("\nExiting pipeline. Goodbye!")
            sys.exit(0)

        else:
            print("\n✗ Invalid choice. Please enter a number between 1 and 8.")

        # Pause for readability
        if choice in ['1', '2', '3', '4', '5', '6', '7']:
            try:
                input("\nPress Enter to continue...")
            except (KeyboardInterrupt, EOFError):
                print("\n\nExiting pipeline. Goodbye!")
                sys.exit(0)


if __name__ == "__main__":
    # Handle direct script execution
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)