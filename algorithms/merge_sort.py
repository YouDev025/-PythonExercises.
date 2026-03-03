# ============================================================
# Interactive Merge Sort Algorithm
# A menu-driven program that sorts a list of numbers using
# Merge Sort. It visualises every split and merge step,
# tracks comparisons and recursive calls, and lets you
# benchmark Merge Sort against Bubble Sort side-by-side.
# ------------------------------------------------------------
# Author  : Claude (Anthropic)
# Version : 1.0
# ============================================================

import time
import random

# ─────────────────────────────────────────────────────────────
#  GLOBAL STATS  (single-element lists so nested functions
#  can mutate them without 'global' or 'nonlocal')
# ─────────────────────────────────────────────────────────────
comparisons     = [0]
recursive_calls = [0]
split_log       = []    # list of str – one entry per divide step
merge_log       = []    # list of str – one entry per merge step


def reset_stats():
    comparisons[0]     = 0
    recursive_calls[0] = 0
    split_log.clear()
    merge_log.clear()


# ═════════════════════════════════════════════════════════════
#  UTILITY HELPERS
# ═════════════════════════════════════════════════════════════

def print_separator(char="─", width=58):
    print(char * width)


def print_header(title):
    print_separator("═")
    print(f"  {title}")
    print_separator("═")


def bar(label, value, ref, width=28):
    """ASCII bar-chart row for the benchmark display."""
    filled = int((value / ref) * width) if ref else 0
    b = "█" * filled + "░" * (width - filled)
    return f"  {label:<14} [{b}]  {value:,}"


# ═════════════════════════════════════════════════════════════
#  MERGE  ──  Conquer / Combine step
# ═════════════════════════════════════════════════════════════

def merge(left, right, verbose=False):
    """
    Merge two sorted sub-arrays into one sorted array.

    ── Conquer / Combine ──────────────────────────────────────
    Compare the front elements of 'left' and 'right' one at a
    time; always take the smaller one.  Whatever remains in
    whichever half is not yet exhausted gets appended as-is
    (it is already sorted).

    Every head-to-head comparison is counted.
    """
    result = []
    i = j  = 0

    # ── Compare heads and build sorted result ─────────────────
    while i < len(left) and j < len(right):
        comparisons[0] += 1
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # ── Append whatever is left (already sorted) ──────────────
    result.extend(left[i:])
    result.extend(right[j:])

    if verbose:
        merge_log.append(
            f"  merge  {str(left):<24} + {str(right):<24}  →  {result}"
        )

    return result


# ═════════════════════════════════════════════════════════════
#  MERGE SORT  ──  Divide step + recursive calls
# ═════════════════════════════════════════════════════════════

def merge_sort(arr, depth=0, verbose=False):
    """
    Recursively sort 'arr' using the divide-and-conquer strategy.

    ── Divide ─────────────────────────────────────────────────
    Split the array in half.  Keep splitting until every
    sub-array contains a single element (a list of one is
    trivially sorted).

    ── Conquer ────────────────────────────────────────────────
    Return single-element arrays as-is (base case).

    ── Combine ────────────────────────────────────────────────
    Call merge() to combine two sorted halves into one sorted
    array, bubbling the result back up the call stack.
    """
    recursive_calls[0] += 1

    # ── Base case: nothing to split ───────────────────────────
    if len(arr) <= 1:
        return arr

    # ── Divide: find the midpoint ─────────────────────────────
    mid   = len(arr) // 2
    left  = arr[:mid]
    right = arr[mid:]

    if verbose:
        indent = "  " * depth
        split_log.append(
            f"  {indent}split  {str(arr):<30}  →  L={left}  R={right}"
        )

    # ── Conquer: recursively sort each half ───────────────────
    left  = merge_sort(left,  depth + 1, verbose)
    right = merge_sort(right, depth + 1, verbose)

    # ── Combine: merge the two sorted halves ──────────────────
    return merge(left, right, verbose)


# ═════════════════════════════════════════════════════════════
#  BUBBLE SORT  (for benchmarking only)
# ═════════════════════════════════════════════════════════════

def bubble_sort(arr):
    """O(n²) Bubble Sort; returns (sorted_copy, comparison_count)."""
    a, cmp = list(arr), 0
    n = len(a)
    for i in range(n):
        for j in range(n - i - 1):
            cmp += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a, cmp


# ═════════════════════════════════════════════════════════════
#  SHARED STATE
# ═════════════════════════════════════════════════════════════

the_list   = []    # working list (unsorted input)
sorted_list = []   # result of the last sort


# ═════════════════════════════════════════════════════════════
#  MENU ACTIONS
# ═════════════════════════════════════════════════════════════

def action_enter_elements():
    """Option 1 – add numbers to the working list."""
    print_header("ENTER ELEMENTS")
    print("  Type one number per line.  Blank line = done.\n")

    new_items = []
    while True:
        raw = input(f"  Element {len(new_items) + 1}: ").strip()
        if raw == "":
            if not new_items:
                print("  ✗  Enter at least one number.")
                continue
            break
        try:
            val = int(raw) if "." not in raw else float(raw)
            new_items.append(val)
        except ValueError:
            print("  ✗  Not a valid number – skipped.")

    mode = input("\n  (A)ppend to current list or (R)eplace it? [A/R]: ").strip().upper()
    if mode == "R":
        the_list.clear()
        sorted_list.clear()

    the_list.extend(new_items)
    print(f"\n  ✓  {len(new_items)} element(s) added.  List now has {len(the_list)} element(s).")
    print_separator()


