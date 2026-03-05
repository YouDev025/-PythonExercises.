# =============================================================================
# Interactive Simple Data Compression Tool
# Compresses text by stripping redundant spaces then applying Run-Length
# Encoding (RLE) — replacing consecutive repeated characters with char+count.
# Decompresses back to the original trimmed text and reports full statistics.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================


# ── Encoding format note ──────────────────────────────────────────────────────
#
# Each RLE token is written as:  char + ":" + count + ","
# Example:  "A5B4C2"  is stored as  "A:5,B:4,C:2,"
#
# The colon separator is necessary when the compressed text itself contains
# digit characters (e.g. "1111" → "1:4,").  Without it, "14" would be
# ambiguous: does it mean character '1' repeated 4 times, or 14 of something?
#
# The format is still human-readable and the display layer strips the
# punctuation for cleaner output summaries.
#
# ─────────────────────────────────────────────────────────────────────────────


# ── Core compression functions ────────────────────────────────────────────────

def compress_text(text):
    """
    Compress *text* using a two-step pipeline:

      Step 1 – Space normalisation
        Collapse every run of whitespace into a single space and strip
        leading/trailing whitespace.  Removes the most common source of
        unnecessary bloat in plain text.

      Step 2 – Run-Length Encoding (RLE)
        Scan the normalised string character by character.
        Track the current character and how many times it repeats.
        When the character changes (or the string ends), emit a token
        in the format  char:count,  into the output list.

    Example:
        'AAAAABBBBCC'   ->  'A:5,B:4,C:2,'
        'hello  world'  ->  'h:1,e:1,l:2,o:1, :1,w:1,o:1,r:1,l:1,d:1,'

    Returns a dict:
        compressed   – the full RLE string (with ':' and ',' delimiters)
        display      – compact display form  (e.g. 'A5 B4 C2')
        normalised   – text after space-normalisation
        pairs        – list of (char, count) tuples
        original     – the raw input text (unchanged)
    """
    if not text:
        return {
            "compressed" : "",
            "display"    : "",
            "normalised" : "",
            "pairs"      : [],
            "original"   : text,
        }

    # ── Step 1: normalise spaces ──────────────────────────────────────────────
    normalised = " ".join(text.split())

    # If the entire input was whitespace, nothing remains after normalisation
    if not normalised:
        return {
            "compressed" : "",
            "display"    : "",
            "normalised" : "",
            "pairs"      : [],
            "original"   : text,
        }

    # ── Step 2: RLE encoding ──────────────────────────────────────────────────
    tokens  = []          # Collect "char:count," strings
    pairs   = []          # Collect (char, count) tuples for display
    current = normalised[0]
    count   = 1

    for i in range(1, len(normalised)):
        if normalised[i] == current:
            count += 1          # Extend the current run
        else:
            tokens.append(f"{current}:{count},")
            pairs.append((current, count))
            current = normalised[i]
            count   = 1

    # Flush the last run
    tokens.append(f"{current}:{count},")
    pairs.append((current, count))

    compressed = "".join(tokens)

    # Friendly display form: "A5 B4 C2" (no punctuation, space-separated)
    display = " ".join(f"{ch}{n}" for ch, n in pairs)

    return {
        "compressed" : compressed,
        "display"    : display,
        "normalised" : normalised,
        "pairs"      : pairs,
        "original"   : text,
    }


def decompress_text(compressed_text):
    """
    Decompress a string produced by compress_text().

    Expected format:  char:count,  tokens (e.g. 'A:5,B:4,C:2,').

    Validation:
        Returns valid=False with a human-readable error for:
          • a token that is missing a colon separator
          • a count field that is not a positive integer
          • an empty character field

    Example:
        'A:5,B:4,C:2,'  ->  'AAAAABBBBCC'

    Returns a dict:
        decoded  – the reconstructed string
        pairs    – list of (char, count) tuples
        valid    – True if input was well-formed
        error    – problem description (empty when valid)
    """
    if not compressed_text:
        return {"decoded": "", "pairs": [], "valid": True, "error": ""}

    output = []
    pairs  = []

    # Split on commas; the trailing comma produces one empty string at the end
    tokens = compressed_text.split(",")

    for token in tokens:
        if not token:
            continue    # Skip the empty string after the final comma

        # Each valid token must contain exactly one colon
        if ":" not in token:
            return {
                "decoded" : "",
                "pairs"   : [],
                "valid"   : False,
                "error"   : (
                    f"Token '{token}' is missing a ':' separator. "
                    "Make sure you paste text that was compressed by this tool."
                ),
            }

        # Split on the FIRST colon only (the character itself could theoretically
        # be a colon if someone types one — unlikely but safe to handle)
        colon_pos = token.index(":")
        ch        = token[:colon_pos]
        count_str = token[colon_pos + 1:]

        if not ch:
            return {
                "decoded" : "",
                "pairs"   : [],
                "valid"   : False,
                "error"   : f"Empty character field in token '{token}'.",
            }

        if not count_str.isdigit() or int(count_str) < 1:
            return {
                "decoded" : "",
                "pairs"   : [],
                "valid"   : False,
                "error"   : f"Invalid count '{count_str}' in token '{token}'. Must be a positive integer.",
            }

        n = int(count_str)
        pairs.append((ch, n))
        output.append(ch * n)

    return {"decoded": "".join(output), "pairs": pairs, "valid": True, "error": ""}


