from cryptography.fernet import Fernet
from django.conf import settings

# Load the key ONCE from settings
cipher = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """
    Encrypts a string (like a card number) and returns a string safe for DB storage.
    """
    if not data:
        return ""
    # 1. Convert string to bytes
    # 2. Encrypt
    # 3. Convert encrypted bytes back to string for storage
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    Takes the encrypted string from DB and returns the original card number.
    """
    if not encrypted_data:
        return ""
    # 1. Convert string to bytes
    # 2. Decrypt
    # 3. Convert decrypted bytes back to string
    return cipher.decrypt(encrypted_data.encode()).decode()
