"""
Interactive LCM Calculator
--------------------------
This program allows users to compute the Least Common Multiple (LCM) of two or more integers
using the Euclidean algorithm for GCD. It displays intermediate steps, compares naive vs GCD-based
approaches, and explains time complexity.

Author: Youssef Adardour
Date: March 2026
"""

# -----------------------------
# Utility Functions
# -----------------------------

def validate_integer(prompt):
    """Prompt until user enters a valid integer (positive or negative allowed)."""
    while True:
        try:
            num = int(input(prompt))  # try converting input to integer
            if num == 0:
                print("Error: Zero is not allowed. Please enter a non-zero integer.")
            else:
                return abs(num)  # store absolute value (handle negatives)
        except ValueError:
            print("Error: Invalid input. Please enter an integer.")

def gcd(a, b):
    """Compute GCD using Euclidean algorithm with step tracking."""
    steps = []
    while b != 0:  # repeat until remainder is zero
        steps.append((a, b, a % b))  # store current step
        a, b = b, a % b  # update values
    return a, steps  # return final GCD and steps

def lcm(a, b):
    """Compute LCM using GCD."""
    gcd_val, steps = gcd(a, b)  # compute GCD first
    lcm_val = abs(a * b) // gcd_val  # formula: |a*b| / gcd(a,b)
    return lcm_val, steps

def lcm_multiple(numbers):
    """Compute LCM of multiple numbers iteratively."""
    current_lcm = numbers[0]  # start with first number
    all_steps = []
    for num in numbers[1:]:  # process remaining numbers
        lcm_val, steps = lcm(current_lcm, num)
        current_lcm = lcm_val  # update current LCM
        all_steps.extend(steps)  # collect all steps
    return current_lcm, all_steps

def naive_lcm(a, b):
    """Naive LCM calculation by checking multiples."""
    steps = []
    max_val = max(a, b)  # start from larger number
    lcm_val = max_val
    operations = 0
    while True:
        operations += 1
        steps.append(lcm_val)  # store trial value
        if lcm_val % a == 0 and lcm_val % b == 0:  # check divisibility
            return lcm_val, steps, operations
        lcm_val += max_val  # increment by max value

def display_gcd_steps(steps):
    """Display steps of GCD calculation."""
    print("\nGCD Steps:")
    print(f"{'a':<8}{'b':<8}{'a % b':<8}")
    print("-" * 24)
    for a, b, mod in steps:
        print(f"{a:<8}{b:<8}{mod:<8}")

# -----------------------------
# Menu System
# -----------------------------

def menu():
    """Interactive menu system."""
    numbers = []      # list to store user input numbers
    last_steps = []   # list to store last GCD steps

    while True:
        print("\n=== Interactive LCM Calculator ===")
        print("1. Enter integers")
        print("2. Calculate LCM (GCD-based)")
        print("3. Display intermediate GCD calculations")
        print("4. Compare naive vs GCD-based LCM")
        print("5. Show time complexity explanation")
        print("6. Exit")

        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            # Input multiple integers
            raw_input = input("Enter integers separated by spaces: ").split()
            numbers = []
            for val in raw_input:
                try:
                    num = int(val)
                    if num != 0:
                        numbers.append(abs(num))  # store absolute values
                    else:
                        print("Skipping zero (not allowed).")
                except ValueError:
                    print(f"Skipping invalid input: {val}")
            if numbers:
                print(f"Integers stored: {numbers}")
            else:
                print("No valid integers entered.")

        elif choice == "2":
            # Calculate LCM of stored numbers
            if numbers:
                lcm_val, steps = lcm_multiple(numbers)
                last_steps = steps
                print(f"\nLCM of {numbers} = {lcm_val}")
            else:
                print("Please enter integers first (Option 1).")

        elif choice == "3":
            # Display GCD steps from last calculation
            if last_steps:
                display_gcd_steps(last_steps)
            else:
                print("No GCD steps recorded yet. Perform an LCM calculation first.")

        elif choice == "4":
            # Compare naive vs GCD-based LCM for first two numbers
            if len(numbers) >= 2:
                a, b = numbers[0], numbers[1]
                lcm_gcd, steps_gcd = lcm(a, b)
                lcm_naive, steps_naive, ops = naive_lcm(a, b)
                print(f"\nComparing LCM of {a} and {b}:")
                print(f"GCD-based LCM = {lcm_gcd}")
                print(f"Naive LCM = {lcm_naive}")
                print(f"Naive method operations: {ops}")
                print(f"GCD-based steps: {len(steps_gcd)}")
            else:
                print("Please enter at least two integers first (Option 1).")

        elif choice == "5":
            # Explain time complexity
            print("\nTime Complexity Explanation:")
            print("Naive LCM approach can take O(a*b) in worst case.")
            print("GCD-based LCM uses Euclidean algorithm, which runs in O(log(min(a, b))).")
            print("Thus, GCD-based LCM is far more efficient.")

        elif choice == "6":
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
