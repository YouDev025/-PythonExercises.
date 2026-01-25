def afficher_notes(notes):
    print("="*50)
    print("Notes actuelles :")
    if notes:
        for i, note in enumerate(notes, start=1):
            print(f"{i}. {note}")
    else:
        print("Aucune note disponible.")
    print("="*50)


def ajouter_note(notes):
    try:
        note = float(input("Entrez la nouvelle note (0-20) : "))
        if 0 <= note <= 20:
            notes.append(note)
            print(f"Note {note} ajoutée avec succès")
        else:
            print("Erreur : La note doit être comprise entre 0 et 20.")
    except ValueError:
        print("Erreur : Veuillez entrer un nombre valide.")
    return notes


def modifier_note(notes):
    afficher_notes(notes)
    if not notes:
        return notes
    try:
        choix = int(input("Entrez le numéro de la note à modifier : "))
        if 1 <= choix <= len(notes):
            try:
                nouvelle_note = float(input("Entrez la nouvelle valeur (0-20) : "))
                if 0 <= nouvelle_note <= 20:
                    confirmation = input(f"Confirmez la modification de {notes[choix-1]} en {nouvelle_note} (oui/non) : ").lower()
                    if confirmation in ["oui", "o", "yes", "y"]:
                        notes[choix-1] = nouvelle_note
                        print("Modification effectuée")
                    else:
                        print("Modification annulée")
                else:
                    print("Erreur : La note doit être comprise entre 0 et 20.")
            except ValueError:
                print("Erreur : Veuillez entrer un nombre valide.")
        else:
            print("Erreur : Numéro invalide.")
    except ValueError:
        print("Erreur : Veuillez entrer un nombre valide.")
    return notes


def supprimer_note(notes):
    afficher_notes(notes)
    if not notes:
        return notes
    try:
        choix = int(input("Entrez le numéro de la note à supprimer : "))
        if 1 <= choix <= len(notes):
            confirmation = input(f"Confirmez la suppression de {notes[choix-1]} (oui/non) : ").lower()
            if confirmation in ["oui", "o", "yes", "y"]:
                supprimee = notes.pop(choix-1)
                print(f"Note {supprimee} supprimée")
            else:
                print("Suppression annulée")
        else:
            print("Erreur : Numéro invalide.")
    except ValueError:
        print("Erreur : Veuillez entrer un nombre valide.")
    return notes


def analyser_notes(notes):
    if not notes:
        print("Erreur : Aucune note à analyser.")
        return {}

    moyenne = sum(notes) / len(notes)
    note_max = max(notes)
    note_min = min(notes)
    resultat = "Moyenne suffisante" if moyenne >= 10 else "Moyenne insuffisante"

    print("="*50)
    print("Analyse des notes")
    print("="*50)
    print(f"Moyenne : {round(moyenne, 2)}")
    print(f"Note maximale : {note_max}")
    print(f"Note minimale : {note_min}")
    print(f"Résultat : {resultat}")
    print("="*50)

    return {
        "moyenne": round(moyenne, 2),
        "note_max": note_max,
        "note_min": note_min,
        "resultat": resultat
    }


# Programme principal avec redémarrage
if __name__ == "__main__":
    while True:  # boucle principale pour recommencer le programme
        notes = []
        while True:
            print("\n=== Menu Principal ===")
            print("1. Afficher les notes")
            print("2. Ajouter une note")
            print("3. Modifier une note")
            print("4. Supprimer une note")
            print("5. Analyser les notes")
            print("0. Quitter le menu")
            print("======================")

            try:
                choix = int(input("Votre choix : "))
            except ValueError:
                print("Erreur : Veuillez entrer un nombre valide.")
                continue

            if choix == 1:
                afficher_notes(notes)
            elif choix == 2:
                notes = ajouter_note(notes)
            elif choix == 3:
                notes = modifier_note(notes)
            elif choix == 4:
                notes = supprimer_note(notes)
            elif choix == 5:
                analyser_notes(notes)
            elif choix == 0:
                print("Fin du menu.")
                break
            else:
                print("Erreur : Choix invalide.")

        # Demander si on recommence le programme
        restart = input("Voulez-vous recommencer le programme complet ? (oui/non) : ").lower()
        if restart not in ["oui", "o", "yes", "y"]:
            print("Au revoir")
            break
