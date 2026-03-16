import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import re
import uuid
from enum import Enum


class CertificateStatus(Enum):
    """Enumeration for certificate status."""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    RENEWED = "renewed"


class KeyAlgorithm(Enum):
    """Enumeration for key algorithms."""
    RSA_2048 = "RSA-2048"
    RSA_4096 = "RSA-4096"
    ECDSA_256 = "ECDSA-256"
    ECDSA_384 = "ECDSA-384"
    ED25519 = "ED25519"


class Certificate:
    """Represents a digital certificate."""

    def __init__(self, domain_name: str, issuer: str, validity_days: int = 365,
                 key_algorithm: KeyAlgorithm = KeyAlgorithm.RSA_2048):
        """
        Initialize a new certificate.

        Args:
            domain_name: Domain name for the certificate
            issuer: Certificate authority that issues the certificate
            validity_days: Number of days the certificate is valid
            key_algorithm: Encryption algorithm used
        """
        self.certificate_id = self._generate_certificate_id()
        self.domain_name = self._validate_domain(domain_name)
        self.issuer = issuer
        self.key_algorithm = key_algorithm
        self.issue_date = datetime.now()
        self.expiration_date = self.issue_date + timedelta(days=validity_days)
        self.status = CertificateStatus.VALID
        self.revocation_reason = None
        self.public_key = self._generate_public_key()
        self.signature = None
        self.metadata = {}

    def _generate_certificate_id(self) -> str:
        """Generate a unique certificate ID."""
        return f"CERT-{uuid.uuid4().hex[:8].upper()}-{datetime.now().strftime('%Y%m')}"

    def _validate_domain(self, domain: str) -> str:
        """Validate domain name format."""
        if not domain or not isinstance(domain, str):
            raise ValueError("Domain name must be a non-empty string")

        # Basic domain validation
        domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$|^localhost$|^\*\.'
        if not re.match(domain_pattern, domain) and domain != 'localhost':
            # Allow wildcard domains
            if not domain.startswith('*.'):
                print(f"Warning: '{domain}' may not be a valid domain format")

        return domain.lower()

    def _generate_public_key(self) -> str:
        """Generate a mock public key."""
        # In a real system, this would generate actual cryptographic keys
        key_length = {
            KeyAlgorithm.RSA_2048: 2048,
            KeyAlgorithm.RSA_4096: 4096,
            KeyAlgorithm.ECDSA_256: 256,
            KeyAlgorithm.ECDSA_384: 384,
            KeyAlgorithm.ED25519: 256
        }.get(self.key_algorithm, 2048)

        return f"PUBKEY-{self.key_algorithm.value}-{uuid.uuid4().hex[:16].upper()}"

    def sign(self, ca_private_key: str) -> str:
        """Sign the certificate with CA's private key."""
        # Mock signature generation
        self.signature = f"SIG-{hash(self.certificate_id + self.domain_name + ca_private_key)}"
        return self.signature

    def is_expired(self) -> bool:
        """Check if the certificate is expired."""
        return datetime.now() > self.expiration_date

    def days_until_expiration(self) -> int:
        """Get number of days until expiration."""
        if self.is_expired():
            return -1 * (datetime.now() - self.expiration_date).days
        return (self.expiration_date - datetime.now()).days

    def revoke(self, reason: str) -> None:
        """Revoke the certificate."""
        self.status = CertificateStatus.REVOKED
        self.revocation_reason = reason

    def renew(self, validity_days: int = 365) -> 'Certificate':
        """
        Renew the certificate.

        Returns:
            New certificate with updated dates
        """
        new_cert = Certificate(self.domain_name, self.issuer, validity_days, self.key_algorithm)
        new_cert.metadata['renewed_from'] = self.certificate_id
        self.status = CertificateStatus.RENEWED
        return new_cert

    def to_dict(self) -> Dict:
        """Convert certificate to dictionary for storage/display."""
        return {
            'certificate_id': self.certificate_id,
            'domain_name': self.domain_name,
            'issuer': self.issuer,
            'key_algorithm': self.key_algorithm.value,
            'issue_date': self.issue_date.isoformat(),
            'expiration_date': self.expiration_date.isoformat(),
            'status': self.status.value,
            'revocation_reason': self.revocation_reason,
            'public_key': self.public_key,
            'signature': self.signature,
            'metadata': self.metadata,
            'days_valid': (self.expiration_date - self.issue_date).days
        }

    def __str__(self) -> str:
        """String representation of the certificate."""
        status_icon = {
            CertificateStatus.VALID: "✅",
            CertificateStatus.EXPIRED: "❌",
            CertificateStatus.REVOKED: "🚫",
            CertificateStatus.PENDING: "⏳",
            CertificateStatus.RENEWED: "🔄"
        }.get(self.status, "❓")

        exp_info = f"Expires: {self.expiration_date.strftime('%Y-%m-%d')}"
        if self.status == CertificateStatus.VALID:
            days = self.days_until_expiration()
            exp_info += f" ({days} days remaining)"

        return f"{status_icon} {self.certificate_id}: {self.domain_name} [{self.status.value}] - {exp_info}"


