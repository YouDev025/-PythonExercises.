# Variable de contrôle pour la boucle principale
Dont_Stop = True

# Boucle principale du programme
while Dont_Stop:
    # Demander le nombre d'éléments de l'ensemble
    taille = int(input("Entrer le nombre d'éléments de l'ensemble : "))

    # Initialiser un ensemble vide
    mon_set = set()

    # Vérifier si la taille est valide
    if taille == 0:
        print("Erreur : L'ensemble sera vide")
        # On peut continuer avec un ensemble vide
    else:
        # Remplir l'ensemble avec les valeurs (les doublons seront automatiquement ignorés)
        print("\n--- Remplissage de l'ensemble ---")
        print("Note : Les doublons seront automatiquement supprimés")
        for i in range(taille):
            valeur = input(f"Entrer l'élément {i + 1} : ")
            mon_set.add(valeur)  # Ajouter l'élément à l'ensemble

    # Afficher l'ensemble original
    print("#" * 50)
    print("L'ensemble original est :", mon_set)
    print(f"Taille réelle (sans doublons) : {len(mon_set)}")

    # Variable de contrôle pour le menu
    continuer_menu = True

    # Boucle du menu d'options
    while continuer_menu:
        # Affichage du menu
        print("\n" + "#" * 10 + " MENU " + "#" * 10)
        print("1. Ajouter un élément")
        print("2. Supprimer un élément")
        print("3. Rechercher un élément")
        print("4. Union avec un autre ensemble")
        print("5. Intersection avec un autre ensemble")
        print("6. Différence avec un autre ensemble")
        print("7. Afficher l'ensemble")
        print("8. Afficher statistiques")
        print("9. Vider l'ensemble")
        print("10. Différence symétrique")
        print("0. Quitter")

        # Récupérer le choix de l'utilisateur
        choix = input("Choisissez une option : ")

        # Option 1 : Ajouter un élément
        if choix == "1":
            print("#" * 25 + " Ajout " + "#" * 25)
            element = input("Entrer l'élément à ajouter : ")

            # Vérifier si l'élément existe déjà
            if element in mon_set:
                print(f"⚠ L'élément '{element}' existe déjà dans l'ensemble (pas de doublons)")
            else:
                mon_set.add(element)  # Ajouter l'élément
                print(f"✓ L'élément '{element}' a été ajouté")

            print(f"L'ensemble après ajout : {mon_set}")

        # Option 2 : Supprimer un élément
        elif choix == "2":
            print("#" * 25 + " Suppression " + "#" * 25)

            # Vérifier si l'ensemble n'est pas vide
            if not mon_set:
                print("L'ensemble est vide !")
            else:
                element = input("Entrer l'élément à supprimer : ")

                # Vérifier si l'élément existe
                if element in mon_set:
                    mon_set.remove(element)  # Supprimer l'élément
                    print(f"✓ L'élément '{element}' a été supprimé")
                    print(f"L'ensemble après suppression : {mon_set}")
                else:
                    print(f"✗ L'élément '{element}' n'existe pas dans l'ensemble")

        # Option 3 : Rechercher un élément
        elif choix == "3":
            print("#" * 25 + " Rechercher un élément " + "#" * 25)

            # Vérifier si l'ensemble n'est pas vide
            if not mon_set:
                print("L'ensemble est vide !")
            else:
                element = input("Entrer l'élément à rechercher : ")

                # Vérifier si l'élément existe (opération très rapide O(1))
                if element in mon_set:
                    print(f"✓ L'élément '{element}' existe dans l'ensemble")
                else:
                    print(f"✗ L'élément '{element}' n'existe pas dans l'ensemble")

        # Option 4 : Union avec un autre ensemble
        elif choix == "4":
            print("#" * 25 + " Union " + "#" * 25)
            print("L'union combine tous les éléments des deux ensembles (sans doublons)")

            taille_union = int(input("Combien d'éléments dans le nouvel ensemble ? "))
            nouveau_set = set()

            for i in range(taille_union):
                element = input(f"Entrer l'élément {i + 1} : ")
                nouveau_set.add(element)

            # Calculer l'union
            ensemble_union = mon_set.union(nouveau_set)
            # Ou : ensemble_union = mon_set | nouveau_set

            print(f"\nEnsemble actuel : {mon_set}")
            print(f"Nouvel ensemble : {nouveau_set}")
            print(f"Union (A ∪ B) : {ensemble_union}")

            # Demander si on veut remplacer l'ensemble actuel
            remplacer = input("\nVoulez-vous remplacer l'ensemble actuel par l'union ? (oui/non) : ")
            if remplacer.lower() in ["oui", "o"]:
                mon_set = ensemble_union
                print("L'ensemble a été remplacé")

        # Option 5 : Intersection avec un autre ensemble
        elif choix == "5":
            print("#" * 25 + " Intersection " + "#" * 25)
            print("L'intersection contient uniquement les éléments communs aux deux ensembles")

            taille_inter = int(input("Combien d'éléments dans le nouvel ensemble ? "))
            nouveau_set = set()

            for i in range(taille_inter):
                element = input(f"Entrer l'élément {i + 1} : ")
                nouveau_set.add(element)

            # Calculer l'intersection
            ensemble_intersection = mon_set.intersection(nouveau_set)
            # Ou : ensemble_intersection = mon_set & nouveau_set

            print(f"\nEnsemble actuel : {mon_set}")
            print(f"Nouvel ensemble : {nouveau_set}")
            print(f"Intersection (A ∩ B) : {ensemble_intersection}")

            if not ensemble_intersection:
                print("⚠ Les deux ensembles n'ont aucun élément en commun (ensembles disjoints)")

            # Demander si on veut remplacer l'ensemble actuel
            remplacer = input("\nVoulez-vous remplacer l'ensemble actuel par l'intersection ? (oui/non) : ")
            if remplacer.lower() in ["oui", "o"]:
                mon_set = ensemble_intersection
                print("L'ensemble a été remplacé")

        # Option 6 : Différence avec un autre ensemble
        elif choix == "6":
            print("#" * 25 + " Différence " + "#" * 25)
            print("La différence contient les éléments de A qui ne sont pas dans B")

            taille_diff = int(input("Combien d'éléments dans le nouvel ensemble ? "))
            nouveau_set = set()

            for i in range(taille_diff):
                element = input(f"Entrer l'élément {i + 1} : ")
                nouveau_set.add(element)

            # Calculer la différence
            ensemble_difference = mon_set.difference(nouveau_set)
            # Ou : ensemble_difference = mon_set - nouveau_set

            print(f"\nEnsemble actuel (A) : {mon_set}")
            print(f"Nouvel ensemble (B) : {nouveau_set}")
            print(f"Différence (A - B) : {ensemble_difference}")

            # Demander si on veut remplacer l'ensemble actuel
            remplacer = input("\nVoulez-vous remplacer l'ensemble actuel par la différence ? (oui/non) : ")
            if remplacer.lower() in ["oui", "o"]:
                mon_set = ensemble_difference
                print("L'ensemble a été remplacé")

        # Option 7 : Afficher l'ensemble
        elif choix == "7":
            print("#" * 25 + " Affichage " + "#" * 25)

            # Vérifier si l'ensemble n'est pas vide
            if not mon_set:
                print("L'ensemble est vide : set()")
            else:
                print("L'ensemble actuel :")
                # Afficher chaque élément
                for element in sorted(mon_set):  # Trié pour un affichage plus lisible
                    print(f"  - {element}")
                print(f"\nReprésentation : {mon_set}")
                print(f"Type : {type(mon_set)}")

        # Option 8 : Afficher les statistiques
        elif choix == "8":
            print("#" * 25 + " Statistiques " + "#" * 25)

            # Vérifier si l'ensemble n'est pas vide
            if not mon_set:
                print("L'ensemble est vide !")
                print(f"Nombre d'éléments : 0")
            else:
                print(f"Nombre d'éléments : {len(mon_set)}")

                # Essayer de calculer des stats si ce sont des nombres
                try:
                    # Convertir en nombres pour calculer les statistiques
                    nombres = {float(x) for x in mon_set}
                    print(f"\nStatistiques numériques :")
                    print(f"  Minimum : {min(nombres)}")
                    print(f"  Maximum : {max(nombres)}")
                    print(f"  Somme : {sum(nombres)}")
                    print(f"  Moyenne : {sum(nombres) / len(nombres):.2f}")
                except (ValueError, TypeError):
                    print("\n⚠ L'ensemble contient des éléments non numériques")

                # Trouver l'élément le plus long (si ce sont des chaînes)
                try:
                    element_plus_long = max(mon_set, key=len)
                    print(f"\nÉlément le plus long : '{element_plus_long}' ({len(element_plus_long)} caractères)")
                except TypeError:
                    pass

                # Propriétés de l'ensemble
                print(f"\nPropriétés :")
                print(f"  - Pas de doublons : ✓")
                print(f"  - Non ordonné : ✓")
                print(f"  - Éléments mutables : ✗")

        # Option 9 : Vider l'ensemble
        elif choix == "9":
            print("#" * 25 + " Vider l'ensemble " + "#" * 25)
            confirmation = input("Êtes-vous sûr de vouloir vider l'ensemble ? (oui/non) : ")

            if confirmation.lower() in ["oui", "o"]:
                mon_set.clear()  # Supprimer tous les éléments
                print("L'ensemble a été vidé : set()")
            else:
                print("Opération annulée")

        # Option 10 : Différence symétrique
        elif choix == "10":
            print("#" * 25 + " Différence symétrique " + "#" * 25)
            print("La différence symétrique contient les éléments présents dans A ou B, mais pas dans les deux")

            taille_sym = int(input("Combien d'éléments dans le nouvel ensemble ? "))
            nouveau_set = set()

            for i in range(taille_sym):
                element = input(f"Entrer l'élément {i + 1} : ")
                nouveau_set.add(element)

            # Calculer la différence symétrique
            ensemble_sym = mon_set.symmetric_difference(nouveau_set)
            # Ou : ensemble_sym = mon_set ^ nouveau_set

            print(f"\nEnsemble actuel (A) : {mon_set}")
            print(f"Nouvel ensemble (B) : {nouveau_set}")
            print(f"Différence symétrique (A Δ B) : {ensemble_sym}")

            # Demander si on veut remplacer l'ensemble actuel
            remplacer = input("\nVoulez-vous remplacer l'ensemble actuel par la différence symétrique ? (oui/non) : ")
            if remplacer.lower() in ["oui", "o"]:
                mon_set = ensemble_sym
                print("L'ensemble a été remplacé")

        # Option 0 : Quitter le programme
        elif choix == "0":
            print("Au revoir !")
            Dont_Stop = False  # Arrêter la boucle principale
            continuer_menu = False  # Arrêter la boucle du menu

        # Option invalide
        else:
            print("Option invalide ! Veuillez choisir une option valide de 0 à 10 du menu")

    # Demander si l'utilisateur veut continuer avec un nouveau ensemble
    if Dont_Stop:
        r_continue = input("\nVoulez-vous continuer avec un nouveau ensemble (oui/non) : ")
        if r_continue.lower() in ["non", "n"]:
            Dont_Stop = False  # Arrêter le programme