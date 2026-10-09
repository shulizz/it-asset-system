"""Encryption helpers for recoverable third-party credentials stored in SQLite."""
import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


_PREFIX = "enc:v1:"


def _fernet():
    secret = os.getenv("IT_ASSET_SECRET_KEY", "")
    if not secret or secret == "it-asset-secret-key-change-in-production":
        raise RuntimeError("IT_ASSET_SECRET_KEY must be configured before using stored credentials")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_credential(value):
    if value is None or value == "":
        return value
    if isinstance(value, str) and value.startswith(_PREFIX):
        return value
    token = _fernet().encrypt(str(value).encode("utf-8")).decode("ascii")
    return _PREFIX + token


def decrypt_credential(value):
    if value is None or not value.startswith(_PREFIX):
        return value  # legacy plaintext; new writes are always encrypted
    try:
        token = value[len(_PREFIX):].encode("ascii")
        return _fernet().decrypt(token).decode("utf-8")
    except (InvalidToken, UnicodeError, ValueError) as exc:
        raise RuntimeError("Stored credential cannot be decrypted; verify IT_ASSET_SECRET_KEY") from exc
