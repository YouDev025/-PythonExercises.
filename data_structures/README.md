# 📦 Data Structures Module

## Overview
This module demonstrates **fundamental and advanced data structures** including lists, dictionaries, stacks, queues, tuples, sets, and specialized structures for real-world applications like shopping carts, inventory systems, and contact management.

---

## 📚 Contents by Data Structure

### **Lists (Linear Data Structures)**

| File | Purpose | Key Operations |
|------|---------|---|
| `List_Traversal.py` | Iterate and process lists | Looping, filtering, transformation |
| `merge_lists.py` | Combine multiple lists | Union, concatenation |
| `remove_duplicates.py` | Eliminate redundant items | Set conversion, uniqueness |
| `max_min_search.py` | Find extreme values | Min/max functions, iteration |
| `gestion_liste_courses.py` | Shopping list manager | Add, remove, organize items |
| `student_list_management.py` | Manage student records | Sorting, searching, filtering |

### **Dictionaries (Key-Value Pairs)**

| File | Purpose | Use Case |
|------|---------|----------|
| `Dictionary_Iteration.py` | Access and traverse dicts | Keys, values, items methods |
| `contact_book.py` | Store contact information | Key: name, Value: details |
| `Gestionnaire_de_Contacts.py` | French contact manager | CRUD operations |
| `word_frequency.py` | Count word occurrences | Frequency analysis, NLP |
| `occurrence_counter.py` | Track element frequencies | Statistics, analysis |
| `vote_management_system.py` | Track voting results | Aggregation, reporting |
| `synonym_dictionary.py` | Thesaurus application | Word relationships |

### **Tuples (Immutable Sequences)**

| File | Purpose | Characteristics |
|------|---------|---|
| `TupleOperations.py` | Tuple manipulation | Packing, unpacking, indexing |
| `Tuple_Iteration.py` | Traverse tuple elements | Read-only iteration |

### **Sets (Unique Collections)**

| File | Purpose | Operations |
|------|---------|----------|
| `SetOperationsGame.py` | Interactive set operations | Union, intersection, difference |
| `Sets_Iteration.py` | Access set elements | Iteration, membership testing |
| `UniqueNumbersCounter.py` | Count unique values | Duplicates removal |

### **Stacks & Queues**

| File | Type | Application |
|------|------|-------------|
| `stack_implementation.py` | Stack (LIFO) | Function calls, expression parsing |
| `queue_management.py` | Queue (FIFO) | Task scheduling, buffering |

### **Specialized Collections**

| File | Type | Purpose |
|------|------|---------|
| `associative_array.py` | Hash Map | Key-based lookup |
| `cache_data_structure.py` | Cache | Fast data retrieval |
| `priority_manager.py` | Priority Queue | Task prioritization |

### **Real-World Applications**

| File | Application | Concepts Used |
|------|-------------|---|
| `ecommerce_cart.py` | Shopping cart | Lists, dicts, totals |
| `ShoppingCartAnalyzer.py` | Cart analysis | Aggregation, statistics |
| `ShoppingCartAnalyze.py` | Advanced analysis | Discounts, promotions |
| `inventory_management.py` | Product inventory | Stock tracking, updates |
| `contact_book.py` | Contact management | Data storage, retrieval |
| `user_history_tracker.py` | Activity tracking | Timeline, sequence |
| `grade_analysis.py` | Academic records | Averaging, ranking |
| `score_ranking_system.py` | Leaderboard | Sorting, positioning |

### **Data Transformation & Analysis**

| File | Task | Output |
|------|------|--------|
| `Concatenation.py` | Combine strings/lists | Merged output |
| `StringManipulation.py` | Text operations | Modified strings |
| `EvenOddSeparator.py` | Partition data | Two groups |
| `matrix_operations.py` | 2D array operations | Matrix math |
| `manual_sort.py` | Custom sorting | Sorted collections |
| `multi_criteria_sorting.py` | Complex sorting | Multiple sort keys |

### **Advanced Systems**

| File | System Type | Features |
|------|---|---|
| `mini_search_engine.py` | Search system | Indexing, querying |
| `data_indexing_system.py` | Index structure | Fast lookups |
| `json_serialization_system.py` | Data persistence | JSON I/O |
| `advanced_statistics_system.py` | Data analysis | Statistics, distributions |
| `anomaly_detection_system.py` | Pattern analysis | Outlier detection |
| `log_analyzer.py` | Log processing | Event analysis |
| `EmployeeRecordSystem.py` | HR database | Employee data |

### **Utility Programs**

| File | Purpose | Complexity |
|------|---------|----------|
| `TableDeMultiplication.py` | Multiplication table | 2D array display |
| `Concatenation.py` | Join sequences | String/list operations |

---

## 🏗️ Data Structure Comparison

| Structure | Ordered | Unique | Mutable | Use Case |
|-----------|---------|--------|---------|----------|
| **List** | ✅ | ❌ | ✅ | General ordered collections |
| **Tuple** | ✅ | ❌ | ❌ | Immutable sequences, dict keys |
| **Set** | ❌ | ✅ | ✅ | Unique items, membership |
| **Dictionary** | ✅* | ✅** | ✅ | Key-value lookups |
| **Stack** | ✅ | ❌ | ✅ | LIFO operations |
| **Queue** | ✅ | ❌ | ✅ | FIFO operations |

*Python 3.7+ maintains insertion order  
**Unique keys

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- No external dependencies

### Running Examples

**Basic Data Structures:**
```bash
python data_structures/List_Traversal.py
python data_structures/Dictionary_Iteration.py
python data_structures/SetOperationsGame.py
```

