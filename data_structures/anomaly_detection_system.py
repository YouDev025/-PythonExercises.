"""
Anomaly Detection System
------------------------
This program analyzes numerical data (e.g., network traffic, login attempts, sensor readings)
to calculate basic statistics and detect anomalies based on statistical thresholds.

Author: Youssef Adardour
Date: February 2026
"""

import statistics

# Function to safely collect numerical input from the user
def collect_data():
    data = []
    print("Enter numerical values (type 'done' to finish):")
    while True:
        user_input = input("> ")
        if user_input.lower() == "done":
            break
        try:
            value = float(user_input)  # Convert input to float
            data.append(value)         # Store values in a list
        except ValueError:
            print("Invalid input. Please enter a number or 'done'.")
    return data

# Function to calculate statistics and store them in a dictionary
def calculate_statistics(data):
    stats = {}
    if data:
        stats["mean"] = statistics.mean(data)
        stats["median"] = statistics.median(data)
        stats["std_dev"] = statistics.pstdev(data)  # Population standard deviation
    else:
        stats["mean"] = stats["median"] = stats["std_dev"] = None
    return stats

# Function to detect anomalies based on mean ± 2*std_dev
def detect_anomalies(data, stats):
    anomalies = []
    if stats["mean"] is not None and stats["std_dev"] is not None:
        lower_bound = stats["mean"] - 2 * stats["std_dev"]
        upper_bound = stats["mean"] + 2 * stats["std_dev"]
        for value in data:
            if value < lower_bound or value > upper_bound:
                anomalies.append(value)
    return anomalies

# Function to display results
def display_results(data, stats, anomalies):
    print("\n--- Results ---")
    print("All values:", data)
    print("Statistics:", stats)
    print("Detected anomalies:", anomalies)
    print("Number of anomalies:", len(anomalies))
    print("Unique anomalies (set):", set(anomalies))  # Using a set for uniqueness

# Optional: Sliding window detection (advanced)
def sliding_window_detection(data, window_size=3):
    spikes = []
    for i in range(window_size, len(data)):
        diff = data[i] - data[i - window_size]
        if abs(diff) > 2 * statistics.pstdev(data):  # Sudden spike rule
            spikes.append((i, data[i]))
    return spikes

# Main program
def main():
    data = collect_data()
    if not data:
        print("No data entered. Exiting program.")
        return

    stats = calculate_statistics(data)
    anomalies = detect_anomalies(data, stats)
    display_results(data, stats, anomalies)

    # Advanced option: detect spikes
    spikes = sliding_window_detection(data)
    if spikes:
        print("\nSudden spikes detected at positions:", spikes)

if __name__ == "__main__":
    main()
