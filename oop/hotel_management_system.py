"""
hotel_management_system.py
A command-line hotel management simulator using Python OOP principles.
"""

from __future__ import annotations
import os
import datetime
from enum import Enum


# ──────────────────────────────────────────────
#  Enums & Constants
# ──────────────────────────────────────────────

class RoomType(Enum):
    SINGLE    = "Single"
    DOUBLE    = "Double"
    SUITE     = "Suite"
    DELUXE    = "Deluxe"
    PENTHOUSE = "Penthouse"


class RoomStatus(Enum):
    AVAILABLE  = "Available"
    RESERVED   = "Reserved"
    OCCUPIED   = "Occupied"
    MAINTENANCE = "Maintenance"


CURRENCY = "$"
DIVIDER  = "─" * 72
DIVIDER2 = "═" * 72


# ──────────────────────────────────────────────
#  Guest
# ──────────────────────────────────────────────

class Guest:
    """Stores personal and contact information for a hotel guest."""

    _id_counter: int = 1000

    def __init__(
        self,
        name: str,
        phone: str,
        email: str,
        guest_id: int | None = None,
    ) -> None:
        if guest_id is not None:
            self.__id = guest_id
        else:
            self.__id = Guest._id_counter
            Guest._id_counter += 1

        self.name  = name
        self.phone = phone
        self.email = email

    # ── properties ────────────────────────────

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip().title()
        if not value:
            raise ValueError("Guest name cannot be empty.")
        self.__name = value

    @property
    def phone(self) -> str:
        return self.__phone

    @phone.setter
    def phone(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Phone number cannot be empty.")
        self.__phone = value

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, value: str) -> None:
        value = value.strip().lower()
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email address.")
        self.__email = value

    # ── helpers ───────────────────────────────

    def summary(self) -> str:
        return (
            f"  [Guest #{self.__id}]  {self.__name:<26}  "
            f"📞 {self.__phone:<16}  ✉  {self.__email}"
        )

    def __str__(self) -> str:
        return self.summary()

    def __repr__(self) -> str:
        return f"Guest(id={self.__id}, name={self.__name!r})"


# ──────────────────────────────────────────────
#  Reservation
# ──────────────────────────────────────────────

class Reservation:
    """Links a Guest to a Room for a specific date range."""

    _counter: int = 5000

    def __init__(
        self,
        guest: Guest,
        room_number: str,
        check_in: datetime.date,
        check_out: datetime.date,
    ) -> None:
        if check_out <= check_in:
            raise ValueError("Check-out date must be after check-in date.")

        self.__id         = Reservation._counter
        Reservation._counter += 1
        self.__guest      = guest
        self.__room_number = room_number
        self.__check_in   = check_in
        self.__check_out  = check_out
        self.__created_at = datetime.datetime.now()
        self.__is_active  = True

    # ── read-only properties ──────────────────

    @property
    def id(self) -> int:
        return self.__id

    @property
    def guest(self) -> Guest:
        return self.__guest

    @property
    def room_number(self) -> str:
        return self.__room_number

    @property
    def check_in(self) -> datetime.date:
        return self.__check_in

    @property
    def check_out(self) -> datetime.date:
        return self.__check_out

    @property
    def nights(self) -> int:
        return (self.__check_out - self.__check_in).days

    @property
    def is_active(self) -> bool:
        return self.__is_active

    def cancel(self) -> None:
        self.__is_active = False

    # ── helpers ───────────────────────────────

    def __str__(self) -> str:
        status = "ACTIVE" if self.__is_active else "CANCELLED"
        return (
            f"  [Res #{self.__id}]  Room {self.__room_number:<5}  "
            f"Guest: {self.__guest.name:<22}  "
            f"{self.__check_in} → {self.__check_out}  "
            f"({self.nights} night{'s' if self.nights != 1 else ''})  [{status}]"
        )


# ──────────────────────────────────────────────
#  Room
# ──────────────────────────────────────────────

