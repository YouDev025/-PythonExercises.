import os
import datetime


# Function to clear the screen  
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Function to safely get a float input from the user
def get_float_input(prompt, allow_negative=False):
    while True:
        try:
            value = float(input(prompt))
            if not allow_negative and value < 0:
                print("Please enter a positive number.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a numeric value.")


# Function to validate menu choices
def get_choice_input(prompt, choices):
    while True:
        choice = input(prompt).strip()
        if choice in choices:
            return choice
        print(f"Invalid choice. Options are: {', '.join(choices)}")


# Common TVA rates (can be customized by country)
COMMON_TVA_RATES = {
    "1": {"name": "Standard (20%)", "rate": 20.0},
    "2": {"name": "Reduced (10%)", "rate": 10.0},
    "3": {"name": "Super-reduced (5.5%)", "rate": 5.5},
    "4": {"name": "Special (2.1%)", "rate": 2.1},
    "5": {"name": "Custom rate", "rate": None}
}


# Get TVA rate from user
def get_tva_rate():
    print("\nSelect TVA rate:")
    for key, value in COMMON_TVA_RATES.items():
        print(f"{key}. {value['name']}")

    choice = get_choice_input("Select option (1-5): ", ["1", "2", "3", "4", "5"])

    if choice == "5":
        return get_float_input("Enter custom TVA rate (%): ")
    else:
        return COMMON_TVA_RATES[choice]["rate"]


# Display calculation with detailed formatting
def display_calculation(ht, tva, ttc, rate, calculation_type):
    print("\n" + "=" * 60)
    print(f"TVA CALCULATION - {calculation_type}")
    print("=" * 60)
    print(f"HT (Before Tax):        {ht:>15,.2f} €")
    print(f"TVA ({rate:.2f}%):             {tva:>15,.2f} €")
    print("-" * 60)
    print(f"TTC (All Taxes):        {ttc:>15,.2f} €")
    print("=" * 60)
    print(f"Calculation Date: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    print("=" * 60 + "\n")


# Calculate and display multiple items
def calculate_multiple_items():
    clear_screen()
    print("=== Multiple Items TVA Calculator ===\n")

    rate = get_tva_rate()
    num_items = int(get_float_input("How many items? ", False))

    items = []
    total_ht = 0

    for i in range(num_items):
        print(f"\nItem {i + 1}:")
        description = input("Description (optional): ").strip()
        ht = get_float_input("Enter HT amount: ")
        tva = ht * rate / 100
        ttc = ht + tva

        items.append({
            "description": description if description else f"Item {i + 1}",
            "ht": ht,
            "tva": tva,
            "ttc": ttc
        })
        total_ht += ht

    total_tva = total_ht * rate / 100
    total_ttc = total_ht + total_tva

    # Display itemized breakdown
    print("\n" + "=" * 80)
    print("ITEMIZED TVA CALCULATION")
    print("=" * 80)
    print(f"{'Description':<30} {'HT':>12} {'TVA':>12} {'TTC':>12}")
    print("-" * 80)

    for item in items:
        print(f"{item['description']:<30} {item['ht']:>12,.2f} {item['tva']:>12,.2f} {item['ttc']:>12,.2f}")

    print("-" * 80)
    print(f"{'TOTAL':<30} {total_ht:>12,.2f} {total_tva:>12,.2f} {total_ttc:>12,.2f}")
    print("=" * 80)
    print(f"TVA Rate: {rate:.2f}%")
    print(f"Date: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    print("=" * 80 + "\n")


# Calculate discount with TVA
def calculate_with_discount():
    clear_screen()
    print("=== TVA Calculator with Discount ===\n")

    ht_original = get_float_input("Enter original HT amount: ")
    discount_percent = get_float_input("Enter discount percentage: ")
    rate = get_tva_rate()

    discount_amount = ht_original * discount_percent / 100
    ht_after_discount = ht_original - discount_amount
    tva = ht_after_discount * rate / 100
    ttc = ht_after_discount + tva

    print("\n" + "=" * 60)
    print("TVA CALCULATION WITH DISCOUNT")
    print("=" * 60)
    print(f"Original HT:            {ht_original:>15,.2f} €")
    print(f"Discount ({discount_percent:.2f}%):         {discount_amount:>15,.2f} €")
    print("-" * 60)
    print(f"HT After Discount:      {ht_after_discount:>15,.2f} €")
    print(f"TVA ({rate:.2f}%):             {tva:>15,.2f} €")
    print("-" * 60)
    print(f"TTC (Final Price):      {ttc:>15,.2f} €")
    print("=" * 60)
    print(f"Total Savings:          {ht_original + (ht_original * rate / 100) - ttc:>15,.2f} €")
    print("=" * 60 + "\n")


# Compare TVA rates
def compare_tva_rates():
    clear_screen()
    print("=== TVA Rate Comparison ===\n")

    ht = get_float_input("Enter HT amount: ")

    print("\n" + "=" * 70)
    print("TVA RATE COMPARISON")
    print("=" * 70)
    print(f"{'Rate':<20} {'TVA Amount':>15} {'TTC':>15}")
    print("-" * 70)

    rates = [20.0, 10.0, 5.5, 2.1]
    rate_names = ["Standard (20%)", "Reduced (10%)", "Super-reduced (5.5%)", "Special (2.1%)"]

    for rate, name in zip(rates, rate_names):
        tva = ht * rate / 100
        ttc = ht + tva
        print(f"{name:<20} {tva:>15,.2f} € {ttc:>15,.2f} €")

    print("=" * 70 + "\n")


# Main TVA calculation logic
def calculate_tva():
    clear_screen()
    print("=" * 60)
    print("   TVA CALCULATOR")
    print("=" * 60)
    print("1. Calculate TTC from HT")
    print("2. Calculate HT from TTC")
    print("3. Multiple items calculation")
    print("4. Calculate with discount")
    print("5. Compare TVA rates")
    print("6. Reverse charge (0% TVA)")
    print("7. Exit")
    print("=" * 60)

    choice = get_choice_input("Select an option (1-7): ", ["1", "2", "3", "4", "5", "6", "7"])

    if choice == "1":
        ht = get_float_input("Enter HT amount: ")
        rate = get_tva_rate()
        tva = ht * rate / 100
        ttc = ht + tva
        display_calculation(ht, tva, ttc, rate, "HT → TTC")

    elif choice == "2":
        ttc = get_float_input("Enter TTC amount: ")
        rate = get_tva_rate()
        ht = ttc / (1 + rate / 100)
        tva = ttc - ht
        display_calculation(ht, tva, ttc, rate, "TTC → HT")

    elif choice == "3":
        calculate_multiple_items()

    elif choice == "4":
        calculate_with_discount()

    elif choice == "5":
        compare_tva_rates()

    elif choice == "6":
        ht = get_float_input("Enter HT amount (reverse charge): ")
        print("\n" + "=" * 60)
        print("REVERSE CHARGE CALCULATION (0% TVA)")
        print("=" * 60)
        print(f"HT (Before Tax):        {ht:>15,.2f} €")
        print(f"TVA (0%):               {0:>15,.2f} €")
        print("-" * 60)
        print(f"TTC (All Taxes):        {ht:>15,.2f} €")
        print("=" * 60)
        print("Note: Reverse charge applies - buyer pays VAT")
        print("=" * 60 + "\n")

    elif choice == "7":
        print("\nExiting TVA Calculator. Goodbye!")
        return False

    return True


# Program loop
def main():
    while True:
        if not calculate_tva():
            break
        again = get_choice_input("Do you want to perform another calculation? (y/n): ", ["y", "n"])
        if again == "n":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()