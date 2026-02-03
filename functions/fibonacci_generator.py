"""
fibonacci_generator.py

This program generates the Fibonacci sequence based on user input.
The user specifies how many terms to generate and can choose between
an iterative or recursive method. Input is validated to ensure it is
a positive integer. The sequence is displayed clearly in one line.
The user can also choose to run the program again without restarting.
"""

# Generate Fibonacci sequence using an iterative approach
def generate_fibonacci_iterative(n_terms):
    sequence = []
    a, b = 0, 1
    for _ in range(n_terms):
        sequence.append(a)
        a, b = b, a + b
    return sequence

# Generate Fibonacci sequence using recursion
def generate_fibonacci_recursive(n_terms, a=0, b=1, sequence=None):
    if sequence is None:
        sequence = []
    if n_terms == 0:
        return sequence
    sequence.append(a)
    return generate_fibonacci_recursive(n_terms - 1, b, a + b, sequence)

# Prompt the user until they enter a valid positive integer
def get_positive_integer(prompt):
    while True:
        try:
            integer = int(input(prompt))
            if integer > 0:
                return integer
            else:
                print("Please enter a positive integer.")
        except ValueError:
            print("Invalid input. Please enter a positive integer.")

# Ask the user if they want to try again
def ask_try_again():
    while True:
        choice = input("Do you want to try again? (yes/no): ").strip().lower()
        if choice in ("yes", "y"):
            return True
        elif choice in ("no", "n"):
            return False
        else:
            print("Invalid choice. Please enter 'yes' or 'no'.")

# Main function to run the Fibonacci generator program
def main():
    print("-" * 40)
    print("Welcome to the Fibonacci Sequence Generator")
    print("-" * 40)

    while True:
        n_terms = get_positive_integer("How many terms would you like to generate? : ")

        # Ask user for method choice
        method = ""
        while method not in ("iterative", "recursive"):
            method = input("Please enter either 'iterative' or 'recursive': ").strip().lower()
            if method not in ("iterative", "recursive"):
                print("Error: Invalid input. Please enter 'iterative' or 'recursive'.")

        # Generate sequence
        if method == "iterative":
            fib_sequence = generate_fibonacci_iterative(n_terms)
        else:
            fib_sequence = generate_fibonacci_recursive(n_terms)

        # Display result
        print("-" * 40)
        print("Fibonacci Sequence:")
        print(" ".join(map(str, fib_sequence)))
        print("-" * 40)

        # Ask if user wants to try again
        if not ask_try_again():
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()