class Room:
    """Represents a single hotel room."""

    def __init__(
        self,
        room_number: str,
        room_type: RoomType,
        price_per_night: float,
        floor: int = 1,
    ) -> None:
        self.__room_number     = str(room_number).strip().upper()
        self.room_type         = room_type
        self.price_per_night   = price_per_night
        self.__floor           = floor
        self.__status          = RoomStatus.AVAILABLE
        self.__current_guest: Guest | None = None
        self.__reservation: Reservation | None = None

    # ── properties ────────────────────────────

    @property
    def room_number(self) -> str:
        return self.__room_number

    @property
    def room_type(self) -> RoomType:
        return self.__room_type

    @room_type.setter
    def room_type(self, value: RoomType) -> None:
        if not isinstance(value, RoomType):
            raise ValueError("Invalid room type.")
        self.__room_type = value

    @property
    def price_per_night(self) -> float:
        return self.__price

    @price_per_night.setter
    def price_per_night(self, value: float) -> None:
        value = float(value)
        if value <= 0:
            raise ValueError("Price must be greater than zero.")
        self.__price = round(value, 2)

    @property
    def floor(self) -> int:
        return self.__floor

    @property
    def status(self) -> RoomStatus:
        return self.__status

    @property
    def current_guest(self) -> Guest | None:
        return self.__current_guest

    @property
    def current_reservation(self) -> Reservation | None:
        return self.__reservation

    @property
    def is_available(self) -> bool:
        return self.__status == RoomStatus.AVAILABLE

    # ── state transitions ─────────────────────

    def reserve(self, reservation: Reservation) -> None:
        self.__status      = RoomStatus.RESERVED
        self.__reservation = reservation

    def check_in(self, guest: Guest) -> None:
        self.__status        = RoomStatus.OCCUPIED
        self.__current_guest = guest

    def check_out(self) -> None:
        self.__status        = RoomStatus.AVAILABLE
        self.__current_guest = None
        self.__reservation   = None

    def set_maintenance(self) -> None:
        self.__status = RoomStatus.MAINTENANCE

    def set_available(self) -> None:
        self.__status = RoomStatus.AVAILABLE

    # ── helpers ───────────────────────────────

    def status_badge(self) -> str:
        badges = {
            RoomStatus.AVAILABLE:   "🟢 Available",
            RoomStatus.RESERVED:    "🟡 Reserved",
            RoomStatus.OCCUPIED:    "🔴 Occupied",
            RoomStatus.MAINTENANCE: "🔧 Maintenance",
        }
        return badges[self.__status]

    def __str__(self) -> str:
        guest_info = ""
        if self.__current_guest:
            guest_info = f"  👤 {self.__current_guest.name}"
        elif self.__reservation:
            guest_info = f"  📋 {self.__reservation.guest.name} (reserved)"
        return (
            f"  [{self.__room_number:<4}]  Floor {self.__floor}  "
            f"{self.__room_type.value:<12}  "
            f"{CURRENCY}{self.__price:>8.2f}/night   "
            f"{self.status_badge():<20}{guest_info}"
        )

    def __repr__(self) -> str:
        return (
            f"Room(number={self.__room_number!r}, type={self.__room_type.value!r}, "
            f"price={self.__price}, status={self.__status.value!r})"
        )


# ──────────────────────────────────────────────
#  HotelManagement
# ──────────────────────────────────────────────

