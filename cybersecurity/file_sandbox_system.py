"""
file_sandbox_system.py
======================
A simulated sandbox environment for safely analyzing potentially dangerous files.
Uses OOP principles: encapsulation, abstraction, and modularity.
"""

import hashlib
import random
import time
import os
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
# FileSample Class
# ─────────────────────────────────────────────

class FileSample:
    """
    Represents a file submitted for sandbox analysis.
    Encapsulates file metadata and analysis state.
    """

    ALLOWED_TYPES = {
        ".exe": "Executable",
        ".dll": "Dynamic Library",
        ".bat": "Batch Script",
        ".sh":  "Shell Script",
        ".py":  "Python Script",
        ".js":  "JavaScript",
        ".pdf": "PDF Document",
        ".zip": "Archive",
        ".doc": "Word Document",
        ".docx":"Word Document",
        ".unknown": "Unknown",
    }

    def __init__(self, file_name: str, file_path: str):
        if not file_name or not isinstance(file_name, str):
            raise ValueError("file_name must be a non-empty string.")
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be a non-empty string.")

        self.__file_name = file_name.strip()
        self.__file_path = file_path.strip()
        self.__file_type = self._detect_type()
        self.__hash_value = self._compute_hash()
        self.__analysis_status = "Pending"
        self.__submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Private Helpers ──────────────────────

    def _detect_type(self) -> str:
        _, ext = os.path.splitext(self.__file_name)
        ext = ext.lower() if ext else ".unknown"
        return self.ALLOWED_TYPES.get(ext, "Unknown")

    def _compute_hash(self) -> str:
        """Generate a deterministic simulated SHA-256 hash from file name + path."""
        raw = f"{self.__file_name}{self.__file_path}".encode()
        return hashlib.sha256(raw).hexdigest()

    # ── Public Properties (read-only) ────────

    @property
    def file_name(self) -> str:
        return self.__file_name

    @property
    def file_path(self) -> str:
        return self.__file_path

    @property
    def file_type(self) -> str:
        return self.__file_type

    @property
    def hash_value(self) -> str:
        return self.__hash_value

    @property
    def analysis_status(self) -> str:
        return self.__analysis_status

    @analysis_status.setter
    def analysis_status(self, status: str):
        valid = {"Pending", "Running", "Completed", "Failed"}
        if status not in valid:
            raise ValueError(f"Invalid status '{status}'. Must be one of {valid}.")
        self.__analysis_status = status

    @property
    def submitted_at(self) -> str:
        return self.__submitted_at

    def __repr__(self) -> str:
        return (f"FileSample(name='{self.__file_name}', type='{self.__file_type}', "
                f"status='{self.__analysis_status}')")


# ─────────────────────────────────────────────
# SandboxEnvironment Class
# ─────────────────────────────────────────────

