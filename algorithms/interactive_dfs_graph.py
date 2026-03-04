"""
Interactive Depth First Search (DFS) Graph Explorer
---------------------------------------------------
This program allows users to build a graph interactively,
then perform a Depth First Search (DFS) traversal with
detailed output including traversal order and recursion count.

Author: Youssef Adardour
Date: March 2026
"""

# Graph stored as adjacency list
graph = {}

# Global counter for recursive calls
recursive_calls = 0


def add_node():
    """Add a new node to the graph."""
    node = input("Enter node name: ").strip()
    if node in graph:
        print(f"Node '{node}' already exists.")
    else:
        graph[node] = []
        print(f"Node '{node}' added successfully.")


def add_edge():
    """Add an edge between two nodes."""
    u = input("Enter first node: ").strip()
    v = input("Enter second node: ").strip()

    if u not in graph or v not in graph:
        print("Both nodes must exist in the graph.")
        return

    if v not in graph[u]:
        graph[u].append(v)
    if u not in graph[v]:
        graph[v].append(u)

    print(f"Edge added between '{u}' and '{v}'.")


def display_graph():
    """Display the adjacency list of the graph."""
    if not graph:
        print("Graph is empty.")
        return
    print("\nGraph adjacency list:")
    for node, neighbors in graph.items():
        print(f"{node}: {neighbors}")


def dfs(graph, node, visited, traversal):
    """
    Recursive DFS function.
    - Visits node
    - Explores neighbors recursively
    - Tracks backtracking
    """
    global recursive_calls
    recursive_calls += 1

    print(f"Visiting node: {node}")
    visited.add(node)
    traversal.append(node)

    for neighbor in graph[node]:
        if neighbor not in visited:
            print(f"Exploring neighbor: {neighbor} from {node}")
            dfs(graph, neighbor, visited, traversal)
        else:
            print(f"Already visited {neighbor}, skipping.")

    print(f"Backtracking from node: {node}")


def perform_dfs():
    """Perform DFS traversal starting from a user-specified node."""
    if not graph:
        print("Graph is empty. Add nodes and edges first.")
        return

    start = input("Enter starting node for DFS: ").strip()
    if start not in graph:
        print(f"Node '{start}' does not exist in the graph.")
        return

    visited = set()
    traversal = []
    global recursive_calls
    recursive_calls = 0

    print("\n--- DFS Traversal ---")
    dfs(graph, start, visited, traversal)

    print("\nTraversal order:", traversal)
    print("Number of recursive calls:", recursive_calls)


def menu():
    """Interactive menu system."""
    while True:
        print("\n--- Interactive DFS Graph Explorer ---")
        print("1. Add a node")
        print("2. Add an edge")
        print("3. Display graph")
        print("4. Perform DFS traversal")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            add_node()
        elif choice == "2":
            add_edge()
        elif choice == "3":
            display_graph()
        elif choice == "4":
            perform_dfs()
        elif choice == "5":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


# Run the program
if __name__ == "__main__":
    menu()
