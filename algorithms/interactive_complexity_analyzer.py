# =============================================================================
# Interactive Algorithm Complexity Analyzer
# Lets users test Linear Search, Binary Search, and Bubble Sort on their own
# data, counting every comparison and iteration to demonstrate Big-O behavior.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================

import math
import time


# ── Input helpers ─────────────────────────────────────────────────────────────

def parse_numbers(raw):
    """
    Convert a comma/space-separated string into a list of floats.
    Returns (numbers, bad_tokens) so the caller can warn about bad input.
    """
    tokens  = raw.replace(",", " ").split()
    numbers = []
    errors  = []
    for t in tokens:
        try:
            numbers.append(float(t))
        except ValueError:
            errors.append(t)
    return numbers, errors


def get_number_list(prompt="  Enter numbers (space or comma-separated): "):
    """Prompt until the user supplies at least two valid numbers."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            print("  [!] Input cannot be empty.")
            continue
        numbers, errors = parse_numbers(raw)
        if errors:
            print(f"  [!] Skipped non-numeric tokens: {errors}")
        if len(numbers) < 2:
            print("  [!] Please enter at least 2 numbers.")
            continue
        return numbers


def get_single_number(prompt):
    """Prompt until the user enters a single valid number."""
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("  [!] Please enter a valid number.")


# ── Core algorithm functions ──────────────────────────────────────────────────

def linear_search(arr, target):
    """
    Search for *target* in *arr* by checking every element in order.

    Complexity:
      Best case  : O(1)  — target is the first element
      Average    : O(n)  — target is somewhere in the middle
      Worst case : O(n)  — target is last or not present

    Returns a stats dictionary so the caller can display results.
    """
    comparisons = 0   # Count every equality test
    iterations  = 0   # Count every loop cycle
    found_index = -1

    for i in range(len(arr)):
        iterations  += 1
        comparisons += 1          # We compare arr[i] to target

        if arr[i] == target:
            found_index = i
            break                 # Stop on first match (best-case scenario)

    return {
        "algorithm"   : "Linear Search",
        "comparisons" : comparisons,
        "iterations"  : iterations,
        "found"       : found_index != -1,
        "found_index" : found_index,
        "complexity"  : "O(n)",
        "best"        : "O(1)  — target is the first element",
        "average"     : "O(n)  — target is near the middle",
        "worst"       : "O(n)  — target is last or absent",
    }


def binary_search(arr, target):
    """
    Search for *target* in a SORTED copy of *arr* using divide-and-conquer.

    Each iteration halves the search space, so at most ⌈log₂(n)⌉ + 1
    comparisons are needed.

    Complexity:
      Best case  : O(1)     — target is the middle element on the first probe
      Average    : O(log n) — target found after several halvings
      Worst case : O(log n) — target not present; search space exhausted

    Returns a stats dictionary.
    """
    # Binary search requires a sorted array; sort a copy so we don't mutate.
    sorted_arr  = sorted(arr)
    comparisons = 0
    iterations  = 0
    found_index = -1

    low  = 0
    high = len(sorted_arr) - 1

    while low <= high:
        iterations  += 1
        mid          = (low + high) // 2

        comparisons += 1                      # Compare mid element to target
        if sorted_arr[mid] == target:
            found_index = mid
            break
        elif sorted_arr[mid] < target:
            comparisons += 1                  # The elif is also a comparison
            low = mid + 1                     # Discard left half
        else:
            high = mid - 1                    # Discard right half

    theoretical_max = math.ceil(math.log2(len(arr))) + 1 if len(arr) > 1 else 1

    return {
        "algorithm"       : "Binary Search",
        "comparisons"     : comparisons,
        "iterations"      : iterations,
        "found"           : found_index != -1,
        "found_index"     : found_index,
        "complexity"      : "O(log n)",
        "theoretical_max" : theoretical_max,
        "best"            : "O(1)     — target is the midpoint on first probe",
        "average"         : "O(log n) — target found after several halvings",
        "worst"           : "O(log n) — target absent; all halvings exhausted",
        "note"            : "Array was sorted before searching.",
    }


def bubble_sort(arr):
    """
    Sort a COPY of *arr* by repeatedly swapping adjacent out-of-order elements.

    Each full pass bubbles the largest unsorted element to its final position,
    so the algorithm needs at most n-1 passes.

    Complexity:
      Best case  : O(n)   — array already sorted (with early-exit optimisation)
      Average    : O(n²)  — random data
      Worst case : O(n²)  — array sorted in reverse order

    Returns a stats dictionary.
    """
    data        = arr[:]   # Work on a copy; never mutate caller's data
    n           = len(data)
    comparisons = 0
    swaps       = 0
    passes      = 0        # Outer loop iterations

    for i in range(n - 1):
        passes    += 1
        swapped    = False   # Early-exit flag

        # Inner loop: compare each adjacent pair in the unsorted portion
        for j in range(n - i - 1):
            comparisons += 1              # Every adjacent comparison counts

            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
                swaps   += 1
                swapped  = True

        # If no swap happened the array is already sorted — stop early
        if not swapped:
            break

    return {
        "algorithm"   : "Bubble Sort",
        "comparisons" : comparisons,
        "iterations"  : passes,           # Outer-loop passes
        "swaps"       : swaps,
        "sorted_arr"  : data,
        "complexity"  : "O(n²)",
        "best"        : "O(n)  — already sorted (early-exit fires after 1 pass)",
        "average"     : "O(n²) — random order",
        "worst"       : "O(n²) — reverse-sorted input",
    }


# ── Display helpers ───────────────────────────────────────────────────────────

def divider(char="─", width=58):
    print("  " + char * width)


def print_stats(stats):
    """Pretty-print a stats dictionary returned by any algorithm function."""
    divider("═")
    print(f"  Algorithm        : {stats['algorithm']}")
    divider()
    print(f"  Elements         : {stats.get('n', '—')}")
    print(f"  Comparisons      : {stats['comparisons']}")
    print(f"  Iterations       : {stats['iterations']}")
    if "swaps" in stats:
        print(f"  Swaps            : {stats['swaps']}")
    if "theoretical_max" in stats:
        print(f"  Theoretical max  : {stats['theoretical_max']} comparisons  (⌈log₂ n⌉ + 1)")
    divider()
    print(f"  Estimated Complexity : {stats['complexity']}")
    divider()
    print("  Case analysis:")
    print(f"    Best    — {stats['best']}")
    print(f"    Average — {stats['average']}")
    print(f"    Worst   — {stats['worst']}")
    if "note" in stats:
        print(f"  Note: {stats['note']}")
    divider("═")
    print()


def show_found(stats, target):
    """Print a one-line search result after a search algorithm."""
    if stats["found"]:
        print(f"  ✔  Target {target} found at index {stats['found_index']}.")
    else:
        print(f"  ✘  Target {target} not found in the list.")
    print()


# ── Menu actions ──────────────────────────────────────────────────────────────

def run_linear_search(state):
    """Prompt for data + target, run linear search, display stats."""
    print("\n── Linear Search ─────────────────────────────────────────")
    arr    = get_number_list()
    target = get_single_number("  Enter the target value to search for: ")

    stats          = linear_search(arr, target)
    stats["n"]     = len(arr)

    # Save to history for comparison
    state["history"]["linear"] = stats

    print()
    print_stats(stats)
    show_found(stats, target)


def run_binary_search(state):
    """Prompt for data + target, run binary search, display stats."""
    print("\n── Binary Search ─────────────────────────────────────────")
    arr    = get_number_list()
    target = get_single_number("  Enter the target value to search for: ")

    stats          = binary_search(arr, target)
    stats["n"]     = len(arr)

    state["history"]["binary"] = stats

    print()
    print_stats(stats)
    show_found(stats, target)


def run_bubble_sort(state):
    """Prompt for data, run bubble sort, display stats + sorted output."""
    print("\n── Bubble Sort ───────────────────────────────────────────")
    arr = get_number_list()

    stats      = bubble_sort(arr)
    stats["n"] = len(arr)

    state["history"]["bubble"] = stats

    print()
    print_stats(stats)

    # Show sorted result (truncate very long lists)
    sorted_arr = stats["sorted_arr"]
    preview    = sorted_arr[:20]
    suffix     = f"  ... (+{len(sorted_arr)-20} more)" if len(sorted_arr) > 20 else ""
    print(f"  Sorted result: {preview}{suffix}")
    print()


def compare_algorithms(state):
    """
    Side-by-side comparison table of all algorithms run so far.
    Prompts the user to run any that are missing.
    """
    print("\n── Algorithm Comparison ──────────────────────────────────")

    history = state["history"]

    if not any(history.values()):
        print("  [!] No algorithms have been run yet.")
        print("      Please use options 1–3 first, then compare.\n")
        return

    # Table header
    col = 22
    print()
    print(f"  {'Metric':<{col}}  {'Linear Search':>{col}}  {'Binary Search':>{col}}  {'Bubble Sort':>{col}}")
    divider(width=col * 4 + 6)

    rows = [
        ("Elements (n)",   "n"),
        ("Comparisons",    "comparisons"),
        ("Iterations",     "iterations"),
        ("Complexity",     "complexity"),
    ]

    for label, key in rows:
        lin = history.get("linear")
        bin_ = history.get("binary")
        bub = history.get("bubble")

        v_lin  = str(lin[key])  if lin  and key in lin  else "—"
        v_bin  = str(bin_[key]) if bin_ and key in bin_ else "—"
        v_bub  = str(bub[key])  if bub  and key in bub  else "—"

        print(f"  {label:<{col}}  {v_lin:>{col}}  {v_bin:>{col}}  {v_bub:>{col}}")

    divider()
    print()

    # Highlight winner (fewest comparisons) among search algorithms
    search_results = {k: history[k] for k in ("linear", "binary") if history.get(k)}
    if len(search_results) == 2:
        winner = min(search_results, key=lambda k: search_results[k]["comparisons"])
        names  = {"linear": "Linear Search", "binary": "Binary Search"}
        print(f"  ✔ Fewer comparisons for search: {names[winner]}")
        print()

    # Complexity summary
    print("  Complexity summary:")
    print("    Linear Search : O(n)   — scans every element in worst case")
    print("    Binary Search : O(log n) — halves search space each step")
    print("    Bubble Sort   : O(n²)  — nested loops for every pair")
    print()


# ── Main menu ─────────────────────────────────────────────────────────────────

def show_menu():
    """Print the main menu and return a validated choice string."""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        Interactive Algorithm Complexity Analyzer         ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  1. Test Linear Search complexity                        ║")
    print("║  2. Test Binary Search complexity                        ║")
    print("║  3. Test Bubble Sort complexity                          ║")
    print("║  4. Compare all algorithms                               ║")
    print("║  5. Exit                                                 ║")
    print("╚══════════════════════════════════════════════════════════╝")

    while True:
        choice = input("  Choose an option [1-5]: ").strip()
        if choice in {"1", "2", "3", "4", "5"}:
            return choice
        print("  [!] Invalid choice. Enter a number from 1 to 5.")


def main():
    """
    Program entry point.

    State is a plain dictionary — no globals, no classes needed.
    'history' stores the last stats dict for each algorithm so the
    comparison view always reflects the most recent run.
    """
    state = {
        "history": {
            "linear": None,
            "binary": None,
            "bubble": None,
        }
    }

    print("\nWelcome to the Interactive Algorithm Complexity Analyzer!\n")

    while True:
        print()
        choice = show_menu()

        if choice == "1":
            run_linear_search(state)
        elif choice == "2":
            run_binary_search(state)
        elif choice == "3":
            run_bubble_sort(state)
        elif choice == "4":
            compare_algorithms(state)
        elif choice == "5":
            print("\n  Goodbye! Happy analyzing.\n")
            break


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()