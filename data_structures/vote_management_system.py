"""
Vote Management System (Interactive)
--------------------------------------------
This program allows users to register candidates, cast votes, and display results.
It prevents duplicate voting and determines the winner(s) based on vote counts.

Author: Youssef Adardour
Date: February 2026
"""

import json
import heapq

# Data structures
candidates = []          # List to store candidate names
votes = {}               # Dictionary: candidate_name -> vote_count
voters = set()           # Set to prevent duplicate voters


def register_candidate():
    """Register a new candidate."""
    name = input("Enter candidate name: ").strip()
    if not name:
        print("Invalid input. Candidate name cannot be empty.")
        return
    if name in candidates:
        print(f"Candidate '{name}' is already registered.")
    else:
        candidates.append(name)
        votes[name] = 0
        print(f"Candidate '{name}' registered successfully.")


def cast_vote():
    """Cast a vote for a candidate."""
    voter_id = input("Enter your voter ID: ").strip()
    if voter_id in voters:
        print("You have already voted. Duplicate voting not allowed.")
        return

    candidate_name = input("Enter candidate name to vote for: ").strip()
    if candidate_name not in candidates:
        print(f"Candidate '{candidate_name}' not found.")
        return

    voters.add(voter_id)
    votes[candidate_name] += 1
    print(f"Vote cast by '{voter_id}' for '{candidate_name}'.")


def display_results():
    """Display total votes, per candidate counts, and winner(s)."""
    print("\n--- Election Results ---")
    total_votes = sum(votes.values())
    print(f"Total votes: {total_votes}")

    # Sort results by vote count (descending)
    sorted_results = sorted(votes.items(), key=lambda x: x[1], reverse=True)
    for candidate, count in sorted_results:
        print(f"{candidate}: {count} votes")

    # Handle ties
    if sorted_results:
        max_votes = sorted_results[0][1]
        winners = [c for c, v in sorted_results if v == max_votes]
        if len(winners) > 1:
            print(f"Tie between: {', '.join(winners)} with {max_votes} votes each.")
        else:
            print(f"Winner: {winners[0]} with {max_votes} votes.")


def save_results():
    """Save results to a JSON file."""
    filename = "results.json"
    data = {
        "candidates": candidates,
        "votes": votes,
        "total_voters": len(voters)
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Results saved to {filename}")


def display_ranking_priority_queue():
    """Use a priority queue (heap) to display ranking."""
    print("\n--- Candidate Ranking (Priority Queue) ---")
    heap = [(-count, candidate) for candidate, count in votes.items()]
    heapq.heapify(heap)
    rank = 1
    while heap:
        count, candidate = heapq.heappop(heap)
        print(f"Rank {rank}: {candidate} with {-count} votes")
        rank += 1


def menu():
    """Interactive menu loop."""
    while True:
        print("\n--- Vote Management System ---")
        print("1. Register Candidate")
        print("2. Cast Vote")
        print("3. Display Results")
        print("4. Save Results to JSON")
        print("5. Display Ranking (Priority Queue)")
        print("6. Exit")

        choice = input("Choose an option: ").strip()
        if choice == "1":
            register_candidate()
        elif choice == "2":
            cast_vote()
        elif choice == "3":
            display_results()
        elif choice == "4":
            save_results()
        elif choice == "5":
            display_ranking_priority_queue()
        elif choice == "6":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


# Run interactive program
if __name__ == "__main__":
    menu()
