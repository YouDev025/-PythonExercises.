# =============================================================================
# Interactive Cycle Detection (Undirected Graph)
# This program lets users build an undirected graph interactively and detect
# whether it contains a cycle using a recursive Depth-First Search (DFS).
# It reports the result, the number of recursive calls made, and the cycle path.
# =============================================================================
# Author  : Claude (Anthropic)
# Version : 1.0
# =============================================================================


# ─────────────────────────────────────────────
#  Graph helpers
# ─────────────────────────────────────────────

def create_graph():
    """Return an empty undirected adjacency-list graph."""
    return {}


def add_node(graph, node):
    """Add a node to the graph; warn if it already exists."""
    node = node.strip().upper()
    if node in graph:
        print(f"  [!] Node '{node}' already exists.")
    else:
        graph[node] = []
        print(f"  [+] Node '{node}' added.")
    return node


def add_edge(graph, u, v):
    """
    Add an undirected edge between u and v.
    Auto-creates either node if it is not yet in the graph.
    """
    u, v = u.strip().upper(), v.strip().upper()

    if u == v:
        print("  [!] Self-loops are not allowed.")
        return

    # Auto-create missing nodes
    for node in (u, v):
        if node not in graph:
            graph[node] = []
            print(f"  [+] Node '{node}' auto-created.")

    # Prevent duplicate edges
    if v in graph[u]:
        print(f"  [!] Edge {u} — {v} already exists.")
        return

    graph[u].append(v)
    graph[v].append(u)
    print(f"  [+] Edge {u} — {v} added.")


def display_graph(graph):
    """Pretty-print the adjacency list."""
    if not graph:
        print("  [!] Graph is empty.")
        return

    print("\n  ┌─── Graph ────────────────────────────────────┐")
    for node in sorted(graph):
        if graph[node]:
            neighbours = ",  ".join(sorted(graph[node]))
            print(f"  │  {node}  →  {neighbours}")
        else:
            print(f"  │  {node}  →  (no edges)")
    print("  └──────────────────────────────────────────────┘\n")


# ─────────────────────────────────────────────
#  Cycle Detection — DFS (recursive)
# ─────────────────────────────────────────────

def dfs(graph, node, parent, visited, call_counter, path):
    """
    Recursive DFS that looks for a back-edge (cycle indicator).

    Parameters
    ──────────
    graph        : adjacency-list dict
    node         : the node currently being explored
    parent       : the node we arrived from (avoids treating the
                   incoming undirected edge as a back-edge)
    visited      : set of already-visited nodes
    call_counter : list with one int element — used as a mutable
                   counter so recursive calls can increment it
    path         : list tracking the current DFS path for cycle display

    Returns
    ───────
    (cycle_found: bool, cycle_path: list)
        cycle_found  – True if a back-edge was discovered
        cycle_path   – the nodes forming the detected cycle ([] if none)
    """

    # ── Mark current node as visited and record the call ────────────────────
    visited.add(node)
    call_counter[0] += 1
    path.append(node)

    print(f"  {'  ' * (call_counter[0] - 1)}↳ Visit: {node}"
          f"  (parent: {parent if parent else '—'})"
          f"  │  call #{call_counter[0]}")

    # ── Explore every neighbour ──────────────────────────────────────────────
    for neighbour in graph[node]:

        if neighbour not in visited:
            # Neighbour not yet seen → recurse deeper
            found, cycle_path = dfs(
                graph, neighbour, node, visited, call_counter, path
            )
            if found:
                return True, cycle_path

        elif neighbour != parent:
            # ── Cycle detected ───────────────────────────────────────────────
            # Neighbour IS visited AND is not the node we came from →
            # we have found a back-edge, which means a cycle exists.
            call_counter[0] += 1
            print(f"  {'  ' * call_counter[0]}↳ Back-edge detected:"
                  f"  {node} — {neighbour}  │  call #{call_counter[0]}")

            # Reconstruct just the cycle portion of the path
            if neighbour in path:
                cycle_start = path.index(neighbour)
                cycle_path  = path[cycle_start:] + [neighbour]
            else:
                cycle_path  = path + [neighbour]

            return True, cycle_path

    # ── Backtrack: remove node from current path ─────────────────────────────
    path.pop()
    return False, []


def detect_cycle(graph):
    """
    Drive the DFS over every connected component of the graph.

    Uses a shared 'visited' set so each node is processed only once,
    even in disconnected graphs.

    Returns
    ───────
    (cycle_found: bool, cycle_path: list, total_calls: int)
    """
    visited      = set()     # tracks globally visited nodes
    call_counter = [0]       # mutable counter shared across all DFS calls

    for node in sorted(graph):                 # sorted for deterministic output
        if node not in visited:
            found, cycle_path = dfs(
                graph, node, None, visited, call_counter, []
            )
            if found:
                return True, cycle_path, call_counter[0]

    return False, [], call_counter[0]


# ─────────────────────────────────────────────
#  Input helpers
# ─────────────────────────────────────────────

def get_non_empty_string(prompt):
    """Keep asking until the user provides a non-blank string."""
    while True:
        raw = input(prompt).strip()
        if raw:
            return raw.upper()
        print("  [!] Input cannot be empty. Please try again.")


def require_node(graph, name):
    """Return True if the node exists; otherwise print a warning."""
    if name not in graph:
        print(f"  [!] Node '{name}' does not exist in the graph.")
        return False
    return True


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
    u = get_non_empty_string("  First node : ")
    v = get_non_empty_string("  Second node: ")
    add_edge(graph, u, v)


def menu_detect_cycle(graph):
    if not graph:
        print("  [!] Graph is empty — nothing to analyse.")
        return

    # Check if there are any edges at all
    has_edges = any(graph[n] for n in graph)
    if not has_edges:
        print("  [!] Graph has no edges — a cycle is impossible.")
        return

    print("\n  ── DFS Traversal ───────────────────────────────────")
    cycle_found, cycle_path, total_calls = detect_cycle(graph)
    print()

    print("  ┌─── Cycle Detection Result ────────────────────────┐")
    if cycle_found:
        path_str = "  →  ".join(cycle_path)
        print(f"  │  ✗  Cycle DETECTED")
        print(f"  │  Cycle path       : {path_str}")
    else:
        print(f"  │  ✓  No cycle found  (graph is acyclic)")
    print(f"  │  Recursive calls  : {total_calls}")
    print("  └────────────────────────────────────────────────────┘\n")


# ─────────────────────────────────────────────
#  Main menu loop
# ─────────────────────────────────────────────

MENU = """
  ╔══════════════════════════════════════════════════╗
  ║    Interactive Cycle Detection — Undirected      ║
  ╠══════════════════════════════════════════════════╣
  ║  1.  Add node                                    ║
  ║  2.  Add edge                                    ║
  ║  3.  Display graph                               ║
  ║  4.  Detect cycle                                ║
  ║  5.  Exit                                        ║
  ╚══════════════════════════════════════════════════╝"""


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
            menu_detect_cycle(graph)

        elif choice == "5":
            print("\n  Goodbye!\n")
            break

        else:
            print("  [!] Invalid choice. Please enter a number from 1 to 5.")


if __name__ == "__main__":
    main()