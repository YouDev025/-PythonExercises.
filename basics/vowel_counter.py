print("-"*50)
print("Vowel Counter ")
print("-"*50)

#Get input from user
text = input("Enter a text to count vowels : ")
vowels = 'aeiouAEIOU'

#initialization vowel counts
a_count = 0
e_count = 0
i_count = 0
o_count = 0
u_count = 0

#Count each vowel
for char in text:
    if char in vowels:
        if char.lower() == 'a':
            a_count += 1
        elif char.lower() == 'e':
            e_count += 1
        elif char.lower() == 'i':
            i_count += 1
        elif char.lower() == 'o':
            o_count += 1
        elif char.lower() == 'u':
            u_count += 1

#calculate total
total = a_count + e_count + i_count + o_count + u_count

#Display results
print(f"Result : {text}")
print("-"*50)
print("A : ",a_count)
print("E : ",e_count)
print("I : ",i_count)
print("O : ",o_count)
print("U : ",u_count)
print("-"*50)
print("Total vowels: ",total)
print("-"*50)