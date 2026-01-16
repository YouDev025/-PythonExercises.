# Demander une phrase à l'utilisateur
phrase = input("Entrer une phrase : ")

print(f"\nPhrase saisie : {phrase}")
print("Recherche du mot le plus long...\n")

# Séparer la phrase en mots
mots = phrase.split()

print(f"Mots trouvés : {mots}")
print(f"Nombre de mots : {len(mots)}\n")

# Trouver le mot le plus long
mot_plus_long = ""
longueur_max = 0

for mot in mots:
    longueur_actuelle = len(mot)
    print(f"Mot : '{mot}' → longueur = {longueur_actuelle}")

    if longueur_actuelle > longueur_max:
        longueur_max = longueur_actuelle
        mot_plus_long = mot

# Afficher le résultat
print("\n" + "=" * 50)
print(f"✓ Le mot le plus long est : '{mot_plus_long}'")
print(f"✓ Longueur : {longueur_max} caractères")
print("=" * 50)
"""exemples = [
    "Python est un langage de programmation",
    "Le chat mange une pomme",
    "Algorithme recherche dichotomique",
    "Bonjour monde"
]
"""