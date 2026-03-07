"""
atm_simulation.py
A command-line ATM simulator using Python OOP principles.
"""

from __future__ import annotations
import os
import hashlib
import datetime
from enum import Enum


# ──────────────────────────────────────────────
#  Enums & Constants
# ──────────────────────────────────────────────

class TransactionType(Enum):
    DEPOSIT    = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER   = "Transfer"
    INQUIRY    = "Balance Inquiry"


MAX_LOGIN_ATTEMPTS  = 3
WITHDRAWAL_LIMIT    = 2_000.00   # per transaction
DAILY_WITHDRAW_CAP  = 5_000.00
MIN_DEPOSIT         = 1.00
CURRENCY            = "$"


# ──────────────────────────────────────────────
#  Transaction
# ──────────────────────────────────────────────

class Transaction:
    """Immutable record of a single ATM event."""

    _counter: int = 1

    def __init__(
        self,
        tx_type: TransactionType,
        amount: float,
        balance_after: float,
        note: str = "",
    ) -> None:
        self.__tx_id        = Transaction._counter
        Transaction._counter += 1
        self.__type         = tx_type
        self.__amount       = round(amount, 2)
        self.__balance_after = round(balance_after, 2)
        self.__note         = note
        self.__timestamp    = datetime.datetime.now()

    # ── read-only properties ──────────────────

    @property
    def tx_id(self) -> int:         return self.__tx_id
    @property
    def tx_type(self) -> TransactionType: return self.__type
    @property
    def amount(self) -> float:      return self.__amount
    @property
    def balance_after(self) -> float: return self.__balance_after
    @property
    def note(self) -> str:          return self.__note
    @property
    def timestamp(self) -> datetime.datetime: return self.__timestamp

    def __str__(self) -> str:
        ts     = self.__timestamp.strftime("%Y-%m-%d  %H:%M:%S")
        amount = f"{CURRENCY}{self.__amount:>10.2f}" if self.__amount else "          —"
        note   = f"  ({self.__note})" if self.__note else ""
        return (
            f"  #{self.__tx_id:<4}  {ts}   "
            f"{self.__type.value:<18}  {amount}   "
            f"Bal: {CURRENCY}{self.__balance_after:.2f}{note}"
        )


# ──────────────────────────────────────────────
#  BankAccount
# ──────────────────────────────────────────────

