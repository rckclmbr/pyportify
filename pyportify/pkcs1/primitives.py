import binascii

import operator

import math

import sys

from functools import reduce

from .defaults import default_crypto_random

try:
    import gmpy
except ImportError:
    gmpy = None

from . import exceptions


'''Primitive functions extracted from the PKCS1 RFC'''

def _pow(a, b, mod):
    '''Exponentiation function using acceleration from gmpy if possible'''
    if gmpy:
        return long(pow(gmpy.mpz(a), gmpy.mpz(b), gmpy.mpz(mod)))
    else:
        return pow(a, b, mod)

def integer_ceil(a, b):
    '''Return the ceil integer of a div b.'''
    quanta, mod = divmod(a, b)
    if mod:
        quanta += 1
    return quanta

def integer_byte_size(n):
    '''Returns the number of bytes necessary to store the integer n.'''
    quanta, mod = divmod(integer_bit_size(n), 8)
    if mod or n == 0:
        quanta += 1
    return quanta

def integer_bit_size(n):
    '''Returns the number of bits necessary to store the integer n.'''
    if n == 0:
        return 1
    s = 0
    while n:
        s += 1
        n >>= 1
    return s

def bezout(a, b):
    '''Compute the bezout algorithm of a and b, i.e. it returns u, v, p such as:

          p = GCD(a,b)
          a * u + b * v = p

       Copied from http://www.labri.fr/perso/betrema/deug/poly/euclide.html.
    '''
    u = 1
    v = 0
    s = 0
    t = 1
    while b > 0:
        q = a // b
        r = a % b
        a = b
        b = r
        tmp = s
        s = u - q * s
        u = tmp
        tmp = t
        t = v - q * t
        v = tmp
    return u, v, a

def i2osp(x, x_len):
    '''Converts the integer x to its big-endian representation of length
       x_len.
    '''
    if x > 256**x_len:
        raise exceptions.IntegerTooLarge
    h = hex(x)[2:]
    if h[-1] == 'L':
        h = h[:-1]
    if len(h) & 1 == 1:
        h = '0%s' % h
    x = binascii.unhexlify(h)
    return b'\x00' * int(x_len-len(x)) + x

def os2ip(x):
    '''Converts the byte string x representing an integer reprented using the
       big-endian convient to an integer.
    '''
    h = binascii.hexlify(x)
    return int(h, 16)

def string_xor(a, b):
    '''Computes the XOR operator between two byte strings. If the strings are
       of different lengths, the result string is as long as the shorter.
    '''
    if sys.version_info[0] < 3:
        return ''.join((chr(ord(x) ^ ord(y)) for (x,y) in zip(a,b)))
    else:
        return bytes(x ^ y for (x, y) in zip(a, b))

def product(*args):
    '''Computes the product of its arguments.'''
    return reduce(operator.__mul__, args)

def get_nonzero_random_bytes(length, rnd=default_crypto_random):
    '''
       Accumulate random bit string and remove \0 bytes until the needed length
       is obtained.
    '''
    result = []
    i = 0
    while i < length:
        l = rnd.getrandbits(12*length)
        s = i2osp(l, 3*length)
        s = s.replace('\x00', '')
        result.append(s)
        i += len(s)
    return (''.join(result))[:length]

def constant_time_cmp(a, b):
    '''Compare two strings using constant time.'''
    result = True
    for x, y in zip(a,b):
        result &= (x == y)
    return result

import textwrap

def dump_hex(data):
    if isinstance(data, basestring):
        print('length', len(data))
        print(textwrap.fill(''.join(['%s ' % x.encode('hex') for x in data]), 72))
