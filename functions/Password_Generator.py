"""
password_generator.py

This program generates secure random passwords based on user preferences.
The user specifies the desired password length and which character types
to include (uppercase, lowercase, digits, symbols). Input is validated to
ensure a minimum length and at least one character type selected.

Bonus features:
- Generate multiple passwords at once
- Copy the generated password(s) to clipboard (requires pyperclip)
- Display a simple password strength indicator
- Ask the user if they like the password or want another one
"""

import string
import secrets

try:
    import pyperclip  # optional for clipboard support
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


def get_positive_integer(prompt, min_value=1):
    """Prompt the user until they enter a valid positive integer >= min_value."""
    while True:
        try:
            value = int(input(prompt))
            if value >= min_value:
                return value
            else:
                print(f"Please enter an integer greater than or equal to {min_value}.")
        except ValueError:
            print("Invalid input. Please enter a positive integer.")


def ask_yes_no(prompt):
    """Prompt the user for a yes/no answer and return True/False."""
    while True:
        choice = input(prompt + " (y/n): ").strip().lower()
        if choice in ("y", "yes"):
            return True
        elif choice in ("n", "no"):
            return False
        else:
            print("Invalid choice. Please enter 'y' or 'n'.")


def build_character_pool(include_upper, include_lower, include_digits, include_symbols):
    """Build the pool of characters based on user choices."""
    pool = ""
    if include_upper:
        pool += string.ascii_uppercase
    if include_lower:
        pool += string.ascii_lowercase
    if include_digits:
        pool += string.digits
    if include_symbols:
        pool += string.punctuation
    return pool


def generate_password(length, pool):
    """Generate a secure random password of given length from the pool."""
    return "".join(secrets.choice(pool) for _ in range(length))


def password_strength(password):
    """Simple strength indicator based on length and variety of characters."""
    score = 0
    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1

    if score >= 6:
        return "Strong"
    elif score >= 4:
        return "Medium"
    else:
        return "Weak"


def main():
    print("-" * 40)
    print("Welcome to the Secure Password Generator")
    print("-" * 40)

    # Ask for password length
    length = get_positive_integer("Enter desired password length: ", min_value=4)

    # Ask which character types to include
    include_upper = ask_yes_no("Include uppercase letters?")
    include_lower = ask_yes_no("Include lowercase letters?")
    include_digits = ask_yes_no("Include digits?")
    include_symbols = ask_yes_no("Include symbols?")

    # Validate at least one type selected
    if not (include_upper or include_lower or include_digits or include_symbols):
        print("Error: You must select at least one character type.")
        return

    # Build character pool
    pool = build_character_pool(include_upper, include_lower, include_digits, include_symbols)

    while True:
        # Generate password
        pwd = generate_password(length, pool)
        print("\nGenerated Password:")
        print(pwd)
        print(f"Strength: {password_strength(pwd)}")

        # Copy to clipboard if available
        if CLIPBOARD_AVAILABLE:
            pyperclip.copy(pwd)
            print("-> Password copied to clipboard!")

        # Ask if user likes it
        if ask_yes_no("Do you like this password?"):
            print("Great! Use it safely.")
            break
        else:
            print("Okay, let's generate another one...")

    print("-" * 40)
    print("Goodbye!")


if __name__ == "__main__":
    main()
