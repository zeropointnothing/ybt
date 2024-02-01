"""
Encryption module for YBT.
"""
from cryptography.fernet import Fernet
import base64, hashlib

def gen_key(key: bytes) -> bytes:
    """
    Generates a key that Fernet will accept.

    Hashes `key` and converts it to a urlsafe key.
    """
    assert isinstance(key, bytes)

    hlib = hashlib.md5()
    hlib.update(key)

    return base64.urlsafe_b64encode(hlib.hexdigest().encode('latin-1'))

def __vigenere_encrypt(plain_text: str, key):
   encrypted_text = ''
   key_repeated = (key * (len(plain_text) // len(key))) + key[:len(plain_text) % len(key)]
   for i in range(len(plain_text)):
       if plain_text[i].isalpha():
           shift = ord(key_repeated[i].upper()) - ord('A')
           if plain_text[i].isupper():
               encrypted_text += chr((ord(plain_text[i]) + shift - ord('A')) % 26 + ord('A'))
           else:
               encrypted_text += chr((ord(plain_text[i]) + shift - ord('a')) % 26 + ord('a'))
       else:
           encrypted_text += plain_text[i]
   return encrypted_text

def __vigenere_decrypt(encrypted_text: str, key):
   decrypted_text = ''
   key_repeated = (key * (len(encrypted_text) // len(key))) + key[:len(encrypted_text) % len(key)]
   for i in range(len(encrypted_text)):
       if encrypted_text[i].isalpha():
           shift = ord(key_repeated[i].upper()) - ord('A')
           if encrypted_text[i].isupper():
               decrypted_text += chr((ord(encrypted_text[i]) - shift - ord('A')) % 26 + ord('A'))
           else:
               decrypted_text += chr((ord(encrypted_text[i]) - shift - ord('a')) % 26 + ord('a'))
       else:
           decrypted_text += encrypted_text[i]
   return decrypted_text

def full_encrypt(data: bytes, key: bytes):
    """
    Fully encrypts a file.
    
    `key` must meet Fernet standards to encrypt. You can generate a key from another key by using
    the `gen_key` function.


    @data: (bytes) - The data to encrypt.
    @key: (bytes) - The encryption key.
    """
    shifted_data = __vigenere_encrypt(data.decode(), key.decode())

    enc = Fernet(key)
    encrypted_data = enc.encrypt(shifted_data.encode())

    return encrypted_data

def full_decrypt(data: bytes, key: bytes):
    """
    Fully decrypts a file.
    
    Expects `data` to be in the same state as it was when `full_encrypt` finished.

    `key` must meet Fernet standards to decrypt. You can generate a key from another key by using
    the `gen_key` function.


    @data: (bytes) - The data to decrypt.
    @key: (bytes) - The decryption key.
    """
    enc = Fernet(key)

    decrypted_data = enc.decrypt(data)
    shifted_data = __vigenere_decrypt(decrypted_data.decode(), key.decode())

    return shifted_data