import random


# Rock Paper Scissors game

# Function to display welcome message
def display_welcome():
    print("=" * 50)
    print("Welcome to the Rock Paper Scissors game!")
    print("=" * 50)


# Function to display menu
def display_menu():
    print("=" * 50)
    print("Choose one of the following options:")
    print("1. Rock")
    print("2. Paper")
    print("3. Scissors")
    print("=" * 50)


# Function to get player choice with validation
def get_player_choice():
    valid_choice = False
    while not valid_choice:
        display_menu()
        choice = input("Enter your choice (1/2/3): ")
        if choice in ["1", "2", "3"]:
            valid_choice = True
        else:
            print("=" * 50)
            print("Please enter a valid option (1, 2, or 3).")
            print("=" * 50)
    return convert_choice(int(choice))


# Function to generate computer random choice
def get_computer_choice():
    computer_choice = random.randint(1, 3)
    return convert_choice(computer_choice)


# Convert number to choice name
def convert_choice(choice):
    if choice == 1:
        return "Rock"
    elif choice == 2:
        return "Paper"
    elif choice == 3:
        return "Scissors"


# Function to display both player and computer choices
def display_choices(player_choice, computer_choice):
    print("=" * 50)
    print(f"Your choice: {player_choice}")
    print(f"Computer choice: {computer_choice}")
    print("=" * 50)


# Function to determine the winner of the round
def determine_winner(player_choice, computer_choice):
    if player_choice == computer_choice:
        return "Draw"
    elif (player_choice == "Rock" and computer_choice == "Scissors") or \
            (player_choice == "Paper" and computer_choice == "Rock") or \
            (player_choice == "Scissors" and computer_choice == "Paper"):
        return "Player Wins"
    else:
        return "Computer Wins"


# Function to display the result of the round
def display_round_result(result):
    print("=" * 50)
    if result == "Draw":
        print("It's a tie!")
    elif result == "Player Wins":
        print("You won this round!")
    else:
        print("Computer won this round!")
    print("=" * 50)


# Function to update scores
def update_score(result, player_score, computer_score):
    if result == "Player Wins":
        player_score += 10
    elif result == "Computer Wins":
        computer_score += 10
    return player_score, computer_score


# Function to display current score
def display_score(round_number, player_score, computer_score):
    print("=" * 50)
    print(f"Round {round_number}")
    print(f"Score: YOU {player_score}, COMPUTER {computer_score}")
    print("=" * 50)


# Function to ask the player if they want to play again
def ask_player_again():
    print("=" * 50)
    play_again = input("Do you want to play again? (y/n): ").lower()
    print("=" * 50)
    return play_again in ["y", "yes"]


# Function to display final result
def display_final_result(round_number, player_score, computer_score):
    print("=" * 50)
    print("---- FINAL RESULT ----")
    print(f"Number of rounds: {round_number}")
    print(f"Your score: {player_score}")
    print(f"Computer's score: {computer_score}")

    if player_score > computer_score:
        print("Congratulations! You win!")
    elif player_score < computer_score:
        print("Computer wins! Better luck next time!")
    else:
        print("It's a draw! Try again next time!")

    print("Thank you for playing!")
    print("=" * 50)


# Main function
def play_game():
    display_welcome()

    # Initialize the scores
    player_score = 0
    computer_score = 0
    round_number = 0

    # Main game loop
    continue_playing = True
    while continue_playing:
        round_number += 1
        display_score(round_number, player_score, computer_score)

        # Get choices
        player_choice = get_player_choice()
        computer_choice = get_computer_choice()

        display_choices(player_choice, computer_choice)
        result = determine_winner(player_choice, computer_choice)
        display_round_result(result)
        player_score, computer_score = update_score(result, player_score, computer_score)
        continue_playing = ask_player_again()

    display_final_result(round_number, player_score, computer_score)


# Run the game
if __name__ == "__main__":
    play_game()
