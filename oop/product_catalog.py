"""
product_catalog.py
A command-line product catalog manager using Python OOP principles.
"""

from __future__ import annotations
import os


# ──────────────────────────────────────────────
#  Product
# ──────────────────────────────────────────────

class Product:
    """Represents a single product with encapsulated attributes."""

    _id_counter: int = 1  # class-level auto-increment

    def __init__(
        self,
        name: str,
        price: float,
        quantity: int,
        category: str,
        product_id: int | None = None,
    ) -> None:
        if product_id is not None:
            self.__id = product_id
        else:
            self.__id = Product._id_counter
            Product._id_counter += 1

        self.name = name          # validated via setter
        self.price = price        # validated via setter
        self.quantity = quantity  # validated via setter
        self.category = category

    # ── properties ────────────────────────────

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Product name cannot be empty.")
        self.__name = value

    @property
    def price(self) -> float:
        return self.__price

    @price.setter
    def price(self, value: float) -> None:
        value = float(value)
        if value < 0:
            raise ValueError("Price cannot be negative.")
        self.__price = round(value, 2)

    @property
    def quantity(self) -> int:
        return self.__quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        value = int(value)
        if value < 0:
            raise ValueError("Quantity cannot be negative.")
        self.__quantity = value

    @property
    def category(self) -> str:
        return self.__category

    @category.setter
    def category(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Category cannot be empty.")
        self.__category = value

    # ── helpers ───────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.__id,
            "name": self.__name,
            "price": self.__price,
            "quantity": self.__quantity,
            "category": self.__category,
        }

    def __str__(self) -> str:
        return (
            f"[ID: {self.__id:>4}]  {self.__name:<30}  "
            f"${self.__price:>8.2f}  Qty: {self.__quantity:>5}  "
            f"Category: {self.__category}"
        )

    def __repr__(self) -> str:
        return (
            f"Product(id={self.__id}, name={self.__name!r}, "
            f"price={self.__price}, quantity={self.__quantity}, "
            f"category={self.__category!r})"
        )


# ──────────────────────────────────────────────
#  ProductCatalog
# ──────────────────────────────────────────────

class ProductCatalog:
    """Manages a collection of Product objects."""

    def __init__(self) -> None:
        self.__products: dict[int, Product] = {}

    # ── internal helpers ──────────────────────

    def __find_by_id(self, product_id: int) -> Product | None:
        return self.__products.get(product_id)

    # ── public CRUD methods ───────────────────

    def add_product(
        self,
        name: str,
        price: float,
        quantity: int,
        category: str,
    ) -> Product:
        """Create and add a new product; returns the created Product."""
        product = Product(name, price, quantity, category)
        self.__products[product.id] = product
        return product

    def remove_product(self, product_id: int) -> bool:
        """Remove a product by ID. Returns True if found and removed."""
        if product_id in self.__products:
            del self.__products[product_id]
            return True
        return False

    def update_product(
        self,
        product_id: int,
        name: str | None = None,
        price: float | None = None,
        quantity: int | None = None,
        category: str | None = None,
    ) -> bool:
        """Update one or more fields of an existing product."""
        product = self.__find_by_id(product_id)
        if product is None:
            return False
        if name is not None:
            product.name = name
        if price is not None:
            product.price = price
        if quantity is not None:
            product.quantity = quantity
        if category is not None:
            product.category = category
        return True

    def search_by_id(self, product_id: int) -> Product | None:
        return self.__find_by_id(product_id)

    def search_by_name(self, query: str) -> list[Product]:
        """Case-insensitive substring search on product name."""
        query = query.lower()
        return [p for p in self.__products.values() if query in p.name.lower()]

    def get_all_products(self) -> list[Product]:
        return list(self.__products.values())

    def count(self) -> int:
        return len(self.__products)


# ──────────────────────────────────────────────
#  CLI helpers
# ──────────────────────────────────────────────

DIVIDER = "─" * 70


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def prompt(msg: str, default: str = "") -> str:
    value = input(msg).strip()
    return value if value else default


def prompt_float(msg: str) -> float:
    while True:
        try:
            return float(input(msg).strip())
        except ValueError:
            print("  ✗  Please enter a valid number.")


def prompt_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg).strip())
        except ValueError:
            print("  ✗  Please enter a whole number.")