class HotelManagement:
    """Central system managing rooms, guests, and reservations."""

    def __init__(self, hotel_name: str = "Grand PyHotel") -> None:
        self.__name         = hotel_name
        self.__rooms: dict[str, Room]             = {}
        self.__guests: dict[int, Guest]           = {}
        self.__reservations: dict[int, Reservation] = {}

    # ── properties ────────────────────────────

    @property
    def name(self) -> str:
        return self.__name

    # ── Room management ───────────────────────

    def add_room(
        self,
        room_number: str,
        room_type: RoomType,
        price: float,
        floor: int = 1,
    ) -> str:
        room_number = str(room_number).strip().upper()
        if room_number in self.__rooms:
            return f"  ✗  Room {room_number} already exists."
        room = Room(room_number, room_type, price, floor)
        self.__rooms[room_number] = room
        return f"  ✓  Room {room_number} ({room_type.value}) added at {CURRENCY}{price:.2f}/night."

    def get_room(self, room_number: str) -> Room | None:
        return self.__rooms.get(room_number.strip().upper())

    def get_all_rooms(self) -> list[Room]:
        return sorted(self.__rooms.values(), key=lambda r: r.room_number)

    def get_available_rooms(
        self,
        room_type: RoomType | None = None,
    ) -> list[Room]:
        rooms = [r for r in self.__rooms.values() if r.is_available]
        if room_type:
            rooms = [r for r in rooms if r.room_type == room_type]
        return sorted(rooms, key=lambda r: r.price_per_night)

    def set_room_maintenance(self, room_number: str) -> str:
        room = self.get_room(room_number)
        if room is None:
            return f"  ✗  Room {room_number} not found."
        if room.status == RoomStatus.OCCUPIED:
            return f"  ✗  Room {room_number} is currently occupied."
        room.set_maintenance()
        return f"  ✓  Room {room_number} set to Maintenance."

    def set_room_available(self, room_number: str) -> str:
        room = self.get_room(room_number)
        if room is None:
            return f"  ✗  Room {room_number} not found."
        room.set_available()
        return f"  ✓  Room {room_number} is now Available."

    def total_rooms(self) -> int:
        return len(self.__rooms)

    # ── Guest management ──────────────────────

    def register_guest(self, name: str, phone: str, email: str) -> Guest:
        guest = Guest(name, phone, email)
        self.__guests[guest.id] = guest
        return guest

    def get_guest(self, guest_id: int) -> Guest | None:
        return self.__guests.get(guest_id)

    def find_guests_by_name(self, query: str) -> list[Guest]:
        q = query.lower()
        return [g for g in self.__guests.values() if q in g.name.lower()]

    def get_all_guests(self) -> list[Guest]:
        return list(self.__guests.values())

    # ── Reservation management ────────────────

    def make_reservation(
        self,
        room_number: str,
        guest: Guest,
        check_in: datetime.date,
        check_out: datetime.date,
    ) -> str:
        room = self.get_room(room_number)
        if room is None:
            return f"  ✗  Room {room_number} not found."
        if not room.is_available:
            return f"  ✗  Room {room_number} is not available ({room.status.value})."
        try:
            reservation = Reservation(guest, room.room_number, check_in, check_out)
        except ValueError as e:
            return f"  ✗  {e}"
        room.reserve(reservation)
        self.__reservations[reservation.id] = reservation
        nights = reservation.nights
        total  = nights * room.price_per_night
        return (
            f"  ✓  Reservation #{reservation.id} confirmed!\n"
            f"     Room {room.room_number} for {guest.name}  |  "
            f"{check_in} → {check_out}  ({nights} night{'s' if nights!=1 else ''})  |  "
            f"Total: {CURRENCY}{total:,.2f}"
        )

    def check_in_guest(self, room_number: str) -> str:
        room = self.get_room(room_number)
        if room is None:
            return f"  ✗  Room {room_number} not found."
        if room.status == RoomStatus.OCCUPIED:
            return f"  ✗  Room {room_number} is already occupied."
        if room.status == RoomStatus.AVAILABLE:
            return f"  ✗  Room {room_number} has no reservation. Make a reservation first."
        if room.status == RoomStatus.MAINTENANCE:
            return f"  ✗  Room {room_number} is under maintenance."
        guest = room.current_reservation.guest
        room.check_in(guest)
        return (
            f"  ✓  Check-in successful!\n"
            f"     Welcome, {guest.name}!  Room {room_number} is now occupied."
        )

    def check_out_guest(self, room_number: str) -> str:
        room = self.get_room(room_number)
        if room is None:
            return f"  ✗  Room {room_number} not found."
        if room.status != RoomStatus.OCCUPIED:
            return f"  ✗  Room {room_number} is not occupied."
        guest     = room.current_guest
        res       = room.current_reservation
        bill_info = ""
        if res:
            nights   = res.nights
            total    = nights * room.price_per_night
            bill_info = (
                f"\n     Stay: {res.check_in} → {res.check_out}  "
                f"({nights} night{'s' if nights!=1 else ''})  |  "
                f"Bill: {CURRENCY}{total:,.2f}"
            )
            res.cancel()
        room.check_out()
        return (
            f"  ✓  Check-out successful!\n"
            f"     Goodbye, {guest.name}!  Room {room_number} is now available.{bill_info}"
        )

    def cancel_reservation(self, reservation_id: int) -> str:
        res = self.__reservations.get(reservation_id)
        if res is None:
            return f"  ✗  Reservation #{reservation_id} not found."
        if not res.is_active:
            return f"  ✗  Reservation #{reservation_id} is already cancelled."
        room = self.get_room(res.room_number)
        if room and room.status == RoomStatus.RESERVED:
            room.set_available()
        res.cancel()
        return f"  ✓  Reservation #{reservation_id} cancelled. Room {res.room_number} is now available."

    def get_all_reservations(self, active_only: bool = True) -> list[Reservation]:
        if active_only:
            return [r for r in self.__reservations.values() if r.is_active]
        return list(self.__reservations.values())

    # ── Reporting ─────────────────────────────

    def occupancy_summary(self) -> dict:
        counts = {s: 0 for s in RoomStatus}
        for room in self.__rooms.values():
            counts[room.status] += 1
        return counts

    def revenue_summary(self) -> float:
        """Estimate revenue from all active reservations."""
        total = 0.0
        for res in self.__reservations.values():
            if res.is_active:
                room = self.get_room(res.room_number)
                if room:
                    total += res.nights * room.price_per_night
        return round(total, 2)


