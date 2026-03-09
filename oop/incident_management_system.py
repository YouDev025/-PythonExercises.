"""
incident_management_system.py
A command-line Incident Management System built with Python OOP.
Supports reporting, assigning, tracking, searching, and closing incidents.
"""

from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
SEVERITIES  = ("Low", "Medium", "High", "Critical")
STATUSES    = ("Open", "In Progress", "Resolved", "Closed")
DATE_FORMAT = "%Y-%m-%d %H:%M"


# ─────────────────────────────────────────────
#  INCIDENT
# ─────────────────────────────────────────────
class Incident:
    """Represents a single incident record."""

    _id_counter = 1

    def __init__(
        self,
        title: str,
        description: str,
        severity: str,
        reported_by: str,
    ):
        self._validate_severity(severity)
        if not title.strip():
            raise ValueError("Title cannot be empty.")
        if not reported_by.strip():
            raise ValueError("Reporter name cannot be empty.")

        self._incident_id  = f"INC-{Incident._id_counter:05d}"
        Incident._id_counter += 1

        self._title        = title.strip()
        self._description  = description.strip()
        self._severity     = severity
        self._status       = "Open"
        self._reported_by  = reported_by.strip()
        self._assigned_to  = "Unassigned"
        self._date_reported = datetime.now().strftime(DATE_FORMAT)
        self._date_updated  = self._date_reported
        self._resolution_note = ""

    # ── static validation ─────────────────────
    @staticmethod
    def _validate_severity(value: str):
        if value not in SEVERITIES:
            raise ValueError(
                f"Invalid severity '{value}'. "
                f"Choose from: {', '.join(SEVERITIES)}."
            )

    @staticmethod
    def _validate_status(value: str):
        if value not in STATUSES:
            raise ValueError(
                f"Invalid status '{value}'. "
                f"Choose from: {', '.join(STATUSES)}."
            )

    # ── getters ───────────────────────────────
    @property
    def incident_id(self) -> str:     return self._incident_id
    @property
    def title(self) -> str:           return self._title
    @property
    def description(self) -> str:     return self._description
    @property
    def severity(self) -> str:        return self._severity
    @property
    def status(self) -> str:          return self._status
    @property
    def reported_by(self) -> str:     return self._reported_by
    @property
    def assigned_to(self) -> str:     return self._assigned_to
    @property
    def date_reported(self) -> str:   return self._date_reported
    @property
    def date_updated(self) -> str:    return self._date_updated
    @property
    def resolution_note(self) -> str: return self._resolution_note

    # ── controlled mutations ──────────────────
    def assign(self, technician: str):
        if not technician.strip():
            raise ValueError("Technician name cannot be empty.")
        if self._status == "Closed":
            raise PermissionError("Cannot reassign a closed incident.")
        self._assigned_to  = technician.strip()
        self._status       = "In Progress"
        self._date_updated = datetime.now().strftime(DATE_FORMAT)

    def update_status(self, new_status: str, note: str = ""):
        self._validate_status(new_status)
        if self._status == "Closed":
            raise PermissionError("Closed incidents cannot be modified.")
        if new_status == "Closed":
            raise PermissionError(
                "Use close() to close an incident (a resolution note is required)."
            )
        self._status       = new_status
        self._date_updated = datetime.now().strftime(DATE_FORMAT)
        if note.strip():
            self._resolution_note = note.strip()

    def close(self, resolution_note: str):
        if not resolution_note.strip():
            raise ValueError("A resolution note is required to close an incident.")
        if self._status == "Closed":
            raise PermissionError("Incident is already closed.")
        self._status          = "Closed"
        self._resolution_note = resolution_note.strip()
        self._date_updated    = datetime.now().strftime(DATE_FORMAT)

    # ── display ───────────────────────────────
    def summary_row(self) -> str:
        """Single-line summary for table views."""
        sev_tag = f"[{self._severity:<8}]"
        sta_tag = f"[{self._status:<11}]"
        return (
            f"  {self._incident_id}  {sev_tag}  {sta_tag}  "
            f"{self._title[:35]:<35}  {self._assigned_to:<20}  {self._date_reported}"
        )

    def detail_view(self) -> str:
        """Full multi-line detail card."""
        sep = "─" * 62
        lines = [
            sep,
            f"  Incident ID   : {self._incident_id}",
            f"  Title         : {self._title}",
            f"  Description   : {self._description}",
            f"  Severity      : {self._severity}",
            f"  Status        : {self._status}",
            f"  Reported By   : {self._reported_by}",
            f"  Assigned To   : {self._assigned_to}",
            f"  Date Reported : {self._date_reported}",
            f"  Last Updated  : {self._date_updated}",
        ]
        if self._resolution_note:
            lines.append(f"  Resolution    : {self._resolution_note}")
        lines.append(sep)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.detail_view()


