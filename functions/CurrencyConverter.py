"""
Currency Converter - Simple console program
Allows user to convert between currencies using predefined exchange rates.
"""


def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def show_menu():
    print("=" * 50)
    print("           SIMPLE CURRENCY CONVERTER")
    print("=" * 50)
    print("Available currencies:")
    print("  USD - US Dollar")
    print("  EUR - Euro")
    print("  GBP - British Pound")
    print("  MAD - Moroccan Dirham")
    print("=" * 50)


def get_exchange_rates():
    # Example static rates (relative to USD)
    return {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.78,
        "MAD": 10.0
    }


def get_currency_input(prompt, rates):
    while True:
        code = input(prompt).strip().upper()
        if code in rates:
            return code
        else:
            print("Invalid currency code. Please try again.")


def get_amount_input(prompt):
    while True:
        try:
            amount = float(input(prompt))
            if amount >= 0:
                return amount
            else:
                print("Amount must be non-negative.")
        except ValueError:
            print("Invalid number. Please enter a valid amount.")


def convert_currency(amount, from_currency, to_currency, rates):
    usd_amount = amount / rates[from_currency]  # convert to USD
    return usd_amount * rates[to_currency]


def main():
    rates = get_exchange_rates()
    running = True

    while running:
        clear_screen()
        show_menu()

        from_currency = get_currency_input("Convert from (code): ", rates)
        to_currency = get_currency_input("Convert to (code): ", rates)
        amount = get_amount_input(f"Amount in {from_currency}: ")

        result = convert_currency(amount, from_currency, to_currency, rates)
        print("=" * 50)
        print(f"{amount:.2f} {from_currency} = {result:.2f} {to_currency}")
        print("=" * 50)

        choice = input("Do you want another conversion? (Y/N): ").strip().upper()
        if choice != 'Y':
            running = False

    clear_screen()
    print("Currency Converter closed. Goodbye!")


if __name__ == "__main__":
    main()
