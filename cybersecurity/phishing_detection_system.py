"""
Phishing Detection System
=========================
Analyzes emails and URLs for phishing indicators using heuristic rules.
Built with OOP principles: encapsulation, single-responsibility, clean APIs.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Enums & lightweight value objects
# ─────────────────────────────────────────────────────────────────────────────

class RiskLevel(Enum):
    SAFE       = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    PHISHING   = "PHISHING"

    # Convenience: order by severity
    def __lt__(self, other: RiskLevel) -> bool:
        order = [RiskLevel.SAFE, RiskLevel.SUSPICIOUS, RiskLevel.PHISHING]
        return order.index(self) < order.index(other)


@dataclass(frozen=True)
class RiskFlag:
    """A single detected risk indicator."""
    code:        str   # short machine-readable key
    description: str   # human-readable explanation
    severity:    int   # 1 = low, 2 = medium, 3 = high


# ─────────────────────────────────────────────────────────────────────────────
#  Message  – encapsulated data holder
# ─────────────────────────────────────────────────────────────────────────────

class Message:
    """
    Represents an email or URL submission to be analysed.

    Attributes are private; access is via read-only properties so that
    the object cannot be mutated after construction.
    """

    def __init__(
        self,
        *,
        sender:  str = "",
        subject: str = "",
        content: str = "",
        links:   list[str] | None = None,
    ) -> None:
        self._sender:  str       = sender.strip()
        self._subject: str       = subject.strip()
        self._content: str       = content.strip()
        self._links:   list[str] = [lnk.strip() for lnk in (links or []) if lnk.strip()]
        self._submitted_at: datetime = datetime.now()

    # ── read-only properties ──────────────────
    @property
    def sender(self) -> str:        return self._sender
    @property
    def subject(self) -> str:       return self._subject
    @property
    def content(self) -> str:       return self._content
    @property
    def links(self) -> list[str]:   return list(self._links)   # defensive copy
    @property
    def submitted_at(self) -> datetime: return self._submitted_at

    def is_url_only(self) -> bool:
        """True when the submission is a bare URL (no email fields)."""
        return bool(not self._sender and not self._subject and not self._content
                    and self._links)

    def full_text(self) -> str:
        """Concatenation of all textual fields for keyword scanning."""
        return " ".join(filter(None, [self._sender, self._subject, self._content]))

    def __repr__(self) -> str:
        return (
            f"Message(sender={self._sender!r}, subject={self._subject!r}, "
            f"links={len(self._links)})"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  AnalysisResult  – immutable result object returned by PhishingDetector
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AnalysisResult:
    message:    Message
    risk_level: RiskLevel
    score:      int
    flags:      tuple[RiskFlag, ...]
    analysed_at: datetime = field(default_factory=datetime.now)

    def summary(self) -> str:
        lines = [
            f"  Risk level : {self.risk_level.value}",
            f"  Score      : {self.score}",
            f"  Flags ({len(self.flags)}):",
        ]
        if self.flags:
            for f_ in self.flags:
                sev_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(f_.severity, "?")
                lines.append(f"    [{sev_label}] {f_.description}")
        else:
            lines.append("    None – no suspicious indicators found.")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  PhishingDetector  – all heuristic analysis logic
# ─────────────────────────────────────────────────────────────────────────────

class PhishingDetector:
    """
    Analyses a Message using configurable heuristic rule-sets.

    Score thresholds:
        0–4   → SAFE
        5–9   → SUSPICIOUS
        10+   → PHISHING
    """

    SAFE_THRESHOLD       = 4   # score >= 4 → SUSPICIOUS
    PHISHING_THRESHOLD   = 10

    # ── known URL shorteners ──────────────────
    _URL_SHORTENERS: frozenset[str] = frozenset({
        "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
        "buff.ly", "rebrand.ly", "cutt.ly", "tiny.cc", "rb.gy", "shorturl.at",
    })

    # ── suspicious TLDs ──────────────────────
    _SUSPICIOUS_TLDS: frozenset[str] = frozenset({
        ".xyz", ".top", ".club", ".icu", ".tk", ".ml", ".ga", ".cf",
        ".gq", ".pw", ".work", ".click", ".link", ".buzz",
    })

    # ── phishing keyword groups ───────────────
    _URGENT_KEYWORDS: list[str] = [
        "urgent", "immediately", "act now", "account suspended",
        "verify now", "limited time", "expires today", "last chance",
        "your account will be", "failure to verify",
    ]
    _SENSITIVE_KEYWORDS: list[str] = [
        "password", "social security", "ssn", "credit card", "bank account",
        "confirm your identity", "update your payment", "billing information",
        "enter your pin", "full name and date of birth", "mother's maiden name",
    ]
    _IMPERSONATION_KEYWORDS: list[str] = [
        "paypal", "amazon", "apple", "microsoft", "google", "irs", "ssa",
        "netflix", "bank of america", "chase bank", "wells fargo",
        "facebook", "instagram", "whatsapp",
    ]
    _DECEPTIVE_PHRASES: list[str] = [
        "click here to", "login to verify", "verify your account",
        "your account has been", "we noticed unusual activity",
        "confirm your account", "update required", "you have won",
        "congratulations you", "free gift", "wire transfer",
    ]

    # ── public API ────────────────────────────

    def analyse(self, message: Message) -> AnalysisResult:
        """Run all heuristic checks and return an AnalysisResult."""
        flags: list[RiskFlag] = []

        flags.extend(self._check_sender(message))
        flags.extend(self._check_subject(message))
        flags.extend(self._check_content_keywords(message))
        flags.extend(self._check_links(message))

        score = sum(f.severity for f in flags)
        risk  = self._classify(score)

        return AnalysisResult(
            message=message,
            risk_level=risk,
            score=score,
            flags=tuple(flags),
        )

    # ── private rule methods ──────────────────

    def _check_sender(self, msg: Message) -> list[RiskFlag]:
        flags: list[RiskFlag] = []
        sender = msg.sender.lower()
        if not sender:
            return flags

        # Suspicious characters / obfuscation in sender
        if re.search(r"[0-9]{4,}", sender):
            flags.append(RiskFlag(
                "SENDER_NUMERIC",
                f"Sender address contains a long numeric sequence: '{msg.sender}'",
                severity=1,
            ))

        # Domain impersonation via hyphens (e.g. paypal-security.com)
        domain_match = re.search(r"@([\w\.\-]+)", sender)
        if domain_match:
            domain = domain_match.group(1)
            for brand in self._IMPERSONATION_KEYWORDS:
                if brand in domain and not domain.endswith(f"{brand}.com"):
                    flags.append(RiskFlag(
                        "SENDER_IMPERSONATION",
                        f"Sender domain may impersonate '{brand}': '{domain}'",
                        severity=3,
                    ))
                    break

        # Free email providers used for corporate-sounding subjects
        free_providers = ("gmail.com", "yahoo.com", "hotmail.com",
                          "outlook.com", "protonmail.com", "aol.com")
        subject_lower  = msg.subject.lower()
        if any(sender.endswith(p) for p in free_providers):
            if any(brand in subject_lower for brand in self._IMPERSONATION_KEYWORDS):
                flags.append(RiskFlag(
                    "SENDER_FREE_BRAND_MISMATCH",
                    "Corporate brand claimed in subject but sender uses a free email provider.",
                    severity=2,
                ))

        return flags

    def _check_subject(self, msg: Message) -> list[RiskFlag]:
        flags: list[RiskFlag] = []
        subject = msg.subject.lower()
        if not subject:
            return flags

        if any(kw in subject for kw in self._URGENT_KEYWORDS):
            matched = [kw for kw in self._URGENT_KEYWORDS if kw in subject]
            flags.append(RiskFlag(
                "SUBJECT_URGENCY",
                f"Subject uses urgency tactics: {matched}",
                severity=2,
            ))

        # ALL-CAPS words (screaming urgency)
        caps_words = re.findall(r'\b[A-Z]{3,}\b', msg.subject)
        if len(caps_words) >= 2:
            flags.append(RiskFlag(
                "SUBJECT_CAPS",
                f"Subject contains multiple ALL-CAPS words: {caps_words}",
                severity=1,
            ))

        # Excessive punctuation
        if re.search(r'[!?]{2,}', msg.subject):
            flags.append(RiskFlag(
                "SUBJECT_PUNCTUATION",
                "Subject contains excessive punctuation (!! or ??).",
                severity=1,
            ))

        return flags

    def _check_content_keywords(self, msg: Message) -> list[RiskFlag]:
        flags: list[RiskFlag] = []
        text = msg.full_text().lower()
        if not text:
            return flags

        # Sensitive info requests
        sensitive_hits = [kw for kw in self._SENSITIVE_KEYWORDS if kw in text]
        if sensitive_hits:
            flags.append(RiskFlag(
                "SENSITIVE_INFO_REQUEST",
                f"Requests sensitive information: {sensitive_hits}",
                severity=3,
            ))

        # Deceptive phrases
        deceptive_hits = [ph for ph in self._DECEPTIVE_PHRASES if ph in text]
        if deceptive_hits:
            flags.append(RiskFlag(
                "DECEPTIVE_PHRASES",
                f"Contains deceptive / manipulative phrases: {deceptive_hits}",
                severity=2,
            ))

        # Urgency in body
        urgent_hits = [kw for kw in self._URGENT_KEYWORDS if kw in text]
        if urgent_hits:
            flags.append(RiskFlag(
                "CONTENT_URGENCY",
                f"Body text uses urgency language: {urgent_hits}",
                severity=2,
            ))

        # Brand impersonation in body
        brand_hits = [b for b in self._IMPERSONATION_KEYWORDS if b in text]
        if brand_hits:
            flags.append(RiskFlag(
                "CONTENT_BRAND_MENTION",
                f"References known brand(s) that are frequently impersonated: {brand_hits}",
                severity=1,
            ))

        return flags

    def _check_links(self, msg: Message) -> list[RiskFlag]:
        flags: list[RiskFlag] = []
        links = msg.links
        if not links:
            return flags

        for url in links:
            flags.extend(self._analyse_url(url, msg))

        return flags

    def _analyse_url(self, url: str, msg: Message) -> list[RiskFlag]:
        flags: list[RiskFlag] = []
        url_lower = url.lower()

        # ── parse URL ────────────────────────
        try:
            parsed = urllib.parse.urlparse(url if "://" in url else "http://" + url)
            netloc = parsed.netloc.lower().lstrip("www.")
        except Exception:
            flags.append(RiskFlag(
                "URL_UNPARSEABLE",
                f"Could not parse URL: '{url}'",
                severity=2,
            ))
            return flags

        # No HTTPS
        if parsed.scheme and parsed.scheme != "https":
            flags.append(RiskFlag(
                "URL_NO_HTTPS",
                f"URL does not use HTTPS: '{url}'",
                severity=2,
            ))

        # URL shortener
        if any(netloc == s or netloc.endswith("." + s) for s in self._URL_SHORTENERS):
            flags.append(RiskFlag(
                "URL_SHORTENER",
                f"URL uses a shortening service (destination hidden): '{url}'",
                severity=2,
            ))

        # Suspicious TLD
        for tld in self._SUSPICIOUS_TLDS:
            if netloc.endswith(tld):
                flags.append(RiskFlag(
                    "URL_SUSPICIOUS_TLD",
                    f"URL uses a high-risk TLD '{tld}': '{url}'",
                    severity=2,
                ))
                break

        # IP address as host
        if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', netloc):
            flags.append(RiskFlag(
                "URL_IP_ADDRESS",
                f"URL uses a raw IP address instead of a domain: '{url}'",
                severity=3,
            ))

        # Excessive subdomains (e.g. paypal.com.evil.com)
        parts = netloc.split(".")
        if len(parts) >= 5:
            flags.append(RiskFlag(
                "URL_EXCESSIVE_SUBDOMAINS",
                f"URL has an unusually deep subdomain structure: '{netloc}'",
                severity=2,
            ))

        # Brand name in subdomain but different root domain
        for brand in self._IMPERSONATION_KEYWORDS:
            if brand in netloc:
                # Check if the *registered* domain matches the brand
                registered = ".".join(parts[-2:]) if len(parts) >= 2 else netloc
                if not registered.startswith(brand):
                    flags.append(RiskFlag(
                        "URL_DOMAIN_MISMATCH",
                        f"Brand '{brand}' appears in subdomain but root domain is '{registered}' — possible spoofing.",
                        severity=3,
                    ))
                    break

        # Encoded characters (obfuscation)
        if "%" in url and re.search(r'%[0-9A-Fa-f]{2}', url):
            flags.append(RiskFlag(
                "URL_ENCODED_CHARS",
                f"URL contains percent-encoded characters (possible obfuscation): '{url}'",
                severity=1,
            ))

        # Extremely long URL
        if len(url) > 150:
            flags.append(RiskFlag(
                "URL_EXCESSIVE_LENGTH",
                f"URL is unusually long ({len(url)} chars) — common in phishing.",
                severity=1,
            ))

        # Mismatch between display text domain and link domain (when possible)
        # Heuristic: if sender domain exists and differs from link domain
        sender_domain = ""
        if msg.sender and "@" in msg.sender:
            sender_domain = msg.sender.split("@")[-1].lower().lstrip("www.")
        if sender_domain and netloc and sender_domain != netloc:
            # Only flag if the sender is a known brand
            for brand in self._IMPERSONATION_KEYWORDS:
                if brand in sender_domain and brand not in netloc:
                    flags.append(RiskFlag(
                        "URL_SENDER_MISMATCH",
                        f"Link domain '{netloc}' doesn't match sender domain '{sender_domain}'.",
                        severity=3,
                    ))
                    break

        return flags

    # ── classification ────────────────────────

    def _classify(self, score: int) -> RiskLevel:
        if score >= self.PHISHING_THRESHOLD:
            return RiskLevel.PHISHING
        if score >= self.SAFE_THRESHOLD:
            return RiskLevel.SUSPICIOUS
        return RiskLevel.SAFE


# ─────────────────────────────────────────────────────────────────────────────
#  DetectionManager  – orchestration + history storage
# ─────────────────────────────────────────────────────────────────────────────

class DetectionManager:
    """
    Manages the end-to-end detection workflow and maintains analysis history.
    """

    def __init__(self) -> None:
        self._detector: PhishingDetector  = PhishingDetector()
        self._history:  list[AnalysisResult] = []

    # ── public API ────────────────────────────

    def analyse(self, message: Message) -> AnalysisResult:
        result = self._detector.analyse(message)
        self._history.append(result)
        return result

    @property
    def history(self) -> list[AnalysisResult]:
        return list(self._history)   # defensive copy

    def stats(self) -> dict[str, int]:
        counts: dict[str, int] = {level.value: 0 for level in RiskLevel}
        for r in self._history:
            counts[r.risk_level.value] += 1
        counts["TOTAL"] = len(self._history)
        return counts

    def clear_history(self) -> None:
        self._history.clear()


# ─────────────────────────────────────────────────────────────────────────────
#  CLI helpers
# ─────────────────────────────────────────────────────────────────────────────

BANNER = r"""
╔══════════════════════════════════════════════════╗
║        Phishing Detection System  v1.0           ║
║    Heuristic email & URL threat analyser         ║
╚══════════════════════════════════════════════════╝
"""

MENU = """
  [1] Analyse an email
  [2] Analyse a URL
  [3] View analysis history
  [4] View session statistics
  [5] Clear history
  [H] Help
  [Q] Quit
