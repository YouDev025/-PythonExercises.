"""
Data Indexing System
--------------------
This program allows users to input multiple text documents and builds an inverted index.
Users can search for words across documents, view occurrences, and explore frequent words.

Author: Youssef Adardour
Date: February 2026
"""

# -----------------------------
# Data Structures Used:
# - List: to store documents
# - Dictionary: to store inverted index {word: set(doc_ids)}
# - Set: to avoid duplicate document entries per word
# -----------------------------

def build_inverted_index(documents):
    """
    Build an inverted index from a list of documents.
    Case-insensitive indexing.
    """
    index = {}  # Dictionary: word -> set of document IDs
    for doc_id, text in enumerate(documents):
        words = text.lower().split()
        for word in words:
            if word not in index:
                index[word] = set()  # Set: avoids duplicate doc IDs
            index[word].add(doc_id)
    return index


def search_word(word, documents, index):
    """
    Search for a word in the inverted index.
    Display documents containing the word and number of occurrences.
    """
    word = word.lower()
    if word in index:
        doc_ids = index[word]
        print(f"\nWord '{word}' found in {len(doc_ids)} document(s):")
        for doc_id in doc_ids:
            count = documents[doc_id].lower().split().count(word)
            print(f"- Document {doc_id}: {count} occurrence(s)")
    else:
        print(f"\nWord '{word}' not found in any document.")


def most_frequent_words(documents, index, top_n=5):
    """
    Display the most frequent indexed words.
    Sorted alphabetically.
    """
    word_counts = {}
    for word, doc_ids in index.items():
        # Count total occurrences across all documents
        total_count = sum(documents[doc_id].lower().split().count(word) for doc_id in doc_ids)
        word_counts[word] = total_count

    # Sort alphabetically first, then by frequency (descending)
    sorted_words = sorted(word_counts.items(), key=lambda x: (-x[1], x[0]))

    print(f"\nTop {top_n} most frequent words:")
    for word, count in sorted_words[:top_n]:
        print(f"- {word}: {count} occurrence(s)")


def main():
    documents = []  # List: stores all user documents
    index = {}      # Dictionary: stores inverted index

    while True:
        print("\n--- Data Indexing System ---")
        print("1. Add a document")
        print("2. Build inverted index")
        print("3. Search for a word")
        print("4. Show most frequent words")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            text = input("Enter document text: ").strip()
            if text:
                documents.append(text)
                print("Document added successfully.")
            else:
                print("Invalid input. Document cannot be empty.")

        elif choice == "2":
            if documents:
                index = build_inverted_index(documents)
                print("Inverted index built successfully.")
            else:
                print("No documents available. Please add documents first.")

        elif choice == "3":
            if not index:
                print("Index not built yet. Please build the index first.")
            else:
                word = input("Enter word to search: ").strip()
                if word:
                    search_word(word, documents, index)
                else:
                    print("Invalid input. Word cannot be empty.")

        elif choice == "4":
            if not index:
                print("Index not built yet. Please build the index first.")
            else:
                most_frequent_words(documents, index)

        elif choice == "5":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    main()
