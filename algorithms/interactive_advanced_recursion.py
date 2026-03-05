# =============================================================================
# Interactive Advanced Recursion Explorer
# Demonstrates four classic recursive algorithms — factorial, Fibonacci,
# Tower of Hanoi, and string permutations — showing results, recursive call
# counts, and step-by-step execution traces so users can learn how recursion
# actually unfolds at runtime.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================


import sys

# Raise the default recursion limit slightly so larger inputs work smoothly.
# Python's default is 1000; we keep it modest to stay safe.
sys.setrecursionlimit(5000)


# ── Shared call-counter helper ────────────────────────────────────────────────

def make_counter():
    """Return a one-element list used as a mutable integer counter.
    Lists are passed by reference, so nested recursive calls can increment
    the same counter without using global variables or classes."""
    return [0]


# ── 1. Factorial ──────────────────────────────────────────────────────────────

def factorial(n, counter, depth=0):
    """
    Recursive factorial: n! = n * (n-1)!

    Base case  : factorial(0) = 1  (and factorial(1) = 1)
    Recursive  : factorial(n) = n * factorial(n-1)

    Each call reduces n by 1, so the call stack grows to depth n before
    the base case is reached and the results multiply back up.

    Arguments:
        n       – non-negative integer
        counter – [int] mutable list used to count every call
        depth   – current recursion depth (for indented trace output)

    Returns the integer n!
    """
    counter[0] += 1                   # Count this call

    indent = "  " * depth             # Visual indentation for trace

    if n <= 1:
        # Base case: stop recursing
        print(f"{indent}factorial({n}) = 1  ← base case")
        return 1

    # Recursive case: call ourselves with n-1
    print(f"{indent}factorial({n}) = {n} × factorial({n - 1})")
    result = n * factorial(n - 1, counter, depth + 1)
    print(f"{indent}factorial({n}) returned {result}")
    return result


# ── 2. Fibonacci ──────────────────────────────────────────────────────────────

def fibonacci(n, counter, memo=None):
    """
    Recursive Fibonacci with memoization.

    Base cases : fib(0) = 0,  fib(1) = 1
    Recursive  : fib(n) = fib(n-1) + fib(n-2)

    Without memoization the naive recursion recomputes fib(k) many times,
    giving O(2^n) calls.  The memo dict makes it O(n) by caching each result
    the first time it is computed.

    Arguments:
        n       – non-negative integer
        counter – [int] call counter
        memo    – dict cache {n: fib(n)}; created on the first call

    Returns the nth Fibonacci number.
    """
    counter[0] += 1

    if memo is None:
        memo = {}       # Initialise cache on the very first call

    # Base cases
    if n == 0:
        return 0
    if n == 1:
        return 1

    # Return cached result if already computed
    if n in memo:
        return memo[n]

    # Recursive case: sum the two preceding numbers
    result  = fibonacci(n - 1, counter, memo) + fibonacci(n - 2, counter, memo)
    memo[n] = result    # Cache before returning
    return result


def fibonacci_sequence(limit, counter):
    """
    Build the Fibonacci sequence up to the nth term by calling fibonacci()
    for each index.  Returns a list of (index, value) pairs.
    """
    sequence = []
    for i in range(limit + 1):
        val = fibonacci(i, counter)
        sequence.append((i, val))
    return sequence


# ── 3. Tower of Hanoi ─────────────────────────────────────────────────────────

