"""
User Management System
A complete demonstration of Object-Oriented Programming principles in Python

This program demonstrates:
1. Encapsulation - Private attributes with getters/setters
2. Abstraction - Abstract base class Account
3. Inheritance - User, AdminUser, and ModeratorUser inherit from Account
4. Polymorphism - Method overriding
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import re
import sys


# ============================================================================
# ABSTRACTION: Abstract Base Class
# ============================================================================
# Abstraction hides complex implementation details and shows only essential
# features. An abstract class cannot be instantiated directly and serves as
# a blueprint for other classes.

class Account(ABC):
    """
    Abstract base class representing a user account.
    This class cannot be instantiated directly - it must be inherited.
    """

    def __init__(self, user_id: str, username: str, email: str, password: str):
        """
        Initialize an Account object.

        Args:
            user_id: Unique user identifier
            username: Username for login
            email: Email address
            password: Password (will be hashed)
        """
        # ENCAPSULATION: Private attributes (using _ prefix)
        # These attributes should not be accessed directly from outside
        self._user_id = user_id
        self._username = username
        self._email = email
        self._password_hash = self._hash_password(password)
        self._created_at = datetime.now()
        self._last_login = None
        self._is_active = True
        self._login_attempts = 0
        self._activity_log: List[str] = []

        # Log account creation
        self._log_activity("Account created")

    # ENCAPSULATION: Getter methods (properties)
    # These provide controlled access to private attributes

    @property
    def user_id(self) -> str:
        """Get the user ID."""
        return self._user_id

    @property
    def username(self) -> str:
        """Get the username."""
        return self._username

    @property
    def email(self) -> str:
        """Get the email."""
        return self._email

    @property
    def created_at(self) -> datetime:
        """Get account creation date."""
        return self._created_at

    @property
    def last_login(self) -> Optional[datetime]:
        """Get last login time."""
        return self._last_login

    @property
    def is_active(self) -> bool:
        """Check if account is active."""
        return self._is_active

    @property
    def login_attempts(self) -> int:
        """Get number of failed login attempts."""
        return self._login_attempts

    @property
    def activity_log(self) -> List[str]:
        """Get activity log."""
        return self._activity_log.copy()

    # ENCAPSULATION: Setter methods with validation

    @username.setter
    def username(self, value: str):
        """Set username with validation."""
        if not self._validate_username(value):
            raise ValueError("Username must be 3-20 characters, alphanumeric and underscores only")
        self._username = value
        self._log_activity(f"Username changed to {value}")

    @email.setter
    def email(self, value: str):
        """Set email with validation."""
        if not self._validate_email(value):
            raise ValueError("Invalid email format")
        self._email = value
        self._log_activity(f"Email changed to {value}")

    # Helper methods for validation
    @staticmethod
    def _validate_username(username: str) -> bool:
        """Validate username format."""
        if not username or not isinstance(username, str):
            return False
        if len(username) < 3 or len(username) > 20:
            return False
        return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format."""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def _validate_password(password: str) -> bool:
        """Validate password strength."""
        if not password or not isinstance(password, str):
            return False
        if len(password) < 6:
            return False
        # Could add more complex rules here
        return True

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _log_activity(self, activity: str):
        """Log user activity with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._activity_log.append(f"[{timestamp}] {activity}")

    # Public methods
    def update_email(self, new_email: str) -> bool:
        """
        Update email address.

        Args:
            new_email: New email address

        Returns:
            True if successful

        Raises:
            ValueError: If email format is invalid
        """
        if not self._validate_email(new_email):
            raise ValueError("Invalid email format")

        old_email = self._email
        self._email = new_email
        self._log_activity(f"Email updated from {old_email} to {new_email}")
        return True

    def update_password(self, old_password: str, new_password: str) -> bool:
        """
        Update password.

        Args:
            old_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            ValueError: If old password is incorrect or new password is invalid
        """
        # Verify old password
        if not self.verify_password(old_password):
            raise ValueError("Incorrect current password")

        # Validate new password
        if not self._validate_password(new_password):
            raise ValueError("New password must be at least 6 characters")

        # Update password
        self._password_hash = self._hash_password(new_password)
        self._log_activity("Password updated")
        return True

    def verify_password(self, password: str) -> bool:
        """Verify if provided password matches stored hash."""
        return self._hash_password(password) == self._password_hash

    def login(self, password: str) -> bool:
        """
        Attempt to login with password.

        Args:
            password: Password to verify

        Returns:
            True if login successful
        """
        if not self._is_active:
            raise ValueError("Account is deactivated")

        if self._login_attempts >= 5:
            raise ValueError("Account locked due to too many failed attempts")

        if self.verify_password(password):
            self._last_login = datetime.now()
            self._login_attempts = 0
            self._log_activity("Successful login")
            return True
        else:
            self._login_attempts += 1
            self._log_activity(f"Failed login attempt ({self._login_attempts}/5)")
            return False

    def deactivate(self):
        """Deactivate the account."""
        self._is_active = False
        self._log_activity("Account deactivated")

    def activate(self):
        """Activate the account."""
        self._is_active = True
        self._login_attempts = 0
        self._log_activity("Account activated")

    def reset_login_attempts(self):
        """Reset failed login attempts counter."""
        self._login_attempts = 0
        self._log_activity("Login attempts reset")

    # ABSTRACTION: Abstract methods
    # These methods MUST be implemented by any class that inherits from Account

    @abstractmethod
    def display_info(self):
        """Display account information. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_role(self) -> str:
        """Return the user role. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_permissions(self) -> List[str]:
        """Return list of permissions. Must be implemented by subclasses."""
        pass


# ============================================================================
# INHERITANCE: User class inherits from Account
# ============================================================================

class User(Account):
    """
    Standard User class that inherits from Account.
    Represents a regular user with basic permissions.
    """

    def __init__(self, user_id: str, username: str, email: str, password: str,
                 full_name: str = "", phone: str = ""):
        """
        Initialize a User object.

        Args:
            user_id: Unique user ID
            username: Username
            email: Email address
            password: Password
            full_name: Full name (optional)
            phone: Phone number (optional)
        """
        # Call parent class constructor using super()
        super().__init__(user_id, username, email, password)

        # ENCAPSULATION: Additional private attributes specific to User
        self._full_name = full_name
        self._phone = phone

    @property
    def full_name(self) -> str:
        """Get the full name."""
        return self._full_name

    @full_name.setter
    def full_name(self, value: str):
        """Set the full name."""
        self._full_name = value
        self._log_activity(f"Full name updated to {value}")

    @property
    def phone(self) -> str:
        """Get the phone number."""
        return self._phone

    @phone.setter
    def phone(self, value: str):
        """Set the phone number."""
        self._phone = value
        self._log_activity(f"Phone number updated")

    # POLYMORPHISM: Implement the abstract methods
    def display_info(self):
        """Display complete user information."""
        print("\n" + "=" * 70)
        print(f"{'USER INFORMATION':^70}")
        print("=" * 70)
        print(f"User ID       : {self._user_id}")
        print(f"Username      : {self._username}")
        print(f"Email         : {self._email}")
        print(f"Full Name     : {self._full_name if self._full_name else 'Not set'}")
        print(f"Phone         : {self._phone if self._phone else 'Not set'}")
        print(f"Role          : {self.get_role()}")
        print(f"Status        : {'ACTIVE' if self._is_active else 'DEACTIVATED'}")
        print(f"Created       : {self._created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if self._last_login:
            print(f"Last Login    : {self._last_login.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"Last Login    : Never")

        print(f"Failed Logins : {self._login_attempts}")
        print("=" * 70)

    def get_role(self) -> str:
        """Return the user role."""
        return "User"

    def get_permissions(self) -> List[str]:
        """Return list of user permissions."""
        return [
            "view_own_profile",
            "update_own_profile",
            "change_own_password"
        ]


# ============================================================================
# INHERITANCE & POLYMORPHISM: AdminUser class
# ============================================================================

class AdminUser(User):
    """
    AdminUser class that inherits from User.
    Administrators have elevated privileges.
    """

    def __init__(self, user_id: str, username: str, email: str, password: str,
                 full_name: str = "", phone: str = "", department: str = ""):
        """
        Initialize an AdminUser object.

        Args:
            user_id: Unique user ID
            username: Username
            email: Email address
            password: Password
            full_name: Full name
            phone: Phone number
            department: Department name
        """
        super().__init__(user_id, username, email, password, full_name, phone)

        # ENCAPSULATION: Admin-specific attributes
        self._department = department
        self._admin_actions: List[str] = []

    @property
    def department(self) -> str:
        """Get the department."""
        return self._department

    @department.setter
    def department(self, value: str):
        """Set the department."""
        self._department = value
        self._log_activity(f"Department updated to {value}")

    @property
    def admin_actions(self) -> List[str]:
        """Get admin action history."""
        return self._admin_actions.copy()

    def log_admin_action(self, action: str):
        """Log an administrative action."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._admin_actions.append(f"[{timestamp}] {action}")
        self._log_activity(f"Admin action: {action}")

    # POLYMORPHISM: Override display_info with admin-specific information
    def display_info(self):
        """Display complete admin information."""
        print("\n" + "=" * 70)
        print(f"{'ADMINISTRATOR INFORMATION':^70}")
        print("=" * 70)
        print(f"User ID       : {self._user_id}")
        print(f"Username      : {self._username}")
        print(f"Email         : {self._email}")
        print(f"Full Name     : {self._full_name if self._full_name else 'Not set'}")
        print(f"Phone         : {self._phone if self._phone else 'Not set'}")
        print(f"Department    : {self._department if self._department else 'Not set'}")
        print(f"Role          : {self.get_role()}")
        print(f"Status        : {'ACTIVE' if self._is_active else 'DEACTIVATED'}")
        print(f"Created       : {self._created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if self._last_login:
            print(f"Last Login    : {self._last_login.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"Last Login    : Never")

        print(f"Admin Actions : {len(self._admin_actions)}")
        print("=" * 70)

    # POLYMORPHISM: Override get_role
    def get_role(self) -> str:
        """Return the user role."""
        return "Administrator"

    # POLYMORPHISM: Override get_permissions with expanded privileges
    def get_permissions(self) -> List[str]:
        """Return list of admin permissions."""
        return [
            "view_own_profile",
            "update_own_profile",
            "change_own_password",
            "view_all_users",
            "create_users",
            "delete_users",
            "modify_users",
            "deactivate_users",
            "view_activity_logs",
            "reset_passwords",
            "manage_roles"
        ]


# ============================================================================
# INHERITANCE & POLYMORPHISM: ModeratorUser class
# ============================================================================

class ModeratorUser(User):
    """
    ModeratorUser class that inherits from User.
    Moderators have limited administrative privileges.
    """

    def __init__(self, user_id: str, username: str, email: str, password: str,
                 full_name: str = "", phone: str = "", moderation_area: str = ""):
        """
        Initialize a ModeratorUser object.

        Args:
            user_id: Unique user ID
            username: Username
            email: Email address
            password: Password
            full_name: Full name
            phone: Phone number
            moderation_area: Area of moderation responsibility
        """
        super().__init__(user_id, username, email, password, full_name, phone)

        # ENCAPSULATION: Moderator-specific attributes
        self._moderation_area = moderation_area
        self._warnings_issued = 0

    @property
    def moderation_area(self) -> str:
        """Get the moderation area."""
        return self._moderation_area

    @property
    def warnings_issued(self) -> int:
        """Get the number of warnings issued."""
        return self._warnings_issued

    def issue_warning(self, target_user: str, reason: str):
        """Issue a warning to a user."""
        self._warnings_issued += 1
        self._log_activity(f"Issued warning to {target_user}: {reason}")

    # POLYMORPHISM: Override display_info
    def display_info(self):
        """Display complete moderator information."""
        print("\n" + "=" * 70)
        print(f"{'MODERATOR INFORMATION':^70}")
        print("=" * 70)
        print(f"User ID          : {self._user_id}")
        print(f"Username         : {self._username}")
        print(f"Email            : {self._email}")
        print(f"Full Name        : {self._full_name if self._full_name else 'Not set'}")
        print(f"Phone            : {self._phone if self._phone else 'Not set'}")
        print(f"Moderation Area  : {self._moderation_area if self._moderation_area else 'Not set'}")
        print(f"Role             : {self.get_role()}")
        print(f"Status           : {'ACTIVE' if self._is_active else 'DEACTIVATED'}")
        print(f"Created          : {self._created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if self._last_login:
            print(f"Last Login       : {self._last_login.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"Last Login       : Never")

        print(f"Warnings Issued  : {self._warnings_issued}")
        print("=" * 70)

    def get_role(self) -> str:
        """Return the user role."""
        return "Moderator"

    def get_permissions(self) -> List[str]:
        """Return list of moderator permissions."""
        return [
            "view_own_profile",
            "update_own_profile",
            "change_own_password",
            "view_users",
            "issue_warnings",
            "deactivate_users",
            "view_activity_logs"
        ]


# ============================================================================
# UserManager Class - Main User Collection Manager
# ============================================================================

class UserManager:
    """
    UserManager class to manage a collection of users.
    Demonstrates composition and user management operations.
    """

    def __init__(self):
        """Initialize the UserManager."""
        # ENCAPSULATION: Private attributes
        self._users: Dict[str, Account] = {}  # Dictionary for fast lookup by user_id
        self._usernames: Dict[str, str] = {}  # Map username to user_id for uniqueness
        self._next_user_id = 1001

    @property
    def total_users(self) -> int:
        """Get total number of users."""
        return len(self._users)

    @property
    def active_users(self) -> int:
        """Get number of active users."""
        return sum(1 for user in self._users.values() if user.is_active)

    def generate_user_id(self) -> str:
        """Generate a unique user ID."""
        user_id = f"USR{self._next_user_id:05d}"
        self._next_user_id += 1
        return user_id

    def add_user(self, user: Account) -> bool:
        """
        Add a user to the system.

        Args:
            user: Account object to add

        Returns:
            True if successful

        Raises:
            ValueError: If user_id or username already exists
        """
        if user.user_id in self._users:
            raise ValueError(f"User ID {user.user_id} already exists")

        if user.username in self._usernames:
            raise ValueError(f"Username '{user.username}' is already taken")

        self._users[user.user_id] = user
        self._usernames[user.username] = user.user_id
        return True

    def remove_user(self, user_id: str) -> bool:
        """
        Remove a user from the system.

        Args:
            user_id: ID of user to remove

        Returns:
            True if successful

        Raises:
            ValueError: If user not found
        """
        if user_id not in self._users:
            raise ValueError(f"User ID {user_id} not found")

        user = self._users[user_id]
        del self._usernames[user.username]
        del self._users[user_id]
        return True

    def find_user_by_id(self, user_id: str) -> Optional[Account]:
        """Find a user by ID."""
        return self._users.get(user_id)

    def find_user_by_username(self, username: str) -> Optional[Account]:
        """Find a user by username."""
        user_id = self._usernames.get(username)
        if user_id:
            return self._users.get(user_id)
        return None

    def find_users_by_email(self, email: str) -> List[Account]:
        """Find users by email (partial match)."""
        email_lower = email.lower()
        return [user for user in self._users.values()
                if email_lower in user.email.lower()]

    def list_users(self) -> List[Account]:
        """Get list of all users."""
        return list(self._users.values())

    def list_users_by_role(self, role: str) -> List[Account]:
        """Get list of users by role."""
        return [user for user in self._users.values()
                if user.get_role().lower() == role.lower()]

    def list_active_users(self) -> List[Account]:
        """Get list of active users."""
        return [user for user in self._users.values() if user.is_active]

    def list_inactive_users(self) -> List[Account]:
        """Get list of inactive users."""
        return [user for user in self._users.values() if not user.is_active]

    def display_statistics(self):
        """Display user management statistics."""
        total = self.total_users
        active = self.active_users
        admins = len(self.list_users_by_role("Administrator"))
        mods = len(self.list_users_by_role("Moderator"))
        regular = len(self.list_users_by_role("User"))

        print("\n" + "=" * 70)
        print(f"{'USER MANAGEMENT STATISTICS':^70}")
        print("=" * 70)
        print(f"Total Users       : {total}")
        print(f"Active Users      : {active}")
        print(f"Inactive Users    : {total - active}")
        print(f"Administrators    : {admins}")
        print(f"Moderators        : {mods}")
        print(f"Regular Users     : {regular}")
        print("=" * 70)


# ============================================================================
# User Management System - Interactive Interface
# ============================================================================

class UserManagementSystem:
    """Main system to manage users with interactive menu."""

    def __init__(self):
        """Initialize the user management system."""
        self.manager = UserManager()

    def create_user(self):
        """Create a new regular user."""
        print("\n" + "=" * 70)
        print("CREATE NEW USER")
        print("=" * 70)

        try:
            username = input("Enter username (3-20 chars, alphanumeric): ").strip()
            email = input("Enter email: ").strip()
            password = input("Enter password (min 6 chars): ").strip()
            full_name = input("Enter full name (optional): ").strip()
            phone = input("Enter phone number (optional): ").strip()

            user_id = self.manager.generate_user_id()
            user = User(user_id, username, email, password, full_name, phone)
            self.manager.add_user(user)

            print(f"\n[SUCCESS] User created successfully!")
            print(f"          User ID: {user_id}")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def create_admin(self):
        """Create a new admin user."""
        print("\n" + "=" * 70)
        print("CREATE NEW ADMINISTRATOR")
        print("=" * 70)

        try:
            username = input("Enter username (3-20 chars, alphanumeric): ").strip()
            email = input("Enter email: ").strip()
            password = input("Enter password (min 6 chars): ").strip()
            full_name = input("Enter full name (optional): ").strip()
            phone = input("Enter phone number (optional): ").strip()
            department = input("Enter department (optional): ").strip()

            user_id = self.manager.generate_user_id()
            admin = AdminUser(user_id, username, email, password, full_name, phone, department)
            self.manager.add_user(admin)

            print(f"\n[SUCCESS] Administrator created successfully!")
            print(f"          User ID: {user_id}")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def create_moderator(self):
        """Create a new moderator user."""
        print("\n" + "=" * 70)
        print("CREATE NEW MODERATOR")
        print("=" * 70)

        try:
            username = input("Enter username (3-20 chars, alphanumeric): ").strip()
            email = input("Enter email: ").strip()
            password = input("Enter password (min 6 chars): ").strip()
            full_name = input("Enter full name (optional): ").strip()
            phone = input("Enter phone number (optional): ").strip()
            mod_area = input("Enter moderation area (optional): ").strip()

            user_id = self.manager.generate_user_id()
            mod = ModeratorUser(user_id, username, email, password, full_name, phone, mod_area)
            self.manager.add_user(mod)

            print(f"\n[SUCCESS] Moderator created successfully!")
            print(f"          User ID: {user_id}")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def update_user_email(self):
        """Update a user's email."""
        try:
            username = input("\nEnter username: ").strip()
            user = self.manager.find_user_by_username(username)

            if not user:
                print(f"[ERROR] User '{username}' not found!")
                return

            new_email = input("Enter new email: ").strip()
            user.update_email(new_email)
            print(f"[SUCCESS] Email updated successfully!")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def update_user_password(self):
        """Update a user's password."""
        try:
            username = input("\nEnter username: ").strip()
            user = self.manager.find_user_by_username(username)

            if not user:
                print(f"[ERROR] User '{username}' not found!")
                return

            old_password = input("Enter current password: ").strip()
            new_password = input("Enter new password: ").strip()
            user.update_password(old_password, new_password)
            print(f"[SUCCESS] Password updated successfully!")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def login_user(self):
        """Simulate user login."""
        try:
            username = input("\nEnter username: ").strip()
            password = input("Enter password: ").strip()

            user = self.manager.find_user_by_username(username)

            if not user:
                print(f"[ERROR] User '{username}' not found!")
                return

            if user.login(password):
                print(f"[SUCCESS] Login successful! Welcome, {username}!")
                print(f"          Role: {user.get_role()}")
            else:
                print(f"[ERROR] Incorrect password!")
                print(f"        Failed attempts: {user.login_attempts}/5")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def view_user_info(self):
        """View detailed user information."""
        username = input("\nEnter username: ").strip()
        user = self.manager.find_user_by_username(username)

        if user:
            # POLYMORPHISM: Correct display_info is called based on user type
            user.display_info()
        else:
            print(f"[ERROR] User '{username}' not found!")

    def list_all_users(self):
        """List all users in the system."""
        users = self.manager.list_users()

        if not users:
            print("\n[INFO] No users in the system yet!")
            return

        print("\n" + "=" * 70)
        print(f"{'ALL USERS':^70}")
        print("=" * 70)
        print(f"{'Username':<20} {'Role':<15} {'Email':<25} {'Status':<10}")
        print("-" * 70)

        for user in users:
            status = "ACTIVE" if user.is_active else "INACTIVE"
            print(f"{user.username:<20} {user.get_role():<15} {user.email:<25} {status:<10}")

        print("=" * 70)
        print(f"Total: {len(users)} user(s)")

    def list_users_by_role(self):
        """List users filtered by role."""
        print("\n1. Administrators")
        print("2. Moderators")
        print("3. Regular Users")

        choice = input("\nSelect role (1-3): ").strip()

        role_map = {
            '1': 'Administrator',
            '2': 'Moderator',
            '3': 'User'
        }

        if choice not in role_map:
            print("[ERROR] Invalid choice!")
            return

        role = role_map[choice]
        users = self.manager.list_users_by_role(role)

        if users:
            print(f"\n{role.upper()}S")
            print("-" * 70)
            for user in users:
                status = "ACTIVE" if user.is_active else "INACTIVE"
                print(f"{user.username:<20} {user.email:<30} {status}")
            print(f"\nTotal: {len(users)} {role.lower()}(s)")
        else:
            print(f"[INFO] No {role.lower()}s found.")

    def deactivate_user(self):
        """Deactivate a user account."""
        try:
            username = input("\nEnter username to deactivate: ").strip()
            user = self.manager.find_user_by_username(username)

            if not user:
                print(f"[ERROR] User '{username}' not found!")
                return

            user.deactivate()
            print(f"[SUCCESS] User '{username}' deactivated successfully!")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def activate_user(self):
        """Activate a user account."""
        try:
            username = input("\nEnter username to activate: ").strip()
            user = self.manager.find_user_by_username(username)

            if not user:
                print(f"[ERROR] User '{username}' not found!")
                return

            user.activate()
            print(f"[SUCCESS] User '{username}' activated successfully!")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def remove_user(self):
        """Remove a user from the system."""
        try:
            username = input("\nEnter username to remove: ").strip()
            user = self.manager.find_user_by_username(username)

            if not user:
                print(f"[ERROR] User '{username}' not found!")
                return

            confirm = input(f"Are you sure you want to remove '{username}'? (yes/no): ").strip().lower()

            if confirm == 'yes':
                self.manager.remove_user(user.user_id)
                print(f"[SUCCESS] User '{username}' removed successfully!")
            else:
                print("[INFO] Removal cancelled.")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def view_activity_log(self):
        """View user activity log."""
        username = input("\nEnter username: ").strip()
        user = self.manager.find_user_by_username(username)

        if not user:
            print(f"[ERROR] User '{username}' not found!")
            return

        print("\n" + "=" * 70)
        print(f"ACTIVITY LOG FOR {username.upper()}")
        print("=" * 70)

        log = user.activity_log
        if log:
            for entry in log:
                print(entry)
        else:
            print("No activity recorded.")

        print("=" * 70)

    def run(self):
        """Run the interactive menu system."""
        print("\n" + "=" * 70)
        print(f"{'WELCOME TO USER MANAGEMENT SYSTEM':^70}")
        print(f"{'Demonstrating OOP Principles':^70}")
        print("=" * 70)

        while True:
            print("\n" + "-" * 70)
            print("MAIN MENU")
            print("-" * 70)
            print("1.  Create Regular User")
            print("2.  Create Administrator")
            print("3.  Create Moderator")
            print("4.  Update User Email")
            print("5.  Update User Password")
            print("6.  Login User")
            print("7.  View User Info")
            print("8.  List All Users")
            print("9.  List Users by Role")
            print("10. Deactivate User")
            print("11. Activate User")
            print("12. Remove User")
            print("13. View Activity Log")
            print("14. View Statistics")
            print("15. Exit")
            print("-" * 70)

            choice = input("Enter your choice (1-15): ").strip()

            if choice == '1':
                self.create_user()
            elif choice == '2':
                self.create_admin()
            elif choice == '3':
                self.create_moderator()
            elif choice == '4':
                self.update_user_email()
            elif choice == '5':
                self.update_user_password()
            elif choice == '6':
                self.login_user()
            elif choice == '7':
                self.view_user_info()
            elif choice == '8':
                self.list_all_users()
            elif choice == '9':
                self.list_users_by_role()
            elif choice == '10':
                self.deactivate_user()
            elif choice == '11':
                self.activate_user()
            elif choice == '12':
                self.remove_user()
            elif choice == '13':
                self.view_activity_log()
            elif choice == '14':
                self.manager.display_statistics()
            elif choice == '15':
                print("\n" + "=" * 70)
                print(f"{'THANK YOU FOR USING THE SYSTEM!':^70}")
                print(f"{'Goodbye!':^70}")
                print("=" * 70 + "\n")
                sys.exit(0)
            else:
                print("[ERROR] Invalid choice! Please enter a number between 1 and 15.")

            input("\nPress Enter to continue...")


# ============================================================================
# Program Entry Point
# ============================================================================

if __name__ == "__main__":
    # Check if user wants interactive mode or demo mode
    print("\n" + "=" * 70)
    print(f"{'USER MANAGEMENT SYSTEM':^70}")
    print("=" * 70)
    print("\n1. Interactive Mode (Full Menu System)")
    print("2. Demo Mode (See Examples)")

    mode = input("\nSelect mode (1 or 2): ").strip()

    if mode == '1':
        # Run interactive system
        system = UserManagementSystem()
        system.run()
    else:
        # Run demonstration
        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATION MODE':^70}")
        print("=" * 70)

        # Create user manager
        manager = UserManager()

        # Create different user types
        print("\n>>> Creating Regular User...")
        user1 = User("USR00001", "alice_j", "alice@example.com", "password123",
                     "Alice Johnson", "555-0101")
        manager.add_user(user1)
        print(f"    Created: {user1.username} ({user1.get_role()})")

        print("\n>>> Creating Administrator...")
        admin1 = AdminUser("USR00002", "bob_admin", "bob@example.com", "admin123",
                           "Bob Smith", "555-0102", "IT Department")
        manager.add_user(admin1)
        print(f"    Created: {admin1.username} ({admin1.get_role()})")

        print("\n>>> Creating Moderator...")
        mod1 = ModeratorUser("USR00003", "carol_mod", "carol@example.com", "mod123",
                             "Carol Davis", "555-0103", "Content Moderation")
        manager.add_user(mod1)
        print(f"    Created: {mod1.username} ({mod1.get_role()})")

        # Demonstrate login
        print("\n>>> Testing user login...")
        try:
            if user1.login("password123"):
                print(f"    {user1.username} logged in successfully")
        except ValueError as e:
            print(f"    [ERROR] {e}")

        # Update email
        print("\n>>> Updating Alice's email...")
        try:
            user1.update_email("alice.johnson@example.com")
            print(f"    Email updated to: {user1.email}")
        except ValueError as e:
            print(f"    [ERROR] {e}")

        # Update password
        print("\n>>> Updating Alice's password...")
        try:
            user1.update_password("password123", "newpassword456")
            print(f"    Password updated successfully")
        except ValueError as e:
            print(f"    [ERROR] {e}")

        # Search users
        print("\n>>> Searching for user by username...")
        found = manager.find_user_by_username("bob_admin")
        if found:
            print(f"    Found: {found.username} - {found.email} ({found.get_role()})")

        # POLYMORPHISM demonstration
        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATING POLYMORPHISM':^70}")
        print("=" * 70)
        print("\nDisplaying different user types (polymorphic behavior):")

        user1.display_info()
        admin1.display_info()
        mod1.display_info()

        # Display permissions
        print("\n>>> Comparing user permissions...")
        print(f"\nRegular User permissions:")
        for perm in user1.get_permissions():
            print(f"  - {perm}")

        print(f"\nAdministrator permissions:")
        for perm in admin1.get_permissions():
            print(f"  - {perm}")

        print(f"\nModerator permissions:")
        for perm in mod1.get_permissions():
            print(f"  - {perm}")

        # Display statistics
        manager.display_statistics()

        # Activity log
        print("\n>>> Viewing Alice's activity log...")
        print("-" * 70)
        for entry in user1.activity_log[:5]:  # Show first 5 entries
            print(entry)

        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATION COMPLETED':^70}")
        print("=" * 70 + "\n")