"""
Interactive GCD Calculator (Euclidean Algorithm)
------------------------------------------------
This program allows users to compute the Greatest Common Divisor (GCD) of two or more integers
using both iterative and recursive Euclidean algorithms. It also displays algorithm steps,
counts iterations/recursive calls, and can compute the Least Common Multiple (LCM).

Author: Youssef Adardour
Date: March 2026
"""

# -----------------------------
# Utility Functions
# -----------------------------

def validate_integer(prompt):
    """Prompt until user enters a valid positive integer."""
    while True:
        try:
            num = int(input(prompt))  # try converting input to integer
            if num <= 0:
                print("Error: Please enter a positive integer greater than zero.")
            else:
                return num  # return valid integer
        except ValueError:
            print("Error: Invalid input. Please enter an integer.")

def gcd_iterative(a, b):
    """Iterative Euclidean algorithm with step tracking."""
    steps = []        # list to store steps
    iterations = 0    # count iterations
    while b != 0:     # repeat until remainder is zero
        steps.append((a, b, a % b))  # store current step
        a, b = b, a % b              # update values
        iterations += 1
    return a, steps, iterations      # return GCD, steps, and iteration count

def gcd_recursive(a, b, steps=None, calls=0):
    """Recursive Euclidean algorithm with step tracking."""
    if steps is None:
        steps = []  # initialize steps list
    if b == 0:      # base case
        return a, steps, calls
    steps.append((a, b, a % b))  # store current step
    return gcd_recursive(b, a % b, steps, calls + 1)  # recursive call

def lcm(a, b):
    """Compute LCM using GCD."""
    gcd_val, _, _ = gcd_iterative(a, b)  # compute GCD first
    return abs(a * b) // gcd_val         # formula: |a*b| / gcd(a,b)

def gcd_multiple(numbers):
    """Compute GCD of a list of numbers iteratively."""
    current_gcd = numbers[0]   # start with first number
    total_steps = []           # store all steps
    total_iterations = 0       # count total iterations
    for num in numbers[1:]:    # process remaining numbers
        gcd_val, steps, iterations = gcd_iterative(current_gcd, num)
        current_gcd = gcd_val
        total_steps.extend(steps)
        total_iterations += iterations
    return current_gcd, total_steps, total_iterations

def display_steps(steps):
    """Display the steps of the Euclidean algorithm."""
    print("\nAlgorithm Steps:")
    print(f"{'a':<8}{'b':<8}{'a % b':<8}")
    print("-" * 24)
    for a, b, mod in steps:
        print(f"{a:<8}{b:<8}{mod:<8}")

# -----------------------------
# Menu System
# -----------------------------

def menu():
    """Interactive menu system."""
    num1, num2, last_steps = None, None, []  # initialize variables

    while True:
        # Display menu options
        print("\n=== Interactive GCD Calculator ===")
        print("1. Enter two integers")
        print("2. Calculate GCD (Iterative)")
        print("3. Calculate GCD (Recursive)")
        print("4. Display steps of last calculation")
        print("5. Compute LCM using GCD")
        print("6. Compute GCD of multiple numbers")
        print("7. Show time complexity explanation")
        print("8. Exit")

        choice = input("Choose an option (1-8): ").strip()

        if choice == "1":
            # Input two integers
            num1 = validate_integer("Enter first integer: ")
            num2 = validate_integer("Enter second integer: ")
            last_steps = []
            print("Inputs stored successfully.")

        elif choice == "2":
            # Iterative GCD
            if num1 and num2:
                gcd_val, steps, iterations = gcd_iterative(num1, num2)
                last_steps = steps
                print(f"\nIterative GCD of {num1} and {num2} = {gcd_val}")
                print(f"Number of iterations: {iterations}")
            else:
                print("Please enter integers first (Option 1).")

        elif choice == "3":
            # Recursive GCD
            if num1 and num2:
                gcd_val, steps, calls = gcd_recursive(num1, num2)
                last_steps = steps
                print(f"\nRecursive GCD of {num1} and {num2} = {gcd_val}")
                print(f"Number of recursive calls: {calls}")
            else:
                print("Please enter integers first (Option 1).")

        elif choice == "4":
            # Display steps
            if last_steps:
                display_steps(last_steps)
            else:
                print("No steps recorded yet. Perform a GCD calculation first.")

        elif choice == "5":
            # Compute LCM
            if num1 and num2:
                lcm_val = lcm(num1, num2)
                print(f"\nLCM of {num1} and {num2} = {lcm_val}")
            else:
                print("Please enter integers first (Option 1).")

        elif choice == "6":
            # Compute GCD of multiple numbers
            raw_input = input("Enter integers separated by spaces: ").split()
            numbers = []
            for val in raw_input:
                try:
                    num = int(val)
                    if num > 0:
                        numbers.append(num)
                    else:
                        print(f"Skipping invalid number: {val}")
                except ValueError:
                    print(f"Skipping invalid input: {val}")
            if numbers:
                gcd_val, steps, iterations = gcd_multiple(numbers)
                last_steps = steps
                print(f"\nGCD of {numbers} = {gcd_val}")
                print(f"Total iterations: {iterations}")
            else:
                print("No valid integers entered.")

        elif choice == "7":
            # Explain time complexity
            print("\nTime Complexity Explanation:")
            print("The Euclidean Algorithm runs in O(log(min(a, b))).")
            print("This is because each step reduces the problem size significantly.")
            print("It is one of the most efficient algorithms for computing GCD.")

        elif choice == "8":
            # Exit program
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option.")

# -----------------------------
# Main Execution
# -----------------------------

if __name__ == "__main__":
    menu()
