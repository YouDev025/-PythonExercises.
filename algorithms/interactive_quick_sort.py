# ============================================================
# Interactive Quick Sort Algorithm
# A menu-driven program that sorts a list of numbers using
# Quick Sort (in-place, Lomuto scheme). It tracks comparisons,
# recursive calls, pivot history, and benchmarks against
# Bubble Sort so you can see the performance difference.
# ------------------------------------------------------------
# Author  : Claude (Anthropic)
# Version : 1.0
# ============================================================

import time
import copy
import random

# ─────────────────────────────────────────────────────────────
#  GLOBAL STATS  (lists so nested functions can mutate them)
# ─────────────────────────────────────────────────────────────
comparisons     = [0]
recursive_calls = [0]
pivot_history   = []          # list of (pivot_value, low, high)


def reset_stats():
    comparisons[0]     = 0
    recursive_calls[0] = 0
    pivot_history.clear()


# ═════════════════════════════════════════════════════════════
#  UTILITY HELPERS
# ═════════════════════════════════════════════════════════════

def print_separator(char="─", width=56):
    print(char * width)


def print_header(title):
    print_separator("═")
    print(f"  {title}")
    print_separator("═")


def get_valid_number(prompt):
    """Accept an integer or float; keep asking until input is valid."""
    while True:
        raw = input(prompt).strip()
        try:
            # Accept int if possible, else float
            val = int(raw) if "." not in raw else float(raw)
            return val
        except ValueError:
            print("  ✗  Not a valid number. Try again.")


def get_positive_int(prompt, min_val=1, max_val=9999):
    """Return a validated integer in [min_val, max_val]."""
    while True:
        raw = input(prompt).strip()
        if raw.lstrip("-").isdigit():
            val = int(raw)
            if min_val <= val <= max_val:
                return val
        print(f"  ✗  Enter a whole number between {min_val} and {max_val}.")


def bar_chart(label, value, total, width=30):
    """Render a simple ASCII progress bar for visual comparison."""
    filled = int((value / total) * width) if total else 0
    bar    = "█" * filled + "░" * (width - filled)
    return f"  {label:<14} [{bar}]  {value:,}"


# ═════════════════════════════════════════════════════════════
#  PIVOT STRATEGIES
# ═════════════════════════════════════════════════════════════

PIVOT_STRATEGIES = {
    "1": "Last element",
    "2": "First element",
    "3": "Middle element",
    "4": "Median-of-three",
    "5": "Random element",
}


def choose_pivot_index(arr, low, high, strategy):
    """
    Return the index of the chosen pivot element.
    The pivot is then swapped to arr[high] before partitioning
    so the Lomuto scheme always reads arr[high] as pivot.
    """
    if strategy == "1":                          # last
        return high
    elif strategy == "2":                        # first
        return low
    elif strategy == "3":                        # middle
        return (low + high) // 2
    elif strategy == "4":                        # median-of-three
        mid = (low + high) // 2
        triple = sorted([(arr[low], low), (arr[mid], mid), (arr[high], high)],
                        key=lambda x: x[0])
        return triple[1][1]
    else:                                        # random
        return random.randint(low, high)


# ═════════════════════════════════════════════════════════════
#  LOMUTO PARTITION  (in-place)
# ═════════════════════════════════════════════════════════════

def partition(arr, low, high, strategy):
    """
    Lomuto in-place partition scheme.

    1. Choose a pivot using the selected strategy and swap it to arr[high].
    2. Walk index i from low-1; whenever arr[j] <= pivot, increment i
       and swap arr[i] with arr[j].
    3. Finally place the pivot between the two partitions.

    All comparisons are counted here.
    """
    # ── Pick pivot and move it to the end ────────────────────
    pivot_idx = choose_pivot_index(arr, low, high, strategy)
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]

    pivot = arr[high]
    pivot_history.append((pivot, low, high))    # record for display

    i = low - 1   # boundary of the "smaller" partition

    for j in range(low, high):
        comparisons[0] += 1
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]    # grow the smaller partition

    # ── Place pivot in its final sorted position ─────────────
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1   # pivot's final index


# ═════════════════════════════════════════════════════════════
#  QUICK SORT  (recursive, in-place, Lomuto)
# ═════════════════════════════════════════════════════════════

