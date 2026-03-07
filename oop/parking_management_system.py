"""
parking_management_system.py
A command-line parking lot management simulator using Python OOP principles.
"""

from __future__ import annotations
import os
import datetime
from enum import Enum


# ──────────────────────────────────────────────
#  Enums & Constants
# ──────────────────────────────────────────────

class VehicleType(Enum):
    MOTORCYCLE = "Motorcycle"
    CAR        = "Car"
    TRUCK      = "Truck"
    EV         = "Electric Vehicle"


class SpotType(Enum):
    MOTORCYCLE = "Motorcycle"
    COMPACT    = "Compact"
    STANDARD   = "Standard"
    LARGE      = "Large"
    EV         = "EV Charging"


# Hourly rates per vehicle type  ($/hr)
HOURLY_RATES: dict[VehicleType, float] = {
    VehicleType.MOTORCYCLE: 1.50,
    VehicleType.CAR:        3.00,
    VehicleType.TRUCK:      5.00,
    VehicleType.EV:         3.50,
}

# Which spot types accept which vehicle types
COMPATIBLE: dict[VehicleType, list[SpotType]] = {
    VehicleType.MOTORCYCLE: [SpotType.MOTORCYCLE, SpotType.COMPACT, SpotType.STANDARD],
    VehicleType.CAR:        [SpotType.COMPACT, SpotType.STANDARD, SpotType.LARGE],
    VehicleType.TRUCK:      [SpotType.LARGE],
    VehicleType.EV:         [SpotType.EV, SpotType.STANDARD, SpotType.LARGE],
}

CURRENCY  = "$"
DIVIDER   = "─" * 72
DIVIDER2  = "═" * 72
MIN_FEE   = 1.00   # minimum charge per visit


# ──────────────────────────────────────────────
#  ParkingRecord  (immutable receipt)
# ──────────────────────────────────────────────

class ParkingRecord:
    """Immutable receipt created when a vehicle exits."""

    _counter: int = 1

    def __init__(
        self,
        license_plate: str,
        vehicle_type: VehicleType,
        spot_id: str,
        entry_time: datetime.datetime,
        exit_time: datetime.datetime,
        fee: float,
    ) -> None:
        self.__record_id    = ParkingRecord._counter
        ParkingRecord._counter += 1
        self.__license_plate = license_plate
        self.__vehicle_type  = vehicle_type
        self.__spot_id       = spot_id
        self.__entry_time    = entry_time
        self.__exit_time     = exit_time
        self.__fee           = fee

    # ── read-only properties ──────────────────

    @property
    def record_id(self) -> int:       return self.__record_id
    @property
    def license_plate(self) -> str:   return self.__license_plate
    @property
    def vehicle_type(self) -> VehicleType: return self.__vehicle_type
    @property
    def spot_id(self) -> str:         return self.__spot_id
    @property
    def entry_time(self) -> datetime.datetime: return self.__entry_time
    @property
    def exit_time(self) -> datetime.datetime:  return self.__exit_time
    @property
    def fee(self) -> float:           return self.__fee

    @property
    def duration_hours(self) -> float:
        delta = self.__exit_time - self.__entry_time
        return round(delta.total_seconds() / 3600, 4)

    def __str__(self) -> str:
        dur = self.__exit_time - self.__entry_time
        hrs, rem = divmod(int(dur.total_seconds()), 3600)
        mins = rem // 60
        return (
            f"  [#{self.__record_id:<4}]  {self.__license_plate:<12}  "
            f"{self.__vehicle_type.value:<18}  Spot {self.__spot_id:<5}  "
            f"{self.__entry_time.strftime('%H:%M')} → {self.__exit_time.strftime('%H:%M')}  "
            f"({hrs}h {mins:02d}m)  Fee: {CURRENCY}{self.__fee:.2f}"
        )


# ──────────────────────────────────────────────
#  Vehicle
# ──────────────────────────────────────────────

