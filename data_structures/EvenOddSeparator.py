print("-" * 20 + "EvenOddSeparator" + "-" * 20)
c = True

while c:
    # Vérification de la saisie du nombre
    try:
        n = int(input("Entrer le nombre de valeurs que vous voulez traiter : "))
    except ValueError:
        print("Erreur : vous devez entrer un nombre entier valide !")
        continue  # redemande directement

    if n <= 0:
        print("Vous avez choisi une valeur nulle ! Il faut choisir une valeur supérieure à 0 !")
    else:
        toutes_valeurs = []
        valeurs_paires = []
        valeurs_impaires = []

        for i in range(n):
            # Vérification de chaque valeur saisie
            while True:
                try:
                    valeur = int(input(f"Entrer la valeur de Tab[{i}] = "))
                    break
                except ValueError:
                    print("Erreur : veuillez entrer un entier valide !")

            toutes_valeurs.append(valeur)

            if valeur % 2 == 0:
                valeurs_paires.append(valeur)
            else:
                valeurs_impaires.append(valeur)

        # Affichage après toutes les saisies
        print("-" * 50)
        print(f"Les valeurs que vous avez tapées : {toutes_valeurs}")
        print(f"Les valeurs paires   : {valeurs_paires}")
        print(f"Les valeurs impaires : {valeurs_impaires}")
        print("-" * 50)

    # Vérification de la réponse oui/non
    while True:
        r = input("Voulez-vous continuer ? (oui/non): ").strip().lower()
        if r in ["oui", "non"]:
            break
        else:
            print("Réponse invalide ! Tapez seulement 'oui' ou 'non'.")

    if r == "non":
        c = False
        print("-" * 20 + "LE PROGRAMME EST TERMINÉ" + "-" * 20)
