# =============================================================================
# Interactive Pattern Matching Tool
# Searches for a user-supplied pattern inside a text using the Naive Search
# algorithm — sliding the pattern one position at a time and comparing each
# character.  Reports every match position and the total number of comparisons.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================


# ── Core algorithm ────────────────────────────────────────────────────────────

def pattern_search(text, pattern):
    """
    Naive (Brute-Force) Pattern Matching.

    Algorithm:
      For every starting index i in the text (0 … len(text) - len(pattern)):
        Compare pattern[0] with text[i], pattern[1] with text[i+1], etc.
        If all m characters match → record position i as a match.
        On the first mismatch → stop the inner loop and slide one step right.

    Complexity:
      Best case  : O(n)    — mismatch on the first character every time
      Worst case : O(n*m)  — e.g. text="AAAAAAA", pattern="AAAB"
      Average    : O(n)    — typical text with diverse characters

    Arguments:
      text    – the string to search in
      pattern – the string to search for

    Returns a dict:
      positions   – list of 0-based start indices where pattern was found
      comparisons – total number of character-level comparisons made
      matches     – number of matches (len(positions))
      text        – the original text
      pattern     – the original pattern
    """
    n           = len(text)
    m           = len(pattern)
    positions   = []    # Collect every match start index
    comparisons = 0     # Count every single character comparison

    # Slide the pattern across every valid starting position
    for i in range(n - m + 1):          # i: 0  →  n-m  (inclusive)

        j = 0   # j tracks how far we've matched into the pattern

        # Inner loop: compare character by character
        while j < m:
            comparisons += 1            # One comparison per iteration

            if text[i + j] == pattern[j]:
                j += 1                  # Characters match — advance inside pattern
            else:
                break                   # Mismatch — stop, slide one step right

        # If j reached m, every character matched → full match found
        if j == m:
            positions.append(i)

    return {
        "positions"  : positions,
        "comparisons": comparisons,
        "matches"    : len(positions),
        "text"       : text,
        "pattern"    : pattern,
    }


# ── Visual helpers ────────────────────────────────────────────────────────────

def highlight_matches(text, positions, pattern_len, max_width=70):
    """
    Return two strings:
      line1 – the text (truncated if necessary)
      line2 – a caret line marking every match start with '^'

    Only the first max_width characters are shown to keep the display clean.
    """
    display_text = text[:max_width]
    markers      = [" "] * len(display_text)

    for pos in positions:
        if pos < len(display_text):
            # Mark the start of the match with '^' and the rest with '-'
            for k in range(pattern_len):
                if pos + k < len(display_text):
                    markers[pos + k] = "-" if k > 0 else "^"

    truncated = len(text) > max_width
    suffix    = f"  … (+{len(text) - max_width} more)" if truncated else ""

    return display_text + suffix, "".join(markers)


# ── Display helpers ───────────────────────────────────────────────────────────

def divider(char="─", width=58):
    print("  " + char * width)


def truncate(s, max_len=60):
    return s if len(s) <= max_len else s[:max_len] + f"… (+{len(s) - max_len} more)"


def print_search_result(result):
    """Pretty-print the full pattern search result."""
    divider("═")
    print(f"  Text    : {truncate(result['text'])}")
    print(f"  Pattern : {result['pattern']}")
    divider()

    if result["matches"] == 0:
        print("  No matches found.")
    else:
        positions_str = ", ".join(str(p) for p in result["positions"])
        print(f"  Pattern found at position(s) : {positions_str}")
        print(f"  Total matches                : {result['matches']}")

        # Visual alignment display
        print()
        line1, line2 = highlight_matches(result["text"], result["positions"], len(result["pattern"]))
        print(f"  Text    : {line1}")
        print(f"  Markers : {line2}")
        print(f"            (^ = match start,  - = rest of match)")

    divider()
    print(f"  Comparisons performed : {result['comparisons']}")
    print(f"  Text length (n)       : {len(result['text'])}")
    print(f"  Pattern length (m)    : {len(result['pattern'])}")
    print(f"  Positions checked     : {len(result['text']) - len(result['pattern']) + 1}")
    divider("═")
    print()


def print_positions_only(result):
    """Display just the match positions (used from the dedicated menu option)."""
    if not result:
        print("\n  [!] No search has been run yet. Use option 3 first.\n")
        return

    divider("═")
    print(f"  Text    : {truncate(result['text'])}")
    print(f"  Pattern : {result['pattern']}")
    divider()

    if result["matches"] == 0:
        print("  No matches found.")
    else:
        for i, pos in enumerate(result["positions"], start=1):
            # Show a small excerpt around each match
            start   = max(0, pos - 3)
            end     = min(len(result["text"]), pos + len(result["pattern"]) + 3)
            excerpt = result["text"][start:end]
            offset  = pos - start   # Caret offset within the excerpt
            caret   = " " * offset + "^"
            print(f"  Match {i:>3} at index {pos:>5}  →  ...{excerpt}...")
            print(f"  {'':>26}   ...{caret}...")

    divider()
    print(f"  Total : {result['matches']} match(es)  |  "
          f"{result['comparisons']} comparison(s)")
    divider("═")
    print()


