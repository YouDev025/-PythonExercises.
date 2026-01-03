# ============================================
# PROGRAMME : GESTION DE LISTE DE COURSES
# ============================================
# Ce programme permet de gérer une liste de courses
# avec les opérations : ajouter, afficher, supprimer

# --- INITIALISATION ---
# Créer une liste vide qui va contenir tous les articles
courses = []

# --- BOUCLE PRINCIPALE ---
# while True crée une boucle infinie.
# Elle continue jusqu'à rencontrer un "break"
while True:

    # --- AFFICHAGE DU MENU ---
    # \n crée une ligne vide pour espacer
    print("\nMenu :")
    print("1. Ajouter un course !")
    print("2. Afficher un course !")
    print("3. Supprimer un course !")
    print("4. Quitter un course !")

    # --- DEMANDER LE CHOIX DE L'UTILISATEUR ---
    # input() récupère ce que l'utilisateur tape
    # Le résultat est une chaîne de caractères (string)
    choix = input("Choisisser une option : ")

    # ==========================================
    # OPTION 1 : AJOUTER UN ARTICLE
    # ==========================================
    if choix == "1":
        # Demander le nom de l'article
        course = input("Entrer le nom du course : ")

        # append() est une méthode qui ajoute un élément à la FIN de la liste
        # Exemple : si courses = ["Pain"], après courses.append("Lait")
        #           courses devient ["Pain", "Lait"]
        courses.append(course)

        # Afficher un message de confirmation
        print(course, "a été ajoué a la liste de courses")


    # ==========================================
    # OPTION 2 : AFFICHER LA LISTE
    # ==========================================
    elif choix == "2":
        # Vérifier si la liste est vide
        # "not courses" est équivalent à "len(courses) == 0"
        # Si la liste est vide, "not courses" retourne True
        if not courses:
            print(" La liste est vide.")

        # Si la liste n'est PAS vide (elle contient des articles)
        else:
            print("La liste des courses est : ")

            # enumerate() est une fonction qui parcourt une liste
            # et donne à la fois l'index ET l'élément
            # Exemple : pour ["Pain", "Lait", "Œufs"]
            #   Tour 1 : i=1, course="Pain"
            #   Tour 2 : i=2, course="Lait"
            #   Tour 3 : i=3, course="Œufs"
            # start=1 fait commencer à 1 au lieu de 0
            for i, course in enumerate(courses, start=1):
                # i : le numéro (1, 2, 3...)
                # course : le nom de l'article
                print(i, "-", course)


    # ==========================================
    # OPTION 3 : SUPPRIMER UN ARTICLE
    # ==========================================
    elif choix == "3":
        # D'abord vérifier si la liste est vide
        # On ne peut pas supprimer d'une liste vide !
        if not courses:
            print(" La liste est vide.")

        # Si la liste contient des articles
        else:
            # Afficher la liste pour que l'utilisateur voie les numéros
            for i, course in enumerate(courses, start=1):
                print(i, "-", course)

        # Demander quel article supprimer
        # int() convertit le texte en nombre
        # Exemple : "3" (texte) devient 3 (nombre)
        num = int(input("Choisisser le course a supprimer : "))

        # Vérifier que le numéro est valide
        # Il doit être >= 1 ET <= nombre d'articles
        # Exemple : si courses a 5 articles, num doit être entre 1 et 5
        if 1 <= num <= len(courses):
            # pop(index) supprime l'élément à la position "index"
            # ET retourne cet élément (pour qu'on puisse l'afficher)
            #
            # ATTENTION : Les index commencent à 0 !
            # Si l'utilisateur tape 1, on doit supprimer l'index 0
            # Si l'utilisateur tape 2, on doit supprimer l'index 1
            # Donc : index = num - 1
            #
            # Exemple : courses = ["Pain", "Lait", "Œufs"]
            #   Si num = 2 (l'utilisateur veut supprimer "Lait")
            #   On fait courses.pop(2-1) = courses.pop(1)
            #   Cela supprime "Lait" (qui est à l'index 1)
            supprime = courses.pop(num - 1)

            # Afficher ce qui a été supprimé
            print(supprime, " a été supprimé.")

        # Si le numéro n'est pas valide (trop petit ou trop grand)
        else:
            print(" Le numero est invalide.")


    # ==========================================
    # OPTION 4 : QUITTER LE PROGRAMME
    # ==========================================
    elif choix == "4":
        # Message d'au revoir
        print("Au revoir !")

        # break arrête la boucle while
        # Le programme se termine ici
        break

# Fin du programme
# Si on arrive ici, c'est que l'utilisateur a quitté (choix 4)