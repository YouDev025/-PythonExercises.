"""
grade_management_system.py
A command-line grade management system using Python OOP principles.
"""

from __future__ import annotations
import os
import statistics


# ──────────────────────────────────────────────
#  GradeRecord  (immutable value object)
# ──────────────────────────────────────────────

class GradeRecord:
    """Stores a single grade entry: subject + numeric score."""

    VALID_SUBJECTS = (
        "Mathematics", "Science", "English", "History",
        "Geography", "Physics", "Chemistry", "Biology",
        "Computer Science", "Art", "Music", "Physical Education",
    )

    def __init__(self, subject: str, score: float, record_id: int) -> None:
        self.__id      = record_id
        self.subject   = subject    # validated via setter
        self.score     = score      # validated via setter

    # ── properties ────────────────────────────

    @property
    def id(self) -> int:
        return self.__id

    @property
    def subject(self) -> str:
        return self.__subject

    @subject.setter
    def subject(self, value: str) -> None:
        value = value.strip().title()
        if not value:
            raise ValueError("Subject cannot be empty.")
        self.__subject = value

    @property
    def score(self) -> float:
        return self.__score

    @score.setter
    def score(self, value: float) -> None:
        value = float(value)
        if not (0.0 <= value <= 100.0):
            raise ValueError("Score must be between 0 and 100.")
        self.__score = round(value, 2)

    # ── helpers ───────────────────────────────

    @staticmethod
    def letter_grade(score: float) -> str:
        if score >= 90:  return "A"
        if score >= 80:  return "B"
        if score >= 70:  return "C"
        if score >= 60:  return "D"
        return "F"

    @property
    def letter(self) -> str:
        return self.letter_grade(self.__score)

    def __str__(self) -> str:
        return (
            f"  [#{self.__id:>3}]  {self.__subject:<22}  "
            f"{self.__score:>6.2f}/100   {self.letter}"
        )

    def __repr__(self) -> str:
        return f"GradeRecord(id={self.__id}, subject={self.__subject!r}, score={self.__score})"


# ──────────────────────────────────────────────
#  Student
# ──────────────────────────────────────────────

class Student:
    """Represents a student and their grade history."""

    _id_counter: int = 1000   # IDs start at 1000 for realism

    def __init__(self, name: str, student_id: int | None = None) -> None:
        if student_id is not None:
            self.__id = student_id
        else:
            self.__id = Student._id_counter
            Student._id_counter += 1

        self.name          = name
        self.__grades: list[GradeRecord] = []
        self.__next_gid    = 1          # per-student grade record counter

    # ── properties ────────────────────────────

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip().title()
        if not value:
            raise ValueError("Student name cannot be empty.")
        self.__name = value

    # ── grade operations ──────────────────────

    def add_grade(self, subject: str, score: float) -> GradeRecord:
        record = GradeRecord(subject, score, self.__next_gid)
        self.__next_gid += 1
        self.__grades.append(record)
        return record

    def get_grade(self, grade_id: int) -> GradeRecord | None:
        return next((g for g in self.__grades if g.id == grade_id), None)

    def update_grade(
        self,
        grade_id: int,
        subject: str | None = None,
        score: float | None = None,
    ) -> bool:
        record = self.get_grade(grade_id)
        if record is None:
            return False
        if subject is not None:
            record.subject = subject
        if score is not None:
            record.score = score
        return True

    def delete_grade(self, grade_id: int) -> bool:
        for i, g in enumerate(self.__grades):
            if g.id == grade_id:
                self.__grades.pop(i)
                return True
        return False

    def get_grades(self) -> list[GradeRecord]:
        return list(self.__grades)

    # ── statistics ────────────────────────────

    def average(self) -> float | None:
        if not self.__grades:
            return None
        return round(statistics.mean(g.score for g in self.__grades), 2)

    def highest(self) -> GradeRecord | None:
        return max(self.__grades, key=lambda g: g.score, default=None)

    def lowest(self) -> GradeRecord | None:
        return min(self.__grades, key=lambda g: g.score, default=None)

    def grade_count(self) -> int:
        return len(self.__grades)

    # ── helpers ───────────────────────────────

    def summary_line(self) -> str:
        avg = self.average()
        avg_str = f"{avg:.2f}  ({GradeRecord.letter_grade(avg)})" if avg is not None else "N/A"
        return (
            f"  [ID: {self.__id}]  {self.__name:<24}  "
            f"Grades: {self.grade_count():>2}   Avg: {avg_str}"
        )

    def __str__(self) -> str:
        return self.summary_line()

    def __repr__(self) -> str:
        return f"Student(id={self.__id}, name={self.__name!r}, grades={len(self.__grades)})"


