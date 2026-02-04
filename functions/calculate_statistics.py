import os
import math


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_numbers():
    """
    Get numbers from user input.

    Returns:
        List of numbers, or None if invalid input
    """
    try:
        user_input = input("\nEnter numbers separated by spaces: ").strip()

        if not user_input:
            print("No numbers entered. Please enter at least one number.")
            return None

        numbers = [float(x) for x in user_input.split()]

        if len(numbers) == 0:
            print("No valid numbers found.")
            return None

        return numbers
    except ValueError:
        print("Invalid input. Please enter only numbers separated by spaces.")
        return None


def calculate_mean(numbers):
    """Calculate the arithmetic mean (average)."""
    return sum(numbers) / len(numbers)


def calculate_median(numbers):
    """Calculate the median (middle value)."""
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)

    if n % 2 == 0:
        # Even number of elements - average of two middle values
        return (sorted_numbers[n // 2 - 1] + sorted_numbers[n // 2]) / 2
    else:
        # Odd number of elements - middle value
        return sorted_numbers[n // 2]


def calculate_mode(numbers):
    """
    Calculate the mode (most frequent value).
    Returns list of modes if multiple values have same highest frequency.
    """
    frequency = {}
    for num in numbers:
        frequency[num] = frequency.get(num, 0) + 1

    max_freq = max(frequency.values())
    modes = [num for num, freq in frequency.items() if freq == max_freq]

    # If all numbers appear with same frequency, there's no mode
    if len(modes) == len(frequency):
        return None

    return modes


def calculate_range(numbers):
    """Calculate the range (difference between max and min)."""
    return max(numbers) - min(numbers)


def calculate_variance(numbers):
    """Calculate the variance."""
    mean = calculate_mean(numbers)
    squared_diff = [(x - mean) ** 2 for x in numbers]
    return sum(squared_diff) / len(numbers)


def calculate_std_deviation(numbers):
    """Calculate the standard deviation."""
    return math.sqrt(calculate_variance(numbers))


def calculate_sum(numbers):
    """Calculate the sum of all numbers."""
    return sum(numbers)


def calculate_all_statistics(numbers):
    """
    Calculate all statistics for the given numbers.

    Returns:
        Dictionary containing all statistical measures
    """
    stats = {
        'count': len(numbers),
        'sum': calculate_sum(numbers),
        'mean': calculate_mean(numbers),
        'median': calculate_median(numbers),
        'mode': calculate_mode(numbers),
        'range': calculate_range(numbers),
        'min': min(numbers),
        'max': max(numbers),
        'variance': calculate_variance(numbers),
        'std_dev': calculate_std_deviation(numbers)
    }

    return stats


def display_statistics(numbers, stats):
    """Display all calculated statistics in a formatted way."""
    print("\n" + "=" * 60)
    print("STATISTICAL ANALYSIS RESULTS")
    print("=" * 60)

    # Display the dataset
    print(f"\nDataset: {', '.join(map(str, numbers))}")

    print("\n" + "-" * 60)
    print("BASIC STATISTICS")
    print("-" * 60)
    print(f"Count:              {stats['count']}")
    print(f"Sum:                {stats['sum']:.4f}")
    print(f"Minimum:            {stats['min']:.4f}")
    print(f"Maximum:            {stats['max']:.4f}")
    print(f"Range:              {stats['range']:.4f}")

    print("\n" + "-" * 60)
    print("MEASURES OF CENTRAL TENDENCY")
    print("-" * 60)
    print(f"Mean (Average):     {stats['mean']:.4f}")
    print(f"Median:             {stats['median']:.4f}")

    if stats['mode'] is None:
        print(f"Mode:               No mode (all values appear equally)")
    elif len(stats['mode']) == 1:
        print(f"Mode:               {stats['mode'][0]:.4f}")
    else:
        modes_str = ', '.join([f"{m:.4f}" for m in stats['mode']])
        print(f"Mode:               {modes_str} (multimodal)")

    print("\n" + "-" * 60)
    print("MEASURES OF DISPERSION")
    print("-" * 60)
    print(f"Variance:           {stats['variance']:.4f}")
    print(f"Standard Deviation: {stats['std_dev']:.4f}")

    print("=" * 60)


def display_menu():
    """Display the main menu."""
    print("=== Statistics Calculator ===")
    print("1. Calculate all statistics")
    print("2. Calculate specific statistic")
    print("3. Exit")
    print()


def display_specific_menu():
    """Display menu for specific statistics."""
    print("\n=== Choose a Statistic ===")
    print("1. Mean (Average)")
    print("2. Median")
    print("3. Mode")
    print("4. Range")
    print("5. Variance")
    print("6. Standard Deviation")
    print("7. Min and Max")
    print("8. Sum")
    print("9. Back to main menu")
    print()


def calculate_specific_statistic(numbers, choice):
    """Calculate and display a specific statistic."""
    print("\n" + "=" * 60)

    if choice == 1:
        result = calculate_mean(numbers)
        print(f"Mean (Average): {result:.4f}")
    elif choice == 2:
        result = calculate_median(numbers)
        print(f"Median: {result:.4f}")
    elif choice == 3:
        result = calculate_mode(numbers)
        if result is None:
            print("Mode: No mode (all values appear equally)")
        elif len(result) == 1:
            print(f"Mode: {result[0]:.4f}")
        else:
            modes_str = ', '.join([f"{m:.4f}" for m in result])
            print(f"Mode: {modes_str} (multimodal)")
    elif choice == 4:
        result = calculate_range(numbers)
        print(f"Range: {result:.4f}")
    elif choice == 5:
        result = calculate_variance(numbers)
        print(f"Variance: {result:.4f}")
    elif choice == 6:
        result = calculate_std_deviation(numbers)
        print(f"Standard Deviation: {result:.4f}")
    elif choice == 7:
        print(f"Minimum: {min(numbers):.4f}")
        print(f"Maximum: {max(numbers):.4f}")
    elif choice == 8:
        result = calculate_sum(numbers)
        print(f"Sum: {result:.4f}")

    print("=" * 60)


def main():
    """Main program loop."""
    while True:
        clear_screen()
        display_menu()

        try:
            choice = int(input("Enter your choice (1-3): "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("\nPress Enter to continue...")
            continue

        if choice == 3:
            clear_screen()
            print("Thank you for using Statistics Calculator!")
            print("Goodbye!")
            break

        if choice not in [1, 2]:
            print("Invalid choice. Please enter 1, 2, or 3.")
            input("\nPress Enter to continue...")
            continue

        # Get numbers from user
        numbers = get_numbers()

        if numbers is None:
            input("\nPress Enter to continue...")
            continue

        if choice == 1:
            # Calculate all statistics
            stats = calculate_all_statistics(numbers)
            display_statistics(numbers, stats)

            input("\nPress Enter to continue...")

        elif choice == 2:
            # Calculate specific statistic
            while True:
                display_specific_menu()

                try:
                    stat_choice = int(input("Enter your choice (1-9): "))
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    input("\nPress Enter to continue...")
                    continue

                if stat_choice == 9:
                    break

                if stat_choice not in range(1, 9):
                    print("Invalid choice. Please enter a number between 1 and 9.")
                    input("\nPress Enter to continue...")
                    continue

                calculate_specific_statistic(numbers, stat_choice)

                cont = input("\nCalculate another statistic? (y/n): ").strip().lower()
                if cont != 'y':
                    break


if __name__ == "__main__":
    main()
