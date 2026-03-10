"""
Password Strength Checker
A modular, OOP-based system for evaluating password strength and providing
actionable improvement suggestions.
"""

import re
import string
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ──────────────────────────────────────────────
# Enums & Constants
# ──────────────────────────────────────────────

class StrengthLevel(Enum):
    """Password strength classification."""
    VERY_WEAK  = (0, "Very Weak",  "🔴")
    WEAK       = (1, "Weak",       "🟠")
    MEDIUM     = (2, "Medium",     "🟡")
    STRONG     = (3, "Strong",     "🟢")
    VERY_STRONG= (4, "Very Strong","✅")

    def __init__(self, score: int, label: str, icon: str) -> None:
        self.score = score
        self.label = label
        self.icon  = icon

    def __str__(self) -> str:
        return f"{self.icon}  {self.label}"


# Criteria identifiers used as dict keys throughout the program
class Criterion:
    MIN_LENGTH         = "min_length"
    GOOD_LENGTH        = "good_length"
    GREAT_LENGTH       = "great_length"
    HAS_UPPERCASE      = "has_uppercase"
    HAS_LOWERCASE      = "has_lowercase"
    HAS_DIGIT          = "has_digit"
    HAS_SPECIAL        = "has_special"
    NO_SPACES          = "no_spaces"
    NO_REPEATED_CHARS  = "no_repeated_chars"
    NO_COMMON_PATTERNS = "no_common_patterns"


# ──────────────────────────────────────────────
# Custom Exceptions
# ──────────────────────────────────────────────

class PasswordError(Exception):
    """Raised for invalid password inputs."""
    pass


# ──────────────────────────────────────────────
# CriteriaResult (immutable result per criterion)
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class CriteriaResult:
    """The outcome of evaluating a single password criterion."""
    key:        str
    passed:     bool
    label:      str                        # short human-readable name
    suggestion: Optional[str] = None       # shown only when failed


# ──────────────────────────────────────────────
# Password Class
# ──────────────────────────────────────────────

class Password:
    """
    Encapsulates a password value and exposes read-only derived attributes.

    Attributes (all read-only via properties):
        value   – the raw password string
        length  – number of characters
    """

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise PasswordError("Password must be a string.")
        if len(value) == 0:
            raise PasswordError("Password cannot be empty.")
        self.__value = value          # name-mangled for encapsulation

    # ── Properties ──────────────────────────────

    @property
    def value(self) -> str:
        return self.__value

    @property
    def length(self) -> int:
        return len(self.__value)

    # ── Convenience helpers ──────────────────────

    def has_uppercase(self) -> bool:
        return any(c.isupper() for c in self.__value)

    def has_lowercase(self) -> bool:
        return any(c.islower() for c in self.__value)

    def has_digit(self) -> bool:
        return any(c.isdigit() for c in self.__value)

    def has_special(self) -> bool:
        return any(c in string.punctuation for c in self.__value)

    def has_spaces(self) -> bool:
        return " " in self.__value

    def has_excessive_repeats(self, max_consecutive: int = 3) -> bool:
        """Return True if any character repeats more than max_consecutive times."""
        pattern = r"(.)\1{" + str(max_consecutive) + r",}"
        return bool(re.search(pattern, self.__value))

    def masked(self, visible: int = 2) -> str:
        """Return a partially masked version for safe display."""
        if self.length <= visible * 2:
            return "*" * self.length
        return self.__value[:visible] + "*" * (self.length - visible * 2) + self.__value[-visible:]

    def __len__(self) -> int:
        return self.length

    def __repr__(self) -> str:
        return f"Password(length={self.length}, masked='{self.masked()}')"


# ──────────────────────────────────────────────
# PasswordStrengthChecker Class
# ──────────────────────────────────────────────

