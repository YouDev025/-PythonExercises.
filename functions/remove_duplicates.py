import os


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_input_data():
    """
    Get data from user input.

    Returns:
        List of items, or None if invalid input
    """
    user_input = input("\nEnter items separated by spaces: ").strip()

    if not user_input:
        print("No items entered. Please enter at least one item.")
        return None

    items = user_input.split()
    return items


def remove_duplicates_preserve_order(items):
    """
    Remove duplicates while preserving the original order.

    Args:
        items: List of items

    Returns:
        List with duplicates removed (order preserved)
    """
    seen = set()
    result = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def remove_duplicates_sorted(items):
    """
    Remove duplicates and sort the result.

    Args:
        items: List of items

    Returns:
        Sorted list with duplicates removed
    """
    return sorted(set(items))


def remove_duplicates_case_insensitive(items):
    """
    Remove duplicates treating uppercase and lowercase as same.

    Args:
        items: List of items

    Returns:
        List with duplicates removed (case-insensitive, keeps first occurrence)
    """
    seen = set()
    result = []

    for item in items:
        lower_item = item.lower()
        if lower_item not in seen:
            seen.add(lower_item)
            result.append(item)

    return result


def keep_only_duplicates(items):
    """
    Keep only items that appear more than once.

    Args:
        items: List of items

    Returns:
        List of items that appeared multiple times (unique duplicates)
    """
    from collections import Counter

    counts = Counter(items)
    duplicates = [item for item, count in counts.items() if count > 1]

    return duplicates


def find_duplicate_info(items):
    """
    Find detailed information about duplicates.

    Args:
        items: List of items

    Returns:
        Dictionary with duplicate information
    """
    from collections import Counter

    counts = Counter(items)

    duplicates = {item: count for item, count in counts.items() if count > 1}
    unique_items = {item: count for item, count in counts.items() if count == 1}

    return {
        'duplicates': duplicates,
        'unique': unique_items,
        'total_items': len(items),
        'unique_count': len(counts),
        'duplicate_count': sum(counts.values()) - len(counts)
    }


def remove_consecutive_duplicates(items):
    """
    Remove only consecutive duplicates.

    Args:
        items: List of items

    Returns:
        List with consecutive duplicates removed
    """
    if not items:
        return []

    result = [items[0]]

    for i in range(1, len(items)):
        if items[i] != items[i - 1]:
            result.append(items[i])

    return result


def display_comparison(original, processed, title="Results"):
    """
    Display original and processed lists side by side.

    Args:
        original: Original list
        processed: Processed list
        title: Title for the display
    """
    print("\n" + "=" * 70)
    print(f"{title:^70}")
    print("=" * 70)

    print(f"\nOriginal ({len(original)} items):")
    print(f"  {', '.join(original)}")

    print(f"\nAfter removing duplicates ({len(processed)} items):")
    print(f"  {', '.join(processed)}")

    removed_count = len(original) - len(processed)
    print(f"\nDuplicates removed: {removed_count}")

    print("=" * 70)


def display_duplicate_analysis(items):
    """Display detailed duplicate analysis."""
    info = find_duplicate_info(items)

    print("\n" + "=" * 70)
    print("DUPLICATE ANALYSIS")
    print("=" * 70)

    print(f"\nTotal items:           {info['total_items']}")
    print(f"Unique items:          {info['unique_count']}")
    print(f"Duplicate items:       {info['duplicate_count']}")

    if info['duplicates']:
        print("\n" + "-" * 70)
        print("Items with duplicates:")
        print("-" * 70)
        print(f"{'Item':<30} {'Occurrences':>20} {'Duplicates':>18}")
        print("-" * 70)

        sorted_duplicates = sorted(info['duplicates'].items(),
                                   key=lambda x: -x[1])

        for item, count in sorted_duplicates:
            item_str = str(item)
            if len(item_str) > 28:
                item_str = item_str[:25] + "..."
            print(f"{item_str:<30} {count:>20} {count - 1:>18}")
    else:
        print("\nNo duplicates found!")

    if info['unique']:
        print("\n" + "-" * 70)
        print(f"Unique items (appear only once): {len(info['unique'])}")
        print("-" * 70)
        unique_list = ', '.join(info['unique'].keys())
        print(f"  {unique_list}")

    print("=" * 70)


