print("=== Time Converter ===\n")
print("Convert between different time units")
print("1. Seconds to Minutes/Hours/Days")
print("2. Minutes to Seconds/Hours/Days")
print("3. Hours to Seconds/Minutes/Days")
print("4. Days to Seconds/Minutes/Hours")

choice = input("\nEnter your choice (1-4): ")
value = float(input("Enter the value to convert: "))

print("\n" + "=" * 40)

if choice == '1':
    # Seconds to other units
    print(f"\n{value} seconds equals:")
    print(f"  {value / 60:.2f} minutes")
    print(f"  {value / 3600:.2f} hours")
    print(f"  {value / 86400:.4f} days")

elif choice == '2':
    # Minutes to other units
    print(f"\n{value} minutes equals:")
    print(f"  {value * 60:.2f} seconds")
    print(f"  {value / 60:.2f} hours")
    print(f"  {value / 1440:.4f} days")

elif choice == '3':
    # Hours to other units
    print(f"\n{value} hours equals:")
    print(f"  {value * 3600:.2f} seconds")
    print(f"  {value * 60:.2f} minutes")
    print(f"  {value / 24:.4f} days")

elif choice == '4':
    # Days to other units
    print(f"\n{value} days equals:")
    print(f"  {value * 86400:.2f} seconds")
    print(f"  {value * 1440:.2f} minutes")
    print(f"  {value * 24:.2f} hours")

else:
    print("\nInvalid choice! Please run the program again and choose 1-4.")

print("=" * 40)