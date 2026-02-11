"""
custom_reduce_function.py
Interactive program demonstrating a custom version of Python's reduce() function.
Includes input validation, error handling, and comparison with functools.reduce().
"""

from functools import reduce

def custom_reduce(data_list, operation_func, initial=None):
    """
    Custom reduce function.
    Parameters:
        data_list (list): The list of elements to reduce.
        operation_func (function): A binary function that combines two elements.
        initial (optional): Initial value to start reduction.
    Returns:
        result: A single reduced value.
    """
    # Validate inputs
    if not isinstance(data_list, list):
        raise TypeError("First argument must be a list.")
    if not callable(operation_func):
        raise TypeError("Second argument must be a function.")

    # Handle empty list case
    if not data_list and initial is None:
        raise ValueError("Reduce of empty list with no initial value.")

    # Start with initial value if provided, else first element
    iterator = iter(data_list)
    if initial is None:
        result = next(iterator)
    else:
        result = initial

    # Apply operation iteratively
    for item in iterator:
        try:
            result = operation_func(result, item)
        except Exception as e:
            print(f"Skipping item {item} due to error: {e}")
    return result


def get_numbers_from_user():
    """Ask the user to input a list of numbers separated by spaces."""
    while True:
        user_input = input("Enter numbers separated by spaces: ").strip()
        try:
            numbers = [int(x) for x in user_input.split()]
            return numbers
        except ValueError:
            print("Invalid input. Please enter only integers separated by spaces.")


def get_words_from_user():
    """Ask the user to input a list of words separated by spaces."""
    while True:
        user_input = input("Enter words separated by spaces: ").strip()
        if user_input:
            return user_input.split()
        else:
            print("Invalid input. Please enter at least one word.")


def reduce_numbers():
    numbers = get_numbers_from_user()
    print("\nYour numbers:", numbers)
    print("Choose a reduction operation:")
    print("1. Sum")
    print("2. Product")
    print("3. Maximum value")

    choice = input("Enter choice: ").strip()
    if choice == "1":
        result_custom = custom_reduce(numbers, lambda a, b: a + b)
        result_builtin = reduce(lambda a, b: a + b, numbers)
    elif choice == "2":
        result_custom = custom_reduce(numbers, lambda a, b: a * b)
        result_builtin = reduce(lambda a, b: a * b, numbers)
    elif choice == "3":
        result_custom = custom_reduce(numbers, lambda a, b: a if a > b else b)
        result_builtin = reduce(lambda a, b: a if a > b else b, numbers)
    else:
        print("Invalid choice.")
        return

    print("Reduced (custom):", result_custom)
    print("Reduced (functools.reduce):", result_builtin)


def reduce_strings():
    words = get_words_from_user()
    print("\nYour words:", words)
    print("Choose a reduction operation:")
    print("1. Concatenate all words")

    choice = input("Enter choice: ").strip()
    if choice == "1":
        result_custom = custom_reduce(words, lambda a, b: a + b)
        result_builtin = reduce(lambda a, b: a + b, words)
    else:
        print("Invalid choice.")
        return

    print("Reduced (custom):", result_custom)
    print("Reduced (functools.reduce):", result_builtin)


def main():
    # Main interactive loop
    while True:
        print("\n=== Custom Reduce Interactive Menu ===")
        print("1. Reduce numbers")
        print("2. Reduce strings")
        print("3. Exit")

        choice = input("Enter choice: ").strip()
        if choice == "1":
            reduce_numbers()
        elif choice == "2":
            reduce_strings()
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
