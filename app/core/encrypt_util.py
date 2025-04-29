from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode
import os
from app.core.config import settings

# Use SECRET_KEY for key derivation, but you may want to use a separate salt for production
SECRET_KEY = settings.SECRET_KEY.encode()
SALT = b'dbcapture-conn-salt'  # Should be kept secret and unique in production

# Key derivation (AES-256)
def _derive_key(secret_key: bytes, salt: bytes = SALT) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend(),
    )
    return kdf.derive(secret_key)

KEY = _derive_key(SECRET_KEY)

def encrypt_password(plain: str) -> str:
    aesgcm = AESGCM(KEY)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plain.encode(), None)
    return urlsafe_b64encode(nonce + ct).decode()

def decrypt_password(token: str) -> str:
    raw = urlsafe_b64decode(token.encode())
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(KEY)
    return aesgcm.decrypt(nonce, ct, None).decode()