class SandboxEnvironment:
    """
    Simulates an isolated execution environment for a single FileSample.
    Performs behavioral analysis and generates a structured report.
    """

    # Simulated suspicious behaviors per file type
    _BEHAVIOR_POOL = {
        "Executable": [
            "Attempted to write to SYSTEM32 directory",
            "Created a hidden process",
            "Modified Windows Registry keys",
            "Spawned child processes",
            "Contacted external IP: 185.220.101.47",
        ],
        "Dynamic Library": [
            "Injected into explorer.exe",
            "Hooked NtCreateFile API",
            "Loaded unsigned drivers",
        ],
        "Batch Script": [
            "Executed encoded PowerShell command",
            "Disabled Windows Defender",
            "Enumerated running processes",
        ],
        "Shell Script": [
            "Added cron job for persistence",
            "Exfiltrated /etc/passwd",
            "Installed a reverse shell",
        ],
        "Python Script": [
            "Imported subprocess module",
            "Accessed os.environ for credentials",
            "Made outbound HTTP request to unknown domain",
        ],
        "JavaScript": [
            "Executed eval() on remote payload",
            "Set obfuscated localStorage value",
            "Attempted DOM injection",
        ],
        "PDF Document": [
            "Embedded JavaScript trigger",
            "Attempted to launch external URL",
            "Contains suspicious /OpenAction entry",
        ],
        "Archive": [
            "Contains password-protected inner archive",
            "Path traversal detected in ZIP entries",
            "Dropped hidden executable on extraction",
        ],
        "Word Document": [
            "Macro execution triggered on open",
            "External OLE object linked",
            "Auto-run VBA script detected",
        ],
        "Unknown": [
            "Unrecognized file header",
            "High entropy sections detected (possible encryption)",
            "Attempted to contact C2 server",
        ],
    }

    _BENIGN_BEHAVIORS = [
        "Read local configuration file",
        "Opened standard I/O streams",
        "Checked system locale settings",
        "Loaded standard runtime libraries",
        "Wrote temporary log file",
    ]

    def __init__(self, sample: FileSample):
        if not isinstance(sample, FileSample):
            raise TypeError("sample must be a FileSample instance.")
        self.__sample = sample
        self.__report: Optional[dict] = None
        self.__is_loaded = False

    # ── Public Methods ───────────────────────

    def load_file(self) -> None:
        """Load the file into the sandbox environment."""
        print(f"\n  [SANDBOX] Loading '{self.__sample.file_name}' into isolated environment...")
        time.sleep(0.5)
        self.__is_loaded = True
        self.__sample.analysis_status = "Running"
        print(f"  [SANDBOX] File loaded successfully. Hash: {self.__sample.hash_value[:16]}...")

    def analyze(self) -> dict:
        """
        Simulate behavioral analysis of the loaded file.
        Returns a structured analysis report dictionary.
        """
        if not self.__is_loaded:
            raise RuntimeError("File must be loaded before analysis. Call load_file() first.")

        print(f"  [SANDBOX] Analysing behavior of '{self.__sample.file_name}'...")
        time.sleep(0.8)

        file_type = self.__sample.file_type
        behavior_pool = self._BEHAVIOR_POOL.get(file_type, self._BEHAVIOR_POOL["Unknown"])

        # Randomly pick suspicious and benign behaviors
        num_suspicious = random.randint(0, min(3, len(behavior_pool)))
        num_benign = random.randint(1, 3)

        suspicious_behaviors = random.sample(behavior_pool, num_suspicious)
        benign_behaviors = random.sample(self._BENIGN_BEHAVIORS, num_benign)

        threat_score = self._calculate_threat_score(num_suspicious)
        verdict = self._determine_verdict(threat_score)

        self.__report = {
            "file_name":            self.__sample.file_name,
            "file_path":            self.__sample.file_path,
            "file_type":            self.__sample.file_type,
            "hash_sha256":          self.__sample.hash_value,
            "submitted_at":         self.__sample.submitted_at,
            "analysis_completed_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "threat_score":         threat_score,
            "verdict":              verdict,
            "suspicious_behaviors": suspicious_behaviors,
            "benign_behaviors":     benign_behaviors,
            "network_requests":     self._simulate_network_requests(num_suspicious),
            "file_operations":      self._simulate_file_operations(),
        }

        self.__sample.analysis_status = "Completed"
        print(f"  [SANDBOX] Analysis complete. Verdict: {verdict}")
        return self.__report

    def get_report(self) -> Optional[dict]:
        """Return the generated report, or None if analysis hasn't run yet."""
        return self.__report

    # ── Private Helpers ──────────────────────

    @staticmethod
    def _calculate_threat_score(num_suspicious: int) -> int:
        base = num_suspicious * 25
        noise = random.randint(-5, 10)
        return max(0, min(100, base + noise))

    @staticmethod
    def _determine_verdict(score: int) -> str:
        if score == 0:
            return "CLEAN"
        elif score < 30:
            return "LOW RISK"
        elif score < 60:
            return "MEDIUM RISK"
        elif score < 85:
            return "HIGH RISK"
        else:
            return "MALICIOUS"

    @staticmethod
    def _simulate_network_requests(num_suspicious: int) -> list:
        if num_suspicious == 0:
            return []
        fake_ips = [
            "185.220.101.47", "91.108.4.0", "10.0.0.255",
            "203.0.113.42", "198.51.100.7",
        ]
        domains = [
            "update-service.ru", "cdn-fast.net", "analytics-beacon.io",
        ]
        requests = []
        for _ in range(random.randint(1, num_suspicious + 1)):
            if random.random() > 0.5:
                requests.append(f"DNS lookup: {random.choice(domains)}")
            else:
                requests.append(f"TCP connect: {random.choice(fake_ips)}:{random.choice([80,443,4444,8080])}")
        return requests

    @staticmethod
    def _simulate_file_operations() -> list:
        ops_pool = [
            "READ  C:\\Users\\Public\\config.ini",
            "WRITE C:\\Temp\\~tmp8f3a.dat",
            "READ  /etc/hosts",
            "WRITE /tmp/.hidden_lock",
            "DELETE C:\\Windows\\Temp\\old_log.txt",
            "EXEC  cmd.exe /c whoami",
        ]
        return random.sample(ops_pool, random.randint(1, 4))


# ─────────────────────────────────────────────
# SandboxManager Class
# ─────────────────────────────────────────────