def tower_of_hanoi(n, source, target, auxiliary, counter, moves):
    """
    Solve Tower of Hanoi for n disks.

    The classic three-step recursion:
      1. Move the top (n-1) disks from source to auxiliary (using target).
      2. Move the largest disk directly from source to target.
      3. Move the (n-1) disks from auxiliary to target (using source).

    Base case  : n == 0  — nothing to move, return immediately.
    Recursive  : two recursive calls, each with n-1 disks.

    Total moves for n disks = 2^n − 1.

    Arguments:
        n          – number of disks
        source     – peg the disks start on (e.g. 'A')
        target     – peg the disks must end on (e.g. 'C')
        auxiliary  – spare peg (e.g. 'B')
        counter    – [int] call counter
        moves      – list to collect move strings

    Returns nothing; results accumulate in *moves*.
    """
    counter[0] += 1

    if n == 0:
        return   # Base case: no disk to move

    # Step 1: move n-1 disks out of the way onto the auxiliary peg
    tower_of_hanoi(n - 1, source, auxiliary, target, counter, moves)

    # Step 2: move the nth (largest remaining) disk to the target
    move = f"  Move disk {n:>2}  :  {source}  →  {target}"
    moves.append(move)
    print(move)

    # Step 3: move the n-1 disks from auxiliary onto the target
    tower_of_hanoi(n - 1, auxiliary, target, source, counter, moves)


# ── 4. Permutations ───────────────────────────────────────────────────────────

def permutations(s, prefix, result, counter):
    """
    Generate every permutation of string *s* by recursion.

    Base case  : s is empty — *prefix* is a complete permutation; record it.
    Recursive  : for each character c in s, fix c as the next character in
                 the prefix and recurse on the remaining characters.

    The number of permutations of k distinct characters is k! (k-factorial).
    For strings with repeated characters the algorithm still generates all
    arrangements (including duplicates).

    Arguments:
        s       – the remaining (not yet placed) characters
        prefix  – characters placed so far (built up through recursion)
        result  – list that accumulates completed permutations
        counter – [int] call counter

    Returns nothing; completed permutations accumulate in *result*.
    """
    counter[0] += 1

    if len(s) == 0:
        # Base case: nothing left to place — we have a full permutation
        result.append(prefix)
        return

    # Try placing each remaining character in the current position
    for i in range(len(s)):
        chosen    = s[i]                      # Pick the i-th remaining char
        remaining = s[:i] + s[i + 1:]        # Everything else

        # Recurse with the chosen char appended to the prefix
        permutations(remaining, prefix + chosen, result, counter)


# ── Display helpers ───────────────────────────────────────────────────────────

def divider(char="─", width=58):
    print("  " + char * width)


def divider_top():
    divider("═")


def divider_bottom():
    divider("═")


# ── Input helpers ─────────────────────────────────────────────────────────────

def get_positive_integer(prompt, min_val=0, max_val=None):
    """Prompt until the user enters an integer within [min_val, max_val]."""
    while True:
        raw = input(prompt).strip()
        if not raw.isdigit():
            print(f"  [!] Please enter a whole number (≥ {min_val}).")
            continue
        value = int(raw)
        if value < min_val:
            print(f"  [!] Value must be at least {min_val}.")
            continue
        if max_val is not None and value > max_val:
            print(f"  [!] Value must be at most {max_val}.")
            continue
        return value


def get_nonempty_string(prompt, max_len=8):
    """Prompt until the user enters a non-empty string within max_len."""
    while True:
        value = input(prompt).strip()
        if not value:
            print("  [!] Input cannot be empty.")
            continue
        if len(value) > max_len:
            print(f"  [!] Please enter at most {max_len} characters "
                  f"(you entered {len(value)}).")
            continue
        return value


# ── Menu actions ──────────────────────────────────────────────────────────────

def action_factorial():
    print("\n── Factorial (Recursion) ───────────────────────────────────")
    n       = get_positive_integer("  Enter n (0–12): ", min_val=0, max_val=12)
    counter = make_counter()

    print()
    divider_top()
    print(f"  Calculating {n}!  —  recursive trace:")
    divider()
    result = factorial(n, counter)
    divider()
    print(f"  Result          : {n}! = {result}")
    print(f"  Recursive calls : {counter[0]}")
    divider_bottom()
    print()


