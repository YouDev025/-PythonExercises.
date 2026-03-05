# =============================================================================
# Interactive Memory Optimization Analyzer
# Analyzes a user-supplied list of numbers, removes duplicates, and reports
# memory usage before and after optimization using sys.getsizeof().
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================

import sys


# ── Input helpers ─────────────────────────────────────────────────────────────

def parse_numbers(raw):
    """
    Parse a whitespace/comma-separated string into a list of floats.

    Returns (numbers, errors) where errors is a list of tokens that
    could not be converted, so the caller can decide how to handle them.
    """
    # Split on commas and whitespace, then try to cast each token
    tokens  = raw.replace(",", " ").split()
    numbers = []
    errors  = []

    for token in tokens:
        try:
            numbers.append(float(token))
        except ValueError:
            errors.append(token)   # Keep track of bad tokens

    return numbers, errors


def get_numbers_input():
    """
    Prompt the user until at least one valid number is entered.

    Returns a list of floats.
    """
    while True:
        raw = input("  Enter numbers (space or comma-separated): ").strip()
        if not raw:
            print("  [!] Input cannot be empty. Please try again.")
            continue

        numbers, errors = parse_numbers(raw)

        if errors:
            print(f"  [!] Skipped non-numeric tokens: {errors}")

        if not numbers:
            print("  [!] No valid numbers found. Please try again.")
            continue

        return numbers


# ── Core analysis functions ───────────────────────────────────────────────────

def memory_usage(data_structure):
    """
    Return the shallow memory footprint of a data structure in bytes.

    Uses sys.getsizeof(), which measures the container object itself
    (not the memory of every element it holds).
    """
    return sys.getsizeof(data_structure)


def remove_duplicates(data_list):
    """
    Remove duplicate values from a list while preserving insertion order.

    Algorithm:
      1. Iterate through each element.
      2. Track seen values in a set for O(1) look-up.
      3. Append only the first occurrence to the result list.

    Returns a dict with:
      - unique_list      : deduplicated list (order preserved)
      - unique_set       : set of unique values (for compressed form)
      - duplicates_count : how many duplicate entries were removed
      - frequency        : dict mapping each value → occurrence count
    """
    seen       = set()       # Fast membership check
    unique     = []          # Result list with order preserved
    frequency  = {}          # Optional frequency counter

    for item in data_list:
        # Count every occurrence regardless of duplication
        frequency[item] = frequency.get(item, 0) + 1

        if item not in seen:
            seen.add(item)
            unique.append(item)  # First time we've seen this value

    duplicates_count = len(data_list) - len(unique)

    return {
        "unique_list"      : unique,
        "unique_set"       : seen,          # Already built as a by-product
        "duplicates_count" : duplicates_count,
        "frequency"        : frequency,
    }


# ── Display helpers ───────────────────────────────────────────────────────────

def fmt_list(lst, max_items=20):
    """Return a compact string representation, truncating long lists."""
    if len(lst) <= max_items:
        return str(lst)
    shown = lst[:max_items]
    return f"{shown}  ... (+{len(lst) - max_items} more)"


def display_list(state):
    """Print the currently stored list, or a notice if none exists."""
    if not state["data"]:
        print("\n  [!] No data loaded. Please enter numbers first (Option 1).")
        return

    print("\n── Current List ────────────────────────────────────────")
    print(f"  Items  : {len(state['data'])}")
    print(f"  Values : {fmt_list(state['data'])}")
    print(f"  Memory : {memory_usage(state['data'])} bytes")
    print()


def display_optimization_report(state):
    """Run deduplication and print a side-by-side memory report."""
    if not state["data"]:
        print("\n  [!] No data loaded. Please enter numbers first (Option 1).")
        return

    data   = state["data"]
    result = remove_duplicates(data)

    mem_before = memory_usage(data)
    mem_after  = memory_usage(result["unique_list"])
    saved      = mem_before - mem_after

    print("\n── Memory Optimization Report ──────────────────────────")
    print(f"  Original list length   : {len(data)}")
    print(f"  Optimized list length  : {len(result['unique_list'])}")
    print(f"  Duplicates removed     : {result['duplicates_count']}")
    print("─" * 55)
    print(f"  Original memory usage  : {mem_before} bytes")
    print(f"  Optimized memory usage : {mem_after} bytes")
    if saved > 0:
        print(f"  Memory saved           : {saved} bytes  ✔")
    elif saved == 0:
        print("  Memory saved           : 0 bytes  (no duplicates found)")
    else:
        # Very small lists can have identical or inverted sizes due to
        # Python's internal list over-allocation; we report 0 in that case.
        print("  Memory saved           : 0 bytes  (list overhead unchanged)")
    print()

    # Cache the result so the compress option can reuse it
    state["last_result"] = result