class SandboxManager:
    """
    Manages the lifecycle of multiple file analyses.
    Stores results and provides reporting capabilities.
    """

    def __init__(self):
        self.__analyses: dict[str, dict] = {}   # hash → report
        self.__samples:  dict[str, FileSample] = {}  # hash → FileSample

    # ── Public Interface ─────────────────────

    def submit_file(self, file_name: str, file_path: str) -> FileSample:
        """
        Create and register a new FileSample.
        Returns the created FileSample object.
        """
        sample = FileSample(file_name, file_path)
        if sample.hash_value in self.__samples:
            print(f"\n  [MANAGER] File '{file_name}' was already submitted (same hash). "
                  f"Returning existing record.")
            return self.__samples[sample.hash_value]

        self.__samples[sample.hash_value] = sample
        print(f"\n  [MANAGER] File '{file_name}' submitted successfully.")
        print(f"            Type   : {sample.file_type}")
        print(f"            Hash   : {sample.hash_value[:32]}...")
        return sample

    def run_analysis(self, sample: FileSample) -> dict:
        """
        Run a full sandbox simulation for the given FileSample.
        Returns the completed report.
        """
        if sample.hash_value in self.__analyses:
            print(f"\n  [MANAGER] Analysis already exists for '{sample.file_name}'. "
                  f"Returning cached report.")
            return self.__analyses[sample.hash_value]

        env = SandboxEnvironment(sample)
        try:
            env.load_file()
            report = env.analyze()
            self.__analyses[sample.hash_value] = report
            return report
        except Exception as exc:
            sample.analysis_status = "Failed"
            print(f"\n  [ERROR] Analysis failed: {exc}")
            raise

    def get_report(self, file_name: str) -> Optional[dict]:
        """Retrieve a stored report by file name (case-insensitive)."""
        for report in self.__analyses.values():
            if report["file_name"].lower() == file_name.strip().lower():
                return report
        return None

    def list_files(self) -> list[FileSample]:
        """Return a list of all submitted FileSample objects."""
        return list(self.__samples.values())

    def print_report(self, report: dict) -> None:
        """Pretty-print a single analysis report to the console."""
        sep = "─" * 60
        verdict_color = self._verdict_prefix(report["verdict"])

        print(f"\n{'═'*60}")
        print(f"  SANDBOX ANALYSIS REPORT")
        print(f"{'═'*60}")
        print(f"  File Name   : {report['file_name']}")
        print(f"  File Path   : {report['file_path']}")
        print(f"  File Type   : {report['file_type']}")
        print(f"  SHA-256     : {report['hash_sha256'][:40]}...")
        print(f"  Submitted   : {report['submitted_at']}")
        print(f"  Completed   : {report['analysis_completed_at']}")
        print(sep)
        print(f"  Threat Score: {report['threat_score']}/100")
        print(f"  Verdict     : {verdict_color}{report['verdict']}\033[0m")
        print(sep)

        if report["suspicious_behaviors"]:
            print("  ⚠  Suspicious Behaviors Detected:")
            for b in report["suspicious_behaviors"]:
                print(f"     • {b}")
        else:
            print("  ✓  No suspicious behaviors detected.")

        print(f"\n  ℹ  Benign Behaviors:")
        for b in report["benign_behaviors"]:
            print(f"     • {b}")

        if report["network_requests"]:
            print(f"\n  🌐 Network Activity:")
            for r in report["network_requests"]:
                print(f"     • {r}")

        print(f"\n  📁 File System Operations:")
        for op in report["file_operations"]:
            print(f"     • {op}")

        print(f"{'═'*60}\n")

    # ── Private Helper ───────────────────────

    @staticmethod
    def _verdict_prefix(verdict: str) -> str:
        colors = {
            "CLEAN":       "\033[92m",  # green
            "LOW RISK":    "\033[96m",  # cyan
            "MEDIUM RISK": "\033[93m",  # yellow
            "HIGH RISK":   "\033[91m",  # red
            "MALICIOUS":   "\033[95m",  # magenta
        }
        return colors.get(verdict, "")


