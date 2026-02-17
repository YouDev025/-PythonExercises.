# ecommerce_cart.py
# A simple e-commerce shopping cart system.
# Beginner-friendly with clear comments and safeguards.

# Cart structure:
# [
#     {"name": "ProductName", "price": float, "quantity": int},
#     ...
# ]

cart = []


def add_product():
    """Add a new product to the cart."""
    name = input("Enter product name: ").strip()

    # Retry until valid price is entered
    while True:
        try:
            price = float(input("Enter product price: "))
            break
        except ValueError:
            print("Invalid input. Price must be a number. Try again.")

    # Retry until valid quantity is entered
    while True:
        try:
            quantity = int(input("Enter product quantity: "))
            break
        except ValueError:
            print("Invalid input. Quantity must be an integer. Try again.")

    cart.append({"name": name, "price": price, "quantity": quantity})
    print(f"{name} added successfully!")


def remove_product():
    """Remove a product from the cart."""
    name = input("Enter product name to remove: ").strip()
    for item in cart:
        if item["name"].lower() == name.lower():
            cart.remove(item)
            print(f"{name} removed successfully!")
            return
    print("Product not found in cart.")


def update_quantity():
    """Update the quantity of a product in the cart."""
    name = input("Enter product name to update: ").strip()
    for item in cart:
        if item["name"].lower() == name.lower():
            while True:
                try:
                    quantity = int(input("Enter new quantity: "))
                    item["quantity"] = quantity
                    print(f"Quantity for {name} updated successfully!")
                    return
                except ValueError:
                    print("Invalid input. Quantity must be an integer. Try again.")
    print("Product not found in cart.")


def display_cart():
    """Display all products in the cart."""
    if not cart:
        print("Cart is empty.")
        return
    print("\n--- Shopping Cart ---")
    for item in cart:
        print(f"Product: {item['name']}, Price: ${item['price']:.2f}, Quantity: {item['quantity']}")
    print("---------------------\n")


def calculate_total():
    """Calculate and display the total price of the cart."""
    if not cart:
        print("Cart is empty.")
        return
    total = sum(item["price"] * item["quantity"] for item in cart)
    print(f"Total Price: ${total:.2f}")


def menu():
    """Display the menu and handle user choices."""
    while True:
        print("\nE-commerce Shopping Cart")
        print("1. Add Product")
        print("2. Remove Product")
        print("3. Update Quantity")
        print("4. Display Cart")
        print("5. Calculate Total")
        print("6. Exit")

        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            add_product()
        elif choice == "2":
            remove_product()
        elif choice == "3":
            update_quantity()
        elif choice == "4":
            display_cart()
        elif choice == "5":
            calculate_total()
        elif choice == "6":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")


# Run the program
if __name__ == "__main__":
    menu()
