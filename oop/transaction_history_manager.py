"""
Transaction History Manager
A secure OOP-based financial transaction management system with a CLI menu.
"""

import os
from datetime import datetime


# ─────────────────────────────────────────────
#  TRANSACTION CLASS
# ─────────────────────────────────────────────

class Transaction:
    """Represents a single financial transaction with encapsulated data."""

    TYPE_DEPOSIT    = "Deposit"
    TYPE_WITHDRAWAL = "Withdrawal"
    TYPE_TRANSFER   = "Transfer"
    VALID_TYPES     = {TYPE_DEPOSIT, TYPE_WITHDRAWAL, TYPE_TRANSFER}

    def __init__(self, transaction_id: int, amount: float,
                 t_type: str, description: str = "", date: str = ""):
        if t_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid type '{t_type}'. Must be one of: {self.VALID_TYPES}")
        if amount <= 0:
            raise ValueError("Amount must be a positive number.")

        self.__transaction_id: int   = transaction_id
        self.__amount: float         = round(amount, 2)
        self.__type: str             = t_type
        self.__description: str      = description.strip() or "No description"
        self.__date: str             = date or datetime.now().strftime("%Y-%m-%d")
        self.__timestamp: str        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Read-only properties ────────────────────

    @property
    def transaction_id(self) -> int:
        return self.__transaction_id

    @property
    def amount(self) -> float:
        return self.__amount

    @property
    def type(self) -> str:
        return self.__type

    @property
    def description(self) -> str:
        return self.__description

    @property
    def date(self) -> str:
        return self.__date

    @property
    def timestamp(self) -> str:
        return self.__timestamp

    # ── Helpers ─────────────────────────────────

    @property
    def signed_amount(self) -> float:
        """Returns negative amount for withdrawals/transfers, positive for deposits."""
        return self.__amount if self.__type == self.TYPE_DEPOSIT else -self.__amount

    def to_dict(self) -> dict:
        return {
            "ID":          self.__transaction_id,
            "Date":        self.__date,
            "Type":        self.__type,
            "Amount":      f"${self.__amount:,.2f}",
            "Description": self.__description,
            "Recorded At": self.__timestamp,
        }

    def __repr__(self) -> str:
        sign = "+" if self.__type == self.TYPE_DEPOSIT else "-"
        return (f"Transaction(id={self.__transaction_id}, "
                f"date='{self.__date}', type='{self.__type}', "
                f"amount={sign}${self.__amount:,.2f})")


# ─────────────────────────────────────────────
#  TRANSACTION HISTORY CLASS
# ─────────────────────────────────────────────

