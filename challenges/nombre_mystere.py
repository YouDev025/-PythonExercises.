import random

# Afficher le titre
print("=" * 50)
print("Bienvenue au Jeu nombre mystère !")
print("=" * 50)
print("J'ai choisi un nombre entre 0 et 100")
print("À vous de le deviner !")
print("=" * 50)

# demander le nom du joueur
nom = input("Quel est votre nom ? : ")
while not nom.strip():
    print("=" * 50)
    nom = input("Erreur : Vous n'avez pas entré le nom ! Quel est votre nom ? : ")

print("=" * 50)
print(f"Bonjour {nom} ! On commence !")
print("=" * 50)

# La boucle principale
notStop = True
while notStop:

    # choisir un nombre aléatoire
    nombre_aleatoire = random.randint(0, 100)
    tentatives = 0
    trouve = False

    # Boucle du jeu
    while not trouve:
        essaie = ""
        while not essaie.isdigit():
            essaie = input("Veuillez entrer un nombre entre 0 et 100 : ")
            if not essaie.isdigit():
                print("=" * 50)
                print("Erreur ! Vous devez entrer un nombre valide de 0 à 100 !")
                print("=" * 50)

        essaie = int(essaie)  # conversion en entier
        tentatives += 1

        # Vérification si le nombre est dans la plage
        if essaie < 0 or essaie > 100:
            print("=" * 50)
            print("Erreur : veuillez entrer un nombre entre 0 et 100.")
            print("=" * 50)
        elif essaie < nombre_aleatoire:
            print("C'est plus haut !")
        elif essaie > nombre_aleatoire:
            print("C'est plus bas !")
        else:
            trouve = True
            print("\n" + "=" * 50)
            print(f"Bravo {nom}, vous avez trouvé le nombre {nombre_aleatoire} !")
            print(f"Nombre de tentatives : {tentatives}")
            print("=" * 50)

            # Performance du joueur
            if tentatives <= 5:
                print(f"Excellent {nom} ! Vous êtes un Master Class !")
            elif tentatives <= 10:
                print(f"Très bien joué {nom} !")
            else:
                print(f"Bien joué {nom} ! Continuez à pratiquer pour devenir un pro !")

    print(f"MERCI {nom} ! Au revoir, bye bye !!")
    print("=" * 50)
    R_continue = input("Voulez-vous rejouer une autre fois (oui / non) : ")
    if R_continue.lower() in ["non", "n"]:
        notStop = False

print("=" * 50)
print("Au revoir !")
print("=" * 50)