# ──────────────────────────────────────────────
#  CLI helpers
# ──────────────────────────────────────────────

def cls() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str, sub: str = "") -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    if sub:
        print(f"  {sub}")
    print(DIVIDER)


def prompt_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg).strip())
        except ValueError:
            print("  ✗  Please enter a whole number.")


def prompt_float(msg: str) -> float:
    while True:
        try:
            v = float(input(msg).strip())
            if v <= 0:
                print("  ✗  Value must be greater than zero.")
                continue
            return v
        except ValueError:
            print("  ✗  Please enter a number.")


def prompt_date(msg: str, default_offset: int = 0) -> datetime.date:
    default = datetime.date.today() + datetime.timedelta(days=default_offset)
    while True:
        raw = input(f"{msg} [YYYY-MM-DD, Enter for {default}]: ").strip()
        if not raw:
            return default
        try:
            return datetime.date.fromisoformat(raw)
        except ValueError:
            print("  ✗  Invalid date format. Use YYYY-MM-DD.")


def pick_room_type() -> RoomType:
    types = list(RoomType)
    print("\n  Room Types:")
    for i, rt in enumerate(types, 1):
        print(f"    {i}. {rt.value}")
    while True:
        choice = prompt_int("  Select type: ")
        if 1 <= choice <= len(types):
            return types[choice - 1]
        print("  ✗  Invalid selection.")


def pick_or_register_guest(hotel: HotelManagement) -> Guest | None:
    """Let the user choose an existing guest or register a new one."""
    print("\n  1. Register new guest")
    print("  2. Search existing guest by name")
    print("  3. Enter guest ID directly")
    sub = input("  Choice: ").strip()

    if sub == "1":
        return menu_register_guest(hotel, silent=True)
    elif sub == "2":
        query   = input("  Search name: ").strip()
        results = hotel.find_guests_by_name(query)
        if not results:
            print("  No guests found.")
            return None
        print(f"\n  Found {len(results)} guest(s):")
        for g in results:
            print(g)
        gid = prompt_int("\n  Enter Guest ID: ")
        return hotel.get_guest(gid)
    elif sub == "3":
        gid = prompt_int("  Enter Guest ID: ")
        g   = hotel.get_guest(gid)
        if g is None:
            print(f"  ✗  Guest #{gid} not found.")
        return g
    print("  ✗  Invalid choice.")
    return None


# ──────────────────────────────────────────────
#  Seed data
# ──────────────────────────────────────────────

