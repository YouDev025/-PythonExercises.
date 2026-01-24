print("=" * 50)
print("Count Up Generator !")
print("=" * 50)


# Définition de la fonction générateur
def countUp(start=0, step=1, limit=10):
    """
    Générateur qui compte à partir de 'start',
    en ajoutant 'step' à chaque fois,
    jusqu'à atteindre 'limit'.
    """
    current = start
    # La condition doit comparer avec une limite, pas avec step
    if step > 0:
        while current <= limit:
            yield current
            current += step
    else:
        while current >= limit:
            yield current
            current += step


# Fonction principale
if __name__ == "__main__":
    # Compter de 0 à 9 avec pas de 1
    print("=" * 50)
    print("Compte de 0 avec pas de 1 :")
    print("=" * 50)
    counter = countUp(start=0, step=1, limit=9)
    for num in counter:
        print(num)

    # Compter de 10 à 28 avec pas de 2
    print("=" * 50 + "\n")
    print("Compte de 10 avec pas de 2 :")
    print("=" * 50)
    counter2 = countUp(start=10, step=2, limit=28)
    for num in counter2:
        print(num)

    # Compte à rebours de 10 à 1
    print("=" * 50 + "\n")
    print("Compte à rebours de 10 :")
    print("=" * 50)
    countdown = countUp(start=10, step=-1, limit=1)
    for num in countdown:
        print(num)
