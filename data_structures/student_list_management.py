# student_list_management.py
# A simple program to manage a list of students
# Features: Add, Delete, Display, Search, Modify, Clear list, and Restart

# -----------------------------
# Functions
# -----------------------------

def add_student(students):
    # Add one or more students
    while True:
        name = input("Enter student name to add: ")
        students.append(name)
        print(f"Student '{name}' added successfully.")

        # Ask if user wants to add another
        resp = input("Do you want to add another student? (yes/no): ")
        if resp.lower() not in ['yes', 'y']:
            break  # Exit loop if answer is no

def delete_student(students, name):
    # Delete a student if they exist
    if name in students:
        students.remove(name)
        print(f"Student '{name}' deleted successfully.")
    else:
        print(f"Student '{name}' not found in the list.")

def display_students(students):
    # Show all students in the list
    if students:
        print("\nList of Students:")
        for i, student in enumerate(students, start=1):
            print(f"{i}. {student}")
    else:
        print("No students in the list yet.")

def search_student(students, name):
    # Search for a student by name
    if name in students:
        print(f"Student '{name}' found in the list.")
    else:
        print(f"Student '{name}' not found.")

def modify_student(students, old_name, new_name):
    # Change a student's name if they exist
    if old_name in students:
        index = students.index(old_name)
        students[index] = new_name
        print(f"Student '{old_name}' changed to '{new_name}'.")
    else:
        print(f"Student '{old_name}' not found in the list.")

def clear_students(students):
    # Clear all students, only if list is not empty
    if students:
        students.clear()
        print("All students have been removed from the list.")
    else:
        print("The student list is already empty.")

# -----------------------------
# Main Program
# -----------------------------

def main():
    students = []  # Empty list to store student names

    while True:
        # Display menu
        print("\n===== Student List Management =====")
        print("1. Add Student")
        print("2. Delete Student")
        print("3. Display All Students")
        print("4. Search Student")
        print("5. Modify Student")
        print("6. Clear Student List")
        print("7. Exit")

        choice = input("Enter your choice (1-7): ")

        if choice == "1":
            # Add student(s)
            add_student(students)

        elif choice == "2":
            # Delete student
            name = input("Enter student name to delete: ")
            delete_student(students, name)

        elif choice == "3":
            # Display all students
            display_students(students)

        elif choice == "4":
            # Search student
            name = input("Enter student name to search: ")
            search_student(students, name)

        elif choice == "5":
            # Modify student
            old_name = input("Enter the current student name: ")
            new_name = input("Enter the new student name: ")
            modify_student(students, old_name, new_name)

        elif choice == "6":
            # Clear student list
            confirm = input("Are you sure you want to clear the list? (yes/no): ")
            if confirm.lower() in ['yes', 'y']:
                clear_students(students)
            else:
                print("Clear operation cancelled.")

        elif choice == "7":
            # Exit program
            print("Exiting program. Goodbye!")
            restart = input("Do you want to restart the program? (yes/no): ")
            if restart.lower() in ['yes', 'y']:
                main()  # Restart program
            break

        else:
            # Invalid choice
            print("Invalid choice. Please enter a number between 1 and 7.")

# Run the program
if __name__ == "__main__":
    main()