def action_fibonacci():
    print("\n── Fibonacci Sequence (Recursion + Memoization) ───────────")
    n       = get_positive_integer("  Enter how many terms to show (1–40): ", min_val=1, max_val=40)
    counter = make_counter()

    print()
    divider_top()
    print(f"  Fibonacci sequence — first {n + 1} terms (fib(0) … fib({n})):")
    divider()

    sequence = fibonacci_sequence(n, counter)

    # Print in rows of 5 for readability
    row = []
    for idx, val in sequence:
        row.append(f"fib({idx:>2}) = {val}")
        if len(row) == 5:
            print("  " + "   ".join(row))
            row = []
    if row:
        print("  " + "   ".join(row))

    divider()
    print(f"  fib({n}) = {sequence[-1][1]}")
    print(f"  Recursive calls : {counter[0]}  (memoization avoids recomputation)")
    divider_bottom()
    print()


def action_hanoi():
    print("\n── Tower of Hanoi (Recursion) ──────────────────────────────")
    n       = get_positive_integer("  Enter number of disks (1–10): ", min_val=1, max_val=10)
    counter = make_counter()
    moves   = []

    expected = (2 ** n) - 1
    print()
    divider_top()
    print(f"  Solving Tower of Hanoi with {n} disk(s):")
    print(f"  Source=A  Target=C  Auxiliary=B  |  Expected moves: {expected}")
    divider()

    tower_of_hanoi(n, "A", "C", "B", counter, moves)

    divider()
    print(f"  Total moves     : {len(moves)}  (= 2^{n} − 1 = {expected})")
    print(f"  Recursive calls : {counter[0]}")
    divider_bottom()
    print()


def action_permutations():
    print("\n── String Permutations (Recursion) ─────────────────────────")
    s       = get_nonempty_string("  Enter a string (1–8 characters): ", max_len=8)
    counter = make_counter()
    result  = []

    permutations(s, "", result, counter)

    # Remove duplicates while preserving order (for repeated-char strings)
    unique = list(dict.fromkeys(result))

    print()
    divider_top()
    print(f"  Permutations of '{s}'  ({len(s)} character(s)):")
    divider()

    # Print up to 120 permutations; truncate beyond that
    display_limit = 120
    for i, perm in enumerate(unique[:display_limit]):
        end = "\n" if (i + 1) % 8 == 0 else "  "
        print(f"  {perm}", end=end)

    if len(unique) % 8 != 0:
        print()   # End the last partial line

    if len(unique) > display_limit:
        hidden = len(unique) - display_limit
        print(f"  … and {hidden} more (total: {len(unique)})")

    divider()
    print(f"  Total permutations    : {len(result)}")
    print(f"  Unique permutations   : {len(unique)}")
    print(f"  Expected (n!)         : {_factorial_simple(len(s))}")
    print(f"  Recursive calls       : {counter[0]}")
    divider_bottom()
    print()


def _factorial_simple(n):
    """Non-recursive helper used only for the expected-count display."""
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


# ── Main menu ─────────────────────────────────────────────────────────────────

def show_menu():
    print("╔════════════════════════════════════════════════════════╗")
    print("║          Interactive Advanced Recursion Explorer        ║")
    print("╠════════════════════════════════════════════════════════╣")
    print("║  1. Calculate factorial using recursion                ║")
    print("║  2. Generate Fibonacci sequence using recursion        ║")
    print("║  3. Solve Tower of Hanoi                               ║")
    print("║  4. Generate all permutations of a string              ║")
    print("║  5. Exit                                               ║")
    print("╚════════════════════════════════════════════════════════╝")

    while True:
        choice = input("  Choose an option [1-5]: ").strip()
        if choice in {"1", "2", "3", "4", "5"}:
            return choice
        print("  [!] Invalid choice. Please enter a number from 1 to 5.")


def main():
    """
    Program entry point.
    No globals, no classes — everything is passed through function arguments.
    """
    print("\nWelcome to the Interactive Advanced Recursion Explorer!\n")

    while True:
        print()
        choice = show_menu()

        if choice == "1":
            action_factorial()
        elif choice == "2":
            action_fibonacci()
        elif choice == "3":
            action_hanoi()
        elif choice == "4":
            action_permutations()
        elif choice == "5":
            print("\n  Goodbye!\n")
            break


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()