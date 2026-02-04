import os
from collections import Counter


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


def get_text_input():
    """
    Get text input for character/word frequency analysis.

    Returns:
        String of text, or None if invalid input
    """
    user_input = input("\nEnter text: ").strip()

    if not user_input:
        print("No text entered. Please enter some text.")
        return None

    return user_input


def count_frequency(items):
    """
    Count frequency of items.

    Args:
        items: List of items to count

    Returns:
        Counter object with frequencies
    """
    return Counter(items)


def count_character_frequency(text, case_sensitive=True):
    """
    Count frequency of characters in text.

    Args:
        text: String to analyze
        case_sensitive: Whether to treat uppercase and lowercase as different

    Returns:
        Counter object with character frequencies
    """
    if not case_sensitive:
        text = text.lower()

    return Counter(text)


def count_word_frequency(text, case_sensitive=False):
    """
    Count frequency of words in text.

    Args:
        text: String to analyze
        case_sensitive: Whether to treat uppercase and lowercase as different

    Returns:
        Counter object with word frequencies
    """
    # Remove common punctuation and split into words
    import string

    # Create translation table to remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator)

    if not case_sensitive:
        cleaned_text = cleaned_text.lower()

    words = cleaned_text.split()
    return Counter(words)


def display_frequency_table(frequency_counter, title="Frequency Analysis"):
    """
    Display frequency data in a formatted table.

    Args:
        frequency_counter: Counter object with frequency data
        title: Title for the table
    """
    print("\n" + "=" * 70)
    print(f"{title:^70}")
    print("=" * 70)
    print(f"{'Item':<30} {'Frequency':>15} {'Percentage':>15}")
    print("-" * 70)

    total = sum(frequency_counter.values())

    # Sort by frequency (descending), then by item name
    sorted_items = sorted(frequency_counter.items(),
                          key=lambda x: (-x[1], str(x[0])))

    for item, count in sorted_items:
        percentage = (count / total) * 100
        # Truncate long items for display
        item_str = str(item)
        if len(item_str) > 28:
            item_str = item_str[:25] + "..."
        print(f"{item_str:<30} {count:>15} {percentage:>14.2f}%")

    print("-" * 70)
    print(f"{'Total':<30} {total:>15} {'100.00%':>15}")
    print("=" * 70)


def display_statistics(frequency_counter):
    """Display statistical information about the frequency data."""
    if not frequency_counter:
        print("No data to analyze.")
        return

    total_items = sum(frequency_counter.values())
    unique_items = len(frequency_counter)
    most_common = frequency_counter.most_common(1)[0]
    least_common = frequency_counter.most_common()[-1]

    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)
    print(f"Total items:           {total_items}")
    print(f"Unique items:          {unique_items}")
    print(f"Most common:           '{most_common[0]}' (appears {most_common[1]} times)")
    print(f"Least common:          '{least_common[0]}' (appears {least_common[1]} times)")

    # Calculate average frequency
    avg_frequency = total_items / unique_items
    print(f"Average frequency:     {avg_frequency:.2f}")
    print("=" * 70)


def display_top_n(frequency_counter, n=5):
    """Display top N most frequent items."""
    print(f"\n{'=' * 70}")
    print(f"TOP {n} MOST FREQUENT ITEMS")
    print("=" * 70)
    print(f"{'Rank':<8} {'Item':<30} {'Frequency':>15} {'Percentage':>15}")
    print("-" * 70)

    total = sum(frequency_counter.values())
    top_items = frequency_counter.most_common(n)

    for rank, (item, count) in enumerate(top_items, 1):
        percentage = (count / total) * 100
        item_str = str(item)
        if len(item_str) > 28:
            item_str = item_str[:25] + "..."
        print(f"{rank:<8} {item_str:<30} {count:>15} {percentage:>14.2f}%")

    print("=" * 70)


def filter_by_frequency(frequency_counter, min_freq=None, max_freq=None):
    """
    Filter items by frequency range.

    Args:
        frequency_counter: Counter object
        min_freq: Minimum frequency (inclusive)
        max_freq: Maximum frequency (inclusive)

    Returns:
        Filtered Counter object
    """
    filtered = Counter()

    for item, count in frequency_counter.items():
        if min_freq is not None and count < min_freq:
            continue
        if max_freq is not None and count > max_freq:
            continue
        filtered[item] = count

    return filtered


