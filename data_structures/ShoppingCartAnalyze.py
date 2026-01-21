print("="*50)
print("ANALYSEUR DE PANIER D'ACHAT !")
print("="*50)

stop_programme = True
while stop_programme:
    # Dictionnaire des produits disponibles
    produits_disponibles = {
        "Ordinateur": 899.99,
        "Souris": 25.50,
        "Clavier": 75.00,
        "Écran": 250.00,
        "Casque": 120.00,
        "Webcam": 85.00,
        "Imprimante": 150.00,
        "Disque dur": 95.00,
        "USB": 15.00,
        "Chaise": 299.99
    }

    # Afficher les produits disponibles
    print("Produits disponibles :")
    print("-"*60)
    for produit, prix in produits_disponibles.items():
        print(f"- {produit:<15} : {prix:8.2f} MAD")
    print("-"*60)

    # Panier d'achat de l'utilisateur
    panier = {}

    # Demander à l'utilisateur d'ajouter des produits
    print("Ajoutez des produits à votre panier !")
    print("(Tapez 'stop' pour terminer)")

    while True:
        produit_choisi = input("Veuillez entrer le nom du produit : ").strip()

        # Vérifier si l'utilisateur veut arrêter
        if produit_choisi.lower() == "stop":
            break

        # Vérifier si le produit existe
        if produit_choisi in produits_disponibles:
            panier[produit_choisi] = produits_disponibles[produit_choisi]
            print(f"{produit_choisi} ajouté au panier ✅")
        else:
            print("Produit non disponible ❌")

    # Vérifier si le panier est vide
    if len(panier) == 0:
        print("Votre panier est vide !")
    else:
        print("-"*60)
        print("ANALYSE DU PANIER !")
        print("-"*60)

        # Afficher le contenu du panier
        print("Contenu du panier :")
        for produit, prix in panier.items():
            print(f"- {produit:<15} : {prix:8.2f} MAD")
        print("-"*60)

        # Calculer le total du panier
        total = sum(panier.values())
        print(f"TOTAL initial : {total:.2f} MAD")
        print("-"*60)

        # Produits premium (>100 MAD)
        print("Produits premium (prix > 100 MAD) :")
        produits_chers = [p for p, prix in panier.items() if prix > 100]
        if produits_chers:
            for p in produits_chers:
                print(f"- {p} : {panier[p]:.2f} MAD")
        else:
            print("Aucun produit cher !")

        # Produit le plus cher
        produit_max = max(panier, key=panier.get)
        prix_max = panier[produit_max]
        print(f"Produit le plus cher : {produit_max} ({prix_max:.2f} MAD)")
        print("="*50)

        # Réduction si total > 500
        print("RÉDUCTION DE PRIX !")
        print("-"*50)
        if total > 500:
            reduction = total * 0.10
            total_final = total - reduction
            print("Félicitations ! Vous bénéficiez de 10% de réduction 🎉")
            print(f"Montant de la réduction : -{reduction:.2f} MAD")
            print(f"Total après réduction : {total_final:.2f} MAD")
        else:
            total_final = total
            montant_restant = 500 - total
            print(f"Ajoutez encore {montant_restant:.2f} MAD pour bénéficier de 10% de réduction.")
            print(f"Total à payer : {total_final:.2f} MAD")

        # Statistiques
        print("="*50)
        print("STATISTIQUES :")
        print("-"*50)
        print(f"- Nombre d'articles : {len(panier)}")
        print(f"- Total initial : {total:.2f} MAD")
        if total > 500:
            print(f"- Réduction 10% : -{reduction:.2f} MAD")
        print(f"- TOTAL à payer : {total_final:.2f} MAD")
        print("="*50)

    # Demander si on recommence
    r_stop_programme = input("Voulez-vous recommencer le programme ? [y/n] : ")
    if r_stop_programme.lower() in ["n", "non"]:
        stop_programme = False

print("="*50)
print("Merci pour votre visite ! Au revoir !")
