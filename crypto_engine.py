"""
crypto_engine.py
Core E2EE cryptographic operations for the platform.
Uses X25519 (ECDH) for key exchange and AES-256-GCM for content encryption.
All operations are performed client-side (within the Streamlit session).
"""

import os
import base64
import json
import hashlib
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# ──────────────────────────────────────────────
# KEY PAIR GENERATION  (X25519 ECDH)
# ──────────────────────────────────────────────

def generate_key_pair() -> dict:
    """Generate an X25519 key pair. Returns base64-encoded pub/priv keys."""
    private_key = X25519PrivateKey.generate()
    public_key  = private_key.public_key()

    priv_b64 = base64.b64encode(
        private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    ).decode()
    pub_b64 = base64.b64encode(
        public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    ).decode()

    return {"private_key": priv_b64, "public_key": pub_b64}


def derive_shared_secret(my_private_b64: str, their_public_b64: str) -> bytes:
    """Perform X25519 ECDH and derive a 32-byte shared secret via HKDF-SHA256."""
    priv_bytes = base64.b64decode(my_private_b64)
    pub_bytes  = base64.b64decode(their_public_b64)

    private_key = X25519PrivateKey.from_private_bytes(priv_bytes)
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    public_key  = X25519PublicKey.from_public_bytes(pub_bytes)

    raw_secret = private_key.exchange(public_key)

    # HKDF to derive a proper symmetric key
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"e2ee-messaging-v1",
    )
    return hkdf.derive(raw_secret)


# ──────────────────────────────────────────────
# AES-256-GCM  ENCRYPT / DECRYPT
# ──────────────────────────────────────────────

def encrypt_message(plaintext: str, shared_secret: bytes) -> str:
    """
    Encrypt a plaintext string with AES-256-GCM.
    Returns a base64-encoded JSON blob: {nonce, ciphertext}.
    """
    aesgcm  = AESGCM(shared_secret)
    nonce   = os.urandom(12)          # 96-bit nonce
    ct      = aesgcm.encrypt(nonce, plaintext.encode(), None)

    payload = {
        "nonce": base64.b64encode(nonce).decode(),
        "ct":    base64.b64encode(ct).decode(),
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()


def decrypt_message(cipherblob: str, shared_secret: bytes) -> str:
    """Decrypt an AES-256-GCM cipherblob produced by encrypt_message."""
    payload = json.loads(base64.b64decode(cipherblob).decode())
    nonce   = base64.b64decode(payload["nonce"])
    ct      = base64.b64decode(payload["ct"])

    aesgcm    = AESGCM(shared_secret)
    plaintext = aesgcm.decrypt(nonce, ct, None)
    return plaintext.decode()


def encrypt_file(file_bytes: bytes, shared_secret: bytes) -> bytes:
    """
    Encrypt raw file bytes using AES-256-GCM (chunked, 1 MB chunks).
    Returns a bytes blob: [4-byte chunk_count][chunk_1_nonce+ct]...
    """
    CHUNK = 1024 * 1024   # 1 MB
    aesgcm = AESGCM(shared_secret)
    chunks = [file_bytes[i:i+CHUNK] for i in range(0, len(file_bytes), CHUNK)]

    out_parts = [len(chunks).to_bytes(4, "big")]
    for chunk in chunks:
        nonce = os.urandom(12)
        ct    = aesgcm.encrypt(nonce, chunk, None)
        # 4-byte length prefix + nonce + ciphertext
        blob  = nonce + ct
        out_parts.append(len(blob).to_bytes(4, "big") + blob)

    return b"".join(out_parts)


def decrypt_file(enc_bytes: bytes, shared_secret: bytes) -> bytes:
    """Decrypt a chunked file blob produced by encrypt_file."""
    aesgcm    = AESGCM(shared_secret)
    n_chunks  = int.from_bytes(enc_bytes[:4], "big")
    pos       = 4
    plaintext = bytearray()

    for _ in range(n_chunks):
        blob_len = int.from_bytes(enc_bytes[pos:pos+4], "big")
        pos     += 4
        blob     = enc_bytes[pos:pos+blob_len]
        pos     += blob_len

        nonce = blob[:12]
        ct    = blob[12:]
        plaintext.extend(aesgcm.decrypt(nonce, ct, None))

    return bytes(plaintext)


# ──────────────────────────────────────────────
# PASSWORD HASHING  (PBKDF2-SHA256)
# ──────────────────────────────────────────────

def hash_password(password: str, salt: bytes = None) -> dict:
    """Hash a password with PBKDF2-HMAC-SHA256. Returns {hash_b64, salt_b64}."""
    if salt is None:
        salt = os.urandom(32)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    pw_hash = kdf.derive(password.encode())
    return {
        "hash": base64.b64encode(pw_hash).decode(),
        "salt": base64.b64encode(salt).decode(),
    }


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    salt   = base64.b64decode(stored_salt)
    result = hash_password(password, salt)
    return result["hash"] == stored_hash


# ──────────────────────────────────────────────
# FINGERPRINT  (public key verification)
# ──────────────────────────────────────────────

def key_fingerprint(public_key_b64: str) -> str:
    """Return a human-readable SHA-256 fingerprint of a public key."""
    raw  = base64.b64decode(public_key_b64)
    h    = hashlib.sha256(raw).hexdigest().upper()
    return ":".join(h[i:i+4] for i in range(0, 32, 4))
