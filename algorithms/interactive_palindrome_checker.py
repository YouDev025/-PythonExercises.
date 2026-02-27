"""
Interactive Palindrome Checker
------------------------------
This program allows the user to check whether a given string is a palindrome.
It provides options to enter text, check single words or sentences, and display results interactively.

Author: Youssef Adardour
Date: 2026-02-27
"""


# Function: Check if a string is a palindrome
def is_palindrome(text):
    """
    Check if the given text is a palindrome.
    - Convert to lowercase
    - Remove spaces and non-alphanumeric characters
    - Compare with reversed version
    """
    cleaned = "".join(ch.lower() for ch in text if ch.isalnum())
    return cleaned == cleaned[::-1]


# Function: Validate user input
def get_valid_string(prompt):
    while True:
        text = input(prompt).strip()
        if text == "":
            print("Please enter a non-empty string.")
        else:
            return text


# Function: Menu system
def menu():
    while True:
        print("\n=== Interactive Palindrome Checker ===")
        print("1. Enter a word or sentence")
        print("2. Check if it is a palindrome")
        print("3. Exit program")

        choice = input("Select an option (1-3): ")

        if choice == "1":
            text = get_valid_string("Enter text: ")
            print(f"Text stored: {text}")

        elif choice == "2":
            text = get_valid_string("Enter text to check: ")
            if is_palindrome(text):
                print(f"'{text}' is a palindrome.")
            else:
                print(f"'{text}' is not a palindrome.")

        elif choice == "3":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option (1-3).")


# Run the program
if __name__ == "__main__":
    menu()
