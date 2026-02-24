"""
Multi-Criteria Sorting System
-----------------------------
This program allows users to enter multiple records (e.g., students with name, age, and score).
It supports sorting by multiple criteria (score, age, name) and displays results clearly.

Author: Youssef Adardour
Date: February 2026
"""


# -----------------------------
# Data Structures Used:
# - List: to store records
# - Dictionary: each record stored as {"name": str, "age": int, "score": int}
# - Sorting: custom key function (lambda) or manual merge sort
# -----------------------------

def add_record(records):
    """Add a new student record with validation."""
    try:
        name = input("Enter student name: ").strip()
        age = int(input("Enter student age: ").strip())
        score = int(input("Enter student score: ").strip())
        if name and age >= 0 and score >= 0:
            records.append({"name": name, "age": age, "score": score})
            print("Record added successfully.")
        else:
            print("Invalid input. Age and score must be non-negative.")
    except ValueError:
        print("Invalid input. Age and score must be integers.")


def sort_records_builtin(records):
    """
    Sort records using Python's built-in sort.
    Criteria:
    - Score (descending)
    - Age (ascending)
    - Name (alphabetical)
    """
    return sorted(records, key=lambda r: (-r["score"], r["age"], r["name"].lower()))


def merge_sort(records, criteria):
    """
    Manual merge sort implementation.
    Criteria is a list of tuples: (field, order)
    order = 'asc' or 'desc'
    """
    if len(records) <= 1:
        return records

    mid = len(records) // 2
    left = merge_sort(records[:mid], criteria)
    right = merge_sort(records[mid:], criteria)

    return merge(left, right, criteria)


def merge(left, right, criteria):
    """Helper function for merge sort."""
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if compare_records(left[i], right[j], criteria):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def compare_records(a, b, criteria):
    """
    Compare two records based on multiple criteria.
    Returns True if 'a' should come before 'b'.
    """
    for field, order in criteria:
        if a[field] != b[field]:
            if order == "asc":
                return a[field] < b[field]
            else:  # desc
                return a[field] > b[field]
    return True  # if all fields equal


def display_records(records):
    """Display records clearly."""
    if not records:
        print("No records to display.")
        return
    print("\n--- Sorted Records ---")
    for r in records:
        print(f"Name: {r['name']}, Age: {r['age']}, Score: {r['score']}")


def main():
    records = []

    while True:
        print("\n--- Multi-Criteria Sorting System ---")
        print("1. Add a record")
        print("2. Sort records (built-in)")
        print("3. Sort records (manual merge sort)")
        print("4. Display records")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            add_record(records)

        elif choice == "2":
            if records:
                sorted_records = sort_records_builtin(records)
                display_records(sorted_records)
            else:
                print("No records available.")

        elif choice == "3":
            if records:
                # Default criteria: score desc, age asc, name asc
                criteria = [("score", "desc"), ("age", "asc"), ("name", "asc")]
                sorted_records = merge_sort(records, criteria)
                display_records(sorted_records)
            else:
                print("No records available.")

        elif choice == "4":
            display_records(records)

        elif choice == "5":
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    main()
