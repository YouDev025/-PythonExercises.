# ⚙️ Functions Module

## Overview
This module covers **function design, parameters, return values, generators, decorators, and functional programming**. Perfect for understanding how to organize reusable code and apply advanced function concepts.

---

## 📚 Contents by Category

### **Basic Functions**

| File | Purpose | Concepts |
|------|---------|----------|
| `Simple_Calculator.py` | Basic arithmetic operations | Parameters, return values |
| `find_max.py` | Find maximum from inputs | Comparisons, conditional logic |
| `remove_duplicates.py` | Remove repeated items | List operations, uniqueness |
| `search_tool.py` | Search functionality | Iteration, conditionals |
| `text_analyzer.py` | Analyze text properties | String operations, counters |

### **Mathematical Functions**

| File | Function | Output |
|------|----------|--------|
| `RecursiveFactorial.py` | Factorial (recursive) | n! calculation |
| `PrimeNumberChecker.py` | Check if prime | Boolean result |
| `CurrencyConverter.py` | Convert currencies | Exchange rates |
| `BinaryDecimalConverter.py` | Number base conversion | Hex, binary, decimal |
| `distance_calculato.py` | Calculate distance | Geometric calculations |
| `calculate_volume.py` | Calculate volumes | 3D geometry |
| `calculate_statistics.py` | Statistical analysis | Mean, median, std dev |
| `calculate_speed.py` | Speed calculation | Physics formulas |

### **Data Transformation**

| File | Operation | Input → Output |
|------|-----------|---|
| `custom_map_function.py` | Apply function to all items | List transformation |
| `custom_reduce_function.py` | Aggregate values | Single result |
| `custom_sort.py` | Sort by custom criteria | Ordered collection |
| `filter_function.py` | Filter items by condition | Subset of data |
| `frequency_counter.py` | Count item occurrences | Item frequencies |

### **Generators**

| File | Generator Type | Yields |
|------|---|---|
| `Even_Numbers_Generator.py` | Even number sequence | Infinite sequence |
| `fibonacci_generator.py` | Fibonacci sequence | Fibonacci numbers |
| `CountUpGenerator.py` | Count-up sequence | Numbers from n |
| `RandomDateGenerator.py` | Random dates | Date sequences |

### **String Operations**

| File | Operation | Use Case |
|------|-----------|----------|
| `CharCounter.py` | Count characters | Character frequency |
| `email_validator.py` | Validate email format | Input validation |
| `ip_validator.py` | Validate IP addresses | Network validation |
| `Password_Generator.py` | Generate passwords | Security |

### **File Operations**

| File | Operation | Purpose |
|------|-----------|---------|
| `text_file_analyzer.py` | Analyze text files | File processing |
| `TrafficLightSimulator.py` | Simulate traffic states | State management |

### **Advanced Functions**

| File | Concept | Feature |
|------|---------|---------|
| `pagination_function.py` | Data pagination | Split large datasets |
| `elements_uniques.py` | Find unique elements | Deduplication |
| `SimpleQuizApp.py` | Quiz system | Question handling |
| `ConsoleStopwatch.py` | Timer functionality | Time tracking |

### **Utility Functions**

| File | Purpose | Returns |
|------|---------|---------|
| `average_calculation.py` | Calculate average | Mean value |
| `analyser_notes.py` | Analyze grades | Statistics |
| `date_converter.py` | Convert date formats | Formatted date |
| `calculate_hotel_bill.py` | Calculate bill | Total cost |
| `TVACalculator.py` | Calculate tax | Tax amount |
| `CharCounter.py` | Count characters | Integer count |
| `user_id_generator.py` | Generate IDs | Unique ID string |
| `uuid_generator.py` | Generate UUIDs | Random UUID |

### **Interactive Programs**

| File | Type | Interaction |
|------|------|-------------|
| `email_validator.py` | Validator | User input |
| `gerer_courses.py` | Shopping list | Menu-driven |
| `traiter_ages.py` | Age processor | User input |

---

## 🏗️ Function Fundamentals

### Function Definition
```python
def function_name(parameters):
    """Docstring explaining function"""
    # Implementation
    return result
```

### Parameters & Arguments
```python
# Positional arguments
def greet(name, age):
    return f"{name} is {age} years old"

# Default arguments
def greet(name, age=18):
    return f"{name} is {age} years old"

# Keyword arguments
greet(name="John", age=30)

# *args (variable positional)
def sum_all(*numbers):
    return sum(numbers)

# **kwargs (variable keyword)
def print_info(**data):
    for key, value in data.items():
        print(f"{key}: {value}")
```

### Return Values
```python
# Single return
def add(a, b):
    return a + b

# Multiple return (tuple)
def divide_mod(a, b):
    return a // b, a % b

# No return (None)
def print_msg(msg):
    print(msg)
```

---

## 🎯 Function Types

### 1. Pure Functions
```python
# No side effects, same input → same output
def add(a, b):
    return a + b
```

### 2. Higher-Order Functions
```python
# Functions that take or return functions
def apply_operation(a, b, operation):
    return operation(a, b)

result = apply_operation(5, 3, lambda a, b: a + b)
```

