# WordCounter.py

# Boucle infinie pour afficher le menu tant que l'utilisateur ne choisit pas de quitter
while True:
    print("=== Word Counter Program ===")
    print("1. Entrer du texte manuellement")
    print("2. Quitter")

    # On essaie de convertir le choix en entier
    try:
        choice = int(input("Entrez votre choix: "))
    except ValueError:
        # Si l'utilisateur entre autre chose qu'un nombre
        print("=" * 50)
        print("Veuillez entrer un nombre entre 1 et 2")
        print("=" * 50)
    else:
        # Si l'utilisateur choisit l'option 1
        if choice == 1:
            # Demander une phrase
            text = input("Entrez une phrase: ")
            # Découper la phrase en mots (séparés par des espaces)
            words = text.split()
            # Compter le nombre de mots
            numWords = len(words)
            # Afficher le résultat
            print("-" * 50)
            print(f"Nombre de mots : {numWords} mots")
            print("-" * 50)
            input("Appuyez sur Entrée pour continuer...")

        # Si l'utilisateur choisit l'option 2
        elif choice == 2:
            confirm = input("Voulez-vous quitter (y/n)? ")
            # Vérifier la confirmation
            if confirm.lower() == "y":
                print("Fermeture du programme...")
                break

        # Si l'utilisateur entre un nombre autre que 1 ou 2
        else:
            print("Veuillez entrer un choix valide.")
