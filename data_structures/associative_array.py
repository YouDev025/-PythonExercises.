"""
Associative Array Implementation (Procedural)
---------------------------------------------
This program demonstrates a custom implementation of an associative array
(hash table) using lists as the underlying storage. It supports put, get,
remove, and display operations with collision handling.

Author: Youssef Adardour
Date: February 2026
"""

# -------------------------------
# Data Structures
# -------------------------------
capacity = 10
table = [[] for _ in range(capacity)]
collisions = 0


def _hash(key):
    """Simple hash function: sum of character codes modulo capacity."""
    return sum(ord(c) for c in str(key)) % capacity


def put(key, value):
    """Insert or update a key-value pair."""
    global collisions
    index = _hash(key)
    bucket = table[index]

    for i, (k, v) in enumerate(bucket):
        if k == key:
            bucket[i] = (key, value)
            print(f"Updated key '{key}' with value '{value}'")
            return

    if bucket:  # Collision occurred
        collisions += 1
        print(f"Collision detected at index {index} for key '{key}'")

    bucket.append((key, value))
    print(f"Inserted ({key}: {value}) at index {index}")


def get(key):
    """Retrieve value by key."""
    index = _hash(key)
    bucket = table[index]

    for k, v in bucket:
        if k == key:
            print(f"Get({key}) -> {v}")
            return v

    print(f"Get({key}) -> Key not found")
    return None


def remove(key):
    """Remove key-value pair by key."""
    index = _hash(key)
    bucket = table[index]

    for i, (k, v) in enumerate(bucket):
        if k == key:
            del bucket[i]
            print(f"Removed key '{key}' from index {index}")
            return

    print(f"Remove({key}) -> Key not found")


def display():
    """Display current table content."""
    print("\n--- Hash Table Content ---")
    for i, bucket in enumerate(table):
        print(f"Index {i}: {bucket}")
    print(f"Total collisions so far: {collisions}")


# -------------------------------
# Interactive Menu
# -------------------------------
def main():
    while True:
        print("\n--- Associative Array Menu ---")
        print("1. Put (Insert/Update)")
        print("2. Get (Retrieve)")
        print("3. Remove (Delete)")
        print("4. Display Table")
        print("5. Exit")

        choice = input("Enter choice (1-5): ").strip()

        if choice == "1":
            key = input("Enter key: ").strip()
            value = input("Enter value: ").strip()
            put(key, value)

        elif choice == "2":
            key = input("Enter key: ").strip()
            get(key)

        elif choice == "3":
            key = input("Enter key: ").strip()
            remove(key)

        elif choice == "4":
            display()

        elif choice == "5":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    main()
