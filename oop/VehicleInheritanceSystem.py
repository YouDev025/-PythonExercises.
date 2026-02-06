# ============================================
# VehicleInheritanceSystem - Interactive Version
# ============================================

class Vehicle:
    """Base class for all vehicles"""

    def __init__(self, brand, model, year):
        self.brand = brand
        self.model = model
        self.year = year

    def display_info(self):
        return f"Vehicle: {self.year} {self.brand} {self.model}"

    def get_type(self):
        return "Vehicle"


class Car(Vehicle):
    """Car class - inherits from Vehicle"""

    def __init__(self, brand, model, year, number_of_doors):
        super().__init__(brand, model, year)  # Call parent constructor
        self.number_of_doors = number_of_doors

    def display_info(self):
        return f"Car: {self.year} {self.brand} {self.model} | Doors: {self.number_of_doors}"

    def get_type(self):
        return "Car"


class Motorcycle(Vehicle):
    """Motorcycle class - inherits from Vehicle"""

    def __init__(self, brand, model, year, has_sidecar):
        super().__init__(brand, model, year)  # Call parent constructor
        self.has_sidecar = has_sidecar

    def display_info(self):
        sidecar_status = "with sidecar" if self.has_sidecar else "no sidecar"
        return f"Motorcycle: {self.year} {self.brand} {self.model} | {sidecar_status}"

    def get_type(self):
        return "Motorcycle"


class VehicleManager:
    """Manages the collection of vehicles"""

    def __init__(self):
        self.vehicles = []  # Store all vehicles in a list

    def add_vehicle(self, vehicle):
        """Add a vehicle to the inventory"""
        self.vehicles.append(vehicle)
        print(f"\n✓ {vehicle.get_type()} added successfully!")

    def display_all_vehicles(self):
        """Display all vehicles"""
        if not self.vehicles:
            print("\n⚠ No vehicles in inventory!")
            return

        print("\n" + "=" * 60)
        print("ALL VEHICLES IN INVENTORY")
        print("=" * 60)
        for index, vehicle in enumerate(self.vehicles, 1):
            print(f"{index}. {vehicle.display_info()}")
        print("=" * 60)

    def display_by_type(self, vehicle_type):
        """Display vehicles filtered by type"""
        filtered = [v for v in self.vehicles if v.get_type() == vehicle_type]

        if not filtered:
            print(f"\n⚠ No {vehicle_type}s found in inventory!")
            return

        print("\n" + "=" * 60)
        print(f"ALL {vehicle_type.upper()}S IN INVENTORY")
        print("=" * 60)
        for index, vehicle in enumerate(filtered, 1):
            print(f"{index}. {vehicle.display_info()}")
        print("=" * 60)

    def delete_vehicle(self, index):
        """Delete a vehicle by index"""
        if 0 <= index < len(self.vehicles):
            removed = self.vehicles.pop(index)
            print(f"\n✓ {removed.get_type()} deleted successfully!")
            return True
        else:
            print("\n✗ Invalid vehicle number!")
            return False

    def edit_vehicle(self, index):
        """Edit a vehicle by index"""
        if index < 0 or index >= len(self.vehicles):
            print("\n✗ Invalid vehicle number!")
            return False

        vehicle = self.vehicles[index]
        print(f"\nEditing: {vehicle.display_info()}")
        print("\nWhat would you like to edit?")
        print("1. Brand")
        print("2. Model")
        print("3. Year")

        # Show type-specific edit options
        if isinstance(vehicle, Car):
            print("4. Number of Doors")
        elif isinstance(vehicle, Motorcycle):
            print("4. Sidecar Status")

        choice = input("\nEnter your choice (or 0 to cancel): ").strip()

        try:
            if choice == "1":
                vehicle.brand = input("Enter new brand: ").strip()
                print("✓ Brand updated!")
            elif choice == "2":
                vehicle.model = input("Enter new model: ").strip()
                print("✓ Model updated!")
            elif choice == "3":
                vehicle.year = int(input("Enter new year: ").strip())
                print("✓ Year updated!")
            elif choice == "4":
                if isinstance(vehicle, Car):
                    vehicle.number_of_doors = int(input("Enter new number of doors: ").strip())
                    print("✓ Number of doors updated!")
                elif isinstance(vehicle, Motorcycle):
                    sidecar = input("Has sidecar? (yes/no): ").strip().lower()
                    vehicle.has_sidecar = sidecar in ['yes', 'y']
                    print("✓ Sidecar status updated!")
            elif choice == "0":
                print("Edit cancelled.")
                return False
            else:
                print("✗ Invalid choice!")
                return False
            return True
        except ValueError:
            print("✗ Invalid input!")
            return False


