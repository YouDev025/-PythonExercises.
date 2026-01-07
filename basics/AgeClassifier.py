continuer = True

while continuer:
    age = int(input("Entrez votre âge : "))

    while age < 6:
        print("Valeur invalide. L'âge minimum est 6 ans.")
        age = int(input("Entrez votre âge : "))

    if 6 <= age <= 7:
        print("Vous êtes GAMIN")
    elif 8 <= age <= 9:
        print("Vous êtes PUPILLE")
    elif 10 <= age <= 11:
        print("Vous êtes JEUNE")
    elif 12 <= age <= 17:
        print("Vous êtes CADET")
    elif age >= 18:
        print("Vous êtes ADULTE")

    print("------------------------------------------")
    reponse = input("Voulez-vous vérifier un autre âge ? (oui/non) : ")
    if reponse.lower() != "oui":
        continuer = False

print("Merci d'avoir utilisé le programme !")