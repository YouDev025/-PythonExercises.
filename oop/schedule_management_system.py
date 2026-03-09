"""
schedule_management_system.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A command-line Schedule Management System built with Python OOP.

Features
  • Add / update / delete events
  • Search by date or title keyword
  • Conflict detection (overlapping time slots on same date)
  • Full schedule display with timeline view
  • Upcoming-events dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from datetime import datetime, date, time, timedelta
from typing import Optional


# ─────────────────────────────────────────────────────────────
#  CONSTANTS & ANSI COLOURS
# ─────────────────────────────────────────────────────────────
DATE_FMT       = "%Y-%m-%d"
TIME_FMT       = "%H:%M"
DISPLAY_DATE   = "%A, %d %B %Y"          # e.g. Monday, 09 March 2026
DISPLAY_TIME   = "%I:%M %p"              # e.g. 09:30 AM

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# Colour cycle for events in timeline view
EVENT_COLOURS = [CYAN, GREEN, YELLOW, MAGENTA, BLUE]


# ─────────────────────────────────────────────────────────────
#  EVENT
# ─────────────────────────────────────────────────────────────
class Event:
    """Represents a single scheduled event."""

    _id_counter = 1

    def __init__(
        self,
        title: str,
        description: str,
        event_date: date,
        start_time: time,
        end_time: time,
        location: str = "TBD",
    ):
        self._validate_inputs(title, event_date, start_time, end_time)

        self._event_id   = f"EVT-{Event._id_counter:04d}"
        Event._id_counter += 1

        self._title       = title.strip()
        self._description = description.strip()
        self._date        = event_date
        self._start_time  = start_time
        self._end_time    = end_time
        self._location    = location.strip() or "TBD"
        self._created_at  = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── static validation ─────────────────────────────────────
    @staticmethod
    def _validate_inputs(title: str, event_date: date,
                         start_time: time, end_time: time):
        if not title.strip():
            raise ValueError("Event title cannot be empty.")
        if end_time <= start_time:
            raise ValueError(
                f"End time ({end_time.strftime(TIME_FMT)}) must be "
                f"after start time ({start_time.strftime(TIME_FMT)})."
            )

    # ── properties (read-only from outside) ──────────────────
    @property
    def event_id(self) -> str:      return self._event_id
    @property
    def title(self) -> str:         return self._title
    @property
    def description(self) -> str:   return self._description
    @property
    def date(self) -> date:         return self._date
    @property
    def start_time(self) -> time:   return self._start_time
    @property
    def end_time(self) -> time:     return self._end_time
    @property
    def location(self) -> str:      return self._location
    @property
    def created_at(self) -> str:    return self._created_at

    @property
    def duration_minutes(self) -> int:
        start_dt = datetime.combine(self._date, self._start_time)
        end_dt   = datetime.combine(self._date, self._end_time)
        return int((end_dt - start_dt).total_seconds() // 60)

    # ── controlled update ─────────────────────────────────────
    def update(
        self,
        title: Optional[str]       = None,
        description: Optional[str] = None,
        event_date: Optional[date] = None,
        start_time: Optional[time] = None,
        end_time: Optional[time]   = None,
        location: Optional[str]    = None,
    ):
        new_title      = title.strip()       if title       is not None else self._title
        new_date       = event_date          if event_date  is not None else self._date
        new_start      = start_time          if start_time  is not None else self._start_time
        new_end        = end_time            if end_time    is not None else self._end_time
        new_location   = location.strip()    if location    is not None else self._location
        new_description= description.strip() if description is not None else self._description

        self._validate_inputs(new_title, new_date, new_start, new_end)

        self._title       = new_title
        self._description = new_description
        self._date        = new_date
        self._start_time  = new_start
        self._end_time    = new_end
        self._location    = new_location or "TBD"

    # ── overlap check ─────────────────────────────────────────
    def overlaps_with(self, other: "Event") -> bool:
        """True if both events share the same date and their times overlap."""
        if self._date != other._date:
            return False
        if self._event_id == other._event_id:
            return False
        # Overlap when one starts before the other ends
        return self._start_time < other._end_time and other._start_time < self._end_time

    # ── display helpers ───────────────────────────────────────
    def summary_row(self, colour: str = CYAN) -> str:
        dur = f"{self.duration_minutes}min"
        return (
            f"  {colour}{self._event_id}{RESET}  "
            f"{self._date.strftime(DATE_FMT)}  "
            f"{self._start_time.strftime(DISPLAY_TIME)}–"
            f"{self._end_time.strftime(DISPLAY_TIME)}  "
            f"{colour}{BOLD}{self._title[:30]:<30}{RESET}  "
            f"{DIM}{dur:<8}{RESET}  {self._location}"
        )

    def detail_card(self) -> str:
        sep = f"  {'─' * 60}"
        is_past = self._date < date.today()
        status_tag = f"{DIM}[Past]{RESET}" if is_past else f"{GREEN}[Upcoming]{RESET}"

        lines = [
            sep,
            f"  {BOLD}{CYAN}{self._event_id}{RESET}  {status_tag}",
            f"  {BOLD}Title       :{RESET} {self._title}",
            f"  {BOLD}Description :{RESET} {self._description or '—'}",
            f"  {BOLD}Date        :{RESET} {self._date.strftime(DISPLAY_DATE)}",
            f"  {BOLD}Time        :{RESET} "
            f"{self._start_time.strftime(DISPLAY_TIME)} → "
            f"{self._end_time.strftime(DISPLAY_TIME)} "
            f"({self.duration_minutes} min)",
            f"  {BOLD}Location    :{RESET} {self._location}",
            f"  {BOLD}Created     :{RESET} {self._created_at}",
            sep,
        ]
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.detail_card()

    def __repr__(self) -> str:
        return (f"Event({self._event_id!r}, {self._title!r}, "
                f"{self._date}, {self._start_time}–{self._end_time})")


# ─────────────────────────────────────────────────────────────
#  SCHEDULE MANAGER
# ─────────────────────────────────────────────────────────────
class ScheduleManager:
    """Manages all events and enforces business rules."""

    def __init__(self, owner: str = "My Schedule"):
        self._owner  = owner
        self._events: dict[str, Event] = {}

    # ── add ───────────────────────────────────────────────────
    def add_event(
        self,
        title: str,
        description: str,
        event_date: date,
        start_time: time,
        end_time: time,
        location: str = "TBD",
    ) -> tuple[Event, list[Event]]:
        """
        Create and store a new event.
        Returns (new_event, list_of_conflicting_events).
        """
        evt = Event(title, description, event_date, start_time, end_time, location)
        conflicts = self._find_conflicts(evt)
        self._events[evt.event_id] = evt
        return evt, conflicts

    # ── retrieve ──────────────────────────────────────────────
    def get_event(self, event_id: str) -> Optional[Event]:
        return self._events.get(event_id.upper())

    def all_events(self, ascending: bool = True) -> list[Event]:
        return sorted(
            self._events.values(),
            key=lambda e: (e.date, e.start_time),
            reverse=not ascending,
        )

    def events_on_date(self, target: date) -> list[Event]:
        return sorted(
            [e for e in self._events.values() if e.date == target],
            key=lambda e: e.start_time,
        )

    def search_by_title(self, keyword: str) -> list[Event]:
        kw = keyword.lower()
        return [
            e for e in self._events.values()
            if kw in e.title.lower() or kw in e.description.lower()
        ]

    def upcoming_events(self, days: int = 7) -> list[Event]:
        today = date.today()
        cutoff = today + timedelta(days=days)
        return sorted(
            [e for e in self._events.values() if today <= e.date <= cutoff],
            key=lambda e: (e.date, e.start_time),
        )

    # ── update ────────────────────────────────────────────────
    def update_event(self, event_id: str, **kwargs) -> tuple[Event, list[Event]]:
        evt = self._require(event_id)
        evt.update(**kwargs)
        conflicts = [c for c in self._find_conflicts(evt)]
        return evt, conflicts

    # ── delete ────────────────────────────────────────────────
    def delete_event(self, event_id: str) -> Event:
        evt = self._require(event_id)
        del self._events[event_id.upper()]
        return evt

    # ── conflict detection ────────────────────────────────────
    def _find_conflicts(self, target: Event) -> list[Event]:
        return [e for e in self._events.values() if target.overlaps_with(e)]

    def check_all_conflicts(self) -> dict[str, list[Event]]:
        """Return a map of event_id → list of events it conflicts with."""
        result: dict[str, list[Event]] = {}
        events = list(self._events.values())
        for i, e1 in enumerate(events):
            for e2 in events[i + 1:]:
                if e1.overlaps_with(e2):
                    result.setdefault(e1.event_id, []).append(e2)
                    result.setdefault(e2.event_id, []).append(e1)
        return result

    # ── statistics ────────────────────────────────────────────
    def statistics(self) -> dict:
        today = date.today()
        total    = len(self._events)
        upcoming = sum(1 for e in self._events.values() if e.date >= today)
        past     = total - upcoming
        conflicts= len(self.check_all_conflicts())
        dates    = sorted({e.date for e in self._events.values()})
        return {
            "total": total, "upcoming": upcoming,
            "past": past, "conflicting": conflicts,
            "busy_dates": len(dates),
        }

    # ── private helpers ───────────────────────────────────────
    def _require(self, event_id: str) -> Event:
        evt = self.get_event(event_id)
        if not evt:
            raise KeyError(f"Event '{event_id.upper()}' not found.")
        return evt


# ─────────────────────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────────────────────
def _sep(char: str = "═", width: int = 64):
    print(char * width)

def _header(title: str):
    _sep()
    print(f"  {BOLD}{title}{RESET}")
    _sep()

def _inp(prompt: str) -> str:
    return input(f"  {prompt}").strip()

def _inp_optional(prompt: str, current: str = "") -> Optional[str]:
    hint = f" [{current}]" if current else ""
    raw = input(f"  {prompt}{hint}: ").strip()
    return raw if raw else None

def _parse_date(raw: str) -> date:
    try:
        return datetime.strptime(raw.strip(), DATE_FMT).date()
    except ValueError:
        raise ValueError(f"Invalid date '{raw}'. Use YYYY-MM-DD format.")

def _parse_time(raw: str) -> time:
    for fmt in ("%H:%M", "%I:%M%p", "%I:%M %p"):
        try:
            return datetime.strptime(raw.strip().upper(), fmt.upper()).time()
        except ValueError:
            continue
    raise ValueError(f"Invalid time '{raw}'. Use HH:MM (24h) or HH:MM AM/PM.")

def _input_date(prompt: str, default: Optional[date] = None) -> date:
    hint = f" [{default.strftime(DATE_FMT)}]" if default else " (YYYY-MM-DD)"
    while True:
        raw = input(f"  {prompt}{hint}: ").strip()
        if not raw and default:
            return default
        try:
            return _parse_date(raw)
        except ValueError as e:
            print(f"  {RED}✖  {e}{RESET}")

def _input_time(prompt: str, default: Optional[time] = None) -> time:
    hint = f" [{default.strftime(TIME_FMT)}]" if default else " (HH:MM)"
    while True:
        raw = input(f"  {prompt}{hint}: ").strip()
        if not raw and default:
            return default
        try:
            return _parse_time(raw)
        except ValueError as e:
            print(f"  {RED}✖  {e}{RESET}")

def _display_table(events: list[Event], heading: str = "Events"):
    if not events:
        print(f"  {DIM}No {heading.lower()} found.{RESET}")
        return
    _header(heading)
    print(
        f"  {BOLD}{'ID':<10}  {'Date':<12}  {'Time Range':<23}  "
        f"{'Title':<30}  {'Dur':<8}  Location{RESET}"
    )
    print(f"  {'─' * 100}")
    for i, evt in enumerate(events):
        colour = EVENT_COLOURS[i % len(EVENT_COLOURS)]
        print(evt.summary_row(colour))

def _show_conflicts(conflicts: list[Event], new_title: str = ""):
    if conflicts:
        label = f"'{new_title}' " if new_title else ""
        print(f"\n  {YELLOW}{BOLD}⚠  Scheduling Conflict!{RESET}")
        print(f"  {YELLOW}Event {label}overlaps with:{RESET}")
        for c in conflicts:
            print(
                f"    • {c.event_id}  {c.title}  "
                f"({c.start_time.strftime(DISPLAY_TIME)}–"
                f"{c.end_time.strftime(DISPLAY_TIME)})"
            )


# ─────────────────────────────────────────────────────────────
#  TIMELINE VIEW  (text-based hour blocks)
# ─────────────────────────────────────────────────────────────
def _timeline_view(events: list[Event], target_date: date):
    """Print a simple hour-by-hour timeline for a given date."""
    if not events:
        print(f"  {DIM}No events on this date.{RESET}")
        return

    print(f"\n  {BOLD}Timeline — {target_date.strftime(DISPLAY_DATE)}{RESET}\n")
    start_h = min(e.start_time.hour for e in events)
    end_h   = max(e.end_time.hour + (1 if e.end_time.minute else 0) for e in events)
    start_h = max(0, start_h - 1)
    end_h   = min(23, end_h + 1)

    for hour in range(start_h, end_h + 1):
        hour_t = time(hour, 0)
        hour_events = [
            e for e in events
            if e.start_time <= hour_t < e.end_time
            or (e.start_time.hour == hour)
        ]
        # dedupe
        seen = set()
        unique = []
        for e in hour_events:
            if e.event_id not in seen:
                seen.add(e.event_id)
                unique.append(e)

        slot = f"  {hour:02d}:00 │"
        if unique:
            labels = "  ".join(
                f"{EVENT_COLOURS[i % len(EVENT_COLOURS)]}"
                f"▌{e.title[:18]}{RESET}"
                for i, e in enumerate(unique)
            )
            print(f"{slot} {labels}")
        else:
            print(f"{DIM}{slot}{RESET}")
    print()


# ─────────────────────────────────────────────────────────────
#  MENU ACTION FUNCTIONS
# ─────────────────────────────────────────────────────────────
def action_add_event(mgr: ScheduleManager):
    _header("Add New Event")
    title       = _inp("Title       : ")
    description = _inp("Description : ")
    evt_date    = _input_date("Date        ")
    start       = _input_time("Start time  ")
    end         = _input_time("End time    ")
    location    = _inp("Location    : ")

    try:
        evt, conflicts = mgr.add_event(
            title, description, evt_date, start, end, location
        )
        print(f"\n  {GREEN}✔  Event added — {evt.event_id}{RESET}")
        _show_conflicts(conflicts, title)
    except ValueError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_update_event(mgr: ScheduleManager):
    _header("Update Event")
    _display_table(mgr.all_events(), "All Events")
    evt_id = _inp("\nEvent ID to update: ").upper()

    evt = mgr.get_event(evt_id)
    if not evt:
        print(f"  {RED}✖  Event '{evt_id}' not found.{RESET}")
        return

    print(f"\n  {DIM}Leave a field blank to keep its current value.{RESET}\n")
    print(evt.detail_card())

    raw_title = _inp_optional("New title       ", evt.title)
    raw_desc  = _inp_optional("New description ", evt.description)
    raw_date  = _inp_optional("New date        ", evt.date.strftime(DATE_FMT))
    raw_start = _inp_optional("New start time  ", evt.start_time.strftime(TIME_FMT))
    raw_end   = _inp_optional("New end time    ", evt.end_time.strftime(TIME_FMT))
    raw_loc   = _inp_optional("New location    ", evt.location)

    kwargs: dict = {}
    try:
        if raw_title:  kwargs["title"]       = raw_title
        if raw_desc:   kwargs["description"] = raw_desc
        if raw_date:   kwargs["event_date"]  = _parse_date(raw_date)
        if raw_start:  kwargs["start_time"]  = _parse_time(raw_start)
        if raw_end:    kwargs["end_time"]    = _parse_time(raw_end)
        if raw_loc:    kwargs["location"]    = raw_loc

        evt, conflicts = mgr.update_event(evt_id, **kwargs)
        print(f"\n  {GREEN}✔  {evt_id} updated successfully.{RESET}")
        _show_conflicts(conflicts, evt.title)
    except (ValueError, KeyError) as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_delete_event(mgr: ScheduleManager):
    _header("Delete Event")
    _display_table(mgr.all_events(), "All Events")
    evt_id = _inp("\nEvent ID to delete: ").upper()
    confirm = _inp(f"Are you sure you want to delete {evt_id}? (y/n): ").lower()
    if confirm != "y":
        print("  Deletion cancelled.")
        return
    try:
        evt = mgr.delete_event(evt_id)
        print(f"\n  {GREEN}✔  '{evt.title}' ({evt_id}) deleted.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_view_event(mgr: ScheduleManager):
    _header("View Event Detail")
    evt_id = _inp("Event ID: ").upper()
    evt = mgr.get_event(evt_id)
    if evt:
        print()
        print(evt.detail_card())
    else:
        print(f"  {RED}✖  Event '{evt_id}' not found.{RESET}")


def action_display_all(mgr: ScheduleManager):
    _display_table(mgr.all_events(), "Full Schedule")


def action_search(mgr: ScheduleManager):
    _header("Search Events")
    print(f"  1. Search by date")
    print(f"  2. Search by title / keyword")
    choice = _inp("Choice: ")

    if choice == "1":
        target = _input_date("Date to search")
        results = mgr.events_on_date(target)
        _display_table(results, f"Events on {target.strftime(DISPLAY_DATE)}")
        if results:
            show_tl = _inp("\nShow timeline view? (y/n): ").lower()
            if show_tl == "y":
                _timeline_view(results, target)

    elif choice == "2":
        kw = _inp("Keyword: ")
        results = mgr.search_by_title(kw)
        _display_table(results, f'Results for "{kw}"')
    else:
        print(f"  {RED}✖  Invalid choice.{RESET}")


def action_timeline(mgr: ScheduleManager):
    _header("Timeline View")
    target = _input_date("Date")
    events = mgr.events_on_date(target)
    _timeline_view(events, target)
    _display_table(events, f"Events on {target.strftime(DISPLAY_DATE)}")


def action_conflicts(mgr: ScheduleManager):
    _header("Conflict Report")
    conflict_map = mgr.check_all_conflicts()
    if not conflict_map:
        print(f"  {GREEN}✔  No scheduling conflicts detected.{RESET}")
        return
    seen_pairs: set[frozenset] = set()
    for eid, clashes in conflict_map.items():
        for clash in clashes:
            pair = frozenset([eid, clash.event_id])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            e1 = mgr.get_event(eid)
            if not e1:
                continue
            print(
                f"\n  {RED}{BOLD}⚠  CONFLICT{RESET}  "
                f"{e1.date.strftime(DATE_FMT)}"
            )
            for ev in (e1, clash):
                print(
                    f"    • {ev.event_id}  {BOLD}{ev.title}{RESET}  "
                    f"{ev.start_time.strftime(DISPLAY_TIME)}–"
                    f"{ev.end_time.strftime(DISPLAY_TIME)}  "
                    f"{DIM}{ev.location}{RESET}"
                )


def action_upcoming(mgr: ScheduleManager):
    _header("Upcoming Events (Next 7 Days)")
    events = mgr.upcoming_events(7)
    _display_table(events, "Upcoming Events")


def action_statistics(mgr: ScheduleManager):
    _header("Schedule Statistics")
    s = mgr.statistics()
    rows = [
        ("Total events",        s["total"],      CYAN),
        ("Upcoming",            s["upcoming"],   GREEN),
        ("Past",                s["past"],       DIM),
        ("Events with conflicts", s["conflicting"], RED if s["conflicting"] else GREEN),
        ("Distinct busy dates", s["busy_dates"], YELLOW),
    ]
    for label, val, colour in rows:
        bar = "█" * val
        print(f"  {label:<26} {colour}{val:>4}  {bar}{RESET}")


# ─────────────────────────────────────────────────────────────
#  DEMO SEED DATA
# ─────────────────────────────────────────────────────────────
def seed_demo_data(mgr: ScheduleManager):
    today = date.today()

    demos = [
        ("Team Stand-up",       "Daily morning sync",
         today,                  time(9,  0), time(9, 30),  "Zoom"),
        ("Sprint Planning",     "Plan Q2 sprint goals",
         today,                  time(10, 0), time(12, 0),  "Conf Room A"),
        ("Lunch with Client",   "Discuss contract renewal",
         today,                  time(12,30), time(13,30),  "The Grand Café"),
        ("Code Review",         "Review PR #241",
         today + timedelta(1),   time(14, 0), time(15, 0),  "Slack Huddle"),
        ("Project Demo",        "Demo v2 to stakeholders",
         today + timedelta(1),   time(15, 0), time(16, 0),  "Main Hall"),
        ("1:1 with Manager",    "Quarterly check-in",
         today + timedelta(2),   time(11, 0), time(11,30),  "Manager's Office"),
        ("Conflict Test A",     "Intentional overlap",
         today + timedelta(3),   time(10, 0), time(11, 0),  "Room 1"),
        ("Conflict Test B",     "Overlaps with A",
         today + timedelta(3),   time(10,30), time(11,30),  "Room 2"),
        ("Past Retrospective",  "Sprint retro recap",
         today - timedelta(5),   time(15, 0), time(16, 0),  "Zoom"),
    ]
    for title, desc, d, s, e, loc in demos:
        mgr.add_event(title, desc, d, s, e, loc)


# ─────────────────────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────────────────────
MENU = f"""
  {BOLD}┌─────────────────────────────────────────────┐
  │         SCHEDULE MANAGEMENT SYSTEM          │
  ├─────────────────────────────────────────────┤
  │{RESET}   1.  Add Event                             {BOLD}│
  │{RESET}   2.  Update Event                          {BOLD}│
  │{RESET}   3.  Delete Event                          {BOLD}│
  │{RESET}   4.  View Event Detail                     {BOLD}│
  │{RESET}   5.  Display Full Schedule                 {BOLD}│
  │{RESET}   6.  Search Events                         {BOLD}│
  │{RESET}   7.  Timeline View (by date)               {BOLD}│
  │{RESET}   8.  Conflict Report                       {BOLD}│
  │{RESET}   9.  Upcoming Events (7 days)              {BOLD}│
  │{RESET}  10.  Statistics                            {BOLD}│
  │{RESET}   0.  Exit                                  {BOLD}│
  └─────────────────────────────────────────────┘{RESET}"""

ACTIONS = {
    "1":  action_add_event,
    "2":  action_update_event,
    "3":  action_delete_event,
    "4":  action_view_event,
    "5":  action_display_all,
    "6":  action_search,
    "7":  action_timeline,
    "8":  action_conflicts,
    "9":  action_upcoming,
    "10": action_statistics,
}


def _banner():
    print()
    _sep("═")
    print(f"""
  {BOLD}{CYAN}
   ███████╗ ██████╗██╗  ██╗███████╗██████╗
   ██╔════╝██╔════╝██║  ██║██╔════╝██╔══██╗
   ███████╗██║     ███████║█████╗  ██║  ██║
   ╚════██║██║     ██╔══██║██╔══╝  ██║  ██║
   ███████║╚██████╗██║  ██║███████╗██████╔╝
   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝{RESET}
  {BOLD}      M A N A G E M E N T   S Y S T E M{RESET}
  {DIM}  Organise your time. Stay ahead of conflicts.{RESET}
""")
    _sep("═")
    print()


def main():
    _banner()

    owner = _inp("Your name (or schedule title): ") or "My Schedule"
    mgr   = ScheduleManager(owner)

    load = _inp("Load demo events? (y/n): ").lower()
    if load == "y":
        seed_demo_data(mgr)
        stats = mgr.statistics()
        print(
            f"\n  {GREEN}✔  {stats['total']} demo events loaded "
            f"({stats['conflicting']} conflict(s) intentionally included).{RESET}"
        )

    while True:
        print(MENU)
        choice = _inp("Select option: ")

        if choice == "0":
            print(f"\n  {CYAN}Schedule saved. See you next time! 👋{RESET}\n")
            break
        elif choice in ACTIONS:
            print()
            ACTIONS[choice](mgr)
            input(f"\n  {DIM}Press Enter to return to menu…{RESET}")
        else:
            print(f"  {RED}✖  Unrecognised option. Please try again.{RESET}")


if __name__ == "__main__":
    main()