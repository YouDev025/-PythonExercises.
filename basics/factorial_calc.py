continuer = True

while continuer:
    number = int(input("Entrez un nombre : "))
    print(f"---------- FACTORIELLE DE {number} ------------")

    while number < 0:
        print("ERREUR : La factorielle n'est pas définie pour les nombres négatifs.")
        print("La valeur doit être positive ou égale à 0.")
        number = int(input("Entrez un nombre : "))

    f = 1
    for i in range(2, number + 1):
        f *= i

    print(f"Factorielle de {number}! = {f}")
    print("------------------------------------------")

    reponse = input("Voulez-vous calculer une autre factorielle ? (oui/non) : ")
    if reponse.lower() != "oui":
        continuer = False

print("Merci d'avoir utilisé le programme !")