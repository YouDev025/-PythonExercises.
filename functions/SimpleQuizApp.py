import os


# Clear the screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Validate choice input
def get_choice_input(prompt, choices):
    while True:
        choice = input(prompt).strip().lower()
        if choice in choices:
            return choice
        print(f"Invalid choice. Options are: {', '.join(choices)}")


# Quiz questions stored as a list of dictionaries
quiz_questions = [
    {
        "question": "What is the capital of France?",
        "options": ["a) Paris", "b) Rome", "c) Madrid", "d) Berlin"],
        "answer": "a"
    },
    {
        "question": "Which language is primarily used for data science?",
        "options": ["a) Java", "b) Python", "c) C++", "d) Ruby"],
        "answer": "b"
    },
    {
        "question": "What does 'HTTP' stand for?",
        "options": ["a) HyperText Transfer Protocol",
                    "b) HighText Transfer Protocol",
                    "c) Hyper Transfer Text Process",
                    "d) None of the above"],
        "answer": "a"
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["a) Venus", "b) Jupiter", "c) Mars", "d) Saturn"],
        "answer": "c"
    },
    {
        "question": "What is 7 × 8?",
        "options": ["a) 54", "b) 56", "c) 64", "d) 48"],
        "answer": "b"
    },
    {
        "question": "Who wrote 'Romeo and Juliet'?",
        "options": ["a) Charles Dickens", "b) Mark Twain", "c) William Shakespeare", "d) Jane Austen"],
        "answer": "c"
    },
    {
        "question": "What is the largest ocean on Earth?",
        "options": ["a) Atlantic Ocean", "b) Indian Ocean", "c) Arctic Ocean", "d) Pacific Ocean"],
        "answer": "d"
    },
    {
        "question": "Which element has the chemical symbol 'O'?",
        "options": ["a) Gold", "b) Oxygen", "c) Silver", "d) Iron"],
        "answer": "b"
    },
    {
        "question": "In what year did World War II end?",
        "options": ["a) 1943", "b) 1944", "c) 1945", "d) 1946"],
        "answer": "c"
    },
    {
        "question": "What is the smallest prime number?",
        "options": ["a) 0", "b) 1", "c) 2", "d) 3"],
        "answer": "c"
    }
]


# Run the quiz
def run_quiz():
    clear_screen()
    print("=== Simple Quiz App ===\n")
    score = 0

    for i, q in enumerate(quiz_questions, start=1):
        print(f"Q{i}: {q['question']}")
        for option in q["options"]:
            print(option)

        user_answer = get_choice_input("Your answer (a/b/c/d): ", ["a", "b", "c", "d"])

        if user_answer == q["answer"]:
            print("Correct!\n")
            score += 1
        else:
            print(f"Wrong! Correct answer: {q['answer']}\n")

    print(f"Quiz finished! Your score: {score}/{len(quiz_questions)}\n")


# Menu logic
def quiz_menu():
    clear_screen()
    print("=== Quiz Menu ===")
    print("1. Start Quiz")
    print("2. Exit")

    choice = get_choice_input("Select an option (1/2): ", ["1", "2"])

    if choice == "1":
        run_quiz()
    elif choice == "2":
        print("Exiting Quiz App.")
        return False

    return True


# Program loop
def main():
    while True:
        if not quiz_menu():
            break
        again = get_choice_input("Do you want to try again? (y/n): ", ["y", "n"])
        if again == "n":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()