"""
Bank Account Management System
A complete demonstration of Object-Oriented Programming principles in Python

This program demonstrates:
1. Encapsulation - Private attributes with getters/setters
2. Abstraction - Abstract base class Account
3. Inheritance - SavingsAccount and CheckingAccount inherit from BankAccount
4. Polymorphism - Method overriding
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
import sys


# ============================================================================
# ABSTRACTION: Abstract Base Class
# ============================================================================
# Abstraction hides complex implementation details and shows only essential
# features. An abstract class cannot be instantiated directly and serves as
# a blueprint for other classes.

class Account(ABC):
    """
    Abstract base class representing a generic account.
    This class cannot be instantiated directly - it must be inherited.
    """

    def __init__(self, account_number: str, account_holder: str, initial_balance: float = 0.0):
        """
        Initialize an Account object.

        Args:
            account_number: Unique account identifier
            account_holder: Name of the account holder
            initial_balance: Initial balance (default 0.0)
        """
        # ENCAPSULATION: Private attributes (using _ prefix)
        # These attributes should not be accessed directly from outside
        self._account_number = account_number
        self._account_holder = account_holder
        self._balance = initial_balance
        self._transaction_history: List[str] = []

        # Record initial deposit if any
        if initial_balance > 0:
            self._add_transaction(f"Initial deposit: ${initial_balance:.2f}")

    # ENCAPSULATION: Getter methods (properties)
    # These provide controlled access to private attributes

    @property
    def account_number(self) -> str:
        """Get the account number."""
        return self._account_number

    @property
    def account_holder(self) -> str:
        """Get the account holder's name."""
        return self._account_holder

    @property
    def balance(self) -> float:
        """Get the current balance."""
        return self._balance

    @property
    def transaction_history(self) -> List[str]:
        """Get a copy of transaction history."""
        return self._transaction_history.copy()

    # ENCAPSULATION: Setter methods with validation

    @account_holder.setter
    def account_holder(self, value: str):
        """Set the account holder's name with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("Account holder name must be a non-empty string")
        self._account_holder = value

    # Protected helper method for transaction logging
    def _add_transaction(self, description: str):
        """Add a transaction to the history with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._transaction_history.append(f"[{timestamp}] {description}")

    # Common methods for all accounts
    def deposit(self, amount: float) -> bool:
        """
        Deposit money into the account.

        Args:
            amount: Amount to deposit

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If amount is invalid
        """
        if not isinstance(amount, (int, float)):
            raise ValueError("Deposit amount must be a number")
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        self._balance += amount
        self._add_transaction(f"Deposit: +${amount:.2f} | Balance: ${self._balance:.2f}")
        return True

    def withdraw(self, amount: float) -> bool:
        """
        Withdraw money from the account.

        Args:
            amount: Amount to withdraw

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If amount is invalid or insufficient funds
        """
        if not isinstance(amount, (int, float)):
            raise ValueError("Withdrawal amount must be a number")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise ValueError(f"Insufficient funds. Current balance: ${self._balance:.2f}")

        self._balance -= amount
        self._add_transaction(f"Withdrawal: -${amount:.2f} | Balance: ${self._balance:.2f}")
        return True

    def display_balance(self):
        """Display the current account balance."""
        print(f"\nCurrent Balance: ${self._balance:.2f}")

    def display_transaction_history(self):
        """Display all transactions for this account."""
        print("\n" + "=" * 70)
        print(f"{'TRANSACTION HISTORY':^70}")
        print("=" * 70)
        print(f"Account: {self._account_number} - {self._account_holder}")
        print("-" * 70)

        if not self._transaction_history:
            print("No transactions yet.")
        else:
            for transaction in self._transaction_history:
                print(transaction)

        print("=" * 70)

    # ABSTRACTION: Abstract method
    # This method MUST be implemented by any class that inherits from Account
    @abstractmethod
    def display_account_info(self):
        """Display account information. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_account_type(self) -> str:
        """Return the type of account. Must be implemented by subclasses."""
        pass


# ============================================================================
# INHERITANCE: BankAccount class inherits from Account
# ============================================================================

class BankAccount(Account):
    """
    Base BankAccount class that inherits from Account.
    Represents a standard bank account.
    """

    def __init__(self, account_number: str, account_holder: str, initial_balance: float = 0.0):
        """
        Initialize a BankAccount object.

        Args:
            account_number: Unique account number
            account_holder: Name of account holder
            initial_balance: Initial balance (default 0.0)
        """
        # Call parent class constructor
        super().__init__(account_number, account_holder, initial_balance)

    # POLYMORPHISM: Implement the abstract method
    def display_account_info(self):
        """Display complete bank account information."""
        print("\n" + "=" * 70)
        print(f"{'BANK ACCOUNT INFORMATION':^70}")
        print("=" * 70)
        print(f"Account Number : {self._account_number}")
        print(f"Account Holder : {self._account_holder}")
        print(f"Account Type   : {self.get_account_type()}")
        print(f"Current Balance: ${self._balance:.2f}")
        print(f"Transactions   : {len(self._transaction_history)}")
        print("=" * 70)

    def get_account_type(self) -> str:
        """Return the account type."""
        return "Standard Bank Account"


# ============================================================================
# INHERITANCE & POLYMORPHISM: SavingsAccount class
# ============================================================================

class SavingsAccount(BankAccount):
    """
    SavingsAccount class that inherits from BankAccount.
    Includes interest rate and minimum balance requirements.
    """

    def __init__(self, account_number: str, account_holder: str,
                 initial_balance: float = 0.0, interest_rate: float = 2.5,
                 minimum_balance: float = 100.0):
        """
        Initialize a SavingsAccount object.

        Args:
            account_number: Unique account number
            account_holder: Name of account holder
            initial_balance: Initial balance
            interest_rate: Annual interest rate percentage
            minimum_balance: Minimum balance required
        """
        super().__init__(account_number, account_holder, initial_balance)

        # ENCAPSULATION: Additional private attributes for SavingsAccount
        self._interest_rate = interest_rate
        self._minimum_balance = minimum_balance

    @property
    def interest_rate(self) -> float:
        """Get the interest rate."""
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, value: float):
        """Set the interest rate with validation."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Interest rate must be a non-negative number")
        self._interest_rate = value

    @property
    def minimum_balance(self) -> float:
        """Get the minimum balance requirement."""
        return self._minimum_balance

    # POLYMORPHISM: Override withdraw method with additional logic
    def withdraw(self, amount: float) -> bool:
        """
        Withdraw money from savings account with minimum balance check.

        Args:
            amount: Amount to withdraw

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If withdrawal would violate minimum balance
        """
        if not isinstance(amount, (int, float)):
            raise ValueError("Withdrawal amount must be a number")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise ValueError(f"Insufficient funds. Current balance: ${self._balance:.2f}")

        # Check minimum balance requirement
        if (self._balance - amount) < self._minimum_balance:
            raise ValueError(
                f"Withdrawal denied. Minimum balance of ${self._minimum_balance:.2f} required. "
                f"You can withdraw up to ${self._balance - self._minimum_balance:.2f}"
            )

        self._balance -= amount
        self._add_transaction(f"Withdrawal: -${amount:.2f} | Balance: ${self._balance:.2f}")
        return True

    def apply_interest(self):
        """Apply monthly interest to the account."""
        monthly_rate = self._interest_rate / 12 / 100
        interest = self._balance * monthly_rate
        self._balance += interest
        self._add_transaction(
            f"Interest applied ({self._interest_rate}% APR): +${interest:.2f} | Balance: ${self._balance:.2f}"
        )
        return interest

    # POLYMORPHISM: Override display_account_info with additional information
    def display_account_info(self):
        """Display complete savings account information."""
        print("\n" + "=" * 70)
        print(f"{'SAVINGS ACCOUNT INFORMATION':^70}")
        print("=" * 70)
        print(f"Account Number    : {self._account_number}")
        print(f"Account Holder    : {self._account_holder}")
        print(f"Account Type      : {self.get_account_type()}")
        print(f"Current Balance   : ${self._balance:.2f}")
        print(f"Interest Rate     : {self._interest_rate}% APR")
        print(f"Minimum Balance   : ${self._minimum_balance:.2f}")
        print(f"Transactions      : {len(self._transaction_history)}")
        print("=" * 70)

    def get_account_type(self) -> str:
        """Return the account type."""
        return "Savings Account"


