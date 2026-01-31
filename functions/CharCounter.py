#!/usr/bin/env python3
"""
Compteur de Caractères - Character Counter
Un outil simple pour compter les caractères, mots, lignes, etc.
"""

import sys


def count_characters(text):
    """Compte le nombre total de caractères"""
    return len(text)


def count_characters_no_spaces(text):
    """Compte les caractères sans les espaces"""
    return len(text.replace(" ", "").replace("\n", "").replace("\t", ""))


def count_words(text):
    """Compte le nombre de mots"""
    if not text.strip():
        return 0
    return len(text.split())


def count_lines(text):
    """Compte le nombre de lignes"""
    if not text:
        return 0
    return len(text.split('\n'))


def count_sentences(text):
    """Compte le nombre de phrases (approximatif)"""
    if not text.strip():
        return 0

    # Compte les terminaisons de phrases
    count = 0
    for char in ['.', '!', '?']:
        count += text.count(char)

    return count if count > 0 else 1


def count_vowels(text):
    """Compte les voyelles"""
    vowels = "aeiouAEIOUàâäéèêëïîôùûüÿæœÀÂÄÉÈÊËÏÎÔÙÛÜŸÆŒ"
    return sum(1 for char in text if char in vowels)


def count_consonants(text):
    """Compte les consonnes"""
    consonants = "bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZçÇ"
    return sum(1 for char in text if char in consonants)


def count_digits(text):
    """Compte les chiffres"""
    return sum(1 for char in text if char.isdigit())


def count_special_chars(text):
    """Compte les caractères spéciaux"""
    return sum(1 for char in text if not char.isalnum() and not char.isspace())


def analyze_frequency(text):
    """Analyse la fréquence des caractères"""
    frequency = {}
    for char in text:
        if char != '\n' and char != '\r':
            frequency[char] = frequency.get(char, 0) + 1

    # Trier par fréquence décroissante
    sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    return sorted_freq


def display_statistics(text):
    """Affiche toutes les statistiques du texte"""
    print("\n" + "=" * 70)
    print("  STATISTIQUES DU TEXTE / TEXT STATISTICS")
    print("=" * 70)

    print(f"\n  Caractères totaux:              {count_characters(text):,}")
    print(f"  Caractères (sans espaces):      {count_characters_no_spaces(text):,}")
    print(f"  Mots:                           {count_words(text):,}")
    print(f"  Lignes:                         {count_lines(text):,}")
    print(f"  Phrases (approx.):              {count_sentences(text):,}")

    print(f"\n  Voyelles:                       {count_vowels(text):,}")
    print(f"  Consonnes:                      {count_consonants(text):,}")
    print(f"  Chiffres:                       {count_digits(text):,}")
    print(f"  Caractères spéciaux:            {count_special_chars(text):,}")

    # Temps de lecture estimé (environ 200 mots par minute)
    words = count_words(text)
    reading_time = words / 200
    print(f"\n  Temps de lecture estimé:        {reading_time:.1f} minute(s)")

    print("\n" + "=" * 70)


def display_frequency(text, top_n=10):
    """Affiche les caractères les plus fréquents"""
    freq = analyze_frequency(text)

    if not freq:
        print("\nAucun caractère à analyser")
        return

    print("\n" + "=" * 70)
    print(f"  TOP {top_n} CARACTÈRES LES PLUS FRÉQUENTS")
    print("=" * 70)
    print(f"  {'Caractère':<15} {'Occurrences':<15} {'Pourcentage':<15}")
    print("=" * 70)

    total_chars = sum(count for _, count in freq)

    for i, (char, count) in enumerate(freq[:top_n]):
        if char == ' ':
            display_char = '[ESPACE]'
        elif char == '\t':
            display_char = '[TAB]'
        else:
            display_char = char

        percentage = (count / total_chars) * 100
        print(f"  {display_char:<15} {count:<15,} {percentage:>6.2f}%")

    print("=" * 70)


def print_help():
    """Affiche l'aide"""
    print("\n" + "=" * 70)
    print("  COMPTEUR DE CARACTÈRES - COMMANDES DISPONIBLES")
    print("=" * 70)
    print("  text      - Entrer du texte manuellement")
    print("  stats     - Afficher les statistiques du texte actuel")
    print("  freq      - Afficher la fréquence des caractères")
    print("  clear     - Effacer le texte actuel")
    print("  menu      - Afficher le menu principal")
    print("  help      - Afficher cette aide")
    print("  quit      - Quitter le programme")
    print("=" * 70 + "\n")


def display_menu():
    """Affiche le menu principal"""
    print("\n" + "=" * 70)
    print("                    MENU PRINCIPAL")
    print("=" * 70)
    print()
    print("  1. Entrer du texte manuellement")
    print("  2. Afficher les statistiques")
    print("  3. Afficher la fréquence des caractères")
    print("  4. Effacer le texte actuel")
    print("  5. Afficher l'aide")
    print("  6. Quitter")
    print()
    print("=" * 70)
    print("  Vous pouvez aussi taper directement les commandes:")
    print("  text, stats, freq, clear, help, quit")
    print("=" * 70 + "\n")


def main():
    """Fonction principale"""
    current_text = ""

    print("\n" + "=" * 70)
    print("  BIENVENUE AU COMPTEUR DE CARACTÈRES")
    print("  WELCOME TO CHARACTER COUNTER")
    print("=" * 70 + "\n")

    display_menu()

    while True:
        try:
            command = input("compteur> ").strip().lower()

            if not command:
                continue

            # Menu numérique
            if command == '1':
                command = 'text'
            elif command == '2':
                command = 'stats'
            elif command == '3':
                command = 'freq'
            elif command == '4':
                command = 'clear'
            elif command == '5':
                command = 'help'
            elif command == '6':
                command = 'quit'

            if command in ['text', 't']:
                print("\nEntrez votre texte (tapez 'FIN' sur une nouvelle ligne pour terminer):")
                lines = []
                while True:
                    line = input()
                    if line.strip().upper() == 'FIN':
                        break
                    lines.append(line)

                current_text = '\n'.join(lines)

                if current_text:
                    display_statistics(current_text)
                else:
                    print("\nAucun texte entré")

            elif command in ['stats', 's']:
                if current_text:
                    display_statistics(current_text)
                else:
                    print("\nAucun texte à analyser. Utilisez 'text' d'abord.")

            elif command in ['freq', 'frequency']:
                if current_text:
                    try:
                        top_n = input("Nombre de caractères à afficher (défaut: 10): ").strip()
                        top_n = int(top_n) if top_n else 10
                    except ValueError:
                        top_n = 10

                    display_frequency(current_text, top_n)
                else:
                    print("\nAucun texte à analyser. Utilisez 'text' d'abord.")

            elif command in ['clear', 'c']:
                current_text = ""
                print("\nTexte effacé")

            elif command in ['menu', 'm']:
                display_menu()

            elif command in ['help', 'h', '?']:
                print_help()

            elif command in ['quit', 'q', 'exit']:
                print("\nAu revoir! / Goodbye!\n")
                break

            else:
                print(f"\nCommande inconnue: '{command}'. Tapez 'help' pour l'aide.")

        except KeyboardInterrupt:
            print("\n\nAu revoir! / Goodbye!\n")
            break
        except EOFError:
            print("\n\nAu revoir! / Goodbye!\n")
            break


if __name__ == "__main__":
    main()