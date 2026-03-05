# =============================================================================
# Interactive String Comparison Tool
# Compares two strings character by character to find similarities and
# differences. Displays matching count, first differing index, and similarity%.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================


def get_string_input(prompt):
    """Prompt the user for a non-empty string and return it."""
    while True:
        value = input(prompt)
        if value:  # Ensure the input is not blank
            return value
        print("  [!] Input cannot be empty. Please try again.")


def compare_strings(str1, str2):
    """
    Compare two strings character by character.

    Converts both strings to lists of characters, then walks through
    each position to count matches and locate the first difference.

    Returns a dict with:
      - chars1       : list of characters from str1
      - chars2       : list of characters from str2
      - matching     : number of positions where characters are equal
      - first_diff   : index of first mismatch (-1 if strings are identical)
      - are_equal    : True only when both content AND length are identical
    """
    # Convert strings to character lists for explicit element-wise access
    chars1 = list(str1)
    chars2 = list(str2)

    matching    = 0
    first_diff  = -1                        # -1 means "no difference found yet"
    min_len     = min(len(chars1), len(chars2))

    # Walk through the overlapping portion of both lists
    for i in range(min_len):
        if chars1[i] == chars2[i]:
            matching += 1                   # Characters match at this position
        else:
            if first_diff == -1:            # Record only the first mismatch
                first_diff = i

    # If one string is longer, the extra characters count as a difference
    if first_diff == -1 and len(chars1) != len(chars2):
        first_diff = min_len                # Divergence starts right after overlap

    are_equal = (str1 == str2)             # True only if length AND content match

    return {
        "chars1"     : chars1,
        "chars2"     : chars2,
        "matching"   : matching,
        "first_diff" : first_diff,
        "are_equal"  : are_equal,
    }


def similarity_score(str1, str2):
    """
    Calculate how similar two strings are as a percentage.

    Uses the longer string's length as the denominator so that extra
    characters in one string always reduce the score.

    Returns a float between 0.0 and 100.0.
    """
    max_len = max(len(str1), len(str2))

    # Edge case: both strings are empty → treat as 100% similar
    if max_len == 0:
        return 100.0

    result   = compare_strings(str1, str2)
    matching = result["matching"]

    # Matching characters divided by the longest string length × 100
    return round((matching / max_len) * 100, 2)


def display_results(str1, str2):
    """Run the full comparison and print a formatted results block."""
    result  = compare_strings(str1, str2)
    score   = similarity_score(str1, str2)

    print("\n" + "─" * 45)
    print("  COMPARISON RESULTS")
    print("─" * 45)
    print(f"  String 1 : \"{str1}\"  (length: {len(str1)})")
    print(f"  String 2 : \"{str2}\"  (length: {len(str2)})")
    print("─" * 45)

    # Identical check
    if result["are_equal"]:
        print("  ✔  Strings are IDENTICAL")
    else:
        print("  ✘  Strings are NOT identical")

    # Matching character count
    print(f"  Matching characters : {result['matching']}")

    # First differing position
    if result["first_diff"] == -1:
        print("  First difference at : N/A  (no difference)")
    else:
        print(f"  First difference at : index {result['first_diff']}")

    # Similarity percentage
    print(f"  Similarity          : {score}%")
    print("─" * 45 + "\n")


def enter_strings(state):
    """Interactively collect two strings from the user and store them."""
    print("\n── Enter Strings ──────────────────────────")
    state["str1"] = get_string_input("  String 1 : ")
    state["str2"] = get_string_input("  String 2 : ")
    print("  [✔] Strings saved.")


def run_comparison(state):
    """Ensure strings exist, then display the full comparison."""
    if not state["str1"] or not state["str2"]:
        print("\n  [!] Please enter both strings first (Option 1).")
        return
    display_results(state["str1"], state["str2"])


def show_menu():
    """Print the main menu and return the user's validated choice."""
    print("╔══════════════════════════════════════════╗")
    print("║   Interactive String Comparison Tool     ║")
    print("╠══════════════════════════════════════════╣")
    print("║  1. Enter two strings                    ║")
    print("║  2. Compare strings (full report)        ║")
    print("║  3. Check if strings are equal           ║")
    print("║  4. Find first differing position        ║")
    print("║  5. Display similarity percentage        ║")
    print("║  6. Exit                                 ║")
    print("╚══════════════════════════════════════════╝")

    while True:
        choice = input("  Choose an option [1-6]: ").strip()
        if choice in {"1", "2", "3", "4", "5", "6"}:
            return choice
        print("  [!] Invalid choice. Please enter a number from 1 to 6.")


def main():
    """
    Main program loop.

    Uses a simple dictionary as shared state so no global variables
    or classes are needed.
    """
    # Shared state — holds the two strings across menu interactions
    state = {"str1": "", "str2": ""}

    print("\nWelcome to the Interactive String Comparison Tool!\n")

    while True:
        print()
        choice = show_menu()

        if choice == "1":
            # Collect both strings from the user
            enter_strings(state)

        elif choice == "2":
            # Full comparison report
            run_comparison(state)

        elif choice == "3":
            # Quick equality check
            if not state["str1"] or not state["str2"]:
                print("\n  [!] Please enter both strings first (Option 1).")
            else:
                result = compare_strings(state["str1"], state["str2"])
                print("\n── Equality Check ─────────────────────────")
                if result["are_equal"]:
                    print(f'  ✔  "{state["str1"]}" == "{state["str2"]}"  →  EQUAL')
                else:
                    print(f'  ✘  "{state["str1"]}" != "{state["str2"]}"  →  NOT EQUAL')
                print()

        elif choice == "4":
            # Show only the first differing index
            if not state["str1"] or not state["str2"]:
                print("\n  [!] Please enter both strings first (Option 1).")
            else:
                result = compare_strings(state["str1"], state["str2"])
                print("\n── First Difference ───────────────────────")
                if result["first_diff"] == -1:
                    print("  ✔  No difference found — strings are identical.")
                else:
                    idx  = result["first_diff"]
                    c1   = state["str1"][idx] if idx < len(state["str1"]) else "<end>"
                    c2   = state["str2"][idx] if idx < len(state["str2"]) else "<end>"
                    print(f"  First difference at index : {idx}")
                    print(f"  String 1 has : '{c1}'")
                    print(f"  String 2 has : '{c2}'")
                print()

        elif choice == "5":
            # Show only the similarity percentage
            if not state["str1"] or not state["str2"]:
                print("\n  [!] Please enter both strings first (Option 1).")
            else:
                score = similarity_score(state["str1"], state["str2"])
                print("\n── Similarity Score ───────────────────────")
                print(f"  Similarity : {score}%")
                print()

        elif choice == "6":
            # Exit gracefully
            print("\n  Goodbye! Thanks for using the String Comparison Tool.\n")
            break


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()