class TransactionHistory:
    """Stores and manages all financial transactions."""

    def __init__(self, account_name: str = "My Account"):
        self.__account_name: str              = account_name
        self.__transactions: list[Transaction] = []
        self.__next_id: int                   = 1

    # ── Internal helpers ────────────────────────

    def _next_id(self) -> int:
        uid = self.__next_id
        self.__next_id += 1
        return uid

    def _find_by_id(self, tid: int) -> "Transaction | None":
        return next((t for t in self.__transactions if t.transaction_id == tid), None)

    @staticmethod
    def _validate_amount(raw: str) -> tuple[bool, float, str]:
        try:
            val = float(raw.replace(",", "").replace("$", "").strip())
            if val <= 0:
                return False, 0.0, "Amount must be greater than zero."
            return True, val, "OK"
        except ValueError:
            return False, 0.0, "Please enter a valid numeric amount."

    @staticmethod
    def _validate_date(raw: str) -> tuple[bool, str]:
        raw = raw.strip()
        if not raw:
            return True, datetime.now().strftime("%Y-%m-%d")   # default to today
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return True, raw
        except ValueError:
            return False, "Date must be in YYYY-MM-DD format."

    @staticmethod
    def _validate_type(raw: str) -> tuple[bool, str]:
        mapping = {"1": Transaction.TYPE_DEPOSIT,
                   "2": Transaction.TYPE_WITHDRAWAL,
                   "3": Transaction.TYPE_TRANSFER,
                   "deposit":    Transaction.TYPE_DEPOSIT,
                   "withdrawal": Transaction.TYPE_WITHDRAWAL,
                   "transfer":   Transaction.TYPE_TRANSFER}
        key = raw.strip().lower()
        if key in mapping:
            return True, mapping[key]
        return False, f"Invalid type. Enter 1/2/3 or deposit/withdrawal/transfer."

    # ── Core operations ─────────────────────────

    def add_transaction(self, amount: float, t_type: str,
                        description: str = "", date: str = "") -> "Transaction | None":
        try:
            t = Transaction(self._next_id(), amount, t_type, description, date)
            self.__transactions.append(t)
            return t
        except ValueError as exc:
            print(f"  [!] {exc}")
            return None

    def delete_transaction(self, tid: int) -> bool:
        t = self._find_by_id(tid)
        if t is None:
            print(f"  [!] Transaction #{tid} not found.")
            return False
        self.__transactions.remove(t)
        print(f"  [✓] Transaction #{tid} deleted.")
        return True

    # ── Search ──────────────────────────────────

    def search_by_date(self, date: str) -> list[Transaction]:
        return [t for t in self.__transactions if t.date == date.strip()]

    def search_by_date_range(self, start: str, end: str) -> list[Transaction]:
        try:
            s = datetime.strptime(start.strip(), "%Y-%m-%d")
            e = datetime.strptime(end.strip(),   "%Y-%m-%d")
        except ValueError:
            print("  [!] Invalid date format. Use YYYY-MM-DD.")
            return []
        return [t for t in self.__transactions
                if s <= datetime.strptime(t.date, "%Y-%m-%d") <= e]

    def search_by_type(self, t_type: str) -> list[Transaction]:
        ok, resolved = self._validate_type(t_type)
        if not ok:
            print(f"  [!] {resolved}")
            return []
        return [t for t in self.__transactions if t.type == resolved]

    def search_by_description(self, keyword: str) -> list[Transaction]:
        kw = keyword.strip().lower()
        return [t for t in self.__transactions if kw in t.description.lower()]

    # ── Totals / balance ────────────────────────

    @property
    def total_deposits(self) -> float:
        return round(sum(t.amount for t in self.__transactions
                         if t.type == Transaction.TYPE_DEPOSIT), 2)

    @property
    def total_withdrawals(self) -> float:
        return round(sum(t.amount for t in self.__transactions
                         if t.type == Transaction.TYPE_WITHDRAWAL), 2)

    @property
    def total_transfers(self) -> float:
        return round(sum(t.amount for t in self.__transactions
                         if t.type == Transaction.TYPE_TRANSFER), 2)

    @property
    def balance(self) -> float:
        return round(sum(t.signed_amount for t in self.__transactions), 2)

    @property
    def transaction_count(self) -> int:
        return len(self.__transactions)

    @property
    def account_name(self) -> str:
        return self.__account_name

    # ── Display ─────────────────────────────────

    def _print_transactions(self, transactions: list[Transaction], title: str = "Transactions"):
        if not transactions:
            print(f"  [~] No transactions found.")
            return

        print(f"\n  ┌─ {title} ({len(transactions)}) " + "─" * 35)
        for t in transactions:
            sign  = "+" if t.type == Transaction.TYPE_DEPOSIT else "-"
            color = "📈" if t.type == Transaction.TYPE_DEPOSIT else (
                    "📉" if t.type == Transaction.TYPE_WITHDRAWAL else "🔄")
            print(f"  │")
            print(f"  │  {color} #{t.transaction_id:<4}  {t.date}  │  "
                  f"{t.type:<12}  │  {sign}${t.amount:>12,.2f}")
            print(f"  │       └─ {t.description}")
        print("  └" + "─" * 60)

    def display_all(self):
        self._print_transactions(self.__transactions, f"Full History — {self.__account_name}")

    def display_summary(self):
        b = self.balance
        sign = "+" if b >= 0 else ""
        print(f"""
  ┌─ Account Summary ── {self.__account_name} {'─' * 20}
  │   Transactions  : {self.transaction_count}
  │   Total Deposits    : +${self.total_deposits:>12,.2f}
  │   Total Withdrawals :  -${self.total_withdrawals:>12,.2f}
  │   Total Transfers   :  -${self.total_transfers:>12,.2f}
  │   ─────────────────────────────────
  │   Current Balance   :  {sign}${abs(b):>12,.2f}  {'✅' if b >= 0 else '⚠️  Negative balance'}
  └{'─' * 50}""")


# ─────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────

def _clear():
    os.system("cls" if os.name == "nt" else "clear")