"""

RISK_COLOURS = {
    RiskLevel.SAFE:       "\033[92m",   # green
    RiskLevel.SUSPICIOUS: "\033[93m",   # yellow
    RiskLevel.PHISHING:   "\033[91m",   # red
}
RESET = "\033[0m"


def _colour(text: str, level: RiskLevel) -> str:
    return f"{RISK_COLOURS[level]}{text}{RESET}"


def _get_input(prompt: str, required: bool = True) -> str:
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("  ⚠  This field cannot be empty.")


def _get_choice(prompt: str, valid: set[str]) -> str:
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid:
            return choice
        print(f"  ⚠  Please enter one of: {', '.join(sorted(valid))}")


def _collect_links() -> list[str]:
    print("  Enter URLs/links found in the email (one per line).")
    print("  Leave blank and press Enter when finished.")
    links: list[str] = []
    idx = 1
    while True:
        raw = input(f"    Link {idx}: ").strip()
        if not raw:
            break
        links.append(raw)
        idx += 1
    return links


def _print_result(result: AnalysisResult) -> None:
    label = _colour(f"  ► {result.risk_level.value}", result.risk_level)
    print(f"\n{'─'*52}")
    print(label)
    print(result.summary())
    print(f"{'─'*52}\n")


# ── workflow actions ──────────────────────────────

def action_analyse_email(manager: DetectionManager) -> None:
    print("\n── Analyse Email ────────────────────────────────")
    sender  = _get_input("  Sender address  : ")
    subject = _get_input("  Subject line    : ")
    print("  Email body (paste text, end with a blank line):")
    lines: list[str] = []
    while True:
        line = input("    > ")
        if line == "":
            break
        lines.append(line)
    content = "\n".join(lines)
    links   = _collect_links()

    msg    = Message(sender=sender, subject=subject, content=content, links=links)
    result = manager.analyse(msg)
    _print_result(result)


def action_analyse_url(manager: DetectionManager) -> None:
    print("\n── Analyse URL ──────────────────────────────────")
    url = _get_input("  URL to analyse  : ")
    msg = Message(links=[url])
    result = manager.analyse(msg)
    _print_result(result)


def action_history(manager: DetectionManager) -> None:
    history = manager.history
    if not history:
        print("\n  No analyses recorded yet.\n")
        return

    print(f"\n── Analysis History ({len(history)} entries) ─────────────────")
    for i, result in enumerate(history, 1):
        msg   = result.message
        label = _colour(result.risk_level.value, result.risk_level)
        ts    = result.analysed_at.strftime("%H:%M:%S")
        if msg.is_url_only():
            desc = msg.links[0] if msg.links else "(URL)"
        else:
            desc = msg.subject or msg.sender or "(email)"
        print(f"  {i:>3}. [{ts}] {label:30s}  {desc[:50]}")
    print()


def action_stats(manager: DetectionManager) -> None:
    stats = manager.stats()
    print("\n── Session Statistics ───────────────────────────")
    print(f"  Total analysed : {stats['TOTAL']}")
    for level in RiskLevel:
        count = stats[level.value]
        bar   = "█" * count
        print(f"  {level.value:<12}: {count:>3}  {_colour(bar, level)}")
    print()


def action_clear(manager: DetectionManager) -> None:
    confirm = _get_choice("  Clear all history? [y/n]: ", {"y", "n"})
    if confirm == "y":
        manager.clear_history()
        print("  ✓ History cleared.\n")
    else:
        print("  Cancelled.\n")


HELP_TEXT = """
  ── How it works ─────────────────────────────────
  The detector runs heuristic checks across several
  categories:

  SENDER      – domain impersonation, free-provider
                mismatch, numeric obfuscation
  SUBJECT     – urgency language, ALL-CAPS, excessive
                punctuation
  CONTENT     – sensitive-info requests, deceptive
                phrases, urgency wording, brand mentions
  LINKS/URLS  – shorteners, suspicious TLDs, raw IP
                addresses, excessive subdomains,
                domain spoofing, encoded characters

  Each flag carries a severity (1–3).  The total
  score determines the verdict:
    0–4  → SAFE        (green)
    5–9  → SUSPICIOUS  (yellow)
    10+  → PHISHING    (red)
  ─────────────────────────────────────────────────
"""


def main() -> None:
    print(BANNER)
    manager = DetectionManager()

    while True:
        print(MENU)
        choice = _get_choice("  Your choice: ", {"1", "2", "3", "4", "5", "h", "q"})

        if choice == "1":
            action_analyse_email(manager)
        elif choice == "2":
            action_analyse_url(manager)
        elif choice == "3":
            action_history(manager)
        elif choice == "4":
            action_stats(manager)
        elif choice == "5":
            action_clear(manager)
        elif choice == "h":
            print(HELP_TEXT)
        elif choice == "q":
            print("\n  Stay safe online!  Goodbye. 👋\n")
            break


if __name__ == "__main__":
    main()