print(" COMPTEUR DE NOMBRES UNIQUE !")
print("="*50)
stop_programme = True
while stop_programme :
    #Demander le nombre des elements
    while True:
        try :
            n = int(input("Combien de nombres voulez-vous saisir ? :  "))
            if n <= 0:
                print("Veullez entrer un nombre positif !")
                continue
            break
        except ValueError:
            print("Erreur : Entrée Invalide .Veuillez entrer un nombre entier positive : ")

    #Saisie de nombres
    nombres =[]
    print(f"Veuillez saisir {n} nombres : ")

    for i in range(n):
        while True:
            try:
                nombre = int(input(f"Veuillez le nombre {i+1} : "))
                nombres.append(nombre)
                break
            except ValueError:
                print("Erreur : Entrée Invalide ! Veuillez entrer un nombre entier positif : ")

    #conversion en set pour obtenir les valeurs uniques
    nombres_unique =set(nombres)

    #Affichage des résultats
    print("="*50)
    print("Résultats : ")
    print("="*50)

    print(f"Liste des nombres originales : {nombres}")
    print(f"Nombre uniques : {sorted(nombres_unique)}")
    print(f"Nombre de valeur unique : {len(nombres_unique)}")

    #Plus grand et plus  petit
    max_unique = max(nombres_unique)
    min_unique = min(nombres_unique)

    print(f"Le plus grand nombres unique : {max_unique}")
    print(f"Le plus petit nombres unique : {min_unique}")

    #Calcule de moyenne des nombres uniques
    moyenne = round(sum(nombres_unique)/len(nombres_unique), 2)
    print(f"Moyenne des nombres uniques : {moyenne}")
    print("="*50)
    reponse_arret = input("Veuillez vous relancez le programme (oui / non ): ")
    print("=" * 50)
    if reponse_arret in ["non" , "n"]:
        print("Programme Términé !")
        stop_programme = False

