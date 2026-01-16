# Demander la taille du tableau
table_taille = int(input("DONNER LA TAILLE DE TABLEAU : "))

# Créer une liste vide
liste = []

# Demander à l'utilisateur de saisir les éléments
print(f"Saisir {table_taille} éléments :")
for i in range(table_taille):
    element = int(input(f"Élément {i+1} : "))
    liste.append(element)

# Afficher la liste saisie
print("\nInput:", liste)
print("Output:")

# Créer un dictionnaire vide pour stocker les fréquences
frequences = {}

# Parcourir chaque élément de la liste
for element in liste:
    # Si l'élément existe déjà, incrémenter son compteur
    if element in frequences:
        frequences[element] += 1
    # Sinon, l'initialiser à 1
    else:
        frequences[element] = 1

# Afficher les fréquences
for element, frequence in frequences.items():
    print(f"{element} -> {frequence}")