def find_max(numbers):
    """
    Retourne le plus grand élément d'une liste de nombres.

    Args:
        numbers: Liste de nombres (int ou float)

    Returns:
        Le plus grand élément de la liste

    Raises:
        ValueError: Si la liste est vide
    """
    if not numbers:
        raise ValueError("La liste ne peut pas être vide")

    max_value = numbers[0]

    for num in numbers[1:]:
        if num > max_value:
            max_value = num

    return max_value


def get_numbers_from_user():
    """
    Demande à l'utilisateur de saisir des nombres et les valide.

    Returns:
        Liste de nombres validés
    """
    numbers = []

    print("=== MAXIMUM FINDER ===")
    print("Entrez des nombres (tapez 'fin' pour terminer)")
    print()

    while True:
        user_input = input("Entrez un nombre (ou 'fin'): ").strip()

        # Vérifier si l'utilisateur veut terminer
        if user_input.lower() == 'fin':
            break

        # Valider et convertir l'entrée
        try:
            number = float(user_input)
            numbers.append(number)
            print(f"✓ Nombre ajouté: {number}")
        except ValueError:
            print("✗ Erreur: Veuillez entrer un nombre valide ou 'fin'")

    return numbers


# Programme principal
if __name__ == "__main__":
    # Demander les nombres à l'utilisateur
    numbers_list = get_numbers_from_user()

    # Vérifier si la liste est vide
    if not numbers_list:
        print("\n⚠ Aucun nombre n'a été saisi!")
    else:
        # Afficher les nombres saisis
        print(f"\n Nombres saisis: {numbers_list}")
        print(f" Nombre total: {len(numbers_list)}")

        # Trouver et afficher le maximum
        try:
            maximum = find_max(numbers_list)
            print(f"\n Le maximum est: {maximum}")
        except ValueError as e:
            print(f"\n✗ Erreur: {e}")