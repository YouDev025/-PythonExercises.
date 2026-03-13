"""
Incident Management System
==========================
A modular OOP-based system for reporting, tracking, and resolving
security or system incidents through a command-line interface.
"""

from datetime import datetime
from typing import Optional
from collections import defaultdict
import textwrap


# ═══════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════

SEVERITIES      = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
STATUSES        = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]

# Valid status transitions  (current → allowed next states)
TRANSITIONS: dict[str, list[str]] = {
    "OPEN":        ["IN_PROGRESS", "CLOSED"],
    "IN_PROGRESS": ["RESOLVED", "OPEN"],
    "RESOLVED":    ["CLOSED", "IN_PROGRESS"],
    "CLOSED":      [],                         # terminal state
}

SEV_ICON = {"LOW": "🔵", "MEDIUM": "🟡", "HIGH": "🔴", "CRITICAL": "💀"}
STA_ICON = {"OPEN": "📂", "IN_PROGRESS": "🔧", "RESOLVED": "✅", "CLOSED": "🔒"}

LINE  = "─" * 66
DLINE = "═" * 66


# ═══════════════════════════════════════════════════════════
#  IncidentHistory  (value object – no mutation after append)
# ═══════════════════════════════════════════════════════════

class HistoryEntry:
    """One immutable audit-log record."""

    def __init__(self, field: str, old_value: str, new_value: str, changed_by: str):
        self._field      = field
        self._old_value  = old_value
        self._new_value  = new_value
        self._changed_by = changed_by
        self._timestamp  = datetime.now()

    @property
    def field(self)      -> str:      return self._field
    @property
    def old_value(self)  -> str:      return self._old_value
    @property
    def new_value(self)  -> str:      return self._new_value
    @property
    def changed_by(self) -> str:      return self._changed_by
    @property
    def timestamp(self)  -> datetime: return self._timestamp

    def __str__(self) -> str:
        ts = self._timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"  [{ts}] {self._changed_by} changed {self._field}: "
            f"'{self._old_value}' → '{self._new_value}'"
        )


# ═══════════════════════════════════════════════════════════
#  Incident
# ═══════════════════════════════════════════════════════════