class BankAccount:
    """Encapsulates account credentials, balance, and transaction history."""

    def __init__(
        self,
        account_number: str,
        account_holder: str,
        pin: str,
        initial_balance: float = 0.0,
    ) -> None:
        self.__account_number  = account_number
        self.__account_holder  = account_holder.strip().title()
        self.__pin_hash        = self._hash(pin)         # never store raw PIN
        self.__balance         = round(float(initial_balance), 2)
        self.__transactions: list[Transaction] = []
        self.__daily_withdrawn: float = 0.0
        self.__last_tx_date: datetime.date | None = None
        self.__locked: bool = False

    # ── private helper ────────────────────────

    @staticmethod
    def _hash(pin: str) -> str:
        return hashlib.sha256(pin.encode()).hexdigest()

    def _reset_daily_limit_if_needed(self) -> None:
        today = datetime.date.today()
        if self.__last_tx_date != today:
            self.__daily_withdrawn = 0.0
            self.__last_tx_date    = today

    def _record(self, tx: Transaction) -> None:
        self.__transactions.append(tx)

    # ── read-only properties ──────────────────

    @property
    def account_number(self) -> str:
        return self.__account_number

    @property
    def account_holder(self) -> str:
        return self.__account_holder

    @property
    def balance(self) -> float:
        return self.__balance

    @property
    def is_locked(self) -> bool:
        return self.__locked

    # ── authentication ────────────────────────

    def verify_pin(self, pin: str) -> bool:
        return self.__pin_hash == self._hash(pin)

    def lock(self) -> None:
        self.__locked = True

    def change_pin(self, old_pin: str, new_pin: str) -> str:
        if not self.verify_pin(old_pin):
            return "  ✗  Incorrect current PIN."
        if len(new_pin) < 4:
            return "  ✗  New PIN must be at least 4 digits."
        if not new_pin.isdigit():
            return "  ✗  PIN must contain digits only."
        self.__pin_hash = self._hash(new_pin)
        return "  ✓  PIN changed successfully."

    # ── transactions ──────────────────────────

    def deposit(self, amount: float) -> str:
        if self.__locked:
            return "  ✗  Account is locked. Please contact the bank."
        amount = round(float(amount), 2)
        if amount < MIN_DEPOSIT:
            return f"  ✗  Minimum deposit is {CURRENCY}{MIN_DEPOSIT:.2f}."
        self.__balance += amount
        tx = Transaction(TransactionType.DEPOSIT, amount, self.__balance)
        self._record(tx)
        return f"  ✓  Deposited {CURRENCY}{amount:.2f}.  New balance: {CURRENCY}{self.__balance:.2f}"

    def withdraw(self, amount: float) -> str:
        if self.__locked:
            return "  ✗  Account is locked. Please contact the bank."
        amount = round(float(amount), 2)
        if amount <= 0:
            return "  ✗  Withdrawal amount must be greater than zero."
        if amount > WITHDRAWAL_LIMIT:
            return f"  ✗  Single-transaction limit is {CURRENCY}{WITHDRAWAL_LIMIT:,.2f}."
        self._reset_daily_limit_if_needed()
        if self.__daily_withdrawn + amount > DAILY_WITHDRAW_CAP:
            remaining = DAILY_WITHDRAW_CAP - self.__daily_withdrawn
            return (
                f"  ✗  Daily withdrawal cap reached.  "
                f"Remaining today: {CURRENCY}{remaining:.2f}."
            )
        if amount > self.__balance:
            return (
                f"  ✗  Insufficient funds.  "
                f"Available: {CURRENCY}{self.__balance:.2f}."
            )
        self.__balance         -= amount
        self.__daily_withdrawn += amount
        tx = Transaction(TransactionType.WITHDRAWAL, amount, self.__balance)
        self._record(tx)
        return f"  ✓  Dispensed {CURRENCY}{amount:.2f}.  New balance: {CURRENCY}{self.__balance:.2f}"

    def record_inquiry(self) -> None:
        tx = Transaction(TransactionType.INQUIRY, 0.0, self.__balance)
        self._record(tx)

    def record_transfer_out(self, amount: float, to_account: str) -> str:
        """Internal debit leg of a transfer; validation done by ATM."""
        self.__balance -= amount
        self.__daily_withdrawn += amount
        tx = Transaction(
            TransactionType.TRANSFER, amount, self.__balance,
            note=f"To {to_account}",
        )
        self._record(tx)
        return f"  ✓  Transferred {CURRENCY}{amount:.2f} to account {to_account}."

    def record_transfer_in(self, amount: float, from_account: str) -> None:
        self.__balance += amount
        tx = Transaction(
            TransactionType.TRANSFER, amount, self.__balance,
            note=f"From {from_account}",
        )
        self._record(tx)

    def get_transactions(self, n: int | None = None) -> list[Transaction]:
        txs = list(self.__transactions)
        return txs[-n:] if n else txs

    def daily_withdrawn(self) -> float:
        self._reset_daily_limit_if_needed()
        return self.__daily_withdrawn


# ──────────────────────────────────────────────
#  Bank  (account registry)
# ──────────────────────────────────────────────

class Bank:
    """Holds all registered accounts; simulates the bank's back-end."""

    def __init__(self, name: str = "PyBank") -> None:
        self.__name     = name
        self.__accounts: dict[str, BankAccount] = {}

    @property
    def name(self) -> str:
        return self.__name

    def register(self, account: BankAccount) -> None:
        self.__accounts[account.account_number] = account

    def find(self, account_number: str) -> BankAccount | None:
        return self.__accounts.get(account_number)

    def count(self) -> int:
        return len(self.__accounts)


