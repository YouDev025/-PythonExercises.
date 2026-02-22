"""
User History Tracker
--------------------
A simple program to track user actions or activities.
Users can add actions, view their history, clear it, and optionally save/load history from a text file.

Author: Youssef Adardour
Date: February 2026
"""

# List to store history in memory
history = []


# Function to add an action
def add_action():
    action = input("Enter an action/activity: ").strip()
    if action:
        history.append(action)
        print(f"Action '{action}' added to history.\n")
    else:
        print("Invalid input! Action not added.\n")


# Function to display history
def display_history():
    if not history:
        print("History is empty.\n")
    else:
        print("\n--- User History ---")
        for idx, action in enumerate(history, start=1):
            print(f"{idx}. {action}")
        print()


# Function to clear history
def clear_history():
    confirm = input("Are you sure you want to clear history? (y/n): ").strip().lower()
    if confirm == "y":
        history.clear()
        print("History cleared.\n")
    else:
        print("Clear operation canceled.\n")


# Function to save history to a file
def save_history(filename="history.txt"):
    try:
        with open(filename, "w") as file:
            for action in history:
                file.write(action + "\n")
        print(f"History saved to {filename}.\n")
    except Exception as e:
        print(f"Error saving history: {e}\n")


# Function to load history from a file
def load_history(filename="history.txt"):
    try:
        with open(filename, "r") as file:
            loaded = [line.strip() for line in file.readlines()]
            history.clear()
            history.extend(loaded)
        print(f"History loaded from {filename}.\n")
    except FileNotFoundError:
        print(f"No history file found ({filename}).\n")
    except Exception as e:
        print(f"Error loading history: {e}\n")


# Function to display the menu
def menu():
    while True:
        print("User History Tracker Menu")
        print("1. Add Action")
        print("2. View History")
        print("3. Clear History")
        print("4. Save History")
        print("5. Load History")
        print("6. Exit")

        choice = input("Enter choice (1-6): ").strip()

        if choice == "1":
            add_action()
        elif choice == "2":
            display_history()
        elif choice == "3":
            clear_history()
        elif choice == "4":
            save_history()
        elif choice == "5":
            load_history()
        elif choice == "6":
            print("Exiting User History Tracker. Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.\n")


# Run the program
if __name__ == "__main__":
    menu()