class Incident:
    """
    Represents a single tracked incident.

    All mutation goes through property setters that validate
    input and record an audit trail.
    """

    def __init__(
        self,
        incident_id: str,
        title: str,
        description: str,
        severity: str,
        reported_by: str,
    ):
        self._incident_id  = incident_id
        self._title        = self._check_nonempty(title,       "title")
        self._description  = self._check_nonempty(description, "description")
        self._severity     = self._check_severity(severity)
        self._reported_by  = self._check_nonempty(reported_by, "reported_by")
        self._assigned_to  = "Unassigned"
        self._status       = "OPEN"
        self._timestamp    = datetime.now()
        self._updated_at   = self._timestamp
        self._history: list[HistoryEntry] = []

    # ── Validators ────────────────────────────
    @staticmethod
    def _check_nonempty(value: str, field: str) -> str:
        v = str(value).strip()
        if not v:
            raise ValueError(f"'{field}' must not be empty.")
        return v

    @staticmethod
    def _check_severity(value: str) -> str:
        v = value.strip().upper()
        if v not in SEVERITIES:
            raise ValueError(
                f"Invalid severity '{value}'. Choose: {', '.join(SEVERITIES)}"
            )
        return v

    @staticmethod
    def _check_status(value: str) -> str:
        v = value.strip().upper()
        if v not in STATUSES:
            raise ValueError(
                f"Invalid status '{value}'. Choose: {', '.join(STATUSES)}"
            )
        return v

    # ── Audit helper ──────────────────────────
    def _record(self, field: str, old: str, new: str, actor: str) -> None:
        self._history.append(HistoryEntry(field, old, new, actor))
        self._updated_at = datetime.now()

    # ── Properties ────────────────────────────
    @property
    def incident_id(self)  -> str:            return self._incident_id
    @property
    def title(self)        -> str:            return self._title
    @property
    def description(self)  -> str:            return self._description
    @property
    def severity(self)     -> str:            return self._severity
    @property
    def status(self)       -> str:            return self._status
    @property
    def reported_by(self)  -> str:            return self._reported_by
    @property
    def assigned_to(self)  -> str:            return self._assigned_to
    @property
    def timestamp(self)    -> datetime:       return self._timestamp
    @property
    def updated_at(self)   -> datetime:       return self._updated_at
    @property
    def history(self)      -> list[HistoryEntry]: return list(self._history)
    @property
    def is_closed(self)    -> bool:           return self._status == "CLOSED"

    # ── Mutators ──────────────────────────────
    def assign(self, technician: str, actor: str = "system") -> None:
        technician = self._check_nonempty(technician, "technician")
        old = self._assigned_to
        self._assigned_to = technician
        self._record("assigned_to", old, technician, actor)

    def update_status(self, new_status: str, actor: str = "system") -> None:
        new_status = self._check_status(new_status)
        allowed    = TRANSITIONS[self._status]
        if new_status not in allowed:
            raise ValueError(
                f"Cannot move from '{self._status}' → '{new_status}'. "
                f"Allowed: {allowed or ['(none — terminal state)']}"
            )
        old = self._status
        self._status = new_status
        self._record("status", old, new_status, actor)

    def update_severity(self, new_severity: str, actor: str = "system") -> None:
        new_severity = self._check_severity(new_severity)
        old = self._severity
        self._severity = new_severity
        self._record("severity", old, new_severity, actor)

    def update_description(self, new_desc: str, actor: str = "system") -> None:
        new_desc = self._check_nonempty(new_desc, "description")
        old = self._description
        self._description = new_desc
        self._record("description", old[:40] + "…", new_desc[:40] + "…", actor)

    # ── Display ───────────────────────────────
    def display(self, compact: bool = False) -> None:
        created  = self._timestamp.strftime("%Y-%m-%d %H:%M:%S")
        updated  = self._updated_at.strftime("%Y-%m-%d %H:%M:%S")
        sev_icon = SEV_ICON[self._severity]
        sta_icon = STA_ICON[self._status]

        if compact:
            print(
                f"  {self._incident_id}  {sev_icon} {self._severity:<8}  "
                f"{sta_icon} {self._status:<11}  {self._title[:40]}"
            )
            return

        print(DLINE)
        print(f"  Incident  : {self._incident_id}")
        print(f"  Title     : {self._title}")
        # Word-wrap long descriptions
        wrapped = textwrap.fill(self._description, width=56,
                                initial_indent="              ",
                                subsequent_indent="              ")
        print(f"  Desc      :{wrapped[13:]}")
        print(f"  Severity  : {sev_icon}  {self._severity}")
        print(f"  Status    : {sta_icon}  {self._status}")
        print(f"  Reporter  : {self._reported_by}")
        print(f"  Assigned  : {self._assigned_to}")
        print(f"  Created   : {created}")
        print(f"  Updated   : {updated}")
        print(DLINE)

    def display_history(self) -> None:
        print(f"\n  Audit history for {self._incident_id} ({len(self._history)} entries)")
        print(LINE)
        if not self._history:
            print("  (no changes recorded)")
        else:
            for entry in self._history:
                print(entry)
        print(LINE + "\n")


# ═══════════════════════════════════════════════════════════
#  IncidentManager
# ═══════════════════════════════════════════════════════════

