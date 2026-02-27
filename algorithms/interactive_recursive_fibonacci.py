"""
Interactive Recursive Fibonacci
-------------------------------
This program allows the user to compute Fibonacci numbers using recursion.
It provides options to display the nth Fibonacci number, the full sequence up to n,
and compare recursive vs iterative performance with memoization concepts.

Author: Youssef Adardour
Date: 2026-02-27
"""


# Recursive Fibonacci function
def fibonacci_recursive(n, call_counter):
    """
    Compute the nth Fibonacci number using recursion.
    Base cases:
        if n == 0 -> return 0
        if n == 1 -> return 1
    Each call increments the call_counter dictionary.
    """
    call_counter["calls"] += 1

    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci_recursive(n - 1, call_counter) + fibonacci_recursive(n - 2, call_counter)


# Recursive Fibonacci with memoization
def fibonacci_memoized(n, memo, call_counter):
    """
    Optimized recursive Fibonacci using memoization.
    Stores previously computed values in a dictionary to avoid redundant calls.
    """
    call_counter["calls"] += 1

    if n in memo:
        return memo[n]

    if n == 0:
        memo[0] = 0
    elif n == 1:
        memo[1] = 1
    else:
        memo[n] = fibonacci_memoized(n - 1, memo, call_counter) + fibonacci_memoized(n - 2, memo, call_counter)

    return memo[n]


# Iterative Fibonacci for comparison
def fibonacci_iterative(n):
    """
    Compute the nth Fibonacci number using an iterative loop.
    """
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


# Function: Display complexity information
def show_complexity():
    print("\n--- Complexity Analysis ---")
    print("Recursive Fibonacci (naive):")
    print("  Time Complexity: O(2^n) (exponential)")
    print("  Space Complexity: O(n) (recursion stack)")
    print("\nRecursive Fibonacci with memoization:")
    print("  Time Complexity: O(n)")
    print("  Space Complexity: O(n) (dictionary storage)")
    print("\nIterative Fibonacci:")
    print("  Time Complexity: O(n)")
    print("  Space Complexity: O(1)\n")


# Function: Validate user input
def get_valid_integer(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value < 0:
                print("Please enter a non-negative integer.")
            else:
                return value
        except ValueError:
            print("Invalid input. Please enter an integer.")


# Function: Menu system
def menu():
    while True:
        print("\n=== Interactive Recursive Fibonacci ===")
        print("1. Enter a number n")
        print("2. Display the nth Fibonacci number (recursive)")
        print("3. Display the full Fibonacci sequence up to n")
        print("4. Compare recursive vs iterative performance")
        print("5. Show complexity analysis")
        print("6. Exit program")

        choice = input("Select an option (1-6): ")

        if choice == "1":
            n = get_valid_integer("Enter a non-negative integer n: ")
            print(f"Number stored: {n}")

        elif choice == "2":
            n = get_valid_integer("Enter n to compute Fibonacci(n): ")
            call_counter = {"calls": 0}
            result = fibonacci_recursive(n, call_counter)
            print(f"Fibonacci({n}) = {result}")
            print(f"Recursive calls performed: {call_counter['calls']}")

        elif choice == "3":
            n = get_valid_integer("Enter n to display sequence up to n: ")
            sequence = []
            call_counter = {"calls": 0}
            for i in range(n + 1):
                sequence.append(fibonacci_recursive(i, call_counter))
            print(f"Fibonacci sequence up to {n}: {sequence}")
            print(f"Recursive calls performed: {call_counter['calls']}")

        elif choice == "4":
            n = get_valid_integer("Enter n to compare performance: ")

            # Naive recursion
            call_counter_naive = {"calls": 0}
            result_naive = fibonacci_recursive(n, call_counter_naive)

            # Memoized recursion
            call_counter_memo = {"calls": 0}
            result_memo = fibonacci_memoized(n, {}, call_counter_memo)

            # Iterative
            result_iter = fibonacci_iterative(n)

            print("\n--- Performance Comparison ---")
            print(f"Naive Recursive Fibonacci({n}) = {result_naive}, Calls: {call_counter_naive['calls']}")
            print(f"Memoized Recursive Fibonacci({n}) = {result_memo}, Calls: {call_counter_memo['calls']}")
            print(f"Iterative Fibonacci({n}) = {result_iter}")

        elif choice == "5":
            show_complexity()

        elif choice == "6":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option (1-6).")


# Run the program
if __name__ == "__main__":
    menu()
