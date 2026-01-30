import re

# Email Validator without functions

print("=== EMAIL VALIDATOR ===")
print()

# Continue validating emails
continue_validation = True

while continue_validation:
    # Get email from user
    email = input("Enter an email address to validate (or 'quit' to exit): ").strip()

    if email.lower() == 'quit':
        print("\nThank you for using Email Validator!")
        break

    print(f"\nValidating: {email}")
    print("-" * 50)

    # Initialize validation flags
    is_valid = True
    errors = []

    # Check if email is empty
    if len(email) == 0:
        is_valid = False
        errors.append("❌ Email cannot be empty")
    else:
        # Check for @ symbol
        if email.count('@') == 0:
            is_valid = False
            errors.append("❌ Email must contain @ symbol")
        elif email.count('@') > 1:
            is_valid = False
            errors.append("❌ Email must contain exactly one @ symbol")
        else:
            # Split email into local and domain parts
            parts = email.split('@')
            local_part = parts[0]
            domain_part = parts[1]

            # Validate local part (before @)
            if len(local_part) == 0:
                is_valid = False
                errors.append("❌ Local part (before @) cannot be empty")
            elif len(local_part) > 64:
                is_valid = False
                errors.append("❌ Local part (before @) cannot exceed 64 characters")
            else:
                # Check for invalid characters in local part
                valid_local_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.!#$%&'*+-/=?^_`{|}~"
                for char in local_part:
                    if char not in valid_local_chars:
                        is_valid = False
                        errors.append(f"❌ Invalid character '{char}' in local part")
                        break

                # Check if starts or ends with dot
                if local_part.startswith('.') or local_part.endswith('.'):
                    is_valid = False
                    errors.append("❌ Local part cannot start or end with a dot")

                # Check for consecutive dots
                if '..' in local_part:
                    is_valid = False
                    errors.append("❌ Local part cannot contain consecutive dots")

            # Validate domain part (after @)
            if len(domain_part) == 0:
                is_valid = False
                errors.append("❌ Domain part (after @) cannot be empty")
            elif len(domain_part) > 255:
                is_valid = False
                errors.append("❌ Domain part (after @) cannot exceed 255 characters")
            else:
                # Check for dot in domain
                if '.' not in domain_part:
                    is_valid = False
                    errors.append("❌ Domain must contain at least one dot (.)")
                else:
                    # Check if starts or ends with dot or hyphen
                    if domain_part.startswith('.') or domain_part.endswith('.'):
                        is_valid = False
                        errors.append("❌ Domain cannot start or end with a dot")

                    if domain_part.startswith('-') or domain_part.endswith('-'):
                        is_valid = False
                        errors.append("❌ Domain cannot start or end with a hyphen")

                    # Split domain into labels (parts separated by dots)
                    domain_labels = domain_part.split('.')

                    for label in domain_labels:
                        if len(label) == 0:
                            is_valid = False
                            errors.append("❌ Domain cannot have empty labels (consecutive dots)")
                            break

                        if len(label) > 63:
                            is_valid = False
                            errors.append(f"❌ Domain label '{label}' exceeds 63 characters")
                            break

                        # Check for valid characters in domain (alphanumeric and hyphen)
                        valid_domain_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
                        for char in label:
                            if char not in valid_domain_chars:
                                is_valid = False
                                errors.append(f"❌ Invalid character '{char}' in domain")
                                break

                        # Check if label starts or ends with hyphen
                        if label.startswith('-') or label.endswith('-'):
                            is_valid = False
                            errors.append(f"❌ Domain label '{label}' cannot start or end with hyphen")
                            break

                    # Check top-level domain (last part)
                    if len(domain_labels) > 0:
                        tld = domain_labels[-1]
                        if len(tld) < 2:
                            is_valid = False
                            errors.append("❌ Top-level domain must be at least 2 characters")

                        # Check if TLD is all letters
                        tld_is_letters = True
                        for char in tld:
                            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                                tld_is_letters = False
                                break

                        if not tld_is_letters:
                            is_valid = False
                            errors.append("❌ Top-level domain should contain only letters")

        # Additional checks using regex for common patterns
        if is_valid:
            # Check for spaces
            if ' ' in email:
                is_valid = False
                errors.append("❌ Email cannot contain spaces")

    # Display results
    print()
    if is_valid:
        print("✅ VALID EMAIL!")
        print(f"   Email: {email}")

        # Extract and display parts
        if '@' in email:
            parts = email.split('@')
            print(f"   Local part: {parts[0]}")
            print(f"   Domain: {parts[1]}")
    else:
        print("❌ INVALID EMAIL!")
        print("\nErrors found:")
        for error in errors:
            print(f"   {error}")

    print()
    print("=" * 50)
    print()

print("\nGoodbye!")