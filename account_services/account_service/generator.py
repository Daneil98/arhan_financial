import random

def generate_account_number():
    """Generate a unique 10-digit account number."""
    return str(random.randint(10**9, 10**10 - 1))

def generate_card_number():
    """Generate a unique 16-digit card number."""
    return str(random.randint(10**15, 10**16 - 1))

def generate_cvv():
    """Generate a 3-digit CVV number."""
    return str(random.randint(100, 999))