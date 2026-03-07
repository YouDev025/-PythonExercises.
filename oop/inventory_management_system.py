"""
inventory_management_system.py
A command-line store inventory manager using Python OOP principles.
"""

from __future__ import annotations
import os
import datetime
from enum import Enum


# ──────────────────────────────────────────────
#  Enums & Constants
# ──────────────────────────────────────────────

class StockStatus(Enum):
    IN_STOCK    = "In Stock"
    LOW_STOCK   = "Low Stock"
    OUT_OF_STOCK = "Out of Stock"


CURRENCY         = "$"
LOW_STOCK_THRESHOLD = 5
DIVIDER          = "─" * 74
DIVIDER2         = "═" * 74


# ──────────────────────────────────────────────
#  StockTransaction  (immutable audit log entry)
# ──────────────────────────────────────────────

class StockTransaction:
    """Records every quantity change for audit purposes."""

    _counter: int = 1

    def __init__(
        self,
        product_id: str,
        change: int,
        reason: str,
        qty_after: int,
    ) -> None:
        self.__tx_id      = StockTransaction._counter
        StockTransaction._counter += 1
        self.__product_id = product_id
        self.__change     = change          # positive = restock, negative = sale/removal
        self.__reason     = reason
        self.__qty_after  = qty_after
        self.__timestamp  = datetime.datetime.now()

    # ── read-only properties ──────────────────

    @property
    def tx_id(self) -> int:           return self.__tx_id
    @property
    def product_id(self) -> str:      return self.__product_id
    @property
    def change(self) -> int:          return self.__change
    @property
    def reason(self) -> str:          return self.__reason
    @property
    def qty_after(self) -> int:       return self.__qty_after
    @property
    def timestamp(self) -> datetime.datetime: return self.__timestamp

    def __str__(self) -> str:
        sign  = "+" if self.__change >= 0 else ""
        ts    = self.__timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"  [#{self.__tx_id:<4}]  {ts}  "
            f"ID: {self.__product_id:<10}  "
            f"Change: {sign}{self.__change:<6}  "
            f"Qty after: {self.__qty_after:<6}  "
            f"Reason: {self.__reason}"
        )


# ──────────────────────────────────────────────
#  Product
# ──────────────────────────────────────────────