class CertificateAuthority:
    """Represents a Certificate Authority that issues and validates certificates."""

    def __init__(self, name: str):
        """
        Initialize a Certificate Authority.

        Args:
            name: Name of the Certificate Authority
        """
        self.name = name
        self.ca_id = f"CA-{uuid.uuid4().hex[:8].upper()}"
        self.private_key = self._generate_private_key()
        self.public_key = self._generate_public_key()
        self.root_certificate = None
        self.issued_certificates = 0
        self.revoked_certificates = 0
        self.certificate_policies = {
            'max_validity_days': 825,  # Max 2 years + 3 months (RFC 3647)
            'allowed_algorithms': [alg for alg in KeyAlgorithm],
            'require_dcv': True,  # Domain Control Validation
            'revocation_api': True
        }

    def _generate_private_key(self) -> str:
        """Generate a mock private key."""
        return f"PRIVKEY-{uuid.uuid4().hex[:32].upper()}"

    def _generate_public_key(self) -> str:
        """Generate a mock public key."""
        return f"CAPUBKEY-{uuid.uuid4().hex[:24].upper()}"

    def issue_certificate(self, domain_name: str, validity_days: int = 365,
                          key_algorithm: KeyAlgorithm = KeyAlgorithm.RSA_2048,
                          perform_validation: bool = True) -> Optional[Certificate]:
        """
        Issue a new certificate.

        Args:
            domain_name: Domain to issue certificate for
            validity_days: Certificate validity period
            key_algorithm: Key algorithm to use
            perform_validation: Whether to perform domain validation

        Returns:
            Issued certificate or None if validation fails
        """
        try:
            # Validate request
            if validity_days > self.certificate_policies['max_validity_days']:
                raise ValueError(f"Validity period cannot exceed {self.certificate_policies['max_validity_days']} days")

            if key_algorithm not in self.certificate_policies['allowed_algorithms']:
                raise ValueError(f"Key algorithm {key_algorithm.value} not allowed")

            # Perform domain validation if required
            if perform_validation and self.certificate_policies['require_dcv']:
                if not self._validate_domain_control(domain_name):
                    raise ValueError(f"Domain control validation failed for {domain_name}")

            # Create and sign certificate
            cert = Certificate(domain_name, self.name, validity_days, key_algorithm)
            cert.sign(self.private_key)

            # Update statistics
            self.issued_certificates += 1

            print(f"✅ Certificate issued for {domain_name} (valid for {validity_days} days)")
            return cert

        except Exception as e:
            print(f"❌ Failed to issue certificate: {e}")
            return None

    def _validate_domain_control(self, domain_name: str) -> bool:
        """
        Simulate domain control validation.
        In real implementation, this would check DNS records, HTTP challenges, etc.
        """
        # Mock validation - always passes except for certain domains
        blocked_domains = {'malicious.com', 'hacker.net', 'test.local'}

        if domain_name in blocked_domains:
            print(f"⚠️  Domain validation failed: {domain_name} is blocked")
            return False

        # Simulate validation success
        print(f"✓ Domain control validated for {domain_name}")
        return True

    def validate_certificate(self, certificate: Certificate) -> bool:
        """
        Validate a certificate's authenticity and status.

        Returns:
            True if certificate is valid, False otherwise
        """
        # Check signature (mock validation)
        if not certificate.signature:
            print("❌ Certificate is not signed")
            return False

        # Check if issued by this CA
        if certificate.issuer != self.name:
            print(f"❌ Certificate issued by {certificate.issuer}, not {self.name}")
            return False

        # Check expiration
        if certificate.is_expired():
            print(f"❌ Certificate expired on {certificate.expiration_date.strftime('%Y-%m-%d')}")
            return False

        # Check revocation status
        if certificate.status == CertificateStatus.REVOKED:
            reason = certificate.revocation_reason or "Unknown reason"
            print(f"❌ Certificate is revoked: {reason}")
            return False

        return True

    def revoke_certificate(self, certificate: Certificate, reason: str) -> bool:
        """
        Revoke a certificate.

        Returns:
            True if revocation successful
        """
        if certificate.status == CertificateStatus.REVOKED:
            print(f"⚠️  Certificate {certificate.certificate_id} already revoked")
            return False

        certificate.revoke(reason)
        self.revoked_certificates += 1
        print(f"🚫 Certificate {certificate.certificate_id} revoked: {reason}")
        return True

    def get_statistics(self) -> Dict:
        """Get CA statistics."""
        return {
            'ca_name': self.name,
            'ca_id': self.ca_id,
            'issued_certificates': self.issued_certificates,
            'revoked_certificates': self.revoked_certificates,
            'active_certificates': self.issued_certificates - self.revoked_certificates,
            'policies': self.certificate_policies
        }


