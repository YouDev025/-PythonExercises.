print(" COMPTEUR DE NOMBRES UNIQUES !")
print("=" * 50)

stop_programme = True
while stop_programme:
    # Demander le nombre des éléments
    while True:
        try:
            n = int(input("Combien de nombres voulez-vous saisir ? : "))
            if n <= 0:
                print("Veuillez entrer un nombre entier positif !")
                continue
            break
        except ValueError:
            print("Erreur : Entrée invalide. Veuillez entrer un nombre entier positif.")

    # Saisie des nombres
    nombres = []
    print(f"Veuillez saisir {n} nombres : ")

    for i in range(n):
        while True:
            try:
                nombre = int(input(f"Veuillez entrer le nombre {i+1} : "))
                nombres.append(nombre)
                break
            except ValueError:
                print("Erreur : Entrée invalide ! Veuillez entrer un nombre entier.")

    # Conversion en set pour obtenir les valeurs uniques
    nombres_unique = set(nombres)

    # Affichage des résultats
    print("=" * 50)
    print("Résultats : ")
    print("=" * 50)

    print(f"Liste des nombres originaux : {nombres}")
    print(f"Nombres uniques : {sorted(nombres_unique)}")
    print(f"Nombre de valeurs uniques : {len(nombres_unique)}")

    # Plus grand et plus petit
    max_unique = max(nombres_unique)
    min_unique = min(nombres_unique)

    print(f"Le plus grand nombre unique : {max_unique}")
    print(f"Le plus petit nombre unique : {min_unique}")

    # Calcul de la moyenne des nombres uniques
    moyenne = round(sum(nombres_unique) / len(nombres_unique), 2)
    print(f"Moyenne des nombres uniques : {moyenne}")
    print("=" * 50)

    # Relance du programme
    reponse_arret = input("Voulez-vous relancer le programme ? (oui / non) : ").strip().lower()
    print("=" * 50)
    if reponse_arret in ["non", "n"]:
        print("Programme terminé !")
        stop_programme = False
