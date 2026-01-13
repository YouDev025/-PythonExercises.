print("-" * 20 + "EmployeeRecordSystem" + "-" * 20)

# 1. Initialiser la liste en dehors de la boucle principale pour ne pas perdre les données
employes = []
continuer = True

while continuer:
    print("\n=== CRÉATION D'UN ENREGISTREMENT EMPLOYÉ ===\n")

    n_str = input("Combien d'employés voulez-vous enregistrer pour cette session ? ")

    # Validation du nombre d'employés
    if not n_str.isdigit():
        print("Erreur : veuillez entrer un nombre entier valide !")
        continue  # Retourne au début de la boucle while

    n = int(n_str)

    if n <= 0:
        print("Erreur : le nombre d'employés doit être supérieur à 0 !")
        continue

    # Boucle pour chaque employé
    for i in range(n):
        print(f"\n--- Enregistrement de l'employé {i + 1} sur {n} ---")

        # ID (Boucle de validation)
        while True:
            employee_id = input("Entrer l'ID de l'employé : ").strip()
            if employee_id:
                break
            print("Erreur : l'ID ne peut pas être vide !")

        # Nom (Boucle de validation)
        while True:
            nom = input("Entrer le nom de l'employé : ").strip()
            if nom:
                break
            print("Erreur : le nom ne peut pas être vide !")

        # Salaire (Boucle de validation)
        while True:
            salaire_str = input("Entrer le salaire de l'employé : ").strip()
            try:
                salaire = float(salaire_str)
                if salaire > 0:
                    break
                print("Erreur : le salaire doit être supérieur à 0 !")
            except ValueError:
                print("Erreur : veuillez entrer un nombre valide (ex: 5000.50)")

        # Création et ajout du tuple
        employe = (employee_id, nom, salaire)
        employes.append(employe)
        print(f"-> Employé {nom} ajouté avec succès.")

    # Demander si l'utilisateur veut continuer une nouvelle session
    reponse = input("\nVoulez-vous ajouter un autre groupe d'employés ? (oui/non) : ").strip().lower()
    if "non" in reponse:
        continuer = False
        print("\n" + "-" * 20 + "PROGRAMME TERMINÉ" + "-" * 20)

# Afficher le résumé FINAL
print("\n" + "=" * 50)
print("RÉCAPITULATIF FINAL DE TOUS LES EMPLOYÉS")
print("=" * 50)
print(
    f"Nombre total d'employés enregistrés : {len(employes)}")  # J'ai retiré 'MAD' ici car c'est un nombre, pas un prix
print("-" * 50)

if len(employes) > 0:
    print(f"{'ID':<10} | {'NOM':<20} | {'SALAIRE':<10}")
    print("-" * 50)
    for emp in employes:
        # emp[0] est l'ID, emp[1] le Nom, emp[2] le Salaire
        print(f"{emp[0]:<10} | {emp[1]:<20} | {emp[2]:<10.2f} MAD")
else:
    print("Aucun employé enregistré.")

print("=" * 50)