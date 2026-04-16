#!/usr/bin/env python3
"""Minimal test to run INSIDE the HA container to check v3.5 connectivity."""
import asyncio
import os
import struct
import time

# Try to import from HA's cryptography
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DEVICE_ID = "bfbecd0dc4a9b8bc17m9jy"
IP = "192.168.1.18"
PORT = 6668
LOCAL_KEY = b"Tw.itw`XWQqB[sG/"
TIMEOUT = 10.0

MAGIC_PREFIX_35 = 0x00006699
MAGIC_SUFFIX_35 = 0x00009966
MAGIC_SUFFIX_35_BYTES = struct.pack(">I", MAGIC_SUFFIX_35)


def build_sess_key_neg_start(nonce, key, seq=1):
    payload_size = 12 + len(nonce) + 16
    header = struct.pack(">IBBIII", MAGIC_PREFIX_35, 0, 0, seq, 0x03, payload_size)
    aad = header[4:]
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ct_with_tag = aesgcm.encrypt(iv, nonce, aad)
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    footer = struct.pack(">16sI", tag, MAGIC_SUFFIX_35)
    return header + iv + ciphertext + footer


async def main():
    nonce = os.urandom(16)
    msg = build_sess_key_neg_start(nonce, LOCAL_KEY)
    print(f"Message: {msg.hex()} ({len(msg)} bytes)")

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(IP, PORT), timeout=TIMEOUT
        )
        print(f"Connected to {IP}:{PORT}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    writer.write(msg)
    await writer.drain()
    print("Sent SESS_KEY_NEG_START")

    try:
        raw = await asyncio.wait_for(
            reader.readuntil(MAGIC_SUFFIX_35_BYTES), timeout=TIMEOUT
        )
        print(f"Received {len(raw)} bytes: {raw[:20].hex()}...")
        print("SUCCESS!")
    except asyncio.IncompleteReadError as e:
        print(f"IncompleteReadError: partial={len(e.partial)} bytes, hex={e.partial.hex()}")
    except asyncio.TimeoutError:
        print("TIMEOUT waiting for response")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    writer.close()


asyncio.run(main())
