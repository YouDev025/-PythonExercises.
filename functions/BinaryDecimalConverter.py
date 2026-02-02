import os


# Clear the screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Validate integer input
def get_int_input(prompt, min_val=None, max_val=None):
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(f"Value must be >= {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"Value must be <= {max_val}.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter an integer.")


# Validate binary string input
def get_binary_input(prompt):
    while True:
        value = input(prompt).strip()
        if value and all(ch in "01" for ch in value):
            return value
        print("Invalid input. Please enter a binary number (only 0s and 1s).")


# Validate hexadecimal string input
def get_hex_input(prompt):
    while True:
        value = input(prompt).strip().lower()
        if value and all(ch in "0123456789abcdef" for ch in value):
            return value
        print("Invalid input. Please enter a hexadecimal number (0-9, A-F).")


# Validate octal string input
def get_octal_input(prompt):
    while True:
        value = input(prompt).strip()
        if value and all(ch in "01234567" for ch in value):
            return value
        print("Invalid input. Please enter an octal number (only 0-7).")


# Convert binary to decimal
def binary_to_decimal(binary_str):
    try:
        return int(binary_str, 2)
    except ValueError:
        return None


# Convert decimal to binary
def decimal_to_binary(decimal_int):
    return bin(decimal_int)[2:]


# Convert hexadecimal to decimal
def hex_to_decimal(hex_str):
    try:
        return int(hex_str, 16)
    except ValueError:
        return None


# Convert decimal to hexadecimal
def decimal_to_hex(decimal_int):
    return hex(decimal_int)[2:].upper()


# Convert octal to decimal
def octal_to_decimal(octal_str):
    try:
        return int(octal_str, 8)
    except ValueError:
        return None


# Convert decimal to octal
def decimal_to_octal(decimal_int):
    return oct(decimal_int)[2:]


# Display conversion result with all bases
def display_all_conversions(decimal_val):
    print("\n" + "=" * 50)
    print("CONVERSION RESULTS:")
    print("=" * 50)
    print(f"Decimal:     {decimal_val}")
    print(f"Binary:      {decimal_to_binary(decimal_val)}")
    print(f"Hexadecimal: {decimal_to_hex(decimal_val)}")
    print(f"Octal:       {decimal_to_octal(decimal_val)}")
    print("=" * 50 + "\n")


# Menu logic
def converter_menu():
    clear_screen()
    print("=" * 50)
    print("   NUMBER BASE CONVERTER")
    print("=" * 50)
    print("1. Binary to Decimal")
    print("2. Decimal to Binary")
    print("3. Hexadecimal to Decimal")
    print("4. Decimal to Hexadecimal")
    print("5. Octal to Decimal")
    print("6. Decimal to Octal")
    print("7. Convert Decimal to All Bases")
    print("8. Convert Any Base to All Bases")
    print("9. Exit")
    print("=" * 50)

    choice = get_int_input("Select an option (1-9): ", 1, 9)

    if choice == 1:
        binary_str = get_binary_input("Enter a binary number: ")
        decimal_val = binary_to_decimal(binary_str)
        if decimal_val is not None:
            print(f"\nBinary: {binary_str}")
            print(f"Decimal: {decimal_val}\n")
        else:
            print("\nError during conversion.\n")

    elif choice == 2:
        decimal_val = get_int_input("Enter a decimal number (>=0): ", 0)
        binary_str = decimal_to_binary(decimal_val)
        print(f"\nDecimal: {decimal_val}")
        print(f"Binary: {binary_str}\n")

    elif choice == 3:
        hex_str = get_hex_input("Enter a hexadecimal number: ")
        decimal_val = hex_to_decimal(hex_str)
        if decimal_val is not None:
            print(f"\nHexadecimal: {hex_str.upper()}")
            print(f"Decimal: {decimal_val}\n")
        else:
            print("\nError during conversion.\n")

    elif choice == 4:
        decimal_val = get_int_input("Enter a decimal number (>=0): ", 0)
        hex_str = decimal_to_hex(decimal_val)
        print(f"\nDecimal: {decimal_val}")
        print(f"Hexadecimal: {hex_str}\n")

    elif choice == 5:
        octal_str = get_octal_input("Enter an octal number: ")
        decimal_val = octal_to_decimal(octal_str)
        if decimal_val is not None:
            print(f"\nOctal: {octal_str}")
            print(f"Decimal: {decimal_val}\n")
        else:
            print("\nError during conversion.\n")

    elif choice == 6:
        decimal_val = get_int_input("Enter a decimal number (>=0): ", 0)
        octal_str = decimal_to_octal(decimal_val)
        print(f"\nDecimal: {decimal_val}")
        print(f"Octal: {octal_str}\n")

    elif choice == 7:
        decimal_val = get_int_input("Enter a decimal number (>=0): ", 0)
        display_all_conversions(decimal_val)

    elif choice == 8:
        clear_screen()
        print("=" * 50)
        print("SELECT INPUT BASE:")
        print("=" * 50)
        print("1. Binary")
        print("2. Hexadecimal")
        print("3. Octal")
        print("=" * 50)
        base_choice = get_int_input("Select input base (1-3): ", 1, 3)

        decimal_val = None
        if base_choice == 1:
            binary_str = get_binary_input("Enter a binary number: ")
            decimal_val = binary_to_decimal(binary_str)
        elif base_choice == 2:
            hex_str = get_hex_input("Enter a hexadecimal number: ")
            decimal_val = hex_to_decimal(hex_str)
        elif base_choice == 3:
            octal_str = get_octal_input("Enter an octal number: ")
            decimal_val = octal_to_decimal(octal_str)

        if decimal_val is not None:
            display_all_conversions(decimal_val)
        else:
            print("\nError during conversion.\n")

    elif choice == 9:
        print("\nExiting Number Base Converter. Goodbye!")
        return False

    return True


# Program loop
def main():
    while True:
        if not converter_menu():
            break
        again = input("Do you want another conversion? (y/n): ").strip().lower()
        if again == "n":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()