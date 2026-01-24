print("=" * 50)
print("Even Numbers Generator")
print("=" * 50)


# Définition de la fonction générateur
def even_numbers_generator(start=0):
    """
    Générateur qui produit des nombres pairs
    à partir de 'start' (inclus ou ajusté).
    """
    n = start if start % 2 == 0 else start + 1
    while True:
        yield n
        n += 2


# Fonction principale
if __name__ == "__main__":
    # Crée un générateur de nombres pairs
    evens = even_numbers_generator()

    # Affiche les 10 premiers nombres pairs
    for _ in range(10):
        print(next(evens))
