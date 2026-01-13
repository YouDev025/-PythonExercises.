print("-" * 20 + "ShoppingCartAnalyzer" + "-" * 20)

continuer = True

while continuer:
    # Vérification du nombre d'articles
    n_str = input("Combien d'articles voulez-vous ajouter au panier ? ")
    if not n_str.isdigit():
        print("Erreur : vous devez entrer un nombre entier valide !")
        continue
    n = int(n_str)

    if n <= 0:
        print("Le nombre d'articles doit être supérieur à 0 !")
    else:
        # Créer une liste de prix
        prix = []

        for i in range(n):
            article_prix_str = input(f"Entrer le prix de l'article {i + 1} : ")

            # Vérification que le prix est bien un nombre
            try:
                article_prix = float(article_prix_str)
                if article_prix < 0:
                    print("Erreur : le prix ne peut pas être négatif !")
                    continue
                prix.append(article_prix)
            except ValueError:
                print("Erreur : veuillez entrer un prix valide (nombre) !")
                continue

        # Affichage des résultats seulement si la liste n'est pas vide
        if prix:
            print("\n" + "=" * 50)
            print("ANALYSE DU PANIER D'ACHAT")
            print("=" * 50)
            print(f"Liste des prix           : {prix}")
            print(f"Prix le plus cher        : {max(prix):.2f} €")
            print(f"Prix le moins cher       : {min(prix):.2f} €")
            print(f"Prix triés (croissant)   : {sorted(prix)}")
            print(f"Total du panier          : {sum(prix):.2f} €")
            print(f"Prix moyen               : {sum(prix)/len(prix):.2f} €")
            print("=" * 50 + "\n")
        else:
            print("Aucun prix valide n'a été saisi.")

    # Vérification de la réponse oui/non
    reponse = input("Voulez-vous analyser un autre panier ? (oui/non) : ").strip().lower()
    if reponse == "non":
        continuer = False
        print("\n" + "-" * 20 + "PROGRAMME TERMINÉ" + "-" * 20)
    elif reponse != "oui":
        print("Réponse invalide ! Tapez seulement 'oui' ou 'non'.")
