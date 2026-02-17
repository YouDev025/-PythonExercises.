# inventory_management.py
# A simple inventory management system using a dictionary.
# Beginner-friendly with clear comments and safeguards.

# Inventory dictionary structure:
# {
#     "product_name": {"quantity": int, "price": float}
# }

inventory = {}

def add_product():
    """Add a new product to the inventory."""
    name = input("Enter product name: ").strip()
    if name in inventory:
        print("Product already exists. Use update option instead.")
        return

    # Keep asking until valid quantity is entered
    while True:
        try:
            quantity = int(input("Enter quantity: "))
            break
        except ValueError:
            print("Invalid input. Quantity must be an integer. Try again.")

    # Keep asking until valid price is entered
    while True:
        try:
            price = float(input("Enter price: "))
            break
        except ValueError:
            print("Invalid input. Price must be a number. Try again.")

    inventory[name] = {"quantity": quantity, "price": price}
    print(f"{name} added successfully!")

def update_quantity():
    """Update the quantity of an existing product."""
    name = input("Enter product name to update: ").strip()
    if name not in inventory:
        print("Product not found.")
        return
    try:
        quantity = int(input("Enter new quantity: "))
        inventory[name]["quantity"] = quantity
        print(f"Quantity for {name} updated successfully!")
    except ValueError:
        print("Invalid input. Quantity must be an integer.")

def delete_product():
    """Delete a product from the inventory."""
    name = input("Enter product name to delete: ").strip()
    if name in inventory:
        del inventory[name]
        print(f"{name} deleted successfully!")
    else:
        print("Product not found.")

def display_products():
    """Display all products in the inventory."""
    if not inventory:
        print("Inventory is empty.")
        return
    print("\n--- Inventory ---")
    for name, details in inventory.items():
        print(f"Product: {name}, Quantity: {details['quantity']}, Price: ${details['price']:.2f}")
    print("-----------------\n")

def menu():
    """Display the menu and handle user choices."""
    while True:
        print("\nInventory Management System")
        print("1. Add Product")
        print("2. Update Quantity")
        print("3. Delete Product")
        print("4. Display Products")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            add_product()
        elif choice == "2":
            update_quantity()
        elif choice == "3":
            delete_product()
        elif choice == "4":
            display_products()
        elif choice == "5":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

# Run the program
if __name__ == "__main__":
    menu()
