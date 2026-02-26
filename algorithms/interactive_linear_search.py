"""
Interactive Linear Search Algorithm
-----------------------------------
This program allows the user to manage a list of elements and perform
linear search operations interactively through a menu system.

Author: Youssef Adardour
Date: February 2026
"""


# Function: Perform linear search manually
def linear_search(data_list, target):
    positions = []  # Store all positions where target is found
    comparisons = 0  # Count number of comparisons made

    # Loop through the list manually
    for index in range(len(data_list)):
        comparisons += 1
        if data_list[index] == target:
            positions.append(index)

    # Return results
    if positions:
        return {
            "found": True,
            "positions": positions,
            "comparisons": comparisons
        }
    else:
        return {
            "found": False,
            "positions": [],
            "comparisons": comparisons
        }


# Function: Display menu
def display_menu():
    print("\n=== Interactive Linear Search Menu ===")
    print("1. Enter elements into the list")
    print("2. Display the list")
    print("3. Search for a value (Linear Search)")
    print("4. Count how many times a value appears")
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
    search_results = {}  # Dictionary: value → list of positions

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
            # Display list
            if data_list:
                print("Current List:", data_list)
            else:
                print("The list is empty.")

        elif choice == "3":
            # Search for a value
            if not data_list:
                print("List is empty. Please add elements first.")
                continue
            target = get_integer_input("Enter value to search: ")
            result = linear_search(data_list, target)

            if result["found"]:
                print(f"Value {target} found at positions: {result['positions']}")
                print(f"Comparisons made: {result['comparisons']}")
                search_results[target] = result["positions"]
            else:
                print(f"Value {target} not found in the list.")
                print(f"Comparisons made: {result['comparisons']}")

        elif choice == "4":
            # Count occurrences
            if not data_list:
                print("List is empty. Please add elements first.")
                continue
            target = get_integer_input("Enter value to count: ")
            count = data_list.count(target)  # Built-in count for comparison
            print(f"Value {target} appears {count} time(s) in the list.")

        elif choice == "5":
            # Exit program
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice! Please select a valid option (1-5).")


# Run the program
if __name__ == "__main__":
    main()
