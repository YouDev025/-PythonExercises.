"""
Interactive Bubble Sort Algorithm
---------------------------------
This program allows the user to enter numerical elements into a list,
display them, and sort them using the Bubble Sort algorithm interactively.

Author: Youssef Adardour
Date: February 2026
"""


# Function: Bubble Sort (manual implementation)
def bubble_sort(data_list, ascending=True):
    n = len(data_list)
    comparisons = 0
    swaps = 0

    # Outer loop for passes
    for i in range(n - 1):
        swapped = False
        print(f"\nPass {i + 1}:")

        # Inner loop for comparisons
        for j in range(n - i - 1):
            comparisons += 1
            print(f"Comparing {data_list[j]} and {data_list[j + 1]}")

            # Ascending or descending order
            if (ascending and data_list[j] > data_list[j + 1]) or (not ascending and data_list[j] < data_list[j + 1]):
                # Swap elements
                data_list[j], data_list[j + 1] = data_list[j + 1], data_list[j]
                swaps += 1
                swapped = True
                print(f"Swapped → {data_list}")

        # If no swaps occurred, list is already sorted
        if not swapped:
            print("No swaps in this pass → List is sorted early.")
            break

    return {"comparisons": comparisons, "swaps": swaps}


# Function: Display menu
def display_menu():
    print("\n=== Interactive Bubble Sort Menu ===")
    print("1. Enter numerical elements into the list")
    print("2. Display the current list")
    print("3. Sort the list using Bubble Sort")
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
            # Sort using Bubble Sort
            if not data_list:
                print("List is empty. Please add elements first.")
                continue
            order_choice = input("Sort in ascending (A) or descending (D) order? ").strip().lower()
            ascending = True if order_choice == "a" else False
            result = bubble_sort(data_list, ascending)
            print("\nSorting complete.")
            print(f"Total comparisons: {result['comparisons']}")
            print(f"Total swaps: {result['swaps']}")

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
