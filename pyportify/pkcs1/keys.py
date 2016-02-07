import fractions
from . import primitives
from . import exceptions

from .defaults import default_crypto_random
from .primes import get_prime, DEFAULT_ITERATION

class RsaPublicKey(object):
    __slots__ = ('n', 'e', 'bit_size', 'byte_size')

    def __init__(self, n, e):
        self.n = n
        self.e = e
        self.bit_size = primitives.integer_bit_size(n)
        self.byte_size = primitives.integer_byte_size(n)


    def __repr__(self):
        return '<RsaPublicKey n: %d e: %d bit_size: %d>' % (self.n, self.e, self.bit_size)

    def rsavp1(self, s):
        if not (0 <= s <= self.n-1):
            raise exceptions.SignatureRepresentativeOutOfRange
        return self.rsaep(s)

    def rsaep(self, m):
        if not (0 <= m <= self.n-1):
            raise exceptions.MessageRepresentativeOutOfRange
        return primitives._pow(m, self.e, self.n)

class RsaPrivateKey(object):
    __slots__ = ('n', 'd', 'bit_size', 'byte_size')

    def __init__(self, n, d):
        self.n = n
        self.d = d
        self.bit_size = primitives.integer_bit_size(n)
        self.byte_size = primitives.integer_byte_size(n)

    def __repr__(self):
        return '<RsaPrivateKey n: %d d: %d bit_size: %d>' % (self.n, self.d, self.bit_size)

    def rsadp(self, c):
        if not (0 <= c <= self.n-1):
            raise exceptions.CiphertextRepresentativeOutOfRange
        return primitives._pow(c, self.d, self.n)

    def rsasp1(self, m):
        if not (0 <= m <= self.n-1):
            raise exceptions.MessageRepresentativeOutOfRange
        return self.rsadp(m)

class MultiPrimeRsaPrivateKey(object):
    __slots__ = ('primes', 'blind', 'blind_inv', 'n', 'e', 'exponents', 'crts', 'bit_size', 'byte_size')

    def __init__(self, primes, e, blind=True, rnd=default_crypto_random):
        self.primes = primes
        self.n = primitives.product(*primes)
        self.e = e
        self.bit_size = primitives.integer_bit_size(self.n)
        self.byte_size = primitives.integer_byte_size(self.n)
        self.exponents = []
        for prime in primes:
            exponent, a, b = primitives.bezout(e, prime-1)
            assert b == 1
            if exponent < 0:
                exponent += prime-1
            self.exponents.append(exponent)
        self.crts = [1]
        R = primes[0]
        for prime in primes[1:]:
            crt, a, b = primitives.bezout(R, prime)
            assert b == 1
            R *= prime
            self.crts.append(crt)
        public = RsaPublicKey(self.n, self.e)
        if blind:
            while True:
                blind_factor = rnd.getrandbits(self.bit_size-1)
                self.blind = public.rsaep(blind_factor)
                u, v, gcd = primitives.bezout(blind_factor, self.n)
                if gcd == 1:
                    self.blind_inv = u if u > 0 else u + self.n
                    assert (blind_factor * self.blind_inv) % self.n == 1
                    break
        else:
            self.blind = None
            self.blind_inv = None


    def __repr__(self):
        return '<RsaPrivateKey n: %d primes: %s bit_size: %d>' % (self.n, self.primes, self.bit_size)


    def rsadp(self, c):
        if not (0 <= c <= self.n-1):
            raise exceptions.CiphertextRepresentativeOutOfRange
        R = 1
        m = 0
        if self.blind:
            c = (c * self.blind) % self.n
        for prime, exponent, crt in zip(self.primes, self.exponents, self.crts):
            m_i = primitives._pow(c, exponent, prime)
            h = ((m_i - m) * crt) % prime
            m += R * h
            R *= prime
        if self.blind_inv:
            m = (m * self.blind_inv) % self.n
        return m

    def rsasp1(self, m):
        if not (0 <= m <= self.n-1):
            raise exceptions.MessageRepresentativeOutOfRange
        return self.rsadp(m)

def generate_key_pair(size=512, number=2, rnd=default_crypto_random, k=DEFAULT_ITERATION,
        primality_algorithm=None, strict_size=True, e=0x10001):
    '''Generates an RSA key pair.

       size:
           the bit size of the modulus, default to 512.
       number:
           the number of primes to use, default to 2.
       rnd:
           the random number generator to use, default to SystemRandom from the
           random library.
       k:
           the number of iteration to use for the probabilistic primality
           tests.
       primality_algorithm:
           the primality algorithm to use.
       strict_size:
           whether to use size as a lower bound or a strict goal.
       e:
           the public key exponent.

       Returns the pair (public_key, private_key).
    '''
    primes = []
    lbda = 1
    bits = size // number + 1
    n = 1
    while len(primes) < number:
        if number - len(primes) == 1:
            bits = size - primitives.integer_bit_size(n) + 1
        prime = get_prime(bits, rnd, k, algorithm=primality_algorithm)
        if prime in primes:
            continue
        if e is not None and fractions.gcd(e, lbda) != 1:
            continue
        if strict_size and number - len(primes) == 1 and primitives.integer_bit_size(n*prime) != size:
            continue
        primes.append(prime)
        n *= prime
        lbda *= prime - 1
    if e is None:
        e = 0x10001
        while e < lbda:
            if fractions.gcd(e, lbda) == 1:
                break
            e += 2
    assert 3 <= e <= n-1
    public = RsaPublicKey(n, e)
    private = MultiPrimeRsaPrivateKey(primes, e, blind=True, rnd=rnd)
    return public, private
