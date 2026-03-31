#!/usr/bin/env python3
"""
Professional Subdomain Enumeration Tool
For educational and authorized penetration testing purposes only.

Features:
- DNS brute-force with customizable wordlist
- Passive reconnaissance via crt.sh
- Concurrent subdomain resolution
- HTTP probing with technology detection
- Localhost support with port handling
- Multiple output formats (text, JSON)
- Rate limiting and timeout controls
- Clean table display with color coding
"""

import socket
import json
import logging
import argparse
import sys
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import requests
from urllib3.exceptions import InsecureRequestWarning

# Try to import dnspython, fall back to socket if not available
try:
    import dns.resolver
    import dns.exception

    DNS_PYTHON_AVAILABLE = True
except ImportError:
    DNS_PYTHON_AVAILABLE = False
    print("[!] dnspython not installed. Using socket module for DNS resolution.")
    print("[!] Install dnspython for better performance: pip install dnspython")

# Suppress SSL warnings for HTTPS probing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ──────────────────────────────────────────────
# Configuration and Constants
# ──────────────────────────────────────────────

DEFAULT_THREADS = 20
DEFAULT_TIMEOUT = 5
DEFAULT_HTTP_TIMEOUT = 10
DEFAULT_RATE_LIMIT = 0.1  # Seconds between requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

    # Windows compatibility - disable colors on Windows if needed
    @staticmethod
    def disable_colors():
        Colors.GREEN = Colors.YELLOW = Colors.RED = Colors.BLUE = Colors.CYAN = Colors.END = Colors.BOLD = ''


# Check if running on Windows and disable colors if needed
if sys.platform == 'win32':
    # Colors work on Windows 10+ with ANSI support
    # If you see weird characters, uncomment the next line
    # Colors.disable_colors()
    pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Core Classes
# ──────────────────────────────────────────────

