"""
mini_erp_system.py
A simplified Enterprise Resource Planning (ERP) system for small business management.
Implements OOP principles: encapsulation, modularity, and clean class design.
"""

from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
#  PRODUCT
# ─────────────────────────────────────────────
class Product:
    """Represents a product in the system."""

    _id_counter = 1

    def __init__(self, name: str, price: float, quantity: int = 0):
        if not name.strip():
            raise ValueError("Product name cannot be empty.")
        if price < 0:
            raise ValueError("Price cannot be negative.")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        self._product_id = f"P{Product._id_counter:04d}"
        Product._id_counter += 1
        self._name = name.strip()
        self._price = price
        self._quantity = quantity

    # ── getters ──────────────────────────────
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
    def quantity(self) -> int:
        return self._quantity

    # ── setters ──────────────────────────────
    @price.setter
    def price(self, value: float):
        if value < 0:
            raise ValueError("Price cannot be negative.")
        self._price = value

    @quantity.setter
    def quantity(self, value: int):
        if value < 0:
            raise ValueError("Quantity cannot be negative.")
        self._quantity = value

    def __str__(self) -> str:
        return (f"[{self._product_id}] {self._name:<25} "
                f"${self._price:>8.2f}   Stock: {self._quantity}")


# ─────────────────────────────────────────────
#  CUSTOMER
# ─────────────────────────────────────────────
class Customer:
    """Stores customer information."""

    _id_counter = 1

    def __init__(self, name: str, email: str, phone: str = ""):
        if not name.strip():
            raise ValueError("Customer name cannot be empty.")
        if "@" not in email:
            raise ValueError("Invalid email address.")

        self._customer_id = f"C{Customer._id_counter:04d}"
        Customer._id_counter += 1
        self._name = name.strip()
        self._email = email.strip()
        self._phone = phone.strip()

    # ── getters ──────────────────────────────
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

    def __str__(self) -> str:
        phone_display = self._phone if self._phone else "N/A"
        return (f"[{self._customer_id}] {self._name:<25} "
                f"{self._email:<30}  Phone: {phone_display}")


# ─────────────────────────────────────────────
#  ORDER LINE ITEM
# ─────────────────────────────────────────────
class OrderItem:
    """A single line in an order (product + quantity)."""

    def __init__(self, product: Product, qty: int):
        if qty <= 0:
            raise ValueError("Order quantity must be at least 1.")
        self._product = product
        self._qty = qty

    @property
    def product(self) -> Product:
        return self._product

    @property
    def qty(self) -> int:
        return self._qty

    @property
    def subtotal(self) -> float:
        return round(self._product.price * self._qty, 2)

    def __str__(self) -> str:
        return (f"  {self._product.name:<25} x{self._qty:>3}  "
                f"@ ${self._product.price:.2f} = ${self.subtotal:.2f}")