# ──────────────────────────────────────────────
#  GradeManager
# ──────────────────────────────────────────────

class GradeManager:
    """Central registry for all students and their grades."""

    def __init__(self) -> None:
        self.__students: dict[int, Student] = {}

    # ── student CRUD ──────────────────────────

    def add_student(self, name: str) -> Student:
        student = Student(name)
        self.__students[student.id] = student
        return student

    def remove_student(self, student_id: int) -> bool:
        if student_id in self.__students:
            del self.__students[student_id]
            return True
        return False

    def get_student(self, student_id: int) -> Student | None:
        return self.__students.get(student_id)

    def search_by_name(self, query: str) -> list[Student]:
        q = query.lower()
        return [s for s in self.__students.values() if q in s.name.lower()]

    def get_all_students(self) -> list[Student]:
        return sorted(self.__students.values(), key=lambda s: s.name)

    def student_count(self) -> int:
        return len(self.__students)

    # ── grade operations (delegate) ───────────

    def record_grade(self, student_id: int, subject: str, score: float) -> str:
        student = self.get_student(student_id)
        if student is None:
            return f"  ✗  Student ID {student_id} not found."
        record = student.add_grade(subject, score)
        return f"  ✓  Grade recorded: {student.name} — {record.subject} {record.score}/100 ({record.letter})"

    def update_grade(
        self,
        student_id: int,
        grade_id: int,
        subject: str | None = None,
        score: float | None = None,
    ) -> str:
        student = self.get_student(student_id)
        if student is None:
            return f"  ✗  Student ID {student_id} not found."
        if student.update_grade(grade_id, subject, score):
            return f"  ✓  Grade #{grade_id} updated successfully."
        return f"  ✗  Grade #{grade_id} not found for {student.name}."

    def delete_grade(self, student_id: int, grade_id: int) -> str:
        student = self.get_student(student_id)
        if student is None:
            return f"  ✗  Student ID {student_id} not found."
        if student.delete_grade(grade_id):
            return f"  ✓  Grade #{grade_id} removed from {student.name}'s record."
        return f"  ✗  Grade #{grade_id} not found for {student.name}."


# ──────────────────────────────────────────────
#  CLI helpers
# ──────────────────────────────────────────────

DIVIDER  = "─" * 70
DIVIDER2 = "═" * 70


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def prompt_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg).strip())
        except ValueError:
            print("  ✗  Please enter a whole number.")


def prompt_float(msg: str) -> float:
    while True:
        try:
            v = float(input(msg).strip())
            if not (0.0 <= v <= 100.0):
                print("  ✗  Score must be between 0 and 100.")
                continue
            return v
        except ValueError:
            print("  ✗  Please enter a numeric score.")


def pick_subject() -> str:
    subjects = GradeRecord.VALID_SUBJECTS
    print("\n  Available subjects:")
    for i, s in enumerate(subjects, 1):
        print(f"    {i:>2}. {s}")
    print(f"    {len(subjects)+1:>2}. Enter custom subject")
    while True:
        choice = prompt_int("\n  Select subject number: ")
        if 1 <= choice <= len(subjects):
            return subjects[choice - 1]
        if choice == len(subjects) + 1:
            custom = input("  Enter subject name: ").strip().title()
            if custom:
                return custom
        print("  ✗  Invalid selection.")


def pick_student(manager: GradeManager, prompt_msg: str = "  Enter student ID: ") -> Student | None:
    student_id = prompt_int(prompt_msg)
    student    = manager.get_student(student_id)
    if student is None:
        print(f"  ✗  No student found with ID {student_id}.")
    return student


