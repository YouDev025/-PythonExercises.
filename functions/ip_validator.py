def validate_ip(ip_address):
    try:
        # Split the IP address into parts separated by "."
        parts = ip_address.split(".")

        # Check if there are exactly 4 parts
        if len(parts) != 4:
            return False

        for part in parts:
            # Try converting each part to an integer
            number = int(part)

            # Check if number is within valid IPv4 range (0–255)
            if number < 0 or number > 255:
                return False

        # If all checks pass, it's valid
        return True

    except ValueError:
        # Raised if part cannot be converted to integer (e.g. letters or empty string)
        return False


def main():
    while True:  # Loop to allow multiple validations
        print("---- IPv4 Address Validator ----")

        # Ask user for input
        ip_address = input("Enter your IPv4 Address: ")

        # Validate and display result
        if validate_ip(ip_address):
            print("Your IPv4 Address is valid")
        else:
            print("Your IPv4 Address is invalid. "
                  "It must have 4 numbers between 0 and 255 in the format x.x.x.x")

        # Ask if user wants to continue
        user_response = input("Do you want to continue (y/n)? ").strip().lower()
        if user_response in ["n", "no", "non"]:  # Accept English/French exit
            print("Exiting...")
            break


if __name__ == "__main__":
    main()