class CertificateManager:
    """Manages multiple certificates, handles expiration, renewal, and revocation."""

    def __init__(self, ca: CertificateAuthority):
        """
        Initialize the certificate manager.

        Args:
            ca: Certificate Authority instance
        """
        self.ca = ca
        self.certificates: Dict[str, Certificate] = {}  # cert_id -> Certificate
        self.domain_index: Dict[str, List[str]] = {}  # domain -> list of cert_ids
        self.notification_thresholds = [30, 15, 7, 3, 1]  # Days before expiry to notify
        self.renewal_auto_threshold = 30  # Auto-renew when days left < this
        self.audit_log = []

    def create_certificate(self, domain_name: str, validity_days: int = 365,
                           key_algorithm: KeyAlgorithm = KeyAlgorithm.RSA_2048,
                           auto_renew: bool = True) -> Optional[Certificate]:
        """
        Create and issue a new certificate.

        Args:
            domain_name: Domain for the certificate
            validity_days: Validity period
            key_algorithm: Key algorithm
            auto_renew: Whether to enable auto-renewal

        Returns:
            Issued certificate or None if failed
        """
        # Check for existing valid certificate
        existing = self.get_valid_certificate(domain_name)
        if existing:
            print(f"⚠️  Domain {domain_name} already has valid certificate: {existing.certificate_id}")
            override = input("Issue new certificate anyway? (y/n): ").lower()
            if override != 'y':
                return None

        # Issue certificate
        cert = self.ca.issue_certificate(domain_name, validity_days, key_algorithm)

        if cert:
            # Store certificate
            self.certificates[cert.certificate_id] = cert

            # Update domain index
            if domain_name not in self.domain_index:
                self.domain_index[domain_name] = []
            self.domain_index[domain_name].append(cert.certificate_id)

            # Add metadata
            cert.metadata['auto_renew'] = auto_renew

            # Log the action
            self._log_action('CREATE', cert.certificate_id, f"Certificate created for {domain_name}")

        return cert

    def get_certificate(self, cert_id: str) -> Optional[Certificate]:
        """Get certificate by ID."""
        return self.certificates.get(cert_id)

    def get_certificates_by_domain(self, domain_name: str) -> List[Certificate]:
        """Get all certificates for a domain."""
        cert_ids = self.domain_index.get(domain_name, [])
        return [self.certificates[cid] for cid in cert_ids if cid in self.certificates]

    def get_valid_certificate(self, domain_name: str) -> Optional[Certificate]:
        """Get the latest valid certificate for a domain."""
        certs = self.get_certificates_by_domain(domain_name)

        # Filter valid certificates
        valid_certs = [c for c in certs if c.status == CertificateStatus.VALID and not c.is_expired()]

        if not valid_certs:
            return None

        # Return the one with latest expiration date
        return max(valid_certs, key=lambda c: c.expiration_date)

    def check_expired_certificates(self) -> List[Certificate]:
        """Check for expired certificates and update their status."""
        expired = []

        for cert in self.certificates.values():
            if cert.status == CertificateStatus.VALID and cert.is_expired():
                cert.status = CertificateStatus.EXPIRED
                expired.append(cert)
                self._log_action('EXPIRE', cert.certificate_id, "Certificate expired")

        return expired

    def check_expiring_certificates(self, days_threshold: int = 30) -> List[Certificate]:
        """Find certificates expiring within the threshold."""
        expiring = []
        cutoff_date = datetime.now() + timedelta(days=days_threshold)

        for cert in self.certificates.values():
            if cert.status == CertificateStatus.VALID and cert.expiration_date <= cutoff_date:
                expiring.append(cert)

        return expiring

    def renew_certificate(self, cert_id: str, validity_days: int = 365) -> Optional[Certificate]:
        """Renew a certificate."""
        cert = self.get_certificate(cert_id)

        if not cert:
            print(f"❌ Certificate {cert_id} not found")
            return None

        if cert.status == CertificateStatus.REVOKED:
            print(f"❌ Cannot renew revoked certificate")
            return None

        # Issue new certificate
        new_cert = self.create_certificate(
            cert.domain_name,
            validity_days,
            cert.key_algorithm,
            cert.metadata.get('auto_renew', True)
        )

        if new_cert:
            self._log_action('RENEW', cert_id, f"Renewed to {new_cert.certificate_id}")
            print(f"🔄 Certificate renewed: {new_cert.certificate_id}")

        return new_cert

    def revoke_certificate(self, cert_id: str, reason: str) -> bool:
        """Revoke a certificate."""
        cert = self.get_certificate(cert_id)

        if not cert:
            print(f"❌ Certificate {cert_id} not found")
            return False

        if self.ca.revoke_certificate(cert, reason):
            self._log_action('REVOKE', cert_id, f"Revoked: {reason}")
            return True

        return False

    def auto_renew_certificates(self) -> List[Certificate]:
        """Automatically renew certificates that are due for renewal."""
        renewed = []
        expiring = self.check_expiring_certificates(self.renewal_auto_threshold)

        for cert in expiring:
            if cert.metadata.get('auto_renew', False):
                print(f"🔄 Auto-renewing {cert.certificate_id} for {cert.domain_name}")
                new_cert = self.renew_certificate(cert.certificate_id)
                if new_cert:
                    renewed.append(new_cert)

        return renewed

    def display_certificate_details(self, cert_id: str = None) -> None:
        """Display detailed certificate information."""
        if cert_id:
            certs = [self.get_certificate(cert_id)] if self.get_certificate(cert_id) else []
        else:
            certs = list(self.certificates.values())

        if not certs:
            print("No certificates found.")
            return

        for cert in certs:
            if not cert:
                continue

            print("\n" + "=" * 60)
            print(f"CERTIFICATE DETAILS: {cert.certificate_id}")
            print("=" * 60)

            data = cert.to_dict()

            # Format and display certificate data
            print(f"Domain: {data['domain_name']}")
            print(f"Issuer: {data['issuer']}")
            print(f"Algorithm: {data['key_algorithm']}")
            print(f"Issued: {data['issue_date'][:10]}")
            print(f"Expires: {data['expiration_date'][:10]}")
            print(f"Status: {data['status'].upper()}")

            if data['revocation_reason']:
                print(f"Revocation Reason: {data['revocation_reason']}")

            print(f"Public Key: {data['public_key'][:30]}...")
            print(f"Signature: {data['signature'][:30]}..." if data['signature'] else "Signature: Not signed")

            if cert.status == CertificateStatus.VALID:
                days = cert.days_until_expiration()
                if days < 30:
                    print(f"⚠️  WARNING: Certificate expires in {days} days!")

            # Show renewal info
            if 'renewed_from' in data['metadata']:
                print(f"Renewed from: {data['metadata']['renewed_from']}")

    def generate_report(self) -> Dict:
        """Generate a comprehensive certificate management report."""
        self.check_expired_certificates()  # Update status

        total = len(self.certificates)
        valid = sum(1 for c in self.certificates.values() if c.status == CertificateStatus.VALID and not c.is_expired())
        expired = sum(1 for c in self.certificates.values() if c.status == CertificateStatus.EXPIRED or c.is_expired())
        revoked = sum(1 for c in self.certificates.values() if c.status == CertificateStatus.REVOKED)

        expiring_30 = len(self.check_expiring_certificates(30))
        expiring_7 = len(self.check_expiring_certificates(7))

        report = {
            'generated_at': datetime.now().isoformat(),
            'ca_name': self.ca.name,
            'total_certificates': total,
            'valid_certificates': valid,
            'expired_certificates': expired,
            'revoked_certificates': revoked,
            'expiring_in_30_days': expiring_30,
            'expiring_in_7_days': expiring_7,
            'auto_renewal_threshold': self.renewal_auto_threshold,
            'domains': list(self.domain_index.keys()),
            'recent_activity': self.audit_log[-10:]  # Last 10 activities
        }

        return report

    def display_report(self) -> None:
        """Display the certificate management report."""
        report = self.generate_report()

        print("\n" + "=" * 60)
        print("📊 CERTIFICATE MANAGEMENT REPORT")
        print("=" * 60)
        print(f"Generated: {report['generated_at'][:16]}")
        print(f"Certificate Authority: {report['ca_name']}")
        print("\n📈 Statistics:")
        print(f"  Total Certificates: {report['total_certificates']}")
        print(f"  ✅ Valid: {report['valid_certificates']}")
        print(f"  ❌ Expired: {report['expired_certificates']}")
        print(f"  🚫 Revoked: {report['revoked_certificates']}")

        if report['expiring_in_30_days'] > 0:
            print(f"\n⚠️  Certificates expiring:")
            print(f"  • Within 30 days: {report['expiring_in_30_days']}")
            print(f"  • Within 7 days: {report['expiring_in_7_days']}")

        if report['recent_activity']:
            print("\n📝 Recent Activity:")
            for activity in report['recent_activity'][-5:]:  # Last 5
                print(f"  • {activity}")

    def export_certificates(self, filename: str = "certificates.json") -> None:
        """Export all certificates to JSON file."""
        data = {
            'ca_name': self.ca.name,
            'export_date': datetime.now().isoformat(),
            'certificates': [cert.to_dict() for cert in self.certificates.values()]
        }

        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Certificates exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting certificates: {e}")

    def _log_action(self, action: str, cert_id: str, details: str) -> None:
        """Log an action to the audit log."""
        log_entry = f"{datetime.now().isoformat()} - {action}: {cert_id} - {details}"
        self.audit_log.append(log_entry)

    def show_audit_log(self, limit: int = 20) -> None:
        """Display the audit log."""
        if not self.audit_log:
            print("No audit log entries.")
            return

        print("\n📋 AUDIT LOG")
        print("-" * 60)
        for entry in self.audit_log[-limit:]:
            print(entry)


