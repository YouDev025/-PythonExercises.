"""
Stack Implementation Program
----------------------------
This program demonstrates a basic implementation of a Stack data structure
using Python lists. It provides the following operations:
- push(item): Add an item to the stack
- pop(): Remove the top item from the stack
- peek(): View the top item without removing it
- is_empty(): Check if the stack is empty
- size(): Get the number of items in the stack
- display(): Print a visual representation of the stack.

The program also includes a simple interactive menu for user operations.
Error handling is included to prevent invalid actions (e.g., popping from an empty stack).
"""

stack = []

# ─────────────────────────────────────────────
#  Stack Operations
# ─────────────────────────────────────────────

def push(item):
    """Push an item onto the top of the stack."""
    stack.append(item)
    print(f"  ✔ '{item}' pushed onto the stack.")


def pop():
    """Remove and return the top item from the stack."""
    if is_empty():
        print("  ✘ Error: Cannot pop from an empty stack.")
        return None
    item = stack.pop()
    print(f"  ✔ '{item}' popped from the stack.")
    return item


def peek():
    """Return the top item without removing it."""
    if is_empty():
        print("  ✘ Error: Cannot peek at an empty stack.")
        return None
    print(f"  ✔ Top item is: '{stack[-1]}'")
    return stack[-1]


def is_empty():
    """Return True if the stack has no items."""
    return len(stack) == 0


def size():
    """Return the number of items in the stack."""
    print(f"  ✔ Stack size: {len(stack)} item(s).")
    return len(stack)


def display():
    """Print a visual representation of the stack."""
    if is_empty():
        print("  [ Stack is empty ]")
    else:
        print("  ┌─────────────┐")
        for item in reversed(stack):
            marker = " ← TOP" if item == stack[-1] else ""
            print(f"  │  {str(item):<10} │{marker}")
        print("  └─────────────┘")


# ─────────────────────────────────────────────
#  Menu
# ─────────────────────────────────────────────

DIVIDER = "─" * 40

def print_menu():
    print(f"\n{'═' * 40}")
    print("       STACK IMPLEMENTATION MENU")
    print(f"{'═' * 40}")
    print("  1. Push item")
    print("  2. Pop item")
    print("  3. Peek at top item")
    print("  4. Check if stack is empty")
    print("  5. Get stack size")
    print("  6. Display stack")
    print("  7. Exit")
    print(DIVIDER)


def main():
    print("\n  Welcome to the Stack Implementation!")

    while True:
        print_menu()
        choice = input("  Enter your choice (1–7): ").strip()
        print()

        if choice == "1":
            value = input("  Enter the item to push: ").strip()
            if value:
                push(value)
            else:
                print("  ✘ No input provided. Please enter a valid item.")

        elif choice == "2":
            pop()

        elif choice == "3":
            peek()

        elif choice == "4":
            if is_empty():
                print("  ✔ The stack is EMPTY.")
            else:
                print("  ✔ The stack is NOT empty.")

        elif choice == "5":
            size()

        elif choice == "6":
            print("  Current Stack:")
            display()

        elif choice == "7":
            print("  Goodbye! Thanks for using Stack Implementation.\n")
            break

        else:
            print("  ✘ Invalid choice. Please enter a number between 1 and 7.")


if __name__ == "__main__":
    main()