class Vehicle:
    """Represents a vehicle entering the parking lot."""

    def __init__(
        self,
        license_plate: str,
        vehicle_type: VehicleType,
        owner_name: str = "",
    ) -> None:
        self.license_plate = license_plate
        self.vehicle_type  = vehicle_type
        self.owner_name    = owner_name
        self.__entry_time  = datetime.datetime.now()

    # ── properties ────────────────────────────

    @property
    def license_plate(self) -> str:
        return self.__license_plate

    @license_plate.setter
    def license_plate(self, value: str) -> None:
        value = value.strip().upper()
        if not value:
            raise ValueError("License plate cannot be empty.")
        self.__license_plate = value

    @property
    def vehicle_type(self) -> VehicleType:
        return self.__vehicle_type

    @vehicle_type.setter
    def vehicle_type(self, value: VehicleType) -> None:
        if not isinstance(value, VehicleType):
            raise ValueError("Invalid vehicle type.")
        self.__vehicle_type = value

    @property
    def owner_name(self) -> str:
        return self.__owner_name

    @owner_name.setter
    def owner_name(self, value: str) -> None:
        self.__owner_name = value.strip().title()

    @property
    def entry_time(self) -> datetime.datetime:
        return self.__entry_time

    @property
    def hourly_rate(self) -> float:
        return HOURLY_RATES[self.__vehicle_type]

    # ── helpers ───────────────────────────────

    def duration_str(self) -> str:
        delta = datetime.datetime.now() - self.__entry_time
        hrs, rem = divmod(int(delta.total_seconds()), 3600)
        mins = rem // 60
        return f"{hrs}h {mins:02d}m"

    def current_fee(self) -> float:
        delta   = datetime.datetime.now() - self.__entry_time
        hours   = delta.total_seconds() / 3600
        fee     = max(MIN_FEE, round(hours * self.__vehicle_type_rate(), 2))
        return fee

    def __vehicle_type_rate(self) -> float:
        return HOURLY_RATES[self.__vehicle_type]

    def __str__(self) -> str:
        owner = f"  Owner: {self.__owner_name}" if self.__owner_name else ""
        return (
            f"{self.__license_plate:<12}  "
            f"{self.__vehicle_type.value:<18}  "
            f"In: {self.__entry_time.strftime('%Y-%m-%d %H:%M')}  "
            f"({self.duration_str()}){owner}"
        )

    def __repr__(self) -> str:
        return f"Vehicle(plate={self.__license_plate!r}, type={self.__vehicle_type.value!r})"


# ──────────────────────────────────────────────
#  ParkingSpot
# ──────────────────────────────────────────────

class ParkingSpot:
    """Represents one physical parking spot in the lot."""

    def __init__(
        self,
        spot_id: str,
        spot_type: SpotType,
        floor: int = 1,
    ) -> None:
        self.__spot_id      = str(spot_id).strip().upper()
        self.__spot_type    = spot_type
        self.__floor        = floor
        self.__is_available = True
        self.__vehicle: Vehicle | None = None

    # ── properties ────────────────────────────

    @property
    def spot_id(self) -> str:
        return self.__spot_id

    @property
    def spot_type(self) -> SpotType:
        return self.__spot_type

    @property
    def floor(self) -> int:
        return self.__floor

    @property
    def is_available(self) -> bool:
        return self.__is_available

    @property
    def vehicle(self) -> Vehicle | None:
        return self.__vehicle

    # ── state transitions ─────────────────────

    def park(self, vehicle: Vehicle) -> None:
        self.__vehicle      = vehicle
        self.__is_available = False

    def vacate(self) -> Vehicle | None:
        departed            = self.__vehicle
        self.__vehicle      = None
        self.__is_available = True
        return departed

    def can_fit(self, vehicle_type: VehicleType) -> bool:
        return self.__spot_type in COMPATIBLE.get(vehicle_type, [])

    # ── helpers ───────────────────────────────

    def status_badge(self) -> str:
        return "🟢 Free" if self.__is_available else "🔴 Taken"

    def __str__(self) -> str:
        vehicle_info = ""
        if self.__vehicle:
            vehicle_info = f"  → {self.__vehicle.license_plate}"
        return (
            f"  [{self.__spot_id:<5}]  Floor {self.__floor}  "
            f"{self.__spot_type.value:<14}  {self.status_badge():<12}{vehicle_info}"
        )

    def __repr__(self) -> str:
        return (
            f"ParkingSpot(id={self.__spot_id!r}, type={self.__spot_type.value!r}, "
            f"available={self.__is_available})"
        )


# ──────────────────────────────────────────────
#  ParkingLot
# ──────────────────────────────────────────────

