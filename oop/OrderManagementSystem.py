"""
Order Management System - Interactive Python OOP Application
Author: Python OOP Expert
Description: A comprehensive order management system demonstrating OOP principles
"""

from datetime import datetime
from typing import List, Optional
import json


class Product:
    """Represents a product in the inventory"""

    def __init__(self, product_id: str, name: str, price: float, stock: int):
        self._product_id = product_id
        self._name = name
        self._price = price
        self._stock = stock

    # Getters (Encapsulation)
    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def price(self) -> float:
        return self._price

    @property
    def stock(self) -> int:
        return self._stock

    # Setters with validation
    @price.setter
    def price(self, value: float):
        if value < 0:
            raise ValueError("Price cannot be negative")
        self._price = value

    @stock.setter
    def stock(self, value: int):
        if value < 0:
            raise ValueError("Stock cannot be negative")
        self._stock = value

    def add_stock(self, quantity: int):
        """Add stock to inventory"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        self._stock += quantity

    def reduce_stock(self, quantity: int):
        """Reduce stock from inventory"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > self._stock:
            raise ValueError(f"Insufficient stock. Available: {self._stock}")
        self._stock -= quantity

    def __str__(self) -> str:
        return f"Product(ID: {self._product_id}, Name: {self._name}, Price: ${self._price:.2f}, Stock: {self._stock})"

    def __repr__(self) -> str:
        return self.__str__()


class Customer:
    """Represents a customer"""

    def __init__(self, customer_id: str, name: str, email: str, phone: str):
        self._customer_id = customer_id
        self._name = name
        self._email = email
        self._phone = phone
        self._orders: List['Order'] = []

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def orders(self) -> List['Order']:
        return self._orders

    def add_order(self, order: 'Order'):
        """Add an order to customer's order history"""
        self._orders.append(order)

    def get_total_spent(self) -> float:
        """Calculate total amount spent by customer"""
        return sum(order.get_total() for order in self._orders)

    def __str__(self) -> str:
        return f"Customer(ID: {self._customer_id}, Name: {self._name}, Email: {self._email}, Orders: {len(self._orders)})"


class OrderItem:
    """Represents an item in an order"""

    def __init__(self, product: Product, quantity: int):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        self._product = product
        self._quantity = quantity

    @property
    def product(self) -> Product:
        return self._product

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int):
        if value <= 0:
            raise ValueError("Quantity must be positive")
        self._quantity = value

    def get_subtotal(self) -> float:
        """Calculate subtotal for this item"""
        return self._product.price * self._quantity

    def __str__(self) -> str:
        return f"{self._product.name} x {self._quantity} = ${self.get_subtotal():.2f}"


class Order:
    """Represents a customer order"""

    _order_counter = 1000

    def __init__(self, customer: Customer):
        Order._order_counter += 1
        self._order_id = f"ORD{Order._order_counter}"
        self._customer = customer
        self._items: List[OrderItem] = []
        self._order_date = datetime.now()
        self._status = "Pending"  # Pending, Confirmed, Shipped, Delivered, Cancelled

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def items(self) -> List[OrderItem]:
        return self._items

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        valid_statuses = ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of {valid_statuses}")
        self._status = value

    def add_item(self, product: Product, quantity: int):
        """Add an item to the order"""
        # Check if product already exists in order
        for item in self._items:
            if item.product.product_id == product.product_id:
                item.quantity += quantity
                return

        # Add new item
        order_item = OrderItem(product, quantity)
        self._items.append(order_item)

    def remove_item(self, product_id: str):
        """Remove an item from the order"""
        self._items = [item for item in self._items if item.product.product_id != product_id]

    def get_total(self) -> float:
        """Calculate total order amount"""
        return sum(item.get_subtotal() for item in self._items)

    def confirm_order(self):
        """Confirm the order and reduce stock"""
        if self._status != "Pending":
            raise ValueError("Only pending orders can be confirmed")

        # Reduce stock for all items
        for item in self._items:
            item.product.reduce_stock(item.quantity)

        self._status = "Confirmed"

    def __str__(self) -> str:
        items_str = "\n    ".join(str(item) for item in self._items)
        return (f"Order ID: {self._order_id}\n"
                f"  Customer: {self._customer.name}\n"
                f"  Date: {self._order_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  Status: {self._status}\n"
                f"  Items:\n    {items_str}\n"
                f"  Total: ${self.get_total():.2f}")


