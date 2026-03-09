"""
card_game.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A command-line card game simulator built with Python OOP.

Game Rules  –  "High Card Showdown"
  • Each player is dealt a hand of N cards (default 5).
  • Each round, every player plays their highest-value card.
  • The player who plays the highest card wins the round and
    scores a point.  Ties are possible (no point awarded).
  • After all rounds the player with the most points wins.

Card Values  (low → high)
  2 3 4 5 6 7 8 9 10 J Q K A
Suits have no tiebreaking role – a true tie scores 0 points.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import random
from typing import Optional


# ─────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────
SUITS  = ("♠ Spades", "♥ Hearts", "♦ Diamonds", "♣ Clubs")
RANKS  = ("2", "3", "4", "5", "6", "7", "8", "9", "10",
          "J", "Q", "K", "A")
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}  # 2→2 … A→14

SUIT_SYMBOLS = {
    "♠ Spades":   "♠",
    "♥ Hearts":   "♥",
    "♦ Diamonds": "♦",
    "♣ Clubs":    "♣",
}

# ANSI colour codes
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


# ─────────────────────────────────────────────────────────────
#  CARD
# ─────────────────────────────────────────────────────────────
class Card:
    """Represents a single playing card."""

    def __init__(self, suit: str, rank: str):
        if suit not in SUITS:
            raise ValueError(f"Invalid suit: '{suit}'.")
        if rank not in RANKS:
            raise ValueError(f"Invalid rank: '{rank}'.")
        self._suit  = suit
        self._rank  = rank
        self._value = RANK_VALUES[rank]

    # ── getters ──────────────────────────────────────────────
    @property
    def suit(self) -> str:
        return self._suit

    @property
    def rank(self) -> str:
        return self._rank

    @property
    def value(self) -> int:
        return self._value

    # ── comparisons ──────────────────────────────────────────
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Card) and self._value == other._value

    def __lt__(self, other: "Card") -> bool:
        return self._value < other._value

    def __gt__(self, other: "Card") -> bool:
        return self._value > other._value

    # ── display ──────────────────────────────────────────────
    def short(self) -> str:
        """Compact label: A♠  10♥  3♦"""
        sym = SUIT_SYMBOLS[self._suit]
        col = RED if "♥" in sym or "♦" in sym else ""
        return f"{col}{self._rank}{sym}{RESET}"

    def card_art(self) -> list[str]:
        """7-line ASCII card face."""
        sym = SUIT_SYMBOLS[self._suit]
        col = RED if "♥" in sym or "♦" in sym else ""
        r   = self._rank.ljust(2)        # left-aligned rank (10 needs 2 chars)
        r2  = self._rank.rjust(2)        # right-aligned for bottom
        return [
            f"{col}┌─────────┐{RESET}",
            f"{col}│ {r}      │{RESET}",
            f"{col}│         │{RESET}",
            f"{col}│    {sym}    │{RESET}",
            f"{col}│         │{RESET}",
            f"{col}│      {r2} │{RESET}",
            f"{col}└─────────┘{RESET}",
        ]

    def __str__(self) -> str:
        return f"{self._rank} of {self._suit}"

    def __repr__(self) -> str:
        return f"Card({self._rank!r}, {self._suit!r})"


# ─────────────────────────────────────────────────────────────
#  DECK
# ─────────────────────────────────────────────────────────────
class Deck:
    """A standard 52-card deck."""

    def __init__(self):
        self._cards: list[Card] = [
            Card(suit, rank)
            for suit in SUITS
            for rank in RANKS
        ]

    @property
    def remaining(self) -> int:
        return len(self._cards)

    def shuffle(self):
        random.shuffle(self._cards)

    def deal(self, n: int = 1) -> list[Card]:
        if n < 1:
            raise ValueError("Must deal at least 1 card.")
        if n > self.remaining:
            raise ValueError(
                f"Cannot deal {n} cards — only {self.remaining} remain."
            )
        dealt, self._cards = self._cards[:n], self._cards[n:]
        return dealt

    def reset(self):
        self.__init__()

    def __len__(self) -> int:
        return self.remaining

    def __str__(self) -> str:
        return f"Deck({self.remaining} cards remaining)"


# ─────────────────────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────────────────────
class Player:
    """A game participant who holds and plays cards."""

    def __init__(self, name: str):
        if not name.strip():
            raise ValueError("Player name cannot be empty.")
        self._name:   str        = name.strip()
        self._hand:   list[Card] = []
        self._score:  int        = 0

    # ── getters ──────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self._name

    @property
    def hand(self) -> list[Card]:
        return list(self._hand)          # return copy – encapsulation

    @property
    def score(self) -> int:
        return self._score

    @property
    def hand_size(self) -> int:
        return len(self._hand)

    # ── hand management ──────────────────────────────────────
    def receive(self, cards: list[Card]):
        self._hand.extend(cards)

    def play_best_card(self) -> Optional[Card]:
        """Remove and return the highest-value card from hand."""
        if not self._hand:
            return None
        best = max(self._hand, key=lambda c: c.value)
        self._hand.remove(best)
        return best

    def clear_hand(self):
        self._hand.clear()

    def add_point(self):
        self._score += 1

    def reset_score(self):
        self._score = 0

    # ── display ──────────────────────────────────────────────
    def display_hand(self):
        """Print all cards in hand as side-by-side ASCII art."""
        if not self._hand:
            print(f"  {self._name}'s hand is empty.")
            return

        # Sort hand high → low for display
        sorted_hand = sorted(self._hand, key=lambda c: c.value, reverse=True)
        rows = [c.card_art() for c in sorted_hand]

        print(f"\n  {BOLD}{CYAN}{self._name}'s Hand:{RESET}")
        for line_idx in range(7):          # each card art is 7 lines tall
            print("  " + "  ".join(row[line_idx] for row in rows))

        # compact label row
        labels = [f"  {c.short():<6}" for c in sorted_hand]
        print("  " + " ".join(labels))

    def __str__(self) -> str:
        return f"{self._name} (score: {self._score}, cards: {self.hand_size})"


# ─────────────────────────────────────────────────────────────
#  GAME
# ─────────────────────────────────────────────────────────────
class Game:
    """
    Orchestrates a full session of High Card Showdown.

    Flow
    ────
    1. Collect player names.
    2. Shuffle & deal N cards each.
    3. Play N rounds: each player reveals their best card;
       highest card wins the round.
    4. Tally scores and crown the overall winner.
    5. Offer a rematch.
    """

    MIN_PLAYERS    = 2
    MAX_PLAYERS    = 6
    DEFAULT_CARDS  = 5

    def __init__(self):
        self._deck:    Deck         = Deck()
        self._players: list[Player] = []

    # ── setup ────────────────────────────────────────────────
    def _setup_players(self):
        _header("Player Setup")
        n = _input_int(
            f"How many players? ({self.MIN_PLAYERS}–{self.MAX_PLAYERS}): ",
            lo=self.MIN_PLAYERS,
            hi=self.MAX_PLAYERS,
        )
        self._players.clear()
        names_used: set[str] = set()
        for i in range(1, n + 1):
            while True:
                raw = _inp(f"  Player {i} name: ")
                if not raw:
                    print("  ✖  Name cannot be blank.")
                elif raw.lower() in names_used:
                    print(f"  ✖  '{raw}' is already taken.")
                else:
                    self._players.append(Player(raw))
                    names_used.add(raw.lower())
                    break

    def _deal_cards(self, cards_each: int):
        self._deck.reset()
        self._deck.shuffle()
        for p in self._players:
            p.clear_hand()
            p.receive(self._deck.deal(cards_each))

    # ── round logic ──────────────────────────────────────────
    def _play_round(self, round_num: int, total_rounds: int):
        _sep("─")
        print(
            f"  {BOLD}Round {round_num} / {total_rounds}{RESET}  "
            f"{DIM}({total_rounds - round_num} round(s) remaining after this){RESET}"
        )
        _sep("─")

        plays: list[tuple[Player, Card]] = []
        for p in self._players:
            card = p.play_best_card()
            if card:
                print(f"  {p.name:<18} plays  {card.short()}")
                plays.append((p, card))

        # Find the maximum card value played this round
        max_val = max(c.value for _, c in plays)
        winners = [p for p, c in plays if c.value == max_val]

        print()
        if len(winners) == 1:
            winners[0].add_point()
            card_played = next(c for p, c in plays if p == winners[0])
            print(
                f"  {GREEN}{BOLD}🏆  {winners[0].name} wins the round "
                f"with {card_played.short()}{GREEN}!{RESET}"
            )
        else:
            names = "  &  ".join(w.name for w in winners)
            print(f"  {YELLOW}⚡  Tie between {names} — no point awarded.{RESET}")

    # ── scoreboard ───────────────────────────────────────────
    def _display_scoreboard(self):
        print(f"\n  {BOLD}{'─'*38}{RESET}")
        print(f"  {BOLD}{'Player':<20}{'Score':>8}{'Cards Left':>10}{RESET}")
        print(f"  {'─'*38}")
        ranked = sorted(self._players, key=lambda p: p.score, reverse=True)
        for p in ranked:
            print(f"  {p.name:<20}{p.score:>8}{p.hand_size:>10}")
        print(f"  {'─'*38}\n")

    def _announce_winner(self):
        _header("🎉  Game Over  🎉")
        top_score = max(p.score for p in self._players)
        champions = [p for p in self._players if p.score == top_score]

        if len(champions) == 1:
            print(
                f"  {GREEN}{BOLD}Champion: {champions[0].name}  "
                f"with {top_score} point(s)!{RESET}\n"
            )
        else:
            names = ", ".join(c.name for c in champions)
            print(
                f"  {YELLOW}{BOLD}It's a tie!  "
                f"Joint champions: {names}  ({top_score} pts each){RESET}\n"
            )
        self._display_scoreboard()

    # ── main entry point ─────────────────────────────────────
    def run(self):
        _banner()

        while True:
            # 1. Player setup
            self._setup_players()
            for p in self._players:
                p.reset_score()

            # 2. Choose hand size
            max_cards = min(
                self.DEFAULT_CARDS,
                52 // len(self._players),
            )
            cards_each = _input_int(
                f"Cards per player? (1–{max_cards}): ",
                lo=1,
                hi=max_cards,
            )

            # 3. Deal
            self._deal_cards(cards_each)
            print(f"\n  {GREEN}✔  {cards_each} card(s) dealt to each player.{RESET}")

            # 4. Show hands
            show = _inp("\nReveal all hands before playing? (y/n): ").lower()
            if show == "y":
                for p in self._players:
                    p.display_hand()
                input(f"\n  {DIM}Press Enter to start the game…{RESET}")

            # 5. Play rounds
            total_rounds = cards_each
            for rnd in range(1, total_rounds + 1):
                input(f"\n  {DIM}Press Enter to play Round {rnd}…{RESET}")
                self._play_round(rnd, total_rounds)
                self._display_scoreboard()

            # 6. Winner
            self._announce_winner()

            # 7. Rematch?
            again = _inp("Play again? (y/n): ").lower()
            if again != "y":
                print(
                    f"\n  {CYAN}Thanks for playing High Card Showdown!  "
                    f"Goodbye 👋{RESET}\n"
                )
                break


# ─────────────────────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────────────────────
def _sep(char: str = "═", width: int = 56):
    print(char * width)

def _header(title: str):
    _sep()
    print(f"  {BOLD}{title}{RESET}")
    _sep()

def _inp(prompt: str) -> str:
    return input(f"  {prompt}").strip()

def _input_int(prompt: str, lo: int = 1, hi: int = 100) -> int:
    while True:
        raw = _inp(prompt)
        if raw.isdigit() and lo <= int(raw) <= hi:
            return int(raw)
        print(f"  ✖  Please enter a whole number between {lo} and {hi}.")

def _banner():
    print()
    _sep("═")
    print(f"""  {BOLD}{YELLOW}
    ██╗  ██╗██╗ ██████╗ ██╗  ██╗
    ██║  ██║██║██╔════╝ ██║  ██║
    ███████║██║██║  ███╗███████║
    ██╔══██║██║██║   ██║██╔══██║
    ██║  ██║██║╚██████╔╝██║  ██║
    ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝
    {RESET}""")
    print(f"  {BOLD}     C A R D   S H O W D O W N{RESET}")
    print(f"  {DIM}  Play your best card each round.{RESET}")
    print(f"  {DIM}  Most round wins takes the game.{RESET}\n")
    _sep("═")
    print()


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()