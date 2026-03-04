# =============================================================================
# Interactive Dijkstra Shortest Path Solver
# This program allows users to build a weighted graph interactively and find
# the shortest path between any two nodes using Dijkstra's algorithm.
# It displays the shortest distance, reconstructed path, and iteration count.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================

import math


# ─────────────────────────────────────────────
#  Graph helpers
# ─────────────────────────────────────────────

def create_graph():
    """Return an empty weighted adjacency-list graph."""
    return {}


def add_node(graph, node):
    """Add a node to the graph if it does not already exist."""
    node = node.strip().upper()
    if node in graph:
        print(f"  [!] Node '{node}' already exists.")
    else:
        graph[node] = []
        print(f"  [+] Node '{node}' added.")
    return node


def add_edge(graph, u, v, weight, directed=False):
    """
    Add a weighted edge between u and v.
    By default the graph is undirected (edge added both ways).
    """
    u, v = u.strip().upper(), v.strip().upper()

    # Auto-create nodes that don't exist yet
    for node in (u, v):
        if node not in graph:
            graph[node] = []
            print(f"  [+] Node '{node}' auto-created.")

    # Prevent duplicate edges
    if any(neighbor == v for neighbor, _ in graph[u]):
        print(f"  [!] Edge {u} → {v} already exists.")
        return

    graph[u].append((v, weight))
    if not directed:
        graph[v].append((u, weight))

    arrow = "↔" if not directed else "→"
    print(f"  [+] Edge {u} {arrow} {v}  (weight: {weight}) added.")


def display_graph(graph):
    """Pretty-print the adjacency list."""
    if not graph:
        print("  [!] Graph is empty.")
        return

    print("\n  ┌─── Graph ───────────────────────────────┐")
    for node in sorted(graph):
        if graph[node]:
            neighbours = ",  ".join(
                f"{nb} (w={wt})" for nb, wt in graph[node]
            )
            print(f"  │  {node}  →  {neighbours}")
        else:
            print(f"  │  {node}  →  (no edges)")
    print("  └─────────────────────────────────────────┘\n")


# ─────────────────────────────────────────────
#  Dijkstra's Algorithm
# ─────────────────────────────────────────────

def dijkstra(graph, start, end):
    """
    Find the shortest path from 'start' to 'end' using Dijkstra's algorithm.

    Data structures used
    ────────────────────
    distances   : dict  – current best distance from start to every node
    previous    : dict  – tracks the preceding node on the best-known path
    visited     : set   – nodes whose shortest distance is finalised
    iterations  : int   – counts how many times we select a node to relax

    Returns
    ───────
    (distance, path, iterations)
        distance   – total shortest distance (math.inf if unreachable)
        path       – list of nodes forming the shortest path ([] if none)
        iterations – number of main-loop iterations performed
    """

    # ── Initialisation ──────────────────────────────────────────────────────
    # Set every node's tentative distance to infinity; source gets 0.
    distances = {node: math.inf for node in graph}
    previous  = {node: None     for node in graph}
    visited   = set()

    if start not in distances or end not in distances:
        return math.inf, [], 0

    distances[start] = 0
    iterations = 0

    print("\n  ── Distance initialisation ─────────────────────────")
    for node in sorted(distances):
        dist_str = "0" if node == start else "∞"
        print(f"     {node}: {dist_str}")
    print()

    # ── Main loop ────────────────────────────────────────────────────────────
    while True:
        # ── Node selection ───────────────────────────────────────────────────
        # Pick the unvisited node with the smallest tentative distance.
        current = None
        current_dist = math.inf
        for node, dist in distances.items():
            if node not in visited and dist < current_dist:
                current      = node
                current_dist = dist

        # No reachable unvisited node remains → stop.
        if current is None:
            break

        # Destination reached → no need to continue.
        if current == end:
            iterations += 1
            break

        visited.add(current)
        iterations += 1

        print(f"  Iteration {iterations:>3}  │  Visiting: {current}"
              f"  (dist from {start} = {current_dist})")

        # ── Distance update (relaxation) ─────────────────────────────────────
        # For each neighbour of the current node, check whether going through
        # 'current' gives a shorter path than the one recorded so far.
        for neighbour, weight in graph[current]:
            if neighbour in visited:
                continue

            new_dist = distances[current] + weight

            if new_dist < distances[neighbour]:
                distances[neighbour] = new_dist
                previous[neighbour]  = current
                print(f"           │    Update {neighbour}:"
                      f"  ∞  →  {new_dist}"
                      if distances[neighbour] == new_dist and previous[neighbour] == current
                      else
                      f"           │    Update {neighbour}:"
                      f"  old={distances[neighbour]}  →  {new_dist}")

    # ── Path reconstruction ───────────────────────────────────────────────────
    # Walk backwards from 'end' through the 'previous' map to rebuild the path.
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()

    # If path doesn't begin with start, the destination is unreachable.
    if path[0] != start:
        path = []

    return distances[end], path, iterations


