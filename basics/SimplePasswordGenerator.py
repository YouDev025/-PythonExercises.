import random
import string

while True:
    print("=" * 50)
    print("Simple Password Generator")
    print("=" * 50)
    print("1. Generate password")
    print("2. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        try:
            length_password = int(input("Enter the password length: "))
        except ValueError:
            print("Please enter a valid number.")
        else:
            # Use letters, digits, and punctuation
            chars = string.ascii_letters + string.digits + string.punctuation
            password = "".join(random.choice(chars) for _ in range(length_password))

            print("=" * 50)
            print("Your password is:", password)
            print("=" * 50)
        input("Press Enter to continue...")

    elif choice == "2":
        confirm_exit = input("Are you sure you want to exit? (y/n): ")
        if confirm_exit.lower() == "y":
            print("Exiting...")
            break
    else:
        print("Please enter a valid choice.")