# ─────────────────────────────────────────────
#  ORDER
# ─────────────────────────────────────────────
class Order:
    """Manages a customer order."""

    STATUSES = ("Pending", "Processing", "Shipped", "Delivered", "Cancelled")
    _id_counter = 1

    def __init__(self, customer: Customer):
        self._order_id = f"O{Order._id_counter:05d}"
        Order._id_counter += 1
        self._customer = customer
        self._items: list[OrderItem] = []
        self._status = "Pending"
        self._created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── getters ──────────────────────────────
    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def items(self) -> list:
        return list(self._items)

    @property
    def status(self) -> str:
        return self._status

    @property
    def created_at(self) -> str:
        return self._created_at

    @property
    def total(self) -> float:
        return round(sum(item.subtotal for item in self._items), 2)

    def add_item(self, item: OrderItem):
        self._items.append(item)

    def update_status(self, new_status: str):
        if new_status not in Order.STATUSES:
            raise ValueError(f"Invalid status. Choose from: {Order.STATUSES}")
        self._status = new_status

    def __str__(self) -> str:
        lines = [
            f"Order  : {self._order_id}  ({self._created_at})",
            f"Customer: {self._customer.name}  [{self._customer.customer_id}]",
            f"Status : {self._status}",
            "Items  :",
        ]
        for item in self._items:
            lines.append(str(item))
        lines.append(f"{'─'*50}")
        lines.append(f"  TOTAL: ${self.total:.2f}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
#  INVENTORY
# ─────────────────────────────────────────────
class Inventory:
    """Manages the product catalogue and stock levels."""

    def __init__(self):
        self._products: dict[str, Product] = {}   # keyed by product_id

    def add_product(self, product: Product):
        if product.product_id in self._products:
            raise ValueError(f"Product {product.product_id} already exists.")
        self._products[product.product_id] = product
        print(f"  ✔ Product '{product.name}' added (ID: {product.product_id}).")

    def get_product(self, product_id: str) -> Optional[Product]:
        return self._products.get(product_id)

    def all_products(self) -> list[Product]:
        return list(self._products.values())

    def update_quantity(self, product_id: str, delta: int):
        """delta can be positive (restock) or negative (sell)."""
        p = self._products.get(product_id)
        if not p:
            raise KeyError(f"Product ID '{product_id}' not found.")
        new_qty = p.quantity + delta
        if new_qty < 0:
            raise ValueError(
                f"Insufficient stock for '{p.name}'. "
                f"Available: {p.quantity}, Requested: {-delta}."
            )
        p.quantity = new_qty

    def is_available(self, product_id: str, qty: int) -> bool:
        p = self._products.get(product_id)
        return p is not None and p.quantity >= qty

    def low_stock_report(self, threshold: int = 5) -> list[Product]:
        return [p for p in self._products.values() if p.quantity <= threshold]

    def display_stock(self):
        if not self._products:
            print("  No products in inventory.")
            return
        print(f"\n  {'ID':<8} {'Name':<25} {'Price':>10}  {'Stock':>6}")
        print(f"  {'─'*55}")
        for p in self._products.values():
            print(f"  {p.product_id:<8} {p.name:<25} ${p.price:>9.2f}  {p.quantity:>6}")


# ─────────────────────────────────────────────
#  ERP SYSTEM  (main coordinator)
# ─────────────────────────────────────────────
class ERPSystem:
    """Coordinates customers, inventory, and orders."""

    def __init__(self, company_name: str = "My Business"):
        self._company_name = company_name
        self._inventory = Inventory()
        self._customers: dict[str, Customer] = {}
        self._orders: dict[str, Order] = {}

    # ══════════════════════════════════════════
    #  CUSTOMER operations
    # ══════════════════════════════════════════
    def add_customer(self, name: str, email: str, phone: str = "") -> Customer:
        c = Customer(name, email, phone)
        self._customers[c.customer_id] = c
        return c

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self._customers.get(customer_id)

    def list_customers(self):
        if not self._customers:
            print("  No customers registered.")
            return
        print(f"\n  {'ID':<8} {'Name':<25} {'Email':<30}  {'Phone'}")
        print(f"  {'─'*75}")
        for c in self._customers.values():
            phone = c.phone if c.phone else "N/A"
            print(f"  {c.customer_id:<8} {c.name:<25} {c.email:<30}  {phone}")

    # ══════════════════════════════════════════
    #  PRODUCT / INVENTORY operations
    # ══════════════════════════════════════════
    def add_product(self, name: str, price: float, quantity: int = 0) -> Product:
        p = Product(name, price, quantity)
        self._inventory.add_product(p)
        return p

    def restock_product(self, product_id: str, qty: int):
        self._inventory.update_quantity(product_id, qty)
        p = self._inventory.get_product(product_id)
        print(f"  ✔ Restocked '{p.name}'. New stock: {p.quantity}.")

    # ══════════════════════════════════════════
    #  ORDER operations
    # ══════════════════════════════════════════
    def create_order(self, customer_id: str,
                     items: list[tuple[str, int]]) -> Order:
        """
        items: list of (product_id, quantity) tuples.
        Validates stock, deducts inventory, creates & stores the order.
        """
        customer = self._customers.get(customer_id)
        if not customer:
            raise KeyError(f"Customer '{customer_id}' not found.")

        # Validate all items first (atomic check)
        resolved = []
        for pid, qty in items:
            product = self._inventory.get_product(pid)
            if not product:
                raise KeyError(f"Product '{pid}' not found.")
            if not self._inventory.is_available(pid, qty):
                raise ValueError(
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.quantity}, Requested: {qty}."
                )
            resolved.append((product, qty))

        # Commit: deduct stock and build order
        order = Order(customer)
        for product, qty in resolved:
            self._inventory.update_quantity(product.product_id, -qty)
            order.add_item(OrderItem(product, qty))

        self._orders[order.order_id] = order
        return order

    def update_order_status(self, order_id: str, status: str):
        order = self._orders.get(order_id)
        if not order:
            raise KeyError(f"Order '{order_id}' not found.")
        order.update_status(status)
        print(f"  ✔ Order {order_id} status → {status}.")

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    # ══════════════════════════════════════════
    #  REPORTS
    # ══════════════════════════════════════════
    def report_orders(self):
        if not self._orders:
            print("  No orders placed yet.")
            return
        print(f"\n  {'Order ID':<10} {'Date':<17} {'Customer':<25} "
              f"{'Total':>10}  {'Status'}")
        print(f"  {'─'*80}")
        for o in self._orders.values():
            print(f"  {o.order_id:<10} {o.created_at:<17} "
                  f"{o.customer.name:<25} ${o.total:>9.2f}  {o.status}")

    def report_stock(self):
        self._inventory.display_stock()

    def report_low_stock(self, threshold: int = 5):
        items = self._inventory.low_stock_report(threshold)
        if not items:
            print(f"  ✔ All products are above the threshold of {threshold} units.")
        else:
            print(f"\n  ⚠ Low-stock products (≤ {threshold} units):")
            for p in items:
                print(f"    {p}")


