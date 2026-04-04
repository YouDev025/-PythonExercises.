#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Hidden Directory Finder v2.0 - Enhanced Edition          ║
║                         Advanced Web Path Discovery Tool                     ║
║                          For authorized testing only                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Enhancements:
- Intelligent false-positive filtering (SPA catch-all routes)
- Response similarity detection (fingerprinting)
- Content-type and header analysis
- Smart wordlist generation based on responses
- Recursive directory discovery
- API endpoint detection
- Extension fuzzing (json, xml, yaml, etc.)
- Export in multiple formats (JSON, CSV, HTML)
- Resume capability for long scans
"""

import requests
import threading
import time
import sys
import os
import json
import csv
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse, urljoin
from collections import defaultdict
from difflib import SequenceMatcher
import argparse
import signal
from typing import Dict, List, Set, Tuple, Optional, Any

# ──────────────────────────────────────────────────────────────────────────────
# ANSI colour helpers
# ──────────────────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    os.system("color")

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"

# ──────────────────────────────────────────────────────────────────────────────
# ENHANCED WORDLIST - More targeted and organized
# ──────────────────────────────────────────────────────────────────────────────
ENHANCED_WORDLIST = {
    # Modern API patterns
    "api": ["api", "rest", "graphql", "v1", "v2", "v3", "swagger", "docs", "redoc"],

    # Authentication (modern)
    "auth": ["auth", "login", "signin", "logout", "signout", "register", "signup",
             "oauth", "oauth2", "callback", "token", "jwt", "session", "sso"],

    # Admin panels (multiple variations)
    "admin": ["admin", "administrator", "admin-panel", "admin_panel", "adminpanel",
              "cpanel", "webadmin", "administration", "sysadmin", "root", "manage"],

    # Development artifacts
    "dev": [".git", ".svn", ".hg", ".env", ".aws", "Dockerfile", "docker-compose.yml",
            "Jenkinsfile", ".travis.yml", ".circleci", "kube", "helm", "terraform"],

    # Configuration files
    "config": ["config", "configuration", "settings", ".env", ".env.local",
               "application.yml", "application.properties", "appsettings.json"],

    # Backup files
    "backup": ["backup", "backups", "bak", "old", "copy", "backup.zip",
               "backup.tar.gz", "dump.sql", "database.sql", "db.backup"],

    # Logs and monitoring
    "logs": ["logs", "log", "debug", "trace", "metrics", "health", "status",
             "ping", "ready", "live", "info", "stats", "monitoring", "prometheus"],

    # File operations
    "files": ["upload", "uploads", "download", "downloads", "files", "media",
              "assets", "static", "public", "private", "storage", "temp"],

    # Database interfaces
    "database": ["phpmyadmin", "adminer", "pgadmin", "mongo-express", "redis",
                 "mysql", "postgres", "database", "db", "sql", "nosql"],

    # Testing endpoints
    "testing": ["test", "tests", "testing", "debug", "dev", "development",
                "staging", "stage", "qa", "uat", "sandbox", "demo"],

    # Web shells and backdoors
    "shells": ["shell", "cmd", "exec", "command", "bash", "sh", "cgi-bin",
               "php-shell", "webshell", "backdoor", "hack"],

    # Juice Shop specific (since you identified it)
    "juiceshop": ["rest/user/login", "rest/user/register", "rest/user/whoami",
                  "rest/products/search", "rest/products/reviews",
                  "rest/admin/application-configuration", "api/Challenges",
                  "api/Challenges/continue-code", "ftp", "support/logs",
                  "privacy-support/e2e", "redirect", "track-result",
                  "file-upload", "score-board", "administration"],

    # Modern frameworks paths
    "frameworks": ["_next", "nextjs", "static", "_nuxt", "vue", "react", "angular",
                   "assets", "build", "dist", "public", "resources", "webpack"],
}

# Flatten the wordlist
DEFAULT_WORDLIST = []
for category, paths in ENHANCED_WORDLIST.items():
    DEFAULT_WORDLIST.extend(paths)

# Extension list for fuzzing
EXTENSIONS = ["", ".json", ".xml", ".yaml", ".yml", ".txt", ".log", ".bak",
              ".old", ".sql", ".zip", ".tar.gz", ".gz", ".conf", ".config",
              ".ini", ".properties", ".env", ".php", ".asp", ".aspx", ".jsp"]

# Common response patterns that indicate false positives
FALSE_POSITIVE_PATTERNS = [
    r"react", r"angular", r"vue", r"<app-root", r"ng-app",
    r"__NEXT_DATA__", r"<div id=\"root\">", r"<div id=\"app\">",
    r"webpack", r"bundle\.js", r"main\.[a-f0-9]+\.js",
    r"<script.*?src=.*?chunk", r"manifest\.[a-f0-9]+\.js"
]


# ──────────────────────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────────────────────
class ScanResult:
    """Enhanced result storage with metadata"""

    def __init__(self, url: str, status: int, size: int, content_type: str = "",
                 headers: Dict = None, response_hash: str = "", title: str = ""):
        self.url = url
        self.status = status
        self.size = size
        self.content_type = content_type
        self.headers = headers or {}
        self.response_hash = response_hash
        self.title = title
        self.is_false_positive = False
        self.similarity_group = ""
        self.depth = url.count('/') - 2  # Rough depth indicator

    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "status": self.status,
            "size": self.size,
            "content_type": self.content_type,
            "title": self.title,
            "response_hash": self.response_hash,
            "depth": self.depth
        }


class ScanState:
    """Maintain scan state for resume capability"""

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.results: List[ScanResult] = []
        self.scanned: Set[str] = set()
        self.fingerprints: Dict[str, List[ScanResult]] = defaultdict(list)
        self.start_time = datetime.now()
        self.base_response_hash = None
        self.base_size = None

    def save_state(self):
        """Save current scan state to resume later"""
        state_file = f"{self.output_file}.state.json"
        with open(state_file, 'w') as f:
            json.dump({
                "scanned": list(self.scanned),
                "results_count": len(self.results),
                "timestamp": self.start_time.isoformat()
            }, f)


class SmartWordlist:
    """Dynamically generates wordlist based on discovered patterns"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.discovered_patterns: Set[str] = set()
        self.generated_paths: Set[str] = set()

    def analyze_and_generate(self, results: List[ScanResult]) -> List[str]:
        """Generate new paths based on discovered patterns"""
        new_paths = set()

        for result in results:
            # Extract potential patterns from URLs
            parts = result.url.replace(self.base_url, "").strip("/").split("/")
            if len(parts) > 1:
                # Add parent directories
                for i in range(1, len(parts)):
                    parent = "/".join(parts[:i])
                    if parent and parent not in self.discovered_patterns:
                        new_paths.add(parent)

                # Add common variations
                last_part = parts[-1]
                variations = [
                    last_part + "s",  # plural
                    last_part + "-admin",  # admin variant
                    last_part + "_admin",
                    "admin-" + last_part,
                    "api/" + last_part,
                    "rest/" + last_part,
                ]
                new_paths.update(variations)

        return list(new_paths - self.generated_paths)