class PasswordStrengthChecker:
    """
    Analyses a Password object against a configurable set of criteria
    and produces a StrengthReport.

    Configuration constants (class-level, easy to tune):
        MIN_LENGTH      – absolute minimum length (default 8)
        GOOD_LENGTH     – length for a "good length" bonus (default 12)
        GREAT_LENGTH    – length for a "great length" bonus (default 16)
    """

    MIN_LENGTH   = 8
    GOOD_LENGTH  = 12
    GREAT_LENGTH = 16

    # Common keyboard-walk / dictionary patterns to flag
    _COMMON_PATTERNS = [
        r"123\d*",          # sequential digits
        r"abc",             # sequential letters
        r"qwerty",          # keyboard walk
        r"asdf",
        r"zxcv",
        r"password",        # the word itself
        r"letmein",
        r"iloveyou",
        r"admin",
        r"welcome",
    ]

    def __init__(self) -> None:
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self._COMMON_PATTERNS
        ]

    # ── Public API ──────────────────────────────

    def check(self, password: Password) -> "StrengthReport":
        """
        Evaluate password against all criteria and return a StrengthReport.

        Args:
            password: a Password instance to analyse.

        Returns:
            StrengthReport with level, score, criteria results, and suggestions.
        """
        results = self._evaluate_all(password)
        score   = self._calculate_score(results)
        level   = self._classify(score, len(results))
        return StrengthReport(password=password, results=results, score=score, level=level)

    # ── Evaluation helpers ───────────────────────

    def _evaluate_all(self, pwd: Password) -> list[CriteriaResult]:
        """Run every criterion check and collect results."""
        return [
            self._check_min_length(pwd),
            self._check_good_length(pwd),
            self._check_great_length(pwd),
            self._check_uppercase(pwd),
            self._check_lowercase(pwd),
            self._check_digit(pwd),
            self._check_special(pwd),
            self._check_no_spaces(pwd),
            self._check_no_repeated_chars(pwd),
            self._check_no_common_patterns(pwd),
        ]

    def _check_min_length(self, pwd: Password) -> CriteriaResult:
        passed = pwd.length >= self.MIN_LENGTH
        return CriteriaResult(
            key        = Criterion.MIN_LENGTH,
            passed     = passed,
            label      = f"At least {self.MIN_LENGTH} characters",
            suggestion = f"Add {self.MIN_LENGTH - pwd.length} more character(s) to reach the minimum length." if not passed else None,
        )

    def _check_good_length(self, pwd: Password) -> CriteriaResult:
        passed = pwd.length >= self.GOOD_LENGTH
        return CriteriaResult(
            key        = Criterion.GOOD_LENGTH,
            passed     = passed,
            label      = f"At least {self.GOOD_LENGTH} characters (good length)",
            suggestion = f"Aim for {self.GOOD_LENGTH}+ characters for a stronger password." if not passed else None,
        )

    def _check_great_length(self, pwd: Password) -> CriteriaResult:
        passed = pwd.length >= self.GREAT_LENGTH
        return CriteriaResult(
            key        = Criterion.GREAT_LENGTH,
            passed     = passed,
            label      = f"At least {self.GREAT_LENGTH} characters (great length)",
            suggestion = f"Use {self.GREAT_LENGTH}+ characters for maximum length strength." if not passed else None,
        )

    def _check_uppercase(self, pwd: Password) -> CriteriaResult:
        passed = pwd.has_uppercase()
        return CriteriaResult(
            key        = Criterion.HAS_UPPERCASE,
            passed     = passed,
            label      = "Contains uppercase letter(s) (A–Z)",
            suggestion = "Add at least one uppercase letter (e.g. A, B, C…)." if not passed else None,
        )

    def _check_lowercase(self, pwd: Password) -> CriteriaResult:
        passed = pwd.has_lowercase()
        return CriteriaResult(
            key        = Criterion.HAS_LOWERCASE,
            passed     = passed,
            label      = "Contains lowercase letter(s) (a–z)",
            suggestion = "Add at least one lowercase letter (e.g. a, b, c…)." if not passed else None,
        )

    def _check_digit(self, pwd: Password) -> CriteriaResult:
        passed = pwd.has_digit()
        return CriteriaResult(
            key        = Criterion.HAS_DIGIT,
            passed     = passed,
            label      = "Contains digit(s) (0–9)",
            suggestion = "Include at least one number (e.g. 1, 2, 3…)." if not passed else None,
        )

    def _check_special(self, pwd: Password) -> CriteriaResult:
        passed = pwd.has_special()
        return CriteriaResult(
            key        = Criterion.HAS_SPECIAL,
            passed     = passed,
            label      = "Contains special character(s) (!@#$…)",
            suggestion = "Add a special character such as !, @, #, $, %, &, *." if not passed else None,
        )

    def _check_no_spaces(self, pwd: Password) -> CriteriaResult:
        passed = not pwd.has_spaces()
        return CriteriaResult(
            key        = Criterion.NO_SPACES,
            passed     = passed,
            label      = "No spaces",
            suggestion = "Remove spaces — they can cause issues with many systems." if not passed else None,
        )

    def _check_no_repeated_chars(self, pwd: Password) -> CriteriaResult:
        passed = not pwd.has_excessive_repeats()
        return CriteriaResult(
            key        = Criterion.NO_REPEATED_CHARS,
            passed     = passed,
            label      = "No excessive repeated characters (e.g. aaa, 111)",
            suggestion = "Avoid repeating the same character 3 or more times in a row." if not passed else None,
        )

    def _check_no_common_patterns(self, pwd: Password) -> CriteriaResult:
        hit = next(
            (p.pattern for p in self._compiled_patterns if p.search(pwd.value)),
            None,
        )
        passed = hit is None
        return CriteriaResult(
            key        = Criterion.NO_COMMON_PATTERNS,
            passed     = passed,
            label      = "No common patterns or dictionary words",
            suggestion = "Avoid common sequences like '123', 'abc', 'qwerty', or words like 'password'." if not passed else None,
        )

    # ── Scoring & Classification ─────────────────

    @staticmethod
    def _calculate_score(results: list[CriteriaResult]) -> int:
        return sum(1 for r in results if r.passed)

    @staticmethod
    def _classify(score: int, total: int) -> StrengthLevel:
        # score bands: 0-3=VeryWeak, 4-5=Weak, 6-7=Medium, 8-9=Strong, 10=VeryStrong
        if score < 4:
            return StrengthLevel.VERY_WEAK
        if score < 6:
            return StrengthLevel.WEAK
        if score < 8:
            return StrengthLevel.MEDIUM
        if score < 10:
            return StrengthLevel.STRONG
        return StrengthLevel.VERY_STRONG


