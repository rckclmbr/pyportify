class PKCS1BaseException(Exception):
    pass

class DecryptionError(PKCS1BaseException):
    pass

class MessageTooLong(PKCS1BaseException):
    pass

class WrongLength(PKCS1BaseException):
    pass

class MessageTooShort(PKCS1BaseException):
    pass

class InvalidSignature(PKCS1BaseException):
    pass

class RSAModulusTooShort(PKCS1BaseException):
    pass

class IntegerTooLarge(PKCS1BaseException):
    pass

class MessageRepresentativeOutOfRange(PKCS1BaseException):
    pass

class CiphertextRepresentativeOutOfRange(PKCS1BaseException):
    pass

class SignatureRepresentativeOutOfRange(PKCS1BaseException):
    pass

class EncodingError(PKCS1BaseException):
    pass