class ParkingLot:
    """
    Central manager: tracks all spots, parked vehicles,
    and completed parking records.
    """

    def __init__(self, name: str = "PyPark") -> None:
        self.__name     = name
        self.__spots:   dict[str, ParkingSpot]  = {}   # spot_id → spot
        self.__parked:  dict[str, str]           = {}   # license_plate → spot_id
        self.__records: list[ParkingRecord]      = []

    # ── properties ────────────────────────────

    @property
    def name(self) -> str:
        return self.__name

    # ── Spot management ───────────────────────

    def add_spot(
        self,
        spot_id: str,
        spot_type: SpotType,
        floor: int = 1,
    ) -> str:
        sid = spot_id.strip().upper()
        if sid in self.__spots:
            return f"  ✗  Spot {sid} already exists."
        self.__spots[sid] = ParkingSpot(sid, spot_type, floor)
        return f"  ✓  Spot {sid} ({spot_type.value}, Floor {floor}) added."

    def get_spot(self, spot_id: str) -> ParkingSpot | None:
        return self.__spots.get(spot_id.strip().upper())

    def total_spots(self) -> int:
        return len(self.__spots)

    def available_spots(
        self,
        vehicle_type: VehicleType | None = None,
    ) -> list[ParkingSpot]:
        spots = [s for s in self.__spots.values() if s.is_available]
        if vehicle_type:
            spots = [s for s in spots if s.can_fit(vehicle_type)]
        return sorted(spots, key=lambda s: (s.floor, s.spot_id))

    def occupied_spots(self) -> list[ParkingSpot]:
        return [s for s in self.__spots.values() if not s.is_available]

    # ── Vehicle operations ────────────────────

    def park_vehicle(
        self,
        license_plate: str,
        vehicle_type: VehicleType,
        owner_name: str = "",
        preferred_spot: str | None = None,
    ) -> str:
        plate = license_plate.strip().upper()

        if plate in self.__parked:
            sid = self.__parked[plate]
            return f"  ✗  Vehicle {plate} is already parked in spot {sid}."

        # Validate vehicle
        try:
            vehicle = Vehicle(plate, vehicle_type, owner_name)
        except ValueError as e:
            return f"  ✗  {e}"

        # Try preferred spot first
        if preferred_spot:
            psid = preferred_spot.strip().upper()
            spot = self.get_spot(psid)
            if spot is None:
                return f"  ✗  Spot {psid} does not exist."
            if not spot.is_available:
                return f"  ✗  Spot {psid} is already occupied."
            if not spot.can_fit(vehicle_type):
                return (
                    f"  ✗  Spot {psid} ({spot.spot_type.value}) "
                    f"is not compatible with {vehicle_type.value}."
                )
            spot.park(vehicle)
            self.__parked[plate] = psid
            return (
                f"  ✓  {vehicle_type.value} {plate} parked in spot {psid}  "
                f"(Floor {spot.floor})  Rate: {CURRENCY}{vehicle.hourly_rate:.2f}/hr"
            )

        # Auto-assign best available spot
        candidates = self.available_spots(vehicle_type)
        if not candidates:
            return (
                f"  ✗  No available spots for {vehicle_type.value}. "
                f"Lot is full for this vehicle type."
            )
        spot = candidates[0]
        spot.park(vehicle)
        self.__parked[plate] = spot.spot_id
        return (
            f"  ✓  {vehicle_type.value} {plate} parked in spot {spot.spot_id}  "
            f"(Floor {spot.floor})  Rate: {CURRENCY}{vehicle.hourly_rate:.2f}/hr"
        )

    def remove_vehicle(self, license_plate: str) -> str:
        plate = license_plate.strip().upper()

        if plate not in self.__parked:
            return f"  ✗  Vehicle {plate} is not currently parked here."

        spot_id = self.__parked[plate]
        spot    = self.get_spot(spot_id)
        vehicle = spot.vacate()
        del self.__parked[plate]

        # Calculate fee
        exit_time = datetime.datetime.now()
        delta     = exit_time - vehicle.entry_time
        hours     = delta.total_seconds() / 3600
        fee       = max(MIN_FEE, round(hours * vehicle.hourly_rate, 2))

        # Save record
        record = ParkingRecord(
            plate,
            vehicle.vehicle_type,
            spot_id,
            vehicle.entry_time,
            exit_time,
            fee,
        )
        self.__records.append(record)

        dur = vehicle.duration_str()
        return (
            f"  ✓  Vehicle {plate} has exited spot {spot_id}.\n"
            f"     Duration: {dur}  |  "
            f"Fee: {CURRENCY}{fee:.2f}  |  "
            f"Thank you!"
        )

    def calculate_fee(self, license_plate: str) -> str:
        plate = license_plate.strip().upper()
        if plate not in self.__parked:
            return f"  ✗  Vehicle {plate} is not currently parked here."
        spot_id = self.__parked[plate]
        vehicle = self.get_spot(spot_id).vehicle
        delta   = datetime.datetime.now() - vehicle.entry_time
        hours   = delta.total_seconds() / 3600
        fee     = max(MIN_FEE, round(hours * vehicle.hourly_rate, 2))
        return (
            f"  Vehicle : {plate}  ({vehicle.vehicle_type.value})\n"
            f"  Spot    : {spot_id}\n"
            f"  Parked  : {vehicle.entry_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"  Duration: {vehicle.duration_str()}\n"
            f"  Rate    : {CURRENCY}{vehicle.hourly_rate:.2f}/hr\n"
            f"  Fee so far: {CURRENCY}{fee:.2f}"
        )

    def find_vehicle(self, license_plate: str) -> str:
        plate = license_plate.strip().upper()
        if plate not in self.__parked:
            return f"  Vehicle {plate} is not currently in the lot."
        spot_id = self.__parked[plate]
        spot    = self.get_spot(spot_id)
        vehicle = spot.vehicle
        return (
            f"  Found: {plate} in spot {spot_id}  "
            f"(Floor {spot.floor}, {spot.spot_type.value})\n"
            f"  Entry: {vehicle.entry_time.strftime('%Y-%m-%d %H:%M')}  "
            f"Duration: {vehicle.duration_str()}"
        )

    # ── Stats & reporting ─────────────────────

    def get_all_vehicles(self) -> list[tuple[str, ParkingSpot]]:
        """Returns (spot_id, spot) pairs for all occupied spots."""
        return [
            (sid, self.get_spot(sid))
            for sid in self.__parked.values()
        ]

    def get_records(self, last_n: int | None = None) -> list[ParkingRecord]:
        records = list(self.__records)
        return records[-last_n:] if last_n else records

    def total_revenue(self) -> float:
        return round(sum(r.fee for r in self.__records), 2)

    def occupancy_rate(self) -> float:
        if not self.__spots:
            return 0.0
        return round(len(self.__parked) / len(self.__spots) * 100, 1)

    def spot_type_summary(self) -> dict[SpotType, tuple[int, int]]:
        """Returns {SpotType: (total, available)} for each type."""
        result: dict[SpotType, list[int]] = {}
        for spot in self.__spots.values():
            st = spot.spot_type
            if st not in result:
                result[st] = [0, 0]
            result[st][0] += 1
            if spot.is_available:
                result[st][1] += 1
        return {k: tuple(v) for k, v in result.items()}


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


