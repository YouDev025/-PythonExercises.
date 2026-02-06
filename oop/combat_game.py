"""
RPG Combat Game - Object-Oriented Python Program
Description: A turn-based combat game demonstrating OOP principles
"""

import random
import time
from typing import List, Optional


class Character:
    """Base class for all characters"""

    def __init__(self, name: str, health: int, attack: int, defense: int):
        self._name = name
        self._max_health = health
        self._health = health
        self._attack = attack
        self._defense = defense
        self._is_alive = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def health(self) -> int:
        return self._health

    @property
    def max_health(self) -> int:
        return self._max_health

    @property
    def attack(self) -> int:
        return self._attack

    @property
    def defense(self) -> int:
        return self._defense

    @property
    def is_alive(self) -> bool:
        return self._is_alive

    def take_damage(self, damage: int):
        """Character takes damage"""
        actual_damage = max(0, damage - self._defense)
        self._health -= actual_damage

        if self._health <= 0:
            self._health = 0
            self._is_alive = False
            print(f"{self._name} has been defeated!")

        return actual_damage

    def heal(self, amount: int):
        """Heals the character"""
        if self._is_alive:
            self._health = min(self._health + amount, self._max_health)

    def basic_attack(self, target: 'Character') -> int:
        """Performs a basic attack on target"""
        if not self._is_alive:
            print(f"{self._name} cannot attack (KO)!")
            return 0

        damage = random.randint(self._attack - 5, self._attack + 5)
        damage_dealt = target.take_damage(damage)

        print(f"{self._name} attacks {target.name} and deals {damage_dealt} damage!")
        return damage_dealt

    def display_status(self):
        """Displays character status"""
        health_bar = self._create_health_bar()
        status = "ALIVE" if self._is_alive else "KO"
        print(f"{self._name}: {health_bar} {self._health}/{self._max_health} HP [{status}]")

    def _create_health_bar(self) -> str:
        """Creates a visual health bar"""
        bar_length = 20
        percentage = self._health / self._max_health
        filled = int(bar_length * percentage)
        empty = bar_length - filled
        return "[" + "=" * filled + " " * empty + "]"

    def __str__(self) -> str:
        return f"{self._name} (HP: {self._health}/{self._max_health})"


class Warrior(Character):
    """Warrior class - High attack and defense"""

    def __init__(self, name: str):
        super().__init__(name, health=150, attack=30, defense=10)
        self._rage = 0

    def special_ability(self, target: 'Character'):
        """Power Strike - Deals extra damage"""
        if not self._is_alive:
            print(f"{self._name} cannot use ability (KO)!")
            return 0

        print(f"{self._name} uses POWER STRIKE!")
        damage = random.randint(self._attack + 10, self._attack + 25)
        damage_dealt = target.take_damage(damage)
        print(f"Deals {damage_dealt} critical damage!")
        return damage_dealt


class Mage(Character):
    """Mage class - Powerful magic but fragile"""

    def __init__(self, name: str):
        super().__init__(name, health=100, attack=40, defense=5)
        self._mana = 100
        self._max_mana = 100

    @property
    def mana(self) -> int:
        return self._mana

    def special_ability(self, target: 'Character'):
        """Fireball - Powerful magic attack"""
        if not self._is_alive:
            print(f"{self._name} cannot use ability (KO)!")
            return 0

        mana_cost = 30
        if self._mana < mana_cost:
            print(f"{self._name} doesn't have enough mana! ({self._mana}/{mana_cost})")
            return 0

        self._mana -= mana_cost
        print(f"{self._name} casts FIREBALL! (Mana: {self._mana}/{self._max_mana})")
        damage = random.randint(self._attack + 15, self._attack + 30)
        damage_dealt = target.take_damage(damage)
        print(f"Deals {damage_dealt} magic damage!")
        return damage_dealt

    def restore_mana(self, amount: int):
        """Restores mana"""
        self._mana = min(self._mana + amount, self._max_mana)

    def display_status(self):
        """Displays status including mana"""
        super().display_status()
        print(f"  Mana: {self._mana}/{self._max_mana}")


