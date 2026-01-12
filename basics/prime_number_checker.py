print("=" * 40,end="")
print("PRIME NUMBER CHECKER",end="")
print("=" * 40)

Nbr = int(input("Entrer un nombre: "))

if Nbr < 2:
    print(f"{Nbr} n'est pas un nombre premier")
else:
    i = 2

    while Nbr % i != 0 and i < Nbr:
        i += 1

    if i == Nbr:
        print(f"{Nbr} est un nombre PREMIER ")
    else:
        print(f"{Nbr} n'est PAS un nombre premier ")
        print(f"{Nbr} est divisible par {i}")