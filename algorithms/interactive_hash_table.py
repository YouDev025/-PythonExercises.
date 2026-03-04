# =============================================================================
# Interactive Hash Table Implementation
# This program implements a fixed-size hash table with chaining for collision
# resolution. Users can interactively insert, search, delete, and display
# key-value pairs, while tracking collisions and comparisons in real time.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================


# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────

DEFAULT_SIZE = 11          # A prime number reduces clustering
COLLISION_COUNT = [0]      # Mutable global collision counter


# ─────────────────────────────────────────────
#  Core hash-table functions
# ─────────────────────────────────────────────

def create_table(size=DEFAULT_SIZE):
    """
    Initialise and return a hash table as a list of empty bucket lists.
    Each bucket will hold (key, value) tuples (chaining).
    """
    return [[] for _ in range(size)]


def hash_function(key, size):
    """
    Compute a bucket index for the given string key.

    Algorithm: sum every character's ASCII value, then take modulo table_size.
        index = ( ord(c₀) + ord(c₁) + … ) % size

    Returns the integer index in [0, size).
    """
    return sum(ord(ch) for ch in str(key)) % size


def insert(table, key, value):
    """
    Insert or update a key-value pair in the hash table.

    Steps
    ─────
    1. Compute the bucket index with hash_function.
    2. If the bucket already contains an entry with the same key → update it.
    3. Otherwise append a new (key, value) tuple.
    4. If the bucket was non-empty before insertion → count it as a collision.

    Returns
    ───────
    (index, is_update, is_collision)
    """
    size       = len(table)
    index      = hash_function(key, size)
    bucket     = table[index]
    is_update  = False
    is_collision = False

    # Check for an existing entry with the same key (update path)
    for i, (k, _) in enumerate(bucket):
        if k == key:
            bucket[i] = (key, value)
            is_update = True
            return index, is_update, False      # update never counts as collision

    # New key — collision if bucket already has at least one entry
    if bucket:
        is_collision = True
        COLLISION_COUNT[0] += 1

    bucket.append((key, value))
    return index, is_update, is_collision


def search(table, key):
    """
    Look up a key in the hash table.

    Returns
    ───────
    (value, index, comparisons)
        value       – the stored value, or None if not found
        index       – the bucket index that was checked
        comparisons – number of key comparisons made inside the bucket
    """
    size        = len(table)
    index       = hash_function(key, size)
    bucket      = table[index]
    comparisons = 0

    for k, v in bucket:
        comparisons += 1
        if k == key:
            return v, index, comparisons

    return None, index, comparisons


def delete(table, key):
    """
    Remove a key-value pair from the hash table.

    Returns
    ───────
    (deleted: bool, index: int, comparisons: int)
        deleted     – True if the key was found and removed
        index       – the bucket index that was checked
        comparisons – number of key comparisons made
    """
    size        = len(table)
    index       = hash_function(key, size)
    bucket      = table[index]
    comparisons = 0

    for i, (k, _) in enumerate(bucket):
        comparisons += 1
        if k == key:
            del bucket[i]
            return True, index, comparisons

    return False, index, comparisons


def display_table(table):
    """
    Pretty-print the entire hash table, showing every bucket's contents.
    Empty buckets are shown as '—'.
    """
    size        = len(table)
    total_items = sum(len(b) for b in table)
    load_factor = total_items / size

    print(f"\n  ┌─── Hash Table  (size={size}) ──────────────────────────────────┐")
    print(f"  │  Total items : {total_items}   │   "
          f"Load factor : {load_factor:.2f}   │   "
          f"Collisions : {COLLISION_COUNT[0]}")
    print(f"  ├─────────────────────────────────────────────────────────────┤")

    for i, bucket in enumerate(table):
        if bucket:
            entries = "  →  ".join(f"({k!r}: {v!r})" for k, v in bucket)
            chain   = f"[{entries}]"
            clash   = f"  ⚡ {len(bucket)} entries" if len(bucket) > 1 else ""
            print(f"  │  [{i:>2}]  {chain}{clash}")
        else:
            print(f"  │  [{i:>2}]  —")

    print(f"  └─────────────────────────────────────────────────────────────┘\n")


