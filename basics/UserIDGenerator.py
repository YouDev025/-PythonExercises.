import random
import string
from datetime import datetime

# User ID Generator without functions

print("=== USER ID GENERATOR ===")
print()

# Store generated IDs to avoid duplicates
generated_ids = []

# Continue generating IDs
continue_generation = True

while continue_generation:
    print("\n--- ID Generation Options ---")
    print("1 - Simple ID (numbers only)")
    print("2 - Alphanumeric ID (letters + numbers)")
    print("3 - Username-based ID")
    print("4 - Timestamp-based ID")
    print("5 - UUID-style ID")
    print("6 - Custom ID")
    print("0 - Quit")
    print()

    choice = input("Choose ID type (0-6): ").strip()

    if choice == "0":
        print("\nThank you for using User ID Generator!")
        break

    # Variable to store the generated ID
    user_id = ""

    # Option 1: Simple ID (numbers only)
    if choice == "1":
        print("\n--- Simple Numeric ID ---")
        length = input("Enter ID length (default 8): ").strip()

        if length == "":
            length = 8
        else:
            length = int(length)

        # Generate random numbers
        user_id = ""
        for i in range(length):
            user_id += str(random.randint(0, 9))

        print(f"\n Generated ID: {user_id}")

    # Option 2: Alphanumeric ID
    elif choice == "2":
        print("\n--- Alphanumeric ID ---")
        length = input("Enter ID length (default 10): ").strip()

        if length == "":
            length = 10
        else:
            length = int(length)

        # Characters to use
        characters = string.ascii_uppercase + string.digits

        # Generate random alphanumeric ID
        user_id = ""
        for i in range(length):
            user_id += random.choice(characters)

        print(f"\n Generated ID: {user_id}")

    # Option 3: Username-based ID
    elif choice == "3":
        print("\n--- Username-based ID ---")
        username = input("Enter username: ").strip()

        if username == "":
            print(" Username cannot be empty!")
        else:
            # Clean username (remove spaces, convert to lowercase)
            clean_username = username.lower().replace(" ", "")

            # Add random number
            random_number = random.randint(1000, 9999)

            user_id = f"{clean_username}{random_number}"

            print(f"\n Generated ID: {user_id}")

    # Option 4: Timestamp-based ID
    elif choice == "4":
        print("\n--- Timestamp-based ID ---")
        prefix = input("Enter prefix (optional): ").strip()

        # Get current timestamp
        timestamp = datetime.now()

        # Format: YYYYMMDDHHMMSS
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")

        # Add random suffix
        random_suffix = random.randint(100, 999)

        if prefix == "":
            user_id = f"{timestamp_str}{random_suffix}"
        else:
            user_id = f"{prefix}_{timestamp_str}{random_suffix}"

        print(f"\n Generated ID: {user_id}")

    # Option 5: UUID-style ID
    elif choice == "5":
        print("\n--- UUID-style ID ---")

        # Generate UUID-style format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        characters = string.ascii_lowercase + string.digits

        # First section (8 characters)
        section1 = ""
        for i in range(8):
            section1 += random.choice(characters)

        # Second section (4 characters)
        section2 = ""
        for i in range(4):
            section2 += random.choice(characters)

        # Third section (4 characters)
        section3 = ""
        for i in range(4):
            section3 += random.choice(characters)

        # Fourth section (4 characters)
        section4 = ""
        for i in range(4):
            section4 += random.choice(characters)

        # Fifth section (12 characters)
        section5 = ""
        for i in range(12):
            section5 += random.choice(characters)

        user_id = f"{section1}-{section2}-{section3}-{section4}-{section5}"

        print(f"\n Generated ID: {user_id}")

    # Option 6: Custom ID
    elif choice == "6":
        print("\n--- Custom ID Generator ---")
        prefix = input("Enter prefix: ").strip()
        separator = input("Enter separator (- or _ or none): ").strip()
        length = input("Enter random part length (default 6): ").strip()
        use_letters = input("Include letters? (y/n, default y): ").strip().lower()
        use_uppercase = input("Use uppercase? (y/n, default y): ").strip().lower()

        if length == "":
            length = 6
        else:
            length = int(length)

        if use_letters == "" or use_letters == "y":
            use_letters = True
        else:
            use_letters = False

        if use_uppercase == "" or use_uppercase == "y":
            use_uppercase = True
        else:
            use_uppercase = False

        # Build character set
        characters = string.digits
        if use_letters:
            if use_uppercase:
                characters += string.ascii_uppercase
            else:
                characters += string.ascii_lowercase

        # Generate random part
        random_part = ""
        for i in range(length):
            random_part += random.choice(characters)

        # Build final ID
        if prefix == "":
            user_id = random_part
        else:
            if separator == "":
                user_id = f"{prefix}{random_part}"
            else:
                user_id = f"{prefix}{separator}{random_part}"

        print(f"\n Generated ID: {user_id}")

    else:
        print("\n Invalid choice! Please select 0-6.")
        continue

    # Add to generated IDs list
    if user_id != "":
        generated_ids.append(user_id)

        # Display ID information
        print(f"   Length: {len(user_id)} characters")

        # Check if unique in current session
        count = generated_ids.count(user_id)
        if count > 1:
            print(f"  Warning: This ID was generated {count} times in this session")
        else:
            print("   ✓ Unique in this session")

    print("\n" + "=" * 50)

# Display summary
if len(generated_ids) > 0:
    print("\n--- Session Summary ---")
    print(f"Total IDs generated: {len(generated_ids)}")
    print(f"Unique IDs: {len(set(generated_ids))}")

    show_all = input("\nShow all generated IDs? (y/n): ").strip().lower()
    if show_all == "y" or show_all == "yes":
        print("\nGenerated IDs:")
        for idx, user_id in enumerate(generated_ids, 1):
            print(f"  {idx}. {user_id}")

print("\nGoodbye!")