# ============================================================================
# INHERITANCE & POLYMORPHISM: CheckingAccount class
# ============================================================================

class CheckingAccount(BankAccount):
    """
    CheckingAccount class that inherits from BankAccount.
    Includes overdraft protection and transaction limits.
    """

    def __init__(self, account_number: str, account_holder: str,
                 initial_balance: float = 0.0, overdraft_limit: float = 500.0,
                 monthly_fee: float = 10.0):
        """
        Initialize a CheckingAccount object.

        Args:
            account_number: Unique account number
            account_holder: Name of account holder
            initial_balance: Initial balance
            overdraft_limit: Maximum overdraft allowed
            monthly_fee: Monthly maintenance fee
        """
        super().__init__(account_number, account_holder, initial_balance)

        # ENCAPSULATION: Additional private attributes for CheckingAccount
        self._overdraft_limit = overdraft_limit
        self._monthly_fee = monthly_fee
        self._overdraft_used = 0.0

    @property
    def overdraft_limit(self) -> float:
        """Get the overdraft limit."""
        return self._overdraft_limit

    @property
    def monthly_fee(self) -> float:
        """Get the monthly fee."""
        return self._monthly_fee

    @property
    def overdraft_used(self) -> float:
        """Get the current overdraft amount used."""
        return self._overdraft_used

    @property
    def available_balance(self) -> float:
        """Get available balance including overdraft."""
        return self._balance + (self._overdraft_limit - self._overdraft_used)

    # POLYMORPHISM: Override withdraw method with overdraft logic
    def withdraw(self, amount: float) -> bool:
        """
        Withdraw money from checking account with overdraft protection.

        Args:
            amount: Amount to withdraw

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If amount exceeds available balance with overdraft
        """
        if not isinstance(amount, (int, float)):
            raise ValueError("Withdrawal amount must be a number")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        # Check if withdrawal exceeds available balance (including overdraft)
        if amount > self.available_balance:
            raise ValueError(
                f"Insufficient funds. Available balance (with overdraft): ${self.available_balance:.2f}"
            )

        # Process withdrawal
        if amount <= self._balance:
            # Normal withdrawal
            self._balance -= amount
            self._add_transaction(f"Withdrawal: -${amount:.2f} | Balance: ${self._balance:.2f}")
        else:
            # Overdraft required
            overdraft_needed = amount - self._balance
            self._balance = 0.0
            self._overdraft_used += overdraft_needed
            self._add_transaction(
                f"Withdrawal: -${amount:.2f} (${overdraft_needed:.2f} overdraft) | "
                f"Balance: ${self._balance:.2f} | Overdraft: ${self._overdraft_used:.2f}"
            )

        return True

    # POLYMORPHISM: Override deposit to pay back overdraft first
    def deposit(self, amount: float) -> bool:
        """
        Deposit money into checking account, paying overdraft first.

        Args:
            amount: Amount to deposit

        Returns:
            True if successful, False otherwise
        """
        if not isinstance(amount, (int, float)):
            raise ValueError("Deposit amount must be a number")
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        # Pay back overdraft first
        if self._overdraft_used > 0:
            if amount >= self._overdraft_used:
                # Deposit covers all overdraft
                amount -= self._overdraft_used
                self._overdraft_used = 0.0
                self._balance += amount
                self._add_transaction(
                    f"Deposit: +${amount:.2f} (overdraft cleared) | Balance: ${self._balance:.2f}"
                )
            else:
                # Deposit only partially covers overdraft
                self._overdraft_used -= amount
                self._add_transaction(
                    f"Deposit: +${amount:.2f} (to overdraft) | "
                    f"Balance: ${self._balance:.2f} | Overdraft: ${self._overdraft_used:.2f}"
                )
        else:
            # Normal deposit
            self._balance += amount
            self._add_transaction(f"Deposit: +${amount:.2f} | Balance: ${self._balance:.2f}")

        return True

    def charge_monthly_fee(self):
        """Charge the monthly maintenance fee."""
        self._balance -= self._monthly_fee
        self._add_transaction(
            f"Monthly fee charged: -${self._monthly_fee:.2f} | Balance: ${self._balance:.2f}"
        )

    # POLYMORPHISM: Override display_account_info with additional information
    def display_account_info(self):
        """Display complete checking account information."""
        print("\n" + "=" * 70)
        print(f"{'CHECKING ACCOUNT INFORMATION':^70}")
        print("=" * 70)
        print(f"Account Number       : {self._account_number}")
        print(f"Account Holder       : {self._account_holder}")
        print(f"Account Type         : {self.get_account_type()}")
        print(f"Current Balance      : ${self._balance:.2f}")
        print(f"Overdraft Limit      : ${self._overdraft_limit:.2f}")
        print(f"Overdraft Used       : ${self._overdraft_used:.2f}")
        print(f"Available Balance    : ${self.available_balance:.2f}")
        print(f"Monthly Fee          : ${self._monthly_fee:.2f}")
        print(f"Transactions         : {len(self._transaction_history)}")
        print("=" * 70)

    def get_account_type(self) -> str:
        """Return the account type."""
        return "Checking Account"