def seed_hotel(hotel: HotelManagement) -> None:
    rooms = [
        ("101", RoomType.SINGLE,    89.00, 1),
        ("102", RoomType.SINGLE,    89.00, 1),
        ("103", RoomType.DOUBLE,   129.00, 1),
        ("104", RoomType.DOUBLE,   129.00, 1),
        ("201", RoomType.DOUBLE,   139.00, 2),
        ("202", RoomType.DELUXE,   199.00, 2),
        ("203", RoomType.DELUXE,   199.00, 2),
        ("301", RoomType.SUITE,    299.00, 3),
        ("302", RoomType.SUITE,    299.00, 3),
        ("401", RoomType.PENTHOUSE,599.00, 4),
    ]
    for num, rtype, price, floor in rooms:
        hotel.add_room(num, rtype, price, floor)

    # Sample guests
    g1 = hotel.register_guest("Alice Johnson",  "+1-555-0101", "alice@example.com")
    g2 = hotel.register_guest("Bob Martinez",   "+1-555-0202", "bob@example.com")
    g3 = hotel.register_guest("Clara Nguyen",   "+1-555-0303", "clara@example.com")

    # Sample reservations
    today = datetime.date.today()
    hotel.make_reservation("201", g1, today, today + datetime.timedelta(days=3))
    hotel.make_reservation("301", g2, today, today + datetime.timedelta(days=5))

    # Check in one guest
    hotel.check_in_guest("201")

    # One room under maintenance
    hotel.set_room_maintenance("104")


# ──────────────────────────────────────────────
#  Menu actions
# ──────────────────────────────────────────────

def menu_display_rooms(hotel: HotelManagement) -> None:
    print_header(f"ALL ROOMS  —  {hotel.name}", f"Total: {hotel.total_rooms()} rooms")
    summary = hotel.occupancy_summary()
    print(
        f"  🟢 Available: {summary[RoomStatus.AVAILABLE]}   "
        f"🟡 Reserved: {summary[RoomStatus.RESERVED]}   "
        f"🔴 Occupied: {summary[RoomStatus.OCCUPIED]}   "
        f"🔧 Maintenance: {summary[RoomStatus.MAINTENANCE]}\n"
    )
    print(f"  {'Room':<6}  {'Floor':<6} {'Type':<13} {'Price/Night':>12}   Status")
    print(f"  {'─'*6}  {'─'*6} {'─'*13} {'─'*12}   {'─'*20}")
    for room in hotel.get_all_rooms():
        print(room)


def menu_check_availability(hotel: HotelManagement) -> None:
    print_header("CHECK AVAILABILITY")
    print("  Filter by type? (leave blank for all)")
    print("  0. All types")
    types = list(RoomType)
    for i, rt in enumerate(types, 1):
        print(f"  {i}. {rt.value}")
    raw = input("\n  Choice [0]: ").strip()
    rt_filter = None
    if raw.isdigit() and 1 <= int(raw) <= len(types):
        rt_filter = types[int(raw) - 1]

    available = hotel.get_available_rooms(rt_filter)
    label     = f"({rt_filter.value})" if rt_filter else "(all types)"
    print_header(f"AVAILABLE ROOMS  {label}", f"{len(available)} room(s) available")
    if not available:
        print("  No rooms available matching that filter.")
        return
    print(f"  {'Room':<6}  {'Floor':<6} {'Type':<13} {'Price/Night':>12}")
    print(f"  {'─'*6}  {'─'*6} {'─'*13} {'─'*12}")
    for room in available:
        print(
            f"  [{room.room_number:<4}]  Floor {room.floor}  "
            f"{room.room_type.value:<13} {CURRENCY}{room.price_per_night:>8.2f}/night"
        )


def menu_add_room(hotel: HotelManagement) -> None:
    print_header("ADD NEW ROOM")
    room_number = input("  Room Number   : ").strip().upper()
    if not room_number:
        print("  ✗  Room number cannot be empty.")
        return
    floor       = prompt_int("  Floor         : ")
    room_type   = pick_room_type()
    price       = prompt_float("  Price/night   : $")
    print(f"\n{hotel.add_room(room_number, room_type, price, floor)}")


