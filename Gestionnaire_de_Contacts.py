# ============================================
# GESTIONNAIRE DE CONTACTS
# ============================================
# Programme pour gérer un répertoire de contacts
# avec nom, téléphone et email

# --- INITIALISATION DES LISTES ---
# Trois listes parallèles pour stocker les informations
noms = []  # Liste des noms
telephones = []  # Liste des numéros de téléphone
emails = []  # Liste des emails

# --- BOUCLE PRINCIPALE ---
while True:
    # Afficher le menu principal
    print("\n" + "=" * 40)
    print("📱 GESTIONNAIRE DE CONTACTS")
    print("=" * 40)
    print(f"Total : {len(noms)} contact(s)")
    print("\n1. ➕ Ajouter un contact")
    print("2. 📋 Afficher tous les contacts")
    print("3. 🔍 Chercher un contact")
    print("4. ✏️  Modifier un contact")
    print("5. ❌ Supprimer un contact")
    print("6. 📊 Nombre de contacts")
    print("7. 🔤 Trier par nom")
    print("8. 📧 Contacts sans email")
    print("9. 🚪 Quitter")

    # Demander le choix de l'utilisateur
    choix = input("\nVotre choix : ")

    # ==========================================
    # OPTION 1 : AJOUTER UN CONTACT
    # ==========================================
    if choix == "1":
        print("\n--- AJOUTER UN CONTACT ---")

        # Demander les informations
        nom = input("Nom : ")
        telephone = input("Téléphone : ")
        email = input("Email (Entrée pour passer) : ")

        # Ajouter aux trois listes en même temps
        # Important : ajouter au même moment pour garder les index synchronisés
        noms.append(nom)
        telephones.append(telephone)
        emails.append(email)  # Peut être une chaîne vide ""

        print(f"✅ Contact '{nom}' ajouté avec succès !")

    # ==========================================
    # OPTION 2 : AFFICHER TOUS LES CONTACTS
    # ==========================================
    elif choix == "2":
        print("\n--- TOUS LES CONTACTS ---")

        # Vérifier si la liste est vide
        if len(noms) == 0:
            print("📭 Aucun contact dans le répertoire")
        else:
            # Parcourir tous les contacts avec leur index
            for i in range(len(noms)):
                print(f"\n{i + 1}. {noms[i]}")
                print(f"   📞 {telephones[i]}")

                # Afficher l'email seulement s'il n'est pas vide
                if emails[i] != "":
                    print(f"   📧 {emails[i]}")
                else:
                    print("   📧 Pas d'email")

    # ==========================================
    # OPTION 3 : CHERCHER UN CONTACT
    # ==========================================
    elif choix == "3":
        print("\n--- CHERCHER UN CONTACT ---")

        # Demander le nom à chercher
        recherche = input("Nom à chercher : ")

        # Variable pour savoir si on a trouvé au moins un contact
        trouve = False

        # Parcourir tous les contacts
        for i in range(len(noms)):
            # Comparer en minuscules pour ignorer la casse
            # "in" permet de chercher une partie du nom
            if recherche.lower() in noms[i].lower():
                trouve = True

                # Afficher le contact trouvé
                print(f"\n✅ Contact trouvé :")
                print(f"   Nom : {noms[i]}")
                print(f"   📞 {telephones[i]}")

                if emails[i] != "":
                    print(f"   📧 {emails[i]}")
                else:
                    print("   📧 Pas d'email")

        # Si aucun contact trouvé
        if not trouve:
            print(f"❌ Aucun contact trouvé pour '{recherche}'")

    # ==========================================
    # OPTION 4 : MODIFIER UN CONTACT
    # ==========================================
    elif choix == "4":
        print("\n--- MODIFIER UN CONTACT ---")

        # Vérifier si la liste est vide
        if len(noms) == 0:
            print("📭 Aucun contact à modifier")
        else:
            # Afficher tous les contacts avec numéros
            print("\nContacts :")
            for i in range(len(noms)):
                print(f"{i + 1}. {noms[i]} - {telephones[i]}")

            # Demander quel contact modifier
            try:
                num = int(input("\nNuméro du contact à modifier : "))

                # Vérifier que le numéro est valide
                if 1 <= num <= len(noms):
                    index = num - 1  # Convertir en index (commence à 0)

                    print(f"\nModification de : {noms[index]}")
                    print("(Appuyez sur Entrée pour garder la valeur actuelle)")

                    # Demander les nouvelles valeurs
                    nouveau_nom = input(f"Nouveau nom [{noms[index]}] : ")
                    nouveau_tel = input(f"Nouveau téléphone [{telephones[index]}] : ")
                    nouvel_email = input(f"Nouvel email [{emails[index]}] : ")

                    # Modifier seulement si l'utilisateur a entré quelque chose
                    if nouveau_nom != "":
                        noms[index] = nouveau_nom

                    if nouveau_tel != "":
                        telephones[index] = nouveau_tel

                    # Pour l'email, on accepte même une chaîne vide
                    if nouvel_email != emails[index]:
                        emails[index] = nouvel_email

                    print("✅ Contact modifié avec succès !")
                else:
                    print("❌ Numéro invalide")

            except ValueError:
                print("❌ Veuillez entrer un nombre valide")

    # ==========================================
    # OPTION 5 : SUPPRIMER UN CONTACT
    # ==========================================
    elif choix == "5":
        print("\n--- SUPPRIMER UN CONTACT ---")

        # Vérifier si la liste est vide
        if len(noms) == 0:
            print("📭 Aucun contact à supprimer")
        else:
            # Afficher tous les contacts
            print("\nContacts :")
            for i in range(len(noms)):
                print(f"{i + 1}. {noms[i]} - {telephones[i]}")

            # Demander quel contact supprimer
            try:
                num = int(input("\nNuméro du contact à supprimer : "))

                # Vérifier que le numéro est valide
                if 1 <= num <= len(noms):
                    index = num - 1  # Convertir en index

                    # Demander confirmation
                    confirmation = input(f"Êtes-vous sûr de supprimer '{noms[index]}' ? (oui/non) : ")

                    if confirmation.lower() == "oui":
                        # Supprimer des trois listes en même temps
                        # Important : pop() au même index pour garder la cohérence
                        nom_supprime = noms.pop(index)
                        telephones.pop(index)
                        emails.pop(index)

                        print(f"✅ Contact '{nom_supprime}' supprimé")
                    else:
                        print("❌ Suppression annulée")
                else:
                    print("❌ Numéro invalide")

            except ValueError:
                print("❌ Veuillez entrer un nombre valide")

    # ==========================================
    # OPTION 6 : NOMBRE DE CONTACTS
    # ==========================================
    elif choix == "6":
        nombre = len(noms)
        print(f"\n📊 Vous avez {nombre} contact(s) dans votre répertoire")

        # Statistiques supplémentaires
        if nombre > 0:
            # Compter combien ont un email
            avec_email = 0
            for email in emails:
                if email != "":
                    avec_email += 1

            sans_email = nombre - avec_email

            print(f"   - Avec email : {avec_email}")
            print(f"   - Sans email : {sans_email}")

    # ==========================================
    # OPTION 7 : TRIER PAR NOM
    # ==========================================
    elif choix == "7":
        print("\n--- TRIER LES CONTACTS ---")

        if len(noms) == 0:
            print("📭 Aucun contact à trier")
        else:
            # Créer une liste de tuples (triplets) pour garder les infos ensemble
            # Chaque tuple contient : (nom, téléphone, email)
            contacts = []
            for i in range(len(noms)):
                contacts.append((noms[i], telephones[i], emails[i]))

            # Trier la liste de tuples par le premier élément (le nom)
            contacts.sort()

            # Vider les listes originales
            noms.clear()
            telephones.clear()
            emails.clear()

            # Remplir à nouveau les listes avec les données triées
            for contact in contacts:
                noms.append(contact[0])  # Nom
                telephones.append(contact[1])  # Téléphone
                emails.append(contact[2])  # Email

            print("✅ Contacts triés par ordre alphabétique !")

    # ==========================================
    # OPTION 8 : CONTACTS SANS EMAIL
    # ==========================================
    elif choix == "8":
        print("\n--- CONTACTS SANS EMAIL ---")

        # Compter et afficher les contacts sans email
        trouve = False

        for i in range(len(noms)):
            # Si l'email est une chaîne vide
            if emails[i] == "":
                trouve = True
                print(f"- {noms[i]} : {telephones[i]}")

        if not trouve:
            print("✅ Tous les contacts ont un email !")

    # ==========================================
    # OPTION 9 : QUITTER
    # ==========================================
    elif choix == "9":
        print("\n👋 Au revoir ! Merci d'avoir utilisé le gestionnaire de contacts")
        break  # Sortir de la boucle while

    # ==========================================
    # CHOIX INVALIDE
    # ==========================================
    else:
        print("\n❌ Choix invalide ! Veuillez choisir entre 1 et 9")

# Fin du programme