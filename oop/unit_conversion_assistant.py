"""
Unit Conversion Assistant - Object-Oriented Programming
A program that performs unit conversions using OOP principles.
"""

from abc import ABC, abstractmethod


class UnitConverter(ABC):
    """
    Abstract base class for all unit converters.
    Defines the common interface that all conversion classes must implement.
    """

    def __init__(self):
        """Initialize the converter with private attributes."""
        self._value = 0.0
        self._source_unit = ""
        self._target_unit = ""
        self._result = 0.0

    @abstractmethod
    def get_supported_units(self):
        """
        Return a list of supported units for this converter.
        Must be implemented by child classes.
        """
        pass

    @abstractmethod
    def convert(self):
        """
        Perform the conversion calculation.
        Must be implemented by child classes.
        """
        pass

    def set_conversion_params(self, value, source_unit, target_unit):
        """
        Set the parameters for conversion with validation.

        Args:
            value: The numeric value to convert
            source_unit: The unit to convert from
            target_unit: The unit to convert to

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate value is numeric
        try:
            self._value = float(value)
        except (ValueError, TypeError):
            raise ValueError("Value must be a valid number")

        # Validate units are not empty
        if not source_unit or not source_unit.strip():
            raise ValueError("Source unit cannot be empty")

        if not target_unit or not target_unit.strip():
            raise ValueError("Target unit cannot be empty")

        # Validate units are supported
        supported = self.get_supported_units()

        source_clean = source_unit.strip().lower()
        target_clean = target_unit.strip().lower()

        if source_clean not in [u.lower() for u in supported]:
            raise ValueError(f"Source unit '{source_unit}' is not supported")

        if target_clean not in [u.lower() for u in supported]:
            raise ValueError(f"Target unit '{target_unit}' is not supported")

        self._source_unit = source_clean
        self._target_unit = target_clean

    def get_result(self):
        """
        Return the formatted conversion result.

        Returns:
            A string with the formatted result
        """
        return f"{self._value} {self._source_unit} = {self._result:.4f} {self._target_unit}"

    def get_value(self):
        """Getter for the value attribute."""
        return self._value

    def get_source_unit(self):
        """Getter for the source unit."""
        return self._source_unit

    def get_target_unit(self):
        """Getter for the target unit."""
        return self._target_unit


class LengthConverter(UnitConverter):
    """Handles length unit conversions (meters, feet, kilometers, miles, etc.)."""

    def __init__(self):
        """Initialize with length-specific conversion factors."""
        super().__init__()
        # Conversion factors to meters (base unit)
        self._conversion_factors = {
            'meter': 1.0,
            'meters': 1.0,
            'm': 1.0,
            'kilometer': 1000.0,
            'kilometers': 1000.0,
            'km': 1000.0,
            'centimeter': 0.01,
            'centimeters': 0.01,
            'cm': 0.01,
            'millimeter': 0.001,
            'millimeters': 0.001,
            'mm': 0.001,
            'foot': 0.3048,
            'feet': 0.3048,
            'ft': 0.3048,
            'inch': 0.0254,
            'inches': 0.0254,
            'in': 0.0254,
            'yard': 0.9144,
            'yards': 0.9144,
            'yd': 0.9144,
            'mile': 1609.34,
            'miles': 1609.34,
            'mi': 1609.34
        }

    def get_supported_units(self):
        """Return list of supported length units."""
        return list(set(self._conversion_factors.keys()))

    def convert(self):
        """
        Perform length conversion by converting to base unit (meters) then to target.

        Raises:
            ValueError: If conversion parameters haven't been set
        """
        if not self._source_unit or not self._target_unit:
            raise ValueError("Conversion parameters must be set before converting")

        try:
            # Convert source to meters (base unit)
            value_in_meters = self._value * self._conversion_factors[self._source_unit]

            # Convert from meters to target unit
            self._result = value_in_meters / self._conversion_factors[self._target_unit]

        except KeyError as e:
            raise ValueError(f"Conversion error: Unit {e} not found")
        except ZeroDivisionError:
            raise ValueError("Conversion error: Division by zero")


class MassConverter(UnitConverter):
    """Handles mass/weight unit conversions (kilograms, pounds, grams, etc.)."""

    def __init__(self):
        """Initialize with mass-specific conversion factors."""
        super().__init__()
        # Conversion factors to kilograms (base unit)
        self._conversion_factors = {
            'kilogram': 1.0,
            'kilograms': 1.0,
            'kg': 1.0,
            'gram': 0.001,
            'grams': 0.001,
            'g': 0.001,
            'milligram': 0.000001,
            'milligrams': 0.000001,
            'mg': 0.000001,
            'pound': 0.453592,
            'pounds': 0.453592,
            'lb': 0.453592,
            'lbs': 0.453592,
            'ounce': 0.0283495,
            'ounces': 0.0283495,
            'oz': 0.0283495,
            'ton': 1000.0,
            'tons': 1000.0,
            'tonne': 1000.0,
            'tonnes': 1000.0
        }

    def get_supported_units(self):
        """Return list of supported mass units."""
        return list(set(self._conversion_factors.keys()))

    def convert(self):
        """
        Perform mass conversion by converting to base unit (kilograms) then to target.

        Raises:
            ValueError: If conversion parameters haven't been set
        """
        if not self._source_unit or not self._target_unit:
            raise ValueError("Conversion parameters must be set before converting")

        try:
            # Convert source to kilograms (base unit)
            value_in_kg = self._value * self._conversion_factors[self._source_unit]

            # Convert from kilograms to target unit
            self._result = value_in_kg / self._conversion_factors[self._target_unit]

        except KeyError as e:
            raise ValueError(f"Conversion error: Unit {e} not found")
        except ZeroDivisionError:
            raise ValueError("Conversion error: Division by zero")


class TemperatureConverter(UnitConverter):
    """Handles temperature conversions (Celsius, Fahrenheit, Kelvin)."""

    def __init__(self):
        """Initialize temperature converter."""
        super().__init__()
        self._supported_units = [
            'celsius', 'c', 'fahrenheit', 'f', 'kelvin', 'k'
        ]

    def get_supported_units(self):
        """Return list of supported temperature units."""
        return self._supported_units

    def convert(self):
        """
        Perform temperature conversion using specific formulas.
        Temperature conversions don't use simple multiplication factors.

        Raises:
            ValueError: If conversion parameters haven't been set
        """
        if not self._source_unit or not self._target_unit:
            raise ValueError("Conversion parameters must be set before converting")

        # First, convert source to Celsius (base unit)
        if self._source_unit in ['celsius', 'c']:
            celsius_value = self._value
        elif self._source_unit in ['fahrenheit', 'f']:
            celsius_value = (self._value - 32) * 5/9
        elif self._source_unit in ['kelvin', 'k']:
            celsius_value = self._value - 273.15
        else:
            raise ValueError(f"Unknown source unit: {self._source_unit}")

        # Then, convert from Celsius to target unit
        if self._target_unit in ['celsius', 'c']:
            self._result = celsius_value
        elif self._target_unit in ['fahrenheit', 'f']:
            self._result = (celsius_value * 9/5) + 32
        elif self._target_unit in ['kelvin', 'k']:
            self._result = celsius_value + 273.15
        else:
            raise ValueError(f"Unknown target unit: {self._target_unit}")


class TimeConverter(UnitConverter):
    """Handles time unit conversions (seconds, minutes, hours, days, etc.)."""

    def __init__(self):
        """Initialize with time-specific conversion factors."""
        super().__init__()
        # Conversion factors to seconds (base unit)
        self._conversion_factors = {
            'second': 1.0,
            'seconds': 1.0,
            's': 1.0,
            'sec': 1.0,
            'minute': 60.0,
            'minutes': 60.0,
            'min': 60.0,
            'hour': 3600.0,
            'hours': 3600.0,
            'hr': 3600.0,
            'h': 3600.0,
            'day': 86400.0,
            'days': 86400.0,
            'd': 86400.0,
            'week': 604800.0,
            'weeks': 604800.0,
            'wk': 604800.0,
            'month': 2592000.0,  # Approximate: 30 days
            'months': 2592000.0,
            'year': 31536000.0,  # 365 days
            'years': 31536000.0,
            'yr': 31536000.0
        }

    def get_supported_units(self):
        """Return list of supported time units."""
        return list(set(self._conversion_factors.keys()))

    def convert(self):
        """
        Perform time conversion by converting to base unit (seconds) then to target.

        Raises:
            ValueError: If conversion parameters haven't been set
        """
        if not self._source_unit or not self._target_unit:
            raise ValueError("Conversion parameters must be set before converting")

        try:
            # Convert source to seconds (base unit)
            value_in_seconds = self._value * self._conversion_factors[self._source_unit]

            # Convert from seconds to target unit
            self._result = value_in_seconds / self._conversion_factors[self._target_unit]

        except KeyError as e:
            raise ValueError(f"Conversion error: Unit {e} not found")
        except ZeroDivisionError:
            raise ValueError("Conversion error: Division by zero")


class ConversionApp:
    """
    Application manager class that controls the entire program.
    Handles user interaction, menu display, and delegates conversion tasks.
    """

    def __init__(self):
        """Initialize the application with all converter objects."""
        self._converters = {
            '1': LengthConverter(),
            '2': MassConverter(),
            '3': TemperatureConverter(),
            '4': TimeConverter()
        }
        self._category_names = {
            '1': 'Length',
            '2': 'Mass',
            '3': 'Temperature',
            '4': 'Time'
        }
        self._running = True

    def display_main_menu(self):
        """Display the main menu of conversion categories."""
        print("\n" + "="*50)
        print("   UNIT CONVERSION ASSISTANT")
        print("="*50)
        print("\nSelect a conversion category:")
        print("  1. Length (meters, feet, kilometers, etc.)")
        print("  2. Mass (kilograms, pounds, grams, etc.)")
        print("  3. Temperature (Celsius, Fahrenheit, Kelvin)")
        print("  4. Time (seconds, minutes, hours, etc.)")
        print("  5. Exit")
        print("="*50)

    def display_supported_units(self, converter):
        """
        Display the supported units for a given converter.

        Args:
            converter: The UnitConverter object
        """
        units = converter.get_supported_units()
        print("\nSupported units:")
        # Display in a neat format, sorted
        sorted_units = sorted(units)
        for i, unit in enumerate(sorted_units, 1):
            print(f"  - {unit}", end="")
            if i % 4 == 0:  # New line every 4 units
                print()
        print()  # Final newline

    def get_user_choice(self):
        """
        Get and validate the user's menu choice.

        Returns:
            The user's choice as a string
        """
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            else:
                print("[ERROR] Invalid choice. Please enter a number between 1 and 5.")

    def get_conversion_details(self, converter):
        """
        Get conversion details from the user.

        Args:
            converter: The UnitConverter object to use

        Returns:
            Tuple of (value, source_unit, target_unit) or None if user cancels
        """
        print("\n" + "-"*50)

        # Get value
        while True:
            value_input = input("Enter the value to convert (or 'back' to return): ").strip()
            if value_input.lower() == 'back':
                return None

            try:
                value = float(value_input)
                break
            except ValueError:
                print("[ERROR] Please enter a valid number.")

        # Get source unit
        while True:
            source_unit = input("Enter the source unit: ").strip()
            if source_unit:
                break
            print("[ERROR] Source unit cannot be empty. Please try again.")

        # Get target unit
        while True:
            target_unit = input("Enter the target unit: ").strip()
            if target_unit:
                break
            print("[ERROR] Target unit cannot be empty. Please try again.")

        return value, source_unit, target_unit

    def perform_conversion(self, category_choice):
        """
        Perform a conversion for the selected category.

        Args:
            category_choice: The user's category selection
        """
        converter = self._converters[category_choice]
        category_name = self._category_names[category_choice]

        print(f"\n--- {category_name} Conversion ---")

        # Display supported units
        self.display_supported_units(converter)

        # Get conversion details
        details = self.get_conversion_details(converter)

        if details is None:
            print("\n  Returning to main menu...")
            return

        value, source_unit, target_unit = details

        # Attempt the conversion with error handling
        try:
            converter.set_conversion_params(value, source_unit, target_unit)
            converter.convert()
            result = converter.get_result()

            print("\n" + "="*50)
            print("[OK] CONVERSION RESULT:")
            print(f"   {result}")
            print("="*50)

        except ValueError as e:
            print(f"\n[ERROR] Error: {e}")
            print("Please try again with valid inputs.")
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            print("Please try again.")

    def run(self):
        """Main application loop."""
        print("\n Welcome to the Unit Conversion Assistant!")
        print("This program uses Object-Oriented Programming principles.")

        while self._running:
            self.display_main_menu()
            choice = self.get_user_choice()

            if choice == '5':
                self._running = False
                print("\n Thank you for using the Unit Conversion Assistant!")
                print("Goodbye!\n")
            else:
                self.perform_conversion(choice)
                input("\nPress Enter to continue...")


# Main program entry point
if __name__ == "__main__":
    app = ConversionApp()
    app.run()