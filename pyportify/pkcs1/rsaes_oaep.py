import hashlib

from . import primitives
from . import exceptions
from . import mgf
from .defaults import default_crypto_random

def encrypt(public_key, message, label=b'', hash_class=hashlib.sha1,
        mgf=mgf.mgf1, seed=None, rnd=default_crypto_random):
    '''Encrypt a byte message using a RSA public key and the OAEP wrapping
       algorithm,

       Parameters:
       public_key - an RSA public key
       message - a byte string
       label - a label a per-se PKCS#1 standard
       hash_class - a Python class for a message digest algorithme respecting
         the hashlib interface
       mgf1 - a mask generation function
       seed - a seed to use instead of generating it using a random generator
       rnd - a random generator class, respecting the random generator
       interface from the random module, if seed is None, it is used to
       generate it.

       Return value:
       the encrypted string of the same length as the public key
    '''

    hash = hash_class()
    h_len = hash.digest_size
    k = public_key.byte_size
    max_message_length = k - 2 * h_len - 2
    if len(message) > max_message_length:
        raise exceptions.MessageTooLong
    hash.update(label)
    label_hash = hash.digest()
    ps = b'\0' * int(max_message_length - len(message))
    db = b''.join((label_hash, ps, b'\x01', message))
    if not seed:
        seed = primitives.i2osp(rnd.getrandbits(h_len*8), h_len)
    db_mask = mgf(seed, k - h_len - 1, hash_class=hash_class)
    masked_db = primitives.string_xor(db, db_mask)
    seed_mask = mgf(masked_db, h_len, hash_class=hash_class)
    masked_seed = primitives.string_xor(seed, seed_mask)
    em = b''.join((b'\x00', masked_seed, masked_db))
    m = primitives.os2ip(em)
    c = public_key.rsaep(m)
    output = primitives.i2osp(c, k)
    return output

def decrypt(private_key, message, label=b'', hash_class=hashlib.sha1,
        mgf=mgf.mgf1):
    '''Decrypt a byte message using a RSA private key and the OAEP wrapping algorithm,

       Parameters:
       public_key - an RSA public key
       message - a byte string
       label - a label a per-se PKCS#1 standard
       hash_class - a Python class for a message digest algorithme respecting
         the hashlib interface
       mgf1 - a mask generation function

       Return value:
       the string before encryption (decrypted)
    '''
    hash = hash_class()
    h_len = hash.digest_size
    k = private_key.byte_size
    # 1. check length
    if len(message) != k or k < 2 * h_len + 2:
        raise ValueError('decryption error')
    # 2. RSA decryption
    c = primitives.os2ip(message)
    m = private_key.rsadp(c)
    em = primitives.i2osp(m, k)
    # 4. EME-OAEP decoding
    hash.update(label)
    label_hash = hash.digest()
    y, masked_seed, masked_db = em[0], em[1:h_len+1], em[1+h_len:]
    if y != b'\x00' and y != 0:
        raise ValueError('decryption error')
    seed_mask = mgf(masked_db, h_len)
    seed = primitives.string_xor(masked_seed, seed_mask)
    db_mask = mgf(seed, k - h_len - 1)
    db = primitives.string_xor(masked_db, db_mask)
    label_hash_prime, rest = db[:h_len], db[h_len:]
    i = rest.find(b'\x01')
    if i == -1:
        raise exceptions.DecryptionError
    if rest[:i].strip(b'\x00') != b'':
        print(rest[:i].strip(b'\x00'))
        raise exceptions.DecryptionError
    m = rest[i+1:]
    if label_hash_prime != label_hash:
        raise exceptions.DecryptionError
    return m

