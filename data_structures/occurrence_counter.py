"""
Occurrence Counter Using Data Structures
----------------------------------------
This program counts the occurrences of elements (numbers or words) entered by the user.
It displays each element's frequency, the most frequent element, and the least frequent element.

Author: Youssef Adardour
Date: February 2026
"""


# Function to get user input and store elements in a list
def get_elements():
    """
    Stores all user-entered elements in a list.
    """
    elements = []
    print("Enter elements separated by spaces (numbers or words):")
    user_input = input("> ").split()
    for item in user_input:
        elements.append(item)  # List stores all elements
    return elements


# Function to count occurrences using a dictionary
def count_occurrences(elements):
    """
    Uses a dictionary to count how many times each element appears.
    Keys = elements, Values = frequency counts.
    """
    occurrence_dict = {}
    for item in elements:
        occurrence_dict[item] = occurrence_dict.get(item, 0) + 1
    return occurrence_dict


# Function to display results
def display_results(elements, occurrence_dict):
    """
    Displays frequency of each element, most frequent, and least frequent.
    Also shows unique elements using a set.
    """
    print("\n--- Occurrence Results ---")
    print("All elements:", elements)

    # Set to store unique elements
    unique_elements = set(elements)
    print("Unique elements:", unique_elements)

    print("\nFrequency of each element:")
    for item, count in occurrence_dict.items():
        print(f"{item}: {count}")

    # Find most and least frequent elements
    most_frequent = max(occurrence_dict, key=occurrence_dict.get)
    least_frequent = min(occurrence_dict, key=occurrence_dict.get)

    print(f"\nMost frequent element: {most_frequent} ({occurrence_dict[most_frequent]} times)")
    print(f"Least frequent element: {least_frequent} ({occurrence_dict[least_frequent]} times)")


# Main function
def main():
    try:
        elements = get_elements()
        if not elements:
            print("Error: No elements entered.")
            return
        occurrence_dict = count_occurrences(elements)
        display_results(elements, occurrence_dict)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
