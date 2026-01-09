print("--- Recherche du MAX et MIN ---")

# On définit la variable ici directement
Continuer = True

while Continuer:
    # 1. Demander combien de valeurs
    # On ajoute un try/except simple pour éviter le crash si on tape des lettres
    try:
        n = int(input("Entrer le nombre de valeurs que vous avez : "))
    except ValueError:
        print("Erreur : Veuillez entrer un nombre entier.")
        continue # On recommence la boucle depuis le début

    list_valeur = []
    print("Entrer les valeurs une par une :")

    # 2. Récupérer les valeurs
    for i in range(1, n + 1):
        while True: # Petite boucle pour valider chaque nombre
            try:
                valide_valeur = float(input(f"Valeur numero {i} : "))
                list_valeur.append(valide_valeur)
                break # Sort de la petite boucle si le nombre est valide
            except ValueError:
                print("Ce n'est pas un nombre valide. Réessayez.")

    # 3. Calculer et Afficher (seulement si la liste n'est pas vide)
    if list_valeur:
        max_valeur = max(list_valeur)
        min_valeur = min(list_valeur)
        print("------------------------------")
        print(f"Valeur maximale : {max_valeur}")
        print(f"Valeur minimale : {min_valeur}")
        print("------------------------------")
    else:
        print("Aucune valeur n'a été saisie.")

    # 4. Demander si on continue
    reponse = input("Voulez-vous continuer (oui / non) ? : ")
    if reponse.lower() in ["non", "n"]:
        Continuer = False

print("Fin du programme.")