"""
Score Ranking System
Allows users to enter player names and scores, ranks them, and optionally saves results to a file.
"""

players = {}  # { name: score }

DIVIDER = "─" * 45


# ─────────────────────────────────────────────
#  Helper Functions
# ─────────────────────────────────────────────

def ordinal(n):
    """Return ordinal string for a number (1 → 1st, 2 → 2nd, etc.)"""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def get_ranking():
    """Return a sorted list of (rank, name, score) tuples."""
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    ranking = []
    for i, (name, score) in enumerate(sorted_players, start=1):
        ranking.append((i, name, score))
    return ranking


def medal(rank):
    """Return a medal emoji for top 3 ranks."""
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "  ")


# ─────────────────────────────────────────────
#  Core Operations
# ─────────────────────────────────────────────

def add_player():
    """Prompt the user to enter a player name and score."""
    print(f"\n  {'ADD PLAYER':^41}")
    print(DIVIDER)
    name = input("  Enter player name: ").strip()
    if not name:
        print("  ✘ Name cannot be empty.")
        return

    if name in players:
        print(f"  ✘ '{name}' already exists. Use 'Update Score' to change their score.")
        return

    score_input = input(f"  Enter score for '{name}': ").strip()
    try:
        score = float(score_input)
        players[name] = score
        print(f"  ✔ '{name}' added with a score of {score:g}.")
    except ValueError:
        print(f"  ✘ Invalid score '{score_input}'. Please enter a numeric value.")


def add_multiple_players():
    """Batch-add players until the user is done."""
    print(f"\n  {'ADD MULTIPLE PLAYERS':^41}")
    print(DIVIDER)
    print("  Enter player names and scores one by one.")
    print("  Type 'done' as the player name to stop.\n")

    while True:
        name = input("  Player name (or 'done' to stop): ").strip()
        if name.lower() == "done":
            print("  ✔ Finished adding players.")
            break
        if not name:
            print("  ✘ Name cannot be empty. Try again.")
            continue
        if name in players:
            print(f"  ✘ '{name}' already exists. Skipping.")
            continue

        score_input = input(f"  Score for '{name}': ").strip()
        try:
            score = float(score_input)
            players[name] = score
            print(f"  ✔ '{name}' added with a score of {score:g}.\n")
        except ValueError:
            print(f"  ✘ Invalid score '{score_input}'. Skipping '{name}'.\n")


def update_score():
    """Update the score of an existing player."""
    if not players:
        print("\n  ✘ No players yet. Add some players first.")
        return

    print(f"\n  {'UPDATE SCORE':^41}")
    print(DIVIDER)
    name = input("  Enter the player name to update: ").strip()
    if name not in players:
        print(f"  ✘ '{name}' not found.")
        return

    score_input = input(f"  Enter new score for '{name}' (current: {players[name]:g}): ").strip()
    try:
        score = float(score_input)
        players[name] = score
        print(f"  ✔ '{name}' score updated to {score:g}.")
    except ValueError:
        print(f"  ✘ Invalid score '{score_input}'. No changes made.")


def remove_player():
    """Remove a player from the list."""
    if not players:
        print("\n  ✘ No players yet. Add some players first.")
        return

    print(f"\n  {'REMOVE PLAYER':^41}")
    print(DIVIDER)
    name = input("  Enter the player name to remove: ").strip()
    if name in players:
        del players[name]
        print(f"  ✔ '{name}' has been removed.")
    else:
        print(f"  ✘ '{name}' not found.")


def display_ranking():
    """Display all players ranked by score."""
    print(f"\n  {'SCORE RANKING':^41}")
    print(DIVIDER)

    if not players:
        print("  [ No players have been added yet ]")
        return

    ranking = get_ranking()

    print(f"  {'Rank':<6} {'Player':<20} {'Score':>10}")
    print(DIVIDER)
    for rank, name, score in ranking:
        icon = medal(rank)
        rank_str = ordinal(rank)
        print(f"  {icon} {rank_str:<4} {name:<20} {score:>10g}")
    print(DIVIDER)
    print(f"  Total players: {len(players)}")


def save_to_file():
    """Save the current ranking to a .txt file."""
    if not players:
        print("\n  ✘ No players to save. Add some players first.")
        return

    print(f"\n  {'SAVE TO FILE':^41}")
    print(DIVIDER)
    filename = input("  Enter filename (without extension): ").strip()
    if not filename:
        filename = "ranking_results"

    filename = filename + ".txt"
    ranking = get_ranking()

    try:
        with open(filename, "w") as f:
            f.write("=" * 45 + "\n")
            f.write("           SCORE RANKING RESULTS\n")
            f.write("=" * 45 + "\n")
            f.write(f"  {'Rank':<6} {'Player':<20} {'Score':>10}\n")
            f.write("-" * 45 + "\n")
            for rank, name, score in ranking:
                rank_str = ordinal(rank)
                f.write(f"  {rank_str:<6} {name:<20} {score:>10g}\n")
            f.write("-" * 45 + "\n")
            f.write(f"  Total players: {len(players)}\n")

        print(f"  ✔ Ranking saved to '{filename}' successfully.")
    except IOError as e:
        print(f"  ✘ Failed to save file: {e}")


# ─────────────────────────────────────────────
#  Menu
# ─────────────────────────────────────────────

def print_menu():
    print(f"\n{'═' * 45}")
    print("         SCORE RANKING SYSTEM")
    print(f"{'═' * 45}")
    print("  1. Add a single player")
    print("  2. Add multiple players")
    print("  3. Update a player's score")
    print("  4. Remove a player")
    print("  5. Display ranking")
    print("  6. Save ranking to file")
    print("  7. Exit")
    print(DIVIDER)


def print_intro():
    """Display a welcome banner with a short program description."""
    print()
    print("  ╔═════════════════════════════════════════╗")
    print("  ║       SCORE RANKING SYSTEM  🏆           ║")
    print("  ╠═════════════════════════════════════════╣")
    print("  ║  Track and rank players by their scores ║")
    print("  ║  • Add single or multiple players       ║")
    print("  ║  • Update or remove player entries      ║")
    print("  ║  • View live ranked leaderboard         ║")
    print("  ║  • Save results to a .txt file          ║")
    print("  ╚═════════════════════════════════════════╝")


def main():
    print_intro()

    while True:
        print_menu()
        choice = input("  Enter your choice (1–7): ").strip()

        if choice == "1":
            add_player()
        elif choice == "2":
            add_multiple_players()
        elif choice == "3":
            update_score()
        elif choice == "4":
            remove_player()
        elif choice == "5":
            display_ranking()
        elif choice == "6":
            save_to_file()
        elif choice == "7":
            print("\n  Goodbye! Thanks for using the Score Ranking System.\n")
            break
        else:
            print("  ✘ Invalid choice. Please enter a number between 1 and 7.")


if __name__ == "__main__":
    main()