# ──────────────────────────────────────────────
# StrengthReport (result object)
# ──────────────────────────────────────────────

@dataclass
class StrengthReport:
    """
    Immutable result of a strength check.

    Attributes:
        password  – the Password that was analysed
        results   – per-criterion outcomes
        score     – number of criteria passed
        level     – StrengthLevel enum value
    """
    password : Password
    results  : list[CriteriaResult]
    score    : int
    level    : StrengthLevel

    @property
    def total_criteria(self) -> int:
        return len(self.results)

    @property
    def suggestions(self) -> list[str]:
        return [r.suggestion for r in self.results if not r.passed and r.suggestion]

    def passed_criteria(self) -> list[CriteriaResult]:
        return [r for r in self.results if r.passed]

    def failed_criteria(self) -> list[CriteriaResult]:
        return [r for r in self.results if not r.passed]


# ──────────────────────────────────────────────
# CLI Renderer
# ──────────────────────────────────────────────

DIVIDER      = "─" * 58
THIN_DIVIDER = "·" * 58

def _strength_bar(score: int, total: int, width: int = 20) -> str:
    """Render a simple ASCII progress bar."""
    filled = round(score / total * width) if total else 0
    bar    = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {score}/{total}"

def _print_report(report: StrengthReport) -> None:
    """Pretty-print a StrengthReport to stdout."""
    print(f"\n{DIVIDER}")
    print(f"  Password : {report.password.masked()}")
    print(f"  Length   : {report.password.length} characters")
    print(DIVIDER)

    # Strength level + bar
    print(f"  Strength : {report.level}")
    print(f"  Score    : {_strength_bar(report.score, report.total_criteria)}")
    print(THIN_DIVIDER)

    # Criteria checklist
    print("  Criteria:")
    for r in report.results:
        icon = "✔" if r.passed else "✘"
        print(f"    {icon}  {r.label}")

    # Suggestions
    if report.suggestions:
        print(THIN_DIVIDER)
        print("  Suggestions to improve your password:")
        for i, tip in enumerate(report.suggestions, start=1):
            print(f"    {i}. {tip}")
    else:
        print(THIN_DIVIDER)
        print("  🎉  Excellent! Your password meets all criteria.")

    print(DIVIDER)


# ──────────────────────────────────────────────
# CLI Loop
# ──────────────────────────────────────────────

def _get_password_input() -> Optional[str]:
    """Prompt the user for a password. Returns None on empty input (exit signal)."""
    try:
        raw = input("\n  Enter a password to check (or press Enter to exit): ")
        return raw if raw else None
    except (EOFError, KeyboardInterrupt):
        return None


def run_cli() -> None:
    """Interactive command-line interface for the password strength checker."""
    checker = PasswordStrengthChecker()

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║         🔍  Password Strength Checker  v1.0              ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("  Evaluates passwords against 10 security criteria.")
    print("  Your input is never stored or transmitted.")

    while True:
        raw = _get_password_input()
        if raw is None:
            print("\n  Goodbye! Stay secure. 🔒\n")
            break

        try:
            password = Password(raw)
            report   = checker.check(password)
            _print_report(report)
        except PasswordError as exc:
            print(f"\n  ✖  {exc}")


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    run_cli()