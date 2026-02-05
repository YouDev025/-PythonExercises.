"""
Interactive Student Management System
A complete demonstration of Object-Oriented Programming principles in Python
with interactive menu-driven interface

This program demonstrates:
1. Encapsulation - Private attributes with getters/setters
2. Abstraction - Abstract base class Person
3. Inheritance - Student inherits from Person
4. Polymorphism - Method overriding
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import sys


# ============================================================================
# ABSTRACTION: Abstract Base Class
# ============================================================================

class Person(ABC):
    """
    Abstract base class representing a person.
    This class cannot be instantiated directly - it must be inherited.
    """

    def __init__(self, person_id: int, name: str, age: int):
        """Initialize a Person object with validation."""
        # ENCAPSULATION: Private attributes
        self._person_id = person_id
        self._name = name
        self._age = age

    # ENCAPSULATION: Getter methods (properties)

    @property
    def person_id(self) -> int:
        """Get the person's ID."""
        return self._person_id

    @property
    def name(self) -> str:
        """Get the person's name."""
        return self._name

    @property
    def age(self) -> int:
        """Get the person's age."""
        return self._age

    # ENCAPSULATION: Setter methods with validation

    @name.setter
    def name(self, value: str):
        """Set the person's name with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("Name must be a non-empty string")
        self._name = value

    @age.setter
    def age(self, value: int):
        """Set the person's age with validation."""
        if not isinstance(value, int) or value < 0:
            raise ValueError("Age must be a positive integer")
        self._age = value

    # ABSTRACTION: Abstract method
    @abstractmethod
    def display_info(self):
        """Display information about the person. Must be implemented by subclasses."""
        pass


# ============================================================================
# INHERITANCE: Student class inherits from Person
# ============================================================================

class Student(Person):
    """
    Student class that inherits from Person.
    Represents a student with academic information.
    """

    def __init__(self, student_id: int, name: str, age: int, major: str):
        """Initialize a Student object."""
        super().__init__(student_id, name, age)
        self._major = major
        self._grades: List[float] = []

    @property
    def major(self) -> str:
        """Get the student's major."""
        return self._major

    @major.setter
    def major(self, value: str):
        """Set the student's major with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("Major must be a non-empty string")
        self._major = value

    @property
    def grades(self) -> List[float]:
        """Get a copy of the student's grades."""
        return self._grades.copy()

    def add_grade(self, grade: float):
        """Add a grade to the student's grade list."""
        if not isinstance(grade, (int, float)):
            raise ValueError("Grade must be a number")
        if grade < 0 or grade > 100:
            raise ValueError("Grade must be between 0 and 100")

        self._grades.append(float(grade))
        return True

    def remove_last_grade(self):
        """Remove the last grade added."""
        if self._grades:
            removed = self._grades.pop()
            return removed
        return None

    def calculate_average(self) -> float:
        """Calculate the average of all grades."""
        if not self._grades:
            return 0.0
        return sum(self._grades) / len(self._grades)

    def get_letter_grade(self) -> str:
        """Get letter grade based on average."""
        avg = self.calculate_average()
        if avg >= 90:
            return 'A'
        elif avg >= 80:
            return 'B'
        elif avg >= 70:
            return 'C'
        elif avg >= 60:
            return 'D'
        else:
            return 'F'

    # POLYMORPHISM: Override the abstract method from Person
    def display_info(self):
        """Display complete student information."""
        print("\n" + "=" * 60)
        print(f"{'STUDENT INFORMATION':^60}")
        print("=" * 60)
        print(f"Student ID    : {self._person_id}")
        print(f"Name          : {self._name}")
        print(f"Age           : {self._age}")
        print(f"Major         : {self._major}")
        print(f"Total Grades  : {len(self._grades)}")

        if self._grades:
            print(f"Grades        : {', '.join(map(str, self._grades))}")
            print(f"Average       : {self.calculate_average():.2f}")
            print(f"Letter Grade  : {self.get_letter_grade()}")
        else:
            print("Grades        : No grades recorded yet")
        print("=" * 60)


# ============================================================================
# INHERITANCE & POLYMORPHISM: GraduateStudent class
# ============================================================================