def pick_vehicle_type() -> VehicleType:
    types = list(VehicleType)
    print("\n  Vehicle Types:")
    for i, vt in enumerate(types, 1):
        print(f"    {i}. {vt.value}  (Rate: {CURRENCY}{HOURLY_RATES[vt]:.2f}/hr)")
    while True:
        choice = prompt_int("  Select: ")
        if 1 <= choice <= len(types):
            return types[choice - 1]
        print("  ✗  Invalid selection.")


def pick_spot_type() -> SpotType:
    types = list(SpotType)
    print("\n  Spot Types:")
    for i, st in enumerate(types, 1):
        print(f"    {i}. {st.value}")
    while True:
        choice = prompt_int("  Select: ")
        if 1 <= choice <= len(types):
            return types[choice - 1]
        print("  ✗  Invalid selection.")


# ──────────────────────────────────────────────
#  Seed data
# ──────────────────────────────────────────────

def seed_lot(lot: ParkingLot) -> None:
    """Pre-populate with a realistic multi-floor lot."""
    layout = [
        # (spot_id, spot_type, floor)
        ("M01", SpotType.MOTORCYCLE, 1), ("M02", SpotType.MOTORCYCLE, 1),
        ("M03", SpotType.MOTORCYCLE, 1),
        ("C01", SpotType.COMPACT,    1), ("C02", SpotType.COMPACT,    1),
        ("C03", SpotType.COMPACT,    1), ("C04", SpotType.COMPACT,    1),
        ("S01", SpotType.STANDARD,   1), ("S02", SpotType.STANDARD,   1),
        ("S03", SpotType.STANDARD,   1), ("S04", SpotType.STANDARD,   1),
        ("S05", SpotType.STANDARD,   2), ("S06", SpotType.STANDARD,   2),
        ("S07", SpotType.STANDARD,   2), ("S08", SpotType.STANDARD,   2),
        ("L01", SpotType.LARGE,      2), ("L02", SpotType.LARGE,      2),
        ("L03", SpotType.LARGE,      2),
        ("E01", SpotType.EV,         1), ("E02", SpotType.EV,         1),
    ]
    for sid, stype, floor in layout:
        lot.add_spot(sid, stype, floor)

    # Park a few sample vehicles
    lot.park_vehicle("ABC-1234", VehicleType.CAR,        "Alice Johnson")
    lot.park_vehicle("XYZ-5678", VehicleType.MOTORCYCLE, "Bob Martinez")
    lot.park_vehicle("TRK-9999", VehicleType.TRUCK,      "Clara Logistics")
    lot.park_vehicle("EV-2024",  VehicleType.EV,         "Dave Green")


