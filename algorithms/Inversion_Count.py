"""
Comptage d'inversions (Inversion Count)
---------------------------------------
This program allows users to count the number of inversions in an array.
It uses both a naive O(n^2) approach and an efficient O(n log n) merge-sort based approach.
It also displays intermediate steps if desired.

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

def count_inversions_naive(arr):
    """Naive O(n^2) inversion count."""
    count = 0
    steps = []
    n = len(arr)
    for i in range(n):
        for j in range(i+1, n):
            if arr[i] > arr[j]:
                count += 1
                steps.append((i, j, arr[i], arr[j]))
    return count, steps

def merge_and_count(arr, temp, left, mid, right):
    """Helper for merge sort inversion count."""
    i, j, k = left, mid+1, left
    inv_count = 0
    while i <= mid and j <= right:
        if arr[i] <= arr[j]:
            temp[k] = arr[i]
            i += 1
        else:
            temp[k] = arr[j]
            inv_count += (mid - i + 1)  # count inversions
            j += 1
        k += 1
    while i <= mid:
        temp[k] = arr[i]
        i += 1
        k += 1
    while j <= right:
        temp[k] = arr[j]
        j += 1
        k += 1
    for idx in range(left, right+1):
        arr[idx] = temp[idx]
    return inv_count

def merge_sort_count(arr, temp, left, right):
    """Recursive merge sort inversion count."""
    inv_count = 0
    if left < right:
        mid = (left + right) // 2
        inv_count += merge_sort_count(arr, temp, left, mid)
        inv_count += merge_sort_count(arr, temp, mid+1, right)
        inv_count += merge_and_count(arr, temp, left, mid, right)
    return inv_count

def count_inversions_merge(arr):
    """Efficient O(n log n) inversion count using merge sort."""
    temp = arr.copy()
    return merge_sort_count(arr, temp, 0, len(arr)-1)

def display_steps(steps):
    """Display inversion pairs found in naive method."""
    print("\nInversion Pairs (Naive):")
    print(f"{'i':<4}{'j':<4}{'arr[i]':<8}{'arr[j]':<8}")
    print("-" * 28)
    for i, j, ai, aj in steps:
        print(f"{i:<4}{j:<4}{ai:<8}{aj:<8}")

# -----------------------------
# Menu System
# -----------------------------

def menu():
    """Interactive menu system."""
    arr, last_steps = [], []

    while True:
        print("\n=== Comptage d'inversions ===")
        print("1. Enter array of integers")
        print("2. Count inversions (Naive O(n^2))")
        print("3. Count inversions (Efficient O(n log n))")
        print("4. Display inversion pairs (Naive)")
        print("5. Show time complexity explanation")
        print("6. Exit")

        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            arr = validate_list("Enter integers separated by spaces: ")
            last_steps = []
            print(f"Array stored: {arr}")

        elif choice == "2":
            if arr:
                count, steps = count_inversions_naive(arr.copy())
                last_steps = steps
                print(f"\nNaive inversion count = {count}")
            else:
                print("Please enter an array first (Option 1).")

        elif choice == "3":
            if arr:
                count = count_inversions_merge(arr.copy())
                print(f"\nEfficient inversion count = {count}")
            else:
                print("Please enter an array first (Option 1).")

        elif choice == "4":
            if last_steps:
                display_steps(last_steps)
            else:
                print("No inversion pairs recorded yet. Run naive method first.")

        elif choice == "5":
            print("\nTime Complexity Explanation:")
            print("Naive method: O(n^2) — checks all pairs.")
            print("Merge-sort method: O(n log n) — efficient for large arrays.")

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