class GraduateStudent(Student):
    """
    GraduateStudent class that inherits from Student.
    Graduate students have weighted averages and research areas.
    """

    def __init__(self, student_id: int, name: str, age: int, major: str,
                 research_area: str):
        """Initialize a GraduateStudent object."""
        super().__init__(student_id, name, age, major)
        self._research_area = research_area
        self._thesis_title = ""

    @property
    def research_area(self) -> str:
        """Get the graduate student's research area."""
        return self._research_area

    @research_area.setter
    def research_area(self, value: str):
        """Set the research area with validation."""
        if not value or not isinstance(value, str):
            raise ValueError("Research area must be a non-empty string")
        self._research_area = value

    @property
    def thesis_title(self) -> str:
        """Get the thesis title."""
        return self._thesis_title

    @thesis_title.setter
    def thesis_title(self, value: str):
        """Set the thesis title."""
        self._thesis_title = value

    # POLYMORPHISM: Override calculate_average() with weighted logic
    def calculate_average(self) -> float:
        """
        Calculate weighted average for graduate student.
        Recent grades are weighted more heavily.
        """
        if not self._grades:
            return 0.0

        total_weight = 0
        weighted_sum = 0

        for index, grade in enumerate(self._grades, start=1):
            weight = index
            weighted_sum += grade * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    # POLYMORPHISM: Override display_info()
    def display_info(self):
        """Display complete graduate student information."""
        print("\n" + "=" * 60)
        print(f"{'GRADUATE STUDENT INFORMATION':^60}")
        print("=" * 60)
        print(f"Student ID    : {self._person_id}")
        print(f"Name          : {self._name}")
        print(f"Age           : {self._age}")
        print(f"Major         : {self._major}")
        print(f"Research Area : {self._research_area}")
        if self._thesis_title:
            print(f"Thesis Title  : {self._thesis_title}")
        print(f"Total Grades  : {len(self._grades)}")

        if self._grades:
            print(f"Grades        : {', '.join(map(str, self._grades))}")
            print(f"Weighted Avg  : {self.calculate_average():.2f}")
            print(f"Letter Grade  : {self.get_letter_grade()}")
            print("(Recent grades weighted more heavily)")
        else:
            print("Grades        : No grades recorded yet")
        print("=" * 60)


# ============================================================================
# Student Management System - Main Controller Class
# ============================================================================

