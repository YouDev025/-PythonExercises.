import random  # Import the random module to generate random numbers

# Infinite loop to keep showing the menu until the user chooses to exit
while True:
    print("=" * 50)
    print("Welcome to Dice Roll Simulator")
    print("=" * 50)
    print("1. Roll a dice")
    print("2. Exit the game")

    # Get the user's choice (always a string from input)
    choice = input("Enter your choice: ")

    # Option 1: Roll the dice
    if choice == "1":
        print("-" * 50)
        print("Let's roll a dice!")
        print("-" * 50)

        # Generate a random number between 1 and 6 (like a real dice)
        dice = random.randint(1, 6)

        # Display the result
        print("=" * 50)
        print(f"You rolled: {dice}")
        print("=" * 50)

        # Pause so the user can see the result before continuing
        input("Press Enter to continue...")

    # Option 2: Exit the game
    elif choice == "2":
        # Ask for confirmation before exiting
        confirm_exit = input("Are you sure you want to exit the game? (y/n): ")
        if confirm_exit.lower() == "y":
            print("Exiting the game... see you next time!")
            break  # End the loop and exit the program

    # Handle invalid choices
    else:
        print("Please enter a valid choice.")
