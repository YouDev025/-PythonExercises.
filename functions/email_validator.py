
"""
Email Address Validator

This program validates email addresses entered by the user.
It checks if the email follows the correct format:
- Contains exactly one '@' symbol
- Has a valid domain part after '@'
- Contains only allowed characters
- Has valid username (local part) before '@'
"""

import re
import string


def validate_email(email):
    """
    Validate an email address based on common rules.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    # Check if email is empty
    if not email or not email.strip():
        return False, "Email cannot be empty"
    
    email = email.strip()
    
    # Check for exactly one '@' symbol
    at_count = email.count('@')
    if at_count == 0:
        return False, "Email must contain '@' symbol"
    elif at_count > 1:
        return False, "Email must contain exactly one '@' symbol"
    
    # Split email into local and domain parts
    try:
        local_part, domain_part = email.split('@')
    except ValueError:
        return False, "Invalid email format"
    
    # Validate local part (before '@')
    is_valid, error = validate_local_part(local_part)
    if not is_valid:
        return False, error
    
    # Validate domain part (after '@')
    is_valid, error = validate_domain_part(domain_part)
    if not is_valid:
        return False, error
    
    return True, "Valid email address"


def validate_local_part(local):
    """
    Validate the local part (username) of the email address.
    
    Args:
        local (str): Local part of email (before '@')
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    # Check if local part is empty
    if not local:
        return False, "Username part cannot be empty"
    
    # Check length (typically 1-64 characters)
    if len(local) > 64:
        return False, "Username part is too long (max 64 characters)"
    
    # Check for invalid starting/ending characters
    if local.startswith('.') or local.endswith('.'):
        return False, "Username cannot start or end with a dot"
    
    # Check for consecutive dots
    if '..' in local:
        return False, "Username cannot contain consecutive dots"
    
    # Allowed characters in local part
    allowed_chars = string.ascii_letters + string.digits + "._+-"
    
    # Check for invalid characters
    for char in local:
        if char not in allowed_chars:
            return False, f"Invalid character '{char}' in username part"
    
    return True, ""


def validate_domain_part(domain):
    """
    Validate the domain part of the email address.
    
    Args:
        domain (str): Domain part of email (after '@')
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    # Check if domain is empty
    if not domain:
        return False, "Domain part cannot be empty"
    
    # Check length (typically 1-255 characters)
    if len(domain) > 255:
        return False, "Domain part is too long (max 255 characters)"
    
    # Check if domain contains at least one dot
    if '.' not in domain:
        return False, "Domain must contain at least one dot (e.g., example.com)"
    
    # Check for invalid starting/ending characters
    if domain.startswith('.') or domain.endswith('.'):
        return False, "Domain cannot start or end with a dot"
    
    if domain.startswith('-') or domain.endswith('-'):
        return False, "Domain cannot start or end with a hyphen"
    
    # Check for consecutive dots
    if '..' in domain:
        return False, "Domain cannot contain consecutive dots"
    
    # Split domain into parts (labels)
    labels = domain.split('.')
    
    # Validate each label
    for label in labels:
        if not label:
            return False, "Domain contains empty label"
        
        if len(label) > 63:
            return False, f"Domain label '{label}' is too long (max 63 characters)"
        
        # Check for valid characters in domain (letters, digits, hyphens)
        if not re.match(r'^[a-zA-Z0-9-]+$', label):
            return False, f"Domain label '{label}' contains invalid characters"
        
        # Check that label doesn't start or end with hyphen
        if label.startswith('-') or label.endswith('-'):
            return False, f"Domain label '{label}' cannot start or end with hyphen"
    
    # Check that TLD (last label) is at least 2 characters and contains only letters
    tld = labels[-1]
    if len(tld) < 2:
        return False, "Top-level domain must be at least 2 characters"
    
    if not tld.isalpha():
        return False, "Top-level domain must contain only letters"
    
    return True, ""


def get_email_input():
    """
    Get email address from user with option to quit.
    
    Returns:
        str or None: Email address or None if user wants to quit
    """
    email = input("\nEnter email address to validate (or 'quit' to exit): ").strip()
    
    if email.lower() in ['quit', 'exit', 'q']:
        return None
    
    return email


def display_validation_result(email, is_valid, message):
    """
    Display the validation result in a formatted way.
    
    Args:
        email (str): Email address that was validated
        is_valid (bool): Whether the email is valid
        message (str): Validation message
    """
    print("\n" + "="*60)
    print("VALIDATION RESULT")
    print("="*60)
    print(f"Email: {email}")
    print(f"Status: {'VALID' if is_valid else 'INVALID'}")
    
    if is_valid:
        print(f"Message: {message}")
    else:
        print(f"Reason: {message}")
    
    print("="*60)


def main():
    """Main function to run the email validator program."""
    print("="*60)
    print("EMAIL ADDRESS VALIDATOR")
    print("="*60)
    print("\nThis program validates email addresses based on standard rules.")
    
    # Main validation loop
    while True:
        email = get_email_input()
        
        # Check if user wants to quit
        if email is None:
            print("\nThank you for using Email Address Validator!")
            break
        
        # Validate the email
        is_valid, message = validate_email(email)
        
        # Display result
        display_validation_result(email, is_valid, message)


if __name__ == "__main__":
    main()