class StudentManagementSystem:
    """Main system to manage students with interactive menu."""

    def __init__(self):
        """Initialize the management system."""
        self.students: Dict[int, Person] = {}
        self.next_id = 1000

    def generate_id(self) -> int:
        """Generate a unique student ID."""
        student_id = self.next_id
        self.next_id += 1
        return student_id

    def add_student(self):
        """Add a new undergraduate student."""
        print("\n" + "=" * 60)
        print("ADD NEW UNDERGRADUATE STUDENT")
        print("=" * 60)

        try:
            name = input("Enter student name: ").strip()
            if not name:
                print("[ERROR] Name cannot be empty!")
                return

            age = int(input("Enter student age: "))
            if age < 16 or age > 100:
                print("[ERROR] Age must be between 16 and 100!")
                return

            major = input("Enter major: ").strip()
            if not major:
                print("[ERROR] Major cannot be empty!")
                return

            student_id = self.generate_id()
            student = Student(student_id, name, age, major)
            self.students[student_id] = student

            print(f"\n[SUCCESS] Student added successfully!")
            print(f"          Student ID: {student_id}")

        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")

    def add_graduate_student(self):
        """Add a new graduate student."""
        print("\n" + "=" * 60)
        print("ADD NEW GRADUATE STUDENT")
        print("=" * 60)

        try:
            name = input("Enter student name: ").strip()
            if not name:
                print("[ERROR] Name cannot be empty!")
                return

            age = int(input("Enter student age: "))
            if age < 21 or age > 100:
                print("[ERROR] Graduate student age must be between 21 and 100!")
                return

            major = input("Enter major: ").strip()
            if not major:
                print("[ERROR] Major cannot be empty!")
                return

            research_area = input("Enter research area: ").strip()
            if not research_area:
                print("[ERROR] Research area cannot be empty!")
                return

            student_id = self.generate_id()
            student = GraduateStudent(student_id, name, age, major, research_area)

            thesis = input("Enter thesis title (optional, press Enter to skip): ").strip()
            if thesis:
                student.thesis_title = thesis

            self.students[student_id] = student

            print(f"\n[SUCCESS] Graduate student added successfully!")
            print(f"          Student ID: {student_id}")

        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")

    def find_student(self, student_id: int) -> Optional[Person]:
        """Find a student by ID."""
        return self.students.get(student_id)

    def display_all_students(self):
        """Display all students in the system."""
        if not self.students:
            print("\n[INFO] No students in the system yet!")
            return

        print("\n" + "=" * 60)
        print(f"{'ALL STUDENTS':^60}")
        print("=" * 60)
        print(f"{'ID':<10} {'Name':<25} {'Type':<15} {'Avg':<10}")
        print("-" * 60)

        for student_id, student in sorted(self.students.items()):
            student_type = "Graduate" if isinstance(student, GraduateStudent) else "Undergraduate"
            avg = student.calculate_average()
            avg_str = f"{avg:.2f}" if avg > 0 else "N/A"
            print(f"{student_id:<10} {student.name:<25} {student_type:<15} {avg_str:<10}")

        print("=" * 60)
        print(f"Total Students: {len(self.students)}")

    def view_student_details(self):
        """View detailed information for a specific student."""
        if not self.students:
            print("\n[INFO] No students in the system yet!")
            return

        try:
            student_id = int(input("\nEnter Student ID: "))
            student = self.find_student(student_id)

            if student:
                student.display_info()
            else:
                print(f"[ERROR] Student with ID {student_id} not found!")

        except ValueError:
            print("[ERROR] Invalid ID! Please enter a number.")

    def add_grade_to_student(self):
        """Add a grade to a student."""
        if not self.students:
            print("\n[INFO] No students in the system yet!")
            return

        try:
            student_id = int(input("\nEnter Student ID: "))
            student = self.find_student(student_id)

            if not student:
                print(f"[ERROR] Student with ID {student_id} not found!")
                return

            grade = float(input("Enter grade (0-100): "))
            student.add_grade(grade)
            print(f"[SUCCESS] Grade {grade} added successfully!")
            print(f"          New Average: {student.calculate_average():.2f}")

        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")

    def remove_student(self):
        """Remove a student from the system."""
        if not self.students:
            print("\n[INFO] No students in the system yet!")
            return

        try:
            student_id = int(input("\nEnter Student ID to remove: "))
            student = self.find_student(student_id)

            if not student:
                print(f"[ERROR] Student with ID {student_id} not found!")
                return

            print(f"\nStudent to remove: {student.name}")
            confirm = input("Are you sure? (yes/no): ").strip().lower()

            if confirm == 'yes':
                del self.students[student_id]
                print(f"[SUCCESS] Student {student_id} removed successfully!")
            else:
                print("[INFO] Removal cancelled.")

        except ValueError:
            print("[ERROR] Invalid ID! Please enter a number.")

    def search_students(self):
        """Search students by name."""
        if not self.students:
            print("\n[INFO] No students in the system yet!")
            return

        search_term = input("\nEnter name to search: ").strip().lower()

        results = [s for s in self.students.values()
                   if search_term in s.name.lower()]

        if results:
            print(f"\n[SUCCESS] Found {len(results)} student(s):")
            for student in results:
                print(f"          ID: {student.person_id} - {student.name} ({student.major})")
        else:
            print(f"[INFO] No students found with name containing '{search_term}'")

    def display_statistics(self):
        """Display system statistics."""
        if not self.students:
            print("\n[INFO] No students in the system yet!")
            return

        undergrads = [s for s in self.students.values()
                      if not isinstance(s, GraduateStudent)]
        grads = [s for s in self.students.values()
                 if isinstance(s, GraduateStudent)]

        students_with_grades = [s for s in self.students.values()
                                if s.grades]

        print("\n" + "=" * 60)
        print(f"{'SYSTEM STATISTICS':^60}")
        print("=" * 60)
        print(f"Total Students        : {len(self.students)}")
        print(f"Undergraduate Students: {len(undergrads)}")
        print(f"Graduate Students     : {len(grads)}")
        print(f"Students with Grades  : {len(students_with_grades)}")

        if students_with_grades:
            all_averages = [s.calculate_average() for s in students_with_grades]
            overall_avg = sum(all_averages) / len(all_averages)
            print(f"Overall Average       : {overall_avg:.2f}")

        print("=" * 60)

    def run(self):
        """Run the interactive menu system."""
        print("\n" + "=" * 60)
        print(f"{'WELCOME TO STUDENT MANAGEMENT SYSTEM':^60}")
        print(f"{'Demonstrating OOP Principles':^60}")
        print("=" * 60)

        while True:
            print("\n" + "-" * 60)
            print("MAIN MENU")
            print("-" * 60)
            print("1.  Add Undergraduate Student")
            print("2.  Add Graduate Student")
            print("3.  View All Students")
            print("4.  View Student Details")
            print("5.  Add Grade to Student")
            print("6.  Search Students by Name")
            print("7.  Remove Student")
            print("8.  Display Statistics")
            print("9.  Exit")
            print("-" * 60)

            choice = input("Enter your choice (1-9): ").strip()

            if choice == '1':
                self.add_student()
            elif choice == '2':
                self.add_graduate_student()
            elif choice == '3':
                self.display_all_students()
            elif choice == '4':
                self.view_student_details()
            elif choice == '5':
                self.add_grade_to_student()
            elif choice == '6':
                self.search_students()
            elif choice == '7':
                self.remove_student()
            elif choice == '8':
                self.display_statistics()
            elif choice == '9':
                print("\n" + "=" * 60)
                print(f"{'THANK YOU FOR USING THE SYSTEM!':^60}")
                print(f"{'Goodbye!':^60}")
                print("=" * 60 + "\n")
                sys.exit(0)
            else:
                print("[ERROR] Invalid choice! Please enter a number between 1 and 9.")

            input("\nPress Enter to continue...")


# ============================================================================
# Program Entry Point
# ============================================================================

if __name__ == "__main__":
    system = StudentManagementSystem()
    system.run()