class IncidentManager:
    """
    Central repository and coordinator for all Incident objects.

    Responsibilities
    ----------------
    * Auto-generate unique IDs
    * CRUD operations
    * Search / filter
    * Aggregate statistics
    """

    def __init__(self):
        self._incidents: dict[str, Incident] = {}
        self._counter   = 0

    # ── ID generation ─────────────────────────
    def _next_id(self) -> str:
        self._counter += 1
        return f"INC-{self._counter:04d}"

    # ── Create ────────────────────────────────
    def report(
        self,
        title: str,
        description: str,
        severity: str,
        reported_by: str,
    ) -> Incident:
        inc_id = self._next_id()
        incident = Incident(inc_id, title, description, severity, reported_by)
        self._incidents[inc_id] = incident
        return incident

    # ── Retrieve ──────────────────────────────
    def get(self, incident_id: str) -> Incident:
        inc = self._incidents.get(incident_id.strip().upper())
        if inc is None:
            raise KeyError(f"Incident '{incident_id}' not found.")
        return inc

    @property
    def all_incidents(self) -> list[Incident]:
        return list(self._incidents.values())

    @property
    def count(self) -> int:
        return len(self._incidents)

    # ── Search / filter ───────────────────────
    def by_severity(self, severity: str) -> list[Incident]:
        s = severity.strip().upper()
        if s not in SEVERITIES:
            raise ValueError(f"Invalid severity '{severity}'. Choose: {SEVERITIES}")
        return [i for i in self._incidents.values() if i.severity == s]

    def by_status(self, status: str) -> list[Incident]:
        s = status.strip().upper()
        if s not in STATUSES:
            raise ValueError(f"Invalid status '{status}'. Choose: {STATUSES}")
        return [i for i in self._incidents.values() if i.status == s]

    def by_assignee(self, name: str) -> list[Incident]:
        n = name.strip().lower()
        return [i for i in self._incidents.values()
                if i.assigned_to.lower() == n]

    def search_title(self, query: str) -> list[Incident]:
        q = query.strip().lower()
        return [i for i in self._incidents.values() if q in i.title.lower()]

    # ── Aggregate stats ───────────────────────
    def statistics(self) -> dict:
        sev_counts: dict[str, int] = defaultdict(int)
        sta_counts: dict[str, int] = defaultdict(int)
        for inc in self._incidents.values():
            sev_counts[inc.severity] += 1
            sta_counts[inc.status]   += 1
        return {
            "total":    self.count,
            "severity": dict(sev_counts),
            "status":   dict(sta_counts),
        }

    # ── Convenience actions (delegating) ──────
    def assign(self, incident_id: str, technician: str, actor: str = "system") -> None:
        self.get(incident_id).assign(technician, actor)

    def update_status(self, incident_id: str, status: str, actor: str = "system") -> None:
        self.get(incident_id).update_status(status, actor)

    def close(self, incident_id: str, actor: str = "system") -> None:
        inc = self.get(incident_id)
        if inc.status not in ("RESOLVED",):
            raise ValueError(
                f"Incident must be RESOLVED before closing. "
                f"Current status: {inc.status}"
            )
        inc.update_status("CLOSED", actor)

    # ── Display helpers ───────────────────────
    def display_all(self, incidents: Optional[list[Incident]] = None) -> None:
        items = incidents if incidents is not None else list(self._incidents.values())
        if not items:
            print("\n  No incidents to display.\n")
            return
        print(f"\n{'─'*66}")
        print(f"  {'ID':<12}  {'SEV':<10}  {'STATUS':<14}  TITLE")
        print(f"{'─'*66}")
        for inc in sorted(items, key=lambda x: x.timestamp, reverse=True):
            inc.display(compact=True)
        print(f"{'─'*66}  ({len(items)} record(s))\n")

    def display_statistics(self) -> None:
        stats = self.statistics()
        print(f"\n{'─'*45}")
        print("  INCIDENT STATISTICS")
        print(f"{'─'*45}")
        print(f"  Total incidents : {stats['total']}")

        print("\n  By Severity:")
        for sev in SEVERITIES:
            n   = stats["severity"].get(sev, 0)
            bar = "█" * n
            print(f"    {SEV_ICON[sev]} {sev:<8} {bar} ({n})")

        print("\n  By Status:")
        for sta in STATUSES:
            n   = stats["status"].get(sta, 0)
            bar = "█" * n
            print(f"    {STA_ICON[sta]} {sta:<12} {bar} ({n})")
        print(f"{'─'*45}\n")


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════

