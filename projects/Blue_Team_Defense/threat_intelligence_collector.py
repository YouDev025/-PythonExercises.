#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          THREAT INTELLIGENCE COLLECTOR v1.0                      ║
║          Integrates AbuseIPDB · VirusTotal · IPinfo              ║
╚══════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 QUICK-START GUIDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 STEP 1 ── Install the only required dependency
 ───────────────────────────────────────────────
   pip install requests

 STEP 2 ── Run the program
 ──────────────────────────
   python threat_intelligence_collector.py

 STEP 3 ── (Optional) Add real API keys for live data
 ──────────────────────────────────────────────────────
   Without keys the tool still works using simulated data,
   which is clearly marked in the output.  To enable real
   lookups, choose ONE of the two methods below:

   Method A – set environment variables before running:

     Linux / macOS:
       export ABUSEIPDB_KEY="your_abuseipdb_key"
       export VIRUSTOTAL_KEY="your_virustotal_key"
       export IPINFO_TOKEN="your_ipinfo_token"    # optional
       python threat_intelligence_collector.py

     Windows (CMD):
       set ABUSEIPDB_KEY=your_abuseipdb_key
       set VIRUSTOTAL_KEY=your_virustotal_key
       set IPINFO_TOKEN=your_ipinfo_token
       python threat_intelligence_collector.py

     Windows (PowerShell):
       $env:ABUSEIPDB_KEY  = "your_abuseipdb_key"
       $env:VIRUSTOTAL_KEY = "your_virustotal_key"
       $env:IPINFO_TOKEN   = "your_ipinfo_token"
       python threat_intelligence_collector.py

   Method B – enter keys interactively inside the tool:
     Select menu option 6 "Configure API keys" and paste
     each key when prompted.  Keys stay active for the
     current session only (not saved to disk).

 WHERE TO GET FREE API KEYS
 ───────────────────────────
   AbuseIPDB  → https://www.abuseipdb.com/register
                Free tier: 1 000 checks / day
   VirusTotal → https://www.virustotal.com/gui/join-us
                Free tier: 4 requests / minute, 500 / day
   IPinfo     → https://ipinfo.io/signup
                Free tier: 50 000 requests / month
                (also works without a token at lower rate)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 MENU OPTIONS – WHAT EACH ONE DOES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 1. Analyse an IP address
    ┌─────────────────────────────────────────────────────────┐
    │ Prompts for an IPv4 or IPv6 address.                    │
    │ Queries: AbuseIPDB + VirusTotal + IPinfo                │
    │ Shows  : abuse confidence score, report count,          │
    │          malicious/suspicious detections, ISP, country, │
    │          city, timezone, and a composite risk level.    │
    │ Example input: 8.8.8.8                                  │
    └─────────────────────────────────────────────────────────┘

 2. Analyse a domain
    ┌─────────────────────────────────────────────────────────┐
    │ Prompts for a bare domain name (no http:// needed,      │
    │ but the tool strips it if you include it).              │
    │ Queries: VirusTotal domain report                       │
    │ Shows  : malicious / suspicious / harmless engine       │
    │          counts, reputation score, site categories,     │
    │          and a risk level.                              │
    │ Example input: example.com                              │
    └─────────────────────────────────────────────────────────┘

 3. Analyse a URL  (domain + resolved IP)
    ┌─────────────────────────────────────────────────────────┐
    │ Prompts for a full URL starting with http:// or         │
    │ https://.  Automatically:                               │
    │   a) Extracts the domain and runs a domain analysis.   │
    │   b) Resolves the domain to an IP via Cloudflare DoH   │
    │      and runs a full IP analysis.                       │
    │ Gives you the most complete picture of a suspicious     │
    │ link in one step.                                       │
    │ Example input: https://suspicious-site.example.com     │
    └─────────────────────────────────────────────────────────┘

 4. View session summary
    ┌─────────────────────────────────────────────────────────┐
    │ Prints a compact table of every target analysed in      │
    │ the current session with its risk level and score.      │
    │ Also shows totals: HIGH / MEDIUM / LOW counts.          │
    └─────────────────────────────────────────────────────────┘

 5. Export results to JSON
    ┌─────────────────────────────────────────────────────────┐
    │ Saves all session results (including raw API responses) │
    │ to  tic_results.json  in the current directory.         │
    │ Useful for further analysis, reporting, or importing    │
    │ into a SIEM / spreadsheet.                              │
    └─────────────────────────────────────────────────────────┘

 6. Configure API keys
    ┌─────────────────────────────────────────────────────────┐
    │ Lets you paste API keys interactively without           │
    │ restarting the program.  Shows which keys are           │
    │ currently set and which are using simulation mode.      │
    └─────────────────────────────────────────────────────────┘

 7. Exit
    Quits the program. You can also press Ctrl+C at any time.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 UNDERSTANDING THE OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Risk levels are colour-coded:
   HIGH   (red)    – score ≥ 60/100 – treat as confirmed threat
   MEDIUM (yellow) – score ≥ 20/100 – investigate further
   LOW    (green)  – score  < 20/100 – likely benign

 Composite score for IP:
   50 % AbuseIPDB confidence + 50 % VirusTotal detection ratio

 Composite score for domain:
   70 % VirusTotal detection ratio + 30 % reputation penalty

 "[simulated]" tag means no real API key was available for that
 source.  Simulated values are deterministically derived from
 the target string – useful for UI testing, not for real intel.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 CACHING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Results are cached in  tic_cache.json  for 1 hour (3 600 s).
 Re-querying the same target within that window returns the
 cached result instantly and does not consume API quota.
 To force a fresh lookup, delete tic_cache.json and re-run.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EXAMPLE WORKFLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 You received a suspicious email with a link.  Here is how to
 investigate it end-to-end:

   1. Run: python threat_intelligence_collector.py
   2. Select option 3 (Analyse a URL).
   3. Paste the suspicious link and press Enter.
   4. Review the domain report and the resolved-IP report.
   5. Select option 4 to see the combined session summary.
   6. Select option 5 to export the evidence to JSON.
   7. Attach tic_results.json to your incident report.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 NOTES & LIMITATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 • This tool is for defensive / investigative purposes only.
 • Always respect each API's rate limits and terms of service.
 • AbuseIPDB free tier: do not submit private / RFC-1918 IPs.
 • VirusTotal free tier: max 4 requests per minute.
 • The tool does NOT submit anything to VirusTotal for scanning;
   it only reads existing analysis results.
 • DNS resolution uses Cloudflare's public DoH endpoint
   (https://cloudflare-dns.com/dns-query) – no data is stored.

"""

import sys
import json
import time
import hashlib
import ipaddress
import re
import os
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

# ── graceful import of requests ──────────────────────────────────
try:
    import requests
except ImportError:
    print("[FATAL] 'requests' is not installed.  Run: pip install requests")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
#  CONFIGURATION  (edit these or set as environment variables)
# ─────────────────────────────────────────────────────────────────

CONFIG = {
    # Paste your real keys here, or leave empty to use simulated data
    "ABUSEIPDB_KEY":  os.environ.get("ABUSEIPDB_KEY",  ""),
    "VIRUSTOTAL_KEY": os.environ.get("VIRUSTOTAL_KEY", ""),
    "IPINFO_TOKEN":   os.environ.get("IPINFO_TOKEN",   ""),   # optional

    "REQUEST_TIMEOUT":   10,      # seconds
    "CACHE_FILE":        "tic_cache.json",
    "RESULTS_FILE":      "tic_results.json",
    "CACHE_TTL_SECONDS": 3600,    # 1 hour
}

# ─────────────────────────────────────────────────────────────────
#  COLOUR HELPERS
# ─────────────────────────────────────────────────────────────────

class C:
    """ANSI colour codes – disabled automatically on Windows if needed."""
    _on = sys.platform != "win32" or os.environ.get("FORCE_COLOR")
    RED    = "\033[91m" if _on else ""
    YELLOW = "\033[93m" if _on else ""
    GREEN  = "\033[92m" if _on else ""
    CYAN   = "\033[96m" if _on else ""
    BOLD   = "\033[1m"  if _on else ""
    DIM    = "\033[2m"  if _on else ""
    RESET  = "\033[0m"  if _on else ""

def risk_colour(level: str) -> str:
    return {
        "HIGH":   C.RED,
        "MEDIUM": C.YELLOW,
        "LOW":    C.GREEN,
    }.get(level.upper(), C.RESET)

def banner():
    print(f"""
{C.CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════════╗
║         THREAT INTELLIGENCE COLLECTOR  v1.0                      ║
║         AbuseIPDB · VirusTotal · IPinfo                          ║
╚══════════════════════════════════════════════════════════════════╝
{C.RESET}""")

# ─────────────────────────────────────────────────────────────────
#  CACHE LAYER
# ─────────────────────────────────────────────────────────────────

class Cache:
    """Simple JSON-file-backed cache with TTL."""

    def __init__(self, path: str, ttl: int):
        self.path = path
        self.ttl  = ttl
        self._data: dict = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r") as fh:
                self._data = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {}

    def _save(self):
        with open(self.path, "w") as fh:
            json.dump(self._data, fh, indent=2)

    def _key(self, namespace: str, target: str) -> str:
        raw = f"{namespace}:{target.lower()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, namespace: str, target: str) -> Optional[dict]:
        k = self._key(namespace, target)
        entry = self._data.get(k)
        if entry is None:
            return None
        age = time.time() - entry["ts"]
        if age > self.ttl:
            del self._data[k]
            self._save()
            return None
        return entry["payload"]

    def set(self, namespace: str, target: str, payload: dict):
        k = self._key(namespace, target)
        self._data[k] = {"ts": time.time(), "payload": payload}
        self._save()


_cache = Cache(CONFIG["CACHE_FILE"], CONFIG["CACHE_TTL_SECONDS"])

# ─────────────────────────────────────────────────────────────────
#  VALIDATION HELPERS
# ─────────────────────────────────────────────────────────────────

def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

def is_valid_domain(value: str) -> bool:
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, value))

def is_valid_url(value: str) -> bool:
    try:
        result = urlparse(value)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────────
#  SIMULATED DATA  (used when no API key is configured)
# ─────────────────────────────────────────────────────────────────

def _simulated_abuseipdb(ip: str) -> dict:
    """Return plausible-looking simulated AbuseIPDB data."""
    seed = sum(ord(c) for c in ip) % 100
    return {
        "source":        "AbuseIPDB (simulated)",
        "ip":            ip,
        "abuse_score":   seed,
        "total_reports": seed // 5,
        "last_reported": "2024-11-01T12:00:00+00:00" if seed > 10 else None,
        "usage_type":    "Data Center/Web Hosting/Transit" if seed > 40 else "ISP",
        "isp":           "Simulated ISP Corp",
        "domain":        "simulated-isp.example",
        "country_code":  "US",
        "simulated":     True,
    }

def _simulated_virustotal_ip(ip: str) -> dict:
    seed = sum(ord(c) for c in ip) % 100
    return {
        "source":     "VirusTotal (simulated)",
        "ip":         ip,
        "malicious":  seed // 15,
        "suspicious": seed // 25,
        "harmless":   max(0, 20 - seed // 10),
        "undetected": 50,
        "network":    "203.0.113.0/24",
        "country":    "US",
        "simulated":  True,
    }

def _simulated_virustotal_domain(domain: str) -> dict:
    seed = sum(ord(c) for c in domain) % 100
    return {
        "source":       "VirusTotal (simulated)",
        "domain":       domain,
        "malicious":    seed // 20,
        "suspicious":   seed // 30,
        "harmless":     max(0, 20 - seed // 10),
        "undetected":   50,
        "reputation":   -(seed // 10),
        "categories":   {"Forcepoint ThreatSeeker": "information technology"},
        "simulated":    True,
    }

def _simulated_ipinfo(ip: str) -> dict:
    return {
        "source":    "IPinfo (simulated)",
        "ip":        ip,
        "city":      "Ashburn",
        "region":    "Virginia",
        "country":   "US",
        "org":       "AS14618 Amazon.com, Inc.",
        "timezone":  "America/New_York",
        "simulated": True,
    }

# ─────────────────────────────────────────────────────────────────
#  API CLIENTS
# ─────────────────────────────────────────────────────────────────

def _get(url: str, headers: dict = None, params: dict = None) -> Optional[dict]:
    """Wrapper around requests.get with error handling."""
    try:
        resp = requests.get(
            url,
            headers=headers or {},
            params=params or {},
            timeout=CONFIG["REQUEST_TIMEOUT"],
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        print(f"  {C.YELLOW}[WARN] Request timed out: {url}{C.RESET}")
    except requests.exceptions.HTTPError as exc:
        print(f"  {C.YELLOW}[WARN] HTTP {exc.response.status_code} from {url}{C.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"  {C.YELLOW}[WARN] Connection error reaching {url}{C.RESET}")
    except Exception as exc:
        print(f"  {C.YELLOW}[WARN] Unexpected error: {exc}{C.RESET}")
    return None


# ── AbuseIPDB ────────────────────────────────────────────────────

def fetch_abuseipdb(ip: str) -> dict:
    cached = _cache.get("abuseipdb", ip)
    if cached:
        return cached

    key = CONFIG["ABUSEIPDB_KEY"]
    if not key:
        result = _simulated_abuseipdb(ip)
        _cache.set("abuseipdb", ip, result)
        return result

    url  = "https://api.abuseipdb.com/api/v2/check"
    data = _get(url,
                headers={"Key": key, "Accept": "application/json"},
                params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": True})

    if data and "data" in data:
        d = data["data"]
        result = {
            "source":        "AbuseIPDB",
            "ip":            ip,
            "abuse_score":   d.get("abuseConfidenceScore", 0),
            "total_reports": d.get("totalReports", 0),
            "last_reported": d.get("lastReportedAt"),
            "usage_type":    d.get("usageType", "Unknown"),
            "isp":           d.get("isp", "Unknown"),
            "domain":        d.get("domain", "Unknown"),
            "country_code":  d.get("countryCode", "??"),
            "simulated":     False,
        }
    else:
        result = _simulated_abuseipdb(ip)

    _cache.set("abuseipdb", ip, result)
    return result


# ── VirusTotal ───────────────────────────────────────────────────

def fetch_virustotal_ip(ip: str) -> dict:
    cached = _cache.get("vt_ip", ip)
    if cached:
        return cached

    key = CONFIG["VIRUSTOTAL_KEY"]
    if not key:
        result = _simulated_virustotal_ip(ip)
        _cache.set("vt_ip", ip, result)
        return result

    url  = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    data = _get(url, headers={"x-apikey": key})

    if data and "data" in data:
        stats = data["data"]["attributes"].get("last_analysis_stats", {})
        attrs = data["data"]["attributes"]
        result = {
            "source":     "VirusTotal",
            "ip":         ip,
            "malicious":  stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless":   stats.get("harmless", 0),
            "undetected": stats.get("undetected", 0),
            "network":    attrs.get("network", "Unknown"),
            "country":    attrs.get("country", "??"),
            "simulated":  False,
        }
    else:
        result = _simulated_virustotal_ip(ip)

    _cache.set("vt_ip", ip, result)
    return result


def fetch_virustotal_domain(domain: str) -> dict:
    cached = _cache.get("vt_domain", domain)
    if cached:
        return cached

    key = CONFIG["VIRUSTOTAL_KEY"]
    if not key:
        result = _simulated_virustotal_domain(domain)
        _cache.set("vt_domain", domain, result)
        return result

    url  = f"https://www.virustotal.com/api/v3/domains/{domain}"
    data = _get(url, headers={"x-apikey": key})

    if data and "data" in data:
        stats = data["data"]["attributes"].get("last_analysis_stats", {})
        attrs = data["data"]["attributes"]
        result = {
            "source":     "VirusTotal",
            "domain":     domain,
            "malicious":  stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless":   stats.get("harmless", 0),
            "undetected": stats.get("undetected", 0),
            "reputation": attrs.get("reputation", 0),
            "categories": attrs.get("categories", {}),
            "simulated":  False,
        }
    else:
        result = _simulated_virustotal_domain(domain)

    _cache.set("vt_domain", domain, result)
    return result


# ── IPinfo ───────────────────────────────────────────────────────

def fetch_ipinfo(ip: str) -> dict:
    cached = _cache.get("ipinfo", ip)
    if cached:
        return cached

    token = CONFIG["IPINFO_TOKEN"]
    url   = f"https://ipinfo.io/{ip}/json"
    data  = _get(url, params={"token": token} if token else {})

    if data and "ip" in data:
        result = {
            "source":    "IPinfo",
            "ip":        ip,
            "city":      data.get("city", "Unknown"),
            "region":    data.get("region", "Unknown"),
            "country":   data.get("country", "??"),
            "org":       data.get("org", "Unknown"),
            "timezone":  data.get("timezone", "Unknown"),
            "simulated": False,
        }
    else:
        result = _simulated_ipinfo(ip)

    _cache.set("ipinfo", ip, result)
    return result

# ─────────────────────────────────────────────────────────────────
#  RISK SCORING ENGINE
# ─────────────────────────────────────────────────────────────────

def compute_risk_ip(abuse: dict, vt: dict) -> tuple[str, int, list[str]]:
    """
    Returns (risk_level, composite_score_0_100, [finding strings]).
    Weights: AbuseIPDB 50 %, VirusTotal 50 %.
    """
    findings = []

    # AbuseIPDB contribution (0-100)
    abuse_score  = abuse.get("abuse_score", 0)
    vt_malicious = vt.get("malicious", 0)
    vt_total     = (vt_malicious
                    + vt.get("suspicious", 0)
                    + vt.get("harmless", 0)
                    + vt.get("undetected", 0))
    vt_score = int((vt_malicious / vt_total) * 100) if vt_total else 0

    composite = int(abuse_score * 0.5 + vt_score * 0.5)

    if abuse_score > 0:
        findings.append(f"AbuseIPDB confidence score: {abuse_score}%")
    if abuse.get("total_reports", 0) > 0:
        findings.append(f"Total abuse reports: {abuse['total_reports']}")
    if abuse.get("last_reported"):
        findings.append(f"Last reported: {abuse['last_reported']}")
    if vt_malicious > 0:
        findings.append(f"VirusTotal malicious detections: {vt_malicious}/{vt_total}")
    if vt.get("suspicious", 0) > 0:
        findings.append(f"VirusTotal suspicious detections: {vt['suspicious']}/{vt_total}")

    isp = abuse.get("isp") or vt.get("org", "")
    if isp:
        findings.append(f"ISP / Org: {isp}")
    country = abuse.get("country_code") or vt.get("country", "")
    if country:
        findings.append(f"Country: {country}")

    if composite >= 60:
        level = "HIGH"
    elif composite >= 20:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not findings:
        findings.append("No significant threat indicators found.")

    return level, composite, findings


def compute_risk_domain(vt: dict) -> tuple[str, int, list[str]]:
    """Domain-only risk calculation via VirusTotal."""
    findings = []

    vt_malicious = vt.get("malicious", 0)
    vt_total     = (vt_malicious
                    + vt.get("suspicious", 0)
                    + vt.get("harmless", 0)
                    + vt.get("undetected", 0))
    vt_score = int((vt_malicious / vt_total) * 100) if vt_total else 0

    reputation = vt.get("reputation", 0)
    # Normalise negative reputation into 0-100 threat score (cap at -50 → 100)
    rep_score  = min(100, max(0, -reputation * 2))
    composite  = int(vt_score * 0.7 + rep_score * 0.3)

    if vt_malicious > 0:
        findings.append(f"VirusTotal malicious detections: {vt_malicious}/{vt_total}")
    if vt.get("suspicious", 0) > 0:
        findings.append(f"VirusTotal suspicious detections: {vt['suspicious']}/{vt_total}")
    if reputation < 0:
        findings.append(f"VirusTotal reputation score: {reputation} (negative = suspicious)")
    cats = vt.get("categories", {})
    if cats:
        cat_str = ", ".join(set(cats.values()))
        findings.append(f"Categories: {cat_str}")

    if composite >= 60:
        level = "HIGH"
    elif composite >= 20:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not findings:
        findings.append("No significant threat indicators found.")

    return level, composite, findings

# ─────────────────────────────────────────────────────────────────
#  DISPLAY / REPORTING
# ─────────────────────────────────────────────────────────────────

SEP = "─" * 66

def _sim_notice(is_simulated: bool) -> str:
    if is_simulated:
        return f"  {C.DIM}(no API key – simulated data){C.RESET}"
    return ""

def print_ip_report(ip: str, abuse: dict, vt: dict, geo: dict):
    level, score, findings = compute_risk_ip(abuse, vt)
    colour = risk_colour(level)

    print(f"\n{C.BOLD}{SEP}{C.RESET}")
    print(f"  IP ANALYSIS REPORT  ·  {ip}")
    print(f"  Timestamp : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{SEP}")

    # Risk badge
    print(f"  Risk Level    : {colour}{C.BOLD}{level}{C.RESET}  (composite score: {score}/100)")
    print()

    # Geo info
    print(f"  {C.BOLD}── Geolocation (IPinfo){_sim_notice(geo.get('simulated', False))}:{C.RESET}")
    print(f"     City    : {geo.get('city', 'N/A')}, {geo.get('region', 'N/A')}")
    print(f"     Country : {geo.get('country', 'N/A')}")
    print(f"     Org/ASN : {geo.get('org', 'N/A')}")
    print(f"     TZ      : {geo.get('timezone', 'N/A')}")
    print()

    # AbuseIPDB
    print(f"  {C.BOLD}── AbuseIPDB{_sim_notice(abuse.get('simulated', False))}:{C.RESET}")
    ab_score = abuse.get("abuse_score", 0)
    ab_col   = C.RED if ab_score > 60 else (C.YELLOW if ab_score > 20 else C.GREEN)
    print(f"     Confidence Score : {ab_col}{ab_score}%{C.RESET}")
    print(f"     Total Reports    : {abuse.get('total_reports', 0)}")
    print(f"     Last Reported    : {abuse.get('last_reported', 'Never')}")
    print(f"     ISP              : {abuse.get('isp', 'N/A')}")
    print(f"     Usage Type       : {abuse.get('usage_type', 'N/A')}")
    print(f"     Country          : {abuse.get('country_code', '??')}")
    print()

    # VirusTotal
    print(f"  {C.BOLD}── VirusTotal{_sim_notice(vt.get('simulated', False))}:{C.RESET}")
    mal = vt.get("malicious", 0)
    sus = vt.get("suspicious", 0)
    hrm = vt.get("harmless", 0)
    unc = vt.get("undetected", 0)
    mal_col = C.RED if mal > 5 else (C.YELLOW if mal > 0 else C.GREEN)
    print(f"     Malicious   : {mal_col}{mal}{C.RESET}")
    print(f"     Suspicious  : {sus}")
    print(f"     Harmless    : {hrm}")
    print(f"     Undetected  : {unc}")
    print(f"     Network     : {vt.get('network', 'N/A')}")
    print()

    # Key findings
    print(f"  {C.BOLD}── Key Findings:{C.RESET}")
    for f in findings:
        print(f"     • {f}")

    print(f"{SEP}\n")
    return level, score, findings


def print_domain_report(domain: str, vt: dict):
    level, score, findings = compute_risk_domain(vt)
    colour = risk_colour(level)

    print(f"\n{C.BOLD}{SEP}{C.RESET}")
    print(f"  DOMAIN ANALYSIS REPORT  ·  {domain}")
    print(f"  Timestamp : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{SEP}")

    print(f"  Risk Level : {colour}{C.BOLD}{level}{C.RESET}  (composite score: {score}/100)")
    print()

    print(f"  {C.BOLD}── VirusTotal{_sim_notice(vt.get('simulated', False))}:{C.RESET}")
    mal = vt.get("malicious", 0)
    sus = vt.get("suspicious", 0)
    hrm = vt.get("harmless", 0)
    unc = vt.get("undetected", 0)
    mal_col = C.RED if mal > 5 else (C.YELLOW if mal > 0 else C.GREEN)
    print(f"     Malicious   : {mal_col}{mal}{C.RESET}")
    print(f"     Suspicious  : {sus}")
    print(f"     Harmless    : {hrm}")
    print(f"     Undetected  : {unc}")
    print(f"     Reputation  : {vt.get('reputation', 'N/A')}")
    cats = vt.get("categories", {})
    if cats:
        print(f"     Categories  : {', '.join(set(cats.values()))}")
    print()

    print(f"  {C.BOLD}── Key Findings:{C.RESET}")
    for f in findings:
        print(f"     • {f}")

    print(f"{SEP}\n")
    return level, score, findings

# ─────────────────────────────────────────────────────────────────
#  SESSION RESULTS STORE
# ─────────────────────────────────────────────────────────────────

_session_results: list[dict] = []

def store_result(target: str, target_type: str, risk_level: str,
                 score: int, findings: list[str], raw: dict):
    _session_results.append({
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "target":      target,
        "type":        target_type,
        "risk_level":  risk_level,
        "score":       score,
        "findings":    findings,
        "raw_data":    raw,
    })


def print_summary():
    if not _session_results:
        print(f"\n  {C.YELLOW}No analyses performed in this session.{C.RESET}\n")
        return

    print(f"\n{C.BOLD}{SEP}{C.RESET}")
    print(f"  SESSION SUMMARY  ({len(_session_results)} item(s) analysed)")
    print(SEP)
    for i, r in enumerate(_session_results, 1):
        colour = risk_colour(r["risk_level"])
        sim_tag = ""
        for src in r["raw_data"].values():
            if isinstance(src, dict) and src.get("simulated"):
                sim_tag = f" {C.DIM}[sim]{C.RESET}"
                break
        print(f"  {i:>2}. [{r['type'].upper():>6}]  {r['target']:<40} "
              f"{colour}{r['risk_level']:>6}{C.RESET}  (score {r['score']:>3}/100){sim_tag}")
    print(SEP)
    highs   = sum(1 for r in _session_results if r["risk_level"] == "HIGH")
    mediums = sum(1 for r in _session_results if r["risk_level"] == "MEDIUM")
    lows    = sum(1 for r in _session_results if r["risk_level"] == "LOW")
    print(f"\n  {C.RED}HIGH: {highs}{C.RESET}   "
          f"{C.YELLOW}MEDIUM: {mediums}{C.RESET}   "
          f"{C.GREEN}LOW: {lows}{C.RESET}\n")


def export_results():
    if not _session_results:
        print(f"\n  {C.YELLOW}Nothing to export.{C.RESET}\n")
        return
    path = CONFIG["RESULTS_FILE"]
    with open(path, "w") as fh:
        json.dump(_session_results, fh, indent=2, default=str)
    print(f"\n  {C.GREEN}Results exported → {os.path.abspath(path)}{C.RESET}\n")

# ─────────────────────────────────────────────────────────────────
#  ACTION HANDLERS
# ─────────────────────────────────────────────────────────────────

def action_analyse_ip():
    ip = input("  Enter IP address: ").strip()
    if not is_valid_ip(ip):
        print(f"  {C.RED}Invalid IP address.{C.RESET}")
        return

    print(f"\n  {C.CYAN}Querying AbuseIPDB …{C.RESET}")
    abuse = fetch_abuseipdb(ip)
    print(f"  {C.CYAN}Querying VirusTotal …{C.RESET}")
    vt    = fetch_virustotal_ip(ip)
    print(f"  {C.CYAN}Querying IPinfo …{C.RESET}")
    geo   = fetch_ipinfo(ip)

    level, score, findings = print_ip_report(ip, abuse, vt, geo)
    store_result(ip, "ip", level, score, findings,
                 {"abuseipdb": abuse, "virustotal": vt, "ipinfo": geo})


def action_analyse_domain():
    domain = input("  Enter domain (e.g. example.com): ").strip().lower()
    # strip scheme if user typed a URL
    if domain.startswith(("http://", "https://")):
        domain = urlparse(domain).netloc

    if not is_valid_domain(domain):
        print(f"  {C.RED}Invalid domain name.{C.RESET}")
        return

    print(f"\n  {C.CYAN}Querying VirusTotal …{C.RESET}")
    vt = fetch_virustotal_domain(domain)

    level, score, findings = print_domain_report(domain, vt)
    store_result(domain, "domain", level, score, findings, {"virustotal": vt})


def action_analyse_url():
    raw = input("  Enter full URL (https://...): ").strip()
    if not is_valid_url(raw):
        print(f"  {C.RED}Invalid URL.  Must start with http:// or https://{C.RESET}")
        return

    parsed = urlparse(raw)
    domain = parsed.netloc
    print(f"\n  {C.DIM}Extracted domain: {domain}{C.RESET}")

    # Resolve IP via a lightweight DNS-over-HTTPS lookup (Cloudflare)
    ip = None
    try:
        resp = requests.get(
            "https://cloudflare-dns.com/dns-query",
            headers={"Accept": "application/dns-json"},
            params={"name": domain, "type": "A"},
            timeout=CONFIG["REQUEST_TIMEOUT"],
        )
        resp.raise_for_status()
        answers = resp.json().get("Answer", [])
        # Filter for A records (type 1) and pick first
        a_records = [a["data"] for a in answers if a.get("type") == 1]
        if a_records:
            ip = a_records[0]
            print(f"  {C.DIM}Resolved IP: {ip}{C.RESET}")
    except Exception:
        pass  # DNS lookup failure is non-fatal

    print(f"\n  {C.CYAN}Querying VirusTotal for domain …{C.RESET}")
    vt_domain = fetch_virustotal_domain(domain)
    d_level, d_score, d_findings = print_domain_report(domain, vt_domain)
    store_result(domain, "domain", d_level, d_score, d_findings,
                 {"virustotal": vt_domain})

    if ip:
        print(f"\n  {C.CYAN}Analysing resolved IP {ip} …{C.RESET}")
        abuse = fetch_abuseipdb(ip)
        vt_ip = fetch_virustotal_ip(ip)
        geo   = fetch_ipinfo(ip)
        i_level, i_score, i_findings = print_ip_report(ip, abuse, vt_ip, geo)
        store_result(ip, "ip", i_level, i_score, i_findings,
                     {"abuseipdb": abuse, "virustotal": vt_ip, "ipinfo": geo})


def action_configure_keys():
    print(f"""
  {C.BOLD}── API Key Configuration ──{C.RESET}
  Press Enter to keep the current value.

  Current key status:
    AbuseIPDB  : {'✓ set' if CONFIG['ABUSEIPDB_KEY']  else '✗ not set (simulated)'}
    VirusTotal : {'✓ set' if CONFIG['VIRUSTOTAL_KEY'] else '✗ not set (simulated)'}
    IPinfo     : {'✓ set' if CONFIG['IPINFO_TOKEN']   else '✗ not set (free tier)'}
""")
    for field, label in [
        ("ABUSEIPDB_KEY",  "AbuseIPDB key"),
        ("VIRUSTOTAL_KEY", "VirusTotal key"),
        ("IPINFO_TOKEN",   "IPinfo token (optional)"),
    ]:
        val = input(f"  {label}: ").strip()
        if val:
            CONFIG[field] = val
            print(f"  {C.GREEN}✓ {label} updated.{C.RESET}")
    print()

# ─────────────────────────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────────────────────────

MENU = [
    ("Analyse an IP address",           action_analyse_ip),
    ("Analyse a domain",                action_analyse_domain),
    ("Analyse a URL (domain + IP)",     action_analyse_url),
    ("View session summary",            print_summary),
    ("Export results to JSON",          export_results),
    ("Configure API keys",              action_configure_keys),
    ("Exit",                            None),
]


def print_menu():
    print(f"\n{C.BOLD}  Main Menu{C.RESET}")
    print(f"  {SEP[:40]}")
    for idx, (label, _) in enumerate(MENU, 1):
        print(f"  {C.CYAN}{idx}{C.RESET}.  {label}")
    print()


def main():
    banner()

    # Warn if no keys are set
    if not any([CONFIG["ABUSEIPDB_KEY"], CONFIG["VIRUSTOTAL_KEY"]]):
        print(f"  {C.YELLOW}[INFO] No API keys configured – running in simulation mode.")
        print(f"         Select option 6 to add your real keys.{C.RESET}\n")

    while True:
        print_menu()
        try:
            choice = input("  Select option [1-7]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {C.DIM}Interrupted. Goodbye!{C.RESET}\n")
            break

        if not choice.isdigit() or not (1 <= int(choice) <= len(MENU)):
            print(f"  {C.RED}Invalid choice. Enter a number between 1 and {len(MENU)}.{C.RESET}")
            continue

        idx = int(choice) - 1
        label, fn = MENU[idx]

        if fn is None:          # Exit
            print(f"\n  {C.DIM}Goodbye!{C.RESET}\n")
            break

        print(f"\n  {C.BOLD}» {label}{C.RESET}")
        fn()


# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()