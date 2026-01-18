import random

# titre du jeu
print("=" * 50)
print(" Bonjour dans le jeu : Rock-Paper-Scissors ✊ ✋ ✌️")
print("=" * 50)

Stop = True
while Stop:
    # Demander le nom du joueur
    nom = input("Veuillez entrer un nom : ")
    while not nom.strip():
        print("=" * 50)
        nom = input("Erreur : Veuillez entrer un nom valide (pas vide) : ")

    print("=" * 50)
    print(f"Bienvenue {nom} !")
    score_Joueur = 0
    score_ordinateur = 0
    nombre_matches = 0

    # boucle principale de jeu
    continuer = True
    while continuer:
        print("=" * 50)
        print(f"Score : {nom} {score_Joueur} - {score_ordinateur} Ordinateur")
        print("=" * 50)
        print("Choisissez : ")
        print("1- Pierre")
        print("2- Papier")
        print("3- Ciseaux")
        print("0- Quitter")

        # Choix du joueur
        choix_joueur = input("Choisissez un nombre (0/1/2/3) : ")
        if choix_joueur == "0":
            continuer = False
            break

        # Vérification si le choix est correct
        if choix_joueur not in ["1", "2", "3"]:
            print("Erreur : Choix invalide ! Veuillez réessayer.")
            continue

        # choix de l'ordinateur
        choix_ordinateur = random.randint(1, 3)

        # conversion des choix en texte
        options = {1: "Pierre", 2: "Papier", 3: "Ciseaux"}
        choix_joueur = int(choix_joueur)
        nombre_matches += 1

        print(f"{nom} : {options[choix_joueur]}")
        print(f"Ordinateur : {options[choix_ordinateur]}")

        # Déterminer le gagnant
        if choix_joueur == choix_ordinateur:
            print("ÉGALITÉ")
        elif (choix_joueur == 1 and choix_ordinateur == 3) or \
             (choix_joueur == 2 and choix_ordinateur == 1) or \
             (choix_joueur == 3 and choix_ordinateur == 2):
            print(f"{nom} gagne le match, bravo !")
            score_Joueur += 1
        else:
            print("Pas mal ! L'ordinateur gagne ce match. Réessayez la prochaine fois, bon courage !")
            score_ordinateur += 1

    # Affichage des résultats finaux
    print("=" * 50)
    print("Résultat Final du match !")
    print("=" * 50)
    print(f"Matchs joués : {nombre_matches}")
    print(f"{nom} : {score_Joueur} victoire(s)")
    print(f"Ordinateur : {score_ordinateur} victoire(s)")
    if score_Joueur > score_ordinateur:
        print(f"{nom} est le Champion ! 🏆")
    elif score_ordinateur > score_Joueur:
        print("Ordinateur est le Champion ! Retentez votre chance !")
    else:
        print("Match NUL ⚖️")

    # Demander si on continue
    r_continue = input("Voulez-vous continuer ? (oui / non) : ")
    if r_continue.lower() in ["non", "n"]:
        Stop = False

print("=" * 50)
print(f"Merci et Au revoir [{nom}] ! À bientôt !")
print("=" * 50)
