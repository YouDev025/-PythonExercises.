import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import ipaddress


class RiskLevel(Enum):
    """Enumeration for configuration risk levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ConfigType(Enum):
    """Enumeration for configuration item types."""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    IP_ADDRESS = "ip_address"
    PORT = "port"
    FILE_PATH = "file_path"
    REGEX = "regex"
    LIST = "list"


class ConfigurationItem:
    """Represents a single configuration item."""

    def __init__(self, config_name: str, value: Any, config_type: ConfigType = ConfigType.STRING,
                 description: str = "", category: str = "general"):
        """
        Initialize a configuration item.

        Args:
            config_name: Name of the configuration
            value: Current value of the configuration
            config_type: Type of configuration value
            description: Description of what this configuration does
            category: Category (security, performance, logging, etc.)
        """
        self.config_name = self._validate_name(config_name)
        self.value = value
        self.config_type = self._validate_type(config_type)
        self.description = description
        self.category = category.lower()
        self.recommended_value = None
        self.risk_level = RiskLevel.INFO
        self.is_compliant = None
        self.scan_timestamp = None
        self.violation_reason = None

    def _validate_name(self, name: str) -> str:
        """Validate configuration name."""
        if not name or not isinstance(name, str):
            raise ValueError("Configuration name must be a non-empty string")

        # Config name should be alphanumeric with underscores/dots
        if not re.match(r'^[a-zA-Z0-9_.-]+$', name):
            print(f"Warning: '{name}' contains unusual characters")

        return name

    def _validate_type(self, config_type: ConfigType) -> ConfigType:
        """Validate configuration type."""
        if not isinstance(config_type, ConfigType):
            raise ValueError("Config type must be a ConfigType enum value")
        return config_type

    def set_recommended_value(self, value: Any, risk_level: RiskLevel = RiskLevel.MEDIUM) -> None:
        """Set the recommended secure value for this configuration."""
        self.recommended_value = value
        self.risk_level = risk_level

    def validate_value_type(self) -> bool:
        """Validate that the current value matches the expected type."""
        try:
            if self.config_type == ConfigType.INTEGER:
                return isinstance(self.value, int) or str(self.value).isdigit()
            elif self.config_type == ConfigType.BOOLEAN:
                return isinstance(self.value, bool) or str(self.value).lower() in ['true', 'false', 'yes', 'no', '1',
                                                                                   '0']
            elif self.config_type == ConfigType.IP_ADDRESS:
                ipaddress.ip_address(str(self.value))
                return True
            elif self.config_type == ConfigType.PORT:
                port = int(self.value)
                return 1 <= port <= 65535
            elif self.config_type == ConfigType.FILE_PATH:
                # Basic path validation
                return isinstance(self.value, str) and len(self.value) > 0
            elif self.config_type == ConfigType.REGEX:
                re.compile(str(self.value))
                return True
            elif self.config_type == ConfigType.LIST:
                return isinstance(self.value, (list, tuple, set))
            else:  # STRING
                return isinstance(self.value, str)
        except:
            return False

    def to_dict(self) -> Dict:
        """Convert configuration item to dictionary."""
        return {
            'config_name': self.config_name,
            'value': str(self.value),
            'config_type': self.config_type.value,
            'description': self.description,
            'category': self.category,
            'recommended_value': str(self.recommended_value) if self.recommended_value is not None else None,
            'risk_level': self.risk_level.value,
            'is_compliant': self.is_compliant,
            'scan_timestamp': self.scan_timestamp.isoformat() if self.scan_timestamp else None,
            'violation_reason': self.violation_reason
        }

    def __str__(self) -> str:
        """String representation of configuration item."""
        status = "✅ COMPLIANT" if self.is_compliant else "❌ NON-COMPLIANT" if self.is_compliant is not None else "⏳ NOT SCANNED"
        risk_icon = {
            RiskLevel.CRITICAL: "🔴",
            RiskLevel.HIGH: "🟠",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.LOW: "🟢",
            RiskLevel.INFO: "🔵"
        }.get(self.risk_level, "⚪")

        return f"{status} {risk_icon} {self.config_name}: {self.value} (expected: {self.recommended_value})"


class ConfigurationRule:
    """Defines secure configuration standards and validation conditions."""

    def __init__(self, name: str, description: str, risk_level: RiskLevel = RiskLevel.MEDIUM):
        """
        Initialize a configuration rule.

        Args:
            name: Rule name
            description: Rule description
            risk_level: Risk level if rule is violated
        """
        self.name = name
        self.description = description
        self.risk_level = risk_level
        self.conditions = []  # List of validation functions
        self.target_categories = []  # Categories this rule applies to
        self.target_configs = []  # Specific config names this rule applies to
        self.enabled = True
        self.rule_id = f"RULE-{hash(name) % 10000:04d}"

    def add_condition(self, condition_func: Callable[[ConfigurationItem], bool],
                      failure_message: str) -> None:
        """
        Add a validation condition to the rule.

        Args:
            condition_func: Function that takes a ConfigItem and returns bool
            failure_message: Message to display if condition fails
        """
        self.conditions.append({
            'func': condition_func,
            'message': failure_message
        })

    def add_value_match_condition(self, expected_value: Any, message: str = None) -> None:
        """Add condition to match exact value."""

        def match_value(item: ConfigurationItem) -> bool:
            return str(item.value) == str(expected_value)

        msg = message or f"Value should be '{expected_value}'"
        self.add_condition(match_value, msg)

    def add_regex_match_condition(self, pattern: str, message: str = None) -> None:
        """Add condition to match regex pattern."""
        compiled = re.compile(pattern)

        def match_regex(item: ConfigurationItem) -> bool:
            return bool(compiled.match(str(item.value)))

        msg = message or f"Value should match pattern '{pattern}'"
        self.add_condition(match_regex, msg)

    def add_range_condition(self, min_val: float = None, max_val: float = None,
                            message: str = None) -> None:
        """Add condition for numeric range validation."""

        def check_range(item: ConfigurationItem) -> bool:
            try:
                val = float(item.value)
                if min_val is not None and val < min_val:
                    return False
                if max_val is not None and val > max_val:
                    return False
                return True
            except:
                return False

        range_str = []
        if min_val is not None:
            range_str.append(f">= {min_val}")
        if max_val is not None:
            range_str.append(f"<= {max_val}")

        msg = message or f"Value should be within {' and '.join(range_str)}"
        self.add_condition(check_range, msg)

    def add_in_list_condition(self, allowed_values: List[Any], message: str = None) -> None:
        """Add condition to check if value is in allowed list."""
        allowed_str = [str(v) for v in allowed_values]

        def in_list(item: ConfigurationItem) -> bool:
            return str(item.value) in allowed_str

        msg = message or f"Value should be one of: {', '.join(allowed_str)}"
        self.add_condition(in_list, msg)

    def add_complexity_condition(self, min_length: int = 8, require_upper: bool = True,
                                 require_lower: bool = True, require_digit: bool = True,
                                 require_special: bool = True, message: str = None) -> None:
        """Add condition for password/complexity validation."""

        def check_complexity(item: ConfigurationItem) -> bool:
            val = str(item.value)

            if len(val) < min_length:
                return False
            if require_upper and not re.search(r'[A-Z]', val):
                return False
            if require_lower and not re.search(r'[a-z]', val):
                return False
            if require_digit and not re.search(r'\d', val):
                return False
            if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', val):
                return False
            return True

        msg = message or f"Value must meet complexity requirements (min length: {min_length})"
        self.add_condition(check_complexity, msg)

    def applies_to(self, item: ConfigurationItem) -> bool:
        """Check if this rule applies to a configuration item."""
        if not self.enabled:
            return False

        # Check specific config names
        if self.target_configs and item.config_name in self.target_configs:
            return True

        # Check categories
        if self.target_categories and item.category in self.target_categories:
            return True

        # If no targets specified, apply to all
        return not (self.target_configs or self.target_categories)

    def validate(self, item: ConfigurationItem) -> tuple[bool, List[str]]:
        """
        Validate a configuration item against this rule.

        Returns:
            Tuple of (is_compliant, list of violation messages)
        """
        violations = []

        for condition in self.conditions:
            if not condition['func'](item):
                violations.append(condition['message'])

        return len(violations) == 0, violations

    def to_dict(self) -> Dict:
        """Convert rule to dictionary."""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'risk_level': self.risk_level.value,
            'enabled': self.enabled,
            'target_categories': self.target_categories,
            'target_configs': self.target_configs,
            'condition_count': len(self.conditions)
        }


class ConfigurationScanner:
    """Responsible for analyzing configuration items against security rules."""

    def __init__(self):
        """Initialize the configuration scanner."""
        self.rules: List[ConfigurationRule] = []
        self.scan_history = []
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize scanner with common security configuration rules."""

        # Password policy rules
        pwd_rule = ConfigurationRule(
            "Password Complexity",
            "Ensure passwords meet complexity requirements",
            RiskLevel.CRITICAL
        )
        pwd_rule.target_categories = ['password', 'authentication', 'security']
        pwd_rule.target_configs = ['password', 'admin_password', 'db_password', 'api_key']
        pwd_rule.add_complexity_condition(
            min_length=12,
            require_upper=True,
            require_lower=True,
            require_digit=True,
            require_special=True
        )
        self.add_rule(pwd_rule)

        # Port security rule
        port_rule = ConfigurationRule(
            "Secure Port Configuration",
            "Ensure services are not running on insecure ports",
            RiskLevel.HIGH
        )
        port_rule.target_categories = ['network', 'port']
        port_rule.target_configs = ['port', 'listen_port', 'service_port']
        port_rule.add_in_list_condition(
            [443, 8443, 22, 3306, 5432],  # Common secure ports
            "Port should be a standard secure port"
        )
        port_rule.add_range_condition(min_val=1024, max_val=49151, message="Port should be in registered range")
        self.add_rule(port_rule)

        # Debug mode rule
        debug_rule = ConfigurationRule(
            "Debug Mode Disabled",
            "Debug mode should be disabled in production",
            RiskLevel.HIGH
        )
        debug_rule.target_configs = ['debug', 'debug_mode', 'development_mode']
        debug_rule.add_value_match_condition(False, "Debug mode must be disabled in production")
        self.add_rule(debug_rule)

        # TLS/SSL version rule
        tls_rule = ConfigurationRule(
            "Secure TLS Version",
            "Use secure TLS versions only",
            RiskLevel.CRITICAL
        )
        tls_rule.target_configs = ['tls_version', 'ssl_version', 'min_tls']
        tls_rule.add_in_list_condition(
            ['TLSv1.2', 'TLSv1.3'],
            "TLS version should be 1.2 or higher"
        )
        self.add_rule(tls_rule)

        # File permissions rule
        perm_rule = ConfigurationRule(
            "Secure File Permissions",
            "Sensitive files should have restricted permissions",
            RiskLevel.HIGH
        )
        perm_rule.target_configs = ['file_permissions', 'umask', 'config_file_mode']
        perm_rule.add_range_condition(max_val=644, message="File permissions should be 644 or stricter")
        self.add_rule(perm_rule)

        # Session timeout rule
        session_rule = ConfigurationRule(
            "Session Timeout",
            "Session timeout should be set appropriately",
            RiskLevel.MEDIUM
        )
        session_rule.target_configs = ['session_timeout', 'session_lifetime', 'idle_timeout']
        session_rule.add_range_condition(min_val=300, max_val=3600,
                                         message="Session timeout should be between 5 minutes and 1 hour")
        self.add_rule(session_rule)

        # IP binding rule
        ip_rule = ConfigurationRule(
            "Secure IP Binding",
            "Services should bind to specific interfaces",
            RiskLevel.HIGH
        )
        ip_rule.target_configs = ['bind_address', 'listen_address', 'host']
        ip_rule.add_in_list_condition(
            ['127.0.0.1', 'localhost', '::1'],
            "Services should bind to localhost unless necessary"
        )
        self.add_rule(ip_rule)

        # CORS policy rule
        cors_rule = ConfigurationRule(
            "CORS Policy",
            "CORS should be properly configured",
            RiskLevel.MEDIUM
        )
        cors_rule.target_configs = ['cors_origin', 'allowed_origins', 'cors_allowed_origins']

        def check_cors(item: ConfigurationItem) -> bool:
            value = str(item.value).lower()
            return value != '*' and 'null' not in value

        cors_rule.add_condition(check_cors, "CORS should not allow '*' or 'null' origins")
        self.add_rule(cors_rule)

        # Encryption algorithm rule
        crypto_rule = ConfigurationRule(
            "Strong Encryption",
            "Use strong encryption algorithms",
            RiskLevel.CRITICAL
        )
        crypto_rule.target_configs = ['encryption_algorithm', 'cipher', 'algorithm']
        crypto_rule.add_in_list_condition(
            ['AES-256', 'AES-128', 'ChaCha20', 'RSA-2048', 'RSA-4096'],
            "Use strong, modern encryption algorithms"
        )
        self.add_rule(crypto_rule)

        # Logging level rule
        log_rule = ConfigurationRule(
            "Appropriate Logging",
            "Logging level should be set appropriately",
            RiskLevel.LOW
        )
        log_rule.target_configs = ['log_level', 'logging_level', 'loglevel']
        log_rule.add_in_list_condition(
            ['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            "Log level should not be DEBUG in production"
        )
        self.add_rule(log_rule)

    def add_rule(self, rule: ConfigurationRule) -> None:
        """Add a configuration rule to the scanner."""
        self.rules.append(rule)

    def scan_item(self, item: ConfigurationItem) -> ConfigurationItem:
        """
        Scan a single configuration item against all applicable rules.

        Args:
            item: ConfigurationItem to scan

        Returns:
            Updated ConfigurationItem with scan results
        """
        item.scan_timestamp = datetime.now()

        # Validate value type first
        if not item.validate_value_type():
            item.is_compliant = False
            item.violation_reason = f"Value type mismatch: expected {item.config_type.value}"
            return item

        all_violations = []

        for rule in self.rules:
            if rule.applies_to(item):
                is_compliant, violations = rule.validate(item)
                if not is_compliant:
                    all_violations.extend(violations)

        item.is_compliant = len(all_violations) == 0
        item.violation_reason = "; ".join(all_violations) if all_violations else None

        # Log scan
        self.scan_history.append({
            'timestamp': item.scan_timestamp.isoformat(),
            'config_name': item.config_name,
            'compliant': item.is_compliant
        })

        return item

    def scan_items(self, items: List[ConfigurationItem]) -> List[ConfigurationItem]:
        """Scan multiple configuration items."""
        return [self.scan_item(item) for item in items]

    def get_statistics(self) -> Dict:
        """Get scanner statistics."""
        total_scans = len(self.scan_history)
        if total_scans == 0:
            return {'total_scans': 0}

        compliant_scans = sum(1 for scan in self.scan_history if scan['compliant'])

        return {
            'total_scans': total_scans,
            'compliant_scans': compliant_scans,
            'non_compliant_scans': total_scans - compliant_scans,
            'compliance_rate': (compliant_scans / total_scans * 100) if total_scans > 0 else 0,
            'last_scan': self.scan_history[-1]['timestamp'] if self.scan_history else None
        }


class ScanManager:
    """Manages configuration data, runs scans, and generates reports."""

    def __init__(self):
        """Initialize the scan manager."""
        self.config_items: Dict[str, ConfigurationItem] = {}  # name -> ConfigItem
        self.scanner = None
        self.scan_results = []
        self.categories = set()

    def set_scanner(self, scanner: ConfigurationScanner) -> None:
        """Set the configuration scanner instance."""
        self.scanner = scanner

    def add_configuration(self, name: str, value: Any, config_type: ConfigType = ConfigType.STRING,
                          description: str = "", category: str = "general",
                          recommended_value: Any = None, risk_level: RiskLevel = RiskLevel.MEDIUM) -> Optional[
        ConfigurationItem]:
        """
        Add a configuration item.

        Args:
            name: Configuration name
            value: Current value
            config_type: Type of configuration
            description: Description
            category: Category
            recommended_value: Recommended secure value
            risk_level: Risk level if misconfigured

        Returns:
            ConfigurationItem if successful, None otherwise
        """
        try:
            # Validate input
            if name in self.config_items:
                print(f"⚠️  Configuration '{name}' already exists. Overwriting...")

            item = ConfigurationItem(name, value, config_type, description, category)

            if recommended_value is not None:
                item.set_recommended_value(recommended_value, risk_level)

            self.config_items[name] = item
            self.categories.add(category)

            print(f"✅ Added configuration: {name}")
            return item

        except ValueError as e:
            print(f"❌ Error adding configuration: {e}")
            return None

    def add_configuration_interactive(self) -> None:
        """Interactive method to add a configuration."""
        print("\n--- Add New Configuration ---")

        name = input("Configuration name: ").strip()
        if not name:
            print("Configuration name cannot be empty")
            return

        print("\nConfiguration type:")
        for i, ct in enumerate(ConfigType, 1):
            print(f"{i}. {ct.value}")

        type_choice = input("Select type (1-8, default: 1): ").strip()
        type_map = {str(i): ct for i, ct in enumerate(ConfigType, 1)}
        config_type = type_map.get(type_choice, ConfigType.STRING)

        value = input(f"Current value: ").strip()

        # Convert value based on type
        try:
            if config_type == ConfigType.INTEGER:
                value = int(value)
            elif config_type == ConfigType.BOOLEAN:
                value = value.lower() in ['true', 'yes', '1', 'on']
            elif config_type == ConfigType.PORT:
                value = int(value)
            elif config_type == ConfigType.LIST:
                value = [v.strip() for v in value.split(',')]
        except:
            print(f"Warning: Could not convert value to {config_type.value}")

        description = input("Description (optional): ").strip()
        category = input("Category (default: general): ").strip() or "general"

        add_recommended = input("Add recommended value? (y/n): ").lower() == 'y'
        recommended_value = None
        risk_level = RiskLevel.MEDIUM

        if add_recommended:
            recommended_value = input("Recommended secure value: ").strip()

            print("\nRisk level if misconfigured:")
            for i, rl in enumerate(RiskLevel, 1):
                print(f"{i}. {rl.value}")

            risk_choice = input("Select risk level (1-5, default: 3): ").strip()
            risk_map = {str(i): rl for i, rl in enumerate(RiskLevel, 1)}
            risk_level = risk_map.get(risk_choice, RiskLevel.MEDIUM)

        self.add_configuration(name, value, config_type, description, category, recommended_value, risk_level)

    def run_scan(self) -> Dict[str, bool]:
        """
        Run configuration scan on all items.

        Returns:
            Dictionary mapping config names to compliance status
        """
        if not self.scanner:
            print("❌ Scanner not initialized!")
            return {}

        if not self.config_items:
            print("❌ No configurations added for scanning!")
            return {}

        print(f"\n🔍 Running configuration scan on {len(self.config_items)} items...")
        print("-" * 50)

        items = list(self.config_items.values())
        scanned_items = self.scanner.scan_items(items)

        # Update stored items
        results = {}
        for item in scanned_items:
            self.config_items[item.config_name] = item
            results[item.config_name] = item.is_compliant

            # Display result
            status = "✅" if item.is_compliant else "❌"
            print(f"{status} {item.config_name}: {item.value}")
            if not item.is_compliant and item.violation_reason:
                print(f"   ↳ {item.violation_reason}")

        # Store scan results
        self.scan_results.append({
            'timestamp': datetime.now().isoformat(),
            'total_items': len(scanned_items),
            'compliant': sum(1 for i in scanned_items if i.is_compliant),
            'non_compliant': sum(1 for i in scanned_items if not i.is_compliant)
        })

        print("-" * 50)
        print(f"✅ Scan complete! Found {results.values()} issues.")

        return results

    def get_non_compliant_items(self, risk_level: Optional[RiskLevel] = None) -> List[ConfigurationItem]:
        """Get all non-compliant items, optionally filtered by risk level."""
        non_compliant = []

        for item in self.config_items.values():
            if item.is_compliant is False:  # Only include scanned non-compliant items
                if risk_level is None or item.risk_level == risk_level:
                    non_compliant.append(item)

        return non_compliant

    def display_issues(self, risk_level: Optional[RiskLevel] = None) -> None:
        """Display detected configuration issues."""
        issues = self.get_non_compliant_items(risk_level)

        if not issues:
            print("\n✨ No configuration issues detected!")
            return

        print("\n" + "=" * 70)
        print("🔴 DETECTED CONFIGURATION ISSUES")
        print("=" * 70)

        # Group by risk level
        by_risk = {}
        for issue in issues:
            by_risk.setdefault(issue.risk_level, []).append(issue)

        # Display in order of criticality
        for risk in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.INFO]:
            if risk in by_risk:
                risk_icon = {
                    RiskLevel.CRITICAL: "🔴 CRITICAL",
                    RiskLevel.HIGH: "🟠 HIGH",
                    RiskLevel.MEDIUM: "🟡 MEDIUM",
                    RiskLevel.LOW: "🟢 LOW",
                    RiskLevel.INFO: "🔵 INFO"
                }.get(risk, "⚪")

                print(f"\n{risk_icon} RISK ISSUES:")

                for issue in by_risk[risk]:
                    print(f"\n  📌 {issue.config_name}")
                    print(f"     Current: {issue.value}")
                    print(f"     Recommended: {issue.recommended_value}")
                    print(f"     Category: {issue.category}")
                    if issue.violation_reason:
                        print(f"     Reason: {issue.violation_reason}")

    def display_summary(self) -> None:
        """Display summary of secure and insecure configurations."""
        if not self.config_items:
            print("No configurations to display.")
            return

        total = len(self.config_items)
        scanned = sum(1 for item in self.config_items.values() if item.is_compliant is not None)
        compliant = sum(1 for item in self.config_items.values() if item.is_compliant)
        non_compliant = sum(1 for item in self.config_items.values() if item.is_compliant is False)
        not_scanned = total - scanned

        print("\n" + "=" * 70)
        print("📊 CONFIGURATION SCAN SUMMARY")
        print("=" * 70)
        print(f"Total Configurations: {total}")
        print(f"Scanned: {scanned}")
        print(f"✅ Compliant: {compliant}")
        print(f"❌ Non-Compliant: {non_compliant}")
        print(f"⏳ Not Scanned: {not_scanned}")

        if non_compliant > 0:
            print("\n⚠️  Issues by Risk Level:")
            for risk in RiskLevel:
                count = len(self.get_non_compliant_items(risk))
                if count > 0:
                    icon = {
                        RiskLevel.CRITICAL: "🔴",
                        RiskLevel.HIGH: "🟠",
                        RiskLevel.MEDIUM: "🟡",
                        RiskLevel.LOW: "🟢",
                        RiskLevel.INFO: "🔵"
                    }.get(risk, "⚪")
                    print(f"  {icon} {risk.value}: {count}")

        # Category breakdown
        if self.categories:
            print("\n📁 By Category:")
            for category in sorted(self.categories):
                cat_items = [i for i in self.config_items.values() if i.category == category]
                cat_compliant = sum(1 for i in cat_items if i.is_compliant)
                cat_total = len(cat_items)
                if cat_total > 0:
                    percentage = (cat_compliant / cat_total * 100) if cat_total > 0 else 0
                    print(f"  {category}: {cat_compliant}/{cat_total} compliant ({percentage:.1f}%)")

    def generate_report(self) -> Dict:
        """Generate comprehensive report."""
        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_configurations': len(self.config_items),
            'scanned_configurations': sum(1 for i in self.config_items.values() if i.is_compliant is not None),
            'compliant': sum(1 for i in self.config_items.values() if i.is_compliant),
            'non_compliant': sum(1 for i in self.config_items.values() if i.is_compliant is False),
            'categories': list(self.categories),
            'risk_breakdown': {},
            'issues': [],
            'scan_history': self.scan_results
        }

        # Risk level breakdown
        for risk in RiskLevel:
            count = len(self.get_non_compliant_items(risk))
            summary['risk_breakdown'][risk.value] = count

            # Add critical issues to issues list
            if count > 0 and risk in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                for item in self.get_non_compliant_items(risk):
                    summary['issues'].append({
                        'config': item.config_name,
                        'current_value': str(item.value),
                        'recommended': str(item.recommended_value),
                        'risk': risk.value,
                        'reason': item.violation_reason
                    })

        # Add scanner stats
        if self.scanner:
            summary['scanner_stats'] = self.scanner.get_statistics()

        return summary

    def display_report(self) -> None:
        """Display formatted report."""
        report = self.generate_report()

        print("\n" + "=" * 70)
        print("📋 CONFIGURATION SCAN REPORT")
        print("=" * 70)
        print(f"Generated: {report['generated_at'][:16]}")
        print(f"Total Configurations: {report['total_configurations']}")
        print(f"Scanned: {report['scanned_configurations']}")
        print(f"✅ Compliant: {report['compliant']}")
        print(f"❌ Non-Compliant: {report['non_compliant']}")

        if report['risk_breakdown']:
            print("\n⚠️  Risk Breakdown:")
            for risk, count in report['risk_breakdown'].items():
                if count > 0:
                    icon = {
                        'CRITICAL': '🔴',
                        'HIGH': '🟠',
                        'MEDIUM': '🟡',
                        'LOW': '🟢',
                        'INFO': '🔵'
                    }.get(risk, '⚪')
                    print(f"  {icon} {risk}: {count}")

        if report['issues']:
            print("\n🔴 Top Priority Issues:")
            for issue in report['issues'][:5]:  # Top 5
                print(f"\n  • {issue['config']}")
                print(f"    Current: {issue['current_value']}")
                print(f"    Recommended: {issue['recommended']}")
                print(f"    Risk: {issue['risk']}")

    def export_report(self, filename: str = "config_scan_report.json") -> None:
        """Export report to JSON file."""
        report = self.generate_report()

        # Add all configuration details
        report['configurations'] = [item.to_dict() for item in self.config_items.values()]

        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"✅ Report exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting report: {e}")

    def get_compliance_by_category(self) -> Dict[str, float]:
        """Get compliance percentage by category."""
        category_stats = {}

        for category in self.categories:
            items = [i for i in self.config_items.values() if i.category == category and i.is_compliant is not None]
            if items:
                compliant = sum(1 for i in items if i.is_compliant)
                category_stats[category] = (compliant / len(items)) * 100

        return category_stats


