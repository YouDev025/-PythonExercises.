"""
Matrix Operations Using Data Structures
---------------------------------------
This program allows users to create and manipulate matrices using lists of lists.
It supports matrix addition, multiplication, and transpose operations with proper
dimension validation and error handling.

Author: Youssef Adardour
Date: February 2026
"""


# Function to create a matrix
def create_matrix(rows, cols):
    matrix = []  # List of lists to represent the matrix
    print(f"Enter elements row by row ({rows}x{cols}):")
    for i in range(rows):
        row = []
        for j in range(cols):
            while True:
                try:
                    val = int(input(f"Element [{i + 1},{j + 1}]: "))
                    row.append(val)
                    break
                except ValueError:
                    print("Invalid input. Please enter an integer.")
        matrix.append(row)
    return matrix


# Function to display a matrix
def display_matrix(matrix):
    print("\nMatrix:")
    for row in matrix:
        print(" ".join(map(str, row)))


# Function for matrix addition
def add_matrices(matrix1, matrix2):
    if len(matrix1) != len(matrix2) or len(matrix1[0]) != len(matrix2[0]):
        print("Error: Matrices must have the same dimensions for addition.")
        return None
    result = []
    for i in range(len(matrix1)):
        row = []
        for j in range(len(matrix1[0])):
            row.append(matrix1[i][j] + matrix2[i][j])
        result.append(row)
    return result


# Function for matrix multiplication
def multiply_matrices(matrix1, matrix2):
    if len(matrix1[0]) != len(matrix2):
        print("Error: Number of columns in Matrix1 must equal number of rows in Matrix2.")
        return None
    result = []
    for i in range(len(matrix1)):
        row = []
        for j in range(len(matrix2[0])):
            val = 0
            for k in range(len(matrix2)):
                val += matrix1[i][k] * matrix2[k][j]
            row.append(val)
        result.append(row)
    return result


# Function for matrix transpose
def transpose_matrix(matrix):
    rows, cols = len(matrix), len(matrix[0])
    result = []
    for j in range(cols):
        row = []
        for i in range(rows):
            row.append(matrix[i][j])
        result.append(row)
    return result


# Main menu
def main():
    matrix1, matrix2 = None, None

    while True:
        print("\n--- Matrix Menu ---")
        print("1. Create Matrix 1")
        print("2. Create Matrix 2")
        print("3. Display Matrices")
        print("4. Add Matrices")
        print("5. Multiply Matrices")
        print("6. Transpose Matrix 1")
        print("7. Transpose Matrix 2")
        print("8. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            rows = int(input("Enter number of rows: "))
            cols = int(input("Enter number of columns: "))
            matrix1 = create_matrix(rows, cols)
        elif choice == "2":
            rows = int(input("Enter number of rows: "))
            cols = int(input("Enter number of columns: "))
            matrix2 = create_matrix(rows, cols)
        elif choice == "3":
            if matrix1:
                print("\nMatrix 1:")
                display_matrix(matrix1)
            else:
                print("Matrix 1 not created yet.")
            if matrix2:
                print("\nMatrix 2:")
                display_matrix(matrix2)
            else:
                print("Matrix 2 not created yet.")
        elif choice == "4":
            if matrix1 and matrix2:
                result = add_matrices(matrix1, matrix2)
                if result:
                    print("\nResult of Addition:")
                    display_matrix(result)
            else:
                print("Both matrices must be created first.")
        elif choice == "5":
            if matrix1 and matrix2:
                result = multiply_matrices(matrix1, matrix2)
                if result:
                    print("\nResult of Multiplication:")
                    display_matrix(result)
            else:
                print("Both matrices must be created first.")
        elif choice == "6":
            if matrix1:
                result = transpose_matrix(matrix1)
                print("\nTranspose of Matrix 1:")
                display_matrix(result)
            else:
                print("Matrix 1 not created yet.")
        elif choice == "7":
            if matrix2:
                result = transpose_matrix(matrix2)
                print("\nTranspose of Matrix 2:")
                display_matrix(result)
            else:
                print("Matrix 2 not created yet.")
        elif choice == "8":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
