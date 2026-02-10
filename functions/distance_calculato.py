import math  # Import math module for square root function


# Function to safely get a numeric coordinate from the user
def get_coordonate(prompt):
    while True:
        try:
            value = float(input(prompt))  # Try converting input to float
            return value
        except ValueError:
            print("Error : Invalid input. Please try again 'numeric value'.")


# Function to get unit of measurement (restricted to m or km)
def get_unit():
    while True:
        unit = input("Please enter your unit: ")  # Ask user for unit
        if unit.lower() in ["m", "km", "meters", "kilometers"]:  # Accept only valid units
            return unit
        else:
            print("Error : Invalid input ! Please try again ' m or Km ' for meters or kilometers.")


def main():
    print("===== Distance Calculator =====")

    # Get coordinates with validation
    x1 = get_coordonate("Enter the first x1 coordinate: ")
    y1 = get_coordonate("Enter the first y1 coordinate: ")
    x2 = get_coordonate("Enter the second x2 coordinate: ")
    y2 = get_coordonate("Enter the second y2 coordinate: ")

    # Get unit (m or km)
    unit = get_unit()

    # Apply distance formula
    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    # Display result with unit
    print(f"The distance between the two points is : {distance:.2f} {unit}")


# Entry point of the program
if __name__ == "__main__":
    main()