class OrderManagementSystem:
    """Main system to manage products, customers, and orders"""

    def __init__(self):
        self._products: dict[str, Product] = {}
        self._customers: dict[str, Customer] = {}
        self._orders: dict[str, Order] = {}
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with some sample data"""
        # Add sample products
        self.add_product(Product("P001", "Laptop", 999.99, 10))
        self.add_product(Product("P002", "Mouse", 29.99, 50))
        self.add_product(Product("P003", "Keyboard", 79.99, 30))
        self.add_product(Product("P004", "Monitor", 299.99, 15))
        self.add_product(Product("P005", "USB Cable", 9.99, 100))

        # Add sample customers
        self.add_customer(Customer("C001", "John Doe", "john@email.com", "555-0101"))
        self.add_customer(Customer("C002", "Jane Smith", "jane@email.com", "555-0102"))

    # Product Management
    def add_product(self, product: Product):
        """Add a product to the system"""
        self._products[product.product_id] = product

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product by ID"""
        return self._products.get(product_id)

    def list_products(self) -> List[Product]:
        """List all products"""
        return list(self._products.values())

    def update_product_price(self, product_id: str, new_price: float):
        """Update product price"""
        product = self.get_product(product_id)
        if product:
            product.price = new_price
        else:
            raise ValueError(f"Product {product_id} not found")

    def add_product_stock(self, product_id: str, quantity: int):
        """Add stock to a product"""
        product = self.get_product(product_id)
        if product:
            product.add_stock(quantity)
        else:
            raise ValueError(f"Product {product_id} not found")

    # Customer Management
    def add_customer(self, customer: Customer):
        """Add a customer to the system"""
        self._customers[customer.customer_id] = customer

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID"""
        return self._customers.get(customer_id)

    def list_customers(self) -> List[Customer]:
        """List all customers"""
        return list(self._customers.values())

    # Order Management
    def create_order(self, customer_id: str) -> Order:
        """Create a new order for a customer"""
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        order = Order(customer)
        self._orders[order.order_id] = order
        customer.add_order(order)
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        return self._orders.get(order_id)

    def list_orders(self) -> List[Order]:
        """List all orders"""
        return list(self._orders.values())

    def confirm_order(self, order_id: str):
        """Confirm an order"""
        order = self.get_order(order_id)
        if order:
            order.confirm_order()
        else:
            raise ValueError(f"Order {order_id} not found")

    def cancel_order(self, order_id: str):
        """Cancel an order"""
        order = self.get_order(order_id)
        if order:
            order.status = "Cancelled"
        else:
            raise ValueError(f"Order {order_id} not found")

    # Reporting
    def get_total_revenue(self) -> float:
        """Calculate total revenue from all confirmed orders"""
        return sum(order.get_total() for order in self._orders.values()
                   if order.status in ["Confirmed", "Shipped", "Delivered"])

    def get_customer_orders(self, customer_id: str) -> List[Order]:
        """Get all orders for a specific customer"""
        customer = self.get_customer(customer_id)
        return customer.orders if customer else []


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_menu():
    """Display the main menu"""
    print_header("ORDER MANAGEMENT SYSTEM - MAIN MENU")
    print("1.  Product Management")
    print("2.  Customer Management")
    print("3.  Order Management")
    print("4.  Reports")
    print("5.  Exit")
    print("-" * 60)


def product_menu(system: OrderManagementSystem):
    """Handle product management menu"""
    while True:
        print_header("PRODUCT MANAGEMENT")
        print("1. List all products")
        print("2. Add new product")
        print("3. Update product price")
        print("4. Add product stock")
        print("5. Back to main menu")
        print("-" * 60)

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            products = system.list_products()
            print("\nPRODUCTS:")
            for product in products:
                print(f"  {product}")

        elif choice == "2":
            try:
                product_id = input("Product ID: ").strip()
                name = input("Product Name: ").strip()
                price = float(input("Price: ").strip())
                stock = int(input("Stock: ").strip())

                product = Product(product_id, name, price, stock)
                system.add_product(product)
                print(f"Product '{name}' added successfully!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "3":
            try:
                product_id = input("Product ID: ").strip()
                new_price = float(input("New Price: ").strip())
                system.update_product_price(product_id, new_price)
                print(f"Price updated successfully!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "4":
            try:
                product_id = input("Product ID: ").strip()
                quantity = int(input("Quantity to add: ").strip())
                system.add_product_stock(product_id, quantity)
                print(f"Stock added successfully!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "5":
            break

        else:
            print("Invalid choice!")


def customer_menu(system: OrderManagementSystem):
    """Handle customer management menu"""
    while True:
        print_header("CUSTOMER MANAGEMENT")
        print("1. List all customers")
        print("2. Add new customer")
        print("3. View customer details")
        print("4. Back to main menu")
        print("-" * 60)

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            customers = system.list_customers()
            print("\nCUSTOMERS:")
            for customer in customers:
                print(f"  {customer}")

        elif choice == "2":
            try:
                customer_id = input("Customer ID: ").strip()
                name = input("Customer Name: ").strip()
                email = input("Email: ").strip()
                phone = input("Phone: ").strip()

                customer = Customer(customer_id, name, email, phone)
                system.add_customer(customer)
                print(f"Customer '{name}' added successfully!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "3":
            try:
                customer_id = input("Customer ID: ").strip()
                customer = system.get_customer(customer_id)
                if customer:
                    print(f"\n{customer}")
                    print(f"Total Spent: ${customer.get_total_spent():.2f}")
                    print(f"Order History: {len(customer.orders)} orders")
                else:
                    print(f"Customer not found!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "4":
            break

        else:
            print("Invalid choice!")


def order_menu(system: OrderManagementSystem):
    """Handle order management menu"""
    while True:
        print_header("ORDER MANAGEMENT")
        print("1. Create new order")
        print("2. Add item to order")
        print("3. View order details")
        print("4. Confirm order")
        print("5. Cancel order")
        print("6. List all orders")
        print("7. Back to main menu")
        print("-" * 60)

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            try:
                customer_id = input("Customer ID: ").strip()
                order = system.create_order(customer_id)
                print(f"Order {order.order_id} created successfully!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "2":
            try:
                order_id = input("Order ID: ").strip()
                order = system.get_order(order_id)

                if not order:
                    print("Order not found!")
                    continue

                product_id = input("Product ID: ").strip()
                product = system.get_product(product_id)

                if not product:
                    print("Product not found!")
                    continue

                quantity = int(input("Quantity: ").strip())
                order.add_item(product, quantity)
                print(f"Item added to order!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "3":
            try:
                order_id = input("Order ID: ").strip()
                order = system.get_order(order_id)
                if order:
                    print(f"\n{order}")
                else:
                    print("Order not found!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "4":
            try:
                order_id = input("Order ID: ").strip()
                system.confirm_order(order_id)
                print(f"Order confirmed successfully!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "5":
            try:
                order_id = input("Order ID: ").strip()
                system.cancel_order(order_id)
                print(f"Order cancelled successfully!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "6":
            orders = system.list_orders()
            print("\nORDERS:")
            for order in orders:
                print(f"\n{order}")
                print("-" * 60)

        elif choice == "7":
            break

        else:
            print("Invalid choice!")


def reports_menu(system: OrderManagementSystem):
    """Handle reports menu"""
    while True:
        print_header("REPORTS")
        print("1. Total Revenue")
        print("2. Customer Order History")
        print("3. Low Stock Products")
        print("4. Back to main menu")
        print("-" * 60)

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            revenue = system.get_total_revenue()
            print(f"\nTotal Revenue: ${revenue:.2f}")

        elif choice == "2":
            try:
                customer_id = input("Customer ID: ").strip()
                orders = system.get_customer_orders(customer_id)
                customer = system.get_customer(customer_id)

                if customer:
                    print(f"\nOrders for {customer.name}:")
                    for order in orders:
                        print(f"\n{order}")
                        print("-" * 60)
                else:
                    print("Customer not found!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "3":
            products = system.list_products()
            low_stock = [p for p in products if p.stock < 20]
            print("\nLOW STOCK PRODUCTS:")
            for product in low_stock:
                print(f"  {product}")

        elif choice == "4":
            break

        else:
            print("Invalid choice!")


def main():
    """Main function to run the interactive system"""
    system = OrderManagementSystem()

    print_header("WELCOME TO ORDER MANAGEMENT SYSTEM")
    print("Demonstrating Object-Oriented Programming in Python")

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            product_menu(system)
        elif choice == "2":
            customer_menu(system)
        elif choice == "3":
            order_menu(system)
        elif choice == "4":
            reports_menu(system)
        elif choice == "5":
            print_header("THANK YOU FOR USING ORDER MANAGEMENT SYSTEM")
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.")


if __name__ == "__main__":
    main()