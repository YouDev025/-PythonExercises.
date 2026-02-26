"""
Interactive Insertion Sort Algorithm
------------------------------------
This program allows the user to enter numerical elements into a list,
display them, and sort them using the Insertion Sort algorithm interactively.

Author: Youssef Adardour
Date: February 2026
"""


# Function: Insertion Sort (manual implementation)
def insertion_sort(data_list, ascending=True):
    comparisons = 0
    shifts = 0

    # Traverse from the second element to the end
    for i in range(1, len(data_list)):
        key = data_list[i]  # Current element to insert
        j = i - 1
        print(f"\nStep {i}: Inserting {key}")

        # Shift elements greater (or smaller for descending) than key
        while j >= 0:
            comparisons += 1
            if (ascending and data_list[j] > key) or (not ascending and data_list[j] < key):
                data_list[j + 1] = data_list[j]
                shifts += 1
                j -= 1
                print(f"Shifted → {data_list}")
            else:
                break

        # Insert the key at the correct position
        data_list[j + 1] = key
        print(f"Inserted {key} → {data_list}")

    return {"comparisons": comparisons, "shifts": shifts}


# Function: Display menu
def display_menu():
    print("\n=== Interactive Insertion Sort Menu ===")
    print("1. Enter numerical elements into the list")
    print("2. Display the current list")
    print("3. Sort the list using Insertion Sort")
    print("4. Display the sorted list")
    print("5. Exit program")


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
        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            # Enter elements
            num = get_integer_input("How many elements do you want to add? ")
            for i in range(num):
                element = get_integer_input(f"Enter element {i + 1}: ")
                data_list.append(element)
            print("Elements added successfully.")

        elif choice == "2":
            # Display current list
            if data_list:
                print("Current List:", data_list)
            else:
                print("The list is empty.")

        elif choice == "3":
            # Sort using Insertion Sort
            if not data_list:
                print("List is empty. Please add elements first.")
                continue
            order_choice = input("Sort in ascending (A) or descending (D) order? ").strip().lower()
            ascending = True if order_choice == "a" else False
            result = insertion_sort(data_list, ascending)
            print("\nSorting complete.")
            print(f"Total comparisons: {result['comparisons']}")
            print(f"Total shifts: {result['shifts']}")
            print("Best-case complexity: O(n) → already sorted list.")
            print("Worst-case complexity: O(n²) → reverse sorted list.")

        elif choice == "4":
            # Display sorted list
            if data_list:
                print("Sorted List:", data_list)
            else:
                print("The list is empty.")

        elif choice == "5":
            # Exit program
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice! Please select a valid option (1-5).")


# Run the program
if __name__ == "__main__":
    main()
