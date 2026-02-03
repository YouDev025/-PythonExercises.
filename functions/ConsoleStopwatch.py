"""
Console Stopwatch - A simple command-line stopwatch application
Commands:
  start - Start the stopwatch
  stop - Stop/pause the stopwatch
  lap - Record a lap time
  reset - Reset to zero
  quit - Exit the program
"""

import time
import sys

# Global variables to track stopwatch state
start_time = None
elapsed_time = 0
running = False
laps = []
last_lap_time = 0


def format_time(seconds):
    """Format seconds into HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def get_current_time():
    """Get current elapsed time"""
    global start_time, elapsed_time, running

    if running:
        return time.time() - start_time
    return elapsed_time


def start_stopwatch():
    """Start the stopwatch"""
    global start_time, elapsed_time, running

    if not running:
        start_time = time.time() - elapsed_time
        running = True
        print("✓ Stopwatch started")
    else:
        print("✗ Stopwatch is already running")


def stop_stopwatch():
    """Stop/pause the stopwatch"""
    global start_time, elapsed_time, running

    if running:
        elapsed_time = time.time() - start_time
        running = False
        print(f"✓ Stopwatch stopped at {format_time(elapsed_time)}")
    else:
        print("✗ Stopwatch is not running")


def reset_stopwatch():
    """Reset the stopwatch to zero"""
    global start_time, elapsed_time, running, laps, last_lap_time

    start_time = None
    elapsed_time = 0
    running = False
    laps = []
    last_lap_time = 0
    print("✓ Stopwatch reset")


def record_lap():
    """Record a lap time"""
    global laps, last_lap_time, running

    if running:
        current_time = get_current_time()
        lap_split = current_time - last_lap_time
        lap_num = len(laps) + 1
        laps.append((lap_num, current_time, lap_split))
        last_lap_time = current_time
        print(f"✓ Lap {lap_num}: {format_time(current_time)} (split: {format_time(lap_split)})")
    else:
        print("✗ Start the stopwatch first to record laps")


def display_status():
    """Display current stopwatch status"""
    global running, laps

    print("\n" + "=" * 60)
    current_time = format_time(get_current_time())
    status = "RUNNING ️" if running else "STOPPED"

    print(f"  Current Time: {current_time}")
    print(f"  Status: {status}")

    if laps:
        print("\n  Lap Times:")
        print("  " + "-" * 56)
        print(f"  {'Lap':<6} {'Total Time':<20} {'Split Time':<20}")
        print("  " + "-" * 56)

        for lap_num, total_time, split_time in laps:
            total_str = format_time(total_time)
            split_str = format_time(split_time)
            print(f"  {lap_num:<6} {total_str:<20} {split_str:<20}")

    print("=" * 60 + "\n")


def print_help():
    """Print available commands"""
    print("\n" + "=" * 60)
    print("  CONSOLE STOPWATCH - Available Commands:")
    print("=" * 60)
    print("  start  - Start the stopwatch")
    print("  stop   - Stop/pause the stopwatch")
    print("  lap    - Record a lap time")
    print("  reset  - Reset stopwatch to zero")
    print("  status - Show current status and lap times")
    print("  help   - Show this help message")
    print("  quit   - Exit the program")
    print("=" * 60 + "\n")


def main():
    """Main function to run the stopwatch"""
    print("\n" + "=" * 60)
    print("  WELCOME TO CONSOLE STOPWATCH")
    print("=" * 60)
    print("  Type 'help' for available commands or 'start' to begin")
    print("=" * 60 + "\n")

    while True:
        try:
            # Get user input
            command = input("stopwatch> ").strip().lower()

            if not command:
                continue

            # Process commands
            if command in ['start', 's']:
                start_stopwatch()

            elif command in ['stop', 'p', 'pause']:
                stop_stopwatch()

            elif command in ['lap', 'l']:
                record_lap()

            elif command in ['reset', 'r']:
                reset_stopwatch()

            elif command in ['status', 'show', 'display']:
                display_status()

            elif command in ['help', 'h', '?']:
                print_help()

            elif command in ['quit', 'q', 'exit']:
                print("\n✓ Goodbye!\n")
                break

            else:
                print(f"✗ Unknown command: '{command}'. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\n\n✓ Goodbye!\n")
            break
        except EOFError:
            print("\n\n✓ Goodbye!\n")
            break


if __name__ == "__main__":
    main()