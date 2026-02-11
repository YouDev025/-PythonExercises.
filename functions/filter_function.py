"""
filter_function.py
Interactive program demonstrating a custom filtering function with
robust input validation, error handling, and comparison to Python's built-in filter().
"""

def custom_filter(data_list, condition_func):
    """
    Custom filtering function.
    Parameters:
        data_list (list): The list of elements to filter.
        condition_func (function): A function that returns True/False for each element.
    Returns:
        list: A new list containing only elements that satisfy the condition.
    """
    # Validate inputs
    if not isinstance(data_list, list):
        raise TypeError("First argument must be a list.")
    if not callable(condition_func):
        raise TypeError("Second argument must be a function.")

    result = []
    for item in data_list:
        try:
            # Apply condition safely
            if condition_func(item):
                result.append(item)
        except Exception as e:
            # Skip items that cause errors
            print(f"Skipping item {item} due to error: {e}")
    return result


def get_numbers_from_user():
    """
    Ask the user to input a list of numbers separated by spaces.
    Returns a list of integers.
    """
    while True:
        user_input = input("Enter numbers separated by spaces: ").strip()
        try:
            numbers = [int(x) for x in user_input.split()]
            return numbers
        except ValueError:
            print("Invalid input. Please enter only integers separated by spaces.")


def get_words_from_user():
    """
    Ask the user to input a list of words separated by spaces.
    Returns a list of strings.
    """
    while True:
        user_input = input("Enter words separated by spaces: ").strip()
        if user_input:
            words = user_input.split()
            return words
        else:
            print("Invalid input. Please enter at least one word.")


def filter_numbers():
    # Ask user to provide their own list
    numbers = get_numbers_from_user()
    print("\nYour numbers:", numbers)
    print("Choose a filter:")
    print("1. Even numbers")
    print("2. Numbers greater than 10")

    choice = input("Enter choice: ").strip()
    if choice == "1":
        result = custom_filter(numbers, lambda x: isinstance(x, int) and x % 2 == 0)
    elif choice == "2":
        result = custom_filter(numbers, lambda x: isinstance(x, int) and x > 10)
    else:
        print("Invalid choice.")
        return

    # Show both custom and built-in filter results
    print("Filtered (custom):", result)
    print("Filtered (built-in):", list(filter(lambda x: isinstance(x, int) and (x % 2 == 0 if choice == "1" else x > 10), numbers)))


def filter_strings():
    # Ask user to provide their own list
    words = get_words_from_user()
    print("\nYour words:", words)
    print("Choose a filter:")
    print("1. Words longer than 5 characters")
    print("2. Words starting with 'a'")

    choice = input("Enter choice: ").strip()
    if choice == "1":
        result = custom_filter(words, lambda s: isinstance(s, str) and len(s) > 5)
    elif choice == "2":
        result = custom_filter(words, lambda s: isinstance(s, str) and s.startswith("a"))
    else:
        print("Invalid choice.")
        return

    # Show both custom and built-in filter results
    print("Filtered (custom):", result)
    print("Filtered (built-in):", list(filter(lambda s: isinstance(s, str) and (len(s) > 5 if choice == "1" else s.startswith("a")), words)))


def main():
    # Main interactive loop
    while True:
        print("\n=== Custom Filter Interactive Menu ===")
        print("1. Filter numbers")
        print("2. Filter strings")
        print("3. Exit")

        choice = input("Enter choice: ").strip()
        if choice == "1":
            filter_numbers()
        elif choice == "2":
            filter_strings()
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
