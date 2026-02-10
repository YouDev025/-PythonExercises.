import uuid  # Import the built-in uuid module


def generate_uuid():
    """Generate a random UUID (UUID4)."""
    return uuid.uuid4()


def main():
    print("=== UUID Generator ===")

    while True:
        # Generate and display a UUID
        new_uuid = generate_uuid()
        print(f"\nGenerated UUID: {new_uuid}")

        # Ask if the user wants another one
        choice = input("\nDo you want to generate another UUID? (y/n): ").strip().lower()
        if choice == "y":
            continue
        elif choice == "n":
            print("Exiting UUID Generator. Goodbye!")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            # Loop continues automatically


if __name__ == "__main__":
    main()
