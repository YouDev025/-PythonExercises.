"""
Interactive Maximum Subarray
----------------------------
This program allows users to compute the maximum subarray sum of a list of integers.
It supports both a naive O(n^2) approach and the efficient Kadane's Algorithm (O(n)).

Author: Youssef Adardour
Date: March 2026
"""

# -----------------------------
# Utility Functions
# -----------------------------

def validate_list(prompt):
    """Prompt user to enter a list of integers."""
    while True:
        try:
            raw = input(prompt).split()
            arr = [int(x) for x in raw]
            if arr:
                return arr
            else:
                print("Error: Please enter at least one integer.")
        except ValueError:
            print("Error: Invalid input. Please enter integers only.")

def max_subarray_naive(arr):
    """Naive O(n^2) maximum subarray sum."""
    max_sum = float('-inf')
    steps = []
    n = len(arr)
    for i in range(n):
        current_sum = 0
        for j in range(i, n):
            current_sum += arr[j]
            steps.append((i, j, current_sum))
            max_sum = max(max_sum, current_sum)
    return max_sum, steps

def kadane(arr):
    """Kadane's Algorithm O(n) maximum subarray sum."""
    max_sum = arr[0]
    current_sum = arr[0]
    steps = [(0, arr[0])]
    for i in range(1, len(arr)):
        current_sum = max(arr[i], current_sum + arr[i])
        max_sum = max(max_sum, current_sum)
        steps.append((i, current_sum))
    return max_sum, steps

def display_steps(steps, method="Naive"):
    """Display steps of the algorithm."""
    print(f"\n{method} Steps:")
    if method == "Naive":
        print(f"{'i':<4}{'j':<4}{'sum':<8}")
        print("-" * 20)
        for i, j, s in steps:
            print(f"{i:<4}{j:<4}{s:<8}")
    else:  # Kadane
        print(f"{'index':<8}{'current_sum':<12}")
        print("-" * 20)
        for i, s in steps:
            print(f"{i:<8}{s:<12}")

# -----------------------------
# Menu System
# -----------------------------

def menu():
    """Interactive menu system."""
    arr, last_steps, last_method = [], [], ""

    while True:
        print("\n=== Interactive Maximum Subarray ===")
        print("1. Enter array of integers")
        print("2. Compute maximum subarray (Naive)")
        print("3. Compute maximum subarray (Kadane's Algorithm)")
        print("4. Display steps of last calculation")
        print("5. Show time complexity explanation")
        print("6. Exit")

        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            arr = validate_list("Enter integers separated by spaces: ")
            last_steps, last_method = [], ""
            print(f"Array stored: {arr}")

        elif choice == "2":
            if arr:
                max_sum, steps = max_subarray_naive(arr)
                last_steps, last_method = steps, "Naive"
                print(f"\nNaive maximum subarray sum = {max_sum}")
            else:
                print("Please enter an array first (Option 1).")

        elif choice == "3":
            if arr:
                max_sum, steps = kadane(arr)
                last_steps, last_method = steps, "Kadane"
                print(f"\nKadane's maximum subarray sum = {max_sum}")
            else:
                print("Please enter an array first (Option 1).")

        elif choice == "4":
            if last_steps:
                display_steps(last_steps, last_method)
            else:
                print("No steps recorded yet. Perform a calculation first.")

        elif choice == "5":
            print("\nTime Complexity Explanation:")
            print("Naive method: O(n^2) — checks all subarrays.")
            print("Kadane's Algorithm: O(n) — efficient for large arrays.")

        elif choice == "6":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option.")

# -----------------------------
# Main Execution
# -----------------------------

if __name__ == "__main__":
    menu()
