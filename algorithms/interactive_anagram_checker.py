"""
Interactive Anagram Checker
---------------------------
This program allows users to check if two words or sentences are anagrams,
compare their character frequencies, and group lists of words into anagram sets.

Author: Youssef Adardour
Date: March 2026
"""

# -----------------------------
# Utility Functions
# -----------------------------

def clean_string(s):
    """Remove spaces and convert to lowercase for uniform comparison."""
    return ''.join(ch.lower() for ch in s if ch.isalpha())  # keep only letters


def char_frequency(s):
    """Return a dictionary of character frequencies for a given string."""
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1  # count occurrences
    return freq


def is_anagram(str1, str2):
    """Check if two strings are anagrams using frequency comparison."""
    s1, s2 = clean_string(str1), clean_string(str2)  # clean inputs
    return char_frequency(s1) == char_frequency(s2)  # compare dictionaries


def display_frequency_table(str1, str2):
    """Display frequency tables for both strings side by side."""
    s1, s2 = clean_string(str1), clean_string(str2)
    freq1, freq2 = char_frequency(s1), char_frequency(s2)

    print("\nCharacter Frequency Comparison:")
    print(f"{'Char':<6}{'Word1':<8}{'Word2':<8}")
    print("-" * 24)
    # union of all characters from both words
    all_chars = sorted(set(freq1.keys()) | set(freq2.keys()))
    for ch in all_chars:
        print(f"{ch:<6}{freq1.get(ch, 0):<8}{freq2.get(ch, 0):<8}")


def group_anagrams(words):
    """Group words into anagram sets using sorted characters as keys."""
    groups = {}       # dictionary to group words
    comparisons = 0   # count comparisons (rough estimate)
    for word in words:
        cleaned = clean_string(word)
        sorted_key = ''.join(sorted(cleaned))  # sorted letters as key
        comparisons += len(cleaned) * (len(cleaned) - 1) // 2
        groups.setdefault(sorted_key, []).append(word)  # group words
    return list(groups.values()), comparisons


# -----------------------------
# Menu System
# -----------------------------

def menu():
    """Interactive menu system."""
    while True:
        print("\n=== Interactive Anagram Checker ===")
        print("1. Enter two words/sentences")
        print("2. Check if they are anagrams")
        print("3. Display character frequency comparison")
        print("4. Group a list of words into anagram sets")
        print("5. Exit")

        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            # Store user inputs
            global word1, word2
            word1 = input("Enter first word/sentence: ").strip()
            word2 = input("Enter second word/sentence: ").strip()
            print("Inputs stored successfully.")

        elif choice == "2":
            # Check if stored words are anagrams
            if word1 and word2:
                result = is_anagram(word1, word2)
                print("\nResult:")
                if result:
                    print(f"'{word1}' and '{word2}' ARE anagrams.")
                else:
                    print(f"'{word1}' and '{word2}' are NOT anagrams.")
            else:
                print("Please enter words first (Option 1).")

        elif choice == "3":
            # Show frequency comparison
            if word1 and word2:
                display_frequency_table(word1, word2)
            else:
                print("Please enter words first (Option 1).")

        elif choice == "4":
            # Group words into anagram sets
            words = input("Enter words separated by spaces: ").split()
            groups, comparisons = group_anagrams(words)
            print("\nAnagram Groups:")
            for group in groups:
                print(group)
            print(f"\nNumber of character comparisons (approx): {comparisons}")

        elif choice == "5":
            # Exit program
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please select a valid option.")


# -----------------------------
# Main Execution
# -----------------------------

if __name__ == "__main__":
    word1, word2 = "", ""  # Initialize global variables
    menu()
