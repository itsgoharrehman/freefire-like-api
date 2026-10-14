import base64
from typing import Any
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from google.protobuf import json_format, message

MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')


def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded)


def aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ciphertext)
    return unpad(decrypted, AES.block_size)


def decode_protobuf(encoded_data: bytes, message_type: Any) -> Any:
    message_instance = message_type()
    try:
        message_instance.ParseFromString(encoded_data)
    except Exception:
        if len(encoded_data) > 64:
            message_instance.ParseFromString(encoded_data[64:])
        else:
            raise
    return message_instance


def json_to_proto(json_dict: dict, proto_message: Any) -> bytes:
    json_format.ParseDict(json_dict, proto_message)
    return proto_message.SerializeToString()
