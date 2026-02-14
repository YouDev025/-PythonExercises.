# Contact book using dictionary
contacts = {}


def add_contact():
    try:
        name = input("Enter contact name: ")

        # Keep asking until phone is valid
        while True:
            phone = input("Enter phone number (digits only): ")
            if phone.isdigit():
                contacts[name] = phone
                print(f"{name} added.")
                break
            else:
                print(" Phone must be numbers only. Please try again.")

    except Exception as e:
        print("Error:", e)


def delete_contact():
    try:
        name = input("Enter name to delete: ")
        if name in contacts:
            confirm = input(f"Are you sure you want to delete {name}? (y/n): ")
            if confirm.lower() in ["y", "yes"]:
                del contacts[name]
                print(f"{name} removed.")
            else:
                print("Deletion cancelled.")
        else:
            print("Name not found.")
    except Exception as e:
        print("Error:", e)


def search_contact():
    try:
        name = input("Enter name to search: ")
        if name in contacts:
            print(f"{name}: {contacts[name]}")
        else:
            print("Name not found.")
    except Exception as e:
        print("Error:", e)


def display_contacts():
    try:
        if contacts:
            print("All contacts:")
            for name, phone in contacts.items():
                print(f"{name}: {phone}")
        else:
            print("List empty.")
    except Exception as e:
        print("Error:", e)


def update_contact():
    try:
        name = input("Enter name to update: ")
        if name in contacts:
            print(f"Current phone: {contacts[name]}")
            new_phone = input("Enter new phone (digits only): ")
            if not new_phone.isdigit():
                raise ValueError("Phone must be numbers only.")
            contacts[name] = new_phone
            print("Updated successfully.")
        else:
            print("Name not found.")
    except ValueError as e:
        print(e)
    except Exception as e:
        print("Error:", e)


def main():
    while True:
        print("\n==== Contact Book Menu ====")
        print("1. Add contact")
        print("2. Remove contact")
        print("3. Search contact")
        print("4. Display contacts")
        print("5. Update contact")
        print("6. Exit")

        choice = input("Enter choice: ")
        try:
            if choice == "1":
                add_contact()
            elif choice == "2":
                delete_contact()
            elif choice == "3":
                search_contact()
            elif choice == "4":
                display_contacts()
            elif choice == "5":
                update_contact()
            elif choice == "6":
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
