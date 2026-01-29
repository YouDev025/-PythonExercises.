# Fibonacci Sequence Generator

while True:
    print("-" * 40)
    print("Welcome to Fibonacci Sequence Generator")
    print("-" * 40)
    print("1. Generate Fibonacci Sequence")
    print("2. Exit the program")

    choice = input("Enter your choice: ")

    if choice == "1":
        try:
            number = int(input("Enter how many terms you want to generate: "))
        except ValueError:
            # Handle invalid input
            print("Error: Please enter a positive integer. Valid number!")
        else:
            # Initialize first two Fibonacci numbers
            a, b = 0, 1
            sequence = []
            for _ in range(number):
                sequence.append(a)   # Append 'a' to start with 0
                a, b = b, a + b      # Update values for next term

            # Display the sequence
            print("=" * 50)
            print(f"Fibonacci Sequence: {sequence}")
            print("=" * 50)

        input("Press Enter to continue...")

    elif choice == "2":
        confirm_exit = input("Do you want to exit the program? (y/n): ")
        if confirm_exit.lower() == "y":
            print("Thank you for using Fibonacci Sequence Generator")
            break

    else:
        print("Please enter a valid choice.")
