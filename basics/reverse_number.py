continuer = True

while continuer:
    number = input("Entrer un numero: ")

    while not number.isdigit() or int(number) < 0:
        print("Valeur invalide. Veuillez entrer un nombre positif.")
        number = input("Entrer un numero: ")

    inverse = number[::-1]
    print(f"---- Le {number} inversé est {inverse} ----")
    print("------------------------------------------")

    reponse = input("Voulez-vous inverser un autre nombre ? (oui/non) : ")
    if reponse.lower() == "non" or reponse.lower() == "n":
        continuer = False

print("Merci d'avoir utilisé le programme !")

'''
2ème méthode 
number = int(input("Donner un nombre: "))

reversed_number = 0
while number > 0:
    digit = number % 10  # Extraire le dernier chiffre
    reversed_number = reversed_number * 10 + digit  # Ajouter au résultat
    number = number // 10  # Supprimer le dernier chiffre

print(f"Le nombre inversé est {reversed_number}")
'''