def action_display_list():
    """Option 2 – show the current unsorted list with basic stats."""
    print_header("CURRENT LIST")
    if not the_list:
        print("  (empty – use option 1 to add elements)")
    else:
        print(f"  Size : {len(the_list)}")
        print(f"  Data : {the_list}")
        print(f"\n  Min  : {min(the_list)}")
        print(f"  Max  : {max(the_list)}")
        print(f"  Avg  : {sum(the_list) / len(the_list):.2f}")
    print_separator()


def action_sort():
    """Option 3 – run Merge Sort with optional step-by-step trace."""
    global sorted_list
    print_header("MERGE SORT")

    if not the_list:
        print("  ✗  List is empty.  Add elements first (option 1).")
        print_separator()
        return

    verbose_in = input("  Show split / merge steps? [y/N]: ").strip().lower()
    verbose    = verbose_in == "y"

    print(f"\n  Before  : {the_list}")

    reset_stats()
    start      = time.perf_counter()
    sorted_list = merge_sort(list(the_list), verbose=verbose)
    elapsed    = (time.perf_counter() - start) * 1000

    # ── Optional step trace ───────────────────────────────────
    if verbose:
        cap = 40   # cap lines to avoid floods on large arrays

        if split_log:
            print(f"\n  ── Split steps ({len(split_log)} total) " + "─" * 20)
            for line in split_log[:cap]:
                print(line)
            if len(split_log) > cap:
                print(f"  … {len(split_log) - cap} more split steps hidden")

        if merge_log:
            print(f"\n  ── Merge steps ({len(merge_log)} total) " + "─" * 20)
            for line in merge_log[:cap]:
                print(line)
            if len(merge_log) > cap:
                print(f"  … {len(merge_log) - cap} more merge steps hidden")

    # ── Summary ───────────────────────────────────────────────
    print(f"\n  After   : {sorted_list}")
    print(f"\n  ── Statistics {'─' * 38}")
    print(f"  Comparisons     : {comparisons[0]:,}")
    print(f"  Recursive calls : {recursive_calls[0]:,}")
    print(f"  Time elapsed    : {elapsed:.4f} ms")
    print_separator()


def action_display_sorted():
    """Option 4 – display the result of the last sort."""
    print_header("SORTED LIST")
    if not sorted_list:
        print("  (no sort has been run yet – use option 3)")
    else:
        print(f"  Size : {len(sorted_list)}")
        print(f"  Data : {sorted_list}")
    print_separator()


def action_benchmark():
    """Option 5 – compare Merge Sort vs Bubble Sort on random data."""
    print_header("BENCHMARK  ──  Merge Sort  vs  Bubble Sort")

    while True:
        raw = input("  Random integers to generate (10 – 5000): ").strip()
        if raw.isdigit() and 10 <= int(raw) <= 5000:
            size = int(raw)
            break
        print("  ✗  Enter a whole number between 10 and 5000.")

    sample = [random.randint(-9999, 9999) for _ in range(size)]
    print(f"\n  Array size : {size}")
    print(f"  Sample     : {sample[:8]}{'...' if size > 8 else ''}\n")

    # Merge Sort
    reset_stats()
    t0    = time.perf_counter()
    ms_result = merge_sort(list(sample))
    ms_time   = (time.perf_counter() - t0) * 1000
    ms_cmp    = comparisons[0]
    ms_calls  = recursive_calls[0]

    # Bubble Sort
    t0 = time.perf_counter()
    bs_result, bs_cmp = bubble_sort(sample)
    bs_time = (time.perf_counter() - t0) * 1000

    assert ms_result == bs_result, "Sort mismatch – this should never happen!"

    ref_cmp  = max(ms_cmp,  bs_cmp)  or 1
    ref_time = max(ms_time, bs_time) or 1

    print("  Comparisons:")
    print(bar("Merge Sort",  ms_cmp, ref_cmp))
    print(bar("Bubble Sort", bs_cmp, ref_cmp))

    print("\n  Time (ms):")
    print(bar("Merge Sort",  round(ms_time, 6), ref_time))
    print(bar("Bubble Sort", round(bs_time, 6), ref_time))

    print(f"\n  Merge Sort recursive calls : {ms_calls:,}")

    if ms_cmp:
        print(f"\n  Merge Sort made {bs_cmp / ms_cmp:.1f}× fewer comparisons")
    if ms_time > 0:
        ratio = bs_time / ms_time
        print(f"  Merge Sort was  {ratio:.1f}× faster")

    print_separator()


def action_clear_list():
    """Option 6 – wipe the working and sorted lists."""
    confirm = input("  Clear the entire list? [y/N]: ").strip().lower()
    if confirm == "y":
        the_list.clear()
        sorted_list.clear()
        print("  ✓  List cleared.")
    else:
        print("  Cancelled.")
    print_separator()


# ═════════════════════════════════════════════════════════════
#  MAIN MENU
# ═════════════════════════════════════════════════════════════

MENU = """
  ╔══════════════════════════════════════════════╗
  ║   Interactive Merge Sort Algorithm  v1.0     ║
  ╠══════════════════════════════════════════════╣
  ║  1.  Enter elements into the list            ║
  ║  2.  Display current list                    ║
  ║  3.  Sort list with Merge Sort               ║
  ║  4.  Display sorted list                     ║
  ║  5.  Benchmark  (Merge Sort vs Bubble Sort)  ║
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
        n      = len(the_list)
        status = (f"  List: {n} element(s)  →  "
                  f"{the_list[:6]}{'...' if n > 6 else ''}" if n
                  else "  List: (empty)")
        print(status)
        print()

        choice = input("  Select an option [1-7]: ").strip()

        if choice == "7":
            print("\n  Goodbye! 👋\n")
            break
        elif choice in ACTIONS:
            print()
            ACTIONS[choice]()
            input("\n  Press Enter to return to the menu...")
        else:
            print("  ✗  Invalid choice. Please enter 1–7.\n")


if __name__ == "__main__":
    main()