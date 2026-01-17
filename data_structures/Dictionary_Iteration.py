# Variable de contrôle pour la boucle principale
Dont_Stop = True

# Boucle principale du programme
while Dont_Stop:
    # Demander le nombre d'éléments du dictionnaire
    taille = int(input("Entrer le nombre d'éléments du dictionnaire : "))

    # Initialiser un dictionnaire vide
    mon_dict = {}

    # Vérifier si la taille est valide
    if taille == 0:
        print("Erreur : Le dictionnaire sera vide")
        # On peut continuer avec un dictionnaire vide
    else:
        # Remplir le dictionnaire avec les paires clé-valeur
        print("\n--- Remplissage du dictionnaire ---")
        for i in range(taille):
            cle = input(f"Entrer la clé {i + 1} : ")
            valeur = input(f"Entrer la valeur pour '{cle}' : ")
            mon_dict[cle] = valeur

    # Afficher le dictionnaire original
    print("#" * 50)
    print("Le dictionnaire original est :", mon_dict)

    # Variable de contrôle pour le menu
    continuer_menu = True

    # Boucle du menu d'options
    while continuer_menu:
        # Affichage du menu
        print("\n" + "#" * 10 + " MENU " + "#" * 10)
        print("1. Ajouter/Modifier une paire clé-valeur")
        print("2. Supprimer une paire clé-valeur")
        print("3. Rechercher une clé")
        print("4. Rechercher une valeur")
        print("5. Afficher toutes les clés")
        print("6. Afficher toutes les valeurs")
        print("7. Afficher le dictionnaire")
        print("8. Afficher statistiques")
        print("9. Vider le dictionnaire")
        print("10. Fusionner avec un autre dictionnaire")
        print("0. Quitter")

        # Récupérer le choix de l'utilisateur
        choix = input("Choisissez une option : ")

        # Option 1 : Ajouter ou modifier une paire clé-valeur
        if choix == "1":
            print("#" * 25 + " Ajout/Modification " + "#" * 25)
            cle = input("Entrer la clé : ")
            valeur = input("Entrer la valeur : ")

            # Si la clé existe déjà, c'est une modification, sinon c'est un ajout
            if cle in mon_dict:
                print(f"La clé '{cle}' existe déjà avec la valeur '{mon_dict[cle]}'")
                print("Elle sera modifiée.")

            mon_dict[cle] = valeur  # Ajouter ou modifier la paire
            print(f"Le dictionnaire après ajout/modification : {mon_dict}")

        # Option 2 : Supprimer une paire clé-valeur
        elif choix == "2":
            print("#" * 25 + " Suppression " + "#" * 25)

            # Vérifier si le dictionnaire n'est pas vide
            if not mon_dict:
                print("Le dictionnaire est vide !")
            else:
                cle = input("Entrer la clé à supprimer : ")

                # Vérifier si la clé existe
                if cle in mon_dict:
                    valeur_supprimee = mon_dict[cle]
                    del mon_dict[cle]  # Supprimer la paire clé-valeur
                    print(f"La paire '{cle}': '{valeur_supprimee}' a été supprimée")
                    print(f"Le dictionnaire après suppression : {mon_dict}")
                else:
                    print(f"La clé '{cle}' n'existe pas dans le dictionnaire !")

        # Option 3 : Rechercher une clé
        elif choix == "3":
            print("#" * 25 + " Rechercher une clé " + "#" * 25)

            # Vérifier si le dictionnaire n'est pas vide
            if not mon_dict:
                print("Le dictionnaire est vide !")
            else:
                cle = input("Entrer la clé à rechercher : ")

                # Vérifier si la clé existe
                if cle in mon_dict:
                    print(f"✓ La clé '{cle}' existe dans le dictionnaire")
                    print(f"  Valeur associée : '{mon_dict[cle]}'")
                else:
                    print(f"✗ La clé '{cle}' n'existe pas dans le dictionnaire")

        # Option 4 : Rechercher une valeur
        elif choix == "4":
            print("#" * 25 + " Rechercher une valeur " + "#" * 25)

            # Vérifier si le dictionnaire n'est pas vide
            if not mon_dict:
                print("Le dictionnaire est vide !")
            else:
                valeur = input("Entrer la valeur à rechercher : ")

                # Trouver toutes les clés ayant cette valeur
                cles_trouvees = [cle for cle, val in mon_dict.items() if val == valeur]

                if cles_trouvees:
                    print(f"✓ La valeur '{valeur}' existe dans le dictionnaire")
                    print(f"  Clés associées : {cles_trouvees}")
                else:
                    print(f"✗ La valeur '{valeur}' n'existe pas dans le dictionnaire")

        # Option 5 : Afficher toutes les clés
        elif choix == "5":
            print("#" * 25 + " Toutes les clés " + "#" * 25)

            # Vérifier si le dictionnaire n'est pas vide
            if not mon_dict:
                print("Le dictionnaire est vide !")
            else:
                print("Liste des clés :")
                for cle in mon_dict.keys():
                    print(f"  - {cle}")
                print(f"\nTotal : {len(mon_dict.keys())} clé(s)")

        # Option 6 : Afficher toutes les valeurs
        elif choix == "6":
            print("#" * 25 + " Toutes les valeurs " + "#" * 25)

            # Vérifier si le dictionnaire n'est pas vide
            if not mon_dict:
                print("Le dictionnaire est vide !")
            else:
                print("Liste des valeurs :")
                for valeur in mon_dict.values():
                    print(f"  - {valeur}")
                print(f"\nTotal : {len(mon_dict.values())} valeur(s)")

        # Option 7 : Afficher le dictionnaire
        elif choix == "7":
            print("#" * 25 + " Affichage " + "#" * 25)

            # Vérifier si le dictionnaire n'est pas vide
            if not mon_dict:
                print("Le dictionnaire est vide : {}")
            else:
                print("Le dictionnaire actuel :")
                for cle, valeur in mon_dict.items():
                    print(f"  '{cle}' : '{valeur}'")
                print(f"\nReprésentation : {mon_dict}")

        # Option 8 : Afficher les statistiques
        elif choix == "8":
            print("#" * 25 + " Statistiques " + "#" * 25)

            # Vérifier si le dictionnaire n'est pas vide
            if not mon_dict:
                print("Le dictionnaire est vide !")
                print(f"Nombre d'éléments : 0")
            else:
                print(f"Nombre de paires clé-valeur : {len(mon_dict)}")
                print(f"Nombre de clés : {len(mon_dict.keys())}")
                print(f"Nombre de valeurs : {len(mon_dict.values())}")

                # Trouver la clé la plus longue
                cle_plus_longue = max(mon_dict.keys(), key=len)
                print(f"Clé la plus longue : '{cle_plus_longue}' ({len(cle_plus_longue)} caractères)")

                # Trouver la valeur la plus longue
                valeur_plus_longue = max(mon_dict.values(), key=len)
                print(f"Valeur la plus longue : '{valeur_plus_longue}' ({len(valeur_plus_longue)} caractères)")

                # Vérifier s'il y a des doublons dans les valeurs
                valeurs_list = list(mon_dict.values())
                valeurs_uniques = set(valeurs_list)
                if len(valeurs_list) != len(valeurs_uniques):
                    print("⚠ Il y a des valeurs en double dans le dictionnaire")
                else:
                    print("✓ Toutes les valeurs sont uniques")

        # Option 9 : Vider le dictionnaire
        elif choix == "9":
            print("#" * 25 + " Vider le dictionnaire " + "#" * 25)
            confirmation = input("Êtes-vous sûr de vouloir vider le dictionnaire ? (oui/non) : ")

            if confirmation.lower() in ["oui", "o"]:
                mon_dict.clear()  # Supprimer tous les éléments
                print("Le dictionnaire a été vidé : {}")
            else:
                print("Opération annulée")

        # Option 10 : Fusionner avec un autre dictionnaire
        elif choix == "10":
            print("#" * 25 + " Fusion de dictionnaires " + "#" * 25)
            taille_fusion = int(input("Combien de paires clé-valeur voulez-vous ajouter ? "))

            # Créer un nouveau dictionnaire temporaire
            nouveau_dict = {}
            for i in range(taille_fusion):
                cle = input(f"Entrer la clé {i + 1} : ")
                valeur = input(f"Entrer la valeur pour '{cle}' : ")
                nouveau_dict[cle] = valeur

            # Fusionner les deux dictionnaires (les clés existantes seront écrasées)
            print(f"\nDictionnaire actuel : {mon_dict}")
            print(f"Nouveau dictionnaire : {nouveau_dict}")

            mon_dict.update(nouveau_dict)  # Fusion
            print(f"Dictionnaire après fusion : {mon_dict}")

        # Option 0 : Quitter le programme
        elif choix == "0":
            print("Au revoir !")
            Dont_Stop = False  # Arrêter la boucle principale
            continuer_menu = False  # Arrêter la boucle du menu

        # Option invalide
        else:
            print("Option invalide ! Veuillez choisir une option valide de 0 à 10 du menu")

    # Demander si l'utilisateur veut continuer avec un nouveau dictionnaire
    if Dont_Stop:
        r_continue = input("\nVoulez-vous continuer avec un nouveau dictionnaire (oui/non) : ")
        if r_continue.lower() in ["non", "n"]:
            Dont_Stop = False  # Arrêter le programme