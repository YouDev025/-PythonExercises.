"""
text_analyzer.py

This program analyzes a piece of text entered by the user.
It calculates and displays:
- Number of characters
- Number of words
- Number of sentences
- Most frequent words

After each analysis, the user can choose to analyze another text.
"""

import string

def count_characters(text):
    """Return the number of characters in the text (excluding spaces)."""
    return len(text.replace(" ", ""))

def count_words(text):
    """Return the number of words in the text."""
    words = text.split()
    return len(words)

def count_sentences(text):
    """Return the number of sentences in the text (basic split by .!?)."""
    sentences = [s for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    return len(sentences)

def most_frequent_words(text, top_n=5):
    """Return the most frequent words in the text."""
    words = text.lower().translate(str.maketrans("", "", string.punctuation)).split()
    frequency = {}
    for word in words:
        frequency[word] = frequency.get(word, 0) + 1
    sorted_words = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:top_n]

def main():
    print("-" * 40)
    print("Welcome to the Text Analyzer")
    print("-" * 40)

    while True:
        text = input("Enter your text: ").strip()

        print("\nAnalysis Results:")
        print(f"Characters (excluding spaces): {count_characters(text)}")
        print(f"Words: {count_words(text)}")
        print(f"Sentences: {count_sentences(text)}")

        print("\nMost Frequent Words:")
        for word, freq in most_frequent_words(text):
            print(f"{word}: {freq}")

        print("-" * 40)

        # Ask if user wants to analyze another text
        choice = input("Do you want to analyze another text? (y/n): ").strip().lower()
        if choice not in ("y", "yes"):
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()
