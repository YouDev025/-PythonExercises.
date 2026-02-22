# ============================================================
# Mini Search Engine: Allows the user to search for a keyword
# across multiple text documents or a loaded text file.
# Displays all matching lines and a total match count.
# ============================================================
# Author: Youssef Adardour
# Date: February 2026
# ============================================================

import os


# A small built-in document collection used when no file is loaded
SAMPLE_DOCUMENTS = {
    "doc1.txt": [
        "Python is a popular programming language.",
        "It is widely used in data science and web development.",
        "Python supports object-oriented and functional programming.",
    ],
    "doc2.txt": [
        "Search engines index documents to allow fast retrieval.",
        "A keyword search scans documents for matching terms.",
        "Case-insensitive search improves usability.",
    ],
    "doc3.txt": [
        "Machine learning is a subset of artificial intelligence.",
        "Python libraries like scikit-learn make machine learning accessible.",
        "Data preprocessing is a key step in any machine learning pipeline.",
    ],
}


# ── File loading ──────────────────────────────────────────────

def load_file(filepath):
    """
    Load a text file and return its lines as a list.
    Returns None if the file cannot be opened.
    """
    if not os.path.isfile(filepath):
        print(f"  Error: '{filepath}' does not exist.")
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f.readlines()]
        if not lines:
            print("  Warning: The file is empty.")
            return None
        print(f"  Loaded '{filepath}' successfully ({len(lines)} lines).")
        return lines
    except PermissionError:
        print(f"  Error: Permission denied when reading '{filepath}'.")
        return None
    except UnicodeDecodeError:
        print(f"  Error: Could not decode '{filepath}'. Make sure it is a UTF-8 text file.")
        return None


# ── Search logic ──────────────────────────────────────────────

def search_in_lines(lines, keyword, source_name):
    """
    Search for a keyword (case-insensitive) in a list of lines.
    Returns a list of result dicts: {source, line_number, line}.
    """
    results = []
    keyword_lower = keyword.lower()

    for i, line in enumerate(lines, start=1):
        if keyword_lower in line.lower():
            results.append({
                "source": source_name,
                "line_number": i,
                "line": line,
            })

    return results


def search_documents(documents, keyword):
    """
    Search across a dictionary of {name: [lines]} documents.
    Returns all collected results.
    """
    all_results = []

    for name, lines in documents.items():
        matches = search_in_lines(lines, keyword, name)
        all_results.extend(matches)

    return all_results


# ── Display ───────────────────────────────────────────────────

def display_results(results, keyword):
    """Print search results in a readable format."""
    if not results:
        print(f"\n  No matches found for '{keyword}'.")
        return

    print(f"\n  Results for '{keyword}':")
    print("  " + "-" * 60)

    # Group results by source document for cleaner output
    current_source = None
    for result in results:
        if result["source"] != current_source:
            current_source = result["source"]
            print(f"\n  [ {current_source} ]")

        print(f"    Line {result['line_number']:>4}: {result['line']}")

    print("\n  " + "-" * 60)
    print(f"  Total matches found: {len(results)}")


# ── Menu helpers ──────────────────────────────────────────────

def get_keyword():
    """Prompt the user for a non-empty search keyword."""
    while True:
        keyword = input("\n  Enter search keyword: ").strip()
        if keyword:
            return keyword
        print("  Keyword cannot be empty. Please try again.")


def choose_source():
    """
    Ask the user whether to search the built-in sample documents
    or load an external text file.
    """
    print("\n  Source options:")
    print("  1. Use built-in sample documents")
    print("  2. Load a text file")

    while True:
        choice = input("  Choose (1/2): ").strip()
        if choice in ("1", "2"):
            return choice
        print("  Invalid choice. Please enter 1 or 2.")


def load_user_file():
    """
    Prompt the user for a file path and attempt to load it.
    Returns a documents dict on success, or None on failure.
    """
    filepath = input("  Enter file path: ").strip()
    if not filepath:
        print("  File path cannot be empty.")
        return None

    lines = load_file(filepath)
    if lines is None:
        return None

    # Wrap the file lines in a documents dict using the filename as the key
    filename = os.path.basename(filepath)
    return {filename: lines}


# ── Main loop ─────────────────────────────────────────────────

def main():
    print("\n  ================================")
    print("       MINI SEARCH ENGINE        ")
    print("  ================================")

    while True:
        print("\n  Main Menu:")
        print("  1. New search")
        print("  2. Quit")

        choice = input("  Choose (1/2): ").strip()

        if choice == "2":
            print("\n  Goodbye.\n")
            break

        if choice != "1":
            print("  Invalid option. Please enter 1 or 2.")
            continue

        # Choose document source
        source_choice = choose_source()

        if source_choice == "1":
            documents = SAMPLE_DOCUMENTS
            print(f"  Using {len(documents)} built-in sample documents.")
        else:
            documents = load_user_file()
            if documents is None:
                # File loading failed; return to main menu
                continue

        # Get the search keyword from the user
        keyword = get_keyword()

        # Perform the search across all loaded documents
        results = search_documents(documents, keyword)

        # Show the results
        display_results(results, keyword)


# Entry point
if __name__ == "__main__":
    main()