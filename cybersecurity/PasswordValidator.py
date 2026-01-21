print("="*50)
print("VALIDATION DE MOT DE PASSE")
print("="*50)

# Critères du mot de passe
print("Critères requis pour un mot de passe valide :")
print("1- Au moins 8 caractères")
print("2- Au moins 1 chiffre (0-9)")
print("3- Au moins 1 lettre majuscule (A-Z)")
print("4- Au moins 1 caractère spécial (!@#$%*-+....)")
print("="*50)

# Définir les ensembles de caractères
chiffres = set('0123456789')
majuscules = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
caracteres_speciaux = set("!@#$%^&*()-_=+[]{}|;:,.<>?/~`")

# Limiter à 3 tentatives
tentatives_max = 3
tentatives = 0

# Boucle de validation
mot_de_passe_valide = False
while tentatives < tentatives_max and not mot_de_passe_valide:
    tentatives += 1
    print(f"Tentative # {tentatives}/{tentatives_max}")
    mot_de_passe = input("Entrez un mot de passe : ")
    print("="*50)

    # Initialiser les critères
    longueur_ok = len(mot_de_passe) >= 8
    a_chiffre = any(c in chiffres for c in mot_de_passe)
    a_majuscule = any(c in majuscules for c in mot_de_passe)
    a_special = any(c in caracteres_speciaux for c in mot_de_passe)

    # Afficher les résultats de validation
    print("="*50)
    print("ANALYSE DU MOT DE PASSE")
    print("="*50)

    print(f"Longueur : {len(mot_de_passe)} caractères {'OK' if longueur_ok else '(minimum 8 requis !)'}")
    print("Contient au moins 1 chiffre" if a_chiffre else "Aucun chiffre trouvé !")
    print("Contient au moins 1 majuscule" if a_majuscule else "Aucune majuscule trouvée !")
    print("Contient au moins 1 caractère spécial" if a_special else "Aucun caractère spécial trouvé !")
    print("="*50)

    # Vérification si tous les critères sont remplis
    if longueur_ok and a_chiffre and a_special and a_majuscule:
        mot_de_passe_valide = True
        print("FÉLICITATIONS ! VOTRE MOT DE PASSE EST VALIDE !")

        # Évaluer la force du mot de passe
        force = 0
        if len(mot_de_passe) >= 12:
            force += 1
        if sum(c in chiffres for c in mot_de_passe) >= 2:
            force += 1
        if sum(c in majuscules for c in mot_de_passe) >= 2:
            force += 1
        if sum(c in caracteres_speciaux for c in mot_de_passe) >= 2:
            force += 1

        print("="*50)
        print("FORCE DU MOT DE PASSE")
        print("="*50)
        if force == 0:
            print("Faible")
        elif force == 1:
            print("Bon mot de passe")
        elif force == 2:
            print("Très bon mot de passe")
        elif force == 3:
            print("Excellent mot de passe")
        else:
            print("Exceptionnel mot de passe")
    else:
        if tentatives < tentatives_max:
            print("MOT DE PASSE INVALIDE. Réessayez !")
        else:
            print("ÉCHEC ! Nombre maximum de tentatives atteint.")

# Résultat final
print("="*50)
if mot_de_passe_valide:
    print("Votre mot de passe a été accepté avec succès !")
else:
    print("Validation échouée. Veuillez réessayer plus tard.")
    print("Conseils pour un mot de passe fort :")
    print("  • Utilisez au moins 12 caractères")
    print("  • Mélangez majuscules, minuscules, chiffres et symboles")
    print("  • Évitez les mots du dictionnaire")
    print("  • N'utilisez pas d'informations personnelles")

print("="*60)