# ──────────────────────────────────────────────
#  Menu actions
# ──────────────────────────────────────────────

def menu_view_all_spots(lot: ParkingLot) -> None:
    print_header(
        f"ALL PARKING SPOTS  —  {lot.name}",
        f"Total: {lot.total_spots()}  |  Occupancy: {lot.occupancy_rate()}%",
    )
    summary = lot.spot_type_summary()
    print(f"  {'Type':<16}  {'Total':>6}  {'Available':>10}  {'Occupied':>9}")
    print(f"  {'─'*16}  {'─'*6}  {'─'*10}  {'─'*9}")
    for st, (total, avail) in sorted(summary.items(), key=lambda x: x[0].value):
        print(f"  {st.value:<16}  {total:>6}  {avail:>10}  {total-avail:>9}")
    print(f"\n  {'ID':<7}  {'Floor':<6} {'Type':<15} Status")
    print(f"  {'─'*7}  {'─'*6} {'─'*15} {'─'*18}")
    for spot in sorted(lot._ParkingLot__spots.values(), key=lambda s: (s.floor, s.spot_id)):
        print(spot)


def menu_check_availability(lot: ParkingLot) -> None:
    print_header("CHECK AVAILABLE SPOTS")
    print("  Filter by vehicle type? (Enter to skip)")
    print("  0. Show all available spots")
    vtypes = list(VehicleType)
    for i, vt in enumerate(vtypes, 1):
        print(f"  {i}. {vt.value}")
    raw = input("\n  Choice [0]: ").strip()
    vt_filter = None
    if raw.isdigit() and 1 <= int(raw) <= len(vtypes):
        vt_filter = vtypes[int(raw) - 1]

    available = lot.available_spots(vt_filter)
    label     = f"for {vt_filter.value}" if vt_filter else "(all types)"
    print_header(f"AVAILABLE SPOTS  {label}", f"{len(available)} spot(s) free")

    if not available:
        print("  ✗  No available spots matching that filter.")
        return
    print(f"  {'ID':<7}  {'Floor':<6} {'Type':<15} Compatible with")
    print(f"  {'─'*7}  {'─'*6} {'─'*15} {'─'*30}")
    for spot in available:
        compat = ", ".join(
            vt.value for vt, allowed in COMPATIBLE.items()
            if spot.spot_type in allowed
        )
        print(f"  [{spot.spot_id:<5}]  Floor {spot.floor}  {spot.spot_type.value:<15} {compat}")