# ── Statistics helper ─────────────────────────────────────────────────────────

def compression_stats(original, compressed, normalised=""):
    """
    Return a statistics dictionary comparing original and compressed lengths.

    Keys:
        original_len    – raw character count
        normalised_len  – length after space-normalisation
        compressed_len  – length of the compressed string
        space_saved     – characters removed by space-normalisation
        rle_delta       – characters removed (positive) or added (negative) by RLE vs normalised
        total_saved     – characters saved vs original (may be negative)
        ratio           – compressed_len / original_len
        percent_saved   – percentage saved vs original
        verdict         – one-line summary
    """
    orig_len = len(original)
    comp_len = len(compressed)

    if orig_len == 0:
        return {
            "original_len"  : 0,
            "normalised_len": 0,
            "compressed_len": 0,
            "space_saved"   : 0,
            "rle_delta"     : 0,
            "total_saved"   : 0,
            "ratio"         : 1.0,
            "percent_saved" : 0.0,
            "verdict"       : "Empty string — nothing to compress.",
        }

    norm_len     = len(normalised) if normalised else len(" ".join(original.split()))
    space_saved  = orig_len - norm_len
    rle_delta    = norm_len - comp_len
    total_saved  = orig_len - comp_len
    ratio        = comp_len / orig_len
    percent_saved = (1 - ratio) * 100

    if total_saved > 0:
        verdict = f"Compression reduced size by {total_saved} character(s) ({percent_saved:.1f}% smaller)."
    elif total_saved < 0:
        verdict = (
            f"Compression expanded size by {abs(total_saved)} character(s) "
            f"— text has too few repetitions for RLE to help."
        )
    else:
        verdict = "Compression produced no change in size."

    return {
        "original_len"  : orig_len,
        "normalised_len": norm_len,
        "compressed_len": comp_len,
        "space_saved"   : space_saved,
        "rle_delta"     : rle_delta,
        "total_saved"   : total_saved,
        "ratio"         : ratio,
        "percent_saved" : percent_saved,
        "verdict"       : verdict,
    }


# ── Display helpers ───────────────────────────────────────────────────────────

def divider(char="─", width=56):
    print("  " + char * width)


def truncate(s, max_len=58):
    """Shorten long strings for display."""
    return s if len(s) <= max_len else s[:max_len] + f"… (+{len(s) - max_len} more)"


def print_compress_result(result, stats):
    divider("═")
    print(f"  Original text    : {truncate(result['original'])}")
    if result["normalised"] != result["original"].strip():
        print(f"  Normalised text  : {truncate(result['normalised'])}")
    print(f"  Compressed text  : {truncate(result['display'])}")
    divider()
    pairs_preview = result["pairs"][:10]
    suffix = "  …" if len(result["pairs"]) > 10 else ""
    print(f"  RLE pairs        : {pairs_preview}{suffix}")
    divider()
    print(f"  Original size    : {stats['original_len']} characters")
    if stats["space_saved"] > 0:
        print(f"  After spaces     : {stats['normalised_len']} characters  (-{stats['space_saved']} spaces removed)")
    print(f"  Compressed size  : {stats['compressed_len']} characters")
    print(f"  Total saved      : {stats['total_saved']} characters")
    print(f"  Compression ratio: {stats['ratio']:.4f}  ({stats['percent_saved']:+.1f}%)")
    divider()
    print(f"  {stats['verdict']}")
    divider("═")
    print()


def print_decompress_result(compressed, result):
    divider("═")
    print(f"  Compressed text  : {truncate(compressed)}")
    print(f"  Decompressed text: {truncate(result['decoded'])}")
    divider()
    pairs_preview = result["pairs"][:10]
    suffix = "  …" if len(result["pairs"]) > 10 else ""
    print(f"  RLE pairs        : {pairs_preview}{suffix}")
    divider("═")
    print()