# ──────────────────────────────────────────────
#  Seed data
# ──────────────────────────────────────────────

def seed_data(manager: GradeManager) -> None:
    sample = [
        ("Alice Johnson",  [("Mathematics",88),("Science",92),("English",75),("History",81)]),
        ("Bob Martinez",   [("Mathematics",73),("Science",68),("Computer Science",95),("Art",88)]),
        ("Clara Nguyen",   [("English",97),("History",89),("Geography",84),("Music",91)]),
        ("David Okonkwo",  [("Physics",78),("Chemistry",82),("Biology",76)]),
        ("Emma Petrova",   [("Mathematics",65),("English",71),("Physical Education",90)]),
    ]
    for name, grades in sample:
        s = manager.add_student(name)
        for subject, score in grades:
            s.add_grade(subject, score)


# ──────────────────────────────────────────────
#  Menu actions
# ──────────────────────────────────────────────

def menu_add_student(manager: GradeManager) -> None:
    print_header("ADD STUDENT")
    name = input("  Full name: ").strip()
    try:
        student = manager.add_student(name)
        print(f"\n  ✓  Student added: {student.name}  (ID: {student.id})")
    except ValueError as e:
        print(f"\n  ✗  {e}")


def menu_remove_student(manager: GradeManager) -> None:
    print_header("REMOVE STUDENT")
    if manager.student_count() == 0:
        print("  No students on record.")
        return
    menu_display_all(manager)
    print()
    student = pick_student(manager)
    if student is None:
        return
    confirm = input(f"  Remove '{student.name}' and all their grades? (y/n): ").strip().lower()
    if confirm == "y":
        manager.remove_student(student.id)
        print("  ✓  Student removed.")
    else:
        print("  ↩  Cancelled.")


def menu_record_grade(manager: GradeManager) -> None:
    print_header("RECORD GRADE")
    if manager.student_count() == 0:
        print("  No students on record. Please add a student first.")
        return
    menu_display_all(manager)
    print()
    student = pick_student(manager)
    if student is None:
        return
    subject = pick_subject()
    score   = prompt_float(f"\n  Score for {subject} (0–100): ")
    print(f"\n{manager.record_grade(student.id, subject, score)}")


def menu_update_grade(manager: GradeManager) -> None:
    print_header("UPDATE GRADE")
    student = pick_student(manager)
    if student is None:
        return
    if not student.get_grades():
        print(f"  {student.name} has no grades recorded.")
        return
    _print_student_grades(student)
    grade_id = prompt_int("\n  Enter grade # to update: ")
    record   = student.get_grade(grade_id)
    if record is None:
        print(f"  ✗  Grade #{grade_id} not found.")
        return
    print(f"\n  Current: {record}")
    print("  (Press Enter to keep current value)\n")

    raw_subject = input(f"  Subject [{record.subject}]: ").strip()
    raw_score   = input(f"  Score   [{record.score}]: ").strip()

    try:
        result = manager.update_grade(
            student.id,
            grade_id,
            subject = raw_subject or None,
            score   = float(raw_score) if raw_score else None,
        )
        print(f"\n{result}")
    except ValueError as e:
        print(f"\n  ✗  {e}")


def menu_delete_grade(manager: GradeManager) -> None:
    print_header("DELETE GRADE")
    student = pick_student(manager)
    if student is None:
        return
    if not student.get_grades():
        print(f"  {student.name} has no grades recorded.")
        return
    _print_student_grades(student)
    grade_id = prompt_int("\n  Enter grade # to delete: ")
    confirm  = input(f"  Delete grade #{grade_id}? (y/n): ").strip().lower()
    if confirm == "y":
        print(f"\n{manager.delete_grade(student.id, grade_id)}")
    else:
        print("  ↩  Cancelled.")