def quick_sort(arr, low, high, strategy="1"):
    """
    Divide-and-conquer sort.

    Divide   : partition() splits arr[low..high] around a pivot.
    Conquer  : recursively sort the sub-array left of the pivot
               and the sub-array right of the pivot.
    Combine  : nothing to merge – the in-place partition means
               the array is sorted once all calls return.
    """
    recursive_calls[0] += 1

    if low < high:
        # Find pivot's final position
        pivot_pos = partition(arr, low, high, strategy)

        # ── Recurse on the left partition (elements < pivot) ──
        quick_sort(arr, low, pivot_pos - 1, strategy)

        # ── Recurse on the right partition (elements > pivot) ─
        quick_sort(arr, pivot_pos + 1, high, strategy)


# ═════════════════════════════════════════════════════════════
#  BUBBLE SORT  (for comparison only)
# ═════════════════════════════════════════════════════════════

def bubble_sort(arr):
    """Standard O(n²) Bubble Sort; returns (sorted_copy, comparisons)."""
    a   = list(arr)
    n   = len(a)
    cmp = 0
    for i in range(n):
        for j in range(0, n - i - 1):
            cmp += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a, cmp


# ═════════════════════════════════════════════════════════════
#  MENU ACTIONS
# ═════════════════════════════════════════════════════════════

# The working list lives here so every action shares it
the_list = []


def action_enter_elements():
    """Option 1 – enter numbers into the list."""
    print_header("ENTER ELEMENTS")
    print("  Type numbers one per line.  Press Enter on a blank line to finish.\n")

    new_items = []
    while True:
        raw = input(f"  Element {len(new_items) + 1}: ").strip()
        if raw == "":
            if not new_items:
                print("  ✗  You must enter at least one number.")
                continue
            break
        try:
            val = int(raw) if "." not in raw else float(raw)
            new_items.append(val)
        except ValueError:
            print("  ✗  Not a valid number – skipped.")

    mode = input("\n  (A)ppend to existing list or (R)eplace it? [A/R]: ").strip().upper()
    if mode == "R":
        the_list.clear()

    the_list.extend(new_items)
    print(f"\n  ✓  {len(new_items)} element(s) added.  List now has {len(the_list)} element(s).")
    print_separator()


def action_display_list():
    """Option 2 – show the current (unsorted) list."""
    print_header("CURRENT LIST")
    if not the_list:
        print("  (empty – use option 1 to add elements)")
    else:
        print(f"  Size : {len(the_list)}")
        print(f"  Data : {the_list}")

        # quick stats
        print(f"\n  Min  : {min(the_list)}")
        print(f"  Max  : {max(the_list)}")
        avg = sum(the_list) / len(the_list)
        print(f"  Avg  : {avg:.2f}")
    print_separator()


def action_sort():
    """Option 3 – sort with Quick Sort using the chosen pivot strategy."""
    print_header("QUICK SORT")
    if not the_list:
        print("  ✗  List is empty.  Add elements first (option 1).")
        print_separator()
        return

    # ── Choose pivot strategy ─────────────────────────────────
    print("  Pivot strategy:")
    for k, v in PIVOT_STRATEGIES.items():
        print(f"    {k}.  {v}")
    strategy = input("\n  Choose [1-5] (default 1): ").strip() or "1"
    if strategy not in PIVOT_STRATEGIES:
        strategy = "1"

    print(f"\n  Strategy : {PIVOT_STRATEGIES[strategy]}")
    print(f"  Before   : {the_list}\n")

    # Work on a fresh copy so the original is preserved for display
    work = list(the_list)
    reset_stats()

    start = time.perf_counter()
    quick_sort(work, 0, len(work) - 1, strategy)
    elapsed = (time.perf_counter() - start) * 1000   # ms

    # Overwrite the_list in-place with sorted values
    the_list[:] = work

    # ── Show pivot history ────────────────────────────────────
    if len(pivot_history) <= 20:
        print("  Pivot trace (pivot | sub-array range):")
        for step, (pv, lo, hi) in enumerate(pivot_history, 1):
            print(f"    Step {step:>2}:  pivot={pv}  [{lo}..{hi}]")
    else:
        print(f"  (Pivot trace suppressed – {len(pivot_history)} pivots chosen)")

    # ── Results ───────────────────────────────────────────────
    print(f"\n  After    : {the_list}")
    print(f"\n  ── Performance ──────────────────────────────────")
    print(f"  Comparisons     : {comparisons[0]:,}")
    print(f"  Recursive calls : {recursive_calls[0]:,}")
    print(f"  Time elapsed    : {elapsed:.4f} ms")
    print_separator()