# ─────────────────────────────────────────────
# Command-Line Interface
# ─────────────────────────────────────────────

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║          FILE SANDBOX ANALYSIS SYSTEM v1.0               ║
║     Simulated malware analysis in an isolated env.       ║
╚══════════════════════════════════════════════════════════╝
""")


def print_menu():
    print("  ┌─────────────────────────────────────┐")
    print("  │  MAIN MENU                          │")
    print("  │  1. Submit a file for analysis      │")
    print("  │  2. Run sandbox simulation          │")
    print("  │  3. View analysis report            │")
    print("  │  4. List all submitted files        │")
    print("  │  5. Exit                            │")
    print("  └─────────────────────────────────────┘")


def get_choice(prompt: str, valid: set) -> str:
    while True:
        choice = input(prompt).strip()
        if choice in valid:
            return choice
        print(f"  [!] Invalid choice. Please enter one of: {', '.join(sorted(valid))}")


def cmd_submit(manager: SandboxManager) -> Optional[FileSample]:
    print("\n  ── Submit File ───────────────────────")
    file_name = input("  Enter file name (e.g., malware.exe): ").strip()
    if not file_name:
        print("  [!] File name cannot be empty.")
        return None
    file_path = input("  Enter file path (e.g., C:\\Samples\\malware.exe): ").strip()
    if not file_path:
        print("  [!] File path cannot be empty.")
        return None
    try:
        return manager.submit_file(file_name, file_path)
    except ValueError as e:
        print(f"  [!] Error: {e}")
        return None


def cmd_run_analysis(manager: SandboxManager):
    samples = manager.list_files()
    if not samples:
        print("\n  [!] No files submitted yet. Submit a file first (option 1).")
        return

    print("\n  ── Run Analysis ──────────────────────")
    pending = [s for s in samples if s.analysis_status in ("Pending",)]
    completed = [s for s in samples if s.analysis_status == "Completed"]

    if pending:
        print("  Pending files:")
        for i, s in enumerate(pending, 1):
            print(f"    {i}. {s.file_name}  [{s.file_type}]")
        choice = input("  Enter file name to analyse (or ENTER to cancel): ").strip()
        if not choice:
            return
        target = next((s for s in pending if s.file_name.lower() == choice.lower()), None)
        if not target:
            print("  [!] File not found in pending list.")
            return
    elif completed:
        print("  All submitted files have already been analysed.")
        rerun = input("  Re-run analysis on a file? (y/n): ").strip().lower()
        if rerun != "y":
            return
        print("  Completed files:")
        for i, s in enumerate(completed, 1):
            print(f"    {i}. {s.file_name}")
        choice = input("  Enter file name: ").strip()
        target = next((s for s in completed if s.file_name.lower() == choice.lower()), None)
        if not target:
            print("  [!] File not found.")
            return
        # Reset status to allow re-run
        target.analysis_status = "Pending"
        # Remove old report
        manager._SandboxManager__analyses.pop(target.hash_value, None)
    else:
        print("  [!] No files available for analysis.")
        return

    try:
        report = manager.run_analysis(target)
        print("\n  Analysis complete! View the full report using option 3.")
    except Exception as e:
        print(f"\n  [!] Analysis encountered an error: {e}")


def cmd_view_report(manager: SandboxManager):
    samples = manager.list_files()
    completed = [s for s in samples if s.analysis_status == "Completed"]
    if not completed:
        print("\n  [!] No completed analyses found. Run a simulation first (option 2).")
        return

    print("\n  ── View Report ───────────────────────")
    print("  Completed analyses:")
    for i, s in enumerate(completed, 1):
        print(f"    {i}. {s.file_name}  [{s.file_type}]")

    choice = input("  Enter file name to view report: ").strip()
    report = manager.get_report(choice)
    if report:
        manager.print_report(report)
    else:
        print(f"  [!] No report found for '{choice}'.")


def cmd_list_files(manager: SandboxManager):
    samples = manager.list_files()
    if not samples:
        print("\n  [!] No files have been submitted yet.")
        return

    print(f"\n  {'─'*60}")
    print(f"  {'#':<4} {'File Name':<25} {'Type':<18} {'Status'}")
    print(f"  {'─'*60}")
    for i, s in enumerate(samples, 1):
        status_color = {
            "Pending":   "\033[93m",
            "Running":   "\033[96m",
            "Completed": "\033[92m",
            "Failed":    "\033[91m",
        }.get(s.analysis_status, "")
        print(f"  {i:<4} {s.file_name:<25} {s.file_type:<18} "
              f"{status_color}{s.analysis_status}\033[0m")
    print(f"  {'─'*60}")
    print(f"  Total files: {len(samples)}\n")


def main():
    print_banner()
    manager = SandboxManager()
    last_sample: Optional[FileSample] = None

    while True:
        print_menu()
        choice = get_choice("  Select an option [1-5]: ", {"1", "2", "3", "4", "5"})

        if choice == "1":
            sample = cmd_submit(manager)
            if sample:
                last_sample = sample
                run_now = input("\n  Run analysis now? (y/n): ").strip().lower()
                if run_now == "y":
                    try:
                        manager.run_analysis(sample)
                        view_now = input("  View report now? (y/n): ").strip().lower()
                        if view_now == "y":
                            report = manager.get_report(sample.file_name)
                            if report:
                                manager.print_report(report)
                    except Exception:
                        pass

        elif choice == "2":
            cmd_run_analysis(manager)

        elif choice == "3":
            cmd_view_report(manager)

        elif choice == "4":
            cmd_list_files(manager)

        elif choice == "5":
            print("\n  [*] Shutting down sandbox system. Goodbye!\n")
            break


if __name__ == "__main__":
    main()