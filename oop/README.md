# 🏛️ Object-Oriented Programming (OOP) Module

## Overview
This module demonstrates **object-oriented programming principles** including classes, objects, inheritance, polymorphism, encapsulation, and design patterns. Essential for building scalable, maintainable software systems.

---

## 📚 Contents by Concept

### **Core OOP Implementation**

| File | Concept | Focus |
|------|---------|-------|
| `atm_simulation.py` | Object state | Banking operations, transactions |
| `bank_account_system.py` | Class design | Account management, CRUD |
| `card_game.py` | Game logic | Deck, shuffle, deal mechanics |
| `VehicleInheritanceSystem.py` | Inheritance | Parent-child relationships |

### **Business Systems (CRUD Applications)**

| File | Type | Features |
|------|------|----------|
| `student_management_system.py` | Education | Enrollment, grades, records |
| `employee_management_system.py` | HR | Hiring, payroll, performance |
| `library_management_system.py` | Services | Books, borrowing, returns |
| `hotel_management_system.py` | Hospitality | Rooms, reservations, billing |
| `inventory_management_system.py` | Supply Chain | Stock, tracking, reordering |
| `event_management_system.py` | Planning | Events, registrations, tickets |
| `OrderManagementSystem.py` | Ecommerce | Orders, items, fulfillment |

### **Enterprise Systems**

| File | System | Complexity |
|------|--------|-----------|
| `mini_erp_system.py` | ERP | Complete business functions |
| `mini_search_engine.py` | Search | Indexing, querying |
| `project_management_system.py` | Project Mgmt | Tasks, timelines, resources |

### **Access Control & Security**

| File | Type | Purpose |
|------|------|---------|
| `permission_management_system.py` | RBAC | Role-based access control |
| `role_management_system.py` | Access | User roles and permissions |
| `object_authentication_system.py` | Auth | User validation, tokens |
| `user_management_system.py` | Users | Registration, profiles, settings |

### **Financial Systems**

| File | Application | Operations |
|------|-------------|-----------|
| `shopping_cart.py` | Ecommerce | Add items, checkout |
| `transaction_history_manager.py` | Banking | Transaction logs, reports |
| `subscription_management_system.py` | SaaS | Plans, billing, cancelation |

### **Specialized Systems**

| File | Domain | Classes |
|------|--------|---------|
| `parking_management_system.py` | Parking | Spots, vehicles, fees |
| `schedule_management_system.py` | Calendar | Events, reminders, conflicts |
| `reservation_system.py` | Booking | Reservations, confirmations |
| `product_catalog.py` | Catalog | Categories, products, pricing |
| `messaging_system.py` | Communication | Messages, threads, users |
| `notification_system.py` | Alerts | Notifications, subscriptions |
| `grade_management_system.py` | Education | Grades, transcripts, GPA |
| `combat_game.py` | Gaming | Characters, combat, HP |
| `unit_conversion_assistant.py` | Utility | Conversions, formulas |
| `console_mini_framework.py` | Framework | Base utilities, helpers |

---

## 🏗️ OOP Principles

### 1. Encapsulation
```python
class BankAccount:
    def __init__(self, balance):
        self.__balance = balance  # Private attribute
    
    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
    
    def get_balance(self):
        return self.__balance
```

### 2. Inheritance
```python
class Vehicle:
    def __init__(self, brand):
        self.brand = brand

class Car(Vehicle):
    def __init__(self, brand, doors):
        super().__init__(brand)
        self.doors = doors
```

### 3. Polymorphism
```python
class Animal:
    def make_sound(self):
        pass

class Dog(Animal):
    def make_sound(self):
        return "Woof"

class Cat(Animal):
    def make_sound(self):
        return "Meow"

# Same method, different behavior
for animal in [Dog(), Cat()]:
    print(animal.make_sound())
```

### 4. Abstraction
```python
from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def query(self):
        pass
```

---

## 🏢 System Architecture Patterns

### Model-View-Controller (MVC)
```
┌─────────────┐
│    View     │  (User Interface)
└──────┬──────┘
       │
┌──────▼──────┐
│ Controller  │  (Logic)
└──────┬──────┘
       │
┌──────▼──────┐
│    Model    │  (Data)
└─────────────┘
```

### Layered Architecture
```
┌───────────────────┐
│ Presentation Layer │  (UI, input/output)
├───────────────────┤
│  Business Layer   │  (Logic, rules)
├───────────────────┤
│  Persistence Layer │  (Data storage)
├───────────────────┤
│  Database Layer   │  (CRUD operations)
└───────────────────┘
```

---

## 💼 Real-World Systems

### Bank Account System
```python
class BankAccount:
    def __init__(self, account_number, balance):
        self.account_number = account_number
        self.__balance = balance
    
    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            return True
        return False
    
    def withdraw(self, amount):
        if 0 < amount <= self.__balance:
            self.__balance -= amount
            return True
        return False
    
    def get_balance(self):
        return self.__balance
```

### Student Management
```python
class Student:
    def __init__(self, name, student_id):
        self.name = name
        self.student_id = student_id
        self.grades = {}
    
    def add_grade(self, subject, grade):
        self.grades[subject] = grade
    
    def get_average(self):
        if not self.grades:
            return 0
        return sum(self.grades.values()) / len(self.grades)
    
    def get_gpa(self):
        # Calculate GPA based on grades
        pass
```