# ============================================================================
# Bank Management System - Main Controller Class
# ============================================================================

class BankManagementSystem:
    """Main system to manage bank accounts with interactive menu."""

    def __init__(self):
        """Initialize the bank management system."""
        self.accounts: Dict[str, Account] = {}
        self.next_account_number = 1001

    def generate_account_number(self) -> str:
        """Generate a unique account number."""
        account_num = f"ACC{self.next_account_number:06d}"
        self.next_account_number += 1
        return account_num

    def create_savings_account(self):
        """Create a new savings account."""
        print("\n" + "=" * 70)
        print("CREATE NEW SAVINGS ACCOUNT")
        print("=" * 70)

        try:
            holder = input("Enter account holder name: ").strip()
            if not holder:
                print("[ERROR] Account holder name cannot be empty!")
                return

            initial = float(input("Enter initial deposit amount: $"))
            if initial < 0:
                print("[ERROR] Initial deposit cannot be negative!")
                return

            interest = float(input("Enter annual interest rate (default 2.5%): ") or "2.5")
            min_balance = float(input("Enter minimum balance requirement (default $100): ") or "100")

            account_num = self.generate_account_number()
            account = SavingsAccount(account_num, holder, initial, interest, min_balance)
            self.accounts[account_num] = account

            print(f"\n[SUCCESS] Savings account created successfully!")
            print(f"          Account Number: {account_num}")
            print(f"          Initial Balance: ${initial:.2f}")

        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")

    def create_checking_account(self):
        """Create a new checking account."""
        print("\n" + "=" * 70)
        print("CREATE NEW CHECKING ACCOUNT")
        print("=" * 70)

        try:
            holder = input("Enter account holder name: ").strip()
            if not holder:
                print("[ERROR] Account holder name cannot be empty!")
                return

            initial = float(input("Enter initial deposit amount: $"))
            if initial < 0:
                print("[ERROR] Initial deposit cannot be negative!")
                return

            overdraft = float(input("Enter overdraft limit (default $500): ") or "500")
            fee = float(input("Enter monthly fee (default $10): ") or "10")

            account_num = self.generate_account_number()
            account = CheckingAccount(account_num, holder, initial, overdraft, fee)
            self.accounts[account_num] = account

            print(f"\n[SUCCESS] Checking account created successfully!")
            print(f"          Account Number: {account_num}")
            print(f"          Initial Balance: ${initial:.2f}")

        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")

    def deposit_to_account(self):
        """Deposit money to an account."""
        if not self.accounts:
            print("\n[INFO] No accounts in the system yet!")
            return

        try:
            account_num = input("\nEnter account number: ").strip()
            account = self.accounts.get(account_num)

            if not account:
                print(f"[ERROR] Account {account_num} not found!")
                return

            amount = float(input("Enter deposit amount: $"))
            account.deposit(amount)
            print(f"[SUCCESS] Deposited ${amount:.2f} successfully!")
            print(f"          New balance: ${account.balance:.2f}")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def withdraw_from_account(self):
        """Withdraw money from an account."""
        if not self.accounts:
            print("\n[INFO] No accounts in the system yet!")
            return

        try:
            account_num = input("\nEnter account number: ").strip()
            account = self.accounts.get(account_num)

            if not account:
                print(f"[ERROR] Account {account_num} not found!")
                return

            amount = float(input("Enter withdrawal amount: $"))
            account.withdraw(amount)
            print(f"[SUCCESS] Withdrew ${amount:.2f} successfully!")
            print(f"          New balance: ${account.balance:.2f}")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def view_account_info(self):
        """View detailed account information."""
        if not self.accounts:
            print("\n[INFO] No accounts in the system yet!")
            return

        account_num = input("\nEnter account number: ").strip()
        account = self.accounts.get(account_num)

        if account:
            # POLYMORPHISM: The correct display_account_info is called based on account type
            account.display_account_info()
        else:
            print(f"[ERROR] Account {account_num} not found!")

    def view_balance(self):
        """View account balance."""
        if not self.accounts:
            print("\n[INFO] No accounts in the system yet!")
            return

        account_num = input("\nEnter account number: ").strip()
        account = self.accounts.get(account_num)

        if account:
            account.display_balance()
        else:
            print(f"[ERROR] Account {account_num} not found!")

    def view_transaction_history(self):
        """View transaction history for an account."""
        if not self.accounts:
            print("\n[INFO] No accounts in the system yet!")
            return

        account_num = input("\nEnter account number: ").strip()
        account = self.accounts.get(account_num)

        if account:
            account.display_transaction_history()
        else:
            print(f"[ERROR] Account {account_num} not found!")

    def list_all_accounts(self):
        """List all accounts in the system."""
        if not self.accounts:
            print("\n[INFO] No accounts in the system yet!")
            return

        print("\n" + "=" * 70)
        print(f"{'ALL ACCOUNTS':^70}")
        print("=" * 70)
        print(f"{'Account #':<15} {'Holder':<25} {'Type':<20} {'Balance':<10}")
        print("-" * 70)

        for account_num, account in sorted(self.accounts.items()):
            account_type = account.get_account_type()
            print(f"{account_num:<15} {account.account_holder:<25} {account_type:<20} ${account.balance:.2f}")

        print("=" * 70)
        print(f"Total Accounts: {len(self.accounts)}")

    def apply_interest(self):
        """Apply interest to all savings accounts."""
        savings_accounts = [acc for acc in self.accounts.values()
                            if isinstance(acc, SavingsAccount)]

        if not savings_accounts:
            print("\n[INFO] No savings accounts in the system!")
            return

        print("\n" + "=" * 70)
        print("APPLYING INTEREST TO SAVINGS ACCOUNTS")
        print("=" * 70)

        for account in savings_accounts:
            interest = account.apply_interest()
            print(f"Account {account.account_number}: +${interest:.2f} interest")

        print(f"\n[SUCCESS] Interest applied to {len(savings_accounts)} account(s)")

    def run(self):
        """Run the interactive menu system."""
        print("\n" + "=" * 70)
        print(f"{'WELCOME TO BANK ACCOUNT MANAGEMENT SYSTEM':^70}")
        print(f"{'Demonstrating OOP Principles':^70}")
        print("=" * 70)

        while True:
            print("\n" + "-" * 70)
            print("MAIN MENU")
            print("-" * 70)
            print("1.  Create Savings Account")
            print("2.  Create Checking Account")
            print("3.  Deposit Money")
            print("4.  Withdraw Money")
            print("5.  View Account Information")
            print("6.  View Account Balance")
            print("7.  View Transaction History")
            print("8.  List All Accounts")
            print("9.  Apply Interest (Savings Accounts)")
            print("10. Exit")
            print("-" * 70)

            choice = input("Enter your choice (1-10): ").strip()

            if choice == '1':
                self.create_savings_account()
            elif choice == '2':
                self.create_checking_account()
            elif choice == '3':
                self.deposit_to_account()
            elif choice == '4':
                self.withdraw_from_account()
            elif choice == '5':
                self.view_account_info()
            elif choice == '6':
                self.view_balance()
            elif choice == '7':
                self.view_transaction_history()
            elif choice == '8':
                self.list_all_accounts()
            elif choice == '9':
                self.apply_interest()
            elif choice == '10':
                print("\n" + "=" * 70)
                print(f"{'THANK YOU FOR USING OUR BANKING SYSTEM!':^70}")
                print(f"{'Goodbye!':^70}")
                print("=" * 70 + "\n")
                sys.exit(0)
            else:
                print("[ERROR] Invalid choice! Please enter a number between 1 and 10.")

            input("\nPress Enter to continue...")