# ──────────────────────────────────────────────
#  ATM
# ──────────────────────────────────────────────

class ATM:
    """
    Manages the ATM session lifecycle:
    authentication → operations → logout.
    """

    def __init__(self, bank: Bank, atm_id: str = "ATM-001") -> None:
        self.__bank            = bank
        self.__atm_id          = atm_id
        self.__session_account: BankAccount | None = None
        self.__login_attempts  = 0

    # ── session helpers ───────────────────────

    @property
    def is_authenticated(self) -> bool:
        return self.__session_account is not None

    @property
    def current_account(self) -> BankAccount | None:
        return self.__session_account

    def logout(self) -> None:
        if self.__session_account:
            print(f"\n  Session ended for {self.__session_account.account_holder}.")
        self.__session_account = None
        self.__login_attempts  = 0

    # ── authentication ────────────────────────

    def authenticate(self, account_number: str, pin: str) -> str:
        account = self.__bank.find(account_number)
        if account is None:
            return "  ✗  Account not found."
        if account.is_locked:
            return "  ✗  This account is locked. Please contact the bank."

        if account.verify_pin(pin):
            self.__session_account = account
            self.__login_attempts  = 0
            return f"  ✓  Welcome, {account.account_holder}!"
        else:
            self.__login_attempts += 1
            remaining = MAX_LOGIN_ATTEMPTS - self.__login_attempts
            if remaining <= 0:
                account.lock()
                return (
                    "  ✗  Too many failed attempts. "
                    "Your account has been locked."
                )
            return f"  ✗  Incorrect PIN. {remaining} attempt(s) remaining."

    # ── ATM operations (require authentication) ──

    def _require_auth(self) -> bool:
        if not self.is_authenticated:
            print("  ✗  No active session. Please insert your card first.")
            return False
        return True

    def check_balance(self) -> str:
        if not self._require_auth(): return ""
        self.__session_account.record_inquiry()
        acc = self.__session_account
        remaining = DAILY_WITHDRAW_CAP - acc.daily_withdrawn()
        return (
            f"\n  Account   : {acc.account_number}\n"
            f"  Holder    : {acc.account_holder}\n"
            f"  Balance   : {CURRENCY}{acc.balance:,.2f}\n"
            f"  Daily W/D remaining: {CURRENCY}{remaining:,.2f}"
        )

    def deposit(self, amount: float) -> str:
        if not self._require_auth(): return ""
        return self.__session_account.deposit(amount)

    def withdraw(self, amount: float) -> str:
        if not self._require_auth(): return ""
        return self.__session_account.withdraw(amount)

    def transfer(self, amount: float, target_account_number: str) -> str:
        if not self._require_auth(): return ""
        src = self.__session_account
        dst = self.__bank.find(target_account_number)

        if dst is None:
            return f"  ✗  Destination account '{target_account_number}' not found."
        if dst.account_number == src.account_number:
            return "  ✗  Cannot transfer to the same account."

        amount = round(float(amount), 2)
        if amount <= 0:
            return "  ✗  Transfer amount must be greater than zero."
        if amount > src.balance:
            return f"  ✗  Insufficient funds. Available: {CURRENCY}{src.balance:,.2f}."
        if amount > WITHDRAWAL_LIMIT:
            return f"  ✗  Single-transaction limit is {CURRENCY}{WITHDRAWAL_LIMIT:,.2f}."
        src._reset_daily_limit_if_needed()
        if src.daily_withdrawn() + amount > DAILY_WITHDRAW_CAP:
            remaining = DAILY_WITHDRAW_CAP - src.daily_withdrawn()
            return f"  ✗  Daily limit reached. Remaining: {CURRENCY}{remaining:.2f}."

        msg = src.record_transfer_out(amount, target_account_number)
        dst.record_transfer_in(amount, src.account_number)
        return msg

    def change_pin(self, old_pin: str, new_pin: str) -> str:
        if not self._require_auth(): return ""
        return self.__session_account.change_pin(old_pin, new_pin)

    def transaction_history(self, last_n: int | None = 10) -> str:
        if not self._require_auth(): return ""
        txs = self.__session_account.get_transactions(last_n)
        if not txs:
            return "  No transactions on record."
        lines = [
            f"\n  {'#':<5}  {'Date':>10}    {'Time':>8}   "
            f"{'Type':<18}  {'Amount':>12}   Balance",
            "  " + "─" * 68,
        ]
        for tx in txs:
            lines.append(str(tx))
        return "\n".join(lines)


