# =============================================================================
# Interactive Run-Length Encoding Tool
# Encodes strings by collapsing consecutive repeated characters into
# character+count pairs (e.g. AAABBC → A3B2C1), and decodes them back.
# Displays compression statistics so users can see when RLE helps or hurts.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================


# ── Core algorithm functions ──────────────────────────────────────────────────

def encode_rle(text):
    """
    Encode *text* using Run-Length Encoding.

    Algorithm:
      Walk through the string character by character.
      Keep a running count of the current character.
      When the character changes (or we reach the end), append
      'char + count' to the output list, then reset the counter.

    Example:
      AAAABBBCCDAA  →  A4B3C2D1A2

    Returns a dict with:
      encoded   – the RLE string
      pairs     – list of (char, count) tuples for inspection
      original  – the input text (unchanged)
    """
    if not text:
        return {"encoded": "", "pairs": [], "original": text}

    pairs   = []   # Accumulate (char, count) tuples
    current = text[0]
    count   = 1

    # Start from index 1; compare each char to the one before it
    for i in range(1, len(text)):
        if text[i] == current:
            count += 1          # Same character — extend the run
        else:
            pairs.append((current, count))   # Run ended — save it
            current = text[i]                # Start a new run
            count   = 1

    pairs.append((current, count))           # Don't forget the last run

    # Build the encoded string from the pairs list
    encoded = "".join(f"{ch}{n}" for ch, n in pairs)

    return {"encoded": encoded, "pairs": pairs, "original": text}


def decode_rle(encoded_text):
    """
    Decode an RLE string back to the original text.

    Algorithm:
      Scan left-to-right.
      When we hit a letter (or any non-digit), it starts a new token.
      Accumulate following digit characters to form the count.
      When the next non-digit arrives (or end of string), repeat the
      saved character 'count' times and append to the output list.

    Example:
      A4B3C2D1A2  →  AAAABBBCCDAA

    Returns a dict with:
      decoded  – the reconstructed string
      pairs    – list of (char, count) tuples parsed from input
      valid    – True if the input was well-formed
      error    – description of any problem found (empty string if none)
    """
    if not encoded_text:
        return {"decoded": "", "pairs": [], "valid": True, "error": ""}

    output      = []   # Build decoded characters here
    pairs       = []   # Track (char, count) for display
    current_ch  = ""   # The character we're currently expanding
    count_str   = ""   # Digit(s) that follow the character

    for ch in encoded_text:
        if ch.isdigit():
            if not current_ch:
                return {
                    "decoded" : "",
                    "pairs"   : [],
                    "valid"   : False,
                    "error"   : f"Unexpected digit '{ch}' with no preceding character.",
                }
            count_str += ch          # Could be multi-digit count (e.g. A12)
        else:
            # Non-digit: flush the previous token (if any), start a new one
            if current_ch:
                if not count_str:
                    return {
                        "decoded" : "",
                        "pairs"   : [],
                        "valid"   : False,
                        "error"   : f"Character '{current_ch}' has no count.",
                    }
                n = int(count_str)
                pairs.append((current_ch, n))
                output.append(current_ch * n)

            current_ch = ch
            count_str  = ""

    # Flush the final token
    if current_ch:
        if not count_str:
            return {
                "decoded" : "",
                "pairs"   : [],
                "valid"   : False,
                "error"   : f"Character '{current_ch}' at end of string has no count.",
            }
        n = int(count_str)
        pairs.append((current_ch, n))
        output.append(current_ch * n)

    return {"decoded": "".join(output), "pairs": pairs, "valid": True, "error": ""}


# ── Statistics helper ─────────────────────────────────────────────────────────

def compression_stats(original, encoded):
    """
    Build a statistics dictionary comparing original and encoded lengths.

    Keys:
      original_len   – character count of the original string
      encoded_len    – character count of the encoded string
      saved          – characters saved (negative means expansion)
      ratio          – encoded_len / original_len  (lower = better compression)
      percent_change – how much smaller (negative) or larger (positive) in %
      verdict        – human-readable summary
    """
    orig_len = len(original)
    enc_len  = len(encoded)

    if orig_len == 0:
        return {
            "original_len"  : 0,
            "encoded_len"   : 0,
            "saved"         : 0,
            "ratio"         : 1.0,
            "percent_change": 0.0,
            "verdict"       : "Empty string — nothing to compress.",
        }

    saved          = orig_len - enc_len
    ratio          = enc_len / orig_len
    percent_change = (1 - ratio) * 100   # Positive = compression, negative = expansion

    if saved > 0:
        verdict = f"RLE compressed the string by {saved} character(s)."
    elif saved < 0:
        verdict = f"RLE expanded the string by {abs(saved)} character(s) (few repetitions)."
    else:
        verdict = "RLE produced no change in length."

    return {
        "original_len"  : orig_len,
        "encoded_len"   : enc_len,
        "saved"         : saved,
        "ratio"         : ratio,
        "percent_change": percent_change,
        "verdict"       : verdict,
    }


# ── Display helpers ───────────────────────────────────────────────────────────

def divider(char="─", width=56):
    print("  " + char * width)


def truncate(s, max_len=60):
    """Shorten a long string for display with an ellipsis."""
    return s if len(s) <= max_len else s[:max_len] + f"… (+{len(s)-max_len} more)"


