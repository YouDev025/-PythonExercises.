print("---------------------AVERAGE OF NUMBERS---------------------------")

continuer = True

while continuer:
    n = int(input("Entrer le nombre des valeurs voulez vous calculer la moyenne : "))

    if n <= 0:
        print("Le nombre n'est pas valide, doit être positif!")
    elif n == 1:
        print("La moyenne de 1 est: 1")
    else:
        somme = 0
        for i in range(1, n + 1):
            nombre = float(input(f"Entrer la valeur {i}: "))
            somme += nombre

        moyenne = somme / n

        # Affichage du résultat
        print("\n" + "=" * 40)
        print(f"Nombre de valeurs: {n}")
        print(f"La somme totale: {somme}")
        print(f"La moyenne est: {moyenne:.2f}")
        print("=" * 40)

    reponse = input("\nVoulez-vous recalculer une autre moyenne (oui/non): ")
    if reponse.lower() in ["non", "n"]:
        continuer = False
        print("Merci d'avoir utilisé le programme!")