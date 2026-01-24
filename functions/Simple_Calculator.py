print("=" * 50)
print("Simple Calculator")
print("=" * 50)

def Simple_Calculator(a, b, operation):
    if operation == "+":
        return a + b
    elif operation == "-":
        return a - b
    elif operation == "*":
        return a * b
    elif operation == "/":
        return a / b if b != 0 else "Erreur : Division par zéro !"
    else:
        return "Opération invalide, réessayer"

def obtenir_nombre(message):
    while True:
        try:
            return float(input(message))
        except ValueError:
            print(" Erreur : Veuillez entrer un nombre valide !")

if __name__ == "__main__":
    print("Bienvenue dans Simple Calculator")

    while True:
        a = obtenir_nombre("Entrez la 1ère valeur : ")
        b = obtenir_nombre("Entrez la 2ème valeur : ")

        Operation = input("Choisissez l'opérateur [ + , - , * , / ] : ")
        while Operation not in ["+", "-", "*", "/"]:
            print("Opération invalide, réessayer")
            Operation = input("Choisissez l'opérateur [ + , - , * , / ] : ")

        match Operation:
            case "+":
                print(f" La somme de {a} et {b} est : {Simple_Calculator(a, b, Operation)}")
            case "-":
                print(f" La soustraction de {a} et {b} est : {Simple_Calculator(a, b, Operation)}")
            case "*":
                print(f" La multiplication de {a} et {b} est : {Simple_Calculator(a, b, Operation)}")
            case "/":
                print(f" La division de {a} et {b} est : {Simple_Calculator(a, b, Operation)}")

        # Option pour continuer ou quitter
        choix = input("Voulez-vous faire un autre calcul ? (o/n) : ").lower()
        if choix != "o":
            print(" Merci d'avoir utilisé Simple Calculator !")
            break
