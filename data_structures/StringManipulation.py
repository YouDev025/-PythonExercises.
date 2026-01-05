
while True:
    myString = input("Please enter a string from 0 to 20 caracters : ")
    _upperCase = myString.upper()
    _lowerCase = myString.lower()
    _streped = myString.strip()
    _splited = myString.split()
    _replaced = myString.replace(" ", "--")

    if len(myString) == 0 :
        print("Your String is empty")
    elif len(myString) > 50:
        print("Your string is too long ")
    else:
        print(f"Your string is {myString} and the length is {len(myString)}")
        print(f"Your string on Upper Case is {_upperCase}")
        print(f"Your string on Lower Case is {_lowerCase}")
        print(f"Your string Splited is {_splited}")
        print(f"Your string Streped is {_streped}")
        print(f"Your string Replaced is {_replaced}")








