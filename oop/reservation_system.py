"""
Hotel Reservation System - Object-Oriented Python Program
Description: A complete hotel reservation management system
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from enum import Enum


class RoomType(Enum):
    """Enumeration of room types"""
    SINGLE = ("Single", 80)
    DOUBLE = ("Double", 120)
    SUITE = ("Suite", 200)
    DELUXE = ("Deluxe", 350)

    def __init__(self, name: str, price: float):
        self._name = name
        self._price = price

    @property
    def room_name(self) -> str:
        return self._name

    @property
    def base_price(self) -> float:
        return self._price


class ReservationStatus(Enum):
    """Enumeration of reservation statuses"""
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


class Room:
    """Represents a hotel room"""

    _room_counter = 100

    def __init__(self, room_type: RoomType, floor: int):
        Room._room_counter += 1
        self._number = Room._room_counter
        self._type = room_type
        self._floor = floor
        self._is_available = True
        self._amenities: List[str] = self._initialize_amenities()

    def _initialize_amenities(self) -> List[str]:
        """Initialize amenities based on room type"""
        base_amenities = ["Wi-Fi", "TV", "Air Conditioning"]

        if self._type == RoomType.SINGLE:
            return base_amenities + ["Single Bed"]
        elif self._type == RoomType.DOUBLE:
            return base_amenities + ["Double Bed", "Mini-bar"]
        elif self._type == RoomType.SUITE:
            return base_amenities + ["King Bed", "Mini-bar", "Jacuzzi", "Living Room"]
        else:  # DELUXE
            return base_amenities + ["King Bed", "Mini-bar", "Jacuzzi", "Living Room", "Balcony", "Ocean View"]

    @property
    def number(self) -> int:
        return self._number

    @property
    def type(self) -> RoomType:
        return self._type

    @property
    def floor(self) -> int:
        return self._floor

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def amenities(self) -> List[str]:
        return self._amenities.copy()

    @property
    def price_per_night(self) -> float:
        return self._type.base_price

    def mark_occupied(self):
        """Marks the room as occupied"""
        self._is_available = False

    def mark_available(self):
        """Marks the room as available"""
        self._is_available = True

    def __str__(self) -> str:
        status = "Available" if self._is_available else "Occupied"
        return f"Room {self._number} - {self._type.room_name} - Floor {self._floor} - {status}"

    def display_details(self):
        """Displays complete room details"""
        print(f"\n--- Room {self._number} ---")
        print(f"Type: {self._type.room_name}")
        print(f"Floor: {self._floor}")
        print(f"Price per night: ${self._type.base_price:.2f}")
        print(f"Status: {'Available' if self._is_available else 'Occupied'}")
        print(f"Amenities: {', '.join(self._amenities)}")


class Customer:
    """Represents a hotel customer"""

    _customer_counter = 1000

    def __init__(self, first_name: str, last_name: str, email: str, phone: str):
        Customer._customer_counter += 1
        self._customer_id = f"CUST{Customer._customer_counter}"
        self._first_name = first_name
        self._last_name = last_name
        self._email = email
        self._phone = phone
        self._reservations: List['Reservation'] = []
        self._loyalty_points = 0

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def full_name(self) -> str:
        return f"{self._first_name} {self._last_name}"

    @property
    def email(self) -> str:
        return self._email

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def reservations(self) -> List['Reservation']:
        return self._reservations.copy()

    @property
    def loyalty_points(self) -> int:
        return self._loyalty_points

    def add_reservation(self, reservation: 'Reservation'):
        """Adds a reservation to the customer"""
        self._reservations.append(reservation)

    def add_points(self, points: int):
        """Adds loyalty points"""
        self._loyalty_points += points

    def calculate_total_spent(self) -> float:
        """Calculates total amount spent by customer"""
        return sum(r.calculate_total_price() for r in self._reservations
                   if r.status != ReservationStatus.CANCELLED)

    def __str__(self) -> str:
        return f"Customer {self._customer_id}: {self.full_name} ({self._email})"

    def display_details(self):
        """Displays complete customer details"""
        print(f"\n--- Customer {self._customer_id} ---")
        print(f"Name: {self.full_name}")
        print(f"Email: {self._email}")
        print(f"Phone: {self._phone}")
        print(f"Loyalty Points: {self._loyalty_points}")
        print(f"Number of Reservations: {len(self._reservations)}")
        print(f"Total Spent: ${self.calculate_total_spent():.2f}")


class Reservation:
    """Represents a room reservation"""

    _reservation_counter = 2000

    def __init__(self, customer: Customer, room: Room, check_in: datetime, check_out: datetime):
        Reservation._reservation_counter += 1
        self._reservation_number = f"RES{Reservation._reservation_counter}"
        self._customer = customer
        self._room = room
        self._check_in = check_in
        self._check_out = check_out
        self._creation_date = datetime.now()
        self._status = ReservationStatus.PENDING
        self._additional_services: List['Service'] = []

        # Validation
        if check_out <= check_in:
            raise ValueError("Check-out date must be after check-in date")

    @property
    def reservation_number(self) -> str:
        return self._reservation_number

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def room(self) -> Room:
        return self._room

    @property
    def check_in(self) -> datetime:
        return self._check_in

    @property
    def check_out(self) -> datetime:
        return self._check_out

    @property
    def status(self) -> ReservationStatus:
        return self._status

    @property
    def number_of_nights(self) -> int:
        """Calculates number of nights"""
        return (self._check_out - self._check_in).days

    def add_service(self, service: 'Service'):
        """Adds an additional service"""
        self._additional_services.append(service)

    def calculate_room_price(self) -> float:
        """Calculates room price"""
        return self._room.price_per_night * self.number_of_nights

    def calculate_services_price(self) -> float:
        """Calculates additional services price"""
        return sum(service.price for service in self._additional_services)

    def calculate_total_price(self) -> float:
        """Calculates total reservation price"""
        return self.calculate_room_price() + self.calculate_services_price()

    def confirm(self):
        """Confirms the reservation"""
        if self._status != ReservationStatus.PENDING:
            raise ValueError("Only pending reservations can be confirmed")

        self._status = ReservationStatus.CONFIRMED
        self._room.mark_occupied()

        # Add loyalty points (1 point per $10 spent)
        points = int(self.calculate_total_price() / 10)
        self._customer.add_points(points)

    def cancel(self):
        """Cancels the reservation"""
        if self._status == ReservationStatus.COMPLETED:
            raise ValueError("Completed reservations cannot be cancelled")

        self._status = ReservationStatus.CANCELLED
        self._room.mark_available()

    def complete(self):
        """Completes the reservation (check-out)"""
        if self._status != ReservationStatus.CONFIRMED:
            raise ValueError("Only confirmed reservations can be completed")

        self._status = ReservationStatus.COMPLETED
        self._room.mark_available()

    def __str__(self) -> str:
        return (f"Reservation {self._reservation_number} - "
                f"{self._customer.full_name} - "
                f"Room {self._room.number} - "
                f"{self._status.value}")

    def display_details(self):
        """Displays complete reservation details"""
        print(f"\n--- Reservation {self._reservation_number} ---")
        print(f"Customer: {self._customer.full_name}")
        print(f"Room: {self._room.number} ({self._room.type.room_name})")
        print(f"Check-in: {self._check_in.strftime('%m/%d/%Y')}")
        print(f"Check-out: {self._check_out.strftime('%m/%d/%Y')}")
        print(f"Number of nights: {self.number_of_nights}")
        print(f"Status: {self._status.value}")
        print(f"\nPrice Breakdown:")
        print(f"  Room: ${self.calculate_room_price():.2f}")
        if self._additional_services:
            print(f"  Services:")
            for service in self._additional_services:
                print(f"    - {service.name}: ${service.price:.2f}")
        print(f"  TOTAL: ${self.calculate_total_price():.2f}")


class Service:
    """Represents an additional service"""

    def __init__(self, name: str, price: float, description: str = ""):
        self._name = name
        self._price = price
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def price(self) -> float:
        return self._price

    @property
    def description(self) -> str:
        return self._description

    def __str__(self) -> str:
        return f"{self._name} - ${self._price:.2f}"


class Hotel:
    """Represents the hotel with all its rooms"""

    def __init__(self, name: str, address: str):
        self._name = name
        self._address = address
        self._rooms: Dict[int, Room] = {}
        self._customers: Dict[str, Customer] = {}
        self._reservations: Dict[str, Reservation] = {}
        self._available_services: List[Service] = []
        self._initialize_hotel()

    def _initialize_hotel(self):
        """Initializes the hotel with rooms and services"""
        # Create rooms
        for floor in range(1, 4):
            for _ in range(2):
                self.add_room(Room(RoomType.SINGLE, floor))
            for _ in range(2):
                self.add_room(Room(RoomType.DOUBLE, floor))

        for floor in range(3, 5):
            self.add_room(Room(RoomType.SUITE, floor))
            self.add_room(Room(RoomType.DELUXE, floor))

        # Add services
        self._available_services = [
            Service("Breakfast", 15.0, "Continental buffet"),
            Service("Parking", 20.0, "24h secure parking"),
            Service("Spa", 60.0, "Spa access with massage"),
            Service("Airport Transfer", 40.0, "Private shuttle"),
            Service("Room Service", 25.0, "24h room service")
        ]

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    def add_room(self, room: Room):
        """Adds a room to the hotel"""
        self._rooms[room.number] = room

    def add_customer(self, customer: Customer):
        """Adds a customer"""
        self._customers[customer.customer_id] = customer

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Gets a customer by ID"""
        return self._customers.get(customer_id)

    def get_room(self, number: int) -> Optional[Room]:
        """Gets a room by number"""
        return self._rooms.get(number)

    def list_available_rooms(self, room_type: Optional[RoomType] = None) -> List[Room]:
        """Lists available rooms"""
        rooms = [r for r in self._rooms.values() if r.is_available]

        if room_type:
            rooms = [r for r in rooms if r.type == room_type]

        return rooms

    def list_services(self) -> List[Service]:
        """Lists available services"""
        return self._available_services.copy()

    def create_reservation(self, customer: Customer, room: Room,
                           check_in: datetime, check_out: datetime) -> Reservation:
        """Creates a new reservation"""
        if not room.is_available:
            raise ValueError("This room is not available")

        reservation = Reservation(customer, room, check_in, check_out)
        self._reservations[reservation.reservation_number] = reservation
        customer.add_reservation(reservation)

        return reservation

    def get_reservation(self, reservation_number: str) -> Optional[Reservation]:
        """Gets a reservation by number"""
        return self._reservations.get(reservation_number)

    def list_reservations(self, status: Optional[ReservationStatus] = None) -> List[Reservation]:
        """Lists reservations"""
        reservations = list(self._reservations.values())

        if status:
            reservations = [r for r in reservations if r.status == status]

        return reservations

    def calculate_total_revenue(self) -> float:
        """Calculates total hotel revenue"""
        return sum(r.calculate_total_price() for r in self._reservations.values()
                   if r.status != ReservationStatus.CANCELLED)

    def occupancy_rate(self) -> float:
        """Calculates current occupancy rate"""
        total_rooms = len(self._rooms)
        occupied_rooms = sum(1 for r in self._rooms.values() if not r.is_available)
        return (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0


class ReservationSystem:
    """Main reservation management system"""

    def __init__(self):
        self._hotel = Hotel("Grand Hotel", "123 Main Street, New York")
        self._running = True

    def start(self):
        """Starts the reservation system"""
        self._display_welcome()
        self._main_menu()

    def _display_welcome(self):
        """Displays welcome screen"""
        print("\n" + "=" * 60)
        print(f"  Welcome to {self._hotel.name}")
        print(f"  {self._hotel.address}")
        print("=" * 60)

    def _main_menu(self):
        """Displays main menu"""
        while self._running:
            print("\n" + "=" * 60)
            print("  MAIN MENU")
            print("=" * 60)
            print("1. Customer Management")
            print("2. Room Management")
            print("3. Reservation Management")
            print("4. Statistics")
            print("5. Exit")
            print("-" * 60)

            choice = input("Your choice: ").strip()

            if choice == "1":
                self._customer_menu()
            elif choice == "2":
                self._room_menu()
            elif choice == "3":
                self._reservation_menu()
            elif choice == "4":
                self._display_statistics()
            elif choice == "5":
                print("\nThank you for using our system!")
                self._running = False
            else:
                print("Invalid choice!")

    def _customer_menu(self):
        """Customer management menu"""
        while True:
            print("\n" + "=" * 60)
            print("  CUSTOMER MANAGEMENT")
            print("=" * 60)
            print("1. Add Customer")
            print("2. Search Customer")
            print("3. List All Customers")
            print("4. Back")
            print("-" * 60)

            choice = input("Your choice: ").strip()

            if choice == "1":
                self._add_customer()
            elif choice == "2":
                self._search_customer()
            elif choice == "3":
                self._list_customers()
            elif choice == "4":
                break
            else:
                print("Invalid choice!")

    def _add_customer(self):
        """Adds a new customer"""
        print("\n--- New Customer ---")
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        email = input("Email: ").strip()
        phone = input("Phone: ").strip()

        if not all([first_name, last_name, email, phone]):
            print("All fields are required!")
            return

        customer = Customer(first_name, last_name, email, phone)
        self._hotel.add_customer(customer)
        print(f"\nCustomer created successfully! ID: {customer.customer_id}")

    def _search_customer(self):
        """Searches for a customer by ID"""
        customer_id = input("\nCustomer ID: ").strip()
        customer = self._hotel.get_customer(customer_id)

        if customer:
            customer.display_details()
        else:
            print("Customer not found!")

    def _list_customers(self):
        """Lists all customers"""
        customers = list(self._hotel._customers.values())

        if not customers:
            print("\nNo customers registered.")
            return

        print("\n--- Customer List ---")
        for customer in customers:
            print(customer)

    def _room_menu(self):
        """Room management menu"""
        while True:
            print("\n" + "=" * 60)
            print("  ROOM MANAGEMENT")
            print("=" * 60)
            print("1. List All Rooms")
            print("2. List Available Rooms")
            print("3. Room Details")
            print("4. Back")
            print("-" * 60)

            choice = input("Your choice: ").strip()

            if choice == "1":
                self._list_rooms()
            elif choice == "2":
                self._list_available_rooms()
            elif choice == "3":
                self._display_room_details()
            elif choice == "4":
                break
            else:
                print("Invalid choice!")

    def _list_rooms(self):
        """Lists all rooms"""
        rooms = list(self._hotel._rooms.values())

        print("\n--- All Rooms ---")
        for room in sorted(rooms, key=lambda r: r.number):
            print(room)

    def _list_available_rooms(self):
        """Lists available rooms by type"""
        print("\n--- Available Rooms ---")
        print("Choose type (or press Enter for all):")
        print("1. Single")
        print("2. Double")
        print("3. Suite")
        print("4. Deluxe")

        choice = input("Your choice: ").strip()

        type_map = {
            "1": RoomType.SINGLE,
            "2": RoomType.DOUBLE,
            "3": RoomType.SUITE,
            "4": RoomType.DELUXE
        }

        room_type = type_map.get(choice)
        rooms = self._hotel.list_available_rooms(room_type)

        if not rooms:
            print("\nNo rooms available.")
        else:
            for room in rooms:
                print(room)

    def _display_room_details(self):
        """Displays room details"""
        try:
            number = int(input("\nRoom Number: ").strip())
            room = self._hotel.get_room(number)

            if room:
                room.display_details()
            else:
                print("Room not found!")
        except ValueError:
            print("Invalid number!")

    def _reservation_menu(self):
        """Reservation management menu"""
        while True:
            print("\n" + "=" * 60)
            print("  RESERVATION MANAGEMENT")
            print("=" * 60)
            print("1. Create Reservation")
            print("2. Confirm Reservation")
            print("3. Cancel Reservation")
            print("4. Complete Reservation (Check-out)")
            print("5. List All Reservations")
            print("6. Reservation Details")
            print("7. Back")
            print("-" * 60)

            choice = input("Your choice: ").strip()

            if choice == "1":
                self._create_reservation()
            elif choice == "2":
                self._confirm_reservation()
            elif choice == "3":
                self._cancel_reservation()
            elif choice == "4":
                self._complete_reservation()
            elif choice == "5":
                self._list_reservations()
            elif choice == "6":
                self._display_reservation_details()
            elif choice == "7":
                break
            else:
                print("Invalid choice!")

    def _create_reservation(self):
        """Creates a new reservation"""
        print("\n--- New Reservation ---")

        # Get customer
        customer_id = input("Customer ID: ").strip()
        customer = self._hotel.get_customer(customer_id)

        if not customer:
            print("Customer not found!")
            return

        # Display available rooms
        print("\nAvailable rooms:")
        rooms = self._hotel.list_available_rooms()
        for room in rooms:
            print(f"  {room.number} - {room.type.room_name} - ${room.price_per_night}/night")

        # Get room
        try:
            room_number = int(input("\nRoom Number: ").strip())
            room = self._hotel.get_room(room_number)

            if not room or not room.is_available:
                print("Room not available!")
                return
        except ValueError:
            print("Invalid number!")
            return

        # Get dates
        try:
            check_in_str = input("Check-in date (MM/DD/YYYY): ").strip()
            check_out_str = input("Check-out date (MM/DD/YYYY): ").strip()

            check_in = datetime.strptime(check_in_str, "%m/%d/%Y")
            check_out = datetime.strptime(check_out_str, "%m/%d/%Y")

            # Create reservation
            reservation = self._hotel.create_reservation(customer, room, check_in, check_out)

            # Offer services
            self._add_services_to_reservation(reservation)

            print(f"\nReservation created successfully! Number: {reservation.reservation_number}")
            reservation.display_details()

        except ValueError as e:
            print(f"Error: {e}")

    def _add_services_to_reservation(self, reservation: Reservation):
        """Adds services to a reservation"""
        print("\nWould you like to add services? (y/n)")
        if input().strip().lower() != 'y':
            return

        services = self._hotel.list_services()

        while True:
            print("\nAvailable services:")
            for i, service in enumerate(services, 1):
                print(f"{i}. {service}")
            print("0. Done")

            try:
                choice = int(input("\nChoose a service: ").strip())

                if choice == 0:
                    break
                elif 1 <= choice <= len(services):
                    reservation.add_service(services[choice - 1])
                    print(f"Service '{services[choice - 1].name}' added!")
                else:
                    print("Invalid choice!")
            except ValueError:
                print("Enter a number!")

    def _confirm_reservation(self):
        """Confirms a reservation"""
        number = input("\nReservation Number: ").strip()
        reservation = self._hotel.get_reservation(number)

        if not reservation:
            print("Reservation not found!")
            return

        try:
            reservation.confirm()
            print("Reservation confirmed successfully!")
            reservation.display_details()
        except ValueError as e:
            print(f"Error: {e}")

    def _cancel_reservation(self):
        """Cancels a reservation"""
        number = input("\nReservation Number: ").strip()
        reservation = self._hotel.get_reservation(number)

        if not reservation:
            print("Reservation not found!")
            return

        try:
            reservation.cancel()
            print("Reservation cancelled successfully!")
        except ValueError as e:
            print(f"Error: {e}")

    def _complete_reservation(self):
        """Completes a reservation (check-out)"""
        number = input("\nReservation Number: ").strip()
        reservation = self._hotel.get_reservation(number)

        if not reservation:
            print("Reservation not found!")
            return

        try:
            reservation.complete()
            print("Check-out completed successfully!")
            print(f"Total amount: ${reservation.calculate_total_price():.2f}")
        except ValueError as e:
            print(f"Error: {e}")

    def _list_reservations(self):
        """Lists all reservations"""
        reservations = self._hotel.list_reservations()

        if not reservations:
            print("\nNo reservations.")
            return

        print("\n--- All Reservations ---")
        for reservation in reservations:
            print(reservation)

    def _display_reservation_details(self):
        """Displays reservation details"""
        number = input("\nReservation Number: ").strip()
        reservation = self._hotel.get_reservation(number)

        if reservation:
            reservation.display_details()
        else:
            print("Reservation not found!")

    def _display_statistics(self):
        """Displays hotel statistics"""
        print("\n" + "=" * 60)
        print("  STATISTICS")
        print("=" * 60)

        total_rooms = len(self._hotel._rooms)
        available_rooms = len(self._hotel.list_available_rooms())
        occupancy = self._hotel.occupancy_rate()
        total_revenue = self._hotel.calculate_total_revenue()
        total_customers = len(self._hotel._customers)
        total_reservations = len(self._hotel._reservations)

        print(f"\nTotal Rooms: {total_rooms}")
        print(f"Available Rooms: {available_rooms}")
        print(f"Occupancy Rate: {occupancy:.1f}%")
        print(f"\nRegistered Customers: {total_customers}")
        print(f"Total Reservations: {total_reservations}")
        print(f"\nTotal Revenue: ${total_revenue:.2f}")

        # Statistics by status
        print("\nReservations by status:")
        for status in ReservationStatus:
            count = len(self._hotel.list_reservations(status))
            print(f"  {status.value}: {count}")


def main():
    """Main function"""
    system = ReservationSystem()
    system.start()


if __name__ == "__main__":
    main()