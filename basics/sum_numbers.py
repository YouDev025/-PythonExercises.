print("=" * 40,end="")
print("NUMBER SUM CALCULATOR",end="")
print("=" * 40)
N=int(input("Entrer le nombre des valeurs : "))
i=0
somme=0
print("Calcul du somme: ")
while i<N:
    somme=somme+i
    print(f"  {i} -> somme = {somme}")
    i=i+1

print("\n" + "=" * 40)
print(f"La somme totale de 1 à 10 est: {somme}")
print("=" * 40 )
