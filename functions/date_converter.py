from datetime import datetime

def convert_date(date):
    try:
        # Try to parse the input date in DD/MM/YYYY format
        dat_date = datetime.strptime(date, "%d/%m/%Y")

        # Convert to YYYY-MM-DD format
        return dat_date.strftime("%Y-%m-%d")

    except ValueError:
        # Raised if the input doesn't match the expected format or is invalid
        return None


def main():
    while True:  # Loop to allow multiple conversions
        print("---- DATE CONVERTER ----")
        print("Choose one of the following options:")
        print("1. DD/MM/YYYY")
        print("2. MM-DD-YYYY")
        print("3. YYYY.MM.DD")
        print("4. Exit")

        # Ask user to select input format
        choice = input("Enter your choice from 1 to 4: ").strip()

        # Map choice to format string
        if choice == "1":
            input_format = "%d/%m/%Y"
        elif choice == "2":
            input_format = "%m-%d-%Y"
        elif choice == "3":
            input_format = "%Y.%m.%d"
        elif choice == "4":
            print("Goodbye")
            break
        else:
            print("Invalid option")
            continue

        # Ask user for date in chosen format
        date = input("Enter a date (DD/MM/YYYY): ")

        # Convert date using helper function
        converted_date = convert_date(date)

        # Display result
        if converted_date:
            print(f"Converted date: {converted_date}")
        else:
            print("Invalid date format: Please use DD/MM/YYYY and ensure the date is valid.")

        # Ask if user wants to continue
        user_response = input("Do you want to continue (y/n)? ").strip().lower()
        if user_response in ["n", "no", "non"]:  # Accept English/French exit
            print("Exiting...")
            break


if __name__ == "__main__":
    main()