# ─────────────────────────────────────────────
#  Input helpers
# ─────────────────────────────────────────────

def get_positive_float(prompt):
    """Keep asking until the user enters a positive number."""
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value <= 0:
                print("  [!] Weight must be a positive number.")
                continue
            return value
        except ValueError:
            print("  [!] Invalid number. Please try again.")


def get_non_empty_string(prompt):
    """Keep asking until the user enters a non-blank string."""
    while True:
        raw = input(prompt).strip()
        if raw:
            return raw.upper()
        print("  [!] Input cannot be empty.")


def require_nodes(graph, *nodes):
    """
    Return True if all nodes exist in the graph.
    Print a helpful message for each missing node.
    """
    ok = True
    for n in nodes:
        if n not in graph:
            print(f"  [!] Node '{n}' does not exist in the graph.")
            ok = False
    return ok


# ─────────────────────────────────────────────
#  Menu handlers
# ─────────────────────────────────────────────

def menu_add_node(graph):
    name = get_non_empty_string("  Enter node name: ")
    add_node(graph, name)


def menu_add_edge(graph):
    if len(graph) < 2:
        print("  [!] You need at least 2 nodes to add an edge.")
        return

    u = get_non_empty_string("  From node: ")
    v = get_non_empty_string("  To node  : ")

    if u == v:
        print("  [!] Self-loops are not allowed.")
        return

    weight = get_positive_float("  Weight    : ")
    add_edge(graph, u, v, weight)


def menu_find_path(graph):
    if len(graph) < 2:
        print("  [!] You need at least 2 nodes to search for a path.")
        return

    src = get_non_empty_string("  Source node     : ")
    dst = get_non_empty_string("  Destination node: ")

    if not require_nodes(graph, src, dst):
        return

    if src == dst:
        print("  [!] Source and destination are the same node.")
        return

    print()
    distance, path, iterations = dijkstra(graph, src, dst)

    print("\n  ┌─── Result ───────────────────────────────────────┐")
    if math.isinf(distance):
        print(f"  │  No path found from '{src}' to '{dst}'.")
    else:
        path_str = "  →  ".join(path)
        print(f"  │  Shortest distance : {distance}")
        print(f"  │  Path              : {path_str}")
        print(f"  │  Iterations        : {iterations}")
    print("  └──────────────────────────────────────────────────┘\n")


# ─────────────────────────────────────────────
#  Main menu loop
# ─────────────────────────────────────────────

MENU = """
  ╔══════════════════════════════════════════════╗
  ║     Interactive Dijkstra Path Solver         ║
  ╠══════════════════════════════════════════════╣
  ║  1. Add a node                               ║
  ║  2. Add a weighted edge                      ║
  ║  3. Display graph                            ║
  ║  4. Find shortest path                       ║
  ║  5. Exit                                     ║
  ╚══════════════════════════════════════════════╝"""


def main():
    graph = create_graph()

    print(MENU)

    while True:
        print()
        choice = input("  Select option (1-5): ").strip()

        if choice == "1":
            menu_add_node(graph)

        elif choice == "2":
            menu_add_edge(graph)

        elif choice == "3":
            display_graph(graph)

        elif choice == "4":
            menu_find_path(graph)

        elif choice == "5":
            print("\n  Goodbye!\n")
            break

        else:
            print("  [!] Invalid choice. Please enter a number from 1 to 5.")


if __name__ == "__main__":
    main()