# ─────────────────────────────────────────────
#  INCIDENT MANAGER
# ─────────────────────────────────────────────
class IncidentManager:
    """Central manager for all incident operations."""

    def __init__(self):
        self._incidents: dict[str, Incident] = {}

    # ── reporting ─────────────────────────────
    def report_incident(
        self,
        title: str,
        description: str,
        severity: str,
        reported_by: str,
    ) -> Incident:
        inc = Incident(title, description, severity, reported_by)
        self._incidents[inc.incident_id] = inc
        return inc

    # ── retrieval ─────────────────────────────
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self._incidents.get(incident_id.upper())

    def all_incidents(self) -> list[Incident]:
        return list(self._incidents.values())

    def search_by_severity(self, severity: str) -> list[Incident]:
        if severity not in SEVERITIES:
            raise ValueError(
                f"Invalid severity. Choose from: {', '.join(SEVERITIES)}."
            )
        return [i for i in self._incidents.values() if i.severity == severity]

    def search_by_status(self, status: str) -> list[Incident]:
        if status not in STATUSES:
            raise ValueError(
                f"Invalid status. Choose from: {', '.join(STATUSES)}."
            )
        return [i for i in self._incidents.values() if i.status == status]

    def search_by_keyword(self, keyword: str) -> list[Incident]:
        kw = keyword.lower()
        return [
            i for i in self._incidents.values()
            if kw in i.title.lower() or kw in i.description.lower()
        ]

    # ── mutations (delegate to Incident) ──────
    def assign_incident(self, incident_id: str, technician: str) -> Incident:
        inc = self._require(incident_id)
        inc.assign(technician)
        return inc

    def update_status(
        self, incident_id: str, new_status: str, note: str = ""
    ) -> Incident:
        inc = self._require(incident_id)
        inc.update_status(new_status, note)
        return inc

    def close_incident(self, incident_id: str, resolution_note: str) -> Incident:
        inc = self._require(incident_id)
        inc.close(resolution_note)
        return inc

    # ── statistics ────────────────────────────
    def statistics(self) -> dict:
        total = len(self._incidents)
        by_status   = {s: 0 for s in STATUSES}
        by_severity = {s: 0 for s in SEVERITIES}
        for inc in self._incidents.values():
            by_status[inc.status]     += 1
            by_severity[inc.severity] += 1
        return {
            "total": total,
            "by_status": by_status,
            "by_severity": by_severity,
        }

    # ── display helpers ───────────────────────
    def display_table(self, incidents: list[Incident], heading: str = "Incidents"):
        if not incidents:
            print(f"\n  No {heading.lower()} found.")
            return
        _header(heading)
        hdr = (
            f"  {'ID':<12}  {'Severity':<10}  {'Status':<13}  "
            f"{'Title':<35}  {'Assigned To':<20}  {'Reported'}"
        )
        print(hdr)
        print(f"  {'─' * 110}")
        for inc in incidents:
            print(inc.summary_row())

    # ── private helpers ───────────────────────
    def _require(self, incident_id: str) -> Incident:
        inc = self.get_incident(incident_id)
        if not inc:
            raise KeyError(f"Incident '{incident_id}' not found.")
        return inc


# ─────────────────────────────────────────────
#  CLI UTILITIES
# ─────────────────────────────────────────────
def _sep(char: str = "═", width: int = 64):
    print(char * width)

