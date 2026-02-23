"""
Simple Graph Implementation
---------------------------
This program demonstrates a graph using an adjacency list representation.
It allows users to add nodes, add edges (directed/undirected), display the graph,
and perform Depth-First Search (DFS) and Breadth-First Search (BFS).

Author: Youssef Adardour
Date: February 2026
"""

from collections import deque  # Queue for BFS

# Graph implemented using a dictionary (adjacency list)
graph = {}  # Keys = nodes, Values = list of adjacent nodes


# Function to add a node
def add_node(node):
    if node not in graph:
        graph[node] = []  # Each node maps to a list of neighbors
        print(f"Node '{node}' added.")
    else:
        print(f"Node '{node}' already exists.")


# Function to add an edge
def add_edge(node1, node2, directed=False):
    if node1 not in graph or node2 not in graph:
        print("Error: One or both nodes do not exist.")
        return

    graph[node1].append(node2)  # Add edge node1 → node2
    if not directed:
        graph[node2].append(node1)  # Add edge node2 → node1 if undirected
    print(f"Edge added between '{node1}' and '{node2}' (Directed={directed}).")


# Function to display the graph
def display_graph():
    print("\n--- Graph (Adjacency List) ---")
    for node, neighbors in graph.items():
        print(f"{node}: {neighbors}")


# Depth-First Search (DFS) using recursion
def dfs(start, visited=None):
    if visited is None:
        visited = set()  # Set to track visited nodes

    if start not in graph:
        print(f"Error: Node '{start}' does not exist.")
        return

    visited.add(start)
    print(start, end=" ")  # Process node

    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(neighbor, visited)


# Breadth-First Search (BFS) using a queue
def bfs(start):
    if start not in graph:
        print(f"Error: Node '{start}' does not exist.")
        return

    visited = set()  # Set to track visited nodes
    queue = deque([start])  # Queue for BFS

    while queue:
        node = queue.popleft()
        if node not in visited:
            print(node, end=" ")  # Process node
            visited.add(node)
            # Add unvisited neighbors to queue
            for neighbor in graph[node]:
                if neighbor not in visited:
                    queue.append(neighbor)


# Main menu
def main():
    while True:
        print("\n--- Graph Menu ---")
        print("1. Add Node")
        print("2. Add Edge")
        print("3. Display Graph")
        print("4. DFS Traversal")
        print("5. BFS Traversal")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            node = input("Enter node name: ")
            add_node(node)
        elif choice == "2":
            node1 = input("Enter first node: ")
            node2 = input("Enter second node: ")
            directed = input("Directed edge? (y/n): ").lower() == "y"
            add_edge(node1, node2, directed)
        elif choice == "3":
            display_graph()
        elif choice == "4":
            start = input("Enter start node for DFS: ")
            print("DFS Traversal:", end=" ")
            dfs(start)
            print()
        elif choice == "5":
            start = input("Enter start node for BFS: ")
            print("BFS Traversal:", end=" ")
            bfs(start)
            print()
        elif choice == "6":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
