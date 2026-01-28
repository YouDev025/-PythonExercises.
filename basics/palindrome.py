print("=== Palindrome Checker ===\n")

# Get input from user
text = input("Enter a word or phrase to check: ")

# Remove spaces and convert to lowercase for comparison
cleaned_text = text.replace(" ", "").lower()

# Reverse the cleaned text
reversed_text = cleaned_text[::-1]

# Check if palindrome
if cleaned_text == reversed_text:
    print(f"\n✓ '{text}' IS a palindrome!")
else:
    print(f"\n✗ '{text}' is NOT a palindrome.")

# Show the comparison
print(f"\nOriginal (cleaned): {cleaned_text}")
print(f"Reversed:           {reversed_text}")

#radar, ici, tôt, gag, ses, pop.
#Ada, Anna, Bob, Ève, Otto, Laval, Noyon.
#19291, 2002.