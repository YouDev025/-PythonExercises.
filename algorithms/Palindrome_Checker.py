# Demander la chaîne à vérifier
chaine = input("Entrer une chaîne de caractères : ")

# Convertir en minuscules et enlever les espaces pour une meilleure vérification
chaine_nettoyee = chaine.lower().replace(" ", "")

print(f"\nChaîne originale : {chaine}")
print(f"Chaîne nettoyée : {chaine_nettoyee}")
print()

# Vérifier si c'est un palindrome
est_palindrome = True
longueur = len(chaine_nettoyee)

# Comparer caractère par caractère depuis les extrémités
for i in range(longueur // 2):
    print(
        f"Comparaison : '{chaine_nettoyee[i]}' (position {i}) avec '{chaine_nettoyee[longueur - 1 - i]}' (position {longueur - 1 - i})")

    if chaine_nettoyee[i] != chaine_nettoyee[longueur - 1 - i]:
        est_palindrome = False
        break

# Afficher le résultat
print("\n" + "=" * 50)
if est_palindrome:
    print(f"✓ '{chaine}' est un PALINDROME")
else:
    print(f"✗ '{chaine}' n'est PAS un palindrome")

print("\n" + "=" * 50)
print("EXEMPLES PRÉDÉFINIS :")
print("=" * 50)

# Liste d'exemples
exemples = ["radar", "kayak", "hello", "A man a plan a canal Panama", "noon", "python"]

for exemple in exemples:
    chaine_test = exemple.lower().replace(" ", "")
    est_palindrome_test = True
    longueur_test = len(chaine_test)

    for i in range(longueur_test // 2):
        if chaine_test[i] != chaine_test[longueur_test - 1 - i]:
            est_palindrome_test = False
            break

    resultat = "✓ PALINDROME" if est_palindrome_test else "✗ PAS palindrome"
    print(f"{exemple:30} → {resultat}")