"""
Library Management System
A complete demonstration of Object-Oriented Programming principles in Python

This program demonstrates:
1. Encapsulation - Private attributes with getters/setters
2. Abstraction - Abstract base class Item
3. Inheritance - Book and DigitalBook inherit from Item
4. Polymorphism - Method overriding
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys


# ============================================================================
# ABSTRACTION: Abstract Base Class
# ============================================================================
# Abstraction hides complex implementation details and shows only essential
# features. An abstract class cannot be instantiated directly and serves as
# a blueprint for other classes.

class Item(ABC):
    """
    Abstract base class representing a library item.
    This class cannot be instantiated directly - it must be inherited.
    """

    def __init__(self, item_id: str, title: str, author: str, year: int):
        """
        Initialize an Item object.

        Args:
            item_id: Unique identifier for the item
            title: Title of the item
            author: Author/creator of the item
            year: Publication year
        """
        # ENCAPSULATION: Private attributes (using _ prefix)
        # These attributes should not be accessed directly from outside
        self._item_id = item_id
        self._title = title
        self._author = author
        self._year = year
        self._available = True
        self._borrowed_by = None
        self._due_date = None
        self._borrow_history: List[str] = []

    # ENCAPSULATION: Getter methods (properties)
    # These provide controlled access to private attributes

    @property
    def item_id(self) -> str:
        """Get the item ID."""
        return self._item_id

    @property
    def title(self) -> str:
        """Get the title."""
        return self._title

    @property
    def author(self) -> str:
        """Get the author."""
        return self._author

    @property
    def year(self) -> int:
        """Get the publication year."""
        return self._year

    @property
    def available(self) -> bool:
        """Check if item is available."""
        return self._available

    @property
    def borrowed_by(self) -> Optional[str]:
        """Get who borrowed the item."""
        return self._borrowed_by

    @property
    def due_date(self) -> Optional[datetime]:
        """Get the due date."""
        return self._due_date

    @property
    def borrow_history(self) -> List[str]:
        """Get borrow history."""
        return self._borrow_history.copy()

    # ENCAPSULATION: Setter methods with validation

    @title.setter
    def title(self, value: str):
        """Set the title with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("Title must be a non-empty string")
        self._title = value

    @author.setter
    def author(self, value: str):
        """Set the author with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("Author must be a non-empty string")
        self._author = value

    @year.setter
    def year(self, value: int):
        """Set the year with validation."""
        current_year = datetime.now().year
        if not isinstance(value, int) or value < 1000 or value > current_year + 1:
            raise ValueError(f"Year must be between 1000 and {current_year + 1}")
        self._year = value

    # Common methods for all items
    def borrow_item(self, borrower_name: str, days: int = 14) -> bool:
        """
        Borrow the item.

        Args:
            borrower_name: Name of the person borrowing
            days: Number of days for the loan

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If item is not available
        """
        if not self._available:
            raise ValueError(f"Item '{self._title}' is not available. Currently borrowed by {self._borrowed_by}")

        self._available = False
        self._borrowed_by = borrower_name
        self._due_date = datetime.now() + timedelta(days=days)

        # Add to history
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._borrow_history.append(
            f"[{timestamp}] Borrowed by {borrower_name} - Due: {self._due_date.strftime('%Y-%m-%d')}"
        )

        return True

    def return_item(self) -> bool:
        """
        Return the item.

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If item is already available
        """
        if self._available:
            raise ValueError(f"Item '{self._title}' is already available (not borrowed)")

        # Check if overdue
        is_overdue = datetime.now() > self._due_date

        # Add to history
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "OVERDUE" if is_overdue else "On time"
        self._borrow_history.append(
            f"[{timestamp}] Returned by {self._borrowed_by} - {status}"
        )

        self._available = True
        self._borrowed_by = None
        self._due_date = None

        return is_overdue

    def is_overdue(self) -> bool:
        """Check if the item is overdue."""
        if self._available or not self._due_date:
            return False
        return datetime.now() > self._due_date

    def days_until_due(self) -> Optional[int]:
        """Get number of days until due (negative if overdue)."""
        if self._available or not self._due_date:
            return None
        delta = self._due_date - datetime.now()
        return delta.days

    # ABSTRACTION: Abstract methods
    # These methods MUST be implemented by any class that inherits from Item

    @abstractmethod
    def display_info(self):
        """Display item information. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_item_type(self) -> str:
        """Return the type of item. Must be implemented by subclasses."""
        pass


