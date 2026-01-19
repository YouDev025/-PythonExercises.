import random

# Le titre du jeu
print("=" * 50)
print(" BIENVENUE AU JEU DE MORPION (X / O) ")
print("=" * 50)
joueur1 = "X"
print("=" * 50)

# Demander les noms des joueurs
joueur1 = input("\nNom du Joueur 1 (X) : ")
while not joueur1.strip():
    joueur1 = input("Erreur : Veuillez entrer un nom valide : ")

joueur2 = input("Nom du Joueur 2 (O) : ")
while not joueur2.strip():
    joueur2 = input("Erreur : Veuillez entrer un nom valide : ")

print("=" * 50)
print(f"⚔  {joueur1} (X) VS {joueur2} (O)")
print("=" * 50)

# Scores
score_joueur1 = 0
score_joueur2 = 0
matchs_nuls = 0

# Boucle pour rejouer
continuer = True

while continuer:
    # Initialiser la grille (positions 1-9)
    grille = [" ", " ", " ", " ", " ", " ", " ", " ", " "]
    joueur_actuel = "X"
    partie_terminee = False
    coups_joues = 0

    print("\n Positions de la grille :")
    print("  1 | 2 | 3")
    print(" -----------")
    print("  4 | 5 | 6")
    print(" -----------")
    print("  7 | 8 | 9")
    print()

    # Boucle principale du jeu
    while not partie_terminee and coups_joues < 9:
        # Afficher la grille actuelle
        print("\n🎮 Grille de jeu :")
        print(f"  {grille[0]} | {grille[1]} | {grille[2]}")
        print(" -----------")
        print(f"  {grille[3]} | {grille[4]} | {grille[5]}")
        print(" -----------")
        print(f"  {grille[6]} | {grille[7]} | {grille[8]}")
        print()

        # Déterminer le nom du joueur actuel
        nom_actuel = joueur1 if joueur_actuel == "X" else joueur2

        # Demander la position
        print(f"Tour de {nom_actuel} ({joueur_actuel})")
        position = input("Choisissez une position (1-9) : ")

        # Vérification complète de la position
        # 1. Vérifier si l'entrée est vide
        if not position.strip():
            print("\n️  Erreur : Vous n'avez rien entré ! Veuillez choisir une position.")
            continue

        # 2. Vérifier si c'est un chiffre
        if not position.isdigit():
            print("\n️  Erreur : Veuillez entrer un CHIFFRE entre 1 et 9 !")
            continue

        # 3. Convertir en entier
        position = int(position)

        # 4. Vérifier si la position est entre 1 et 9
        if position < 1 or position > 9:
            print("\n️  Erreur : La position doit être entre 1 et 9 !")
            continue

        # 5. Vérifier si la case est déjà occupée
        if grille[position - 1] != " ":
            print("\n Erreur : Cette case est déjà occupée ! Choisissez une autre position.")
            continue

        # Placer le symbole sur la grille
        grille[position - 1] = joueur_actuel
        coups_joues += 1

        # Vérifier s'il y a un gagnant
        # Combinaisons gagnantes
        combinaisons = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Lignes
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Colonnes
            [0, 4, 8], [2, 4, 6]  # Diagonales
        ]

        for combo in combinaisons:
            if grille[combo[0]] == grille[combo[1]] == grille[combo[2]] == joueur_actuel:
                partie_terminee = True
                # Afficher la grille finale
                print("\n🎮 Grille finale :")
                print(f"  {grille[0]} | {grille[1]} | {grille[2]}")
                print(" -----------")
                print(f"  {grille[3]} | {grille[4]} | {grille[5]}")
                print(" -----------")
                print(f"  {grille[6]} | {grille[7]} | {grille[8]}")
                print()
                print("=" * 50)
                print(f" {nom_actuel} ({joueur_actuel}) a gagné ! 🎉")
                print("=" * 50)

                # Mettre à jour le score
                if joueur_actuel == "X":
                    score_joueur1 += 1
                else:
                    score_joueur2 += 1
                break

        # Changer de joueur
        if not partie_terminee:
            joueur_actuel = "O" if joueur_actuel == "X" else "X"

    # Vérifier si c'est un match nul
    if not partie_terminee and coups_joues == 9:
        print("\n Grille finale :")
        print(f"  {grille[0]} | {grille[1]} | {grille[2]}")
        print(" -----------")
        print(f"  {grille[3]} | {grille[4]} | {grille[5]}")
        print(" -----------")
        print(f"  {grille[6]} | {grille[7]} | {grille[8]}")
        print()
        print("=" * 50)
        print(" Match nul ! Aucun gagnant.")
        print("=" * 50)
        matchs_nuls += 1

    # Afficher les scores
    print("\n SCORES :")
    print(f"{joueur1} (X) : {score_joueur1}")
    print(f"{joueur2} (O) : {score_joueur2}")
    print(f"Matchs nuls : {matchs_nuls}")

    # Demander si les joueurs veulent rejouer
    rejouer = input("\nVoulez-vous rejouer ? (oui/non) : ")
    if rejouer.lower() in ["non", "n"]:
        continuer = False

# Message de fin
print("\n" + "=" * 50)
print(" RÉSULTATS FINAUX :")
print(f"{joueur1} (X) : {score_joueur1} victoire(s)")
print(f"{joueur2} (O) : {score_joueur2} victoire(s)")
print(f"Matchs nuls : {matchs_nuls}")

if score_joueur1 > score_joueur2:
    print(f"\n {joueur1} remporte la série ! CHAMPION !")
elif score_joueur2 > score_joueur1:
    print(f"\n {joueur2} remporte la série ! CHAMPION !")
else:
    print("\n Égalité parfaite ! Bravo à tous les deux !")

print(f"\n Merci d'avoir joué ! À bientôt !")
print("=" * 50)