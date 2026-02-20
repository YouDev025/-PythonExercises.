# ============================================================
# Student Grade Manager
# This program collects student names and grades (/20),
# then displays each student's pass/fail status along with
# a summary analysis (average, highest, lowest, pass count).
# The program loops until the user chooses to exit.
# ============================================================
while True:
    # Get a valid number of students from the user
    try:
        num_students = int(input("Enter number of students: "))
        if num_students <= 0:
            print("Number of students must be positive")
            continue
    except ValueError:
        print("Please enter an integer")
        continue

    # Collect each student's name and grade
    students = []
    for number in range(num_students):
        name = input(f"Enter the name of student number {number + 1}: ")

        # Keep asking until a valid grade is entered
        while True:
            try:
                grade = float(input(f"Enter the grade of {name} (/20): "))
                if grade < 0 or grade > 20:
                    print("Grade must be between 0 and 20")
                    continue
                break
            except ValueError:
                print("Please enter a valid number")

        students.append((name, grade))

    # Initialize stats using the first student as the baseline
    total = 0
    highest_grade = students[0][1]
    lowest_grade = students[0][1]
    passed_count = 0

    # Calculate total, highest, lowest, and pass count
    for name, grade in students:
        total += grade
        if grade > highest_grade:
            highest_grade = grade
        if grade < lowest_grade:
            lowest_grade = grade
        if grade >= 10:
            passed_count += 1

    average_grade = total / num_students

    # Display each student's grade and pass/fail status
    print("----- Student Grades -----")
    for name, grade in students:
        status = "Passed" if grade >= 10 else "Failed"
        print(f"{name} : {grade} -> {status}")

    # Display overall stats
    print("----- Grades Analysis -----")
    print(f"Average grade: {average_grade:.2f}")
    print(f"Highest grade: {highest_grade}")
    print(f"Lowest grade: {lowest_grade}")
    print(f"Number of students passed: {passed_count}")

    # Ask the user if they want to run again
    again = input("Do you want to continue? (y/n): ").strip().lower()
    if again in ["non", "no", "n"]:  # "non" covers French input
        print("Exiting...")
        break