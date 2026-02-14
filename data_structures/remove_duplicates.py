# remove_duplicates.py
# Program that removes duplicates using two methods:
# 1. Loops and conditionals (preserves order)
# 2. Using set() (fast but order not guaranteed)

# Step 1: Ask the user to enter items
user_input = input("Enter a list of numbers or words separated by spaces: ")
original_list = user_input.split()

# Step 2: Ask the user which method to use
print("\nChoose a method to remove duplicates:")
print("1 - Loops and conditionals (preserves order)")
print("2 - Using set() (fast but order may change)")
choice = input("Enter 1 or 2: ")

# Step 3: Apply the chosen method
if choice == "1":
    # Method 1: Loops and conditionals
    unique_list = []
    for item in original_list:
        if item not in unique_list:
            unique_list.append(item)
    method_used = "Loops and conditionals"
elif choice == "2":
    # Method 2: Using set()
    unique_list = list(set(original_list))
    method_used = "set()"
else:
    print("Invalid choice. Defaulting to method 1 (loops).")
    unique_list = []
    for item in original_list:
        if item not in unique_list:
            unique_list.append(item)
    method_used = "Loops and conditionals"

# Step 4: Display results
print("\nOriginal list:", original_list)
print("List without duplicates:", unique_list)
print("Method used:", method_used)
