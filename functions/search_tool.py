def search_items(keyword, items):
    # Convert keyword to lowercase for case-insensitive search
    keyword_lower = keyword.lower()
    # Return all items that contain the keyword
    result = [item for item in items if keyword_lower in item.lower()]
    return result


def main():
    while True:  # Loop to allow repeated searches
        print("----- Welcome to Items Researcher -----")

        # List of items to search through
        items = [
            "Apple iPhone 14",
            "Samsung Galaxy S23",
            "Google Pixel 7",
            "Apple MacBook Pro",
            "Dell XPS 15",
            "Sony PlayStation 5",
            "Microsoft Xbox Series X",
            "Apple iPad Air",
            "Samsung Galaxy Tab",
            "Amazon Kindle",
            "Apple Watch Series 8",
            "Fitbit Charge 5",
            "Sony WH-1000XM5 Headphones",
            "Apple AirPods Pro",
            "Bose QuietComfort Earbuds"
        ]

        print("=" * 50)
        print(f"Searching through {len(items)} items...")

        # Ask user for keyword
        keyword = input("Enter keyword to search: ")
        if not keyword.strip():  # Check if input is empty
            print("Error: Please enter a valid keyword")
            continue  # Retry instead of exiting

        print(f"Searching for '{keyword}' ....")
        results = search_items(keyword, items)  # Perform search

        # Display results
        if results:
            print(f"Found these {len(results)} items:")
            print("-" * 50)
            for i, item in enumerate(results, 1):
                print(f"{i}. {item}")
        else:
            print("No results found")

        print("=" * 50)

        # Ask if user wants to continue
        user_response = input("Do you want to continue (y/n)? ").strip().lower()
        if user_response in ["n", "no", "non"]:  # Accept English/French exit
            print("Exiting...")
            break


if __name__ == "__main__":
    main()
