def main():
    while True:
        try:
            numbers_input = input("Please enter numbers separated by spaces:")
            numbers = [int(x) for x in numbers_input.split()]
        except ValueError:
            print("Invalid input. Only numbers separated by spaces are allowed.")
            continue
        max_value = numbers[0]
        min_value = numbers[0]

        for number in numbers:
            if number > max_value:
                max_value = number
            if number < min_value:
                min_value = number
        print("="*50)
        print(f"Maximum value is {max_value} and minimum value is {min_value}")
        print("=" * 50)
        resp_user = input("Do you want to restart the program? (yes/no): ")
        if resp_user.lower() not in ['y','ye', 'yes']:
            print("Program ended.")
            break
if __name__ == "__main__":
    main()