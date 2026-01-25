def gerer_courses(liste_courses):
    if not isinstance(liste_courses, list):
        print("Erreur : La liste n'est pas valide !")
        return []

    print("="*50)
    print("Gestion de la liste de courses :")
    print("="*50)
    print(f"Liste actuelle : {liste_courses}")
    print(f"Nombre d'articles actuels : {len(liste_courses)}")
    print("="*50)

    # Demander si on veut ajouter des articles
    reponse = input("Voulez-vous ajouter des articles ? (oui/non) : ").lower()
    if reponse in ["oui", "o", "yes", "y"]:
        try:
            nombre = int(input("Combien d'articles voulez-vous ajouter ? : "))
        except ValueError:
            print("Erreur : Veuillez entrer un nombre valide.")
            return liste_courses

        if nombre < 0:
            print("Erreur : Le nombre n'est pas valide.")
            return liste_courses
        else:
            for i in range(nombre):
                while True:
                    article = input(f"Article {i+1} à ajouter : ").strip()
                    if article:
                        liste_courses.append(article)
                        print(f"{article} a été ajouté !")
                        break
                    else:
                        print("Erreur : Article non valide. Réessayez !")
    else:
        print("Ajout d'articles annulé.")

    # Suppression d’un article choisi
    print("="*50)
    print("Suppression des articles : ")
    print("="*50)
    if liste_courses:
        print("Articles disponibles :")
        for i, article in enumerate(liste_courses, start=1):
            print(f"{i}. {article}")

        try:
            choix = int(input("Entrez le numéro de l'article à supprimer (0 pour annuler) : "))
            if choix == 0:
                print("Suppression annulée !")
            elif 1 <= choix <= len(liste_courses):
                article_supprime = liste_courses.pop(choix - 1)
                print(f"Article '{article_supprime}' a été supprimé !")
            else:
                print("Erreur : Numéro invalide.")
        except ValueError:
            print("Erreur : Veuillez entrer un nombre valide.")
    else:
        print("Erreur : La liste est vide, impossible de supprimer un article !")

    # Affichage final
    print("="*50)
    print("Résultat final : ")
    print("="*50)
    print(f"Nombre total d'articles : {len(liste_courses)}")
    print(f"Liste finale : {liste_courses}")

    return liste_courses


# Fonction principale avec redémarrage
if __name__ == "__main__":
    while True:  # boucle principale pour recommencer le programme
        print("="*50)
        print("Création de la liste de courses initiale")
        print("="*50)

        while True:
            nb_articles = input("Combien d'articles voulez-vous ajouter dans la liste initiale ? : ")
            if nb_articles.isdigit() and int(nb_articles) >= 0:
                nb_articles = int(nb_articles)
                break
            else:
                print("Erreur : Le nombre doit être un entier positif !")

        # Créer la liste initiale
        mes_courses = []
        for i in range(nb_articles):
            while True:
                article = input(f"Article {i+1} à ajouter : ").strip()
                if article:
                    mes_courses.append(article)
                    break
                else:
                    print("Erreur : Article non valide.")

        # Appel de la fonction de gestion
        mes_courses = gerer_courses(mes_courses)

        print("="*50)
        print("Programme terminé !")
        print("="*50)

        # Demander si on recommence
        restart = input("Voulez-vous recommencer le programme ? (oui/non) : ").lower()
        if restart not in ["oui", "o", "yes", "y"]:
            print("Au revoir !")
            break