class Product:
    """Represents a single inventory item with full encapsulation."""

    _id_counter: int = 1000

    def __init__(
        self,
        name: str,
        quantity: int,
        price: float,
        category: str,
        product_id: str | None = None,
    ) -> None:
        if product_id is not None:
            self.__id = str(product_id).strip().upper()
        else:
            self.__id = f"P{Product._id_counter}"
            Product._id_counter += 1

        self.name     = name
        self.quantity = quantity
        self.price    = price
        self.category = category
        self.__created_at = datetime.datetime.now()
        self.__updated_at = datetime.datetime.now()

    # ── properties ────────────────────────────

    @property
    def product_id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip().title()
        if not value:
            raise ValueError("Product name cannot be empty.")
        self.__name = value
        self.__touch()

    @property
    def quantity(self) -> int:
        return self.__quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        value = int(value)
        if value < 0:
            raise ValueError("Quantity cannot be negative.")
        self.__quantity = value
        self.__touch()

    @property
    def price(self) -> float:
        return self.__price

    @price.setter
    def price(self, value: float) -> None:
        value = float(value)
        if value < 0:
            raise ValueError("Price cannot be negative.")
        self.__price = round(value, 2)
        self.__touch()

    @property
    def category(self) -> str:
        return self.__category

    @category.setter
    def category(self, value: str) -> None:
        value = value.strip().title()
        if not value:
            raise ValueError("Category cannot be empty.")
        self.__category = value
        self.__touch()

    @property
    def created_at(self) -> datetime.datetime:
        return self.__created_at

    @property
    def updated_at(self) -> datetime.datetime:
        return self.__updated_at

    # ── computed properties ───────────────────

    @property
    def total_value(self) -> float:
        return round(self.__price * self.__quantity, 2)

    @property
    def stock_status(self) -> StockStatus:
        if self.__quantity == 0:
            return StockStatus.OUT_OF_STOCK
        if self.__quantity <= LOW_STOCK_THRESHOLD:
            return StockStatus.LOW_STOCK
        return StockStatus.IN_STOCK

    @property
    def status_badge(self) -> str:
        badges = {
            StockStatus.IN_STOCK:     "🟢 In Stock",
            StockStatus.LOW_STOCK:    "🟡 Low Stock",
            StockStatus.OUT_OF_STOCK: "🔴 Out of Stock",
        }
        return badges[self.stock_status]

    # ── stock mutation ────────────────────────

    def restock(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Restock amount must be positive.")
        self.__quantity += amount
        self.__touch()

    def sell(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Sell amount must be positive.")
        if amount > self.__quantity:
            raise ValueError(
                f"Insufficient stock. Available: {self.__quantity}, requested: {amount}."
            )
        self.__quantity -= amount
        self.__touch()

    # ── private helpers ───────────────────────

    def __touch(self) -> None:
        try:
            self.__updated_at = datetime.datetime.now()
        except AttributeError:
            pass   # called during __init__ before __updated_at exists

    # ── display helpers ───────────────────────

    def one_liner(self) -> str:
        return (
            f"  [{self.__id:<6}]  {self.__name:<28}  "
            f"{self.__category:<16}  "
            f"Qty: {self.__quantity:>5}  "
            f"{CURRENCY}{self.__price:>8.2f}  "
            f"Value: {CURRENCY}{self.total_value:>10.2f}  "
            f"{self.status_badge}"
        )

    def detail_card(self) -> str:
        return (
            f"\n  {DIVIDER}\n"
            f"  Product ID  : {self.__id}\n"
            f"  Name        : {self.__name}\n"
            f"  Category    : {self.__category}\n"
            f"  Price       : {CURRENCY}{self.__price:.2f}\n"
            f"  Quantity    : {self.__quantity}\n"
            f"  Total Value : {CURRENCY}{self.total_value:.2f}\n"
            f"  Status      : {self.status_badge}\n"
            f"  Created     : {self.__created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"  Updated     : {self.__updated_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"  {DIVIDER}"
        )

    def __str__(self) -> str:
        return self.one_liner()

    def __repr__(self) -> str:
        return (
            f"Product(id={self.__id!r}, name={self.__name!r}, "
            f"qty={self.__quantity}, price={self.__price})"
        )


# ──────────────────────────────────────────────
#  InventoryManager
# ──────────────────────────────────────────────

class InventoryManager:
    """Central registry for all products with full CRUD and reporting."""

    def __init__(self, store_name: str = "PyStore") -> None:
        self.__store_name  = store_name
        self.__products:   dict[str, Product]          = {}
        self.__transactions: list[StockTransaction]    = []

    # ── properties ────────────────────────────

    @property
    def store_name(self) -> str:
        return self.__store_name

    # ── internal helpers ──────────────────────

    def __log(self, product_id: str, change: int, reason: str, qty_after: int) -> None:
        self.__transactions.append(
            StockTransaction(product_id, change, reason, qty_after)
        )

    # ── Product CRUD ──────────────────────────

    def add_product(
        self,
        name: str,
        quantity: int,
        price: float,
        category: str,
    ) -> str:
        try:
            product = Product(name, quantity, price, category)
        except ValueError as e:
            return f"  ✗  {e}"
        self.__products[product.product_id] = product
        self.__log(product.product_id, quantity, "Initial stock", quantity)
        return (
            f"  ✓  Product added: '{product.name}'  "
            f"(ID: {product.product_id})  "
            f"Qty: {quantity}  Price: {CURRENCY}{price:.2f}"
        )

    def remove_product(self, product_id: str) -> str:
        pid = product_id.strip().upper()
        if pid not in self.__products:
            return f"  ✗  Product '{pid}' not found."
        name = self.__products[pid].name
        self.__log(pid, -self.__products[pid].quantity, "Product removed", 0)
        del self.__products[pid]
        return f"  ✓  Product '{name}' (ID: {pid}) removed from inventory."

    def get_product(self, product_id: str) -> Product | None:
        return self.__products.get(product_id.strip().upper())

    def update_product(
        self,
        product_id: str,
        name: str | None = None,
        price: float | None = None,
        category: str | None = None,
    ) -> str:
        product = self.get_product(product_id)
        if product is None:
            return f"  ✗  Product '{product_id.upper()}' not found."
        try:
            if name is not None:
                product.name = name
            if price is not None:
                product.price = price
            if category is not None:
                product.category = category
        except ValueError as e:
            return f"  ✗  {e}"
        return f"  ✓  Product '{product.name}' (ID: {product.product_id}) updated."

    # ── Stock operations ──────────────────────

    def restock(self, product_id: str, amount: int) -> str:
        product = self.get_product(product_id)
        if product is None:
            return f"  ✗  Product '{product_id.upper()}' not found."
        try:
            product.restock(amount)
        except ValueError as e:
            return f"  ✗  {e}"
        self.__log(product.product_id, amount, "Restock", product.quantity)
        return (
            f"  ✓  Restocked '{product.name}' by +{amount}.  "
            f"New quantity: {product.quantity}"
        )

    def sell_stock(self, product_id: str, amount: int) -> str:
        product = self.get_product(product_id)
        if product is None:
            return f"  ✗  Product '{product_id.upper()}' not found."
        try:
            product.sell(amount)
        except ValueError as e:
            return f"  ✗  {e}"
        self.__log(product.product_id, -amount, "Sale", product.quantity)
        warning = (
            f"\n  ⚠  Warning: '{product.name}' is now low on stock ({product.quantity} left)."
            if product.stock_status == StockStatus.LOW_STOCK else
            f"\n  ⚠  Warning: '{product.name}' is now OUT OF STOCK."
            if product.stock_status == StockStatus.OUT_OF_STOCK else ""
        )
        return (
            f"  ✓  Sold {amount}x '{product.name}'.  "
            f"Remaining: {product.quantity}{warning}"
        )

    # ── Search ────────────────────────────────

    def search_by_name(self, query: str) -> list[Product]:
        q = query.lower()
        return [p for p in self.__products.values() if q in p.name.lower()]

    def search_by_category(self, query: str) -> list[Product]:
        q = query.lower()
        return [p for p in self.__products.values() if q in p.category.lower()]

    def get_low_stock(self) -> list[Product]:
        return [
            p for p in self.__products.values()
            if p.stock_status in (StockStatus.LOW_STOCK, StockStatus.OUT_OF_STOCK)
        ]

    def get_all_products(
        self,
        sort_by: str = "name",
        category_filter: str | None = None,
    ) -> list[Product]:
        products = list(self.__products.values())
        if category_filter:
            products = [p for p in products if p.category.lower() == category_filter.lower()]
        sort_keys = {
            "name":     lambda p: p.name,
            "price":    lambda p: p.price,
            "quantity": lambda p: p.quantity,
            "category": lambda p: (p.category, p.name),
            "value":    lambda p: p.total_value,
            "id":       lambda p: p.product_id,
        }
        key = sort_keys.get(sort_by, sort_keys["name"])
        return sorted(products, key=key)

    def get_categories(self) -> list[str]:
        return sorted(set(p.category for p in self.__products.values()))

    def product_count(self) -> int:
        return len(self.__products)

    # ── Reporting ─────────────────────────────

    def total_inventory_value(self) -> float:
        return round(sum(p.total_value for p in self.__products.values()), 2)

    def get_transactions(self, product_id: str | None = None, last_n: int | None = 20) -> list[StockTransaction]:
        txs = self.__transactions
        if product_id:
            txs = [t for t in txs if t.product_id == product_id.upper()]
        return txs[-last_n:] if last_n else txs

    def category_report(self) -> dict[str, tuple[int, float]]:
        """Returns {category: (product_count, total_value)}."""
        result: dict[str, list] = {}
        for p in self.__products.values():
            if p.category not in result:
                result[p.category] = [0, 0.0]
            result[p.category][0] += 1
            result[p.category][1] += p.total_value
        return {k: (v[0], round(v[1], 2)) for k, v in result.items()}


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


def prompt_int(msg: str, allow_zero: bool = True) -> int:
    while True:
        try:
            v = int(input(msg).strip())
            if not allow_zero and v == 0:
                print("  ✗  Value must not be zero.")
                continue
            return v
        except ValueError:
            print("  ✗  Please enter a whole number.")


def prompt_positive_int(msg: str) -> int:
    while True:
        try:
            v = int(input(msg).strip())
            if v <= 0:
                print("  ✗  Value must be greater than zero.")
                continue
            return v
        except ValueError:
            print("  ✗  Please enter a whole number.")


def prompt_float(msg: str) -> float:
    while True:
        try:
            v = float(input(msg).strip())
            if v < 0:
                print("  ✗  Value cannot be negative.")
                continue
            return v
        except ValueError:
            print("  ✗  Please enter a number.")


def print_product_table_header() -> None:
    print(f"\n  {'ID':<8}  {'Name':<28}  {'Category':<16}  {'Qty':>5}  {'Price':>9}  {'Total Value':>12}  Status")
    print(f"  {'─'*8}  {'─'*28}  {'─'*16}  {'─'*5}  {'─'*9}  {'─'*12}  {'─'*16}")


def print_products(products: list[Product]) -> None:
    if not products:
        print("  (no products)")
        return
    print_product_table_header()
    for p in products:
        print(p)


def pick_sort_key() -> str:
    keys = ["name", "price", "quantity", "category", "value", "id"]
    print("\n  Sort by:")
    for i, k in enumerate(keys, 1):
        print(f"    {i}. {k.title()}")
    raw = input("  Choice [1=Name]: ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(keys):
        return keys[int(raw) - 1]
    return "name"


# ──────────────────────────────────────────────
#  Seed data
# ──────────────────────────────────────────────

def seed_inventory(mgr: InventoryManager) -> None:
    products = [
        ("Laptop Pro 15\"",     12,  1_299.99, "Electronics"),
        ("Wireless Mouse",      45,     29.95, "Electronics"),
        ("USB-C Hub 7-in-1",    30,     39.99, "Electronics"),
        ("Mechanical Keyboard",  8,     89.95, "Electronics"),
        ("27\" 4K Monitor",      5,    349.00, "Electronics"),
        ("Standing Desk",        3,    449.00, "Furniture"),
        ("Ergonomic Chair",      7,    299.50, "Furniture"),
        ("Desk Lamp LED",       22,     24.99, "Furniture"),
        ("Notebook A5 Pack",    60,      8.99, "Stationery"),
        ("Ballpoint Pens Box",  80,      5.49, "Stationery"),
        ("Sticky Notes (100)",  50,      3.99, "Stationery"),
        ("Python Cookbook",     18,     39.99, "Books"),
        ("Clean Code",          14,     35.00, "Books"),
        ("Design Patterns",      2,     42.00, "Books"),
        ("Coffee Blend 1kg",    25,     18.99, "Beverages"),
        ("Green Tea Box",        4,     12.50, "Beverages"),
    ]
    for name, qty, price, cat in products:
        mgr.add_product(name, qty, price, cat)


# ──────────────────────────────────────────────
#  Menu actions
# ──────────────────────────────────────────────

def menu_view_all(mgr: InventoryManager) -> None:
    print_header(
        f"ALL PRODUCTS  —  {mgr.store_name}",
        f"{mgr.product_count()} products  |  "
        f"Total value: {CURRENCY}{mgr.total_inventory_value():,.2f}",
    )
    sort_by = pick_sort_key()

    # Optional category filter
    cats = mgr.get_categories()
    print(f"\n  Filter by category? Categories: {', '.join(cats)}")
    cat_filter = input("  Category (Enter to skip): ").strip() or None

    products = mgr.get_all_products(sort_by=sort_by, category_filter=cat_filter)
    label    = f" — Category: {cat_filter}" if cat_filter else ""
    print_header(f"PRODUCTS  (sorted by {sort_by.title()}){label}", f"{len(products)} item(s)")
    print_products(products)

    total = sum(p.total_value for p in products)
    print(f"\n  {'─'*54}")
    print(f"  Subtotal value: {CURRENCY}{total:,.2f}")


def menu_add_product(mgr: InventoryManager) -> None:
    print_header("ADD NEW PRODUCT")
    try:
        name     = input("  Name      : ").strip()
        category = input("  Category  : ").strip()
        price    = prompt_float("  Price     : $")
        quantity = prompt_int("  Quantity  : ", allow_zero=True)
        print(f"\n{mgr.add_product(name, quantity, price, category)}")
    except KeyboardInterrupt:
        print("\n  ↩  Cancelled.")


def menu_remove_product(mgr: InventoryManager) -> None:
    print_header("REMOVE PRODUCT")
    if mgr.product_count() == 0:
        print("  Inventory is empty.")
        return
    pid     = input("  Product ID : ").strip().upper()
    product = mgr.get_product(pid)
    if product is None:
        print(f"  ✗  Product '{pid}' not found.")
        return
    print(f"\n{product.detail_card()}")
    confirm = input("  Permanently remove this product? (y/n): ").strip().lower()
    if confirm == "y":
        print(f"\n{mgr.remove_product(pid)}")
    else:
        print("  ↩  Removal cancelled.")


def menu_update_product(mgr: InventoryManager) -> None:
    print_header("UPDATE PRODUCT")
    pid     = input("  Product ID : ").strip().upper()
    product = mgr.get_product(pid)
    if product is None:
        print(f"  ✗  Product '{pid}' not found.")
        return
    print(product.detail_card())
    print("  (Press Enter to keep current value)\n")

    raw_name  = input(f"  Name     [{product.name}]     : ").strip()
    raw_price = input(f"  Price    [{product.price:.2f}]  : ").strip()
    raw_cat   = input(f"  Category [{product.category}] : ").strip()

    try:
        result = mgr.update_product(
            pid,
            name     = raw_name  or None,
            price    = float(raw_price) if raw_price else None,
            category = raw_cat   or None,
        )
        print(f"\n{result}")
    except ValueError as e:
        print(f"\n  ✗  {e}")


def menu_restock(mgr: InventoryManager) -> None:
    print_header("RESTOCK — INCREASE QUANTITY")
    pid = input("  Product ID : ").strip().upper()
    p   = mgr.get_product(pid)
    if p is None:
        print(f"  ✗  Product '{pid}' not found.")
        return
    print(f"\n  Product: {p.name}  |  Current qty: {p.quantity}\n")
    amount = prompt_positive_int("  Amount to add: ")
    print(f"\n{mgr.restock(pid, amount)}")


def menu_sell(mgr: InventoryManager) -> None:
    print_header("SELL / DECREASE QUANTITY")
    pid = input("  Product ID : ").strip().upper()
    p   = mgr.get_product(pid)
    if p is None:
        print(f"  ✗  Product '{pid}' not found.")
        return
    if p.quantity == 0:
        print(f"  ✗  '{p.name}' is out of stock.")
        return
    print(f"\n  Product: {p.name}  |  Current qty: {p.quantity}\n")
    amount = prompt_positive_int("  Amount to sell: ")
    print(f"\n{mgr.sell_stock(pid, amount)}")


def menu_search(mgr: InventoryManager) -> None:
    print_header("SEARCH PRODUCTS")
    print("  1. Search by name")
    print("  2. Search by ID")
    print("  3. Search by category")
    print("  4. Show low / out-of-stock items")
    choice = input("\n  Choice: ").strip()

    if choice == "1":
        query   = input("  Name query: ").strip()
        results = mgr.search_by_name(query)
        print_header(f"RESULTS FOR \"{query}\"", f"{len(results)} match(es)")
        print_products(results)

    elif choice == "2":
        pid     = input("  Product ID: ").strip().upper()
        product = mgr.get_product(pid)
        if product:
            print(product.detail_card())
        else:
            print(f"  ✗  Product '{pid}' not found.")

    elif choice == "3":
        query   = input("  Category: ").strip()
        results = mgr.search_by_category(query)
        print_header(f"CATEGORY: \"{query}\"", f"{len(results)} product(s)")
        print_products(results)

    elif choice == "4":
        results = mgr.get_low_stock()
        print_header("LOW / OUT-OF-STOCK PRODUCTS", f"{len(results)} item(s) need attention")
        if not results:
            print("  All products are well-stocked. ✓")
        else:
            print_products(results)
    else:
        print("  ✗  Invalid choice.")


def menu_inventory_value(mgr: InventoryManager) -> None:
    print_header(
        "INVENTORY VALUE REPORT",
        f"Total: {CURRENCY}{mgr.total_inventory_value():,.2f}",
    )
    cat_report = mgr.category_report()
    total      = mgr.total_inventory_value()

    print(f"\n  {'Category':<20}  {'Products':>9}  {'Total Value':>14}  {'% of Inventory':>16}")
    print(f"  {'─'*20}  {'─'*9}  {'─'*14}  {'─'*16}")
    for cat, (count, value) in sorted(cat_report.items(), key=lambda x: -x[1][1]):
        pct = (value / total * 100) if total else 0
        print(f"  {cat:<20}  {count:>9}  {CURRENCY}{value:>13,.2f}  {pct:>15.1f}%")

    print(f"\n  {DIVIDER}")
    print(f"  {'TOTAL':<20}  {mgr.product_count():>9}  {CURRENCY}{total:>13,.2f}  {'100.0%':>16}")

    # Top 5 by value
    top5 = mgr.get_all_products(sort_by="value")[-5:][::-1]
    print(f"\n  Top 5 products by total value:")
    print(f"  {'─'*50}")
    for p in top5:
        print(f"    [{p.product_id}]  {p.name:<30}  {CURRENCY}{p.total_value:,.2f}")


def menu_transaction_log(mgr: InventoryManager) -> None:
    print_header("STOCK TRANSACTION LOG  (Last 20)")
    txs = mgr.get_transactions()
    if not txs:
        print("  No transactions recorded.")
        return
    for tx in txs:
        print(tx)


def menu_dashboard(mgr: InventoryManager) -> None:
    print_header(f"DASHBOARD  —  {mgr.store_name}")
    products = mgr.get_all_products()
    low      = mgr.get_low_stock()
    cats     = mgr.get_categories()
    total_v  = mgr.total_inventory_value()

    in_stock = sum(1 for p in products if p.stock_status == StockStatus.IN_STOCK)
    low_s    = sum(1 for p in products if p.stock_status == StockStatus.LOW_STOCK)
    out_s    = sum(1 for p in products if p.stock_status == StockStatus.OUT_OF_STOCK)

    print(f"  {'Store':<28}: {mgr.store_name}")
    print(f"  {'Total Products':<28}: {mgr.product_count()}")
    print(f"  {'Categories':<28}: {len(cats)}  ({', '.join(cats)})")
    print(f"  {'Total Inventory Value':<28}: {CURRENCY}{total_v:,.2f}")
    print(f"  {'🟢 In Stock':<28}: {in_stock}")
    print(f"  {'🟡 Low Stock':<28}: {low_s}")
    print(f"  {'🔴 Out of Stock':<28}: {out_s}")
    print(f"  {'Stock Transactions':<28}: {len(mgr.get_transactions(last_n=None))}")

    if low:
        print(f"\n  ⚠  Items needing attention ({len(low)}):")
        for p in low:
            print(f"     [{p.product_id}]  {p.name:<28}  Qty: {p.quantity}  {p.status_badge}")


# ──────────────────────────────────────────────
#  Main menu loop
# ──────────────────────────────────────────────

MENU = """
  ╔════════════════════════════════════════╗
  ║       INVENTORY MANAGEMENT SYSTEM      ║
  ╠════════════════════════════════════════╣
  ║   PRODUCTS                             ║
  ║   1.   View all products               ║
  ║   2.   Add new product                 ║
  ║   3.   Update product info             ║
  ║   4.   Remove product                  ║
  ╠════════════════════════════════════════╣
  ║   STOCK                                ║
  ║   5.   Restock (increase quantity)     ║
  ║   6.   Sell (decrease quantity)        ║
  ╠════════════════════════════════════════╣
  ║   SEARCH & REPORTS                     ║
  ║   7.   Search products                 ║
  ║   8.   Inventory value report          ║
  ║   9.   Stock transaction log           ║
  ║   10.  Dashboard                       ║
  ╠════════════════════════════════════════╣
  ║   0.   Exit                            ║
  ╚════════════════════════════════════════╝"""

ACTIONS = {
    "1":  menu_view_all,
    "2":  menu_add_product,
    "3":  menu_update_product,
    "4":  menu_remove_product,
    "5":  menu_restock,
    "6":  menu_sell,
    "7":  menu_search,
    "8":  menu_inventory_value,
    "9":  menu_transaction_log,
    "10": menu_dashboard,
}


def main() -> None:
    mgr = InventoryManager("PyStore Inventory")
    seed_inventory(mgr)

    print(f"\n{DIVIDER2}")
    print(f"  Welcome to {mgr.store_name}")
    print(
        f"  {mgr.product_count()} products loaded  |  "
        f"Total value: {CURRENCY}{mgr.total_inventory_value():,.2f}  |  "
        f"Date: {datetime.date.today()}"
    )
    print(DIVIDER2)

    first = True
    while True:
        if not first:
            cls()
        first = False

        print(MENU)

        # Live status bar
        low_count = len(mgr.get_low_stock())
        alert     = f"  ⚠  {low_count} item(s) need restocking!" if low_count else ""
        print(
            f"  Products: {mgr.product_count()}  |  "
            f"Value: {CURRENCY}{mgr.total_inventory_value():,.2f}"
            + (f"  |  {alert}" if alert else "")
        )
        print()

        choice = input("  Select option: ").strip()

        if choice == "0":
            print(f"\n  Goodbye from {mgr.store_name}!\n")
            break
        elif choice in ACTIONS:
            ACTIONS[choice](mgr)
        else:
            print("\n  ✗  Invalid option. Please try again.")

        input("\n  Press Enter to return to menu...")


if __name__ == "__main__":
    main()