def menu_park_vehicle(lot: ParkingLot) -> None:
    print_header("PARK A VEHICLE")

    # Show quick availability summary
    available = lot.available_spots()
    if not available:
        print("  ✗  The parking lot is completely full!")
        return
    print(f"  {len(available)} spot(s) available.\n")

    plate     = input("  License Plate  : ").strip().upper()
    if not plate:
        print("  ✗  License plate cannot be empty.")
        return
    vtype     = pick_vehicle_type()
    owner     = input("\n  Owner Name (optional): ").strip()

    # Show compatible spots
    compat = lot.available_spots(vtype)
    if not compat:
        print(f"\n  ✗  No available spots for {vtype.value}.")
        return
    print(f"\n  Available spots for {vtype.value}:")
    for s in compat:
        print(f"    [{s.spot_id}]  Floor {s.floor}  {s.spot_type.value}")

    preferred = input("\n  Preferred spot ID (Enter to auto-assign): ").strip().upper()
    result    = lot.park_vehicle(
        plate, vtype, owner,
        preferred_spot=preferred if preferred else None,
    )
    print(f"\n{result}")


def menu_remove_vehicle(lot: ParkingLot) -> None:
    print_header("REMOVE VEHICLE  /  EXIT")
    parked = lot.get_all_vehicles()
    if not parked:
        print("  No vehicles currently parked.")
        return

    print("  Currently parked:\n")
    print(f"  {'Plate':<13}  {'Type':<18}  {'Spot':<7}  {'Duration':<12}  {'Fee so far'}")
    print(f"  {'─'*13}  {'─'*18}  {'─'*7}  {'─'*12}  {'─'*12}")
    for sid, spot in sorted(parked, key=lambda x: x[0]):
        v   = spot.vehicle
        delta   = datetime.datetime.now() - v.entry_time
        hours   = delta.total_seconds() / 3600
        fee_est = max(MIN_FEE, round(hours * v.hourly_rate, 2))
        print(
            f"  {v.license_plate:<13}  {v.vehicle_type.value:<18}  "
            f"[{sid:<5}]  {v.duration_str():<12}  {CURRENCY}{fee_est:.2f}"
        )

    plate = input("\n  License plate to remove: ").strip().upper()
    print(f"\n{lot.remove_vehicle(plate)}")


def menu_calculate_fee(lot: ParkingLot) -> None:
    print_header("CALCULATE PARKING FEE")
    plate = input("  License Plate: ").strip().upper()
    print(f"\n{lot.calculate_fee(plate)}")


def menu_find_vehicle(lot: ParkingLot) -> None:
    print_header("FIND VEHICLE")
    plate = input("  License Plate: ").strip().upper()
    print(f"\n{lot.find_vehicle(plate)}")


def menu_add_spot(lot: ParkingLot) -> None:
    print_header("ADD PARKING SPOT")
    spot_id  = input("  Spot ID  : ").strip().upper()
    if not spot_id:
        print("  ✗  Spot ID cannot be empty.")
        return
    floor    = prompt_int("  Floor    : ")
    stype    = pick_spot_type()
    print(f"\n{lot.add_spot(spot_id, stype, floor)}")


def menu_view_parked(lot: ParkingLot) -> None:
    print_header("ALL PARKED VEHICLES")
    parked = lot.get_all_vehicles()
    if not parked:
        print("  No vehicles currently parked.")
        return
    print(f"  {len(parked)} vehicle(s) in the lot.\n")
    print(f"  {'Plate':<13}  {'Type':<18}  {'Spot':<7}  {'Floor':<6}  {'Entry':<17}  {'Duration'}")
    print(f"  {'─'*13}  {'─'*18}  {'─'*7}  {'─'*6}  {'─'*17}  {'─'*10}")
    for sid, spot in sorted(parked, key=lambda x: x[0]):
        v = spot.vehicle
        print(
            f"  {v.license_plate:<13}  {v.vehicle_type.value:<18}  "
            f"[{sid:<5}]  Floor {spot.floor}  "
            f"{v.entry_time.strftime('%Y-%m-%d %H:%M')}  "
            f"{v.duration_str()}"
        )


def menu_history(lot: ParkingLot) -> None:
    print_header("EXIT HISTORY  (Last 20 records)")
    records = lot.get_records(last_n=20)
    if not records:
        print("  No exit records yet.")
        return
    print(f"  {'#':<5}  {'Plate':<12}  {'Type':<18}  {'Spot':<6}  {'Entry→Exit':<23}  {'Fee'}")
    print(f"  {'─'*5}  {'─'*12}  {'─'*18}  {'─'*6}  {'─'*23}  {'─'*8}")
    for r in records:
        print(r)
    print(f"\n  Total revenue collected: {CURRENCY}{lot.total_revenue():,.2f}")


