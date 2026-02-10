def paginate(items, page_number, items_per_page):
    """
    Paginate a list of items.
    """
    if not items:
        return []
    if page_number < 1 or items_per_page < 1:
        return []

    start_index = (page_number - 1) * items_per_page
    end_index = start_index + items_per_page

    if start_index >= len(items):
        return []

    return items[start_index:end_index]


def main():
    print("=== Pagination Function ===")

    # Ask user for items
    raw_items = input("Enter items separated by commas: ").strip()
    items = [item.strip() for item in raw_items.split(",") if item.strip()]

    if not items:
        print("No items provided. Exiting...")
        return

    # Ask for items per page
    while True:
        try:
            items_per_page = int(input("Enter number of items per page: "))
            if items_per_page < 1:
                print("Items per page must be at least 1.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    # Interactive navigation
    page_number = 1
    while True:
        page_items = paginate(items, page_number, items_per_page)

        if page_items:
            print(f"\n--- Page {page_number} ---")
            for i, item in enumerate(page_items, start=1):
                print(f"{i}. {item}")
        else:
            print(f"\nPage {page_number} is empty.")

        # Navigation options
        choice = input("\nEnter 'n' for next page, 'p' for previous page, 'q' to quit: ").strip().lower()
        if choice == "n":
            page_number += 1
        elif choice == "p":
            if page_number > 1:
                page_number -= 1
            else:
                print("Already at the first page.")
        elif choice == "q":
            print("Exiting Pagination Function...")
            break
        else:
            print("Invalid input. Please enter 'n', 'p', or 'q'.")


if __name__ == "__main__":
    main()