# ============================================================================
# INHERITANCE: Book class inherits from Item
# ============================================================================
# Inheritance allows a class to inherit attributes and methods from a parent
# class, promoting code reuse and establishing a relationship between classes.

class Book(Item):
    """
    Book class that inherits from Item.
    Represents a physical book in the library.
    """

    def __init__(self, book_id: str, title: str, author: str, year: int,
                 isbn: str = "", pages: int = 0, genre: str = "General"):
        """
        Initialize a Book object.

        Args:
            book_id: Unique book ID
            title: Book title
            author: Book author
            year: Publication year
            isbn: ISBN number
            pages: Number of pages
            genre: Book genre
        """
        # Call parent class constructor using super()
        super().__init__(book_id, title, author, year)

        # ENCAPSULATION: Additional private attributes specific to Book
        self._isbn = isbn
        self._pages = pages
        self._genre = genre

    # ENCAPSULATION: Getters for book-specific attributes

    @property
    def isbn(self) -> str:
        """Get the ISBN."""
        return self._isbn

    @property
    def pages(self) -> int:
        """Get the number of pages."""
        return self._pages

    @property
    def genre(self) -> str:
        """Get the genre."""
        return self._genre

    @genre.setter
    def genre(self, value: str):
        """Set the genre with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("Genre must be a non-empty string")
        self._genre = value

    # Convenience methods for Book
    def borrow_book(self, borrower_name: str, days: int = 14) -> bool:
        """Borrow the book (calls parent method)."""
        return self.borrow_item(borrower_name, days)

    def return_book(self) -> bool:
        """Return the book (calls parent method)."""
        return self.return_item()

    # POLYMORPHISM: Override the abstract method from Item
    def display_info(self):
        """Display complete book information."""
        print("\n" + "=" * 70)
        print(f"{'BOOK INFORMATION':^70}")
        print("=" * 70)
        print(f"Book ID      : {self._item_id}")
        print(f"Title        : {self._title}")
        print(f"Author       : {self._author}")
        print(f"Year         : {self._year}")
        print(f"ISBN         : {self._isbn if self._isbn else 'N/A'}")
        print(f"Pages        : {self._pages if self._pages else 'N/A'}")
        print(f"Genre        : {self._genre}")
        print(f"Type         : {self.get_item_type()}")

        # Availability status
        if self._available:
            print(f"Status       : AVAILABLE")
        else:
            print(f"Status       : BORROWED")
            print(f"Borrowed by  : {self._borrowed_by}")
            print(f"Due date     : {self._due_date.strftime('%Y-%m-%d')}")
            days = self.days_until_due()
            if days < 0:
                print(f"OVERDUE      : {abs(days)} days")
            else:
                print(f"Days left    : {days} days")

        print(f"Borrow count : {len(self._borrow_history) // 2}")  # Each borrow has 2 entries
        print("=" * 70)

    def get_item_type(self) -> str:
        """Return the item type."""
        return "Physical Book"


# ============================================================================
# INHERITANCE & POLYMORPHISM: DigitalBook class
# ============================================================================
# DigitalBook inherits from Book and demonstrates polymorphism by
# overriding methods with digital-specific implementations.

class DigitalBook(Book):
    """
    DigitalBook class that inherits from Book.
    Represents a digital/ebook in the library.
    """

    def __init__(self, book_id: str, title: str, author: str, year: int,
                 isbn: str = "", pages: int = 0, genre: str = "General",
                 file_format: str = "PDF", file_size_mb: float = 0.0, download_link: str = ""):
        """
        Initialize a DigitalBook object.

        Args:
            book_id: Unique book ID
            title: Book title
            author: Book author
            year: Publication year
            isbn: ISBN number
            pages: Number of pages
            genre: Book genre
            file_format: File format (PDF, EPUB, MOBI, etc.)
            file_size_mb: File size in megabytes
            download_link: Download URL or path
        """
        # Call parent class (Book) constructor
        super().__init__(book_id, title, author, year, isbn, pages, genre)

        # ENCAPSULATION: Additional attributes specific to digital books
        self._file_format = file_format
        self._file_size_mb = file_size_mb
        self._download_link = download_link
        self._download_count = 0

    @property
    def file_format(self) -> str:
        """Get the file format."""
        return self._file_format

    @property
    def file_size_mb(self) -> float:
        """Get the file size in MB."""
        return self._file_size_mb

    @property
    def download_link(self) -> str:
        """Get the download link."""
        return self._download_link

    @property
    def download_count(self) -> int:
        """Get the download count."""
        return self._download_count

    # POLYMORPHISM: Override borrow method for digital books
    def borrow_item(self, borrower_name: str, days: int = 7) -> bool:
        """
        Borrow digital book (shorter loan period, unlimited copies).
        Digital books have unlimited copies, so always available.

        Args:
            borrower_name: Name of the person borrowing
            days: Number of days for the loan (default 7 for digital)

        Returns:
            True if successful
        """
        # Digital books don't become unavailable (unlimited copies)
        # Just track the borrow
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        due_date = datetime.now() + timedelta(days=days)
        self._borrow_history.append(
            f"[{timestamp}] Downloaded by {borrower_name} - Due: {due_date.strftime('%Y-%m-%d')}"
        )
        self._download_count += 1

        return True

    # POLYMORPHISM: Override return method for digital books
    def return_item(self) -> bool:
        """
        Digital books don't need to be returned.
        They expire automatically.
        """
        # Digital books auto-expire, so this is just for tracking
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._borrow_history.append(
            f"[{timestamp}] License expired/returned"
        )
        return False  # Never overdue

    # POLYMORPHISM: Override display_info with digital-specific information
    def display_info(self):
        """Display complete digital book information."""
        print("\n" + "=" * 70)
        print(f"{'DIGITAL BOOK INFORMATION':^70}")
        print("=" * 70)
        print(f"Book ID      : {self._item_id}")
        print(f"Title        : {self._title}")
        print(f"Author       : {self._author}")
        print(f"Year         : {self._year}")
        print(f"ISBN         : {self._isbn if self._isbn else 'N/A'}")
        print(f"Pages        : {self._pages if self._pages else 'N/A'}")
        print(f"Genre        : {self._genre}")
        print(f"Type         : {self.get_item_type()}")
        print(f"Format       : {self._file_format}")
        print(f"File Size    : {self._file_size_mb} MB")
        print(f"Status       : AVAILABLE (unlimited copies)")
        print(f"Downloads    : {self._download_count}")
        if self._download_link:
            print(f"Download Link: {self._download_link}")
        print("=" * 70)

    def get_item_type(self) -> str:
        """Return the item type."""
        return f"Digital Book ({self._file_format})"


# ============================================================================
# Library Class - Main Collection Manager
# ============================================================================

class Library:
    """
    Library class to manage a collection of books and digital books.
    Demonstrates composition (Library has-a collection of Items).
    """

    def __init__(self, name: str, address: str):
        """
        Initialize a Library object.

        Args:
            name: Library name
            address: Library address
        """
        # ENCAPSULATION: Private attributes
        self._name = name
        self._address = address
        self._items: Dict[str, Item] = {}  # Dictionary for fast lookup by ID
        self._members: Dict[str, List[str]] = {}  # Track member borrowings

    @property
    def name(self) -> str:
        """Get the library name."""
        return self._name

    @property
    def address(self) -> str:
        """Get the library address."""
        return self._address

    @property
    def total_items(self) -> int:
        """Get total number of items."""
        return len(self._items)

    @property
    def available_items(self) -> int:
        """Get number of available items."""
        return sum(1 for item in self._items.values() if item.available)

    def add_book(self, item: Item) -> bool:
        """
        Add a book to the library.

        Args:
            item: Item object to add

        Returns:
            True if successful, False otherwise
        """
        if item.item_id in self._items:
            raise ValueError(f"Item with ID {item.item_id} already exists")

        self._items[item.item_id] = item
        return True

    def remove_book(self, item_id: str) -> bool:
        """
        Remove a book from the library.

        Args:
            item_id: ID of the item to remove

        Returns:
            True if successful, False otherwise
        """
        if item_id not in self._items:
            raise ValueError(f"Item with ID {item_id} not found")

        item = self._items[item_id]
        if not item.available:
            raise ValueError(f"Cannot remove item '{item.title}' - currently borrowed")

        del self._items[item_id]
        return True

    def find_book_by_id(self, item_id: str) -> Optional[Item]:
        """Find a book by ID."""
        return self._items.get(item_id)

    def find_book_by_title(self, title: str) -> List[Item]:
        """
        Find books by title (partial match, case-insensitive).

        Args:
            title: Title to search for

        Returns:
            List of matching items
        """
        title_lower = title.lower()
        return [item for item in self._items.values()
                if title_lower in item.title.lower()]

    def find_books_by_author(self, author: str) -> List[Item]:
        """Find books by author (partial match, case-insensitive)."""
        author_lower = author.lower()
        return [item for item in self._items.values()
                if author_lower in item.author.lower()]

    def find_books_by_genre(self, genre: str) -> List[Item]:
        """Find books by genre."""
        genre_lower = genre.lower()
        return [item for item in self._items.values()
                if isinstance(item, Book) and genre_lower in item.genre.lower()]

    def list_available_books(self) -> List[Item]:
        """Get list of all available books."""
        return [item for item in self._items.values() if item.available]

    def list_borrowed_books(self) -> List[Item]:
        """Get list of all borrowed books."""
        return [item for item in self._items.values() if not item.available]

    def list_overdue_books(self) -> List[Item]:
        """Get list of all overdue books."""
        return [item for item in self._items.values() if item.is_overdue()]

    def borrow_book(self, item_id: str, borrower_name: str, days: int = 14) -> bool:
        """
        Borrow a book from the library.

        Args:
            item_id: ID of the item to borrow
            borrower_name: Name of the borrower
            days: Loan period in days

        Returns:
            True if successful
        """
        item = self.find_book_by_id(item_id)
        if not item:
            raise ValueError(f"Item with ID {item_id} not found")

        # Track member borrowings
        if borrower_name not in self._members:
            self._members[borrower_name] = []

        result = item.borrow_item(borrower_name, days)

        if result and isinstance(item, Book) and not isinstance(item, DigitalBook):
            # Only track physical books for members
            self._members[borrower_name].append(item_id)

        return result

    def return_book(self, item_id: str) -> bool:
        """
        Return a book to the library.

        Args:
            item_id: ID of the item to return

        Returns:
            True if overdue, False if on time
        """
        item = self.find_book_by_id(item_id)
        if not item:
            raise ValueError(f"Item with ID {item_id} not found")

        is_overdue = item.return_item()

        # Remove from member's borrowed list
        if item.borrowed_by and item.borrowed_by in self._members:
            if item_id in self._members[item.borrowed_by]:
                self._members[item.borrowed_by].remove(item_id)

        return is_overdue

    def get_member_books(self, member_name: str) -> List[Item]:
        """Get all books currently borrowed by a member."""
        if member_name not in self._members:
            return []

        return [self._items[item_id] for item_id in self._members[member_name]
                if item_id in self._items]

    def display_library_info(self):
        """Display library information."""
        print("\n" + "=" * 70)
        print(f"{'LIBRARY INFORMATION':^70}")
        print("=" * 70)
        print(f"Name              : {self._name}")
        print(f"Address           : {self._address}")
        print(f"Total Items       : {self.total_items}")
        print(f"Available Items   : {self.available_items}")
        print(f"Borrowed Items    : {self.total_items - self.available_items}")
        print(f"Registered Members: {len(self._members)}")
        print("=" * 70)


# ============================================================================
# Library Management System - Interactive Interface
# ============================================================================

class LibraryManagementSystem:
    """Main system to manage library with interactive menu."""

    def __init__(self):
        """Initialize the library management system."""
        self.library: Optional[Library] = None
        self.next_book_id = 1001

    def generate_book_id(self) -> str:
        """Generate a unique book ID."""
        book_id = f"BK{self.next_book_id:05d}"
        self.next_book_id += 1
        return book_id

    def create_library(self):
        """Create a new library."""
        print("\n" + "=" * 70)
        print("CREATE NEW LIBRARY")
        print("=" * 70)

        name = input("Enter library name: ").strip()
        if not name:
            print("[ERROR] Library name cannot be empty!")
            return

        address = input("Enter library address: ").strip()
        if not address:
            print("[ERROR] Library address cannot be empty!")
            return

        self.library = Library(name, address)
        print(f"\n[SUCCESS] Library '{name}' created successfully!")

    def add_physical_book(self):
        """Add a new physical book."""
        if not self.library:
            print("\n[ERROR] Please create a library first!")
            return

        print("\n" + "=" * 70)
        print("ADD NEW PHYSICAL BOOK")
        print("=" * 70)

        try:
            title = input("Enter book title: ").strip()
            if not title:
                print("[ERROR] Title cannot be empty!")
                return

            author = input("Enter author name: ").strip()
            if not author:
                print("[ERROR] Author cannot be empty!")
                return

            year = int(input("Enter publication year: "))
            isbn = input("Enter ISBN (optional): ").strip()
            pages = int(input("Enter number of pages (0 if unknown): ") or "0")
            genre = input("Enter genre (default: General): ").strip() or "General"

            book_id = self.generate_book_id()
            book = Book(book_id, title, author, year, isbn, pages, genre)
            self.library.add_book(book)

            print(f"\n[SUCCESS] Physical book added successfully!")
            print(f"          Book ID: {book_id}")

        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")

    def add_digital_book(self):
        """Add a new digital book."""
        if not self.library:
            print("\n[ERROR] Please create a library first!")
            return

        print("\n" + "=" * 70)
        print("ADD NEW DIGITAL BOOK")
        print("=" * 70)

        try:
            title = input("Enter book title: ").strip()
            if not title:
                print("[ERROR] Title cannot be empty!")
                return

            author = input("Enter author name: ").strip()
            if not author:
                print("[ERROR] Author cannot be empty!")
                return

            year = int(input("Enter publication year: "))
            isbn = input("Enter ISBN (optional): ").strip()
            pages = int(input("Enter number of pages (0 if unknown): ") or "0")
            genre = input("Enter genre (default: General): ").strip() or "General"
            file_format = input("Enter file format (PDF/EPUB/MOBI, default: PDF): ").strip() or "PDF"
            file_size = float(input("Enter file size in MB (default: 0): ") or "0")
            download_link = input("Enter download link (optional): ").strip()

            book_id = self.generate_book_id()
            book = DigitalBook(book_id, title, author, year, isbn, pages, genre,
                               file_format, file_size, download_link)
            self.library.add_book(book)

            print(f"\n[SUCCESS] Digital book added successfully!")
            print(f"          Book ID: {book_id}")

        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")

    def borrow_book(self):
        """Borrow a book from the library."""
        if not self.library:
            print("\n[ERROR] Please create a library first!")
            return

        try:
            book_id = input("\nEnter book ID: ").strip()
            borrower = input("Enter borrower name: ").strip()

            if not borrower:
                print("[ERROR] Borrower name cannot be empty!")
                return

            days_input = input("Enter loan period in days (default: 14): ").strip()
            days = int(days_input) if days_input else 14

            self.library.borrow_book(book_id, borrower, days)
            print(f"[SUCCESS] Book borrowed successfully by {borrower}!")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def return_book(self):
        """Return a book to the library."""
        if not self.library:
            print("\n[ERROR] Please create a library first!")
            return

        try:
            book_id = input("\nEnter book ID: ").strip()
            is_overdue = self.library.return_book(book_id)

            if is_overdue:
                print(f"[WARNING] Book returned successfully but was OVERDUE!")
            else:
                print(f"[SUCCESS] Book returned successfully on time!")

        except ValueError as e:
            print(f"[ERROR] {e}")

    def search_books(self):
        """Search for books."""
        if not self.library:
            print("\n[ERROR] Please create a library first!")
            return

        print("\n" + "=" * 70)
        print("SEARCH OPTIONS")
        print("=" * 70)
        print("1. Search by Title")
        print("2. Search by Author")
        print("3. Search by Genre")
        print("4. Search by ID")

        choice = input("\nEnter choice (1-4): ").strip()

        results = []

        if choice == '1':
            title = input("Enter title to search: ").strip()
            results = self.library.find_book_by_title(title)
        elif choice == '2':
            author = input("Enter author to search: ").strip()
            results = self.library.find_books_by_author(author)
        elif choice == '3':
            genre = input("Enter genre to search: ").strip()
            results = self.library.find_books_by_genre(genre)
        elif choice == '4':
            book_id = input("Enter book ID: ").strip()
            book = self.library.find_book_by_id(book_id)
            if book:
                results = [book]
        else:
            print("[ERROR] Invalid choice!")
            return

        if results:
            print(f"\n[SUCCESS] Found {len(results)} book(s):")
            print("-" * 70)
            for item in results:
                status = "AVAILABLE" if item.available else "BORROWED"
                print(f"ID: {item.item_id} | {item.title} by {item.author} | {item.get_item_type()} | {status}")
        else:
            print("[INFO] No books found matching your search.")

    def list_books(self):
        """List all books or filter by status."""
        if not self.library:
            print("\n[ERROR] Please create a library first!")
            return

        print("\n" + "=" * 70)
        print("LIST OPTIONS")
        print("=" * 70)
        print("1. All Books")
        print("2. Available Books Only")
        print("3. Borrowed Books Only")
        print("4. Overdue Books Only")

        choice = input("\nEnter choice (1-4): ").strip()

        items = []
        title = ""

        if choice == '1':
            items = list(self.library._items.values())
            title = "ALL BOOKS"
        elif choice == '2':
            items = self.library.list_available_books()
            title = "AVAILABLE BOOKS"
        elif choice == '3':
            items = self.library.list_borrowed_books()
            title = "BORROWED BOOKS"
        elif choice == '4':
            items = self.library.list_overdue_books()
            title = "OVERDUE BOOKS"
        else:
            print("[ERROR] Invalid choice!")
            return

        if items:
            print(f"\n{'=' * 70}")
            print(f"{title:^70}")
            print("=" * 70)
            print(f"{'ID':<12} {'Title':<30} {'Type':<20} {'Status':<8}")
            print("-" * 70)

            for item in items:
                status = "AVAIL" if item.available else "BORROWED"
                item_type = item.get_item_type()
                title_short = item.title[:28] + ".." if len(item.title) > 30 else item.title
                print(f"{item.item_id:<12} {title_short:<30} {item_type:<20} {status:<8}")

            print("=" * 70)
            print(f"Total: {len(items)} book(s)")
        else:
            print(f"[INFO] No books found in this category.")

    def view_book_details(self):
        """View detailed information about a book."""
        if not self.library:
            print("\n[ERROR] Please create a library first!")
            return

        book_id = input("\nEnter book ID: ").strip()
        book = self.library.find_book_by_id(book_id)

        if book:
            # POLYMORPHISM: Correct display_info is called based on book type
            book.display_info()
        else:
            print(f"[ERROR] Book with ID {book_id} not found!")

    def view_member_books(self):
        """View books borrowed by a specific member."""
        if not self.library:
            print("\n[ERROR] Please create a library first!")
            return

        member = input("\nEnter member name: ").strip()
        books = self.library.get_member_books(member)

        if books:
            print(f"\n{'=' * 70}")
            print(f"BOOKS BORROWED BY {member.upper()}")
            print("=" * 70)

            for book in books:
                days = book.days_until_due()
                due_str = f"{days} days" if days >= 0 else f"OVERDUE {abs(days)} days"
                print(f"ID: {book.item_id} | {book.title} | Due: {due_str}")

            print("=" * 70)
        else:
            print(f"[INFO] No books currently borrowed by {member}")

    def run(self):
        """Run the interactive menu system."""
        print("\n" + "=" * 70)
        print(f"{'WELCOME TO LIBRARY MANAGEMENT SYSTEM':^70}")
        print(f"{'Demonstrating OOP Principles':^70}")
        print("=" * 70)

        while True:
            print("\n" + "-" * 70)
            print("MAIN MENU")
            print("-" * 70)
            print("1.  Create Library")
            print("2.  Add Physical Book")
            print("3.  Add Digital Book")
            print("4.  Borrow Book")
            print("5.  Return Book")
            print("6.  Search Books")
            print("7.  List Books")
            print("8.  View Book Details")
            print("9.  View Member's Books")
            print("10. View Library Info")
            print("11. Exit")
            print("-" * 70)

            choice = input("Enter your choice (1-11): ").strip()

            if choice == '1':
                self.create_library()
            elif choice == '2':
                self.add_physical_book()
            elif choice == '3':
                self.add_digital_book()
            elif choice == '4':
                self.borrow_book()
            elif choice == '5':
                self.return_book()
            elif choice == '6':
                self.search_books()
            elif choice == '7':
                self.list_books()
            elif choice == '8':
                self.view_book_details()
            elif choice == '9':
                self.view_member_books()
            elif choice == '10':
                if self.library:
                    self.library.display_library_info()
                else:
                    print("[ERROR] Please create a library first!")
            elif choice == '11':
                print("\n" + "=" * 70)
                print(f"{'THANK YOU FOR USING THE LIBRARY SYSTEM!':^70}")
                print(f"{'Goodbye!':^70}")
                print("=" * 70 + "\n")
                sys.exit(0)
            else:
                print("[ERROR] Invalid choice! Please enter a number between 1 and 11.")

            input("\nPress Enter to continue...")


# ============================================================================
# Program Entry Point
# ============================================================================

if __name__ == "__main__":
    # Check if user wants interactive mode or demo mode
    print("\n" + "=" * 70)
    print(f"{'LIBRARY MANAGEMENT SYSTEM':^70}")
    print("=" * 70)
    print("\n1. Interactive Mode (Full Menu System)")
    print("2. Demo Mode (See Examples)")

    mode = input("\nSelect mode (1 or 2): ").strip()

    if mode == '1':
        # Run interactive system
        system = LibraryManagementSystem()
        system.run()
    else:
        # Run demonstration
        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATION MODE':^70}")
        print("=" * 70)

        # Create library
        print("\n>>> Creating City Central Library...")
        library = Library("City Central Library", "123 Main Street, Downtown")
        library.display_library_info()

        # Add physical books
        print("\n>>> Adding physical books...")
        book1 = Book("BK00001", "The Great Gatsby", "F. Scott Fitzgerald", 1925,
                     "9780743273565", 180, "Classic Fiction")
        book2 = Book("BK00002", "1984", "George Orwell", 1949,
                     "9780451524935", 328, "Dystopian Fiction")
        book3 = Book("BK00003", "To Kill a Mockingbird", "Harper Lee", 1960,
                     "9780061120084", 324, "Classic Fiction")

        library.add_book(book1)
        library.add_book(book2)
        library.add_book(book3)
        print("    Added 3 physical books")

        # Add digital books
        print("\n>>> Adding digital books...")
        ebook1 = DigitalBook("BK00004", "Clean Code", "Robert C. Martin", 2008,
                             "9780132350884", 464, "Programming", "PDF", 5.2,
                             "http://library.example.com/cleancode.pdf")
        ebook2 = DigitalBook("BK00005", "The Pragmatic Programmer", "Andrew Hunt", 1999,
                             "9780201616224", 352, "Programming", "EPUB", 3.8,
                             "http://library.example.com/pragmatic.epub")

        library.add_book(ebook1)
        library.add_book(ebook2)
        print("    Added 2 digital books")

        # Borrow books
        print("\n>>> Borrowing books...")
        try:
            library.borrow_book("BK00001", "Alice Johnson", 14)
            print("    Alice borrowed 'The Great Gatsby'")

            library.borrow_book("BK00002", "Bob Smith", 14)
            print("    Bob borrowed '1984'")

            # Digital book - unlimited copies
            library.borrow_book("BK00004", "Charlie Brown", 7)
            print("    Charlie downloaded 'Clean Code' (digital)")

            library.borrow_book("BK00004", "Diana Prince", 7)
            print("    Diana also downloaded 'Clean Code' (unlimited copies)")

        except ValueError as e:
            print(f"    [ERROR] {e}")

        # List available books
        print("\n>>> Listing available books...")
        available = library.list_available_books()
        print(f"    Found {len(available)} available book(s):")
        for book in available:
            print(f"    - {book.title} by {book.author}")

        # POLYMORPHISM demonstration
        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATING POLYMORPHISM':^70}")
        print("=" * 70)
        print("\nDisplaying different book types (polymorphic behavior):")

        book1.display_info()
        ebook1.display_info()

        # Return a book
        print("\n>>> Returning '1984'...")
        try:
            is_overdue = library.return_book("BK00002")
            if is_overdue:
                print("    Book was returned OVERDUE")
            else:
                print("    Book was returned on time")
        except ValueError as e:
            print(f"    [ERROR] {e}")

        # Search functionality
        print("\n>>> Searching for books by 'Fitzgerald'...")
        results = library.find_books_by_author("Fitzgerald")
        print(f"    Found {len(results)} book(s)")

        # Display final library info
        library.display_library_info()

        print("\n" + "=" * 70)
        print(f"{'DEMONSTRATION COMPLETED':^70}")
        print("=" * 70 + "\n")