def _header(title: str):
    _sep()
    print(f"  {title}")
    _sep()

def _inp(prompt: str) -> str:
    return input(f"  {prompt}").strip()

def _choose(prompt: str, options: tuple | list) -> str:
    """Prompt user to choose from a numbered list; return chosen value."""
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        raw = _inp(prompt)
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  ✖ Enter a number between 1 and {len(options)}.")


# ─────────────────────────────────────────────
#  MENU ACTION FUNCTIONS
# ─────────────────────────────────────────────
def action_report(mgr: IncidentManager):
    _header("Report New Incident")
    title       = _inp("Title           : ")
    description = _inp("Description     : ")
    reporter    = _inp("Your name       : ")
    print("  Severity level:")
    severity    = _choose("Choose (1-4)    : ", SEVERITIES)
    try:
        inc = mgr.report_incident(title, description, severity, reporter)
        print(f"\n  ✔ Incident filed  →  ID: {inc.incident_id}  |  Severity: {inc.severity}")
    except ValueError as e:
        print(f"\n  ✖ {e}")


def action_assign(mgr: IncidentManager):
    _header("Assign Incident to Technician")
    mgr.display_table(mgr.search_by_status("Open"), "Open Incidents")
    mgr.display_table(mgr.search_by_status("In Progress"), "In-Progress Incidents")
    inc_id = _inp("\nIncident ID : ").upper()
    tech   = _inp("Technician  : ")
    try:
        inc = mgr.assign_incident(inc_id, tech)
        print(f"\n  ✔ {inc_id} assigned to '{inc.assigned_to}'  |  Status → {inc.status}")
    except (KeyError, ValueError, PermissionError) as e:
        print(f"\n  ✖ {e}")


def action_update_status(mgr: IncidentManager):
    _header("Update Incident Status")
    mgr.display_table(mgr.all_incidents(), "All Incidents")
    inc_id = _inp("\nIncident ID  : ").upper()

    # Show current record
    inc = mgr.get_incident(inc_id)
    if not inc:
        print(f"\n  ✖ Incident '{inc_id}' not found.")
        return
    print(f"\n  Current status : {inc.status}")

    # Filter out Closed (handled by close action) and current status
    available = [s for s in STATUSES if s not in ("Closed", inc.status)]
    if not available:
        print("  ✖ No valid status transitions available.")
        return
    print("  New status:")
    new_status = _choose("Choose         : ", available)
    note       = _inp("Progress note  : ")
    try:
        mgr.update_status(inc_id, new_status, note)
        print(f"\n  ✔ {inc_id} status updated to '{new_status}'.")
    except (KeyError, ValueError, PermissionError) as e:
        print(f"\n  ✖ {e}")


def action_close(mgr: IncidentManager):
    _header("Close Resolved Incident")
    resolved = mgr.search_by_status("Resolved") + mgr.search_by_status("In Progress")
    mgr.display_table(resolved, "Closeable Incidents")
    inc_id = _inp("\nIncident ID      : ").upper()
    note   = _inp("Resolution note  : ")
    try:
        mgr.close_incident(inc_id, note)
        print(f"\n  ✔ {inc_id} has been closed.")
    except (KeyError, ValueError, PermissionError) as e:
        print(f"\n  ✖ {e}")


def action_view_detail(mgr: IncidentManager):
    _header("View Incident Detail")
    inc_id = _inp("Incident ID : ").upper()
    inc = mgr.get_incident(inc_id)
    if inc:
        print()
        print(inc.detail_view())
    else:
        print(f"\n  ✖ Incident '{inc_id}' not found.")


def action_display_all(mgr: IncidentManager):
    _header("All Incidents")
    mgr.display_table(mgr.all_incidents(), "All Incidents")


