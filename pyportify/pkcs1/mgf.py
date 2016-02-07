import hashlib

from .primitives import integer_ceil, i2osp

def mgf1(mgf_seed, mask_len, hash_class=hashlib.sha1):
    '''
       Mask Generation Function v1 from the PKCS#1 v2.0 standard.

       mgs_seed - the seed, a byte string
       mask_len - the length of the mask to generate
       hash_class - the digest algorithm to use, default is SHA1

       Return value: a pseudo-random mask, as a byte string
       '''
    h_len = hash_class().digest_size
    if mask_len > 0x10000:
        raise ValueError('mask too long')
    T = b''
    for i in range(0, integer_ceil(mask_len, h_len)):
        C = i2osp(i, 4)
        T = T + hash_class(mgf_seed + C).digest()
    return T[:mask_len]


