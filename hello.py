#Exercice 1 "calculer air du rectangle"

Longueur = float(input("donner longueur du rectangle :"))
Largeur = float(input("donner largeur du rectangle :"))
AIR = Largeur*Largeur
print(f"L'aire de votre rectangle est : {AIR:.2f} métre carrée")


#Exercie 2 : " Shopping Cart Program"
item= input("What item you whant to purchase? :")
price =float(input("Whet is the price of the item you want to purchase? :"))
quantity = int(input("How many items do you want to purchase? :"))
total = price*quantity
print(f"Your total is {total:.2f}$ and your items are {item}'s.Thank You for purching")


#Exericie 3 " Madlibs Game "

adjective1=input("What is your adjective number 1? :")
noun1=input("What is your noun number 1? :")
adjective2=input("What is your adjective number 2? :")
noun2=input("What is your noun number 2? :")
verb1=input("What is your verb ending with 'ing'? :")

print(f"Today i went to the zoo i sow a {adjective1} animal")
print(f"and the owner of the zoo his name is {noun1} that's awsome ")
print(f"I'm so {adjective2} the {noun2} is {verb1}")
