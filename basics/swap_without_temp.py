print("BONJOUR DANS LE swap_without_temp")
a = int(input("Donner une valeur de A: "))
b = int(input("Donner une valeur de B: "))

print(f"Avant l'échange: A = {a}, B = {b}")

a, b = b, a

print(f"Après l'échange: A = {a}, B = {b}")
