import math

# Calculer le volume d'un parallélépipède rectangle
def volume_parallelepipede(hauteur, largeur, profondeur):
    return hauteur * largeur * profondeur

# Calculer le volume d'un cube
def volume_cube(cote):
    return math.pow(cote, 3)

# Calculer le volume d'un cylindre
def volume_cylindre(rayon, hauteur):
    return math.pi * math.pow(rayon, 2) * hauteur

# Calculer le volume d'une pyramide
def volume_pyramide(aire_base, hauteur):
    return (1/3) * aire_base * hauteur

# Calculer le volume d'une pyramide à base carrée
def volume_pyramide_carree(cote_base, hauteur):
    aire_base = cote_base ** 2
    return (1/3) * aire_base * hauteur

# Calculer le volume d'une sphère
def volume_sphere(rayon):
    return (4/3) * math.pi * math.pow(rayon, 3)

# Calculer le volume d'un cône
def volume_cone(rayon, hauteur):
    return (1/3) * math.pi * math.pow(rayon, 2) * hauteur

# Affiche le menu et demande à l'utilisateur quel solide calculer
def menu_principale():
    print("=== CALCULATEUR DE VOLUMES GÉOMÉTRIQUES ===\n")
    print("Choisissez un solide géométrique :")
    print("1. Parallélépipède rectangle")
    print("2. Cube")
    print("3. Sphère")
    print("4. Cylindre")
    print("5. Cône")
    print("6. Pyramide à base carrée")
    print("7. Pyramide (base quelconque)")
    print("0. Quitter")

    choix = input("Votre choix (0 - 7) : ")
    return choix

# Fonction principale qui gère l'interaction avec l'utilisateur
def calculer_volume():
    while True:
        choix = menu_principale()
        if choix == "0":
            print("Au revoir !")
            break
        elif choix == "1":
            print("="*20 + " Parallélépipède rectangle " + "="*20)
            h = float(input("Hauteur : "))
            l = float(input("Largeur : "))
            p = float(input("Profondeur : "))
            resultat = volume_parallelepipede(h, l, p)
            print("=" * 50)
            print(f"Volume = {resultat:.2f} m³")
            print("=" * 50)
        elif choix == "2":
            print("=" * 20 + " Cube " + "=" * 20)
            c = float(input("Côté : "))
            resultat = volume_cube(c)
            print("=" * 50)
            print(f"Volume = {resultat:.2f} m³")
            print("=" * 50)
        elif choix == "3":
            print("=" * 20 + " Sphère " + "=" * 20)
            r = float(input("Rayon : "))
            resultat = volume_sphere(r)
            print("=" * 50)
            print(f"Volume = {resultat:.2f} m³")
            print("=" * 50)
        elif choix == "4":
            print("=" * 20 + " Cylindre " + "=" * 20)
            r = float(input("Rayon : "))
            h = float(input("Hauteur : "))
            resultat = volume_cylindre(r, h)
            print("=" * 50)
            print(f"Volume = {resultat:.2f} m³")
            print("=" * 50)
        elif choix == "5":
            print("=" * 20 + " Cône " + "=" * 20)
            r = float(input("Rayon : "))
            h = float(input("Hauteur : "))
            resultat = volume_cone(r, h)
            print("=" * 50)
            print(f"Volume = {resultat:.2f} m³")
            print("=" * 50)
        elif choix == "6":
            print("=" * 20 + " Pyramide à base carrée " + "=" * 20)
            c = float(input("Côté de la base : "))
            h = float(input("Hauteur : "))
            resultat = volume_pyramide_carree(c, h)
            print("=" * 50)
            print(f"Volume = {resultat:.2f} m³")
            print("=" * 50)
        elif choix == "7":
            print("=" * 20 + " Pyramide (base quelconque) " + "=" * 20)
            aire = float(input("Aire de la base : "))
            h = float(input("Hauteur : "))
            resultat = volume_pyramide(aire, h)
            print("=" * 50)
            print(f"Volume = {resultat:.2f} m³")
            print("=" * 50)
        else:
            print("Choix invalide ! Veuillez choisir entre 0 et 7.")

# Lancement du programme
if __name__ == "__main__":
    calculer_volume()