def print_stats_detail(state):
    if not state["last_original"]:
        print("\n  [!] No text compressed yet. Use option 2 first.\n")
        return

    original   = state["last_original"]
    compressed = state["last_compressed"]
    normalised = state["last_normalised"]
    stats      = compression_stats(original, compressed, normalised)

    divider("═")
    print("  Compression Statistics")
    divider()
    print(f"  Original text    : {truncate(original)}")
    print(f"  Compressed text  : {truncate(state['last_display'])}")
    divider()
    print(f"  Original size    : {stats['original_len']} characters")
    print(f"  After spaces     : {stats['normalised_len']} characters  (spaces removed: {stats['space_saved']})")
    print(f"  Compressed size  : {stats['compressed_len']} characters  (RLE delta: {stats['rle_delta']:+d})")
    print(f"  Total saved      : {stats['total_saved']} characters")
    print(f"  Compression ratio: {stats['ratio']:.4f}")
    print(f"  Space saved      : {stats['percent_saved']:.1f}%")
    divider()
    print(f"  {stats['verdict']}")
    print()
    print("  Technique notes:")
    print("    Step 1 — Space normalisation: collapses repeated whitespace")
    print("    Step 2 — RLE: replaces repeated chars with char+count")
    print("    Best for: text with long repeated character runs")
    print("    e.g.  'AAAAAABBBB'  ->  'A6B4'  (10 -> 4 tokens, 60% smaller)")
    print("    Worst for: alternating characters with no repetition")
    print("    e.g.  'ABCDE'  ->  'A1B1C1D1E1'  (5 -> 15 chars, larger)")
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
    text = get_nonempty_input("  Type your text: ")
    state["current_text"] = text
    print(f"  Text stored ({len(text)} character(s)).\n")


def action_compress(state):
    print("\n── Compress Text ───────────────────────────────────────────")

    if state["current_text"]:
        preview    = truncate(state["current_text"], 30)
        use_stored = input(f"  Use stored text '{preview}'? [Y/n]: ").strip().lower()
        text       = state["current_text"] if use_stored in ("", "y", "yes") else get_nonempty_input("  Type text to compress: ")
    else:
        print("  No text stored yet — please enter some now.")
        text = get_nonempty_input("  Type text to compress: ")

    result = compress_text(text)
    stats  = compression_stats(text, result["compressed"], result["normalised"])

    # Cache results for statistics view and decompression convenience
    state["last_original"]   = text
    state["last_compressed"] = result["compressed"]
    state["last_normalised"] = result["normalised"]
    state["last_display"]    = result["display"]

    print()
    print_compress_result(result, stats)


def action_decompress(state):
    print("\n── Decompress Text ─────────────────────────────────────────")

    if state["last_compressed"]:
        preview    = truncate(state["last_display"], 30)
        use_cached = input(f"  Decompress last result '{preview}'? [Y/n]: ").strip().lower()
        compressed = state["last_compressed"] if use_cached in ("", "y", "yes") else get_nonempty_input("  Paste compressed text: ")
    else:
        compressed = get_nonempty_input("  Paste compressed text: ")

    result = decompress_text(compressed)

    if not result["valid"]:
        print(f"\n  [!] Decompression failed: {result['error']}\n")
        return

    print()
    print_decompress_result(compressed, result)


def action_stats(state):
    print("\n── Compression Statistics ──────────────────────────────────")
    print_stats_detail(state)


# ── Main menu ─────────────────────────────────────────────────────────────────

def show_menu():
    print("╔════════════════════════════════════════════════════════╗")
    print("║       Interactive Simple Data Compression Tool         ║")
    print("╠════════════════════════════════════════════════════════╣")
    print("║  1. Enter a text string                                ║")
    print("║  2. Compress the text                                  ║")
    print("║  3. Decompress the compressed text                     ║")
    print("║  4. Display compression statistics                     ║")
    print("║  5. Exit                                               ║")
    print("╚════════════════════════════════════════════════════════╝")

    while True:
        choice = input("  Choose an option [1-5]: ").strip()
        if choice in {"1", "2", "3", "4", "5"}:
            return choice
        print("  [!] Invalid choice. Please enter a number from 1 to 5.")


def main():
    """
    Program entry point.
    All mutable state lives in one plain dictionary — no globals, no classes.
    """
    state = {
        "current_text"   : "",
        "last_original"  : "",
        "last_compressed": "",
        "last_normalised": "",
        "last_display"   : "",
    }

    print("\nWelcome to the Interactive Simple Data Compression Tool!\n")

    while True:
        print()
        choice = show_menu()

        if choice == "1":
            action_enter_text(state)
        elif choice == "2":
            action_compress(state)
        elif choice == "3":
            action_decompress(state)
        elif choice == "4":
            action_stats(state)
        elif choice == "5":
            print("\n  Goodbye!\n")
            break


if __name__ == "__main__":
    main()