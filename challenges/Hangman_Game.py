import random

# Le titre de jeu " Hangman Game = Jeu du Pendu "
print("=" * 50)
print("Bien venu a Hangman!")
print("=" * 50)

# Demander le nom du joueur
nom = input("Veuillez entrer un nom : ")
while not nom.strip():
    nom = input("Erreur : Veuillez entrer un nom valide : ")

print("=" * 50)
print(f"Bonjour Mr.{nom} Bonne chance !")
print("=" * 50)

# Liste de mots à deviner
liste_mots = [
    "python", "ordinateur", "programmation", "clavier", "souris",
    "ecran", "internet", "logiciel", "fichier", "dossier",
    "telephone", "musique", "cinema", "voyage", "montagne",
    "ocean", "soleil", "nature", "jardin", "fleur",
    "livre", "histoire", "science", "mathematiques", "alphabet"
]

# Boucle pour rejouer
Stopme = True

while Stopme:
    # Choisir un mot aléatoire
    mot_secret = random.choice(liste_mots).upper()
    mot_cache = ["_"] * len(mot_secret)
    lettres_trouvees = []
    lettres_fausses = []
    vies = 7
    gagne = False

    print(f"\nLe mot contient {len(mot_secret)} lettres.")
    print(f"Vous avez {vies} vies. Bonne chance !\n")

    # Boucle principale du jeu
    while vies > 0 and not gagne:
        # Afficher le mot caché
        print("\nMot : ", " ".join(mot_cache))
        print(f"Vies restantes : {'❤️ ' * vies}")

        if lettres_fausses:
            print(f"Lettres incorrectes : {', '.join(lettres_fausses)}")

        # Demander une lettre
        lettre = input("\nProposez une lettre : ")

        # Vérification complète de la lettre
        # 1. Vérifier si l'entrée est vide
        if not lettre.strip():
            print("\n️  Erreur : Vous n'avez rien entré ! Veuillez proposer une lettre.")
            continue

        # 2. Convertir en majuscule
        lettre = lettre.upper()

        # 3. Vérifier si c'est une seule lettre
        if len(lettre) != 1:
            print("\n️  Erreur : Veuillez entrer UNE SEULE lettre !")
            continue

        # 4. Vérifier si c'est bien une lettre (pas un chiffre ou symbole)
        if not lettre.isalpha():
            print("\n️  Erreur : Veuillez entrer une LETTRE (pas un chiffre ou symbole) !")
            continue

        # Vérifier si la lettre a déjà été proposée
        if lettre in lettres_trouvees or lettre in lettres_fausses:
            print("\n  Vous avez déjà proposé cette lettre !")
            continue

        # Vérifier si la lettre est dans le mot
        if lettre in mot_secret:
            print(f"\n Bravo ! La lettre '{lettre}' est dans le mot !")
            lettres_trouvees.append(lettre)

            # Révéler toutes les occurrences de la lettre
            for i in range(len(mot_secret)):
                if mot_secret[i] == lettre:
                    mot_cache[i] = lettre

            # Vérifier si le mot est complet
            if "_" not in mot_cache:
                gagne = True
        else:
            print(f"\n Dommage ! La lettre '{lettre}' n'est pas dans le mot.")
            lettres_fausses.append(lettre)
            vies -= 1

    # Afficher le résultat final
    print("\n" + "=" * 50)

    if gagne:
        print(" FÉLICITATIONS ")
        print(f"{nom}, vous avez gagné !")
        print(f"Le mot était : {mot_secret}")
        print(f"Vies restantes : {vies}")
    else:
        print(" GAME OVER ")
        print(f"Désolé {nom}, vous avez perdu !")
        print(f"Le mot était : {mot_secret}")

    print("=" * 50)

    # Demander si le joueur veut rejouer
    reponse_joueur = input("\nVoulez-vous faire un autre match ? (oui/non) : ")
    if reponse_joueur.lower() in ["non", "n"]:
        Stopme = False

print(f"\n👋 Merci d'avoir joué {nom} ! À bientôt !")
print("=" * 50)