stop_programme = True
while stop_programme:
    print("=" * 50)
    print("** JEU DES OPÉRATIONS SUR LES ENSEMBLES **")
    print("=" * 50)

    # Demander la 1ère liste de nombres
    print("Entrez la première liste de nombres (séparés par des espaces) :")
    input1 = input("Liste 1 : ")
    liste1 = [int(x) for x in input1.split()]
    print("=" * 50)

    # Demander la 2ème liste de nombres
    print("Entrez la deuxième liste de nombres (séparés par des espaces) :")
    input2 = input("Liste 2 : ")
    liste2 = [int(x) for x in input2.split()]

    # Convertir en sets
    set1 = set(liste1)
    set2 = set(liste2)

    # Affichage des sets
    print("=" * 50)
    print("Résultats :")
    print(f"Set 1 : {sorted(set1)}")
    print(f"Set 2 : {sorted(set2)}")

    # Éléments uniques pour les 2 sets
    print("=" * 50)
    unique_set1 = set1 - set2
    unique_set2 = set2 - set1
    print(f"Éléments UNIQUES au Set 1 : {sorted(unique_set1) if unique_set1 else 'Aucun'}")
    print(f"Éléments UNIQUES au Set 2 : {sorted(unique_set2) if unique_set2 else 'Aucun'}")

    # Intersection des 2 sets
    print("=" * 50)
    communs = set1 & set2
    print(f"Éléments communs : {sorted(communs) if communs else 'Aucun'}")

    # Union des 2 sets
    print("=" * 50)
    union = set1 | set2
    print(f"UNION des deux sets : {sorted(union)}")

    # Nombre total d'éléments distincts
    print("=" * 50)
    print(f"Nombre TOTAL des éléments DISTINCTS : {len(union)}")

    # Statistiques des 2 sets
    print("=" * 50)
    print("STATISTIQUES DES 2 SETS :")
    print(f"Taille du Set 1 : {len(set1)}")
    print(f"Taille du Set 2 : {len(set2)}")
    print(f"Éléments en commun : {len(communs)}")
    print(f"Éléments distincts : {len(union)}")
    print("=" * 50)

    # Demander si on recommence
    reponse = input("Voulez-vous recommencer une autre fois [oui/non] : ")
    if reponse.lower() in ["non", "n"]:
        stop_programme = False