# ============================================================================
# DEMONSTRATION OF POLYMORPHISM
# ============================================================================

def demonstrate_polymorphism(account: Account):
    """
    Demonstrate polymorphism by accepting any Account object.
    The correct display_account_info() method will be called based on type.

    Args:
        account: Any object that inherits from Account
    """
    account.display_account_info()


# ============================================================================
# Program Entry Point
# ============================================================================

if __name__ == "__main__":
    # Check if user wants interactive mode or demo mode
    print("\n" + "=" * 70)
    print(f"{'BANK ACCOUNT MANAGEMENT SYSTEM':^70}")
    print("=" * 70)
    print("\n1. Interactive Mode (Full Menu System)")
    print("2. Demo Mode (See Examples)")

    mode = input("\nSelect mode (1 or 2): ").strip()

    if mode == '1':
        # Run interactive system
        system = BankManagementSystem()
        system.run()
    else:
        # Run demonstration
        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATION MODE':^70}")
        print("=" * 70)

        # Create different account types
        print("\n>>> Creating Savings Account...")
        savings = SavingsAccount("ACC001001", "Alice Johnson", 1000.0, 3.0, 100.0)

        print("\n>>> Creating Checking Account...")
        checking = CheckingAccount("ACC001002", "Bob Smith", 500.0, 500.0, 10.0)

        # Demonstrate deposits
        print("\n>>> Depositing to Savings Account...")
        savings.deposit(500)
        print(f"    New balance: ${savings.balance:.2f}")

        print("\n>>> Depositing to Checking Account...")
        checking.deposit(300)
        print(f"    New balance: ${checking.balance:.2f}")

        # Demonstrate withdrawals
        print("\n>>> Withdrawing from Savings Account...")
        try:
            savings.withdraw(200)
            print(f"    New balance: ${savings.balance:.2f}")
        except ValueError as e:
            print(f"    [ERROR] {e}")

        print("\n>>> Withdrawing from Checking Account (with overdraft)...")
        try:
            checking.withdraw(900)  # Will use overdraft
            print(f"    New balance: ${checking.balance:.2f}")
            print(f"    Overdraft used: ${checking.overdraft_used:.2f}")
        except ValueError as e:
            print(f"    [ERROR] {e}")

        # Apply interest
        print("\n>>> Applying interest to Savings Account...")
        interest = savings.apply_interest()
        print(f"    Interest earned: ${interest:.2f}")
        print(f"    New balance: ${savings.balance:.2f}")

        # POLYMORPHISM demonstration
        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATING POLYMORPHISM':^70}")
        print("=" * 70)
        print("\nCalling demonstrate_polymorphism() with different account types:")

        demonstrate_polymorphism(savings)
        demonstrate_polymorphism(checking)

        # Show transaction histories
        savings.display_transaction_history()
        checking.display_transaction_history()

        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATION COMPLETED':^70}")
        print("=" * 70 + "\n")