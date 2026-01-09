print("--- Calculateur de Signe du Produit ---")

Continuer = True

while Continuer:
    # ---------------------------------------------------------
    # Etape 1 : Demander la 1ere valeur avec vérification
    # ---------------------------------------------------------
    valeur_a = ""
    valide_a = False

    while not valide_a:
        valeur_a = input("Entrer la 1ere valeur : ")

        # 1. Vérifier si vide
        if valeur_a.strip() == "":
            print("Erreur : Vous avez un champ vide !")
            continue  # On recommence la boucle

        # 2. Vérification manuelle (Est-ce un nombre ?)
        # On crée une copie temporaire pour tester
        temp = valeur_a.strip()

        # Si ça commence par un tiret (négatif), on l'enlève pour le test
        if temp.startswith("-"):
            temp = temp[1:]

        # On enlève le premier point décimal trouvé pour le test (ex: "12.5" devient "125")
        temp = temp.replace(".", "", 1)

        # Maintenant, il ne doit rester que des chiffres
        if temp.isdigit():
            valide_a = True  # C'est bon, on sort de la boucle
        else:
            print(f"Erreur : '{valeur_a}' n'est pas un nombre valide (pas de lettres) !")

    # ---------------------------------------------------------
    # Etape 2 : Demander la 2eme valeur avec vérification
    # ---------------------------------------------------------
    valeur_b = ""
    valide_b = False

    while not valide_b:
        valeur_b = input("Entrer la 2eme valeur : ")

        if valeur_b.strip() == "":
            print("Erreur : Vous avez un champ vide !")
            continue

        temp = valeur_b.strip()
        if temp.startswith("-"):
            temp = temp[1:]
        temp = temp.replace(".", "", 1)

        if temp.isdigit():
            valide_b = True
        else:
            print(f"Erreur : '{valeur_b}' n'est pas un nombre valide (pas de lettres) !")

    # ---------------------------------------------------------
    # Etape 3 : Conversion et Calcul
    # ---------------------------------------------------------
    # Ici, on est sûr à 100% que float() ne plantera pas
    a = float(valeur_a)
    b = float(valeur_b)

    produit = a * b

    if produit == 0:
        print(f"Le produit de {a} X {b} = {produit} ( PRODUIT NUL )")
    elif produit > 0:
        print(f"Le produit de {a} X {b} = {produit} ( PRODUIT POSITIF )")
    else:
        print(f"Le produit de {a} X {b} = {produit} ( PRODUIT NÉGATIF )")

    print("-------------------------------------------------------------------")

    # ---------------------------------------------------------
    # Etape 4 : Continuer ?
    # ---------------------------------------------------------
    Reponse = input("Voulez-vous continuer (oui / non )? : ")
    if Reponse.lower() == "non" or Reponse.lower() == "n":
        Continuer = False

print("Merci d'avoir utilisé mon programme !")