def menu_dashboard(lot: ParkingLot) -> None:
    print_header(f"DASHBOARD  —  {lot.name}")
    summary = lot.spot_type_summary()
    total   = lot.total_spots()
    occupied_count = sum(1 for _, s in lot.get_all_vehicles() for _ in [None])
    free_count     = total - occupied_count

    print(f"  {'Lot Name':<28}: {lot.name}")
    print(f"  {'Total Spots':<28}: {total}")
    print(f"  {'Occupied':<28}: {occupied_count}")
    print(f"  {'Available':<28}: {free_count}")
    print(f"  {'Occupancy Rate':<28}: {lot.occupancy_rate()}%")
    print(f"  {'Total Revenue (history)':<28}: {CURRENCY}{lot.total_revenue():,.2f}")
    print(f"  {'Exit Records':<28}: {len(lot.get_records())}")
    print()
    print(f"  {'Spot Type':<16}  {'Total':>6}  {'Available':>10}  {'Occupied':>9}")
    print(f"  {'─'*16}  {'─'*6}  {'─'*10}  {'─'*9}")
    for st, (tot, avail) in sorted(summary.items(), key=lambda x: x[0].value):
        print(f"  {st.value:<16}  {tot:>6}  {avail:>10}  {tot-avail:>9}")
    print()
    print(f"  Hourly Rates:")
    for vt, rate in HOURLY_RATES.items():
        print(f"    {vt.value:<20}: {CURRENCY}{rate:.2f}/hr")


# ──────────────────────────────────────────────
#  Main menu
# ──────────────────────────────────────────────

MENU = """
  ╔════════════════════════════════════════╗
  ║       PARKING MANAGEMENT SYSTEM        ║
  ╠════════════════════════════════════════╣
  ║   SPOTS                                ║
  ║   1.  View all spots                   ║
  ║   2.  Check availability               ║
  ║   3.  Add new spot                     ║
  ╠════════════════════════════════════════╣
  ║   VEHICLES                             ║
  ║   4.  Park a vehicle                   ║
  ║   5.  Remove vehicle / Exit            ║
  ║   6.  View all parked vehicles         ║
  ║   7.  Find vehicle by plate            ║
  ║   8.  Calculate parking fee            ║
  ╠════════════════════════════════════════╣
  ║   REPORTS                              ║
  ║   9.  Exit history                     ║
  ║   10. Dashboard                        ║
  ╠════════════════════════════════════════╣
  ║   0.  Exit                             ║
  ╚════════════════════════════════════════╝"""

ACTIONS = {
    "1":  menu_view_all_spots,
    "2":  menu_check_availability,
    "3":  menu_add_spot,
    "4":  menu_park_vehicle,
    "5":  menu_remove_vehicle,
    "6":  menu_view_parked,
    "7":  menu_find_vehicle,
    "8":  menu_calculate_fee,
    "9":  menu_history,
    "10": menu_dashboard,
}


def main() -> None:
    lot = ParkingLot("PyPark Multi-Level")
    seed_lot(lot)

    print(f"\n{DIVIDER2}")
    print(f"  Welcome to {lot.name}")
    print(
        f"  {lot.total_spots()} spots loaded  |  "
        f"{len(lot.available_spots())} available  |  "
        f"Today: {datetime.date.today()}"
    )
    print(DIVIDER2)

    first = True
    while True:
        if not first:
            cls()
        first = False
        print(MENU)
        print(
            f"  🟢 {len(lot.available_spots())} free  |  "
            f"🔴 {len(lot.occupied_spots())} occupied  |  "
            f"Occupancy: {lot.occupancy_rate()}%\n"
        )
        choice = input("  Select option: ").strip()

        if choice == "0":
            print(f"\n  Thank you for using {lot.name}. Goodbye!\n")
            break
        elif choice in ACTIONS:
            ACTIONS[choice](lot)
        else:
            print("\n  ✗  Invalid option. Please try again.")

        input("\n  Press Enter to return to menu...")


if __name__ == "__main__":
    main()