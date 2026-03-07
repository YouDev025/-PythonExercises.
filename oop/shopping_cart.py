"""
object_oriented_shopping_cart.py
A command-line shopping cart simulator using Python OOP principles.
"""

from __future__ import annotations
import os


# ──────────────────────────────────────────────
#  Product
# ──────────────────────────────────────────────

class Product:
    """Represents a store product available for purchase."""

    _id_counter: int = 1

    def __init__(
        self,
        name: str,
        price: float,
        stock: int,
        product_id: int | None = None,
    ) -> None:
        if product_id is not None:
            self.__id = product_id
        else:
            self.__id = Product._id_counter
            Product._id_counter += 1

        self.name  = name
        self.price = price
        self.stock = stock

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
    def stock(self) -> int:
        return self.__stock

    @stock.setter
    def stock(self, value: int) -> None:
        value = int(value)
        if value < 0:
            raise ValueError("Stock cannot be negative.")
        self.__stock = value

    # ── helpers ───────────────────────────────

    def __str__(self) -> str:
        stock_label = f"{self.__stock} in stock" if self.__stock else "OUT OF STOCK"
        return (
            f"[ID: {self.__id:>3}]  {self.__name:<28}  "
            f"${self.__price:>8.2f}   {stock_label}"
        )

    def __repr__(self) -> str:
        return (
            f"Product(id={self.__id}, name={self.__name!r}, "
            f"price={self.__price}, stock={self.__stock})"
        )


# ──────────────────────────────────────────────
#  CartItem  (internal wrapper)
# ──────────────────────────────────────────────

class CartItem:
    """Associates a Product with the quantity chosen by the shopper."""

    def __init__(self, product: Product, quantity: int) -> None:
        self.__product  = product
        self.quantity   = quantity          # validated via setter

    @property
    def product(self) -> Product:
        return self.__product

    @property
    def quantity(self) -> int:
        return self.__quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        value = int(value)
        if value < 1:
            raise ValueError("Cart quantity must be at least 1.")
        self.__quantity = value

    @property
    def subtotal(self) -> float:
        return round(self.__product.price * self.__quantity, 2)

    def __str__(self) -> str:
        return (
            f"  [ID: {self.__product.id:>3}]  {self.__product.name:<28}  "
            f"${self.__product.price:>8.2f}  x{self.__quantity:<4}  "
            f"= ${self.subtotal:>9.2f}"
        )


# ──────────────────────────────────────────────
#  ShoppingCart
# ──────────────────────────────────────────────

class ShoppingCart:
    """Manages a shopper's collection of CartItems."""

    def __init__(self) -> None:
        self.__items: dict[int, CartItem] = {}   # keyed by product_id

    # ── public methods ────────────────────────

    def add_product(self, product: Product, quantity: int = 1) -> str:
        """
        Add `quantity` units of `product` to the cart.
        Respects available stock and merges with any existing cart entry.
        Returns a human-readable result message.
        """
        if product.stock == 0:
            return f"  ✗  '{product.name}' is out of stock."

        existing_qty = self.__items[product.id].quantity if product.id in self.__items else 0
        available    = product.stock - existing_qty

        if quantity > available:
            return (
                f"  ✗  Only {available} more unit(s) of '{product.name}' available "
                f"(you already have {existing_qty} in your cart)."
            )

        if product.id in self.__items:
            self.__items[product.id].quantity += quantity
        else:
            self.__items[product.id] = CartItem(product, quantity)

        return f"  ✓  Added {quantity}× '{product.name}' to the cart."

    def remove_product(self, product_id: int) -> bool:
        """Remove a product entirely from the cart. Returns True if found."""
        if product_id in self.__items:
            del self.__items[product_id]
            return True
        return False

    def update_quantity(self, product_id: int, quantity: int) -> str:
        """
        Change the cart quantity for a product.
        Returns a human-readable result message.
        """
        if product_id not in self.__items:
            return f"  ✗  Product ID {product_id} is not in the cart."
        item = self.__items[product_id]
        if quantity > item.product.stock:
            return (
                f"  ✗  Only {item.product.stock} unit(s) of "
                f"'{item.product.name}' in stock."
            )
        try:
            item.quantity = quantity
        except ValueError as exc:
            return f"  ✗  {exc}"
        return f"  ✓  Updated '{item.product.name}' quantity to {quantity}."

    def get_items(self) -> list[CartItem]:
        return list(self.__items.values())

    def is_empty(self) -> bool:
        return len(self.__items) == 0

    def item_count(self) -> int:
        return sum(item.quantity for item in self.__items.values())

    def total(self) -> float:
        return round(sum(item.subtotal for item in self.__items.values()), 2)

    def clear(self) -> None:
        self.__items.clear()


# ──────────────────────────────────────────────
#  Store (product catalogue)
# ──────────────────────────────────────────────

class Store:
    """Holds all products available for purchase."""

    def __init__(self) -> None:
        self.__products: dict[int, Product] = {}

    def add_product(self, name: str, price: float, stock: int) -> Product:
        p = Product(name, price, stock)
        self.__products[p.id] = p
        return p

    def get_by_id(self, product_id: int) -> Product | None:
        return self.__products.get(product_id)

    def get_all(self) -> list[Product]:
        return list(self.__products.values())

    def count(self) -> int:
        return len(self.__products)


# ──────────────────────────────────────────────
#  CLI helpers
# ──────────────────────────────────────────────

DIVIDER = "─" * 72


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def prompt_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg).strip())
        except ValueError:
            print("  ✗  Please enter a whole number.")


