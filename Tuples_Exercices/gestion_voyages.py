# Demander et valider le nombre de voyages
while True:
    nombre_voyages_str = input("Combien de voyages voulez-vous enregistrer ? ")
    # Vérifie si c'est un nombre
    if nombre_voyages_str.isdigit():
        nombre_voyages = int(nombre_voyages_str)
        if nombre_voyages > 0:
            break
        elif nombre_voyages <= 0:
            print("⚠️ Le nombre de voyages doit être supérieur à 0. Réessayez.\n")
    else:
        print("⚠️ Veuillez entrer un nombre valide.\n")

print()

# Collecter les voyages
voyages = []

for i in range(1, nombre_voyages + 1):
    print(f"=== Voyage {i} ===")

    destination = input("La destination : ")

    # Validation du nombre de jours
    while True:
        jours_str = input("Le nombre de jours : ")
        if jours_str.isdigit():
            nombre_jours = int(jours_str)
            if nombre_jours > 0:
                break
            else:
                print("⚠️ Le nombre de jours doit être supérieur à 0.\n")
        else:
            print("⚠️ Veuillez entrer un nombre valide.\n")

    # Validation du budget
    while True:
        budget_str = input("Le budget (MAD) : ")
        if budget_str.isdigit():
            budget = int(budget_str)
            if budget > 0:
                break
            else:
                print("⚠️ Le budget doit être supérieur à 0.\n")
        else:
            print("⚠️ Veuillez entrer un nombre valide.\n")

    # Validation du nombre de personnes
    while True:
        personnes_str = input("Le nombre de personnes : ")
        if personnes_str.isdigit():
            nombre_personnes = int(personnes_str)
            if nombre_personnes > 0:
                break
            else:
                print("⚠️ Le nombre de personnes doit être supérieur à 0.\n")
        else:
            print("⚠️ Veuillez entrer un nombre valide.\n")

    voyage = (destination, nombre_jours, budget, nombre_personnes)
    voyages.append(voyage)
    print("##########################################\n")

# Convertir en tuple (une seule fois, après la boucle)
voyages = tuple(voyages)

# Afficher le résumé (après avoir collecté tous les voyages)
print("=== LES VOYAGES ENREGISTRÉS ===\n")

for i, (destination, jours, budget, personnes) in enumerate(voyages, start=1):
    print(f"{i}. {destination} - {jours} jours - {budget} MAD - {personnes} personnes")