### 3. Generators
```python
# Use yield instead of return
def count_up(n):
    i = 0
    while i < n:
        yield i
        i += 1

for num in count_up(5):
    print(num)  # 0, 1, 2, 3, 4
```

### 4. Recursive Functions
```python
# Function calls itself
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

### 5. Lambda Functions
```python
# Anonymous functions
square = lambda x: x ** 2
squares = list(map(lambda x: x ** 2, [1, 2, 3, 4]))
```

---

## 🔧 Advanced Concepts

### Decorators
```python
def timer(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Took {end-start:.2f}s")
        return result
    return wrapper

@timer
def slow_function():
    # ... implementation
    pass
```

### Closures
```python
def outer(x):
    def inner(y):
        return x + y
    return inner

add5 = outer(5)
print(add5(3))  # 8
```

### First-Class Functions
```python
# Functions as variables
operations = {
    'add': lambda a, b: a + b,
    'sub': lambda a, b: a - b,
}

result = operations['add'](5, 3)  # 8
```

---

## 📊 Function Categories

### Data Processing
| Function | Input | Output | Use Case |
|----------|-------|--------|----------|
| `map()` | Iterable, function | Mapped iterable | Transform all items |
| `filter()` | Iterable, condition | Filtered iterable | Get matching items |
| `reduce()` | Iterable, function | Single value | Aggregate values |
| `sorted()` | Iterable, key | Sorted list | Custom sorting |

### Built-in Functions
```python
len()           # Length
max(), min()    # Extreme values
sum()           # Total
sorted()        # Sorting
enumerate()     # Index + value
zip()           # Combine iterables
range()         # Number sequence
```

---

## 🚀 Quick Start

### Running Examples

**Basic Functions:**
```bash
python functions/Simple_Calculator.py
python functions/find_max.py
python functions/RecursiveFactorial.py
```

**Generators:**
```bash
python functions/fibonacci_generator.py
python functions/Even_Numbers_Generator.py
```

**Data Transform:**
```bash
python functions/custom_map_function.py
python functions/filter_function.py
```

---

## 💡 Function Design Principles

### Single Responsibility
```python
# Good: One function, one purpose
def calculate_total(items):
    return sum(item['price'] for item in items)

# Bad: Too many responsibilities
def process_order(items):
    # Validate items
    # Calculate total
    # Apply discount
    # Generate receipt
    pass
```

### DRY (Don't Repeat Yourself)
```python
# Bad: Code repetition
if age >= 18:
    print("Adult")
if salary >= 50000:
    print("High earner")

# Good: Reusable function
def check_threshold(value, threshold):
    return value >= threshold
```

### Clear Naming
```python
# Bad
def f(x):
    return x * 1.1

# Good
def apply_tax_rate(amount, rate=0.1):
    return amount * (1 + rate)
```

### Meaningful Return Values
```python
# Bad
def find_item(items, target):
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1  # Ambiguous

# Good
def find_item(items, target):
    try:
        return items.index(target)
    except ValueError:
        return None  # Clear
```

---

## 🐛 Common Mistakes

### ❌ Mutable Default Arguments
```python
# Wrong
def add_item(item, list=[]):
    list.append(item)
    return list

# Right
def add_item(item, list=None):
    if list is None:
        list = []
    list.append(item)
    return list
```

### ❌ Modifying Global Variables
```python
# Bad
counter = 0
def increment():
    global counter  # Changes global state
    counter += 1

# Good
def increment(counter):
    return counter + 1
```

### ❌ Not Handling Exceptions
```python
# Bad
def divide(a, b):
    return a / b  # Crashes if b=0

# Good
def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
```

---

## 📈 Complexity Analysis

### Time Complexity
| Operation | Complexity | Example |
|-----------|-----------|---------|
| Lookup | O(1) | Access list[i] |
| Linear search | O(n) | Find in unsorted |
| Sorting | O(n log n) | Merge sort |
| Matrix ops | O(n²) | Nested loops |

### Space Complexity
| Operation | Space | Trade-off |
|-----------|-------|----------|
| Recursion | O(n) | Call stack |
| Memoization | O(n) | Time for memory |
| Generator | O(1) | Memory efficient |

---

## 🎓 Learning Path

### Phase 1: Basics
1. Function definition
2. Parameters and returns
3. Built-in functions

### Phase 2: Intermediate
1. Lambda functions
2. Higher-order functions
3. List comprehensions

### Phase 3: Advanced
1. Generators and yield
2. Decorators
3. Closures

### Phase 4: Mastery
1. Design patterns
2. Function composition
3. Functional programming paradigms

---

## 🎯 Best Practices

✅ Keep functions small and focused  
✅ Use meaningful names  
✅ Add docstrings for documentation  
✅ Use type hints (Python 3.5+)  
✅ Test edge cases  
✅ Avoid side effects where possible  
✅ Use default parameters wisely  

---

## 🔗 Related Modules

- [Basics](../basics/) - Basic function concepts
- [Algorithms](../algorithms/) - Using functions for algorithms
- [OOP](../oop/) - Functions as methods

---

## 📚 Further Reading

- **First-Class Functions**: Functions as values
- **Higher-Order Functions**: Functions that manipulate functions
- **Functional Programming**: Programming paradigm
- **Design Patterns**: Reusable solutions

---

**Master functions for powerful, organized code! ⚙️**
