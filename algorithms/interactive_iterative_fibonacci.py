"""
Interactive Iterative Fibonacci
-------------------------------
This program allows the user to compute Fibonacci numbers using an iterative method.
It provides options to display the nth Fibonacci number, the full sequence up to n,
and includes complexity analysis and memoization concepts.

Author: Youssef Adardour
Date: 2026-02-27
"""

# Function: Iterative Fibonacci
def fibonacci_iterative(n):
    """
    Compute the nth Fibonacci number using an iterative loop.
    Returns the nth Fibonacci number, the sequence list, and iteration count.
    """
    if n < 0:
        return None, [], 0  # Invalid input

    sequence = []
    a, b = 0, 1
    iterations = 0

    for i in range(n + 1):
        sequence.append(a)
        a, b = b, a + b
        iterations += 1

    return sequence[-1], sequence, iterations


# Function: Display complexity information
def show_complexity():
    print("\n--- Complexity Analysis ---")
    print("Iterative Fibonacci:")
    print("  Time Complexity: O(n)")
    print("  Space Complexity: O(n) (due to storing sequence in a list)")
    print("\nRecursive Fibonacci (naive):")
    print("  Time Complexity: O(2^n) (exponential)")
    print("  Space Complexity: O(n) (due to recursion stack)")
    print("\nMemoization Concept:")
    print("  - We can store computed Fibonacci values in a dictionary")
    print("  - This avoids redundant calculations")
    print("  - Time Complexity reduces to O(n)")
    print("  - Space Complexity: O(n) for dictionary storage\n")


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
    memoization_dict = {}  # Dictionary to store computed Fibonacci values

    while True:
        print("\n=== Interactive Iterative Fibonacci ===")
        print("1. Enter a number n")
        print("2. Display the nth Fibonacci number (iterative)")
        print("3. Display the full Fibonacci sequence up to n")
        print("4. Show complexity analysis")
        print("5. Exit program")

        choice = input("Select an option (1-5): ")

        if choice == "1":
            n = get_valid_integer("Enter a non-negative integer n: ")
            # Store in memoization dictionary
            fib_n, seq, iterations = fibonacci_iterative(n)
            memoization_dict[n] = fib_n
            print(f"Stored Fibonacci({n}) = {fib_n} in memoization dictionary.")

        elif choice == "2":
            if not memoization_dict:
                print("No number entered yet. Please choose option 1 first.")
            else:
                n = get_valid_integer("Enter n to display Fibonacci(n): ")
                if n in memoization_dict:
                    print(f"Fibonacci({n}) = {memoization_dict[n]} (retrieved from memoization dictionary)")
                else:
                    fib_n, seq, iterations = fibonacci_iterative(n)
                    memoization_dict[n] = fib_n
                    print(f"Fibonacci({n}) = {fib_n} (computed iteratively)")
                    print(f"Iterations performed: {iterations}")

        elif choice == "3":
            if not memoization_dict:
                print("No number entered yet. Please choose option 1 first.")
            else:
                n = get_valid_integer("Enter n to display sequence up to n: ")
                fib_n, seq, iterations = fibonacci_iterative(n)
                print(f"Fibonacci sequence up to {n}: {seq}")
                print(f"Iterations performed: {iterations}")

        elif choice == "4":
            show_complexity()

        elif choice == "5":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option (1-5).")


# Run the program
if __name__ == "__main__":
    menu()