class Archer(Character):
    """Archer class - Balanced with precise attacks"""

    def __init__(self, name: str):
        super().__init__(name, health=120, attack=35, defense=7)
        self._special_arrows = 3

    @property
    def special_arrows(self) -> int:
        return self._special_arrows

    def special_ability(self, target: 'Character'):
        """Precise Shot - Ignores defense"""
        if not self._is_alive:
            print(f"{self._name} cannot use ability (KO)!")
            return 0

        if self._special_arrows <= 0:
            print(f"{self._name} has no special arrows left!")
            return 0

        self._special_arrows -= 1
        print(f"{self._name} uses PRECISE SHOT! (Arrows remaining: {self._special_arrows})")

        # Temporarily ignore target's defense
        original_defense = target._defense
        target._defense = 0

        damage = random.randint(self._attack + 5, self._attack + 20)
        damage_dealt = target.take_damage(damage)

        target._defense = original_defense
        print(f"Deals {damage_dealt} precise damage!")
        return damage_dealt

    def display_status(self):
        """Displays status including arrows"""
        super().display_status()
        print(f"  Special Arrows: {self._special_arrows}")


class Potion:
    """Class for healing potions"""

    def __init__(self, name: str, healing: int):
        self._name = name
        self._healing = healing

    @property
    def name(self) -> str:
        return self._name

    @property
    def healing(self) -> int:
        return self._healing

    def use(self, target: Character):
        """Uses the potion on a target"""
        if not target.is_alive:
            print(f"{target.name} is KO, potion is ineffective!")
            return False

        target.heal(self._healing)
        print(f"{target.name} uses {self._name} and recovers {self._healing} HP!")
        return True


class Inventory:
    """Manages player inventory"""

    def __init__(self):
        self._potions: List[Potion] = []
        self._add_starting_potions()

    def _add_starting_potions(self):
        """Adds starting potions"""
        self._potions.append(Potion("Small Potion", 30))
        self._potions.append(Potion("Medium Potion", 50))
        self._potions.append(Potion("Large Potion", 80))

    def add_potion(self, potion: Potion):
        """Adds a potion to inventory"""
        self._potions.append(potion)

    def display_potions(self):
        """Displays available potions"""
        if not self._potions:
            print("No potions available!")
            return

        print("\nAVAILABLE POTIONS:")
        for i, potion in enumerate(self._potions, 1):
            print(f"{i}. {potion.name} (Heals: {potion.healing} HP)")

    def use_potion(self, index: int, target: Character) -> bool:
        """Uses a potion by index"""
        if 0 <= index < len(self._potions):
            potion = self._potions[index]
            if potion.use(target):
                self._potions.pop(index)
                return True
        return False

    def potion_count(self) -> int:
        """Returns number of potions"""
        return len(self._potions)


class Battle:
    """Manages battle logic"""

    def __init__(self, player: Character, enemies: List[Character], inventory: Inventory):
        self._player = player
        self._enemies = enemies
        self._inventory = inventory
        self._turn = 1

    def start(self):
        """Starts the battle"""
        print("\n" + "=" * 60)
        print("  BATTLE BEGINS!")
        print("=" * 60)

        while self._player.is_alive and any(e.is_alive for e in self._enemies):
            self._game_turn()
            self._turn += 1
            time.sleep(1)

        self._end_battle()

    def _game_turn(self):
        """Manages a game turn"""
        print(f"\n{'=' * 60}")
        print(f"  TURN {self._turn}")
        print(f"{'=' * 60}")

        # Display statuses
        self._display_statuses()

        # Player turn
        if self._player.is_alive:
            self._player_turn()

        # Enemy turns
        for enemy in self._enemies:
            if enemy.is_alive and self._player.is_alive:
                time.sleep(0.5)
                self._enemy_turn(enemy)

    def _display_statuses(self):
        """Displays status of all combatants"""
        print("\nYOUR TEAM:")
        self._player.display_status()

        print("\nENEMIES:")
        for enemy in self._enemies:
            enemy.display_status()

    def _player_turn(self):
        """Manages player turn"""
        print(f"\n--- {self._player.name}'s Turn ---")

        while True:
            print("\nWHAT TO DO?")
            print("1. Basic Attack")
            print("2. Special Ability")
            print("3. Use Potion")

            choice = input("Your choice: ").strip()

            if choice == "1":
                target = self._choose_target()
                if target:
                    self._player.basic_attack(target)
                    break

            elif choice == "2":
                target = self._choose_target()
                if target:
                    self._player.special_ability(target)
                    break

            elif choice == "3":
                if self._use_player_potion():
                    break

            else:
                print("Invalid choice!")

    def _choose_target(self) -> Optional[Character]:
        """Allows player to choose a target"""
        alive_enemies = [e for e in self._enemies if e.is_alive]

        if not alive_enemies:
            return None

        if len(alive_enemies) == 1:
            return alive_enemies[0]

        print("\nChoose target:")
        for i, enemy in enumerate(alive_enemies, 1):
            print(f"{i}. {enemy}")

        while True:
            try:
                choice = int(input("Target: ").strip())
                if 1 <= choice <= len(alive_enemies):
                    return alive_enemies[choice - 1]
                else:
                    print("Invalid choice!")
            except ValueError:
                print("Enter a number!")

    def _use_player_potion(self) -> bool:
        """Manages potion usage"""
        if self._inventory.potion_count() == 0:
            print("You have no potions!")
            return False

        self._inventory.display_potions()

        try:
            choice = int(input("\nChoose a potion (0 to cancel): ").strip())
            if choice == 0:
                return False
            if self._inventory.use_potion(choice - 1, self._player):
                return True
        except (ValueError, IndexError):
            print("Invalid choice!")

        return False

    def _enemy_turn(self, enemy: Character):
        """Manages enemy turn"""
        print(f"\n--- {enemy.name}'s Turn ---")

        # Enemy attacks or uses ability randomly
        if random.random() < 0.3:  # 30% chance to use ability
            enemy.special_ability(self._player)
        else:
            enemy.basic_attack(self._player)

    def _end_battle(self):
        """Manages battle end"""
        print("\n" + "=" * 60)
        if self._player.is_alive:
            print("  VICTORY!")
            print(f"  {self._player.name} defeated all enemies!")
        else:
            print("  DEFEAT!")
            print(f"  {self._player.name} has been defeated...")
        print("=" * 60)