# ─────────────────────────────────────────────
#  Input helpers
# ─────────────────────────────────────────────

def get_non_empty_string(prompt):
    """Keep asking until the user provides a non-blank string."""
    while True:
        raw = input(prompt).strip()
        if raw:
            return raw
        print("  [!] Input cannot be empty. Please try again.")


def get_table_size():
    """Ask the user for a table size; fall back to DEFAULT_SIZE."""
    while True:
        raw = input(
            f"  Enter hash table size (default {DEFAULT_SIZE}, "
            f"prime recommended): "
        ).strip()
        if raw == "":
            return DEFAULT_SIZE
        try:
            size = int(raw)
            if size < 1:
                print("  [!] Size must be at least 1.")
                continue
            return size
        except ValueError:
            print("  [!] Please enter a whole number.")


# ─────────────────────────────────────────────
#  Menu handlers
# ─────────────────────────────────────────────

def menu_insert(table):
    key   = get_non_empty_string("  Key   : ")
    value = get_non_empty_string("  Value : ")

    index, is_update, is_collision = insert(table, key, value)

    print(f"\n  ── Insert ──────────────────────────────────────────")
    print(f"     Key           : {key!r}")
    print(f"     Value         : {value!r}")
    print(f"     Hash index    : hash({key!r}) = "
          f"sum_ascii({sum(ord(c) for c in key)}) % {len(table)} = {index}")

    if is_update:
        print(f"     Status        : ✎  Updated existing key")
    elif is_collision:
        print(f"     Status        : ⚡ Collision at index {index}  "
              f"(chained)")
        print(f"     Total collisions so far : {COLLISION_COUNT[0]}")
    else:
        print(f"     Status        : ✓  Inserted into empty bucket")
    print()


def menu_search(table):
    key = get_non_empty_string("  Key to search: ")

    value, index, comparisons = search(table, key)

    print(f"\n  ── Search ──────────────────────────────────────────")
    print(f"     Key           : {key!r}")
    print(f"     Hash index    : {index}")
    print(f"     Comparisons   : {comparisons}")

    if value is not None:
        print(f"     Result        : ✓  Found  →  {value!r}")
    else:
        print(f"     Result        : ✗  Key not found")
    print()


def menu_delete(table):
    key = get_non_empty_string("  Key to delete: ")

    deleted, index, comparisons = delete(table, key)

    print(f"\n  ── Delete ──────────────────────────────────────────")
    print(f"     Key           : {key!r}")
    print(f"     Hash index    : {index}")
    print(f"     Comparisons   : {comparisons}")

    if deleted:
        print(f"     Result        : ✓  Key deleted successfully")
    else:
        print(f"     Result        : ✗  Key not found — nothing deleted")
    print()


# ─────────────────────────────────────────────
#  Main menu loop
# ─────────────────────────────────────────────

MENU = """
  ╔══════════════════════════════════════════════════╗
  ║       Interactive Hash Table Implementation      ║
  ╠══════════════════════════════════════════════════╣
  ║  1.  Insert key-value pair                       ║
  ║  2.  Search for a key                            ║
  ║  3.  Delete a key                                ║
  ║  4.  Display hash table                          ║
  ║  5.  Exit                                        ║
  ╚══════════════════════════════════════════════════╝"""


def main():
    print(MENU)

    print("\n  ── Initialisation ──────────────────────────────────")
    size  = get_table_size()
    table = create_table(size)
    print(f"  [+] Hash table created with {size} buckets.\n")

    while True:
        choice = input("  Select option (1-5): ").strip()
        print()

        if choice == "1":
            menu_insert(table)

        elif choice == "2":
            menu_search(table)

        elif choice == "3":
            menu_delete(table)

        elif choice == "4":
            display_table(table)

        elif choice == "5":
            print("  Goodbye!\n")
            break

        else:
            print("  [!] Invalid choice. Please enter a number from 1 to 5.\n")


if __name__ == "__main__":
    main()