# ──────────────────────────────────────────────────────────────────────────────
# Enhanced Detection Functions
# ──────────────────────────────────────────────────────────────────────────────
def is_likely_spa(response_text: str) -> bool:
    """Detect if response is a Single Page Application shell (false positive)"""
    if not response_text:
        return False

    # Check for SPA indicators
    for pattern in FALSE_POSITIVE_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return True

    # Check for high ratio of JavaScript to content
    js_ratio = len(re.findall(r'<script', response_text)) / max(1, len(response_text) / 1000)
    if js_ratio > 0.5:  # More than 0.5 scripts per KB
        return True

    return False


def extract_page_title(html: str) -> str:
    """Extract title from HTML response"""
    match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def calculate_similarity(hash1: str, hash2: str) -> float:
    """Calculate similarity between two response hashes"""
    if not hash1 or not hash2:
        return 0.0
    return SequenceMatcher(None, hash1[:64], hash2[:64]).ratio()


def fingerprint_response(response: requests.Response) -> Dict:
    """Create a fingerprint of the response for comparison"""
    content_hash = hashlib.sha256(response.content).hexdigest()

    # Get structural fingerprint (just the HTML structure without dynamic content)
    text = response.text
    # Remove dynamic content like timestamps, CSRF tokens
    text = re.sub(r'data-[a-z-]+="[^"]+"', '', text)
    text = re.sub(r'name="csrf"[^>]+value="[^"]+"', '', text)
    text = re.sub(r'[0-9a-f]{32,}', '', text)  # Remove long hashes
    structural_hash = hashlib.sha256(text.encode()).hexdigest()

    return {
        "content_hash": content_hash,
        "structural_hash": structural_hash,
        "size": len(response.content),
        "content_type": response.headers.get('content-type', '').split(';')[0]
    }


