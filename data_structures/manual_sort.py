# manual_sort.py
# A program to sort a list of numbers using bubble sort
# Does not use built-in sorted() or .sort()

def bubble_sort(numbers):
    # Bubble sort algorithm
    n = len(numbers)
    for i in range(n - 1):  # Repeat passes
        for j in range(n - i - 1):  # Compare adjacent elements
            if numbers[j] > numbers[j + 1]:
                # Swap if out of order
                numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]

def main():
    while True:
        try:
            # Ask user for numbers
            numbers_input = input("Enter numbers separated by spaces: ")

            # Convert input string to list of integers
            numbers = [int(x) for x in numbers_input.split()]
        except ValueError:
            # Handle invalid input
            print("Please enter numbers separated by spaces.")
            continue

        # Show list before sorting
        print("List before sorting:", numbers)

        # Sort list manually
        bubble_sort(numbers)

        # Show list after sorting
        print("List after sorting:", numbers)

        # Ask if user wants to restart
        restart = input("Do you want to restart the program? (yes/no): ")
        if restart.lower() not in ['yes', 'y']:
            print("Program ended.")
            break

# Run the program
if __name__ == "__main__":
    main()
