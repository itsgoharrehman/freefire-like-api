# -*- coding: utf-8 -*-
"""AES CBC cryptography routines."""
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

KEY = b'Yg&tc%DEuh6%Zc^8'
IV  = b'6oyZDr22E3ychjM%'

def encrypt_message(plaintext: bytes) -> str:
    """Encrypts raw protobuf payload using Garena production AES-CBC key/IV."""
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded = pad(plaintext, AES.block_size)
    encrypted = cipher.encrypt(padded)
    return encrypted.hex()

def decrypt_message(hex_str: str) -> bytes:
    """Decrypts Garena production AES-CBC encrypted response."""
    data = bytes.fromhex(hex_str)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return unpad(cipher.decrypt(data), AES.block_size)
