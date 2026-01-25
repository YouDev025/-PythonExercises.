def afficher_personnes(personnes):
    print("="*50)
    print("Liste des personnes :")
    if personnes:
        for i, p in enumerate(personnes, start=1):
            nom = p.get("nom", "Inconnu")
            age = p.get("age", "Non renseigné")
            print(f"{i}. Nom: {nom}, Âge: {age}")
    else:
        print("Aucune personne disponible.")
    print("="*50)


def ajouter_personne(personnes):
    nom = input("Nom : ").strip()
    try:
        age = int(input("Âge : "))
        if age < 0 or age > 120:
            print("Erreur : Âge invalide.")
            return personnes
    except ValueError:
        print("Erreur : Âge invalide.")
        return personnes

    if nom:
        personnes.append({"nom": nom, "age": age})
        print(f"Personne {nom} ajoutée avec succès")
    else:
        print("Erreur : Nom invalide.")
    return personnes


def modifier_personne(personnes):
    afficher_personnes(personnes)
    if not personnes:
        return personnes
    try:
        choix = int(input("Entrez le numéro de la personne à modifier : "))
        if 1 <= choix <= len(personnes):
            personne = personnes[choix-1]
            print(f"Modification de {personne.get('nom', 'Inconnu')}")

            nouveau_nom = input("Nouveau nom (laisser vide pour garder) : ").strip()
            try:
                nouveau_age = input("Nouvel âge (laisser vide pour garder) : ").strip()
                if nouveau_age:
                    nouveau_age = int(nouveau_age)
                    if 0 <= nouveau_age <= 120:
                        personne["age"] = nouveau_age
                    else:
                        print("Erreur : Âge invalide.")
                if nouveau_nom:
                    personne["nom"] = nouveau_nom
                print("Modification effectuée")
            except ValueError:
                print("Erreur : Âge invalide.")
        else:
            print("Erreur : Numéro invalide.")
    except ValueError:
        print("Erreur : Veuillez entrer un nombre valide.")
    return personnes


def supprimer_personne(personnes):
    afficher_personnes(personnes)
    if not personnes:
        return personnes
    try:
        choix = int(input("Entrez le numéro de la personne à supprimer : "))
        if 1 <= choix <= len(personnes):
            confirmation = input(f"Confirmez la suppression de {personnes[choix-1].get('nom','Inconnu')} (oui/non) : ").lower()
            if confirmation in ["oui", "o", "yes", "y"]:
                supprimee = personnes.pop(choix-1)
                print(f"Personne {supprimee.get('nom','Inconnu')} supprimée")
            else:
                print("Suppression annulée")
        else:
            print("Erreur : Numéro invalide.")
    except ValueError:
        print("Erreur : Veuillez entrer un nombre valide.")
    return personnes


def traiter_ages(personnes):
    if not personnes:
        print("Erreur : Aucune personne à analyser.")
        return set()

    try:
        noms = [p["nom"] for p in personnes if "nom" in p]
        majeurs = {p["nom"] for p in personnes if "nom" in p and "age" in p and p["age"] >= 18}

        print("="*50)
        print("Analyse des âges")
        print("="*50)
        print(f"Noms extraits : {noms}")
        print(f"Noms des majeurs (≥18) : {majeurs}")
        print("="*50)

        return majeurs
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return set()


# Programme principal avec menu et redémarrage
if __name__ == "__main__":
    while True:  # boucle principale pour recommencer le programme
        personnes = []
        while True:
            print("\n=== Menu Principal ===")
            print("1. Afficher les personnes")
            print("2. Ajouter une personne")
            print("3. Modifier une personne")
            print("4. Supprimer une personne")
            print("5. Analyser les âges")
            print("0. Quitter le menu")
            print("======================")

            try:
                choix = int(input("Votre choix : "))
            except ValueError:
                print("Erreur : Veuillez entrer un nombre valide.")
                continue

            if choix == 1:
                afficher_personnes(personnes)
            elif choix == 2:
                personnes = ajouter_personne(personnes)
            elif choix == 3:
                personnes = modifier_personne(personnes)
            elif choix == 4:
                personnes = supprimer_personne(personnes)
            elif choix == 5:
                traiter_ages(personnes)
            elif choix == 0:
                print("Fin du menu.")
                break
            else:
                print("Erreur : Choix invalide.")

        # Demander si on recommence le programme complet
        restart = input("Voulez-vous recommencer le programme complet ? (oui/non) : ").lower()
        if restart not in ["oui", "o", "yes", "y"]:
            print("Au revoir")
            break
