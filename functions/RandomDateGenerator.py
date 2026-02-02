import os
import random
import datetime


# Clear the screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Validate integer input
def get_int_input(prompt, min_val=None, max_val=None):
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(f"Value must be >= {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"Value must be <= {max_val}.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter an integer.")


# Validate date format
def get_date_input(prompt):
    while True:
        try:
            date_str = input(prompt).strip()
            date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
            return date_obj
        except ValueError:
            print("Invalid date format. Please use DD-MM-YYYY (e.g., 25-12-2023).")


# Generate a random date between two given years
def generate_random_date(start_year, end_year):
    try:
        # Create datetime objects for range
        start_date = datetime.date(start_year, 1, 1)
        end_date = datetime.date(end_year, 12, 31)
        # Calculate days between start and end
        delta_days = (end_date - start_date).days
        # Pick a random offset
        random_days = random.randint(0, delta_days)
        return start_date + datetime.timedelta(days=random_days)
    except ValueError as e:
        print(f"Error generating date: {e}")
        return None


# Generate random date between two specific dates
def generate_random_date_between(start_date, end_date):
    try:
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        delta_days = (end_date - start_date).days
        random_days = random.randint(0, delta_days)
        return start_date + datetime.timedelta(days=random_days)
    except ValueError as e:
        print(f"Error generating date: {e}")
        return None


# Generate multiple random dates
def generate_multiple_dates(start_year, end_year, count):
    dates = []
    for _ in range(count):
        date = generate_random_date(start_year, end_year)
        if date:
            dates.append(date)
    return dates


# Get day of week name
def get_day_of_week(date):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return days[date.weekday()]


# Display date with additional info
def display_date_info(date, label="Random Date"):
    print("\n" + "=" * 50)
    print(f"{label.upper()}:")
    print("=" * 50)
    print(f"Date:         {date.strftime('%d-%m-%Y')}")
    print(f"Full Format:  {date.strftime('%A, %B %d, %Y')}")
    print(f"Day of Week:  {get_day_of_week(date)}")
    print(f"Day of Year:  {date.strftime('%j')}")
    print(f"ISO Format:   {date.isoformat()}")
    print("=" * 50 + "\n")


# Calculate days between two dates
def days_between_dates(date1, date2):
    delta = abs((date2 - date1).days)
    return delta


# Menu logic
def random_date_menu():
    clear_screen()
    print("=" * 50)
    print("   RANDOM DATE GENERATOR")
    print("=" * 50)
    print("1. Generate random date between two years")
    print("2. Generate random date in a specific year")
    print("3. Generate random date between two specific dates")
    print("4. Generate multiple random dates")
    print("5. Generate random date within X days from today")
    print("6. Generate random weekday/weekend date")
    print("7. Calculate days between two dates")
    print("8. Exit")
    print("=" * 50)

    choice = get_int_input("Select an option (1-8): ", 1, 8)

    if choice == 1:
        start_year = get_int_input("Enter start year: ", 1, 9999)
        end_year = get_int_input("Enter end year: ", start_year, 9999)
        date = generate_random_date(start_year, end_year)
        if date:
            display_date_info(date)

    elif choice == 2:
        year = get_int_input("Enter year: ", 1, 9999)
        date = generate_random_date(year, year)
        if date:
            display_date_info(date)

    elif choice == 3:
        print("\nEnter start date:")
        start_date = get_date_input("Start date (DD-MM-YYYY): ")
        print("Enter end date:")
        end_date = get_date_input("End date (DD-MM-YYYY): ")
        date = generate_random_date_between(start_date, end_date)
        if date:
            display_date_info(date)

    elif choice == 4:
        start_year = get_int_input("Enter start year: ", 1, 9999)
        end_year = get_int_input("Enter end year: ", start_year, 9999)
        count = get_int_input("How many dates to generate? ", 1, 100)
        dates = generate_multiple_dates(start_year, end_year, count)

        if dates:
            print("\n" + "=" * 50)
            print(f"GENERATED {len(dates)} RANDOM DATES:")
            print("=" * 50)
            for i, date in enumerate(dates, 1):
                print(f"{i}. {date.strftime('%d-%m-%Y')} ({get_day_of_week(date)})")
            print("=" * 50 + "\n")

    elif choice == 5:
        days_range = get_int_input("Enter number of days from today: ", 1, 3650)
        today = datetime.date.today()
        future_date = today + datetime.timedelta(days=days_range)
        date = generate_random_date_between(today, future_date)
        if date:
            display_date_info(date, "Random Date Within Range")
            print(f"Days from today: {days_between_dates(today, date)}\n")

    elif choice == 6:
        print("\n1. Generate random weekday (Mon-Fri)")
        print("2. Generate random weekend day (Sat-Sun)")
        day_type = get_int_input("Select option (1-2): ", 1, 2)

        start_year = get_int_input("Enter start year: ", 1, 9999)
        end_year = get_int_input("Enter end year: ", start_year, 9999)

        # Generate dates until we get the right type
        max_attempts = 1000
        for _ in range(max_attempts):
            date = generate_random_date(start_year, end_year)
            if date:
                is_weekday = date.weekday() < 5
                if (day_type == 1 and is_weekday) or (day_type == 2 and not is_weekday):
                    display_date_info(date, "Random Weekday" if day_type == 1 else "Random Weekend")
                    break
        else:
            print("\nCould not generate date after maximum attempts.\n")

    elif choice == 7:
        print("\nEnter first date:")
        date1 = get_date_input("First date (DD-MM-YYYY): ")
        print("Enter second date:")
        date2 = get_date_input("Second date (DD-MM-YYYY): ")

        days = days_between_dates(date1, date2)
        years = days // 365
        remaining_days = days % 365

        print("\n" + "=" * 50)
        print("DATE DIFFERENCE:")
        print("=" * 50)
        print(f"Date 1: {date1.strftime('%d-%m-%Y')}")
        print(f"Date 2: {date2.strftime('%d-%m-%Y')}")
        print(f"Days between: {days} days")
        print(f"Approximately: {years} years and {remaining_days} days")
        print("=" * 50 + "\n")

    elif choice == 8:
        print("\nExiting Random Date Generator. Goodbye!")
        return False

    return True


# Program loop
def main():
    random.seed()  # Initialize random number generator
    while True:
        if not random_date_menu():
            break
        again = input("Do you want to continue? (y/n): ").strip().lower()
        if again == "n":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()