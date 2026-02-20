def get_number_from_user(list_number):
    print(f"---- Enter numbers for List {list_number} ----")
    print("Type each number and press Enter. Type 'done' when finished.")  # Fixed: removed capital D since input is lowercased

    numbers = []
    while True:
        user_input = input("Enter a number or 'done' to finish: ").strip().lower()
        if user_input == "done":
            # Bug 3 Fixed: prevent empty lists from being accepted
            if len(numbers) == 0:
                print("You must enter at least one number before finishing.")
                continue
            break
        try:
            number = float(user_input)
            numbers.append(number)
            print(f"Added {number} to the list: {numbers}")  # Fixed: "Add" -> "Added"
        except ValueError:
            print("Error: Invalid input. Please enter a number or type 'done' to exit.")

    return numbers


def merge_lists(list1, list2):
    merged_list = []
    for item in list1:
        merged_list.append(item)
    for item in list2:
        merged_list.append(item)
    return merged_list


def remove_duplicates(numbers):
    unique_list = []
    for number in numbers:
        already_exist = False
        for seen in unique_list:
            if seen == number:
                already_exist = True
                break
        if not already_exist:
            unique_list.append(number)
    return unique_list


def display_lists(label, numbers):
    formatted = [int(n) if n == int(n) else n for n in numbers]  # Fixed: typo "formated" -> "formatted"
    print(f"\n{label} : {formatted} ({len(formatted)} items)\n")


print("=" * 50)
print("Welcome to the Merge Lists Program")
print("=" * 50)

while True:
    # Bug 1 Fixed: removed input() wrapper — just pass the list number (1 or 2)
    list1 = get_number_from_user(1)
    list2 = get_number_from_user(2)

    print("=" * 50)
    print("--- Your Lists ---")
    display_lists("List 1", list1)
    display_lists("List 2", list2)

    print("=" * 50)
    print("---- Merging Lists ----")
    merged_list = merge_lists(list1, list2)
    display_lists("Combined List", merged_list)

    print("Do you want to remove duplicates?")
    choice = input("Enter choice (y/n): ").strip().lower()

    if choice in ["y", "yes"]:
        unique_list = remove_duplicates(merged_list)
        duplicates_removed = len(merged_list) - len(unique_list)
        print("After Removing Duplicates:")
        display_lists("Unique List", unique_list)
        if duplicates_removed == 0:
            print("No duplicates found.")
        else:
            print(f"({duplicates_removed} duplicate(s) removed)")
    else:
        print("Skipping duplicate removal.")

    print("=" * 50)
    again = input("Do you want to merge another pair of lists? (y/n): ").strip().lower()
    if again not in ["y", "yes"]:
        print("Goodbye! Thank you for using the Merge Tool.")
        break