# ── Input helpers ─────────────────────────────────────────────────────────────

def get_nonempty_input(prompt):
    """Keep prompting until the user types at least one character."""
    while True:
        value = input(prompt)
        if value:
            return value
        print("  [!] Input cannot be empty. Please try again.")


# ── Menu actions ──────────────────────────────────────────────────────────────

def action_enter_text(state):
    print("\n── Enter Text ──────────────────────────────────────────────")
    text = get_nonempty_input("  Type (or paste) your text: ")
    state["text"]        = text
    state["last_result"] = None   # Invalidate any previous search
    print(f"  Text stored ({len(text)} character(s)).\n")


def action_enter_pattern(state):
    print("\n── Enter Pattern ───────────────────────────────────────────")
    pattern = get_nonempty_input("  Type the pattern to search for: ")
    state["pattern"]     = pattern
    state["last_result"] = None   # Invalidate previous search
    print(f"  Pattern stored ({len(pattern)} character(s)).\n")


def action_search(state):
    print("\n── Perform Pattern Matching ────────────────────────────────")

    # Ensure both text and pattern are available
    if not state["text"]:
        print("  [!] No text entered yet. Please use option 1 first.\n")
        return
    if not state["pattern"]:
        print("  [!] No pattern entered yet. Please use option 2 first.\n")
        return

    text    = state["text"]
    pattern = state["pattern"]

    if len(pattern) > len(text):
        print(f"  [!] Pattern ({len(pattern)} chars) is longer than the text "
              f"({len(text)} chars) — no matches possible.\n")
        return

    result             = pattern_search(text, pattern)
    state["last_result"] = result

    print()
    print_search_result(result)


def action_show_positions(state):
    print("\n── Match Positions ─────────────────────────────────────────")
    print_positions_only(state["last_result"])


def action_show_comparisons(state):
    print("\n── Comparison Count ────────────────────────────────────────")
    result = state["last_result"]
    if not result:
        print("  [!] No search has been run yet. Use option 3 first.\n")
        return

    divider("═")
    print(f"  Text length (n)       : {len(result['text'])}")
    print(f"  Pattern length (m)    : {len(result['pattern'])}")
    print(f"  Windows checked       : {len(result['text']) - len(result['pattern']) + 1}")
    divider()
    print(f"  Comparisons performed : {result['comparisons']}")
    theoretical_best  = len(result["text"])
    theoretical_worst = (len(result["text"]) - len(result["pattern"]) + 1) * len(result["pattern"])
    print(f"  Theoretical best      : {theoretical_best}  (O(n), 1 mismatch per window)")
    print(f"  Theoretical worst     : {theoretical_worst}  (O(n*m), e.g. 'AAAA…' / 'AAB')")
    divider()
    print("  Naive search algorithm complexity:")
    print("    Best case  : O(n)   — first char mismatches every time")
    print("    Worst case : O(n*m) — near-match patterns on repetitive text")
    print("    Average    : O(n)   — typical natural-language text")
    divider("═")
    print()


# ── Main menu ─────────────────────────────────────────────────────────────────

def show_menu():
    print("╔════════════════════════════════════════════════════════╗")
    print("║           Interactive Pattern Matching Tool            ║")
    print("╠════════════════════════════════════════════════════════╣")
    print("║  1. Enter a text                                       ║")
    print("║  2. Enter a pattern to search                          ║")
    print("║  3. Perform pattern matching                           ║")
    print("║  4. Display all match positions                        ║")
    print("║  5. Show number of comparisons                         ║")
    print("║  6. Exit                                               ║")
    print("╚════════════════════════════════════════════════════════╝")

    while True:
        choice = input("  Choose an option [1-6]: ").strip()
        if choice in {"1", "2", "3", "4", "5", "6"}:
            return choice
        print("  [!] Invalid choice. Please enter a number from 1 to 6.")


def main():
    """
    Program entry point.
    All mutable state lives in one plain dictionary — no globals, no classes.
    """
    state = {
        "text"       : "",    # The text to search in
        "pattern"    : "",    # The pattern to search for
        "last_result": None,  # Dict returned by pattern_search()
    }

    print("\nWelcome to the Interactive Pattern Matching Tool!\n")

    while True:
        print()
        choice = show_menu()

        if choice == "1":
            action_enter_text(state)
        elif choice == "2":
            action_enter_pattern(state)
        elif choice == "3":
            action_search(state)
        elif choice == "4":
            action_show_positions(state)
        elif choice == "5":
            action_show_comparisons(state)
        elif choice == "6":
            print("\n  Goodbye!\n")
            break


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()