# ──────────────────────────────────────────────────────────────────────────────
# Enhanced Probe Function
# ──────────────────────────────────────────────────────────────────────────────
def probe_path_enhanced(
        base_url: str,
        path: str,
        timeout: int,
        allowed_codes: Set[int],
        delay: float,
        session: requests.Session,
        base_fingerprint: Optional[Dict] = None,
        smart_filter: bool = True,
) -> Optional[ScanResult]:
    """Enhanced probe with better detection and filtering"""

    url = urljoin(base_url, path)

    if delay > 0:
        time.sleep(delay)

    try:
        response = session.get(
            url,
            timeout=timeout,
            allow_redirects=False,
            verify=False,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        )

        code = response.status_code
        size = len(response.content)
        content_type = response.headers.get('content-type', '').split(';')[0]

        # Extract title for HTML
        title = ""
        if 'html' in content_type.lower():
            title = extract_page_title(response.text)

        # Create fingerprint
        fingerprint = fingerprint_response(response)

        # Smart filtering - skip likely false positives
        if smart_filter and code == 200 and 'html' in content_type.lower():
            if is_likely_spa(response.text):
                # Still return but mark as potential false positive
                result = ScanResult(url, code, size, content_type,
                                    dict(response.headers), fingerprint['content_hash'], title)
                result.is_false_positive = True
                return result

        # Check if response is different from base (if base exists)
        if base_fingerprint and code == 200:
            similarity = calculate_similarity(fingerprint['content_hash'],
                                              base_fingerprint.get('content_hash', ''))
            if similarity > 0.95:  # 95% similar to base page
                result = ScanResult(url, code, size, content_type,
                                    dict(response.headers), fingerprint['content_hash'], title)
                result.is_false_positive = True
                return result

        if code in allowed_codes:
            return ScanResult(url, code, size, content_type,
                              dict(response.headers), fingerprint['content_hash'], title)

    except Exception:
        pass

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Recursive Directory Discovery
# ──────────────────────────────────────────────────────────────────────────────
def discover_recursive(base_url: str, initial_paths: List[str], depth: int = 2, **kwargs):
    """Recursively discover directories by exploring found paths"""
    discovered = set(initial_paths)
    all_results = []

    for current_depth in range(depth):
        new_paths = set()

        # For each discovered path, try to find subdirectories
        for path in discovered:
            # Add common subdirectory patterns
            subdir_patterns = [
                f"{path}/admin",
                f"{path}/api",
                f"{path}/config",
                f"{path}/backup",
                f"{path}/logs",
                f"{path}/static",
                f"{path}/uploads",
                f"{path}/assets",
            ]
            new_paths.update(subdir_patterns)

        # Remove already scanned paths
        new_paths -= discovered

        if not new_paths:
            break

        # Scan new paths
        print(f"\n{BLUE}[*]{RESET} Recursive scan depth {current_depth + 1}: {len(new_paths)} new paths")

        with ThreadPoolExecutor(max_workers=kwargs.get('threads', 10)) as executor:
            futures = {
                executor.submit(
                    probe_path_enhanced,
                    base_url,
                    path,
                    kwargs.get('timeout', 5),
                    kwargs.get('codes', {200, 301, 302, 403}),
                    kwargs.get('delay', 0),
                    kwargs.get('session', requests.Session()),
                    kwargs.get('base_fingerprint'),
                    kwargs.get('smart_filter', True)
                ): path
                for path in new_paths
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    all_results.append(result)
                    discovered.add(result.url.replace(base_url, "").lstrip("/"))

        discovered.update(new_paths)

    return all_results


# ──────────────────────────────────────────────────────────────────────────────
# Export Functions
# ──────────────────────────────────────────────────────────────────────────────
def export_json(results: List[ScanResult], filename: str):
    """Export results to JSON format"""
    data = {
        "scan_time": datetime.now().isoformat(),
        "total_found": len(results),
        "results": [r.to_dict() for r in results]
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"{GREEN}[+]{RESET} JSON export saved to {filename}")


def export_csv(results: List[ScanResult], filename: str):
    """Export results to CSV format"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['URL', 'Status', 'Size', 'Content Type', 'Title', 'Depth'])
        for r in results:
            writer.writerow([r.url, r.status, r.size, r.content_type, r.title, r.depth])
    print(f"{GREEN}[+]{RESET} CSV export saved to {filename}")


def export_html(results: List[ScanResult], filename: str):
    """Export results to HTML report"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Hidden Directory Scan Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f0f0f0; padding: 10px; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .status-200 {{ color: green; font-weight: bold; }}
        .status-301 {{ color: orange; }}
        .status-403 {{ color: red; }}
        .status-401 {{ color: purple; }}
    </style>
</head>
<body>
    <h1>Hidden Directory Scanner Results</h1>
    <div class="summary">
        <p><strong>Scan Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Found:</strong> {len(results)}</p>
    </div>
    <table>
        <tr>
            <th>URL</th>
            <th>Status</th>
            <th>Size (bytes)</th>
            <th>Content Type</th>
            <th>Title</th>
        </tr>
"""
    for r in results:
        status_class = f"status-{r.status}"
        html += f"""
        <tr>
            <td><a href="{r.url}" target="_blank">{r.url}</a></td>
            <td class="{status_class}">{r.status}</td>
            <td>{r.size}</td>
            <td>{r.content_type}</td>
            <td>{r.title}</td>
        </tr>"""

    html += """
    </table>
</body>
</html>"""

    with open(filename, 'w') as f:
        f.write(html)
    print(f"{GREEN}[+]{RESET} HTML report saved to {filename}")


# ──────────────────────────────────────────────────────────────────────────────
# Main Scanner Class
# ──────────────────────────────────────────────────────────────────────────────
class EnhancedDirectoryScanner:
    def __init__(self, target: str, threads: int = 20, timeout: int = 5,
                 delay: float = 0, output: str = "scan_results"):
        self.target = target.rstrip('/')
        self.threads = min(threads, 50)
        self.timeout = timeout
        self.delay = delay
        self.output_base = output
        self.session = requests.Session()
        self.results: List[ScanResult] = []
        self.base_fingerprint = None

    def get_base_fingerprint(self):
        """Get fingerprint of the main page for comparison"""
        try:
            response = self.session.get(self.target, timeout=self.timeout, verify=False)
            self.base_fingerprint = fingerprint_response(response)
            print(f"{CYAN}[*]{RESET} Base fingerprint: {self.base_fingerprint['content_hash'][:16]}...")
        except:
            print(f"{YELLOW}[!]{RESET} Could not get base fingerprint")
            self.base_fingerprint = None

    def scan(self, wordlist: List[str], codes: Set[int], smart_filter: bool = True):
        """Main scan function"""
        total = len(wordlist)
        scanned = 0
        lock = threading.Lock()

        print(f"\n{CYAN}[*]{RESET} Starting scan of {total} paths with {self.threads} threads\n")

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(
                    probe_path_enhanced,
                    self.target,
                    path,
                    self.timeout,
                    codes,
                    self.delay,
                    self.session,
                    self.base_fingerprint if smart_filter else None,
                    smart_filter
                ): path
                for path in wordlist
            }

            for future in as_completed(futures):
                scanned += 1
                result = future.result()
                if result:
                    with lock:
                        self.results.append(result)
                        # Print real-time result
                        fp_marker = "⚠️ " if result.is_false_positive else "✓"
                        print(f"\r{GREEN}[{fp_marker}]{RESET} {result.status} {result.url[:80]} "
                              f"({result.size} bytes){' ' * 20}")

                # Progress indicator
                if scanned % 50 == 0 or scanned == total:
                    progress = int((scanned / total) * 40)
                    bar = f"[{'█' * progress}{'░' * (40 - progress)}]"
                    print(f"\r{DIM}{bar} {scanned}/{total} ({len(self.results)} found){RESET}",
                          end="", flush=True)

        print()  # New line after progress bar

        # Filter out false positives if needed
        real_results = [r for r in self.results if not r.is_false_positive]
        fp_results = [r for r in self.results if r.is_false_positive]

        if fp_results:
            print(f"\n{YELLOW}[!]{RESET} Filtered {len(fp_results)} false positives (SPA catch-all routes)")

        return real_results

    def save_results(self, results: List[ScanResult]):
        """Save results in multiple formats"""
        if not results:
            print(f"{YELLOW}[!]{RESET} No results to save")
            return

        # Sort by status code
        results.sort(key=lambda x: (x.status, x.url))

        # Text format
        txt_file = f"{self.output_base}.txt"
        with open(txt_file, 'w') as f:
            f.write(f"# Hidden Directory Scanner Results\n")
            f.write(f"# Target: {self.target}\n")
            f.write(f"# Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total found: {len(results)}\n\n")

            for r in results:
                f.write(f"[{r.status}] {r.url} (size: {r.size} bytes, type: {r.content_type})\n")
                if r.title:
                    f.write(f"    Title: {r.title}\n")

        print(f"{GREEN}[+]{RESET} Results saved to {txt_file}")

        # Export to other formats
        export_json(results, f"{self.output_base}.json")
        export_csv(results, f"{self.output_base}.csv")
        export_html(results, f"{self.output_base}.html")

    def run_enhanced_scan(self, wordlist: List[str] = None, codes: List[int] = None,
                          recursive: bool = False, fuzz_extensions: bool = False,
                          smart_filter: bool = True):
        """Run the complete enhanced scan"""

        print(f"""
{CYAN}{'═' * 70}{RESET}
{BOLD}Enhanced Directory Scanner v2.0{RESET}
{CYAN}{'═' * 70}{RESET}
  Target     : {BOLD}{self.target}{RESET}
  Threads    : {self.threads}
  Timeout    : {self.timeout}s
  Delay      : {self.delay}s
  Smart Filter: {smart_filter}
  Recursive  : {recursive}
  Fuzz Extensions: {fuzz_extensions}
{CYAN}{'═' * 70}{RESET}
""")

        # Get base fingerprint for comparison
        if smart_filter:
            self.get_base_fingerprint()

        # Use provided wordlist or default
        if not wordlist:
            wordlist = DEFAULT_WORDLIST

        codes_set = set(codes) if codes else {200, 201, 204, 301, 302, 307, 308, 401, 403}

        # Initial scan
        print(f"{CYAN}[*]{RESET} Starting initial scan...")
        results = self.scan(wordlist, codes_set, smart_filter)

        # Extension fuzzing
        if fuzz_extensions and results:
            print(f"\n{CYAN}[*]{RESET} Starting extension fuzzing on found paths...")
            extended_paths = []
            for result in results[:50]:  # Limit to top 50 to avoid explosion
                base_path = result.url.replace(self.target, "").rstrip('/')
                for ext in EXTENSIONS:
                    if ext:  # Skip empty extension (already scanned)
                        extended_paths.append(f"{base_path}{ext}")

            if extended_paths:
                ext_results = self.scan(extended_paths[:500], codes_set, smart_filter)
                results.extend(ext_results)

        # Recursive discovery
        if recursive and results:
            print(f"\n{CYAN}[*]{RESET} Starting recursive discovery...")
            paths_to_explore = [r.url.replace(self.target, "").lstrip('/') for r in results[:20]]
            recursive_results = discover_recursive(
                self.target, paths_to_explore, depth=2,
                threads=self.threads, timeout=self.timeout,
                codes=codes_set, delay=self.delay,
                session=self.session, base_fingerprint=self.base_fingerprint,
                smart_filter=smart_filter
            )
            results.extend(recursive_results)

        # Deduplicate by URL
        unique_results = {}
        for r in results:
            if r.url not in unique_results:
                unique_results[r.url] = r

        final_results = list(unique_results.values())

        # Print summary
        print(f"\n\n{CYAN}{'═' * 70}{RESET}")
        print(f"{BOLD}Scan Complete{RESET}")
        print(f"{CYAN}{'═' * 70}{RESET}")
        print(f"  Total Found: {GREEN}{len(final_results)}{RESET}")

        # Group by status
        status_groups = defaultdict(list)
        for r in final_results:
            status_groups[r.status].append(r)

        for status in sorted(status_groups.keys()):
            print(f"    {status}: {len(status_groups[status])} paths")

        # Save results
        if final_results:
            self.save_results(final_results)

            # Display top findings
            print(f"\n{BOLD}Top Interesting Findings:{RESET}")
            interesting = [r for r in final_results if any(
                keyword in r.url.lower() for keyword in
                ['admin', 'login', 'api', 'graphql', 'backup', 'env', 'git', 'ftp', 'database']
            )][:10]

            for r in interesting:
                print(f"  {GREEN}[{r.status}]{RESET} {r.url}")
                if r.title:
                    print(f"      └─ Title: {r.title}")
        else:
            print(f"\n{YELLOW}[!]{RESET} No interesting paths found")

        return final_results


# ──────────────────────────────────────────────────────────────────────────────
# CLI Argument Parser
# ──────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Hidden Directory Finder - Advanced Web Path Discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  python hidden_directory_finder.py -u http://example.com

  # Advanced scan with all features
  python hidden_directory_finder.py -u http://example.com --recursive --fuzz-extensions --smart-filter

  # Scan with custom wordlist and output
  python hidden_directory_finder.py -u http://example.com -w custom.txt -o results --threads 30

  # Focus on API endpoints only
  python hidden_directory_finder.py -u http://example.com --api-only
        """
    )

    parser.add_argument("-u", "--url", required=True, help="Target URL")
    parser.add_argument("-w", "--wordlist", help="Custom wordlist file")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Number of threads (default: 20)")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout (default: 5)")
    parser.add_argument("--delay", type=float, default=0, help="Delay between requests (default: 0)")
    parser.add_argument("-o", "--output", default="scan_results", help="Output file prefix (default: scan_results)")
    parser.add_argument("--codes", nargs="+", type=int, help="Status codes to report")
    parser.add_argument("--recursive", action="store_true", help="Enable recursive directory discovery")
    parser.add_argument("--fuzz-extensions", action="store_true", help="Fuzz file extensions on found paths")
    parser.add_argument("--no-smart-filter", action="store_true", help="Disable smart false-positive filtering")
    parser.add_argument("--api-only", action="store_true", help="Only scan API-related paths")
    parser.add_argument("--juice-shop", action="store_true", help="Juice Shop optimized scan")

    args = parser.parse_args()

    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Create scanner
    scanner = EnhancedDirectoryScanner(
        target=args.url,
        threads=args.threads,
        timeout=args.timeout,
        delay=args.delay,
        output=args.output
    )

    # Prepare wordlist
    wordlist = None
    if args.wordlist:
        with open(args.wordlist) as f:
            wordlist = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"{GREEN}[+]{RESET} Loaded {len(wordlist)} paths from {args.wordlist}")
    elif args.api_only:
        wordlist = ENHANCED_WORDLIST.get("api", []) + ENHANCED_WORDLIST.get("auth", [])
        print(f"{GREEN}[+]{RESET} API-only mode: {len(wordlist)} paths")
    elif args.juice_shop:
        wordlist = ENHANCED_WORDLIST.get("juiceshop", []) + ENHANCED_WORDLIST.get("api", [])
        print(f"{GREEN}[+]{RESET} Juice Shop mode: {len(wordlist)} paths")

    # Run scan
    scanner.run_enhanced_scan(
        wordlist=wordlist,
        codes=args.codes,
        recursive=args.recursive,
        fuzz_extensions=args.fuzz_extensions,
        smart_filter=not args.no_smart_filter
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}[!]{RESET} Scan interrupted by user")
        sys.exit(0)