### Employee System
```python
class Employee:
    def __init__(self, name, employee_id, department):
        self.name = name
        self.employee_id = employee_id
        self.department = department
        self.salary = 0
    
    def set_salary(self, salary):
        if salary > 0:
            self.salary = salary
    
    def calculate_bonus(self):
        return self.salary * 0.1  # 10% bonus
    
    def promote(self, new_department, salary_increase):
        self.department = new_department
        self.salary += salary_increase
```

---

## 📋 Design Patterns

### Singleton Pattern
```python
class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Factory Pattern
```python
class VehicleFactory:
    @staticmethod
    def create_vehicle(vehicle_type):
        if vehicle_type == "car":
            return Car()
        elif vehicle_type == "bike":
            return Bike()
```

### Observer Pattern
```python
class Subject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def notify(self):
        for observer in self._observers:
            observer.update()
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- No external dependencies

### Running Examples

**Basic OOP:**
```bash
python oop/bank_account_system.py
python oop/employee_management_system.py
python oop/VehicleInheritanceSystem.py
```

**Complex Systems:**
```bash
python oop/student_management_system.py
python oop/library_management_system.py
python oop/mini_erp_system.py
```

**Games:**
```bash
python oop/card_game.py
python oop/combat_game.py
python oop/atm_simulation.py
```

---

## 📊 Class Design Template

```python
class MyClass:
    # Class variables (shared by all instances)
    class_var = 0
    
    def __init__(self, param1, param2):
        """Initialize instance"""
        self.param1 = param1
        self.param2 = param2
    
    def public_method(self):
        """Public method - accessible everywhere"""
        pass
    
    def _protected_method(self):
        """Protected method - for subclasses"""
        pass
    
    def __private_method(self):
        """Private method - only this class"""
        pass
    
    @property
    def calculated_value(self):
        """Property - accessed like attribute"""
        return self.param1 + self.param2
    
    @staticmethod
    def static_method():
        """Static method - no self parameter"""
        pass
    
    @classmethod
    def class_method(cls):
        """Class method - access class variables"""
        pass
```

---

## 💡 Core Concepts

### Classes and Objects
```python
class Dog:
    species = "Canis familiaris"  # Class variable
    
    def __init__(self, name, age):
        self.name = name           # Instance variables
        self.age = age
    
    def bark(self):
        return f"{self.name} says Woof!"

# Create object
my_dog = Dog("Buddy", 3)
print(my_dog.bark())
```

### Methods
```python
# Instance methods (most common)
def method(self, arg):
    pass

# Class methods (access class variables)
@classmethod
def class_method(cls):
    pass

# Static methods (no access to instance/class)
@staticmethod
def static_method():
    pass
```

### Special Methods
```python
def __init__(self):      # Constructor
def __str__(self):       # String representation
def __repr__(self):      # Official representation
def __len__(self):       # Length
def __getitem__(self):   # Indexing
def __setitem__(self):   # Assignment
def __eq__(self):        # Equality
```

---

## 🎓 Learning Path

### Phase 1: Fundamentals
1. Classes and objects
2. Attributes and methods
3. Instance vs class variables
4. Special methods (__init__, __str__)

### Phase 2: Inheritance
1. Parent and child classes
2. Method overriding
3. Super() function
4. Multiple inheritance

### Phase 3: Advanced
1. Polymorphism
2. Abstract classes
3. Mixins
4. Properties and decorators

### Phase 4: Design
1. Design patterns
2. SOLID principles
3. System architecture
4. Enterprise patterns

---

## 🎯 SOLID Principles

### Single Responsibility
Each class has one reason to change

### Open/Closed
Open for extension, closed for modification

### Liskov Substitution
Derived classes can replace base classes

### Interface Segregation
Many specific interfaces over general ones

### Dependency Inversion
Depend on abstractions, not concrete implementations

---

## 🐛 Common Mistakes

### ❌ Modifying class variables
```python
# Wrong
class Counter:
    count = 0
    def __init__(self):
        Counter.count += 1

# Right
class Counter:
    _instance_count = 0
    def __init__(self):
        self.__class__._instance_count += 1
```

### ❌ Forgetting self parameter
```python
# Wrong
def method():
    pass

# Right
def method(self):
    pass
```

### ❌ Mutable default arguments
```python
# Wrong
def __init__(self, items=[]):
    self.items = items

# Right
def __init__(self, items=None):
    self.items = items if items else []
```

---

## 🔗 Related Modules

- [Basics](../basics/) - Variables and control flow
- [Functions](../functions/) - Function organization
- [Data Structures](../data_structures/) - Store data efficiently
- [Algorithms](../algorithms/) - Implement efficient systems

---

## 📚 Recommended Projects

1. **Bank Management System** - Core OOP concepts
2. **Library System** - Inheritance and polymorphism
3. **Game** - Complex interactions
4. **E-commerce Platform** - Enterprise patterns
5. **Social Network** - Advanced design

---

## 💪 Advanced Topics

- **Metaclasses**: Classes that create classes
- **Descriptors**: Control attribute access
- **Context Managers**: Resource management
- **Async/Await**: Asynchronous OOP
- **Design Patterns**: Reusable solutions
- **Testing**: Unit testing OOP code

---

**Master OOP for professional software development! 🏛️**