def display_compression(state):
    """Show memory comparison across list, set, and optimized-list forms."""
    if not state["data"]:
        print("\n  [!] No data loaded. Please enter numbers first (Option 1).")
        return

    data   = state["data"]

    # Reuse cached result if available, otherwise compute fresh
    if state.get("last_result") is None:
        state["last_result"] = remove_duplicates(data)

    result       = state["last_result"]
    unique_list  = result["unique_list"]
    unique_set   = result["unique_set"]

    mem_list     = memory_usage(data)
    mem_opt_list = memory_usage(unique_list)
    mem_set      = memory_usage(unique_set)

    print("\n── Compression Comparison ──────────────────────────────")
    print(f"  {'Structure':<28}  {'Items':>6}  {'Bytes':>8}")
    print("  " + "─" * 48)
    print(f"  {'Original list':<28}  {len(data):>6}  {mem_list:>8} bytes")
    print(f"  {'Deduplicated list (ordered)':<28}  {len(unique_list):>6}  {mem_opt_list:>8} bytes")
    print(f"  {'Set (unordered, unique)':<28}  {len(unique_set):>6}  {mem_set:>8} bytes")
    print()

    # Recommend the most compact option
    best_mem  = min(mem_opt_list, mem_set)
    best_name = "deduplicated list" if mem_opt_list <= mem_set else "set"
    print(f"  ✔ Most compact structure: {best_name} ({best_mem} bytes)")
    print()


def display_frequency(state):
    """Print a frequency table for every value in the original list."""
    if not state["data"]:
        print("\n  [!] No data loaded. Please enter numbers first (Option 1).")
        return

    if state.get("last_result") is None:
        state["last_result"] = remove_duplicates(state["data"])

    freq = state["last_result"]["frequency"]

    print("\n── Value Frequency Table ───────────────────────────────")
    print(f"  {'Value':>12}   {'Count':>6}   {'Duplicates':>10}")
    print("  " + "─" * 38)

    # Sort by descending count so the most-repeated values appear first
    for value, count in sorted(freq.items(), key=lambda x: -x[1]):
        dups = count - 1   # Occurrences beyond the first are duplicates
        print(f"  {value:>12}   {count:>6}   {dups:>10}")
    print()


# ── Menu ──────────────────────────────────────────────────────────────────────

def show_menu():
    """Print the main menu and return a validated choice string."""
    print("╔══════════════════════════════════════════════════╗")
    print("║     Interactive Memory Optimization Analyzer     ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  1. Enter a list of numbers                      ║")
    print("║  2. Display the list                             ║")
    print("║  3. Remove duplicates & show memory savings      ║")
    print("║  4. Show memory usage before and after           ║")
    print("║  5. Compress data structure (list → set / dedup) ║")
    print("║  6. Show value frequency table                   ║")
    print("║  7. Exit                                         ║")
    print("╚══════════════════════════════════════════════════╝")

    while True:
        choice = input("  Choose an option [1-7]: ").strip()
        if choice in {"1", "2", "3", "4", "5", "6", "7"}:
            return choice
        print("  [!] Invalid choice. Enter a number from 1 to 7.")


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    """
    Program entry point.

    All mutable state lives in a single dictionary so no global variables
    or classes are needed.
    """
    # Shared state dictionary — persists data across menu selections
    state = {
        "data"        : [],    # Current list of numbers entered by the user
        "last_result" : None,  # Cached deduplication result
    }

    print("\nWelcome to the Interactive Memory Optimization Analyzer!\n")

    while True:
        print()
        choice = show_menu()

        if choice == "1":
            # Collect a fresh list of numbers from the user
            print("\n── Enter Numbers ──────────────────────────────────────")
            state["data"]        = get_numbers_input()
            state["last_result"] = None   # Invalidate any cached analysis
            print(f"  [✔] {len(state['data'])} number(s) stored successfully.")

        elif choice == "2":
            display_list(state)

        elif choice == "3":
            # Deduplicate and report memory savings
            display_optimization_report(state)

        elif choice == "4":
            # Side-by-side before/after memory sizes
            if not state["data"]:
                print("\n  [!] No data loaded. Please enter numbers first (Option 1).")
            else:
                data        = state["data"]
                result      = remove_duplicates(data)
                state["last_result"] = result

                mem_before  = memory_usage(data)
                mem_after   = memory_usage(result["unique_list"])
                saved       = max(mem_before - mem_after, 0)

                print("\n── Memory Usage Summary ────────────────────────────")
                print(f"  Original memory usage  : {mem_before} bytes")
                print(f"  Optimized memory usage : {mem_after} bytes")
                print(f"  Duplicates removed     : {result['duplicates_count']}")
                print(f"  Memory saved           : {saved} bytes")
                print()

        elif choice == "5":
            display_compression(state)

        elif choice == "6":
            display_frequency(state)

        elif choice == "7":
            print("\n  Goodbye! Thanks for using the Memory Optimization Analyzer.\n")
            break


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()