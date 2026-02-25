"""
Interactive Advanced Statistics System
--------------------------------------
This program allows users to enter numerical values, store them in a list,
and compute advanced statistics such as mean, median, mode, variance,
standard deviation, quartiles, and outlier detection.

Author: Youssef Adardour
Date: 2026-02-25
"""

import math

# -----------------------------
# Data Structures
# -----------------------------
values = []  # List to store numerical values
statistics = {}  # Dictionary to store computed statistics
# Mode will use a dictionary for frequency counting


# -----------------------------
# Helper Functions
# -----------------------------
def validate_input(user_input):
    """Validate if input is a number (int or float)."""
    try:
        return float(user_input)
    except ValueError:
        return None


def calculate_mean(data):
    return sum(data) / len(data)


def calculate_median(data):
    sorted_data = sorted(data)
    n = len(sorted_data)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2
    else:
        return sorted_data[mid]


def calculate_mode(data):
    freq = {}
    for num in data:
        freq[num] = freq.get(num, 0) + 1
    max_freq = max(freq.values())
    modes = [k for k, v in freq.items() if v == max_freq]
    return modes if len(modes) > 1 else modes[0]


def calculate_variance(data):
    mean = calculate_mean(data)
    return sum((x - mean) ** 2 for x in data) / len(data)


def calculate_std_dev(data):
    return math.sqrt(calculate_variance(data))


def calculate_quartiles(data):
    sorted_data = sorted(data)
    n = len(sorted_data)
    mid = n // 2

    if n % 2 == 0:
        lower_half = sorted_data[:mid]
        upper_half = sorted_data[mid:]
    else:
        lower_half = sorted_data[:mid]
        upper_half = sorted_data[mid + 1:]

    q1 = calculate_median(lower_half)
    q2 = calculate_median(sorted_data)
    q3 = calculate_median(upper_half)

    return q1, q2, q3


def detect_outliers(data):
    q1, _, q3 = calculate_quartiles(data)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = [x for x in data if x < lower_bound or x > upper_bound]
    return outliers


def compute_statistics(data):
    """Compute all statistics and store them in a dictionary."""
    global statistics
    statistics = {
        "Mean": calculate_mean(data),
        "Median": calculate_median(data),
        "Mode": calculate_mode(data),
        "Variance": calculate_variance(data),
        "Standard Deviation": calculate_std_dev(data),
        "Minimum": min(data),
        "Maximum": max(data),
        "Quartiles": calculate_quartiles(data),
        "Outliers": detect_outliers(data),
        "Sorted Values": sorted(data),
        "Unique Values": set(data)  # Using set for uniqueness
    }


def display_statistics():
    """Display computed statistics neatly."""
    for key, value in statistics.items():
        print(f"{key}: {value}")


# -----------------------------
# Menu System
# -----------------------------
def menu():
    while True:
        print("\n--- Interactive Advanced Statistics System ---")
        print("1. Enter numerical values")
        print("2. Display all values")
        print("3. Show statistics")
        print("4. Clear data")
        print("5. Exit program")

        choice = input("Choose an option (1-5): ")

        if choice == "1":
            user_input = input("Enter a number: ")
            num = validate_input(user_input)
            if num is not None:
                values.append(num)
                print("Value added successfully.")
            else:
                print("Invalid input. Please enter a valid number.")

        elif choice == "2":
            print("Values:", values if values else "No data entered yet.")

        elif choice == "3":
            if values:
                compute_statistics(values)
                display_statistics()
            else:
                print("No data available. Please enter values first.")

        elif choice == "4":
            values.clear()
            statistics.clear()
            print("Data cleared successfully.")

        elif choice == "5":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option.")


# -----------------------------
# Program Entry Point
# -----------------------------
if __name__ == "__main__":
    menu()