def print_header(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def print_products(products: list[Product]) -> None:
    if not products:
        print("  (no products found)")
        return
    for p in products:
        print(f"  {p}")


def seed_catalog(catalog: ProductCatalog) -> None:
    """Populate with a few sample products for demonstration."""
    samples = [
        ("Laptop Pro 15",      1299.99, 10, "Electronics"),
        ("Wireless Mouse",       29.95,  50, "Electronics"),
        ("Standing Desk",       449.00,   8, "Furniture"),
        ("Noise-Cancel Headset",129.99,  25, "Electronics"),
        ("Ergonomic Chair",     349.50,   5, "Furniture"),
        ("Python Cookbook",      39.99, 100, "Books"),
    ]
    for name, price, qty, cat in samples:
        catalog.add_product(name, price, qty, cat)


# ──────────────────────────────────────────────
#  Menu actions
# ──────────────────────────────────────────────

def menu_add(catalog: ProductCatalog) -> None:
    print_header("ADD NEW PRODUCT")
    try:
        name     = input("  Name     : ").strip()
        price    = prompt_float("  Price    : ")
        quantity = prompt_int("  Quantity : ")
        category = input("  Category : ").strip()
        product  = catalog.add_product(name, price, quantity, category)
        print(f"\n  ✓  Product added successfully!\n  {product}")
    except ValueError as exc:
        print(f"\n  ✗  Error: {exc}")


def menu_remove(catalog: ProductCatalog) -> None:
    print_header("REMOVE PRODUCT")
    product_id = prompt_int("  Enter product ID to remove: ")
    product    = catalog.search_by_id(product_id)
    if product is None:
        print(f"\n  ✗  No product found with ID {product_id}.")
        return
    print(f"\n  Found: {product}")
    confirm = input("  Confirm removal? (y/n): ").strip().lower()
    if confirm == "y":
        catalog.remove_product(product_id)
        print("  ✓  Product removed.")
    else:
        print("  ↩  Removal cancelled.")


def menu_update(catalog: ProductCatalog) -> None:
    print_header("UPDATE PRODUCT")
    product_id = prompt_int("  Enter product ID to update: ")
    product    = catalog.search_by_id(product_id)
    if product is None:
        print(f"\n  ✗  No product found with ID {product_id}.")
        return

    print(f"\n  Current: {product}")
    print("  (Press Enter to keep current value)\n")

    raw_name  = input(f"  Name     [{product.name}]: ").strip()
    raw_price = input(f"  Price    [{product.price:.2f}]: ").strip()
    raw_qty   = input(f"  Quantity [{product.quantity}]: ").strip()
    raw_cat   = input(f"  Category [{product.category}]: ").strip()

    try:
        updated = catalog.update_product(
            product_id,
            name     = raw_name   or None,
            price    = float(raw_price) if raw_price else None,
            quantity = int(raw_qty)     if raw_qty   else None,
            category = raw_cat          or None,
        )
        if updated:
            print(f"\n  ✓  Updated: {catalog.search_by_id(product_id)}")
    except ValueError as exc:
        print(f"\n  ✗  Error: {exc}")


def menu_search(catalog: ProductCatalog) -> None:
    print_header("SEARCH PRODUCTS")
    print("  1. Search by ID")
    print("  2. Search by Name")
    choice = input("\n  Choice: ").strip()

    if choice == "1":
        product_id = prompt_int("  Enter product ID: ")
        product    = catalog.search_by_id(product_id)
        print()
        if product:
            print(f"  {product}")
        else:
            print(f"  ✗  No product found with ID {product_id}.")

    elif choice == "2":
        query   = input("  Enter name (or partial): ").strip()
        results = catalog.search_by_name(query)
        print(f"\n  Found {len(results)} result(s):")
        print_products(results)
    else:
        print("  ✗  Invalid choice.")


def menu_display_all(catalog: ProductCatalog) -> None:
    print_header(f"ALL PRODUCTS  ({catalog.count()} total)")
    print_products(catalog.get_all_products())


# ──────────────────────────────────────────────
#  Main loop
# ──────────────────────────────────────────────

MENU = """
  ╔══════════════════════════════╗
  ║     PRODUCT CATALOG MENU     ║
  ╠══════════════════════════════╣
  ║  1. Add product              ║
  ║  2. Remove product           ║
  ║  3. Update product           ║
  ║  4. Search product           ║
  ║  5. Display all products     ║
  ║  0. Exit                     ║
  ╚══════════════════════════════╝
"""

ACTIONS = {
    "1": menu_add,
    "2": menu_remove,
    "3": menu_update,
    "4": menu_search,
    "5": menu_display_all,
}


def main() -> None:
    catalog = ProductCatalog()
    seed_catalog(catalog)

    print("\n  Welcome to the Product Catalog Manager!")
    print(f"  ({catalog.count()} sample products pre-loaded)\n")

    while True:
        print(MENU)
        choice = input("  Enter your choice: ").strip()

        if choice == "0":
            print("\n  Goodbye!\n")
            break
        elif choice in ACTIONS:
            ACTIONS[choice](catalog)
        else:
            print("\n  ✗  Invalid choice. Please try again.")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()