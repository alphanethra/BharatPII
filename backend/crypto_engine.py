import hashlib
from cryptography.fernet import Fernet


# ==========================================================
# 1️⃣ SHA-256 HASHING (FOR AUDIT LOGS)
# ==========================================================

def hash_value(value: str) -> str:
    """
    Returns SHA-256 hash of a string value.
    Used for secure audit logging of PII.
    """
    return hashlib.sha256(value.encode()).hexdigest()


def hash_pii_results(pii_results: dict) -> dict:
    """
    Hash all detected PII values.
    Returns dictionary with hashed values only.
    """

    hashed_data = {}

    for key, values in pii_results.items():
        hashed_data[key] = [hash_value(v) for v in values]

    return hashed_data


# ==========================================================
# 2️⃣ AES ENCRYPTION USING FERNET
# ==========================================================

# ⚠ In production, store this key securely (env variable)
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)


def encrypt_bytes(data: bytes) -> bytes:
    """
    Encrypt raw bytes using AES (Fernet).
    """
    return cipher.encrypt(data)


def decrypt_bytes(data: bytes) -> bytes:
    """
    Decrypt encrypted bytes.
    """
    return cipher.decrypt(data)