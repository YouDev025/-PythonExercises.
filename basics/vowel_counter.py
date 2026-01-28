print("=== Vowel Counter ===\n")

# Get input from user
text = input("Enter a text to count vowels: ")

# Initialize vowel counts
vowels = 'aeiouAEIOU'
a_count = 0
e_count = 0
i_count = 0
o_count = 0
u_count = 0

# Count each vowel
for char in text:
    if char in vowels:
        if char.lower() == 'a':
            a_count += 1
        elif char.lower() == 'e':
            e_count += 1
        elif char.lower() == 'i':
            i_count += 1
        elif char.lower() == 'o':
            o_count += 1
        elif char.lower() == 'u':
            u_count += 1

# Calculate total
total = a_count + e_count + i_count + o_count + u_count

# Display results
print(f"\nResults for: '{text}'")
print("-" * 40)
print(f"A: {a_count}")
print(f"E: {e_count}")
print(f"I: {i_count}")
print(f"O: {o_count}")
print(f"U: {u_count}")
print("-" * 40)
print(f"Total vowels: {total}")