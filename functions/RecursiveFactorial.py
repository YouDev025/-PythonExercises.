"""
Calcul de factorielle avec approche récursive et itérative
"""


def factorielle_recursive(n):
    """
    Calcule la factorielle de n de manière récursive

    Formule: n! = n × (n-1)!
    Cas de base: 0! = 1

    Args:
        n: nombre entier positif ou nul

    Returns:
        int: factorielle de n

    Raises:
        ValueError: si n est négatif
    """
    if n < 0:
        raise ValueError("La factorielle n'est pas définie pour les nombres négatifs")

    # Cas de base
    if n == 0 or n == 1:
        return 1

    # Appel récursif
    return n * factorielle_recursive(n - 1)


def factorielle_iterative(n):
    """
    Calcule la factorielle de n de manière itérative
    (Pour comparaison avec la version récursive)

    Args:
        n: nombre entier positif ou nul

    Returns:
        int: factorielle de n
    """
    if n < 0:
        raise ValueError("La factorielle n'est pas définie pour les nombres négatifs")

    resultat = 1
    for i in range(2, n + 1):
        resultat *= i

    return resultat


def afficher_etapes_recursion(n, niveau=0):
    """
    Affiche visuellement les étapes de la récursion

    Args:
        n: nombre pour le calcul factoriel
        niveau: niveau de profondeur de la récursion (pour l'indentation)

    Returns:
        int: factorielle de n
    """
    indentation = "  " * niveau

    if n == 0 or n == 1:
        print(f"{indentation}factorielle({n}) = 1  [cas de base]")
        return 1

    print(f"{indentation}factorielle({n}) = {n} × factorielle({n - 1})")
    resultat_recursif = afficher_etapes_recursion(n - 1, niveau + 1)
    resultat = n * resultat_recursif
    print(f"{indentation}factorielle({n}) = {n} × {resultat_recursif} = {resultat}")

    return resultat


def tableau_factorielles(debut, fin):
    """
    Affiche un tableau de factorielles

    Args:
        debut: nombre de départ
        fin: nombre de fin
    """
    print("\n" + "=" * 50)
    print("   TABLEAU DES FACTORIELLES")
    print("=" * 50)
    print(f"{'n':>5} | {'n!':>20}")
    print("-" * 50)

    for n in range(debut, fin + 1):
        fact = factorielle_recursive(n)
        print(f"{n:>5} | {fact:>20,}")

    print("=" * 50)


def mode_interactif():
    """Mode interactif pour calculer des factorielles"""
    print("\n" + "=" * 60)
    print("   CALCULATEUR DE FACTORIELLE (RÉCURSIF)")
    print("=" * 60)
    print("1. Calculer une factorielle")
    print("2. Voir les étapes de la récursion")
    print("3. Afficher un tableau de factorielles")
    print("4. Comparer récursif vs itératif")
    print("5. Quitter")
    print("=" * 60)

    while True:
        choix = input("\nChoisissez une option (1-5): ").strip()

        if choix == "1":
            try:
                n = int(input("\nEntrez un nombre entier (0-20): "))
                if n < 0:
                    print("✗ Le nombre doit être positif ou nul")
                elif n > 20:
                    print("⚠ Attention: valeurs très grandes! Calcul en cours...")
                    resultat = factorielle_recursive(n)
                    print(f"\n✓ {n}! = {resultat:,}")
                else:
                    resultat = factorielle_recursive(n)
                    print(f"\n✓ {n}! = {resultat:,}")
            except ValueError as e:
                print(f"✗ Erreur: {e}")
            except RecursionError:
                print("✗ Erreur: nombre trop grand pour la récursion!")

        elif choix == "2":
            try:
                n = int(input("\nEntrez un nombre (0-10 recommandé): "))
                if n < 0:
                    print("✗ Le nombre doit être positif ou nul")
                elif n > 10:
                    print("⚠ L'affichage sera très long pour n > 10")
                    confirmation = input("Continuer? (o/n): ").lower()
                    if confirmation == 'o':
                        print("\nÉtapes de la récursion:")
                        print("-" * 60)
                        afficher_etapes_recursion(n)
                else:
                    print("\nÉtapes de la récursion:")
                    print("-" * 60)
                    afficher_etapes_recursion(n)
            except ValueError as e:
                print(f"✗ Erreur: {e}")

        elif choix == "3":
            try:
                debut = int(input("\nNombre de départ: "))
                fin = int(input("Nombre de fin: "))
                if debut < 0 or fin < 0:
                    print("✗ Les nombres doivent être positifs")
                elif fin > 20:
                    print("⚠ Attention: les valeurs seront très grandes!")
                    tableau_factorielles(debut, fin)
                else:
                    tableau_factorielles(debut, fin)
            except ValueError:
                print("✗ Erreur: entrez des nombres entiers valides")

        elif choix == "4":
            try:
                n = int(input("\nEntrez un nombre (0-1000): "))
                if n < 0:
                    print("✗ Le nombre doit être positif ou nul")
                else:
                    import time

                    # Test récursif
                    debut = time.time()
                    try:
                        resultat_rec = factorielle_recursive(n)
                        temps_rec = time.time() - debut
                        print(f"\n✓ Récursif: {n}! calculé en {temps_rec:.6f} secondes")
                    except RecursionError:
                        print(f"\n✗ Récursif: dépassement de la limite de récursion")
                        temps_rec = None
                        resultat_rec = None

                    # Test itératif
                    debut = time.time()
                    resultat_iter = factorielle_iterative(n)
                    temps_iter = time.time() - debut
                    print(f"✓ Itératif: {n}! calculé en {temps_iter:.6f} secondes")

                    if temps_rec and resultat_rec == resultat_iter:
                        print(f"\n✓ Les deux méthodes donnent le même résultat")
                        if temps_rec < temps_iter:
                            print(f"⚡ Récursif est {temps_iter / temps_rec:.2f}x plus rapide")
                        else:
                            print(f"⚡ Itératif est {temps_rec / temps_iter:.2f}x plus rapide")
            except ValueError:
                print("✗ Erreur: entrez un nombre entier valide")

        elif choix == "5":
            print("\nAu revoir!  ")
            break

        else:
            print("✗ Option invalide. Choisissez 1, 2, 3, 4 ou 5.")


# Exemples et tests
if __name__ == "__main__":
    # Mode interactif
    mode_interactif()