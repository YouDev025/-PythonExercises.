def calculatrice(a, b, operation):
    try:
        if operation == "+":
            return a + b
        elif operation == "-":
            return a - b
        elif operation == "*":
            return a * b
        elif operation == "/":
            try:
                return a / b
            except ZeroDivisionError:
                return "Erreur : Division par zéro impossible."
        else:
            return "Erreur : Opération non reconnue."
    except Exception as e:
        return f"Erreur inattendue : {e}"


# Programme principal avec menu et redémarrage
if __name__ == "__main__":
    while True:  # boucle principale pour recommencer le programme
        print("="*50)
        print("Programme : Calculatrice sécurisée")
        print("="*50)

        while True:
            print("\n=== Menu Calculatrice ===")
            print("1. Addition (+)")
            print("2. Soustraction (-)")
            print("3. Multiplication (*)")
            print("4. Division (/)")
            print("0. Quitter le menu")
            print("==========================")

            try:
                choix = int(input("Votre choix : "))
            except ValueError:
                print("Erreur : Veuillez entrer un nombre valide.")
                continue

            if choix == 0:
                print("Fin du menu.")
                break

            # Vérification de l'opération choisie
            if choix == 1:
                operation = "+"
            elif choix == 2:
                operation = "-"
            elif choix == 3:
                operation = "*"
            elif choix == 4:
                operation = "/"
            else:
                print("Erreur : Choix invalide.")
                continue

            # Saisie des nombres
            try:
                a = float(input("Entrez le premier nombre : "))
                b = float(input("Entrez le deuxième nombre : "))
            except ValueError:
                print("Erreur : Veuillez entrer des nombres valides.")
                continue

            # Calcul
            resultat = calculatrice(a, b, operation)

            # Affichage avec 2 décimales si c'est un nombre
            if isinstance(resultat, (int, float)):
                print(f"Résultat de {a} {operation} {b} = {resultat:.2f}")
            else:
                print(resultat)

        # Demander si on recommence le programme complet
        restart = input("Voulez-vous recommencer le programme complet ? (oui/non) : ").lower()
        if restart not in ["oui", "o", "yes", "y"]:
            print("Au revoir")
            break
