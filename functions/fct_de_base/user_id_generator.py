import random
import string
from datetime import datetime


# User ID Generator with functions

def display_welcome():
    """Display welcome message"""
    print("=== USER ID GENERATOR ===")
    print()


def display_menu():
    """Display the main menu"""
    print("\n--- ID Generation Options ---")
    print("1 - Simple ID (numbers only)")
    print("2 - Alphanumeric ID (letters + numbers)")
    print("3 - Username-based ID")
    print("4 - Timestamp-based ID")
    print("5 - UUID-style ID")
    print("6 - Custom ID")
    print("0 - Quit")
    print()


def get_user_choice():
    """Get and return user's menu choice"""
    choice = input("Choose ID type (0-6): ").strip()
    return choice


def generate_simple_id():
    """Generate a simple numeric ID"""
    print("\n--- Simple Numeric ID ---")
    length = input("Enter ID length (default 8): ").strip()

    if length == "":
        length = 8
    else:
        length = int(length)

    user_id = ""
    for i in range(length):
        user_id += str(random.randint(0, 9))

    return user_id


def generate_alphanumeric_id():
    """Generate an alphanumeric ID"""
    print("\n--- Alphanumeric ID ---")
    length = input("Enter ID length (default 10): ").strip()

    if length == "":
        length = 10
    else:
        length = int(length)

    characters = string.ascii_uppercase + string.digits

    user_id = ""
    for i in range(length):
        user_id += random.choice(characters)

    return user_id


def generate_username_based_id():
    """Generate a username-based ID"""
    print("\n--- Username-based ID ---")
    username = input("Enter username: ").strip()

    if username == "":
        print("❌ Username cannot be empty!")
        return ""

    clean_username = username.lower().replace(" ", "")
    random_number = random.randint(1000, 9999)
    user_id = f"{clean_username}{random_number}"

    return user_id


def generate_timestamp_id():
    """Generate a timestamp-based ID"""
    print("\n--- Timestamp-based ID ---")
    prefix = input("Enter prefix (optional): ").strip()

    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
    random_suffix = random.randint(100, 999)

    if prefix == "":
        user_id = f"{timestamp_str}{random_suffix}"
    else:
        user_id = f"{prefix}_{timestamp_str}{random_suffix}"

    return user_id


def generate_uuid_style_id():
    """Generate a UUID-style ID"""
    print("\n--- UUID-style ID ---")

    characters = string.ascii_lowercase + string.digits

    # Generate each section
    sections = []
    section_lengths = [8, 4, 4, 4, 12]

    for length in section_lengths:
        section = ""
        for i in range(length):
            section += random.choice(characters)
        sections.append(section)

    user_id = "-".join(sections)
    return user_id


def generate_custom_id():
    """Generate a custom ID based on user preferences"""
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

    return user_id


def display_generated_id(user_id, generated_ids):
    """Display the generated ID with information"""
    if user_id == "":
        return

    print(f"\n✅ Generated ID: {user_id}")
    print(f"   Length: {len(user_id)} characters")

    # Check if unique in current session
    count = generated_ids.count(user_id)
    if count > 1:
        print(f"   ⚠️  Warning: This ID was generated {count} times in this session")
    else:
        print("   ✓ Unique in this session")

    print("\n" + "=" * 50)


def display_session_summary(generated_ids):
    """Display summary of the session"""
    if len(generated_ids) == 0:
        return

    print("\n--- Session Summary ---")
    print(f"Total IDs generated: {len(generated_ids)}")
    print(f"Unique IDs: {len(set(generated_ids))}")

    show_all = input("\nShow all generated IDs? (y/n): ").strip().lower()
    if show_all == "y" or show_all == "yes":
        print("\nGenerated IDs:")
        for idx, user_id in enumerate(generated_ids, 1):
            print(f"  {idx}. {user_id}")


def main():
    """Main function to run the ID generator"""
    display_welcome()

    generated_ids = []
    continue_generation = True

    while continue_generation:
        display_menu()
        choice = get_user_choice()

        if choice == "0":
            print("\nThank you for using User ID Generator!")
            break

        user_id = ""

        if choice == "1":
            user_id = generate_simple_id()
        elif choice == "2":
            user_id = generate_alphanumeric_id()
        elif choice == "3":
            user_id = generate_username_based_id()
        elif choice == "4":
            user_id = generate_timestamp_id()
        elif choice == "5":
            user_id = generate_uuid_style_id()
        elif choice == "6":
            user_id = generate_custom_id()
        else:
            print("\n❌ Invalid choice! Please select 0-6.")
            continue

        if user_id != "":
            generated_ids.append(user_id)
            display_generated_id(user_id, generated_ids)

    display_session_summary(generated_ids)
    print("\nGoodbye!")


# Run the program
if __name__ == "__main__":
    main()