# ─────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────
def _separator(char: str = "═", width: int = 60):
    print(char * width)

def _header(title: str):
    _separator()
    print(f"  {title}")
    _separator()

def _input(prompt: str) -> str:
    return input(f"  {prompt}").strip()

def _input_float(prompt: str) -> float:
    while True:
        try:
            return float(_input(prompt))
        except ValueError:
            print("  ✖ Please enter a valid number.")

def _input_int(prompt: str) -> int:
    while True:
        try:
            return int(_input(prompt))
        except ValueError:
            print("  ✖ Please enter a whole number.")


# ─────────────────────────────────────────────
#  MENU ACTIONS
# ─────────────────────────────────────────────
def menu_add_customer(erp: ERPSystem):
    _header("Add New Customer")
    name  = _input("Full name  : ")
    email = _input("Email      : ")
    phone = _input("Phone (opt): ")
    try:
        c = erp.add_customer(name, email, phone)
        print(f"\n  ✔ Customer added — ID: {c.customer_id}")
    except ValueError as e:
        print(f"\n  ✖ {e}")


def menu_list_customers(erp: ERPSystem):
    _header("All Customers")
    erp.list_customers()


def menu_add_product(erp: ERPSystem):
    _header("Add New Product")
    name  = _input("Product name : ")
    price = _input_float("Unit price   : $")
    qty   = _input_int("Initial stock: ")
    try:
        p = erp.add_product(name, price, qty)
        print(f"  ✔ Product added — ID: {p.product_id}")
    except ValueError as e:
        print(f"\n  ✖ {e}")


def menu_restock(erp: ERPSystem):
    _header("Restock Product")
    erp.report_stock()
    pid = _input("\nProduct ID to restock: ")
    qty = _input_int("Quantity to add      : ")
    try:
        erp.restock_product(pid, qty)
    except (KeyError, ValueError) as e:
        print(f"\n  ✖ {e}")


