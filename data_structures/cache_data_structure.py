"""
LRU Cache Implementation (Procedural)
-------------------------------------
This program demonstrates a Least Recently Used (LRU) cache.
It stores key-value pairs with a fixed capacity and evicts the least
recently used item when the cache exceeds capacity.

Author: Youssef Adardour
Date: February 2026
"""

# -------------------------------
# Data Structures
# -------------------------------
capacity = 3
cache = {}          # Dictionary: key -> value
usage_order = []    # List to track usage order (most recent at end)


def get(key):
    """Retrieve value by key and update usage order."""
    if key not in cache:
        print(f"Get({key}) -> Key not found")
        return None
    # Move key to end (most recently used)
    usage_order.remove(key)
    usage_order.append(key)
    print(f"Get({key}) -> {cache[key]}")
    return cache[key]


def put(key, value):
    """Insert or update a key-value pair with LRU eviction."""
    global cache, usage_order

    if key in cache:
        # Update value and mark as recently used
        cache[key] = value
        usage_order.remove(key)
        usage_order.append(key)
        print(f"Updated key {key} with value {value}")
    else:
        if len(cache) >= capacity:
            # Evict least recently used (first in list)
            lru = usage_order.pop(0)
            evicted_value = cache.pop(lru)
            print(f"Evicted ({lru}: {evicted_value})")
        cache[key] = value
        usage_order.append(key)
        print(f"Inserted ({key}: {value})")


def display():
    """Display current cache content in usage order."""
    print("\n--- Cache Content (LRU order) ---")
    for k in usage_order:
        print(f"{k}: {cache[k]}")
    print("-------------------------------")


# -------------------------------
# Interactive Menu
# -------------------------------
def main():
    while True:
        print("\n--- LRU Cache Menu ---")
        print("1. Put (Insert/Update)")
        print("2. Get (Retrieve)")
        print("3. Display Cache")
        print("4. Exit")

        choice = input("Enter choice (1-4): ").strip()

        if choice == "1":
            key = input("Enter key: ").strip()
            value = input("Enter value: ").strip()
            put(key, value)

        elif choice == "2":
            key = input("Enter key: ").strip()
            get(key)

        elif choice == "3":
            display()

        elif choice == "4":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 4.")


if __name__ == "__main__":
    main()