class SubdomainEnumerator:
    """Main enumerator class managing all enumeration activities."""

    def __init__(self, domain: str, port: Optional[int] = None,
                 threads: int = DEFAULT_THREADS, timeout: int = DEFAULT_TIMEOUT,
                 http_timeout: int = DEFAULT_HTTP_TIMEOUT,
                 rate_limit: float = DEFAULT_RATE_LIMIT):
        """
        Initialize enumerator with configuration.

        Args:
            domain: Target domain
            port: Optional port number
            threads: Number of concurrent threads
            timeout: DNS resolution timeout
            http_timeout: HTTP probing timeout
            rate_limit: Delay between HTTP requests
        """
        self.domain = domain
        self.port = port
        self.threads = threads
        self.timeout = timeout
        self.http_timeout = http_timeout
        self.rate_limit = rate_limit
        self.results: List[Dict] = []
        self.last_request_time = 0

        # Configure DNS resolver based on available libraries
        if DNS_PYTHON_AVAILABLE:
            self.dns_resolver = dns.resolver.Resolver()
            self.dns_resolver.timeout = timeout
            self.dns_resolver.lifetime = timeout

    def _rate_limit_wait(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()

    def resolve_subdomain(self, subdomain: str) -> Optional[Dict]:
        """
        Resolve a subdomain to IP addresses using DNS.

        Args:
            subdomain: Full subdomain to resolve

        Returns:
            Dictionary with subdomain info or None if resolution fails
        """
        try:
            # Handle localhost special case
            if self.domain == "localhost" or subdomain.endswith(".localhost") or subdomain == "localhost":
                return {
                    "subdomain": subdomain,
                    "ips": ["127.0.0.1"],
                    "resolved": True
                }

            ips = []

            # Use dnspython if available
            if DNS_PYTHON_AVAILABLE:
                try:
                    answers = self.dns_resolver.resolve(subdomain, 'A')
                    ips = [str(r) for r in answers]
                except (dns.exception.DNSException, Exception):
                    # Try AAAA records if A records fail
                    try:
                        answers = self.dns_resolver.resolve(subdomain, 'AAAA')
                        ips = [str(r) for r in answers]
                    except:
                        pass
            else:
                # Fallback to socket
                try:
                    socket.setdefaulttimeout(self.timeout)
                    addrinfo = socket.getaddrinfo(subdomain, None, socket.AF_INET)
                    ips = list(set([addr[4][0] for addr in addrinfo]))
                except socket.gaierror:
                    pass
                except socket.timeout:
                    pass

            if ips:
                return {
                    "subdomain": subdomain,
                    "ips": ips,
                    "resolved": True
                }

            return None

        except Exception as e:
            log.debug(f"Resolution failed for {subdomain}: {e}")
            return None

    def http_probe(self, subdomain: str) -> Optional[Dict]:
        """
        Probe HTTP/HTTPS services on discovered subdomains.

        Args:
            subdomain: Subdomain to probe

        Returns:
            Dictionary with HTTP information or None if unreachable
        """
        self._rate_limit_wait()

        protocols = ['https', 'http']
        result = {
            "subdomain": subdomain,
            "status_codes": [],
            "technologies": set(),
            "alive": False
        }

        for protocol in protocols:
            url = f"{protocol}://{subdomain}"
            if self.port:
                url = f"{protocol}://{subdomain}:{self.port}"

            try:
                response = requests.get(
                    url,
                    timeout=self.http_timeout,
                    verify=False,
                    headers={'User-Agent': USER_AGENT},
                    allow_redirects=True
                )

                status_code = response.status_code
                result["status_codes"].append(status_code)
                result["alive"] = True

                # Detect technologies from headers
                server = response.headers.get('Server', '')
                if server:
                    result["technologies"].add(f"Server: {server}")

                powered_by = response.headers.get('X-Powered-By', '')
                if powered_by:
                    result["technologies"].add(f"Powered By: {powered_by}")

                # Check for common frameworks
                if 'X-AspNet-Version' in response.headers:
                    result["technologies"].add("ASP.NET")
                if 'X-PHP-Version' in response.headers:
                    result["technologies"].add("PHP")
                if 'X-Generator' in response.headers:
                    result["technologies"].add(f"Generator: {response.headers['X-Generator']}")

                # If HTTPS works, don't try HTTP
                if protocol == 'https' and status_code < 400:
                    break

            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.ConnectionError:
                continue
            except Exception as e:
                log.debug(f"Probe failed for {subdomain} ({protocol}): {e}")
                continue

        if result["alive"]:
            result["technologies"] = list(result["technologies"])
            return result

        return None

    def brute_force(self, wordlist: List[str]) -> List[Dict]:
        """
        Perform DNS brute-force enumeration.

        Args:
            wordlist: List of subdomain names to try

        Returns:
            List of discovered subdomains
        """
        log.info(f"Starting brute-force enumeration with {len(wordlist)} words...")
        discovered = []

        # Build full subdomain list
        if self.domain == "localhost":
            subdomains = [f"{word}.localhost" for word in wordlist]
            # Add localhost itself
            subdomains.append("localhost")
        else:
            subdomains = [f"{word}.{self.domain}" for word in wordlist]

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_subdomain = {
                executor.submit(self.resolve_subdomain, subdomain): subdomain
                for subdomain in subdomains
            }

            for future in as_completed(future_to_subdomain):
                result = future.result()
                if result:
                    discovered.append(result)
                    log.debug(f"Found: {result['subdomain']}")

        log.info(f"Brute-force completed: {len(discovered)} subdomains found")
        return discovered

    def passive_enumeration(self) -> List[Dict]:
        """
        Perform passive enumeration using certificate transparency logs.

        Returns:
            List of discovered subdomains from crt.sh
        """
        log.info("Starting passive enumeration from crt.sh...")
        discovered = []

        try:
            # Query crt.sh API
            url = f"https://crt.sh/?q=%.{self.domain}&output=json"
            response = requests.get(url, timeout=self.http_timeout)

            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    log.warning("Failed to parse crt.sh response")
                    return []

                subdomains_set = set()

                for entry in data:
                    name_value = entry.get('name_value', '')
                    if not name_value:
                        continue

                    for name in name_value.split('\n'):
                        name = name.strip().lower()
                        if not name:
                            continue

                        # Remove wildcards
                        if name.startswith('*.'):
                            name = name[2:]

                        # Filter only relevant subdomains
                        if name.endswith(self.domain) and name != self.domain:
                            subdomains_set.add(name)

                log.info(f"Found {len(subdomains_set)} unique subdomains from crt.sh")

                # Resolve each discovered subdomain
                with ThreadPoolExecutor(max_workers=self.threads) as executor:
                    future_to_subdomain = {
                        executor.submit(self.resolve_subdomain, subdomain): subdomain
                        for subdomain in subdomains_set
                    }

                    for future in as_completed(future_to_subdomain):
                        result = future.result()
                        if result:
                            discovered.append(result)
                            log.debug(f"Found (passive): {result['subdomain']}")

                log.info(f"Passive enumeration completed: {len(discovered)} subdomains found")
            else:
                log.warning(f"Failed to fetch data from crt.sh (HTTP {response.status_code})")

        except requests.exceptions.RequestException as e:
            log.error(f"Network error during passive enumeration: {e}")
        except Exception as e:
            log.error(f"Passive enumeration error: {e}")

        return discovered

    def probe_subdomains(self, subdomains: List[Dict]) -> List[Dict]:
        """
        Perform HTTP probing on discovered subdomains.

        Args:
            subdomains: List of discovered subdomains

        Returns:
            List with HTTP probe information added
        """
        log.info("Starting HTTP probing...")

        if not subdomains:
            log.warning("No subdomains to probe")
            return []

        # Extract subdomain names
        subdomain_names = [s['subdomain'] for s in subdomains]

        probed_results = []

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_subdomain = {
                executor.submit(self.http_probe, subdomain): subdomain
                for subdomain in subdomain_names
            }

            for future in as_completed(future_to_subdomain):
                probe_result = future.result()
                if probe_result:
                    # Find corresponding DNS result
                    dns_result = next(
                        (s for s in subdomains if s['subdomain'] == probe_result['subdomain']),
                        None
                    )
                    if dns_result:
                        combined = {**dns_result, **probe_result}
                        probed_results.append(combined)
                        log.debug(f"Probed: {probe_result['subdomain']} - {probe_result['status_codes']}")

        log.info(f"HTTP probing completed: {len(probed_results)} services detected")
        return probed_results

    def merge_results(self, brute_results: List[Dict], passive_results: List[Dict]) -> List[Dict]:
        """
        Merge and deduplicate results from different sources.

        Args:
            brute_results: Results from brute-force
            passive_results: Results from passive enumeration

        Returns:
            Merged and deduplicated results
        """
        merged = {}

        for result in brute_results + passive_results:
            subdomain = result['subdomain']
            if subdomain not in merged:
                merged[subdomain] = {
                    'subdomain': subdomain,
                    'ips': result['ips'],
                    'resolved': result['resolved']
                }
            else:
                # Merge IPs
                merged[subdomain]['ips'] = list(set(merged[subdomain]['ips'] + result['ips']))

        return list(merged.values())

    def save_results(self, results: List[Dict], output_file: str):
        """
        Save results to both text and JSON formats.

        Args:
            results: List of result dictionaries
            output_file: Base filename for output
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save as JSON
        json_file = f"{output_file}_{timestamp}.json"
        try:
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2)
            log.info(f"Results saved to {json_file}")
        except Exception as e:
            log.error(f"Failed to save JSON results: {e}")

        # Save as human-readable text
        txt_file = f"{output_file}_{timestamp}.txt"
        try:
            with open(txt_file, 'w') as f:
                f.write(f"Subdomain Enumeration Results - {self.domain}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if self.port:
                    f.write(f"Port: {self.port}\n")
                f.write("=" * 80 + "\n\n")

                for result in results:
                    f.write(f"Subdomain: {result['subdomain']}\n")
                    f.write(f"IP Addresses: {', '.join(result['ips'])}\n")

                    if 'status_codes' in result and result['status_codes']:
                        f.write(f"HTTP Status Codes: {', '.join(map(str, result['status_codes']))}\n")
                    if 'technologies' in result and result['technologies']:
                        f.write(f"Technologies: {', '.join(result['technologies'])}\n")

                    f.write("-" * 40 + "\n")

                f.write(f"\nTotal subdomains found: {len(results)}\n")

            log.info(f"Results saved to {txt_file}")
        except Exception as e:
            log.error(f"Failed to save text results: {e}")

    def display_results(self, results: List[Dict]):
        """
        Display results in a clean table format in the terminal.

        Args:
            results: List of result dictionaries
        """
        if not results:
            print(f"\n{Colors.YELLOW}No subdomains found.{Colors.END}")
            return

        # Table header
        print(f"\n{Colors.BOLD}{'Subdomain':<35} {'IP Addresses':<25} {'Status':<15} {'Technologies'}{Colors.END}")
        print("=" * 110)

        for result in results:
            subdomain = result['subdomain']
            ips = ', '.join(result['ips'][:3])  # Show first 3 IPs
            if len(result['ips']) > 3:
                ips += f", +{len(result['ips']) - 3} more"

            # Status coloring
            if 'status_codes' in result and result['status_codes']:
                status = ', '.join(map(str, result['status_codes']))
                if any(code < 400 for code in result['status_codes']):
                    status = f"{Colors.GREEN}{status}{Colors.END}"
                elif any(code >= 500 for code in result['status_codes']):
                    status = f"{Colors.RED}{status}{Colors.END}"
                else:
                    status = f"{Colors.YELLOW}{status}{Colors.END}"
            else:
                status = f"{Colors.CYAN}Alive{Colors.END}"

            # Technologies
            tech = ', '.join(result.get('technologies', ['N/A'])[:2])
            if len(result.get('technologies', [])) > 2:
                tech += f", +{len(result['technologies']) - 2} more"

            # Truncate long fields
            subdomain_display = subdomain[:34] + ('..' if len(subdomain) > 34 else '')
            tech_display = tech[:30] + ('..' if len(tech) > 30 else '')

            print(f"{subdomain_display:<35} {ips:<25} {status:<15} {tech_display}")

        print("=" * 110)
        print(f"\n{Colors.BOLD}Summary:{Colors.END}")
        print(f"  Total subdomains found: {len(results)}")
        if any('status_codes' in r for r in results):
            live = sum(1 for r in results if 'status_codes' in r and r['status_codes'])
            print(f"  Live services detected: {live}")
        print()


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def load_wordlist(wordlist_file: Optional[str]) -> List[str]:
    """
    Load wordlist from file or use default.

    Args:
        wordlist_file: Path to wordlist file

    Returns:
        List of subdomain names
    """
    default_wordlist = [
        "www", "mail", "ftp", "admin", "dev", "test", "api", "staging", "beta",
        "app", "secure", "portal", "webmail", "cpanel", "whm", "blog", "shop",
        "store", "support", "help", "docs", "status", "demo", "qa", "stage",
        "prod", "production", "development", "internal", "external", "vpn",
        "remote", "exchange", "autodiscover", "m", "mobile", "mob", "ns1", "ns2",
        "dns", "dns1", "dns2", "mx", "mx1", "mx2", "smtp", "pop", "imap"
    ]

    if wordlist_file and Path(wordlist_file).exists():
        try:
            with open(wordlist_file, 'r', encoding='utf-8') as f:
                words = [line.strip().lower() for line in f if line.strip()]
            log.info(f"Loaded {len(words)} words from {wordlist_file}")
            return words
        except Exception as e:
            log.error(f"Error loading wordlist: {e}")
            log.info("Using default wordlist")
            return default_wordlist

    log.info("Using default wordlist")
    return default_wordlist


def validate_target(target: str) -> Tuple[str, Optional[int]]:
    """
    Validate and parse target domain/port.

    Args:
        target: Target string (e.g., example.com or localhost:5173)

    Returns:
        Tuple of (domain, port)
    """
    target = target.strip().lower()

    # Remove protocol prefixes
    for prefix in ["https://", "http://", "www."]:
        if target.startswith(prefix):
            target = target[len(prefix):]

    target = target.rstrip("/")

    # Extract port
    port = None
    if ":" in target:
        domain, port_str = target.split(":", 1)
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        except ValueError:
            raise ValueError(f"Invalid port: {port_str}")
    else:
        domain = target

    # Validate domain
    if domain != "localhost" and not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", domain):
        raise ValueError(f"Invalid domain: {domain}")

    return domain, port


def display_banner(domain: str, port: Optional[int]):
    """Display tool banner with target information."""
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{'Professional Subdomain Enumeration Tool'.center(70)}{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.END}")
    target_display = f"{domain}:{port}" if port else domain
    print(f"{Colors.YELLOW}Target:{Colors.END} {target_display}")
    print(f"{Colors.YELLOW}Started:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.RED}{'WARNING: Use only on authorized targets!'.center(70)}{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.END}\n")


# ──────────────────────────────────────────────
# Main Execution
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Professional Subdomain Enumeration Tool",
        epilog="For educational and authorized penetration testing only."
    )

    # Required arguments
    parser.add_argument("target", help="Target domain (e.g., example.com or localhost:5173)")

    # Enumeration options
    parser.add_argument("-w", "--wordlist", help="Custom wordlist file")
    parser.add_argument("--no-brute", action="store_true", help="Disable brute-force enumeration")
    parser.add_argument("--no-passive", action="store_true", help="Disable passive enumeration")
    parser.add_argument("--no-probe", action="store_true", help="Disable HTTP probing")

    # Performance options
    parser.add_argument("-t", "--threads", type=int, default=DEFAULT_THREADS,
                        help=f"Number of threads (default: {DEFAULT_THREADS})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"DNS timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--http-timeout", type=int, default=DEFAULT_HTTP_TIMEOUT,
                        help=f"HTTP timeout in seconds (default: {DEFAULT_HTTP_TIMEOUT})")
    parser.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT,
                        help=f"Rate limit in seconds (default: {DEFAULT_RATE_LIMIT})")

    # Output options
    parser.add_argument("-o", "--output", default="subdomain_results",
                        help="Output file prefix (default: subdomain_results)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Validate target
        domain, port = validate_target(args.target)
    except ValueError as e:
        log.error(f"Invalid target: {e}")
        sys.exit(1)

    # Display banner
    display_banner(domain, port)

    # Initialize enumerator
    enumerator = SubdomainEnumerator(
        domain=domain,
        port=port,
        threads=args.threads,
        timeout=args.timeout,
        http_timeout=args.http_timeout,
        rate_limit=args.rate_limit
    )

    # Load wordlist
    wordlist = load_wordlist(args.wordlist)

    all_results = []

    try:
        # Perform brute-force enumeration
        if not args.no_brute:
            brute_results = enumerator.brute_force(wordlist)
            all_results.extend(brute_results)
        else:
            log.info("Brute-force enumeration disabled")

        # Perform passive enumeration
        if not args.no_passive and domain != "localhost":
            passive_results = enumerator.passive_enumeration()
            all_results.extend(passive_results)
        else:
            if domain == "localhost":
                log.info("Passive enumeration skipped for localhost")
            else:
                log.info("Passive enumeration disabled")

        # Merge results
        if all_results:
            merged_results = enumerator.merge_results(all_results, [])

            # Perform HTTP probing
            if not args.no_probe:
                probed_results = enumerator.probe_subdomains(merged_results)
                final_results = probed_results if probed_results else merged_results
            else:
                log.info("HTTP probing disabled")
                final_results = merged_results

            # Display and save results
            enumerator.display_results(final_results)
            enumerator.save_results(final_results, args.output)
        else:
            log.warning("No subdomains discovered")
            print(
                f"\n{Colors.YELLOW}No subdomains were discovered. Try increasing threads or timeout values.{Colors.END}")

    except KeyboardInterrupt:
        log.warning("\nEnumeration interrupted by user")
        sys.exit(0)
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Security warning
    print(f"\n{Colors.RED}{Colors.BOLD}╔{'═' * 68}╗{Colors.END}")
    print(f"{Colors.RED}{Colors.BOLD}║{'WARNING: This tool is for authorized testing only!'.center(68)}║{Colors.END}")
    print(f"{Colors.RED}{Colors.BOLD}║{'Unauthorized use is illegal and unethical.'.center(68)}║{Colors.END}")
    print(f"{Colors.RED}{Colors.BOLD}╚{'═' * 68}╝{Colors.END}\n")

    main()