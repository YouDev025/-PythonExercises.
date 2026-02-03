# Fonction utilitaire pour saisir une valeur numérique positive
def saisir_valeur_positive(message):
    while True:
        try:
            valeur = float(input(message))
            if valeur < 0:
                print("Erreur : la valeur doit être positive.")
            else:
                return valeur
        except ValueError:
            print("Erreur : veuillez entrer un nombre valide.")

# Calcule la vitesse : v = d / t
def calculer_speed(distance, temps):
    if temps == 0:
        return "Erreur : Le temps ne peut pas être zéro !"
    return distance / temps

# Calcule la distance : d = v * t
def calculer_distance(vitesse, temps):
    return vitesse * temps

# Calcule le temps : t = d / v
def calculer_temps(vitesse, distance):
    if vitesse == 0:
        return "Erreur : La vitesse ne peut pas être zéro !"
    return distance / vitesse

# Convertit km/h en m/s
def convertir_km_h_vers_m_s(vitesse_km_h):
    return vitesse_km_h / 3.6

# Convertit m/s en km/h
def convertir_m_s_vers_km_h(vitesse_m_s):
    return vitesse_m_s * 3.6

# Affiche le menu principal
def menu_principale():
    print("\n=== CALCULATEUR DE VITESSE ===\n")
    print("Que voulez-vous calculer ?")
    print("1. Vitesse (à partir de distance et temps)")
    print("2. Distance (à partir de vitesse et temps)")
    print("3. Temps (à partir de distance et vitesse)")
    print("4. Convertir km/h en m/s")
    print("5. Convertir m/s en km/h")
    print("0. Quitter")

    choix = input("Votre choix (0 - 5) : ")
    return choix

# Fonction principale qui gère l'interaction avec l'utilisateur
def calculeur_vitesse():
    while True:
        choix = menu_principale()

        if choix == "0":
            print("Au revoir !")
            break

        elif choix == "1":
            print("="*20 + " Calcul de la vitesse " + "="*20)
            distance = saisir_valeur_positive("Distance (en mètres ou km) : ")
            temps = saisir_valeur_positive("Temps (en secondes ou heures) : ")
            resultat = calculer_speed(distance, temps)
            print(f"Vitesse = {resultat:.2f} (m/s ou km/h)")

        elif choix == "2":
            print("="*20 + " Calcul de la distance " + "="*20)
            vitesse = saisir_valeur_positive("Vitesse (m/s ou km/h) : ")
            temps = saisir_valeur_positive("Temps (en secondes ou heures) : ")
            resultat = calculer_distance(vitesse, temps)
            print(f"Distance = {resultat:.2f} (m ou km)")

        elif choix == "3":
            print("="*20 + " Calcul du temps " + "="*20)
            vitesse = saisir_valeur_positive("Vitesse (m/s ou km/h) : ")
            distance = saisir_valeur_positive("Distance (en mètres ou km) : ")
            resultat = calculer_temps(vitesse, distance)
            if isinstance(resultat, str):
                print(resultat)
            else:
                print(f"Temps = {resultat:.2f} (s ou h)")

        elif choix == "4":
            print("="*20 + " Conversion km/h → m/s " + "="*20)
            vitesse_km_h = saisir_valeur_positive("Vitesse en km/h : ")
            resultat = convertir_km_h_vers_m_s(vitesse_km_h)
            print(f"{vitesse_km_h:.2f} km/h = {resultat:.2f} m/s")

        elif choix == "5":
            print("="*20 + " Conversion m/s → km/h " + "="*20)
            vitesse_m_s = saisir_valeur_positive("Vitesse en m/s : ")
            resultat = convertir_m_s_vers_km_h(vitesse_m_s)
            print(f"{vitesse_m_s:.2f} m/s = {resultat:.2f} km/h")

        else:
            print("Choix invalide ! Veuillez choisir entre 0 et 5.")

# Lancement du programme
if __name__ == "__main__":
    print("Bienvenue dans le calculateur de vitesse !")
    print("Formules : v = d / t, d = v * t, t = d / v")
    calculeur_vitesse()
