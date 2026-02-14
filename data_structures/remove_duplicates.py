# remove_duplicates.py
# A beginner-friendly program to remove duplicates from a list
# without using the set() function.

# Step 1: Ask the user to enter items separated by spaces
user_input = input("Enter a list of numbers or words separated by spaces: ")

# Step 2: Split the input string into a list
original_list = user_input.split()

# Step 3: Create an empty list to store unique elements
unique_list = []

# Step 4: Loop through the original list
for item in original_list:
    # If the item is not already in unique_list, add it
    if item not in unique_list:
        unique_list.append(item)

# Step 5: Display the results
print("\nOriginal list:", original_list)
print("List without duplicates:", unique_list)
