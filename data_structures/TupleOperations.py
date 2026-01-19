print("OPÉRATION SUR LES TUPLES !")
print("=" * 50)

stop_programme = True
while stop_programme:
    # Demander le nombre d'éléments
    while True:
        try:
            n = int(input("Combien de nombres voulez-vous saisir ?: "))
            if n <= 0:
                print("Veuillez entrer un nombre positif : ")
                continue
            break
        except ValueError:
            print("Erreur : Valeur invalide ! Veuillez entrer un nombre entier positif.")

    # Saisie des nombres et création du tuple
    liste_nombres = []
    print(f"Veuillez saisir {n} nombres : ")
    for i in range(n):
        while True:
            try:
                nombre = int(input(f"Le nombre {i+1} : "))
                liste_nombres.append(nombre)
                break
            except ValueError:
                print("Entrée invalide ! Veuillez entrer un nombre entier positif.")

    # Création du tuple
    nombre_tuple = tuple(liste_nombres)

    # Affichage des résultats
    print("=" * 50)
    print("Résultats : ")
    print("=" * 50)

    # Tuple d'origine
    print(f"Le tuple original : {nombre_tuple}")

    # Tuple trié
    tuple_trie = tuple(sorted(nombre_tuple))
    print(f"Tuple trié : {tuple_trie}")
    print("=" * 50)

    # Nombres pairs du tuple
    tuple_paires = tuple([x for x in nombre_tuple if x % 2 == 0])
    print(f"Tuple des nombres pairs : {tuple_paires}")

    # Nombre d'occurrences de chaque nombre
    print("=" * 50)
    print("Occurrences des nombres :")
    for nombre in set(nombre_tuple):
        occurrence = nombre_tuple.count(nombre)
        print(f"{nombre} : {occurrence} fois")

    # Vérifier la présence d'un nombre
    print("=" * 50)
    print("Rechercher un nombre dans le tuple !")
    print("=" * 50)
    while True:
        try:
            nombre_rechercher = int(input("Entrez le nombre à rechercher : "))
            break
        except ValueError:
            print("Erreur : Entrée invalide. Veuillez entrer un nombre entier positif !")

    print("=" * 50)
    if nombre_rechercher in nombre_tuple:
        occurrence = nombre_tuple.count(nombre_rechercher)
        print(f"Le nombre {nombre_rechercher} est présent dans le tuple !")
        print(f"Il apparaît {occurrence} fois !")

        # Trouver les positions
        positions = [i for i, val in enumerate(nombre_tuple) if val == nombre_rechercher]
        print(f"Positions : {positions}")
    else:
        print(f"Le nombre {nombre_rechercher} n'est pas présent dans le tuple !")

    print("=" * 50)
    reponse_stop = input("Voulez-vous relancer le programme (oui / non) : ").strip().lower()
    print("=" * 50)
    if reponse_stop in ["non", "n"]:
        print("Programme terminé !")
        stop_programme = False
