# Variable de contrôle pour la boucle principale
Dont_Stop = True

# Boucle principale du programme
while Dont_Stop:
    # Demander la taille du tuple à l'utilisateur
    taille = int(input("Entrer la taille du tuple : "))

    # Vérifier si la taille est valide
    if taille == 0:
        print("Erreur : La taille du tuple est 0")
        continue  # Recommencer la boucle

    # Créer une liste temporaire pour stocker les valeurs
    valeurs_temp = []
    for i in range(taille):
        valeur = int(input(f"Entrer le nombre {i} : "))
        valeurs_temp.append(valeur)

    # Convertir la liste en tuple (les tuples sont immuables)
    mon_tuple = tuple(valeurs_temp)

    # Afficher le tuple original
    print("#" * 50)
    print("Le tuple original est :", mon_tuple)

    # Variable de contrôle pour le menu
    continuer_menu = True

    # Boucle du menu d'options
    while continuer_menu:
        # Affichage du menu
        print("\n" + "#" * 10 + " MENU " + "#" * 10)
        print("1. Créer un nouveau tuple avec ajout")
        print("2. Créer un nouveau tuple avec modification")
        print("3. Créer un nouveau tuple avec suppression")
        print("4. Rechercher une valeur")
        print("5. Trier le tuple (nouveau tuple)")
        print("6. Inverser le tuple (nouveau tuple)")
        print("7. Afficher le tuple")
        print("8. Afficher statistiques")
        print("9. Concaténer avec un autre tuple")
        print("0. Quitter")

        # Récupérer le choix de l'utilisateur
        choix = input("Choisissez une option : ")

        # Option 1 : Ajouter une valeur (crée un nouveau tuple)
        if choix == "1":
            print("#" * 25 + " Ajout " + "#" * 25)
            print("Note : Les tuples sont immuables, un nouveau tuple sera créé")
            nouvelle_valeur = int(input("Entrer la valeur à ajouter : "))
            # Créer un nouveau tuple avec la valeur ajoutée
            mon_tuple = mon_tuple + (nouvelle_valeur,)
            print(f"Le nouveau tuple après ajout de {nouvelle_valeur} :", mon_tuple)

        # Option 2 : Modifier une valeur (crée un nouveau tuple)
        elif choix == "2":
            print("#" * 25 + " Modification " + "#" * 25)
            print("Note : Les tuples sont immuables, un nouveau tuple sera créé")
            indice_edit = int(input(f"Donner l'indice de l'élément à modifier (0 à {len(mon_tuple) - 1}) : "))

            # Vérifier que l'indice est valide
            if 0 <= indice_edit < len(mon_tuple):
                new_valeur = int(input(f"Entrer la nouvelle valeur pour l'indice {indice_edit} : "))
                # Convertir en liste pour modifier, puis reconvertir en tuple
                liste_temp = list(mon_tuple)
                liste_temp[indice_edit] = new_valeur
                mon_tuple = tuple(liste_temp)
                print("Le nouveau tuple après modification :", mon_tuple)
            else:
                print("Indice invalide ! Veuillez réessayer.")

        # Option 3 : Supprimer une valeur (crée un nouveau tuple)
        elif choix == "3":
            print("#" * 25 + " Suppression " + "#" * 25)
            print("Note : Les tuples sont immuables, un nouveau tuple sera créé")
            indice_del = int(input(f"Donner l'indice de valeur à supprimer (0 à {len(mon_tuple) - 1}) : "))

            # Vérifier que l'indice est valide
            if 0 <= indice_del < len(mon_tuple):
                valeur_supprimee = mon_tuple[indice_del]
                # Créer un nouveau tuple sans l'élément à supprimer
                mon_tuple = mon_tuple[:indice_del] + mon_tuple[indice_del + 1:]
                print(f"Le nouveau tuple après suppression de {valeur_supprimee} :", mon_tuple)
            else:
                print("Indice invalide ! Veuillez réessayer.")

        # Option 4 : Rechercher une valeur
        elif choix == "4":
            print("#" * 25 + " Rechercher une valeur " + "#" * 25)

            # Vérifier si le tuple n'est pas vide
            if not mon_tuple:
                print("Le tuple est vide !")
            else:
                val = int(input("Entrer la valeur à rechercher : "))
                # Trouver tous les indices où la valeur apparaît
                indices = [i for i, v in enumerate(mon_tuple) if v == val]

                if indices:
                    # Compter le nombre d'occurrences
                    nombre_occurrences = mon_tuple.count(val)
                    print(f"La valeur {val} existe dans le tuple aux positions : {indices}")
                    print(f"Nombre d'occurrences : {nombre_occurrences}")
                else:
                    print("La valeur n'existe pas dans le tuple !")

        # Option 5 : Trier le tuple (crée un nouveau tuple)
        elif choix == "5":
            print("#" * 25 + " Tri " + "#" * 25)
            # Trier et créer un nouveau tuple
            mon_tuple = tuple(sorted(mon_tuple))
            print("Le tuple trié est :", mon_tuple)

        # Option 6 : Inverser le tuple (crée un nouveau tuple)
        elif choix == "6":
            print("#" * 25 + " Inversion " + "#" * 25)
            # Inverser l'ordre des éléments
            mon_tuple = mon_tuple[::-1]
            print("Le tuple inversé est :", mon_tuple)

        # Option 7 : Afficher le tuple
        elif choix == "7":
            print("#" * 25 + " Affichage " + "#" * 25)
            print("Le tuple actuel :", mon_tuple)
            print(f"Type : {type(mon_tuple)}")

        # Option 8 : Afficher les statistiques
        elif choix == "8":
            print("#" * 25 + " Statistiques " + "#" * 25)

            # Vérifier si le tuple n'est pas vide
            if mon_tuple:
                print(f"La taille du tuple : {len(mon_tuple)}")
                print(f"La valeur maximale du tuple : {max(mon_tuple)}")
                print(f"La valeur minimale du tuple : {min(mon_tuple)}")
                print(f"La somme du tuple : {sum(mon_tuple)}")
                print(f"La moyenne du tuple : {sum(mon_tuple) / len(mon_tuple):.2f}")
                print(f"Le tuple est immuable : {isinstance(mon_tuple, tuple)}")
            else:
                print("Le tuple est vide !")

        # Option 9 : Concaténer avec un autre tuple
        elif choix == "9":
            print("#" * 25 + " Concaténation " + "#" * 25)
            taille_concat = int(input("Combien de valeurs voulez-vous ajouter ? "))
            valeurs_concat = []
            for i in range(taille_concat):
                val = int(input(f"Entrer la valeur {i} : "))
                valeurs_concat.append(val)

            # Créer un nouveau tuple et le concaténer
            nouveau_tuple = tuple(valeurs_concat)
            mon_tuple = mon_tuple + nouveau_tuple
            print("Le tuple après concaténation :", mon_tuple)

        # Option 0 : Quitter le programme
        elif choix == "0":
            print("Au revoir !")
            Dont_Stop = False  # Arrêter la boucle principale
            continuer_menu = False  # Arrêter la boucle du menu

        # Option invalide
        else:
            print("Option invalide ! Veuillez choisir une option valide de 0 à 9 du menu")

    # Demander si l'utilisateur veut continuer avec un nouveau tuple
    if Dont_Stop:
        r_continue = input("\nVoulez-vous continuer avec un nouveau tuple (oui/non) : ")
        if r_continue.lower() in ["non", "n"]:
            Dont_Stop = False  # Arrêter le programme