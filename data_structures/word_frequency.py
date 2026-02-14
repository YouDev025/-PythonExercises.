# word_frequency.py
# A simple program to count word frequencies in a sentence or paragraph.
# Beginner-friendly: uses only loops, conditionals, and dictionaries.

# Step 1: Ask the user to enter text
text = input("Enter a sentence or paragraph: ")

# Step 2: Convert text to lowercase (so 'Word' and 'word' are treated the same)
text = text.lower()

# Step 3: Split the text into words
# .split() breaks the text into a list using spaces
words = text.split()

# Step 4: Create an empty dictionary to store word counts
frequency = {}

# Step 5: Loop through each word
for word in words:
    # If the word is already in the dictionary, increase its count
    if word in frequency:
        frequency[word] += 1
    # If not, add it to the dictionary with count = 1
    else:
        frequency[word] = 1

# Step 6: Display the results
print("\nWord frequencies:")
for word, count in frequency.items():
    print(word, ":", count)
