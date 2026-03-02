"""
Interactive Greedy Algorithm
----------------------------
This program allows users to experiment with greedy algorithms.
It includes examples like coin change (minimum coins) and activity selection.
Users can choose which problem to solve interactively.

Author: Youssef Adardour
Date: March 2026
"""

# -----------------------------
# Utility Functions
# -----------------------------

def coin_change_greedy(coins, amount):
    """Greedy coin change: pick largest coin first.

    Example:
        coins = [1, 2, 5]
        amount = 11
        -> Result = [5, 5, 1]
    """
    coins.sort(reverse=True)  # sort coins descending
    result = []
    for coin in coins:
        while amount >= coin:
            amount -= coin
            result.append(coin)
    return result

def activity_selection(activities):
    """Greedy activity selection: choose earliest finishing activities.

    Example:
        activities = [(1, 3), (2, 5), (4, 6), (6, 7)]
        -> Result = [(1, 3), (4, 6), (6, 7)]
    """
    activities.sort(key=lambda x: x[1])  # sort by finish time
    selected = []
    last_finish = 0
    for start, finish in activities:
        if start >= last_finish:
            selected.append((start, finish))
            last_finish = finish
    return selected

# -----------------------------
# Menu System
# -----------------------------

def menu():
    """Interactive menu system for greedy algorithms."""
    while True:
        print("\n=== Interactive Greedy Algorithm ===")
        print("1. Coin Change Problem")
        print("2. Activity Selection Problem")
        print("3. Exit")

        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            # Example: coins = [1, 2, 5], amount = 11
            coins = list(map(int, input("Enter coin denominations (space-separated): ").split()))
            amount = int(input("Enter amount to make change for: "))
            result = coin_change_greedy(coins, amount)
            print(f"Greedy coin change result: {result}")

        elif choice == "2":
            # Example: activities = [(1, 3), (2, 5), (4, 6), (6, 7)]
            n = int(input("Enter number of activities: "))
            activities = []
            for i in range(n):
                while True:
                    parts = input(f"Enter start and finish time for activity {i+1} (e.g., '1 3'): ").split()
                    if len(parts) == 2:
                        try:
                            start, finish = map(int, parts)
                            activities.append((start, finish))
                            break
                        except ValueError:
                            print("Error: Please enter two integers.")
                    else:
                        print("Error: Please enter exactly two numbers separated by a space.")
            selected = activity_selection(activities)
            print(f"Selected activities: {selected}")

        elif choice == "3":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option.")

# -----------------------------
# Main Execution
# -----------------------------

if __name__ == "__main__":
    menu()