**Real-World Applications:**
```bash
python data_structures/ecommerce_cart.py
python data_structures/contact_book.py
python data_structures/inventory_management.py
```

**Advanced Systems:**
```bash
python data_structures/mini_search_engine.py
python data_structures/advanced_statistics_system.py
python data_structures/json_serialization_system.py
```

---

## 💡 Core Concepts

### Lists
```python
# Creation
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]

# Operations
numbers.append(6)        # Add item
numbers.remove(3)        # Remove item
numbers[2]              # Access by index
numbers[1:3]            # Slicing
len(numbers)            # Length
```

### Dictionaries
```python
# Creation
person = {"name": "John", "age": 30}
empty = {}

# Operations
person["email"] = "john@example.com"  # Add/Update
person["name"]                         # Access
del person["email"]                    # Delete
person.keys()                          # Get keys
person.values()                        # Get values
```

### Sets
```python
# Creation
numbers = {1, 2, 3}
empty_set = set()

# Operations
numbers.add(4)           # Add item
numbers.remove(2)        # Remove item
{1,2} | {2,3}           # Union
{1,2} & {2,3}           # Intersection
{1,2} - {2,3}           # Difference
```

### Stacks
```python
# LIFO (Last In, First Out)
stack = []
stack.append(1)         # Push
stack.append(2)
value = stack.pop()     # Pop (returns 2)
```

### Queues
```python
# FIFO (First In, First Out)
from collections import deque
queue = deque()
queue.append(1)         # Enqueue
queue.append(2)
value = queue.popleft() # Dequeue (returns 1)
```

---

## 📊 Time Complexity Analysis

| Operation | List | Dict | Set | Tuple |
|-----------|------|------|-----|-------|
| Access | O(1) | O(1)* | - | O(1) |
| Search | O(n) | O(1)* | O(1)* | O(n) |
| Insert | O(n) | O(1)* | O(1)* | - |
| Delete | O(n) | O(1)* | O(1)* | - |

*Average case

---

## 🎯 Learning Path

### Level 1: Basics
1. Lists and basic operations
2. Tuples and immutability
3. Dictionaries for key-value pairs
4. Sets for uniqueness

### Level 2: Intermediate
1. List comprehensions
2. Dictionary methods and iteration
3. Stack and queue concepts
4. Nested data structures

### Level 3: Advanced
1. Custom data structures
2. Data serialization (JSON)
3. Optimization techniques
4. Real-world system design

---

## 🛠️ Real-World Examples

### Shopping Cart System
```python
cart = {
    "item1": {"name": "Laptop", "price": 999, "qty": 1},
    "item2": {"name": "Mouse", "price": 25, "qty": 2}
}

total = sum(item["price"] * item["qty"] for item in cart.values())
```

### Contact Book
```python
contacts = {
    "John": {"email": "john@example.com", "phone": "123-456-7890"},
    "Jane": {"email": "jane@example.com", "phone": "098-765-4321"}
}

# Search
contact = contacts.get("John")
```

### Grade Tracking
```python
grades = {
    "Math": [95, 87, 92],
    "Science": [88, 91, 89],
    "English": [92, 88, 95]
}

averages = {subject: sum(scores)/len(scores) 
            for subject, scores in grades.items()}
```

---

## 🐛 Common Mistakes

### ❌ Using mutable default arguments
```python
# Wrong
def add_item(item, cart=[]):
    cart.append(item)
    return cart

# Correct
def add_item(item, cart=None):
    if cart is None:
        cart = []
    cart.append(item)
    return cart
```

### ❌ Modifying list while iterating
```python
# Wrong
for item in items:
    if item > 5:
        items.remove(item)  # Causes skips!

# Correct
items = [item for item in items if item <= 5]
```

### ❌ Forgetting dictionaries are mutable
```python
# Problem: shallow copy
original = {"data": [1, 2, 3]}
copy_dict = original.copy()
copy_dict["data"].append(4)
print(original)  # Also modified!

# Solution: deep copy
import copy
deep_copy = copy.deepcopy(original)
```

---

## 📚 Specialized Structures

### Stack (LIFO)
**Use**: Function calls, expression parsing, undo functionality

### Queue (FIFO)
**Use**: Task scheduling, breadth-first search, buffering

### Priority Queue
**Use**: Task prioritization, event scheduling, Dijkstra's algorithm

### Hash Table (Dictionary)
**Use**: Fast lookups, caching, counting frequencies

---

## 🎓 Practice Projects

1. **Contact Management App**: Full CRUD operations
2. **Inventory System**: Stock tracking and updates
3. **Student Grading System**: Multiple data structures
4. **Shopping Cart**: Real-world ecommerce scenario
5. **Cache Implementation**: Performance optimization

---

## 🔗 Related Modules

- [Algorithms](../algorithms/) - Searching and sorting data
- [Functions](../functions/) - Organize data operations
- [OOP](../oop/) - Design custom data structures

---

## 💪 Advanced Topics

- **Memory optimization**: Reduce space usage
- **Custom comparators**: Sort by multiple criteria
- **Data serialization**: JSON, pickle, CSV
- **Indexing**: Fast lookups in large datasets
- **Caching strategies**: Improve performance
- **Data validation**: Ensure data integrity

---

## 🎯 Performance Tips

✅ Use appropriate data structure for your use case  
✅ Prefer dictionaries for frequent lookups  
✅ Use sets for membership testing  
✅ Avoid nested loops where possible  
✅ Cache computed results  
✅ Consider space-time tradeoffs  

---

**Master data structures for optimal programming! 📦**
