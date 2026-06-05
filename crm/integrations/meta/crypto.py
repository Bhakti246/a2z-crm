import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet():
    key = settings.META_TOKEN_ENCRYPTION_KEY
    if not key:
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    elif isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_value(value):
    if value is None:
        return ''
    return _fernet().encrypt(str(value).encode()).decode()


def decrypt_value(value):
    if not value:
        return ''
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError('Encrypted token could not be decrypted') from exc