def export_to_csv(frequency_counter, filename="frequency_data.csv"):
    """Export frequency data to CSV file."""
    try:
        with open(filename, 'w') as f:
            f.write("Item,Frequency,Percentage\n")
            total = sum(frequency_counter.values())

            sorted_items = sorted(frequency_counter.items(),
                                  key=lambda x: (-x[1], str(x[0])))

            for item, count in sorted_items:
                percentage = (count / total) * 100
                f.write(f'"{item}",{count},{percentage:.2f}\n')

        print(f"\n✓ Data exported successfully to '{filename}'")
        return True
    except Exception as e:
        print(f"\n✗ Error exporting data: {e}")
        return False


def display_main_menu():
    """Display the main menu."""
    print("=== Frequency Counter Program ===")
    print("1. Count item frequency (list of items)")
    print("2. Count word frequency (text)")
    print("3. Count character frequency (text)")
    print("4. Exit")
    print()


def display_analysis_menu():
    """Display the analysis options menu."""
    print("\n=== Analysis Options ===")
    print("1. View full frequency table")
    print("2. View statistics")
    print("3. View top N items")
    print("4. Filter by frequency range")
    print("5. Export to CSV")
    print("6. Back to main menu")
    print()


def handle_item_frequency():
    """Handle item frequency counting workflow."""
    items = get_input_data()

    if items is None:
        return None

    frequency = count_frequency(items)
    return frequency


def handle_word_frequency():
    """Handle word frequency counting workflow."""
    text = get_text_input()

    if text is None:
        return None

    case_choice = input("Case-sensitive? (y/n): ").strip().lower()
    case_sensitive = (case_choice == 'y')

    frequency = count_word_frequency(text, case_sensitive)
    return frequency


def handle_character_frequency():
    """Handle character frequency counting workflow."""
    text = get_text_input()

    if text is None:
        return None

    case_choice = input("Case-sensitive? (y/n): ").strip().lower()
    case_sensitive = (case_choice == 'y')

    include_spaces = input("Include spaces? (y/n): ").strip().lower()

    if include_spaces != 'y':
        text = text.replace(' ', '')

    frequency = count_character_frequency(text, case_sensitive)
    return frequency


def analyze_frequency_data(frequency_counter):
    """Provide analysis options for frequency data."""
    while True:
        display_analysis_menu()

        try:
            choice = int(input("Enter your choice (1-6): "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("\nPress Enter to continue...")
            continue

        if choice == 6:
            break

        if choice == 1:
            display_frequency_table(frequency_counter)
            input("\nPress Enter to continue...")

        elif choice == 2:
            display_statistics(frequency_counter)
            input("\nPress Enter to continue...")

        elif choice == 3:
            try:
                n = int(input("How many top items to display? "))
                if n > 0:
                    display_top_n(frequency_counter, n)
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
            input("\nPress Enter to continue...")

        elif choice == 4:
            try:
                min_freq = input("Minimum frequency (press Enter to skip): ").strip()
                max_freq = input("Maximum frequency (press Enter to skip): ").strip()

                min_f = int(min_freq) if min_freq else None
                max_f = int(max_freq) if max_freq else None

                filtered = filter_by_frequency(frequency_counter, min_f, max_f)

                if filtered:
                    display_frequency_table(filtered, "Filtered Frequency Analysis")
                else:
                    print("No items found in the specified range.")
            except ValueError:
                print("Invalid input. Please enter valid numbers.")
            input("\nPress Enter to continue...")

        elif choice == 5:
            filename = input("Enter filename (default: frequency_data.csv): ").strip()
            if not filename:
                filename = "frequency_data.csv"
            elif not filename.endswith('.csv'):
                filename += '.csv'

            export_to_csv(frequency_counter, filename)
            input("\nPress Enter to continue...")

        else:
            print("Invalid choice. Please enter a number between 1 and 6.")
            input("\nPress Enter to continue...")


def main():
    """Main program loop."""
    while True:
        clear_screen()
        display_main_menu()

        try:
            choice = int(input("Enter your choice (1-4): "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("\nPress Enter to continue...")
            continue

        if choice == 4:
            clear_screen()
            print("Thank you for using Frequency Counter!")
            print("Goodbye!")
            break

        if choice not in [1, 2, 3]:
            print("Invalid choice. Please enter a number between 1 and 4.")
            input("\nPress Enter to continue...")
            continue

        # Process based on choice
        frequency_data = None

        if choice == 1:
            frequency_data = handle_item_frequency()
        elif choice == 2:
            frequency_data = handle_word_frequency()
        elif choice == 3:
            frequency_data = handle_character_frequency()

        if frequency_data is None:
            input("\nPress Enter to continue...")
            continue

        # Analyze the frequency data
        analyze_frequency_data(frequency_data)


if __name__ == "__main__":
    main()