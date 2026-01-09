# Programme pour calculer la valeur absolue d'un nombre
# Avec deux méthodes différentes

# Demander le premier nombre à l'utilisateur
number = int(input("Entrer un numero: "))
continuer = True

while continuer:
    print("------------------------------------------")

    # Méthode 1 : Utilisation de la fonction abs()
    valeur_abs_1 = abs(number)
    print(f"Méthode 1 (fonction abs()): La valeur absolue de {number} est : {valeur_abs_1}")

    # Méthode 2 : Utilisation d'une condition if/else
    if number >= 0:
        valeur_abs_2 = int(number)
    else:
        valeur_abs_2 = int(-number) # Inverser le signe si négatif
    print(f"Méthode 2 (condition if/else): La valeur absolue de {number} est : {valeur_abs_2}")
    print("------------------------------------------")

    # Demander à l'utilisateur s'il veut continuer
    reponse = input("Voulez-vous calculer une nouvelle valeur absolue d'un nombre (oui/non) : ")

    # Vérifier la réponse (convertie en minuscules pour accepter OUI, Oui, oui, etc.)
    if reponse.lower() != "oui":
        continuer = False  # Arrêter la boucle
    else:
        # Demander un nouveau nombre
        number = int(input("Entrer un numero: "))

# Message de fin
print("MERCI")