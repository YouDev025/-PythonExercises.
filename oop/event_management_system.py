"""
event_management_system.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A command-line Event Management System built with Python OOP.

Features
  • Create / update / delete events with capacity limits
  • Register & remove participants per event
  • Capacity enforcement with waitlist support
  • Search events by date, title, or location
  • Participant lookup across all events
  • Live statistics dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from datetime import datetime, date, timedelta
from typing import Optional


# ─────────────────────────────────────────────────────────────
#  CONSTANTS & ANSI COLOURS
# ─────────────────────────────────────────────────────────────
DATE_FMT     = "%Y-%m-%d"
DISPLAY_DATE = "%A, %d %B %Y"

CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

ACCENT_COLOURS = [CYAN, GREEN, YELLOW, MAGENTA, BLUE]


# ─────────────────────────────────────────────────────────────
#  PARTICIPANT
# ─────────────────────────────────────────────────────────────
class Participant:
    """Represents a person who can be registered to events."""

    _id_counter = 1

    def __init__(self, name: str, email: str, phone: str = ""):
        if not name.strip():
            raise ValueError("Participant name cannot be empty.")
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError(f"Invalid email address: '{email}'.")

        self._participant_id = f"PAR-{Participant._id_counter:04d}"
        Participant._id_counter += 1

        self._name       = name.strip()
        self._email      = email.strip().lower()
        self._phone      = phone.strip()
        self._registered = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── properties ───────────────────────────────────────────
    @property
    def participant_id(self) -> str: return self._participant_id
    @property
    def name(self) -> str:           return self._name
    @property
    def email(self) -> str:          return self._email
    @property
    def phone(self) -> str:          return self._phone
    @property
    def registered(self) -> str:     return self._registered

    def update(self, name: Optional[str]=None, email: Optional[str]=None,
               phone: Optional[str]=None):
        if name is not None:
            if not name.strip():
                raise ValueError("Name cannot be empty.")
            self._name = name.strip()
        if email is not None:
            if "@" not in email or "." not in email.split("@")[-1]:
                raise ValueError(f"Invalid email: '{email}'.")
            self._email = email.strip().lower()
        if phone is not None:
            self._phone = phone.strip()

    def summary_row(self, colour: str = CYAN, index: int = 0) -> str:
        phone_display = self._phone if self._phone else "—"
        return (
            f"    {DIM}{index:>2}.{RESET}  "
            f"{colour}{self._participant_id}{RESET}  "
            f"{BOLD}{self._name:<25}{RESET}  "
            f"{self._email:<32}  "
            f"{DIM}{phone_display}{RESET}"
        )

    def detail_card(self) -> str:
        sep = f"  {'─' * 58}"
        return "\n".join([
            sep,
            f"  {BOLD}{CYAN}{self._participant_id}{RESET}",
            f"  {BOLD}Name       :{RESET} {self._name}",
            f"  {BOLD}Email      :{RESET} {self._email}",
            f"  {BOLD}Phone      :{RESET} {self._phone or '—'}",
            f"  {BOLD}Registered :{RESET} {self._registered}",
            sep,
        ])

    def __str__(self) -> str:
        return self.detail_card()

    def __repr__(self) -> str:
        return f"Participant({self._participant_id!r}, {self._name!r})"


# ─────────────────────────────────────────────────────────────
#  EVENT
# ─────────────────────────────────────────────────────────────
class Event:
    """Represents an organised event with a participant roster."""

    _id_counter = 1

    def __init__(self, title: str, description: str, event_date: date,
                 location: str, capacity: int):
        self._validate_inputs(title, capacity)
        self._event_id    = f"EVT-{Event._id_counter:04d}"
        Event._id_counter += 1
        self._title       = title.strip()
        self._description = description.strip()
        self._date        = event_date
        self._location    = location.strip() or "TBD"
        self._capacity    = capacity
        self._participants: dict[str, Participant] = {}
        self._waitlist:     list[Participant]      = []
        self._created_at  = datetime.now().strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _validate_inputs(title: str, capacity: int):
        if not title.strip():
            raise ValueError("Event title cannot be empty.")
        if capacity < 1:
            raise ValueError("Capacity must be at least 1.")

    # ── properties ───────────────────────────────────────────
    @property
    def event_id(self) -> str:          return self._event_id
    @property
    def title(self) -> str:             return self._title
    @property
    def description(self) -> str:       return self._description
    @property
    def date(self) -> date:             return self._date
    @property
    def location(self) -> str:          return self._location
    @property
    def capacity(self) -> int:          return self._capacity
    @property
    def registered_count(self) -> int:  return len(self._participants)
    @property
    def waitlist_count(self) -> int:    return len(self._waitlist)
    @property
    def available_slots(self) -> int:   return self._capacity - len(self._participants)
    @property
    def is_full(self) -> bool:          return len(self._participants) >= self._capacity
    @property
    def is_past(self) -> bool:          return self._date < date.today()
    @property
    def created_at(self) -> str:        return self._created_at

    def get_participants(self) -> list:
        return list(self._participants.values())

    def get_waitlist(self) -> list:
        return list(self._waitlist)

    def update(self, title: Optional[str]=None, description: Optional[str]=None,
               event_date: Optional[date]=None, location: Optional[str]=None,
               capacity: Optional[int]=None):
        new_title    = title.strip() if title is not None else self._title
        new_capacity = capacity if capacity is not None else self._capacity
        self._validate_inputs(new_title, new_capacity)
        if new_capacity < self.registered_count:
            raise ValueError(
                f"New capacity ({new_capacity}) is less than current "
                f"registrations ({self.registered_count})."
            )
        self._title       = new_title
        if description is not None: self._description = description.strip()
        if event_date  is not None: self._date        = event_date
        if location    is not None: self._location    = location.strip() or "TBD"
        self._capacity = new_capacity

    def register(self, participant: "Participant") -> str:
        pid = participant.participant_id
        if pid in self._participants:
            return "duplicate_registered"
        if any(p.participant_id == pid for p in self._waitlist):
            return "duplicate_waitlisted"
        if self.is_full:
            self._waitlist.append(participant)
            return "waitlisted"
        self._participants[pid] = participant
        return "registered"

    def remove_participant(self, participant_id: str) -> Optional["Participant"]:
        pid = participant_id.upper()
        if pid in self._participants:
            removed = self._participants.pop(pid)
            if self._waitlist:
                promoted = self._waitlist.pop(0)
                self._participants[promoted.participant_id] = promoted
            return removed
        for i, p in enumerate(self._waitlist):
            if p.participant_id == pid:
                return self._waitlist.pop(i)
        return None

    def has_participant(self, participant_id: str) -> bool:
        return participant_id.upper() in self._participants

    def _capacity_bar(self, width: int = 20) -> str:
        filled = int((self.registered_count / self._capacity) * width)
        bar    = "█" * filled + "░" * (width - filled)
        pct    = int((self.registered_count / self._capacity) * 100)
        colour = RED if pct >= 90 else YELLOW if pct >= 60 else GREEN
        return f"{colour}{bar}{RESET} {colour}{pct}%{RESET}"

    def summary_row(self, colour: str = CYAN) -> str:
        status = f"{RED}FULL{RESET}" if self.is_full else f"{GREEN}{self.available_slots} left{RESET}"
        past   = f" {DIM}[past]{RESET}" if self.is_past else ""
        return (
            f"  {colour}{self._event_id}{RESET}  "
            f"{self._date.strftime(DATE_FMT)}  "
            f"{colour}{BOLD}{self._title[:32]:<32}{RESET}  "
            f"{self._location[:22]:<22}  "
            f"{self.registered_count:>3}/{self._capacity:<3}  "
            f"{status}{past}"
        )

    def detail_card(self, show_participants: bool = True) -> str:
        sep     = f"  {'─' * 62}"
        wl_line = (f"  {BOLD}Waitlist   :{RESET} {self.waitlist_count} person(s)"
                   if self._waitlist else "")
        past_tag = (f"  {DIM}[Past Event]{RESET}" if self.is_past
                    else f"  {GREEN}[Upcoming]{RESET}")

        lines = [
            sep,
            f"  {BOLD}{CYAN}{self._event_id}{RESET}  {past_tag}",
            f"  {BOLD}Title      :{RESET} {self._title}",
            f"  {BOLD}Description:{RESET} {self._description or '—'}",
            f"  {BOLD}Date       :{RESET} {self._date.strftime(DISPLAY_DATE)}",
            f"  {BOLD}Location   :{RESET} {self._location}",
            f"  {BOLD}Capacity   :{RESET} {self.registered_count}/{self._capacity}  "
            f"{self._capacity_bar()}",
        ]
        if wl_line:
            lines.append(wl_line)
        lines.append(f"  {BOLD}Created    :{RESET} {self._created_at}")

        if show_participants and self._participants:
            lines.append(f"\n  {BOLD}Registered Participants:{RESET}")
            lines.append(
                f"    {'#':>3}  {'ID':<10}  {'Name':<25}  {'Email':<32}  Phone"
            )
            lines.append(f"    {'─' * 85}")
            for i, p in enumerate(self._participants.values(), 1):
                colour = ACCENT_COLOURS[i % len(ACCENT_COLOURS)]
                lines.append(p.summary_row(colour, i))

        if show_participants and self._waitlist:
            lines.append(f"\n  {BOLD}{YELLOW}Waitlist:{RESET}")
            for i, p in enumerate(self._waitlist, 1):
                lines.append(p.summary_row(YELLOW, i))

        lines.append(sep)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.detail_card()

    def __repr__(self) -> str:
        return f"Event({self._event_id!r}, {self._title!r}, {self._date})"


# ─────────────────────────────────────────────────────────────
#  EVENT MANAGER
# ─────────────────────────────────────────────────────────────
class EventManager:
    """Central coordinator for events and global participant registry."""

    def __init__(self, org_name: str = "My Organisation"):
        self._org_name    = org_name
        self._events:       dict[str, Event]       = {}
        self._participants: dict[str, Participant] = {}

    # ── event CRUD ───────────────────────────────────────────
    def create_event(self, title: str, description: str, event_date: date,
                     location: str, capacity: int) -> Event:
        evt = Event(title, description, event_date, location, capacity)
        self._events[evt.event_id] = evt
        return evt

    def get_event(self, event_id: str) -> Optional[Event]:
        return self._events.get(event_id.upper())

    def update_event(self, event_id: str, **kwargs) -> Event:
        evt = self._require_event(event_id)
        evt.update(**kwargs)
        return evt

    def delete_event(self, event_id: str) -> Event:
        evt = self._require_event(event_id)
        del self._events[event_id.upper()]
        return evt

    def all_events(self, ascending: bool = True) -> list:
        return sorted(self._events.values(), key=lambda e: e.date,
                      reverse=not ascending)

    def search_by_title(self, keyword: str) -> list:
        kw = keyword.lower()
        return [e for e in self._events.values()
                if kw in e.title.lower() or kw in e.description.lower()]

    def search_by_date(self, target: date) -> list:
        return [e for e in self._events.values() if e.date == target]

    def search_by_location(self, keyword: str) -> list:
        kw = keyword.lower()
        return [e for e in self._events.values() if kw in e.location.lower()]

    def upcoming_events(self) -> list:
        today = date.today()
        return sorted([e for e in self._events.values() if e.date >= today],
                      key=lambda e: e.date)

    # ── participant CRUD ─────────────────────────────────────
    def add_participant(self, name: str, email: str, phone: str = "") -> Participant:
        for p in self._participants.values():
            if p.email == email.strip().lower():
                raise ValueError(
                    f"A participant with email '{email}' already exists "
                    f"({p.participant_id} – {p.name})."
                )
        par = Participant(name, email, phone)
        self._participants[par.participant_id] = par
        return par

    def get_participant(self, participant_id: str) -> Optional[Participant]:
        return self._participants.get(participant_id.upper())

    def find_by_email(self, email: str) -> Optional[Participant]:
        email = email.strip().lower()
        return next((p for p in self._participants.values()
                     if p.email == email), None)

    def update_participant(self, participant_id: str, **kwargs) -> Participant:
        par = self._require_participant(participant_id)
        new_email = kwargs.get("email")
        if new_email:
            existing = self.find_by_email(new_email)
            if existing and existing.participant_id != par.participant_id:
                raise ValueError(
                    f"Email '{new_email}' is already used by "
                    f"{existing.participant_id} – {existing.name}."
                )
        par.update(**kwargs)
        return par

    def all_participants(self) -> list:
        return sorted(self._participants.values(), key=lambda p: p.name)

    # ── registrations ────────────────────────────────────────
    def register_participant(self, event_id: str, participant_id: str) -> str:
        evt = self._require_event(event_id)
        par = self._require_participant(participant_id)
        return evt.register(par)

    def remove_participant(self, event_id: str, participant_id: str) -> Participant:
        evt     = self._require_event(event_id)
        removed = evt.remove_participant(participant_id)
        if removed is None:
            raise KeyError(
                f"Participant '{participant_id.upper()}' is not registered "
                f"for event '{event_id.upper()}'."
            )
        return removed

    def participant_events(self, participant_id: str) -> list:
        pid = participant_id.upper()
        return [e for e in self._events.values() if e.has_participant(pid)]

    # ── statistics ───────────────────────────────────────────
    def statistics(self) -> dict:
        today        = date.today()
        total_events = len(self._events)
        upcoming     = sum(1 for e in self._events.values() if e.date >= today)
        full_events  = sum(1 for e in self._events.values() if e.is_full)
        total_regs   = sum(e.registered_count for e in self._events.values())
        total_cap    = sum(e.capacity for e in self._events.values())
        waitlisted   = sum(e.waitlist_count for e in self._events.values())
        return {
            "total_events":        total_events,
            "upcoming":            upcoming,
            "past":                total_events - upcoming,
            "full_events":         full_events,
            "total_participants":  len(self._participants),
            "total_registrations": total_regs,
            "total_capacity":      total_cap,
            "waitlisted":          waitlisted,
            "fill_rate_pct":       round((total_regs / total_cap * 100)
                                        if total_cap else 0, 1),
        }

    # ── private helpers ──────────────────────────────────────
    def _require_event(self, event_id: str) -> Event:
        evt = self.get_event(event_id)
        if not evt:
            raise KeyError(f"Event '{event_id.upper()}' not found.")
        return evt

    def _require_participant(self, participant_id: str) -> Participant:
        par = self.get_participant(participant_id)
        if not par:
            raise KeyError(f"Participant '{participant_id.upper()}' not found.")
        return par


# ─────────────────────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────────────────────
def _sep(char: str = "═", width: int = 66):
    print(char * width)

def _header(title: str):
    _sep()
    print(f"  {BOLD}{title}{RESET}")
    _sep()

def _inp(prompt: str) -> str:
    return input(f"  {prompt}").strip()

def _inp_optional(prompt: str, current: str = "") -> Optional[str]:
    hint = f" [{current}]" if current else ""
    raw  = input(f"  {prompt}{hint}: ").strip()
    return raw if raw else None

def _parse_date(raw: str) -> date:
    try:
        return datetime.strptime(raw.strip(), DATE_FMT).date()
    except ValueError:
        raise ValueError(f"Invalid date '{raw}'. Use YYYY-MM-DD.")

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

def _input_int(prompt: str, lo: int = 1, hi: int = 100_000,
               default: Optional[int] = None) -> int:
    hint = f" [{default}]" if default is not None else f" ({lo}–{hi})"
    while True:
        raw = input(f"  {prompt}{hint}: ").strip()
        if not raw and default is not None:
            return default
        if raw.isdigit() and lo <= int(raw) <= hi:
            return int(raw)
        print(f"  {RED}✖  Enter a whole number between {lo} and {hi}.{RESET}")

def _display_event_table(events: list, heading: str = "Events"):
    if not events:
        print(f"  {DIM}No {heading.lower()} found.{RESET}")
        return
    _header(heading)
    print(f"  {BOLD}{'ID':<10}  {'Date':<12}  {'Title':<32}  "
          f"{'Location':<22}  {'Reg/Cap':<8}  Status{RESET}")
    print(f"  {'─' * 100}")
    for i, evt in enumerate(events):
        colour = ACCENT_COLOURS[i % len(ACCENT_COLOURS)]
        print(evt.summary_row(colour))

def _display_participant_table(participants: list, heading: str = "Participants"):
    if not participants:
        print(f"  {DIM}No {heading.lower()} found.{RESET}")
        return
    _header(heading)
    print(f"    {'#':>3}  {BOLD}{'ID':<10}  {'Name':<25}  {'Email':<32}  Phone{RESET}")
    print(f"    {'─' * 82}")
    for i, par in enumerate(participants, 1):
        colour = ACCENT_COLOURS[i % len(ACCENT_COLOURS)]
        print(par.summary_row(colour, i))


# ─────────────────────────────────────────────────────────────
#  MENU ACTIONS
# ─────────────────────────────────────────────────────────────
def action_create_event(mgr: EventManager):
    _header("Create New Event")
    title       = _inp("Title       : ")
    description = _inp("Description : ")
    evt_date    = _input_date("Date        ")
    location    = _inp("Location    : ")
    capacity    = _input_int("Capacity", lo=1, hi=100_000)
    try:
        evt = mgr.create_event(title, description, evt_date, location, capacity)
        print(f"\n  {GREEN}✔  Event created — {evt.event_id}{RESET}")
    except ValueError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_update_event(mgr: EventManager):
    _header("Update Event")
    _display_event_table(mgr.all_events(), "All Events")
    eid = _inp("\nEvent ID to update: ").upper()
    evt = mgr.get_event(eid)
    if not evt:
        print(f"  {RED}✖  Event '{eid}' not found.{RESET}"); return
    print(f"\n{evt.detail_card(show_participants=False)}")
    print(f"  {DIM}Leave blank to keep current value.{RESET}\n")

    raw_title    = _inp_optional("New title       ", evt.title)
    raw_desc     = _inp_optional("New description ", evt.description)
    raw_date     = _inp_optional("New date        ", evt.date.strftime(DATE_FMT))
    raw_location = _inp_optional("New location    ", evt.location)
    raw_capacity = _inp_optional("New capacity    ", str(evt.capacity))

    kwargs: dict = {}
    try:
        if raw_title:    kwargs["title"]       = raw_title
        if raw_desc:     kwargs["description"] = raw_desc
        if raw_date:     kwargs["event_date"]  = _parse_date(raw_date)
        if raw_location: kwargs["location"]    = raw_location
        if raw_capacity: kwargs["capacity"]    = int(raw_capacity)
        mgr.update_event(eid, **kwargs)
        print(f"\n  {GREEN}✔  {eid} updated successfully.{RESET}")
    except (ValueError, KeyError) as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_delete_event(mgr: EventManager):
    _header("Delete Event")
    _display_event_table(mgr.all_events(), "All Events")
    eid     = _inp("\nEvent ID to delete: ").upper()
    confirm = _inp("Type event ID again to confirm: ").upper()
    if eid != confirm:
        print(f"  {YELLOW}Deletion cancelled.{RESET}"); return
    try:
        evt = mgr.delete_event(eid)
        print(f"\n  {GREEN}✔  '{evt.title}' ({eid}) deleted.{RESET}")
    except KeyError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_view_event(mgr: EventManager):
    _header("View Event Detail")
    eid = _inp("Event ID: ").upper()
    evt = mgr.get_event(eid)
    if evt:
        print(); print(evt.detail_card(show_participants=True))
    else:
        print(f"  {RED}✖  Event '{eid}' not found.{RESET}")


def action_display_all_events(mgr: EventManager):
    _display_event_table(mgr.all_events(), "All Events")


def action_add_participant(mgr: EventManager):
    _header("Add New Participant")
    name  = _inp("Full name   : ")
    email = _inp("Email       : ")
    phone = _inp("Phone (opt) : ")
    try:
        par = mgr.add_participant(name, email, phone)
        print(f"\n  {GREEN}✔  Participant added — {par.participant_id}{RESET}")
    except ValueError as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_update_participant(mgr: EventManager):
    _header("Update Participant")
    _display_participant_table(mgr.all_participants(), "All Participants")
    pid = _inp("\nParticipant ID to update: ").upper()
    par = mgr.get_participant(pid)
    if not par:
        print(f"  {RED}✖  Participant '{pid}' not found.{RESET}"); return
    print(f"\n{par.detail_card()}")
    print(f"  {DIM}Leave blank to keep current value.{RESET}\n")

    kwargs: dict = {}
    raw_name  = _inp_optional("New name  ", par.name)
    raw_email = _inp_optional("New email ", par.email)
    raw_phone = _inp_optional("New phone ", par.phone)
    if raw_name:  kwargs["name"]  = raw_name
    if raw_email: kwargs["email"] = raw_email
    if raw_phone: kwargs["phone"] = raw_phone
    try:
        mgr.update_participant(pid, **kwargs)
        print(f"\n  {GREEN}✔  {pid} updated.{RESET}")
    except (ValueError, KeyError) as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_list_participants(mgr: EventManager):
    _display_participant_table(mgr.all_participants(), "All Participants")


def action_register(mgr: EventManager):
    _header("Register Participant to Event")
    _display_event_table(mgr.upcoming_events(), "Upcoming Events")
    eid = _inp("\nEvent ID    : ").upper()
    evt = mgr.get_event(eid)
    if not evt:
        print(f"  {RED}✖  Event '{eid}' not found.{RESET}"); return

    print(f"\n  {CYAN}{evt.title}{RESET}  —  {evt.registered_count}/{evt.capacity} registered")
    print(f"\n  1. Use existing participant ID")
    print(f"  2. Register a new participant")
    sub = _inp("Choice: ")

    if sub == "1":
        pid = _inp("Participant ID: ").upper()
    elif sub == "2":
        name  = _inp("Name  : ")
        email = _inp("Email : ")
        phone = _inp("Phone : ")
        try:
            par = mgr.add_participant(name, email, phone)
            pid = par.participant_id
            print(f"  {GREEN}✔  New participant: {pid}{RESET}")
        except ValueError as e:
            print(f"  {RED}✖  {e}{RESET}"); return
    else:
        print(f"  {RED}✖  Invalid choice.{RESET}"); return

    try:
        result = mgr.register_participant(eid, pid)
        par    = mgr.get_participant(pid)
        pname  = par.name if par else pid
        msgs = {
            "registered":         f"  {GREEN}✔  {pname} registered for '{evt.title}'.{RESET}",
            "waitlisted":         f"  {YELLOW}⚠  Event full. {pname} added to waitlist (#{evt.waitlist_count}).{RESET}",
            "duplicate_registered": f"  {YELLOW}⚠  {pname} is already registered.{RESET}",
            "duplicate_waitlisted": f"  {YELLOW}⚠  {pname} is already on the waitlist.{RESET}",
        }
        print(f"\n{msgs.get(result, result)}")
    except (KeyError, ValueError) as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_remove_participant(mgr: EventManager):
    _header("Remove Participant from Event")
    _display_event_table(mgr.all_events(), "All Events")
    eid = _inp("\nEvent ID      : ").upper()
    evt = mgr.get_event(eid)
    if not evt:
        print(f"  {RED}✖  Event '{eid}' not found.{RESET}"); return
    print(f"\n{evt.detail_card(show_participants=True)}")
    pid = _inp("\nParticipant ID to remove: ").upper()
    try:
        removed = mgr.remove_participant(eid, pid)
        print(f"\n  {GREEN}✔  {removed.name} removed from '{evt.title}'.{RESET}")
        if evt.waitlist_count == 0 and evt.registered_count > 0:
            print(f"  {CYAN}ℹ  A waitlisted participant may have been promoted.{RESET}")
    except (KeyError, ValueError) as e:
        print(f"\n  {RED}✖  {e}{RESET}")


def action_search(mgr: EventManager):
    _header("Search Events")
    print("  1. By title / keyword")
    print("  2. By date")
    print("  3. By location")
    choice = _inp("Choice: ")
    if choice == "1":
        kw = _inp("Keyword: ")
        _display_event_table(mgr.search_by_title(kw), f'Events matching "{kw}"')
    elif choice == "2":
        target = _input_date("Date")
        _display_event_table(mgr.search_by_date(target),
                             f"Events on {target.strftime(DISPLAY_DATE)}")
    elif choice == "3":
        kw = _inp("Location keyword: ")
        _display_event_table(mgr.search_by_location(kw),
                             f'Events at "{kw}"')
    else:
        print(f"  {RED}✖  Invalid choice.{RESET}")


def action_participant_events(mgr: EventManager):
    _header("Events for a Participant")
    _display_participant_table(mgr.all_participants(), "All Participants")
    pid = _inp("\nParticipant ID: ").upper()
    par = mgr.get_participant(pid)
    if not par:
        print(f"  {RED}✖  Participant '{pid}' not found.{RESET}"); return
    events = mgr.participant_events(pid)
    print(f"\n  {BOLD}{par.name}{RESET} is registered for {len(events)} event(s):")
    _display_event_table(events, f"Events for {par.name}")


def action_statistics(mgr: EventManager):
    _header("Statistics Dashboard")
    s = mgr.statistics()
    rows = [
        ("Total events",           s["total_events"],        CYAN),
        ("Upcoming",               s["upcoming"],            GREEN),
        ("Past",                   s["past"],                DIM),
        ("Full events",            s["full_events"],         RED if s["full_events"] else GREEN),
        ("Total participants",     s["total_participants"],  CYAN),
        ("Total registrations",    s["total_registrations"], MAGENTA),
        ("On waitlist",            s["waitlisted"],          YELLOW),
    ]
    for label, val, colour in rows:
        bar = "█" * min(val, 40)
        print(f"  {label:<28} {colour}{val:>4}  {bar}{RESET}")
    pct = s["fill_rate_pct"]
    c   = RED if pct >= 90 else YELLOW if pct >= 60 else GREEN
    bar = "█" * int(pct // 5)
    print(f"  {'Overall fill rate':<28} {c}{pct}%  {bar}{RESET}")


# ─────────────────────────────────────────────────────────────
#  SEED DATA
# ─────────────────────────────────────────────────────────────
def seed_demo_data(mgr: EventManager):
    today = date.today()
    e1 = mgr.create_event("Tech Summit 2026", "Annual tech conference",
                           today + timedelta(7), "Grand Convention Centre", 3)
    e2 = mgr.create_event("Python Workshop", "Hands-on OOP training",
                           today + timedelta(14), "Room 204, Tech Hub", 5)
    e3 = mgr.create_event("Team Quarterly Offsite", "Q2 planning & team building",
                           today + timedelta(21), "Mountain Retreat Lodge", 4)
    mgr.create_event("Past Hackathon", "24-hour coding marathon",
                     today - timedelta(10), "Innovation Lab", 20)

    alice = mgr.add_participant("Alice Johnson",  "alice@example.com", "555-0101")
    bob   = mgr.add_participant("Bob Martinez",   "bob@example.com",   "555-0202")
    carol = mgr.add_participant("Carol Williams", "carol@example.com")
    diana = mgr.add_participant("Diana Chen",     "diana@example.com", "555-0404")
    evan  = mgr.add_participant("Evan Torres",    "evan@example.com")

    for p in (alice, bob, carol):
        mgr.register_participant(e1.event_id, p.participant_id)
    mgr.register_participant(e1.event_id, diana.participant_id)   # → waitlisted

    for p in (alice, evan, diana):
        mgr.register_participant(e2.event_id, p.participant_id)

    for p in (bob, carol):
        mgr.register_participant(e3.event_id, p.participant_id)


# ─────────────────────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────────────────────
MENU = f"""
  {BOLD}┌──────────────────────────────────────────────────┐
  │         EVENT MANAGEMENT SYSTEM                  │
  ├──────────────────────────────────────────────────┤
  │  {CYAN}EVENTS{RESET}{BOLD}                                           │
  │{RESET}    1.  Create Event                              {BOLD}│
  │{RESET}    2.  Update Event                              {BOLD}│
  │{RESET}    3.  Delete Event                              {BOLD}│
  │{RESET}    4.  View Event Detail                         {BOLD}│
  │{RESET}    5.  Display All Events                        {BOLD}│
  │{RESET}    6.  Search Events                             {BOLD}│
  │{RESET}    7.  Upcoming Events                           {BOLD}│
  │  {CYAN}PARTICIPANTS{RESET}{BOLD}                                      │
  │{RESET}    8.  Add Participant                           {BOLD}│
  │{RESET}    9.  Update Participant                        {BOLD}│
  │{RESET}   10.  List All Participants                     {BOLD}│
  │  {CYAN}REGISTRATIONS{RESET}{BOLD}                                     │
  │{RESET}   11.  Register Participant to Event             {BOLD}│
  │{RESET}   12.  Remove Participant from Event             {BOLD}│
  │{RESET}   13.  View Participant's Events                 {BOLD}│
  │  {CYAN}REPORTS{RESET}{BOLD}                                           │
  │{RESET}   14.  Statistics Dashboard                      {BOLD}│
  │{RESET}    0.  Exit                                      {BOLD}│
  └──────────────────────────────────────────────────┘{RESET}"""

ACTIONS = {
    "1":  action_create_event,
    "2":  action_update_event,
    "3":  action_delete_event,
    "4":  action_view_event,
    "5":  action_display_all_events,
    "6":  action_search,
    "7":  lambda m: _display_event_table(m.upcoming_events(), "Upcoming Events"),
    "8":  action_add_participant,
    "9":  action_update_participant,
    "10": action_list_participants,
    "11": action_register,
    "12": action_remove_participant,
    "13": action_participant_events,
    "14": action_statistics,
}


def _banner():
    print()
    _sep("═")
    print(f"""
  {BOLD}{CYAN}
   ███████╗██╗   ██╗███████╗███╗   ██╗████████╗███████╗
   ██╔════╝██║   ██║██╔════╝████╗  ██║╚══██╔══╝██╔════╝
   █████╗  ██║   ██║█████╗  ██╔██╗ ██║   ██║   ███████╗
   ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║   ██║   ╚════██║
   ███████╗ ╚████╔╝ ███████╗██║ ╚████║   ██║   ███████║
   ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝{RESET}
  {BOLD}         M A N A G E M E N T   S Y S T E M{RESET}
  {DIM}    Organise events. Manage people. Stay in control.{RESET}
""")
    _sep("═")
    print()


def main():
    _banner()
    org = _inp("Organisation name: ") or "My Organisation"
    mgr = EventManager(org)

    load = _inp("Load demo data? (y/n): ").lower()
    if load == "y":
        seed_demo_data(mgr)
        s = mgr.statistics()
        print(
            f"\n  {GREEN}✔  Demo data loaded — "
            f"{s['total_events']} events, "
            f"{s['total_participants']} participants, "
            f"{s['total_registrations']} registrations "
            f"(1 waitlisted).{RESET}"
        )

    while True:
        print(MENU)
        choice = _inp("Select option: ")
        if choice == "0":
            print(f"\n  {CYAN}Goodbye! Stay organised. 👋{RESET}\n")
            break
        elif choice in ACTIONS:
            print()
            ACTIONS[choice](mgr)
            input(f"\n  {DIM}Press Enter to return to menu…{RESET}")
        else:
            print(f"  {RED}✖  Unrecognised option. Please try again.{RESET}")


if __name__ == "__main__":
    main()