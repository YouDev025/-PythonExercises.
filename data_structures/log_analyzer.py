"""
Log Analyzer Using Data Structures
----------------------------------
This program analyzes a given log file to extract useful insights such as
log level counts, IP address frequency, and unique IP addresses.

Author: Youssef Adardour
Date: February 2026
"""


# Function to read log file and store entries
def read_log_file(file_path):
    try:
        with open(file_path, "r") as file:
            # List to store all log entries
            log_entries = file.readlines()
        return log_entries
    except FileNotFoundError:
        print("Error: The specified file was not found.")
        return None
    except Exception as e:
        print(f"Error: Unable to read file. Details: {e}")
        return None


# Function to analyze logs using data structures
def analyze_logs(log_entries):
    # Dictionary to count occurrences of log levels
    log_levels = {"INFO": 0, "WARNING": 0, "ERROR": 0}

    # Dictionary to count IP address frequency
    ip_frequency = {}

    # Set to store unique IP addresses
    unique_ips = set()

    for entry in log_entries:
        parts = entry.strip().split()

        # Example log format assumption: "IP LOGLEVEL Message"
        if len(parts) >= 2:
            ip = parts[0]
            level = parts[1]

            # Count log levels
            if level in log_levels:
                log_levels[level] += 1

            # Count IP frequency
            ip_frequency[ip] = ip_frequency.get(ip, 0) + 1

            # Add to unique IP set
            unique_ips.add(ip)

    return log_levels, ip_frequency, unique_ips


# Function to display results
def display_results(log_entries, log_levels, ip_frequency, unique_ips):
    print("\n--- Log Analysis Results ---")
    print(f"Total number of log entries: {len(log_entries)}")

    print("\nCount per log level:")
    for level, count in log_levels.items():
        print(f"{level}: {count}")

    # Find most frequent IP
    if ip_frequency:
        most_frequent_ip = max(ip_frequency, key=ip_frequency.get)
        print(f"\nMost frequent IP address: {most_frequent_ip} ({ip_frequency[most_frequent_ip]} times)")
    else:
        print("\nNo IP addresses found.")

    print(f"Number of unique IP addresses: {len(unique_ips)}")


# Main function
def main():
    file_path = input("Enter the path to the log file: ")
    log_entries = read_log_file(file_path)

    if log_entries is not None:
        log_levels, ip_frequency, unique_ips = analyze_logs(log_entries)
        display_results(log_entries, log_levels, ip_frequency, unique_ips)


if __name__ == "__main__":
    main()