def display_menu():
    """Display the main menu"""
    print("\n" + "=" * 60)
    print("VEHICLE MANAGEMENT SYSTEM")
    print("=" * 60)
    print("1. Add Vehicle")
    print("2. Display All Vehicles")
    print("3. Display Vehicles by Type")
    print("4. Edit Vehicle")
    print("5. Delete Vehicle")
    print("6. Exit")
    print("=" * 60)


def get_vehicle_input(vehicle_type):
    """Get user input for creating a vehicle"""
    try:
        print(f"\n--- Enter {vehicle_type} Details ---")
        brand = input("Brand: ").strip()
        model = input("Model: ").strip()
        year = int(input("Year: ").strip())

        if vehicle_type == "Car":
            doors = int(input("Number of doors: ").strip())
            return Car(brand, model, year, doors)
        elif vehicle_type == "Motorcycle":
            sidecar = input("Has sidecar? (yes/no): ").strip().lower()
            has_sidecar = sidecar in ['yes', 'y']
            return Motorcycle(brand, model, year, has_sidecar)
        else:
            return Vehicle(brand, model, year)
    except ValueError:
        print("\n✗ Invalid input! Please enter correct data types.")
        return None


def add_vehicle_menu(manager):
    """Menu for adding a vehicle"""
    print("\n--- Add Vehicle ---")
    print("1. Add Generic Vehicle")
    print("2. Add Car")
    print("3. Add Motorcycle")
    print("0. Cancel")

    choice = input("\nEnter your choice: ").strip()

    if choice == "1":
        vehicle = get_vehicle_input("Vehicle")
        if vehicle:
            manager.add_vehicle(vehicle)
    elif choice == "2":
        vehicle = get_vehicle_input("Car")
        if vehicle:
            manager.add_vehicle(vehicle)
    elif choice == "3":
        vehicle = get_vehicle_input("Motorcycle")
        if vehicle:
            manager.add_vehicle(vehicle)
    elif choice == "0":
        print("Cancelled.")
    else:
        print("✗ Invalid choice!")


def display_by_type_menu(manager):
    """Menu for displaying vehicles by type"""
    print("\n--- Display by Type ---")
    print("1. Display Generic Vehicles")
    print("2. Display Cars")
    print("3. Display Motorcycles")
    print("0. Cancel")

    choice = input("\nEnter your choice: ").strip()

    if choice == "1":
        manager.display_by_type("Vehicle")
    elif choice == "2":
        manager.display_by_type("Car")
    elif choice == "3":
        manager.display_by_type("Motorcycle")
    elif choice == "0":
        print("Cancelled.")
    else:
        print("✗ Invalid choice!")


def edit_vehicle_menu(manager):
    """Menu for editing a vehicle"""
    if not manager.vehicles:
        print("\n⚠ No vehicles to edit!")
        return

    manager.display_all_vehicles()
    try:
        choice = int(input("\nEnter vehicle number to edit (0 to cancel): ").strip())
        if choice == 0:
            print("Cancelled.")
            return
        manager.edit_vehicle(choice - 1)  # Convert to 0-based index
    except ValueError:
        print("✗ Invalid input!")


def delete_vehicle_menu(manager):
    """Menu for deleting a vehicle"""
    if not manager.vehicles:
        print("\n⚠ No vehicles to delete!")
        return

    manager.display_all_vehicles()
    try:
        choice = int(input("\nEnter vehicle number to delete (0 to cancel): ").strip())
        if choice == 0:
            print("Cancelled.")
            return
        manager.delete_vehicle(choice - 1)  # Convert to 0-based index
    except ValueError:
        print("✗ Invalid input!")


def main():
    """Main function - runs the interactive program"""
    # Create vehicle manager
    manager = VehicleManager()

    # Main program loop
    while True:
        display_menu()
        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            add_vehicle_menu(manager)
        elif choice == "2":
            manager.display_all_vehicles()
        elif choice == "3":
            display_by_type_menu(manager)
        elif choice == "4":
            edit_vehicle_menu(manager)
        elif choice == "5":
            delete_vehicle_menu(manager)
        elif choice == "6":
            print("\n Thank you for using Vehicle Management System!")
            print("Goodbye!\n")
            break
        else:
            print("\n✗ Invalid choice! Please try again.")


# Run the program
if __name__ == "__main__":
    main()