"""Traffic Light Simulator - Console
Displays the states of a traffic light (Red, Green, Yellow) with timing.
"""

import time
import os


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def show_light(color, duration):
    clear_screen()
    print("=" * 40)
    print("          TRAFFIC LIGHT SIMULATOR")
    print("=" * 40)
    print()
    print(f"   >>> {color} <<<")
    print()
    print(f"   Please wait {duration} second(s)...")
    print()
    print("=" * 40)


def traffic_light_simulator():
    # Durations in seconds
    durations = {
        "RED": 5,
        "GREEN": 5,
        "YELLOW": 2
    }

    sequence = ["RED", "GREEN", "YELLOW"]

    try:
        while True:
            for color in sequence:
                show_light(color, durations[color])
                time.sleep(durations[color])
    except KeyboardInterrupt:
        clear_screen()
        print("Simulation stopped. Goodbye!")


if __name__ == "__main__":
    traffic_light_simulator()