def print_encode_result(result, stats):
    divider("═")
    print(f"  Original  : {truncate(result['original'])}")
    print(f"  Encoded   : {truncate(result['encoded'])}")
    divider()
    pairs_preview = result['pairs'][:10]
    print(f"  Pairs     : {pairs_preview}", end="")
    print("  …" if len(result['pairs']) > 10 else "")
    divider()
    print(f"  Original length  : {stats['original_len']} characters")
    print(f"  Encoded length   : {stats['encoded_len']} characters")
    print(f"  Characters saved : {stats['saved']}")
    print(f"  Compression ratio: {stats['ratio']:.4f}  ({stats['percent_change']:+.1f}%)")
    print(f"  Verdict          : {stats['verdict']}")
    divider("═")
    print()


def print_decode_result(encoded, result):
    divider("═")
    print(f"  Encoded   : {truncate(encoded)}")
    print(f"  Decoded   : {truncate(result['decoded'])}")
    divider()
    pairs_preview = result['pairs'][:10]
    print(f"  Pairs     : {pairs_preview}", end="")
    print("  …" if len(result['pairs']) > 10 else "")
    divider("═")
    print()


def print_stats_only(state):
    """Print statistics for the last encoded string stored in state."""
    if not state["last_original"]:
        print("\n  [!] No string encoded yet. Use option 2 first.\n")
        return

    original = state["last_original"]
    encoded  = state["last_encoded"]
    stats    = compression_stats(original, encoded)

    divider("═")
    print("  Compression Statistics")
    divider()
    print(f"  Original string  : {truncate(original)}")
    print(f"  Encoded string   : {truncate(encoded)}")
    divider()
    print(f"  Original length  : {stats['original_len']} characters")
    print(f"  Encoded length   : {stats['encoded_len']} characters")
    print(f"  Characters saved : {stats['saved']}")
    print(f"  Compression ratio: {stats['ratio']:.4f}")
    print(f"  Space saved      : {stats['percent_change']:+.1f}%")
    divider()
    print(f"  {stats['verdict']}")
    print()
    print("  RLE works best on strings with long repeated runs.")
    print("    e.g.  AAAAAAAAAA  ->  A10  (10 chars -> 3 chars)")
    print("    RLE is inefficient on alternating characters.")
    print("    e.g.  ABCDEF      ->  A1B1C1D1E1F1  (6 -> 12 chars)")
    divider("═")
    print()


# ── Input helpers ─────────────────────────────────────────────────────────────

def get_nonempty_string(prompt):
    """Prompt until the user enters at least one character."""
    while True:
        value = input(prompt)
        if value:
            return value
        print("  [!] Input cannot be empty. Please try again.")


# ── Menu actions ──────────────────────────────────────────────────────────────

def action_enter_string(state):
    """Store a new string in state for use by other options."""
    print("\n── Enter a String ──────────────────────────────────────────")
    text = get_nonempty_string("  Type your string: ")
    state["current_string"] = text
    print(f"  String stored ({len(text)} character(s)).\n")


def action_encode(state):
    """Encode the current string (or ask for one) and show results."""
    print("\n── Encode String (RLE) ─────────────────────────────────────")

    if state["current_string"]:
        preview = truncate(state["current_string"], 30)
        use_stored = input(f"  Use stored string '{preview}'? [Y/n]: ").strip().lower()
        if use_stored in ("", "y", "yes"):
            text = state["current_string"]
        else:
            text = get_nonempty_string("  Type a string to encode: ")
    else:
        print("  No string stored yet — please enter one now.")
        text = get_nonempty_string("  Type a string to encode: ")

    result = encode_rle(text)
    stats  = compression_stats(text, result["encoded"])

    # Cache for the statistics view
    state["last_original"] = text
    state["last_encoded"]  = result["encoded"]

    print()
    print_encode_result(result, stats)


def action_decode(state):
    """Decode an RLE-encoded string entered by the user."""
    print("\n── Decode String (RLE) ─────────────────────────────────────")
    encoded = get_nonempty_string("  Enter an RLE-encoded string (e.g. A4B3C2D1): ")

    result = decode_rle(encoded)

    if not result["valid"]:
        print(f"\n  [!] Decoding failed: {result['error']}\n")
        return

    print()
    print_decode_result(encoded, result)


def action_stats(state):
    """Show compression statistics for the most recently encoded string."""
    print("\n── Compression Statistics ──────────────────────────────────")
    print_stats_only(state)


# ── Main menu ─────────────────────────────────────────────────────────────────

def show_menu():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          Interactive Run-Length Encoding Tool            ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  1. Enter a string                                       ║")
    print("║  2. Encode string (RLE)                                  ║")
    print("║  3. Decode an encoded string                             ║")
    print("║  4. Display compression statistics                       ║")
    print("║  5. Exit                                                 ║")
    print("╚══════════════════════════════════════════════════════════╝")

    while True:
        choice = input("  Choose an option [1-5]: ").strip()
        if choice in {"1", "2", "3", "4", "5"}:
            return choice
        print("  [!] Invalid choice. Please enter a number from 1 to 5.")


def main():
    """
    Entry point — no globals, no classes.
    All mutable program state lives in this dictionary.
    """
    state = {
        "current_string": "",   # Last string entered by the user
        "last_original" : "",   # Last string that was encoded
        "last_encoded"  : "",   # Its RLE-encoded counterpart
    }

    print("\nWelcome to the Interactive Run-Length Encoding Tool!\n")

    while True:
        print()
        choice = show_menu()

        if choice == "1":
            action_enter_string(state)
        elif choice == "2":
            action_encode(state)
        elif choice == "3":
            action_decode(state)
        elif choice == "4":
            action_stats(state)
        elif choice == "5":
            print("\n  Goodbye!\n")
            break


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()