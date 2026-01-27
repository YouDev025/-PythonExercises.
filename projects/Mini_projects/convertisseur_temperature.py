# Convertisseur de température Celsius ↔ Fahrenheit

# Convertit des degrés Celsius en Fahrenheit
def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9 / 5) + 32

# Convertit des degrés Fahrenheit en Celsius
def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9

# Affiche le menu principal
def afficher_menu() -> None:
    print("-" * 50)
    print("Bienvenue dans le CONVERTISSEUR DE TEMPÉRATURE !")
    print("-" * 50)
    print("1. Celsius → Fahrenheit")
    print("2. Fahrenheit → Celsius")
    print("3. Quitter")
    print("-" * 50)

# Fonction principale du programme
def main() -> None:
    while True:
        afficher_menu()
        try:
            choice = int(input("Choix de la commande : "))
        except ValueError:
            print("Erreur : Veuillez entrer un nombre valide (1, 2 ou 3).")
            continue

        if choice == 1:
            try:
                celsius = float(input("Entrez la température en Celsius : "))
                fahrenheit = celsius_to_fahrenheit(celsius)
                print(f"{celsius:.2f}°C = {fahrenheit:.2f}°F")
            except ValueError:
                print("Erreur : Veuillez entrer un nombre valide !")

        elif choice == 2:
            try:
                fahrenheit = float(input("Entrez la température en Fahrenheit : "))
                celsius = fahrenheit_to_celsius(fahrenheit)
                print(f"{fahrenheit:.2f}°F = {celsius:.2f}°C")
            except ValueError:
                print("Erreur : Veuillez entrer un nombre valide !")

        elif choice == 3:
            while True:
                quitter = input("Êtes-vous sûr de vouloir quitter ? (oui/o pour confirmer, non/n pour annuler) : ").strip().lower()
                if quitter in ["oui", "o"]:
                    print("Merci d'avoir utilisé le convertisseur. Au revoir !")
                    return
                elif quitter in ["non", "n"]:
                    print("Retour au menu principal.")
                    break
                else:
                    print("Réponse invalide. Veuillez entrer 'oui/o' ou 'non/n'.")

        else:
            print("Option invalide. Choisissez 1, 2 ou 3.")

if __name__ == "__main__":
    main()
