# Programme de calcul de moyenne et statistiques

# Fonction de moyenne
def moyenne(nombres: list[float]) -> float:
    if not nombres:
        raise ValueError("La liste ne peut pas être vide")
    return sum(nombres) / len(nombres)

# Fonction somme
def somme(nombres: list[float]) -> float:
    return sum(nombres)

# Fonction maximum
def maximum(nombres: list[float]) -> float:
    return max(nombres)

# Fonction minimum
def minimum(nombres: list[float]) -> float:
    return min(nombres)

# Fonction tri croissant
def tri_croissant(nombres: list[float]) -> list[float]:
    return sorted(nombres)

# Fonction tri décroissant
def tri_decroissant(nombres: list[float]) -> list[float]:
    return sorted(nombres, reverse=True)

# Saisie interactive des nombres
def saisir_nombres() -> list[float]:
    nombres = []
    print("\nEntrez les nombres (tapez 'fin' pour terminer):")
    while True:
        entree = input(f"Nombre {len(nombres) + 1}: ").strip().lower()
        if entree == "fin":
            if nombres:
                return nombres
            else:
                print("Vous devez entrer au moins un nombre!")
                continue
        try:
            nombre = float(entree)
            nombres.append(nombre)
            print(f"Ajouté : {nombre:.2f}")
        except ValueError:
            print("Erreur : Veuillez entrer un nombre valide ou 'fin'.")

# Affiche le menu principal
def afficher_menu() -> None:
    print("-" * 50)
    print("MENU PRINCIPAL")
    print("-" * 50)
    print("1. Calculer une moyenne")
    print("2. Calculer la somme")
    print("3. Trouver le maximum")
    print("4. Trouver le minimum")
    print("5. Trier du plus petit au plus grand")
    print("6. Trier du plus grand au plus petit")
    print("7. Quitter")
    print("-" * 50)

# Fonction principale
def main() -> None:
    while True:
        afficher_menu()
        try:
            choix = int(input("Choix de la commande : "))
        except ValueError:
            print("Erreur : Veuillez entrer un nombre valide (1 à 7).")
            continue

        if choix in [1, 2, 3, 4, 5, 6]:
            nombres = saisir_nombres()

            if choix == 1:
                print("-" * 50)
                print(f"Moyenne : {moyenne(nombres):.2f}")
            elif choix == 2:
                print("-" * 50)
                print(f"Somme : {somme(nombres):.2f}")
            elif choix == 3:
                print("-" * 50)
                print(f"Maximum : {maximum(nombres):.2f}")
            elif choix == 4:
                print("-" * 50)
                print(f"Minimum : {minimum(nombres):.2f}")
            elif choix == 5:
                print("-" * 50)
                print(f"Tri croissant : {tri_croissant(nombres)}")
            elif choix == 6:
                print("-" * 50)
                print(f"Tri décroissant : {tri_decroissant(nombres)}")

        elif choix == 7:
            confirmation = input("Êtes-vous sûr de vouloir quitter ? (oui/o pour confirmer) : ").strip().lower()
            if confirmation in ["oui", "o"]:
                print("Merci d'avoir utilisé le programme. Au revoir !")
                break
            else:
                print("Retour au menu principal.")
        else:
            print("Option invalide. Choisissez entre 1 et 7.")

if __name__ == "__main__":
    main()
