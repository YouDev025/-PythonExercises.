"""
Interactive Substring Search
----------------------------
This program allows users to search for a substring (pattern) inside a given text.
It supports both a naive O(n*m) approach and the efficient Knuth-Morris-Pratt (KMP) algorithm.

Author: Youssef Adardour
Date: March 2026
"""

# -----------------------------
# Utility Functions
# -----------------------------

def naive_search(text, pattern):
    """Naive substring search: check all possible positions."""
    positions = []
    n, m = len(text), len(pattern)
    for i in range(n - m + 1):
        if text[i:i+m] == pattern:
            positions.append(i)
    return positions

def kmp_prefix_function(pattern):
    """Compute longest prefix-suffix (LPS) array for KMP."""
    lps = [0] * len(pattern)
    length = 0
    i = 1
    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length-1]
            else:
                lps[i] = 0
                i += 1
    return lps

def kmp_search(text, pattern):
    """KMP substring search algorithm."""
    positions = []
    lps = kmp_prefix_function(pattern)
    i = j = 0
    while i < len(text):
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == len(pattern):
                positions.append(i - j)
                j = lps[j-1]
        else:
            if j != 0:
                j = lps[j-1]
            else:
                i += 1
    return positions

# -----------------------------
# Menu System
# -----------------------------

def menu():
    """Interactive menu system."""
    text, pattern = "", ""

    while True:
        print("\n=== Interactive Substring Search ===")
        print("1. Enter text and pattern")
        print("2. Search using naive method")
        print("3. Search using KMP algorithm")
        print("4. Exit")

        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            text = input("Enter the text: ")
            pattern = input("Enter the pattern (substring): ")
            print("Inputs stored successfully.")

        elif choice == "2":
            if text and pattern:
                positions = naive_search(text, pattern)
                if positions:
                    print(f"\nPattern found at positions: {positions}")
                else:
                    print("\nPattern not found.")
            else:
                print("Please enter text and pattern first (Option 1).")

        elif choice == "3":
            if text and pattern:
                positions = kmp_search(text, pattern)
                if positions:
                    print(f"\nPattern found at positions: {positions}")
                else:
                    print("\nPattern not found.")
            else:
                print("Please enter text and pattern first (Option 1).")

        elif choice == "4":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option.")

# -----------------------------
# Main Execution
# -----------------------------

if __name__ == "__main__":
    menu()
