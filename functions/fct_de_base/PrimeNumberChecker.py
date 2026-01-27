# Vérificateur de nombres premiers

def est_premier(n: int) -> bool:
    """Vérifie si un nombre est premier."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False

    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def trouver_diviseur(n: int) -> list[int]:
    """Trouve tous les diviseurs d'un nombre."""
    diviseur = []
    for i in range(1, int(n ** 0.5) + 1):
        if n % i == 0:
            diviseur.append(i)
            if i != n // i:
                diviseur.append(n // i)
    return sorted(diviseur)


def nombres_premiers_jusqu_a(limite: int) -> list[int]:
    """Trouve tous les nombres premiers jusqu'à une limite donnée (Crible d'Ératosthène)."""
    if limite < 2:
        return []

    est_premier_list = [True] * (limite + 1)
    est_premier_list[0] = est_premier_list[1] = False

    for i in range(2, int(limite ** 0.5) + 1):
        if est_premier_list[i]:
            for j in range(i * i, limite + 1, i):
                est_premier_list[j] = False

    return [i for i in range(limite + 1) if est_premier_list[i]]


def afficher_analyse(n: int) -> None:
    """Affiche une analyse complète d'un nombre."""
    print("-" * 50)
    print(f"ANALYSE DU NOMBRE: {n}")
    print("-" * 50)

    if est_premier(n):
        print(f"{n} est un NOMBRE PREMIER")
        print(f"Diviseurs: 1 et {n}")
    else:
        print(f"{n} n'est PAS un nombre premier")
        diviseur = trouver_diviseur(n)
        print(f"Diviseurs: {diviseur}")

        # Décomposition en facteurs premiers
        facteurs = []
        temp = n
        d = 2
        while d * d <= temp:
            while temp % d == 0:
                facteurs.append(d)
                temp //= d
            d += 1
        if temp > 1:
            facteurs.append(temp)

        if facteurs:
            facteurs_str = " × ".join(map(str, facteurs))
            print(f"Décomposition: {n} = {facteurs_str}")
    print("-" * 50)


def mode_interactif() -> None:
    """Mode interactif du vérificateur"""
    while True:
        print("\n" + "=" * 60)
        print("   VÉRIFICATEUR DE NOMBRES PREMIERS")
        print("=" * 60)
        print("1. Vérifier un nombre")
        print("2. Trouver tous les nombres premiers jusqu'à N")
        print("3. Quitter")
        print("=" * 60)

        choix = input("\nChoisissez une option (1-3): ").strip()

        if choix == "1":
            try:
                n = int(input("\nEntrez un nombre entier: "))
                afficher_analyse(n)
            except ValueError:
                print("Erreur: Veuillez entrer un nombre entier valide!")

        elif choix == "2":
            try:
                limite = int(input("\nEntrez la limite: "))
                if limite < 2:
                    print("La limite doit être au moins 2")
                else:
                    premiers = nombres_premiers_jusqu_a(limite)
                    print(f"\nNombres premiers de 2 à {limite}:")
                    print(f"Total: {len(premiers)} nombres premiers")
                    print(f"Liste: {premiers}")
            except ValueError:
                print("Erreur: Veuillez entrer un nombre entier valide!")

        elif choix == "3":
            print("\nAu revoir!")
            break

        else:
            print("Option invalide. Choisissez 1, 2 ou 3.")


# Exemples et tests
if __name__ == "__main__":
    # Mode interactif
    mode_interactif()