def _print_student_grades(student: Student) -> None:
    """Shared helper: print one student's grade table + stats."""
    grades = student.get_grades()
    print(f"\n  Student : {student.name}  (ID: {student.id})")
    print(f"  {DIVIDER}")
    print(f"  {'#':>4}   {'Subject':<22}  {'Score':>6}   Letter")
    print(f"  {'─'*4}   {'─'*22}  {'─'*6}   {'─'*6}")
    if grades:
        for g in grades:
            print(g)
    else:
        print("  (no grades recorded)")
    print(f"  {DIVIDER}")

    avg  = student.average()
    high = student.highest()
    low  = student.lowest()

    if avg is not None:
        print(f"  Average : {avg:.2f}  ({GradeRecord.letter_grade(avg)})")
        print(f"  Highest : {high.score:.2f}  ({high.subject})")
        print(f"  Lowest  : {low.score:.2f}  ({low.subject})")
    else:
        print("  Average : N/A")


def menu_view_student(manager: GradeManager) -> None:
    print_header("VIEW STUDENT GRADES")
    student = pick_student(manager)
    if student is None:
        return
    _print_student_grades(student)


def menu_display_all(manager: GradeManager) -> None:
    students = manager.get_all_students()
    print_header(f"ALL STUDENTS  ({manager.student_count()} total)")
    if not students:
        print("  No students on record.")
        return
    print(f"  {'ID':<6}  {'Name':<24}  {'Grades':>6}   {'Average':>10}")
    print(f"  {'─'*6}  {'─'*24}  {'─'*6}   {'─'*10}")
    for s in students:
        avg = s.average()
        avg_str = f"{avg:.2f} ({GradeRecord.letter_grade(avg)})" if avg is not None else "N/A"
        print(f"  {s.id:<6}  {s.name:<24}  {s.grade_count():>6}   {avg_str:>10}")


def menu_class_report(manager: GradeManager) -> None:
    print_header("CLASS PERFORMANCE REPORT")
    students = manager.get_all_students()
    if not students:
        print("  No students on record.")
        return

    graded = [s for s in students if s.average() is not None]
    if not graded:
        print("  No grades have been recorded yet.")
        return

    all_avgs = [(s.name, s.average()) for s in graded]
    all_avgs.sort(key=lambda x: x[1], reverse=True)

    class_mean = round(statistics.mean(a for _, a in all_avgs), 2)

    print(f"\n  {'Rank':<5}  {'Student':<24}  {'Average':>8}   Grade")
    print(f"  {'─'*5}  {'─'*24}  {'─'*8}   {'─'*5}")
    for rank, (name, avg) in enumerate(all_avgs, 1):
        print(f"  {rank:<5}  {name:<24}  {avg:>8.2f}   {GradeRecord.letter_grade(avg)}")

    print(f"\n  {DIVIDER}")
    print(f"  Class average : {class_mean:.2f}  ({GradeRecord.letter_grade(class_mean)})")
    print(f"  Top student   : {all_avgs[0][0]} ({all_avgs[0][1]:.2f})")
    print(f"  Needs support : {all_avgs[-1][0]} ({all_avgs[-1][1]:.2f})")


# ──────────────────────────────────────────────
#  Main loop
# ──────────────────────────────────────────────

MENU = """
  ╔══════════════════════════════════╗
  ║    GRADE MANAGEMENT SYSTEM       ║
  ╠══════════════════════════════════╣
  ║  1.  Add student                 ║
  ║  2.  Remove student              ║
  ║  3.  Record grade                ║
  ║  4.  Update grade                ║
  ║  5.  Delete grade                ║
  ║  6.  View student grades         ║
  ║  7.  Display all students        ║
  ║  8.  Class performance report    ║
  ║  0.  Exit                        ║
  ╚══════════════════════════════════╝
"""

ACTIONS = {
    "1": menu_add_student,
    "2": menu_remove_student,
    "3": menu_record_grade,
    "4": menu_update_grade,
    "5": menu_delete_grade,
    "6": menu_view_student,
    "7": menu_display_all,
    "8": menu_class_report,
}


def main() -> None:
    manager = GradeManager()
    seed_data(manager)

    print(f"\n  Welcome to the Grade Management System!")
    print(f"  {manager.student_count()} sample students pre-loaded.\n")

    while True:
        print(MENU)
        choice = input("  Enter your choice: ").strip()

        if choice == "0":
            print("\n  Goodbye! 👋\n")
            break
        elif choice in ACTIONS:
            ACTIONS[choice](manager)
        else:
            print("\n  ✗  Invalid option. Please try again.")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()