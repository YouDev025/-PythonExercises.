# Demander la valeur de n
n = int(input("Entrer la valeur de n (nombre maximum) : "))

# Créer la liste avec n-1 éléments
arr = []
print(f"\nSaisir {n-1} nombres entre 1 et {n} :")
for i in range(n - 1):
    nombre = int(input(f"Nombre {i + 1} : "))
    arr.append(nombre)

print(f"\nListe saisie : {arr}")
print(f"Recherche du nombre manquant entre 1 et {n}...")

# Calculer la somme attendue de 1 à n
somme_attendue = 0
for i in range(1, n + 1):
    somme_attendue += i

print(f"\nSomme attendue (1 + 2 + ... + {n}) = {somme_attendue}")

# Calculer la somme réelle de la liste
somme_reelle = 0
for nombre in arr:
    somme_reelle += nombre

print(f"Somme de la liste saisie = {somme_reelle}")

# Trouver le nombre manquant
nombre_manquant = somme_attendue - somme_reelle

print("\n" + "=" * 50)
print(f"✓ Le nombre manquant est : {nombre_manquant}")
print("=" * 50)