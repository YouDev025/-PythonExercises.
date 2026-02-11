"""
custom_map_function.py
Interactive program demonstrating a custom version of Python's built-in map() function.
Includes input validation, error handling, and comparison with the built-in map().
"""

def custom_map(data_list, transform_func):
    """
    Custom map function.
    Parameters:
        data_list (list): The list of elements to transform.
        transform_func (function): A function that transforms each element.
    Returns:
        list: A new list containing transformed elements.
    """
    # Validate inputs
    if not isinstance(data_list, list):
        raise TypeError("First argument must be a list.")
    if not callable(transform_func):
        raise TypeError("Second argument must be a function.")

    result = []
    for item in data_list:
        try:
            # Apply transformation safely
            result.append(transform_func(item))
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


def map_numbers():
    # Ask user to provide their own list
    numbers = get_numbers_from_user()
    print("\nYour numbers:", numbers)
    print("Choose a transformation:")
    print("1. Square numbers")
    print("2. Double values")

    choice = input("Enter choice: ").strip()
    if choice == "1":
        result = custom_map(numbers, lambda x: x ** 2)
    elif choice == "2":
        result = custom_map(numbers, lambda x: x * 2)
    else:
        print("Invalid choice.")
        return

    # Show both custom and built-in map results
    print("Transformed (custom):", result)
    print("Transformed (built-in):", list(map(lambda x: x ** 2 if choice == "1" else x * 2, numbers)))


def map_strings():
    # Ask user to provide their own list
    words = get_words_from_user()
    print("\nYour words:", words)
    print("Choose a transformation:")
    print("1. Convert to uppercase")
    print("2. Reverse strings")

    choice = input("Enter choice: ").strip()
    if choice == "1":
        result = custom_map(words, lambda s: s.upper())
    elif choice == "2":
        result = custom_map(words, lambda s: s[::-1])
    else:
        print("Invalid choice.")
        return

    # Show both custom and built-in map results
    print("Transformed (custom):", result)
    print("Transformed (built-in):", list(map(lambda s: s.upper() if choice == "1" else s[::-1], words)))


def main():
    # Main interactive loop
    while True:
        print("\n=== Custom Map Interactive Menu ===")
        print("1. Transform numbers")
        print("2. Transform strings")
        print("3. Exit")

        choice = input("Enter choice: ").strip()
        if choice == "1":
            map_numbers()
        elif choice == "2":
            map_strings()
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
