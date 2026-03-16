# 🔢 Algorithms Module

## Overview
This module contains implementations of fundamental and advanced algorithms covering **sorting**, **searching**, **graph traversal**, **dynamic programming**, and **mathematical algorithms**.

---

## 📚 Contents

### **Sorting Algorithms**
| File | Algorithm | Complexity | Use Case |
|------|-----------|-----------|----------|
| `bubble_sort.py` | Bubble Sort | O(n²) | Educational, nearly sorted data |
| `interactive_bubble_sort.py` | Bubble Sort (Interactive) | O(n²) | Learning with step-by-step execution |
| `insertion_sort.py` | Insertion Sort | O(n²) | Small datasets, partially sorted data |
| `interactive_insertion_sort.py` | Insertion Sort (Interactive) | O(n²) | Learning mode |
| `selection_sort.py` | Selection Sort | O(n²) | Memory-constrained environments |
| `interactive_selection_sort.py` | Selection Sort (Interactive) | O(n²) | Learning mode |
| `quick_sort.py` | Quick Sort | O(n log n) | General-purpose, in-place sorting |
| `interactive_quick_sort.py` | Quick Sort (Interactive) | O(n log n) | Learning with visualizations |
| `merge_sort.py` | Merge Sort | O(n log n) | Stable sorting, linked lists |

### **Searching Algorithms**
| File | Algorithm | Complexity | Description |
|------|-----------|-----------|-------------|
| `binary_search.py` | Binary Search | O(log n) | Efficient search on sorted arrays |
| `interactive_binary_search.py` | Binary Search (Interactive) | O(log n) | Step-by-step learning |
| `linear_search.py` | Linear Search | O(n) | Unsorted data searching |
| `interactive_linear_search.py` | Linear Search (Interactive) | O(n) | Educational implementation |

### **Graph Algorithms**
| File | Algorithm | Description |
|------|-----------|-------------|
| `interactive_bfs_graph.py` | BFS (Breadth-First Search) | Level-order tree/graph traversal |
| `interactive_dfs_graph.py` | DFS (Depth-First Search) | Depth-order tree/graph traversal |
| `interactive_dijkstra_shortest_path.py` | Dijkstra's Algorithm | Shortest path in weighted graphs |
| `interactive_cycle_detection_undirected.py` | Cycle Detection | Detect cycles in undirected graphs |

### **String & Pattern Algorithms**
| File | Algorithm | Purpose |
|------|-----------|---------|
| `interactive_pattern_matching.py` | Pattern Matching | Find patterns in strings |
| `interactive_substring_search.py` | Substring Search | Locate substrings efficiently |
| `interactive_palindrome_checker.py` | Palindrome Detection | Check if string reads same forward/backward |
| `interactive_anagram_checker.py` | Anagram Detection | Check if strings are anagrams |
| `interactive_run_length_encoding.py` | Run-Length Encoding | Compress consecutive characters |
| `interactive_simple_compression.py` | Simple Compression | Basic data compression |
| `interactive_string_comparison.py` | String Comparison | Compare and analyze strings |

### **Mathematical Algorithms**
| File | Algorithm | Use Case |
|------|-----------|----------|
| `interactive_recursive_fibonacci.py` | Fibonacci (Recursive) | Demonstrates recursion, exponential complexity |
| `interactive_iterative_fibonacci.py` | Fibonacci (Iterative) | Efficient Fibonacci computation |
| `interactive_gcd_calculator.py` | GCD (Euclidean Algorithm) | Find greatest common divisor |
| `interactive_lcm_calculator.py` | LCM Calculator | Find least common multiple |

### **Advanced Algorithms**
| File | Algorithm | Purpose |
|------|-----------|---------|
| `interactive_advanced_recursion.py` | Advanced Recursion | Complex recursive problem-solving |
| `interactive_complexity_analyzer.py` | Complexity Analysis | Analyze time/space complexity |
| `interactive_memory_optimization.py` | Memory Optimization | Techniques to reduce space usage |
| `interactive_maximum_subarray.py` | Maximum Subarray (Kadane's) | Find contiguous subarray with max sum |
| `interactive_greedy_algorithm.py` | Greedy Algorithm | Greedy problem-solving approach |
| `simple_backtracking.py` | Backtracking | Solve problems using backtracking |

### **Array & List Problems**
| File | Problem | Difficulty |
|------|---------|-----------|
| `Array_Frequency_Counter.py` | Count element frequencies | Easy |
| `Inversion_Count.py` | Count inversions in array | Medium |
| `Missing_Number.py` | Find missing number in sequence | Easy |
| `Longest_Word_Finder.py` | Find longest word in list | Easy |
| `Palindrome_Checker.py` | Advanced palindrome checking | Medium |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Optional: `numpy` for advanced analysis

### Running Examples

**Basic Sorting:**
```bash
python algorithms/bubble_sort.py
python algorithms/merge_sort.py
```

**Interactive Learning:**
```bash
python algorithms/interactive_bubble_sort.py
python algorithms/interactive_dijkstra_shortest_path.py
```

**Searching:**
```bash
python algorithms/binary_search.py
python algorithms/linear_search.py
```

---

## 📊 Complexity Cheat Sheet

### Sorting
| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |

### Searching
| Algorithm | Best | Average | Worst | Use Case |
|-----------|------|---------|-------|----------|
| Linear Search | O(1) | O(n) | O(n) | Any array |
| Binary Search | O(1) | O(log n) | O(log n) | Sorted array |

---

## 💡 Learning Path

### Level 1: Foundations
1. Array Frequency Counter
2. Binary Search
3. Linear Search
4. Basic Sorting (Bubble, Insertion, Selection)

### Level 2: Intermediate
1. Efficient Sorting (Quick Sort, Merge Sort)
2. Graph Basics (BFS, DFS)
3. String Algorithms (Pattern Matching, Palindrome)
4. Recursion & Fibonacci

### Level 3: Advanced
1. Dijkstra's Shortest Path
2. Cycle Detection
3. Advanced Recursion
4. Complexity Analysis
5. Greedy & Dynamic Programming

---

## 📖 Key Concepts

- **Time Complexity**: How algorithm performance scales with input size
- **Space Complexity**: Memory required by the algorithm
- **Big O Notation**: Standard way to describe algorithm efficiency
- **Algorithm Paradigms**: Divide & Conquer, Greedy, Dynamic Programming, Backtracking

---

## 🎯 Best Practices

✅ Understand the problem before coding  
✅ Analyze time and space complexity  
✅ Test with edge cases  
✅ Choose the right algorithm for your use case  
✅ Consider memory constraints  

---

## 📝 Notes

- Interactive versions include step-by-step execution for learning
- All algorithms are implemented from scratch (no library shortcuts)
- Comments explain key logic and complexity considerations
- Test cases provided where applicable

---

## 🔗 Related Topics

- [Data Structures](../data_structures/)
- [Functions](../functions/)
- [Challenges](../challenges/)

