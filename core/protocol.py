# -*- coding: utf-8 -*-
"""Garena protobuf protocol builders and decoders."""
import sys
import os
from typing import Optional, Dict, Any

# Ensure target directory is in python path to import pb2 modules
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import like_pb2
import uid_generator_pb2
import visit_count_pb2
from core.crypto import encrypt_message

def create_like_payload(target_uid: int, region: str) -> bytes:
    """Serializes and encrypts like_pb2.like protobuf frame."""
    msg = like_pb2.like()
    msg.uid = int(target_uid)
    msg.region = str(region).upper()
    serialized = msg.SerializeToString()
    enc_hex = encrypt_message(serialized)
    return bytes.fromhex(enc_hex)

def create_profile_payload(target_uid: int) -> bytes:
    """Serializes and encrypts uid_generator_pb2.uid_generator protobuf frame."""
    msg = uid_generator_pb2.uid_generator()
    msg.saturn_ = int(target_uid)
    msg.garena = 1
    serialized = msg.SerializeToString()
    enc_hex = encrypt_message(serialized)
    return bytes.fromhex(enc_hex)

def parse_profile_response(binary_data: bytes) -> Optional[Dict[str, Any]]:
    """Decodes Garena's visit_count_pb2.Info response."""
    try:
        decoded = visit_count_pb2.Info()
        decoded.ParseFromString(binary_data)
        info = decoded.AccountInfo
        return {
            "uid": info.UID,
            "nickname": info.PlayerNickname,
            "region": info.PlayerRegion,
            "level": info.Levels,
            "likes": info.Likes
        }
    except Exception:
        return None