def _inp(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""

def _pause():
    input("\n  Press Enter to continue...")

def _divider():
    print("  " + "─" * 52)

def _banner(th: TransactionHistory):
    b = th.balance
    sign = "+" if b >= 0 else ""
    print(f"""
╔══════════════════════════════════════════════════════╗
║        💳  Transaction History Manager               ║
╚══════════════════════════════════════════════════════╝
  Account : {th.account_name:<20}  Transactions : {th.transaction_count}
  Balance : {sign}${abs(b):,.2f}  |  Deposits: ${th.total_deposits:,.2f}  |  Withdrawals: ${th.total_withdrawals:,.2f}""")


# ─────────────────────────────────────────────
#  MENU HANDLERS
# ─────────────────────────────────────────────

def menu_add(th: TransactionHistory):
    print("\n  ── Add Transaction ──────────────────────────")
    print("  Type: [1] Deposit  [2] Withdrawal  [3] Transfer")
    raw_type = _inp("  Choice      : ")
    ok, t_type = th._validate_type(raw_type)
    if not ok:
        print(f"  [!] {t_type}")
        return

    raw_amount = _inp("  Amount ($)  : ")
    ok, amount, msg = th._validate_amount(raw_amount)
    if not ok:
        print(f"  [!] {msg}")
        return

    raw_date = _inp("  Date (YYYY-MM-DD) [Enter = today]: ")
    ok, date = th._validate_date(raw_date)
    if not ok:
        print(f"  [!] {date}")
        return

    description = _inp("  Description : ")

    t = th.add_transaction(amount, t_type, description, date)
    if t:
        sign = "+" if t_type == Transaction.TYPE_DEPOSIT else "-"
        print(f"  [✓] {t_type} of {sign}${amount:,.2f} added as Transaction #{t.transaction_id}.")


def menu_delete(th: TransactionHistory):
    print("\n  ── Delete Transaction ───────────────────────")
    th.display_all()
    raw = _inp("  Enter Transaction ID to delete: ")
    if not raw.isdigit():
        print("  [!] Please enter a valid numeric ID.")
        return
    confirm = _inp(f"  Delete transaction #{raw}? (y/n): ").lower()
    if confirm == "y":
        th.delete_transaction(int(raw))
    else:
        print("  [~] Cancelled.")


def menu_search(th: TransactionHistory):
    print("""
  ── Search Transactions ──────────────────────
    [1] By exact date
    [2] By date range
    [3] By type
    [4] By description keyword""")
    choice = _inp("  Choice: ")

    if choice == "1":
        raw = _inp("  Date (YYYY-MM-DD): ")
        ok, date = th._validate_date(raw)
        if not ok:
            print(f"  [!] {date}")
            return
        results = th.search_by_date(date)
        th._print_transactions(results, f"Results for {date}")

    elif choice == "2":
        start = _inp("  Start date (YYYY-MM-DD): ")
        end   = _inp("  End   date (YYYY-MM-DD): ")
        results = th.search_by_date_range(start, end)
        th._print_transactions(results, f"Results {start} → {end}")

    elif choice == "3":
        print("  [1] Deposit  [2] Withdrawal  [3] Transfer")
        raw = _inp("  Choice: ")
        ok, t_type = th._validate_type(raw)
        if not ok:
            print(f"  [!] {t_type}")
            return
        results = th.search_by_type(t_type)
        th._print_transactions(results, f"{t_type} Transactions")

    elif choice == "4":
        kw = _inp("  Keyword: ")
        results = th.search_by_description(kw)
        th._print_transactions(results, f"Results for '{kw}'")

    else:
        print("  [!] Invalid choice.")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

MENU = """
  ── Main Menu ──────────────────────────────────
    [1] Add transaction
    [2] Delete transaction
    [3] Search transactions
    [4] Display full history
    [5] Display account summary
    [0] Exit
  ───────────────────────────────────────────────"""

def _seed(th: TransactionHistory):
    """Pre-load demo transactions so the system isn't empty on first run."""
    data = [
        (5000.00, Transaction.TYPE_DEPOSIT,    "Initial deposit",        "2025-01-01"),
        (1200.00, Transaction.TYPE_WITHDRAWAL, "Rent payment",           "2025-01-05"),
        ( 300.00, Transaction.TYPE_WITHDRAWAL, "Grocery shopping",       "2025-01-10"),
        (2500.00, Transaction.TYPE_DEPOSIT,    "Freelance payment",      "2025-01-15"),
        ( 800.00, Transaction.TYPE_TRANSFER,   "Transfer to savings",    "2025-01-20"),
        ( 150.00, Transaction.TYPE_WITHDRAWAL, "Electricity bill",       "2025-02-01"),
        (3000.00, Transaction.TYPE_DEPOSIT,    "Monthly salary",         "2025-02-05"),
        ( 450.00, Transaction.TYPE_WITHDRAWAL, "Car insurance",          "2025-02-12"),
        (1000.00, Transaction.TYPE_TRANSFER,   "Transfer to investment", "2025-02-18"),
        ( 200.00, Transaction.TYPE_WITHDRAWAL, "Restaurant & dining",    "2025-02-25"),
    ]
    for amount, t_type, desc, date in data:
        th.add_transaction(amount, t_type, desc, date)


def main():
    name = _inp("  Enter account name [Press Enter for 'My Account']: ")
    th = TransactionHistory(name or "My Account")
    _seed(th)

    while True:
        _clear()
        _banner(th)
        print(MENU)
        _divider()
        choice = _inp("  Choice: ")
        print()

        if   choice == "1": menu_add(th)
        elif choice == "2": menu_delete(th)
        elif choice == "3": menu_search(th)
        elif choice == "4": th.display_all()
        elif choice == "5": th.display_summary()
        elif choice == "0":
            print("  Goodbye! 👋\n")
            break
        else:
            print("  [!] Invalid option. Please choose from the menu.")

        _pause()


if __name__ == "__main__":
    main()