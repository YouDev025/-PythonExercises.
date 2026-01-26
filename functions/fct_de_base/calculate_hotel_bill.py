# Liste pour enregistrer les factures
factures = []

# Calcule le prix total d'un séjour à l'hôtel
def calculer_prix_sejour(nombre_nuits, nombre_repas):
    PRIX_NUITS = 90
    PRIX_REPAS = 30
    prix_chambres = nombre_nuits * PRIX_NUITS
    prix_repas_total = nombre_repas * PRIX_REPAS
    prix_total = prix_chambres + prix_repas_total
    return prix_total

# Affiche une facture détaillée pour le client
def afficher_facture(nombre_nuits, nombre_repas, numero_facture):
    PRIX_NUITS = 90
    PRIX_REPAS = 30
    prix_chambres = nombre_nuits * PRIX_NUITS
    prix_repas_total = nombre_repas * PRIX_REPAS
    prix_total = prix_chambres + prix_repas_total
    print("="*20, end="")
    print(f"FACTURE HÔTEL N°{numero_facture}", end="")
    print("="*20)
    print(f"Chambres : {nombre_nuits} nuit(s) x {PRIX_NUITS} MAD = {prix_chambres} MAD")
    print(f"Repas : {nombre_repas} repas x {PRIX_REPAS} MAD = {prix_repas_total} MAD")
    print("="*60)
    print(f"TOTAL À PAYER : {prix_total} MAD")
    print("="*60)
    return prix_total

# Fonction principale qui gère l'interaction avec l'utilisateur
def calculateur_hotel():
    print("="*20, end="")
    print("CALCULATEUR DE PRIX - HÔTEL", end="")
    print("="*20)
    print("Prix par nuit : 90 MAD")
    print("Prix par repas : 30 MAD")

    numero_facture = 1

    while True:
        print("\nQue voulez-vous faire ?")
        print("1. Calculer le prix d'un séjour")
        print("2. Afficher une facture détaillée et l'enregistrer")
        print("3. Voir toutes les factures enregistrées")
        print("0. Quitter")

        try:
            choix = int(input("Votre choix (0-3) : "))
        except ValueError:
            print("Erreur : veuillez entrer un nombre valide !")
            continue

        if choix == 0:
            print("Au revoir !")
            break
        elif choix == 1:
            try:
                nuits = int(input("Nombre de nuits : "))
                repas = int(input("Nombre de repas : "))
                if nuits < 0 or repas < 0:
                    print("Erreur : les nombres doivent être positifs !")
                    continue
                prix = calculer_prix_sejour(nuits, repas)
                print(f"Prix total à payer : {prix} MAD")
            except ValueError:
                print("Erreur : veuillez entrer des nombres valides !")
        elif choix == 2:
            try:
                nuits = int(input("Nombre de nuits : "))
                repas = int(input("Nombre de repas : "))
                if nuits < 0 or repas < 0:
                    print("Erreur : les nombres doivent être positifs !")
                    continue
                prix_total = afficher_facture(nuits, repas, numero_facture)
                factures.append({
                    "numero": numero_facture,
                    "nuits": nuits,
                    "repas": repas,
                    "total": prix_total
                })
                print("Facture enregistrée avec succès.")
                numero_facture += 1
            except ValueError:
                print("Erreur : veuillez entrer des nombres valides !")
        elif choix == 3:
            if not factures:
                print("Aucune facture enregistrée.")
            else:
                print("\n=== LISTE DES FACTURES ENREGISTRÉES ===")
                for f in factures:
                    print(f"Facture N°{f['numero']} - Nuits: {f['nuits']} | Repas: {f['repas']} | Total: {f['total']} MAD")
        else:
            print("Choix invalide ! Veuillez choisir entre 0 et 3.")

# Lancement du programme
if __name__ == "__main__":
    calculateur_hotel()