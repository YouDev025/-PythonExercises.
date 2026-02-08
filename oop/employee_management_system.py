class Employee:
    """Base class for all employees in the system"""

    def __init__(self, emp_id, name, salary):
        self.emp_id = emp_id
        self.name = name
        # FIX: Use the setter to ensure salary validation happens during initialization
        self._salary = 0
        self.set_salary(salary)

    def get_salary(self):
        return self._salary

    def set_salary(self, new_salary):
        if new_salary >= 0:
            self._salary = new_salary
        else:
            print(f"[ERROR] Salary {new_salary} cannot be negative. Defaulting to 0.")
            self._salary = 0

    def calculate_bonus(self):
        return self._salary * 0.05

    def __str__(self):
        return f"ID: {self.emp_id} | Name: {self.name} | Salary: ${self._salary:,.2f} | Role: {self.__class__.__name__}"


class Manager(Employee):
    def __init__(self, emp_id, name, salary, department):
        super().__init__(emp_id, name, salary)
        self.department = department

    def calculate_bonus(self):
        return self._salary * 0.20

    def __str__(self):
        return super().__str__() + f" | Dept: {self.department}"


class Developer(Employee):
    def __init__(self, emp_id, name, salary, language):
        super().__init__(emp_id, name, salary)
        self.language = language

    def calculate_bonus(self):
        return (self._salary * 0.10) + 500

    def __str__(self):
        return super().__str__() + f" | Tech: {self.language}"


class ManagementSystem:
    def __init__(self):
        self.employees = {}

    def add_employee(self, employee):
        if employee.emp_id in self.employees:
            print(f"Error: Employee ID {employee.emp_id} already exists.")
        else:
            self.employees[employee.emp_id] = employee
            print(f"Employee '{employee.name}' added successfully.")

    def remove_employee(self, emp_id):
        if emp_id in self.employees:
            removed = self.employees.pop(emp_id)
            print(f"Employee '{removed.name}' removed successfully.")
        else:
            print("Error: Employee ID not found.")

    def display_all(self):
        print("\n" + "=" * 50)
        print(f"{'EMPLOYEE LIST':^50}")
        print("=" * 50)
        if not self.employees:
            print("No employees in the system.")
        else:
            for emp in self.employees.values():
                print(emp)
                print(f"Calculated Bonus: ${emp.calculate_bonus():,.2f}")
                print("-" * 50)

    def find_employee(self, emp_id):
        # Improved find method to return the object or None
        return self.employees.get(emp_id, None)


def main():
    system = ManagementSystem()

    # Pre-populate
    system.add_employee(Manager(101, "Alice Johnson", 90000, "Operations"))
    system.add_employee(Developer(102, "Bob Smith", 80000, "Python/Django"))

    while True:
        print("\n--- Employee Management System ---")
        print("1. Add Manager")
        print("2. Add Developer")
        print("3. List All Employees")
        print("4. Find Employee")  # Added this option
        print("5. Remove Employee")
        print("6. Exit")

        choice = input("Select an option: ")

        if choice in ["1", "2"]:
            try:
                eid = int(input("Enter Employee ID: "))
                name = input("Enter Employee Name: ")
                salary = float(input("Enter Employee Salary: "))

                if choice == "1":
                    dept = input("Enter Department: ")
                    system.add_employee(Manager(eid, name, salary, dept))
                else:
                    lang = input("Enter Primary Language: ")
                    system.add_employee(Developer(eid, name, salary, lang))
            except ValueError:
                print("Error: Invalid input. ID must be an integer and salary a number.")

        elif choice == '3':
            system.display_all()

        elif choice == '4':  # New implementation of search
            try:
                eid = int(input("Enter Employee ID to search: "))
                emp = system.find_employee(eid)
                if emp:
                    print(f"\nMatch Found:\n{emp}")
                else:
                    print("Employee not found.")
            except ValueError:
                print("Error: Invalid ID format.")

        elif choice == '5':
            try:
                eid = int(input("Enter Employee ID to remove: "))
                system.remove_employee(eid)
            except ValueError:
                print("Error: Invalid Employee ID.")

        elif choice == '6':
            print("Exiting system. Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()