import os


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def custom_sort(data, choice):
    """
    Sort data based on the chosen method.

    Args:
        data: List of strings to sort
        choice: Integer representing sort method (1-3)

    Returns:
        Sorted list of strings
    """
    if choice == 1:
        # Sort by length, then alphabetically for ties
        return sorted(data, key=lambda x: (len(x), x.lower()))
    elif choice == 2:
        # Case-insensitive alphabetical sort
        return sorted(data, key=lambda x: x.lower())
    elif choice == 3:
        # Sort by ASCII sum, then alphabetically for ties
        return sorted(data, key=lambda x: (sum(ord(c) for c in x), x.lower()))
    else:
        # Default alphabetical sort
        return sorted(data)


def get_menu_choice():
    """
    Display menu and get user's choice.

    Returns:
        Integer representing user's choice, or None if invalid
    """
    print("=== Custom Sort Program ===")
    print("1. Sort by length")
    print("2. Sort alphabetically (case-insensitive)")
    print("3. Sort by ASCII sum")
    print("4. Exit")
    print()

    try:
        choice = int(input("Enter your choice (1-4): "))
        if choice in [1, 2, 3, 4]:
            return choice
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None


def get_items():
    """
    Get items from user input.

    Returns:
        List of items, or None if no valid items entered
    """
    user_input = input("\nEnter items separated by spaces: ").strip()

    if not user_input:
        print("No items entered. Please enter at least one item.")
        return None

    items = user_input.split()
    return items


def display_results(original, sorted_items, choice):
    """Display the sorting results in a formatted way."""
    sort_methods = {
        1: "Length",
        2: "Alphabetically (case-insensitive)",
        3: "ASCII sum"
    }

    print("\n" + "=" * 50)
    print(f"Sort method: {sort_methods[choice]}")
    print("=" * 50)
    print(f"Original: {', '.join(original)}")
    print(f"Sorted:   {', '.join(sorted_items)}")
    print("=" * 50)


def main():
    """Main program loop."""
    while True:
        clear_screen()

        # Get user's menu choice
        choice = get_menu_choice()

        if choice is None:
            input("\nPress Enter to continue...")
            continue

        # Exit option
        if choice == 4:
            clear_screen()
            print("Thank you for using Custom Sort Program!")
            print("Goodbye!")
            break

        # Get items to sort
        items = get_items()

        if items is None:
            input("\nPress Enter to continue...")
            continue

        # Sort and display results
        sorted_items = custom_sort(items, choice)
        display_results(items, sorted_items, choice)

        # Ask if user wants to continue
        print()
        confirm = input("Do you want to sort again? (y/n): ").strip().lower()

        if confirm != 'y':
            clear_screen()
            print("Thank you for using Custom Sort Program!")
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()