def menu_register_guest(
    hotel: HotelManagement,
    silent: bool = False,
) -> Guest | None:
    if not silent:
        print_header("REGISTER GUEST")
    try:
        name  = input("  Full Name  : ").strip()
        phone = input("  Phone      : ").strip()
        email = input("  Email      : ").strip()
        guest = hotel.register_guest(name, phone, email)
        print(f"\n  ✓  Guest registered: {guest.name}  (ID: #{guest.id})")
        return guest
    except ValueError as e:
        print(f"\n  ✗  {e}")
        return None


def menu_make_reservation(hotel: HotelManagement) -> None:
    print_header("MAKE RESERVATION")

    # Show available rooms first
    available = hotel.get_available_rooms()
    if not available:
        print("  No rooms currently available.")
        return
    print("  Available rooms:\n")
    print(f"  {'Room':<6}  {'Type':<13} {'Price/Night':>12}")
    print(f"  {'─'*6}  {'─'*13} {'─'*12}")
    for r in available:
        print(f"  [{r.room_number:<4}]  {r.room_type.value:<13} {CURRENCY}{r.price_per_night:>8.2f}/night")

    room_number = input("\n  Room Number  : ").strip().upper()
    guest       = pick_or_register_guest(hotel)
    if guest is None:
        return

    print()
    check_in  = prompt_date("  Check-in  date", default_offset=0)
    check_out = prompt_date("  Check-out date", default_offset=1)

    print(f"\n{hotel.make_reservation(room_number, guest, check_in, check_out)}")


def menu_check_in(hotel: HotelManagement) -> None:
    print_header("CHECK IN GUEST")
    # Show reserved rooms
    reserved = [r for r in hotel.get_all_rooms() if r.status == RoomStatus.RESERVED]
    if not reserved:
        print("  No rooms currently have active reservations.")
        return
    print("  Rooms with reservations:\n")
    for r in reserved:
        print(r)
    room_number = input("\n  Room Number to Check In : ").strip().upper()
    print(f"\n{hotel.check_in_guest(room_number)}")


def menu_check_out(hotel: HotelManagement) -> None:
    print_header("CHECK OUT GUEST")
    occupied = [r for r in hotel.get_all_rooms() if r.status == RoomStatus.OCCUPIED]
    if not occupied:
        print("  No rooms are currently occupied.")
        return
    print("  Occupied rooms:\n")
    for r in occupied:
        print(r)
    room_number = input("\n  Room Number to Check Out : ").strip().upper()
    print(f"\n{hotel.check_out_guest(room_number)}")


def menu_cancel_reservation(hotel: HotelManagement) -> None:
    print_header("CANCEL RESERVATION")
    active = hotel.get_all_reservations(active_only=True)
    if not active:
        print("  No active reservations.")
        return
    print("  Active reservations:\n")
    for res in active:
        print(res)
    res_id = prompt_int("\n  Reservation ID to cancel: ")
    confirm = input(f"  Cancel reservation #{res_id}? (y/n): ").strip().lower()
    if confirm == "y":
        print(f"\n{hotel.cancel_reservation(res_id)}")
    else:
        print("  ↩  Cancelled.")


def menu_view_reservations(hotel: HotelManagement) -> None:
    print_header("ALL RESERVATIONS")
    active = hotel.get_all_reservations(active_only=True)
    if not active:
        print("  No active reservations.")
        return
    print(f"  {len(active)} active reservation(s):\n")
    for res in active:
        print(res)


def menu_view_guests(hotel: HotelManagement) -> None:
    print_header(f"REGISTERED GUESTS  ({len(hotel.get_all_guests())} total)")
    guests = hotel.get_all_guests()
    if not guests:
        print("  No guests registered.")
        return
    for g in guests:
        print(g)


def menu_maintenance(hotel: HotelManagement) -> None:
    print_header("ROOM MAINTENANCE")
    print("  1. Set room → Maintenance")
    print("  2. Set room → Available")
    choice = input("\n  Choice: ").strip()
    room_number = input("  Room Number : ").strip().upper()
    if choice == "1":
        print(f"\n{hotel.set_room_maintenance(room_number)}")
    elif choice == "2":
        print(f"\n{hotel.set_room_available(room_number)}")
    else:
        print("  ✗  Invalid choice.")


