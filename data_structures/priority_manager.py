# ============================================================
# Priority Manager: A simple task manager that lets users add,
# view, and complete tasks organized by priority level.
# Tasks are sorted High → Medium → Low for easy tracking.
# ============================================================
# Priority order used for sorting tasks
PRIORITY_ORDER = {"High": 1, "Medium": 2, "Low": 3}


def display_menu():
    """Print the main menu options."""
    print("\n╔══════════════════════════╗")
    print("║     PRIORITY MANAGER     ║")
    print("╠══════════════════════════╣")
    print("║ 1. Add task              ║")
    print("║ 2. View tasks            ║")
    print("║ 3. Complete / remove task║")
    print("║ 4. Quit                  ║")
    print("╚══════════════════════════╝")


def get_priority():
    """Prompt the user to choose a valid priority level."""
    print("\nPriority levels: 1) High  2) Medium  3) Low")
    priority_map = {"1": "High", "2": "Medium", "3": "Low"}

    while True:
        choice = input("Select priority (1/2/3): ").strip()
        if choice in priority_map:
            return priority_map[choice]
        print("  Invalid choice. Please enter 1, 2, or 3.")


def add_task(tasks):
    """Add a new task with a name and priority to the task list."""
    name = input("\nTask name: ").strip()
    if not name:
        print("  Task name cannot be empty.")
        return

    priority = get_priority()

    # Each task is stored as a dictionary
    task = {"name": name, "priority": priority, "done": False}
    tasks.append(task)
    print(f"  Task '{name}' added with {priority} priority.")


def view_tasks(tasks):
    """Display all tasks sorted by priority (High first)."""
    if not tasks:
        print("\n  No tasks found. Add one to get started!")
        return

    # Sort tasks using the PRIORITY_ORDER mapping
    sorted_tasks = sorted(tasks, key=lambda t: PRIORITY_ORDER[t["priority"]])

    print("\n  {:<4} {:<30} {:<10} {}".format("#", "Task", "Priority", "Status"))
    print("  " + "-" * 55)

    for i, task in enumerate(sorted_tasks, start=1):
        status = "Done" if task["done"] else "Pending"
        print("  {:<4} {:<30} {:<10} {}".format(
            i, task["name"][:29], task["priority"], status
        ))


def complete_task(tasks):
    """Mark a task as completed or remove it from the list."""
    if not tasks:
        print("\n  No tasks to manage.")
        return

    view_tasks(tasks)

    # Ask which task number to act on
    try:
        choice = int(input("\nEnter task number: "))
    except ValueError:
        print("  Please enter a valid number.")
        return

    # Map display index back to the sorted list
    sorted_tasks = sorted(tasks, key=lambda t: PRIORITY_ORDER[t["priority"]])

    if choice < 1 or choice > len(sorted_tasks):
        print("  Task number out of range.")
        return

    selected = sorted_tasks[choice - 1]

    print(f"\n  Task: '{selected['name']}' [{selected['priority']}]")
    print("  1) Mark as completed")
    print("  2) Remove task")
    print("  3) Cancel")

    action = input("  Choose action (1/2/3): ").strip()

    if action == "1":
        selected["done"] = True
        print(f"  '{selected['name']}' marked as completed.")
    elif action == "2":
        tasks.remove(selected)
        print(f"  '{selected['name']}' removed from the list.")
    elif action == "3":
        print("  Cancelled.")
    else:
        print("  Invalid option.")


def main():
    """Main loop: display menu and route user input to the right function."""
    tasks = []  # All tasks are stored here as a list of dicts

    print("\n  Welcome to Priority Manager!")

    while True:
        display_menu()
        choice = input("Choose an option (1–4): ").strip()

        if choice == "1":
            add_task(tasks)
        elif choice == "2":
            view_tasks(tasks)
        elif choice == "3":
            complete_task(tasks)
        elif choice == "4":
            print("\n  Goodbye! Stay productive.\n")
            break
        else:
            print("  Invalid option. Please enter a number between 1 and 4.")


# Entry point
if __name__ == "__main__":
    main()