# ──────────────────────────────────────────────
#  CLI helpers
# ──────────────────────────────────────────────

DIVIDER = "─" * 62


def cls() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str, sub: str = "") -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    if sub:
        print(f"  {sub}")
    print(DIVIDER)


def prompt_amount(msg: str) -> float | None:
    raw = input(msg).strip()
    try:
        v = float(raw)
        if v <= 0:
            print("  ✗  Amount must be greater than zero.")
            return None
        return v
    except ValueError:
        print("  ✗  Invalid amount. Please enter a number.")
        return None


def get_pin(prompt_msg: str = "  PIN: ") -> str:
    """Read PIN input. Uses plain input() for full terminal compatibility."""
    return input(prompt_msg)


# ──────────────────────────────────────────────
#  ATM screen actions
# ──────────────────────────────────────────────

def screen_login(atm: ATM) -> bool:
    print_header("INSERT CARD", "Enter your credentials to continue.")
    acc_no = input("  Account Number : ").strip()
    pin    = get_pin("  PIN           : ")
    result = atm.authenticate(acc_no, pin)
    print(f"\n{result}")
    return atm.is_authenticated


def screen_balance(atm: ATM) -> None:
    print_header("BALANCE INQUIRY")
    result = atm.check_balance()
    # check_balance() returns a string starting with \n — strip it so
    # print() does not add a second blank line before the content
    print(result.lstrip("\n"))


def screen_deposit(atm: ATM) -> None:
    print_header("DEPOSIT CASH")
    amount = prompt_amount("  Amount to deposit : $")
    if amount is not None:
        print(f"\n{atm.deposit(amount)}")


def screen_withdraw(atm: ATM) -> None:
    print_header("WITHDRAW CASH")
    print(f"  Per-transaction limit : {CURRENCY}{WITHDRAWAL_LIMIT:,.2f}")
    print(f"  Daily limit           : {CURRENCY}{DAILY_WITHDRAW_CAP:,.2f}\n")
    amount = prompt_amount("  Amount to withdraw : $")
    if amount is not None:
        print(f"\n{atm.withdraw(amount)}")


def screen_transfer(atm: ATM) -> None:
    print_header("FUNDS TRANSFER")
    target = input("  Destination account : ").strip()
    amount = prompt_amount("  Amount to transfer  : $")
    if amount is not None:
        print(f"\n{atm.transfer(amount, target)}")


def screen_history(atm: ATM) -> None:
    print_header("TRANSACTION HISTORY", "Last 10 transactions")
    print(atm.transaction_history(10))


def screen_change_pin(atm: ATM) -> None:
    print_header("CHANGE PIN")
    old = get_pin("  Current PIN : ")
    new = get_pin("  New PIN     : ")
    confirm = get_pin("  Confirm PIN : ")
    if new != confirm:
        print("\n  ✗  New PINs do not match.")
        return
    print(f"\n{atm.change_pin(old, new)}")


# ──────────────────────────────────────────────
#  Menus
# ──────────────────────────────────────────────