def menu_create_order(erp: ERPSystem):
    _header("Create New Order")
    erp.list_customers()
    cid = _input("\nCustomer ID : ")

    erp.report_stock()
    print()
    items: list[tuple[str, int]] = []
    while True:
        pid = _input("Product ID (blank to finish): ")
        if not pid:
            break
        qty = _input_int("Quantity: ")
        items.append((pid, qty))

    if not items:
        print("  ✖ No items added. Order cancelled.")
        return

    try:
        order = erp.create_order(cid, items)
        print(f"\n  ✔ Order created successfully!\n")
        print(order)
    except (KeyError, ValueError) as e:
        print(f"\n  ✖ {e}")


def menu_update_order_status(erp: ERPSystem):
    _header("Update Order Status")
    erp.report_orders()
    oid = _input("\nOrder ID : ")
    print(f"  Statuses: {', '.join(Order.STATUSES)}")
    status = _input("New status: ")
    try:
        erp.update_order_status(oid, status)
    except (KeyError, ValueError) as e:
        print(f"\n  ✖ {e}")


def menu_view_order(erp: ERPSystem):
    _header("View Order Detail")
    oid = _input("Order ID: ")
    order = erp.get_order(oid)
    if order:
        print()
        print(order)
    else:
        print(f"\n  ✖ Order '{oid}' not found.")


def menu_reports(erp: ERPSystem):
    _header("Reports")
    print("  1. All Orders")
    print("  2. Stock Levels")
    print("  3. Low Stock Alert")
    choice = _input("Choice: ")
    if choice == "1":
        erp.report_orders()
    elif choice == "2":
        erp.report_stock()
    elif choice == "3":
        threshold = _input_int("Low-stock threshold (default 5): ")
        erp.report_low_stock(threshold)
    else:
        print("  ✖ Invalid choice.")


# ─────────────────────────────────────────────
#  SEED DATA  (demo)
# ─────────────────────────────────────────────
def seed_demo_data(erp: ERPSystem):
    """Populate the system with sample data for demonstration."""
    erp.add_customer("Alice Johnson",  "alice@example.com", "555-0101")
    erp.add_customer("Bob Martinez",   "bob@example.com",   "555-0202")
    erp.add_customer("Carol Williams", "carol@example.com")

    erp.add_product("Wireless Mouse",     29.99, 50)
    erp.add_product("Mechanical Keyboard",79.99, 30)
    erp.add_product("USB-C Hub",          39.99,  4)   # low stock
    erp.add_product("Monitor Stand",      49.99, 20)
    erp.add_product("Webcam HD",          59.99,  2)   # low stock


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
MENU = """
  ┌─────────────────────────────────────┐
  │         MAIN MENU                   │
  ├─────────────────────────────────────┤
  │  1. Add Customer                    │
  │  2. List Customers                  │
  │  3. Add Product                     │
  │  4. Restock Product                 │
  │  5. Create Order                    │
  │  6. Update Order Status             │
  │  7. View Order Detail               │
  │  8. Reports                         │
  │  0. Exit                            │
  └─────────────────────────────────────┘"""

ACTIONS = {
    "1": menu_add_customer,
    "2": menu_list_customers,
    "3": menu_add_product,
    "4": menu_restock,
    "5": menu_create_order,
    "6": menu_update_order_status,
    "7": menu_view_order,
    "8": menu_reports,
}


def main():
    erp = ERPSystem("Acme Corp")

    _separator("═")
    print("  Welcome to the Mini ERP System")
    print(f"  Company: {erp._company_name}")
    _separator("═")

    load = _input("Load demo data? (y/n): ").lower()
    if load == "y":
        seed_demo_data(erp)
        print("  ✔ Demo data loaded.\n")

    while True:
        print(MENU)
        choice = _input("Select option: ")

        if choice == "0":
            print("\n  Goodbye! 👋\n")
            break
        elif choice in ACTIONS:
            print()
            ACTIONS[choice](erp)
            input("\n  Press Enter to continue…")
        else:
            print("  ✖ Invalid option. Please try again.")


if __name__ == "__main__":
    main()