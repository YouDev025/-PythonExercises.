# Demander la taille du tableau
table_taille = int(input("DONNER LA TAILLE DE TABLEAU : "))

# Créer et remplir le tableau
arr = []
print(f"Saisir {table_taille} éléments (dans l'ordre croissant) :")
for i in range(table_taille):
    element = int(input(f"Élément {i + 1} : "))
    arr.append(element)

# Demander l'élément à rechercher
target = int(input("\nÉlément à rechercher : "))

print(f"\nTableau : {arr}")
print(f"Recherche de : {target}\n")

# Recherche dichotomique
left = 0
right = len(arr) - 1
resultat = -1

while left <= right:
    mid = (left + right) // 2

    print(f"Recherche entre [{left}..{right}], milieu = {mid} (valeur = {arr[mid]})")

    if arr[mid] == target:
        resultat = mid
        break
    elif arr[mid] < target:
        left = mid + 1
    else:
        right = mid - 1

# Afficher le résultat
print("\n" + "=" * 40)
if resultat != -1:
    print(f"✓ Élément {target} trouvé à l'indice {resultat}")
else:
    print(f"✗ Élément {target} non trouvé (retour : -1)")