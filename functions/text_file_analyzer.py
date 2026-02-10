# Function to analyze a text file
def file_analyzer(file_path):
    try:
        # Open file safely with UTF-8 encoding
        with open(file_path, "r", encoding="utf-8") as file:
            lines = 0
            words = 0
            characters = 0

            # Process file line by line (efficient for large files)
            for line in file:
                lines += 1  # Count each line
                words += len(line.split())  # Count words in the line
                characters += len(line)  # Count characters in the line

        return lines, words, characters

    # Handle common errors
    except FileNotFoundError:
        print("Error: File not found. Please enter correct file path.")
        return None
    except PermissionError:
        print("Error: Permission denied. Please enter correct file path.")
        return None
    except Exception as e:
        print(f"Error: Unexpected error {e}. Please enter correct file path.")
        return None


# Main program loop
def main():
    while True:
        print("===== Text File Analyzer =====")
        file_path = input("Enter file path: ")  # Ask user for file path
        result = file_analyzer(file_path)  # Analyze file

        if result:
            lines, words, characters = result
            print("==== Analysis Complete =====")
            print(f"Number of lines: {lines}")
            print(f"Number of words: {words}")
            print(f"Number of characters: {characters}")

        # Ask if user wants to analyze another file
        while True:  # Keep asking until valid input
            user_response = input("Do you want to analyze another file? (y/n): ").strip().lower()
            if user_response == "y":
                print("Returning to main menu...\n")
                break  # Restart main loop
            elif user_response == "n":
                print("Exiting...")
                return  # Exit program
            else:
                print("Invalid input. Please enter 'y' or 'n'.")


# Entry point of the program
if __name__ == "__main__":
    main()