def seed_store(store: Store) -> None:
    """Pre-populate the store with sample products."""
    items = [
        ("Laptop Pro 15″",        1_299.99, 5),
        ("Mechanical Keyboard",      89.95, 20),
        ("4K Webcam",                74.99, 15),
        ("Noise-Cancel Headset",    129.99, 10),
        ("USB-C Hub 7-in-1",         39.99, 30),
        ("Ergonomic Mouse",          49.95, 25),
        ("27″ Monitor",             349.00,  8),
        ("Laptop Stand",             29.99, 40),
        ("Cable Management Kit",     14.99, 50),
        ("Desk Lamp LED",            24.99, 35),
    ]
    for name, price, stock in items:
        store.add_product(name, price, stock)


# ──────────────────────────────────────────────
#  Menu actions
# ──────────────────────────────────────────────

def menu_browse(store: Store) -> None:
    print_header("STORE CATALOGUE")
    col = f"  {'ID':>3}   {'Name':<28}  {'Price':>10}   Stock"
    print(col)
    print(f"  {'─'*3}   {'─'*28}  {'─'*10}   {'─'*12}")
    for p in store.get_all():
        print(f"  {p}")


def menu_add_to_cart(store: Store, cart: ShoppingCart) -> None:
    print_header("ADD TO CART")
    menu_browse(store)
    print()
    product_id = prompt_int("  Enter product ID to add: ")
    product    = store.get_by_id(product_id)
    if product is None:
        print(f"\n  ✗  No product found with ID {product_id}.")
        return
    quantity = prompt_int(f"  Quantity (available: {product.stock}): ")
    print(f"\n{cart.add_product(product, quantity)}")


def menu_remove_from_cart(cart: ShoppingCart) -> None:
    print_header("REMOVE FROM CART")
    if cart.is_empty():
        print("  Your cart is empty.")
        return
    menu_view_cart(cart)
    print()
    product_id = prompt_int("  Enter product ID to remove: ")
    if cart.remove_product(product_id):
        print(f"  ✓  Item removed from cart.")
    else:
        print(f"  ✗  Product ID {product_id} is not in the cart.")


def menu_update_quantity(cart: ShoppingCart) -> None:
    print_header("UPDATE QUANTITY")
    if cart.is_empty():
        print("  Your cart is empty.")
        return
    menu_view_cart(cart)
    print()
    product_id = prompt_int("  Enter product ID to update: ")
    new_qty    = prompt_int("  New quantity            : ")
    print(f"\n{cart.update_quantity(product_id, new_qty)}")


def menu_view_cart(cart: ShoppingCart) -> None:
    print_header(f"YOUR CART  ({cart.item_count()} item(s))")
    if cart.is_empty():
        print("  Your cart is empty.")
        return

    col = f"  {'ID':>3}   {'Name':<28}  {'Unit Price':>10}   Qty    Subtotal"
    print(col)
    print(f"  {'─'*3}   {'─'*28}  {'─'*10}   {'─'*5}  {'─'*11}")
    for item in cart.get_items():
        print(item)
    print(f"\n  {DIVIDER[:58]}")
    print(f"  {'TOTAL':>55}  ${cart.total():>9.2f}")


def menu_checkout(cart: ShoppingCart) -> None:
    print_header("CHECKOUT")
    if cart.is_empty():
        print("  Your cart is empty — nothing to check out.")
        return

    menu_view_cart(cart)
    print()
    confirm = input("  Confirm purchase? (y/n): ").strip().lower()
    if confirm == "y":
        total = cart.total()
        cart.clear()
        print(f"\n  ✓  Purchase complete!  Amount charged: ${total:.2f}")
        print("  Thank you for shopping with us! 🎉")
    else:
        print("  ↩  Checkout cancelled.")


def menu_clear_cart(cart: ShoppingCart) -> None:
    print_header("CLEAR CART")
    if cart.is_empty():
        print("  Your cart is already empty.")
        return
    confirm = input("  Remove all items from the cart? (y/n): ").strip().lower()
    if confirm == "y":
        cart.clear()
        print("  ✓  Cart cleared.")
    else:
        print("  ↩  Cancelled.")


# ──────────────────────────────────────────────
#  Main loop
# ──────────────────────────────────────────────

MENU = """
  ╔════════════════════════════════╗
  ║      SHOPPING CART SYSTEM      ║
  ╠════════════════════════════════╣
  ║  1. Browse store               ║
  ║  2. Add item to cart           ║
  ║  3. Remove item from cart      ║
  ║  4. Update item quantity       ║
  ║  5. View cart                  ║
  ║  6. Checkout                   ║
  ║  7. Clear cart                 ║
  ║  0. Exit                       ║
  ╚════════════════════════════════╝
"""

ACTIONS = {
    "1": lambda store, cart: menu_browse(store),
    "2": lambda store, cart: menu_add_to_cart(store, cart),
    "3": lambda store, cart: menu_remove_from_cart(cart),
    "4": lambda store, cart: menu_update_quantity(cart),
    "5": lambda store, cart: menu_view_cart(cart),
    "6": lambda store, cart: menu_checkout(cart),
    "7": lambda store, cart: menu_clear_cart(cart),
}


def main() -> None:
    store = Store()
    cart  = ShoppingCart()
    seed_store(store)

    print("\n  Welcome to the OOP Shopping Cart! 🛒")
    print(f"  {store.count()} products are available in the store.\n")

    while True:
        print(MENU)
        choice = input("  Enter your choice: ").strip()

        if choice == "0":
            print("\n  Thanks for visiting — goodbye! 👋\n")
            break
        elif choice in ACTIONS:
            ACTIONS[choice](store, cart)
        else:
            print("\n  ✗  Invalid choice. Please try again.")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()