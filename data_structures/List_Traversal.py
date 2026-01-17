Dont_Stop = True
while Dont_Stop:
    taille = int(input("Entrer la taille de la liste : "))
    liste = []

    if taille == 0:
        print("Erreur : La taille de la liste est 0")
        continue

    for i in range(taille):
        valeurs = int(input(f"Entrer le nombre {i} : "))
        liste.append(valeurs)

    print("#" * 50)
    print("La liste originale est :", liste)
    conitinuer_menu = True
    while conitinuer_menu:
        print("\n" + "#" * 10 + " MENU " + "#" * 10)
        print("1. Ajouter/Insérer une valeur")
        print("2. Modifier une valeur")
        print("3. Supprimer une valeur")
        print("4. Rechercher une valeur")
        print("5. Trier la liste")
        print("6. Inverser la liste")
        print("7. Afficher la liste")
        print("8. Afficher statistiques")
        print("9. Vider la liste")
        print("0. Quitter")
        choix = input("Choisissez une option : ")
        # Insertion
        if choix == "1":
            print("#" * 25 + " Insertion " + "#" * 25)
            insert_valeur = int(input(f"Entrer la valeur a inserer : "))
            liste.append(insert_valeur)
            print(f"La liste aprés insertion de la valeur {insert_valeur} :", liste)
        # Modification
        elif choix == "2":
            print("#" *25+" Modification "+"#"*25)
            indice_edit = int(input(f"Donner l'indice de l'élément à modifier (0 à {len(liste)-1}) : "))
            if 0 <= indice_edit < len(liste):
                new_valeur = int(input(f"Entrer la nouvelle valeur pour l'indice {indice_edit} : "))
                liste[indice_edit] = new_valeur
                print("La liste après modification :", liste)
            else:
                print("Indice invalide ! Veuillez réessayer.")
        # Suppression
        elif choix =="3":
            print("#" *25+" Suppression "+"#"*25)
            indice_del =  int(input(f"Donner l'indice de valeur a supprimer de (0 a {len(liste)-1}) : "))
            if 0 <= indice_del < len(liste):
                #del_valeur = int(input("Entrer la valeur a supprimer : "))
                del liste[indice_del]
                print(f"La liste aprés la suppression de la valeur {indice_del} :", liste)
            else:
                print("Indice invalide ! Veuillez réessayer.")
        #Rechercher une valeur
        elif choix =="4":
            print("#" * 25 + " Rechercher une valeur " + "#" * 25)
            if not liste:
                print("La liste n'existe pas ! la liste est vide !")
            else:
                val = int(input(f"Entrer la valeur a rechercher : "))
                indices = [ i for i , v in enumerate(liste) if v == val]
                if indices:
                    print(" La valeur existe dans la liste !")
                else:
                    print("La liste n'existe pas !")
        #triéer la liste
        elif choix =="5":
            print("#" * 25 + " Tri " + "#" * 25)
            liste = sorted(liste)
            print("La liste triée est :", liste)
        # Inverser la liste
        elif choix == "6":
            print("#" * 25 + " Inversion  " + "#" * 25)
            liste.reverse()
            print("La liste inversée est :", liste)
        #Affichage de la liste
        elif choix =="7":
            print("#" * 25 + " Affichage " + "#" * 25)
            print("la liste acctuelle : ", liste)
        #Statistiques de la liste
        elif choix =="8":
            print("#" * 25 + " Statistiques  " + "#" * 25)
            if liste:
                print(f"La taille de la liste : {len(liste)}")
                print(f"La valeur maximale de la liste : {max(liste)}")
                print(f"La valeur minimale de la liste : {min(liste)}")
                print(f"La somme de la liste : {sum(liste)}")
                print(f"Le moyenne de la liste : {sum(liste)/len(liste)}")
            else:
                print("La liste n'existe pas ! la liste est vide !")
            #Vider la liste
        elif choix == "9":
            print("#" * 25 + " Vider la liste " + "#" * 25)
            liste.clear()
            print("La liste a été vidée :", liste)
        #Quitter le Menu
        elif choix =="0":
            print("Au revoir !")
            Dont_Stop= False
            conitinuer_menu = False
        else:
            print("Option invalide ! Veuillez choisir une autre option valide de 0 a 9 du menu ")
        # Continuer ou arrêter
    if Dont_Stop:
        r_continue = input("Voulez-vous continuer avec une nouvelle liste (oui/non) : ")
        if r_continue.lower() in ["non", "n"]:
            Dont_Stop = False

