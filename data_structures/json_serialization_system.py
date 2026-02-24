"""
JSON Serialization System
-------------------------
This program allows users to create structured student records, serialize them into JSON,
and deserialize them back for display. It supports adding, updating, deleting, and validating records.

Author: Youssef Adardour
Date: February 2026
"""

import json
import os


# -----------------------------
# Data Structures Used:
# - List: stores multiple student records
# - Dictionary: represents each student {"name": str, "age": int, "grades": [int]}
# - Nested structures: dictionary containing a list of grades
# -----------------------------

def add_record(records):
    """Add a new student record with validation."""
    try:
        name = input("Enter student name: ").strip()
        age = int(input("Enter student age: ").strip())
        grades_input = input("Enter grades separated by spaces: ").strip()
        grades = [int(g) for g in grades_input.split()] if grades_input else []

        if not name:
            print("Name cannot be empty.")
            return
        if age < 0:
            print("Age must be non-negative.")
            return

        record = {"name": name, "age": age, "grades": grades}
        records.append(record)
        print("Record added successfully.")
    except ValueError:
        print("Invalid input. Age and grades must be integers.")


def update_record(records):
    """Update an existing student record."""
    if not records:
        print("No records available.")
        return

    name = input("Enter the name of the student to update: ").strip()
    for record in records:
        if record["name"].lower() == name.lower():
            try:
                new_age = int(input("Enter new age: ").strip())
                new_grades_input = input("Enter new grades separated by spaces: ").strip()
                new_grades = [int(g) for g in new_grades_input.split()] if new_grades_input else []

                record["age"] = new_age
                record["grades"] = new_grades
                print("Record updated successfully.")
                return
            except ValueError:
                print("Invalid input. Age and grades must be integers.")
                return
    print("Record not found.")


def delete_record(records):
    """Delete a student record by name."""
    if not records:
        print("No records available.")
        return

    name = input("Enter the name of the student to delete: ").strip()
    for record in records:
        if record["name"].lower() == name.lower():
            records.remove(record)
            print("Record deleted successfully.")
            return
    print("Record not found.")


def save_to_json(records, filename="students.json"):
    """Serialize records into a JSON file with pretty-printing."""
    try:
        with open(filename, "w") as f:
            json.dump(records, f, indent=4)
        print(f"Data saved to {filename}.")
    except Exception as e:
        print(f"Error saving data: {e}")


def load_from_json(filename="students.json"):
    """Deserialize records from a JSON file."""
    if not os.path.exists(filename):
        print("No JSON file found.")
        return []
    try:
        with open(filename, "r") as f:
            records = json.load(f)
        print("Data loaded successfully.")
        return records
    except Exception as e:
        print(f"Error loading data: {e}")
        return []


def display_records(records):
    """Display all student records clearly."""
    if not records:
        print("No records to display.")
        return
    print("\n--- Student Records ---")
    for r in records:
        print(f"Name: {r['name']}, Age: {r['age']}, Grades: {r['grades']}")


def main():
    records = []

    while True:
        print("\n--- JSON Serialization System ---")
        print("1. Add a record")
        print("2. Update a record")
        print("3. Delete a record")
        print("4. Save records to JSON")
        print("5. Load records from JSON")
        print("6. Display records")
        print("7. Exit")

        choice = input("Enter your choice (1-7): ").strip()

        if choice == "1":
            add_record(records)
        elif choice == "2":
            update_record(records)
        elif choice == "3":
            delete_record(records)
        elif choice == "4":
            save_to_json(records)
        elif choice == "5":
            records = load_from_json()
        elif choice == "6":
            display_records(records)
        elif choice == "7":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")


if __name__ == "__main__":
    main()