LOGIN_MENU = """
  ╔══════════════════════════════╗
  ║        PyBank  ATM           ║
  ╠══════════════════════════════╣
  ║  1. Insert Card (Login)      ║
  ║  0. Exit                     ║
  ╚══════════════════════════════╝"""

SESSION_MENU = """
  ╔══════════════════════════════╗
  ║       SELECT OPERATION       ║
  ╠══════════════════════════════╣
  ║  1. Check Balance            ║
  ║  2. Deposit                  ║
  ║  3. Withdraw                 ║
  ║  4. Transfer Funds           ║
  ║  5. Transaction History      ║
  ║  6. Change PIN               ║
  ║  0. Eject Card (Logout)      ║
  ╚══════════════════════════════╝"""

SESSION_ACTIONS = {
    "1": screen_balance,
    "2": screen_deposit,
    "3": screen_withdraw,
    "4": screen_transfer,
    "5": screen_history,
    "6": screen_change_pin,
}


def session_loop(atm: ATM) -> None:
    """Inner loop once a user is authenticated."""
    acc = atm.current_account
    first = True
    while atm.is_authenticated:
        # Clear terminal before re-drawing the menu so the output of
        # the previous operation stays visible until Enter is pressed.
        if not first:
            cls()
        first = False
        print(SESSION_MENU)
        print(f"  Logged in as: {acc.account_holder}  |  Bal: {CURRENCY}{acc.balance:,.2f}\n")
        choice = input("  Select operation: ").strip()
        if choice == "0":
            atm.logout()
            break
        elif choice in SESSION_ACTIONS:
            SESSION_ACTIONS[choice](atm)
        else:
            print("\n  ✗  Invalid option.")
        input("\n  Press Enter to return to menu...")


def main_loop(atm: ATM, bank: Bank) -> None:
    print(f"\n  Welcome to {bank.name} ATM")
    while True:
        print(LOGIN_MENU)
        choice = input("  Select option: ").strip()
        if choice == "0":
            print("\n  Thank you for using PyBank ATM. Goodbye!\n")
            break
        elif choice == "1":
            if screen_login(atm):
                input("\n  Press Enter to continue...")
                session_loop(atm)
            else:
                input("\n  Press Enter to try again...")
        else:
            print("\n  ✗  Invalid option.")


# ──────────────────────────────────────────────
#  Seed data & entry point
# ──────────────────────────────────────────────

def seed_bank(bank: Bank) -> None:
    accounts = [
        BankAccount("1001234567", "Alice Johnson",  "1234", 5_800.00),
        BankAccount("1009876543", "Bob Martinez",   "4321", 12_450.75),
        BankAccount("1005551234", "Clara Nguyen",   "0000", 3_200.50),
        BankAccount("1007778888", "David Okonkwo",  "9999", 800.00),
    ]
    for acc in accounts:
        bank.register(acc)


def main() -> None:
    bank = Bank("PyBank")
    seed_bank(bank)
    atm  = ATM(bank, atm_id="ATM-001")

    print("\n" + "═" * 62)
    print("  PyBank ATM Simulation")
    print("  Demo accounts:")
    print("  ┌─────────────────┬──────────────┬──────┬─────────────┐")
    print("  │ Account No.     │ Holder       │ PIN  │ Balance     │")
    print("  ├─────────────────┼──────────────┼──────┼─────────────┤")
    print("  │ 1001234567      │ Alice Johnson│ 1234 │  $5,800.00  │")
    print("  │ 1009876543      │ Bob Martinez │ 4321 │ $12,450.75  │")
    print("  │ 1005551234      │ Clara Nguyen │ 0000 │  $3,200.50  │")
    print("  │ 1007778888      │ David Okonkwo│ 9999 │    $800.00  │")
    print("  └─────────────────┴──────────────┴──────┴─────────────┘")
    print("═" * 62)

    main_loop(atm, bank)


if __name__ == "__main__":
    main()