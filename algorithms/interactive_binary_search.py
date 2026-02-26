"""
Interactive Binary Search Algorithm
-----------------------------------
This program allows the user to manage a list of numerical elements,
automatically sort them, and perform binary search operations interactively.

Author: Youssef Adardour
Date: February 2026
"""


# Function: Iterative Binary Search
def binary_search_iterative(data_list, target):
    left, right = 0, len(data_list) - 1
    comparisons = 0

    while left <= right:
        mid = (left + right) // 2
        comparisons += 1
        print(f"Step: left={left}, right={right}, mid={mid}")

        if data_list[mid] == target:
            return {"found": True, "index": mid, "comparisons": comparisons}
        elif data_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return {"found": False, "index": None, "comparisons": comparisons}


# Function: Recursive Binary Search
def binary_search_recursive(data_list, target, left, right, comparisons=0):
    if left > right:
        return {"found": False, "index": None, "comparisons": comparisons}

    mid = (left + right) // 2
    comparisons += 1
    print(f"Step: left={left}, right={right}, mid={mid}")

    if data_list[mid] == target:
        return {"found": True, "index": mid, "comparisons": comparisons}
    elif data_list[mid] < target:
        return binary_search_recursive(data_list, target, mid + 1, right, comparisons)
    else:
        return binary_search_recursive(data_list, target, left, mid - 1, comparisons)


# Function: Linear Search (for performance comparison)
def linear_search(data_list, target):
    comparisons = 0
    for index in range(len(data_list)):
        comparisons += 1
        if data_list[index] == target:
            return {"found": True, "index": index, "comparisons": comparisons}
    return {"found": False, "index": None, "comparisons": comparisons}


# Function: Display menu
def display_menu():
    print("\n=== Interactive Binary Search Menu ===")
    print("1. Enter numerical elements into the list")
    print("2. Display the sorted list")
    print("3. Search for a value (Binary Search - Iterative)")
    print("4. Search for a value (Binary Search - Recursive)")
    print("5. Compare Linear Search vs Binary Search")
    print("6. Exit program")


# Function: Input validation for integers
def get_integer_input(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input! Please enter a valid integer.")


# Main program loop
def main():
    data_list = []  # Store all elements

    while True:
        display_menu()
        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            # Enter elements
            num = get_integer_input("How many elements do you want to add? ")
            for i in range(num):
                element = get_integer_input(f"Enter element {i + 1}: ")
                data_list.append(element)
            data_list.sort()  # Automatically sort
            print("Elements added and sorted successfully.")

        elif choice == "2":
            # Display sorted list
            if data_list:
                print("Sorted List:", data_list)
            else:
                print("The list is empty.")

        elif choice == "3":
            # Iterative Binary Search
            if not data_list:
                print("List is empty. Please add elements first.")
                continue
            target = get_integer_input("Enter value to search: ")
            result = binary_search_iterative(data_list, target)
            if result["found"]:
                print(f"Value {target} found at index {result['index']}.")
            else:
                print(f"Value {target} not found.")
            print(f"Comparisons made: {result['comparisons']}")

        elif choice == "4":
            # Recursive Binary Search
            if not data_list:
                print("List is empty. Please add elements first.")
                continue
            target = get_integer_input("Enter value to search: ")
            result = binary_search_recursive(data_list, target, 0, len(data_list) - 1)
            if result["found"]:
                print(f"Value {target} found at index {result['index']}.")
            else:
                print(f"Value {target} not found.")
            print(f"Comparisons made: {result['comparisons']}")

        elif choice == "5":
            # Compare Linear vs Binary Search
            if not data_list:
                print("List is empty. Please add elements first.")
                continue
            target = get_integer_input("Enter value to search: ")
            linear_result = linear_search(data_list, target)
            binary_result = binary_search_iterative(data_list, target)

            print("\n--- Performance Comparison ---")
            print(f"Linear Search: {'Found' if linear_result['found'] else 'Not Found'} "
                  f"(Index: {linear_result['index']}, Comparisons: {linear_result['comparisons']})")
            print(f"Binary Search: {'Found' if binary_result['found'] else 'Not Found'} "
                  f"(Index: {binary_result['index']}, Comparisons: {binary_result['comparisons']})")

        elif choice == "6":
            # Exit program
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice! Please select a valid option (1-6).")


# Run the program
if __name__ == "__main__":
    main()