def main():
    """Main function to run the configuration scanner system."""

    print("=" * 70)
    print("🔧 CONFIGURATION SCANNER SYSTEM")
    print("=" * 70)
    print("A tool for detecting insecure configuration settings")

    # Initialize the system
    scanner = ConfigurationScanner()
    manager = ScanManager()
    manager.set_scanner(scanner)

    # Add some example configurations
    print("\n📋 Adding example configurations...")

    # Security configurations
    manager.add_configuration(
        "password_policy", "weakpass", ConfigType.STRING,
        "Password complexity requirement", "security",
        "StrongP@ssw0rd!", RiskLevel.CRITICAL
    )

    manager.add_configuration(
        "debug_mode", True, ConfigType.BOOLEAN,
        "Debug mode enabled", "application",
        False, RiskLevel.HIGH
    )

    manager.add_configuration(
        "tls_version", "TLSv1.1", ConfigType.STRING,
        "TLS version", "security",
        "TLSv1.3", RiskLevel.CRITICAL
    )

    manager.add_configuration(
        "session_timeout", 3600, ConfigType.INTEGER,
        "Session timeout in seconds", "application",
        1800, RiskLevel.MEDIUM
    )

    # Network configurations
    manager.add_configuration(
        "listen_port", 80, ConfigType.PORT,
        "Web server port", "network",
        443, RiskLevel.HIGH
    )

    manager.add_configuration(
        "bind_address", "0.0.0.0", ConfigType.IP_ADDRESS,
        "Bind address", "network",
        "127.0.0.1", RiskLevel.MEDIUM
    )

    # Database configurations
    manager.add_configuration(
        "db_password", "admin123", ConfigType.STRING,
        "Database password", "database",
        "SecureP@ssw0rd123!", RiskLevel.CRITICAL
    )

    manager.add_configuration(
        "db_port", 3306, ConfigType.PORT,
        "Database port", "database",
        3306, RiskLevel.LOW
    )

    # Logging configurations
    manager.add_configuration(
        "log_level", "DEBUG", ConfigType.STRING,
        "Logging level", "logging",
        "INFO", RiskLevel.LOW
    )

    manager.add_configuration(
        "audit_logging", True, ConfigType.BOOLEAN,
        "Audit logging enabled", "logging",
        True, RiskLevel.INFO
    )

    # Interactive menu
    while True:
        print("\n" + "=" * 50)
        print("📌 MAIN MENU")
        print("=" * 50)
        print("1. Add new configuration")
        print("2. View all configurations")
        print("3. Run configuration scan")
        print("4. Display detected issues")
        print("5. Show issues by risk level")
        print("6. Display scan summary")
        print("7. Generate detailed report")
        print("8. Export report to JSON")
        print("9. View compliance by category")
        print("10. Add custom security rule")
        print("11. View scanner statistics")
        print("12. Exit")
        print("-" * 50)

        choice = input("Enter your choice (1-12): ").strip()

        try:
            if choice == '1':
                manager.add_configuration_interactive()

            elif choice == '2':
                if not manager.config_items:
                    print("No configurations added.")
                else:
                    print("\n📋 ALL CONFIGURATIONS:")
                    print("-" * 60)
                    for item in manager.config_items.values():
                        print(item)

            elif choice == '3':
                manager.run_scan()

            elif choice == '4':
                manager.display_issues()

            elif choice == '5':
                print("\nFilter by risk level:")
                for i, rl in enumerate(RiskLevel, 1):
                    print(f"{i}. {rl.value}")

                risk_choice = input("Select risk level (1-5): ").strip()
                risk_map = {str(i): rl for i, rl in enumerate(RiskLevel, 1)}
                selected_risk = risk_map.get(risk_choice)

                if selected_risk:
                    manager.display_issues(selected_risk)
                else:
                    print("Invalid choice")

            elif choice == '6':
                manager.display_summary()

            elif choice == '7':
                manager.display_report()

            elif choice == '8':
                filename = input("Enter filename (default: config_scan_report.json): ").strip()
                if not filename:
                    filename = "config_scan_report.json"
                manager.export_report(filename)

            elif choice == '9':
                category_stats = manager.get_compliance_by_category()
                if category_stats:
                    print("\n📊 COMPLIANCE BY CATEGORY:")
                    print("-" * 40)
                    for category, percentage in sorted(category_stats.items()):
                        bar = "█" * int(percentage / 10)
                        print(f"{category:15} {bar:10} {percentage:.1f}%")
                else:
                    print("No category data available")

            elif choice == '10':
                print("\n--- Add Custom Security Rule ---")
                name = input("Rule name: ").strip()
                desc = input("Rule description: ").strip()

                print("\nRisk level:")
                for i, rl in enumerate(RiskLevel, 1):
                    print(f"{i}. {rl.value}")

                risk_choice = input("Select risk level (1-5, default: 3): ").strip()
                risk_map = {str(i): rl for i, rl in enumerate(RiskLevel, 1)}
                risk_level = risk_map.get(risk_choice, RiskLevel.MEDIUM)

                rule = ConfigurationRule(name, desc, risk_level)

                print("\nAdd condition type:")
                print("1. Exact value match")
                print("2. Numeric range")
                print("3. Allowed values list")
                print("4. Regex pattern")
                print("5. Complexity check")
                print("6. Done adding conditions")

                while True:
                    cond_choice = input("\nSelect condition type (1-6): ").strip()

                    if cond_choice == '1':
                        value = input("Expected value: ").strip()
                        rule.add_value_match_condition(value)
                        print("Added exact match condition")

                    elif cond_choice == '2':
                        min_val = input("Minimum value (press Enter to skip): ").strip()
                        max_val = input("Maximum value (press Enter to skip): ").strip()
                        min_val = float(min_val) if min_val else None
                        max_val = float(max_val) if max_val else None
                        rule.add_range_condition(min_val, max_val)
                        print("Added range condition")

                    elif cond_choice == '3':
                        values = input("Allowed values (comma-separated): ").strip().split(',')
                        values = [v.strip() for v in values]
                        rule.add_in_list_condition(values)
                        print("Added allowed values condition")

                    elif cond_choice == '4':
                        pattern = input("Regex pattern: ").strip()
                        rule.add_regex_match_condition(pattern)
                        print("Added regex condition")

                    elif cond_choice == '5':
                        min_len = int(input("Minimum length (default: 8): ") or "8")
                        rule.add_complexity_condition(min_length=min_len)
                        print("Added complexity condition")

                    elif cond_choice == '6':
                        break

                # Add target configs/categories
                targets = input("\nTarget config names (comma-separated, press Enter to skip): ").strip()
                if targets:
                    rule.target_configs = [t.strip() for t in targets.split(',')]

                categories = input("Target categories (comma-separated, press Enter to skip): ").strip()
                if categories:
                    rule.target_categories = [c.strip() for c in categories.split(',')]

                scanner.add_rule(rule)
                print(f"✅ Added custom rule: {name}")

            elif choice == '11':
                stats = scanner.get_statistics()
                print("\n📊 SCANNER STATISTICS:")
                print("-" * 40)
                for key, value in stats.items():
                    if isinstance(value, float):
                        print(f"{key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        print(f"{key.replace('_', ' ').title()}: {value}")

            elif choice == '12':
                print("\n👋 Exiting Configuration Scanner. Stay secure!")
                break

            else:
                print("❌ Invalid choice. Please enter a number between 1 and 12.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
            break
        except ValueError as e:
            print(f"❌ Input error: {e}")
        except Exception as e:
            print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()