BANNER = r"""
  ╔══════════════════════════════════════════════════════╗
  ║        INCIDENT  MANAGEMENT  SYSTEM  v1.0            ║
  ║    Track · Assign · Resolve · Close · Audit          ║
  ╚══════════════════════════════════════════════════════╝
"""

MENU = """
  ┌──────────────────────────────────────────────────────┐
  │  INCIDENTS                                           │
  │   1. Report new incident                             │
  │   2. View incident details                           │
  │   3. Display all incidents                           │
  │                                                      │
  │  ACTIONS                                             │
  │   4. Assign incident to technician                   │
  │   5. Update incident status                          │
  │   6. Update incident severity                        │
  │   7. Close a resolved incident                       │
  │                                                      │
  │  SEARCH & REPORTS                                    │
  │   8. Search by severity                              │
  │   9. Search by status                                │
  │  10. Search by title keyword                         │
  │  11. View incident history (audit log)               │
  │  12. Statistics dashboard                            │
  │                                                      │
  │   0. Exit                                            │
  └──────────────────────────────────────────────────────┘
  Choice: """


class CLI:

    def __init__(self):
        self._mgr = IncidentManager()

    # ── Input helpers ─────────────────────────
    @staticmethod
    def _ask(prompt: str, required: bool = True) -> str:
        while True:
            val = input(f"  {prompt}").strip()
            if val or not required:
                return val
            print("  [!] This field is required.")

    @staticmethod
    def _choose(prompt: str, options: list[str]) -> str:
        display = "/".join(options)
        while True:
            val = input(f"  {prompt} [{display}]: ").strip().upper()
            if val in options:
                return val
            print(f"  [!] Enter one of: {display}")

    def _ask_incident_id(self) -> Optional[Incident]:
        inc_id = self._ask("Incident ID (e.g. INC-0001): ").upper()
        try:
            return self._mgr.get(inc_id)
        except KeyError as exc:
            print(f"\n  [!] {exc}\n")
            return None

    # ── Menu actions ──────────────────────────
    def _report(self) -> None:
        print(f"\n  {LINE}")
        print("  REPORT NEW INCIDENT")
        print(f"  {LINE}")
        title       = self._ask("Title       : ")
        description = self._ask("Description : ")
        severity    = self._choose("Severity", SEVERITIES)
        reported_by = self._ask("Reported by : ")
        try:
            inc = self._mgr.report(title, description, severity, reported_by)
            print(f"\n  ✔  Incident created successfully:")
            inc.display()
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")

    def _view_details(self) -> None:
        inc = self._ask_incident_id()
        if inc:
            print()
            inc.display()

    def _assign(self) -> None:
        inc = self._ask_incident_id()
        if not inc:
            return
        if inc.is_closed:
            print("  [!] Cannot modify a closed incident.\n")
            return
        tech  = self._ask("Assign to (technician name): ")
        actor = self._ask("Your name (actor)          : ")
        try:
            inc.assign(tech, actor)
            print(f"\n  ✔  {inc.incident_id} assigned to '{tech}'.\n")
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")

    def _update_status(self) -> None:
        inc = self._ask_incident_id()
        if not inc:
            return
        if inc.is_closed:
            print("  [!] Cannot modify a closed incident.\n")
            return
        allowed = TRANSITIONS[inc.status]
        if not allowed:
            print(f"  [!] {inc.incident_id} is in terminal state '{inc.status}'.\n")
            return
        print(f"  Current status  : {inc.status}")
        print(f"  Allowed next    : {', '.join(allowed)}")
        new_status = self._choose("New status", allowed)
        actor      = self._ask("Your name (actor): ")
        try:
            inc.update_status(new_status, actor)
            print(f"\n  ✔  Status updated to '{new_status}'.\n")
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")

    def _update_severity(self) -> None:
        inc = self._ask_incident_id()
        if not inc:
            return
        if inc.is_closed:
            print("  [!] Cannot modify a closed incident.\n")
            return
        print(f"  Current severity: {inc.severity}")
        new_sev = self._choose("New severity", SEVERITIES)
        actor   = self._ask("Your name (actor): ")
        try:
            inc.update_severity(new_sev, actor)
            print(f"\n  ✔  Severity updated to '{new_sev}'.\n")
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")

    def _close(self) -> None:
        inc = self._ask_incident_id()
        if not inc:
            return
        actor = self._ask("Your name (actor): ")
        try:
            self._mgr.close(inc.incident_id, actor)
            print(f"\n  ✔  {inc.incident_id} has been closed.\n")
        except ValueError as exc:
            print(f"\n  [!] {exc}\n")

    def _search_severity(self) -> None:
        sev = self._choose("Filter by severity", SEVERITIES)
        results = self._mgr.by_severity(sev)
        print(f"\n  Results for severity = {sev}:")
        self._mgr.display_all(results)

    def _search_status(self) -> None:
        sta = self._choose("Filter by status", STATUSES)
        results = self._mgr.by_status(sta)
        print(f"\n  Results for status = {sta}:")
        self._mgr.display_all(results)

    def _search_title(self) -> None:
        query   = self._ask("Title keyword: ")
        results = self._mgr.search_title(query)
        print(f"\n  Results for title containing '{query}':")
        self._mgr.display_all(results)

    def _view_history(self) -> None:
        inc = self._ask_incident_id()
        if inc:
            inc.display_history()

    # ── Seed demo data ────────────────────────
    def _seed_demo(self) -> None:
        demos = [
            ("Database server unresponsive",
             "Primary DB node stopped responding to health checks at 03:00 UTC.",
             "CRITICAL", "ops-monitor"),
            ("SSL certificate expiry warning",
             "api.internal cert expires in 7 days; auto-renewal failed.",
             "HIGH", "cert-bot"),
            ("Repeated SSH login failures",
             "Over 200 failed SSH attempts from 198.51.100.42 in last hour.",
             "HIGH", "ids-system"),
            ("Disk usage above 85% on /var",
             "Log volume filling up; rotation job may have failed.",
             "MEDIUM", "disk-monitor"),
            ("Scheduled backup missed",
             "Nightly backup job did not complete; last success 48 h ago.",
             "LOW", "backup-agent"),
        ]
        for title, desc, sev, reporter in demos:
            self._mgr.report(title, desc, sev, reporter)

        # Partial workflow on first two
        self._mgr.assign("INC-0001", "alice", "admin")
        self._mgr.update_status("INC-0001", "IN_PROGRESS", "alice")
        self._mgr.assign("INC-0002", "bob", "admin")
        self._mgr.update_status("INC-0002", "IN_PROGRESS", "bob")
        self._mgr.update_status("INC-0002", "RESOLVED",    "bob")

        print(f"\n  ✔  {len(demos)} demo incidents loaded.\n")

    # ── Main loop ─────────────────────────────
    def run(self) -> None:
        print(BANNER)

        seed = input("  Load demo incidents? (yes/no) [no]: ").strip().lower()
        if seed in ("yes", "y"):
            self._seed_demo()

        dispatch = {
            "1":  self._report,
            "2":  self._view_details,
            "3":  lambda: self._mgr.display_all(),
            "4":  self._assign,
            "5":  self._update_status,
            "6":  self._update_severity,
            "7":  self._close,
            "8":  self._search_severity,
            "9":  self._search_status,
            "10": self._search_title,
            "11": self._view_history,
            "12": self._mgr.display_statistics,
        }

        while True:
            try:
                choice = input(MENU).strip()
                if choice == "0":
                    print("\n  System shutdown. Goodbye!\n")
                    break
                action = dispatch.get(choice)
                if action is None:
                    print("  [!] Invalid choice. Enter 0-12.")
                else:
                    action()
            except KeyboardInterrupt:
                print("\n\n  Interrupted. Goodbye!\n")
                break
            except Exception as exc:
                print(f"\n  [!] Unexpected error: {exc}\n")


# ═══════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    CLI().run()