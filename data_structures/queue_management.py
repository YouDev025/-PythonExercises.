# ============================================================
# queue_management.py - Simple Queue Manager
#
# This program simulates a real-life queue (like a waiting line).
# It follows the FIFO rule: First In, First Out —
# meaning the first person to join is the first to be served.
#
# Features:
#   - Add a person to the end of the queue
#   - Remove (serve) the first person in the queue
#   - Display everyone currently in the queue
#   - Check if the queue is empty
#
# Built using a plain Python list — no external libraries needed.
# ============================================================


# ---- Queue Functions ----

def add_person(queue, name):
    """
    Adds a person to the END of the queue.
    This is the 'enqueue' operation in FIFO.
    """
    queue.append(name)  # append() adds to the end of the list
    print(f"\n  ✓ '{name}' has been added to the queue.")


def remove_person(queue):
    """
    Removes and returns the FIRST person in the queue.
    This is the 'dequeue' operation in FIFO.
    The person who waited the longest gets served first.
    """
    if is_empty(queue):
        # Can't remove from an empty queue
        print("\n  ✗ The queue is empty. No one to remove.")
    else:
        # pop(0) removes the item at index 0 (the first person)
        served = queue.pop(0)
        print(f"\n  ✓ '{served}' has been served and removed from the queue.")


def display_queue(queue):
    """
    Displays all the people currently in the queue,
    from first (front) to last (back).
    """
    if is_empty(queue):
        print("\n  The queue is currently empty.")
    else:
        print("\n  --- Current Queue ---")
        print("  [FRONT]")
        # Loop through the queue and show each person with their position
        for position, name in enumerate(queue, start=1):
            print(f"    {position}. {name}")
        print("  [BACK]")
        print(f"\n  Total people in queue: {len(queue)}")


def is_empty(queue):
    """
    Checks whether the queue has no people in it.
    Returns True if empty, False if there is at least one person.
    """
    return len(queue) == 0  # True if length is 0, False otherwise


def check_empty(queue):
    """
    Prints a user-friendly message about whether the queue is empty.
    Calls is_empty() internally.
    """
    if is_empty(queue):
        print("\n  The queue is EMPTY. No one is waiting.")
    else:
        print(f"\n  The queue is NOT empty. {len(queue)} person(s) are waiting.")


# ---- Menu ----

def show_menu():
    """
    Prints the main menu options to the screen.
    """
    print("\n" + "=" * 40)
    print("       QUEUE MANAGEMENT SYSTEM")
    print("=" * 40)
    print("  1. Add a person to the queue")
    print("  2. Serve (remove) the first person")
    print("  3. Display the queue")
    print("  4. Check if the queue is empty")
    print("  5. Exit")
    print("=" * 40)


# ---- Main Program ----

# This is the queue — just an empty list to start
queue = []

print("\nWelcome to the Queue Management System!")
print("This program simulates a waiting line (FIFO).")

while True:
    # Show the menu on every loop iteration
    show_menu()

    # Ask the user to pick an option
    choice = input("  Enter your choice (1-5): ").strip()

    if choice == "1":
        # Add a person — ask for their name first
        name = input("\n  Enter the person's name: ").strip()
        if name == "":
            print("\n  ✗ Name cannot be empty. Please try again.")
        else:
            add_person(queue, name)

    elif choice == "2":
        # Serve (remove) the first person in the queue
        remove_person(queue)

    elif choice == "3":
        # Show the full queue
        display_queue(queue)

    elif choice == "4":
        # Tell the user if the queue is empty or not
        check_empty(queue)

    elif choice == "5":
        # Exit the program
        print("\n  Goodbye! Thanks for using the Queue Manager.")
        break

    else:
        # The user typed something that isn't 1–5
        print("\n  ✗ Invalid choice. Please enter a number between 1 and 5.")