def main():
    """Main function to run the certificate management system."""

    print("=" * 60)
    print("🔐 CERTIFICATE MANAGEMENT SYSTEM")
    print("=" * 60)
    print("A tool for managing digital certificates")

    # Initialize the system
    ca_name = input("\nEnter Certificate Authority name (default: 'MyCA'): ").strip()
    if not ca_name:
        ca_name = "MyCA"

    ca = CertificateAuthority(ca_name)
    manager = CertificateManager(ca)

    # Add some example certificates
    print("\n📋 Adding example certificates...")

    # Valid certificates
    manager.create_certificate("example.com", 365, KeyAlgorithm.RSA_2048)
    manager.create_certificate("secure.example.com", 180, KeyAlgorithm.ECDSA_256)
    manager.create_certificate("api.example.com", 90, KeyAlgorithm.RSA_4096)

    # Certificate that will expire soon
    soon_cert = Certificate("expiring.com", ca_name, 7, KeyAlgorithm.RSA_2048)
    soon_cert.sign(ca.private_key)
    manager.certificates[soon_cert.certificate_id] = soon_cert
    manager.domain_index.setdefault("expiring.com", []).append(soon_cert.certificate_id)

    # Interactive menu
    while True:
        print("\n" + "=" * 50)
        print("📌 MAIN MENU")
        print("=" * 50)
        print("1. Create new certificate")
        print("2. View all certificates")
        print("3. View certificate details")
        print("4. Check expired/expiring certificates")
        print("5. Renew certificate")
        print("6. Revoke certificate")
        print("7. Auto-renew expiring certificates")
        print("8. Generate management report")
        print("9. Export certificates to JSON")
        print("10. Show audit log")
        print("11. Certificate Authority stats")
        print("12. Validate certificate")
        print("13. Exit")
        print("-" * 50)

        choice = input("Enter your choice (1-13): ").strip()

        try:
            if choice == '1':
                print("\n--- Create New Certificate ---")
                domain = input("Domain name: ").strip()

                print("\nValidity period:")
                print("1. 90 days (3 months)")
                print("2. 180 days (6 months)")
                print("3. 365 days (1 year)")
                print("4. 730 days (2 years)")
                print("5. Custom")

                validity_choice = input("Select validity (1-5): ").strip()
                validity_map = {'1': 90, '2': 180, '3': 365, '4': 730}

                if validity_choice == '5':
                    validity_days = int(input("Enter number of days: "))
                else:
                    validity_days = validity_map.get(validity_choice, 365)

                print("\nKey Algorithm:")
                print("1. RSA-2048")
                print("2. RSA-4096")
                print("3. ECDSA-256")
                print("4. ECDSA-384")
                print("5. ED25519")

                algo_choice = input("Select algorithm (1-5, default: 1): ").strip()
                algo_map = {
                    '1': KeyAlgorithm.RSA_2048,
                    '2': KeyAlgorithm.RSA_4096,
                    '3': KeyAlgorithm.ECDSA_256,
                    '4': KeyAlgorithm.ECDSA_384,
                    '5': KeyAlgorithm.ED25519
                }
                algorithm = algo_map.get(algo_choice, KeyAlgorithm.RSA_2048)

                auto_renew = input("Enable auto-renewal? (y/n, default: y): ").lower() != 'n'

                cert = manager.create_certificate(domain, validity_days, algorithm, auto_renew)

            elif choice == '2':
                if not manager.certificates:
                    print("No certificates found.")
                else:
                    print("\n📜 ALL CERTIFICATES:")
                    print("-" * 60)
                    for cert in manager.certificates.values():
                        print(cert)

            elif choice == '3':
                cert_id = input("Enter certificate ID (leave blank to list all): ").strip()
                manager.display_certificate_details(cert_id if cert_id else None)

            elif choice == '4':
                print("\n--- Expiration Check ---")

                expired = manager.check_expired_certificates()
                if expired:
                    print(f"\n❌ Expired Certificates ({len(expired)}):")
                    for cert in expired:
                        print(
                            f"  • {cert.certificate_id}: {cert.domain_name} (expired {cert.expiration_date.strftime('%Y-%m-%d')})")

                days = int(input("\nCheck for certificates expiring within days (default: 30): ") or "30")
                expiring = manager.check_expiring_certificates(days)

                if expiring:
                    print(f"\n⚠️  Certificates expiring within {days} days ({len(expiring)}):")
                    for cert in expiring:
                        days_left = cert.days_until_expiration()
                        print(f"  • {cert.certificate_id}: {cert.domain_name} ({days_left} days left)")
                else:
                    print(f"\n✅ No certificates expiring within {days} days")

            elif choice == '5':
                cert_id = input("Enter certificate ID to renew: ").strip()
                validity = int(input("New validity period in days (default: 365): ") or "365")
                manager.renew_certificate(cert_id, validity)

            elif choice == '6':
                cert_id = input("Enter certificate ID to revoke: ").strip()
                reason = input("Revocation reason: ").strip()
                if reason:
                    manager.revoke_certificate(cert_id, reason)

            elif choice == '7':
                renewed = manager.auto_renew_certificates()
                if renewed:
                    print(f"\n🔄 Auto-renewed {len(renewed)} certificates")
                else:
                    print("\n✅ No certificates needed auto-renewal")

            elif choice == '8':
                manager.display_report()

            elif choice == '9':
                filename = input("Enter filename (default: certificates.json): ").strip()
                if not filename:
                    filename = "certificates.json"
                manager.export_certificates(filename)

            elif choice == '10':
                limit = int(input("Number of entries to show (default: 20): ") or "20")
                manager.show_audit_log(limit)

            elif choice == '11':
                stats = ca.get_statistics()
                print("\n🏢 CERTIFICATE AUTHORITY STATISTICS")
                print("-" * 40)
                for key, value in stats.items():
                    if key != 'policies':
                        print(f"{key.replace('_', ' ').title()}: {value}")

                print("\n📋 Policies:")
                for policy, value in stats['policies'].items():
                    print(f"  • {policy}: {value}")

            elif choice == '12':
                cert_id = input("Enter certificate ID to validate: ").strip()
                cert = manager.get_certificate(cert_id)
                if cert:
                    print(f"\nValidating certificate {cert_id}...")
                    if ca.validate_certificate(cert):
                        print("✅ Certificate is valid!")
                    else:
                        print("❌ Certificate validation failed")
                else:
                    print("Certificate not found")

            elif choice == '13':
                print("\n👋 Exiting Certificate Management System. Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter a number between 1 and 13.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
            break
        except ValueError as e:
            print(f"❌ Input error: {e}")
        except Exception as e:
            print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()