def action_search(mgr: IncidentManager):
    _header("Search Incidents")
    print("  Search by:")
    print("    1. Severity")
    print("    2. Status")
    print("    3. Keyword (title / description)")
    choice = _inp("Choose (1-3) : ")

    if choice == "1":
        print("  Severity:")
        sev = _choose("Choose : ", SEVERITIES)
        results = mgr.search_by_severity(sev)
        mgr.display_table(results, f"Severity = {sev}")

    elif choice == "2":
        print("  Status:")
        sta = _choose("Choose : ", STATUSES)
        results = mgr.search_by_status(sta)
        mgr.display_table(results, f"Status = {sta}")

    elif choice == "3":
        kw = _inp("Keyword : ")
        results = mgr.search_by_keyword(kw)
        mgr.display_table(results, f'Keyword = "{kw}"')

    else:
        print("  ✖ Invalid choice.")


def action_statistics(mgr: IncidentManager):
    _header("System Statistics")
    stats = mgr.statistics()
    print(f"\n  Total Incidents : {stats['total']}\n")

    print(f"  {'By Status':<20}")
    print(f"  {'─'*30}")
    for status, count in stats["by_status"].items():
        bar = "█" * count
        print(f"  {status:<14} {count:>4}  {bar}")

    print(f"\n  {'By Severity':<20}")
    print(f"  {'─'*30}")
    for severity, count in stats["by_severity"].items():
        bar = "█" * count
        print(f"  {severity:<14} {count:>4}  {bar}")


# ─────────────────────────────────────────────
#  DEMO SEED DATA
# ─────────────────────────────────────────────
def seed_demo_data(mgr: IncidentManager):
    data = [
        ("Production DB unreachable",
         "Database server stopped responding at 03:45 UTC.",
         "Critical", "Ops Team"),
        ("Login page 500 error",
         "Users report a 500 error on /login since last deploy.",
         "High", "QA Team"),
        ("Slow dashboard load",
         "Dashboard takes >10s to load for enterprise users.",
         "Medium", "Alice Brown"),
        ("Typo in welcome email",
         "Welcome email has a spelling mistake in the subject line.",
         "Low", "Bob Smith"),
        ("API rate-limit alerts firing",
         "Rate-limit threshold alerts are triggering on staging.",
         "Medium", "DevOps"),
    ]
    for title, desc, sev, reporter in data:
        mgr.report_incident(title, desc, sev, reporter)

    # Assign and progress a couple for variety
    mgr.assign_incident("INC-00001", "Carlos Méndez")
    mgr.update_status("INC-00001", "In Progress", "DB failover initiated")
    mgr.assign_incident("INC-00002", "Dana Lee")
    mgr.update_status("INC-00002", "Resolved", "Rolled back bad deploy")


# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
MENU = """
  ┌──────────────────────────────────────────┐
  │          INCIDENT MANAGEMENT SYSTEM      │
  ├──────────────────────────────────────────┤
  │   1.  Report New Incident                │
  │   2.  Assign Incident to Technician      │
  │   3.  Update Incident Status             │
  │   4.  Close Incident                     │
  │   5.  View Incident Detail               │
  │   6.  Display All Incidents              │
  │   7.  Search Incidents                   │
  │   8.  Statistics Dashboard               │
  │   0.  Exit                               │
  └──────────────────────────────────────────┘"""

ACTIONS = {
    "1": action_report,
    "2": action_assign,
    "3": action_update_status,
    "4": action_close,
    "5": action_view_detail,
    "6": action_display_all,
    "7": action_search,
    "8": action_statistics,
}


def main():
    mgr = IncidentManager()

    _sep("═")
    print("  Incident Management System  —  v1.0")
    _sep("═")
    load = _inp("Load demo incidents? (y/n): ").lower()
    if load == "y":
        seed_demo_data(mgr)
        print("  ✔ 5 demo incidents loaded.\n")

    while True:
        print(MENU)
        choice = _inp("Select option : ")

        if choice == "0":
            print("\n  System closed. Stay incident-free! 👋\n")
            break
        elif choice in ACTIONS:
            print()
            ACTIONS[choice](mgr)
            input("\n  Press Enter to return to menu…")
        else:
            print("  ✖ Unrecognised option. Please try again.")


if __name__ == "__main__":
    main()