def menu_dashboard(hotel: HotelManagement) -> None:
    print_header(f"DASHBOARD  —  {hotel.name}")
    summary  = hotel.occupancy_summary()
    total    = hotel.total_rooms()
    occupied = summary[RoomStatus.OCCUPIED]
    occ_rate = (occupied / total * 100) if total else 0
    revenue  = hotel.revenue_summary()

    print(f"  {'Total Rooms':<28}: {total}")
    print(f"  {'🟢 Available':<28}: {summary[RoomStatus.AVAILABLE]}")
    print(f"  {'🟡 Reserved':<28}: {summary[RoomStatus.RESERVED]}")
    print(f"  {'🔴 Occupied':<28}: {occupied}")
    print(f"  {'🔧 Under Maintenance':<28}: {summary[RoomStatus.MAINTENANCE]}")
    print(f"  {'Occupancy Rate':<28}: {occ_rate:.1f}%")
    print(f"  {'Estimated Revenue':<28}: {CURRENCY}{revenue:,.2f}")
    print(f"  {'Registered Guests':<28}: {len(hotel.get_all_guests())}")
    print(f"  {'Active Reservations':<28}: {len(hotel.get_all_reservations())}")


# ──────────────────────────────────────────────
#  Main menu
# ──────────────────────────────────────────────

MENU = """
  ╔══════════════════════════════════════╗
  ║      HOTEL MANAGEMENT SYSTEM         ║
  ╠══════════════════════════════════════╣
  ║   ROOMS                              ║
  ║   1.  View all rooms                 ║
  ║   2.  Check availability             ║
  ║   3.  Add new room                   ║
  ║   4.  Room maintenance               ║
  ╠══════════════════════════════════════╣
  ║   GUESTS                             ║
  ║   5.  Register guest                 ║
  ║   6.  View all guests                ║
  ╠══════════════════════════════════════╣
  ║   RESERVATIONS                       ║
  ║   7.  Make reservation               ║
  ║   8.  Check in guest                 ║
  ║   9.  Check out guest                ║
  ║   10. View reservations              ║
  ║   11. Cancel reservation             ║
  ╠══════════════════════════════════════╣
  ║   12. Dashboard / Summary            ║
  ║   0.  Exit                           ║
  ╚══════════════════════════════════════╝"""

ACTIONS = {
    "1":  menu_display_rooms,
    "2":  menu_check_availability,
    "3":  menu_add_room,
    "4":  menu_maintenance,
    "5":  menu_register_guest,
    "6":  menu_view_guests,
    "7":  menu_make_reservation,
    "8":  menu_check_in,
    "9":  menu_check_out,
    "10": menu_view_reservations,
    "11": menu_cancel_reservation,
    "12": menu_dashboard,
}


def main() -> None:
    hotel = HotelManagement("Grand PyHotel")
    seed_hotel(hotel)

    print(f"\n{DIVIDER2}")
    print(f"  Welcome to {hotel.name} Management System")
    print(f"  {hotel.total_rooms()} rooms loaded  |  "
          f"Today: {datetime.date.today()}")
    print(DIVIDER2)

    first = True
    while True:
        if not first:
            cls()
        first = False
        print(MENU)
        summary = hotel.occupancy_summary()
        print(
            f"  🟢 {summary[RoomStatus.AVAILABLE]} avail  "
            f"🟡 {summary[RoomStatus.RESERVED]} reserved  "
            f"🔴 {summary[RoomStatus.OCCUPIED]} occupied  "
            f"🔧 {summary[RoomStatus.MAINTENANCE]} maintenance\n"
        )
        choice = input("  Select option: ").strip()

        if choice == "0":
            print(f"\n  Thank you for using {hotel.name} System. Goodbye!\n")
            break
        elif choice in ACTIONS:
            ACTIONS[choice](hotel)
        else:
            print("\n  ✗  Invalid option. Please try again.")

        input("\n  Press Enter to return to menu...")


if __name__ == "__main__":
    main()