class Game:
    """Main game class"""

    def __init__(self):
        self._player: Optional[Character] = None
        self._inventory = Inventory()

    def start(self):
        """Starts the game"""
        self._display_intro()
        self._create_character()
        self._main_menu()

    def _display_intro(self):
        """Displays introduction"""
        print("\n" + "=" * 60)
        print("  RPG COMBAT GAME")
        print("  Object-Oriented Programming Demonstration")
        print("=" * 60)

    def _create_character(self):
        """Allows player to create their character"""
        print("\nCHARACTER CREATION")
        print("-" * 60)

        name = input("Enter your hero's name: ").strip() or "Hero"

        print("\nChoose your class:")
        print("1. Warrior (High HP, strong defense)")
        print("2. Mage (Powerful magic attacks)")
        print("3. Archer (Balanced, precise attacks)")

        while True:
            choice = input("\nYour choice: ").strip()

            if choice == "1":
                self._player = Warrior(name)
                print(f"\n{name} the Warrior has been created!")
                break
            elif choice == "2":
                self._player = Mage(name)
                print(f"\n{name} the Mage has been created!")
                break
            elif choice == "3":
                self._player = Archer(name)
                print(f"\n{name} the Archer has been created!")
                break
            else:
                print("Invalid choice!")

        self._player.display_status()

    def _main_menu(self):
        """Displays main menu"""
        while True:
            print("\n" + "=" * 60)
            print("  MAIN MENU")
            print("=" * 60)
            print("1. Easy Battle")
            print("2. Medium Battle")
            print("3. Hard Battle")
            print("4. View My Character")
            print("5. Quit")
            print("-" * 60)

            choice = input("Your choice: ").strip()

            if choice == "1":
                self._start_battle("easy")
            elif choice == "2":
                self._start_battle("medium")
            elif choice == "3":
                self._start_battle("hard")
            elif choice == "4":
                self._display_character()
            elif choice == "5":
                print("\nThanks for playing!")
                break
            else:
                print("Invalid choice!")

    def _start_battle(self, difficulty: str):
        """Starts a battle based on difficulty"""
        enemies = self._create_enemies(difficulty)

        # Restore player before battle
        self._player.heal(self._player.max_health)
        if isinstance(self._player, Mage):
            self._player.restore_mana(100)

        battle = Battle(self._player, enemies, self._inventory)
        battle.start()

        # Reward after victory
        if self._player.is_alive:
            self._inventory.add_potion(Potion("Reward Potion", 50))
            print("\nYou received a Reward Potion!")

    def _create_enemies(self, difficulty: str) -> List[Character]:
        """Creates enemies based on difficulty"""
        if difficulty == "easy":
            return [Warrior("Goblin")]
        elif difficulty == "medium":
            return [Warrior("Orc"), Archer("Bandit")]
        else:  # hard
            return [Warrior("Dark Knight"), Mage("Evil Sorcerer"), Archer("Assassin")]

    def _display_character(self):
        """Displays character information"""
        print("\n" + "=" * 60)
        print("  YOUR CHARACTER")
        print("=" * 60)
        self._player.display_status()
        self._inventory.display_potions()


def main():
    """Main function"""
    game = Game()
    game.start()


if __name__ == "__main__":
    main()