def action_display_sorted():
    """Option 4 – display the sorted list (same as current list after sorting)."""
    print_header("SORTED LIST")
    if not the_list:
        print("  (empty – use option 1 to add elements)")
    else:
        print(f"  Size : {len(the_list)}")
        print(f"  Data : {the_list}")
    print_separator()


def action_benchmark():
    """Option 5 – compare Quick Sort vs Bubble Sort performance."""
    print_header("BENCHMARK  ──  Quick Sort  vs  Bubble Sort")

    size = get_positive_int("  How many random integers to generate? [10–5000]: ", 10, 5000)
    sample = [random.randint(-9999, 9999) for _ in range(size)]

    print(f"\n  Array size : {size}")
    print(f"  Sample     : {sample[:8]}{'...' if size > 8 else ''}\n")

    # ── Quick Sort ─────────────────────────────────────────────
    qs_arr = list(sample)
    reset_stats()
    t0 = time.perf_counter()
    quick_sort(qs_arr, 0, len(qs_arr) - 1, "1")
    qs_time = (time.perf_counter() - t0) * 1000
    qs_cmp  = comparisons[0]

    # ── Bubble Sort ────────────────────────────────────────────
    t0 = time.perf_counter()
    bs_arr, bs_cmp = bubble_sort(sample)
    bs_time = (time.perf_counter() - t0) * 1000

    # ── Verify both produced the same output ───────────────────
    assert qs_arr == bs_arr, "Sort mismatch!"

    # ── Display ────────────────────────────────────────────────
    max_cmp  = max(qs_cmp, bs_cmp) or 1
    max_time = max(qs_time, bs_time) or 1

    print("  Comparisons:")
    print(bar_chart("Quick Sort", qs_cmp, max_cmp))
    print(bar_chart("Bubble Sort", bs_cmp, max_cmp))

    print("\n  Time (ms):")
    print(bar_chart("Quick Sort", round(qs_time, 4), max_time))
    print(bar_chart("Bubble Sort", round(bs_time, 4), max_time))

    if bs_cmp > 0:
        cmp_ratio  = bs_cmp  / qs_cmp  if qs_cmp  else float("inf")
        time_ratio = bs_time / qs_time if qs_time else float("inf")
        print(f"\n  Quick Sort made {cmp_ratio:.1f}× fewer comparisons")
        print(f"  Quick Sort was  {time_ratio:.1f}× faster")

    print_separator()


def action_clear_list():
    """Option 6 – wipe the working list."""
    confirm = input("  Clear the entire list? [y/N]: ").strip().lower()
    if confirm == "y":
        the_list.clear()
        print("  ✓  List cleared.")
    else:
        print("  Cancelled.")
    print_separator()


# ═════════════════════════════════════════════════════════════
#  MAIN MENU
# ═════════════════════════════════════════════════════════════

MENU = """
  ╔══════════════════════════════════════════════╗
  ║    Interactive Quick Sort Algorithm  v1.0    ║
  ╠══════════════════════════════════════════════╣
  ║  1.  Enter elements into the list            ║
  ║  2.  Display current list                    ║
  ║  3.  Sort list with Quick Sort               ║
  ║  4.  Display sorted list                     ║
  ║  5.  Benchmark  (Quick Sort vs Bubble Sort)  ║
  ║  6.  Clear list                              ║
  ║  7.  Exit                                    ║
  ╚══════════════════════════════════════════════╝"""

ACTIONS = {
    "1": action_enter_elements,
    "2": action_display_list,
    "3": action_sort,
    "4": action_display_sorted,
    "5": action_benchmark,
    "6": action_clear_list,
}


def main():
    while True:
        print(MENU)
        n = len(the_list)
        status = f"  List: {n} element(s)" + (f"  →  {the_list[:6]}{'...' if n > 6 else ''}" if n else "  (empty)")
        print(status)
        print()

        choice = input("  Select an option [1-7]: ").strip()

        if choice == "7":
            print("\n  Goodbye! \n")
            break
        elif choice in ACTIONS:
            print()
            ACTIONS[choice]()
            input("\n  Press Enter to return to the menu...")
        else:
            print("  ✗  Invalid choice. Please enter 1–7.\n")


if __name__ == "__main__":
    main()