def export_results(original, processed, filename="deduplicated.txt"):
    """Export results to a text file."""
    try:
        with open(filename, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("DUPLICATE REMOVAL RESULTS\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Original ({len(original)} items):\n")
            f.write(f"{', '.join(original)}\n\n")

            f.write(f"After removing duplicates ({len(processed)} items):\n")
            f.write(f"{', '.join(processed)}\n\n")

            f.write(f"Duplicates removed: {len(original) - len(processed)}\n")
            f.write("=" * 70 + "\n")

        print(f"\n✓ Results exported successfully to '{filename}'")
        return True
    except Exception as e:
        print(f"\n✗ Error exporting results: {e}")
        return False


def display_main_menu():
    """Display the main menu."""
    print("=== Remove Duplicates Program ===")
    print("1. Remove duplicates (preserve order)")
    print("2. Remove duplicates (sorted)")
    print("3. Remove duplicates (case-insensitive)")
    print("4. Remove consecutive duplicates only")
    print("5. Keep only duplicate items")
    print("6. Analyze duplicates")
    print("7. Exit")
    print()


def display_options_menu():
    """Display the options menu after processing."""
    print("\n=== Options ===")
    print("1. View results")
    print("2. Export to file")
    print("3. Process another list")
    print("4. Back to main menu")
    print()


def process_data(items, choice):
    """
    Process data based on user choice.

    Args:
        items: List of items to process
        choice: Processing method choice

    Returns:
        Processed list or None
    """
    if choice == 1:
        return remove_duplicates_preserve_order(items)
    elif choice == 2:
        return remove_duplicates_sorted(items)
    elif choice == 3:
        return remove_duplicates_case_insensitive(items)
    elif choice == 4:
        return remove_consecutive_duplicates(items)
    elif choice == 5:
        return keep_only_duplicates(items)
    else:
        return None


def handle_processing(choice):
    """Handle the data processing workflow."""
    if choice == 6:
        # Analyze duplicates
        items = get_input_data()
        if items is None:
            return False

        display_duplicate_analysis(items)
        input("\nPress Enter to continue...")
        return True

    # Get input data
    items = get_input_data()
    if items is None:
        return False

    # Process data
    processed = process_data(items, choice)

    if processed is None:
        print("Error processing data.")
        input("\nPress Enter to continue...")
        return False

    # Determine title based on choice
    titles = {
        1: "Remove Duplicates (Preserve Order)",
        2: "Remove Duplicates (Sorted)",
        3: "Remove Duplicates (Case-Insensitive)",
        4: "Remove Consecutive Duplicates",
        5: "Items That Appear Multiple Times"
    }

    title = titles.get(choice, "Results")

    # Show results immediately
    display_comparison(items, processed, title)

    # Options menu
    while True:
        display_options_menu()

        try:
            option = int(input("Enter your choice (1-4): "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("\nPress Enter to continue...")
            continue

        if option == 4:
            break

        if option == 1:
            display_comparison(items, processed, title)
            input("\nPress Enter to continue...")

        elif option == 2:
            filename = input("Enter filename (default: deduplicated.txt): ").strip()
            if not filename:
                filename = "deduplicated.txt"
            elif not filename.endswith('.txt'):
                filename += '.txt'

            export_results(items, processed, filename)
            input("\nPress Enter to continue...")

        elif option == 3:
            return handle_processing(choice)

        else:
            print("Invalid choice. Please enter a number between 1 and 4.")
            input("\nPress Enter to continue...")

    return True


def main():
    """Main program loop."""
    while True:
        clear_screen()
        display_main_menu()

        try:
            choice = int(input("Enter your choice (1-7): "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("\nPress Enter to continue...")
            continue

        if choice == 7:
            clear_screen()
            print("Thank you for using Remove Duplicates Program!")
            print("Goodbye!")
            break

        if choice not in range(1, 7):
            print("Invalid choice. Please enter a number between 1 and 7.")
            input("\nPress Enter to continue...")
            continue

        # Handle the processing
        handle_processing(choice)


if __name__ == "__main__":
    main()