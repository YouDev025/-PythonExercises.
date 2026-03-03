"""
Interactive Simple Backtracking Solver
--------------------------------------
This program allows the user to explore three classic backtracking problems:
1. Generate all permutations of a list
2. Solve a simple maze (path finding)
3. Solve the N-Queens problem
It is fully interactive with a menu system.

Author: Youssef Adardour
Date: March 2026
"""

# -------------------------------
# Utility: Input validation
# -------------------------------
def get_int_input(prompt, min_val=None, max_val=None):
    """Safely get integer input within optional bounds."""
    while True:
        try:
            val = int(input(prompt))
            if (min_val is not None and val < min_val) or (max_val is not None and val > max_val):
                print(f"Please enter a number between {min_val} and {max_val}.")
                continue
            return val
        except ValueError:
            print("Invalid input. Please enter an integer.")

# -------------------------------
# 1) Permutations
# -------------------------------
def generate_permutations(elements):
    """Recursively generate all permutations using backtracking."""
    results = []

    def backtrack(path, used):
        if len(path) == len(elements):
            results.append(path[:])  # store a copy of the current permutation
            return
        for i in range(len(elements)):
            if used[i]:
                continue
            # Choose
            used[i] = True
            path.append(elements[i])
            # Explore
            backtrack(path, used)
            # Undo choice (backtrack)
            path.pop()
            used[i] = False

    backtrack([], [False] * len(elements))
    return results

def run_permutations():
    print("\n--- Permutations Generator ---")
    raw = input("Enter elements separated by spaces: ").strip()
    elements = raw.split()
    results = generate_permutations(elements)
    print(f"\nTotal permutations: {len(results)}")
    for perm in results:
        print(perm)

# -------------------------------
# 2) Maze Solver
# -------------------------------
def solve_maze(maze, start, end):
    """Recursively solve maze using backtracking."""
    rows, cols = len(maze), len(maze[0])
    path = []
    visited = [[False]*cols for _ in range(rows)]

    def backtrack(r, c):
        if not (0 <= r < rows and 0 <= c < cols):
            return False
        if maze[r][c] == 1 or visited[r][c]:
            return False
        path.append((r, c))
        visited[r][c] = True
        if (r, c) == end:
            return True
        # Explore neighbors
        if (backtrack(r+1, c) or backtrack(r-1, c) or
            backtrack(r, c+1) or backtrack(r, c-1)):
            return True
        # Undo choice (backtrack)
        path.pop()
        return False

    found = backtrack(start[0], start[1])
    return found, path

def run_maze_solver():
    print("\n--- Maze Solver ---")
    maze = [
        [0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 0, 1, 0],
        [1, 1, 0, 0, 0],
        [0, 0, 0, 1, 0]
    ]
    start = (0, 0)
    end = (4, 4)
    found, path = solve_maze(maze, start, end)
    if found:
        print("Path found:", path)
        solution = [[0]*len(maze[0]) for _ in range(len(maze))]
        for r, c in path:
            solution[r][c] = 2  # mark path
        print("Solution matrix:")
        for row in solution:
            print(row)
    else:
        print("No path found.")

# -------------------------------
# 3) N-Queens
# -------------------------------
def solve_n_queens(N):
    """Solve N-Queens using recursion + backtracking."""
    board = [[0]*N for _ in range(N)]
    recursive_calls = [0]  # use list to mutate inside function

    def is_safe(row, col):
        # Check column
        for i in range(row):
            if board[i][col] == 1:
                return False
        # Check upper-left diagonal
        i, j = row-1, col-1
        while i >= 0 and j >= 0:
            if board[i][j] == 1:
                return False
            i -= 1; j -= 1
        # Check upper-right diagonal
        i, j = row-1, col+1
        while i >= 0 and j < N:
            if board[i][j] == 1:
                return False
            i -= 1; j += 1
        return True

    def backtrack(row):
        recursive_calls[0] += 1
        if row == N:
            return True
        for col in range(N):
            if is_safe(row, col):
                board[row][col] = 1
                if backtrack(row+1):
                    return True
                # Undo choice (backtrack)
                board[row][col] = 0
        return False

    found = backtrack(0)
    return found, board, recursive_calls[0]

def run_n_queens():
    print("\n--- N-Queens Solver ---")
    N = get_int_input("Enter board size N (>=4): ", min_val=4)
    found, board, calls = solve_n_queens(N)
    if found:
        print("One valid solution:")
        for row in board:
            print(row)
    else:
        print("No solution found.")
    print("Total recursive calls:", calls)

# -------------------------------
# Menu System
# -------------------------------
def main_menu():
    while True:
        print("\n=== Interactive Simple Backtracking Solver ===")
        print("1. Generate all permutations of a list")
        print("2. Solve a simple maze (path finding)")
        print("3. N-Queens (basic version)")
        print("4. Exit program")
        choice = get_int_input("Choose an option (1-4): ", 1, 4)
        if choice == 1:
            run_permutations()
        elif choice == 2:
            run_maze_solver()
        elif choice == 3:
            run_n_queens()
        elif choice == 4:
            print("Exiting program. Goodbye!")
            break

# -------------------------------
# Entry Point
# -------------------------------
if __name__ == "__main__":
    main_menu()
