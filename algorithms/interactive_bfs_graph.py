"""
Interactive Breadth First Search (BFS) Graph Explorer
-----------------------------------------------------
This program allows users to build a graph interactively,
then perform a Breadth First Search (BFS) traversal with
detailed output including traversal order and iteration count.

Author: Youssef Adardour
Date: March 2026
"""

# Graph stored as adjacency list
graph = {}


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


def bfs(graph, start_node):
    """
    Perform BFS traversal.
    - Enqueue start node
    - Dequeue nodes one by one
    - Visit nodes and enqueue their neighbors
    """
    visited = set()
    queue = []
    traversal = []
    iterations = 0

    # Enqueue start node
    queue.append(start_node)
    visited.add(start_node)

    print("\n--- BFS Traversal ---")
    while queue:
        iterations += 1
        print(f"Queue state: {queue}")

        # Dequeue node
        current = queue.pop(0)
        print(f"Dequeued node: {current}")

        # Visit node
        traversal.append(current)

        # Enqueue neighbors
        for neighbor in graph[current]:
            if neighbor not in visited:
                print(f"Enqueue neighbor: {neighbor}")
                visited.add(neighbor)
                queue.append(neighbor)
            else:
                print(f"Already visited {neighbor}, skipping.")

    return traversal, iterations


def perform_bfs():
    """Perform BFS traversal starting from a user-specified node."""
    if not graph:
        print("Graph is empty. Add nodes and edges first.")
        return

    start = input("Enter starting node for BFS: ").strip()
    if start not in graph:
        print(f"Node '{start}' does not exist in the graph.")
        return

    traversal, iterations = bfs(graph, start)

    print("\nTraversal order:", traversal)
    print("Number of iterations:", iterations)


def menu():
    """Interactive menu system."""
    while True:
        print("\n--- Interactive BFS Graph Explorer ---")
        print("1. Add a node")
        print("2. Add an edge")
        print("3. Display graph")
        print("4. Perform BFS traversal")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            add_node()
        elif choice == "2":
            add_edge()
        elif choice == "3":
            display_graph()
        elif choice == "4":
            perform_bfs()
        elif choice == "5":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


# Run the program
if __name__ == "__main__":
    menu()
