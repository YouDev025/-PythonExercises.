def elements_uniques(liste1, liste2):
    # Vérification des types
    if not isinstance(liste1, list) or not isinstance(liste2, list):
        print("Erreur : Les deux paramètres doivent être des listes.")
        return {}

    print("="*50)
    print("Analyse des éléments uniques et communs")
    print("="*50)
    print(f"Liste 1 : {liste1}")
    print(f"Liste 2 : {liste2}")
    print("="*50)

    # Conversion en sets
    set1 = set(liste1)
    set2 = set(liste2)

    # Éléments communs
    communs = set1.intersection(set2)

    # Éléments uniques à chaque liste
    uniques_liste1 = set1.difference(set2)
    uniques_liste2 = set2.difference(set1)

    # Affichage des résultats
    print("Éléments communs :", communs)
    print("Éléments uniques à la liste 1 :", uniques_liste1)
    print("Éléments uniques à la liste 2 :", uniques_liste2)

    return {
        "communs": communs,
        "uniques_liste1": uniques_liste1,
        "uniques_liste2": uniques_liste2
    }


# Programme principal avec redémarrage
if __name__ == "__main__":
    while True:  # boucle principale pour recommencer le programme
        print("="*50)
        print("Programme : Éliminer les doublons avec des sets")
        print("="*50)

        # Saisie des listes
        try:
            taille1 = int(input("Combien d'éléments dans la liste 1 ? : "))
            taille2 = int(input("Combien d'éléments dans la liste 2 ? : "))
        except ValueError:
            print("Erreur : Veuillez entrer des nombres valides.")
            continue

        liste1 = []
        liste2 = []

        # Remplir liste 1
        for i in range(taille1):
            element = input(f"Élément {i+1} de la liste 1 : ").strip()
            liste1.append(element)

        # Remplir liste 2
        for i in range(taille2):
            element = input(f"Élément {i+1} de la liste 2 : ").strip()
            liste2.append(element)

        # Appel de la fonction
        resultat = elements_uniques(liste1, liste2)

        print("="*50)
        print("Programme terminé !")
        print("="*50)

        # Demander si on recommence
        restart = input("Voulez-vous recommencer le programme complet ? (oui/non) : ").lower()
        if restart not in ["oui", "o", "yes", "y"]:
            print("Au revoir")
            break
